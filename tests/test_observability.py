"""
Automated Unit Tests for Observability & Operational Counters Manager.
Verifies telemetry point counters, simulation execution metrics, backtest decision tracking,
API error rate metrics, and alert condition triggers.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from observability import ObservabilityManager


class TestObservabilityManager(unittest.TestCase):

    def test_operational_counters_increment(self):
        """Verifies operational counter increments for telemetry, simulations, and API requests."""
        obs = ObservabilityManager()
        obs.record_telemetry_points(1500)
        obs.record_simulations(10000)
        obs.record_replay_decisions(5)
        obs.record_api_request(is_error=False)

        summary = obs.get_metrics_summary()
        self.assertEqual(summary["telemetry_points_processed"], 1500)
        self.assertEqual(summary["simulations_executed"], 10000)
        self.assertEqual(summary["replay_decisions_evaluated"], 5)
        self.assertEqual(summary["api_requests_total"], 1)
        self.assertEqual(summary["api_errors_total"], 0)
        self.assertEqual(summary["status"], "HEALTHY")

    def test_alert_condition_trigger_on_high_error_rate(self):
        """Verifies alert condition triggering when API error rate exceeds 5.0%."""
        obs = ObservabilityManager()
        for _ in range(10):
            obs.record_api_request(is_error=False)
        for _ in range(2):
            obs.record_api_request(is_error=True)  # 2 / 12 = 16.7% error rate

        summary = obs.get_metrics_summary()
        self.assertAlmostEqual(summary["api_error_rate_pct"], 16.67, places=1)
        self.assertEqual(summary["status"], "WARNING")
        self.assertTrue(len(summary["active_alerts"]) > 0)


if __name__ == '__main__':
    unittest.main()
