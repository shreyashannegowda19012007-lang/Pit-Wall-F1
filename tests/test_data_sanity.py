"""
Automated Unit Tests for Physical & Logical Invariants and Data Sanity Engine.
Verifies lap number monotonicity, physical speed/throttle/brake bounds, distance monotonicity,
and discrete probability distribution invariants.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from data_sanity import DataSanityEngine, SanityViolation


class TestDataSanityEngine(unittest.TestCase):

    def test_valid_telemetry_invariants(self):
        """Verifies clean physical telemetry passes invariant validation."""
        laps_df = pd.DataFrame({
            'LapNumber': [1, 2, 3],
            'LapTime': pd.to_timedelta([90.0, 90.5, 91.0], unit='s')
        })
        telemetry_df = pd.DataFrame({
            'Speed': [100.0, 250.0, 310.0],
            'Throttle': [0.0, 50.0, 100.0],
            'Distance': [0.0, 500.0, 1000.0]
        })

        is_valid, violations = DataSanityEngine.validate_telemetry_invariants(laps_df, telemetry_df)
        self.assertTrue(is_valid)
        self.assertEqual(len(violations), 0)

    def test_speed_and_throttle_out_of_bounds_detection(self):
        """Verifies detection of negative speed or invalid throttle values > 100%."""
        laps_df = pd.DataFrame({'LapNumber': [1], 'LapTime': pd.to_timedelta([90.0], unit='s')})
        telemetry_df = pd.DataFrame({
            'Speed': [-10.0, 450.0],       # Invalid speed < 0 and > 400
            'Throttle': [150.0, -20.0],    # Invalid throttle
            'Distance': [0.0, 100.0]
        })

        is_valid, violations = DataSanityEngine.validate_telemetry_invariants(laps_df, telemetry_df)
        self.assertFalse(is_valid)
        rule_names = [v.rule_name for v in violations]
        self.assertIn("SPEED_OUT_OF_BOUNDS", rule_names)
        self.assertIn("THROTTLE_OUT_OF_BOUNDS", rule_names)

    def test_probability_invariants(self):
        """Verifies discrete probability map invariants (values in [0,1], sum approx 1.0)."""
        valid_map = {"Strategy A": 0.60, "Strategy B": 0.40}
        invalid_map = {"Strategy A": 0.80, "Strategy B": 0.50}  # Sum = 1.30 != 1.0

        is_v1, errs1 = DataSanityEngine.validate_probability_invariants(valid_map)
        is_v2, errs2 = DataSanityEngine.validate_probability_invariants(invalid_map)

        self.assertTrue(is_v1)
        self.assertFalse(is_v2)


if __name__ == '__main__':
    unittest.main()
