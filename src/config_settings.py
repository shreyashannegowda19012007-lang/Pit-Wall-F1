"""
Central Configuration & Environment Settings Manager.
Reads configuration from environment variables with safe production defaults.
"""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class AppConfig:
    """Production Application Configuration settings."""
    app_name: str = "Pitwall F1 Race Engineering Platform"
    app_version: str = "v2.4.0"
    environment: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./pitwall_f1.db")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    cors_origins: List[str] = field(default_factory=lambda: os.getenv("CORS_ORIGINS", "*").split(","))
    default_simulation_seed: int = int(os.getenv("DEFAULT_SIMULATION_SEED", "42"))
    default_simulation_count: int = int(os.getenv("DEFAULT_SIMULATION_COUNT", "10000"))
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

    def is_production(self) -> bool:
        return self.environment.lower() in ("production", "prod")


config = AppConfig()

