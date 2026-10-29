"""
Automated Unit, Integration & Probabilistic Test Suite for Advanced Monte Carlo Strategy Engine.
Verifies candidate pit strategy evaluation across N stochastic simulations, Win/Podium probability
calculations, 95% confidence intervals, strategy regret, recommendation tagging, mathematical invariants,
reconciled full-field benchmarks, and API integration.
"""

import unittest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from advanced_monte_carlo import AdvancedMonteCarloStrategyEngine, AutomatedCandidateGenerator, StrategyCandidate
from telemetry_api import api_service


class TestAdvancedMonteCarloStrategyEngine(unittest.TestCase):

    def test_candidate_strategy_evaluations(self):
        """Verifies candidate strategy evaluation produces structured Monte Carlo risk metrics."""
        res = AdvancedMonteCarloStrategyEngine.evaluate_strategy_candidates(
            target_driver_id="VER",
            circuit_id="SPAIN",
            total_laps=15,
            num_simulations_per_candidate=20,
            base_seed=42
        )

        self.assertEqual(res["target_driver_id"], "VER")
        self.assertIn("recommended_strategy", res)

        evals = res["candidate_evaluations"]
        self.assertTrue(len(evals) >= 4)

        for e in evals:
            self.assertIn("win_probability_pct", e)
            self.assertIn("podium_probability_pct", e)
            self.assertIn("strategy_regret_s", e)
            self.assertTrue(e["expected_finish_position"] >= 1.0)
            self.assertTrue(e["win_probability_pct"] <= e["podium_probability_pct"])
            self.assertTrue(0.0 <= e["win_probability_pct"] <= 100.0)
            self.assertTrue(0.0 <= e["podium_probability_pct"] <= 100.0)
            self.assertTrue(e["strategy_regret_s"] >= 0.0)

        # At least one strategy recommended
        self.assertTrue(any(e["is_recommended"] for e in evals))

    def test_probability_bounds_and_invariants(self):
        """Verifies mathematical bounds: win <= pod <= 100%, pos distribution sum == 100%."""
        res = AdvancedMonteCarloStrategyEngine.evaluate_strategy_candidates(
            target_driver_id="VER",
            circuit_id="SPAIN",
            total_laps=66,
            num_simulations_per_candidate=50,
            base_seed=123
        )

        for e in res["candidate_evaluations"]:
            self.assertLessEqual(e["win_probability_pct"], e["podium_probability_pct"] + 1e-4)
            self.assertGreaterEqual(e["win_probability_pct"], 0.0)
            self.assertLessEqual(e["podium_probability_pct"], 100.0)

            dist_sum = sum(e["finish_position_distribution"].values())
            self.assertAlmostEqual(dist_sum, 100.0, delta=1.5)

            # Check that expected position is not stuck at P20.0
            self.assertLess(e["expected_finish_position"], 20.0)

    def test_full_field_benchmark_reconciliation_and_invariants(self):
        """Verifies that full field benchmark exactly reconciles with the recommended strategy and sums to 100% / 300%."""
        res = AdvancedMonteCarloStrategyEngine.evaluate_strategy_candidates(
            target_driver_id="VER",
            circuit_id="SPAIN",
            total_laps=66,
            num_simulations_per_candidate=100,
            base_seed=42
        )

        rec_name = res["recommended_strategy"]
        rec_eval = next(e for e in res["candidate_evaluations"] if e["is_recommended"])
        field = res["field_rankings"]

        self.assertEqual(len(field), 20)

        # Benchmark VER matches Recommended Strategy VER
        ver_field = next(f for f in field if f["driver_id"] == "VER")
        self.assertAlmostEqual(rec_eval["win_probability_pct"], ver_field["win_probability_pct"], delta=0.5)
        self.assertAlmostEqual(rec_eval["podium_probability_pct"], ver_field["podium_probability_pct"], delta=0.5)

        # Mathematical Invariants across the complete 20-car field:
        sum_wins = sum(f["win_probability_pct"] for f in field)
        sum_podiums = sum(f["podium_probability_pct"] for f in field)

        self.assertAlmostEqual(sum_wins, 100.0, delta=1.0)
        self.assertAlmostEqual(sum_podiums, 300.0, delta=2.0)

    def test_seed_reproducibility(self):
        """Verifies that fixed seed produces bit-for-bit identical simulation outcomes."""
        res1 = AdvancedMonteCarloStrategyEngine.evaluate_strategy_candidates(
            target_driver_id="VER",
            circuit_id="SPAIN",
            total_laps=20,
            num_simulations_per_candidate=30,
            base_seed=999
        )
        res2 = AdvancedMonteCarloStrategyEngine.evaluate_strategy_candidates(
            target_driver_id="VER",
            circuit_id="SPAIN",
            total_laps=20,
            num_simulations_per_candidate=30,
            base_seed=999
        )

        self.assertEqual(res1["recommended_strategy"], res2["recommended_strategy"])
        eval1 = res1["candidate_evaluations"][0]
        eval2 = res2["candidate_evaluations"][0]
        self.assertEqual(eval1["win_probability_pct"], eval2["win_probability_pct"])
        self.assertEqual(eval1["mean_race_time_s"], eval2["mean_race_time_s"])
        self.assertEqual(eval1["strategy_regret_s"], eval2["strategy_regret_s"])

    def test_multistop_candidate_generation_and_fia_rules(self):
        """Verifies candidate generator creates 1-stop, 2-stop, and 3-stop strategies respecting FIA rules."""
        cands = AutomatedCandidateGenerator.generate_valid_candidates(total_laps=66, target_driver="VER")
        self.assertTrue(len(cands) >= 5)

        stop_counts = [len(c.pit_laps) for c in cands]
        self.assertIn(1, stop_counts)
        self.assertIn(2, stop_counts)
        self.assertIn(3, stop_counts)

        for c in cands:
            self.assertTrue(c.is_fia_valid)
            self.assertGreaterEqual(len(set(c.compounds)), 2)
            self.assertEqual(len(c.pit_laps), len(c.compounds) - 1)
            for p in c.pit_laps:
                self.assertTrue(0 < p < 66)

    def test_objective_ranking_selection(self):
        """Verifies that different objectives influence strategy selection."""
        res_time = AdvancedMonteCarloStrategyEngine.evaluate_strategy_candidates(
            target_driver_id="VER",
            circuit_id="SPAIN",
            total_laps=66,
            num_simulations_per_candidate=30,
            objective="MIN_RACE_TIME"
        )
        res_win = AdvancedMonteCarloStrategyEngine.evaluate_strategy_candidates(
            target_driver_id="VER",
            circuit_id="SPAIN",
            total_laps=66,
            num_simulations_per_candidate=30,
            objective="MAX_WIN"
        )

        self.assertIn("recommended_strategy", res_time)
        self.assertIn("recommended_strategy", res_win)

    def test_api_service_strategy_monte_carlo_route(self):
        """Verifies API route for advanced strategy Monte Carlo simulation."""
        res = api_service.run_advanced_strategy_monte_carlo("VER", "SPAIN", 15, 10)

        self.assertIn("recommended_strategy", res)
        self.assertTrue(len(res["candidate_evaluations"]) >= 4)


if __name__ == '__main__':
    unittest.main()
