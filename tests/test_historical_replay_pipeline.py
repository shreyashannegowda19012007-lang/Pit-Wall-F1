"""
Unit and Integration Tests for Historical Telemetry Replay Pipeline.
Verifies session discovery from local FastF1 caches, session metadata,
driver roster, replay controls (play, pause, resume, restart, seek, speed),
strict data provenance ("HISTORICAL_REPLAY", never "MEASURED" live),
API endpoints (/api/replay/*), and WebSocket replay telemetry streaming.
"""

import pytest
import time
from fastapi.testclient import TestClient
from src.main_api import app
from src.historical_replay_service import (
    historical_replay_service,
    HistoricalReplayProvider
)
from src.live_provider_factory import (
    get_live_provider,
    set_active_provider_mode,
    get_active_provider_mode,
    get_available_providers
)

client = TestClient(app)


class TestHistoricalReplayPipeline:

    def test_provider_factory_mode_switching(self):
        """Verifies provider factory switches cleanly between LIVE and HISTORICAL_REPLAY."""
        # Check available providers list
        modes = get_available_providers()
        mode_keys = [m["mode"] for m in modes]
        assert "LIVE" in mode_keys
        assert "HISTORICAL_REPLAY" in mode_keys

        # Switch to HISTORICAL_REPLAY
        res = set_active_provider_mode("HISTORICAL_REPLAY")
        assert res["success"] is True
        assert get_active_provider_mode() == "HISTORICAL_REPLAY"

        provider = get_live_provider()
        assert isinstance(provider, HistoricalReplayProvider)
        assert provider.get_provider_type() == "HISTORICAL_REPLAY"

        # Switch back to LIVE
        set_active_provider_mode("LIVE")
        assert get_active_provider_mode() == "LIVE"

    def test_historical_session_discovery(self):
        """Verifies discovery of available historical sessions from FastF1 cache."""
        sessions = historical_replay_service.get_available_sessions()
        assert isinstance(sessions, list)
        assert len(sessions) > 0
        
        # Verify schema of session items
        first_session = sessions[0]
        assert "year" in first_session
        assert "grand_prix" in first_session
        assert "session_type" in first_session
        assert "session_key" in first_session
        assert "cached" in first_session
        assert first_session["cached"] is True

    def test_api_replay_sessions_endpoint(self):
        """Verifies GET /api/replay/sessions returns sessions list."""
        response = client.get("/api/replay/sessions")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        sessions = data.get("sessions", [])
        assert len(sessions) > 0

    def test_api_replay_drivers_endpoint(self):
        """Verifies GET /api/replay/drivers returns driver roster for a cached session."""
        response = client.get("/api/replay/drivers?year=2024&grand_prix=Spain&session_type=R")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        drivers = data.get("drivers", [])
        assert len(drivers) > 0
        driver_codes = [d["driver_code"] for d in drivers]
        assert "VER" in driver_codes or "NOR" in driver_codes

    def test_replay_control_lifecycle(self):
        """Verifies full lifecycle of replay controls: start, pause, resume, seek, restart, stop."""
        # 1. Start Replay
        start_payload = {
            "action": "start",
            "year": 2024,
            "grand_prix": "Spain",
            "session_type": "R",
            "driver": "VER",
            "playback_speed": 5.0
        }
        res = client.post("/api/replay/control", json=start_payload)
        assert res.status_code == 200
        status = res.json()["status"]
        assert status["state"] in ("PLAYING", "LOADED")
        assert status["year"] == 2024
        assert status["driver"] == "VER"
        assert status["total_samples"] > 0
        assert status["playback_speed"] == 5.0

        # Let it stream a few samples
        time.sleep(0.3)

        # 2. Check Latest Telemetry
        tel_res = client.get("/api/replay/telemetry/latest?driver=VER")
        assert tel_res.status_code == 200
        tel_data = tel_res.json()
        assert tel_data.get("available") is True
        # STRICT PROVENANCE ENFORCEMENT
        assert tel_data.get("provenance") == "HISTORICAL_REPLAY"
        assert tel_data.get("data_classification") == "HISTORICAL_REPLAY"
        assert tel_data.get("telemetry_status") == "REPLAYING"
        sample = tel_data.get("sample", {})
        assert sample.get("speed_kmh") is not None or sample.get("speed") is not None
        assert sample.get("engine_rpm") is not None or sample.get("rpm") is not None
        assert sample.get("throttle_pct") is not None or sample.get("throttle") is not None
        assert "source_timestamp" in sample
        assert "server_received_at" in sample

        # 3. Check Timing Tower
        tower_res = client.get("/api/replay/timing-tower")
        assert tower_res.status_code == 200
        tower_data = tower_res.json()
        assert tower_data.get("success") is True
        assert len(tower_data.get("rows", [])) > 0
        assert tower_data.get("provenance") == "HISTORICAL_REPLAY"

        # 4. Pause
        pause_res = client.post("/api/replay/control", json={"action": "pause"})
        assert pause_res.status_code == 200
        assert pause_res.json()["status"]["state"] == "PAUSED"

        # 5. Speed change
        speed_res = client.post("/api/replay/control", json={"action": "speed", "playback_speed": 10.0})
        assert speed_res.status_code == 200
        assert speed_res.json()["status"]["playback_speed"] == 10.0

        # 6. Seek
        seek_res = client.post("/api/replay/control", json={"action": "seek", "seek_index": 50})
        assert seek_res.status_code == 200
        assert seek_res.json()["status"]["current_sample_index"] == 50

        # 7. Resume
        resume_res = client.post("/api/replay/control", json={"action": "resume"})
        assert resume_res.status_code == 200
        assert resume_res.json()["status"]["state"] == "PLAYING"

        # 8. Restart
        restart_res = client.post("/api/replay/control", json={"action": "restart"})
        assert restart_res.status_code == 200
        assert restart_res.json()["status"]["current_sample_index"] == 0

        # 9. Stop
        stop_res = client.post("/api/replay/control", json={"action": "stop"})
        assert stop_res.status_code == 200
        assert stop_res.json()["status"]["state"] == "STOPPED"

    def test_websocket_replay_telemetry_streaming(self):
        """Verifies WebSocket endpoint streams real replay telemetry under mode=REPLAY."""
        # Ensure replay is started for VER via client POST
        start_res = client.post("/api/replay/control", json={
            "action": "start",
            "year": 2024,
            "grand_prix": "Spain",
            "session_type": "R",
            "driver": "VER",
            "playback_speed": 10.0
        })
        assert start_res.status_code == 200
        
        with client.websocket_connect("/ws/live/telemetry/20240905/1?mode=REPLAY") as websocket:
            # Receive initial frame
            data1 = websocket.receive_json()
            assert "sample" in data1 or "type" in data1 or "driver" in data1
            
            # Allow replay to deliver a point
            time.sleep(0.3)
            data2 = websocket.receive_json()
            assert data2.get("provenance") == "HISTORICAL_REPLAY"
            assert data2.get("data_classification") == "HISTORICAL_REPLAY"
            assert data2.get("driver") in ("VER", "1")
            smp = data2.get("sample") or data2.get("data") or {}
            assert smp.get("speed_kmh") is not None or smp.get("speed") is not None

        # Clean up
        client.post("/api/replay/control", json={"action": "stop"})

    def test_replay_mode_api_status_consistency(self):
        """Verifies /api/live/status respects active provider mode and reports replay status."""
        set_active_provider_mode("HISTORICAL_REPLAY")
        try:
            res = client.get("/api/live/status")
            assert res.status_code == 200
            data = res.json()
            assert data.get("active_pipeline_mode") == "HISTORICAL_REPLAY"
            assert "replay_status" in data
        finally:
            set_active_provider_mode("LIVE")
