"""
Chapter 06 — Vision-Language-Action Models
workspace/vla/ch06_starter.py

Projects to complete (see courses/vla/ch06_vla/README.md):
  1. Run SmolVLA inference on a single observation
  2. Fine-tune SmolVLA on your demonstration dataset
  3. Evaluate language-conditioned policy performance
"""

# ── TODO 1: SmolVLA inference ────────────────────────────────────────────
def run_smolvla_inference(image_path: str, language_instruction: str):
    """
    Load SmolVLA, pass an image + language instruction, return predicted action.
    See: https://huggingface.co/lerobot/smolvla
    """
    raise NotImplementedError


# ── TODO 2: Fine-tune SmolVLA ────────────────────────────────────────────
# Use LeRobot's train script with SmolVLA policy class:
#   python -m lerobot.scripts.train \
#       --policy-class SmolVLA \
#       --dataset-repo-id YOUR_HF_USERNAME/so101_reach \
#       --output-dir workspace/vla/smolvla_ckpt

def finetune_smolvla(dataset_repo_id: str, output_dir: str = 'workspace/vla/smolvla_ckpt'):
    raise NotImplementedError


# ── TODO 3: Language-conditioned evaluation ──────────────────────────────
EVAL_TASKS = [
    'pick up the red cube',
    'move the block to the left',
    'place the object in the bowl',
]

def evaluate_language_conditioned(checkpoint_dir: str, tasks: list[str]):
    """Run each task instruction and record success rate."""
    raise NotImplementedError


if __name__ == '__main__':
    print('Update YOUR_HF_USERNAME in the CLI commands above, then run them.')
