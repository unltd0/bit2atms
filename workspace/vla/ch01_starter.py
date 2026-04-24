"""
Chapter 01 — Transforms & Forward Kinematics
workspace/vla/ch01_starter.py

Projects to complete (see courses/vla/ch01_transforms/README.md):
  1. Build a 3-D transform library (SO3, SE3, compose, invert)
  2. Implement forward kinematics for a 3-DOF planar arm
  3. Visualise the kinematic chain in MuJoCo or Matplotlib
"""

import numpy as np

# ── TODO 1: SO(3) rotation matrix ────────────────────────────────────────
def rot_x(theta: float) -> np.ndarray:
    """Return 3x3 rotation matrix about X axis."""
    raise NotImplementedError


def rot_y(theta: float) -> np.ndarray:
    raise NotImplementedError


def rot_z(theta: float) -> np.ndarray:
    raise NotImplementedError


# ── TODO 2: SE(3) homogeneous transform ──────────────────────────────────
def make_transform(R: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Pack rotation R (3x3) and translation t (3,) into a 4x4 matrix."""
    raise NotImplementedError


def invert_transform(T: np.ndarray) -> np.ndarray:
    raise NotImplementedError


# ── TODO 3: Forward kinematics ───────────────────────────────────────────
LINK_LENGTHS = [0.3, 0.25, 0.2]  # metres

def forward_kinematics(joint_angles: list[float]) -> np.ndarray:
    """Return end-effector SE(3) transform given joint angles (radians)."""
    raise NotImplementedError


if __name__ == '__main__':
    angles = [np.pi / 4, -np.pi / 6, np.pi / 3]
    T = forward_kinematics(angles)
    print('End-effector transform:\n', T)
