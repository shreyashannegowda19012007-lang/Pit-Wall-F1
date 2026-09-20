"""
Automated Unit, Integration & Reproducibility Test Suite for System Evaluation & Benchmarking Framework.
Verifies MAE, RMSE, Brier score, time-loss reconciliation error, bootstrap 95% CIs,
AI layer accuracy metrics, and 100% benchmark reproducibility across identical seeds.
"""

import unittest
import numpy as np
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from system_evaluation_metrics import SystemEvaluationMetrics, MetricWithCI
from ai_evaluator import AIEngineerEvaluator
from benchmark_runner import BenchmarkRunner


class TestSystemEvaluationFramework(unittest.TestCase):

    def test_mae_rmse_metric_calculations(self):
        """Verifies MAE and RMSE math calculations."""
        preds = [1.0, 2.0, 3.0]
        actuals = [1.5, 2.5, 2.5]

        mae = SystemEvaluationMetrics.calculate_mae(preds, actuals)
        rmse = SystemEvaluationMetrics.calculate_rmse(preds, actuals)

        self.assertAlmostEqual(mae, 0.5, places=4)
        self.assertAlmostEqual(rmse, float(np.sqrt(0.25 + 0.25 + 0.25) / np.sqrt(3)), places=4)

    def test_time_loss_reconciliation_error(self):
        """Verifies time-loss residual error calculation across segments vs total lap loss."""
        totals = [0.50, 0.30, 0.40]
        attributed = [0.48, 0.30, 0.39]

        res = SystemEvaluationMetrics.calculate_reconciliation_error(totals, attributed)

        self.assertAlmostEqual(res["mean_error"], 0.01, places=4)
        self.assertAlmostEqual(res["max_error"], 0.02, places=4)

    def test_paired_bootstrap_confidence_intervals(self):
        """Verifies paired bootstrap 95% confidence interval bounds."""
        data = [0.10, 0.12, 0.09, 0.11, 0.13, 0.10, 0.08, 0.12]
        mean_val, lower, upper = SystemEvaluationMetrics.calculate_bootstrap_ci(data, num_bootstraps=500, ci_pct=95.0)

        self.assertTrue(lower < mean_val < upper)
        self.assertTrue(0.05 < lower < 0.15)
        self.assertTrue(0.05 < upper < 0.15)

    def test_ai_layer_evaluator_metrics(self):
        """Verifies AI Engineer QA layer automated evaluation metrics."""
        res = AIEngineerEvaluator.evaluate_ai_layer()

        self.assertIn("numerical_accuracy_pct", res)
        self.assertIn("hallucination_rate_pct", res)
        self.assertEqual(res["hallucination_rate_pct"], 0.0)  # Must refuse missing data queries
        self.assertEqual(res["evaluation_status"], "PASSED")

    def test_benchmark_runner_execution_and_reproducibility(self):
        """Verifies end-to-end benchmark execution and seed reproducibility."""
        rep1 = BenchmarkRunner.run_full_system_benchmark(seed=42)
        rep2 = BenchmarkRunner.run_full_system_benchmark(seed=42)

        self.assertEqual(rep1["reproducibility_status"], "PASSED_VERIFIED")
        self.assertEqual(rep1["dataset_version"], rep2["dataset_version"])
        self.assertEqual(rep1["telemetry_metrics"]["lap_time_mae_s"], rep2["telemetry_metrics"]["lap_time_mae_s"])


if __name__ == '__main__':
    unittest.main()
