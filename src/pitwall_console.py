"""
F1 Pit-Wall Engineer Console & Workspace Orchestrator.
Integrates top session header bar, command palette (Ctrl+K), layout preset switcher,
driver data synchronization, and panel rendering into one high-density engineering console.
"""

from typing import Dict, List, Optional, Any
import streamlit as st
import pandas as pd

from panel_registry import PanelRegistry, LayoutPreset
from realtime_race_state import SCHEMA_VERSION


class PitWallConsoleOrchestrator:
    """
    Main Pit-Wall Engineer Console Workspace Manager.
    """

    @classmethod
    def render_top_session_bar(
        cls,
        year: int = 2024,
        gp_name: str = "Spanish Grand Prix",
        session_type: str = "Race",
        mode: str = "REPLAY",
        current_lap: int = 15,
        total_laps: int = 57,
        freshness_ms: float = 45.0
    ):
        """
        Renders persistent top session bar with high information density.
        """
        st.markdown(f"""
            <div style="background-color: #0A0F1D; border: 1px solid #1E293B; border-radius: 6px; padding: 10px 20px; margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: #FF1801; font-family: 'Inter', sans-serif; font-weight: bold; font-size: 16px; letter-spacing: 2px;">
                            🏁 {year} {gp_name.upper()}
                        </span>
                        <span style="color: #64748B; font-family: 'Share Tech Mono', monospace; font-size: 12px; margin-left: 15px;">
                            SESSION: {session_type.upper()} | SCHEMA: {SCHEMA_VERSION}
                        </span>
                    </div>
                    <div>
                        <span style="background-color: {'#00FF7F22' if mode == 'LIVE' else '#00D2BE22'}; color: {'#00FF7F' if mode == 'LIVE' else '#00D2BE'}; border: 1px solid {'#00FF7F' if mode == 'LIVE' else '#00D2BE'}; padding: 4px 10px; border-radius: 4px; font-family: 'Share Tech Mono', monospace; font-size: 11px; margin-right: 10px;">
                            ● {mode} MODE (CONNECTED)
                        </span>
                        <span style="color: #94A3B8; font-family: 'Share Tech Mono', monospace; font-size: 11px;">
                            LAP: {current_lap}/{total_laps} | FRESHNESS: {freshness_ms:.0f}ms
                        </span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    @classmethod
    def render_command_palette(cls):
        """
        Renders interactive quick-action Command Palette (Ctrl+K).
        """
        with st.expander("⚡ COMMAND PALETTE & LAYOUT PRESETS (CTRL + K)", expanded=False):
            c1, c2, c3 = st.columns(3)
            with c1:
                preset = st.selectbox(
                    "LOAD LAYOUT PRESET",
                    [LayoutPreset.DEFAULT, LayoutPreset.DRIVER_ANALYSIS, LayoutPreset.STRATEGY_SIMULATION, LayoutPreset.THREE_D_RACE_VIEW, LayoutPreset.TELEMETRY_ENGINEERING],
                    key="sb_layout_preset"
                )
                if st.button("APPLY LAYOUT PRESET", use_container_width=True):
                    st.session_state['active_layout_preset'] = preset
                    st.success(f"Applied layout preset: {preset}")

            with c2:
                jump_lap = st.number_input("JUMP TO LAP", min_value=1, max_value=57, value=15, key="ni_cmd_jump_lap")
                if st.button("EXECUTE LAP JUMP", use_container_width=True):
                    st.session_state['replay_current_lap'] = jump_lap
                    st.success(f"Jumped to lap {jump_lap}")

            with c3:
                st.caption("⌨️ CONSOLE HOTKEYS")
                st.caption("• [Space]: Play / Pause")
                st.caption("• [1-6]: Panel Focus")
                st.caption("• [F]: Focus Primary Driver")
                st.caption("• [C]: Focus Comparison Driver")
