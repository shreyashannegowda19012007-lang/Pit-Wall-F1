"""
Tests for Live Formula 1 Telemetry Pipeline via OpenF1.
Exercises provider connectivity, session discovery, telemetry normalization,
freshness metrics, REST endpoints, and WebSocket streaming.
"""

import pytest
from fastapi.testclient import TestClient
from src.main_api import app
from src.live_telemetry_service import LiveTelemetryService, live_telemetry_service

client = TestClient(app)

class TestLiveTelemetryPipeline:
    
    def test_live_provider_status_contract(self):
        """Verifies that /api/live/status reports genuine live provider status and session state."""
        response = client.get("/api/live/status")
        assert response.status_code == 200
        data = response.json()
        assert "Official F1 Live Timing" in data.get("provider", "") or data.get("provider") == "OpenF1"
        assert "session_status" in data
        assert "is_session_live" in data
        assert "current_utc_time" in data
        assert "data_freshness" in data
        assert "total_records_ingested" in data
        assert "auth_notice" in data
        assert data.get("session_status") in [
            "LIVE_ON_TRACK", "BETWEEN_SESSIONS", "NO_ACTIVE_SESSION", 
            "AUTHENTICATION_REQUIRED", "LIVE_QUALIFYING_RECEIVING", "SESSION_ACTIVE_WAITING",
            "WAITING_FOR_SOURCE_DATA", "CONNECTING", "DISCONNECTED"
        ]

    def test_live_sessions_discovery(self):
        """Verifies session discovery from OpenF1."""
        response = client.get("/api/live/sessions")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        sessions = data.get("sessions", [])
        assert len(sessions) > 0
        first_session = sessions[0]
        assert "session_key" in first_session
        assert "session_name" in first_session
        assert "date_start" in first_session

    def test_live_drivers_roster(self):
        """Verifies that driver roster is correctly extracted for an OpenF1 session."""
        response = client.get("/api/live/drivers?session_key=11390")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        drivers = data.get("drivers", [])
        assert len(drivers) > 0
        driver = drivers[0]
        assert "driver_number" in driver
        assert "driver_code" in driver
        assert "team_name" in driver
        assert "team_colour" in driver

    def test_telemetry_normalization_schema(self):
        """Verifies data normalization from raw car_data into platform standard."""
        raw_sample = {
            "date": "2026-10-23T21:04:46.988000+00:00",
            "session_key": 11390,
            "rpm": 12156,
            "meeting_key": 1297,
            "throttle": 100,
            "brake": 0,
            "drs": 12,
            "speed": 335,
            "driver_number": 1,
            "n_gear": 8
        }
        service = LiveTelemetryService()
        norm = service.normalize_telemetry_point(raw_sample)
        
        assert norm["source"] in ["OpenF1", "TelemetryProvider"]
        assert norm["driver_number"] == 1
        assert norm["session_key"] == 11390
        assert norm["speed_kmh"] == 335.0
        assert norm["engine_rpm"] == 12156
        assert norm["gear"] == 8
        assert norm["throttle_pct"] == 100.0
        assert norm["brake_flag"] == 0
        assert norm["drs_active"] is True
        assert norm["provenance"] == "MEASURED"
        assert norm["data_classification"] == "MEASURED"
        assert norm["source_timestamp_epoch"] is not None

    def test_moving_telemetry_history(self):
        """Verifies retrieval of moving telemetry samples (speed >= 50 km/h) or graceful empty array if unauthenticated."""
        response = client.get("/api/live/telemetry/moving?session_key=11390&driver_number=1&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        history = data.get("history", [])
        if len(history) > 0:
            assert history[0]["speed_kmh"] >= 50.0

    def test_test_stream_isolation_and_labeling(self):
        """Verifies test stream is strictly labeled HYPOTHETICAL and TEST_STREAM."""
        response = client.get("/api/live/telemetry/test-stream?session_key=11390&driver_number=1&step=0")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        sample = data.get("data", {})
        assert sample.get("is_test_stream") is True
        assert sample.get("provenance") == "TEST_STREAM"
        assert sample.get("data_classification") == "HYPOTHETICAL"
        assert sample.get("speed_kmh") is not None

    def test_websocket_streaming_pipeline(self):
        """Verifies full WebSocket lifecycle in simulator mode: connects, receives snapshot, and receives dynamic updates."""
        with client.websocket_connect("/ws/live/telemetry/11390/1?mode=SIMULATOR") as ws:
            snap = ws.receive_json()
            assert snap.get("type") == "INITIAL_SNAPSHOT"
            assert "history" in snap
            
            update = ws.receive_json()
            assert update.get("type") in ["TELEMETRY_UPDATE", "HEARTBEAT"]
            if update.get("type") == "TELEMETRY_UPDATE":
                pt = update.get("data", {})
                assert "speed_kmh" in pt
                assert "engine_rpm" in pt
                assert "gear" in pt
                assert pt.get("provenance") == "TEST_STREAM"
