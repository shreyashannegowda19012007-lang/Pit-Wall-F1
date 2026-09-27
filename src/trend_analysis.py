"""
Time-Series Trend Analysis & Cause Isolation Engine for F1 Telemetry.
Calculates stint degradation slopes, multi-lap corner input trends, and separates
tyre/car degradation from driver-specific corner input changes.
"""

from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np


class TimeSeriesTrendEngine:
    """
    Computes time-series trends over stints and isolates driver vs car/tyre degradation effects.
    """

    @classmethod
    def calculate_stint_pace_degradation(cls, laps_df: pd.DataFrame, driver_id: str, stint_num: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculates pace degradation rate (seconds per lap) over a clean stint via linear regression.
        """
        if laps_df.empty:
            return {"valid": False, "reason": "Laps dataset is empty."}

        driver_laps = laps_df[(laps_df['Driver'] == driver_id) & (laps_df['IsAccurate'] == True)].copy()
        if driver_laps.empty:
            return {"valid": False, "reason": f"No accurate laps for driver {driver_id}."}

        if stint_num is not None:
            stint_laps = driver_laps[driver_laps['Stint'] == stint_num]
            if len(stint_laps) == 0:
                stint_laps = driver_laps
        else:
            stint_laps = driver_laps

        if len(stint_laps) < 3:
            return {
                "valid": False,
                "reason": "Insufficient stint lap count for trend regression (minimum 3 clean laps required).",
                "lap_count": len(stint_laps)
            }

        lap_nums = stint_laps['LapNumber'].values  # type: ignore
        lap_times = stint_laps['LapTime'].dt.total_seconds().values  # type: ignore

        # Linear fit: LapTime = slope * LapNumber + intercept
        slope, intercept = np.polyfit(lap_nums, lap_times, 1)  # type: ignore

        mean_pace = float(np.mean(lap_times))
        std_pace = float(np.std(lap_times))

        return {
            "valid": True,
            "driver_id": driver_id,
            "stint_number": stint_num or int(stint_laps['Stint'].iloc[0]),  # type: ignore
            "lap_count": len(stint_laps),
            "start_lap": int(lap_nums[0]),
            "end_lap": int(lap_nums[-1]),
            "degradation_rate_s_per_lap": round(float(slope), 4),
            "mean_pace_s": round(mean_pace, 3),
            "std_pace_s": round(std_pace, 3),
            "compound": str(stint_laps['Compound'].iloc[0]) if 'Compound' in stint_laps.columns else "UNKNOWN"  # type: ignore
        }

    @classmethod
    def separate_driver_vs_car_effects(
        cls,
        laps_df: pd.DataFrame,
        target_driver: str,
        ref_driver: str,
        corner_analyses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Distinguishes driver input errors from tyre thermal degradation or traffic.
        """
        stint_deg = cls.calculate_stint_pace_degradation(laps_df, target_driver)

        if not stint_deg.get("valid"):
            return {
                "isolated_cause": "UNKNOWN",
                "explanation": "Cause cannot be isolated from available telemetry due to limited stint lap count."
            }

        deg_rate = stint_deg.get("degradation_rate_s_per_lap", 0.0)

        # Check corner time-loss pattern
        significant_corner_losses = [ca for ca in corner_analyses if ca.get("time_loss_seconds", 0.0) > 0.05]

        if not significant_corner_losses and deg_rate > 0.05:
            return {
                "isolated_cause": "TYRE_DEGRADATION",
                "explanation": f"The lap-time decline (+{deg_rate:.3f}s/lap) correlates with increasing tyre age and thermal degradation. Driver-specific corner entry lines remain consistent."
            }

        if significant_corner_losses and abs(deg_rate) < 0.03:
            top_corner = significant_corner_losses[0]
            c_name = top_corner.get("corner_name", "corner")
            return {
                "isolated_cause": "DRIVER_INPUT_DELTA",
                "explanation": f"Pace loss is primarily driver-specific in {c_name} (Braking delta: {top_corner.get('braking_point_delta_m', 0.0)}m, Apex min speed: {top_corner.get('minimum_speed_delta_kmh', 0.0)} km/h), while overall stint tyre degradation is stable (+{deg_rate:.3f}s/lap)."
            }

        if significant_corner_losses and deg_rate > 0.05:
            top_corner = significant_corner_losses[0]
            c_name = top_corner.get("corner_name", "corner")
            return {
                "isolated_cause": "COMBINED_DRIVER_AND_TYRE",
                "explanation": f"Performance loss reflects a combination of driver input line variance in {c_name} (+{top_corner.get('time_loss_seconds', 0.0):.3f}s) and compounding tyre thermal wear (+{deg_rate:.3f}s/lap)."
            }

        return {
            "isolated_cause": "UNISOLATED",
            "explanation": "Cause cannot be isolated from available telemetry."
        }
