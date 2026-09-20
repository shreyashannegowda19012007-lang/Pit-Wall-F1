"""
Historical Context Retrieval Engine for F1 AI Performance Engineer.
Retrieves and ranks relevant contextual telemetry data from current session,
previous laps, best lap, teammate, compound stints, and historical sessions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np


@dataclass
class ContextRelevanceScore:
    """Scored historical comparison context."""
    comparison_id: str
    relevance_score: float         # 0.0 to 100.0 %
    matching_factors: List[str]
    differences: List[str]
    reason_for_selection: str
    target_lap_meta: Dict[str, Any]


class HistoricalRetrievalEngine:
    """
    Retrieves and ranks historical telemetry context without inventing fictional history.
    """

    @classmethod
    def score_context_relevance(cls, candidate_meta: Dict[str, Any], ref_meta: Dict[str, Any]) -> ContextRelevanceScore:
        """
        Ranks historical comparison relevance based on circuit, driver, compound, age, stint, and session matching.
        """
        score = 50.0
        matching = []
        differences = []

        if candidate_meta.get("session_id") == ref_meta.get("session_id"):
            score += 20.0
            matching.append("Same Session")
        else:
            differences.append("Different Session")

        if candidate_meta.get("driver_id") == ref_meta.get("driver_id"):
            score += 15.0
            matching.append("Same Driver")
        else:
            differences.append(f"Different Driver ({candidate_meta.get('driver_id')} vs {ref_meta.get('driver_id')})")

        if candidate_meta.get("compound") == ref_meta.get("compound"):
            score += 10.0
            matching.append(f"Same Compound ({candidate_meta.get('compound')})")
        else:
            differences.append(f"Different Compound ({candidate_meta.get('compound')} vs {ref_meta.get('compound')})")

        age_diff = abs(candidate_meta.get("tyre_age", 0) - ref_meta.get("tyre_age", 0))
        if age_diff <= 3:
            score += 5.0
            matching.append(f"Similar Tyre Age (Δ{age_diff} laps)")
        else:
            differences.append(f"Tyre Age Difference ({candidate_meta.get('tyre_age')} vs {ref_meta.get('tyre_age')} laps)")

        score = min(100.0, max(0.0, score))
        comp_id = f"COMP-{candidate_meta.get('driver_id')}-L{candidate_meta.get('lap_number')}"
        reason = f"Selected based on {', '.join(matching)}" if matching else "Selected as fallback comparison."

        return ContextRelevanceScore(
            comparison_id=comp_id,
            relevance_score=round(score, 1),
            matching_factors=matching,
            differences=differences,
            reason_for_selection=reason,
            target_lap_meta=candidate_meta
        )

    @classmethod
    def get_current_lap_context(cls, laps_df: pd.DataFrame, driver_id: str, lap_num: Optional[int] = None) -> Dict[str, Any]:
        """Retrieves active driver's current or specified lap record."""
        if laps_df.empty:
            return {"found": False, "message": "No lap telemetry available."}

        driver_laps = laps_df[laps_df['Driver'] == driver_id].copy()
        if driver_laps.empty:
            return {"found": False, "message": f"No laps found for driver {driver_id}."}

        if lap_num is not None:
            match = driver_laps[driver_laps['LapNumber'] == lap_num]
            if not match.empty:
                lap = match.iloc[0]
            else:
                lap = driver_laps.iloc[-1]
        else:
            # Default to last completed accurate lap
            acc_laps = driver_laps[driver_laps['IsAccurate'] == True]
            lap = acc_laps.iloc[-1] if not acc_laps.empty else driver_laps.iloc[-1]

        lap_time = lap['LapTime'].total_seconds() if pd.notna(lap.get('LapTime')) else 0.0

        return {
            "found": True,
            "driver_id": driver_id,
            "lap_number": int(lap.get('LapNumber', 0)),
            "lap_time_s": round(lap_time, 3),
            "compound": str(lap.get('Compound', 'UNKNOWN')),
            "tyre_age": int(lap.get('TyreLife', 0)) if pd.notna(lap.get('TyreLife')) else 0,
            "stint": int(lap.get('Stint', 1)) if pd.notna(lap.get('Stint')) else 1,
            "sector_1_s": round(lap['Sector1Time'].total_seconds(), 3) if pd.notna(lap.get('Sector1Time')) else None,
            "sector_2_s": round(lap['Sector2Time'].total_seconds(), 3) if pd.notna(lap.get('Sector2Time')) else None,
            "sector_3_s": round(lap['Sector3Time'].total_seconds(), 3) if pd.notna(lap.get('Sector3Time')) else None,
            "is_accurate": bool(lap.get('IsAccurate', True))
        }

    @classmethod
    def get_previous_laps_context(cls, laps_df: pd.DataFrame, driver_id: str, current_lap_num: int, count: int = 5) -> List[Dict[str, Any]]:
        """Retrieves driver's previous N laps prior to current lap."""
        if laps_df.empty:
            return []

        driver_laps = laps_df[laps_df['Driver'] == driver_id].copy()
        if driver_laps.empty:
            return []

        prev = driver_laps[(driver_laps['LapNumber'] < current_lap_num) & (driver_laps['IsAccurate'] == True)]
        prev = prev.sort_values(by='LapNumber', ascending=False).head(count)

        res = []
        for _, lap in prev.iterrows():
            lap_time = lap['LapTime'].total_seconds() if pd.notna(lap.get('LapTime')) else 0.0
            res.append({
                "driver_id": driver_id,
                "lap_number": int(lap['LapNumber']),
                "lap_time_s": round(lap_time, 3),
                "compound": str(lap.get('Compound', 'UNKNOWN')),
                "tyre_age": int(lap.get('TyreLife', 0)) if pd.notna(lap.get('TyreLife')) else 0,
                "stint": int(lap.get('Stint', 1)) if pd.notna(lap.get('Stint')) else 1
            })

        return sorted(res, key=lambda x: x['lap_number'])

    @classmethod
    def get_best_lap_context(cls, laps_df: pd.DataFrame, driver_id: str) -> Dict[str, Any]:
        """Retrieves active driver's overall personal best lap in session."""
        if laps_df.empty:
            return {"found": False}

        driver_laps = laps_df[(laps_df['Driver'] == driver_id) & (laps_df['IsAccurate'] == True)].copy()
        if driver_laps.empty:
            return {"found": False}

        best_lap = driver_laps.sort_values(by='LapTime').iloc[0]
        lap_time = best_lap['LapTime'].total_seconds() if pd.notna(best_lap.get('LapTime')) else 0.0

        return {
            "found": True,
            "driver_id": driver_id,
            "lap_number": int(best_lap['LapNumber']),
            "lap_time_s": round(lap_time, 3),
            "compound": str(best_lap.get('Compound', 'UNKNOWN')),
            "tyre_age": int(best_lap.get('TyreLife', 0)) if pd.notna(best_lap.get('TyreLife')) else 0,
            "stint": int(best_lap.get('Stint', 1)) if pd.notna(best_lap.get('Stint')) else 1
        }

    @classmethod
    def get_teammate_context(cls, laps_df: pd.DataFrame, target_driver: str, results_df: pd.DataFrame) -> Dict[str, Any]:
        """Identifies and retrieves best lap context for target driver's teammate."""
        if laps_df.empty or results_df.empty:
            return {"found": False, "message": "Results dataset empty."}

        # Find target team
        target_rows = results_df[results_df['Abbreviation'] == target_driver]
        if target_rows.empty:
            return {"found": False, "message": f"Driver {target_driver} not found in results."}

        target_team = target_rows.iloc[0].get('TeamName')
        teammates = results_df[(results_df['TeamName'] == target_team) & (results_df['Abbreviation'] != target_driver)]

        if teammates.empty:
            # Fallback to 2nd driver in results if same team not explicit
            other_drivers = results_df[results_df['Abbreviation'] != target_driver]
            if other_drivers.empty:
                return {"found": False, "message": "No second driver available for comparison."}
            tm_code = other_drivers.iloc[0]['Abbreviation']
        else:
            tm_code = teammates.iloc[0]['Abbreviation']

        best_tm = cls.get_best_lap_context(laps_df, tm_code)
        best_tm["is_teammate"] = True
        return best_tm

