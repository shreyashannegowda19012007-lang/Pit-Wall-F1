import plotly.graph_objects as go
import streamlit as st
import os
import json
import numpy as np
import pandas as pd
import fastf1
from typing import Dict, Any, Optional
from src import config

class TrackGeometryCache:
    """
    Extracts, smooths, normalizes, and caches circuit path coordinates.
    """
    @staticmethod
    def extract_track_from_session(year: int, location: str, session_type: str = "R") -> Dict[str, Any]:
        """
        Extracts GPS coordinate points from the fastest lap, applies smoothing,
        downsamples to ~300 points, and scales to a normalized 0-10000 range.
        """
        # Load session using FastF1 API
        session = fastf1.get_session(year, location, session_type)
        session.load(laps=True, telemetry=True)

        # Pick the fastest lap
        fastest_lap = session.laps.pick_fastest()
        if fastest_lap is None:
            raise ValueError(f"No fastest lap found for {location} ({year}).")
        pos = fastest_lap.get_pos_data()

        if pos.empty or 'X' not in pos.columns:
            raise ValueError(f"No GPS coordinates telemetry available for {location} ({year}).")

        x = pos['X'].dropna().values
        y = pos['Y'].dropna().values

        # Apply Gaussian smoothing (rolling window median/mean)
        x_smooth = pd.Series(x).rolling(window=7, center=True, min_periods=1).mean().values
        y_smooth = pd.Series(y).rolling(window=7, center=True, min_periods=1).mean().values

        # Downsample to optimize Plotly rendering speed while retaining visual accuracy
        step = max(1, len(x_smooth) // 300)
        x_down = x_smooth[::step]
        y_down = y_smooth[::step]

        # Normalize coordinates to constant 0-10000 bounding box (preserves aspect ratio)
        x_min, x_max = float(np.min(x_down)), float(np.max(x_down))
        y_min, y_max = float(np.min(y_down)), float(np.max(y_down))

        scale = 10000.0 / max(x_max - x_min, y_max - y_min) if max(x_max - x_min, y_max - y_min) > 0 else 1.0

        x_norm = ((x_down - x_min) * scale).tolist()
        y_norm = ((y_down - y_min) * scale).tolist()

        return {
            "track_x": x_norm,
            "track_y": y_norm,
            "data_points": len(x_norm),
            "year": year,
            "location": location
        }

    @staticmethod
    def get_or_extract_track(location: str, year: int = 2024) -> Dict[str, Any]:
        """
        Pulls GPS track geometry from disk cache or triggers direct FastF1 extraction.
        """
        cache_dir = config.TRACK_CACHE_DIR
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, f"{location.lower().replace(' ', '_')}.json")

        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass

        # If cache miss, extract and save to disk
        data = TrackGeometryCache.extract_track_from_session(year, location, "R")
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        return data

@st.cache_data(ttl=86400)
def load_track_geometry(location: str, year: int = 2024) -> Dict[str, Any]:
    """
    Streamlit cached wrapper for loading track geometry with fallback protection.
    """
    try:
        return TrackGeometryCache.get_or_extract_track(location, year)
    except Exception as e:
        return {
            "track_x": [],
            "track_y": [],
            "data_points": 0,
            "year": year,
            "location": location,
            "error": str(e)
        }

def ensure_track_geometry(raw_session=None, location: str = "Spain", year: int = 2024) -> Dict[str, Any]:
    """
    Unified track geometry loader ensuring compatibility with legacy and current callers.
    Accepts raw_session dict/object or direct location & year strings.
    """
    if isinstance(raw_session, str):
        # Position swap handling if called positional (location, year)
        location, year = raw_session, int(location) if isinstance(location, int) or (isinstance(location, str) and location.isdigit()) else 2024
    elif hasattr(raw_session, 'event') and raw_session.event is not None:
        location = raw_session.event.get('Location', location)
        year = int(raw_session.event.get('Year', year)) if hasattr(raw_session.event, 'get') else year

    return load_track_geometry(location, year)

