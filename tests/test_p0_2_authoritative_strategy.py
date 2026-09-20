import pytest
from unittest.mock import patch, MagicMock
from src.probabilistic_service import ProbabilisticService
from src.decision_engine import DecisionEngine as FormalDecisionEngine
from src.decision_architecture import DecisionArchitectureOrchestrator, DecisionEngine
from src.monte_carlo_engine import MonteCarloRaceEngine
from src.telemetry_api import TelemetryAPIService

def test_a_templates_cannot_bypass_optimization():
    # Calling evaluate_authoritative_strategy must route through DecisionEngine, not AuthoritativeStrategyEngine
    with patch.object(DecisionArchitectureOrchestrator, "build_race_context") as mock_build:
        mock_build.return_value = MagicMock(telemetry_availability=True, drivers={"VER": MagicMock(last_lap_s=80.0, gap_ahead=0.0)})
        with patch.object(DecisionEngine, "generate_recommendation") as mock_gen:
            mock_rec = MagicMock()
            mock_rec.recommendation = "PIT_NOW"
            mock_rec.p_win = 45.0
            mock_rec.p_podium = 60.0
            mock_rec.primary_reason = "Test Reason"
            mock_rec.risk = "Test Risk"
            mock_rec.confidence_pct = 90.0
            mock_rec.alternative = "STAY_OUT"
            mock_gen.return_value = mock_rec
            
            api = TelemetryAPIService()
            res = api.evaluate_authoritative_strategy()
            
            mock_gen.assert_called_once()
            assert res["recommended_action"] == "PIT_NOW"
            assert res["win_probability_pct"] == 45.0

def test_b_mc_failure_safety():
    # When MC returns no outcomes (simulating failure), it should gracefully degrade to UNAVAILABLE
    with patch("src.decision_architecture.DecisionArchitectureOrchestrator.build_race_context") as mock_build:
        mock_rc = MagicMock(telemetry_availability=True)
        mock_rc.drivers = {"VER": MagicMock(last_lap_s=80.0, gap_ahead=0.0, position=1, tyre_compound="MEDIUM", tyre_age_laps=10)}
        mock_build.return_value = mock_rc
        with patch("src.monte_carlo_engine.MonteCarloRaceEngine.rank_strategies", return_value=[]):
            recommendation = DecisionEngine.generate_recommendation(mock_build.return_value, "VER", "HAM")
            # Should gracefully degrade via DecisionEngine._fallback_decision -> UNAVAILABLE
            assert recommendation.recommendation == "UNAVAILABLE"
            assert recommendation.p_win == 0.0

def test_c_baseline_safety():
    # Baseline candidates (1-stop, 2-stop) exist only as candidates and go through MC optimization
    engine = MonteCarloRaceEngine(iterations=2)
    race_state = MagicMock()
    race_state.current_lap = 20
    race_state.total_laps = 50
    race_state.weather.track_temp_c = 30.0
    race_state.weather.rainfall = 0.0
    race_state.track.track_evolution_factor = 1.0

    target = MagicMock()
    target.tyre_state.compound = "MEDIUM"
    target.tyre_state.age_laps = 10
    target.base_pace_s = 80.0
    
    opponents = []
    
    with patch.object(engine, "simulate_strategy_vectorized") as mock_sim:
        mock_sim.side_effect = [
            MagicMock(win_probability=5, podium_probability=10),
            MagicMock(win_probability=4, podium_probability=9),
            MagicMock(win_probability=3, podium_probability=8),
            MagicMock(win_probability=2, podium_probability=7),
            MagicMock(win_probability=1, podium_probability=6),
        ]
        engine.rank_strategies(target, opponents, race_state)
        # Should simulate the 5 candidate strategies: 1-stop_h, 1-stop_m, undercut, 2-stop, stayout
        assert mock_sim.call_count == 5

def test_d_decision_engine_authority():
    # ProbabilisticService.evaluate_authoritative_strategy uses DecisionArchitectureOrchestrator
    with patch.object(DecisionArchitectureOrchestrator, "build_race_context") as mock_build:
        mock_build.return_value = MagicMock()
        with patch.object(DecisionEngine, "generate_recommendation") as mock_gen:
            ProbabilisticService.evaluate_authoritative_strategy()
            mock_build.assert_called_once()
            mock_gen.assert_called_once()

def test_e_end_to_end_trace():
    # E2E trace should not contain fake strings like "STAY_OUT (2 Laps)" from AuthoritativeStrategyEngine
    with patch.object(DecisionArchitectureOrchestrator, "build_race_context") as mock_build:
        mock_build.return_value = MagicMock(telemetry_availability=False)
        res = ProbabilisticService.evaluate_authoritative_strategy()
        assert res["recommended_action"] != "STAY_OUT (2 Laps)"
    
def test_f_no_fabricated_fallback():
    # FormalDecisionEngine._fallback_decision does not invent data
    fallback = FormalDecisionEngine._fallback_decision(race_lap=10, objective="MAX_WIN")
    assert fallback.recommended_action == "UNAVAILABLE"
    assert fallback.win_probability_pct == 0.0
    assert fallback.podium_probability_pct == 0.0
    assert fallback.expected_finish == 0.0
