# PITWALL F1 COMPLETE TECHNICAL DOCUMENTATION
**Generated:** 2026-09-13 17:16:07
**Status:** Official Engineering Specification

---

## 2. EXECUTIVE SUMMARY
The Pitwall F1 project is an advanced, telemetry-driven race strategy and visualization dashboard. It ingests FastF1 telemetry data, performs spatial intelligence modeling, evaluates race strategies using Monte Carlo simulations, calculates time loss attribution through differential telemetry math, and presents results in a Streamlit-based UI. The system integrates machine learning for overtake predictions and features an AI-driven 'JARVIS' assistant for querying race parameters. After extensive remediation, it successfully utilizes real telemetry rather than mocked procedural calculations.

---

## 3. PROJECT PURPOSE
To provide Formula 1 racing engineers and strategists with real-time and historical race data analysis, stochastic strategy modeling, and granular spatial telemetry diagnostics in a unified Command Center interface.

---

## 4. SYSTEM ARCHITECTURE
### Data Flow Architecture
```mermaid
graph TD
    A[User / Streamlit UI] --> B[Pitwall UI (`src/pitwall_ui.py`)]
    B --> C[Telemetry API / Probabilistic Service]
    C --> D[Data Ingestion Engine (FastF1 `src/data_ingestion.py`)]
    C --> E[Strategy & Monte Carlo Engine (`src/monte_carlo_engine.py`)]
    C --> F[Telemetry Performance Lab (`src/telemetry_performance_lab.py`)]
    E --> G[Production ML Engine (`src/production_ml_engine.py`)]
    G --> H[Model Loader (`src/model_loader.py`)]
```

### Layers
- **Application Entrypoint:** `src/pitwall_ui.py` (Streamlit loop)
- **UI Layer:** `src/pitwall_ui.py`, `src/ui_elements.py`
- **Orchestration Layer:** `src/probabilistic_service.py`, `src/telemetry_api.py`
- **Data Ingestion Layer:** `src/data_ingestion.py` (FastF1 Cache, FIA APIs)
- **Intelligence Layer:** 
  - `src/spatial_intelligence_engine.py` (3D Mapping)
  - `src/telemetry_performance_lab.py` (Driver Differentials)
  - `src/unified_tyre_intelligence.py` (Degradation Models)
- **Simulation Layer:** `src/monte_carlo_engine.py`, `src/race_simulator.py`
- **ML Layer:** `src/production_ml_engine.py`, `src/model_loader.py`
- **Persistence/Cache Layer:** Local `fastf1` file cache in `track_cache` and `%APPDATA%`


---

## 5. REPOSITORY STRUCTURE
The project resides primarily within the `src/` directory, supported by a `scripts/` directory for offline jobs like ML training.
```
D:/Pitwall F1 project/
├── src/                  # Core Application logic
├── scripts/              # Offline tools (e.g., train_overtake_model.py)
├── models/               # Serialized ML Models (e.g., model.pkl)
├── track_cache/          # FastF1 offline track metadata
└── docs/                 # Auto-generated documentation
```

---

## 6. COMPLETE FEATURE CATALOGUE

### Spatial Intelligence Engine
- **Purpose:** Renders the 3D location of all 20 cars.
- **User capability:** Views real-time track map and car gaps.
- **Inputs:** FastF1 X, Y, Z coordinates.
- **Data source:** FastF1 `lap.get_telemetry()`.
- **Processing:** Extracts telemetry at midpoint, computes dx/dy for heading, and maps coordinates.
- **Models:** None (Direct telemetry).
- **Files:** `spatial_intelligence_engine.py`
- **Status:** PRODUCTION / FUNCTIONAL (Refactored from sine/cosine mocks).

### Monte Carlo Strategy Simulator
- **Purpose:** Calculates win probability distributions for pitstop choices.
- **Inputs:** Target compound, pit lap, current grid gaps.
- **Data source:** FastF1 lap time deltas and positions.
- **Processing:** Vectorized numpy simulation sampling from normal/lognormal distributions.
- **Files:** `monte_carlo_engine.py`, `race_simulator.py`
- **Status:** PRODUCTION / FUNCTIONAL

### Telemetry Performance Lab
- **Purpose:** Attributes corner time loss.
- **Processing:** Aligns two drivers' arrays by distance, filters by corner bounds, computes deltas for VMin and Peak Brake.
- **Files:** `telemetry_performance_lab.py`
- **Status:** PRODUCTION / FUNCTIONAL

