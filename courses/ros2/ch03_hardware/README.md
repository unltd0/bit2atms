# Chapter 3 — Hardware

**Time:** 1 day
**Hardware:** Physical robot (TurtleBot3 Burger or Waffle)
**Prerequisites:** Chapters 1–2

---

## What are we here for

The commands are almost identical to ch02. The difference: real lidar data is noisy, the floor isn't flat, and the odometry drifts. You'll feel why sim-to-real matters.

By the end you'll have driven a physical TurtleBot, built a map of a real room, and sent it to a goal autonomously.

**Setup:** TurtleBot3 runs Ubuntu + ROS2 on a Raspberry Pi on board. Your laptop (the "remote PC") connects to the same network and sends commands. You'll run launch files on the laptop; the robot's bringup runs on the Pi.

**ROS2 version note:** TurtleBot3's Jazzy packages are in active development. If `ros-jazzy-turtlebot3-bringup` isn't available in apt, use the Humble image on both robot and laptop: `osrf/ros:humble-desktop`. All commands are identical.

**Skip if you can answer:**
1. What's the difference between the robot's on-board PC and your remote PC in a ROS2 setup?
2. Why does real SLAM drift more than sim SLAM?
3. What is `ROS_DOMAIN_ID` and why does it matter in a shared network?

---

## Projects

| # | Project | What you build |
|---|---------|----------------|
| A | Bring-up & Teleop | Robot online, topics flowing, drive with keyboard |
| B | Real SLAM | Drive around a room, save a real map |
| C | Autonomous Navigation | Send a Nav2 goal, robot navigates the real space |

---

## Project A — Bring-up & Teleop

**Problem:** Get the robot and your laptop talking over ROS2.

**Approach:** ROS2 nodes on different machines discover each other automatically over DDS — as long as they're on the same network and use the same `ROS_DOMAIN_ID`.

