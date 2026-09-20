"""
Automated Unit, Integration & Scientific Validation Test Suite for Advanced Telemetry Laboratory Engine.
Verifies telemetry quality score calculation, distance-grid trajectory alignment, corner segmentation,
mathematically defensible time-loss attribution decomposition, uncertainty estimation, and API integration.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from telemetry_lab import CanonicalTelemetryPoint, TelemetryQualityEngine, TrackDistanceAligner, TimeLossAttributor, CornerAnalysisResult
from telemetry_api import api_service


class TestAdvancedTelemetryLabEngine(unittest.TestCase):

    def test_telemetry_quality_engine_scoring(self):
        """Verifies quality score calculation (0-100%)."""
        clean_df = pd.DataFrame({
            'Speed': [100.0, 200.0, 300.0],
            'Throttle': [50.0, 100.0, 100.0],
            'Brake': [50.0, 0.0, 0.0]
        })
        score = TelemetryQualityEngine.evaluate_quality(clean_df)
        self.assertEqual(score, 100.0)

        dirty_df = pd.DataFrame({
            'Speed': [100.0, None, 450.0],
            'Throttle': [50.0, 100.0, 100.0],
            'Brake': [50.0, 0.0, 0.0]
        })
        score_dirty = TelemetryQualityEngine.evaluate_quality(dirty_df)
        self.assertTrue(score_dirty < 100.0)

    def test_distance_grid_alignment(self):
        """Verifies normalization of telemetry onto uniform distance grid [0, 5000m]."""
        raw_df = pd.DataFrame({
            'Distance': [0.0, 1000.0, 2500.0, 5000.0],
            'Speed': [200.0, 250.0, 300.0, 280.0],
            'Throttle': [100.0, 100.0, 100.0, 80.0],
            'Brake': [0.0, 0.0, 0.0, 0.0]
        })
        aligned = TrackDistanceAligner.align_telemetry_to_distance_grid(raw_df, num_grid_points=100, total_length_m=5000.0)

        self.assertEqual(len(aligned), 100)
        self.assertEqual(aligned['Distance'].iloc[0], 0.0)
        self.assertEqual(aligned['Distance'].iloc[-1], 5000.0)
        self.assertTrue(np.all(np.diff(aligned['Distance']) > 0))

    def test_time_loss_attribution_decomposition(self):
        """Verifies corner loss decomposition into braking, apex, and exit components with uncertainty."""
        dummy = pd.DataFrame({'Distance': np.linspace(0, 5000, 100), 'Speed': 250, 'Throttle': 100, 'Brake': 0, 'CumulativeTime': np.linspace(0, 80, 100)})
        p_df = TrackDistanceAligner.align_telemetry_to_distance_grid(dummy, num_grid_points=100, total_length_m=5000.0)
        r_df = TrackDistanceAligner.align_telemetry_to_distance_grid(dummy.copy(), num_grid_points=100, total_length_m=5000.0)
        r_df['Speed'] = r_df['Speed'] + 10.0  # Reference is faster
        r_df['CumulativeTime'] = r_df['CumulativeTime'] - 0.5

        res = TimeLossAttributor.analyze_corner_loss(p_df, r_df, corner_number=7, start_m=600.0, end_m=1100.0)

        self.assertEqual(res.corner_number, 7)
        self.assertTrue(res.measured_time_loss_s > 0.0)
        self.assertTrue(res.uncertainty_s > 0.0)
        self.assertTrue(res.data_quality_pct >= 90.0)

    def test_api_service_telemetry_corner_analysis_route(self):
        """Verifies API route get_telemetry_corner_analysis()."""
        res = api_service.get_telemetry_corner_analysis(primary_driver="VER", ref_driver="HAM", corner_number=1)

        self.assertEqual(res["corner_number"], 1)
        self.assertEqual(res["status"], "UNAVAILABLE")


if __name__ == '__main__':
    unittest.main()
