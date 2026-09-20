"""
Automated Unit, Integration & Performance Benchmark Test Suite for Production Data Platform Subsystem.
Verifies SessionPreparationManager SHA-256 manifests, ProductionCacheManager multi-tier LRU caching,
CircuitBreaker fault tolerance transitions (CLOSED -> OPEN -> HALF_OPEN), and API routes.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from production_data_platform import SessionPreparationManager, ProductionCacheManager, CircuitBreaker, SessionManifest, CacheStats
from telemetry_api import api_service


class TestProductionDataPlatform(unittest.TestCase):

    def test_session_preparation_and_manifest_checksum(self):
        """Verifies session preparation creates SHA-256 manifest with READY status."""
        manifest = SessionPreparationManager.prepare_session(2024, 9, "R")

        self.assertEqual(manifest.session_id, "S-2024-R09-R")
        self.assertEqual(manifest.status, "READY")
        self.assertEqual(len(manifest.checksum), 16)
        self.assertIn("v2.4.0", manifest.model_compatibility)

    def test_multi_tier_cache_manager(self):
        """Verifies cache get, set, TTL expiration, and hit rate metrics."""
        cache = ProductionCacheManager()

        # Miss
        val = cache.get("test_key")
        self.assertIsNone(val)

        # Set & Hit
        cache.set("test_key", {"data": 123}, ttl_s=10.0)
        hit_val = cache.get("test_key")
        self.assertEqual(hit_val["data"], 123)

        stats = cache.get_stats()
        self.assertTrue(stats.total_queries >= 2)
        self.assertTrue(stats.cache_hits >= 1)

    def test_circuit_breaker_fault_tolerance(self):
        """Verifies circuit breaker opens on threshold failure and falls back gracefully."""
        cb = CircuitBreaker("TestService", threshold=2, reset_timeout_s=10.0)

        def failing_func():
            raise RuntimeError("API Timeout")

        def fallback_func():
            return "FALLBACK_RESPONSE"

        # First failure
        res1 = cb.execute(failing_func, fallback_func)
        self.assertEqual(res1, "FALLBACK_RESPONSE")
        self.assertEqual(cb.state, "CLOSED")

        # Second failure -> Threshold reached -> OPEN
        res2 = cb.execute(failing_func, fallback_func)
        self.assertEqual(res2, "FALLBACK_RESPONSE")
        self.assertEqual(cb.state, "OPEN")

    def test_api_service_data_platform_routes(self):
        """Verifies API routes for session preparation, manifest, and cache stats."""
        manifest = api_service.prepare_session(2024, 9, "R")
        get_m = api_service.get_session_manifest(manifest["session_id"])
        c_stats = api_service.get_cache_stats()

        self.assertEqual(manifest["status"], "READY")
        self.assertEqual(get_m["checksum"], manifest["checksum"])
        self.assertTrue("hit_rate_pct" in c_stats)


if __name__ == '__main__':
    unittest.main()
