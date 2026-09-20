import os
import json
import numpy as np
import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.env_checker import check_env

from src import config
from src.rl_strategy_agent import F1StrategyEnv, ACTION_NAMES

def main():
    print("--- TESTING ENVIRONMENT ---")
    env = F1StrategyEnv()
    check_env(env, warn=True)
    print("Environment check passed!")
    
    print("--- TRAINING PPO AGENT ---")
    # Using a small policy for a fast smoke test, as requested
    model = PPO("MlpPolicy", env, verbose=1, n_steps=128, batch_size=32, n_epochs=3)
    model.learn(total_timesteps=1000)
    
    print("--- EVALUATING RL POLICY ---")
    mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=5)
    print(f"Mean Reward: {mean_reward} +/- {std_reward}")
    
    print("--- SAVING MODEL ARTIFACT ---")
    model_dir = os.path.join(config.BASE_DIR, "models", "rl_strategy")
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, "ppo_strategy_v1")
    model.save(model_path)
    
    metadata = {
        "model_id": "ppo_strategy_v1",
        "algorithm": "PPO",
        "action_space": ACTION_NAMES,
        "metrics": {
            "mean_reward": float(np.mean(mean_reward)),  # type: ignore
            "std_reward": float(np.mean(std_reward))  # type: ignore
        },
        "training_timesteps": 1000
    }
    
    with open(os.path.join(model_dir, "metadata_v1.json"), "w", encoding='utf-8') as f:
        json.dump(metadata, f, indent=4)
        
    print(f"RL Model and metadata saved to {model_dir}")
    
    # Try doing a manual rollout
    print("--- RUNNING MANNUAL EPISODE ---")
    obs, info = env.reset()
    done = False
    total_r = 0
    while not done:
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(int(action))
        total_r += reward
        done = terminated or truncated
    print(f"Manual rollout finished. Reward: {total_r}")

if __name__ == "__main__":
    main()


