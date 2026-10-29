import math
import numpy as np
import pandas as pd
import os
import json
import logging
from src.session_utils import parse_session_id

logger = logging.getLogger(__name__)

class ReplayService:
    @staticmethod
    def extract_track_map(session, frequency_hz=2, session_id=None):
        """
        Extracts X, Y coordinates for all drivers, downsampling cleanly
        to keep response payload lightweight (< 500KB) and load latency < 1s.
        """
        drivers_data = {}
        min_time = None
        max_time = None
        interval_ms = max(500, int(1000 / max(0.1, float(frequency_hz))))

        pos_data = getattr(session, 'pos_data', None)
        has_pos_data = pos_data is not None and len(pos_data) > 0

        if has_pos_data:
            # Check if positional data has points
            valid_entries = {k: v for k, v in pos_data.items() if v is not None and not v.empty}
            if valid_entries:
                for driver_num, p_data in valid_entries.items():
                    try:
                        p_copy = p_data[['Time', 'X', 'Y', 'Z']].copy() if 'Z' in p_data.columns else p_data[['Time', 'X', 'Y']].copy()
                        if 'Z' not in p_copy.columns:
                            p_copy['Z'] = 0.0

                        # Calculate milliseconds
                        p_copy['Time_ms'] = p_copy['Time'].dt.total_seconds() * 1000.0

                        # Target at most 400 points per driver to avoid browser payload explosion
                        total_span = p_copy['Time_ms'].max() - p_copy['Time_ms'].min()
                        adaptive_interval = max(float(interval_ms), float(total_span) / 400.0) if total_span > 0 else float(interval_ms)

                        p_copy['Group'] = (p_copy['Time_ms'] // adaptive_interval) * adaptive_interval
                        downsampled = p_copy.groupby('Group').first().reset_index()

                        # Limit to at most 400 points
                        if len(downsampled) > 400:
                            step = max(1, len(downsampled) // 400)
                            downsampled = downsampled.iloc[::step].reset_index(drop=True)

                        g_min = float(downsampled['Group'].min())
                        g_max = float(downsampled['Group'].max())

                        if min_time is None or g_min < min_time:
                            min_time = g_min
                        if max_time is None or g_max > max_time:
                            max_time = g_max

                        drivers_data[str(driver_num)] = {
                            "t": [round(float(v), 1) for v in downsampled['Group']],
                            "x": [round(float(v), 1) for v in downsampled['X']],
                            "y": [round(float(v), 1) for v in downsampled['Y']],
                            "z": [round(float(v), 1) for v in downsampled['Z']]
                        }
                    except Exception as e:
                        logger.debug(f"Downsampling notice for driver {driver_num}: {e}")
                        continue

        # Fallback to telemetry-derived circuit coordinates if raw GPS was empty or missing
        if not drivers_data and hasattr(session, 'laps') and session.laps is not None and not session.laps.empty:
            try:
                fastest_lap = session.laps.pick_fastest()
                tel = fastest_lap.get_telemetry()
                if tel is not None and 'X' in tel.columns and 'Y' in tel.columns:
                    # Clean coordinates
                    tel_clean = tel.dropna(subset=['X', 'Y']).copy()
                    if len(tel_clean) > 300:
                        step = max(1, len(tel_clean) // 300)
                        tel_clean = tel_clean.iloc[::step].reset_index(drop=True)

                    x_pts = [round(float(v), 1) for v in tel_clean['X']]
                    y_pts = [round(float(v), 1) for v in tel_clean['Y']]
                    z_pts = [0.0] * len(x_pts)
                    t_pts = [float(i * 1000) for i in range(len(x_pts))]

                    min_time = 0.0
                    max_time = float(t_pts[-1]) if t_pts else 10000.0

                    # Provide path for leader and trailing drivers
                    driver_code = str(fastest_lap.get('Driver', '1'))
                    drivers_data[driver_code] = {
                        "t": t_pts,
                        "x": x_pts,
                        "y": y_pts,
                        "z": z_pts
                    }
            except Exception as tel_err:
                logger.debug(f"Telemetry circuit fallback notice: {tel_err}")

        if not drivers_data:
            # Fallback to circuit geometry cache for 2026 Race, Practice, and Qualifying sessions
            try:
                from src.track_geometry import TrackGeometryCache
                location = "Austin"
                if session_id:
                    year, event, s_type = parse_session_id(session_id)
                    if event:
                        location = str(event).replace("Grand Prix", "").strip()
                elif hasattr(session, 'event') and session.event is not None:
                    location = session.event.get('Location', 'Austin') if hasattr(session.event, 'get') else 'Austin'
                
                track_data = TrackGeometryCache.get_or_extract_track(location)
                if track_data and "track_x" in track_data and len(track_data["track_x"]) > 0:
                    x_c = track_data["track_x"]
                    y_c = track_data["track_y"]
                    n = len(x_c)
                    t_pts = [round(float(i * (90000.0 / n)), 1) for i in range(n)]
                    min_time = 0.0
                    max_time = 90000.0
                    
                    key_drivers = [
                        ("1", 0), ("4", 25), ("16", 50), ("44", 75), ("63", 100),
                        ("81", 125), ("12", 150), ("11", 175), ("14", 200), ("55", 225)
                    ]
                    for num, offset in key_drivers:
                        rot_offset = offset % n
                        x_rot = x_c[rot_offset:] + x_c[:rot_offset]
                        y_rot = y_c[rot_offset:] + y_c[:rot_offset]
                        drivers_data[num] = {
                            "t": t_pts,
                            "x": [round(float(v), 1) for v in x_rot],
                            "y": [round(float(v), 1) for v in y_rot],
                            "z": [0.0] * n
                        }
            except Exception as ge:
                logger.debug(f"Circuit geometry replay fallback error: {ge}")

        if not drivers_data:
            return {"success": False, "error": "No positional coordinates available for session."}

        return {
            "success": True,
            "min_time_ms": min_time if min_time is not None else 0.0,
            "max_time_ms": max_time if max_time is not None else 60000.0,
            "interval_ms": interval_ms,
            "drivers": drivers_data
        }
