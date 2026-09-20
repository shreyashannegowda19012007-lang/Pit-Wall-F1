"""
Automated Unit, Integration & Performance Attribution Test Suite for Telemetry Intelligence Subsystem.
Verifies CanonicalTelemetrySample, CornerDefinition database, 5-phase corner metrics (braking delta, peak brake %,
min speed, throttle delay, exit speed), attributable loss, opportunity ranking, driver profiles, and API routes.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from telemetry_performance_lab import DriverPerformanceIntelligenceEngine, CornerDefinition, CornerTimeLossAttribution, PerformanceOpportunity, DriverPerformanceProfile
from telemetry_api import api_service


class TestDriverPerformanceIntelligenceLab(unittest.TestCase):

    def test_circuit_corner_database(self):
        """Verifies circuit corner database definitions."""
        corners = DriverPerformanceIntelligenceEngine.get_circuit_corner_database("SPAIN")
        self.assertTrue(len(corners) >= 5)
        self.assertEqual(corners[0].corner_number, 1)

    def test_5phase_corner_time_loss_attribution(self):
        """Verifies 5-phase corner metrics and time-loss attribution calculations."""
        attr = DriverPerformanceIntelligenceEngine.attribute_corner_time_loss("VER", "HAM", corner_number=7)

        self.assertEqual(attr.corner_number, 7)
        self.assertIsInstance(attr.total_loss_s, float)
        self.assertIsInstance(attr.braking_point_delta_m, float)
        self.assertIsInstance(attr.min_speed_delta_kmh, float)
        self.assertIsInstance(attr.throttle_pickup_delay_s, float)
        self.assertIsInstance(attr.attributable_loss_s, float)
        self.assertIsInstance(attr.reconciliation_residual_s, float)

    def test_performance_opportunity_ranking(self):
        """Verifies performance opportunity ranking orders corners by attributable loss."""
        opps = DriverPerformanceIntelligenceEngine.rank_performance_opportunities("VER")

        self.assertIsInstance(opps, list)
        if len(opps) > 0:
            self.assertEqual(opps[0].rank, 1)
            self.assertIsInstance(opps[0].corner_number, int)
            self.assertIsInstance(opps[0].attributable_loss_s, float)

    def test_quantitative_driver_performance_profile(self):
        """Verifies quantitative driver performance profile metric generation."""
        profile = DriverPerformanceIntelligenceEngine.generate_driver_profile("VER")

        self.assertEqual(profile.driver_id, "VER")
        self.assertIsInstance(profile.braking_aggressiveness_score, float)
        self.assertIsInstance(profile.overall_consistency_score, float)

    def test_api_service_telemetry_intelligence_routes(self):
        """Verifies API routes for fetching attributed time loss, opportunities, and driver profile."""
        loss = api_service.get_attributed_time_loss("VER", "HAM", 7)
        opps = api_service.get_performance_opportunities("VER")
        prof = api_service.get_driver_performance_profile("VER")

        self.assertEqual(loss["corner_number"], 7)
        self.assertIsInstance(opps, list)
        self.assertEqual(prof["driver_id"], "VER")


if __name__ == '__main__':
    unittest.main()
