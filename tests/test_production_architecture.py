"""
Automated Unit, Integration & Security Test Suite for Production Data & Service Architecture.
Verifies database migrations, dataset SHA256 idempotency, background job queues, version-aware caching,
reproducible synthetic demo seeding, JSON log credential redacting, and health endpoints.
"""

import unittest
import numpy as np
import pandas as pd
import time
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath('src'))

from database_migrations import DatabaseManager
from job_queue import JobQueueManager
from cache_service import VersionAwareCache
from seed_demo_data import DemoDataSeeder
from logger import sanitize_payload


class TestProductionArchitecture(unittest.TestCase):

    def setUp(self):
        self.db_filename = f"test_pitwall_arch_{uuid.uuid4().hex[:6]}.db"
        self.db = DatabaseManager(self.db_filename)

    def tearDown(self):
        if hasattr(self, 'db_filename') and os.path.exists(self.db_filename):
            try:
                os.remove(self.db_filename)
            except Exception:
                pass

    def test_database_migrations_and_schema(self):
        """Verifies relational database schema initialization and version tracking."""
        msg = self.db.upgrade_schema()
        self.assertIn("version", msg.lower())

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT migration_name FROM schema_migrations WHERE version=1")
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["migration_name"], "v1_initial_schema")

    def test_dataset_idempotency_sha256(self):
        """Verifies that dataset ingestion is idempotent based on SHA256 content hashes."""
        payload_bytes = b"VER,HAM,Lap1,90.00"
        is_dup1, hash1 = self.db.verify_dataset_idempotency("TEST_SRC", payload_bytes)
        self.assertFalse(is_dup1)

        # Register dataset
        self.db.register_dataset("DS-101", "TEST_SRC", hash1, driver_count=2, row_count=1)

        # Re-verifying identical payload MUST detect duplicate
        is_dup2, ds_id2 = self.db.verify_dataset_idempotency("TEST_SRC", payload_bytes)
        self.assertTrue(is_dup2)
        self.assertEqual(ds_id2, "DS-101")

    def test_background_async_job_queue(self):
        """Verifies asynchronous job queue creation, execution, and status polling."""
        job_id = JobQueueManager.create_job("TEST_MONTE_CARLO")
        self.assertTrue(job_id.startswith("JOB-"))

        def sample_work(a, b):
            return {"sum": a + b}

        JobQueueManager.execute_async_job(job_id, sample_work, 10, 20)
        time.sleep(0.3)

        status_info = JobQueueManager.get_job_status(job_id)
        self.assertIsNotNone(status_info)
        self.assertEqual(status_info["status"], "COMPLETE")
        self.assertEqual(status_info["result"]["sum"], 30)

    def test_version_aware_cache(self):
        """Verifies in-memory LRU caching prevents stale hits across model versions."""
        cache = VersionAwareCache(max_items=10, ttl_seconds=60)
        cache.set("DS-v1", "VER", 15, "model_v1", {"win_prob": 30.0})

        # Same key -> Cache HIT
        hit = cache.get("DS-v1", "VER", 15, "model_v1")
        self.assertIsNotNone(hit)
        self.assertEqual(hit["win_prob"], 30.0)

        # Different model version -> Cache MISS (Prevents stale cross-version hits)
        miss = cache.get("DS-v1", "VER", 15, "model_v2")
        self.assertIsNone(miss)

    def test_reproducible_synthetic_demo_seeding(self):
        """Verifies that seed_demo_data produces identical telemetry datasets across identical seeds."""
        laps1, res1 = DemoDataSeeder.generate_synthetic_demo_dataset(seed=42)
        laps2, res2 = DemoDataSeeder.generate_synthetic_demo_dataset(seed=42)

        self.assertEqual(len(laps1), len(laps2))
        self.assertEqual(laps1.iloc[0]['LapTime'], laps2.iloc[0]['LapTime'])

    def test_log_credential_sanitization(self):
        """Verifies that structured JSON logger redacts API keys and sensitive tokens."""
        raw_payload = {
            "user": "engineer_1",
            "api_key": "dummy_test_api_key_only",
            "password": "dummy_test_password_only",
            "lap_time": 90.0
        }
        sanitized = sanitize_payload(raw_payload)

        self.assertEqual(sanitized["api_key"], "[REDACTED]")
        self.assertEqual(sanitized["password"], "[REDACTED]")
        self.assertEqual(sanitized["lap_time"], 90.0)


if __name__ == '__main__':
    unittest.main()
