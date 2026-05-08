#!/bin/bash
# Restart the full ch02 stack inside the container.
# Kills any running stack first, then starts fresh.
# Run via: docker exec -d ros2 bash /workspace/ros2/ch02/_restart_stack.sh
source /opt/ros/jazzy/setup.bash
export TURTLEBOT3_MODEL=burger

LOG=/tmp/ch02_stack.log
: > "$LOG"

# Kill anything from a previous run
pkill -f turtlebot3_world_headless || true
pkill -f slam_toolbox            || true
pkill -f foxglove_bridge         || true
pkill -f obstacle_detection      || true
pkill -f "topic pub"             || true
sleep 2

# 1. Headless TurtleBot3 world (patched launch: headless + frame_prefix fix + ground truth)
nohup ros2 launch /workspace/ros2/launch/turtlebot3_world_headless.launch.py \
  >> "$LOG" 2>&1 &
echo "world PID=$!" >> "$LOG"
sleep 8

# 2. SLAM Toolbox
nohup ros2 launch slam_toolbox online_async_launch.py use_sim_time:=true \
  >> "$LOG" 2>&1 &
echo "slam PID=$!" >> "$LOG"
sleep 4

# 3. Foxglove bridge (port 8765)
nohup ros2 launch foxglove_bridge foxglove_bridge_launch.xml port:=8765 \
  >> "$LOG" 2>&1 &
echo "foxglove PID=$!" >> "$LOG"

echo "stack ready — run obstacle_detection.py to start mapping" >> "$LOG"
echo "stack ready"
