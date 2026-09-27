import pytest
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.abspath('src'))

from src.ai_engineer_service import AIEngineerService

class DummySession:
    def __init__(self, name="Test Grand Prix"):
        self.session_info = {'Meeting': {'Name': name}}


class DummyTelemetryAnalysisService:
    @staticmethod
    def compare_laps(session, target_driver, ref_driver):
        return {
            "success": True,
            "meta_a": {"lap_number": 14},
            "meta_b": {"lap_number": 14},
            "lap_time_delta_s": 0.45,
            "top_opportunities": [
                {
                    "corner_name": "Turn 7",
                    "entry_m": 1200.5,
                    "time_loss_seconds": 0.15,
                    "minimum_speed_delta_kmh": -5.2,
                    "braking_point_delta_m": 12.0
                }
            ]
        }

@pytest.fixture
def mock_telemetry(monkeypatch):
    import src.telemetry_analysis_service
    monkeypatch.setattr(src.telemetry_analysis_service, "TelemetryAnalysisService", DummyTelemetryAnalysisService)

@pytest.fixture
def service():
    return AIEngineerService()

@pytest.fixture
def test_data():
    laps_df = pd.DataFrame({'LapNumber': [1, 2, 14, 15, 30], 'LapTime': pd.to_timedelta([90.0, 90.2, 91.0, 91.2, 93.0], unit='s'), 'Driver': ['VER', 'VER', 'VER', 'VER', 'VER'], 'Stint': [1, 1, 1, 1, 1], 'Compound': ['SOFT']*5, 'TyreLife': [1,2,14,15,30], 'IsAccurate': [True]*5})
    session = DummySession()
    mc_outcomes = [{"strategy": "1-Stop"}]
    race_state = {"current_lap": 15}
    return laps_df, session, mc_outcomes, race_state


def test_driver_performance_question(service, test_data, mock_telemetry):
    laps_df, session, mc_outcomes, race_state = test_data
    res = service.process_query(
        query="Why are we losing time?",
        primary_driver="VER",
        ref_driver="HAM",
        session=session,
        laps_df=laps_df,
        current_lap=15
    )
    assert res["data_status"] == "SUCCESS"
    assert "Turn 7" in res["answer_markdown"]
    assert "0.15" in res["answer_markdown"]
    print("\nOUTPUT:\n" + res["answer_markdown"])


def test_strategy_question(service, test_data, mock_telemetry, monkeypatch):
    laps_df, session, mc_outcomes, race_state = test_data

    # Mock AIToolRegistry inside ai_engineer_service
    import src.ai_engineer_service
    class MockRegistry:
        @staticmethod
        def get_current_decision(rs, mc):
            return {
                "recommended_action": "PIT_NOW",
                "recommended_compound": "HARD",
                "recommended_pit_lap": 15,
                "primary_reason": "Maximizes win probability."
            }
    monkeypatch.setattr(src.ai_engineer_service, "AIToolRegistry", MockRegistry)

    res = service.process_query(
        query="Should we pit now?",
        session=session,
        laps_df=laps_df,
        race_state=race_state,
        mc_outcomes=mc_outcomes,
        current_lap=15
    )
    if res["data_status"] == "MODEL_ERROR":
        print(res["answer_markdown"])
    assert res["data_status"] == "SUCCESS"
    assert "PIT_NOW" in res["answer_markdown"]
    assert "Maximizes win probability" in res["answer_markdown"]
    print("\nOUTPUT:\n" + res["answer_markdown"])


def test_what_if_question(service, test_data, mock_telemetry, monkeypatch):
    laps_df, session, mc_outcomes, race_state = test_data

    import src.ai_engineer_service
    class MockRegistry:
        @staticmethod
        def get_current_decision(rs, mc):
            return {
                "recommended_action": "PIT_NOW",
                "recommended_compound": "HARD",
                "recommended_pit_lap": 15,
                "primary_reason": "Maximizes win probability."
            }
    monkeypatch.setattr(src.ai_engineer_service, "AIToolRegistry", MockRegistry)

    res = service.process_query(
        query="What happens if we pit three laps earlier?",
        session=session,
        laps_df=laps_df,
        race_state=race_state,
        mc_outcomes=mc_outcomes,
        current_lap=15
    )
    if res["data_status"] == "MODEL_ERROR":
        print(res["answer_markdown"])
    assert res["data_status"] == "SUCCESS"
    assert "Based on Monte Carlo variations" in res["answer_markdown"]
    print("\nOUTPUT:\n" + res["answer_markdown"])


def test_tyre_question(service, test_data):
    laps_df, session, _, _ = test_data
    res = service.process_query(
        query="How much life is left in the current tyre?",
        laps_df=laps_df,
        primary_driver="VER"
    )
    if res["data_status"] == "MODEL_ERROR":
        print(res["answer_markdown"])
    assert res["data_status"] in ["SUCCESS", "MODEL_UNAVAILABLE"]


def test_future_data_protection(service, test_data):
    laps_df, session, _, _ = test_data
    res = service.process_query(
        query="What happened on lap 30?",
        current_lap=15,
        mode="REPLAY"
    )
    assert res["data_status"] == "TEMPORAL_VIOLATION"
    assert "unavailable in the current temporal context" in res["answer_markdown"]
    print("\nOUTPUT:\n" + res["answer_markdown"])


def test_ml_rl_unavailable(service, monkeypatch):
    from src.evidence_engine import StructuredEvidenceResponse
    import src.ai_engineer_service

    class MockEvidenceEngine:
        @classmethod
        def get_ml_evidence(cls, model_name):
            return StructuredEvidenceResponse(question="", answerable=False, session="ANY", reason="Not available")

    monkeypatch.setattr(src.ai_engineer_service, "EvidenceEngine", MockEvidenceEngine)

    res_ml = service.process_query("What does the ML model predict?")
    assert res_ml["data_status"] == "ML_MODEL_NOT_TRAINED"
    assert "not currently available" in res_ml["answer_markdown"]

    res_rl = service.process_query("What does the RL model say?")
    assert res_rl["data_status"] == "RL_MODEL_NOT_TRAINED"


def test_unsupported_claim(service):
    res = service.process_query("I want you to invent a probability for pitting.")
    assert res["data_status"] == "UNSUPPORTED_CLAIM"
    assert "cannot manufacture data" in res["answer_markdown"]


def test_missing_evidence(service):
    res = service.process_query("Why are we losing time at Turn 12?", laps_df=pd.DataFrame())
    assert res["data_status"] == "INSUFFICIENT_EVIDENCE"
