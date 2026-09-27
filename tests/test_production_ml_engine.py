"""
Automated Unit, Integration & Explainability Test Suite for Production ML Subsystem.
Verifies ModelCard registry retrieval, Quantile Lap Time regression (P10/P50/P90),
SHAP feature attribution explanations, Isotonic Probability Calibration, and API routes.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

from src.production_ml_engine import ProductionMLEngine, ModelCard, QuantileLapTimePrediction, SHAPExplanation
from src.telemetry_api import api_service


class TestProductionMLEngine(unittest.TestCase):

    def test_model_catalogue(self):
        """Verifies production model catalogue contains registered models with quality gates."""
        cat = ProductionMLEngine.get_model_catalogue()
        self.assertGreaterEqual(len(cat), 1)
        # Should be ACTIVE or PROMOTED or at least have a status
        self.assertIn(cat[0].status, ["ACTIVE", "PROMOTED", "PRODUCTION", "TRAINED", "READY"])

    def test_quantile_lap_time_prediction(self):
        """Verifies QuantileLapTimePrediction outputs P10 <= P50 <= P90 quantiles."""
        q_pred = ProductionMLEngine.predict_quantile_lap_time("VER", 23, base_pace_s=81.240, tyre_age_laps=15)

        self.assertTrue(q_pred.p10_lap_time_s <= q_pred.p50_lap_time_s <= q_pred.p90_lap_time_s)
        self.assertGreater(q_pred.p50_lap_time_s, 60.0)

    def test_shap_feature_attribution(self):
        """Verifies SHAP explanation for a prediction."""
        exp = ProductionMLEngine.explain_lap_time_prediction("VER", 23)

        self.assertEqual(exp.prediction_id, "PRED-VER-L23")
        self.assertEqual("XGBoostRegressor SHAP Feature Attributions", exp.explanation_summary)
        self.assertGreater(len(exp.feature_contributions), 0)

    def test_calibrated_overtake_probability(self):
        """Verifies Platt/Isotonic calibrated overtake probability."""
        cal = ProductionMLEngine.predict_calibrated_overtake_probability("NOR", "VER", gap_s=0.85)

        self.assertEqual(cal["attacker_id"], "NOR")
        self.assertIn("status", cal)
        self.assertIn("calibrated_probability_pct", cal)
        self.assertTrue(0.0 <= cal["calibrated_probability_pct"] <= 100.0)

    def test_api_service_ml_routes(self):
        """Verifies API routes for model catalogue, quantile prediction, SHAP explanation, and calibrated probability."""
        cat = api_service.get_ml_model_catalogue()
        q_pred = api_service.predict_quantile_lap_time("VER", 23)
        exp = api_service.explain_lap_time_prediction("VER", 23)
        cal = api_service.predict_calibrated_overtake_probability("NOR", "VER", 0.85)

        self.assertGreaterEqual(len(cat), 1)
        self.assertTrue(q_pred["p10_lap_time_s"] <= q_pred["p50_lap_time_s"] <= q_pred["p90_lap_time_s"])
        self.assertEqual("XGBoostRegressor SHAP Feature Attributions", exp["explanation_summary"])
        self.assertIn("status", cal)


if __name__ == '__main__':
    unittest.main()
