import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any
import random
import streamlit as st

# --- 1. DATACLASSE ARCHITECTURE ---

@dataclass
class RaceState:
    current_lap: int
    total_laps: int
    weather_state: str
    safety_car_probability: float
    track_temperature: float
    air_temperature: float
    rainfall: bool
    pit_loss_seconds: float
    track_evolution: float # 0.0 to 1.0 (Low to High)
    race_condition: str # 'Green', 'VSC', 'SC', 'Red'

@dataclass
class DriverState:
    driver: str
    position: int
    compound: str
    tyre_age: int
    tyre_health: float
    current_gap: float
    average_pace: float
    gap_ahead: float
    gap_behind: float

@dataclass
class StrategyOption:
    strategy_name: str
    pit_lap: int
    target_compound: str

@dataclass
class SimulationResult:
    strategy_name: str
    expected_finish_time: float
    expected_position: int
    expected_gap: float
    win_probability: float
    podium_probability: float
    avg_lap_time: float
    total_deg_cost: float
    position_delta: int
    risk_score: float
    strategy_score: float
    reasoning: str
    # Distribution structures for Active Inference
    player_times: Optional[np.ndarray] = None
    ranks: Optional[np.ndarray] = None
    probabilistic_position: Optional[Dict[str, Any]] = None
    probabilistic_race_time: Optional[Dict[str, Any]] = None
    p10_pos: int = 10
    p90_pos: int = 10
    p10_time: float = 0.0
    p90_time: float = 0.0

# --- 2. TRACK INTELLIGENCE DATABASE ---

TRACK_PIT_LOSS = {
    "Monaco Grand Prix": 19.5, "Spanish Grand Prix": 22.5, "British Grand Prix": 20.5,
    "Italian Grand Prix": 24.0, "Singapore Grand Prix": 27.0, "Belgian Grand Prix": 20.8,
    "Abu Dhabi Grand Prix": 20.0, "Miami Grand Prix": 22.5, "Bahrain Grand Prix": 22.0,
    "Saudi Arabian Grand Prix": 21.0, "Las Vegas Grand Prix": 21.5, "Japanese Grand Prix": 22.8,
    "Azerbaijan Grand Prix": 21.0, "Austrian Grand Prix": 20.5, "Hungarian Grand Prix": 21.0,
    "Dutch Grand Prix": 19.8, "Qatar Grand Prix": 22.5, "United States Grand Prix": 21.5,
    "Mexico City Grand Prix": 22.0, "São Paulo Grand Prix": 21.0, "Canadian Grand Prix": 19.5,
    "Emilia Romagna Grand Prix": 20.5, "Chinese Grand Prix": 23.0
}

TRACK_STATS = {
    "Monaco Grand_Prix": {"overtake": "Critical", "sc_freq": "High", "evo": "High"},
    "Spanish Grand Prix": {"overtake": "Medium", "sc_freq": "Low", "evo": "Medium"},
    "Italian Grand Prix": {"overtake": "Easy", "sc_freq": "Medium", "evo": "Low"},
    "Singapore Grand Prix": {"overtake": "Hard", "sc_freq": "Very High", "evo": "High"},
}

# --- 3. ACTIVE INFERENCE STRATEGY SUGGESTOR ---

