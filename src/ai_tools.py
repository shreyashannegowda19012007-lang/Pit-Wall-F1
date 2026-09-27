"""
Controlled AI Tool & Function Access Layer for F1 Performance Engineering Agent.
Provides clean function interfaces for retrieving current lap, previous laps, teammate context,
corner analysis, tyre degradation, weather context, and evidence bundles.
Enforces strict security boundaries to prevent raw database injection or unconstrained execution.
"""

from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np

from historical_retrieval import HistoricalRetrievalEngine
from telemetry_analysis_service import TelemetryAnalysisService
from evidence_engine import EvidenceEngine, StructuredEvidenceResponse


class AIToolRegistry:
    """
    Registry of controlled tool calls exposed to the AI Engineer explanation engine.
    """

    @staticmethod
    def get_current_lap(laps_df: pd.DataFrame, driver_id: str, lap_number: Optional[int] = None) -> Dict[str, Any]:
        """Tool: Retrieves current active lap context for target driver."""
        return HistoricalRetrievalEngine.get_current_lap_context(laps_df, driver_id, lap_number)

    @staticmethod
    def get_previous_laps(laps_df: pd.DataFrame, driver_id: str, current_lap: int, count: int = 5) -> List[Dict[str, Any]]:
        """Tool: Retrieves telemetry metadata for previous N laps."""
        return HistoricalRetrievalEngine.get_previous_laps_context(laps_df, driver_id, current_lap, count)

    @staticmethod
    def get_best_lap(laps_df: pd.DataFrame, driver_id: str) -> Dict[str, Any]:
        """Tool: Retrieves best personal lap context in session."""
        return HistoricalRetrievalEngine.get_best_lap_context(laps_df, driver_id)

    @staticmethod
    def get_teammate_context(laps_df: pd.DataFrame, driver_id: str, results_df: pd.DataFrame) -> Dict[str, Any]:
        """Tool: Retrieves teammate best lap context for benchmark comparison."""
        return HistoricalRetrievalEngine.get_teammate_context(laps_df, driver_id, results_df)

    @staticmethod
    def get_corner_analysis(session: Any, driver_id: str, ref_driver: str) -> Dict[str, Any]:
        """Tool: Retrieves distance-aligned corner time loss and kinematic evidence."""
        return TelemetryAnalysisService.compare_laps(session, driver_id, ref_driver)

    @staticmethod
    def get_tyre_context(laps_df: pd.DataFrame, driver_id: str) -> Dict[str, Any]:
        """Tool: Retrieves stint degradation slope and tyre age context."""
        from trend_analysis import TimeSeriesTrendEngine
        return TimeSeriesTrendEngine.calculate_stint_pace_degradation(laps_df, driver_id)

    @staticmethod
    def get_weather_context(session: Any) -> Dict[str, Any]:
        """Tool: Retrieves weather telemetry if available."""
        if session is not None and hasattr(session, 'weather_data') and session.weather_data is not None and not session.weather_data.empty:
            w = session.weather_data.iloc[-1]
            return {
                "available": True,
                "air_temperature_c": float(w.get('AirTemp', 0.0)) if pd.notna(w.get('AirTemp')) else None,
                "track_temperature_c": float(w.get('TrackTemp', 0.0)) if pd.notna(w.get('TrackTemp')) else None,
                "humidity_pct": float(w.get('Humidity', 0.0)) if pd.notna(w.get('Humidity')) else None,
                "rainfall": bool(w.get('Rainfall', False)) if pd.notna(w.get('Rainfall')) else False,
                "wind_speed_ms": float(w.get('WindSpeed', 0.0)) if pd.notna(w.get('WindSpeed')) else None,
                "wind_direction_deg": float(w.get('WindDirection', 0.0)) if pd.notna(w.get('WindDirection')) else None
            }
        return {"available": False, "message": "Weather telemetry data is unavailable for this session."}

    @staticmethod
    def get_evidence_bundle(question: str, session: Any, laps_df: pd.DataFrame, results_df: pd.DataFrame, target_driver: str, ref_driver: str) -> Dict[str, Any]:
        """Tool: Retrieves full structured evidence bundle for engineering query."""
        bundle = EvidenceEngine.resolve_evidence(question=question, session=session, laps_df=laps_df, target_driver=target_driver, ref_driver=ref_driver)
        return bundle.to_dict()

    @staticmethod
    def get_current_decision(race_state: Any, mc_outcomes: List[Any], objective: str = "MAX_PODIUM_PROBABILITY") -> Dict[str, Any]:
        """Tool: Retrieves authoritative StructuredDecision payload from Decision Engine."""
        from decision_engine import DecisionEngine
        dec = DecisionEngine.evaluate(race_state, None, mc_outcomes, objective=objective)
        return dec.to_dict()

    @staticmethod
    def get_decision_history(lap_a: int, lap_b: int) -> Dict[str, Any]:
        """Tool: Compares decision snapshots at lap A vs lap B to explain why recommendation changed."""
        from decision_history import global_decision_audit
        return global_decision_audit.compare_decisions(lap_a, lap_b)
