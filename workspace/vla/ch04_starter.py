"""
Chapter 04 — Reinforcement Learning for Robots
workspace/vla/ch04_starter.py

Projects to complete (see courses/vla/ch04_rl/README.md):
  1. Define a reward function for a reach task
  2. Train SAC on your ArmEnv using Stable-Baselines3
  3. Evaluate and visualise the learned policy
"""

import numpy as np


# ── TODO 1: Reward function ───────────────────────────────────────────────
def compute_reward(ee_pos: np.ndarray, target_pos: np.ndarray,
                   action: np.ndarray, prev_dist: float) -> tuple[float, dict]:
    """
    Return (reward, info_dict).
    Suggested shaping: dense distance reward + action penalty + success bonus.
    """
    raise NotImplementedError


# ── TODO 2: Train SAC ────────────────────────────────────────────────────
def train_sac(env_id: str = 'ArmReach-v0', total_timesteps: int = 500_000):
    """Train SAC and save the model to workspace/vla/sac_arm/."""
    from stable_baselines3 import SAC
    from stable_baselines3.common.env_util import make_vec_env
    # TODO: create env, instantiate SAC, call model.learn(), save
    raise NotImplementedError


# ── TODO 3: Evaluate policy ──────────────────────────────────────────────
def evaluate(model_path: str, env_id: str, n_episodes: int = 20):
    """Load saved model and report mean episode reward."""
    raise NotImplementedError


if __name__ == '__main__':
    train_sac()
