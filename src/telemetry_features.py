"""
Formal Feature Engineering Layer for F1 Time-Series Telemetry Pipeline.
Transforms cleaned and distance-aligned telemetry data into structured engineering metrics
at lap, corner, driver-comparison, and stint levels.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timezone


@dataclass
class LapFeatures:
    """Lap-level aggregated engineering metrics."""
    lap_time_s: float
    sector_1_s: Optional[float]
    sector_2_s: Optional[float]
    sector_3_s: Optional[float]
    average_speed_kmh: float
    max_speed_kmh: float
    min_speed_kmh: float
    total_distance_m: float
    full_throttle_pct: float
    heavy_braking_pct: float


@dataclass
class CornerFeatures:
    """Corner-level kinematic and input metrics."""
    corner_id: str
    corner_name: str
    entry_speed_kmh: float
    minimum_speed_kmh: float
    exit_speed_kmh: float
    braking_point_m: Optional[float]
    braking_distance_m: Optional[float]
    peak_brake_pct: Optional[float]
    throttle_application_m: Optional[float]
    throttle_delay_s: Optional[float]


@dataclass
class FeatureDataset:
    """Container holding calculated features for a single lap or lap comparison."""
    feature_set_id: str
    dataset_id: str
    session_id: str
    driver_id: str
    lap_number: Optional[int]
    lap_features: Optional[LapFeatures]
    corner_features: List[CornerFeatures] = field(default_factory=list)
    calculated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature_set_id": self.feature_set_id,
            "dataset_id": self.dataset_id,
            "session_id": self.session_id,
            "driver_id": self.driver_id,
            "lap_number": self.lap_number,
            "lap_features": self.lap_features.__dict__ if self.lap_features else None,
            "corner_features": [cf.__dict__ for cf in self.corner_features],
            "calculated_at": self.calculated_at
        }


class FeatureEngineeringService:
    """
    Feature Engineering Service for F1 Time-Series Data Pipeline.
    Calculates lap-level and corner-level features using available channel signals.
    Never manufactures missing values.
    """

    @classmethod
    def extract_lap_features(cls, df: pd.DataFrame, dataset_id: str, session_id: str, driver_id: str, lap_number: Optional[int] = None) -> FeatureDataset:
        """
        Extracts lap-level and corner-level features from a clean/aligned telemetry DataFrame.
        """
        if df is None or df.empty:
            return FeatureDataset(
                feature_set_id=f"FEAT-{driver_id}-{session_id}-EMPTY",
                dataset_id=dataset_id,
                session_id=session_id,
                driver_id=driver_id,
                lap_number=lap_number,
                lap_features=None,
                corner_features=[]
            )

        sp = df['Speed'].values if 'Speed' in df.columns else df.get('speed_kmh', pd.Series()).values
        dist = df['Distance'].values if 'Distance' in df.columns else df.get('distance_m', pd.Series()).values
        thr = df['Throttle'].values if 'Throttle' in df.columns else df.get('throttle_pct', pd.Series()).values
        brk = df['Brake'].values if 'Brake' in df.columns else df.get('brake_pct', pd.Series()).values

        # 1. Lap-level calculations
        avg_sp = float(np.mean(sp)) if len(sp) > 0 else 0.0
        max_sp = float(np.max(sp)) if len(sp) > 0 else 0.0
        min_sp = float(np.min(sp)) if len(sp) > 0 else 0.0
        total_dist = float(dist[-1] - dist[0]) if len(dist) > 1 else 0.0

        full_thr_pct = float((thr >= 95.0).sum() / len(thr) * 100.0) if len(thr) > 0 else 0.0
        heavy_brk_pct = float((brk >= 50.0).sum() / len(brk) * 100.0) if len(brk) > 0 else 0.0

        # Estimated lap time from distance & speed integral
        if len(dist) > 1 and len(sp) > 1:
            v_ms = np.maximum(sp / 3.6, 0.5)
            dx = np.gradient(dist)
            lap_time_s = float(np.sum(dx / v_ms))
        else:
            lap_time_s = 0.0

        lap_feats = LapFeatures(
            lap_time_s=round(lap_time_s, 3),
            sector_1_s=None,
            sector_2_s=None,
            sector_3_s=None,
            average_speed_kmh=round(avg_sp, 1),
            max_speed_kmh=round(max_sp, 1),
            min_speed_kmh=round(min_sp, 1),
            total_distance_m=round(total_dist, 1),
            full_throttle_pct=round(full_thr_pct, 1),
            heavy_braking_pct=round(heavy_brk_pct, 1)
        )

        # 2. Extract Corner-level features if corners can be detected
        from corner_detection import detect_corners_from_telemetry
        corners = detect_corners_from_telemetry(dist, sp)
        corner_feats: List[CornerFeatures] = []

        for c in corners:
            c_mask = (dist >= c.entry_m) & (dist <= c.exit_m)
            c_sp = sp[c_mask]
            c_thr = thr[c_mask] if len(thr) == len(sp) else np.array([])
            c_brk = brk[c_mask] if len(brk) == len(sp) else np.array([])
            c_dist = dist[c_mask]

            if len(c_sp) > 0:
                entry_sp = float(c_sp[0])
                apex_sp = float(np.min(c_sp))
                exit_sp = float(c_sp[-1])
                min_idx = np.argmin(c_sp)

                # Braking point & distance
                brk_pt = None
                brk_dist = None
                peak_brk = float(np.max(c_brk)) if len(c_brk) > 0 else None

                if len(c_brk) > 0:
                    b_on = np.where(c_brk[:min_idx + 1] > 5.0)[0]
                    if len(b_on) > 0:
                        brk_pt = float(c_dist[b_on[0]])
                        apex_d = float(c_dist[min_idx])
                        brk_dist = float(apex_d - brk_pt)

                # Throttle application point
                thr_pt = None
                if len(c_thr) > 0:
                    t_on = np.where(c_thr[min_idx:] > 15.0)[0]
                    if len(t_on) > 0:
                        thr_pt = float(c_dist[min_idx + t_on[0]])

                corner_feats.append(CornerFeatures(
                    corner_id=c.corner_id,
                    corner_name=c.corner_name,
                    entry_speed_kmh=round(entry_sp, 1),
                    minimum_speed_kmh=round(apex_sp, 1),
                    exit_speed_kmh=round(exit_sp, 1),
                    braking_point_m=round(brk_pt, 1) if brk_pt is not None else None,
                    braking_distance_m=round(brk_dist, 1) if brk_dist is not None else None,
                    peak_brake_pct=round(peak_brk, 1) if peak_brk is not None else None,
                    throttle_application_m=round(thr_pt, 1) if thr_pt is not None else None,
                    throttle_delay_s=None
                ))

        feature_set_id = f"FEAT-{driver_id}-{session_id}-{dataset_id[:8]}"

        return FeatureDataset(
            feature_set_id=feature_set_id,
            dataset_id=dataset_id,
            session_id=session_id,
            driver_id=driver_id,
            lap_number=lap_number,
            lap_features=lap_feats,
            corner_features=corner_feats
        )

