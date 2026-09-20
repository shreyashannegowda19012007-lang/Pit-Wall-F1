"""
Formal Telemetry Schema & Field Definitions for F1 Time-Series Data Pipeline.
Defines explicit field types, physical units, nullability constraints, valid ranges, and descriptions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import pandas as pd
import numpy as np


class DataStatus(Enum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    EMPTY = "EMPTY"
    UNAVAILABLE = "UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    INVALID = "INVALID"
    NOT_MEASURED = "NOT_MEASURED"
    RATE_LIMITED = "RATE_LIMITED"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    SCHEMA_ERROR = "SCHEMA_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"


@dataclass
class DataProvenance:
    provider_name: str
    endpoint: str
    session_identifier: str
    retrieval_timestamp: str
    historical_or_live: str
    cache_status: str
    schema_version: str
    data_completeness: DataStatus



@dataclass
class FieldDefinition:
    """Explicit metadata definition for a single telemetry channel field."""
    name: str
    dtype: str
    unit: str
    nullable: bool
    min_val: Optional[float]
    max_val: Optional[float]
    description: str


TELEMETRY_SCHEMA: Dict[str, FieldDefinition] = {
    "Time": FieldDefinition("Time", "timedelta64[ns]", "timedelta", False, None, None, "Elapsed time from session/lap start"),
    "timestamp_s": FieldDefinition("timestamp_s", "float64", "seconds (s)", False, 0.0, 10000.0, "Timestamp in seconds since lap start"),
    "session_id": FieldDefinition("session_id", "string", "identifier", False, None, None, "Unique session reference key"),
    "driver_id": FieldDefinition("driver_id", "string", "identifier", False, None, None, "Driver abbreviation code (e.g. VER, HAM)"),
    "car_id": FieldDefinition("car_id", "string", "identifier", True, None, None, "Chassis / car number reference"),
    "lap_number": FieldDefinition("lap_number", "int64", "integer", False, 1, 200, "Lap number in session"),
    "Distance": FieldDefinition("Distance", "float64", "meters (m)", False, 0.0, 10000.0, "Distance along track from start/finish line"),
    "Speed": FieldDefinition("Speed", "float64", "km/h", False, 0.0, 390.0, "Car ground speed"),
    "Throttle": FieldDefinition("Throttle", "float64", "%", False, 0.0, 100.0, "Throttle pedal position percentage"),
    "Brake": FieldDefinition("Brake", "float64", "%", False, 0.0, 100.0, "Brake application percentage or boolean"),
    "nGear": FieldDefinition("nGear", "int64", "integer", False, 0, 8, "Current transmission gear ratio"),
    "RPM": FieldDefinition("RPM", "float64", "RPM", True, 0.0, 16000.0, "Internal combustion engine speed"),
    "DRS": FieldDefinition("DRS", "int64", "status_code", True, 0, 14, "Drag Reduction System status flag"),
    "Steering": FieldDefinition("Steering", "float64", "degrees (°)", True, -540.0, 540.0, "Steering wheel angle"),
    "Sector": FieldDefinition("Sector", "int64", "integer", True, 1, 3, "Track sector indicator (1, 2, or 3)"),
    "Compound": FieldDefinition("Compound", "string", "category", True, None, None, "Tyre compound specification (SOFT, MEDIUM, HARD, INTERMEDIATE, WET)"),
    "fuel_load": FieldDefinition("fuel_load", "float64", "kg", True, 0.0, 110.0, "Estimated remaining fuel mass"),
    "engine_mode": FieldDefinition("engine_mode", "string", "category", True, None, None, "ICE/ERS power unit deployment mode"),
    "track_temperature": FieldDefinition("track_temperature", "float64", "°C", True, 0.0, 70.0, "Ambient track surface temperature"),
    "air_temperature": FieldDefinition("air_temperature", "float64", "°C", True, -10.0, 60.0, "Ambient air temperature")
}


def validate_schema_compliance(df: pd.DataFrame) -> Tuple[bool, List[str], List[str]]:
    """
    Validates a telemetry DataFrame against the formal TELEMETRY_SCHEMA definition.
    Returns (is_compliant, list_of_errors, list_of_warnings).
    """
    errors: List[str] = []
    warnings: List[str] = []

    if df is None or df.empty:
        return False, ["DataFrame is null or empty."], []

    # Required Mandatory Channels
    mandatory_fields = ["Distance", "Speed"]
    for field_name in mandatory_fields:
        if field_name not in df.columns:
            # Check canonical alias
            alias = TELEMETRY_SCHEMA[field_name].name
            if alias not in df.columns:
                errors.append(f"Mandatory schema channel missing: '{field_name}'.")

    # Check field boundaries & types for present columns
    for col in df.columns:
        if col in TELEMETRY_SCHEMA:
            field_def = TELEMETRY_SCHEMA[col]
            vals = df[col].dropna()

            if not field_def.nullable and len(vals) < len(df):
                num_null = len(df) - len(vals)
                warnings.append(f"Non-nullable channel '{col}' contains {num_null} null values.")

            if field_def.min_val is not None and len(vals) > 0:
                if (vals < field_def.min_val).any():
                    num_below = (vals < field_def.min_val).sum()
                    warnings.append(f"Channel '{col}' contains {num_below} values below min threshold {field_def.min_val} {field_def.unit}.")

            if field_def.max_val is not None and len(vals) > 0:
                if (vals > field_def.max_val).any():
                    num_above = (vals > field_def.max_val).sum()
                    warnings.append(f"Channel '{col}' contains {num_above} values above max threshold {field_def.max_val} {field_def.unit}.")

    is_compliant = len(errors) == 0
    return is_compliant, errors, warnings

