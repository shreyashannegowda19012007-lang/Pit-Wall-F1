"""
Jolpica-F1 API Client for historical championship data.
"""
import requests
import requests_cache
from typing import Dict, List, Any, Optional
import logging
from datetime import timedelta
import time
import os

logger = logging.getLogger(__name__)

class JolpicaF1Client:
    def __init__(self, base_url: str = "https://api.jolpi.ca/ergast/f1", cache_name: str = "f1_cache/jolpica_cache", expire_after: int = 86400):
        self.base_url = os.environ.get('JOLPICA_BASE_URL', base_url).rstrip("/")
        
        # Ensure cache directory exists if a path is provided
        cache_dir = os.path.dirname(cache_name)
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
        
        self.session = requests_cache.CachedSession(
            cache_name,
            backend='sqlite',
            expire_after=timedelta(seconds=expire_after),
            allowable_methods=('GET',)
        )
        self.timeout = int(os.environ.get('JOLPICA_TIMEOUT', 10))
        self.max_retries = int(os.environ.get('JOLPICA_RETRIES', 3))

    def _make_request(self, endpoint: str) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}.json"
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                if not getattr(response, 'from_cache', False):
                    logger.debug(f"Jolpica API Hit: {url}")
                else:
                    logger.debug(f"Jolpica Cache Hit: {url}")
                    
                data = response.json()
                return data.get("MRData", {})
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    logger.warning(f"Rate limited by Jolpica. Retrying... (Attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(2 ** attempt)
                    continue
                logger.error(f"HTTP Error querying Jolpica {endpoint}: {e}")
                return {}
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout querying Jolpica {endpoint}. (Attempt {attempt + 1}/{self.max_retries})")
                time.sleep(1)
                continue
            except requests.exceptions.RequestException as e:
                logger.error(f"Request Error querying Jolpica {endpoint}: {e}")
                return {}
                
        logger.error(f"Max retries exceeded for Jolpica {endpoint}")
        return {}

    def get_seasons(self, limit: int = 30) -> List[Dict[str, Any]]:
        res = self._make_request(f"seasons?limit={limit}")
        return res.get("SeasonTable", {}).get("Seasons", [])

    def get_circuits(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        endpoint = f"{year}/circuits" if year else "circuits"
        res = self._make_request(endpoint)
        return res.get("CircuitTable", {}).get("Circuits", [])

    def get_constructors(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        endpoint = f"{year}/constructors" if year else "constructors"
        res = self._make_request(endpoint)
        return res.get("ConstructorTable", {}).get("Constructors", [])

    def get_drivers(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        endpoint = f"{year}/drivers" if year else "drivers"
        res = self._make_request(endpoint)
        return res.get("DriverTable", {}).get("Drivers", [])

    def get_race_schedule(self, year: int) -> List[Dict[str, Any]]:
        res = self._make_request(f"{year}")
        return res.get("RaceTable", {}).get("Races", [])

    def get_race_results(self, year: int, round_number: int) -> List[Dict[str, Any]]:
        res = self._make_request(f"{year}/{round_number}/results")
        races = res.get("RaceTable", {}).get("Races", [])
        return races[0].get("Results", []) if races else []

    def get_qualifying_results(self, year: int, round_number: int) -> List[Dict[str, Any]]:
        res = self._make_request(f"{year}/{round_number}/qualifying")
        races = res.get("RaceTable", {}).get("Races", [])
        return races[0].get("QualifyingResults", []) if races else []

    def get_driver_standings(self, year: int, round_number: Optional[int] = None) -> List[Dict[str, Any]]:
        endpoint = f"{year}/{round_number}/driverStandings" if round_number else f"{year}/driverStandings"
        res = self._make_request(endpoint)
        lists = res.get("StandingsTable", {}).get("StandingsLists", [])
        return lists[0].get("DriverStandings", []) if lists else []
        
    def get_constructor_standings(self, year: int, round_number: Optional[int] = None) -> List[Dict[str, Any]]:
        endpoint = f"{year}/{round_number}/constructorStandings" if round_number else f"{year}/constructorStandings"
        res = self._make_request(endpoint)
        lists = res.get("StandingsTable", {}).get("StandingsLists", [])
        return lists[0].get("ConstructorStandings", []) if lists else []

    def get_pit_stops(self, year: int, round_number: int) -> List[Dict[str, Any]]:
        res = self._make_request(f"{year}/{round_number}/pitstops")
        races = res.get("RaceTable", {}).get("Races", [])
        return races[0].get("PitStops", []) if races else []
