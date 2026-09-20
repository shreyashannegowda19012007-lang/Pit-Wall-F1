"""
Automated Unit, Integration & Lifecycle Test Suite for Production Data / ML Pipeline & MLOps Infrastructure.
Verifies DatasetRegistry SHA-256 checksum versioning, ModelRegistry quality gate approval & production promotion,
DriftDetector KS statistic and PSI drift detection (PSI > 0.25 trigger), end-to-end MLOps pipeline, and API routes.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from mlops_pipeline import DatasetRegistry, ModelRegistry, DriftDetector, ProductionMLOpsEngine
from telemetry_api import api_service


class TestMLOpsPipelineInfrastructure(unittest.TestCase):

    def test_dataset_registry_checksum_versioning(self):
        """Verifies DatasetRegistry calculates SHA-256 checksum and registers versioned dataset."""
        df = pd.DataFrame({"lap_time": [82.5, 82.8, 83.1], "tyre_age": [1, 2, 3]})
        ds_ver = DatasetRegistry.register_dataset("DS-TEST-01", "v1.0", df, ["tyre_age"])

        self.assertEqual(ds_ver.dataset_id, "DS-TEST-01")
        self.assertEqual(ds_ver.num_samples, 3)
        self.assertTrue(len(ds_ver.checksum_sha256) > 0)

    def test_model_registry_quality_gate(self):
        """Verifies ModelRegistry approves models passing MAE quality gate and rejects failing models."""
        good_metrics = {"mae": 0.12, "rmse": 0.15}
        bad_metrics = {"mae": 0.85, "rmse": 0.95}

        good_art = ModelRegistry.register_model("MDL-GOOD", "GoodModel", "v1.0", "Regression", "DS-TEST-01", good_metrics, mae_threshold=0.50)
        bad_art = ModelRegistry.register_model("MDL-BAD", "BadModel", "v1.0", "Regression", "DS-TEST-01", bad_metrics, mae_threshold=0.50)

        self.assertEqual(good_art.status, "APPROVED")
        self.assertEqual(bad_art.status, "REJECTED")

        # Promote approved model to PRODUCTION
        prod_art = ModelRegistry.promote_to_production("MDL-GOOD")
        self.assertEqual(prod_art.status, "PRODUCTION")

    def test_statistical_drift_detector(self):
        """Verifies DriftDetector identifies feature drift when PSI exceeds 0.25."""
        np.random.seed(42)
        baseline = np.random.normal(10.0, 1.0, 500)
        shifted = np.random.normal(15.0, 1.0, 500)  # Significant shift!

        drift = DriftDetector.detect_feature_drift("test_feature", baseline, shifted)

        self.assertTrue(drift.psi_score > 0.25)
        self.assertTrue(drift.is_drift_detected)

    def test_production_mlops_pipeline_execution(self):
        """Verifies full end-to-end MLOps pipeline run."""
        res = ProductionMLOpsEngine.run_end_to_end_mlops_pipeline("S-2024-SPAIN")

        self.assertEqual(res["pipeline_status"], "SUCCESS")
        self.assertIn("dataset_version", res)
        self.assertIn("production_model", res)
        self.assertIn("drift_monitoring", res)

    def test_api_service_mlops_route(self):
        """Verifies API route for triggering MLOps pipeline."""
        res = api_service.run_mlops_pipeline("S-2024-SPAIN")
        self.assertEqual(res["pipeline_status"], "SUCCESS")


if __name__ == '__main__':
    unittest.main()
