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
SIZE_LIMIT_MB=50

# Dirs always preserved across backup/reset (in addition to >50MB dirs found at runtime).
ALWAYS_PRESERVE=("ext")

# Per-course list of top-level subdir names to preserve. Populated by find_large_dirs.
declare -a PRESERVE_VLA=()
declare -a PRESERVE_ROS2=()

# ── Find top-level subdirs in workspace/<course>/ that exceed SIZE_LIMIT_MB ──
find_large_dirs() {
  local workspace="$1"
  local -a large=()
  [ -d "$workspace" ] || { echo ""; return; }
  while IFS= read -r dir; do
    [ -z "$dir" ] && continue
    local name
    name="$(basename "$dir")"
    local size_kb
    size_kb=$(du -sk "$dir" 2>/dev/null | awk '{print $1}')
    if [ -n "$size_kb" ] && [ "$size_kb" -gt $((SIZE_LIMIT_MB * 1024)) ]; then
      large+=("$name")
    fi
  done < <(find "$workspace" -mindepth 1 -maxdepth 1 -type d 2>/dev/null)
  echo "${large[@]+${large[@]}}"
}

# ── Helper: scaffold one course (no prompting — backup already confirmed) ──
scaffold_course() {
  local course="$1"
  shift
  local chapters=("$@")
  local workspace="$REPO_ROOT/workspace/$course"

  # Resolve preserve list for this course (bash 3.2 compatible: no ${var^^}, no namerefs)
  local course_uc
  course_uc=$(echo "$course" | tr '[:lower:]' '[:upper:]')
  local preserve_var="PRESERVE_${course_uc}"
  local -a preserve=("${ALWAYS_PRESERVE[@]}")
  eval "preserve+=(\${${preserve_var}[@]+\"\${${preserve_var}[@]}\"})"

  # Backup + reset if non-empty
  if [ "$ADD_ONLY" -ne 1 ] && [ -d "$workspace" ] && [ -n "$(find "$workspace" -type f 2>/dev/null)" ]; then
    TS=$(date +%Y%m%d_%H%M%S)
    ZIP="$OLD_DIR/${course}_${TS}.zip"
    mkdir -p "$OLD_DIR"

    # Build zip excludes for preserved dirs
    local -a zip_excludes=()
    for p in "${preserve[@]}"; do
      zip_excludes+=(--exclude "workspace/$course/$p/*" --exclude "workspace/$course/$p/**/*")
    done

    (cd "$REPO_ROOT" && zip -r "$ZIP" "workspace/$course/" "${zip_excludes[@]}" -q)
    echo "Backed up to workspace_old/${course}_${TS}.zip"

    # Build find pruning for preserved dirs
    local -a find_excludes=()
    for p in "${preserve[@]}"; do
      find_excludes+=(! -name "$p")
    done
    find "$workspace" -mindepth 1 -maxdepth 1 "${find_excludes[@]}" -exec rm -rf {} +

    if [ "${#preserve[@]}" -gt 0 ]; then
      echo "  preserved: ${preserve[*]}"
    fi
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

# ── Course definitions ─────────────────────────────────────────────────────
VLA_CHAPTERS=(
  "ch01 read_robot_state.py ik_solver.py pd_controller.py"
  "ch02 train_sac_her.py visualise.py reward_ablation.py curriculum.py"
  "ch03 train_act.sh train_diffusion.sh eval_act.sh failure_analysis.py"
  "ch04 interact_so101.py probe_language.py collect_demos.py finetune_smolvla.sh finetune_mps.py"
  "ch05 teleoperate.sh calibrate.sh collect_demos.sh finetune_smolvla.sh deploy.sh failure_log.py"
)

ROS2_CHAPTERS=(
  "ch01 publisher.py subscriber.py multi_pattern_node.py my_launch.py"
  "ch02 send_goal.py"
  "ch03"
  "ch04 real_nav_goal.py"
)

# ── Scan for large dirs and prompt once for all courses ────────────────────
COURSES=("vla" "ros2")
ANY_NONEMPTY=0
SUMMARY=""

for course in "${COURSES[@]}"; do
  workspace="$REPO_ROOT/workspace/$course"
  if [ -d "$workspace" ] && [ -n "$(find "$workspace" -type f 2>/dev/null)" ]; then
    ANY_NONEMPTY=1
    large_str="$(find_large_dirs "$workspace")"
    course_uc=$(echo "$course" | tr '[:lower:]' '[:upper:]')
    if [ -n "$large_str" ]; then
      # shellcheck disable=SC2206
      large_arr=($large_str)
      eval "PRESERVE_${course_uc}=(\"\${large_arr[@]}\")"
      SUMMARY+="  workspace/$course/  (preserving >${SIZE_LIMIT_MB}MB dirs: ${large_arr[*]})"$'\n'
    else
      SUMMARY+="  workspace/$course/"$'\n'
    fi
  fi
done

if [ "$ADD_ONLY" -ne 1 ] && [ "$ANY_NONEMPTY" -eq 1 ] && [ "${FORCE:-0}" != "1" ]; then
  echo "The following workspaces have existing files:"
  printf '%s' "$SUMMARY"
  # Warn about preserved large dirs across all courses
  warned=0
  for course in "${COURSES[@]}"; do
    course_uc=$(echo "$course" | tr '[:lower:]' '[:upper:]')
    eval "preserved=(\${PRESERVE_${course_uc}[@]+\"\${PRESERVE_${course_uc}[@]}\"})"
    if [ "${#preserved[@]}" -gt 0 ]; then
      if [ "$warned" -eq 0 ]; then
        echo ""
        echo "Note: directories larger than ${SIZE_LIMIT_MB}MB will be skipped"
        echo "(not zipped, not deleted). This is expected — large dirs typically"
        echo "hold models, datasets, or external checkouts you don't want to lose."
        warned=1
      fi
    fi
  done
  echo ""
  read -r -p "Back up and reset all of the above? [y/N] " confirm
  if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
  fi
fi

# ── VLA course ─────────────────────────────────────────────────────────────
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
scaffold_course "ros2" "${ROS2_CHAPTERS[@]}"

# ── ROS2 runtime files (bind-mounted into the container) ───────────────────
# These files must exist in workspace/ when the container starts because
# resources/ is not bind-mounted. Source-of-truth lives in resources/ros2/;
# we copy them into workspace/ros2/ here. Existing files are overwritten.
echo ""
echo "Copying ROS2 runtime files (resources/ros2 → workspace/ros2)..."
ROS2_RESOURCE_FILES=(
  "resources/ros2/launch/turtlebot3_world_headless.launch.py:workspace/ros2/launch/turtlebot3_world_headless.launch.py"
  "resources/ros2/turtlebot3_burger_bridge.yaml:workspace/ros2/turtlebot3_burger_bridge.yaml"
  "resources/ros2/turtlebot3_burger_gt.sdf:workspace/ros2/turtlebot3_burger_gt.sdf"
  "resources/ros2/ground_truth_relay.py:workspace/ros2/ground_truth_relay.py"
  "resources/ros2/ch02/obstacle_detection.py:workspace/ros2/ch02/obstacle_detection.py"
  "resources/ros2/ch02/send_goal.py:workspace/ros2/ch02/send_goal.py"
  "resources/ros2/ch02/nav2_params.yaml:workspace/ros2/ch02/nav2_params.yaml"
  "resources/ros2/ch02/_restart_stack.sh:workspace/ros2/ch02/_restart_stack.sh"
  "resources/ros2/ch03/tiny_bot.urdf.xacro:workspace/ros2/ch03/tiny_bot.urdf.xacro"
  "resources/ros2/ch03/tiny_bot.sdf:workspace/ros2/ch03/tiny_bot.sdf"
  "resources/ros2/ch03/tiny_world.sdf:workspace/ros2/ch03/tiny_world.sdf"
  "resources/ros2/ch03/tiny_bot_bridge.yaml:workspace/ros2/ch03/tiny_bot_bridge.yaml"
  "resources/ros2/ch03/tiny_bot_sim.launch.py:workspace/ros2/ch03/tiny_bot_sim.launch.py"
  "resources/ros2/ch03/car_mover.py:workspace/ros2/ch03/car_mover.py"
  "resources/ros2/ch03/obstacle_stop.py:workspace/ros2/ch03/obstacle_stop.py"
  "resources/ros2/ch03/world_map_publisher.py:workspace/ros2/ch03/world_map_publisher.py"
  "resources/ros2/ch04/real_nav_goal.py:workspace/ros2/ch04/real_nav_goal.py"
)
for entry in "${ROS2_RESOURCE_FILES[@]}"; do
  src="$REPO_ROOT/$(echo $entry | cut -d: -f1)"
  dst="$REPO_ROOT/$(echo $entry | cut -d: -f2)"
  mkdir -p "$(dirname "$dst")"
  if [ -f "$src" ]; then
    cp "$src" "$dst"
    echo "  copied $dst"
  else
    echo "  ⚠️  Source not found: $src"
  fi
done

echo ""
echo "Done. Workspace scaffold ready."
echo "  workspace/vla/   — VLA course"
echo "  workspace/ros2/  — ROS2 course"
echo "ROS2 runtime files (launch, bridge, scripts) copied from resources/ros2/."
echo "Empty placeholders are for you to fill in as you work through each chapter."
