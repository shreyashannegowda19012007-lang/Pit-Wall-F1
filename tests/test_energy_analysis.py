"""
Automated Unit, Integration & Scientific Validation Test Suite for DRS, ERS & Battery Energy Subsystem.
Verifies strict source classification tagging (OBSERVED, DERIVED, MODELLED, UNAVAILABLE),
Pre-2026 DRS zone speed gain analysis, track segment classification, 2026+ bounded ERS battery SOC
physics model (20% <= SOC <= 100%), and API routes.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from energy_analysis import SourceClassification, EnergyDataContract, DRSAnalysisEngine, ERSBatteryModelEngine
from telemetry_api import api_service


class TestEnergyAnalysisSubsystem(unittest.TestCase):

    def test_source_classification_tags(self):
        """Verifies explicit source classification constants."""
        self.assertEqual(SourceClassification.OBSERVED, "OBSERVED")
        self.assertEqual(SourceClassification.DERIVED, "DERIVED")
        self.assertEqual(SourceClassification.MODELLED, "MODELLED")
        self.assertEqual(SourceClassification.UNAVAILABLE, "UNAVAILABLE")

    def test_pre_2026_drs_zone_analysis(self):
        """Verifies Pre-2026 DRS zone activation and speed gain calculation."""
        res = DRSAnalysisEngine.analyze_drs_zone(pd.DataFrame(), driver_id="VER", lap_number=15, zone_id=1)

        self.assertEqual(res.driver_id, "VER")
        self.assertEqual(res.zone_id, 1)
        self.assertEqual(res.source_classification, SourceClassification.DERIVED)
        self.assertTrue(res.speed_delta_kmh > 0.0)

    def test_track_segment_classifier(self):
        """Verifies classification of track segments into STRAIGHT, BRAKING, CORNER, etc."""
        self.assertEqual(ERSBatteryModelEngine.classify_track_segment(speed_kmh=290.0, throttle_pct=100.0, brake_pct=0.0), "STRAIGHT")
        self.assertEqual(ERSBatteryModelEngine.classify_track_segment(speed_kmh=150.0, throttle_pct=0.0, brake_pct=85.0), "BRAKING")
        self.assertEqual(ERSBatteryModelEngine.classify_track_segment(speed_kmh=120.0, throttle_pct=20.0, brake_pct=0.0), "CORNER")

    def test_2026_ers_battery_soc_bounded_physics(self):
        """Verifies 2026+ ERS battery state-of-charge (SOC) stays strictly within [20%, 100%] bounds and is tagged MODELLED."""
        records = ERSBatteryModelEngine.simulate_2026_energy_lap(pd.DataFrame(), initial_soc_pct=80.0, driver_id="VER", lap_number=15)

        self.assertTrue(len(records) > 0)
        for r in records:
            self.assertEqual(r.source_classification, SourceClassification.MODELLED)
            self.assertTrue(20.0 <= r.battery_soc_pct <= 100.0)

    def test_api_service_energy_routes(self):
        """Verifies API routes for DRS and ERS energy analysis."""
        drs_res = api_service.get_drs_zone_analysis("VER", 15, 1)
        ers_res = api_service.get_ers_energy_analysis("VER", 15)

        self.assertIn("speed_delta_kmh", drs_res)
        self.assertTrue(len(ers_res) > 0)
        self.assertEqual(ers_res[0]["source_classification"], SourceClassification.MODELLED)


if __name__ == '__main__':
    unittest.main()
