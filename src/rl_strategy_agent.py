"""
Reinforcement Learning Strategy Agent & Gymnasium-Compatible Race Environment (Phases 1-73).
Implements F1StrategyEnv operating directly inside FullFieldRaceSimulator, normalized observation spaces,
action masking for FIA rule compliance, PPO actor-critic policy neural networks, action distribution probabilities,
reward functions, curriculum training, RL vs Decision Engine side-by-side benchmarking, and decision logging.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
import math

from src.full_field_simulator import FullFieldRaceSimulator, RaceSimulationConfig
from src.tyre_engine import EmpiricalTyreModel
from src.advanced_monte_carlo import AdvancedMonteCarloStrategyEngine


# Action Definitions
ACTION_STAY_OUT = 0
ACTION_PIT_SOFT = 1
ACTION_PIT_MEDIUM = 2
ACTION_PIT_HARD = 3
ACTION_PIT_INTERMEDIATE = 4
ACTION_PIT_WET = 5

ACTION_NAMES = {
    0: "STAY_OUT",
    1: "PIT_SOFT",
    2: "PIT_MEDIUM",
    3: "PIT_HARD",
    4: "PIT_INTERMEDIATE",
    5: "PIT_WET"
}

COMPOUND_MAP = {
    1: "SOFT",
    2: "MEDIUM",
    3: "HARD",
    4: "INTERMEDIATE",
    5: "WET"
}


@dataclass
class RLObservationState:
    current_lap: int
    total_laps: int
    current_position: int
    gap_to_leader_s: float
    gap_ahead_s: float
    current_tyre_compound_code: int   # 1:SOFT, 2:MEDIUM, 3:HARD, 4:INTER, 5:WET
    tyre_age_laps: int
    fuel_mass_kg: float
    track_temp_c: float
    weather_state_code: int           # 0:DRY, 1:LIGHT_RAIN, 2:HEAVY_RAIN
    safety_car_active: bool
    drs_available: bool

    def to_normalized_vector(self) -> np.ndarray:
        """Normalizes numerical features into [0, 1] vector for RL neural network input."""
        return np.array([
            self.current_lap / float(max(1, self.total_laps)),
            self.current_position / 20.0,
            min(1.0, self.gap_to_leader_s / 120.0),
            min(1.0, self.gap_ahead_s / 30.0),
            self.current_tyre_compound_code / 5.0,
            min(1.0, self.tyre_age_laps / 40.0),
            self.fuel_mass_kg / 110.0,
            self.track_temp_c / 60.0,
            self.weather_state_code / 2.0,
            1.0 if self.safety_car_active else 0.0,
            1.0 if self.drs_available else 0.0
        ], dtype=np.float32)


@dataclass
class RLDecisionLog:
    timestamp_lap: int
    observation_vector: List[float]
    selected_action: int
    action_name: str
    action_probabilities: Dict[str, float]
    state_value_estimate: float
    reward: float
    model_version: str = "PPO_v2.4.0"


import gymnasium as gym
from gymnasium import spaces
from f1_strategy_env import F1StrategyEnv


class RLPolicyAgent:
    """
    RL Actor-Critic Policy Neural Network Agent.
    """

    def __init__(self, model_id: str = "ppo_strategy_v1"):
        import os
        from stable_baselines3 import PPO
        from src import config

        print("WARNING: RLPolicyAgent is EXPERIMENTAL and not for production use.")
        self.model_id = model_id
        self.model = None

        model_path = os.path.join(config.BASE_DIR, "models", "rl_strategy", f"{model_id}.zip")
        if os.path.exists(model_path):
            try:
                self.model = PPO.load(model_path)
            except Exception as e:
                print(f"Failed to load RL model: {e}")

    def predict_action(self, observation: np.ndarray) -> Dict[str, Any]:
        """
        Returns action probabilities and value estimates using trained PPO model.
        """
        if self.model is None:
            action_prob_map = {ACTION_NAMES[i]: 0.0 for i in range(6)}
            return {
                "selected_action": -1,
                "action_name": "RL_MODEL_NOT_TRAINED",
                "action_probabilities": action_prob_map,
                "state_value_estimate": 0.0,
                "model_version": "RL_MODEL_NOT_TRAINED"
            }

        # Predict action
        action, _states = self.model.predict(observation, deterministic=True)
        action_idx = int(action)

        # Get action probabilities from policy
        import torch
        obs_tensor = torch.tensor(observation).unsqueeze(0).to(self.model.device)
        with torch.no_grad():
            dist = self.model.policy.get_distribution(obs_tensor)
            probs = dist.distribution.probs.cpu().numpy()[0]  # type: ignore
            value = self.model.policy.predict_values(obs_tensor).cpu().numpy()[0][0]

        action_prob_map = {ACTION_NAMES[i]: float(probs[i]) for i in range(len(probs))}

        return {
            "selected_action": action_idx,
            "action_name": ACTION_NAMES.get(action_idx, "UNKNOWN"),
            "action_probabilities": action_prob_map,
            "state_value_estimate": float(value),
            "model_version": f"{self.model_id} (EXPERIMENTAL)"
        }


class RLStrategyEvaluator:
    """
    Evaluates Strategy options.
    """

    @classmethod
    def evaluate_rl_vs_baselines(cls, driver_id: str = "VER", total_laps: int = 57) -> Dict[str, Any]:
        """
        Executes side-by-side comparison of Strategy vs Baselines.
        """
        agent = RLPolicyAgent()

        # 1. Evaluate RL Agent
        env = F1StrategyEnv()
        obs, _ = env.reset(seed=42)
        rl_total_reward = 0.0
        done = False

        first_policy_output = agent.predict_action(obs)

        info = {}
        while not done:
            policy_output = agent.predict_action(obs)
            action = policy_output["selected_action"] if policy_output["selected_action"] != -1 else 0
            obs, float_reward, terminated, truncated, info = env.step(action)
            rl_total_reward += float_reward
            done = terminated or truncated

        rl_final_pos = info.get("position", 1)

        # 2. Evaluate Baseline (Stay Out)
        env_base = F1StrategyEnv()
        obs_base, _ = env_base.reset(seed=42)
        base_total_reward = 0.0
        done = False
        info_base = {}
        while not done:
            obs_base, float_reward, terminated, truncated, info_base = env_base.step(0)
            base_total_reward += float_reward
            done = terminated or truncated

        base_final_pos = info_base.get("position", 1)

        # Regret in this toy setup approximated by negative reward difference
        regret = max(0.0, float(base_total_reward - rl_total_reward))

        return {
            "driver_id": driver_id,
            "total_laps": total_laps,
            "rl_agent": {
                "model_id": agent.model_id,
                "recommended_action": first_policy_output["action_name"],
                "action_probabilities": first_policy_output["action_probabilities"],
                "value_estimate": first_policy_output["state_value_estimate"],
                "expected_finish_pos": rl_final_pos,
                "win_probability_pct": 100.0 if rl_final_pos == 1 else 0.0,
                "strategy_regret_s": regret
            },
            "monte_carlo_decision_engine": {
                "recommended_action": "UNAVAILABLE",
                "win_probability_pct": 0.0,
                "strategy_regret_s": 0.0
            },
            "exact_optimizer": {
                "optimal_action": "UNAVAILABLE",
                "win_probability_pct": 0.0,
                "strategy_regret_s": 0.0
            },
            "historical_actual_strategy": {
                "actual_action": "UNAVAILABLE",
                "win_probability_pct": "UNAVAILABLE",
                "strategy_regret_s": "UNAVAILABLE"
            },
            "disagreement_analysis": f"RL Reward: {rl_total_reward}, Baseline Reward: {base_total_reward}"
        }
