"""
Automated Unit & Adversarial Test Suite for Historical Context & Evidence Engine.
Verifies context retrieval, relevance scoring, evidence bundle assembly, trend calculation,
and strict anti-hallucination guardrails for missing data queries.
"""

import unittest
import numpy as np
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from historical_retrieval import HistoricalRetrievalEngine, ContextRelevanceScore
from trend_analysis import TimeSeriesTrendEngine
from evidence_engine import EvidenceEngine, StructuredEvidenceResponse, EvidenceItem
from ai_tools import AIToolRegistry
from ai_engineer_qa import AIEngineerQAEngine


class TestEvidenceEngine(unittest.TestCase):

    def setUp(self):
        # Create mock laps DataFrame
        self.mock_laps = pd.DataFrame({
            'Driver': ['VER'] * 6 + ['HAM'] * 6,
            'DriverNumber': ['1'] * 6 + ['44'] * 6,
            'LapNumber': [10, 11, 12, 13, 14, 15] * 2,
            'LapTime': pd.to_timedelta([90.0, 90.2, 90.4, 90.6, 90.8, 91.0,  # VER: +0.2s/lap degradation
                                        90.5, 90.4, 90.3, 90.2, 90.1, 90.0], unit='s'), # HAM: improving
            'Sector1Time': pd.to_timedelta([28.0] * 12, unit='s'),
            'Sector2Time': pd.to_timedelta([32.0] * 12, unit='s'),
            'Sector3Time': pd.to_timedelta([30.0] * 12, unit='s'),
            'Compound': ['SOFT'] * 12,
            'Stint': [1] * 12,
            'TyreLife': [10, 11, 12, 13, 14, 15] * 2,
            'IsAccurate': [True] * 12
        })

        self.mock_results = pd.DataFrame({
            'Abbreviation': ['VER', 'HAM'],
            'TeamColor': ['3671C6', '27F4D2'],
            'TeamName': ['Red Bull Racing', 'Red Bull Racing'],
            'DriverNumber': ['1', '44']
        })

    def test_historical_context_retrieval(self):
        cur_ctx = HistoricalRetrievalEngine.get_current_lap_context(self.mock_laps, "VER")
        self.assertTrue(cur_ctx['found'])
        self.assertEqual(cur_ctx['lap_number'], 15)
        self.assertAlmostEqual(cur_ctx['lap_time_s'], 91.0)

        prev_laps = HistoricalRetrievalEngine.get_previous_laps_context(self.mock_laps, "VER", current_lap_num=15, count=3)
        self.assertEqual(len(prev_laps), 3)

        best_lap = HistoricalRetrievalEngine.get_best_lap_context(self.mock_laps, "VER")
        self.assertEqual(best_lap['lap_number'], 10)
        self.assertAlmostEqual(best_lap['lap_time_s'], 90.0)

    def test_teammate_retrieval(self):
        tm_ctx = HistoricalRetrievalEngine.get_teammate_context(self.mock_laps, "VER", self.mock_results)
        self.assertTrue(tm_ctx['found'])
        self.assertEqual(tm_ctx['driver_id'], "HAM")
        self.assertTrue(tm_ctx['is_teammate'])

    def test_context_relevance_scoring(self):
        candidate = {"session_id": "SPAIN_2024", "driver_id": "VER", "compound": "SOFT", "tyre_age": 12}
        reference = {"session_id": "SPAIN_2024", "driver_id": "VER", "compound": "SOFT", "tyre_age": 14}
        
        score_obj = HistoricalRetrievalEngine.score_context_relevance(candidate, reference)
        self.assertTrue(score_obj.relevance_score >= 90.0)
        self.assertIn("Same Session", score_obj.matching_factors)

    def test_stint_pace_degradation_trend(self):
        stint_deg = TimeSeriesTrendEngine.calculate_stint_pace_degradation(self.mock_laps, "VER")
        self.assertTrue(stint_deg['valid'])
        self.assertEqual(stint_deg['lap_count'], 6)
        self.assertTrue(stint_deg['degradation_rate_s_per_lap'] > 0.15)  # +0.2s/lap deg

    def test_evidence_bundle_assembly(self):
        bundle = EvidenceEngine.resolve_evidence(
            question="Why are we losing time in Turn 7?",
            session=None,
            laps_df=self.mock_laps,
            target_driver="VER",
            ref_driver="HAM"
        )
        # Because we passed session=None, it should fall back to INSUFFICIENT_EVIDENCE
        self.assertFalse(bundle.answerable)
        self.assertIn("INSUFFICIENT_EVIDENCE", bundle.reason)

    def test_ai_tools_registry(self):
        cur_lap = AIToolRegistry.get_current_lap(self.mock_laps, "VER")
        self.assertTrue(cur_lap['found'])
        
        tm = AIToolRegistry.get_teammate_context(self.mock_laps, "VER", self.mock_results)
        self.assertEqual(tm['driver_id'], "HAM")

    def test_adversarial_missing_weather_data(self):
        """Adversarial Test: Asking for wind speed when weather telemetry is unavailable."""
        res = AIEngineerQAEngine.answer_question(
            question="What was the wind speed on Lap 12?",
            session=None,  # No weather data
            laps_df=self.mock_laps,
            results_df=self.mock_results,
            target_driver="VER",
            ref_driver="HAM"
        )
        self.assertFalse(res['has_data'])
        self.assertIn("unavailable", res['answer'].lower())
        self.assertNotIn("3.5", res['answer'])  # Must NOT invent random wind speed!

    def test_adversarial_missing_historical_dataset(self):
        """Adversarial Test: Asking to compare against last year's race when historical session dataset is missing."""
        res = AIEngineerQAEngine.answer_question(
            question="Compare this to last year's race.",
            session=None,
            laps_df=self.mock_laps,
            results_df=self.mock_results,
            target_driver="VER",
            ref_driver="HAM"
        )
        self.assertFalse(res['has_data'])
        self.assertIn("no comparable historical dataset", res['answer'].lower())


if __name__ == '__main__':
    unittest.main()
