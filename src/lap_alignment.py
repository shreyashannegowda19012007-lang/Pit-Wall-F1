"""
Distance-Based Lap Alignment Engine for Formula One Telemetry Analysis.
Resamples and aligns two driver laps onto a common physical track distance coordinate grid.
Computes mathematically rigorous, integrated micro-sector time deltas (dt = dx / v).
"""

from typing import Dict, Tuple, Optional, Any
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
from telemetry_cleaning import clean_telemetry_df


def align_laps_by_distance(
    lap_a_raw_df: pd.DataFrame,
    lap_b_raw_df: pd.DataFrame,
    grid_step_m: float = 1.0,
    driver_a_code: str = "Driver A",
    driver_b_code: str = "Driver B"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Transforms Lap A and Lap B into a common distance coordinate grid.

    Returns:
        aligned_df: DataFrame indexed by Distance (m) with columns:
            Distance, Speed_A, Speed_B, Throttle_A, Throttle_B, Brake_A, Brake_B,
            nGear_A, nGear_B, Time_A, Time_B, DeltaTime
        alignment_metadata: Dict with reconciliation metrics and confidence.
    """
    cleaned_a, meta_a = clean_telemetry_df(lap_a_raw_df)
    cleaned_b, meta_b = clean_telemetry_df(lap_b_raw_df)

    if cleaned_a.empty or cleaned_b.empty:
        return pd.DataFrame(), {
            "status": "FAILED",
            "error": "One or both input telemetry DataFrames are empty."
        }

    # Extract max distance overlap
    max_dist_a = cleaned_a['Distance'].max()
    max_dist_b = cleaned_b['Distance'].max()
    max_dist = min(max_dist_a, max_dist_b)

    if max_dist <= 10.0:
        return pd.DataFrame(), {
            "status": "FAILED",
            "error": f"Insufficient overlap distance ({max_dist:.1f}m)."
        }

    # Define uniform distance coordinate grid
    x_grid = np.arange(0.0, max_dist + grid_step_m, grid_step_m)

    def resample_channel(df: pd.DataFrame, col: str, fill_val: float = 0.0) -> np.ndarray:
        if col not in df.columns:
            return np.full_like(x_grid, fill_val)
        x_orig = df['Distance'].values
        y_orig = df[col].values

        # Linear 1D Interpolation
        f = interp1d(x_orig, y_orig, kind='linear', bounds_error=False, fill_value=(y_orig[0], y_orig[-1]))
        return f(x_grid)

    # Resample primary channels onto uniform grid
    speed_a = np.clip(resample_channel(cleaned_a, 'Speed', 100.0), 1.0, 390.0)
    speed_b = np.clip(resample_channel(cleaned_b, 'Speed', 100.0), 1.0, 390.0)

    throttle_a = np.clip(resample_channel(cleaned_a, 'Throttle', 0.0), 0.0, 100.0)
    throttle_b = np.clip(resample_channel(cleaned_b, 'Throttle', 0.0), 0.0, 100.0)

    brake_a = np.clip(resample_channel(cleaned_a, 'Brake', 0.0), 0.0, 100.0)
    brake_b = np.clip(resample_channel(cleaned_b, 'Brake', 0.0), 0.0, 100.0)

    gear_a = np.round(resample_channel(cleaned_a, 'nGear', 1.0)).astype(int)
    gear_b = np.round(resample_channel(cleaned_b, 'nGear', 1.0)).astype(int)

    # Optional channels
    rpm_a = resample_channel(cleaned_a, 'RPM', np.nan) if 'RPM' in cleaned_a.columns else np.full_like(x_grid, np.nan)
    rpm_b = resample_channel(cleaned_b, 'RPM', np.nan) if 'RPM' in cleaned_b.columns else np.full_like(x_grid, np.nan)

    drs_a = resample_channel(cleaned_a, 'DRS', np.nan) if 'DRS' in cleaned_a.columns else np.full_like(x_grid, np.nan)
    drs_b = resample_channel(cleaned_b, 'DRS', np.nan) if 'DRS' in cleaned_b.columns else np.full_like(x_grid, np.nan)

    # Scientific Time Integration: dt = dx / v (v in m/s)
    # v_ms = speed_kmh / 3.6
    v_a_ms = np.maximum(speed_a / 3.6, 0.5)  # Floor at 0.5 m/s to avoid div by zero
    v_b_ms = np.maximum(speed_b / 3.6, 0.5)

    # Midpoint velocity trapezoidal integration step
    dx = grid_step_m
    dt_a = np.zeros_like(x_grid)
    dt_b = np.zeros_like(x_grid)

    dt_a[1:] = dx / (0.5 * (v_a_ms[:-1] + v_a_ms[1:]))
    dt_b[1:] = dx / (0.5 * (v_b_ms[:-1] + v_b_ms[1:]))

    time_a = np.cumsum(dt_a)
    time_b = np.cumsum(dt_b)

    # Cumulative time delta: DeltaTime = time_a - time_b
    # Positive DeltaTime = Driver A is behind (slower/lost time)
    # Negative DeltaTime = Driver A is ahead (faster/gained time)
    delta_time = time_a - time_b

    aligned_df = pd.DataFrame({
        'Distance': x_grid,
        'Speed_A': speed_a,
        'Speed_B': speed_b,
        'Throttle_A': throttle_a,
        'Throttle_B': throttle_b,
        'Brake_A': brake_a,
        'Brake_B': brake_b,
        'nGear_A': gear_a,
        'nGear_B': gear_b,
        'RPM_A': rpm_a,
        'RPM_B': rpm_b,
        'DRS_A': drs_a,
        'DRS_B': drs_b,
        'Time_A': time_a,
        'Time_B': time_b,
        'DeltaTime': delta_time
    })

    total_time_a = time_a[-1]
    total_time_b = time_b[-1]
    total_delta = delta_time[-1]

    brake_a_present = bool('Brake' in cleaned_a.columns and cleaned_a['Brake'].notna().any())
    brake_b_present = bool('Brake' in cleaned_b.columns and cleaned_b['Brake'].notna().any())
    throttle_a_present = bool('Throttle' in cleaned_a.columns and cleaned_a['Throttle'].notna().any())
    throttle_b_present = bool('Throttle' in cleaned_b.columns and cleaned_b['Throttle'].notna().any())

    metadata = {
        "status": "SUCCESS",
        "grid_step_m": grid_step_m,
        "total_distance_m": max_dist,
        "num_grid_points": len(x_grid),
        "total_time_a_s": round(total_time_a, 3),
        "total_time_b_s": round(total_time_b, 3),
        "integrated_time_delta_s": round(total_delta, 3),
        "driver_a_code": driver_a_code,
        "driver_b_code": driver_b_code,
        "channel_availability_a": {
            "brake": brake_a_present,
            "throttle": throttle_a_present,
            "rpm": bool('RPM' in cleaned_a.columns),
            "drs": bool('DRS' in cleaned_a.columns)
        },
        "channel_availability_b": {
            "brake": brake_b_present,
            "throttle": throttle_b_present,
            "rpm": bool('RPM' in cleaned_b.columns),
            "drs": bool('DRS' in cleaned_b.columns)
        }
    }

    aligned_df.attrs = metadata

    return aligned_df, metadata
