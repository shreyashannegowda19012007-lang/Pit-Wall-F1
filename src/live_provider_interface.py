"""
Pitwall F1 — Live Telemetry Provider Abstraction Interface.
Defines the authoritative contract for live Formula 1 telemetry and timing data sources.
Allows seamless pluggability between live providers (e.g. F1 SignalR Core, OpenF1 Historical, Local Replay)
without rewriting frontend telemetry dashboards or consumers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class BaseLiveProvider(ABC):
    """
    Abstract Base Class defining the contract for live telemetry and timing providers.
    """

    @abstractmethod
    def get_provider_name(self) -> str:
        """Returns the human-readable provider name (e.g. 'F1 Live Timing SignalR Core')."""
        pass

    @abstractmethod
    def get_provider_type(self) -> str:
        """Returns the provider classification identifier ('F1_SIGNALR_CORE', 'OPENF1', etc.)."""
        pass

    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """Returns provider metadata, license info, URL, supported channels, and pricing tier (Free/Paid)."""
        pass

    @abstractmethod
    def get_live_status(self) -> Dict[str, Any]:
        """
        Evaluates current provider availability, active F1 session state, data freshness,
        and transport metrics.
        """
        pass

    @abstractmethod
    def get_sessions(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Discovers current or upcoming sessions from the provider."""
        pass

    @abstractmethod
    def get_session_drivers(self, session_key: int) -> List[Dict[str, Any]]:
        """Retrieves the active driver roster participating in the session."""
        pass

    @abstractmethod
    def get_latest_telemetry(self, session_key: int, driver_number: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves the latest available car telemetry sample for a driver.
        If car telemetry is not provided by the active source, returns None or a record
        clearly marked with provenance and unavailable channels.
        """
        pass

    @abstractmethod
    def get_telemetry_history(
        self,
        session_key: int,
        driver_number: int,
        limit: int = 50,
        since_timestamp: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves bounded telemetry history for rolling strip charts."""
        pass

    @abstractmethod
    def get_timing_tower(self, session_key: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieves live timing tower positions, gaps, sector times, and tyre data."""
        pass

    @abstractmethod
    def get_race_control_messages(self, session_key: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieves official FIA race control incidents, flags, and investigations."""
        pass

    @abstractmethod
    def get_weather(self, session_key: Optional[int] = None) -> Dict[str, Any]:
        """Retrieves track temperature, air temperature, wind, and rain status."""
        pass

    @abstractmethod
    def get_test_stream_point(self, session_key: int, driver_number: int, index: int) -> Dict[str, Any]:
        """
        Generates an explicitly labeled test stream sample for testing animations and UI charts.
        Must strictly carry provenance='TEST_STREAM' and is_test_stream=True.
        """
        pass
