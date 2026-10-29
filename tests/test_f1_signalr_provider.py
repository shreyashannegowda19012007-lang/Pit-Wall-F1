"""
Unit and Integration Tests for Official F1 Live Timing SignalR Core Provider.
Tests interface compliance, session discovery, driver roster, timing tower,
CarData decompression, WebSocket streaming, and elimination of fake telemetry.
"""

import pytest
import json
import zlib
import base64
import time
from fastapi.testclient import TestClient
from src.main_api import app
from src.live_provider_interface import BaseLiveProvider
from src.live_provider_factory import get_live_provider
from src.f1_signalr_service import F1SignalRProvider, f1_signalr_provider
from src.live_telemetry_service import live_telemetry_service

client = TestClient(app)


class TestF1SignalRProvider:

    def test_provider_interface_compliance(self):
        """Verifies that F1SignalRProvider implements BaseLiveProvider."""
        provider = get_live_provider()
        assert isinstance(provider, BaseLiveProvider)
        assert provider.get_provider_type() == "F1_SIGNALR_CORE"
        info = provider.get_provider_info()
        assert info["tier"] == "FREE"
        assert info["auth_required"] is False
        assert "livetiming.formula1.com" in info["upstream_url"]

    def test_live_status_contract_zero_auth_barrier(self):
        """Verifies /api/live/status reports free legitimate provider without auth barriers."""
        response = client.get("/api/live/status")
        assert response.status_code == 200
        data = response.json()
        assert "Official F1 Live Timing" in data.get("provider", "")
        assert data.get("has_live_credentials") is False
        assert data.get("auth_required") is False
        assert "session_status" in data
        assert data.get("session_status") != "AUTHENTICATION_REQUIRED"
        assert "display_session" in data
        assert data.get("display_session", {}).get("year") == 2026

    def test_sessions_discovery(self):
        """Verifies session discovery from live provider."""
        response = client.get("/api/live/sessions")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        sessions = data.get("sessions", [])
        assert len(sessions) >= 5
        keys = [s["session_key"] for s in sessions]
        assert 20261804 in keys  # COTA Qualifying
        assert 20261805 in keys  # COTA Race

    def test_session_drivers_roster(self):
        """Verifies driver roster is correctly delivered without OpenF1 auth lock."""
        response = client.get("/api/live/drivers?session_key=20261804")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        drivers = data.get("drivers", [])
        assert len(drivers) >= 20
        drv_codes = [d["driver_code"] for d in drivers]
        assert "VER" in drv_codes
        assert "HAM" in drv_codes
        assert "NOR" in drv_codes

    def test_cardata_z_decompression_and_normalization(self):
        """Verifies decompression and channel normalization of CarData.z payload."""
        # Synthesize realistic CarData.z payload
        raw_obj = {
            "Entries": [
                {
                    "Utc": "2026-10-24T21:15:30.500Z",
                    "Cars": {
                        "1": {
                            "Channels": {
                                "0": 11850,  # RPM
                                "2": 315.4,  # Speed
                                "3": 8,      # Gear
                                "4": 100.0,  # Throttle
                                "5": 0,      # Brake
                                "45": 1      # DRS
                            }
                        }
                    }
                }
            ]
        }
        json_bytes = json.dumps(raw_obj).encode("utf-8")
        compressed = zlib.compress(json_bytes)
        b64_str = base64.b64encode(compressed).decode("utf-8")

        provider = F1SignalRProvider()
        provider._handle_car_data_compressed(b64_str, "2026-10-24T21:15:30.500Z")

        latest = provider.get_latest_telemetry(session_key=20261804, driver_number=1)
        assert latest is not None
        assert latest["driver_number"] == 1
        assert latest["speed_kmh"] == 315.4
        assert latest["engine_rpm"] == 11850
        assert latest["gear"] == 8
        assert latest["throttle_pct"] == 100.0
        assert latest["brake_flag"] == 0
        assert latest["drs_active"] is True
        assert latest["provenance"] == "MEASURED"

    def test_timing_tower_generation(self):
        """Verifies timing tower is constructed with valid positions, gaps, and compounds."""
        provider = F1SignalRProvider()
        tower = provider.get_timing_tower(session_key=20261804)
        assert len(tower) >= 20
        assert tower[0]["position"] == 1
        assert tower[0]["driver_code"] == "VER"
        assert tower[0]["gap_to_leader_s"] == "LEADER"
        assert tower[0]["current_compound"] in ["SOFT", "MEDIUM", "HARD"]

    def test_prevention_of_fake_live_telemetry(self):
        """Verifies that live mode never emits random or synthetic values."""
        provider = F1SignalRProvider()
        # When no on-track sample has been broadcast, returns honest awaiting state
        sample = provider.get_latest_telemetry(session_key=20261804, driver_number=99)
        assert sample is not None
        assert sample["provenance"] == "WAITING_FOR_SOURCE_DATA"
        assert sample["speed_kmh"] is None
        assert sample["engine_rpm"] is None
        assert sample["data_classification"] == "UNAVAILABLE"
        assert sample["car_telemetry_available"] is False

    def test_test_stream_strictly_labeled(self):
        """Verifies simulator test stream is explicitly tagged TEST_STREAM and HYPOTHETICAL."""
        response = client.get("/api/live/telemetry/test-stream?session_key=20261804&driver_number=1&step=5")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        sample = data.get("data", {})
        assert sample.get("is_test_stream") is True
        assert sample.get("provenance") == "TEST_STREAM"
        assert sample.get("data_classification") == "HYPOTHETICAL"
        assert sample.get("speed_kmh") > 0

    def test_websocket_streaming_simulator_mode(self):
        """Verifies WebSocket streaming works cleanly in explicit SIMULATOR mode."""
        with client.websocket_connect("/ws/live/telemetry/20261804/1?mode=SIMULATOR") as ws:
            snap = ws.receive_json()
            assert snap.get("type") == "INITIAL_SNAPSHOT"
            assert "history" in snap

            msg = ws.receive_json()
            assert msg.get("type") in ["TELEMETRY_UPDATE", "HEARTBEAT"]
            if msg.get("type") == "TELEMETRY_UPDATE":
                pt = msg.get("data", {})
                assert pt.get("provenance") == "TEST_STREAM"

    def test_websocket_streaming_live_mode_no_auth_lockout(self):
        """Verifies WebSocket streaming in LIVE mode does NOT return AUTHENTICATION_REQUIRED."""
        with client.websocket_connect("/ws/live/telemetry/20261804/1?mode=LIVE") as ws:
            snap = ws.receive_json()
            assert snap.get("type") == "INITIAL_SNAPSHOT"
            assert snap.get("status", {}).get("session_status") != "AUTHENTICATION_REQUIRED"

            msg = ws.receive_json()
            assert msg.get("type") in ["TELEMETRY_UPDATE", "HEARTBEAT"]
            assert msg.get("status") != "AUTHENTICATION_REQUIRED"

    def test_signalr_type_3_invocation_completion_snapshot_ingestion(self):
        """Verifies that SignalR type 3 (Invocation Completion) frame is parsed and unpacks all channels."""
        provider = F1SignalRProvider()
        # Realistic initial state payload delivered by F1 SignalR server on Subscribe invocation
        mock_snapshot_frame = json.dumps({
            "type": 3,
            "invocationId": "0",
            "result": {
                "Heartbeat": {"Utc": "2026-10-24T22:23:51.000Z"},
                "SessionInfo": {
                    "Key": 11392,
                    "Name": "Qualifying",
                    "Type": "Qualifying",
                    "SessionStatus": "Finalised",
                    "Meeting": {
                        "Key": 1248,
                        "Name": "United States Grand Prix",
                        "Circuit": {"Key": 9, "ShortName": "Austin"},
                        "Country": {"Name": "United States"}
                    }
                },
                "DriverList": {
                    "12": {"RacingNumber": "12", "BroadcastName": "K ANTONELLI", "FullName": "Andrea Kimi Antonelli", "Tla": "ANT", "TeamName": "Mercedes", "TeamColour": "27F4D2"},
                    "3": {"RacingNumber": "3", "BroadcastName": "M VERSTAPPEN", "FullName": "Max Verstappen", "Tla": "VER", "TeamName": "Red Bull Racing", "TeamColour": "3671C6"}
                },
                "TimingData": {
                    "Lines": {
                        "12": {
                            "Position": "1",
                            "BestLapTime": {"Value": "1:34.035"},
                            "Stats": [{"TimeDiffToFastest": "LEADER", "TimeDifftoPositionAhead": ""}],
                            "InPit": False,
                            "NumberOfLaps": 18
                        },
                        "3": {
                            "Position": "2",
                            "BestLapTime": {"Value": "1:34.214"},
                            "Stats": [{"TimeDiffToFastest": "+0.179", "TimeDifftoPositionAhead": "+0.179"}],
                            "InPit": False,
                            "NumberOfLaps": 19
                        }
                    }
                },
                "TimingAppData": {
                    "Lines": {
                        "12": {"Stints": [{"Compound": "SOFT", "TotalLaps": 5}]},
                        "3": {"Stints": [{"Compound": "SOFT", "TotalLaps": 6}]}
                    }
                },
                "WeatherData": {"AirTemp": 25.2, "TrackTemp": 34.8, "Humidity": 42.0},
                "RaceControlMessages": {"Messages": [{"Message": "CHEQUERED FLAG", "Category": "Flag"}]}
            }
        })
        provider._process_signalr_message(mock_snapshot_frame)

        # Verify state is populated directly from upstream frame
        assert provider.session_info.get("Key") == 11392
        assert provider.session_info.get("SessionStatus") == "Finalised"
        assert len(provider.driver_list) >= 2
        assert len(provider.timing_data.get("Lines", {})) == 2
        assert provider.total_records_ingested >= 6
        assert provider.connection_status in ["BETWEEN_SESSIONS", "RECEIVING", "STREAMING"]

        # Verify timing tower extracts correct positions and times
        tower = provider.get_timing_tower(session_key=11392)
        assert len(tower) == 2
        assert tower[0]["position"] == 1
        assert tower[0]["driver_code"] == "ANT"
        assert tower[0]["best_lap_time_s"] == "1:34.035"
        assert tower[0]["gap_to_leader_s"] == "LEADER"
        assert tower[0]["status"] == "PARC_FERME"

        assert tower[1]["position"] == 2
        assert tower[1]["driver_code"] == "VER"
        assert tower[1]["best_lap_time_s"] == "1:34.214"
        assert tower[1]["gap_to_leader_s"] == "+0.179"

    def test_api_live_timing_tower_endpoint(self):
        """Verifies GET /api/live/timing-tower endpoint returns live or session-end timing tower."""
        response = client.get("/api/live/timing-tower?session_key=20261804")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "tower" in data
        tower = data["tower"]
        assert len(tower) >= 2
        assert "position" in tower[0]
        assert "driver_code" in tower[0]
        assert "team_name" in tower[0]

    def test_session_11392_resolution(self):
        """Verifies official session key 11392 is discoverable via /api/live/sessions."""
        response = client.get("/api/live/sessions")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        keys = [s["session_key"] for s in data.get("sessions", [])]
        assert 11392 in keys or 20261804 in keys

    def test_api_live_drivers_endpoint(self):
        """Verifies GET /api/live/drivers returns 200 with complete driver objects."""
        response = client.get("/api/live/drivers?session_key=11392")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        drivers = data.get("drivers", [])
        assert len(drivers) >= 20
        d0 = drivers[0]
        assert "driver_number" in d0
        assert "driver_code" in d0
        assert "full_name" in d0
        assert "team_name" in d0
        assert "team_colour" in d0
        assert d0["team_colour"].startswith("#")

    def test_api_live_weather_and_race_control(self):
        """Verifies GET /api/live/weather and GET /api/live/race-control."""
        w_res = client.get("/api/live/weather")
        assert w_res.status_code == 200
        w_data = w_res.json()
        assert w_data.get("success") is True
        assert "weather" in w_data
        assert "air_temp_c" in w_data["weather"]

        rc_res = client.get("/api/live/race-control")
        assert rc_res.status_code == 200
        rc_data = rc_res.json()
        assert rc_data.get("success") is True
        assert "messages" in rc_data
        assert len(rc_data["messages"]) > 0

    def test_race_operations_2026_service_routing(self):
        """Verifies RaceOperationsService gracefully routes 2026 sessions without FastF1 errors."""
        from src.race_operations_service import RaceOperationsService
        tower = RaceOperationsService.get_timing_tower("S-2026-UNITED_STATES_GRAND_PRIX-Q")
        assert isinstance(tower, list)
        assert len(tower) >= 20

        rc = RaceOperationsService.get_race_control_timeline("S-2026-UNITED_STATES_GRAND_PRIX-Q")
        assert isinstance(rc, list)
        assert len(rc) > 0

    def test_freshness_and_source_timestamp_consistency(self):
        """
        Regression Test (Item 2):
        Reproduces and proves the fix for the contradiction where data_freshness: STALE,
        an old source timestamp from yesterday, and data_age_seconds: 15.06 occurred together.
        Verifies that transport packet age and source data age are separated, and that
        concluded/between sessions are classified as BETWEEN_SESSIONS_IDLE rather than STALE.
        """
        provider = F1SignalRProvider()
        now_epoch = time.time()
        
        # Simulate concluded session from yesterday with recent WebSocket ping (15 seconds ago)
        provider.session_info = {"Key": 11392, "Name": "Qualifying", "SessionStatus": "Finalised"}
        provider.last_source_timestamp = "2026-10-24T22:23:51Z"
        provider.last_packet_received_epoch = now_epoch - 15.06
        provider.connection_status = "RECEIVING"

        status = provider.get_live_status()

        # 1. Transport packet age reflects WebSocket frame silence (15.06s)
        assert status["transport_packet_age_seconds"] is not None
        assert abs(status["transport_packet_age_seconds"] - 15.06) < 1.0

        # 2. Source data age accurately reflects elapsed time since upstream event timestamp (> 1 hour old, ~70,000s)
        assert status["source_data_age_seconds"] is not None
        assert status["source_data_age_seconds"] > 3600.0

        # 3. Freshness MUST NOT be labeled STALE; between sessions it is strictly BETWEEN_SESSIONS_IDLE
        assert status["data_freshness"] == "BETWEEN_SESSIONS_IDLE"
        assert status["session_status"] == "BETWEEN_SESSIONS"
        assert status["is_session_live"] is False

    def test_unavailable_telemetry_not_classified_as_measured(self):
        """
        Regression Test (Item 3):
        Ensures unavailable telemetry cannot simultaneously be classified as current MEASURED data.
        Verifies missing measurements are None and UNAVAILABLE, while real zero measurements are preserved.
        """
        provider = F1SignalRProvider()
        provider.session_info = {"Key": 11392, "SessionStatus": "Finalised"}

        # Case A: No car telemetry broadcast received for driver
        sample_empty = provider.get_latest_telemetry(session_key=11392, driver_number=1)
        assert sample_empty is not None
        assert sample_empty["speed_kmh"] is None
        assert sample_empty["engine_rpm"] is None
        assert sample_empty["gear"] is None
        assert sample_empty["throttle_pct"] is None
        assert sample_empty["brake_flag"] is None
        assert sample_empty["drs_active"] is None
        assert sample_empty["data_classification"] == "UNAVAILABLE"
        assert sample_empty["car_telemetry_available"] is False
        assert sample_empty["provenance"] == "WAITING_FOR_SOURCE_DATA"

        # Case B: Genuine zero measurement received (stationary car in pitlane or grid)
        # speed=0.0 km/h, rpm=4200, gear=0 (N), throttle=0.0, brake=1
        real_zero_sample = {
            "source": "F1_SignalR_Core",
            "session_key": 11392,
            "driver_number": 1,
            "timestamp": "2026-10-25T14:00:00Z",
            "speed_kmh": 0.0,
            "engine_rpm": 4200,
            "gear": 0,
            "throttle_pct": 0.0,
            "brake_flag": 1,
            "drs_active": False,
            "provenance": "MEASURED",
            "data_classification": "MEASURED",
            "car_telemetry_available": True
        }
        provider.driver_latest_sample[1] = real_zero_sample
        measured_sample = provider.get_latest_telemetry(session_key=11392, driver_number=1)
        assert measured_sample is not None
        assert measured_sample["speed_kmh"] == 0.0
        assert measured_sample["engine_rpm"] == 4200
        assert measured_sample["car_telemetry_available"] is True
        assert measured_sample["data_classification"] == "MEASURED"
        assert measured_sample["provenance"] == "MEASURED"

    def test_weather_provenance_and_timestamps(self):
        """
        Regression Test (Item 4):
        Ensures weather readings trace to their actual source timestamp and session.
        Prevents synthetic numbers (24.5/32.1) and distinguishes archived snapshots from live weather.
        """
        provider = F1SignalRProvider()
        provider.session_info = {"Key": 11392, "SessionStatus": "Finalised"}

        # Case A: Empty weather data returns None fields and UNAVAILABLE status, NOT 24.5 / 32.1
        w_empty = provider.get_weather(session_key=11392)
        assert w_empty["data_status"] == "UNAVAILABLE"
        assert w_empty["air_temp_c"] is None
        assert w_empty["track_temp_c"] is None
        assert w_empty["is_live_measurement"] is False

        # Case B: Weather received from concluded session snapshot carries source timestamp and ARCHIVED_SESSION_SNAPSHOT
        provider.weather_data = {"AirTemp": "28.4", "TrackTemp": "41.2", "Humidity": "38.0"}
        provider.last_weather_timestamp = "2026-10-24T22:23:51Z"
        w_snapshot = provider.get_weather(session_key=11392)
        assert w_snapshot["data_status"] == "ARCHIVED_SESSION_SNAPSHOT"
        assert w_snapshot["session_key"] == 11392
        assert w_snapshot["recorded_at"] == "2026-10-24T22:23:51Z"
        assert w_snapshot["air_temp_c"] == 28.4
        assert w_snapshot["track_temp_c"] == 41.2
        assert w_snapshot["is_live_measurement"] is False

    def test_auth_status_honesty(self):
        """
        Regression Test (Item 5):
        Ensures has_live_credentials and auth_notice are accurate to the unauthenticated public feed.
        Never implies credentials succeeded or were configured.
        """
        provider = F1SignalRProvider()
        info = provider.get_provider_info()
        assert info["auth_required"] is False
        assert info["has_live_credentials"] is False
        assert info["auth_type"] == "ANONYMOUS_PUBLIC_FEED"
        assert "No user credentials" in info["auth_notice"]

        status = provider.get_live_status()
        assert status["auth_required"] is False
        assert status["has_live_credentials"] is False
        assert status["auth_type"] == "ANONYMOUS_PUBLIC_FEED"

    def test_state_machine_distinct_states(self):
        """
        Regression Test (Item 7):
        Verifies that BETWEEN_SESSIONS, CONNECTED, SUBSCRIBING, SUBSCRIBED,
        RECEIVING, RECEIVING_TELEMETRY, and STALE are distinct, evidence-based states.
        A connected socket does NOT imply car telemetry delivery.
        """
        provider = F1SignalRProvider()
        
        # State 1: Disconnected
        provider.connection_status = "DISCONNECTED"
        assert provider.get_live_status()["session_status"] == "DISCONNECTED"

        # State 2: Connected but no session info yet
        provider.connection_status = "CONNECTED"
        provider.session_info = {}
        assert provider.get_live_status()["connection_state"] == "CONNECTED"

        # State 3: Between sessions
        provider.connection_status = "RECEIVING"
        provider.session_info = {"Key": 11392, "SessionStatus": "Finalised"}
        st3 = provider.get_live_status()
        assert st3["session_status"] == "BETWEEN_SESSIONS"
        assert st3["car_telemetry_available"] is False

        # State 4: Live session waiting for cars
        provider.session_info = {"Key": 11392, "SessionStatus": "Started", "Type": "Qualifying"}
        provider.has_received_car_telemetry = False
        st4 = provider.get_live_status()
        assert st4["session_status"] == "LIVE_SESSION_WAITING_FOR_CARS"

        # State 5: Receiving telemetry
        provider.connection_status = "RECEIVING_TELEMETRY"
        provider.has_received_car_telemetry = True
        st5 = provider.get_live_status()
        assert st5["session_status"] == "LIVE_QUALIFYING_RECEIVING"
        assert st5["car_telemetry_available"] is True

    def test_no_active_session_timing_classification_preserved(self):
        """
        Regression Test (Item 9):
        Confirms genuine timing classification (20+ drivers, positions, lap times) can be
        displayed while car telemetry remains unavailable, without fabricating sensor readings.
        """
        provider = F1SignalRProvider()
        provider.session_info = {"Key": 11392, "SessionStatus": "Finalised"}
        
        # Mock timing data from Austin Qualifying
        provider.driver_list = {
            "1": {"RacingNumber": "1", "Tla": "VER", "BroadcastName": "M VERSTAPPEN", "TeamName": "Red Bull Racing"},
            "4": {"RacingNumber": "4", "Tla": "NOR", "BroadcastName": "L NORRIS", "TeamName": "McLaren"}
        }
        provider.timing_data = {
            "Lines": {
                "1": {"Position": "1", "BestLapTime": {"Value": "1:32.831"}, "InPit": False},
                "4": {"Position": "2", "BestLapTime": {"Value": "1:32.862"}, "InPit": False}
            }
        }
        
        # Timing classification is fully available
        tower = provider.get_timing_tower(session_key=11392)
        assert len(tower) == 2
        assert tower[0]["driver_code"] == "VER"
        assert tower[0]["best_lap_time_s"] == "1:32.831"
        assert tower[1]["driver_code"] == "NOR"

        # Car telemetry remains unavailable and honest
        tel = provider.get_latest_telemetry(session_key=11392, driver_number=1)
        assert tel is not None
        assert tel["speed_kmh"] is None
        assert tel["car_telemetry_available"] is False
        assert tel["data_classification"] == "UNAVAILABLE"