### Overtake ML Engine
- **Purpose:** Predicts success probability of an overtake.
- **Processing:** Loads `model.pkl` and infers against gap, DRS, and speed delta.
- **Models:** RandomForestClassifier
- **Files:** `production_ml_engine.py`, `model_loader.py`
- **Status:** PRODUCTION / FUNCTIONAL

### JARVIS AI Intelligence
- **Purpose:** AI assistant for pitwall insights.
- **Processing:** Intent routing via Regex/heuristics to internal engine calls.
- **Files:** `jarvis_engineering_insights.py`
- **Status:** EXPERIMENTAL / PARTIALLY FUNCTIONAL

### Unified Tyre Intelligence
- **Purpose:** Tyre degradation forecasting.
- **Processing:** Calculates slope of empirical lap times using np.polyfit.
- **Status:** PARTIALLY FUNCTIONAL (Thermal model is heuristic/synthetic)



## 7. DATA ARCHITECTURE & 8. FASTF1 INGESTION
- **Provider:** FastF1 API
- **Pipeline:** `data_ingestion.py` -> `fetch_session_data(year, event, session_type)`
- **Cache:** Stored locally in `track_cache` to avoid repeated FIA API hits.
- **Extracted Fields:** Distance, X, Y, Z, Speed, Throttle, Brake, nGear, DRS, Time, LapNumber, Position.

## 9. TELEMETRY ENGINEERING
- **Time Loss Attribution:** Extracts arrays for Driver A and B, subsets by Corner Distance bounds, calculates `Speed.min()`, `Brake.max()`, and overall time integration over distance. Implementation in `telemetry_performance_lab.py`.

## 10. STRATEGY ENGINE & 11. MONTE CARLO
- **Simulations:** Default 250 iterations (vectorized).
- **Stochastic Noise:** Uses `np.random.default_rng(seed)` for Thread-Safe Normal (Pace Noise) and Lognormal (Pit Stop Duration Noise).
- **Ranking:** Strategies are ranked by "MAX_WIN_PROBABILITY".

## 12. MACHINE LEARNING & 13. REINFORCEMENT LEARNING
- **Active ML Model:** `models/overtake_probability/model.pkl` (RandomForestClassifier).
- **Training Pipeline:** `scripts/train_overtake_model.py` generates synthetic overtake data (delta v, DRS state) and trains the scikit-learn model.
- **RL System:** Mentioned in `f1_strategy_env.py` and `rl_strategy_agent.py` but currently **EXPERIMENTAL/ORPHANED** from the main UI orchestration loop.

## 18. WHAT-IF SCENARIO ENGINE
- **Control:** Sidebar inputs for Compound and Pit Lap.
- **Backend Response:** Injects a custom `StrategyPlan` into the Monte Carlo queue. Overrides the `st.session_state` and invokes `mc_engine.simulate_strategy_vectorized()`. Confirmed functional.

## 21. DATA PROVENANCE
- **REAL SOURCE DATA:** FastF1 Lap Times, X/Y/Z Telemetry, Position Gaps.
- **DERIVED FROM REAL DATA:** Corner Min Speeds, Brake Points.
- **ML OUTPUT:** Overtake Probability.
- **STATISTICAL CALCULATION:** Win Probability, Expected Finish Position.
- **SYNTHETIC/HEURISTIC:** Tyre Core/Bulk Temperatures.
- **UNAVAILABLE:** Compound Crossover Lap.

## 27. RUN INSTRUCTIONS
- **Launch Command:** `python -m streamlit run src/pitwall_ui.py`
- **Environment:** Requires `numpy`, `pandas`, `scikit-learn`, `fastf1`, `streamlit`. Python 3.9+ recommended.

## 29. COMPLETE FILE/FUNCTION REFERENCE
### `advanced_monte_carlo.py`
- **Path:** `D:\Pitwall F1 project\src\advanced_monte_carlo.py`
- **Classes:** StrategyCandidate, StrategyMonteCarloResult, AutomatedCandidateGenerator, AdvancedMonteCarloStrategyEngine


### `ai_engineer_qa.py`
- **Path:** `D:\Pitwall F1 project\src\ai_engineer_qa.py`
- **Classes:** AIEngineerQAEngine


