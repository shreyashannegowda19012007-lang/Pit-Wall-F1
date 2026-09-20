import os
import pytest

def test_api_rl_isolation_disabled(monkeypatch):
    monkeypatch.delenv("EXPERIMENTAL_RL_ENABLED", raising=False)
    from src.telemetry_api import TelemetryAPIService
    api_service = TelemetryAPIService()
    
    # Test predict
    res_predict = api_service.predict_rl_action()
    assert res_predict.get("status_code") == 403
    assert res_predict.get("error") == "Forbidden"
    
    # Test evaluate
    res_eval = api_service.evaluate_rl_vs_baselines()
    assert res_eval.get("status_code") == 403
    assert res_eval.get("error") == "Forbidden"

def test_service_rl_isolation_disabled(monkeypatch):
    monkeypatch.delenv("EXPERIMENTAL_RL_ENABLED", raising=False)
    from src.probabilistic_service import ProbabilisticService
    
    res = ProbabilisticService.predict_rl_action()
    assert res.get("status") == "EXPERIMENTAL_FEATURE_DISABLED"
    assert res.get("action_name") == "UNAVAILABLE"
    
    res2 = ProbabilisticService.evaluate_rl_vs_baselines()
    assert res2.get("status") == "EXPERIMENTAL_FEATURE_DISABLED"
    assert res2.get("rl_agent", {}).get("recommended_action") == "UNAVAILABLE"

def test_rl_metadata_correctness(monkeypatch):
    import src.config as config
    from src.decision_architecture import DecisionArchitectureOrchestrator
    
    # Mock RealtimeRaceStateEngine to prevent ImportError
    import sys
    from unittest.mock import MagicMock
    mock_engine = MagicMock()
    mock_engine.get_unified_state.return_value = {"provider": "FALLBACK"}
    # Actually just mock the entire realtime_race_state module's attribute
    import src.realtime_race_state as rrs
    rrs.RealtimeRaceStateEngine = mock_engine
    
    # Simulate model exists
    original_exists = os.path.exists
    monkeypatch.setattr(os.path, "exists", lambda path: True if "ppo_strategy_v1.zip" in str(path) else original_exists(path))
    
    # Case 1: Exists, False -> False
    monkeypatch.delenv("EXPERIMENTAL_RL_ENABLED", raising=False)
    ctx1 = DecisionArchitectureOrchestrator.build_race_context()
    assert ctx1.model_availability["RL_installed"] is True
    assert ctx1.model_availability["RL_experimental_enabled"] is False
    assert ctx1.model_availability["RL"] is False
    
    # Case 2: Exists, True -> True
    monkeypatch.setenv("EXPERIMENTAL_RL_ENABLED", "true")
    ctx2 = DecisionArchitectureOrchestrator.build_race_context()
    assert ctx2.model_availability["RL_installed"] is True
    assert ctx2.model_availability["RL_experimental_enabled"] is True
    assert ctx2.model_availability["RL"] is True
    
    # Case 3: Missing, True -> False
    monkeypatch.setattr(os.path, "exists", lambda path: False if "ppo_strategy_v1.zip" in str(path) else original_exists(path))
    monkeypatch.setenv("EXPERIMENTAL_RL_ENABLED", "true")
    ctx3 = DecisionArchitectureOrchestrator.build_race_context()
    assert ctx3.model_availability["RL_installed"] is False
    assert ctx3.model_availability["RL_experimental_enabled"] is True
    assert ctx3.model_availability["RL"] is False

def test_monte_carlo_empty_fallback():
    from src.decision_engine import DecisionEngine
    # Force empty MC output
    decision = DecisionEngine._fallback_decision(20, "MAX_PODIUM")
    assert decision.recommended_action == "UNAVAILABLE"
    assert decision.expected_finish == 0.0
    assert decision.win_probability_pct == 0.0
    assert decision.podium_probability_pct == 0.0
    assert "Simulation data absent" in decision.primary_reason

def test_rl_isolation_when_disabled(monkeypatch):
    monkeypatch.delenv("EXPERIMENTAL_RL_ENABLED", raising=False)
    from src.rl_config import is_rl_enabled
    assert not is_rl_enabled()

    from unittest.mock import patch, MagicMock
    from src.decision_architecture import DecisionArchitectureOrchestrator, RaceContext, DriverContext

    # Setup dummy context
    rc = RaceContext(2024, 1, "GP", "Race", 1, 57, {"VER": DriverContext("VER", "Red Bull", 1, 0, 0, 1, 80, 80, "MEDIUM", 5, "TRACK", 0.1, "AVAILABLE")}, True, {"RL": False}, "now")
    sd = MagicMock()
    sd.alternatives = []
    sd.downside_risk_pct = 0.0
    sd.win_probability_pct = 0.0
    sd.podium_probability_pct = 0.0

    with patch('src.rl_strategy_agent.RLStrategyEvaluator.evaluate_rl_vs_baselines') as spy:
        from src.decision_architecture import DecisionEngine
        DecisionEngine.generate_recommendation(rc, "VER", "HAM")
        spy.assert_not_called()
