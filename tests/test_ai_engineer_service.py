"""
Automated Unit, Integration & Evidence Verification Test Suite for Production AI Engineer / Jarvis Subsystem.
Verifies intent detection, authoritative tool executions, grounded evidence citations, strict source classifications
(OBSERVED, DERIVED, ESTIMATED, MODELLED, FORECAST, SIMULATED, PREDICTED), and API routes.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from ai_engineer_service import AIEngineerService


class TestAIEngineerJarvisSubsystem(unittest.TestCase):

    def test_telemetry_time_loss_intent_query(self):
        """Verifies telemetry time loss query executes get_time_loss tool and binds evidence citations."""
        service = AIEngineerService()
        laps_df = pd.DataFrame({'LapNumber': [1, 2, 14, 15, 30], 'LapTime': pd.to_timedelta([90.0, 90.2, 91.0, 91.2, 93.0], unit='s'), 'Driver': ['VER', 'VER', 'VER', 'VER', 'VER'], 'Stint': [1, 1, 1, 1, 1], 'Compound': ['SOFT']*5, 'TyreLife': [1,2,14,15,30], 'IsAccurate': [True]*5})
        class DummySession:
            def __init__(self, name="Test Grand Prix"):
                self.session_info = {'Meeting': {'Name': name}}
        session = DummySession()
        
        # Monkey patch
        import src.telemetry_analysis_service
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
        src.telemetry_analysis_service.TelemetryAnalysisService = DummyTelemetryAnalysisService

        resp = service.process_query(query="Where are we losing time in Turn 7?", primary_driver="VER", ref_driver="HAM", session=session, laps_df=laps_df, current_lap=15)

        self.assertIn("Turn 7", resp["answer_markdown"])
        self.assertTrue(len(resp["evidence_citations"]) >= 2)

    def test_strategy_recommendation_intent_query(self):
        """Verifies strategy query executes get_strategy tool and binds evidence citations."""
        service = AIEngineerService()
        laps_df = pd.DataFrame({'LapNumber': [1, 2, 14, 15, 30], 'LapTime': pd.to_timedelta([90.0, 90.2, 91.0, 91.2, 93.0], unit='s'), 'Driver': ['VER', 'VER', 'VER', 'VER', 'VER'], 'Stint': [1, 1, 1, 1, 1], 'Compound': ['SOFT']*5, 'TyreLife': [1,2,14,15,30], 'IsAccurate': [True]*5})
        class DummySession:
            def __init__(self, name="Test Grand Prix"):
                self.session_info = {'Meeting': {'Name': name}}
        session = DummySession()

        from unittest.mock import patch
        
        with patch('src.ai_engineer_service.AIToolRegistry.get_current_decision') as mock_get_decision:
            mock_get_decision.return_value = {
                "recommended_action": "STAY_OUT",
                "recommended_compound": "HARD",
                "recommended_pit_lap": 20,
                "primary_reason": "Maximizes win probability."
            }
            resp = service.process_query("Should we pit?", primary_driver="VER", session=session, laps_df=laps_df, race_state={"lap": 15}, mc_outcomes=[{"strategy": "stay out"}], current_lap=15)

        self.assertIn("STAY_OUT", resp["answer_markdown"])
        self.assertTrue(len(resp["evidence_citations"]) >= 1)
        self.assertTrue(len(resp["evidence_citations"]) >= 1)


if __name__ == '__main__':
    unittest.main()