def render_spatial_map(raw_session):
    """
    Extracts GPS coordinates from the fastest lap and renders a 1:1 scale track map.
    """
    st.markdown("### SPATIAL TRACK GEOMETRY")
    try:
        # Extract the fastest lap to define the circuit boundary
        map_lap = raw_session.laps.pick_fastest()
        pos = map_lap.get_pos_data()

        if pos.empty or 'X' not in pos.columns:
            st.warning("GPS Positional data is missing for this session.")
            return

        fig = go.Figure()

        # Circuit Path Trace
        fig.add_trace(go.Scatter(
            x=pos['X'],
            y=pos['Y'],
            mode='lines',
            line=dict(color='#4A90E2', width=4),
            hoverinfo='skip',
            name='Circuit Path'
        ))

        # Lock Aspect Ratio to physical reality (1:1)
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False,
            xaxis=dict(
                visible=False,
                constrain="domain"
            ),
            yaxis=dict(
                visible=False,
                scaleanchor="x",
                scaleratio=1
            ),
            height=600
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Geometry Engine Failure: {e}")
        st.info("Ensure telemetry is available for the selected session.")

def render_animated_track_trace(raw_session, target_drivers):
    """
    Renders an animated spatial track geometry with live driver positioning representing the fastest laps.
    """
    st.markdown("### ANIMATED SPATIAL KINEMATICS")

    if not target_drivers:
        st.info("Select at least one driver to initialize the geometry animation.")
        return

    try:
        map_lap = raw_session.laps.pick_fastest()
        circuit_pos = map_lap.get_pos_data()

        if circuit_pos.empty or 'X' not in circuit_pos.columns:
            st.warning("GPS Positional data is missing for this session.")
            return

        # Base Circuit trace
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=circuit_pos['X'],
            y=circuit_pos['Y'],
            mode='lines',
            line=dict(color='#1E293B', width=4),
            hoverinfo='skip',
            name='Circuit Path'
        ))

        num_frames = 150
        time_fractions = np.linspace(0, 1, num_frames)

        driver_trajectories = {}
        line_colors = ['#4A90E2', '#EF4444', '#EAE210', '#A020F0', '#00FF7F', '#FFFFFF']

        for i, drv in enumerate(target_drivers):
            # FastF1 pick_drivers support
            if hasattr(raw_session.laps, 'pick_drivers'):
                drv_laps = raw_session.laps.pick_drivers(drv)
            else:
                drv_laps = raw_session.laps[raw_session.laps['Driver'] == drv]

            if drv_laps.empty:
                continue
            drv_lap = drv_laps.pick_fastest()
            pos = drv_lap.get_pos_data()
            if pos.empty:
                continue

            # Normalize time for this driver's lap
            t = pos['Time'].dt.total_seconds().values
            if len(t) < 2 or (t[-1] - t[0]) == 0:
                continue
            t_norm = (t - t[0]) / (t[-1] - t[0])

            # Interpolate X and Y coordinates to common time fractions
            x_interp = np.interp(time_fractions, t_norm, pos['X'].values)
            y_interp = np.interp(time_fractions, t_norm, pos['Y'].values)

            driver_trajectories[drv] = {
                'x': x_interp,
                'y': y_interp,
                'color': line_colors[i % len(line_colors)]
            }

        # Build Frames
        frames = []
        for i in range(num_frames):
            frame_data = []
            for drv, traj in driver_trajectories.items():
                frame_data.append(go.Scatter(
                    x=[traj['x'][i]],
                    y=[traj['y'][i]],
                    mode='markers+text',
                    marker=dict(color=traj['color'], size=14, line=dict(color='white', width=1)),
                    text=[drv],
                    textposition="top center",
                    name=drv
                ))
            traces_indices = list(range(1, len(driver_trajectories) + 1))
            frames.append(go.Frame(data=frame_data, name=str(i), traces=traces_indices))

        # Add initial starting points (Frame 0) as static traces before play is pressed
        for drv, traj in driver_trajectories.items():
            fig.add_trace(go.Scatter(
                x=[traj['x'][0]],
                y=[traj['y'][0]],
                mode='markers+text',
                marker=dict(color=traj['color'], size=14, line=dict(color='white', width=1)),
                text=[drv],
                textposition="top center",
                name=drv
            ))

        # Add Animation Play Controls
        fig.update_layout(
            updatemenus=[dict(
                type="buttons",
                buttons=[dict(
                    label="INITIALIZE ANIMATION LOOP",
                    method="animate",
                    args=[None, {"frame": {"duration": 50, "redraw": False}, "fromcurrent": True, "transition": {"duration": 0}}]
                )],
                showactive=False,
                x=0.5,
                y=-0.1,
                xanchor="center",
                yanchor="top"
            )],
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=30, b=50),
            showlegend=False,
            xaxis=dict(visible=False, constrain="domain"),
            yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
            height=600
        )

        fig.frames = frames
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Animation Matrix Failure: {e}")