def active_inference_strategy_suggestor(rankings: List[SimulationResult], baseline_strategy_name: str = "Stay Out") -> Dict[str, Any]:
    """
    Monitors simulation output arrays and issues real-time strategy recommendations
    based on risk-reward metrics (P50 shift and standard deviation profiles).
    """
    if not rankings:
        return {
            "directive": "MAINTAIN CURRENT WINDOW. telemetry stream synchronization active.",
            "priority": "LOW",
            "action_flag": False,
            "best_strategy": "Stay Out",
            "expected_p50_gain": 0.0
        }

    baseline = next((r for r in rankings if r.strategy_name == baseline_strategy_name), rankings[-1])
    best_strategy = rankings[0]

    directive = "MAINTAIN CURRENT STRATEGY WINDOW. PACE IS OPTIMAL."
    priority = "LOW"
    action_flag = False
    time_savings = 0.0

    if best_strategy.strategy_name != baseline.strategy_name:
        time_savings = baseline.expected_finish_time - best_strategy.expected_finish_time

        if time_savings > 2.0:
            directive = f"DIRECTIVE: INITIATE {best_strategy.strategy_name.upper()} IMMEDIATELY."
            priority = "CRITICAL"
            action_flag = True
        elif time_savings > 0.0:
            directive = f"TACTICAL RECOMMENDATION: ALTERNATIVE PATH '{best_strategy.strategy_name.upper()}' YIELDS POSITION ADVANTAGE."
            priority = "MEDIUM"
            action_flag = True

    return {
        "directive": directive,
        "priority": priority,
        "action_flag": action_flag,
        "best_strategy": best_strategy.strategy_name,
        "expected_p50_gain": round(time_savings, 2)
    }

# --- 4. VEKTORIZED SIMULATION ENGINE ---

