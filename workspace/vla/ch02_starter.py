"""
Chapter 02 — Simulation with MuJoCo
workspace/vla/ch02_starter.py

Projects to complete (see courses/vla/ch02_mujoco/README.md):
  1. Load the SO-101 MJCF model and run a passive simulation
  2. Build a Gymnasium environment wrapping a MuJoCo scene
  3. Implement a PD joint controller and step it for 1000 steps
"""

import numpy as np
import mujoco
import gymnasium as gym
from gymnasium import spaces


# ── TODO 1: Load model and run passive sim ───────────────────────────────
MODEL_PATH = 'path/to/so101.xml'  # update to your model path

def run_passive(model_path: str, duration: float = 5.0):
    """Load model, disable actuators, simulate for `duration` seconds."""
    raise NotImplementedError


# ── TODO 2: Gymnasium environment ────────────────────────────────────────
class ArmEnv(gym.Env):
    metadata = {'render_modes': ['human', 'rgb_array']}

    def __init__(self, model_path: str, render_mode=None):
        super().__init__()
        # TODO: load mujoco model
        # TODO: define observation_space and action_space
        raise NotImplementedError

    def reset(self, *, seed=None, options=None):
        # TODO: reset sim state, return (obs, info)
        raise NotImplementedError

    def step(self, action):
        # TODO: apply action, step sim, compute reward
        # return (obs, reward, terminated, truncated, info)
        raise NotImplementedError

    def render(self):
        raise NotImplementedError

    def close(self):
        pass


# ── TODO 3: PD controller ────────────────────────────────────────────────
def pd_control(q: np.ndarray, dq: np.ndarray,
               q_target: np.ndarray, kp: float = 100.0, kd: float = 10.0) -> np.ndarray:
    """Return torque commands from a PD controller."""
    raise NotImplementedError


if __name__ == '__main__':
    run_passive(MODEL_PATH, duration=2.0)
