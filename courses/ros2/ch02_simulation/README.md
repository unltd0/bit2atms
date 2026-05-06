# Chapter 2 — Simulation

**Time:** Half day
**Hardware:** Laptop only
**Prerequisites:** Chapter 1

---

## What are we here for

Simulation lets you iterate fast — no cable, no batteries, no broken hardware. This chapter puts a robot in a 3D physics simulator, teaches you to see the world through its sensors, builds a map with SLAM, and sends the robot to a goal autonomously.

The tools you'll use here — Gazebo, RViz, Nav2, SLAM Toolbox — are the same ones you use on real hardware in ch03. Learning them in sim first means ch03 is just swapping the data source from simulator to real motors and lidar.

### The vocabulary

**Differential-drive robot** — A robot with two independently-driven wheels (plus usually a passive caster for balance). Steering works by spinning the wheels at different speeds: same speed forward = drive straight, opposite directions = spin in place, slight difference = curve. It's the simplest practical drive system, used by Roombas, warehouse robots, and most research platforms. The `Twist` message you saw in ch01 (`linear.x` + `angular.z`) maps directly to "wheel speeds" through a kinematics formula the robot's driver handles internally.

**TurtleBot3** — A small, cheap, well-documented differential-drive robot designed for ROS education. It exists as physical hardware and as a fully-modeled Gazebo robot — same topics, same TF tree (Same physical structure - so same relative positioning of all components wrt to the robot body), same drivers. The "Burger" variant (used in this chapter) has a 360° lidar on top and two wheels. We use it because everything just works out of the box: ROS2 ships official packages for the robot model, the simulation worlds, and Nav2 configurations.

