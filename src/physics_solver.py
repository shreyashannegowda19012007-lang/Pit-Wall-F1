import streamlit as st

import plotly.graph_objects as go

from plotly.subplots import make_subplots

import pandas as pd

import numpy as np

import fastf1



def render_micro_telemetry_stack(raw_session, comp_drivers):

    r"""

    Renders a synchronized 5-panel telemetry stack against Track Distance.

    Includes Velocity, Throttle, Brake, Gear, and Delta-Time (\Delta t).

    """

    if len(comp_drivers) < 1:

        st.info("Select at least one driver to view telemetry.")

        return



    try:

        def get_driver_laps(session_laps, drv_code):

            if hasattr(session_laps, 'pick_drivers'):

                return session_laps.pick_drivers(drv_code)

            return session_laps[session_laps['Driver'] == drv_code]



        # Define baseline lap for delta calculations

        ref_drv = comp_drivers[0]

        ref_laps = get_driver_laps(raw_session.laps, ref_drv)

        if ref_laps.empty:

            st.warning(f"No lap telemetry found for reference driver {ref_drv}.")

            return



        ref_lap = ref_laps.pick_fastest()



        # UI Colors for contrast

        line_colors = ['#4A90E2', '#FF3333', '#EAE210', '#A020F0', '#00FF7F', '#FFFFFF']



        fig = make_subplots(

            rows=5, cols=1,

            shared_xaxes=True,

            vertical_spacing=0.03,

            subplot_titles=("SPEED (km/h)", "THROTTLE (%)", "BRAKE", "GEAR", f"TIME DELTA (Δt) vs {ref_drv}")

        )



        for i, drv in enumerate(comp_drivers):

            color = line_colors[i % len(line_colors)]

            drv_laps = get_driver_laps(raw_session.laps, drv)

            if drv_laps.empty:

                continue

            drv_lap = drv_laps.pick_fastest()



            # Extract high-frequency telemetry and map to physical distance

            tel = drv_lap.get_telemetry().add_distance()

            if tel.empty:

                continue



            # 1. Speed Vector

            fig.add_trace(go.Scatter(x=tel['Distance'], y=tel['Speed'], name=drv, line=dict(color=color, width=2)), row=1, col=1)



            # 2. Throttle Application

            fig.add_trace(go.Scatter(x=tel['Distance'], y=tel['Throttle'], showlegend=False, line=dict(color=color, width=2)), row=2, col=1)



            # 3. Brake Application (Binary/Pressure)

            fig.add_trace(go.Scatter(x=tel['Distance'], y=tel['Brake'], showlegend=False, line=dict(color=color, width=2)), row=3, col=1)



            # 4. Transmission/Gear State (Step function)

            fig.add_trace(go.Scatter(x=tel['Distance'], y=tel['nGear'], showlegend=False, line=dict(color=color, width=2, shape='hv')), row=4, col=1)



            # 5. Delta Time (\Delta t) vs Reference

            if drv != ref_drv:

                try:

                    delta_time, ref_tel, _ = fastf1.utils.delta_time(ref_lap, drv_lap)

                    fig.add_trace(go.Scatter(x=ref_tel['Distance'], y=delta_time, name=f"Δt {drv}", line=dict(color=color, width=2)), row=5, col=1)

                except Exception:

                    pass

            else:

                # Flatline for the baseline reference driver

                fig.add_trace(go.Scatter(x=tel['Distance'], y=tel['Distance']*0, showlegend=False, line=dict(color=color, width=2, dash='dot')), row=5, col=1)



        fig.update_layout(

            height=1000,

            template="plotly_dark",

            paper_bgcolor='rgba(0,0,0,0)',

            plot_bgcolor='rgba(0,0,0,0)',

            hovermode="x unified",

            margin=dict(l=10, r=10, t=30, b=10)

        )



        # Hardcode limits for specific telemetry boundaries

        fig.update_yaxes(range=[0, 105], row=2, col=1)  # Throttle maxes at 100

        fig.update_yaxes(range=[0, 9], row=4, col=1)    # Max 8 gears



        st.plotly_chart(fig, use_container_width=True)



    except Exception as e:

        st.error(f"Telemetry Sync Failed: {str(e)}")



