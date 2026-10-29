"""
Central Telemetry Analysis Service for Formula One Race Engineering Platform.
Orchestrates telemetry validation, clean preprocessing, distance alignment,
corner window extraction, time-loss integration, and driver weakness opportunity ranking.
"""

from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np
import logging

from telemetry_model import CanonicalLapTelemetry, TelemetryUnits
from telemetry_validation import validate_telemetry_df, TelemetryValidationResult
from telemetry_cleaning import clean_telemetry_df
from lap_alignment import align_laps_by_distance
from corner_detection import detect_corners_from_telemetry, CornerWindow
from time_loss_attribution import analyze_corner_performance, CornerPerformanceAnalysis

logger = logging.getLogger(__name__)


class TelemetryAnalysisService:
    """
    Central API service providing scientifically defensible telemetry comparison,
    time-loss attribution, and driver weakness diagnostics.
    """

    @staticmethod
    def extract_driver_fastest_telemetry(session: Any, driver_code: str, lap_number: Optional[int] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Safely extracts raw telemetry for a driver's lap from FastF1 session object.
        """
        try:
            if not hasattr(session, 'laps') or session.laps is None or session.laps.empty:
                return pd.DataFrame(), {"error": "Session contains no lap data."}

            if hasattr(session.laps, 'pick_drivers'):
                driver_laps = session.laps.pick_drivers(driver_code)
            else:
                driver_laps = session.laps[session.laps['Driver'] == driver_code]

            if driver_laps.empty:
                return pd.DataFrame(), {"error": f"No lap data found for driver {driver_code}."}

            if lap_number is not None:
                selected_laps = driver_laps[driver_laps['LapNumber'] == lap_number]
                if selected_laps.empty:
                    return pd.DataFrame(), {"error": f"Lap {lap_number} not found for driver {driver_code}."}
                lap = selected_laps.iloc[0]
            else:
                lap = driver_laps.pick_fastest()

            if not hasattr(lap, 'get_telemetry'):
                return pd.DataFrame(), {"error": "Lap object does not support get_telemetry()."}

            raw_tel = lap.get_telemetry().add_distance()
            if raw_tel is None or raw_tel.empty:
                return pd.DataFrame(), {"error": "Telemetry trace is empty."}

            lap_time_s = lap['LapTime'].total_seconds() if pd.notna(lap.get('LapTime')) else 0.0
            
            s1_s = lap['Sector1Time'].total_seconds() if pd.notna(lap.get('Sector1Time')) and hasattr(lap.get('Sector1Time'), 'total_seconds') else None
            s2_s = lap['Sector2Time'].total_seconds() if pd.notna(lap.get('Sector2Time')) and hasattr(lap.get('Sector2Time'), 'total_seconds') else None
            s3_s = lap['Sector3Time'].total_seconds() if pd.notna(lap.get('Sector3Time')) and hasattr(lap.get('Sector3Time'), 'total_seconds') else None

            meta = {
                "driver": driver_code,
                "lap_number": int(lap.get('LapNumber', 0)),
                "lap_time_s": lap_time_s,
                "compound": str(lap.get('Compound', 'UNKNOWN')),
                "tyre_age": int(lap.get('TyreLife', 0)) if pd.notna(lap.get('TyreLife')) else 0,
                "sector1_s": s1_s,
                "sector2_s": s2_s,
                "sector3_s": s3_s
            }
            return raw_tel, meta

        except Exception as e:
            logger.error(f"Failed to extract telemetry for {driver_code}: {e}")
            return pd.DataFrame(), {"error": str(e)}

    @classmethod
    def compare_laps(
        cls,
        session: Any,
        target_driver: str,
        ref_driver: str,
        target_lap_num: Optional[int] = None,
        ref_lap_num: Optional[int] = None,
        grid_step_m: float = 1.0
    ) -> Dict[str, Any]:
        """
        Performs comprehensive distance-aligned time loss analysis between target driver and reference driver.
        """
        # 1. Extract raw telemetry
        raw_tel_a, meta_a = cls.extract_driver_fastest_telemetry(session, target_driver, target_lap_num)
        raw_tel_b, meta_b = cls.extract_driver_fastest_telemetry(session, ref_driver, ref_lap_num)

        if raw_tel_a.empty or raw_tel_b.empty:
            return {
                "success": False,
                "error": meta_a.get("error") or meta_b.get("error") or "Failed to load telemetry for one or both drivers."
            }

        # 2. Validate & Clean
        val_a = validate_telemetry_df(raw_tel_a)
        val_b = validate_telemetry_df(raw_tel_b)

        clean_a, _ = clean_telemetry_df(raw_tel_a, val_a)
        clean_b, _ = clean_telemetry_df(raw_tel_b, val_b)

        # 3. Distance-Based Alignment
        aligned_df, align_meta = align_laps_by_distance(
            clean_a, clean_b,
            grid_step_m=grid_step_m,
            driver_a_code=target_driver,
            driver_b_code=ref_driver
        )

        if aligned_df.empty:
            return {"success": False, "error": align_meta.get("error", "Distance alignment failed.")}

        # 4. Corner Detection from Reference Lap Speed Trace
        corners = detect_corners_from_telemetry(
            aligned_df['Distance'].values,
            aligned_df['Speed_B'].values
        )

        # 5. Corner-by-Corner Time Loss & Metric Attribution
        corner_analyses: List[CornerPerformanceAnalysis] = []
        for c in corners:
            analysis = analyze_corner_performance(aligned_df, c, target_driver, ref_driver)
            corner_analyses.append(analysis)

        # 6. Sector Time Loss Breakdown
        track_len = aligned_df['Distance'].max()
        s1_end = track_len * 0.33
        s2_end = track_len * 0.66

        def get_segment_time_loss(start_m: float, end_m: float) -> float:
            sub = aligned_df[(aligned_df['Distance'] >= start_m) & (aligned_df['Distance'] <= end_m)]
            if sub.empty:
                return 0.0
            return float(sub['DeltaTime'].iloc[-1] - sub['DeltaTime'].iloc[0])

        if meta_a.get("sector1_s") is not None and meta_b.get("sector1_s") is not None:
            s1_loss = meta_a["sector1_s"] - meta_b["sector1_s"]
        else:
            s1_loss = get_segment_time_loss(0.0, s1_end)

        if meta_a.get("sector2_s") is not None and meta_b.get("sector2_s") is not None:
            s2_loss = meta_a["sector2_s"] - meta_b["sector2_s"]
        else:
            s2_loss = get_segment_time_loss(s1_end, s2_end)

        if meta_a.get("sector3_s") is not None and meta_b.get("sector3_s") is not None:
            s3_loss = meta_a["sector3_s"] - meta_b["sector3_s"]
        else:
            s3_loss = get_segment_time_loss(s2_end, track_len)

        # 7. Sort Top Opportunities by Time Loss (where target_driver loses most time)
        opportunities = [c for c in corner_analyses if c.time_loss_seconds > 0.01]
        opportunities.sort(key=lambda x: x.time_loss_seconds, reverse=True)

        total_lap_time_delta = meta_a.get("lap_time_s", 0.0) - meta_b.get("lap_time_s", 0.0)
        integrated_time_delta = float(aligned_df['DeltaTime'].iloc[-1])

        return {
            "success": True,
            "target_driver": target_driver,
            "ref_driver": ref_driver,
            "target_meta": meta_a,
            "ref_meta": meta_b,
            "lap_time_delta_s": round(total_lap_time_delta, 3),
            "integrated_time_delta_s": round(integrated_time_delta, 3),
            "sector_time_loss": {
                "sector_1_s": round(s1_loss, 3) if not np.isnan(s1_loss) else 0.0,
                "sector_2_s": round(s2_loss, 3) if not np.isnan(s2_loss) else 0.0,
                "sector_3_s": round(s3_loss, 3) if not np.isnan(s3_loss) else 0.0
            },
            "aligned_telemetry": aligned_df.replace({np.nan: None}).to_dict(orient='records'),
            "corners": [c.to_dict() for c in corners],
            "corner_analyses": [ca.to_dict() for ca in corner_analyses],
            "top_opportunities": [ca.to_dict() for ca in opportunities],
            "validation_a": val_a.to_dict(),
            "validation_b": val_b.to_dict(),
            "alignment_metadata": align_meta
        }
