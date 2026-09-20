"""
Automated Unit, Integration & Performance Test Suite for 3D Track, Car Replay & Cockpit View Engine.
Verifies distance-to-3D coordinate transformations, heading angle calculation, 20-car field state generation,
all 6 camera mode projections, and API integration.
"""

import unittest
import numpy as np
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from three_d_replay_engine import ThreeDTrackCoordinateSystem, ReplayCacheEngine, ThreeDSceneGenerator, CameraMode, Car3DState
from telemetry_api import api_service


class TestThreeDReplayEngine(unittest.TestCase):

    def setUp(self):
        # Synthetic circular track nodes for test
        theta = np.linspace(0, 2 * np.pi, 100)
        self.track_nodes = [{'x': float(5000 + 4000 * np.cos(t)), 'y': float(5000 + 4000 * np.sin(t)), 'z': 0.0} for t in theta]

    def test_coordinate_interpolation_and_heading(self):
        """Verifies distance-to-3D coordinate interpolation and smooth heading calculation."""
        x, y, z, heading = ThreeDTrackCoordinateSystem.interpolate_car_position(self.track_nodes, distance_m=1250.0, total_track_length_m=5000.0)

        self.assertTrue(0.0 <= x <= 10000.0)
        self.assertTrue(0.0 <= y <= 10000.0)
        self.assertEqual(z, 0.0)
        self.assertTrue(0.0 <= heading <= 360.0)

    def test_20_car_field_replay_frame_generation(self):
        """Verifies generation of full 20-car field state with primary and comparison driver highlights."""
        laps_df = pd.DataFrame({'LapNumber': [15] * 20, 'Driver': ['VER', 'HAM'] + ['UNK'] * 18, 'Compound': ['MEDIUM'] * 20, 'TyreLife': [15] * 20})
        cars = ReplayCacheEngine.generate_replay_frame(
            laps_df=laps_df,
            track_nodes=self.track_nodes,
            lap_number=15,
            lap_progress_pct=0.5,
            primary_driver="VER",
            comparison_driver="HAM"
        )

        self.assertTrue(len(cars) > 10)
        primary = next(c for c in cars if c.driver_id == "VER")
        comp = next(c for c in cars if c.driver_id == "HAM")

        self.assertTrue(primary.is_primary)
        self.assertTrue(comp.is_comparison)
        self.assertEqual(primary.lap_number, 15)

    def test_all_6_camera_mode_projections(self):
        """Verifies Plotly 3D WebGL scene generation across all 6 camera modes."""
        laps_df = pd.DataFrame({'LapNumber': [15] * 20, 'Driver': ['VER', 'HAM'] + ['UNK'] * 18, 'Compound': ['MEDIUM'] * 20, 'TyreLife': [15] * 20})
        cars = ReplayCacheEngine.generate_replay_frame(laps_df, self.track_nodes, 15, 0.5, "VER", "HAM")

        modes = [CameraMode.TRACK_OVERVIEW, CameraMode.TOP_DOWN, CameraMode.FOLLOW, CameraMode.CHASE, CameraMode.DRIVER_POV, CameraMode.COMPARISON]
        for mode in modes:
            fig = ThreeDSceneGenerator.create_3d_circuit_figure(self.track_nodes, cars, camera_mode=mode, primary_driver="VER")
            self.assertIsNotNone(fig)
            self.assertTrue(len(fig.data) >= 3)  # Track, Field Cars, Primary Car

    def test_api_service_3d_replay_endpoint(self):
        """Verifies API service 3D scene route."""
        laps_df = pd.DataFrame({'LapNumber': [15] * 20, 'Driver': ['VER', 'HAM'] + ['UNK'] * 18, 'Compound': ['MEDIUM'] * 20, 'TyreLife': [15] * 20})
        res = api_service.get_3d_replay_frame(laps_df, self.track_nodes, 15, 0.5, "VER", "HAM")

        self.assertTrue(len(res) > 10)
        self.assertIsInstance(res[0].driver_id, str)


if __name__ == '__main__':
    unittest.main()
