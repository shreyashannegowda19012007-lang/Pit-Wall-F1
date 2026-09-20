"""
Telemetry Validation Engine for Formula One Telemetry Datasets.
Checks data integrity, timestamps, distances, channel boundaries, and sampling frequency.
Returns explicit, structured validation diagnostics without performing silent mutations.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np


@dataclass
class TelemetryValidationResult:
    """Structured report produced by telemetry validation routines."""
    is_valid: bool
    validation_status: str  # "PASSED", "WARNINGS", "FAILED"
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    rows_checked: int = 0
    rows_removed: int = 0
    rows_repaired: int = 0
    channel_availability: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "validation_status": self.validation_status,
            "errors": self.errors,
            "warnings": self.warnings,
            "rows_checked": self.rows_checked,
            "rows_removed": self.rows_removed,
            "rows_repaired": self.rows_repaired,
            "channel_availability": self.channel_availability,
        }


def validate_telemetry_df(df: pd.DataFrame) -> TelemetryValidationResult:
    """
    Performs comprehensive validation checks on a raw or ingested telemetry DataFrame.
    """
    errors: List[str] = []
    warnings: List[str] = []
    rows_checked = len(df) if df is not None else 0

    if df is None or df.empty:
        return TelemetryValidationResult(
            is_valid=False,
            validation_status="FAILED",
            errors=["Telemetry DataFrame is null or empty."],
            rows_checked=0,
            channel_availability={
                'timestamp': False, 'distance': False, 'speed': False,
                'throttle': False, 'brake': False, 'gear': False,
                'rpm': False, 'drs': False, 'steering': False
            }
        )

    # Channel Map Detection
    dist_col = 'Distance' if 'Distance' in df.columns else ('distance_m' if 'distance_m' in df.columns else None)
    speed_col = 'Speed' if 'Speed' in df.columns else ('speed_kmh' if 'speed_kmh' in df.columns else None)
    throttle_col = 'Throttle' if 'Throttle' in df.columns else ('throttle_pct' if 'throttle_pct' in df.columns else None)
    brake_col = 'Brake' if 'Brake' in df.columns else ('brake_pct' if 'brake_pct' in df.columns else None)
    time_col = 'Time' if 'Time' in df.columns else ('timestamp_s' if 'timestamp_s' in df.columns else None)
    gear_col = 'nGear' if 'nGear' in df.columns else ('gear' if 'gear' in df.columns else None)
    rpm_col = 'RPM' if 'RPM' in df.columns else None
    drs_col = 'DRS' if 'DRS' in df.columns else None
    steering_col = 'Steering' if 'Steering' in df.columns else None

    channel_availability = {
        'timestamp': time_col is not None,
        'distance': dist_col is not None,
        'speed': speed_col is not None,
        'throttle': throttle_col is not None,
        'brake': brake_col is not None,
        'gear': gear_col is not None,
        'rpm': bool(rpm_col is not None and df[rpm_col].notna().any()),
        'drs': bool(drs_col is not None and df[drs_col].notna().any()),
        'steering': bool(steering_col is not None and df[steering_col].notna().any())
    }

    # Mandatory Channel Checks
    if not dist_col:
        errors.append("Critical channel missing: Distance (m).")
    if not speed_col:
        errors.append("Critical channel missing: Speed (km/h).")

    if errors:
        return TelemetryValidationResult(
            is_valid=False,
            validation_status="FAILED",
            errors=errors,
            warnings=warnings,
            rows_checked=rows_checked,
            channel_availability=channel_availability
        )

    # 1. Distance checks
    dist_vals = df[dist_col].dropna().values
    if len(dist_vals) == 0:
        errors.append("Distance channel contains only NaN values.")
    else:
        if (dist_vals < 0).any():
            warnings.append(f"Found {(dist_vals < 0).sum()} negative distance values.")
        
        # Monotonicity check
        dist_diffs = np.diff(dist_vals)
        if (dist_diffs < 0).any():
            neg_count = (dist_diffs < 0).sum()
            warnings.append(f"Non-monotonic distance detected in {neg_count} places (GPS jitter or lap loopback).")

    # 2. Speed checks
    speed_vals = df[speed_col].dropna().values
    if len(speed_vals) > 0:
        if (speed_vals < 0).any():
            warnings.append(f"Found {(speed_vals < 0).sum()} negative speed samples.")
        if (speed_vals > 390.0).any():
            warnings.append(f"Found {(speed_vals > 390.0).sum()} unrealistically high speed samples (>390 km/h).")

    # 3. Throttle checks
    if throttle_col:
        thr_vals = df[throttle_col].dropna().values
        if len(thr_vals) > 0:
            if (thr_vals < 0).any() or (thr_vals > 100.0).any():
                warnings.append(f"Throttle values detected outside valid range [0, 100]%.")

    # 4. Brake checks
    if brake_col:
        brk_vals = df[brake_col].dropna().values
        # Could be boolean or float %
        if pd.api.types.is_numeric_dtype(df[brake_col]):
            if (brk_vals < 0).any() or (brk_vals > 100.0).any():
                warnings.append("Brake values detected outside valid range [0, 100]%.")

    # 5. Gear checks
    if gear_col:
        gear_vals = df[gear_col].dropna().values
        if len(gear_vals) > 0:
            if (gear_vals < 0).any() or (gear_vals > 8).any():
                warnings.append("Invalid gear values detected (<0 or >8).")

    # 6. Sampling Gap Anomaly Detection
    if time_col and hasattr(df[time_col], 'dt'):
        time_sec = df[time_col].dt.total_seconds().values
        time_diffs = np.diff(time_sec)
        gaps = time_diffs[time_diffs > 1.0]
        if len(gaps) > 0:
            warnings.append(f"Detected {len(gaps)} abnormal telemetry sampling gaps > 1.0s (max gap: {gaps.max():.2f}s).")

    is_valid = len(errors) == 0
    status = "PASSED" if (is_valid and len(warnings) == 0) else ("WARNINGS" if is_valid else "FAILED")

    return TelemetryValidationResult(
        is_valid=is_valid,
        validation_status=status,
        errors=errors,
        warnings=warnings,
        rows_checked=rows_checked,
        channel_availability=channel_availability
    )

