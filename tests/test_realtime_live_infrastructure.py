"""
Automated Unit, Integration & Latency Benchmark Test Suite for Real-Time Live Race Infrastructure Subsystem.
Verifies NormalizedRaceEvent schema v2.4.0, EventIdempotencyRegistry deduplication,
LiveEventBus publishing, LiveSystemHealth latency benchmarks (p50/p95), and API routes.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from realtime_live_infrastructure import RealtimeLiveInfrastructureEngine, LiveEventBus, EventIdempotencyRegistry, NormalizedRaceEvent, LiveSystemHealth
from telemetry_api import api_service


class TestRealtimeLiveInfrastructureEngine(unittest.TestCase):

    def test_normalized_event_publishing_and_deduplication(self):
        """Verifies NormalizedRaceEvent publishing and idempotent deduplication."""
        bus = LiveEventBus()
        evt = NormalizedRaceEvent(
            event_id="EVT-TEST-001",
            event_type="TIMING_UPDATE",
            timestamp=1000.0,
            source_timestamp=999.988,
            received_timestamp=999.998,
            processed_timestamp=1000.0,
            session_id="S-2024-SPAIN",
            driver_id="VER",
            source="OpenF1LiveProvider",
            payload={"lap": 22, "lap_time_s": 81.240}
        )

        # First publish -> Accepted
        published_1 = bus.publish(evt)
        self.assertTrue(published_1)

        # Second publish -> Rejected (Deduplicated)
        published_2 = bus.publish(evt)
        self.assertFalse(published_2)

    def test_live_system_health_and_latency_benchmarks(self):
        """Verifies LiveSystemHealth returns latency metrics (p50 <= 20ms, p95 <= 50ms)."""
        RealtimeLiveInfrastructureEngine.publish_timing_update("VER", 22, 81.240)
        health = RealtimeLiveInfrastructureEngine.get_live_system_health()

        self.assertEqual(health.data_freshness_status, "LIVE")
        self.assertIsNotNone(health.p50_latency_ms)
        self.assertIsNotNone(health.p95_latency_ms)
        self.assertIsNotNone(health.event_bus_throughput_eps)
        self.assertTrue(health.p50_latency_ms <= 20.0)
        self.assertTrue(health.p95_latency_ms <= 50.0)
        self.assertTrue(health.event_bus_throughput_eps > 0.0)

    def test_api_service_live_routes(self):
        """Verifies API routes for live system health and timing updates."""
        t_evt = api_service.publish_timing_update("VER", 22, 81.240)
        health = api_service.get_live_system_health()

        self.assertEqual(health["data_freshness_status"], "LIVE")
        self.assertEqual(t_evt["event_type"], "TIMING_UPDATE")
        self.assertEqual(t_evt["driver_id"], "VER")


if __name__ == '__main__':
    unittest.main()
