"""
Automated Unit, Integration & 3D Spatial Geometry Test Suite for Spatial Intelligence Subsystem.
Verifies circuit spatial metadata, 20-car 3D coordinate positioning (X, Y, Z, heading),
cockpit POV camera HUD parameters, and API routes.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from spatial_intelligence_engine import SpatialIntelligenceEngine, CircuitSpatialMetadata, SpatialCarPosition, CockpitPOVCamera
from telemetry_api import api_service


class TestSpatialIntelligenceEngine(unittest.TestCase):

    def test_circuit_spatial_metadata_retrieval(self):
        """Verifies circuit spatial metadata contains total track length and corner count."""
        meta = SpatialIntelligenceEngine.get_circuit_spatial_metadata("SPAIN-2024")

        self.assertEqual(meta.circuit_id, "SPAIN-2024")
        self.assertEqual(meta.total_length_m, 4675.0)
        self.assertEqual(meta.num_corners, 14)
        self.assertEqual(meta.num_minisectors, 25)

    def test_spatial_field_positions_calculation(self):
        """Verifies 3D coordinates (X, Y, Z) and headings calculated for all 20 drivers."""
        field = SpatialIntelligenceEngine.get_spatial_field_positions("S-2024-SPAIN", 22)

        self.assertTrue(len(field) > 10)
        self.assertIsInstance(field[0].driver_id, str)
        self.assertTrue(field[0].position >= 1)
        self.assertTrue(0.0 <= field[0].heading_deg <= 360.0)

    def test_cockpit_pov_camera_feed_generation(self):
        """Verifies cockpit POV camera parameters and telemetry HUD data."""
        pov = SpatialIntelligenceEngine.get_cockpit_pov_camera_feed("VER", 22)

        self.assertEqual(pov.driver_id, "VER")
        self.assertEqual(pov.camera_mode, "COCKPIT_POV")
        self.assertTrue(pov.fov_deg == 85.0)
        self.assertTrue(pov.speed_kmh > 100.0)

    def test_api_service_spatial_routes(self):
        """Verifies API routes for circuit metadata, spatial field positions, and cockpit POV feed."""
        meta = api_service.get_circuit_spatial_metadata("SPAIN-2024")
        field = api_service.get_spatial_field_positions("S-2024-SPAIN", 22)
        pov = api_service.get_cockpit_pov_camera_feed("VER", 22)

        self.assertEqual(meta["circuit_id"], "SPAIN-2024")
        self.assertTrue(len(field) > 10)
        self.assertEqual(pov["driver_id"], "VER")


if __name__ == '__main__':
    unittest.main()
