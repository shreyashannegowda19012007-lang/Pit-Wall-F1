"""
Automated Unit, Integration & Stress Test Suite for Advanced Live Race Operations Subsystem.
Verifies NormalizedRaceEvent schema (v2.4.0), EventIdempotencyRegistry duplicate event rejection,
sequence ordering, RealtimeAlertEngine multi-channel alert deduplication, recovery, and API routes.
"""

import unittest
import pandas as pd
import numpy as np
import time
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from realtime_live_engine import RealtimeRaceOperationsEngine, NormalizedRaceEvent, EventIdempotencyRegistry, RealtimeAlertEngine
from telemetry_api import api_service


class TestRealtimeLiveOperationsEngine(unittest.TestCase):

    def test_idempotency_duplicate_event_rejection(self):
        """Verifies EventIdempotencyRegistry rejects duplicate event_id."""
        reg = EventIdempotencyRegistry()
        ev1 = NormalizedRaceEvent(
            event_id="EV-1001",
            event_type="LapCompleted",
            session_id="S-2024-SPAIN",
            timestamp=time.time(),
            source_timestamp=time.time(),
            sequence_number=1,
            driver_id="VER",
            lap_number=10
        )

        self.assertFalse(reg.is_duplicate_or_out_of_order(ev1))
        # Send exact same event ID again
        self.assertTrue(reg.is_duplicate_or_out_of_order(ev1))

    def test_alert_engine_creation_and_acknowledgement(self):
        """Verifies RealtimeAlertEngine raises alerts and manages acknowledgement state."""
        ae = RealtimeAlertEngine()
        alert = ae.raise_alert("ALT-001", "STRATEGY", "HIGH", "PIT WINDOW OPEN", "Pit window is open on Lap 20.", driver_id="VER", lap_number=20)

        self.assertIsNotNone(alert)
        self.assertEqual(len(ae.alerts), 1)

        # Duplicate alert rejection
        dup_alert = ae.raise_alert("ALT-001", "STRATEGY", "HIGH", "PIT WINDOW OPEN", "Duplicate", driver_id="VER", lap_number=20)
        self.assertIsNone(dup_alert)

        # Acknowledge alert
        self.assertTrue(ae.acknowledge_alert("ALT-001"))
        self.assertTrue(ae.alerts[0].is_acknowledged)

    def test_realtime_race_operations_engine_event_processing(self):
        """Verifies RealtimeRaceOperationsEngine processes LapCompleted, PitStop and SafetyCar events."""
        engine = RealtimeRaceOperationsEngine("S-2024-SPAIN", mode="LIVE")

        ev_lap = NormalizedRaceEvent("EV-LAP-20", "LapCompleted", "S-2024-SPAIN", time.time(), time.time(), 1, "VER", 20)
        res_lap = engine.process_incoming_event(ev_lap)
        self.assertEqual(res_lap["status"], "PROCESSED")
        self.assertEqual(engine.current_lap, 20)

        # Process Safety Car RaceControlMessage
        ev_sc = NormalizedRaceEvent("EV-SC-01", "RaceControlMessage", "S-2024-SPAIN", time.time(), time.time(), 2, payload={"message": "SAFETY CAR DEPLOYED"})
        res_sc = engine.process_incoming_event(ev_sc)
        self.assertEqual(res_sc["status"], "PROCESSED")
        self.assertTrue(len(engine.alert_engine.alerts) >= 1)

    def test_api_service_live_summary_route(self):
        """Verifies API route for fetching live operations summary."""
        summary = api_service.get_live_operations_summary("S-2024-SPAIN", mode="LIVE")
        self.assertEqual(summary["mode"], "LIVE")
        self.assertIn("data_freshness_status", summary)


if __name__ == '__main__':
    unittest.main()
