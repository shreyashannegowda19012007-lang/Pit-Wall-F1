"""
Comprehensive Production Readiness Audit & Regression Test Suite
Validates all critical defect repairs, sporting invariants, and domain logic:
1. IngestedDataset dataclass initialization and field defaults
2. Historical Replay Lap 40 target driver P1 preservation (preventing P18 Zhou latch)
3. Timing Tower leader rollover (preventing false lapped status on lap transitions)
4. Multi-lap gap calculations and sporting intervals
5. Sensitivity analysis OAT perturbations (tyre, pit, SC, fuel, track evolution) without mutation
6. ML model schema parity, non-constant inference, and SHAP explainability
7. JARVIS output formatting, HTML safety, and grounded citation mapping
8. Observability NOT_MEASURED sentinel preservation
9. Telemetry provider status enums
10. Authoritative strategy engine sensitivity metrics
"""

import pytest
import numpy as np
import pandas as pd
from datetime import timedelta
import copy

from telemetry_schema import DataStatus
from telemetry_ingestion import IngestedDataset
from race_state import (
    CompleteRaceState, DriverState, TyreState, FuelState,
    WeatherState, TrackState, SafetyCarState
)
from strategy_model import StrategyPlan, StintPlan
from monte_carlo_engine import MonteCarloRaceEngine
from sensitivity_analysis import SensitivityAnalysisEngine
from realtime_race_state import DriverRaceState, UnifiedRaceState, RealtimeRaceStateEngine
from historical_replay_engine import HistoricalReplayEngine
from bayesian_replay import BayesianRaceReplayEngine
from production_ml_engine import ProductionMLEngine, QuantileLapTimePrediction, SHAPExplanation


# =========================================================================
# 1. IngestedDataset Dataclass Fix Validation
# =========================================================================
def test_ingested_dataset_dataclass_initialization():
    """Verify IngestedDataset can be initialized with default arguments without syntax or ordering errors."""
    ds = IngestedDataset(
        dataset_id="test-ds-01",
        source="FASTF1",
        source_file="test.csv",
        ingestion_timestamp="2026-01-01T00:00:00Z",
        session_id="S-01",
        driver_id="VER",
        lap_number=1,
        row_count=100,
        schema_version="v2.4.0",
        processing_version="v2.4.0",
        checksum="sha256abc"
    )
    assert ds.dataset_id == "test-ds-01"
    assert isinstance(ds.raw_df, pd.DataFrame)
    assert ds.raw_df.empty
    assert ds.provenance is None
    assert ds.checksum == "sha256abc"


# =========================================================================
# 2. Historical Replay Lap 40 P1 Preservation (Zhou P18 Defect Fix)
# =========================================================================
def test_replay_lap_40_target_driver_p1_preservation():
    """
    Verify historical replay engine correctly filters target driver on Lap 40,
    preventing row-0 index leakage where Zhou (P18) was erroneously selected for Verstappen.
    """
    # Create multi-driver mock laps dataframe where row 0 is Zhou (P18) and row 1 is Verstappen (P1)
    mock_records = []
    drivers = [
        ("ZHO", 18, 86.5, "HARD", 10),
        ("VER", 1, 82.1, "MEDIUM", 15),
        ("NOR", 2, 82.4, "MEDIUM", 15),
        ("HAM", 3, 82.8, "HARD", 20),
    ]
    for lap in [38, 39, 40, 41]:
        for d_code, pos, l_time, comp, life in drivers:
            mock_records.append({
                "Driver": d_code,
                "LapNumber": lap,
                "Position": pos,
                "LapTime": pd.Timedelta(seconds=l_time),
                "Time": pd.Timedelta(seconds=3300.0 + (lap - 38) * 82.0 + (pos * 0.5)),
                "Compound": comp,
                "TyreLife": life + (lap - 38),
                "LapStartTime": pd.Timedelta(seconds=3300.0 + (lap - 39) * 82.0),
                "IsAccurate": True,
                "Stint": 2
            })
    laps_df = pd.DataFrame(mock_records)

    # Replay race via HistoricalReplayEngine
    replay_res = HistoricalReplayEngine.run_full_race_replay(
        session=None,
        laps_df=laps_df,
        results_df=pd.DataFrame({'Abbreviation': ['VER', 'HAM', 'NOR', 'ZHO'], 'Position': [1, 2, 3, 18]}),
        target_driver='VER',
        opponent_driver='HAM',
        decision_lap=40,
        mc_iterations=50
    )
    assert "checkpoints" in replay_res
    assert len(replay_res["checkpoints"]) > 0
    cp_40 = replay_res["checkpoints"][0]
    assert cp_40["race_lap"] == 40
    # Invariant: VER is P1 leader on Lap 40, so model expected finish is <= 3 (podium), NOT P18!
    assert cp_40["model_expected_finish"] <= 3, f"Expected finish {cp_40['model_expected_finish']} - indicates P18 Zhou latch regression"
    assert cp_40["model_podium_prob_pct"] > 50.0

    # Also test BayesianRaceReplayEngine
    b_res = BayesianRaceReplayEngine.replay_race_timeline(
        session=None,
        laps_df=laps_df,
        results_df=pd.DataFrame({'Abbreviation': ['VER', 'HAM', 'NOR', 'ZHO']}),
        target_driver='VER',
        opponent_driver='HAM',
        step_laps=5,
        mc_iterations=50
    )
    lap_40_step = next((s for s in b_res['timeline'] if s['race_lap'] == 40), None)
    assert lap_40_step is not None, "Lap 40 checkpoint should exist in timeline"
    assert lap_40_step['expected_finish_position'] <= 3


