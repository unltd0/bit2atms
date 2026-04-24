"""
Chapter 05 — Imitation Learning
workspace/vla/ch05_starter.py

Projects to complete (see courses/vla/ch05_imitation/README.md):
  1. Collect teleoperation demonstrations and save as LeRobot dataset
  2. Train ACT on your dataset
  3. Evaluate the policy in simulation
"""

# ── TODO 1: Record demonstrations ────────────────────────────────────────
# Use LeRobot's record script:
#   python -m lerobot.scripts.record \
#       --robot-path lerobot/configs/robot/so101.yaml \
#       --repo-id YOUR_HF_USERNAME/so101_reach \
#       --num-episodes 50
#
# Or implement a custom recorder below:

def record_demos(robot_config: str, output_repo: str, n_episodes: int = 50):
    """Collect and upload teleoperation demos via LeRobot."""
    raise NotImplementedError


# ── TODO 2: Train ACT ────────────────────────────────────────────────────
# Use LeRobot's train script:
#   python -m lerobot.scripts.train \
#       --policy-class ACT \
#       --dataset-repo-id YOUR_HF_USERNAME/so101_reach \
#       --output-dir workspace/vla/act_ckpt
#
# Or fine-tune programmatically:

def train_act(dataset_repo_id: str, output_dir: str = 'workspace/vla/act_ckpt'):
    raise NotImplementedError


# ── TODO 3: Evaluate in sim ──────────────────────────────────────────────
def evaluate_policy(checkpoint_dir: str, env_id: str, n_episodes: int = 20):
    raise NotImplementedError


if __name__ == '__main__':
    print('See TODO comments above — most steps use LeRobot CLI commands.')
