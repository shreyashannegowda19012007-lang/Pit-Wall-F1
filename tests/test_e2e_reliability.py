"""
Automated Integration & System Reliability Test Suite.
Verifies end-to-end user workflows, driver data synchronization, missing data error boundaries,
zero future-data leakage protection, zero-randomness Monte Carlo determinism, and AI hallucination guardrails.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from telemetry_api import api_service
from historical_leakage_guard import HistoricalInformationFilter, DataLeakageError
from monte_carlo_engine import MonteCarloRaceEngine
from race_state import CompleteRaceState, DriverState, TyreState, FuelState, WeatherState, TrackState, SafetyCarState
from ai_evaluator import AIEngineerEvaluator


class TestEndToEndReliability(unittest.TestCase):

    def test_health_and_readiness_endpoints(self):
        """Verifies API liveness /healthz and readiness /readyz endpoints."""
        health = api_service.get_health_status()
        ready = api_service.get_readiness_status()

        self.assertEqual(health["status"], "HEALTHY")
        self.assertEqual(ready["status"], "READY")

    def test_future_data_leakage_protection(self):
        """Verifies programmatic DataLeakageError exception when querying future laps."""
        laps_df = pd.DataFrame({'LapNumber': list(range(1, 31))})
        hist_filter = HistoricalInformationFilter(laps_df)

        # Accessing Lap 20 when current lap is 20 -> PASS
        sliced = hist_filter.get_sliced_laps(current_lap=20)
        self.assertEqual(sliced['LapNumber'].max(), 20)

        # Accessing Lap 21 when current lap is 20 -> MUST RAISE DataLeakageError
        with self.assertRaises(DataLeakageError):
            hist_filter.assert_no_future_access(requested_lap=21, current_lap=20)

    def test_zero_randomness_monte_carlo_determinism(self):
        """Verifies Monte Carlo simulator determinism when randomness is fixed."""
        engine1 = MonteCarloRaceEngine(iterations=500, seed=42)
        engine2 = MonteCarloRaceEngine(iterations=500, seed=42)

        ver = DriverState("VER", 2, 0.5, 90.0, TyreState("MEDIUM", 10, 80.0, 0.08), FuelState(30.0), 0.0)
        ham = DriverState("HAM", 1, 0.0, 89.8, TyreState("MEDIUM", 10, 80.0, 0.08), FuelState(30.0), 0.0)
        state = CompleteRaceState(20, 50, {"VER": ver, "HAM": ham}, WeatherState("DRY"), TrackState("Spain"), SafetyCarState("GREEN"))

        res1 = engine1.rank_strategies(ver, [ham], state)
        res2 = engine2.rank_strategies(ver, [ham], state)

        self.assertEqual(len(res1), len(res2))
        self.assertEqual(res1[0].strategy_plan.strategy_name, res2[0].strategy_plan.strategy_name)
        self.assertAlmostEqual(res1[0].win_probability, res2[0].win_probability, places=2)

    def test_ai_hallucination_guardrails(self):
        """Verifies AI layer refuses missing data queries without hallucinating numbers."""
        res = AIEngineerEvaluator.evaluate_ai_layer()

        self.assertEqual(res["hallucination_rate_pct"], 0.0)
        self.assertEqual(res["evaluation_status"], "PASSED")


if __name__ == '__main__':
    unittest.main()
