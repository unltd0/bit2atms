# Chapter 2 — Simulation

**Time:** Half day
**Hardware:** Laptop only
**Prerequisites:** Chapter 1

---

## What are we here for

Simulation lets you iterate fast — no cable, no batteries, no broken hardware. This chapter puts a differential-drive robot in Gazebo, teaches you to see the world through its sensors, builds a map with SLAM, and sends it to a goal autonomously.

The tools here — Gazebo, RViz, Nav2, SLAM Toolbox — are what you'll use on real hardware in ch03. Learning them in sim first means ch03 is just swapping the data source.

**Mac users:** Run everything inside the Docker container from ch01. Add display forwarding so Gazebo and RViz render on your Mac screen.

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

Install TurtleBot3 packages (inside Docker or on Linux):

🟢 **Run**

```bash
sudo apt update
sudo apt install -y \
  ros-jazzy-turtlebot3 \
  ros-jazzy-turtlebot3-simulations \
  ros-jazzy-turtlebot3-gazebo \
  ros-jazzy-turtlebot3-navigation2 \
  ros-jazzy-slam-toolbox \
  ros-jazzy-nav2-bringup

# Required env var — tells TurtleBot3 which model to use
echo "export TURTLEBOT3_MODEL=burger" >> ~/.bashrc
source ~/.bashrc
```

**Mac — Gazebo and RViz need a display. Two options:**

