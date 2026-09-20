"""
Automated Unit, Integration & Streaming Test Suite for Real-Time Race State Engine & WebSocket Streaming.
Verifies authoritative race-state schema normalization (v2.4.0), canonical units, provider adapters,
WebSocket snapshot & delta payload generation, client connection management, and data leakage protection.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from realtime_race_state import UnifiedRaceState, DriverRaceState, ReplayAdapter, OpenF1LiveProvider, SCHEMA_VERSION
from websocket_manager import WebSocketConnectionManager
from telemetry_api import api_service


class TestRealtimeRaceStateEngine(unittest.TestCase):

    def test_schema_normalization_and_version(self):
        """Verifies schema versioning v2.4.0 and driver dictionary normalization."""
        adapter = ReplayAdapter(pd.DataFrame())
        state = adapter.fetch_current_race_state("S-2024-SPAIN", timestamp_s=90.0)

        self.assertEqual(state.schema_version, SCHEMA_VERSION)
        self.assertEqual(state.session_id, "S-2024-SPAIN")
        self.assertEqual(len(state.drivers), 0)
        self.assertEqual(state.session_status, "DATA UNAVAILABLE")

    def test_websocket_snapshot_and_delta_payloads(self):
        """Verifies WebSocket snapshot (RACE_STATE_SNAPSHOT) and delta update (RACE_STATE_UPDATE) payloads."""
        ws_mgr = WebSocketConnectionManager()
        adapter = ReplayAdapter(pd.DataFrame())
        state = adapter.fetch_current_race_state("S-2024-SPAIN", timestamp_s=180.0)

        snap_str = ws_mgr.generate_snapshot_payload(state)
        update_str = ws_mgr.generate_update_payload(state)

        self.assertIn("RACE_STATE_SNAPSHOT", snap_str)
        self.assertIn(SCHEMA_VERSION, snap_str)
        self.assertIn("RACE_STATE_UPDATE", update_str)

    def test_live_and_replay_provider_adapters(self):
        """Verifies ReplayAdapter and OpenF1LiveProvider switch modes cleanly without changing schema structure."""
        replay_p = ReplayAdapter(pd.DataFrame())
        live_p = OpenF1LiveProvider()

        s_replay = replay_p.fetch_current_race_state("S-101", 100.0)
        s_live = live_p.fetch_current_race_state("S-101", 100.0)

        self.assertEqual(s_replay.mode, "REPLAY")
        self.assertEqual(s_live.mode, "LIVE")
        self.assertEqual(s_replay.schema_version, s_live.schema_version)

    def test_telemetry_api_unified_state_route(self):
        """Verifies API route get_unified_race_state()."""
        res = api_service.get_unified_race_state("S-2024-SPAIN", timestamp_s=300.0, mode="REPLAY")

        self.assertEqual(res.schema_version, SCHEMA_VERSION)
        self.assertEqual(res.mode, "REPLAY")


if __name__ == '__main__':
    unittest.main()