def render_2d_track_with_positions(raw_session, primary, comp, current_lap):
    import streamlit as st
    import plotly.graph_objects as go

    import textwrap
    st.markdown(textwrap.dedent("""
    <div class="hud-panel-header">
        <span class="hud-panel-title">🏁 TRACK SPATIAL OVERVIEW</span>
        <span class="hud-status-badge active">CIRCUIT GEOMETRY</span>
    </div>
    """).strip(), unsafe_allow_html=True)

    try:
        circuit_info = raw_session.get_circuit_info()
        corners = circuit_info.corners

        # We need generic track x/y. Let's get any fast lap.
        fastest_lap = raw_session.laps.pick_fastest()
        if pd.isna(fastest_lap['LapTime']):
            st.info("No fast lap track layout found.")
            return

        pos = fastest_lap.get_pos_data()
        x, y = pos['X'], pos['Y']

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode='lines',
            line=dict(color='#475569', width=4),
            name='Track Surface',
            hoverinfo='skip'
        ))

        # Primary
        p_laps = raw_session.laps[raw_session.laps['Driver'] == primary]
        if not p_laps.empty:
            p_lap = p_laps[p_laps['LapNumber'] == current_lap]
            if p_lap.empty: p_lap = p_laps.iloc[-1:]
            p_pos = p_lap.iloc[0].get_pos_data() if hasattr(p_lap.iloc[0], 'get_pos_data') else None
            if p_pos is not None and not p_pos.empty:
                fig.add_trace(go.Scatter(
                    x=[p_pos['X'].iloc[-1]], y=[p_pos['Y'].iloc[-1]],
                    mode='markers+text',
                    marker=dict(color='#EF4444', size=14, line=dict(color='#FFFFFF', width=1.5)),
                    text=[primary],
                    textposition="top center",
                    textfont=dict(color='#EF4444', family='Inter', size=11),
                    name=f"Primary: {primary}"
                ))

        # Comp
        c_laps = raw_session.laps[raw_session.laps['Driver'] == comp]
        if not c_laps.empty:
            c_lap = c_laps[c_laps['LapNumber'] == current_lap]
            if c_lap.empty: c_lap = c_laps.iloc[-1:]
            c_pos = c_lap.iloc[0].get_pos_data() if hasattr(c_lap.iloc[0], 'get_pos_data') else None
            if c_pos is not None and not c_pos.empty:
                fig.add_trace(go.Scatter(
                    x=[c_pos['X'].iloc[-1]], y=[c_pos['Y'].iloc[-1]],
                    mode='markers+text',
                    marker=dict(color='#4A90E2', size=14, line=dict(color='#FFFFFF', width=1.5)),
                    text=[comp],
                    textposition="bottom center",
                    textfont=dict(color='#4A90E2', family='Inter', size=11),
                    name=f"Rival: {comp}"
                ))

        fig.update_layout(
            height=440,
            margin=dict(l=25, r=25, t=25, b=25),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(visible=False),
            yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color="#E2E8F0", family='Inter', size=10)
            )
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    except Exception as e:
        st.error(f"TRACK DATA UNAVAILABLE: {e}")
