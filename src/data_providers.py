import os
import pandas as pd
import fastf1
import requests
import json
import logging
from fastf1.core import Session
from datetime import datetime, timezone

from openf1_client import OpenF1Client
from jolpica_client import JolpicaF1Client
from telemetry_schema import DataProvenance, DataStatus

logger = logging.getLogger(__name__)

class BaseDataProvider:
    def fetch_session_data(self, year, event, session_type):
        raise NotImplementedError

    def fetch_live_session_data(self, year, event, session_type, live_file_path):
        raise NotImplementedError

    def get_championship_standings(self, year, round_number=None):
        return {"success": False, "error": "UNAVAILABLE", "reason": "Not supported by this provider."}

    def get_race_results(self, year, round_number):
        return {"success": False, "error": "UNAVAILABLE", "reason": "Not supported by this provider."}

class FastF1Provider(BaseDataProvider):
    """Legacy FastF1 Provider for historical sessions."""
    def __init__(self):
        self.provider_name = "FastF1"

    def fetch_session_data(self, year, event, session_type):
        try:
            from src.universal_session_engine import SessionPreparationManager
            status = SessionPreparationManager.check_session_status(year, event, session_type)
            if status["status"] == "PREPARING":
                return {"success": False, "error": "Session data is downloading from FIA in the background... Please retry in a few moments.", "status": DataStatus.UNAVAILABLE}
            elif status["status"] == "NOT_PREPARED":
                SessionPreparationManager.prepare_session_async(year, event, session_type)
                return {"success": False, "error": "Session data is downloading from FIA in the background... Please retry in a few moments.", "status": DataStatus.UNAVAILABLE}

            session = fastf1.get_session(year, event, session_type)
            session.load(laps=True, telemetry=True, weather=True, messages=True)

            if session.laps is None or session.laps.empty:
                return {"success": False, "error": "Telemetry array not yet finalized by FIA.", "status": DataStatus.PARTIAL}
        except Exception as e:
            if "not been loaded yet" in str(e):
                return {"success": False, "error": "Telemetry array not yet available.", "status": DataStatus.UNAVAILABLE}
            return {"success": False, "error": str(e), "status": DataStatus.NETWORK_ERROR}

        def safe_extract(val, default=0):
            try:
                if isinstance(val, pd.Series):
                    return default if val.empty else val.iloc[0]
                return val
            except Exception:
                return default

        weather_df = session.weather_data.copy()
        info = {
            "MeetingName": session.event.get('EventName', 'Unknown Event'),
            "SessionName": session.name,
            "Location": session.event.get('Location', 'Unknown Location'),
            "TrackStatus": session.session_info.get('Status', 'Unknown') if hasattr(session, 'session_info') else 'Unknown',
            "AirTemp": safe_extract(weather_df['AirTemp'].iloc[-1]) if not weather_df.empty else 0,
            "TrackTemp": safe_extract(weather_df['TrackTemp'].iloc[-1]) if not weather_df.empty else 0,
            "Rainfall": safe_extract(weather_df['Rainfall'].iloc[-1], False) if not weather_df.empty else False
        }

        prov = DataProvenance(
            provider_name=self.provider_name,
            endpoint="fastf1",
            session_identifier=f"{year}-{event}-{session_type}",
            retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
            historical_or_live="historical",
            cache_status="unknown",
            schema_version="v2.4.0",
            data_completeness=DataStatus.AVAILABLE
        )

        return {
            "success": True,
            "laps": session.laps.copy(),
            "results": session.results.copy(),
            "weather": weather_df,
            "messages": pd.DataFrame(session.race_control_messages),
            "info": info,
            "raw_session": session,
            "provenance": prov
        }

    def fetch_live_session_data(self, year, event, session_type, live_file_path):
        return {"success": False, "error": "FastF1 Live stream is deprecated. Switch to OpenF1 Live.", "status": DataStatus.UNAVAILABLE}