### `ai_engineer_service.py`
- **Path:** `D:\Pitwall F1 project\src\ai_engineer_service.py`
- **Classes:** AIEngineerService


### `ai_evaluator.py`
- **Path:** `D:\Pitwall F1 project\src\ai_evaluator.py`
- **Classes:** AIEngineerEvaluator


### `ai_tools.py`
- **Path:** `D:\Pitwall F1 project\src\ai_tools.py`
- **Classes:** AIToolRegistry


### `app.py`
- **Path:** `D:\Pitwall F1 project\src\app.py`
- **Functions:** start_live_worker, stop_live_worker, _main_execution_loop, main


### `authoritative_strategy_engine.py`
- **Path:** `D:\Pitwall F1 project\src\authoritative_strategy_engine.py`


### `bayesian_replay.py`
- **Path:** `D:\Pitwall F1 project\src\bayesian_replay.py`
- **Classes:** BayesianRaceReplayEngine


### `bayesian_state.py`
- **Path:** `D:\Pitwall F1 project\src\bayesian_state.py`
- **Classes:** BayesianRaceState


### `bayesian_tyre_model.py`
- **Path:** `D:\Pitwall F1 project\src\bayesian_tyre_model.py`
- **Classes:** AdvancedTyreDegradationModel
- **Functions:** calculate_degradation_slope


### `bayesian_updating.py`
- **Path:** `D:\Pitwall F1 project\src\bayesian_updating.py`
- **Classes:** BayesianParameter, ConjugateBayesianEstimator


### `benchmark_runner.py`
- **Path:** `D:\Pitwall F1 project\src\benchmark_runner.py`
- **Classes:** BenchmarkRunner


### `cache_service.py`
- **Path:** `D:\Pitwall F1 project\src\cache_service.py`
- **Classes:** VersionAwareCache


### `calibration.py`
- **Path:** `D:\Pitwall F1 project\src\calibration.py`
- **Classes:** ProbabilityCalibrationEngine


### `config.py`
- **Path:** `D:\Pitwall F1 project\src\config.py`
- **Functions:** ensure_directories


### `config_settings.py`
- **Path:** `D:\Pitwall F1 project\src\config_settings.py`
- **Classes:** AppConfig


### `corner_detection.py`
- **Path:** `D:\Pitwall F1 project\src\corner_detection.py`
- **Classes:** CornerWindow
- **Functions:** detect_corners_from_telemetry


### `database_migrations.py`
- **Path:** `D:\Pitwall F1 project\src\database_migrations.py`
- **Classes:** DatabaseManager


### `data_ingestion.py`
- **Path:** `D:\Pitwall F1 project\src\data_ingestion.py`
- **Functions:** safe_extract, get_calendar, fetch_session_data, fetch_live_session_data, get_driver_telemetry, get_auto_live_session


### `data_providers.py`
- **Path:** `D:\Pitwall F1 project\src\data_providers.py`
- **Classes:** BaseDataProvider, FastF1Provider, OpenF1Provider
- **Functions:** get_provider


### `data_sanity.py`
- **Path:** `D:\Pitwall F1 project\src\data_sanity.py`
- **Classes:** SanityViolation, DataSanityEngine


### `decision_architecture.py`
- **Path:** `D:\Pitwall F1 project\src\decision_architecture.py`
- **Classes:** DriverContext, RaceContext, StrategyRecommendation, DecisionEngine, JarvisEvidenceEngine, DecisionArchitectureOrchestrator


### `decision_engine.py`
- **Path:** `D:\Pitwall F1 project\src\decision_engine.py`
- **Classes:** DecisionConstraint, DecisionAlternative, StructuredDecision, DecisionEngine


### `decision_history.py`
- **Path:** `D:\Pitwall F1 project\src\decision_history.py`
- **Classes:** HumanOverrideRecord, DecisionAuditTrail


### `decision_validation.py`
- **Path:** `D:\Pitwall F1 project\src\decision_validation.py`
- **Classes:** DecisionValidationEngine


### `energy_analysis.py`
- **Path:** `D:\Pitwall F1 project\src\energy_analysis.py`
- **Classes:** SourceClassification, EnergyDataContract, DRSZoneAnalysisResult, DRSAnalysisEngine, ERSBatteryModelEngine


