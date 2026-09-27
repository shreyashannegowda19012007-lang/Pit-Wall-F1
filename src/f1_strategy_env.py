import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import math
from src.full_field_simulator import RaceSimulationConfig, DriverSimState, FullFieldRaceSimulator
from src.tyre_engine import EmpiricalTyreModel

class F1StrategyEnv(gym.Env):
    """
    Gymnasium-compatible F1 Strategy Environment wrapper around Full-Field mechanics.
    """

    ACTION_STAY_OUT = 0
    ACTION_PIT_SOFT = 1
    ACTION_PIT_MEDIUM = 2
    ACTION_PIT_HARD = 3

    COMPOUND_MAP = {
        1: "SOFT",
        2: "MEDIUM",
        3: "HARD"
    }

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__()
        self.config_dict = config or {
            "total_laps": 57,
            "seed": 42,
            "driver": "VER"
        }
        self.sim_config = RaceSimulationConfig(
            total_laps=self.config_dict.get("total_laps", 57),
            simulation_seed=self.config_dict.get("seed", 42)
        )
        self.target_driver = self.config_dict.get("driver", "VER")
        self.action_space = spaces.Discrete(4)

        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(11,), dtype=np.float32)

        self.current_lap = 0
        self.rng = None
        self.driver_states = {}
        self.planned_strategies = {}
        self.ml_available = True

    def reset(self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        actual_seed = seed if seed is not None else self.sim_config.simulation_seed
        self.rng = np.random.RandomState(actual_seed)

        self.current_lap = 0

        # Initialize Full Field Grid
        self.driver_states: Dict[str, DriverSimState] = {}
        for pos, (drv_id, team) in enumerate(FullFieldRaceSimulator.DEFAULT_DRIVERS, start=1):
            self.driver_states[drv_id] = DriverSimState(
                driver_id=drv_id,
                team=team,
                grid_position=pos,
                current_position=pos,
                lap_number=0,
                total_race_time_s=0.0,
                last_lap_time_s=0.0,
                best_lap_time_s=999.0,
                tyre_compound="MEDIUM",
                tyre_age_laps=1,
                stint_number=1,
                fuel_mass_kg=self.sim_config.fuel_mass_initial_kg,
                pit_count=0,
                is_pitting=False,
                status="RACING",
                gap_to_leader_s=(pos - 1) * 0.5,
                interval_to_ahead_s=0.5 if pos > 1 else 0.0
            )

        self.planned_strategies = {drv[0]: [(22, "HARD")] for drv in FullFieldRaceSimulator.DEFAULT_DRIVERS}

        obs = self._get_obs()
        info = self._get_info()
        return obs, info

    def _get_obs(self) -> np.ndarray:
        target_state = self.driver_states[self.target_driver]

        comp_norm = 0.5
        if target_state.tyre_compound == "SOFT": comp_norm = 0.0
        elif target_state.tyre_compound == "HARD": comp_norm = 1.0

        ml_deg = 0.075 # Default fallback
        if self.ml_available:
            try:
                from src.production_ml_engine import ProductionMLEngine
                pred = ProductionMLEngine.predict_tyre_degradation(target_state.tyre_compound, target_state.tyre_age_laps, ml_deg)
                if "MODEL_READY" in pred["status"]:
                    ml_deg = pred["predicted_deg"]
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"ML engine error in strategy env: {e}")

        obs = [
            self.current_lap / float(self.sim_config.total_laps),
            target_state.current_position / 20.0,
            min(1.0, target_state.gap_to_leader_s / 100.0),
            min(1.0, target_state.interval_to_ahead_s / 100.0),
            comp_norm,
            min(1.0, target_state.tyre_age_laps / 50.0),
            min(1.0, target_state.stint_number / 5.0),
            target_state.fuel_mass_kg / 110.0,
            32.0 / 60.0,
            0.0, # SC
            min(1.0, ml_deg / 0.5)
        ]

        obs_arr = np.array(obs, dtype=np.float32)
        obs_arr = np.nan_to_num(obs_arr, nan=0.0, posinf=1.0, neginf=0.0)
        obs_arr = np.clip(obs_arr, 0.0, 1.0)
        return obs_arr

    def _get_info(self) -> Dict[str, Any]:
        target_state = self.driver_states[self.target_driver]
        return {
            "lap": self.current_lap,
            "position": target_state.current_position,
            "tyre": target_state.tyre_compound,
            "tyre_age": target_state.tyre_age_laps,
            "race_time": target_state.total_race_time_s,
            "pit_stops": target_state.pit_count,
            "ml_available": self.ml_available,
            "rival_model": "UNAVAILABLE",
            "safety_car_model": "UNAVAILABLE"
        }

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        if self.current_lap >= self.sim_config.total_laps:
            return self._get_obs(), 0.0, True, False, self._get_info()

        self.current_lap += 1
        is_safety_car = (self.rng.rand() < self.sim_config.safety_car_probability_per_lap)

        # Override Target Driver strategy based on action
        if action in self.COMPOUND_MAP:
            # Add pit stop for THIS lap
            self.planned_strategies[self.target_driver] = [(self.current_lap, self.COMPOUND_MAP[action])]
        else:
            self.planned_strategies[self.target_driver] = [] # Stay out

        prev_position = self.driver_states[self.target_driver].current_position

        # 1. Advance all drivers
        for drv_id, state in self.driver_states.items():
            if state.status == "RETIRED": continue

            state.lap_number = self.current_lap
            state.tyre_age_laps += 1

            fuel_penalty = (state.fuel_mass_kg / 10.0) * self.sim_config.fuel_effect_s_per_10kg
            deg_rate = EmpiricalTyreModel.COMPOUND_BASE_DEG.get(state.tyre_compound, 0.075)
            tyre_penalty = state.tyre_age_laps * deg_rate
            lap_noise = self.rng.normal(0.0, 0.08)

            sc_mult = 1.35 if is_safety_car else 1.00
            lap_time = (self.sim_config.base_lap_time_s + fuel_penalty + tyre_penalty + lap_noise) * sc_mult

            pits = self.planned_strategies.get(drv_id, [])
            if any(pit_lap == self.current_lap for pit_lap, _ in pits):
                next_compound = next(comp for p_lap, comp in pits if p_lap == self.current_lap)
                pit_duration = self.sim_config.pit_lane_time_loss_s + max(2.0, self.rng.normal(self.sim_config.pit_stop_mean_duration_s, 0.3))
                if is_safety_car: pit_duration *= 0.6
                lap_time += pit_duration
                state.pit_count += 1
                state.tyre_compound = next_compound
                state.tyre_age_laps = 1
                state.stint_number += 1

            state.fuel_mass_kg = max(0.0, state.fuel_mass_kg - self.sim_config.fuel_burn_per_lap_kg)
            state.last_lap_time_s = round(lap_time, 3)
            state.best_lap_time_s = min(state.best_lap_time_s, state.last_lap_time_s)
            state.total_race_time_s += state.last_lap_time_s

        # 2. Re-sort Race Order
        sorted_drivers = sorted(
            [s for s in self.driver_states.values() if s.status != "RETIRED"],
            key=lambda x: x.total_race_time_s
        )

        leader_time = sorted_drivers[0].total_race_time_s
        for pos, drv in enumerate(sorted_drivers, start=1):
            drv.current_position = pos
            drv.gap_to_leader_s = round(drv.total_race_time_s - leader_time, 3)
            drv.interval_to_ahead_s = round(drv.total_race_time_s - sorted_drivers[pos - 2].total_race_time_s, 3) if pos > 1 else 0.0

        target_state = self.driver_states[self.target_driver]
        terminated = (self.current_lap >= self.sim_config.total_laps)

        # Reward
        lap_time_penalty = -(target_state.last_lap_time_s - self.sim_config.base_lap_time_s) / 10.0
        pos_gain = prev_position - target_state.current_position
        reward = lap_time_penalty + (pos_gain * 2.0)

        if terminated:
            reward += (21 - target_state.current_position) * 10.0

        info = self._get_info()
        info["action"] = action
        info["reward_components"] = {"lap_time_penalty": lap_time_penalty, "pos_gain": pos_gain}

        return self._get_obs(), float(reward), terminated, False, info
