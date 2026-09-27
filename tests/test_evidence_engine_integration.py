import pytest
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.abspath('src'))

from src.evidence_engine import EvidenceEngine, StructuredEvidenceResponse
from src.decision_engine import StructuredDecision, DecisionAlternative

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


def test_real_telemetry_evidence_and_provenance(monkeypatch):
    import src.evidence_engine
    import src.telemetry_analysis_service
    monkeypatch.setattr(src.telemetry_analysis_service, "TelemetryAnalysisService", DummyTelemetryAnalysisService)

    laps_df = pd.DataFrame({'LapNumber': [1, 2, 14]})
    session = DummySession()

    response = EvidenceEngine.resolve_evidence(
        question="Why are we losing time in Turn 7?",
        session=session,
        laps_df=laps_df,
        target_driver="VER",
        ref_driver="HAM",
        current_race_lap=15
    )

    assert response.answerable is True
    assert len(response.evidence_items) > 0

    # Verify provenance and actual values
    t7_loss = next((e for e in response.evidence_items if e.metric == "time_loss_Turn 7"), None)
    assert t7_loss is not None
    assert t7_loss.value == 0.15
    assert t7_loss.source == "TELEMETRY_DERIVED"
    assert "CornerPerformanceAnalysis" in t7_loss.provenance


def test_missing_evidence():
    response = EvidenceEngine.resolve_evidence(
        question="Why did the driver lose 0.143s at Turn 7?",
        session=None,
        laps_df=pd.DataFrame()
    )

    assert response.answerable is False
    assert "INSUFFICIENT_EVIDENCE" in response.reason
    assert len(response.evidence_items) == 0


def test_real_strategy_evidence_and_uncertainty():
    decision_ctx = {
        "recommended_action": "PIT_NOW",
        "win_probability_pct": 25.5,
        "expected_finish": 2.1,
        "downside_risk_pct": 5.0,
        "position_std_dev": 0.8
    }

    response = EvidenceEngine.resolve_evidence(
        question="Why is Strategy B preferred?",
        decision_context=decision_ctx
    )

    assert response.answerable is True

    win_prob = next((e for e in response.evidence_items if e.metric == "win_probability_pct"), None)
    assert win_prob is not None
    assert win_prob.value == 25.5
    assert win_prob.source == "MONTE_CARLO"
    assert win_prob.uncertainty == 0.8
    assert "MonteCarloRaceEngine" in win_prob.provenance


def test_future_data_protection(monkeypatch):
    import src.evidence_engine
    import src.telemetry_analysis_service
    monkeypatch.setattr(src.telemetry_analysis_service, "TelemetryAnalysisService", DummyTelemetryAnalysisService)

    laps_df = pd.DataFrame({'LapNumber': [1, 2, 14, 15, 30]})
    session = DummySession()

    # Mock TelemetryAnalysisService to check the laps_df passed to it, but EvidenceEngine filters it before passing.
    # Actually TelemetryAnalysisService.compare_laps uses session, but EvidenceEngine filters `valid_laps_df`.
    # Let's verify `valid_laps_df` max lap is <= current_race_lap

    # We will hook into _gather_telemetry_evidence to check
    original_gather = src.evidence_engine.EvidenceEngine._gather_telemetry_evidence

    def mock_gather(cls, question, session, valid_laps_df, target_driver, ref_driver, session_name):
        assert valid_laps_df['LapNumber'].max() <= 15
        return original_gather(question, session, valid_laps_df, target_driver, ref_driver, session_name)

    monkeypatch.setattr(src.evidence_engine.EvidenceEngine, "_gather_telemetry_evidence", classmethod(mock_gather))

    EvidenceEngine.resolve_evidence(
        question="Why are we losing time in Turn 7?",
        session=session,
        laps_df=laps_df,
        current_race_lap=15
    )

    print("\n--- ACTUAL EVIDENCE OUTPUT ---")
    response = EvidenceEngine.resolve_evidence(
        question="Why are we losing time in Turn 7?",
        session=session,
        laps_df=laps_df,
        current_race_lap=15
    )
    print(f"QUESTION: {response.question}")
    print(f"ANSWERABLE: {response.answerable}")
    if response.evidence_items:
        item = response.evidence_items[1]
        print(f"EVIDENCE: {item.metric}")
        print(f"SOURCE: {item.source}")
        print(f"SESSION: {response.session}")
        print(f"DRIVER: {item.driver}")
        print(f"LAP: {item.lap}")
        print(f"METRIC: {item.metric}")
        print(f"VALUE: {item.value}")
        print(f"UNCERTAINTY: {item.uncertainty}")