### `evidence_engine.py`
- **Path:** `D:\Pitwall F1 project\src\evidence_engine.py`
- **Classes:** EvidenceItem, StructuredEvidenceResponse, EvidenceEngine


### `f1_strategy_env.py`
- **Path:** `D:\Pitwall F1 project\src\f1_strategy_env.py`
- **Classes:** F1StrategyEnv


### `full_field_intelligence.py`
- **Path:** `D:\Pitwall F1 project\src\full_field_intelligence.py`
- **Classes:** CanonicalDriverAgent, CarState, BattleState, FullFieldDriverState, FullFieldRaceIntelligenceEngine


### `full_field_simulator.py`
- **Path:** `D:\Pitwall F1 project\src\full_field_simulator.py`
- **Classes:** DriverSimState, RaceSimulationConfig, FullFieldSimulationResult, FullFieldRaceSimulator


### `head_to_head_ai.py`
- **Path:** `D:\Pitwall F1 project\src\head_to_head_ai.py`
- **Functions:** compute_pace_delta, compute_tyre_degradation, compute_telemetry_traits, generate_h2h_report, render_performance_evidence


### `historical_ablation.py`
- **Path:** `D:\Pitwall F1 project\src\historical_ablation.py`
- **Classes:** AblationStudyEngine


### `historical_backtest.py`
- **Path:** `D:\Pitwall F1 project\src\historical_backtest.py`
- **Functions:** _baseline_strategy_time, _exact_optimal_pit, _rl_episode, backtest_race, main, _make_plots


### `historical_leakage_guard.py`
- **Path:** `D:\Pitwall F1 project\src\historical_leakage_guard.py`
- **Classes:** DataLeakageError, HistoricalInformationFilter


### `historical_metrics.py`
- **Path:** `D:\Pitwall F1 project\src\historical_metrics.py`
- **Classes:** HistoricalReplayMetrics


### `historical_replay_engine.py`
- **Path:** `D:\Pitwall F1 project\src\historical_replay_engine.py`
- **Classes:** HistoricalReplayEngine


### `historical_replay_evaluator.py`
- **Path:** `D:\Pitwall F1 project\src\historical_replay_evaluator.py`
- **Classes:** FutureDataGuard, HistoricalReplaySession, DecisionCheckpoint, HistoricalEvaluationReport, HistoricalReplayEngine


### `historical_retrieval.py`
- **Path:** `D:\Pitwall F1 project\src\historical_retrieval.py`
- **Classes:** ContextRelevanceScore, HistoricalRetrievalEngine


### `jarvis_engineering_insights.py`
- **Path:** `D:\Pitwall F1 project\src\jarvis_engineering_insights.py`
- **Classes:** JarvisEngineeringInsightsEngine


### `job_queue.py`
- **Path:** `D:\Pitwall F1 project\src\job_queue.py`
- **Classes:** JobQueueManager


### `lap_alignment.py`
- **Path:** `D:\Pitwall F1 project\src\lap_alignment.py`
- **Functions:** align_laps_by_distance


### `live_stream_worker.py`
- **Path:** `D:\Pitwall F1 project\src\live_stream_worker.py`
- **Functions:** get_oauth_token, on_connect, atomic_write_json, on_message, on_disconnect, start_worker


### `logger.py`
- **Path:** `D:\Pitwall F1 project\src\logger.py`
- **Classes:** JSONFormatter
- **Functions:** sanitize_payload, get_logger


### `mlops_pipeline.py`
- **Path:** `D:\Pitwall F1 project\src\mlops_pipeline.py`
- **Classes:** DatasetVersion, ModelArtifact, DriftMetrics, DatasetRegistry, ModelRegistry, DriftDetector, ProductionMLOpsEngine


### `model_loader.py`
- **Path:** `D:\Pitwall F1 project\src\model_loader.py`
- **Classes:** ModelLoader
- **Functions:** get_loader


### `monte_carlo_engine.py`
- **Path:** `D:\Pitwall F1 project\src\monte_carlo_engine.py`
- **Classes:** StochasticSimulationOutcome, MonteCarloRaceEngine


### `observability.py`
- **Path:** `D:\Pitwall F1 project\src\observability.py`
- **Classes:** ObservabilityManager