![TurtleBot3 Burger hardware diagram](https://emanual.robotis.com/assets/images/platform/turtlebot3/hardware_setup/turtlebot3_burger.png)

### On the TurtleBot3 (SSH in)

```bash
ssh ubuntu@<ROBOT_IP>

# On the robot
source /opt/ros/jazzy/setup.bash
export TURTLEBOT3_MODEL=burger
export ROS_DOMAIN_ID=30  # pick any number 0-101, same on both machines

ros2 launch turtlebot3_bringup robot.launch.py
```

The robot now publishes `/scan`, `/odom`, `/tf`. Leave this running.

### On your laptop

🟢 **Run**

```bash
source /opt/ros/jazzy/setup.bash
export TURTLEBOT3_MODEL=burger
export ROS_DOMAIN_ID=30  # must match the robot

# Verify you can see the robot's topics
ros2 topic list
```

You should see `/scan`, `/odom`, `/cmd_vel`, `/tf`. If you don't, check that both machines are on the same WiFi and `ROS_DOMAIN_ID` matches.

### Drive it

🟢 **Run**

```bash
ros2 run turtlebot3_teleop teleop_keyboard
```

W/A/S/D. You're now sending `Twist` messages from your laptop; the robot executes them.

### Verify sensor data

🟡 **Know**

```bash
# Watch lidar scan data (should update at ~5 Hz)
ros2 topic echo /scan --no-arr  # --no-arr skips the 360-point array

# Check publish rate
ros2 topic hz /scan   # expect ~5 Hz for Burger lidar
ros2 topic hz /odom   # expect ~30 Hz
```

---

## Project B — Real SLAM

**Problem:** Build a map of a real room.

**Approach:** Same SLAM Toolbox launch as ch02. The robot's on-board lidar feeds real scan data instead of simulated.

### Launch SLAM on your laptop

With the robot bringup running on the Pi:

🟢 **Run**

```bash
# Laptop terminal 1
ros2 launch slam_toolbox online_async_launch.py

# Laptop terminal 2
ros2 run rviz2 rviz2
```

In RViz: Add → Map (`/map`), Add → LaserScan (`/scan`), Add → RobotModel.

![SLAM map of a real room being built in RViz](https://emanual.robotis.com/assets/images/platform/turtlebot3/slam/slam_map_real.png)

### Drive and map

🔴 **Work** — map the full room; notice where SLAM struggles compared to simulation

```bash
ros2 run turtlebot3_teleop teleop_keyboard
```

Tips for clean maps:
- Drive slowly (< 0.2 m/s linear, < 0.5 rad/s angular)
- Avoid highly reflective surfaces — lidar bounces off glass
- Cover all areas; unknown cells (grey) mean Nav2 treats them as obstacles

Real-world vs sim differences you'll notice:
- The map has more noise at edges — real lidar isn't perfect
- Odometry drifts faster — floor texture, wheel slip
- Revisiting areas helps SLAM "close the loop" and correct drift

### Save the map

🟢 **Run**

```bash
ros2 run nav2_map_server map_saver_cli -f ~/real_room_map
```

---

## Project C — Autonomous Navigation

**Problem:** Send the robot to a goal in the real room.

**Approach:** Nav2 with the saved map. Identical launch to ch02 — the only change is real sensor data.

### Launch Nav2

🟢 **Run**

```bash
ros2 launch turtlebot3_navigation2 navigation2.launch.py \
  map:=$HOME/real_room_map.yaml
```

Set the 2D Pose Estimate in RViz — click the robot's actual location in the room, drag to set heading. Watch the AMCL particle cloud (pink arrows) converge around the robot.

![Nav2 localizing a TurtleBot on a real room map](https://emanual.robotis.com/assets/images/platform/turtlebot3/navigation/nav2_rviz.png)

### Send a goal from Python

🔴 **Work** — send the robot through a sequence of two waypoints and print the result

```python workspace/ros2/ch03/real_nav_goal.py
# workspace/ros2/ch03/real_nav_goal.py
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator
import rclpy

def make_pose(x: float, y: float, w: float = 1.0) -> PoseStamped:
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.orientation.w = w
    return pose

# 1. Navigator connects to Nav2 action server
def main() -> None:
    rclpy.init()
    nav = BasicNavigator()
    nav.waitUntilNav2Active()  # blocks until Nav2 is ready

    # 2. Waypoints — measure real coordinates from the map in RViz
    #    Click any point in RViz and read the coordinates from the status bar
    waypoints = [
        make_pose(1.0, 0.0),   # first goal
        make_pose(1.0, 1.0),   # second goal
    ]

    # 3. Navigate through all waypoints in sequence
    nav.followWaypoints(waypoints)
    while not nav.isTaskComplete():
        feedback = nav.getFeedback()
        if feedback:
            wp = feedback.current_waypoint
            print(f'Heading to waypoint {wp + 1}/{len(waypoints)}')

    print('Done:', nav.getResult())
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

```bash
python3 real_nav_goal.py
```

Watch the robot plan a path in RViz and execute it. If it stops or re-plans mid-route, the costmap detected an obstacle (person, chair) not in the map — that's Nav2's dynamic obstacle avoidance working.

---

## Self-Check

1. ROS2 nodes on two machines don't see each other. First thing to check? — **Answer:** `ROS_DOMAIN_ID` must be the same on both machines, and they must be on the same network segment.
2. SLAM map has a "tear" — two hallways that should connect appear offset. Why? — **Answer:** Odometry drifted before SLAM could close the loop. Drive back through the area; SLAM Toolbox will correct it when it sees overlapping scan data.
3. `nav.waitUntilNav2Active()` hangs. What's wrong? — **Answer:** Nav2 isn't running or failed to start. Check the Nav2 launch terminal for errors — usually a missing map file or wrong topic remapping.
4. The robot stops 0.3 m short of the goal. Why? — **Answer:** Nav2's goal tolerance is set (default ~0.25 m). You can tighten it in the Nav2 params, but on real hardware some tolerance is wise — odometry isn't perfect.
5. Real SLAM is noisier than sim. What's the main cause? — **Answer:** Real lidar has measurement noise, the floor has texture that causes wheel slip (odometry error), and reflective surfaces cause spurious readings.

---

## Common Mistakes

- **`ROS_DOMAIN_ID` mismatch**: Every terminal, every machine, must export the same value. Make it permanent in `.bashrc`.
- **WiFi latency kills teleop**: If the robot stutters, you're on a congested network. Use a dedicated router or hotspot.
- **Sending a goal before setting initial pose**: AMCL starts with high uncertainty — the robot will plan to the wrong place. Always set 2D Pose Estimate first.
- **Driving too fast during SLAM**: Scan matching fails if the robot moves faster than the lidar update rate. Stay under 0.2 m/s.

---

## Resources

1. [TurtleBot3 Hardware Setup](https://emanual.robotis.com/docs/en/platform/turtlebot3/hardware_setup/) — wiring, SD card flash, network setup
2. [TurtleBot3 SLAM](https://emanual.robotis.com/docs/en/platform/turtlebot3/slam/) — official SLAM walkthrough on real hardware
3. [TurtleBot3 Navigation](https://emanual.robotis.com/docs/en/platform/turtlebot3/navigation/) — Nav2 on real hardware
4. [Nav2 — Navigating with Waypoints](https://navigation.ros.org/tutorials/docs/navigation2_with_waypoint_follower.html) — `followWaypoints` and more
