"""
OpenF1 API Client with caching, timeouts, and structured logging.
"""
import requests
import requests_cache
from typing import Dict, List, Any, Optional
import logging
from datetime import timedelta
import time
import os

logger = logging.getLogger(__name__)

class OpenF1Client:
    def __init__(self, base_url: str = "https://api.openf1.org/v1", cache_name: str = "f1_cache/openf1_cache", expire_after: int = 3600):
        self.base_url = os.environ.get('OPENF1_BASE_URL', base_url).rstrip("/")

        # Ensure cache directory exists if a path is provided
        cache_dir = os.path.dirname(cache_name)
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)

        # Initialize a requests-cache session
        self.session = requests_cache.CachedSession(
            cache_name,
            backend='sqlite',
            expire_after=timedelta(seconds=expire_after),
            allowable_methods=('GET',)
        )
        self.timeout = int(os.environ.get('OPENF1_TIMEOUT', 10))
        self.max_retries = int(os.environ.get('OPENF1_RETRIES', 3))

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()

                if not getattr(response, 'from_cache', False):
                    logger.debug(f"OpenF1 API Hit: {url} {params}")
                else:
                    logger.debug(f"OpenF1 Cache Hit: {url} {params}")

                data = response.json()
                if not isinstance(data, list):
                    return [data] if data else []
                return data

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    logger.warning(f"Rate limited by OpenF1. Retrying... (Attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(2 ** attempt)
                    continue
                logger.error(f"HTTP Error querying OpenF1 {endpoint}: {e}")
                return []
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout querying OpenF1 {endpoint}. (Attempt {attempt + 1}/{self.max_retries})")
                time.sleep(1)
                continue
            except requests.exceptions.RequestException as e:
                logger.error(f"Request Error querying OpenF1 {endpoint}: {e}")
                return []

        logger.error(f"Max retries exceeded for OpenF1 {endpoint}")
        return []

    def get_meetings(self, year: Optional[int] = None, meeting_key: Optional[int] = None) -> List[Dict[str, Any]]:
        params = {}
        if year: params['year'] = year
        if meeting_key: params['meeting_key'] = meeting_key
        return self._make_request("meetings", params)

    def get_sessions(self, meeting_key: Optional[int] = None, session_key: Optional[int] = None, year: Optional[int] = None) -> List[Dict[str, Any]]:
        params = {}
        if meeting_key: params['meeting_key'] = meeting_key
        if session_key: params['session_key'] = session_key
        if year: params['year'] = year
        return self._make_request("sessions", params)

    def get_drivers(self, session_key: int) -> List[Dict[str, Any]]:
        return self._make_request("drivers", {"session_key": session_key})

    def get_laps(self, session_key: int, driver_number: Optional[int] = None) -> List[Dict[str, Any]]:
        params = {"session_key": session_key}
        if driver_number: params['driver_number'] = driver_number
        return self._make_request("laps", params)

    def get_car_data(self, session_key: int, driver_number: Optional[int] = None) -> List[Dict[str, Any]]:
        params = {"session_key": session_key}
        if driver_number: params['driver_number'] = driver_number
        return self._make_request("car_data", params)

    def get_intervals(self, session_key: int) -> List[Dict[str, Any]]:
        return self._make_request("intervals", {"session_key": session_key})

    def get_stints(self, session_key: int) -> List[Dict[str, Any]]:
        return self._make_request("stints", {"session_key": session_key})

    def get_pit_stops(self, session_key: int) -> List[Dict[str, Any]]:
        return self._make_request("pit", {"session_key": session_key})

    def get_race_control(self, session_key: int) -> List[Dict[str, Any]]:
        return self._make_request("race_control", {"session_key": session_key})

    def get_weather(self, session_key: int) -> List[Dict[str, Any]]:
        return self._make_request("weather", {"session_key": session_key})

    def get_location(self, session_key: int, driver_number: Optional[int] = None) -> List[Dict[str, Any]]:
        params = {"session_key": session_key}
        if driver_number: params['driver_number'] = driver_number
        return self._make_request("location", params)

    def get_session_result(self, session_key: int) -> List[Dict[str, Any]]:
        return self._make_request("session_result", {"session_key": session_key})
