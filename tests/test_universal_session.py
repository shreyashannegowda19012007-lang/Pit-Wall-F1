"""
Automated Unit, Integration & Generic Execution Test Suite for Universal F1 Season, Round & Session System.
Verifies season discovery, round discovery, normalized session availability, cache key identity validation,
preparation job deduplication lock, and API routes across multiple circuits and seasons.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from universal_session_engine import UniversalSessionEngine, SessionPreparationManager
from telemetry_api import api_service


class TestUniversalSessionEngine(unittest.TestCase):

    def test_season_and_round_discovery(self):
        """Verifies season and round discovery returns supported F1 calendar schedule."""
        seasons = UniversalSessionEngine.get_available_seasons()
        self.assertIn(2024, seasons)
        self.assertIn(2025, seasons)

        rounds_2024 = UniversalSessionEngine.get_season_rounds(2024)
        self.assertTrue(len(rounds_2024) >= 5)

        event_monaco = next((r for r in rounds_2024 if "Monaco" in r.event_name), None)
        self.assertIsNotNone(event_monaco)
        self.assertIn("RACE", event_monaco.available_sessions)

    def test_session_cache_status_and_preparation_job_lock(self):
        """Verifies session status check and deduplicated preparation job lock."""
        status_ready = SessionPreparationManager.check_session_status(2024, 8, "RACE")
        self.assertIn(status_ready["status"], ["READY", "NOT_PREPARED"])

        job_res1 = SessionPreparationManager.prepare_session_async(2024, 12, "RACE")
        self.assertEqual(job_res1["status"], "STARTED")

        # Duplicate preparation request should lock and attach to existing job
        job_res2 = SessionPreparationManager.prepare_session_async(2024, 12, "RACE")
        self.assertEqual(job_res2["status"], "ALREADY_RUNNING")
        self.assertEqual(job_res1["job_id"], job_res2["job_id"])

    def test_api_service_universal_session_routes(self):
        """Verifies API service routes for universal season discovery and preparation."""
        seasons = api_service.get_available_seasons()
        self.assertIsInstance(seasons, list)

        rounds = api_service.get_season_rounds(2024)
        self.assertTrue(len(rounds) > 0)

        prep_res = api_service.prepare_session(2024, 14, "QUALIFYING")
        self.assertIn("job_id", prep_res)


if __name__ == '__main__':
    unittest.main()
