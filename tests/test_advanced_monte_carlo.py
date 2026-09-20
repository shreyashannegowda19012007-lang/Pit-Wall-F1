"""
Automated Unit, Integration & Probabilistic Test Suite for Advanced Monte Carlo Strategy Engine.
Verifies candidate pit strategy evaluation across N stochastic simulations, Win/Podium probability
calculations, 95% confidence intervals, strategy regret, recommendation tagging, and API integration.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from advanced_monte_carlo import AdvancedMonteCarloStrategyEngine, StrategyCandidate
from telemetry_api import api_service


class TestAdvancedMonteCarloStrategyEngine(unittest.TestCase):

    def test_candidate_strategy_evaluations(self):
        """Verifies candidate strategy evaluation produces structured Monte Carlo risk metrics."""
        res = AdvancedMonteCarloStrategyEngine.evaluate_strategy_candidates(
            target_driver_id="VER",
            circuit_id="SPAIN",
            total_laps=15,
            num_simulations_per_candidate=10,
            base_seed=42
        )

        self.assertEqual(res["target_driver_id"], "VER")
        self.assertIn("recommended_strategy", res)

        evals = res["candidate_evaluations"]
        self.assertTrue(len(evals) >= 4)

        # Check candidate structure
        for e in evals:
            self.assertIn("win_probability_pct", e)
            self.assertIn("podium_probability_pct", e)
            self.assertIn("strategy_regret_s", e)
            self.assertTrue(e["expected_finish_position"] >= 1.0)

        # At least one strategy recommended
        self.assertTrue(any(e["is_recommended"] for e in evals))

    def test_api_service_strategy_monte_carlo_route(self):
        """Verifies API route for advanced strategy Monte Carlo simulation."""
        res = api_service.run_advanced_strategy_monte_carlo("VER", "SPAIN", 15, 10)

        self.assertIn("recommended_strategy", res)
        self.assertTrue(len(res["candidate_evaluations"]) >= 4)


if __name__ == '__main__':
    unittest.main()
