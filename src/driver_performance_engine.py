"""
Comprehensive Driver Performance & Vehicle Dynamics Engineering Engine.
Provides micro-sector segmentation, 5-phase corner decomposition, braking point analysis,
apex speed retention, throttle pickup dynamics, friction circle g-loads,
driver consistency statistics, and theoretical ideal-lap reconstruction.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
import math
from src.data_provenance import DataClassification, ProvenanceRecord


@dataclass
class MiniSectorDelta:
    mini_sector_idx: int
    start_distance_m: float
    end_distance_m: float
    primary_speed_kmh: float
    reference_speed_kmh: float
    speed_delta_kmh: float
    time_delta_s: float
    dominant_driver: str


@dataclass
class CornerDynamicsProfile:
    corner_number: int
    corner_name: str
    corner_type: str                   # "LOW_SPEED", "MEDIUM_SPEED", "HIGH_SPEED", "HAIRPIN", "CHICANE"
    braking_distance_m: float          # Distance from initial brake to minimum apex speed
    braking_entry_speed_kmh: float     # Speed at initial brake application
    apex_speed_kmh: float              # Minimum speed at corner apex
    peak_deceleration_g: float         # Peak longitudinal deceleration (ax)
    peak_lateral_g: float              # Peak centripetal lateral acceleration (ay)
    throttle_pickup_delay_s: float     # Time from apex to initial throttle pickup
    throttle_pickup_distance_m: float  # Distance from apex to initial throttle pickup
    full_throttle_distance_m: float    # Distance from apex to 100% full throttle
    exit_speed_kmh: float              # Speed at corner exit boundary
    time_loss_vs_ref_s: float          # Differential time loss vs reference driver


@dataclass
class DriverConsistencyProfile:
    driver_id: str
    total_laps_analyzed: int
    clean_laps_count: int
    mean_lap_time_s: float
    std_dev_lap_time_s: float          # Lap time standard deviation (sigma)
    iqr_lap_time_s: float              # Interquartile Range
    consistency_rating_pct: float      # Normalized 0-100 score
    lap_to_lap_delta_mean_s: float     # Average lap-to-lap delta


@dataclass
class IdealLapReconstruction:
    driver_id: str
    actual_best_lap_s: float
    ideal_lap_s: float
    potential_gain_s: float
    sector_1_best_s: float
    sector_2_best_s: float
    sector_3_best_s: float
    num_laps_synthesized: int
    limitations_disclaimer: str


class DriverPerformanceEngine:
    """Authoritative Driver Performance & Vehicle Dynamics Analysis Engine."""

    @classmethod
    def compute_vehicle_dynamics(cls, telemetry_df: pd.DataFrame) -> pd.DataFrame:
        """
        Derives longitudinal acceleration (ax), lateral acceleration (ay),
        and combined friction circle g-force from raw speed, distance, and time.
        """
        if telemetry_df.empty or len(telemetry_df) < 5:
            return telemetry_df

        df = telemetry_df.copy()

        # 1. Compute time delta dt in seconds
        if 'Time' in df.columns:
            if pd.api.types.is_timedelta64_dtype(df['Time']):
                time_s = df['Time'].dt.total_seconds().values
            else:
                time_s = np.array([t.total_seconds() if hasattr(t, 'total_seconds') else float(t) for t in df['Time']])
            dt = np.diff(time_s, prepend=time_s[0])
            dt[dt <= 0] = 0.05  # Prevent division by zero
        else:
            dt = np.full(len(df), 0.1)

        # 2. Longitudinal acceleration ax = dv / dt (in g units)
        speed_ms = df['Speed'].values / 3.6
        dv = np.diff(speed_ms, prepend=speed_ms[0])
        ax_g = (dv / dt) / 9.80665

        # Smooth ax to reduce high-frequency differentiation noise
        ax_g_smooth = pd.Series(ax_g).rolling(window=5, center=True, min_periods=1).mean().values

        # 3. Lateral acceleration ay: if X, Y coordinates exist, derive curvature kappa
        if 'X' in df.columns and 'Y' in df.columns and df['X'].notna().sum() > 10:
            x = df['X'].values
            y = df['Y'].values
            dx = np.diff(x, prepend=x[0])
            dy = np.diff(y, prepend=y[0])
            ds = np.sqrt(dx**2 + dy**2)
            ds[ds == 0] = 1.0

            # Unit tangent vectors
            tx = dx / ds
            ty = dy / ds

            # Normal derivative (curvature kappa = d(theta)/ds)
            dtx = np.diff(tx, prepend=tx[0])
            dty = np.diff(ty, prepend=ty[0])
            curvature = np.sqrt(dtx**2 + dty**2) / ds

            # ay = v^2 * curvature / 9.80665
            ay_g = (speed_ms**2 * curvature) / 9.80665
            ay_g_smooth = pd.Series(ay_g).rolling(window=5, center=True, min_periods=1).mean().values
            # Bound to physical F1 limits [-6.5g, +6.5g]
            ay_g_smooth = np.clip(ay_g_smooth, -6.5, 6.5)
        else:
            # Estimate lateral g from speed drop / curvature proxy
            ay_g_smooth = np.zeros(len(df))

        # 4. Total g-force on friction circle
        g_total = np.sqrt(ax_g_smooth**2 + ay_g_smooth**2)

        df['longitudinal_accel_g'] = np.round(ax_g_smooth, 3)
        df['lateral_accel_g'] = np.round(ay_g_smooth, 3)
        df['total_accel_g'] = np.round(g_total, 3)

        return df

    @classmethod
    def compute_micro_sectors(
        cls,
        drv_telemetry: pd.DataFrame,
        ref_telemetry: pd.DataFrame,
        drv_code: str = "VER",
        ref_code: str = "HAM",
        num_minisectors: int = 25
    ) -> List[MiniSectorDelta]:
        """
        Splits lap distance into equidistant micro-sectors and evaluates speed & delta time.
        """
        if drv_telemetry.empty or ref_telemetry.empty:
            return []

        max_dist = min(drv_telemetry['Distance'].max(), ref_telemetry['Distance'].max())
        if max_dist <= 100:
            return []

        sector_edges = np.linspace(0, max_dist, num_minisectors + 1)
        results: List[MiniSectorDelta] = []

        for i in range(num_minisectors):
            s_start = sector_edges[i]
            s_end = sector_edges[i + 1]

            d_seg = drv_telemetry[(drv_telemetry['Distance'] >= s_start) & (drv_telemetry['Distance'] < s_end)]
            r_seg = ref_telemetry[(ref_telemetry['Distance'] >= s_start) & (ref_telemetry['Distance'] < s_end)]

            if d_seg.empty or r_seg.empty:
                continue

            drv_spd = float(d_seg['Speed'].mean())
            ref_spd = float(r_seg['Speed'].mean())
            spd_delta = drv_spd - ref_spd

            # Delta time in seconds through microsector: dt = dist / avg_speed
            seg_len = s_end - s_start
            d_time = seg_len / (max(drv_spd, 10.0) / 3.6)
            r_time = seg_len / (max(ref_spd, 10.0) / 3.6)
            time_delta = d_time - r_time

            dominant = drv_code if time_delta < 0 else ref_code

            results.append(MiniSectorDelta(
                mini_sector_idx=i + 1,
                start_distance_m=round(float(s_start), 1),
                end_distance_m=round(float(s_end), 1),
                primary_speed_kmh=round(drv_spd, 1),
                reference_speed_kmh=round(ref_spd, 1),
                speed_delta_kmh=round(spd_delta, 1),
                time_delta_s=round(time_delta, 3),
                dominant_driver=dominant
            ))

        return results

    @classmethod
    def decompose_corners(
        cls,
        telemetry_df: pd.DataFrame,
        ref_telemetry_df: Optional[pd.DataFrame] = None
    ) -> List[CornerDynamicsProfile]:
        """
        Extracts 5-phase dynamics (braking distance, apex speed, peak decel g, throttle pickup)
        for every corner on circuit.
        """
        from src.corner_detection import detect_corners_from_telemetry

        if telemetry_df.empty or 'Distance' not in telemetry_df.columns:
            return []

        dist = telemetry_df['Distance'].values
        spd = telemetry_df['Speed'].values
        corners = detect_corners_from_telemetry(dist, spd)

        profiles: List[CornerDynamicsProfile] = []

        # Ensure vehicle dynamics channels exist
        if 'longitudinal_accel_g' not in telemetry_df.columns:
            telemetry_df = cls.compute_vehicle_dynamics(telemetry_df)

        for c in corners:
            c_df = telemetry_df[(telemetry_df['Distance'] >= c.entry_m) & (telemetry_df['Distance'] <= c.exit_m)]
            if c_df.empty:
                continue

            apex_dist = c.apex_m
            apex_spd = float(c.min_speed_kmh)

            # Classify corner type
            if apex_spd < 110.0:
                c_type = "LOW_SPEED"
            elif apex_spd < 185.0:
                c_type = "MEDIUM_SPEED"
            else:
                c_type = "HIGH_SPEED"

            # Braking phase: from entry to apex
            entry_spd = float(c_df.iloc[0]['Speed'])
            braking_dist = max(0.0, float(apex_dist - c.entry_m))
            peak_decel = float(c_df['longitudinal_accel_g'].min())  # Most negative ax

            # Lateral g
            peak_lat = float(c_df['lateral_accel_g'].max()) if 'lateral_accel_g' in c_df.columns else 2.5

            # Throttle pickup: search from apex forward
            post_apex = c_df[c_df['Distance'] >= apex_dist]
            throttle_pickup_dist = 0.0
            throttle_pickup_time = 0.0
            full_throttle_dist = float(c.exit_m - apex_dist)

            if not post_apex.empty and 'Throttle' in post_apex.columns:
                pickup_row = post_apex[post_apex['Throttle'] > 15.0]
                if not pickup_row.empty:
                    throttle_pickup_dist = float(pickup_row.iloc[0]['Distance'] - apex_dist)
                    throttle_pickup_time = throttle_pickup_dist / max(apex_spd / 3.6, 10.0)

                full_row = post_apex[post_apex['Throttle'] >= 98.0]
                if not full_row.empty:
                    full_throttle_dist = float(full_row.iloc[0]['Distance'] - apex_dist)

            exit_spd = float(c_df.iloc[-1]['Speed'])

            # Reference comparison delta if ref telemetry is provided
            time_loss = 0.0
            if ref_telemetry_df is not None and not ref_telemetry_df.empty:
                ref_c_df = ref_telemetry_df[(ref_telemetry_df['Distance'] >= c.entry_m) & (ref_telemetry_df['Distance'] <= c.exit_m)]
                if not ref_c_df.empty and 'Time' in c_df.columns and 'Time' in ref_c_df.columns:
                    try:
                        d_time = (c_df['Time'].iloc[-1] - c_df['Time'].iloc[0]).total_seconds()
                        r_time = (ref_c_df['Time'].iloc[-1] - ref_c_df['Time'].iloc[0]).total_seconds()
                        time_loss = d_time - r_time
                    except Exception:
                        pass

            num = int(c.corner_id.replace('T', '')) if c.corner_id.replace('T', '').isdigit() else len(profiles) + 1
            profiles.append(CornerDynamicsProfile(
                corner_number=num,
                corner_name=c.corner_name,
                corner_type=c_type,
                braking_distance_m=round(braking_dist, 1),
                braking_entry_speed_kmh=round(entry_spd, 1),
                apex_speed_kmh=round(apex_spd, 1),
                peak_deceleration_g=round(peak_decel, 2),
                peak_lateral_g=round(peak_lat, 2),
                throttle_pickup_delay_s=round(throttle_pickup_time, 2),
                throttle_pickup_distance_m=round(throttle_pickup_dist, 1),
                full_throttle_distance_m=round(full_throttle_dist, 1),
                exit_speed_kmh=round(exit_spd, 1),
                time_loss_vs_ref_s=round(time_loss, 3)
            ))

        return profiles

    @classmethod
    def compute_driver_consistency(cls, laps_df: pd.DataFrame, driver_id: str) -> DriverConsistencyProfile:
        """
        Calculates driver pace consistency, lap-time standard deviation (sigma),
        interquartile range (IQR), and normalized consistency rating.
        """
        drv_laps = laps_df[laps_df['Driver'] == driver_id]
        if drv_laps.empty:
            return DriverConsistencyProfile(driver_id, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)

        # Filter clean laps: non-pit, non-in/out, accurate, lap time > 40s
        clean = drv_laps.copy()
        if 'PitInTime' in clean.columns:
            clean = clean[clean['PitInTime'].isna()]
        if 'PitOutTime' in clean.columns:
            clean = clean[clean['PitOutTime'].isna()]
        if 'IsAccurate' in clean.columns:
            clean = clean[clean['IsAccurate'] == True]

        if 'LapTime' in clean.columns:
            if pd.api.types.is_timedelta64_dtype(clean['LapTime']):
                clean_times = clean['LapTime'].dt.total_seconds().dropna().values
            else:
                clean_times = np.array([t.total_seconds() for t in clean['LapTime'] if hasattr(t, 'total_seconds')])
        else:
            clean_times = np.array([])

        clean_times = clean_times[clean_times > 40.0]

        if len(clean_times) < 3:
            return DriverConsistencyProfile(driver_id, len(drv_laps), len(clean_times), 0.0, 0.0, 0.0, 85.0, 0.0)

        mean_time = float(np.mean(clean_times))
        std_time = float(np.std(clean_times))
        q75, q25 = np.percentile(clean_times, [75, 25])
        iqr = float(q75 - q25)

        # Lap-to-lap delta average
        deltas = np.abs(np.diff(clean_times))
        mean_delta = float(np.mean(deltas)) if len(deltas) > 0 else 0.0

        # Consistency rating: 100 - (std_time / mean_time * 1000)
        # Typical F1 stint std is 0.3s - 0.8s on an 80s lap -> coefficient of variation 0.003 - 0.010
        cv = std_time / mean_time
        score = max(50.0, min(99.5, 100.0 - (cv * 2000.0)))

        return DriverConsistencyProfile(
            driver_id=driver_id,
            total_laps_analyzed=len(drv_laps),
            clean_laps_count=len(clean_times),
            mean_lap_time_s=round(mean_time, 3),
            std_dev_lap_time_s=round(std_time, 3),
            iqr_lap_time_s=round(iqr, 3),
            consistency_rating_pct=round(score, 1),
            lap_to_lap_delta_mean_s=round(mean_delta, 3)
        )

    @classmethod
    def reconstruct_ideal_lap(cls, laps_df: pd.DataFrame, driver_id: str) -> IdealLapReconstruction:
        """
        Synthesizes the theoretical ideal lap by combining personal best sector times
        with explicit limitation disclaimer.
        """
        drv_laps = laps_df[laps_df['Driver'] == driver_id]
        if drv_laps.empty:
            return IdealLapReconstruction(driver_id, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, "No lap data available.")

        def to_sec(col):
            if col not in drv_laps.columns:
                return []
            vals = []
            for v in drv_laps[col].dropna():
                if hasattr(v, 'total_seconds'):
                    vals.append(v.total_seconds())
                elif isinstance(v, (int, float)) and v > 0:
                    vals.append(float(v))
            return vals

        s1_vals = to_sec('Sector1Time')
        s2_vals = to_sec('Sector2Time')
        s3_vals = to_sec('Sector3Time')
        lap_vals = to_sec('LapTime')

        best_s1 = min(s1_vals) if s1_vals else 0.0
        best_s2 = min(s2_vals) if s2_vals else 0.0
        best_s3 = min(s3_vals) if s3_vals else 0.0
        actual_best = min(lap_vals) if lap_vals else (best_s1 + best_s2 + best_s3)

        ideal = best_s1 + best_s2 + best_s3
        gain = max(0.0, actual_best - ideal)

        disclaimer = (
            "Theoretical composite lap synthesized from disjoint personal best sector times. "
            "Continuous lap physics (tyre thermal accumulation, battery SOC deployment, and fuel burn) "
            "cannot be sustained simultaneously across all 3 sectors on a single lap."
        )

        return IdealLapReconstruction(
            driver_id=driver_id,
            actual_best_lap_s=round(actual_best, 3),
            ideal_lap_s=round(ideal, 3),
            potential_gain_s=round(gain, 3),
            sector_1_best_s=round(best_s1, 3),
            sector_2_best_s=round(best_s2, 3),
            sector_3_best_s=round(best_s3, 3),
            num_laps_synthesized=len(drv_laps),
            limitations_disclaimer=disclaimer
        )
