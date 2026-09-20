"""
Scenario Analysis Engine for F1 Monte Carlo Strategy Simulator.
Provides pre-built race scenarios (High Tyre Deg, Early Safety Car, Heavy Rain, etc.)
that dynamically modify physical race states.
"""

from typing import Dict, List, Optional, Any, Tuple
from race_state import CompleteRaceState, WeatherState, SafetyCarState, TrackState


class ScenarioPreset:
    NORMAL = "NORMAL_WEATHER"
    HIGH_DEG = "HIGH_TYRE_DEG"
    LOW_DEG = "LOW_TYRE_DEG"
    EARLY_SC = "EARLY_SAFETY_CAR"
    LATE_SC = "LATE_SAFETY_CAR"
    HEAVY_RAIN = "HEAVY_RAIN"


class ScenarioEngine:
    """
    Applies preset scenario modifications to a CompleteRaceState object.
    """

    @classmethod
    def apply_scenario(cls, race_state: CompleteRaceState, scenario_preset: str) -> CompleteRaceState:
        """Modifies race_state according to selected scenario preset."""
        if scenario_preset == ScenarioPreset.HIGH_DEG:
            race_state.weather.track_temp_c = 48.0  # Hot track accelerates deg
        elif scenario_preset == ScenarioPreset.LOW_DEG:
            race_state.weather.track_temp_c = 22.0  # Cool track reduces deg
        elif scenario_preset == ScenarioPreset.EARLY_SC:
            race_state.safety_car.sc_probability_per_lap = 0.25
            race_state.safety_car.condition = "SC"
        elif scenario_preset == ScenarioPreset.LATE_SC:
            race_state.safety_car.sc_probability_per_lap = 0.35
        elif scenario_preset == ScenarioPreset.HEAVY_RAIN:
            race_state.weather.condition = "HEAVY_RAIN"
            race_state.weather.rainfall = True
            race_state.weather.track_wetness_pct = 90.0

        return race_state

