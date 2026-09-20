"""
Canonical Telemetry Model & Schema for Formula One Telemetry Analysis.
Defines standardized data structures, explicit physical units, and validation interfaces.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np


@dataclass
class TelemetryUnits:
    """Explicit physical units for canonical telemetry channels."""
    timestamp: str = "seconds (s)"
    distance: str = "meters (m)"
    speed: str = "kilometers per hour (km/h)"
    throttle: str = "percentage (%) [0.0 - 100.0]"
    brake: str = "percentage (%) [0.0 - 100.0] or binary"
    gear: str = "integer [0 - 8]"
    rpm: str = "revolutions per minute (RPM)"
    drs: str = "status code [0/1/8/10/12/14]"
    steering: str = "degrees (°)"


@dataclass
class CanonicalTelemetryPoint:
    """Represents a single high-frequency telemetry sample with explicit units."""
    timestamp_s: float
    distance_m: float
    speed_kmh: float
    throttle_pct: float
    brake_pct: float
    gear: int
    rpm: Optional[float] = None
    drs: Optional[int] = None
    steering_deg: Optional[float] = None


@dataclass
class CanonicalLapTelemetry:
    """
    Standardized container for a driver's single lap telemetry.
    Supports clean separation of raw and distance-aligned telemetry data.
    """
    driver_id: str
    lap_number: int
    lap_time_s: float
    session_id: str = "Unknown"
    compound: str = "UNKNOWN"
    tyre_age: int = 0
    raw_df: Optional[pd.DataFrame] = field(default=None, repr=False)
    cleaned_df: Optional[pd.DataFrame] = field(default=None, repr=False)
    units: TelemetryUnits = field(default_factory=TelemetryUnits)
    
    @property
    def channel_availability(self) -> Dict[str, bool]:
        """Returns map of available telemetry channels in cleaned_df."""
        df = self.cleaned_df if self.cleaned_df is not None else self.raw_df
        if df is None or df.empty:
            return {
                'timestamp': False, 'distance': False, 'speed': False,
                'throttle': False, 'brake': False, 'gear': False,
                'rpm': False, 'drs': False, 'steering': False
            }
        return {
            'timestamp': ('Time' in df.columns or 'timestamp_s' in df.columns),
            'distance': ('Distance' in df.columns or 'distance_m' in df.columns),
            'speed': ('Speed' in df.columns or 'speed_kmh' in df.columns),
            'throttle': ('Throttle' in df.columns or 'throttle_pct' in df.columns),
            'brake': ('Brake' in df.columns or 'brake_pct' in df.columns),
            'gear': ('nGear' in df.columns or 'gear' in df.columns),
            'rpm': bool('RPM' in df.columns and df['RPM'].notna().any()),
            'drs': bool('DRS' in df.columns and df['DRS'].notna().any()),
            'steering': bool('Steering' in df.columns and df['Steering'].notna().any())
        }

