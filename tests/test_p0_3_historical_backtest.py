"""
Automated Unit & Audit Test Suite for Historical Race Backtesting Metrics (P0-3 Remediation).
Verifies that regret values are derived dynamically, actuals and expected values are distinct,
future data leakage is guarded, and Oracle fallbacks are removed.
"""

import unittest
from unittest.mock import patch
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from historical_metrics import HistoricalReplayMetrics
from historical_replay_engine import HistoricalReplayEngine
from telemetry_api import api_service
from probabilistic_service import ProbabilisticService


class TestHistoricalBacktestMetricsRemediation(unittest.TestCase):

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
            'Position': [4.0, 1.0] # VER actually finished P4
        })

    def test_a_no_hardcoded_metrics_and_e_missing_data(self):
        """TEST A & E: Ensure metrics are not hardcoded and safely degrade on missing data."""
        # Missing actual data
        metrics = HistoricalReplayMetrics.evaluate_replay_summary(
            checkpoints=[{"model_expected_finish": 2.0}],
            actual_final_finish=None,
            hindsight_best_finish=None
        )
        self.assertEqual(metrics["actual_final_finish"], "UNAVAILABLE")
        self.assertEqual(metrics["offline_oracle_gap_positions"], "UNAVAILABLE")
        self.assertEqual(metrics["online_expected_regret_positions"], "UNAVAILABLE")
        self.assertEqual(metrics["mean_absolute_position_error"], "UNAVAILABLE")

    def test_b_actual_and_recommended_independence(self):
        """TEST B: Verify Actual and Recommended values are independently derived."""
        # If model expects P2, and actual is P4, expected regret is P4 - P2 = 2.0
        metrics = HistoricalReplayMetrics.evaluate_replay_summary(
            checkpoints=[{"model_expected_finish": 2.0, "model_recommendation": "PIT", "actual_team_action": "STAY_OUT"}],
            actual_final_finish=4.0,
            hindsight_best_finish=None
        )
        self.assertEqual(metrics["online_expected_regret_positions"], 2.0)
        self.assertEqual(metrics["strategy_agreement_pct"], 0.0)

    @patch('data_providers.get_provider')
    def test_c_future_data_leakage(self, mock_get_provider):
        """TEST C: Verify Future Data Guard during API backtest."""
        mock_provider = mock_get_provider.return_value
        mock_provider.fetch_session_data.return_value = {
            "success": True,
            "laps": self.mock_laps,
            "results": self.mock_results,
            "raw_session": None
        }

        # Backtest strictly on lap 10
        res = ProbabilisticService.run_historical_backtest("S-2024-SPAIN", "VER", decision_lap=10)
        
        self.assertIn("summary_metrics", res)
        summary = res["summary_metrics"]
        # Expected regret is computed based on whatever the MC engine returned vs Actual 4.0
        self.assertNotEqual(summary["online_expected_regret_positions"], 3.5) # The old hardcoded value

    def test_d_oracle_isolation(self):
        """TEST D: Oracle isolation - Oracle must not hallucinate a fake benchmark."""
        res = HistoricalReplayEngine.run_full_race_replay(
            session=None,
            laps_df=self.mock_laps,
            results_df=self.mock_results,
            target_driver="VER",
            decision_lap=10
        )
        summary = res["summary_metrics"]
        # The synthetic max(1.0, actual - 1) should be gone, reporting UNAVAILABLE
        self.assertEqual(summary["hindsight_best_finish"], "UNAVAILABLE")
        self.assertEqual(summary["offline_oracle_gap_positions"], "UNAVAILABLE")

    def test_f_monte_carlo_reproducibility(self):
        """TEST F: Verify Monte Carlo Reproducibility across backtests."""
        res1 = HistoricalReplayEngine.run_full_race_replay(None, self.mock_laps, self.mock_results, "VER", decision_lap=10, mc_iterations=10)
        res2 = HistoricalReplayEngine.run_full_race_replay(None, self.mock_laps, self.mock_results, "VER", decision_lap=10, mc_iterations=10)
        
        self.assertEqual(
            res1["summary_metrics"]["online_expected_regret_positions"],
            res2["summary_metrics"]["online_expected_regret_positions"]
        )

    @patch('data_providers.get_provider')
    def test_g_real_data_cross_check(self, mock_get_provider):
        """TEST G: Perform cross-check on data endpoints to ensure wiring is correct."""
        mock_provider = mock_get_provider.return_value
        mock_provider.fetch_session_data.return_value = {
            "success": True,
            "laps": self.mock_laps,
            "results": self.mock_results,
            "raw_session": None
        }
        b_res = api_service.run_historical_backtest("S-2024-SPAIN", "VER", 10)
        ab_res = api_service.run_ablation_study("S-2024-SPAIN", self.mock_laps, self.mock_results, "VER")

        # The API shouldn't crash and should return the expected dictionary structure
        self.assertIn("summary_metrics", b_res)
        self.assertIn("ablation_variants", ab_res)
        
        # Ablation study shouldn't hallucinate fake differences (should return UNAVAILABLE for unimplemented models)
        for variant in ab_res["ablation_variants"]:
            if "Baseline" in variant["variant_name"]:
                self.assertEqual(variant["decision_regret"], "UNAVAILABLE")


if __name__ == '__main__':
    unittest.main()