### `panel_registry.py`
- **Path:** `D:\Pitwall F1 project\src\panel_registry.py`
- **Classes:** LayoutPreset, PanelDefinition, PanelRegistry


### `physics_solver.py`
- **Path:** `D:\Pitwall F1 project\src\physics_solver.py`
- **Functions:** render_micro_telemetry_stack, render_pacing_scatter, render_gap_to_leader, render_custom_lap_deficit, render_telemetry_comparison


### `pitwall_console.py`
- **Path:** `D:\Pitwall F1 project\src\pitwall_console.py`
- **Classes:** PitWallConsoleOrchestrator


### `pitwall_ui.py`
- **Path:** `D:\Pitwall F1 project\src\pitwall_ui.py`
- **Functions:** get_tyre_html, format_sector_html, render_session_header, render_engine_component_matrix, render_pitwall_console_header, render_timing_tower, render_track_limits, render_race_control_log, render_driver_time_loss_debrief, render_pipeline_lineage_hud, render_ai_engineer_workstation, render_probabilistic_uncertainty_hud, render_bayesian_updating_hud, render_decision_engine_panel, render_historical_replay_dashboard, render_evaluation_benchmark_dashboard, render_3d_circuit_replay_dashboard, render_unified_realtime_timing_tower, render_universal_session_selector, render_advanced_telemetry_lab, render_drs_ers_energy_dashboard, render_advanced_tyre_degradation_dashboard, render_full_field_simulation_dashboard, render_advanced_monte_carlo_strategy_dashboard, render_historical_backtest_evaluation_dashboard, render_rl_strategy_agent_dashboard, render_ai_engineer_jarvis_console, render_mlops_pipeline_dashboard, render_realtime_live_operations_console, render_driver_performance_intelligence_lab, render_unified_tyre_intelligence_dashboard, render_authoritative_strategy_command_center, render_full_field_intelligence_dashboard, render_production_ml_model_lab, render_historical_replay_scientific_evaluation_dashboard, render_realtime_live_infrastructure_health_console, render_3d_circuit_spatial_intelligence_dashboard, render_production_data_platform_performance_dashboard, render_production_hardening_security_dashboard, render_system_wide_integration_verification_dashboard, render_master_pitwall_console, render_timing_tower_v2, render_race_control_log_v2, render_weather_panel, render_tyre_panel


### `probabilistic_model.py`
- **Path:** `D:\Pitwall F1 project\src\probabilistic_model.py`
- **Classes:** UncertaintyType, IntervalType, ProbabilisticPrediction
- **Functions:** validate_probability_vector


### `probabilistic_service.py`
- **Path:** `D:\Pitwall F1 project\src\probabilistic_service.py`
- **Classes:** ProbabilisticService


### `production_data_platform.py`
- **Path:** `D:\Pitwall F1 project\src\production_data_platform.py`
- **Classes:** SessionManifest, CacheStats, CircuitBreakerStatus, CircuitBreaker, ProductionCacheManager, SessionPreparationManager


### `production_hardening_engine.py`
- **Path:** `D:\Pitwall F1 project\src\production_hardening_engine.py`
- **Classes:** SecurityAuditReport, HealthCheckResult, BackupManifest, InputSanitizer, RateLimiter, AIBoundaryGuard, FaultToleranceEngine, BackupRestoreManager, SystemHealthService


### `production_ml_engine.py`
- **Path:** `D:\Pitwall F1 project\src\production_ml_engine.py`
- **Classes:** ModelCard, QuantileLapTimePrediction, SHAPExplanation, ProductionMLEngine


### `race_simulator.py`
- **Path:** `D:\Pitwall F1 project\src\race_simulator.py`
- **Classes:** RaceState, DriverState, StrategyOption, SimulationResult, RaceSimulator
- **Functions:** active_inference_strategy_suggestor, render_simulator_ui, render_decision_engine_panel


### `race_state.py`
- **Path:** `D:\Pitwall F1 project\src\race_state.py`
- **Classes:** TyreState, FuelState, WeatherState, TrackState, SafetyCarState, DriverState, CompleteRaceState


### `realtime_live_engine.py`
- **Path:** `D:\Pitwall F1 project\src\realtime_live_engine.py`
- **Classes:** NormalizedRaceEvent, RaceOperationAlert, EventIdempotencyRegistry, RealtimeAlertEngine, RealtimeRaceOperationsEngine


