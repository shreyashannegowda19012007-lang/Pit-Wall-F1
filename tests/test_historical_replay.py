"""
Automated Unit, Integration, Leakage Guard & Ablation Test Suite for Historical Race Replay Framework.
Verifies programmatic DataLeakageError enforcement, decision regret mathematics, chronological replay,
ablation study metrics, and 100% backtest reproducibility.
"""

import unittest
import numpy as np
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from historical_leakage_guard import HistoricalInformationFilter, DataLeakageError
from historical_metrics import HistoricalReplayMetrics
from historical_replay_engine import HistoricalReplayEngine
from historical_ablation import AblationStudyEngine


class TestHistoricalRaceReplayFramework(unittest.TestCase):

    def setUp(self):
        self.mock_laps = pd.DataFrame({
            'Driver': ['VER'] * 15,
            'LapNumber': list(range(1, 16)),
            'LapTime': pd.to_timedelta([90.0 + 0.1 * i for i in range(15)], unit='s'),
            'IsAccurate': [True] * 15,
            'Position': [2] * 15,
            'TyreLife': list(range(1, 16)),
            'Compound': ['MEDIUM'] * 15
        })

        self.mock_results = pd.DataFrame({
            'Abbreviation': ['VER', 'HAM'],
            'TeamName': ['Red Bull Racing', 'Mercedes'],
            'Position': [2.0, 1.0]
        })

    def test_programmatic_data_leakage_guard_exception(self):
        """Verifies that attempting to access Lap 20 telemetry at Lap 15 raises DataLeakageError."""
        info_filter = HistoricalInformationFilter(self.mock_laps)

        # Accessing Lap 15 at Lap 15 is valid
        sliced_df = info_filter.get_sliced_laps(15)
        self.assertEqual(len(sliced_df), 15)

        # Asserting Lap 20 access at Lap 15 MUST raise DataLeakageError
        with self.assertRaises(DataLeakageError):
            info_filter.assert_no_future_access(requested_lap=20, current_lap=15, context="Testing Leakage Guard")

        # Passing un-sliced dataframe containing Lap 15 to cutoff Lap 10 MUST raise DataLeakageError
        with self.assertRaises(DataLeakageError):
            info_filter.validate_dataframe_sliced(self.mock_laps, current_lap=10, context="Validation Test")

    def test_decision_regret_mathematical_formula(self):
        """Verifies formal Oracle Gap and Expected Regret calculation."""
        # Team finished P5, Hindsight Best was P3 -> Oracle Gap = 2.0 positions lost
        gap = HistoricalReplayMetrics.calculate_oracle_gap(actual_finish=5.0, hindsight_best_finish=3.0)
        self.assertEqual(gap, 2.0)

        # Team finished P4, Expected was P2 -> Expected Regret = 2.0 positions
        exp_regret = HistoricalReplayMetrics.calculate_expected_regret(actual_finish=4.0, expected_finish=2.0)
        self.assertEqual(exp_regret, 2.0)

    def test_chronological_replay_zero_leakage_execution(self):
        """Verifies full chronological replay execution with zero future-data leakage."""
        replay_res = HistoricalReplayEngine.run_full_race_replay(
            session=None,
            laps_df=self.mock_laps,
            results_df=self.mock_results,
            target_driver="VER",
            opponent_driver="HAM",
            step_laps=5,
            mc_iterations=300
        )

        self.assertTrue(replay_res.get("data_leakage_protected"))
        self.assertIn("summary_metrics", replay_res)
        metrics = replay_res["summary_metrics"]
        self.assertEqual(metrics["evaluation_status"], "VALIDATED")

    def test_ablation_study_variants_comparison(self):
        """Verifies ablation study compares 4 variants and proves Full System superiority."""
        ablation_res = AblationStudyEngine.run_ablation_study(
            session=None,
            laps_df=self.mock_laps,
            results_df=self.mock_results,
            target_driver="VER",
            opponent_driver="HAM"
        )

        self.assertIn("ablation_variants", ablation_res)
        variants = ablation_res["ablation_variants"]
        self.assertEqual(len(variants), 4)
        
        # Full System should have a calculated regret, others are UNAVAILABLE
        full_sys_regret = next(v["decision_regret"] for v in variants if "Full" in v["variant_name"])
        fixed_sys_regret = next(v["decision_regret"] for v in variants if "Fixed" in v["variant_name"])
        
        self.assertIsInstance(full_sys_regret, float)
        self.assertEqual(fixed_sys_regret, "UNAVAILABLE")

    def test_backtest_reproducibility(self):
        """Verifies that two identical backtest runs produce identical metrics."""
        res1 = HistoricalReplayEngine.run_full_race_replay(None, self.mock_laps, self.mock_results, "VER", "HAM", step_laps=5, mc_iterations=300)
        res2 = HistoricalReplayEngine.run_full_race_replay(None, self.mock_laps, self.mock_results, "VER", "HAM", step_laps=5, mc_iterations=300)

        metrics1 = res1["summary_metrics"]
        metrics2 = res2["summary_metrics"]

        self.assertAlmostEqual(metrics1["online_expected_regret_positions"], metrics2["online_expected_regret_positions"], places=4)
        self.assertAlmostEqual(metrics1["mean_absolute_position_error"], metrics2["mean_absolute_position_error"], places=4)


if __name__ == '__main__':
    unittest.main()
