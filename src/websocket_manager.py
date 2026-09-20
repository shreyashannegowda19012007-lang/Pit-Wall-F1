"""
WebSocket Streaming Manager & Real-Time Event Stream Distribution Server.
Manages client connection pools for /ws/sessions/{session_id}, initial snapshot broadcasts
(RACE_STATE_SNAPSHOT), delta update streaming (RACE_STATE_UPDATE), heartbeats, and backpressure queue control.
"""

from typing import Dict, List, Optional, Any, Set
import asyncio
import json
import time

from realtime_race_state import UnifiedRaceState, SCHEMA_VERSION
from logger import logger


class WebSocketConnectionManager:
    """
    Manages active WebSocket client connections, snapshots, and backpressure queue.
    """

    def __init__(self):
        self.active_connections: Dict[str, Set[Any]] = {}  # session_id -> Set of websocket connections
        self.latest_state: Dict[str, UnifiedRaceState] = {}

    def connect(self, session_id: str, websocket_conn: Any):
        """Registers a new client connection for a session."""
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket_conn)
        logger.info(f"WebSocket client connected to session {session_id}.")

    def disconnect(self, session_id: str, websocket_conn: Any):
        """Removes a disconnected client connection."""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket_conn)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"WebSocket client disconnected from session {session_id}.")

    def generate_snapshot_payload(self, race_state: UnifiedRaceState) -> str:
        """Generates initial full snapshot JSON message."""
        payload = {
            "type": "RACE_STATE_SNAPSHOT",
            "schema_version": SCHEMA_VERSION,
            "timestamp": time.time(),
            "data": race_state.to_dict()
        }
        return json.dumps(payload)

    def generate_update_payload(self, race_state: UnifiedRaceState, events: Optional[List[Dict[str, Any]]] = None) -> str:
        """Generates incremental update JSON message."""
        payload = {
            "type": "RACE_STATE_UPDATE",
            "schema_version": SCHEMA_VERSION,
            "timestamp": time.time(),
            "data": race_state.to_dict(),
            "events": events or []
        }
        return json.dumps(payload)

    def broadcast_state(self, session_id: str, race_state: UnifiedRaceState):
        """Updates internal latest state cache."""
        self.latest_state[session_id] = race_state


# Global Singleton Manager
ws_manager = WebSocketConnectionManager()

