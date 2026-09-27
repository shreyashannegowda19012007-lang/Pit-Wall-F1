"""
Formal Race State & State Representation for Monte Carlo Race Strategy Engine.
Sufficient to resume or run stochastic race simulations from any valid lap.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple


@dataclass
class TyreState:
    compound: str                 # "SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"
    age_laps: int
    remaining_grip_pct: float     # 0.0 to 100.0 %
    thermal_deg_rate: float       # sec/lap
    is_warmed_up: bool = True
    warmup_laps_remaining: int = 0

    @property
    def tyre_degradation_rate(self) -> float:
        return self.thermal_deg_rate

    @tyre_degradation_rate.setter
    def tyre_degradation_rate(self, value: float):
        self.thermal_deg_rate = value


@dataclass
class FuelState:
    fuel_remaining_kg: float      # e.g., 110.0 kg starting
    fuel_burn_rate_kg_per_lap: float = 1.9
    fuel_time_penalty_per_kg: float = 0.03  # sec/lap per kg


@dataclass
class WeatherState:
    condition: str = "DRY"        # "DRY", "LIGHT_RAIN", "HEAVY_RAIN"
    track_temp_c: float = 30.0
    air_temp_c: float = 25.0
    rainfall: bool = False
    track_wetness_pct: float = 0.0


@dataclass
class TrackState:
    track_name: str = "Circuit"
    total_laps: int = 57
    pit_lane_loss_seconds: float = 22.5
    track_evolution_factor: float = 0.5   # 0.0 (Low) to 1.0 (High)
    overtaking_difficulty: str = "MEDIUM" # "EASY", "MEDIUM", "HARD", "CRITICAL"


@dataclass
class SafetyCarState:
    condition: str = "GREEN"      # "GREEN", "VSC", "SC", "RED_FLAG"
    sc_probability_per_lap: float = 0.02
    vsc_probability_per_lap: float = 0.04
    vsc_pit_loss_seconds: float = 14.0
    sc_pit_loss_seconds: float = 10.0


@dataclass
class DriverState:
    driver_id: str
    position: int
    current_gap_to_leader_s: float
    base_pace_s: float
    tyre_state: TyreState
    fuel_state: FuelState
    car_performance_delta_s: float = 0.0

    @property
    def tyre_degradation_rate(self) -> float:
        return self.tyre_state.thermal_deg_rate if self.tyre_state else 0.07

    @tyre_degradation_rate.setter
    def tyre_degradation_rate(self, value: float):
        if self.tyre_state:
            self.tyre_state.thermal_deg_rate = value


@dataclass
class CompleteRaceState:
    """
    Comprehensive snapshot of active race state.
    """
    current_lap: int
    total_laps: int
    drivers: Dict[str, DriverState]
    weather: WeatherState
    track: TrackState
    safety_car: SafetyCarState

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_lap": self.current_lap,
            "total_laps": self.total_laps,
            "driver_count": len(self.drivers),
            "weather": self.weather.condition,
            "track_temp": self.weather.track_temp_c,
            "safety_car": self.safety_car.condition
        }
