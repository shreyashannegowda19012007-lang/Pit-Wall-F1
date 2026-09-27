"""
Version-Aware In-Memory LRU Caching Service.
Caches expensive Monte Carlo simulation results, telemetry alignments, and backtest replays.
Ensures cache keys incorporate model version & dataset version to prevent stale results.
"""

from typing import Dict, Any, Optional
import time
import hashlib


class VersionAwareCache:
    """
    In-memory version-aware caching service.
    """

    def __init__(self, max_items: int = 100, ttl_seconds: int = 3600):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.max_items = max_items
        self.ttl_seconds = ttl_seconds

    def _generate_key(self, dataset_version: str, driver: str, lap: int, model_version: str, extra_params: str = "") -> str:
        raw_key = f"{dataset_version}:{driver}:{lap}:{model_version}:{extra_params}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def get(self, dataset_version: str, driver: str, lap: int, model_version: str, extra_params: str = "") -> Optional[Any]:
        """Retrieves non-expired cached value if key exists."""
        key = self._generate_key(dataset_version, driver, lap, model_version, extra_params)
        entry = self._cache.get(key)
        if not entry:
            return None

        if time.time() - entry["timestamp"] > self.ttl_seconds:
            del self._cache[key]
            return None

        return entry["value"]

    def set(self, dataset_version: str, driver: str, lap: int, model_version: str, value: Any, extra_params: str = ""):
        """Sets cached entry, pruning oldest item if max_items exceeded."""
        if len(self._cache) >= self.max_items:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["timestamp"])
            del self._cache[oldest_key]

        key = self._generate_key(dataset_version, driver, lap, model_version, extra_params)
        self._cache[key] = {
            "value": value,
            "timestamp": time.time()
        }

    def clear(self):
        """Clears all cached entries."""
        self._cache.clear()


cache_service = VersionAwareCache()