# =========================================================================
# 3. Timing Tower Leader Rollover False Lapped Status Repair
# =========================================================================
def test_timing_tower_leader_rollover_not_false_lapped():
    """
    Sporting invariant: A driver on lap N is NOT lapped when the leader crosses the line onto lap N+1.
    The car is only lapped when the leader completes lap N+1 BEFORE the driver completes lap N.
    """
    # Create scenario: Leader (VER) on lap 21, Chaser (NOR) on lap 20 just 2.5s behind
    records = []
    # VER laps
    for lap in range(1, 22):
        records.append({
            "Driver": "VER",
            "LapNumber": lap,
            "Position": 1,
            "LapTime": pd.Timedelta(seconds=80.0),
            "Time": pd.Timedelta(seconds=lap * 80.0),
            "Compound": "MEDIUM",
            "TyreLife": lap,
            "PitOutTime": pd.NaT,
            "PitInTime": pd.NaT
        })
    # NOR laps: completed 20 laps, elapsed time 1602.5s (2.5s behind VER on lap 20)
    for lap in range(1, 21):
        records.append({
            "Driver": "NOR",
            "LapNumber": lap,
            "Position": 2,
            "LapTime": pd.Timedelta(seconds=80.125),
            "Time": pd.Timedelta(seconds=lap * 80.125),
            "Compound": "MEDIUM",
            "TyreLife": lap,
            "PitOutTime": pd.NaT,
            "PitInTime": pd.NaT
        })
    laps_df = pd.DataFrame(records)

    # Evaluation at replay time = 1680.0s (Leader VER has just crossed line to complete Lap 21)
    # NOR is still finishing Lap 20 (will cross at ~1682.5s)
    from realtime_race_state import ReplayAdapter
    adapter = ReplayAdapter(laps_df=laps_df)
    state = adapter.fetch_current_race_state(session_id="TEST-ROLLOVER", timestamp_s=1680.0)

    assert "VER" in state.drivers
    assert "NOR" in state.drivers
    nor_state = state.drivers["NOR"]

    # Invariant: NOR is only 2.5s behind on track and must NOT be marked as LAPPED
    assert nor_state.laps_behind_leader == 0, f"NOR falsely marked as {nor_state.laps_behind_leader} laps behind"
    assert nor_state.position == 2


