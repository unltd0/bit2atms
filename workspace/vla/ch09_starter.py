"""
Chapter 09 — Physical Hardware
workspace/vla/ch09_starter.py

Projects to complete (see courses/vla/ch09_hardware/README.md):
  1. Calibrate your SO-101 arm and verify joint limits
  2. Collect a demonstration dataset on real hardware
  3. Deploy a trained policy to the physical robot
"""

# ── TODO 1: Calibration ──────────────────────────────────────────────────
# Run LeRobot's calibration script first:
#   python -m lerobot.scripts.control_robot calibrate \
#       --robot-path lerobot/configs/robot/so101.yaml
#
# Then verify limits programmatically:

def verify_joint_limits(robot_config: str):
    """Command each joint to its min/max and check encoder readings."""
    raise NotImplementedError


# ── TODO 2: Real-hardware data collection ────────────────────────────────
# Teleoperate and record:
#   python -m lerobot.scripts.record \
#       --robot-path lerobot/configs/robot/so101.yaml \
#       --repo-id YOUR_HF_USERNAME/so101_real \
#       --num-episodes 100 \
#       --fps 30

def collect_real_demos(robot_config: str, repo_id: str, n_episodes: int = 100):
    raise NotImplementedError


# ── TODO 3: Deploy policy ────────────────────────────────────────────────
# Evaluate on real robot:
#   python -m lerobot.scripts.control_robot record \
#       --robot-path lerobot/configs/robot/so101.yaml \
#       --policy-path workspace/vla/act_ckpt \
#       --num-episodes 10

def deploy_policy(robot_config: str, policy_path: str, n_episodes: int = 10):
    raise NotImplementedError


if __name__ == '__main__':
    print('Hardware projects require a physical SO-101 arm.')
    print('See courses/vla/ch09_hardware/README.md for setup instructions.')
