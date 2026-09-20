"""
Automated Test Suite for Scientifically Defensible Telemetry Analysis & Time-Loss Attribution.
Verifies validation, safe cleaning, distance alignment, corner detection, integration, and missing channel handling.
"""

import unittest
import numpy as np
import pandas as pd
import sys
import os

# Add src directory to python path
sys.path.insert(0, os.path.abspath('src'))

from telemetry_model import CanonicalTelemetryPoint, CanonicalLapTelemetry, TelemetryUnits
from telemetry_validation import validate_telemetry_df, TelemetryValidationResult
from telemetry_cleaning import clean_telemetry_df
from lap_alignment import align_laps_by_distance
from corner_detection import detect_corners_from_telemetry, CornerWindow
from time_loss_attribution import analyze_corner_performance, CornerPerformanceAnalysis


class TestTelemetryAnalysis(unittest.TestCase):

    def setUp(self):
        # Create synthetic reference lap telemetry (1000m length)
        dist_grid = np.linspace(0.0, 1000.0, 501)  # 2m resolution
        # Speed profile: 250 km/h baseline, corner deceleration at 400m-600m down to 100 km/h (apex at 500m)
        speed_ref = 250.0 - 150.0 * np.exp(-((dist_grid - 500.0) / 60.0)**2)
        
        # Throttle & Brake
        throttle_ref = np.where(speed_ref < 240, 0.0, 100.0)
        brake_ref = np.where(dist_grid < 500.0, (250.0 - speed_ref) / 150.0 * 100.0, 0.0)
        time_ref = pd.to_timedelta(np.cumsum(0.002 / np.maximum(speed_ref / 3.6, 1.0) * 1000.0), unit='s')

        self.df_ref = pd.DataFrame({
            'Distance': dist_grid,
            'Speed': speed_ref,
            'Throttle': throttle_ref,
            'Brake': brake_ref,
            'nGear': np.where(speed_ref < 150, 3, 7),
            'Time': time_ref
        })

        # Create target lap: Identical to ref except driver is slower in corner (drops to 85 km/h, brakes 10m earlier)
        speed_tgt = 250.0 - 165.0 * np.exp(-((dist_grid - 500.0) / 60.0)**2)
        throttle_tgt = np.where(speed_tgt < 240, 0.0, 100.0)
        brake_tgt = np.where(dist_grid < 490.0, (250.0 - speed_tgt) / 165.0 * 100.0, 0.0)
        time_tgt = pd.to_timedelta(np.cumsum(0.002 / np.maximum(speed_tgt / 3.6, 1.0) * 1000.0), unit='s')

        self.df_tgt = pd.DataFrame({
            'Distance': dist_grid,
            'Speed': speed_tgt,
            'Throttle': throttle_tgt,
            'Brake': brake_tgt,
            'nGear': np.where(speed_tgt < 150, 3, 7),
            'Time': time_tgt
        })

    def test_canonical_telemetry_model(self):
        pt = CanonicalTelemetryPoint(
            timestamp_s=10.5,
            distance_m=250.0,
            speed_kmh=185.4,
            throttle_pct=100.0,
            brake_pct=0.0,
            gear=5
        )
        self.assertEqual(pt.distance_m, 250.0)
        self.assertEqual(pt.speed_kmh, 185.4)

        lap = CanonicalLapTelemetry(
            driver_id="VER",
            lap_number=14,
            lap_time_s=85.421,
            cleaned_df=self.df_ref
        )
        avail = lap.channel_availability
        self.assertTrue(avail['distance'])
        self.assertTrue(avail['speed'])
        self.assertFalse(avail['steering'])

    def test_telemetry_validation(self):
        val_res = validate_telemetry_df(self.df_ref)
        self.assertTrue(val_res.is_valid)
        self.assertEqual(val_res.validation_status, "PASSED")
        self.assertTrue(val_res.channel_availability['speed'])

        # Validation on empty df
        val_empty = validate_telemetry_df(pd.DataFrame())
        self.assertFalse(val_empty.is_valid)
        self.assertEqual(val_empty.validation_status, "FAILED")

    def test_telemetry_cleaning(self):
        # Create un-sorted df with duplicate and boolean brake
        dirty_df = pd.DataFrame({
            'Distance': [10.0, 5.0, 5.0, 15.0, 20.0],
            'Speed': [200.0, 180.0, 180.0, 220.0, 240.0],
            'Throttle': [100.0, 50.0, 50.0, 100.0, 100.0],
            'Brake': [False, True, True, False, False]
        })

        cleaned, meta = clean_telemetry_df(dirty_df)
        self.assertFalse(cleaned.empty)
        self.assertTrue(np.all(np.diff(cleaned['Distance'].values) >= 0.0))
        self.assertEqual(cleaned['Brake'].dtype, float)
        self.assertEqual(meta['rows_removed'], 1)  # 1 duplicate removed

    def test_distance_lap_alignment(self):
        aligned_df, meta = align_laps_by_distance(
            self.df_tgt, self.df_ref,
            grid_step_m=1.0,
            driver_a_code="VER",
            driver_b_code="HAM"
        )
        self.assertFalse(aligned_df.empty)
        self.assertIn('Distance', aligned_df.columns)
        self.assertIn('DeltaTime', aligned_df.columns)
        self.assertAlmostEqual(aligned_df['Distance'].iloc[0], 0.0)
        self.assertAlmostEqual(aligned_df['Distance'].iloc[-1], 1000.0)

    def test_identical_laps_zero_time_loss(self):
        # Comparing a lap against itself must yield zero time delta
        aligned_df, _ = align_laps_by_distance(self.df_ref, self.df_ref, grid_step_m=1.0)
        max_delta = np.max(np.abs(aligned_df['DeltaTime'].values))
        self.assertAlmostEqual(max_delta, 0.0, delta=0.01)

    def test_corner_detection(self):
        corners = detect_corners_from_telemetry(self.df_ref['Distance'].values, self.df_ref['Speed'].values)
        self.assertTrue(len(corners) >= 1)
        c = corners[0]
        self.assertAlmostEqual(c.apex_m, 500.0, delta=20.0)

    def test_time_loss_attribution_physics(self):
        aligned_df, _ = align_laps_by_distance(self.df_tgt, self.df_ref, grid_step_m=1.0)
        corners = detect_corners_from_telemetry(aligned_df['Distance'].values, aligned_df['Speed_B'].values)
        self.assertTrue(len(corners) >= 1)
        
        ca = analyze_corner_performance(aligned_df, corners[0], "TGT", "REF")
        # Target was slower in corner -> time loss must be positive
        self.assertTrue(ca.time_loss_seconds > 0.0)
        # Apex speed delta must be negative (target slower)
        self.assertTrue(ca.minimum_speed_delta_kmh < 0.0)

    def test_missing_channel_graceful_handling(self):
        # Telemetry missing Brake & Steering
        no_brake_df = self.df_ref.drop(columns=['Brake'])
        val_res = validate_telemetry_df(no_brake_df)
        self.assertTrue(val_res.is_valid)
        self.assertFalse(val_res.channel_availability['brake'])
        self.assertFalse(val_res.channel_availability['steering'])

        aligned_df, _ = align_laps_by_distance(no_brake_df, self.df_ref)
        corners = detect_corners_from_telemetry(aligned_df['Distance'].values, aligned_df['Speed_B'].values)
        ca = analyze_corner_performance(aligned_df, corners[0], "TGT", "REF")
        # Steering angle metric should be None/unavailable without error
        self.assertFalse(ca.available_metrics['steering'])
        self.assertIsNone(ca.peak_brake_delta_pct)


if __name__ == '__main__':
    unittest.main()