def render_simulator_ui(session, laps, selected_driver, manual_lap, sc_prob, race_cond, track_evo):
    st.markdown("### STOCHASTIC MONTE CARLO RACE SIMULATOR")

    if laps is None or laps.empty:
        st.warning("Telemetry downlink pending...")
        return

    try:
        total_race_laps = session.event['RaceLaps'] if 'RaceLaps' in session.event else 50
        if isinstance(total_race_laps, pd.Series):
            total_race_laps = total_race_laps.iloc[0]
        if pd.isna(total_race_laps):
            total_race_laps = 50
        else:
            total_race_laps = int(total_race_laps)
        track_name = session.event['EventName']
        pit_loss = TRACK_PIT_LOSS.get(track_name, 22.5)

        def get_driver_laps(session_laps, drv_code):
            if hasattr(session_laps, 'pick_drivers'):
                return session_laps.pick_drivers(drv_code)
            return session_laps[session_laps['Driver'] == drv_code]

        current_laps = get_driver_laps(laps, selected_driver)
        if current_laps.empty:
            st.warning(f"No telemetry laps found for {selected_driver}.")
            return

        last_lap = current_laps.iloc[-1]

        # Derive running position at current lap rather than using final race classification
        pos_val = last_lap.get('Position')
        if pd.notna(pos_val):
            current_pos = int(pos_val)
        elif not results.empty and selected_driver in results['Abbreviation'].values:
            pos_val = results[results['Abbreviation'] == selected_driver]['Position'].iloc[0]
            if isinstance(pos_val, pd.Series): pos_val = pos_val.iloc[0]
            current_pos = int(pos_val)
        else:
            current_pos = 10

        avg_pace = current_laps['LapTime'].dt.total_seconds().tail(3).mean()
        if pd.isna(avg_pace): avg_pace = 82.0

        opponents = []
        all_drivers = laps['Driver'].unique()
        for d in all_drivers:
            if d == selected_driver: continue
            d_laps = get_driver_laps(laps, d)
            if d_laps.empty: continue

            d_last = d_laps.iloc[-1]
            p_last = current_laps.iloc[-1]

            common_lap = min(d_last['LapNumber'], p_last['LapNumber'])
            d_match = d_laps[d_laps['LapNumber'] == common_lap]

            # Find gap to leader, not just primary driver
            leader = selected_driver
            if results is not None and not results.empty:
                leader_row = results[results['Position'] == 1.0]
                if not leader_row.empty:
                    leader = leader_row['Abbreviation'].iloc[0]

            ldr_laps = get_driver_laps(laps, leader)
            gap = 0.0
            if not ldr_laps.empty:
                l_match = ldr_laps[ldr_laps['LapNumber'] == common_lap]
                if not d_match.empty and not l_match.empty and pd.notna(d_match['Time'].iloc[0]) and pd.notna(l_match['Time'].iloc[0]):
                    gap = max(0.0, (d_match['Time'].iloc[0] - l_match['Time'].iloc[0]).total_seconds())

            opponents.append(DriverState(
                driver=d, position=0, compound=str(d_last['Compound']),
                tyre_age=int(d_last['TyreLife']), tyre_health=0,
                current_gap=gap,
                average_pace=d_laps['LapTime'].dt.total_seconds().tail(3).mean() or 83.0,
                gap_ahead=0, gap_behind=0
            ))

        weather = session.weather_data.iloc[-1] if not session.weather_data.empty else None

        # Robustly extract weather values avoiding Series ambiguity
        def safe_extract(val, default):
            if val is None: return default
            if isinstance(val, pd.Series): return val.iloc[0]
            return val

        r_state = RaceState(
            current_lap=manual_lap, total_laps=total_race_laps,
            weather_state='Rain' if weather is not None and bool(safe_extract(weather['Rainfall'], False)) else 'Dry',
            safety_car_probability={'None': 0.0, 'Low': 0.1, 'Medium': 0.3, 'High': 0.6}[sc_prob],
            track_temperature=float(safe_extract(weather['TrackTemp'] if weather is not None else 35.0, 35.0)),
            air_temperature=float(safe_extract(weather['AirTemp'] if weather is not None else 25.0, 25.0)),
            rainfall=bool(safe_extract(weather['Rainfall'] if weather is not None else False, False)),
            pit_loss_seconds=pit_loss,
            track_evolution={'Low': 0.1, 'Medium': 0.5, 'High': 0.9}[track_evo],
            race_condition=race_cond
        )

        from bayesian_tyre_model import AdvancedTyreDegradationModel
        t_health = AdvancedTyreDegradationModel.calculate_degradation_slope(
            compound=str(last_lap['Compound']),
            laps_on_tyre=int(last_lap['TyreLife']),
            track_temp=float(safe_extract(weather['TrackTemp'] if weather is not None else 30.0, 30.0)),
            fuel_load_kg=110.0 * (1.0 - (manual_lap / total_race_laps)) if total_race_laps else 50.0
        )

        # Gap for primary driver
        p_gap = 0.0
        if not ldr_laps.empty:
            p_match = current_laps[current_laps['LapNumber'] == last_lap['LapNumber']]
            l_match = ldr_laps[ldr_laps['LapNumber'] == last_lap['LapNumber']]
            if not p_match.empty and not l_match.empty and pd.notna(p_match['Time'].iloc[0]) and pd.notna(l_match['Time'].iloc[0]):
                p_gap = max(0.0, (p_match['Time'].iloc[0] - l_match['Time'].iloc[0]).total_seconds())

        d_state = DriverState(
            driver=selected_driver, position=current_pos, compound=str(last_lap['Compound']),
            tyre_age=int(last_lap['TyreLife']), tyre_health=t_health,
            current_gap=p_gap, average_pace=avg_pace, gap_ahead=1.5, gap_behind=2.0
        )

        # Multi-Objective & Scenario Selection Controls
        c_obj, c_scen = st.columns(2)
        with c_obj:
            obj_choice = st.selectbox(
                "STRATEGY OPTIMIZATION OBJECTIVE:",
                options=[
                    "MAX_PODIUM_PROBABILITY (Balanced)",
                    "MAX_WIN_PROBABILITY (Aggressive)",
                    "MIN_EXPECTED_POSITION (Optimal Pace)",
                    "MIN_DOWNSIDE_RISK (Conservative)",
                    "MIN_RACE_TIME"
                ],
                index=0,
                key="sim_obj_selector"
            )
        with c_scen:
            scen_choice = st.selectbox(
                "RACE SCENARIO PRESET:",
                options=[
                    "NORMAL_WEATHER",
                    "HIGH_TYRE_DEG",
                    "LOW_TYRE_DEG",
                    "EARLY_SAFETY_CAR",
                    "LATE_SAFETY_CAR",
                    "HEAVY_RAIN"
                ],
                index=0,
                key="sim_scenario_selector"
            )

        obj_type = obj_choice.split(" ")[0]

        from monte_carlo_engine import MonteCarloRaceEngine
        from scenario_engine import ScenarioEngine
        from sensitivity_analysis import SensitivityAnalysisEngine
        from race_state import CompleteRaceState, DriverState as RaceDriverState, WeatherState, TrackState, SafetyCarState, TyreState, FuelState

        # Construct CompleteRaceState
        c_race_state = CompleteRaceState(
            current_lap=manual_lap,
            total_laps=total_race_laps,
            drivers={},
            weather=WeatherState(track_temp_c=float(safe_extract(weather['TrackTemp'] if weather is not None else 35.0, 35.0)), rainfall=bool(safe_extract(weather['Rainfall'] if weather is not None else False, False))),
            track=TrackState(track_name=track_name, total_laps=total_race_laps, pit_lane_loss_seconds=pit_loss),
            safety_car=SafetyCarState(sc_probability_per_lap={'None': 0.0, 'Low': 0.1, 'Medium': 0.3, 'High': 0.6}[sc_prob], condition=race_cond)
        )

        c_race_state = ScenarioEngine.apply_scenario(c_race_state, scen_choice)

        t_driver_state = RaceDriverState(
            driver_id=selected_driver,
            position=current_pos,
            current_gap_to_leader_s=p_gap,
            base_pace_s=avg_pace,
            tyre_state=TyreState(compound=str(last_lap['Compound']), age_laps=int(last_lap['TyreLife']), remaining_grip_pct=t_health, thermal_deg_rate=0.07),
            fuel_state=FuelState(fuel_remaining_kg=110.0 * (1.0 - (manual_lap / total_race_laps)) if total_race_laps else 50.0)
        )

        opp_states = []
        for opp in opponents:
            opp_states.append(RaceDriverState(
                driver_id=opp.driver,
                position=opp.position,
                current_gap_to_leader_s=opp.current_gap,
                base_pace_s=opp.average_pace,
                tyre_state=TyreState(compound=opp.compound, age_laps=opp.tyre_age, remaining_grip_pct=opp.tyre_health, thermal_deg_rate=0.07),
                fuel_state=FuelState(fuel_remaining_kg=50.0)
            ))

        c_race_state.drivers = {d.driver_id: d for d in [t_driver_state] + opp_states}

        mc_engine = MonteCarloRaceEngine(iterations=10000, seed=42)
        with st.spinner("Executing 10,000 parallel Monte Carlo simulations..."):
            mc_rankings = mc_engine.rank_strategies(t_driver_state, opp_states, c_race_state, objective=obj_type)

        from decision_engine import DecisionEngine
        # Connect Strategy Panel directly to authoritative DecisionEngine
        decision = DecisionEngine.evaluate(
            race_state=c_race_state,
            bayesian_state=None,  # Or pass if available
            mc_outcomes=mc_rankings,
            objective=obj_type
        )

        directive_color = {
            "PIT_NOW": "#EF4444",
            "PREPARE_PIT": "#FFEA00",
            "STAY_OUT": "#4A90E2"
        }.get(decision.recommended_action, "#27F4D2")

        st.markdown(f"""
            <div style="border: 2px solid {directive_color}; background-color: #0A101C; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="color: {directive_color}; margin: 0; font-family: 'Share Tech Mono';">DECISION ENGINE DIRECTIVE: {decision.recommended_action}</h3>
                <p style="font-size: 16px; font-weight: bold; color: #E2E8F0; margin: 5px 0 0 0;">Recommend: {decision.recommended_action} (Compound: {decision.recommended_compound} lap {decision.recommended_pit_lap})</p>
                <p style="font-size: 13px; color: #27F4D2; margin: 3px 0 0 0;">Expected Finish: P{decision.expected_finish} | Win Prob: {decision.win_probability_pct:.1f}%</p>
                <p style="font-size: 13px; color: #94A3B8; margin: 3px 0 0 0;">Reason: {decision.primary_reason}</p>
                <p style="font-size: 11px; color: #64748B; margin: 3px 0 0 0;">Source: {getattr(decision, 'provenance_metrics', {}).get('source_engine', 'DecisionEngine')}</p>
            </div>
        """, unsafe_allow_html=True)

        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.markdown("##### DRIVER STATE")
            st.write(f"**Position:** P{current_pos} | **Compound:** {d_state.compound} ({d_state.tyre_age} laps)")
            st.write(f"**Est. Health:** {d_state.tyre_health}% | **Laps to Go:** {total_race_laps - manual_lap}")
            st.progress(d_state.tyre_health / 100)

        with col_right:
            st.markdown("##### TRACK INTELLIGENCE")
            st.write(f"**Track:** {track_name} | **Length:** {total_race_laps} Laps")
            st.write(f"**Pit Loss:** {pit_loss}s | **SC Risk:** {sc_prob}")

        from decision_engine import DecisionEngine
        from decision_history import global_decision_audit
        struct_decision = DecisionEngine.evaluate(c_race_state, None, mc_rankings, objective=obj_type)
        global_decision_audit.record_decision(struct_decision)

        # Resolve dynamic comparison driver from session state or opponent field
        comp_driver = st.session_state.get("comparison_driver") or st.session_state.get("comp_driver")
        if not comp_driver or comp_driver == selected_driver:
            valid_comps = [d for d in all_drivers if d != selected_driver]
            comp_driver = valid_comps[0] if valid_comps else ("HAM" if selected_driver != "HAM" else "VER")

        st.divider()
        import pitwall_ui
        pitwall_ui.render_master_pitwall_console(selected_driver, comp_driver)
        pitwall_ui.render_universal_session_selector()
        pitwall_ui.render_system_wide_integration_verification_dashboard()
        pitwall_ui.render_production_hardening_security_dashboard()
        pitwall_ui.render_production_data_platform_performance_dashboard()
        pitwall_ui.render_3d_circuit_spatial_intelligence_dashboard(selected_driver)
        pitwall_ui.render_realtime_live_infrastructure_health_console()
        pitwall_ui.render_historical_replay_scientific_evaluation_dashboard(selected_driver)
        pitwall_ui.render_production_ml_model_lab(selected_driver)
        pitwall_ui.render_full_field_intelligence_dashboard(selected_driver)
        pitwall_ui.render_authoritative_strategy_command_center(selected_driver, comp_driver)
        pitwall_ui.render_unified_tyre_intelligence_dashboard(selected_driver)
        pitwall_ui.render_driver_performance_intelligence_lab(selected_driver, comp_driver)
        pitwall_ui.render_realtime_live_operations_console("SESSION-2024-SPAIN")
        pitwall_ui.render_ai_engineer_jarvis_console(selected_driver, comp_driver)
        pitwall_ui.render_mlops_pipeline_dashboard()
        pitwall_ui.render_advanced_telemetry_lab(selected_driver, comp_driver)
        pitwall_ui.render_drs_ers_energy_dashboard(selected_driver, 2024)
        pitwall_ui.render_advanced_tyre_degradation_dashboard(selected_driver)
        pitwall_ui.render_full_field_simulation_dashboard(selected_driver)
        pitwall_ui.render_advanced_monte_carlo_strategy_dashboard(selected_driver)
        pitwall_ui.render_historical_backtest_evaluation_dashboard(selected_driver)

        from src.rl_config import is_rl_enabled
        if is_rl_enabled():
            pitwall_ui.render_rl_strategy_agent_dashboard(selected_driver)

        pitwall_ui.render_decision_engine_panel(struct_decision, selected_driver)
        pitwall_ui.render_probabilistic_uncertainty_hud(mc_rankings, selected_driver)
        pitwall_ui.render_bayesian_updating_hud(session, laps, pd.DataFrame(), selected_driver, comp_driver)
        pitwall_ui.render_historical_replay_dashboard(session, laps, pd.DataFrame(), selected_driver, comp_driver)
        pitwall_ui.render_evaluation_benchmark_dashboard(session, laps, pd.DataFrame())
        pitwall_ui.render_3d_circuit_replay_dashboard(session, laps, [], selected_driver, comp_driver)
        pitwall_ui.render_unified_realtime_timing_tower("SESSION-2024-SPAIN", "REPLAY")

        # Sensitivity Analysis Card
        if mc_rankings:
            sens_res = SensitivityAnalysisEngine.evaluate_sensitivity(mc_rankings[0].strategy_plan, t_driver_state, opp_states, c_race_state, iterations=1000)
            with st.expander("SENSITIVITY ANALYSIS: UNCERTAINTY FACTOR RANKING"):
                st.markdown(f"**Top Uncertainty Driver:** `{sens_res.get('top_uncertainty_driver')}`")
                for s_fact in sens_res.get("sensitivity_factors", []):
                    st.markdown(f"- **{s_fact['factor']}:** Impact = `{s_fact['relative_impact']}` (Podium Shift: ±{s_fact['podium_delta_pct']}%)")

        results_rows = []
        for r in mc_rankings:
            results_rows.append({
                "Strategy Option": r.strategy_plan.strategy_name,
                "Stops": r.strategy_plan.stop_count,
                "Expected Finish": f"P{r.expected_position:.1f}",
                "Median Finish": f"P{r.median_position}",
                "Win %": f"{r.win_probability*100:.1f}%",
                "Podium %": f"{r.podium_probability*100:.1f}%",
                "Downside Risk % (P10+)": f"{r.downside_risk_probability*100:.1f}%",
                "Expected Race Time": f"{r.expected_race_time_min:.2f} min"
            })

        st.table(pd.DataFrame(results_rows))

    except Exception as e:
        st.error(f"Simulator Offline: {str(e)}")


