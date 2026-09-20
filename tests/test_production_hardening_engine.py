"""
Automated Unit, Integration & Security Audit Test Suite for Production Hardening Subsystem.
Verifies InputSanitizer, PathTraversalGuard, RateLimiter token bucket enforcement,
AIBoundaryGuard read-only write locks, BackupRestoreManager manifests, SystemHealthService (/health, /ready),
and API routes.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from production_hardening_engine import InputSanitizer, RateLimiter, AIBoundaryGuard, FaultToleranceEngine, BackupRestoreManager, SystemHealthService, SecurityAuditReport, HealthCheckResult, BackupManifest
from telemetry_api import api_service


class TestProductionHardeningEngine(unittest.TestCase):

    def test_input_sanitizer_and_path_traversal_guard(self):
        """Verifies driver ID sanitization, season validation, and path traversal rejection."""
        self.assertEqual(InputSanitizer.sanitize_driver_id("  ver  "), "VER")
        self.assertEqual(InputSanitizer.sanitize_driver_id("INVALID123"), "VER")
        self.assertEqual(InputSanitizer.sanitize_season(2024), 2024)
        self.assertEqual(InputSanitizer.sanitize_season(1800), 2024)

        # Path traversal prevention
        with self.assertRaises(ValueError):
            InputSanitizer.sanitize_path("../../etc/passwd")

    def test_rate_limiter_token_bucket(self):
        """Verifies token bucket rate limiter permits valid requests and throttles excess."""
        limiter = RateLimiter(max_requests=2, window_s=60.0)

        self.assertTrue(limiter.is_allowed("client_1"))
        self.assertTrue(limiter.is_allowed("client_1"))
        self.assertFalse(limiter.is_allowed("client_1"))

    def test_ai_boundary_guard_read_only_lock(self):
        """Verifies AI boundary guard raises PermissionError on forbidden write actions."""
        self.assertTrue(AIBoundaryGuard.enforce_read_only("QUERY_TELEM"))

        with self.assertRaises(PermissionError):
            AIBoundaryGuard.enforce_read_only("DELETE_DATASET")

        with self.assertRaises(PermissionError):
            AIBoundaryGuard.enforce_read_only("MODIFY_RACE_STATE")

    def test_backup_restore_manager(self):
        """Verifies automated database backup creation and validated restore flag."""
        backup = BackupRestoreManager.create_backup()

        self.assertEqual(backup.database_status, "BACKED_UP")
        self.assertTrue(backup.validated_restore)
        self.assertEqual(len(backup.metadata_checksum), 16)

    def test_system_health_service(self):
        """Verifies system health status, liveness, and readiness probes."""
        health = SystemHealthService.get_health_status()

        self.assertEqual(health.status, "HEALTHY")
        self.assertTrue(health.liveness)
        self.assertTrue(health.readiness)
        self.assertEqual(health.components["database"], "CONNECTED")

    def test_api_service_hardening_routes(self):
        """Verifies API routes for system health and automated backup creation."""
        health = api_service.get_system_health()
        backup = api_service.create_system_backup()

        self.assertEqual(health["status"], "HEALTHY")
        self.assertEqual(backup["database_status"], "BACKED_UP")


if __name__ == '__main__':
    unittest.main()
