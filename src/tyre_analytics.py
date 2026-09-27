import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any, List

class TyreAnalyticsEngine:
    @staticmethod
    def analyze_stint_degradation(session, driver_id: str) -> Dict[str, Any]:
        """
        Extracts lap times from FastF1 for a given driver, isolates the longest stint,
        applies fuel correction (-0.065s per lap), and computes linear regression
        for tyre degradation.
        """
        laps = session.laps.pick_driver(driver_id)
        if laps.empty:
            return {"success": False, "error": "No laps found for driver"}

        # Filter out in/out laps and safety car laps
        valid_laps = laps.pick_quicklaps().reset_index(drop=True)
        if valid_laps.empty:
            return {"success": False, "error": "No valid quicklaps found"}

        # Identify longest stint
        stint_counts = valid_laps['Stint'].value_counts()
        longest_stint = stint_counts.idxmax()
        stint_laps = valid_laps[valid_laps['Stint'] == longest_stint].copy()

        # Extract tyre age and lap times in seconds
        stint_laps['LapTime_s'] = stint_laps['LapTime'].dt.total_seconds()
        stint_laps = stint_laps.dropna(subset=['LapTime_s', 'TyreLife'])

        if len(stint_laps) < 3:
            return {"success": False, "error": "Not enough laps in stint to calculate degradation"}

        compound = stint_laps['Compound'].iloc[0] if not stint_laps['Compound'].empty else "UNKNOWN"

        # Apply fuel correction: cars get faster by ~0.065s per lap as they burn fuel.
        # To isolate tyre degradation, we add 0.065s * lap_number to the lap time.
        FUEL_EFFECT_S_PER_LAP = 0.065
        stint_laps['FuelCorrected_LapTime_s'] = stint_laps['LapTime_s'] + (stint_laps['LapNumber'] * FUEL_EFFECT_S_PER_LAP)

        # Compute Ordinary Least Squares (OLS) Regression
        x = stint_laps['TyreLife'].astype(float).values
        y = stint_laps['FuelCorrected_LapTime_s'].astype(float).values

        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        # Prepare scatter plot points for the UI
        data_points = []
        for _, row in stint_laps.iterrows():
            age = float(row['TyreLife'])
            data_points.append({
                "lap_number": int(row['LapNumber']),
                "tyre_age": age,
                "raw_lap_time_s": round(row['LapTime_s'], 3),
                "fuel_corrected_lap_time_s": round(row['FuelCorrected_LapTime_s'], 3),
                "trend_lap_time_s": round(intercept + slope * age, 3)
            })

        return {
            "success": True,
            "driver_id": driver_id,
            "stint_number": int(longest_stint),
            "compound": compound,
            "total_laps": len(stint_laps),
            "base_pace_s": round(intercept, 3),
            "degradation_slope_s_per_lap": round(slope, 3),
            "r_squared": round(r_value ** 2, 3),
            "data_points": data_points
        }
