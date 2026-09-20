"""
Corner Detection & Corner Window Engine for Formula One Circuits.
Extracts corner entry, braking, apex, and exit distance boundaries dynamically from telemetry
or uses official circuit layout geometry metadata when available.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
import numpy as np
import pandas as pd
from scipy.signal import find_peaks


@dataclass
class CornerWindow:
    """Represents the distance boundaries of a single corner on circuit."""
    corner_id: str         # e.g., "T1", "T2"
    corner_name: str       # e.g., "Turn 1"
    entry_m: float         # Entry distance (m) where deceleration starts
    apex_m: float          # Apex distance (m) where minimum speed occurs
    exit_m: float          # Exit distance (m) where acceleration levels off
    braking_start_m: Optional[float] = None
    min_speed_kmh: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "corner_id": self.corner_id,
            "corner_name": self.corner_name,
            "entry_m": round(self.entry_m, 1),
            "apex_m": round(self.apex_m, 1),
            "exit_m": round(self.exit_m, 1),
            "braking_start_m": round(self.braking_start_m, 1) if self.braking_start_m is not None else None,
            "min_speed_kmh": round(self.min_speed_kmh, 1)
        }


def detect_corners_from_telemetry(
    distance_arr: np.ndarray,
    speed_arr: np.ndarray,
    min_speed_drop_kmh: float = 12.0,
    min_distance_gap_m: float = 80.0
) -> List[CornerWindow]:
    """
    Detects corners dynamically from a baseline speed trace profile.
    
    Args:
        distance_arr: Distance coordinate array in meters
        speed_arr: Speed trace array in km/h
        min_speed_drop_kmh: Minimum speed drop required to qualify as a corner
        min_distance_gap_m: Minimum spacing between consecutive apexes
        
    Returns:
        List of CornerWindow objects sorted by distance.
    """
    if len(distance_arr) < 10 or len(speed_arr) < 10:
        return []

    grid_step = float(np.mean(np.diff(distance_arr))) if len(distance_arr) > 1 else 1.0
    distance_step = max(1.0, grid_step)
    distance_window_indices = int(max(10, min_distance_gap_m / distance_step))

    # Invert speed to find local minima via find_peaks
    inv_speed = -speed_arr
    peaks, _ = find_peaks(inv_speed, distance=distance_window_indices, prominence=min_speed_drop_kmh * 0.4)

    corners: List[CornerWindow] = []

    for idx, apex_idx in enumerate(peaks):
        apex_dist = distance_arr[apex_idx]
        apex_speed = speed_arr[apex_idx]

        # 1. Search backward for entry_m (where speed was local maximum prior to braking)
        entry_idx = max(0, apex_idx - distance_window_indices)
        for i in range(apex_idx - 1, entry_idx, -1):
            if speed_arr[i] >= speed_arr[i + 1] and speed_arr[i] >= speed_arr[i - 1]:
                entry_idx = i
                break
        entry_dist = distance_arr[entry_idx]

        # 2. Search forward for exit_m (where speed reaches local maximum acceleration plateau)
        exit_idx = min(len(speed_arr) - 1, apex_idx + distance_window_indices)
        for i in range(apex_idx + 1, exit_idx):
            if speed_arr[i] >= speed_arr[i - 1] and speed_arr[i] >= speed_arr[i + 1]:
                exit_idx = i
                break
        exit_dist = distance_arr[exit_idx]

        # Qualify corner drop
        peak_pre_speed = speed_arr[entry_idx]
        if (peak_pre_speed - apex_speed) >= min_speed_drop_kmh:
            corner_num = len(corners) + 1
            corners.append(CornerWindow(
                corner_id=f"T{corner_num}",
                corner_name=f"Turn {corner_num}",
                entry_m=float(entry_dist),
                apex_m=float(apex_dist),
                exit_m=float(exit_dist),
                braking_start_m=float(entry_dist),
                min_speed_kmh=float(apex_speed)
            ))

    return corners

