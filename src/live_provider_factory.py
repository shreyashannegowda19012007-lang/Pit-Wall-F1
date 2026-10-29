"""
Pitwall F1 — Live Telemetry Provider Factory.
Provides decoupled resolution of the active live telemetry provider.
Defaults to the legitimate, free F1SignalRProvider, with optional configuration
for historical or replay providers.
"""

import os
from typing import Optional, List, Dict, Any
from src.live_provider_interface import BaseLiveProvider
from src.f1_signalr_service import f1_signalr_provider
from src.historical_replay_service import historical_replay_provider

# Active singleton provider instance and mode
_active_provider: Optional[BaseLiveProvider] = None
_active_mode: str = "LIVE"  # "LIVE", "HISTORICAL_REPLAY", "TEST_STREAM"


def get_live_provider(mode: Optional[str] = None) -> BaseLiveProvider:
    """
    Returns the configured active telemetry provider.
    Defaults to the free official F1 SignalR provider (f1_signalr_provider) in LIVE mode,
    or historical_replay_provider in HISTORICAL_REPLAY mode.
    """
    global _active_provider, _active_mode
    target_mode = (mode or _active_mode or os.environ.get("PITWALL_LIVE_PROVIDER", "LIVE")).upper()

    if target_mode in ["REPLAY", "HISTORICAL_REPLAY", "FASTF1_REPLAY"]:
        return historical_replay_provider

    if _active_provider is None:
        _active_provider = f1_signalr_provider
    return _active_provider


def set_live_provider(provider: BaseLiveProvider):
    """Dynamically set the active live provider (useful for testing or switching modes)."""
    global _active_provider
    _active_provider = provider


def set_active_provider_mode(mode: str) -> Dict[str, Any]:
    """Switches the active provider mode ('LIVE', 'HISTORICAL_REPLAY', 'TEST_STREAM')."""
    global _active_mode, _active_provider
    mode_upper = mode.upper()
    _active_mode = mode_upper
    if mode_upper in ["REPLAY", "HISTORICAL_REPLAY", "FASTF1_REPLAY"]:
        _active_provider = historical_replay_provider
    else:
        _active_provider = f1_signalr_provider
    return {"success": True, "active_mode": _active_mode}


def get_active_provider_mode() -> str:
    """Returns the current active provider mode identifier."""
    global _active_mode
    return _active_mode


def get_provider_for_mode(mode: str) -> BaseLiveProvider:
    """Returns the provider associated with a specific mode without changing the global default."""
    m = mode.upper()
    if m in ["REPLAY", "HISTORICAL_REPLAY", "FASTF1_REPLAY"]:
        return historical_replay_provider
    return f1_signalr_provider


def get_available_providers() -> List[Dict[str, Any]]:
    """Returns metadata for all available providers."""
    return [
        {
            "mode": "LIVE",
            **f1_signalr_provider.get_provider_info()
        },
        {
            "mode": "HISTORICAL_REPLAY",
            **historical_replay_provider.get_provider_info()
        }
    ]

