"""
Future-Data Leakage Guard & Information Boundary Engine.
Strictly enforces chronological information boundaries during historical race replays.
Raises DataLeakageError if any model component attempts to access future telemetry,
future weather, future safety-car events, or future race outcomes.
"""

from typing import Dict, List, Optional, Any, Tuple
import pandas as pd


class DataLeakageError(Exception):
    """
    Raised when a component attempts to access future historical data during a replay decision point.
    """
    def __init__(self, requested_lap: int, current_lap: int, detail: str = ""):
        message = f"CRITICAL DATA LEAKAGE VIOLATION: Requested Lap {requested_lap} > Current Replay Lap {current_lap}. {detail}"
        super().__init__(message)
        self.requested_lap = requested_lap
        self.current_lap = current_lap


class HistoricalInformationFilter:
    """
    Guards telemetry datasets by strictly slicing data with LapNumber <= current_lap.
    """

    def __init__(self, laps_df: pd.DataFrame, session: Any = None):
        self.laps_df = laps_df.copy() if laps_df is not None else pd.DataFrame()
        self.session = session

    def get_sliced_laps(self, current_lap: int) -> pd.DataFrame:
        """Returns dataframe strictly sliced up to current_lap."""
        if self.laps_df.empty:
            return pd.DataFrame()
        return self.laps_df[self.laps_df['LapNumber'] <= current_lap].copy()

    def assert_no_future_access(self, requested_lap: int, current_lap: int, context: str = ""):
        """Raises DataLeakageError if requested_lap > current_lap."""
        if requested_lap > current_lap:
            raise DataLeakageError(requested_lap, current_lap, context)

    def validate_dataframe_sliced(self, df: pd.DataFrame, current_lap: int, context: str = ""):
        """Validates that no row in df contains LapNumber > current_lap."""
        if df.empty or 'LapNumber' not in df.columns:
            return
        max_lap = int(df['LapNumber'].max())
        if max_lap > current_lap:
            raise DataLeakageError(max_lap, current_lap, f"Dataframe in {context} contains Lap {max_lap} exceeding cutoff Lap {current_lap}.")
