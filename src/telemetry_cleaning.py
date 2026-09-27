"""
Safe Preprocessing & Cleaning Layer for Formula One Telemetry Datasets.
Ensures data consistency without corrupting raw telemetry arrays.
All transformations produce a distinct, cleaned DataFrame with explicit diagnostic records.
"""

from typing import Dict, Tuple, Optional, Any
import pandas as pd
import numpy as np
from telemetry_validation import validate_telemetry_df, TelemetryValidationResult


def clean_telemetry_df(
    raw_df: pd.DataFrame,
    validation_result: Optional[TelemetryValidationResult] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans raw lap telemetry safely, returning (cleaned_df, cleaning_metadata).
    Never mutates raw_df.
    """
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(), {"status": "EMPTY_RAW_DATA", "rows_removed": 0, "rows_repaired": 0}

    # Create distinct copy
    cleaned = raw_df.copy()
    initial_rows = len(cleaned)
    rows_removed = 0
    rows_repaired = 0
    ops_log = []

    # 1. Standardize Primary Column Names if needed
    col_map = {}
    if 'distance_m' in cleaned.columns and 'Distance' not in cleaned.columns:
        col_map['distance_m'] = 'Distance'
    if 'speed_kmh' in cleaned.columns and 'Speed' not in cleaned.columns:
        col_map['speed_kmh'] = 'Speed'
    if 'throttle_pct' in cleaned.columns and 'Throttle' not in cleaned.columns:
        col_map['throttle_pct'] = 'Throttle'
    if 'brake_pct' in cleaned.columns and 'Brake' not in cleaned.columns:
        col_map['brake_pct'] = 'Brake'
    if 'timestamp_s' in cleaned.columns and 'Time' not in cleaned.columns:
        col_map['timestamp_s'] = 'Time'
    if 'gear' in cleaned.columns and 'nGear' not in cleaned.columns:
        col_map['gear'] = 'nGear'

    if col_map:
        cleaned.rename(columns=col_map, inplace=True)
        ops_log.append(f"Renamed columns to canonical format: {col_map}")

    # Ensure required Distance & Speed columns exist
    if 'Distance' not in cleaned.columns or 'Speed' not in cleaned.columns:
        return cleaned, {"status": "MISSING_MANDATORY_COLUMNS", "rows_removed": 0, "rows_repaired": 0}

    # 2. Convert Brake boolean to float % [0.0, 100.0]
    if 'Brake' in cleaned.columns:
        if cleaned['Brake'].dtype == bool or pd.api.types.is_bool_dtype(cleaned['Brake']):
            cleaned['Brake'] = cleaned['Brake'].astype(float) * 100.0
            rows_repaired += initial_rows
            ops_log.append("Converted boolean Brake column to float percentage [0.0, 100.0].")

    # 3. Drop rows with NaN in Distance or Speed
    valid_mask = cleaned['Distance'].notna() & cleaned['Speed'].notna()
    if not valid_mask.all():
        num_invalid = (~valid_mask).sum()
        cleaned = cleaned[valid_mask].copy()
        rows_removed += num_invalid
        ops_log.append(f"Removed {num_invalid} rows with NaN Distance or Speed.")

    # 4. Sort by Distance
    cleaned.sort_values(by='Distance', inplace=True)
    cleaned.reset_index(drop=True, inplace=True)

    # 5. Remove Exact Duplicate Distance points (keep first)
    dup_mask = cleaned.duplicated(subset=['Distance'], keep='first')
    if dup_mask.any():
        num_dups = dup_mask.sum()
        cleaned = cleaned[~dup_mask].copy()
        cleaned.reset_index(drop=True, inplace=True)
        rows_removed += num_dups
        ops_log.append(f"Removed {num_dups} duplicate distance sample rows.")

    # 6. Monotonic Distance Enforcement (Fix micro-steps backwards caused by sensor noise)
    dist_arr = cleaned['Distance'].values
    if len(dist_arr) > 1:
        mono_dist = np.maximum.accumulate(dist_arr)
        repaired_dist_count = (dist_arr != mono_dist).sum()
        if repaired_dist_count > 0:
            cleaned['Distance'] = mono_dist
            rows_repaired += repaired_dist_count
            ops_log.append(f"Enforced non-decreasing distance monotonicity on {repaired_dist_count} samples.")

    # 7. Clip Speed and Throttle to Physical Range
    if 'Speed' in cleaned.columns:
        sp_vals = cleaned['Speed'].values
        clipped_sp = np.clip(sp_vals, 0.0, 390.0)
        num_clipped_sp = (sp_vals != clipped_sp).sum()
        if num_clipped_sp > 0:
            cleaned['Speed'] = clipped_sp
            rows_repaired += num_clipped_sp
            ops_log.append(f"Clipped {num_clipped_sp} Speed values to range [0, 390] km/h.")

    if 'Throttle' in cleaned.columns:
        thr_vals = cleaned['Throttle'].values
        clipped_thr = np.clip(thr_vals, 0.0, 100.0)
        num_clipped_thr = (thr_vals != clipped_thr).sum()
        if num_clipped_thr > 0:
            cleaned['Throttle'] = clipped_thr
            rows_repaired += num_clipped_thr
            ops_log.append(f"Clipped {num_clipped_thr} Throttle values to range [0, 100]%.")

    metadata = {
        "status": "SUCCESS",
        "initial_rows": initial_rows,
        "final_rows": len(cleaned),
        "rows_removed": rows_removed,
        "rows_repaired": rows_repaired,
        "operations": ops_log
    }

    return cleaned, metadata