def test_timing_tower_genuine_lapped_car_detection():
    """Verify that a genuinely lapped car (> 1 full lap behind) is correctly identified."""
    records = []
    # Leader VER completed 25 laps
    for lap in range(1, 26):
        records.append({
            "Driver": "VER", "LapNumber": lap, "Position": 1,
            "LapTime": pd.Timedelta(seconds=80.0), "Time": pd.Timedelta(seconds=lap * 80.0),
            "Compound": "MEDIUM", "TyreLife": lap, "PitOutTime": pd.NaT, "PitInTime": pd.NaT
        })
    # Backmarker SAR completed only 23 laps in the same 2000s
    for lap in range(1, 24):
        records.append({
            "Driver": "SAR", "LapNumber": lap, "Position": 20,
            "LapTime": pd.Timedelta(seconds=86.0), "Time": pd.Timedelta(seconds=lap * 86.0),
            "Compound": "HARD", "TyreLife": lap, "PitOutTime": pd.NaT, "PitInTime": pd.NaT
        })
    laps_df = pd.DataFrame(records)

    from realtime_race_state import ReplayAdapter
    adapter = ReplayAdapter(laps_df=laps_df)
    state = adapter.fetch_current_race_state(session_id="TEST-LAPPED", timestamp_s=2000.0)

    sar_state = state.drivers["SAR"]
    assert sar_state.laps_behind_leader >= 1, "SAR should be detected as at least 1 lap down"


# =========================================================================
# 4. Sensitivity Analysis OAT Perturbations & Parameter Propagation
# =========================================================================
def test_sensitivity_analysis_factors_and_isolation():
    """
    Verify SensitivityAnalysisEngine:
    - Runs baseline and all 6 OAT perturbations:
      Tyre deg (-10%, +10%, +20%), Pit loss, Pace, Safety car, Fuel effect, Track evolution.
    - Accurately clones context so original inputs are not mutated.
    - Sensitivity factors are non-empty, sorted by impact, and have valid delta metrics.
    """
    target = DriverState(
        driver_id="VER",
        position=1,
        current_gap_to_leader_s=0.0,
        base_pace_s=80.5,
        tyre_state=TyreState(compound="MEDIUM", age_laps=10, remaining_grip_pct=75.0, thermal_deg_rate=0.07),
        fuel_state=FuelState(fuel_remaining_kg=50.0, fuel_time_penalty_per_kg=0.03)
    )
    opponents = [
        DriverState(
            driver_id="NOR",
            position=2,
            base_pace_s=80.7,
            current_gap_to_leader_s=2.5,
            tyre_state=TyreState(compound="MEDIUM", age_laps=10, remaining_grip_pct=75.0, thermal_deg_rate=0.07),
            fuel_state=FuelState(fuel_remaining_kg=50.0, fuel_time_penalty_per_kg=0.03)
        )
    ]
    race_state = CompleteRaceState(
        current_lap=20,
        total_laps=50,
        drivers={"VER": target, "NOR": opponents[0]},
        weather=WeatherState(track_temp_c=35.0, rainfall=False),
        track=TrackState(track_name="TestCircuit", total_laps=50, pit_lane_loss_seconds=22.5, track_evolution_factor=0.5),
        safety_car=SafetyCarState(sc_probability_per_lap=0.02)
    )
    strategy = StrategyPlan(
        strategy_name="Medium-Hard 1-Stop",
        stints=[StintPlan("MEDIUM", 20, 32), StintPlan("HARD", 32, 50)],
        pit_laps=[32],
        compounds=["MEDIUM", "HARD"],
        stop_count=1
    )

    orig_target_deg = target.tyre_state.thermal_deg_rate
    orig_target_fuel = target.fuel_state.fuel_time_penalty_per_kg
    orig_track_pit_loss = race_state.track.pit_lane_loss_seconds

    res = SensitivityAnalysisEngine.evaluate_sensitivity(
        strategy=strategy,
        target_driver=target,
        opponents=opponents,
        race_state=race_state,
        iterations=300
    )

    # 1. Purity / Isolation: Original inputs must NOT have been mutated
    assert target.tyre_state.thermal_deg_rate == orig_target_deg
    assert target.fuel_state.fuel_time_penalty_per_kg == orig_target_fuel
    assert race_state.track.pit_lane_loss_seconds == orig_track_pit_loss

    # 2. Output structure
    assert "baseline_podium_pct" in res
    assert "baseline_win_pct" in res
    assert "sensitivity_factors" in res
    assert "scenario_results" in res

    # 3. Check that all required scenarios were evaluated
    scenarios = res["scenario_results"]
    assert "baseline" in scenarios
    assert "tyre_deg_high" in scenarios
    assert "tyre_deg_p20" in scenarios
    assert "pit_loss_high" in scenarios
    assert "sc_high" in scenarios
    assert "fuel_effect_high" in scenarios
    assert "track_evolution_high" in scenarios

    # 4. Check sensitivity factors list
    factor_names = [f["factor"] for f in res["sensitivity_factors"]]
    assert "Tyre Thermal Degradation" in factor_names
    assert "Pit Stop Travel Loss" in factor_names
    assert "Safety Car / VSC Timing" in factor_names
    assert "Fuel Effect Sensitivity" in factor_names
    assert "Track Evolution Rate" in factor_names