def render_pacing_scatter(laps):

    """

    Renders grid-wide lap pacing distribution, filtering out extreme outliers (in/out laps).

    """

    try:

        # Filter strictly for valid laps with recorded times

        valid_laps = laps.dropna(subset=['LapTime']).copy()

        if valid_laps.empty:

            st.warning("Insufficient pacing data to build scatter plot.")

            return



        valid_laps['LapTime_s'] = valid_laps['LapTime'].dt.total_seconds()



        # Outlier Rejection: Remove laps > 1.3x the fastest lap to hide pit stops

        fastest_lap_s = valid_laps['LapTime_s'].min()

        threshold = fastest_lap_s * 1.3

        filtered_laps = valid_laps[valid_laps['LapTime_s'] < threshold]



        compound_colors = {

            'SOFT': '#FF3333',

            'MEDIUM': '#EAE210',

            'HARD': '#FFFFFF',

            'INTERMEDIATE': '#39B54A',

            'WET': '#00AEEF',

            'UNKNOWN': '#64748B'

        }



        fig = go.Figure()



        drivers = filtered_laps['Driver'].unique()

        for i, drv in enumerate(drivers):

            drv_laps = filtered_laps[filtered_laps['Driver'] == drv]



            # Create color array based on compound used for each specific lap

            colors = [compound_colors.get(str(c).upper(), '#64748B') for c in drv_laps['Compound']]



            # Map drivers sequentially along the X-axis, LapTime on Y

            fig.add_trace(go.Scatter(

                x=[drv] * len(drv_laps),

                y=drv_laps['LapTime_s'],

                mode='markers',

                name=drv,

                marker=dict(color=colors, size=6, opacity=0.6, line=dict(width=0)),

                hovertemplate="Lap: %{text}<br>Time: %{y:.3f}s<extra></extra>",

                text=drv_laps['LapNumber']

            ))



            # Overlay a larger marker for median pace

            median_pace = drv_laps['LapTime_s'].median()

            fig.add_trace(go.Scatter(

                x=[drv],

                y=[median_pace],

                mode='markers',

                showlegend=False,

                marker=dict(color='#4A90E2', size=14, symbol='line-ew-open', line=dict(width=3))

            ))



        fig.update_layout(

            height=500,

            template="plotly_dark",

            paper_bgcolor='rgba(0,0,0,0)',

            plot_bgcolor='rgba(0,0,0,0)',

            yaxis_title="Lap Time (Seconds)",

            showlegend=False,

            margin=dict(t=10, b=10)

        )

        st.plotly_chart(fig, use_container_width=True)



    except Exception as e:

        st.error(f"Pacing Scatter Engine Error: {str(e)}")



def render_gap_to_leader(laps):

    """

    Computes and plots the continuous race gap to the overall race leader.

    """

    st.markdown("### ⏱️ RACE GAP TO LEADER EVOLUTION")

    try:

        # Extract laps with valid total session times

        valid_laps = laps.dropna(subset=['Time']).copy()

        if valid_laps.empty:

            st.warning("Insufficient gap delta data.")

            return



        valid_laps['SessionTime_s'] = valid_laps['Time'].dt.total_seconds()



        # Find the absolute minimum session time for each lap number (The Leader)

        leader_times = valid_laps.groupby('LapNumber')['SessionTime_s'].min().reset_index()

        leader_times.rename(columns={'SessionTime_s': 'LeaderTime_s'}, inplace=True)



        # Merge back to calculate individual gaps

        merged = pd.merge(valid_laps, leader_times, on='LapNumber')

        merged['GapToLeader'] = merged['SessionTime_s'] - merged['LeaderTime_s']



        fig = go.Figure()



        # Plot top 10 drivers to avoid cluttering the graph

        top_drivers = merged[merged['LapNumber'] == merged['LapNumber'].max()].sort_values('GapToLeader').head(10)['Driver'].tolist()



        for drv in top_drivers:

            drv_data = merged[merged['Driver'] == drv].sort_values('LapNumber')

            fig.add_trace(go.Scatter(

                x=drv_data['LapNumber'],

                y=drv_data['GapToLeader'],

                mode='lines',

                name=drv,

                line=dict(width=2)

            ))



        fig.update_layout(

            height=600,

            template="plotly_dark",

            paper_bgcolor='rgba(0,0,0,0)',

            plot_bgcolor='rgba(0,0,0,0)',

            xaxis_title="Race Lap",

            yaxis_title="Gap to Leader (Seconds)",

            yaxis=dict(autorange="reversed"), # Reverse Y axis so leader (0s) is at the top

            margin=dict(t=10, b=10)

        )

        st.plotly_chart(fig, use_container_width=True)



    except Exception as e:

        st.error(f"Gap Delta Engine Error: {str(e)}")



