"""
Authoritative Unified Race State Engine & Multi-Source Data Adapters.
Defines versioned race-state schemas (v2.4.0), canonical units enforcement, provider abstractions
(FastF1Provider, OpenF1Provider, ReplayAdapter), and deterministic state snapshot normalization.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
import datetime
import json
import abc
import pandas as pd
import numpy as np


SCHEMA_VERSION = "v2.4.0"


@dataclass
class RaceControlEvent:
    event_id: str
    timestamp_s: float
    session_id: str
    event_type: str      # "SAFETY_CAR", "VSC", "RED_FLAG", "PIT_ENTRY", "OVERTAKE", "WEATHER_UPDATE"
    message: str
    flag: str = "GREEN"


@dataclass
class DriverRaceState:
    driver_id: str
    driver_name: str
    number: int
    team: str
    position: int
    grid_position: int
    lap_number: int
    distance_m: float
    sector: int
    speed_kmh: float
    gear: int
    throttle_pct: float
    brake_pct: float
    drs_status: int           # 0=Off, 1=Available, 8,10,12,14=Active
    tyre_compound: str        # "SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"
    tyre_age_laps: int
    stint_number: int
    pit_status: str           # "ON_TRACK", "IN_PIT_LANE", "PITTING"
    gap_to_leader_s: Optional[float]
    interval_to_ahead_s: Optional[float]
    last_lap_s: float
    best_lap_s: float
    x: float
    y: float
    z: float
    heading_deg: float
    laps_behind_leader: int = 0
    timing_status: str = "VALID" # "VALID", "UNAVAILABLE", "LAPPED", "RETIRED"


@dataclass
class UnifiedRaceState:
    """
    Authoritative single-source-of-truth race state payload.
    """
    session_id: str
    schema_version: str = SCHEMA_VERSION
    mode: str = "REPLAY"            # "LIVE" or "REPLAY"
    timestamp_s: float = 0.0
    elapsed_time_s: float = 0.0
    current_lap: int = 1
    total_laps: int = 57
    session_status: str = "IN_PROGRESS"
    track_status: str = "GREEN"      # "GREEN", "YELLOW", "VSC", "SC", "RED_FLAG"
    air_temp_c: float = 25.0
    track_temp_c: float = 30.0
    rainfall: bool = False
    drivers: Dict[str, DriverRaceState] = field(default_factory=dict)
    race_control_messages: List[RaceControlEvent] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


class BaseDataProvider(abc.ABC):
    """
    Abstract Interface for Race Data Providers.
    """

    @abc.abstractmethod
    def fetch_current_race_state(self, session_id: str, timestamp_s: float) -> UnifiedRaceState:
        pass


class ReplayAdapter(BaseDataProvider):
    """
    Replay Data Provider Adapter normalizing FastF1 / session telemetry into UnifiedRaceState.
    """

    def __init__(self, laps_df: pd.DataFrame, results_df: Optional[pd.DataFrame] = None):
        self.laps_df = laps_df
        self.results_df = results_df

    def fetch_current_race_state(self, session_id: str, timestamp_s: float) -> UnifiedRaceState:
        if self.laps_df is None or self.laps_df.empty:
            return UnifiedRaceState(
                session_id=session_id,
                schema_version=SCHEMA_VERSION,
                mode="REPLAY",
                timestamp_s=timestamp_s,
                elapsed_time_s=timestamp_s,
                current_lap=0,
                total_laps=0,
                session_status="DATA UNAVAILABLE",
                track_status="UNKNOWN",
                drivers={},
                race_control_messages=[]
            )

        try:
            # Replay time in timedelta, normalized to start of session
            t_start = pd.Timedelta(seconds=0)
            if 'LapStartTime' in self.laps_df.columns and not self.laps_df['LapStartTime'].empty:
                t_start = self.laps_df['LapStartTime'].min()

            replay_td = t_start + pd.Timedelta(seconds=timestamp_s)

            # Filter laps up to the replay timestamp
            # 'Time' in fastf1 is the session time at the end of the lap
            # We also include laps that started before timestamp (LapStartTime <= timestamp)
            if 'LapStartTime' in self.laps_df.columns:
                past_laps = self.laps_df[self.laps_df['LapStartTime'] <= replay_td]
            else:
                past_laps = self.laps_df[self.laps_df['Time'] <= replay_td]

            drivers_state = {}
            current_max_lap = 0

            if not past_laps.empty:
                for driver_id in past_laps['Driver'].unique():
                    driver_laps = past_laps[past_laps['Driver'] == driver_id]
                    if driver_laps.empty:
                        continue

                    last_lap_record = driver_laps.iloc[-1]
                    lap_number = int(last_lap_record['LapNumber'])
                    if lap_number > current_max_lap:
                        current_max_lap = lap_number

                    compound = str(last_lap_record.get('Compound', 'UNKNOWN'))

                    tyre_life_val = last_lap_record.get('TyreLife', 1)
                    tyre_life = 1 if pd.isna(tyre_life_val) else int(tyre_life_val)

                    position_val = last_lap_record.get('Position', 0)
                    position = 0 if pd.isna(position_val) else int(position_val)

                    status_val = "ON_TRACK"
                    if 'PitOutTime' in last_lap_record and not pd.isna(last_lap_record['PitOutTime']):
                        if last_lap_record['PitOutTime'] > replay_td:
                            status_val = "IN_PIT"
                    if 'PitInTime' in last_lap_record and not pd.isna(last_lap_record['PitInTime']):
                        if last_lap_record['PitInTime'] <= replay_td:
                            status_val = "IN_PIT"

                    last_lap_time = last_lap_record.get('LapTime')
                    last_lap_time_ms = 0
                    if pd.notna(last_lap_time) and isinstance(last_lap_time, pd.Timedelta):
                        last_lap_time_ms = int(last_lap_time.total_seconds() * 1000)

                    driver_name = str(driver_id)
                    number = 0
                    team = "UNKNOWN"
                    grid_position = 0

                    if self.results_df is not None and not self.results_df.empty:
                        dr = None
                        if 'Abbreviation' in self.results_df.columns:
                            matches = self.results_df[self.results_df['Abbreviation'] == driver_id]
                            if not matches.empty:
                                dr = matches.iloc[0]
                        if dr is None and driver_id in self.results_df.index:
                            dr = self.results_df.loc[driver_id]
                        if dr is None and 'DriverNumber' in self.results_df.columns:
                            matches = self.results_df[self.results_df['DriverNumber'].astype(str) == str(driver_id)]
                            if not matches.empty:
                                dr = matches.iloc[0]

                        if dr is not None:
                            driver_name = str(dr.get('LastName', driver_name))
                            num_val = dr.get('DriverNumber', dr.get('number', 0))
                            number = 0 if pd.isna(num_val) else int(num_val)
                            team = str(dr.get('TeamName', "UNKNOWN"))
                            grid_val = dr.get('GridPosition', 0)
                            grid_position = 0 if pd.isna(grid_val) else int(grid_val)

                    speed_val = last_lap_record.get('SpeedST', last_lap_record.get('SpeedFL', last_lap_record.get('Speed', 0.0)))
                    speed_kmh = float(speed_val) if pd.notna(speed_val) else 0.0

                    throttle_pct = 100.0 if speed_kmh > 0 else 0.0

                    drivers_state[driver_id] = DriverRaceState(
                        driver_id=str(driver_id),
                        driver_name=driver_name,
                        number=number,
                        team=team,
                        position=int(position),
                        grid_position=grid_position,
                        lap_number=int(lap_number),
                        distance_m=0.0,
                        sector=0,
                        speed_kmh=speed_kmh,
                        gear=0,
                        throttle_pct=throttle_pct,
                        brake_pct=0.0,
                        drs_status=0,
                        tyre_compound=str(compound),
                        tyre_age_laps=int(tyre_life),
                        stint_number=0,
                        pit_status=str(status_val),
                        gap_to_leader_s=None,
                        interval_to_ahead_s=None,
                        last_lap_s=last_lap_time_ms / 1000.0,
                        best_lap_s=0.0,
                        x=0.0,
                        y=0.0,
                        z=0.0,
                        heading_deg=0.0
                    )

            # Calculate True Gaps and Intervals
            leader_driver = None
            for drv in drivers_state.values():
                if drv.position == 1:
                    leader_driver = drv.driver_id
                    break

            if leader_driver:
                leader_laps = past_laps[past_laps['Driver'] == leader_driver]
                leader_last_lap_num = drivers_state[leader_driver].lap_number
                leader_time_record = leader_laps[leader_laps['LapNumber'] == leader_last_lap_num]
                leader_time_s = None

                if not leader_time_record.empty and pd.notna(leader_time_record.iloc[-1].get('Time')):
                    lt = leader_time_record.iloc[-1]['Time']
                    if isinstance(lt, pd.Timedelta):
                        leader_time_s = lt.total_seconds()

                if leader_time_s is not None:
                    # Sort drivers by actual position
                    sorted_drivers = sorted(drivers_state.values(), key=lambda d: d.position if d.position > 0 else 999)

                    prev_gap = 0.0
                    for drv in sorted_drivers:
                        if drv.position == 1:
                            drv.gap_to_leader_s = 0.0
                            drv.interval_to_ahead_s = None
                            drv.laps_behind_leader = 0
                            drv.timing_status = "VALID"
                            continue

                        drv_laps = past_laps[past_laps['Driver'] == drv.driver_id]
                        if drv_laps.empty:
                            drv.gap_to_leader_s = None
                            drv.interval_to_ahead_s = None
                            drv.timing_status = "UNAVAILABLE"
                            continue

                        # Determine completed laps (where Time <= replay_td)
                        completed_drv_laps = drv_laps[drv_laps['Time'] <= replay_td] if 'Time' in drv_laps.columns else drv_laps
                        completed_leader_laps = leader_laps[leader_laps['Time'] <= replay_td] if 'Time' in leader_laps.columns else leader_laps

                        drv_comp_num = int(completed_drv_laps['LapNumber'].max()) if not completed_drv_laps.empty else 0
                        ldr_comp_num = int(completed_leader_laps['LapNumber'].max()) if not completed_leader_laps.empty else 0

                        # Determine latest lap time record for drv
                        drv_time_record = drv_laps[drv_laps['LapNumber'] == drv.lap_number]
                        drv_time_s = None
                        if not drv_time_record.empty and pd.notna(drv_time_record.iloc[-1].get('Time')):
                            dt = drv_time_record.iloc[-1]['Time']
                            if isinstance(dt, pd.Timedelta):
                                drv_time_s = dt.total_seconds()

                        # Common reference lap for gap calculation
                        ref_lap = min(drv.lap_number, leader_last_lap_num)
                        leader_same_lap = leader_laps[leader_laps['LapNumber'] == ref_lap]
                        drv_same_lap = drv_laps[drv_laps['LapNumber'] == ref_lap]

                        gap_at_lap = None
                        if not leader_same_lap.empty and not drv_same_lap.empty:
                            lt = leader_same_lap.iloc[-1].get('Time')
                            dt = drv_same_lap.iloc[-1].get('Time')
                            if pd.notna(lt) and pd.notna(dt) and isinstance(lt, pd.Timedelta) and isinstance(dt, pd.Timedelta):
                                gap_at_lap = round(max(0.0, dt.total_seconds() - lt.total_seconds()), 3)

                        # Genuine Formula 1 lapped invariant:
                        # The leader cannot lap a driver on lap N until the leader has completed lap N+1
                        # before the driver finishes lap N.
                        # At leader rollover (leader finishes lap N, starts N+1), any car on lap N
                        # has drv_comp_num >= ldr_comp_num - 1 and is on the lead lap.
                        genuinely_lapped = False
                        laps_behind = 0

                        if ldr_comp_num > drv_comp_num:
                            # Candidate for being lapped: check if leader completed drv_comp_num + 1 before drv completed drv_comp_num
                            leader_check_lap = leader_laps[leader_laps['LapNumber'] == drv_comp_num + 1]
                            drv_check_lap = drv_laps[drv_laps['LapNumber'] == drv_comp_num]

                            if not leader_check_lap.empty and not drv_check_lap.empty:
                                l_check_time = leader_check_lap.iloc[-1].get('Time')
                                d_check_time = drv_check_lap.iloc[-1].get('Time')
                                if pd.notna(l_check_time) and pd.notna(d_check_time):
                                    l_sec = l_check_time.total_seconds() if isinstance(l_check_time, pd.Timedelta) else float(l_check_time)
                                    d_sec = d_check_time.total_seconds() if isinstance(d_check_time, pd.Timedelta) else float(d_check_time)
                                    if l_sec < d_sec or (ldr_comp_num - drv_comp_num >= 2):
                                        genuinely_lapped = True
                                        laps_behind = max(1, ldr_comp_num - drv_comp_num)
                            elif ldr_comp_num - drv_comp_num >= 2:
                                genuinely_lapped = True
                                laps_behind = ldr_comp_num - drv_comp_num

                        if genuinely_lapped:
                            drv.laps_behind_leader = laps_behind
                            drv.timing_status = "LAPPED"
                            drv.gap_to_leader_s = gap_at_lap
                            drv.interval_to_ahead_s = round(gap_at_lap - prev_gap, 3) if (prev_gap is not None and gap_at_lap is not None and gap_at_lap >= prev_gap) else gap_at_lap
                            prev_gap = gap_at_lap or prev_gap
                        else:
                            drv.laps_behind_leader = 0
                            drv.timing_status = "VALID"
                            drv.gap_to_leader_s = gap_at_lap
                            drv.interval_to_ahead_s = round(gap_at_lap - prev_gap, 3) if (prev_gap is not None and gap_at_lap is not None and gap_at_lap >= prev_gap) else gap_at_lap
                            prev_gap = gap_at_lap or prev_gap

            total_laps = int(self.laps_df['LapNumber'].max()) if not self.laps_df.empty else 0

            return UnifiedRaceState(
                session_id=session_id,
                schema_version=SCHEMA_VERSION,
                mode="REPLAY",
                timestamp_s=timestamp_s,
                elapsed_time_s=timestamp_s,
                current_lap=current_max_lap,
                total_laps=total_laps,
                session_status="ONGOING",
                track_status="1",
                drivers=drivers_state,
                race_control_messages=[]
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"ReplayAdapter mapping error: {e}")
            raise RuntimeError(f"PROGRAMMING/CONTRACT ERROR in ReplayAdapter: {e}") from e


class OpenF1LiveProvider(BaseDataProvider):
    """
    Live Data Provider Adapter for OpenF1 API streams.
    """

    def fetch_current_race_state(self, session_id: str, timestamp_s: float) -> UnifiedRaceState:
        # OpenF1 implementation is missing, so we must return UNAVAILABLE.
        return UnifiedRaceState(
            session_id=session_id,
            schema_version=SCHEMA_VERSION,
            mode="LIVE",
            timestamp_s=timestamp_s,
            elapsed_time_s=timestamp_s,
            current_lap=0,
            total_laps=0,
            session_status="LIVE DATA UNAVAILABLE",
            track_status="UNKNOWN",
            drivers={},
            race_control_messages=[]
        )

class RealtimeRaceStateEngine:
    @staticmethod
    def get_unified_state(session_id: str = "S-2024-SPAIN", timestamp_s: float = 1200.0, mode: str = "REPLAY") -> Dict[str, Any]:
        """
        Retrieves the latest unified state mapping for decision architecture orchestration.
        Delegates to ProbabilisticService for actual state fetch.
        """
        try:
            from src.probabilistic_service import ProbabilisticService
        except ImportError:
            from probabilistic_service import ProbabilisticService
        state_obj = ProbabilisticService.get_unified_race_state(session_id, timestamp_s, mode)
        drivers = []
        for d in state_obj.drivers.values():
            drivers.append({
                "driver_id": d.driver_id,
                "team": d.team,
                "position": d.position,
                "gap_to_leader_s": d.gap_to_leader_s if d.gap_to_leader_s is not None else 0.0,
                "interval_to_ahead_s": d.interval_to_ahead_s if d.interval_to_ahead_s is not None else 0.0,
                "current_lap": d.lap_number,
                "last_lap_time_s": d.last_lap_s,
                "best_lap_time_s": d.best_lap_s,
                "tyre_age_laps": d.tyre_age_laps,
                "tyre_compound": d.tyre_compound,
                "stint_number": d.stint_number
            })
        parts = session_id.split('-')
        year = 2024
        event_name = "Grand Prix"
        session_type = "Race"
        if len(parts) >= 3 and parts[1].isdigit():
            year = int(parts[1])
            event_name = parts[2].title() + " Grand Prix"

        return {
            "session_info": {"year": year, "round": 1, "event_name": event_name, "session": session_type},
            "timing_tower": {
                "current_lap": state_obj.current_lap,
                "total_laps": state_obj.total_laps,
                "drivers": drivers
            }
        }