### `realtime_live_infrastructure.py`
- **Path:** `D:\Pitwall F1 project\src\realtime_live_infrastructure.py`
- **Classes:** NormalizedRaceEvent, LiveSystemHealth, EventIdempotencyRegistry, LiveEventBus, RealtimeLiveInfrastructureEngine


### `realtime_race_state.py`
- **Path:** `D:\Pitwall F1 project\src\realtime_race_state.py`
- **Classes:** RaceControlEvent, DriverRaceState, UnifiedRaceState, BaseDataProvider, ReplayAdapter, OpenF1LiveProvider, RealtimeRaceStateEngine


### `rl_config.py`
- **Path:** `D:\Pitwall F1 project\src\rl_config.py`
- **Functions:** is_rl_enabled


### `rl_strategy_agent.py`
- **Path:** `D:\Pitwall F1 project\src\rl_strategy_agent.py`
- **Classes:** RLObservationState, RLDecisionLog, F1StrategyEnv, RLPolicyAgent, RLStrategyEvaluator


### `scenario_engine.py`
- **Path:** `D:\Pitwall F1 project\src\scenario_engine.py`
- **Classes:** ScenarioPreset, ScenarioEngine


### `seed_demo_data.py`
- **Path:** `D:\Pitwall F1 project\src\seed_demo_data.py`
- **Classes:** DemoDataSeeder


### `sensitivity_analysis.py`
- **Path:** `D:\Pitwall F1 project\src\sensitivity_analysis.py`
- **Classes:** SensitivityAnalysisEngine


### `spatial_intelligence_engine.py`
- **Path:** `D:\Pitwall F1 project\src\spatial_intelligence_engine.py`
- **Classes:** SpatialCarPosition, CockpitPOVCamera, CircuitSpatialMetadata, SpatialIntelligenceEngine


### `strategy_model.py`
- **Path:** `D:\Pitwall F1 project\src\strategy_model.py`
- **Classes:** ObjectiveType, StintPlan, StrategyPlan


### `strategy_simulator.py`
- **Path:** `D:\Pitwall F1 project\src\strategy_simulator.py`
- **Functions:** render_jarvis_deck, render_strategy_timeline


### `system_evaluation_metrics.py`
- **Path:** `D:\Pitwall F1 project\src\system_evaluation_metrics.py`
- **Classes:** MetricWithCI, SystemEvaluationMetrics


### `system_integration_validator.py`
- **Path:** `D:\Pitwall F1 project\src\system_integration_validator.py`
- **Classes:** SubsystemStatus, SystemIntegrationReport, SystemIntegrationValidator


### `telemetry_analysis_service.py`
- **Path:** `D:\Pitwall F1 project\src\telemetry_analysis_service.py`
- **Classes:** TelemetryAnalysisService


### `telemetry_api.py`
- **Path:** `D:\Pitwall F1 project\src\telemetry_api.py`
- **Classes:** TelemetryAPIService


### `telemetry_cleaning.py`
- **Path:** `D:\Pitwall F1 project\src\telemetry_cleaning.py`
- **Functions:** clean_telemetry_df


### `telemetry_features.py`
- **Path:** `D:\Pitwall F1 project\src\telemetry_features.py`
- **Classes:** LapFeatures, CornerFeatures, FeatureDataset, FeatureEngineeringService


### `telemetry_ingestion.py`
- **Path:** `D:\Pitwall F1 project\src\telemetry_ingestion.py`
- **Classes:** IngestedDataset, TelemetryIngestionService


### `telemetry_lab.py`
- **Path:** `D:\Pitwall F1 project\src\telemetry_lab.py`
- **Classes:** CanonicalTelemetryPoint, CornerAnalysisResult, TelemetryQualityEngine, TrackDistanceAligner, TimeLossAttributor


### `telemetry_model.py`
- **Path:** `D:\Pitwall F1 project\src\telemetry_model.py`
- **Classes:** TelemetryUnits, CanonicalTelemetryPoint, CanonicalLapTelemetry


### `telemetry_performance_lab.py`
- **Path:** `D:\Pitwall F1 project\src\telemetry_performance_lab.py`
- **Classes:** CanonicalTelemetrySample, CornerDefinition, CornerTimeLossAttribution, PerformanceOpportunity, DriverPerformanceProfile, DriverPerformanceIntelligenceEngine


