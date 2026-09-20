"""
Physical & Logical Invariants & Data Sanity Verification Layer.
Validates physical racing constraints, sensor value boundaries, distance monotonicity,
and probability sum invariants to prevent impossible or corrupt racing telemetry data.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np


@dataclass
class SanityViolation:
    severity: str    # "ERROR", "WARNING", "EXPECTED_VARIATION"
    rule_name: str
    message: str
    affected_rows: int = 1


class DataSanityEngine:
    """
    Automated Physical & Logical Invariant Validator.
    """

    @classmethod
    def validate_telemetry_invariants(cls, laps_df: pd.DataFrame, telemetry_df: Optional[pd.DataFrame] = None) -> Tuple[bool, List[SanityViolation]]:
        """
        Validates telemetry dataframe against physical racing invariants.
        """
        violations: List[SanityViolation] = []

        if laps_df.empty:
            return True, violations

        # 1. Lap Numbers Monotonic Increasing Check
        if 'LapNumber' in laps_df.columns:
            laps_sorted = laps_df['LapNumber'].values
            if not all(x <= y for x, y in zip(laps_sorted, laps_sorted[1:])):
                violations.append(SanityViolation(
                    severity="ERROR",
                    rule_name="NON_MONOTONIC_LAP_NUMBERS",
                    message="Lap numbers do not progress monotonically."
                ))

        # 2. Lap Time Physical Bounds Check (15s <= LapTime <= 300s)
        if 'LapTime' in laps_df.columns:
            sec_times = laps_df['LapTime'].dt.total_seconds().values
            invalid_laps = [t for t in sec_times if pd.notna(t) and (t < 15.0 or t > 300.0)]
            if invalid_laps:
                violations.append(SanityViolation(
                    severity="ERROR",
                    rule_name="UNREALISTIC_LAP_TIME",
                    message=f"Found {len(invalid_laps)} lap times outside physical bounds (15s - 300s).",
                    affected_rows=len(invalid_laps)
                ))

        # 3. High-Frequency Telemetry Invariants Check
        if telemetry_df is not None and not telemetry_df.empty:
            # Speed >= 0 km/h and Speed <= 400 km/h
            if 'Speed' in telemetry_df.columns:
                speed_vals = telemetry_df['Speed'].values
                invalid_speed = np.sum((speed_vals < 0) | (speed_vals > 400))
                if invalid_speed > 0:
                    violations.append(SanityViolation(
                        severity="ERROR",
                        rule_name="SPEED_OUT_OF_BOUNDS",
                        message=f"Found {invalid_speed} speed samples outside physical limits [0, 400] km/h.",
                        affected_rows=int(invalid_speed)
                    ))

            # Throttle & Brake in [0, 100]%
            if 'Throttle' in telemetry_df.columns:
                thr_vals = telemetry_df['Throttle'].values
                invalid_thr = np.sum((thr_vals < 0) | (thr_vals > 100))
                if invalid_thr > 0:
                    violations.append(SanityViolation(
                        severity="ERROR",
                        rule_name="THROTTLE_OUT_OF_BOUNDS",
                        message=f"Found {invalid_thr} throttle samples outside bounds [0, 100]%.",
                        affected_rows=int(invalid_thr)
                    ))

            # Distance Monotonicity within Lap
            if 'Distance' in telemetry_df.columns:
                dist_vals = telemetry_df['Distance'].values
                decreases = np.sum(np.diff(dist_vals) < -5.0)  # Allow small 5m GPS wrap-around reset
                if decreases > 1:
                    violations.append(SanityViolation(
                        severity="WARNING",
                        rule_name="DISTANCE_NON_MONOTONIC",
                        message=f"Found {decreases} distance backward jumps within lap telemetry.",
                        affected_rows=int(decreases)
                    ))

        is_valid = not any(v.severity == "ERROR" for v in violations)
        return is_valid, violations

    @staticmethod
    def validate_probability_invariants(probs_map: Dict[str, float]) -> Tuple[bool, List[str]]:
        """
        Validates discrete probability map invariants (0 <= P <= 1, sum ≈ 1.0).
        """
        errors = []
        if not probs_map:
            return False, ["Probability map is empty."]

        total_sum = sum(probs_map.values())
        for k, v in probs_map.items():
            if not (0.0 <= v <= 1.0):
                errors.append(f"Invalid probability value for {k}: {v} (must be in [0.0, 1.0]).")

        if abs(total_sum - 1.0) > 0.05:
            errors.append(f"Probability sum invariant violated: sum = {total_sum:.4f} != 1.0.")

        return len(errors) == 0, errors

