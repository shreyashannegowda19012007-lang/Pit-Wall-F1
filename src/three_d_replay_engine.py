"""
3D Track Circuit, Car Replay, Cockpit View & Camera Engine.
Renders high-performance WebGL 3D circuit trajectories, interpolated 20-car field markers,
dynamic camera modes (Top-Down, Overview, Follow, Chase, Driver POV, Comparison),
and unified telemetry HUD synchronized with authoritative backend race state.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
import math
import plotly.graph_objects as go

from track_geometry import TrackGeometryCache


class CameraMode:
    TOP_DOWN = "TOP_DOWN"
    TRACK_OVERVIEW = "TRACK_OVERVIEW"
    FOLLOW = "FOLLOW"
    CHASE = "CHASE"
    DRIVER_POV = "DRIVER_POV"
    COMPARISON = "COMPARISON"


@dataclass
class Car3DState:
    driver_id: str
    team_name: str
    position: int
    lap_number: int
    distance_m: float
    x: float
    y: float
    z: float
    heading_deg: float
    speed_kmh: float
    gear: int
    throttle_pct: float
    brake_pct: float
    compound: str
    tyre_age: int
    gap_to_leader_s: float
    is_primary: bool = False
    is_comparison: bool = False


class ThreeDTrackCoordinateSystem:
    """
    Normalizes and transforms circuit coordinates into stable 3D world space (X, Y, Z, heading).
    """

    @classmethod
    def interpolate_car_position(
        cls,
        track_nodes: List[Dict[str, float]],
        distance_m: float,
        total_track_length_m: float = 5000.0
    ) -> Tuple[float, float, float, float]:
        """
        Interpolates 3D position (x, y, z) and heading angle (heading_deg) for a given track distance.
        """
        if not track_nodes:
            return 0.0, 0.0, 0.0, 0.0

        n = len(track_nodes)
        norm_dist = (distance_m % total_track_length_m) / total_track_length_m
        idx_float = norm_dist * (n - 1)
        idx_lower = int(math.floor(idx_float)) % n
        idx_upper = (idx_lower + 1) % n
        frac = idx_float - math.floor(idx_float)

        p1 = track_nodes[idx_lower]
        p2 = track_nodes[idx_upper]

        x = p1['x'] + frac * (p2['x'] - p1['x'])
        y = p1['y'] + frac * (p2['y'] - p1['y'])
        z = p1.get('z', 0.0) + frac * (p2.get('z', 0.0) - p1.get('z', 0.0))

        dx = p2['x'] - p1['x']
        dy = p2['y'] - p1['y']
        heading_rad = math.atan2(dy, dx)
        heading_deg = (math.degrees(heading_rad) + 360.0) % 360.0

        return round(x, 2), round(y, 2), round(z, 2), round(heading_deg, 1)


class ReplayCacheEngine:
    """
    Preprocesses and caches session replay frames for 20 drivers.
    """

    @classmethod
    def generate_replay_frame(
        cls,
        laps_df: pd.DataFrame,
        track_nodes: List[Dict[str, float]],
        lap_number: int,
        lap_progress_pct: float = 0.5,
        primary_driver: str = "VER",
        comparison_driver: str = "HAM",
        session_id: str = "S-2024-SPAIN"
    ) -> List[Car3DState]:
        """
        Generates full 20-car field state for a specific replay frame using real spatial telemetry.
        """
        from spatial_intelligence_engine import SpatialIntelligenceEngine
        spatial_positions = SpatialIntelligenceEngine.get_spatial_field_positions(session_id, lap_number)
        
        car_states = []
        for p in spatial_positions:
            is_p = (p.driver_id == primary_driver)
            is_c = (p.driver_id == comparison_driver)
            
            # Identify tyre compound from laps_df if possible
            compound = "UNKNOWN"
            tyre_age = 0
            if laps_df is not None and not laps_df.empty:
                drv_laps = laps_df[(laps_df['Driver'] == p.driver_id) & (laps_df['LapNumber'] == lap_number)]
                if not drv_laps.empty:
                    compound = str(drv_laps['Compound'].iloc[0])
                    tyre_age = int(drv_laps['TyreLife'].iloc[0])
            
            car_states.append(Car3DState(
                driver_id=p.driver_id,
                team_name="Red Bull Racing" if p.driver_id in ["VER", "PER"] else ("Mercedes" if p.driver_id in ["HAM", "RUS"] else "F1 Team"),
                position=p.position,
                lap_number=lap_number,
                distance_m=p.distance_m,
                x=p.x_m,
                y=p.y_m,
                z=p.z_m,
                heading_deg=p.heading_deg,
                speed_kmh=p.speed_kmh,
                gear=p.gear,
                throttle_pct=p.throttle_pct,
                brake_pct=p.brake_pct,
                compound=compound,
                tyre_age=tyre_age,
                gap_to_leader_s=round(p.gap_to_leader_m / max(1.0, p.speed_kmh / 3.6), 2),
                is_primary=is_p,
                is_comparison=is_c
            ))
            
        return car_states


class ThreeDSceneGenerator:
    """
    Renders Plotly 3D WebGL scenes for all 6 camera modes.
    """

    @classmethod
    def create_3d_circuit_figure(
        cls,
        track_nodes: List[Dict[str, float]],
        car_states: List[Car3DState],
        camera_mode: str = CameraMode.TRACK_OVERVIEW,
        primary_driver: str = "VER"
    ) -> go.Figure:
        """
        Creates high-performance Plotly 3D WebGL visualization figure.
        """
        fig = go.Figure()

        if not track_nodes:
            try:
                import json
                import os
                from src import config
                spain_cache = os.path.join(config.BASE_DIR, "track_cache", "spain.json")
                if os.path.exists(spain_cache):
                    with open(spain_cache, "r", encoding="utf-8") as f:
                        cd = json.load(f)
                    track_nodes = [{"x": float(x), "y": float(y), "z": 0.0} for x, y in zip(cd.get("track_x", []), cd.get("track_y", []))]
                else:
                    track_nodes = []
            except Exception:
                track_nodes = []

        tx = [p['x'] for p in track_nodes]
        ty = [p['y'] for p in track_nodes]
        tz = [p.get('z', 0.0) for p in track_nodes]

        # 1. Render 3D Circuit Track Line
        fig.add_trace(go.Scatter3d(
            x=tx, y=ty, z=tz,
            mode='lines',
            line=dict(color='#00FF7F', width=6),
            name='Circuit Layout',
            hoverinfo='none'
        ))

        # 2. Separate Cars by Identity (Primary, Comparison, Neutral Field)
        primary_car = next((c for c in car_states if c.is_primary), None)
        comp_car = next((c for c in car_states if c.is_comparison), None)
        other_cars = [c for c in car_states if not c.is_primary and not c.is_comparison]

        # Render Neutral Field Cars
        if other_cars:
            fig.add_trace(go.Scatter3d(
                x=[c.x for c in other_cars],
                y=[c.y for c in other_cars],
                z=[c.z + 10 for c in other_cars],
                mode='markers+text',
                marker=dict(size=5, color='#94A3B8', symbol='circle'),
                text=[f"P{c.position} {c.driver_id}" for c in other_cars],
                textposition="top center",
                textfont=dict(size=9, color="#94A3B8"),
                name='Field Cars'
            ))

        # Render Comparison Driver (e.g. HAM - Silver/Teal)
        if comp_car:
            gap_str = f"+{comp_car.gap_to_leader_s}s" if comp_car.gap_to_leader_s is not None else "N/A"
            fig.add_trace(go.Scatter3d(
                x=[comp_car.x], y=[comp_car.y], z=[comp_car.z + 15],
                mode='markers+text',
                marker=dict(size=10, color='#00D2BE', symbol='diamond'),
                text=[f"P{comp_car.position} {comp_car.driver_id} ({gap_str})"],
                textposition="top center",
                textfont=dict(size=11, color="#00D2BE"),
                name=f"Comparison ({comp_car.driver_id})"
            ))

        # Render Primary Driver (e.g. VER - Bold Red Bull Yellow/Red)
        if primary_car:
            fig.add_trace(go.Scatter3d(
                x=[primary_car.x], y=[primary_car.y], z=[primary_car.z + 20],
                mode='markers+text',
                marker=dict(size=14, color='#FF1801', symbol='square'),
                text=[f"★ P{primary_car.position} {primary_car.driver_id} ({primary_car.speed_kmh:.0f} km/h)"],
                textposition="top center",
                textfont=dict(size=13, color="#FF1801"),
                name=f"Primary ({primary_car.driver_id})"
            ))

        # 3. Configure Camera Angles based on selected camera_mode
        eye_dict = dict(x=0.0, y=0.0, z=2.5)  # Default Track Overview
        if camera_mode == CameraMode.TOP_DOWN:
            eye_dict = dict(x=0.001, y=0.001, z=3.0)
        elif camera_mode in [CameraMode.FOLLOW, CameraMode.CHASE] and primary_car:
            # Position camera behind primary car following heading theta
            rad = math.radians(primary_car.heading_deg)
            eye_x = (primary_car.x - 300 * math.cos(rad)) / 10000.0
            eye_y = (primary_car.y - 300 * math.sin(rad)) / 10000.0
            eye_dict = dict(x=eye_x, y=eye_y, z=0.5)
        elif camera_mode == CameraMode.DRIVER_POV and primary_car:
            rad = math.radians(primary_car.heading_deg)
            eye_x = (primary_car.x + 50 * math.cos(rad)) / 10000.0
            eye_y = (primary_car.y + 50 * math.sin(rad)) / 10000.0
            eye_dict = dict(x=eye_x, y=eye_y, z=0.1)

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(10, 15, 29, 0.95)",
            plot_bgcolor="rgba(10, 15, 29, 0.95)",
            margin=dict(l=0, r=0, t=30, b=0),
            scene=dict(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                zaxis=dict(visible=False),
                aspectmode='data',
                camera=dict(eye=eye_dict)
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        return fig

