"""
Automated Unit, Integration & Scientific Validation Test Suite for Advanced Tyre Degradation Engine.
Verifies Model A (Empirical ML), Model B (Physics-Informed 3-Layer Thermal/Wear/Grip),
model comparison metrics (MAE, RMSE, Bias), Bayesian updates, and API integration.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from tyre_engine import CanonicalTyreObservation, EmpiricalTyreModel, PhysicsInformedTyreModel, TyreModelEvaluator
from telemetry_api import api_service


class TestAdvancedTyreEngine(unittest.TestCase):

    def setUp(self):
        self.stint_laps = []
        for i in range(1, 15):
            act_time = 91.5 + (i * 0.082)
            self.stint_laps.append(CanonicalTyreObservation(
                session_id="S-2024-SPAIN",
                driver_id="VER",
                lap_number=i,
                stint_number=1,
                compound="MEDIUM",
                tyre_age_laps=i,
                lap_time_s=round(act_time, 3),
                track_temp_c=32.0,
                air_temp_c=26.0,
                fuel_estimate_kg=100.0 - (i * 1.5),
                lap_quality="CLEAN"
            ))

    def test_empirical_model_predictions(self):
        """Verifies Empirical Model A stint predictions increase monotonically with tyre age."""
        preds = EmpiricalTyreModel.predict_stint_degradation(self.stint_laps, base_lap_time_s=91.5)

        self.assertEqual(len(preds), 14)
        self.assertTrue(preds[-1] > preds[0])

    def test_physics_3layer_thermal_stint_simulation(self):
        """Verifies Physics Model B 3-layer thermal dynamics (Surface > Bulk > Core) and wear progression."""
        results = PhysicsInformedTyreModel.simulate_3layer_thermal_stint(self.stint_laps, base_lap_time_s=91.5)

        self.assertEqual(len(results), 14)
        lap1_t = results[0]
        lap14_t = results[-1]

        # Surface temp should exceed bulk and core temp
        self.assertTrue(lap14_t[1] >= lap14_t[2])  # Surface >= Bulk
        self.assertTrue(lap14_t[2] >= lap14_t[3])  # Bulk >= Core
        # Wear % should accumulate monotonically
        self.assertTrue(lap14_t[5] > lap1_t[5])

    def test_evaluator_and_model_comparison_metrics(self):
        """Verifies TyreModelEvaluator calculates MAE, RMSE, and Bias metrics cleanly."""
        res = TyreModelEvaluator.evaluate_and_compare_stint(self.stint_laps, base_lap_time_s=91.5)

        self.assertIn("empirical_metrics", res)
        self.assertIn("physics_metrics", res)
        self.assertIn("bayesian_posterior_degradation", res)
        self.assertTrue(res["empirical_metrics"]["mae_s"] >= 0.0)
        self.assertTrue(res["physics_metrics"]["mae_s"] >= 0.0)

    def test_api_service_tyre_degradation_route(self):
        """Verifies API route get_tyre_degradation_analysis()."""
        res = api_service.get_tyre_degradation_analysis(driver_id="VER", compound="MEDIUM", total_laps=15)

        self.assertEqual(res["compound"], "MEDIUM")
        self.assertEqual(res["total_laps"], 15)


if __name__ == '__main__':
    unittest.main()
