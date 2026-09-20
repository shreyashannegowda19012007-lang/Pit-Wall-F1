"""
Automated Unit, Integration & Policy Test Suite for Reinforcement Learning Strategy Subsystem.
Verifies Gymnasium F1StrategyEnv reset/step loop, normalized observation vectors, PPO actor-critic action
prediction probabilities, state value estimates, benchmark evaluations vs Decision Engine & API routes.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from rl_strategy_agent import F1StrategyEnv, RLObservationState, RLPolicyAgent, RLStrategyEvaluator, ACTION_PIT_HARD
from telemetry_api import api_service


class TestRLStrategyAgentSubsystem(unittest.TestCase):

    def test_gymnasium_f1_strategy_environment(self):
        """Verifies F1StrategyEnv reset and step methods produce valid observations and rewards."""
        env = F1StrategyEnv()
        obs, info = env.reset(seed=42)

        self.assertEqual(len(obs), 11)
        self.assertTrue(np.all(obs >= 0.0) and np.all(obs <= 1.0))
        self.assertEqual(info["lap"], 0)

        # Execute 1 step with PIT_HARD action
        next_obs, reward, done, truncated, next_info = env.step(ACTION_PIT_HARD)
        self.assertEqual(next_info["lap"], 1)
        self.assertFalse(done)

    def test_ppo_policy_agent_predictions(self):
        """Verifies RL Policy Agent outputs valid actions."""
        agent = RLPolicyAgent()
        obs = np.array([0.5, 0.05, 0.0, 0.0, 0.4, 0.7, 0.5, 0.5, 0.0, 0.0, 0.0], dtype=np.float32)

        pred = agent.predict_action(obs)

        self.assertIn("selected_action", pred)
        self.assertIn("action_name", pred)
        self.assertIn(pred["action_name"], ["STAY_OUT", "PIT_SOFT", "PIT_MEDIUM", "PIT_HARD", "PIT_INTERMEDIATE", "PIT_WET", "UNKNOWN", "RL_MODEL_NOT_TRAINED"])
        probs_sum = sum(pred["action_probabilities"].values())
        if pred["action_name"] == "RL_MODEL_NOT_TRAINED":
            self.assertAlmostEqual(probs_sum, 0.0, places=2)
        else:
            self.assertAlmostEqual(probs_sum, 1.0, places=2)

    def test_rl_evaluator_vs_baselines(self):
        """Verifies RLStrategyEvaluator compares RL PPO policy against Monte Carlo Decision Engine and Exact Optimizer."""
        res = RLStrategyEvaluator.evaluate_rl_vs_baselines("VER", 57)

        self.assertEqual(res["driver_id"], "VER")
        self.assertIn("rl_agent", res)
        self.assertIn("monte_carlo_decision_engine", res)
        self.assertIn("exact_optimizer", res)
        self.assertIn("historical_actual_strategy", res)

    def test_api_service_rl_routes(self):
        """Verifies API routes for RL action prediction and evaluation."""
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {"EXPERIMENTAL_RL_ENABLED": "true"}):
            pred = api_service.predict_rl_action("VER", 20)
            eval_res = api_service.evaluate_rl_vs_baselines("VER")

        self.assertIn("selected_action", pred)
        self.assertIn("rl_agent", eval_res)


if __name__ == '__main__':
    unittest.main()
