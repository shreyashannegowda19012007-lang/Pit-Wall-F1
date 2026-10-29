import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import subprocess
import signal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import data_ingestion
import ui_elements
import pitwall_ui
import physics_solver
import track_geometry
import strategy_simulator
import race_simulator
import tracinginsights
import head_to_head_ai
from src import config
from telemetry_api import api_service

# --- 1. GLOBAL INITIALIZATION ---
st.set_page_config(
    page_title="F1 PIT-WALL | COMMAND CENTER",
    page_icon="F1",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject CSS and Hotkeys
ui_elements.inject_custom_css()
ui_elements.inject_hotkeys()

def start_live_worker():
    if 'live_worker_pid' not in st.session_state:
        worker_script = os.path.join(config.BASE_DIR, "src", "live_stream_worker.py")
        process = subprocess.Popen([sys.executable, worker_script, config.LIVE_STREAM_TXT])
        st.session_state['live_worker_pid'] = process.pid

def stop_live_worker():
    if 'live_worker_pid' in st.session_state:
        pid = st.session_state['live_worker_pid']
        try:
            import psutil
            if psutil.pid_exists(pid):
                proc = psutil.Process(pid)
                proc.terminate()
                proc.wait(timeout=2.0)
        except Exception:
            pass
        del st.session_state['live_worker_pid']

def _main_execution_loop():
    with st.sidebar:
        st.markdown("""
            <div style="margin-bottom: 4px; padding-bottom: 16px; border-bottom: 1px solid #1A2E45;">
                <h1 style="color: #EF4444; font-family: 'Inter', sans-serif; font-size: 22px; font-weight: 900; letter-spacing: 3px; margin: 0; ">
                    PIT-WALL CONSOLE
                </h1>
                <div style="display: flex; align-items: center; gap: 6px; margin-top: 6px;">
                    <span style="display: inline-block; width: 6px; height: 6px; background: #4A90E2; border-radius: 50%; box-shadow: 0 0 6px #4A90E2;"></span>
                    <span style="color: #4A90E2; font-family: 'Share Tech Mono', monospace; font-size: 10px; letter-spacing: 2px; font-weight: 600;">R7 PRODUCTION BUILD</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        app_mode = st.radio("OPERATIONAL MODE", ["REPLAY", "POST-RACE", "LIVE"])

        is_live = app_mode == "LIVE"

        seasons = api_service.get_available_seasons()
        # Default to 2024 for authentic baseline
        default_year_idx = seasons.index(2024) if 2024 in seasons else (len(seasons)-3 if len(seasons) >= 3 else 0)
        selected_year = st.selectbox("CHAMPIONSHIP YEAR", seasons, index=default_year_idx)

        rounds = api_service.get_season_rounds(selected_year)
        round_names = [f"R{r['round_number']} - {r['event_name']} ({r['country']})" for r in rounds]

        # Default to Bahrain Grand Prix for authentic baseline
        default_round_idx = 0
        for i, r in enumerate(rounds):
            if r['event_name'] == "Bahrain Grand Prix":
                default_round_idx = i
                break

        sel_round_idx = st.selectbox("ROUND / GRAND PRIX", range(len(round_names)), index=default_round_idx, format_func=lambda i: round_names[i])

        selected_gp = rounds[sel_round_idx]['event_name']
        avail_sessions = rounds[sel_round_idx].get('available_sessions', ["RACE"])

        # Default to Race session
        default_session_idx = avail_sessions.index("RACE") if "RACE" in avail_sessions else 0
        selected_session = st.selectbox("SESSION", avail_sessions, index=default_session_idx)

        trigger_fetch = st.button("INITIALIZE UPLINK", use_container_width=True)

        if is_live:
            live_active = st.checkbox("Enable OpenF1 Live Uplink", value=False)
            if live_active:
                start_live_worker()
            else:
                stop_live_worker()
                st.caption("ℹ️ Enable checkbox & click Initialize Uplink to stream live session.")
        else:
            stop_live_worker()

        current_session_key = f"{app_mode}_{selected_year}_{selected_gp}_{selected_session}"
        if trigger_fetch:
            # Clear caches and reset session state for new session
            st.cache_data.clear()
            st.session_state['sync_active'] = True
            st.session_state['active_session_key'] = current_session_key
            st.session_state['primary_drv'] = None
            st.session_state['comp_drv'] = None
            st.session_state['current_lap'] = 1
        elif st.session_state.get('active_session_key') and st.session_state.get('active_session_key') != current_session_key:
            st.session_state['sync_active'] = False
            st.session_state['primary_drv'] = None
            st.session_state['comp_drv'] = None

    main_viewport = st.empty()
    if not st.session_state.get('sync_active', False):
        with main_viewport.container():
            ui_elements.render_standby_screen()
        return

    main_viewport.empty()

    # --- FETCH DATA WITH STAGED STATUS INDICATOR ---
    status_placeholder = st.empty()
    with status_placeholder.status("INITIALIZING PIT-WALL TELEMETRY UPLINK...", expanded=True) as status_box:
        st.write(f"📡 Resolving session identity: {selected_gp} ({selected_year}) - {selected_session}...")
        st.write("🔍 Initializing data pipeline and checking local telemetry cache...")
        if is_live:
            st.write("🌐 Connecting to live telemetry ingestion channel...")
            data_bundle = data_ingestion.fetch_live_session_data(selected_year, selected_gp, selected_session)
        else:
            st.write("⚡ Fetching timing matrices, telemetry traces & weather feeds...")
            data_bundle = data_ingestion.fetch_session_data(selected_year, selected_gp, selected_session)

        if data_bundle.get("success", False):
            st.write("✅ Validating telemetry integrity, driver records, and timing...")
            status_box.update(label="UPLINK SYNCHRONIZED", state="complete", expanded=False)
        else:
            status_box.update(label="UPLINK NOTICE", state="error", expanded=True)
    status_placeholder.empty()

    if not data_bundle.get("success", False):
        err_msg = data_bundle.get('error', 'Unknown Error')
        if is_live:
            st.error(f"LIVE TELEMETRY UPLINK NOTICE: {err_msg}")
            st.info("💡 **Pitwall Guidance**: If no live official session is currently taking place on track, select **REPLAY** or **POST-RACE** mode from the sidebar to inspect full historical telemetry, laps, and tyres.")
        else:
            st.error(f"UPLINK NOTICE: {err_msg}")
            st.info("💡 **Pitwall Guidance**: Select another completed Grand Prix session (such as **2024 Bahrain Grand Prix - RACE** or **Spanish Grand Prix - QUALIFYING**).")
        return

    raw_session = data_bundle["raw_session"]
    laps: pd.DataFrame = data_bundle["laps"]  # type: ignore
    results: pd.DataFrame = data_bundle["results"]  # type: ignore
    weather = data_bundle["weather"]
    messages = data_bundle["messages"]
    info = data_bundle["info"]
    provenance = data_bundle.get("provenance")

    # 1. Driver Selection in Sidebar (Resolved before header to guarantee valid CAR #)
    drivers_list = results['Abbreviation'].tolist() if 'Abbreviation' in results.columns else []
    if not drivers_list and 'Driver' in laps.columns:
        drivers_list = [str(d) for d in laps['Driver'].dropna().unique().tolist() if str(d).strip()]
    if not drivers_list and 'DriverNumber' in laps.columns:
        drivers_list = [str(d) for d in laps['DriverNumber'].dropna().unique().tolist() if str(d).strip()]
    if not drivers_list:
        st.warning("No driver records found in loaded session data.")
        return

    with st.sidebar:
        st.markdown("### DRIVER CONTEXT")
        prim_idx = 0
        comp_idx = 1 if len(drivers_list) > 1 else 0

        curr_prim = st.session_state.get('primary_drv')
        prim_selected_idx = drivers_list.index(curr_prim) if curr_prim in drivers_list else prim_idx

        primary = st.selectbox(
            "PRIMARY DRIVER", drivers_list,
            index=prim_selected_idx,
            key="sb_primary"
        )
        st.session_state['primary_drv'] = primary

        curr_comp = st.session_state.get('comp_drv')
        comp_selected_idx = drivers_list.index(curr_comp) if curr_comp in drivers_list else comp_idx

        comp = st.selectbox(
            "COMPARISON DRIVER", drivers_list,
            index=comp_selected_idx,
            key="sb_comp"
        )
        st.session_state['comp_drv'] = comp

    # 2. Global Session Bar with resolved driver references
    pitwall_ui.render_session_header(info, weather, app_mode, primary, comp, provenance)

    # 3. Replay Temporal Filter & Scrubber
    max_laps = int(laps['LapNumber'].max()) if not laps.empty and 'LapNumber' in laps.columns else 1
    current_lap = max_laps
    if app_mode == "REPLAY":
        c_scrub1, c_scrub2 = st.columns([3, 1])
        with c_scrub1:
            current_lap = st.slider(
                "TEMPORAL LAP SCRUBBER",
                min_value=1,
                max_value=max_laps,
                value=min(st.session_state.get('current_lap', max_laps), max_laps)
            )
            st.session_state['current_lap'] = current_lap
        with c_scrub2:
            st.markdown(f"""
                <div style="background: rgba(6,14,26,0.9); border: 1px solid rgba(0,240,255,0.25); border-radius: 6px; padding: 10px; margin-top: 18px; text-align: center;">
                    <span style="color: #8FB4D4; font-size: 10px; font-family: 'Inter'; display: block;">REPLAY PROGRESS</span>
                    <span style="color: #4A90E2; font-size: 16px; font-weight: 900; font-family: 'Share Tech Mono';">LAP {current_lap} / {max_laps}</span>
                </div>
            """, unsafe_allow_html=True)

    if app_mode == "REPLAY":
        filtered_laps = laps[laps['LapNumber'] <= current_lap].copy() if not laps.empty and 'LapNumber' in laps.columns else laps
    else:
        filtered_laps = laps

    # 4. Balanced 3-Column Tactical Command Grid
    st.markdown("""
        <div style="border-top: 1px solid #333842; margin: 8px 0 14px 0;"></div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <div style="display: flex; align-items: center; gap: 6px;">
                <span style="display: inline-block; width: 3px; height: 14px; background: #4A90E2; border-radius: 2px;"></span>
                <span style="color: #6B8BAA; font-family: 'Inter', sans-serif; font-size: 9px; letter-spacing: 2px; font-weight: 700;">TACTICAL COMMAND GRID</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col_left, col_center, col_right = st.columns([1.3, 2.0, 1.2])

    with col_left:
        pitwall_ui.render_timing_tower_v2(results, filtered_laps, primary, comp)
        pitwall_ui.render_weather_panel(weather)
        pitwall_ui.render_race_control_log_v2(messages)

    with col_center:
        track_tab, tele_tab, tyre_tab = st.tabs(["CIRCUIT TRACK", "TELEMETRY LAB", "TYRE STRATEGY"])
        with track_tab:
            track_geometry.render_2d_track_with_positions(raw_session, primary, comp, current_lap)
        with tele_tab:
            physics_solver.render_telemetry_comparison(raw_session, filtered_laps, primary, comp, current_lap)
            head_to_head_ai.render_performance_evidence(raw_session, filtered_laps, primary, comp)
        with tyre_tab:
            pitwall_ui.render_tyre_panel(filtered_laps, primary, comp)

    with col_right:
        race_simulator.render_decision_engine_panel(raw_session, filtered_laps, primary, comp, current_lap, app_mode, info)
        strategy_simulator.render_jarvis_deck(raw_session, primary, filtered_laps, results, info)


def main():
    try:
        _main_execution_loop()
    except Exception as e:
        st.error(f"SYSTEM FAILURE: {e}")

if __name__ == "__main__":
    main()
