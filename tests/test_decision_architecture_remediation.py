import os
import pytest
from src.decision_architecture import DecisionArchitectureOrchestrator, DecisionEngine, DriverContext, RaceContext
from src.jarvis_engineering_insights import JarvisEngineeringInsightsEngine
import pandas as pd

def get_test_race_context():
    drivers = {
        "VER": DriverContext(driver="VER", team="RBR", position=1, gap_to_leader=0.0, interval_to_ahead=0.0, lap=20, last_lap_s=82.0, best_lap_s=81.5, tyre_compound="MEDIUM", tyre_age_laps=20, pit_status="TRACK", degradation_estimate_s_per_lap=0.08, telemetry_state="AVAILABLE"),
        "HAM": DriverContext(driver="HAM", team="MER", position=2, gap_to_leader=2.0, interval_to_ahead=2.0, lap=20, last_lap_s=82.2, best_lap_s=81.6, tyre_compound="HARD", tyre_age_laps=20, pit_status="TRACK", degradation_estimate_s_per_lap=0.05, telemetry_state="AVAILABLE")
    }
    return RaceContext(
        season=2024, round=1, event="Grand Prix", session="Race",
        current_lap=20, total_laps=57, drivers=drivers,
        telemetry_availability=True,
        model_availability={"RL": True, "ML": True},
        data_timestamp="2026-09-03"
    )

class TestDecisionArchitectureRemediation:
    def test_rl_has_zero_influence_when_flag_disabled(self, monkeypatch):
        monkeypatch.delenv("EXPERIMENTAL_RL_ENABLED", raising=False)
        context = get_test_race_context()
        
        # Act
        recommendation = DecisionEngine.generate_recommendation(context, "VER", "HAM")
        
        # Assert
        assert "EXPERIMENTAL RL OVERRIDE" not in recommendation.primary_reason
        assert "Monte Carlo" in recommendation.primary_reason or "Simulator" in recommendation.evidence_refs[1]
        assert "RL_PPO" not in recommendation.model_versions
        assert recommendation.expected_race_time_s > 0
        assert recommendation.p_podium > 0.0

    def test_rl_can_influence_when_flag_enabled(self, monkeypatch):
        monkeypatch.setenv("EXPERIMENTAL_RL_ENABLED", "true")
        context = get_test_race_context()
        
        # Act
        recommendation = DecisionEngine.generate_recommendation(context, "VER", "HAM")
        
        # Assert
        assert "EXPERIMENTAL RL OVERRIDE" in recommendation.primary_reason
        assert "RL_PPO" in recommendation.model_versions
        
    def test_jarvis_recommendations_without_rl(self, monkeypatch):
        monkeypatch.delenv("EXPERIMENTAL_RL_ENABLED", raising=False)
        
        # Mock the build_race_context so we don't need real FastF1 session
        monkeypatch.setattr(DecisionArchitectureOrchestrator, "build_race_context", get_test_race_context)
        
        laps_df = pd.DataFrame()
        results_df = pd.DataFrame()
        
        insights = JarvisEngineeringInsightsEngine.generate_session_insights(laps_df, results_df, {}, raw_session=None, active_driver="VER")
        
        decision_insight = next((i for i in insights if i["id"] == "INS-DECISION-01"), None)
        assert decision_insight is not None
        assert "EXPERIMENTAL RL OVERRIDE" not in decision_insight["why"]
        assert "Ranks highest under" in decision_insight["why"]

