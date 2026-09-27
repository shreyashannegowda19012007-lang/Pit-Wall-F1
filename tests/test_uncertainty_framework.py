"""
Automated Unit & Synthetic Validation Test Suite for Formal Uncertainty Framework.
Verifies distribution creation, interval calculations, probability vector normalization,
calibration metrics (Brier score, Log Loss, ECE), model versioning, and synthetic validation.
"""

import unittest
import numpy as np
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from probabilistic_model import ProbabilisticPrediction, validate_probability_vector, UncertaintyType, IntervalType
from calibration import ProbabilityCalibrationEngine
from bayesian_tyre_model import AdvancedTyreDegradationModel
from race_simulator import DriverState, RaceState
from probabilistic_service import ProbabilisticService


class TestUncertaintyFramework(unittest.TestCase):

    def test_probabilistic_prediction_container(self):
        pred = ProbabilisticPrediction(
            point_estimate=3.8,
            unit="position",
            distribution_type="DISCRETE_EMPIRICAL",
            mean=3.82,
            median=3.0,
            std_dev=1.2,
            lower_bound=2.0,
            upper_bound=5.0,
            interval_pct=0.95,
            sample_size=10000,
            model_name="TestModel",
            model_version="v2.4.0",
            data_quality="HIGH",
            assumptions=["Testing assumption 1"]
        )

        self.assertEqual(pred.point_estimate, 3.8)
        self.assertEqual(pred.model_version, "v2.4.0")
        self.assertIn("3.8 ± 1.2", pred.format_summary())

        p_dict = pred.to_dict()
        self.assertEqual(p_dict["data_quality"], "HIGH")
        self.assertIn("summary_text", p_dict)

    def test_probability_vector_normalization(self):
        # Valid normalized vector
        probs_valid = {f"P{i}": 0.05 for i in range(1, 21)}  # 20 * 0.05 = 1.0
        is_valid, total_sum = validate_probability_vector(probs_valid)
        self.assertTrue(is_valid)
        self.assertAlmostEqual(total_sum, 1.0)

        # Negative probability (invalid)
        probs_negative = {"P1": -0.1, "P2": 1.1}
        is_valid_neg, _ = validate_probability_vector(probs_negative)
        self.assertFalse(is_valid_neg)

    def test_calibration_metrics(self):
        preds = [0.9, 0.8, 0.2, 0.1, 0.95]
        actuals = [1, 1, 0, 0, 1]

        brier = ProbabilityCalibrationEngine.calculate_brier_score(preds, actuals)
        self.assertTrue(0.0 <= brier < 0.1)

        log_loss = ProbabilityCalibrationEngine.calculate_log_loss(preds, actuals)
        self.assertTrue(log_loss > 0.0)

        rel_data = ProbabilityCalibrationEngine.generate_reliability_diagram(preds, actuals, num_bins=5)
        self.assertEqual(rel_data['num_bins'], 5)
        self.assertTrue(rel_data['expected_calibration_error'] < 0.2)

    def test_probabilistic_tyre_degradation(self):
        res = AdvancedTyreDegradationModel.evaluate_tyre_health(
            compound="MEDIUM",
            laps_on_tyre=15,
            track_temp=35.0,
            fuel_load_kg=45.0
        )

        self.assertIn("probabilistic_degradation", res)
        p_deg = res["probabilistic_degradation"]
        self.assertEqual(p_deg["distribution_type"], "BAYESIAN_POSTERIOR")
        self.assertEqual(p_deg["interval_type"], IntervalType.CREDIBLE)
        self.assertTrue(p_deg["lower_bound"] <= p_deg["mean"] <= p_deg["upper_bound"])




if __name__ == '__main__':
    unittest.main()
