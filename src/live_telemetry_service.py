"""
Pitwall F1 — Live Telemetry Service.
Wraps the active live provider (F1 SignalR Core) and coordinates live streaming,
session discovery, driver roster synchronization, and WebSocket broadcast streams.
Provides backward-compatible delegation to the active live provider.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from src.live_provider_factory import get_live_provider

logger = logging.getLogger("LiveTelemetryService")


class LiveTelemetryService:
    """
    Service coordinating live telemetry ingestion and streaming.
    Delegates directly to the configured active BaseLiveProvider (F1SignalRProvider).
    """

    def __init__(self):
        self.moving_cache: Dict[str, Any] = {}

    @property
    def provider(self):
        return get_live_provider()

    def get_live_status(self) -> Dict[str, Any]:
        """Evaluates current provider health, active F1 session state, and data freshness."""
        return self.provider.get_live_status()

    def get_sessions(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Discovers sessions for the target year from the live provider."""
        return self.provider.get_sessions(year=year)

    def get_session_drivers(self, session_key: int) -> List[Dict[str, Any]]:
        """Fetches the participating driver roster for a specific session."""
        return self.provider.get_session_drivers(session_key=session_key)

    def normalize_telemetry_point(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes a raw car_data point into the standardized platform schema."""
        raw_date = raw.get("date") or raw.get("timestamp") or datetime.now(timezone.utc).isoformat()
        source_ts = None
        try:
            dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            source_ts = dt.timestamp()
        except Exception:
            pass

        has_measurements = any(raw.get(k) is not None for k in ["speed", "rpm", "gear", "n_gear", "throttle", "brake"])

        if has_measurements:
            raw_throttle = raw.get("throttle")
            throttle_pct = min(100.0, max(0.0, float(raw_throttle))) if raw_throttle is not None else None

            raw_brake = raw.get("brake")
            brake_val = 1 if (raw_brake is not None and (raw_brake is True or float(raw_brake) > 0)) else (0 if raw_brake is not None else None)

            raw_speed = raw.get("speed")
            speed_kmh = float(raw_speed) if raw_speed is not None else None

            raw_rpm = raw.get("rpm")
            rpm_val = int(raw_rpm) if raw_rpm is not None else None

            raw_gear = raw.get("n_gear") if raw.get("n_gear") is not None else raw.get("gear")
            gear_val = int(raw_gear) if raw_gear is not None else None

            raw_drs = raw.get("drs")
            drs_active = True if raw_drs in [10, 12, 14, 1, True] else (False if raw_drs is not None else None)

            provenance = raw.get("provenance", "MEASURED")
            classification = raw.get("data_classification", "MEASURED")
            car_avail = True
            channel_status = raw.get("channel_status", "CHANNELS_MEASURED")
        else:
            speed_kmh = None
            rpm_val = None
            gear_val = None
            throttle_pct = None
            brake_val = None
            drs_active = None
            provenance = raw.get("provenance", "WAITING_FOR_SOURCE_DATA")
            classification = raw.get("data_classification", "UNAVAILABLE")
            car_avail = False
            channel_status = "AWAITING_ON_TRACK_SAMPLE"

        return {
            "source": raw.get("source", "TelemetryProvider"),
            "session_key": raw.get("session_key"),
            "meeting_key": raw.get("meeting_key"),
            "driver_number": raw.get("driver_number"),
            "timestamp": raw_date,
            "source_timestamp_epoch": source_ts,
            "speed_kmh": round(speed_kmh, 1) if speed_kmh is not None else None,
            "engine_rpm": rpm_val,
            "gear": gear_val,
            "throttle_pct": round(throttle_pct, 1) if throttle_pct is not None else None,
            "brake_flag": brake_val,
            "drs_active": drs_active,
            "provenance": provenance,
            "data_classification": classification,
            "car_telemetry_available": car_avail,
            "channel_status": channel_status
        }

    def get_latest_telemetry(self, session_key: int, driver_number: int, mode: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Fetches the latest available telemetry point for a driver."""
        provider = get_live_provider(mode=mode)
        return provider.get_latest_telemetry(session_key=session_key, driver_number=driver_number)

    def get_telemetry_history(
        self,
        session_key: int,
        driver_number: int,
        limit: int = 50,
        since_timestamp: Optional[str] = None,
        mode: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetches bounded telemetry history from the active or specified provider."""
        provider = get_live_provider(mode=mode)
        return provider.get_telemetry_history(
            session_key=session_key,
            driver_number=driver_number,
            limit=limit,
            since_timestamp=since_timestamp
        )

    def get_moving_telemetry_history(
        self,
        session_key: int,
        driver_number: int,
        limit: int = 50,
        mode: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetches moving telemetry samples, caching recently active points."""
        history = self.get_telemetry_history(session_key=session_key, driver_number=driver_number, limit=limit, mode=mode)
        moving = [pt for pt in history if pt.get("speed_kmh") is not None and pt.get("speed_kmh", 0) >= 30.0]
        return moving if moving else history

    def get_timing_tower(self, session_key: Optional[int] = None, mode: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetches live timing tower from the active or specified provider."""
        provider = get_live_provider(mode=mode)
        return provider.get_timing_tower(session_key=session_key)

    def get_race_control_messages(self, session_key: Optional[int] = None, mode: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetches race control incident logs from the live provider."""
        provider = get_live_provider(mode=mode)
        return provider.get_race_control_messages(session_key=session_key)

    def get_weather(self, session_key: Optional[int] = None, mode: Optional[str] = None) -> Dict[str, Any]:
        """Fetches weather and track temperature from the live provider."""
        provider = get_live_provider(mode=mode)
        return provider.get_weather(session_key=session_key)

    def get_test_stream_point(self, session_key: int, driver_number: int, index: int) -> Dict[str, Any]:
        """Controlled test stream sample for simulator mode."""
        return self.provider.get_test_stream_point(
            session_key=session_key,
            driver_number=driver_number,
            index=index
        )


# Global Singleton Service
live_telemetry_service = LiveTelemetryService()
