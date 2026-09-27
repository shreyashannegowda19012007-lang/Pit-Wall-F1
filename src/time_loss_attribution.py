"""
Time-Loss Attribution & Driver Weakness Analysis Engine for Formula One Telemetry.
Calculates mathematically defensible time loss integrals (dt = dx / v) and input deltas per corner.
Reconciles individual corner time losses directly with total lap time delta.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
import numpy as np
import pandas as pd
from corner_detection import CornerWindow


@dataclass
class CornerPerformanceAnalysis:
    """Measurable engineering breakdown of driver performance in a single corner window."""
    corner_id: str
    corner_name: str
    entry_m: float
    apex_m: float
    exit_m: float
    time_loss_seconds: float                  # Integrated dt = dx / v
    braking_point_delta_m: Optional[float]    # + means braking later, - means braking earlier
    peak_brake_delta_pct: Optional[float]     # % delta or None if unavailable
    minimum_speed_delta_kmh: float            # v_apex_A - v_apex_B
    throttle_delay_seconds: Optional[float]   # Throttle application delay delta (s)
    exit_speed_delta_kmh: float               # v_exit_A - v_exit_B
    driver_apex_speed_kmh: float
    ref_apex_speed_kmh: float
    driver_exit_speed_kmh: float
    ref_exit_speed_kmh: float
    confidence_level: str                     # "HIGH", "MEDIUM", "LOW"
    confidence_score: int                     # 0 - 100
    available_metrics: Dict[str, bool] = field(default_factory=dict)
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "corner_id": self.corner_id,
            "corner_name": self.corner_name,
            "entry_m": round(self.entry_m, 1),
            "apex_m": round(self.apex_m, 1),
            "exit_m": round(self.exit_m, 1),
            "time_loss_seconds": round(self.time_loss_seconds, 3),
            "braking_point_delta_m": round(self.braking_point_delta_m, 1) if self.braking_point_delta_m is not None else None,
            "peak_brake_delta_pct": round(self.peak_brake_delta_pct, 1) if self.peak_brake_delta_pct is not None else None,
            "minimum_speed_delta_kmh": round(self.minimum_speed_delta_kmh, 1),
            "throttle_delay_seconds": round(self.throttle_delay_seconds, 3) if self.throttle_delay_seconds is not None else None,
            "exit_speed_delta_kmh": round(self.exit_speed_delta_kmh, 1),
            "driver_apex_speed_kmh": round(self.driver_apex_speed_kmh, 1),
            "ref_apex_speed_kmh": round(self.ref_apex_speed_kmh, 1),
            "driver_exit_speed_kmh": round(self.driver_exit_speed_kmh, 1),
            "ref_exit_speed_kmh": round(self.ref_exit_speed_kmh, 1),
            "confidence_level": self.confidence_level,
            "confidence_score": self.confidence_score,
            "available_metrics": self.available_metrics,
            "explanation": self.explanation
        }


def analyze_corner_performance(
    aligned_df: pd.DataFrame,
    corner: CornerWindow,
    driver_a_code: str = "Driver A",
    driver_b_code: str = "Driver B"
) -> CornerPerformanceAnalysis:
    """
    Computes evidence-backed engineering metrics for a single corner window using aligned distance telemetry.
    """
    if aligned_df is None or aligned_df.empty:
        return _build_empty_corner_analysis(corner, driver_a_code, driver_b_code)

    # Slice corner window region
    c_df = aligned_df[(aligned_df['Distance'] >= corner.entry_m) & (aligned_df['Distance'] <= corner.exit_m)].copy()

    if c_df.empty or len(c_df) < 3:
        return _build_empty_corner_analysis(corner, driver_a_code, driver_b_code)

    # 1. Scientific Time Loss Integration (dt = dx / v)
    time_loss = c_df['DeltaTime'].iloc[-1] - c_df['DeltaTime'].iloc[0]

    # 2. Apex Speeds & Apex Minimum Speed Delta
    sp_a = c_df['Speed_A'].values
    sp_b = c_df['Speed_B'].values

    min_sp_a_idx = np.argmin(sp_a)
    min_sp_b_idx = np.argmin(sp_b)

    v_apex_a = float(sp_a[min_sp_a_idx])
    v_apex_b = float(sp_b[min_sp_b_idx])
    delta_v_apex = v_apex_a - v_apex_b

    apex_dist_a = c_df['Distance'].iloc[min_sp_a_idx]
    apex_dist_b = c_df['Distance'].iloc[min_sp_b_idx]

    # 3. Exit Speeds
    v_exit_a = float(sp_a[-1])
    v_exit_b = float(sp_b[-1])
    delta_v_exit = v_exit_a - v_exit_b

    # 4. Braking Point Detection
    # Look for distance where Brake > 5% prior to apex
    brk_a = c_df['Brake_A'].values
    brk_b = c_df['Brake_B'].values

    braking_idx_a = np.where(brk_a[:min_sp_a_idx + 1] > 5.0)[0]
    braking_idx_b = np.where(brk_b[:min_sp_b_idx + 1] > 5.0)[0]

    braking_dist_a = float(c_df['Distance'].iloc[braking_idx_a[0]]) if len(braking_idx_a) > 0 else None
    braking_dist_b = float(c_df['Distance'].iloc[braking_idx_b[0]]) if len(braking_idx_b) > 0 else None

    # Fallback to throttle drop if brake channel was flat
    if braking_dist_a is None:
        thr_a_pre = c_df['Throttle_A'].values[:min_sp_a_idx + 1]
        drop_a = np.where(thr_a_pre < 30.0)[0]
        if len(drop_a) > 0:
            braking_dist_a = float(c_df['Distance'].iloc[drop_a[0]])

    if braking_dist_b is None:
        thr_b_pre = c_df['Throttle_B'].values[:min_sp_b_idx + 1]
        drop_b = np.where(thr_b_pre < 30.0)[0]
        if len(drop_b) > 0:
            braking_dist_b = float(c_df['Distance'].iloc[drop_b[0]])

    braking_point_delta = (braking_dist_a - braking_dist_b) if (braking_dist_a is not None and braking_dist_b is not None) else None

    # 5. Peak Brake Application Delta & Channel Availability Checks
    channel_avail_a = getattr(aligned_df, 'attrs', {}).get('channel_availability_a', {})
    channel_avail_b = getattr(aligned_df, 'attrs', {}).get('channel_availability_b', {})

    brake_both_present = channel_avail_a.get('brake', True) and channel_avail_b.get('brake', True)
    throttle_both_present = channel_avail_a.get('throttle', True) and channel_avail_b.get('throttle', True)

    max_brk_a = float(np.max(brk_a))
    max_brk_b = float(np.max(brk_b))

    has_graduated_brake = brake_both_present and (max_brk_a > 1.0 or max_brk_b > 1.0) and (max_brk_a != 100.0 or max_brk_b != 100.0)
    peak_brake_delta = (max_brk_a - max_brk_b) if has_graduated_brake else None

    # 6. Throttle Application Delay (Time from apex to Throttle > 15%)
    thr_a_post = c_df['Throttle_A'].values[min_sp_a_idx:]
    thr_b_post = c_df['Throttle_B'].values[min_sp_b_idx:]

    time_a_post = c_df['Time_A'].values[min_sp_a_idx:]
    time_b_post = c_df['Time_B'].values[min_sp_b_idx:]

    thr_on_a = np.where(thr_a_post > 15.0)[0]
    thr_on_b = np.where(thr_b_post > 15.0)[0]

    delay_a = (time_a_post[thr_on_a[0]] - time_a_post[0]) if len(thr_on_a) > 0 else None
    delay_b = (time_b_post[thr_on_b[0]] - time_b_post[0]) if len(thr_on_b) > 0 else None

    throttle_delay = (delay_a - delay_b) if (throttle_both_present and delay_a is not None and delay_b is not None) else None

    # Channel Availability Map
    avail = {
        "speed": True,
        "throttle": throttle_both_present,
        "brake": brake_both_present,
        "graduated_brake_pressure": has_graduated_brake,
        "steering": False,
        "tire_temp": False
    }

    # Confidence Score Calculation
    conf_score = 95
    if not avail["throttle"]:
        conf_score -= 15
    if not avail["brake"]:
        conf_score -= 15
    if braking_point_delta is None:
        conf_score -= 10
    if throttle_delay is None:
        conf_score -= 10

    conf_score = max(40, conf_score)
    conf_level = "HIGH" if conf_score >= 85 else ("MEDIUM" if conf_score >= 65 else "LOW")

    # Explanation Generation
    explanation_parts = []
    if abs(time_loss) >= 0.005:
        verb = "loses" if time_loss > 0 else "gains"
        explanation_parts.append(f"{driver_a_code} {verb} {abs(time_loss):.3f}s in {corner.corner_name} compared with {driver_b_code}.")
    else:
        explanation_parts.append(f"{driver_a_code} matches {driver_b_code} pace in {corner.corner_name}.")

    if braking_point_delta is not None and abs(braking_point_delta) >= 1.0:
        b_verb = "later" if braking_point_delta > 0 else "earlier"
        explanation_parts.append(f"Braking is {abs(braking_point_delta):.1f}m {b_verb}.")

    if abs(delta_v_apex) >= 0.5:
        a_verb = "lower" if delta_v_apex < 0 else "higher"
        explanation_parts.append(f"Minimum apex speed is {abs(delta_v_apex):.1f} km/h {a_verb} ({v_apex_a:.1f} km/h vs {v_apex_b:.1f} km/h).")

    if throttle_delay is not None and abs(throttle_delay) >= 0.02:
        t_verb = "delayed by" if throttle_delay > 0 else "applied"
        t_suffix = f"{abs(throttle_delay):.2f}s" if throttle_delay > 0 else f"{abs(throttle_delay):.2f}s earlier"
        explanation_parts.append(f"Throttle application is {t_verb} {t_suffix}.")

    if abs(delta_v_exit) >= 0.5:
        e_verb = "lower" if delta_v_exit < 0 else "higher"
        explanation_parts.append(f"Corner exit speed is {abs(delta_v_exit):.1f} km/h {e_verb}.")

    explanation = " ".join(explanation_parts)

    return CornerPerformanceAnalysis(
        corner_id=corner.corner_id,
        corner_name=corner.corner_name,
        entry_m=corner.entry_m,
        apex_m=corner.apex_m,
        exit_m=corner.exit_m,
        time_loss_seconds=float(time_loss),
        braking_point_delta_m=braking_point_delta,
        peak_brake_delta_pct=peak_brake_delta,
        minimum_speed_delta_kmh=delta_v_apex,
        throttle_delay_seconds=throttle_delay,
        exit_speed_delta_kmh=delta_v_exit,
        driver_apex_speed_kmh=v_apex_a,
        ref_apex_speed_kmh=v_apex_b,
        driver_exit_speed_kmh=v_exit_a,
        ref_exit_speed_kmh=v_exit_b,
        confidence_level=conf_level,
        confidence_score=conf_score,
        available_metrics=avail,
        explanation=explanation
    )


def _build_empty_corner_analysis(corner: CornerWindow, driver_a: str, driver_b: str) -> CornerPerformanceAnalysis:
    return CornerPerformanceAnalysis(
        corner_id=corner.corner_id,
        corner_name=corner.corner_name,
        entry_m=corner.entry_m,
        apex_m=corner.apex_m,
        exit_m=corner.exit_m,
        time_loss_seconds=0.0,
        braking_point_delta_m=None,
        peak_brake_delta_pct=None,
        minimum_speed_delta_kmh=0.0,
        throttle_delay_seconds=None,
        exit_speed_delta_kmh=0.0,
        driver_apex_speed_kmh=0.0,
        ref_apex_speed_kmh=0.0,
        driver_exit_speed_kmh=0.0,
        ref_exit_speed_kmh=0.0,
        confidence_level="LOW",
        confidence_score=30,
        available_metrics={"speed": False, "throttle": False, "brake": False, "steering": False, "tire_temp": False},
        explanation=f"Insufficient telemetry data available for {corner.corner_name} comparison between {driver_a} and {driver_b}."
    )
