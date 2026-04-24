"""
Chapter 03 — Kinematics & Motion Planning
workspace/vla/ch03_starter.py

Projects to complete (see courses/vla/ch03_kinematics/README.md):
  1. Implement analytical IK for a 2-DOF planar arm
  2. Use Pink (differential IK) to track a Cartesian target
  3. Plan a straight-line Cartesian trajectory and execute it
"""

import numpy as np


# ── TODO 1: Analytical IK (2-DOF planar) ─────────────────────────────────
L1, L2 = 0.3, 0.25  # link lengths

def ik_2dof(px: float, py: float, elbow_up: bool = True) -> tuple[float, float]:
    """Return (theta1, theta2) in radians for end-effector at (px, py)."""
    raise NotImplementedError


# ── TODO 2: Differential IK with Pink ────────────────────────────────────
def build_pink_robot(urdf_path: str):
    """Load robot with Pink and return (robot, configuration)."""
    # import pink
    raise NotImplementedError


def track_target(robot, config, target_pose, n_steps: int = 100, dt: float = 0.01):
    """Run a differential IK loop to track target_pose (pinocchio SE3)."""
    raise NotImplementedError


# ── TODO 3: Cartesian trajectory ─────────────────────────────────────────
def linear_cartesian_traj(p_start: np.ndarray, p_end: np.ndarray,
                           n_points: int = 50) -> np.ndarray:
    """Return (n_points, 3) array of waypoints along a straight line."""
    raise NotImplementedError


if __name__ == '__main__':
    q1, q2 = ik_2dof(0.4, 0.1)
    print(f'IK solution: theta1={np.degrees(q1):.1f}°, theta2={np.degrees(q2):.1f}°')
