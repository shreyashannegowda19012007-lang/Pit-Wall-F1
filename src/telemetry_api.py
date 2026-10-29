"""
Telemetry Pipeline API Integration Layer for F1 Time-Series Engineering Platform.
Exposes standardized RESTful service endpoints for ingestion, telemetry retrieval,
feature querying, validation diagnostics, lap comparison, and dataset lineage tracking.
"""

from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
import json
import logging

from telemetry_pipeline import TelemetryPipeline, PipelineRunResult
from telemetry_storage import TelemetryStorageEngine
from telemetry_analysis_service import TelemetryAnalysisService

logger = logging.getLogger(__name__)


class TelemetryAPIService:
    """
    Service layer providing clean API endpoints for frontend and backend components.
    """

    def __init__(self):
        self.storage = TelemetryStorageEngine()
        self.pipeline = TelemetryPipeline(storage_engine=self.storage)

    def ingest_telemetry_payload(self, data_payload: Any, session_id: str, driver_id: str, lap_number: Optional[int] = None, source: str = "API") -> Dict[str, Any]:
        """
        POST /telemetry/ingest
        Ingests a telemetry payload (JSON/DataFrame) through the complete 10-stage pipeline.
        """
        res = self.pipeline.process_session_telemetry(
            raw_data=data_payload,
            session_id=session_id,
            driver_id=driver_id,
            lap_number=lap_number,
            source=source
        )
        return res.to_dict()

    def get_lap_telemetry(self, dataset_id_or_lap_id: str) -> Dict[str, Any]:
        """
        GET /telemetry/samples/{dataset_id}
        Retrieves high-volume time-series telemetry samples.
        """
        meta = self.storage.get_dataset_by_id(dataset_id_or_lap_id)
        samples_df = self.storage.get_telemetry_samples(dataset_id_or_lap_id)

        if not samples_df.empty:
            samples_df = samples_df.replace({np.nan: None})

        return {
            "dataset_id": dataset_id_or_lap_id,
            "metadata": meta,
            "sample_count": len(samples_df),
            "samples": samples_df.to_dict(orient='records') if not samples_df.empty else []
        }

    def get_validation_report(self, dataset_id: str) -> Dict[str, Any]:
        """
        GET /telemetry/validation/{dataset_id}
        Retrieves structured data quality and validation diagnostics for a dataset.
        """
        meta = self.storage.get_dataset_by_id(dataset_id)
        if not meta:
            return {"error": f"Dataset '{dataset_id}' not found."}

        with self.storage.get_connection() as conn:
            row = conn.execute("SELECT * FROM validation_results WHERE dataset_id = ?", (dataset_id,)).fetchone()
            if not row:
                return {"error": f"Validation report for dataset '{dataset_id}' not found."}

            res = dict(row)
            res["errors"] = json.loads(res.get("errors_json", "[]"))
            res["warnings"] = json.loads(res.get("warnings_json", "[]"))
            res["channel_availability"] = json.loads(res.get("channel_availability_json", "{}"))
            return res

    def compare_driver_laps(self, session: Any, target_driver: str, ref_driver: str, target_lap: Optional[int] = None, ref_lap: Optional[int] = None) -> Dict[str, Any]:
        """
        GET /telemetry/compare
        Performs distance-aligned lap comparison and time-loss attribution.
        """
        return TelemetryAnalysisService.compare_laps(
            session=session,
            target_driver=target_driver,
            ref_driver=ref_driver,
            target_lap_num=target_lap,
            ref_lap_num=ref_lap
        )

    def get_dataset_lineage(self, analysis_id_or_dataset_id: str) -> Dict[str, Any]:
        """
        GET /telemetry/lineage/{analysis_id}
        Retrieves complete data lineage trace for an analytical result.
        """
        lineage = self.storage.get_lineage(analysis_id_or_dataset_id)
        if not lineage:
            return {
                "found": False,
                "query": analysis_id_or_dataset_id,
                "message": "No explicit lineage record found. Using default pipeline version v2.4.0."
            }
        return {
            "found": True,
            "lineage": lineage
        }

    def get_tyre_degradation_distribution(self, compound: str = "MEDIUM", laps_on_tyre: float = 15.0) -> Dict[str, Any]:
        """
        GET /probabilistic/tyre_degradation
        Retrieves Bayesian posterior degradation distribution.
        """
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_tyre_degradation_distribution(compound, laps_on_tyre)

    def get_calibration_metrics(self, predictions: List[float], actuals: List[int]) -> Dict[str, Any]:
        """
        GET /probabilistic/calibration
        Computes Brier Score, Log Loss, and Reliability Diagram data.
        """
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_calibration_metrics(predictions, actuals)

    def run_bayesian_race_replay(self, session: Any, laps_df: pd.DataFrame, results_df: pd.DataFrame, target_driver: str, opponent_driver: str, step_laps: int = 5) -> Dict[str, Any]:
        """
        POST /probabilistic/bayesian_replay
        Runs deterministic lap-by-lap Bayesian replay with zero future-data leakage.
        """
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.run_bayesian_race_replay(session, laps_df, results_df, target_driver, opponent_driver, step_laps)

    def run_historical_backtest_replay(self, session: Any, laps_df: pd.DataFrame, results_df: pd.DataFrame, target_driver: str, opponent_driver: str = "HAM", step_laps: int = 5) -> Dict[str, Any]:
        """
        POST /historical/backtest_replay
        Runs full historical backtest replay evaluating decision regret and position MAE.
        """
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.run_historical_backtest_replay(session, laps_df, results_df, target_driver, opponent_driver, step_laps)

    def run_ablation_study(self, session: Any, laps_df: pd.DataFrame, results_df: pd.DataFrame, target_driver: str) -> Dict[str, Any]:
        """
        POST /historical/ablation_study
        Compares model performance across 4 ablation variants.
        """
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.run_ablation_study(session, laps_df, results_df, target_driver)

    def run_full_system_benchmark(self, session: Any = None, laps_df: Optional[pd.DataFrame] = None, results_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        POST /evaluation/benchmark
        Executes full reproducible benchmark across all 8 major subsystems.
        """
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.run_full_system_benchmark(session, laps_df, results_df)

    def get_health_status(self) -> Dict[str, Any]:
        """
        GET /healthz
        Basic liveness health check.
        """
        return {"status": "HEALTHY", "service": "Pitwall F1 Backend", "version": "v2.4.0"}

    def get_readiness_status(self) -> Dict[str, Any]:
        """
        GET /readyz
        Readiness check verifying database availability.
        """
        from database_migrations import db_manager
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
            return {"status": "READY", "database": "CONNECTED"}
        except Exception as e:
            return {"status": "NOT_READY", "database": str(e)}

    def get_observability_metrics(self) -> Dict[str, Any]:
        """
        GET /metrics
        Prometheus-compatible system operational counters and active alerts.
        """
        from observability import obs_manager
        return obs_manager.get_metrics_summary()

    def get_3d_replay_frame(self, laps_df: pd.DataFrame, track_nodes: List[Dict[str, float]], lap_number: int, progress_pct: float, primary_driver: str, comparison_driver: str) -> List[Any]:
        """
        GET /sessions/{id}/replay/3d_scene
        Retrieves authoritative 3D frame state for 20-car field.
        """
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_3d_replay_frame(laps_df, track_nodes, lap_number, progress_pct, primary_driver, comparison_driver)

    def get_unified_race_state(self, session_id: str, timestamp_s: float = 1200.0, mode: str = "REPLAY") -> Any:
        """
        GET /sessions/{id}/state
        Returns the single authoritative unified race state payload (v2.4.0).
        """
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_unified_race_state(session_id, timestamp_s, mode)

    def get_available_seasons(self) -> List[int]:
        """GET /api/v1/seasons"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_available_seasons()

    def get_season_rounds(self, season: int) -> List[Dict[str, Any]]:
        """GET /api/v1/seasons/{season}/rounds"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_season_rounds(season)

    def prepare_session(self, season: int, round_number: int, session_type: str) -> Dict[str, Any]:
        """POST /api/v1/sessions/{session_id}/prepare"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.prepare_session(season, round_number, session_type)

    def get_telemetry_corner_analysis(self, primary_driver: str = "VER", ref_driver: str = "HAM", corner_number: int = 1) -> Dict[str, Any]:
        """
        GET /sessions/{id}/telemetry/analysis
        Decomposes corner time loss into distance-aligned telemetry attributions.
        """
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_telemetry_corner_analysis(primary_driver, ref_driver, corner_number)

    def get_drs_zone_analysis(self, driver_id: str = "VER", lap_number: int = 15, zone_id: int = 1) -> Dict[str, Any]:
        """GET /sessions/{id}/drivers/{driver}/drs"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_drs_zone_analysis(driver_id, lap_number, zone_id)

    def get_ers_energy_analysis(self, driver_id: str = "VER", lap_number: int = 15) -> List[Dict[str, Any]]:
        """GET /sessions/{id}/drivers/{driver}/energy"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_ers_energy_analysis(driver_id, lap_number)

    def get_tyre_degradation_analysis(self, driver_id: str = "VER", compound: str = "MEDIUM", total_laps: int = 20) -> Dict[str, Any]:
        """
        GET /sessions/{id}/tyres/degradation
        Compares Model A (Empirical ML) vs Model B (Physics 3-Layer Thermal) degradation.
        """
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_tyre_degradation_analysis(driver_id, compound, total_laps)

    def run_full_field_simulation(self, circuit_id: str = "SPAIN", total_laps: int = 57, seed: int = 42) -> Dict[str, Any]:
        """POST /simulations/full_field"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.run_full_field_simulation(circuit_id, total_laps, seed)

    def run_full_field_monte_carlo(self, circuit_id: str = "SPAIN", total_laps: int = 57, num_sims: int = 100) -> Dict[str, Any]:
        """POST /simulations/monte_carlo"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.run_full_field_monte_carlo(circuit_id, total_laps, num_sims)

    def run_advanced_strategy_monte_carlo(self, target_driver: str = "VER", circuit_id: str = "SPAIN", total_laps: int = 66, num_sims: int = 100, objective: str = "BALANCED") -> Dict[str, Any]:
        """POST /simulations/strategy_monte_carlo"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.run_advanced_strategy_monte_carlo(target_driver, circuit_id, total_laps, num_sims, objective)

    def run_historical_backtest(self, session_id: str = "S-2024-SPAIN", driver_id: str = "VER", decision_lap: int = 20) -> Dict[str, Any]:
        """POST /backtest/run"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.run_historical_backtest(session_id, driver_id, decision_lap)

    def get_backtest_ablation_study(self, session_id: str = "S-2024-SPAIN") -> Dict[str, Any]:
        """GET /backtest/ablations"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_backtest_ablation_study(session_id)

    def predict_rl_action(self, driver_id: str = "VER", current_lap: int = 20) -> Dict[str, Any]:
        """POST /rl/predict"""
        from src.rl_config import is_rl_enabled
        if not is_rl_enabled():
            return {"error": "Forbidden", "status_code": 403, "message": "Experimental RL feature is disabled in production."}
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.predict_rl_action(driver_id, current_lap)

    def evaluate_rl_vs_baselines(self, driver_id: str = "VER") -> Dict[str, Any]:
        """POST /rl/evaluate"""
        from src.rl_config import is_rl_enabled
        if not is_rl_enabled():
            return {"error": "Forbidden", "status_code": 403, "message": "Experimental RL feature is disabled in production."}
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.evaluate_rl_vs_baselines(driver_id)

    def process_ai_engineer_query(self, query: str, primary_driver: str = "VER", ref_driver: str = "HAM") -> Dict[str, Any]:
        """POST /ai/query"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.process_ai_engineer_query(query, primary_driver, ref_driver)

    def run_mlops_pipeline(self, session_id: str = "S-2024-SPAIN") -> Dict[str, Any]:
        """POST /mlops/pipeline"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.run_mlops_pipeline(session_id)

    def get_live_operations_summary(self, session_id: str = "S-2024-SPAIN", mode: str = "LIVE") -> Dict[str, Any]:
        """GET /live/summary"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_live_operations_summary(session_id, mode)

    def get_attributed_time_loss(self, driver_id: str = "VER", ref_driver_id: str = "HAM", corner_number: int = 7) -> Dict[str, Any]:
        """GET /telemetry/time-loss"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_attributed_time_loss(driver_id, ref_driver_id, corner_number)

    def get_performance_opportunities(self, driver_id: str = "VER") -> List[Dict[str, Any]]:
        """GET /telemetry/opportunities"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_performance_opportunities(driver_id)

    def get_driver_performance_profile(self, driver_id: str = "VER", session_id: str = "S-2024-SPAIN") -> Dict[str, Any]:
        """GET /telemetry/driver-profile"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_driver_performance_profile(driver_id, session_id)

    def get_canonical_tyre_state(self, driver_id: str = "VER", compound: str = "MEDIUM", stint_lap: int = 15) -> Dict[str, Any]:
        """GET /tyres/canonical-state"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_canonical_tyre_state(driver_id, compound, stint_lap)

    def get_compound_crossover_forecast(self, compound_a: str = "MEDIUM", compound_b: str = "HARD") -> Dict[str, Any]:
        """GET /tyres/crossover"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_compound_crossover_forecast(compound_a, compound_b)

    def get_optimal_pit_window_forecast(self, stint_lap: int = 15) -> Dict[str, Any]:
        """GET /tyres/pit-window"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_optimal_pit_window_forecast(stint_lap)

    def get_canonical_strategy_state(self, session_id: str = "S-2024-SPAIN", lap: int = 22, driver_id: str = "VER") -> Dict[str, Any]:
        """GET /strategy/canonical-state"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_canonical_strategy_state(session_id, lap, driver_id)

    def analyze_undercut_overcut(self, driver_id: str = "VER", rival_driver_id: str = "HAM", gap_s: float = 2.84, base_pace_s: float = 82.0, rival_base_pace_s: float = None) -> Dict[str, Any]:
        """POST /strategy/undercut-overcut"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.analyze_undercut_overcut(driver_id, rival_driver_id, gap_s, base_pace_s, rival_base_pace_s)

    def evaluate_authoritative_strategy(self, session_id: str = "S-2024-SPAIN", lap: int = 22, driver_id: str = "VER", rival_driver_id: str = "HAM") -> Dict[str, Any]:
        """POST /strategy/evaluate"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.evaluate_authoritative_strategy(session_id, lap, driver_id, rival_driver_id)

    def get_20_car_field_state(self, session_id: str = "S-2024-SPAIN", lap: int = 22) -> List[Dict[str, Any]]:
        """GET /field/state"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_20_car_field_state(session_id, lap)

    def detect_track_battles_and_drs_trains(self, lap: int = 22) -> List[Dict[str, Any]]:
        """GET /field/battles"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.detect_track_battles_and_drs_trains(lap)

    def simulate_full_field_monte_carlo(self, primary_driver_id: str = "VER") -> Dict[str, Any]:
        """GET /field/distributions"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.simulate_full_field_monte_carlo(primary_driver_id)

    def get_ml_model_catalogue(self) -> List[Dict[str, Any]]:
        """GET /ml/models"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_ml_model_catalogue()

    def predict_quantile_lap_time(self, driver_id: str = "VER", lap_number: int = 23, base_pace_s: float = 81.240, tyre_age_laps: int = 15, compound_str: str = "SOFT") -> Dict[str, Any]:
        """POST /ml/predict/lap"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.predict_quantile_lap_time(driver_id, lap_number, base_pace_s, tyre_age_laps, compound_str)

    def explain_lap_time_prediction(self, driver_id: str = "VER", lap_number: int = 23, base_pace_s: float = 81.240, tyre_age_laps: int = 15, compound_str: str = "SOFT") -> Dict[str, Any]:
        """POST /ml/explain"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.explain_lap_time_prediction(driver_id, lap_number, base_pace_s, tyre_age_laps, compound_str)

    def predict_calibrated_overtake_probability(self, attacker_id: str = "NOR", defender_id: str = "VER", gap_s: float = 0.85) -> Dict[str, Any]:
        """POST /ml/predict/overtake"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.predict_calibrated_overtake_probability(attacker_id, defender_id, gap_s)

    def start_historical_replay(self, season: int = 2024, round_num: int = 9, session_name: str = "R") -> Dict[str, Any]:
        """POST /replay/start"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.start_historical_replay(season, round_num, session_name)

    def evaluate_historical_session(self, season: int = 2024, round_num: int = 9, driver_id: str = "VER") -> Dict[str, Any]:
        """GET /benchmark/summary"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.evaluate_historical_session(season, round_num, driver_id)

    def get_live_system_health(self) -> Dict[str, Any]:
        """GET /live/health"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_live_system_health()

    def publish_timing_update(self, driver_id: str = "VER", lap: int = 22, lap_time_s: float = 81.240) -> Dict[str, Any]:
        """POST /live/timing"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.publish_timing_update(driver_id, lap, lap_time_s)

    def get_circuit_spatial_metadata(self, circuit_id: str = "SPAIN-2024") -> Dict[str, Any]:
        """GET /spatial/circuit"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_circuit_spatial_metadata(circuit_id)

    def get_spatial_field_positions(self, session_id: str = "S-2024-SPAIN", lap: int = 22) -> List[Dict[str, Any]]:
        """GET /spatial/field"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_spatial_field_positions(session_id, lap)

    def get_cockpit_pov_camera_feed(self, driver_id: str = "VER", lap: int = 22) -> Dict[str, Any]:
        """GET /spatial/cockpit"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_cockpit_pov_camera_feed(driver_id, lap)

    def prepare_session(self, season: int = 2024, round_num: int = 9, session_type: str = "R") -> Dict[str, Any]:
        """POST /session/prepare"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.prepare_session(season, round_num, session_type)

    def get_session_manifest(self, session_id: str = "S-2024-R09-R") -> Dict[str, Any]:
        """GET /session/manifest"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_session_manifest(session_id)

    def get_cache_stats(self) -> Dict[str, Any]:
        """GET /cache/stats"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_cache_stats()

    def get_system_health(self) -> Dict[str, Any]:
        """GET /health"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.get_system_health()

    def create_system_backup(self) -> Dict[str, Any]:
        """POST /backup/create"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.create_system_backup()

    def validate_system_integration(self) -> Dict[str, Any]:
        """GET /system/integration-report"""
        from probabilistic_service import ProbabilisticService
        return ProbabilisticService.validate_system_integration()


# Global API Service Singleton
api_service = TelemetryAPIService()