if __name__ == '__main__':
    st.set_page_config(
        page_title="F1 PIT-WALL | RACE SIMULATOR",
        page_icon="🏎️",
        layout="wide"
    )
    import pitwall_ui
    pitwall_ui.render_master_pitwall_console("VER", "HAM")
    pitwall_ui.render_universal_session_selector()
    pitwall_ui.render_system_wide_integration_verification_dashboard()

def render_decision_engine_panel(raw_session, laps, primary, comp, current_lap, app_mode, info=None):
    import streamlit as st
    from race_state import DriverState as RDriverState, CompleteRaceState, WeatherState, TrackState, SafetyCarState, TyreState, FuelState
    from monte_carlo_engine import MonteCarloRaceEngine
    from decision_engine import DecisionEngine

    if laps.empty:
        st.info("Insufficient data for strategy projection.")
        return

    try:
        primary_laps = laps[laps['Driver'] == primary]
        if primary_laps.empty:
            st.info(f"No strategy data for {primary}.")
            return

        last_lap = primary_laps.iloc[-1]
        compound = last_lap.get('Compound', 'UNKNOWN')
        tyre_life = last_lap.get('TyreLife', 0)

        results = raw_session.results if raw_session else None

        # Determine actual running positions and true race leader at current replay lap
        driver_positions = {}
        for d in laps['Driver'].unique():
            d_laps = laps[laps['Driver'] == d]
            if not d_laps.empty:
                d_last = d_laps.iloc[-1]
                pos_val = d_last.get('Position')
                if pd.notna(pos_val):
                    driver_positions[d] = int(pos_val)

        # Fallback if Position column is unavailable: sort by (LapNumber desc, Time asc)
        if not driver_positions:
            last_records = []
            for d in laps['Driver'].unique():
                d_laps = laps[laps['Driver'] == d]
                if not d_laps.empty:
                    d_last = d_laps.iloc[-1]
                    last_records.append((d, int(d_last['LapNumber']), d_last['Time']))
            last_records.sort(key=lambda x: (-x[1], x[2]))
            driver_positions = {rec[0]: i + 1 for i, rec in enumerate(last_records)}

        # Find true race leader at the current lap
        leader = next((drv for drv, p in driver_positions.items() if p == 1), primary)
        ldr_laps = laps[laps['Driver'] == leader]

        opponents = []
        for d in laps['Driver'].unique():
            if d != primary:
                d_laps = laps[laps['Driver'] == d]
                if not d_laps.empty:
                    d_last = d_laps.iloc[-1]

                    # Calculate real gap to current leader
                    common_lap = min(d_last['LapNumber'], last_lap['LapNumber'])
                    d_match = d_laps[d_laps['LapNumber'] == common_lap]
                    l_match = ldr_laps[ldr_laps['LapNumber'] == common_lap] if not ldr_laps.empty else pd.DataFrame()
                    gap = 0.0
                    if not d_match.empty and not l_match.empty and pd.notna(d_match['Time'].iloc[0]) and pd.notna(l_match['Time'].iloc[0]):
                        gap = max(0.0, (d_match['Time'].iloc[0] - l_match['Time'].iloc[0]).total_seconds())

                    avg_pace = d_laps['LapTime'].dt.total_seconds().tail(3).mean()
                    if pd.isna(avg_pace): avg_pace = 82.0

                    pos = driver_positions.get(d, 10)
                    opponents.append(RDriverState(driver_id=d, position=pos, current_gap_to_leader_s=gap, base_pace_s=avg_pace, tyre_state=TyreState(str(d_last.get('Compound', 'UNKNOWN')), int(d_last.get('TyreLife', 0)), 50.0, 0.05), fuel_state=FuelState(50.0)))

        total_laps = info.get('TotalLaps', 66) if info else 66
        track_name = info.get('EventName', 'Spain') if info else 'Spain'

        c_race_state = CompleteRaceState(
            current_lap=current_lap, total_laps=total_laps, drivers={}, weather=WeatherState(track_temp_c=35.0, rainfall=False),
            track=TrackState(track_name=track_name, total_laps=total_laps, pit_lane_loss_seconds=22.5),
            safety_car=SafetyCarState(sc_probability_per_lap=0.0, condition="Green Flag")
        )

        p_pos = driver_positions.get(primary, 1)
        p_avg_pace = primary_laps['LapTime'].dt.total_seconds().tail(3).mean()
        if pd.isna(p_avg_pace): p_avg_pace = 82.0

        # Primary driver gap to leader
        p_gap = 0.0
        if not ldr_laps.empty:
            p_match = primary_laps[primary_laps['LapNumber'] == last_lap['LapNumber']]
            l_match = ldr_laps[ldr_laps['LapNumber'] == last_lap['LapNumber']]
            if not p_match.empty and not l_match.empty and pd.notna(p_match['Time'].iloc[0]) and pd.notna(l_match['Time'].iloc[0]):
                p_gap = max(0.0, (p_match['Time'].iloc[0] - l_match['Time'].iloc[0]).total_seconds())

        t_driver = RDriverState(driver_id=primary, position=p_pos, current_gap_to_leader_s=p_gap, base_pace_s=p_avg_pace, tyre_state=TyreState(str(compound), int(tyre_life), 50.0, 0.05), fuel_state=FuelState(50.0))
        c_race_state.drivers = {t_driver.driver_id: t_driver, **{opp.driver_id: opp for opp in opponents}}

        what_if = st.session_state.get("what_if_strategy")

        with st.spinner("Running Monte Carlo + Decision Engine..."):
            mc_engine = MonteCarloRaceEngine(iterations=250, seed=42)
            mc_outcomes = mc_engine.rank_strategies(t_driver, opponents, c_race_state, objective="MAX_WIN_PROBABILITY")

            if what_if:
                from strategy_model import StrategyPlan, StintPlan
                wi_strat = StrategyPlan(
                    strategy_name=f"Custom (Pit L{what_if['lap']} {what_if['compound']})",
                    stints=[
                        StintPlan(str(compound), current_lap, what_if['lap']),
                        StintPlan(what_if['compound'], what_if['lap'], total_laps)
                    ],
                    pit_laps=[what_if['lap']],
                    compounds=[str(compound), what_if['compound']],
                    stop_count=1
                )
                wi_res = mc_engine.simulate_strategy_vectorized(wi_strat, t_driver, opponents, c_race_state)
                # Assign this custom strategy as the chosen decision context if we want to visualize it
                mc_outcomes.insert(0, wi_res)

            decision = DecisionEngine.evaluate(c_race_state, None, mc_outcomes, "MAX_WIN_PROBABILITY")
            st.session_state['race_state'] = c_race_state
            st.session_state['mc_outcomes'] = mc_outcomes

        st.markdown(f"""
            <div class="hud-card" style="border: 1px solid rgba(255, 0, 85, 0.4); box-shadow: 0 0 20px rgba(255, 0, 85, 0.15); margin-top: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255, 0, 85, 0.25); padding-bottom: 8px; margin-bottom: 12px;">
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span style="width: 7px; height: 7px; background: #EF4444; border-radius: 50%; box-shadow: 0 0 8px #EF4444;"></span>
                        <span style="color: #EF4444; font-family: 'Inter'; font-size: 11px; font-weight: 900; letter-spacing: 1.5px;">STRATEGY DIRECTIVE</span>
                    </div>
                    <span class="hud-status-badge rec">RECOMMENDED</span>
                </div>
                <div style="font-size: 18px; font-weight: 900; color: #FFFFFF; font-family: 'Inter'; letter-spacing: 1px; margin-bottom: 4px;">
                    {decision.recommended_action}
                </div>
                <div style="display: flex; align-items: center; gap: 8px; font-size: 12px; color: #4A90E2; font-family: 'Share Tech Mono'; margin-bottom: 14px;">
                    <span>TYRE: <strong style="color: #FFFFFF;">{decision.recommended_compound}</strong></span>
                    <span style="color: #475569;">|</span>
                    <span>TARGET LAP: <strong style="color: #FFEA00;">LAP {decision.recommended_pit_lap}</strong></span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; background: rgba(0,0,0,0.3); padding: 8px; border-radius: 6px; border: 1px solid #142236;">
                    <div style="text-align: center;">
                        <span style="color: #8FB4D4; font-size: 9px; font-family: 'Inter'; display: block;">WIN PROB</span>
                        <span style="color: #00CC64; font-weight: 900; font-family: 'Share Tech Mono'; font-size: 13px;">{decision.win_probability_pct:.1f}%</span>
                    </div>
                    <div style="text-align: center; border-left: 1px solid #142236; border-right: 1px solid #142236;">
                        <span style="color: #8FB4D4; font-size: 9px; font-family: 'Inter'; display: block;">EXP POS</span>
                        <span style="color: #4A90E2; font-weight: 900; font-family: 'Share Tech Mono'; font-size: 13px;">P{decision.expected_finish}</span>
                    </div>
                    <div style="text-align: center;">
                        <span style="color: #8FB4D4; font-size: 9px; font-family: 'Inter'; display: block;">ENGINE</span>
                        <span style="color: #FFB800; font-weight: 700; font-family: 'Share Tech Mono'; font-size: 11px;">M-CARLO</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("##### WHAT-IF SCENARIO")
        with st.expander("Modify Strategy Parameters"):
            with st.form("what_if_form"):
                c1, c2 = st.columns(2)
                with c1:
                    target_compound = st.selectbox("Compound", ["SOFT", "MEDIUM", "HARD"])
                with c2:
                    target_lap = st.number_input("Pit Lap", min_value=1, max_value=int(total_laps), value=int(current_lap)+1)
                submitted = st.form_submit_button("RECALCULATE")
                if submitted:
                    st.session_state["what_if_strategy"] = {"compound": target_compound, "lap": target_lap}
                    st.rerun()

    except Exception as e:
        st.error(f"Strategy Engine Error: {e}")
