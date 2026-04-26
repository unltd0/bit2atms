#!/usr/bin/env bash
# reset_workspace.sh — create a clean workspace scaffold for the VLA course.
#
# If workspace/vla/ already has files, backs them up to workspace_old/<timestamp>.zip
# then wipes and recreates the folder structure with empty placeholder files.
#
# Usage (from repo root):
#   bash scripts/reset_workspace.sh            # backup existing files, then reset
#   bash scripts/reset_workspace.sh --add-only # only create missing files, touch nothing else
#   FORCE=1 bash scripts/reset_workspace.sh    # reset without backup prompt

set -euo pipefail

ADD_ONLY=0
for arg in "$@"; do
  [[ "$arg" == "--add-only" ]] && ADD_ONLY=1
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACE="$REPO_ROOT/workspace/vla"
OLD_DIR="$REPO_ROOT/workspace_old"

# ── Chapter scaffold config ────────────────────────────────────────────────
# Format: "chXX file1.py file2.sh ..."
CHAPTERS=(
  "ch01 read_robot_state.py ik_solver.py pd_controller.py"
  "ch02 train_sac_her.py visualise.py reward_ablation.py curriculum.py"
  "ch03 collect_demos.py eval_policy.py"
  "ch04 smolvla_finetune.py eval_smolvla.py"
  "ch05 physics_dr.py visual_dr.py eval_transfer.py"
  "ch06 fk_subscriber.py ik_service.py"
  "ch07 teleoperate.sh calibrate.sh collect_demos.sh train_real.sh deploy.sh failure_log.py"
  "ch08 perception.py bimanual_env.py"
)

# ── Backup existing workspace if non-empty ─────────────────────────────────
if [ "$ADD_ONLY" -eq 1 ]; then
  echo "Add-only mode: creating missing files only."
elif [ -d "$WORKSPACE" ] && [ -n "$(find "$WORKSPACE" -type f 2>/dev/null)" ]; then
  TS=$(date +%Y%m%d_%H%M%S)
  ZIP="$OLD_DIR/${TS}.zip"

  if [ "${FORCE:-0}" != "1" ]; then
    echo "workspace/vla/ has existing files."
    read -r -p "Back them up and reset? [y/N] " confirm
    [[ "$confirm" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }
  fi

  mkdir -p "$OLD_DIR"
  (cd "$REPO_ROOT" && zip -r "$ZIP" workspace/vla/ \
    --exclude "workspace/vla/ext/*" \
    --exclude "workspace/vla/ext/**/*" \
    -q)
  echo "Backed up to workspace_old/${TS}.zip"
  # Remove everything except the ext/ folder (mujoco_menagerie, lerobot, etc.)
  find "$WORKSPACE" -mindepth 1 -maxdepth 1 ! -name 'ext' -exec rm -rf {} +
fi

# ── Create scaffold ────────────────────────────────────────────────────────
echo "Creating workspace scaffold..."

for entry in "${CHAPTERS[@]}"; do
  parts=($entry)
  ch="${parts[0]}"
  dir="$WORKSPACE/$ch"
  mkdir -p "$dir"
  for i in "${!parts[@]}"; do
    [ "$i" -eq 0 ] && continue
    file="${parts[$i]}"
    path="$dir/$file"
    if [ ! -f "$path" ]; then
      touch "$path"
      echo "  created $path"
    fi
  done
done

echo ""
echo "Done. Workspace scaffold ready at workspace/vla/"
echo "Each file is empty — copy code from the reader as you work through each chapter."