![TurtleBot3 Burger physical robot](https://emanual.robotis.com/assets/images/platform/turtlebot3/hardware_setup/turtlebot3_burger.png)

**Gazebo** — Open-source 3D physics simulator made for robotics. It models gravity, friction, collisions, and sensors (lidar, cameras, IMU) so you can test robot code without hardware. Think Unity, but for robots, and pre-wired to ROS2 topics. Gazebo publishes simulated sensor data to the same topic names a real robot would (`/scan`, `/odom`, `/camera/image_raw`), so your code doesn't need to know whether it's running against sim or hardware.

![Gazebo simulator with TurtleBot3 spawned in the world](https://emanual.robotis.com/assets/images/platform/turtlebot3/simulation/turtlebot3_world_sim.png)

**RViz** — A 3D visualization tool for ROS2 data. It doesn't simulate anything — it just renders whatever's on your topics: lidar scan points, camera images, the map, the TF tree, planned paths.

![Gazebo (left, ground truth) and RViz (right, robot's belief) running side-by-side with TurtleBot3](https://emanual.robotis.com/assets/images/platform/turtlebot3/simulation/turtlebot3_gazebo_rviz.png)

**TF (Transform Library) / TF Tree** — ROS2’s system for tracking all coordinate frames on a robot in a hierarchical parent-child tree (no cycles, one root). For TurtleBot3, the tree looks like: `map → odom → base_footprint → base_link → base_scan / wheel_left_link / wheel_right_link`. TF lets you automatically convert data between frames (e.g., lidar distance readings in the lidar’s frame → robot’s base frame) so every node gets data in the frame it expects. Nav2 *requires* a valid TF tree to know where the robot is relative to the map, and where obstacles are relative to the robot.

### Ground truth vs. belief — one of the most important ideas in this chapter

> **Gazebo shows you what's actually happening in the world. RViz shows you what the robot *believes* is happening.**

These two views are almost never identical, and the gap between them is where every robotics bug lives.

**A concrete example.** You're running SLAM. In **Gazebo** you see the robot sitting in the middle of the arena, exactly where you placed it. In **RViz** you see the robot rendered slightly to the left of where the lidar scan dots line up with the map walls. Same robot, same instant in time — different positions on screen.

What's going on:
- **Gazebo's position** is ground truth — the simulator knows the robot's exact pose because it computed it.
- **RViz's position** comes from `/odom` (odometry — wheel encoders integrated over time) corrected by SLAM's scan matching. After 30 seconds of driving, wheel slip and integration error mean the odometry estimate has drifted ~10 cm from reality. SLAM tries to correct this by aligning the latest lidar scan against the map — but if scan matching is imperfect, the corrected pose still lags ground truth.

You can only spot this gap because you have both views. On real hardware, there's no Gazebo — but there is the real robot's actual physical position AND RViz's estimated belief. If the lidar scan doesn't line up with map walls in RViz, the robot is actually somewhere else in the physical space, and Nav2 will plan into walls.

**Rule of thumb:** Gazebo shows ground truth (the robot's actual position), RViz shows the robot's belief. If they disagree, the robot's belief is wrong — fix the localization (e.g., set 2D Pose Estimate) before sending Nav2 a goal.

**Skip if you can answer:**
1. What is a TF tree and why does Nav2 need it?
2. What does SLAM produce, and what does Nav2 do with that output?
3. A robot has a `/cmd_vel` topic. What message type does it expect and what fields matter?

---

## Projects

| # | Project | What you build |
|---|---------|----------------|
| A | Gazebo + TurtleBot3 | Spawn a robot, drive it, inspect TF in RViz |
| B | SLAM Toolbox | Drive around, watch a map build in real time |
| C | Nav2 Autonomous Navigation | Send a goal, watch the robot plan and execute |

---

## Project A — Gazebo & TurtleBot3

**Problem:** Get a simulated robot running and understand its sensor/TF structure.

**Approach:** Use the official TurtleBot3 Gazebo package — one command spawns the robot in a pre-built world.

### Setup

If you followed ch01, you already have the `bit2atms-ros2` Docker image — it ships with everything ch02 needs (TurtleBot3, Gazebo, Nav2, SLAM Toolbox, RViz, tf2 tools) pre-installed. ch01's container start command was headless; for ch02 you need to add display forwarding so Gazebo and RViz windows render on your Mac screen.

#### Step 1 — Set up X11 display forwarding (Mac only, one-time per host reboot)

*Option A — XQuartz (native Mac window):*
1. Install [XQuartz](https://www.xquartz.org) if not already installed.
2. Open XQuartz.app (must be running for `xhost` to work).
3. Enable network connections: XQuartz menu → Settings (or Preferences) → Security tab → Check "Allow connections from network clients".
4. Quit XQuartz fully (Cmd+Q) and reopen it — the setting only takes effect after a full restart.
5. From a Mac terminal (not inside the container):
   ```bash
   export DISPLAY=:0
   xhost +localhost
   # Expected output: localhost being added to access control list
   ```

*Option B — Linux VM or remote Linux machine (more reliable):* SSH with X forwarding (`ssh -X user@host`), or just use a Linux machine natively. Gazebo on Docker-Mac is fragile; if Option A fails, Linux is the better path for ch02 and ch03.

#### Step 2 — Start the container with display forwarding

🟢 **Run** — from the Mac terminal, in the repo root

```bash
docker run -it --rm \
  --platform linux/amd64 \
  -e DISPLAY=host.docker.internal:0 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $(pwd)/workspace/ros2:/workspace/ros2 \
  --name ros2 \
  bit2atms-ros2
```

You're now inside the container. Everything below runs inside it.

If the image isn't found (`bit2atms-ros2` doesn't exist), build it from the repo root first:

```bash
docker build --platform linux/amd64 -t bit2atms-ros2 -f resources/ros2/docker/Dockerfile .
```

#### Step 3 — Verify the packages are present (inside the container)

🟢 **Run**

```bash
ros2 pkg list | grep -E "turtlebot3_gazebo|nav2_bringup|slam_toolbox"
```

Expected output:

```text
nav2_bringup
slam_toolbox
turtlebot3_gazebo
```

If any are missing, the image is stale. Exit (`exit`), rebuild it from the repo root with `docker build ... -f resources/ros2/docker/Dockerfile .`, and re-run `docker run`.

The workspace folder `/workspace/ros2/ch02/` is already scaffolded by `scripts/reset_workspace.sh` (run from the repo root) — if for some reason it doesn't exist, `mkdir -p /workspace/ros2/ch02` inside the container creates it on the host via the bind mount.

#### Linux native (alternative — skip if you used Docker above)

If you're on Linux and didn't go through the Docker path, install the extra packages directly:

```bash
sudo apt update
sudo apt install -y \
  ros-jazzy-turtlebot3 ros-jazzy-turtlebot3-gazebo \
  ros-jazzy-nav2-bringup ros-jazzy-slam-toolbox \
  ros-jazzy-rviz2 ros-jazzy-tf2-tools
echo "export TURTLEBOT3_MODEL=burger" >> ~/.bashrc
source ~/.bashrc
mkdir -p ~/workspace/ros2/ch02
```

### Terminal plan for this project

You'll need up to four shells inside the container. Open extra ones with `docker exec -it ros2 bash` from a new Mac terminal.

| Terminal | Use |
|---|---|
| T1 | Gazebo (long-running) |
| T2 | Teleop (long-running) |
| T3 | Inspection commands (`tf2_echo`, `topic list/hz/echo`) |
| T4 | RViz (long-running) |

### Launch the simulation

🟢 **Run** — T1, leave running for the rest of Project A

```bash
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

Gazebo opens with a TurtleBot3 Burger in a small arena. The robot is already publishing sensor data — lidar scans on `/scan`, odometry on `/odom`, camera on `/camera/image_raw`.

![TurtleBot3 in the Gazebo simulation world](https://emanual.robotis.com/assets/images/platform/turtlebot3/simulation/turtlebot3_world_sim.png)

🟡 **Know** — T3, verify topics are flowing

```bash
ros2 topic list | grep -E '/scan|/odom|/cmd_vel'
ros2 topic hz /scan       # should be ~5 Hz on TurtleBot3
```

**What this launch file does:** It starts the Gazebo simulator with a TurtleBot3 Burger model in a small arena world. Specifically, it launches:
- Gazebo simulator with the `turtlebot3_world` (a small arena with walls)
- TurtleBot3 model (geometry, joints, mass)
- Sensor plugins that publish `/scan` (lidar), `/odom` (odometry), `/camera/image_raw`
- `robot_state_publisher` for the TF tree (`base_link`, `base_scan`, wheels)

One command gives you a robot running in a simulated world.

### Drive it

🟢 **Run** — T2, leave teleop running

```bash
ros2 run turtlebot3_teleop teleop_keyboard
```

W/A/S/D drives, space stops. **The terminal running teleop must have keyboard focus** — click on the T2 window before pressing keys. Behind the scenes, teleop publishes `geometry_msgs/msg/Twist` to `/cmd_vel`:

```text
linear:
  x: 0.22  # forward speed in m/s
  y: 0.0
  z: 0.0
angular:
  x: 0.0
  y: 0.0
  z: 0.5   # rotation rate in rad/s (yaw)
```

Only `linear.x` and `angular.z` matter for a differential-drive robot — the other fields are zero.

🟡 **Know** — T3, confirm `/cmd_vel` while you drive in T2

```bash
ros2 topic echo /cmd_vel
```

Press Ctrl+C in T3 when done — leave Gazebo (T1) and teleop (T2) running.

### Inspect the TF tree

You already know what TF is from the intro vocabulary. Recall the TurtleBot3 chain: `map → odom → base_footprint → base_link → base_scan / wheels`. `map` only appears once SLAM runs; before that the chain starts at `odom`.

🟡 **Know** — T3

```bash
# Generate frames.pdf showing the full tree (saved in /workspace/ros2/ch02 so it persists)
cd /workspace/ros2/ch02
ros2 run tf2_tools view_frames

# Print a single transform live (source → target)
ros2 run tf2_ros tf2_echo odom base_footprint
```

🟢 **Run** — T4, open RViz to visualize TF + sensor data interactively

```bash
ros2 run rviz2 rviz2
```

In RViz: set "Fixed Frame" to `odom`, then Add → TF. You'll see the chain `odom → base_footprint → base_link → base_scan → wheel_left/right`. After Project B (SLAM), `map` will appear as the new root.

![TurtleBot3 with TF visualization in RViz](https://emanual.robotis.com/assets/images/platform/turtlebot3/simulation/turtlebot3_gazebo_rviz.png)

**Before moving to Project B:** close this RViz window — Project B starts a fresh RViz with different displays. Leave Gazebo (T1) and teleop (T2) running.

---

## Project B — SLAM Toolbox

**Problem:** The robot needs a map to navigate. SLAM (Simultaneous Localization and Mapping) builds one while the robot drives.

**Approach:** SLAM Toolbox listens to `/scan` (lidar) and `/odom`, stitches scans together into a 2D occupancy grid, and publishes the growing map to `/map`.

```
/scan + /odom → SLAM Toolbox → /map (occupancy grid, updates live)
```

### Terminal plan for this project

Carrying over from Project A: T1 still has Gazebo, T2 still has teleop, and you closed Project A's RViz at the end of that section. T3 was used for one-off inspection — reuse it for SLAM. T4 will host a fresh RViz with SLAM-specific displays.

| Terminal | Use |
|---|---|
| T1 | Gazebo (still running from Project A) |
| T2 | Teleop (still running from Project A) |
| T3 | SLAM Toolbox |
| T4 | RViz (fresh, with SLAM-specific displays) |

If Gazebo isn't still running in T1, start it again: `ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py`. Restarting Gazebo resets the world to its default state — fine for now since we haven't saved a map yet.

### Launch SLAM

🟢 **Run** — T3

```bash
ros2 launch slam_toolbox online_async_launch.py
```

**What this launch file does:** It starts the SLAM Toolbox node that:
- Subscribes to `/scan` (lidar) and `/odom` (odometry)
- Publishes the growing `/map` occupancy grid as you drive
- Publishes the `map → odom` TF transform (this adds `map` as the root of your TF tree)

🟢 **Run** — T4, open a fresh RViz to watch the map build

```bash
ros2 run rviz2 rviz2
```

In RViz:
- Set "Fixed Frame" to `map`
- Add → Map → topic `/map`
- Add → LaserScan → topic `/scan` (helpful to see what SLAM is seeing)
- Add → TF (optional — confirms `map → odom → base_footprint` chain)

### Drive and map

🔴 **Work** — drive the robot around the full arena (using T2's teleop) until the map covers it completely

Drive slowly. Watch the map fill in as the lidar sees new walls. The colors mean:
- **Grey** — unknown (lidar hasn't seen it)
- **White** — free space (lidar passed through)
- **Black** — obstacle (lidar hit a wall)

Spinning fast makes scan matching fail and the map drifts. If that happens, restart SLAM (Ctrl+C in T3, re-launch).

![SLAM map being built in RViz as robot explores](https://emanual.robotis.com/assets/images/platform/turtlebot3/slam/slam_running_for_mapping.png)

### Save the map

Update the terminal plan: T1–T4 are all busy, so open T5 with `docker exec -it ros2 bash` from a new Mac terminal.

| Terminal | Use |
|---|---|
| T1 | Gazebo |
| T2 | Teleop |
| T3 | SLAM Toolbox |
| T4 | RViz |
| T5 | One-shot commands (map save, etc.) |

Save into the workspace folder (mounted from your host) so the file persists outside the container.

🟢 **Run** — T5

```bash
ros2 run nav2_map_server map_saver_cli -f /workspace/ros2/ch02/my_map
# Creates my_map.pgm (image) and my_map.yaml (metadata)
```

The `.pgm` is the occupancy grid as a greyscale image — open it in any image viewer. The `.yaml` records the resolution (meters per pixel) and the origin (where pixel (0,0) is in map coordinates) — Nav2 reads it to translate between pixel space and metric space.

```text
# my_map.yaml
image: my_map.pgm
mode: trinary
resolution: 0.05         # 5 cm per pixel
origin: [-1.92, -0.55, 0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.25
```

---

## Project C — Nav2 Autonomous Navigation

**Problem:** Drive the robot to a goal without manual control.

**Approach:** Nav2 is the full autonomous navigation stack — it takes the map from Project B, localizes the robot within it (AMCL), plans a path, and executes it. You send a goal once; Nav2 handles the rest.

```
/map + /scan + /odom → AMCL (localization) → Nav2 planner → /cmd_vel
```

### Reset the terminals

Project B left you with Gazebo (T1), teleop (T2), SLAM (T3), RViz (T4), and a one-shot shell (T5). For Project C you need to:

- **T3 — Ctrl+C to stop SLAM Toolbox.** Nav2 ships its own AMCL localization. Leaving SLAM running causes both SLAM and AMCL to fight over the `map → odom` transform.
- **T4 — close the RViz window** (or Ctrl+C). Nav2 ships a Nav2-configured RViz with the right displays already added.
- Leave T1 (Gazebo) and T2 (teleop) running.

### Terminal plan for this project

| Terminal | Use |
|---|---|
| T1 | Gazebo (still running) |
| T2 | Teleop (still running, optional — you can also drive via Nav2 goals) |
| T3 | Nav2 stack |
| T4 | Nav2-configured RViz |
| T5 | `send_goal.py` (later) |

### Launch Nav2

On Jazzy, the canonical launcher is `nav2_bringup` rather than the old `turtlebot3_navigation2`:

🟢 **Run** — T3

```bash
ros2 launch nav2_bringup bringup_launch.py \
  map:=/workspace/ros2/ch02/my_map.yaml \
  use_sim_time:=true
```

`use_sim_time:=true` is required when running against Gazebo — Nav2 trusts the simulator's clock rather than wall time.

Expected output (last few lines once Nav2 is fully up):

```text
[lifecycle_manager-12] [INFO] Managed nodes are active
[lifecycle_manager-12] [INFO] Creating bond timer...
[bt_navigator-9] [INFO] Begin navigating from current location
```

If you see `Managed nodes are active`, AMCL/planner/controller are all alive. Total startup takes ~10 seconds.

**What this launch file does:** It starts the full Nav2 stack:
- `amcl` — particle filter localization on the loaded map
- `map_server` — loads the saved `.yaml` map, publishes `/map`
- `planner_server` — global path planner (NavFn / A*)
- `controller_server` — local path follower (DWB)
- `behavior_tree_navigator` — orchestrates plan → follow → recover
- `behavior_server` — recovery behaviors (spin, back-up, wait)
- `waypoint_follower` — handles `followWaypoints`
- `lifecycle_manager` — brings all the above up in order

🟢 **Run** — T4, open RViz with the Nav2 view

```bash
ros2 launch nav2_bringup rviz_launch.py
```

**What this launch file does:** Opens RViz preconfigured with the Nav2 layout — map, robot model, particle cloud, planned path, costmap, and goal/initial-pose tool buttons.

RViz opens with the map loaded. The robot appears as a green arrow — but its pose may be wrong initially.

**Set the initial pose:** Look at where the robot is in **Gazebo** (ground truth), then in RViz click "2D Pose Estimate", click that same spot on the map, and drag in the direction the robot is facing. AMCL uses this as a starting point — once the robot moves a little, AMCL refines it from lidar observations. If the Gazebo and RViz robot positions don't match after this, AMCL is misaligned and Nav2 will plan into walls.

![RViz showing the 2D Pose Estimate tool — click and drag to set the robot's starting pose](https://docs.nav2.org/_images/rviz-set-initial-pose.png)

### Send a goal from RViz

Click "Nav2 Goal" in the RViz toolbar, click a destination on the map, drag to set the heading. The robot plans a path (shown as a green line) and drives there.

![Sending a navigation goal — robot plans a path and follows it](https://docs.nav2.org/_images/navigate-to-pose.png)

If the robot drives into a wall, AMCL likely lost track — see Self-Check Q3.

### Send a goal from Python

The `nav2_simple_commander` package wraps Nav2's action interface so you don't have to deal with action clients directly.

🔴 **Work** — extend this to use `nav.followWaypoints([p1, p2, p3])` to visit three waypoints in sequence

Save this to `/workspace/ros2/ch02/send_goal.py`:

```python
# /workspace/ros2/ch02/send_goal.py
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator
import rclpy

# 1. BasicNavigator wraps Nav2's action interface in a synchronous API
def main() -> None:
    rclpy.init()
    nav = BasicNavigator()
    nav.waitUntilNav2Active()  # Nav2 takes ~10s to start — block until it's ready

    # 2. Build a goal pose
    #   header.frame_id: which frame the coordinates are in ('map' = world frame)
    #   position.x/y: meters from the map origin (see my_map.yaml)
    #   orientation: quaternion; w=1 means no rotation (facing +x in map frame)
    goal = PoseStamped()
    goal.header.frame_id = 'map'
    goal.pose.position.x = 1.0
    goal.pose.position.y = 0.5
    goal.pose.orientation.w = 1.0

    # 3. Send goal and stream feedback until done
    nav.goToPose(goal)
    while not nav.isTaskComplete():
        feedback = nav.getFeedback()
        if feedback:
            print(f'Distance remaining: {feedback.distance_remaining:.2f} m')

    # 4. Result is one of: SUCCEEDED, CANCELED, FAILED
    print('Result:', nav.getResult())
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

🟢 **Run** — T5

```bash
python3 /workspace/ros2/ch02/send_goal.py
```

Expected output:

```text
[bt_navigator]: ... goal accepted ...
Distance remaining: 1.32 m
Distance remaining: 1.18 m
Distance remaining: 0.84 m
...
Distance remaining: 0.05 m
Result: TaskResult.SUCCEEDED
```

**Hint for the waypoint exercise:** `BasicNavigator` has `followWaypoints(poses: list[PoseStamped])` instead of `goToPose`. Build three `PoseStamped` objects, pass them as a list. The robot visits each in order without stopping at intermediate ones.

---

## Self-Check

1. What does SLAM Toolbox need as input? — **Answer:** Lidar scans (`/scan`) and odometry (`/odom`). It uses scan matching against a sliding window of previous scans to build the map and refine the robot's pose.
2. AMCL vs SLAM — what's the difference? — **Answer:** SLAM builds the map while exploring (no prior knowledge). AMCL localizes the robot on a known map using a particle filter. Nav2 uses AMCL because navigation assumes the map is already built.
3. The robot drives into a wall. What's wrong? — **Answer:** AMCL is mislocalized. In RViz, the AMCL particle cloud (red arrows around the robot) should be tight; if it's spread out or in the wrong place, the robot doesn't know where it is. Click "2D Pose Estimate" again to reseed it.
4. What is `/cmd_vel` and who publishes to it? — **Answer:** A `geometry_msgs/msg/Twist` message. For a differential-drive robot only `linear.x` (forward m/s) and `angular.z` (yaw rad/s) matter. During teleop the teleop node publishes; during autonomous nav, Nav2's controller publishes; both are interchangeable from the robot's perspective.
5. You save a map but Nav2 can't load it. Why? — **Answer:** Most likely you passed a relative path to `map:=`. Use an absolute path (e.g. `/workspace/ros2/ch02/my_map.yaml`). Also: the `.pgm` and `.yaml` must be in the same directory, and the yaml's `image:` field must match the `.pgm` filename exactly.

---

## Common Mistakes

- **`Package 'turtlebot3_gazebo' not found` in Docker**: You're probably running the bare `osrf/ros:jazzy-desktop` image and `apt install`-ed inside a `--rm` container — packages vanish when the container exits. Rebuild the custom image: `docker build --platform linux/amd64 -t bit2atms-ros2 -f resources/ros2/docker/Dockerfile .` from the repo root, then start with `bit2atms-ros2` instead. On a persistent container, re-source: `source /opt/ros/jazzy/setup.bash`.
- **SLAM drifts on fast turns**: Drive slowly. Scan matching breaks when the lidar scan and the odometry estimate disagree by too much. If the map is corrupted, kill and restart SLAM Toolbox.
- **Nav2 localizes wrong**: Always set 2D Pose Estimate before sending a goal. AMCL's initial uncertainty is high; a wrong pose makes Nav2 plan into walls.
- **Forgetting `use_sim_time:=true`**: When running Nav2 against Gazebo, you must pass `use_sim_time:=true` or Nav2's clock and the simulator's clock disagree. Symptom: TF transforms appear "in the future" or "too old".
- **Map origin mismatch**: If you drove the robot before starting SLAM, the `odom` frame has drifted. The map will be saved with that drift baked in. Restart Gazebo to reset odom to identity, then start SLAM immediately.
- **Mac: no Gazebo window**: XQuartz must be running and `xhost +localhost` must be set on the host **before** starting the Docker container. If you forgot, exit the container, fix it, and re-run `docker run`.
- **Relative paths in launches**: Always pass absolute container paths (`/workspace/ros2/ch02/my_map.yaml`) to launch arguments — Nav2 resolves them from its install directory, not your cwd.

---

## Resources

1. [Gazebo Sim — getting started](https://gazebosim.org/docs/latest/getstarted/) — sim concepts (worlds, models, plugins) without ROS2
2. [RViz user guide](https://github.com/ros2/rviz/blob/jazzy/docs/user_guide/index.md) — visualizing topics, frames, and robot models
3. [TurtleBot3 simulation docs](https://emanual.robotis.com/docs/en/platform/turtlebot3/simulation/) — full setup guide for Gazebo + TurtleBot3
4. [SLAM Toolbox](https://github.com/SteveMacenski/slam_toolbox) — how online async mapping works and configuration options
5. [Nav2 docs — Concepts](https://navigation.ros.org/concepts/index.html) — costmaps, planners, controllers, recovery behaviors
6. [Nav2 first-time setup](https://navigation.ros.org/getting_started/index.html) — what each parameter in the bringup does
7. [nav2_simple_commander API](https://github.com/ros-navigation/navigation2/tree/main/nav2_simple_commander) — `goToPose`, `followWaypoints`, `followPath`, cancel/feedback patterns
8. [TF2 tutorials](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Tf2/Tf2-Main.html) — when you need to write your own static or dynamic transforms
