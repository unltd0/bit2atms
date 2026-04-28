#!/usr/bin/env bash
# Fine-tune SmolVLA on the svla_so101_pickplace dataset.
# The checkpoint was already trained on this same data — this is a pipeline exercise.
#
# Hardware: CUDA GPU required (Colab free T4 works with --batch_size=16)
#           MPS will OOM, CPU will take days.
# Time: ~60–90 min on a T4 for 10k steps.

set -euo pipefail

cd workspace/ext/lerobot

uv run --extra smolvla --extra training --extra dataset \
  lerobot-train \
    --policy.path=lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace \
    --dataset.repo_id=lerobot/svla_so101_pickplace \
    --batch_size=16 \
    --steps=10000 \
    --policy.push_to_hub=false \
    --output_dir=outputs/smolvla_so101_ft
