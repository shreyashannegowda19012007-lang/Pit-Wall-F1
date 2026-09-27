"""
Multi-Frequency Time-Series Synchronization Engine for Formula One Telemetry.
Maps multi-rate asynchronous channels (e.g., Speed 100Hz, Throttle 50Hz, Steering 20Hz, Gear 10Hz)
onto a uniform time coordinate grid using scientifically sound channel-specific interpolation rules.
"""

from typing import Dict, Tuple, Optional, Any, List
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d


# Explicit interpolation rules per channel classification
CHANNEL_INTERPOLATION_RULES: Dict[str, str] = {
    "Speed": "linear",
    "speed_kmh": "linear",
    "Throttle": "linear",
    "throttle_pct": "linear",
    "Brake": "linear",
    "brake_pct": "linear",
    "Steering": "linear",
    "steering_deg": "linear",
    "RPM": "linear",
    "Distance": "linear",
    "distance_m": "linear",
    "nGear": "nearest",
    "gear": "nearest",
    "DRS": "nearest",
    "Sector": "nearest",
    "Compound": "ffill"
}


def synchronize_telemetry_channels(
    df: pd.DataFrame,
    target_freq_hz: float = 100.0,
    time_col: str = 'Time'
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Synchronizes asynchronous, multi-frequency telemetry channels onto a uniform time grid.

    Args:
        df: Input cleaned telemetry DataFrame containing a time column.
        target_freq_hz: Target uniform sampling frequency in Hz (default 100.0 Hz = 0.01s grid step).
        time_col: Name of time column ('Time' or 'timestamp_s').

    Returns:
        (synchronized_df, synchronization_metadata)
    """
    if df is None or df.empty:
        return pd.DataFrame(), {
            "status": "EMPTY_INPUT",
            "target_freq_hz": target_freq_hz,
            "interpolation_methods": {}
        }

    cleaned = df.copy()

    # 1. Extract Time in Seconds
    if time_col not in cleaned.columns:
        if 'timestamp_s' in cleaned.columns:
            time_sec = cleaned['timestamp_s'].values
        elif 'Time' in cleaned.columns and hasattr(cleaned['Time'], 'dt'):
            time_sec = cleaned['Time'].dt.total_seconds().values
        else:
            # Fallback: estimate time from Distance and Speed
            if 'Distance' in cleaned.columns and 'Speed' in cleaned.columns:
                dist = cleaned['Distance'].values
                spd = np.maximum(cleaned['Speed'].values / 3.6, 0.5)
                time_sec = np.cumsum(np.gradient(dist) / spd)
            else:
                time_sec = np.arange(len(cleaned)) * (1.0 / target_freq_hz)
    else:
        if hasattr(cleaned[time_col], 'dt'):
            time_sec = cleaned[time_col].dt.total_seconds().values
        else:
            time_sec = cleaned[time_col].values

    if len(time_sec) < 2:
        return cleaned, {"status": "INSUFFICIENT_SAMPLES", "target_freq_hz": target_freq_hz, "interpolation_methods": {}}

    t_start = time_sec[0]
    t_end = time_sec[-1]
    dt_step = 1.0 / target_freq_hz

    # 2. Define Uniform Target Time Grid
    uniform_time_grid = np.arange(t_start, t_end + dt_step, dt_step)

    synced_data: Dict[str, np.ndarray] = {
        'timestamp_s': uniform_time_grid
    }

    interp_log: Dict[str, str] = {}

    # 3. Synchronize each channel according to its physical type
    for col in cleaned.columns:
        if col in ['Time', 'timestamp_s']:
            continue

        y_vals = cleaned[col].values

        # Skip columns that contain only NaNs
        if pd.isna(y_vals).all():
            synced_data[col] = np.full_like(uniform_time_grid, np.nan)
            interp_log[col] = "none_all_nan"
            continue

        rule = CHANNEL_INTERPOLATION_RULES.get(col, "linear" if pd.api.types.is_float_dtype(cleaned[col]) else "nearest")

        if rule == "linear":
            # Linear continuous interpolation
            f = interp1d(time_sec, y_vals, kind='linear', bounds_error=False, fill_value=(y_vals[0], y_vals[-1]))
            synced_data[col] = f(uniform_time_grid)
            interp_log[col] = "1d_linear_interpolation"

        elif rule == "nearest":
            # Nearest-neighbor step interpolation for integers/booleans
            f = interp1d(time_sec, y_vals, kind='nearest', bounds_error=False, fill_value=(y_vals[0], y_vals[-1]))
            resampled = f(uniform_time_grid)
            if pd.api.types.is_integer_dtype(cleaned[col]):
                synced_data[col] = np.round(resampled).astype(int)
            else:
                synced_data[col] = resampled
            interp_log[col] = "nearest_neighbor_step"

        elif rule == "ffill":
            # Forward-fill categorical strings
            ser = pd.Series(y_vals, index=time_sec)
            reindexed = ser.reindex(ser.index.union(uniform_time_grid)).ffill().bfill()
            synced_data[col] = reindexed.loc[uniform_time_grid].values
            interp_log[col] = "forward_fill_categorical"

    synced_df = pd.DataFrame(synced_data)

    metadata = {
        "status": "SUCCESS",
        "target_freq_hz": target_freq_hz,
        "dt_step_s": dt_step,
        "start_time_s": float(t_start),
        "end_time_s": float(t_end),
        "input_sample_count": len(cleaned),
        "synchronized_sample_count": len(synced_df),
        "interpolation_methods": interp_log
    }

    return synced_df, metadata
