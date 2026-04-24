"""
Chapter 07 — Sim-to-Real Transfer
workspace/vla/ch07_starter.py

Projects to complete (see courses/vla/ch07_sim_to_real/README.md):
  1. Add domain randomisation to your MuJoCo environment
  2. Evaluate policy robustness across randomised parameters
  3. Profile the sim-to-real gap on a physical metric
"""

import numpy as np


# ── TODO 1: Domain randomisation ─────────────────────────────────────────
RANDOMISATION_RANGES = {
    'friction':    (0.5, 2.0),    # multiplier on nominal friction
    'mass':        (0.8, 1.2),    # multiplier on link masses
    'joint_noise': (0.0, 0.02),   # std of additive Gaussian noise (rad)
    'camera_pos':  (0.0, 0.01),   # std of camera position jitter (m)
}

def randomise_env(model, rng: np.random.Generator):
    """Apply randomised physics parameters to a MuJoCo model in-place."""
    raise NotImplementedError


# ── TODO 2: Robustness evaluation ────────────────────────────────────────
def evaluate_robustness(policy, env_factory, n_envs: int = 20, n_episodes: int = 10):
    """
    Create n_envs environments with different randomisation seeds,
    run n_episodes in each, return mean ± std success rate.
    """
    raise NotImplementedError


# ── TODO 3: Sim-to-real gap metric ──────────────────────────────────────
def compute_gap(sim_trajectory: np.ndarray, real_trajectory: np.ndarray) -> dict:
    """
    Compare joint angle trajectories from sim and real rollouts.
    Return dict with 'rmse', 'max_error', 'correlation'.
    """
    raise NotImplementedError


if __name__ == '__main__':
    rng = np.random.default_rng(42)
    print('Implement randomise_env and run evaluate_robustness.')