class OpenF1Provider(BaseDataProvider):
    """OpenF1 Provider for Historical and Live sessions."""
    def __init__(self):
        self.provider_name = "OpenF1"
        self.client = OpenF1Client()
        self.fallback = FastF1Provider()

    def fetch_session_data(self, year, event, session_type):
        try:
            # We wrap the historical fastf1 provider here because translating the ENTIRE fastf1 complex
            # telemetry matrix (X, Y, Z, RPM, Gear, DRS, etc.) from raw OpenF1 REST would require 10k lines
            # of data munging. As per requirements: "Do not modify existing architecture".
            # The AI modules use `.get_telemetry().add_distance()`, which is deeply coupled to FastF1.
            logger.info("OpenF1 fallback: Using FastF1 for detailed historical telemetry matrix.")
            return self.fallback.fetch_session_data(year, event, session_type)
        except Exception as e:
            return {"success": False, "error": f"OpenF1 REST Error: {e}", "status": DataStatus.NETWORK_ERROR}

    def fetch_live_session_data(self, year, event, session_type, live_file_path):
        """Reads the live stream state generated by the OpenF1 MQTT worker."""

        # Check for authentication errors first
        err_path = live_file_path + ".err"
        if os.path.exists(err_path):
            with open(err_path, 'r', encoding='utf-8') as f:
                err_msg = f.read().strip()
            return {"success": False, "error": err_msg, "status": DataStatus.AUTH_REQUIRED}

        if not os.path.exists(live_file_path):
            return {"success": False, "error": "OpenF1 MQTT uplink active, awaiting telemetry...", "status": DataStatus.UNAVAILABLE}

        try:
            with open(live_file_path, 'r', encoding='utf-8') as f:
                state = json.load(f)

            if not state.get('laps'):
                return {"success": False, "error": "Awaiting valid laps from OpenF1 stream...", "status": DataStatus.PARTIAL}

            session = fastf1.get_session(year, event, session_type)

            # Map OpenF1 state back to Pandas DataFrames for legacy modules
            laps_df = pd.DataFrame(state['laps'])
            results_df = pd.DataFrame(state.get('drivers', []))
            weather_df = pd.DataFrame(state.get('weather', []))
            messages_df = pd.DataFrame(state.get('race_control', []))

            info = {
                "MeetingName": event,
                "SessionName": session_type,
                "Location": "Unknown",
                "TrackStatus": "1",
                "AirTemp": weather_df.iloc[-1].get('air_temperature', 0) if not weather_df.empty else 0,
                "TrackTemp": weather_df.iloc[-1].get('track_temperature', 0) if not weather_df.empty else 0,
                "Rainfall": False
            }

            session.laps = fastf1.core.Laps(laps_df)
            session.laps.session = session
            session.results = results_df

            prov = DataProvenance(
                provider_name=self.provider_name,
                endpoint="mqtt_stream",
                session_identifier=f"{year}-{event}-{session_type}",
                retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
                historical_or_live="live",
                cache_status="uncached",
                schema_version="v2.4.0",
                data_completeness=DataStatus.AVAILABLE
            )

            return {
                "success": True,
                "laps": laps_df,
                "results": results_df,
                "weather": weather_df,
                "messages": messages_df,
                "info": info,
                "raw_session": session,
                "openf1_location": pd.DataFrame(state.get('location', [])),
                "provenance": prov
            }
        except Exception as e:
            return {"success": False, "error": f"OpenF1 Stream Parse Error: {e}", "status": DataStatus.SCHEMA_ERROR}


class JolpicaF1Provider(BaseDataProvider):
    """Jolpica-F1 Provider for Historical Results and Standings."""
    def __init__(self):
        self.provider_name = "JolpicaF1"
        self.client = JolpicaF1Client()

    def get_championship_standings(self, year, round_number=None):
        try:
            standings = self.client.get_driver_standings(year, round_number)
            if not standings:
                return {"success": False, "error": "No standings data found.", "status": DataStatus.EMPTY}

            prov = DataProvenance(
                provider_name=self.provider_name,
                endpoint="driverStandings",
                session_identifier=f"{year}-{round_number or 'final'}",
                retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
                historical_or_live="historical",
                cache_status="cached",
                schema_version="v2.4.0",
                data_completeness=DataStatus.AVAILABLE
            )

            return {
                "success": True,
                "standings": standings,
                "provenance": prov
            }
        except Exception as e:
            return {"success": False, "error": str(e), "status": DataStatus.NETWORK_ERROR}

    def get_race_results(self, year, round_number):
        try:
            results = self.client.get_race_results(year, round_number)
            if not results:
                return {"success": False, "error": "No race results found.", "status": DataStatus.EMPTY}

            prov = DataProvenance(
                provider_name=self.provider_name,
                endpoint="results",
                session_identifier=f"{year}-{round_number}",
                retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
                historical_or_live="historical",
                cache_status="cached",
                schema_version="v2.4.0",
                data_completeness=DataStatus.AVAILABLE
            )

            return {
                "success": True,
                "results": results,
                "provenance": prov
            }
        except Exception as e:
            return {"success": False, "error": str(e), "status": DataStatus.NETWORK_ERROR}

def get_provider():
    """Factory for default telemetry provider with fallback logic."""
    provider_env = os.environ.get('F1_DATA_PROVIDER', 'OPENF1')

    # We maintain explicit fallback logging
    if provider_env.upper() == 'OPENF1':
        logger.info("Primary Provider Selected: OpenF1 (Fallback to FastF1 for telemetry matrix)")
        return OpenF1Provider()

    if provider_env.upper() == 'JOLPICA':
        logger.info("Primary Provider Selected: JolpicaF1")
        return JolpicaF1Provider()

    logger.info("Primary Provider Selected: FastF1")
    return FastF1Provider()
