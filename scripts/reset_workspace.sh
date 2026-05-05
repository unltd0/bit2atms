#!/usr/bin/env bash
# reset_workspace.sh — create a clean workspace scaffold for all courses.
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
OLD_DIR="$REPO_ROOT/workspace_old"

# ── Helper: scaffold one course ────────────────────────────────────────────
scaffold_course() {
  local course="$1"   # e.g. "vla" or "ros2"
  shift
  local chapters=("$@")
  local workspace="$REPO_ROOT/workspace/$course"

  # Backup if non-empty
  if [ "$ADD_ONLY" -eq 1 ]; then
    : # skip backup in add-only mode
  elif [ -d "$workspace" ] && [ -n "$(find "$workspace" -type f 2>/dev/null)" ]; then
    TS=$(date +%Y%m%d_%H%M%S)
    ZIP="$OLD_DIR/${course}_${TS}.zip"

    if [ "${FORCE:-0}" != "1" ]; then
      echo "workspace/$course/ has existing files."
      read -r -p "Back them up and reset? [y/N] " confirm
      [[ "$confirm" =~ ^[Yy]$ ]] || { echo "Skipping $course."; return 0; }
    fi

    mkdir -p "$OLD_DIR"
    (cd "$REPO_ROOT" && zip -r "$ZIP" "workspace/$course/" \
      --exclude "workspace/$course/ext/*" \
      --exclude "workspace/$course/ext/**/*" \
      -q)
    echo "Backed up to workspace_old/${course}_${TS}.zip"
    find "$workspace" -mindepth 1 -maxdepth 1 ! -name 'ext' -exec rm -rf {} +
  fi

  # Create scaffold
  echo "Creating workspace/$course/ scaffold..."
  for entry in "${chapters[@]}"; do
    parts=($entry)
    ch="${parts[0]}"
    dir="$workspace/$ch"
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
}

# ── VLA course ─────────────────────────────────────────────────────────────
VLA_CHAPTERS=(
  "ch01 read_robot_state.py ik_solver.py pd_controller.py"
  "ch02 train_sac_her.py visualise.py reward_ablation.py curriculum.py"
  "ch03 train_act.sh train_diffusion.sh eval_act.sh failure_analysis.py"
  "ch04 interact_so101.py probe_language.py collect_demos.py finetune_smolvla.sh finetune_mps.py"
  "ch05 teleoperate.sh calibrate.sh collect_demos.sh finetune_smolvla.sh deploy.sh failure_log.py"
)
scaffold_course "vla" "${VLA_CHAPTERS[@]}"

# ── VLA assets ─────────────────────────────────────────────────────────────
echo ""
echo "Copying VLA assets..."
ASSETS=(
  "courses/vla/ch04_vla/assets/scene_grip.xml:workspace/vla/assets/scene_grip.xml"
)
for entry in "${ASSETS[@]}"; do
  src="$REPO_ROOT/$(echo $entry | cut -d: -f1)"
  dst="$REPO_ROOT/$(echo $entry | cut -d: -f2)"
  mkdir -p "$(dirname "$dst")"
  if [ -f "$src" ]; then
    cp "$src" "$dst"
    echo "  copied $dst"
  else
    echo "  ⚠️  Asset not found: $src"
  fi
done

# ── ROS2 course ────────────────────────────────────────────────────────────
ROS2_CHAPTERS=(
  "ch01 publisher.py subscriber.py multi_pattern_node.py my_launch.py"
  "ch02 send_goal.py"
  "ch03 real_nav_goal.py"
)
scaffold_course "ros2" "${ROS2_CHAPTERS[@]}"

echo ""
echo "Done. Workspace scaffold ready."
echo "  workspace/vla/   — VLA course"
echo "  workspace/ros2/  — ROS2 course"
echo "Each file is empty — copy code from the reader as you work through each chapter."
