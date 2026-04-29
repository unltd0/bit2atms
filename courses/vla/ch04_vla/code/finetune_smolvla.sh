#!/usr/bin/env bash
# Fine-tune SmolVLA on sim grip demos collected by collect_demos.py.
#
# Start from the real-SO-101 checkpoint — it already knows how the arm moves.
# We're only correcting the visual domain shift (real photos → sim renders).
#
# Hardware: CUDA GPU required. Colab free T4 (16 GB) works.
#           MPS will OOM, CPU will take days.
# Time: ~60–90 min on a T4 for 5k steps.
#
# Run collect_demos.py first, then upload sim_grip_data/ to Colab and run this.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
DATA_DIR="$REPO_ROOT/workspace/vla/ch04/sim_grip_data"

if [ ! -d "$DATA_DIR" ]; then
  echo "Dataset not found at $DATA_DIR"
  echo "Run collect_demos.py first."
  exit 1
fi

cd "$REPO_ROOT/workspace/ext/lerobot"

uv run --extra smolvla --extra training --extra dataset \
  lerobot-train \
    --policy.path=lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace \
    --dataset.repo_id=local/sim_grip \
    --dataset.root="$DATA_DIR" \
    --batch_size=16 \
    --steps=5000 \
    --policy.push_to_hub=false \
    --output_dir=outputs/smolvla_sim_grip_ft