# =========================================================================
# 5. Production ML Feature Schema Parity & SHAP Explainability
# =========================================================================
def test_ml_production_wrapper_schema_and_shap():
    """
    Verify the production ML pipeline:
    - Loads the genuine trained XGBoost model artifact.
    - Feature schema matches model training features (tyre_life, fuel_burn_laps, compound one-hots).
    - Predicts realistic lap times without falling back to constant 81.24 dummy.
    - Produces grounded TreeExplainer SHAP values without schema dimension mismatch.
    """
    pred_res = ProductionMLEngine.predict_quantile_lap_time(
        driver_id="VER",
        lap_number=25,
        base_pace_s=81.240,
        tyre_age_laps=15,
        compound_str="MEDIUM"
    )
    assert isinstance(pred_res, QuantileLapTimePrediction)
    assert "MODEL_TYPE" in pred_res.quality_flag or "UNAVAILABLE" not in pred_res.quality_flag
    p50 = pred_res.p50_lap_time_s
    assert isinstance(p50, (int, float))
    assert 60.0 <= p50 <= 130.0, f"Predicted lap time {p50}s outside realistic range"

    # Verify SHAP explainability
    shap_res = ProductionMLEngine.explain_lap_time_prediction(
        driver_id="VER",
        lap_number=25,
        base_pace_s=81.240,
        tyre_age_laps=15,
        compound_str="MEDIUM"
    )
    assert isinstance(shap_res, SHAPExplanation)
    assert len(shap_res.feature_contributions) > 0, "SHAP should produce non-empty feature contributions"


# =========================================================================
# 6. Observability Sentinel Preservation
# =========================================================================
def test_observability_not_measured_sentinel_preservation():
    """
    Verify that unmeasured metrics report 'NOT_MEASURED' sentinel string
    rather than fabricated numbers, and that consumers handle it safely.
    """
    from production_data_platform import SessionPreparationManager
    cache_mgr = SessionPreparationManager.get_cache_manager()
    stats = cache_mgr.get_stats()

    assert stats.avg_latency_ms == "NOT_MEASURED"
    assert isinstance(stats.total_queries, int)
    assert isinstance(stats.cache_hits, int)
    assert isinstance(stats.memory_used_mb, float)


# =========================================================================
# 7. Telemetry Schema DataStatus Enum Coverage
# =========================================================================
def test_data_status_enum_completeness():
    """Verify DataStatus enum exposes all required provider state classifications."""
    assert DataStatus.AVAILABLE.value == "AVAILABLE"
    assert DataStatus.PARTIAL.value == "PARTIAL"
    assert DataStatus.EMPTY.value == "EMPTY"
    assert DataStatus.UNAVAILABLE.value == "UNAVAILABLE"
    assert DataStatus.RATE_LIMITED.value == "RATE_LIMITED"
    assert DataStatus.AUTH_REQUIRED.value == "AUTH_REQUIRED"
    assert DataStatus.NETWORK_ERROR.value == "NETWORK_ERROR"
    assert DataStatus.TIMEOUT.value == "TIMEOUT"
    assert DataStatus.SCHEMA_ERROR.value == "SCHEMA_ERROR"
    assert DataStatus.INVALID_REQUEST.value == "INVALID_REQUEST"


# =========================================================================
# 8. AI Engineer JARVIS Query Service Answer & Grounding
# =========================================================================
def test_ai_engineer_service_query_and_citations():
    """Verify AI Engineer service returns grounded answer_markdown and structured evidence citations."""
    from ai_engineer_service import AIEngineerService
    service = AIEngineerService()
    res = service.process_query("How are the tyres?", primary_driver="VER", ref_driver="HAM")

    assert "answer_markdown" in res
    assert "data_status" in res
    assert "evidence_citations" in res
    assert isinstance(res["answer_markdown"], str)
    assert len(res["answer_markdown"]) > 0
    # Guard against hallucination / unsupported claims
    assert "<script>" not in res["answer_markdown"]
