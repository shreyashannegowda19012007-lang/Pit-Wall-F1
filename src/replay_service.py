import math
import numpy as np
import pandas as pd

class ReplayService:
    @staticmethod
    def extract_track_map(session, frequency_hz=1):
        """
        Extracts X, Y coordinates for all drivers and downsamples to the given frequency.
        Also returns track boundaries or the reference path if possible.
        """
        # Downsample interval
        interval_ms = int(1000 / frequency_hz)

        pos_data = session.pos_data
        if not pos_data or len(pos_data) == 0:
            return {"success": False, "error": "No positional data available for session."}

        drivers_data = {}
        min_time = None
        max_time = None

        for driver_num, p_data in pos_data.items():
            if p_data.empty:
                continue

            p_data = p_data.copy()
            # FastF1 Time is a timedelta. Get milliseconds
            p_data['Time_ms'] = p_data['Time'].dt.total_seconds() * 1000

            p_data['Group'] = (p_data['Time_ms'] // interval_ms) * interval_ms
            downsampled = p_data.groupby('Group').first().reset_index()

            if min_time is None or downsampled['Group'].min() < min_time:
                min_time = downsampled['Group'].min()
            if max_time is None or downsampled['Group'].max() > max_time:
                max_time = downsampled['Group'].max()

            drivers_data[str(driver_num)] = {
                "t": downsampled['Group'].tolist(),
                "x": downsampled['X'].tolist(),
                "y": downsampled['Y'].tolist(),
                "z": downsampled['Z'].tolist()
            }

        return {
            "success": True,
            "min_time_ms": min_time,
            "max_time_ms": max_time,
            "interval_ms": interval_ms,
            "drivers": drivers_data
        }
