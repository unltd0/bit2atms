# Docker Image — bit2atms-ros2

One image for all ROS2 chapters (ch01, ch02, ch03). Build it once; reuse it for everything.

**What's inside:** ROS2 Jazzy, TurtleBot3, Gazebo Harmonic, SLAM Toolbox, Nav2, RViz2, foxglove_bridge, tf2 tools, colcon.

---

## Option A — Docker (Mac, Windows, Linux)

### 1. Build the image (one-time, 10–15 min)

**Intel / AMD (Mac Intel, Windows, Linux):**

```bash
cd /path/to/bit2atms
docker build -t bit2atms-ros2 -f resources/ros2/docker/Dockerfile .
```

**Apple Silicon (M1/M2/M3/M4):**

```bash
cd /path/to/bit2atms
docker build --platform linux/amd64 -t bit2atms-ros2 -f resources/ros2/docker/Dockerfile .
```

### 2. Seed the workspace (one-time, ~5 s)

The container reads chapter source files from a bind-mounted `workspace/ros2/` directory on your host. **Before starting the container, populate that directory** by running the workspace-reset script from the repo root:

```bash
# from bit2atms/
bash scripts/reset_workspace.sh --add-only
```

This copies `resources/ros2/**` (URDFs, launch files, helper scripts, etc.) into `workspace/ros2/`. The container then sees them at `/workspace/ros2/...`. If you skip this step, every chapter's "launch this file" command will fail with *file not found*.

Re-run any time you want a fresh copy (the `--add-only` flag only creates missing files; without it the script offers to back up and rewrite).

### 3. Run the container

**Run from the repo root** (`bit2atms/`) — the `-v $(pwd)/workspace/ros2` bind-mount depends on it.

**Intel / AMD:**

```bash
# from bit2atms/
docker run -it \
  -p 8765:8765 \
  -v $(pwd)/workspace/ros2:/workspace/ros2 \
  --name ros2 \
  bit2atms-ros2
```

**Apple Silicon:**

```bash
# from bit2atms/
docker run -it \
  --platform linux/amd64 \
  -p 8765:8765 \
  -v $(pwd)/workspace/ros2:/workspace/ros2 \
  --name ros2 \
  bit2atms-ros2
```

Port 8765 is the Foxglove WebSocket port — used from ch02 onwards. Publishing it always does no harm and means you never have to restart the container just to add it later.

### 4. Open extra shells

Every new terminal needs its own shell inside the container:

```bash
docker exec -it ros2 bash
```

### 5. Verify packages

```bash
ros2 pkg list | grep -E "turtlebot3_gazebo|nav2_bringup|slam_toolbox|foxglove_bridge"
```

Expected output:

```text
foxglove_bridge
nav2_bringup
slam_toolbox
turtlebot3_gazebo
```

### Notes

- The image auto-sources `/opt/ros/jazzy/setup.bash` and sets `TURTLEBOT3_MODEL=burger` in every shell — no manual sourcing needed.
- The `-v` flag bind-mounts `workspace/ros2/` so your files persist outside the container.
- Port 8765 must be published at startup — it can't be added to a running container. If you forgot it, `docker stop ros2` and re-run with `-p 8765:8765`.
- Do **not** use `--rm` — it discards any packages installed inside the running container on exit.
- **Must run from the repo root.** `docker run` uses `$(pwd)/workspace/ros2` for the bind-mount. If you run it from any other directory, the mount path is wrong and `ros2 launch /workspace/ros2/...` will fail with `ValueError: '...' is not a valid package name`.

---

## Option B — Native install (Linux only)

If you're on Linux and prefer a native install over Docker:

```bash
# Add ROS2 apt repo
sudo apt install -y software-properties-common curl
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
sudo sh -c 'echo "deb http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/ros2.list'
sudo apt update
sudo apt install -y ros-jazzy-desktop python3-colcon-common-extensions \
  ros-jazzy-turtlebot3 ros-jazzy-turtlebot3-simulations \
  ros-jazzy-turtlebot3-gazebo ros-jazzy-turtlebot3-teleop \
  ros-jazzy-nav2-bringup ros-jazzy-slam-toolbox \
  ros-jazzy-rviz2 ros-jazzy-tf2-tools ros-jazzy-foxglove-bridge
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
echo "export TURTLEBOT3_MODEL=burger" >> ~/.bashrc
source ~/.bashrc
```

Verify:

```bash
ros2 pkg list | grep -E "turtlebot3_gazebo|nav2_bringup|slam_toolbox|foxglove_bridge"
```