def render_custom_lap_deficit(raw_session, target_drv, target_lap_num, ref_drv, ref_lap_num):

    """

    Renders a dedicated time deficit (Delta t) plot between two specifically chosen laps.

    """

    try:

        def get_driver_laps(session_laps, drv_code):

            if hasattr(session_laps, 'pick_drivers'):

                return session_laps.pick_drivers(drv_code)

            return session_laps[session_laps['Driver'] == drv_code]



        # Extract the specific laps

        target_laps = get_driver_laps(raw_session.laps, target_drv)

        ref_laps = get_driver_laps(raw_session.laps, ref_drv)



        target_lap = target_laps[target_laps['LapNumber'] == target_lap_num].iloc[0] if not target_laps[target_laps['LapNumber'] == target_lap_num].empty else None

        ref_lap = ref_laps[ref_laps['LapNumber'] == ref_lap_num].iloc[0] if not ref_laps[ref_laps['LapNumber'] == ref_lap_num].empty else None



        if target_lap is None or ref_lap is None:

            st.warning("One or both selected laps are invalid or missing telemetry.")

            return



        # Calculate Delta Time

        delta_time, ref_tel, _ = fastf1.utils.delta_time(ref_lap, target_lap)



        fig = go.Figure()



        # Plot Delta Time with fill area for visual clarity

        fig.add_trace(go.Scatter(

            x=ref_tel['Distance'],

            y=delta_time,

            mode='lines',

            name=f"Δt ({target_drv} L{target_lap_num} vs {ref_drv} L{ref_lap_num})",

            line=dict(color='#4A90E2', width=2),

            fill='tozeroy',

            fillcolor='#333842'

        ))



        fig.update_layout(
            height=400,
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            title=f"MICRO-SECTOR TIME DEFICIT: {target_drv} (Lap {target_lap_num}) vs {ref_drv} (Lap {ref_lap_num})",
            xaxis_title="Track Distance (meters)",
            yaxis_title="Time Delta (Seconds) [Negative = Target is Faster]",
            hovermode="x unified",
            margin=dict(t=40, b=10, l=10, r=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Delta Calculation Failed: {str(e)}")

def render_telemetry_comparison(raw_session, laps, primary, comp, current_lap):
    import streamlit as st
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import textwrap

    st.markdown(textwrap.dedent(f"""
    <div class="hud-panel-header">
        <span class="hud-panel-title">⚡ HIGH-FREQUENCY TELEMETRY OVERLAY</span>
        <span class="hud-status-badge active">{primary} VS {comp}</span>
    </div>
    """).strip(), unsafe_allow_html=True)

    try:
        p_laps = laps[laps['Driver'] == primary] if not laps.empty and 'Driver' in laps.columns else pd.DataFrame()
        c_laps = laps[laps['Driver'] == comp] if not laps.empty and 'Driver' in laps.columns else pd.DataFrame()

        if p_laps.empty or c_laps.empty:
            st.info("Insufficient laps for telemetry comparison.")
            return

        p_fastest = p_laps.loc[p_laps['LapTime'].idxmin()] if not p_laps['LapTime'].isna().all() else p_laps.iloc[-1]
        c_fastest = c_laps.loc[c_laps['LapTime'].idxmin()] if not c_laps['LapTime'].isna().all() else c_laps.iloc[-1]

        p_tel = p_fastest.get_telemetry()
        c_tel = c_fastest.get_telemetry()

        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.42, 0.29, 0.29],
            subplot_titles=["SPEED (KM/H)", "THROTTLE (%)", "BRAKE (%)"]
        )
        fig.add_trace(go.Scatter(x=p_tel['Distance'], y=p_tel['Speed'], name=f"{primary} Speed", line=dict(color='#EF4444', width=1.8)), row=1, col=1)
        fig.add_trace(go.Scatter(x=c_tel['Distance'], y=c_tel['Speed'], name=f"{comp} Speed", line=dict(color='#4A90E2', width=1.8)), row=1, col=1)
        fig.add_trace(go.Scatter(x=p_tel['Distance'], y=p_tel['Throttle'], name=f"{primary} Throttle", line=dict(color='#EF4444', width=1.5)), row=2, col=1)
        fig.add_trace(go.Scatter(x=c_tel['Distance'], y=c_tel['Throttle'], name=f"{comp} Throttle", line=dict(color='#4A90E2', width=1.5)), row=2, col=1)
        fig.add_trace(go.Scatter(x=p_tel['Distance'], y=p_tel['Brake'], name=f"{primary} Brake", line=dict(color='#EF4444', width=1.5)), row=3, col=1)
        fig.add_trace(go.Scatter(x=c_tel['Distance'], y=c_tel['Brake'], name=f"{comp} Brake", line=dict(color='#4A90E2', width=1.5)), row=3, col=1)



        fig.update_layout(

            height=480,

            margin=dict(l=45, r=20, t=30, b=25),

            paper_bgcolor='rgba(0,0,0,0)',

            plot_bgcolor='rgba(0,0,0,0)',

            font=dict(color='#94A3B8', family='Share Tech Mono', size=10),

            legend=dict(

                orientation="h",

                yanchor="bottom",

                y=1.02,

                xanchor="right",

                x=1,

                font=dict(color="#E2E8F0", family='Inter', size=10)

            )

        )

        for i in range(1, 4):

            fig.update_xaxes(gridcolor='rgba(255,255,255,0.06)', zerolinecolor='rgba(255,255,255,0.1)', row=i, col=1)

            fig.update_yaxes(gridcolor='rgba(255,255,255,0.06)', zerolinecolor='rgba(255,255,255,0.1)', row=i, col=1)



        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})



    except Exception as e:

        st.info("ℹ️ High-frequency car sensor telemetry (speed, throttle, brake) is not available for this session. Timing, sector splits, and lap analysis remain fully operational.")
