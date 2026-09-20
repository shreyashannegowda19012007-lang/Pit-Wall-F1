"""
Automated Unit, Integration & Information Cutoff Verification Test Suite for Historical Replay Subsystem.
Verifies HistoricalReplaySession initialization, FutureDataGuard strict access controls,
decision checkpoint snapshotting, tri-strategy regret vs hindsight optimum, and API routes.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from historical_replay_evaluator import HistoricalReplayEngine, HistoricalReplaySession, FutureDataGuard, DecisionCheckpoint, HistoricalEvaluationReport
from telemetry_api import api_service


class TestHistoricalReplayEvaluator(unittest.TestCase):

    def test_historical_replay_session_initialization(self):
        """Verifies replay session initialization with random seed."""
        sess = HistoricalReplayEngine.start_historical_replay(2024, 9, "R", seed=42)

        self.assertEqual(sess.replay_id, "REPLAY-2024-R09-R")
        self.assertEqual(sess.seed, 42)
        self.assertEqual(sess.status, "COMPLETED")

    def test_future_data_guard_access_control(self):
        """Verifies FutureDataGuard blocks access to laps beyond information cutoff."""
        guard = FutureDataGuard(cutoff_lap=22, cutoff_timestamp=1000.0)

        # Valid access up to cutoff
        self.assertTrue(guard.validate_lap_access(22))
        self.assertTrue(guard.validate_timestamp_access(1000.0))

        # Blocked access beyond cutoff
        with self.assertRaises(ValueError) as ctx:
            guard.validate_lap_access(23)
        self.assertIn("FUTURE_LEAKAGE_DETECTED", str(ctx.exception))

    def test_evaluate_historical_session_checkpoints(self):
        """Verifies evaluation report calculates decision checkpoints and regret."""
        report = HistoricalReplayEngine.evaluate_historical_session(2024, 9, "VER")

        self.assertEqual(len(report.checkpoints), 2)
        self.assertEqual(report.checkpoints[0].lap_number, 22)
        self.assertEqual(report.checkpoints[0].quality_classification, "OPTIMAL_DECISION")
        self.assertEqual(report.avg_strategy_regret_s, 0.000)

    def test_api_service_replay_routes(self):
        """Verifies API routes for historical replay start and evaluation summary."""
        sess = api_service.start_historical_replay(2024, 9, "R")
        report = api_service.evaluate_historical_session(2024, 9, "VER")

        self.assertEqual(sess["replay_id"], "REPLAY-2024-R09-R")
        self.assertEqual(len(report["checkpoints"]), 2)
        self.assertTrue(report["overall_mae_s"] <= 0.50)


if __name__ == '__main__':
    unittest.main()