*Option A — XQuartz (native Mac window):*
1. Install [XQuartz](https://www.xquartz.org), open it, go to Preferences → Security → check "Allow connections from network clients", then restart XQuartz.
2. Run: `xhost +localhost`
3. Start Docker with display forwarding:

```bash
docker run -it --rm \
  --platform linux/amd64 \
  -e DISPLAY=host.docker.internal:0 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $(pwd)/workspace/ros2:/workspace/ros2 \
  --name ros2 \
  osrf/ros:jazzy-desktop bash
```

*Option B — Linux VM or remote Linux machine (more reliable):* SSH with X forwarding (`ssh -X user@host`), or just use a Linux machine natively. Gazebo on Docker-Mac is fragile; if Option A fails, Linux is the better path for ch02 and ch03.

### Launch the simulation

🟢 **Run**

```bash
source /opt/ros/jazzy/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

Gazebo opens with a TurtleBot3 Burger in a small arena. The robot is publishing sensor data — lidar scans on `/scan`, odometry on `/odom`, camera on `/camera/image_raw`.

![TurtleBot3 in Gazebo simulation world](https://emanual.robotis.com/assets/images/platform/turtlebot3/simulation/turtlebot3_gazebo_world.png)

### Drive it

In a second terminal:

🟢 **Run**

```bash
ros2 run turtlebot3_teleop teleop_keyboard
```

W/A/S/D to drive, space to stop. You're publishing `Twist` messages to `/cmd_vel`.

### Inspect the TF tree

TF (transform) is how ROS2 tracks the position of every frame — robot base, lidar, wheels, map — relative to each other. Nav2 uses TF to know where the robot is and where its sensors are.

In a third terminal:

🟡 **Know**

```bash
# Print all active transforms
ros2 run tf2_tools view_frames

# Opens RViz with TF visualization
ros2 run rviz2 rviz2
```

In RViz: Add → TF. You'll see the `base_link`, `base_scan`, `odom`, and `map` frames as arrows. The chain `map → odom → base_link → base_scan` is what Nav2 maintains during navigation.

![TF tree showing robot coordinate frames](https://docs.ros.org/en/jazzy/_images/tfs.png)

---

## Project B — SLAM Toolbox

**Problem:** The robot needs a map to navigate. SLAM (Simultaneous Localization and Mapping) builds one while the robot drives.

**Approach:** SLAM Toolbox listens to `/scan` (lidar) and `/odom`, stitches scans together into a 2D occupancy grid, and publishes the growing map to `/map`.

```
/scan + /odom → SLAM Toolbox → /map (occupancy grid, updates live)
```

### Launch SLAM

With the Gazebo simulation running from Project A:

🟢 **Run**

```bash
sudo apt install -y ros-jazzy-slam-toolbox

# Terminal 2: start SLAM
ros2 launch slam_toolbox online_async_launch.py

# Terminal 3: open RViz to watch the map build
ros2 run rviz2 rviz2
```

In RViz: Add → Map → topic `/map`. Add → LaserScan → topic `/scan`.

### Drive and map

🔴 **Work** — drive the robot around the full arena until the map covers it completely

```bash
# Terminal 4: teleop
ros2 run turtlebot3_teleop teleop_keyboard
```

Drive slowly. Watch the map fill in as the lidar sees new walls. The grey cells are unknown, white is free space, black is obstacle.

![SLAM map being built in RViz as robot explores](https://emanual.robotis.com/assets/images/platform/turtlebot3/slam/slam_hector.png)

### Save the map

🟢 **Run**

```bash
ros2 run nav2_map_server map_saver_cli -f ~/my_map
# Creates my_map.pgm (image) and my_map.yaml (metadata)
```

The `.pgm` is the occupancy grid image. The `.yaml` tells Nav2 the resolution and origin.

---

## Project C — Nav2 Autonomous Navigation

**Problem:** Drive the robot to a goal without manual control.

**Approach:** Nav2 is the full autonomous navigation stack — it takes the map from Project B, localizes the robot within it (AMCL), plans a path, and executes it. You send a goal once; Nav2 handles the rest.

```
/map + /scan + /odom → AMCL (localization) → Nav2 planner → /cmd_vel
```

### Launch Nav2

With Gazebo still running and the map saved:

🟢 **Run**

```bash
ros2 launch turtlebot3_navigation2 navigation2.launch.py \
  map:=$HOME/my_map.yaml
```

RViz opens with the map loaded. The robot appears as a green arrow — but its pose may be wrong initially.

**Set the initial pose:** In RViz, click "2D Pose Estimate" then click where the robot actually is on the map and drag to set its heading. AMCL uses this as a starting point and refines it as the robot moves.

![Nav2 stack in RViz with robot localized on a map](https://navigation.ros.org/_images/rviz_launch.png)

### Send a goal from RViz

Click "2D Nav Goal" in RViz, click a destination on the map, drag to set the heading. The robot plans a path and drives there.

### Send a goal from Python

🔴 **Work** — modify the goal coordinates to navigate to three waypoints in sequence

```python workspace/ros2/ch02/send_goal.py
# workspace/ros2/ch02/send_goal.py
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator
import rclpy

# 1. Navigator wraps the Nav2 action interface
def main() -> None:
    rclpy.init()
    nav = BasicNavigator()
    nav.waitUntilNav2Active()  # Nav2 takes ~10s to start — wait before sending goals

    # 2. Build a goal pose — x, y in map frame (meters), z=0 for 2D
    goal = PoseStamped()
    goal.header.frame_id = 'map'
    goal.pose.position.x = 1.0   # meters from map origin
    goal.pose.position.y = 0.5
    goal.pose.orientation.w = 1.0  # facing forward (no rotation)

    # 3. Send goal and wait — blocks until the robot arrives or fails
    nav.goToPose(goal)
    while not nav.isTaskComplete():
        feedback = nav.getFeedback()
        if feedback:
            print(f'Distance remaining: {feedback.distance_remaining:.2f} m')

    print('Result:', nav.getResult())
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

```bash
python3 send_goal.py
```

---

## Self-Check

1. What does SLAM Toolbox need as input? — **Answer:** Lidar scans (`/scan`) and odometry (`/odom`). It uses scan matching to build and update the map.
2. AMCL vs SLAM — what's the difference? — **Answer:** SLAM builds the map while exploring. AMCL localizes the robot on an existing map during navigation. Nav2 uses AMCL.
3. The robot drives into a wall. What's wrong? — **Answer:** The map is stale or the initial pose estimate was wrong. Check the AMCL particle cloud in RViz — if it's spread out, the robot is lost. Re-set the 2D Pose Estimate.
4. What is `/cmd_vel` and who publishes to it? — **Answer:** A `Twist` message: linear.x (forward speed) and angular.z (rotation). During teleop, the teleop node publishes it. During autonomous nav, Nav2's controller publishes it.
5. You save a map but Nav2 can't load it. Why? — **Answer:** The `.pgm` and `.yaml` must be in the same directory and the yaml's `image:` field must match the `.pgm` filename.

---

## Common Mistakes

- **SLAM drifts on fast turns**: Drive slowly. SLAM assumes scan matching works — spinning too fast loses track.
- **Nav2 localizes wrong**: Always set 2D Pose Estimate before sending a goal. AMCL's initial uncertainty is high.
- **Map origin mismatch**: If you drove the robot before starting SLAM, the `odom` frame has drifted. Restart SLAM from a known position.
- **Mac: no Gazebo window**: XQuartz must be running and `xhost +localhost` must be set before starting the Docker container.

---

## Resources

1. [TurtleBot3 Simulation docs](https://emanual.robotis.com/docs/en/platform/turtlebot3/simulation/) — full setup guide for Gazebo + TurtleBot3
2. [SLAM Toolbox](https://github.com/SteveMacenski/slam_toolbox) — how it works and configuration options
3. [Nav2 docs — Concepts](https://navigation.ros.org/concepts/index.html) — clear explanation of the full stack
4. [nav2_simple_commander API](https://github.com/ros-navigation/navigation2/tree/main/nav2_simple_commander) — Python API for sending goals programmatically