### `telemetry_pipeline.py`
- **Path:** `D:\Pitwall F1 project\src\telemetry_pipeline.py`
- **Classes:** PipelineRunResult, TelemetryPipeline


### `telemetry_schema.py`
- **Path:** `D:\Pitwall F1 project\src\telemetry_schema.py`
- **Classes:** FieldDefinition
- **Functions:** validate_schema_compliance


### `telemetry_storage.py`
- **Path:** `D:\Pitwall F1 project\src\telemetry_storage.py`
- **Classes:** TelemetryStorageEngine


### `telemetry_sync.py`
- **Path:** `D:\Pitwall F1 project\src\telemetry_sync.py`
- **Functions:** synchronize_telemetry_channels


### `telemetry_validation.py`
- **Path:** `D:\Pitwall F1 project\src\telemetry_validation.py`
- **Classes:** TelemetryValidationResult
- **Functions:** validate_telemetry_df


### `test_model_loader.py`
- **Path:** `D:\Pitwall F1 project\src\test_model_loader.py`
- **Functions:** test_all_models


### `three_d_replay_engine.py`
- **Path:** `D:\Pitwall F1 project\src\three_d_replay_engine.py`
- **Classes:** CameraMode, Car3DState, ThreeDTrackCoordinateSystem, ReplayCacheEngine, ThreeDSceneGenerator


### `time_loss_attribution.py`
- **Path:** `D:\Pitwall F1 project\src\time_loss_attribution.py`
- **Classes:** CornerPerformanceAnalysis
- **Functions:** analyze_corner_performance, _build_empty_corner_analysis


### `tracinginsights.py`
- **Path:** `D:\Pitwall F1 project\src\tracinginsights.py`
- **Functions:** get_driver_color, calculate_fuel_corrected_pace, apply_tyre_smoothing, generate_fuel_pace_chart, generate_25_zone_map, generate_race_trace, generate_pace_heatmap, detect_corners_from_speed, generate_cornering_kinematics, validate_z_axis, fetch_openf1_intervals, fetch_openf1_radio, map_radio_to_laps, generate_radio_timeline, fetch_fia_documents, render_pdf_viewer


### `track_geometry.py`
- **Path:** `D:\Pitwall F1 project\src\track_geometry.py`
- **Classes:** TrackGeometryCache
- **Functions:** load_track_geometry, ensure_track_geometry, render_spatial_map, render_animated_track_trace, render_2d_track_with_positions


### `train_lap_time_model.py`
- **Path:** `D:\Pitwall F1 project\src\train_lap_time_model.py`
- **Functions:** get_lap_data, main


### `train_overtake_model.py`
- **Path:** `D:\Pitwall F1 project\src\train_overtake_model.py`
- **Functions:** train_overtake_model


### `train_rl_agent.py`
- **Path:** `D:\Pitwall F1 project\src\train_rl_agent.py`
- **Functions:** main


### `trend_analysis.py`
- **Path:** `D:\Pitwall F1 project\src\trend_analysis.py`
- **Classes:** TimeSeriesTrendEngine


### `tyre_engine.py`
- **Path:** `D:\Pitwall F1 project\src\tyre_engine.py`
- **Classes:** CanonicalTyreObservation, StintMetadata, TyrePredictionResult, EmpiricalTyreModel, PhysicsInformedTyreModel, TyreModelEvaluator


### `ui_elements.py`
- **Path:** `D:\Pitwall F1 project\src\ui_elements.py`
- **Functions:** inject_custom_css, render_standby_screen, render_live_track_map, inject_hotkeys


### `unified_tyre_intelligence.py`
- **Path:** `D:\Pitwall F1 project\src\unified_tyre_intelligence.py`
- **Classes:** CanonicalTyreState, CompoundCrossoverForecast, PitWindowForecast, UnifiedTyreIntelligenceEngine


### `universal_session_engine.py`
- **Path:** `D:\Pitwall F1 project\src\universal_session_engine.py`
- **Classes:** EventSessionInfo, UniversalSessionEngine, SessionPreparationManager


### `websocket_manager.py`
- **Path:** `D:\Pitwall F1 project\src\websocket_manager.py`
- **Classes:** WebSocketConnectionManager


### `__init__.py`
- **Path:** `D:\Pitwall F1 project\src\__init__.py`

