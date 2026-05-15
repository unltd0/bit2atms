# Chapter 4 — Hardware

**Time:** 1 day (after the robot is in your hands)
**Hardware:** Physical robot
**Prerequisites:** Chapters 1–3

---

## What are we here for

The commands are almost identical to ch02. The difference: real lidar is noisy, the floor isn't flat, and odometry drifts. You'll feel why sim-to-real matters.

By the end you'll have driven a physical TurtleBot, built a map of a real room, and sent it to a goal autonomously — using the same Foxglove layout from ch02.

This is the **SBC archetype** from ch01: a Raspberry Pi on the robot runs the driver nodes; everything else (SLAM, Nav2, Foxglove) runs on your laptop. No MCU/micro-ROS in the loop — the LDS-02 lidar and OpenCR motor controller talk to the Pi over USB serial via vendor packages.

**Skip if you can answer:**
1. Why does real SLAM drift more than sim SLAM?
2. What is `ROS_DOMAIN_ID` and why does it matter on a shared network?
3. Why does AMCL need an initial pose on a real robot but not in sim?

---

## The hardware

The cheapest path is a **pre-assembled TurtleBot3 Burger** from ROBOTIS or a reseller (~$650). What's in the box:

| Component | Role |
|---|---|
| Raspberry Pi 4 (4GB recommended) | SBC — runs Ubuntu 24.04 + ROS2 Jazzy + driver nodes |
| OpenCR 1.0 | Motor controller, IMU, USB-serial to Pi |
| 2× Dynamixel XL430-W250 | Wheel motors with encoders |
| LDS-02 lidar | 360° 2D scan, ~5 Hz, 12cm–3.5m range |
| 11.1V LiPo + charger | ~2 hours runtime |
| Aluminum chassis + caster | The body |

A from-scratch DIY mobile robot (chassis design, motor selection, encoder wiring, MCU firmware) is a different course — out of scope here.

**SD card flash.** ROBOTIS doesn't publish a pre-built Jazzy SD-card image — you flash plain Ubuntu and install ROS2 yourself. Follow [TurtleBot3 SBC Setup](https://emanual.robotis.com/docs/en/platform/turtlebot3/sbc_setup/). The short version:

1. Flash **Ubuntu Server 24.04 (64-bit)** to a 32GB+ SD card with [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
2. Boot the Pi, connect to WiFi via `nmtui` (over monitor+keyboard, or via the Imager's preconfig screen).
3. SSH in. Install ROS2 Jazzy following the [Jazzy Ubuntu install](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html) — `sudo apt install ros-jazzy-ros-base` is enough on the robot (no `desktop` needed since there's no display).
4. Install the TurtleBot3 packages: `sudo apt install ros-jazzy-turtlebot3* ros-jazzy-dynamixel-sdk ros-jazzy-hls-lfcd-lds-driver` (debs available for arm64 since May 2025).
5. Note the robot's IP (`hostname -I`).

**OpenCR firmware.** Once the Pi is up, flash the OpenCR firmware so it speaks to the bringup node — script and Jazzy-specific firmware path in [OpenCR Setup](https://emanual.robotis.com/docs/en/platform/turtlebot3/opencr_setup/).

---

## Projects

| # | Project | What you build |
|---|---------|----------------|
| A | Bring-up & teleop | Robot online, topics flowing on the laptop, drive with keyboard |
| B | Real SLAM | Drive around a room, save a real map |
| C | Autonomous navigation | Send a Nav2 goal, robot navigates the real space |

---

## Setup

**Network.** Robot and laptop on the same WiFi (or same Ethernet switch). On corporate, hotel, or guest networks, multicast may be blocked — DDS discovery silently fails. If `ros2 topic list` shows nothing on the laptop, try a phone hotspot to confirm the network is the problem.

**`ROS_DOMAIN_ID`.** ROS2 discovery is partitioned by domain ID. Both machines must `export ROS_DOMAIN_ID=<same number>` — pick anything 0–101 (above ~101 collides with ephemeral ports on Linux). Set it in `.bashrc` on both machines so you don't forget.

**Laptop (Mac/Linux/Windows).** Same `bit2atms-ros2` Docker container as ch02 (Jazzy). No image rebuild needed. Foxglove on the host machine connects the same way (`ws://localhost:8765`).

**Foxglove layout.** Reuse `resources/ros2/foxglove/ch02_layout_v3.json` from your local clone — same panels (3D + cmd_vel + odom plots), same publish bindings. The green ground-truth arrow won't appear (no Gazebo PosePublisher on real hardware), but everything else works.

### Terminal plan

| Terminal | Where | Use |
|---|---|---|
| R1 | SSH to Pi | `turtlebot3_bringup` (long-running) |
| T1 | Laptop container | `foxglove_bridge` (long-running) |
| T2 | Laptop container | SLAM Toolbox / Nav2 |
| T3 | Laptop container | Teleop / map save / Python scripts |

---

## Project A — Bring-up & teleop

**Problem:** Get the robot and your laptop talking over ROS2.
**Approach:** ROS2 nodes on different machines auto-discover over DDS as long as they're on the same network with the same `ROS_DOMAIN_ID`.

![TurtleBot3 Burger hardware diagram](https://emanual.robotis.com/assets/images/platform/turtlebot3/hardware_setup/turtlebot3_burger.png)

### 1. Start bringup on the robot

🟢 **Run** — R1, leave running

```bash
ssh ubuntu@<ROBOT_IP>

source /opt/ros/jazzy/setup.bash
export TURTLEBOT3_MODEL=burger
export ROS_DOMAIN_ID=30

ros2 launch turtlebot3_bringup robot.launch.py
```

The Pi now publishes `/scan`, `/odom`, `/tf`, and subscribes to `/cmd_vel`. Leave this running for the rest of the chapter.

### 2. Verify the laptop sees the robot

🟢 **Run** — T3 (laptop container)

```bash
export TURTLEBOT3_MODEL=burger
export ROS_DOMAIN_ID=30

ros2 topic list
ros2 topic hz /scan   # expect ~5 Hz on Burger LDS-02
ros2 topic hz /odom   # expect ~30 Hz
```

You should see `/scan`, `/odom`, `/cmd_vel`, `/tf`. If the list is empty: same `ROS_DOMAIN_ID` on both sides, same network, multicast not blocked.

### 3. Drive it

🟢 **Run** — T3

```bash
ros2 run turtlebot3_teleop teleop_keyboard
```

`W`/`X` adjusts forward speed, `A`/`D` turns, `S` stops. The terminal must have keyboard focus.

### 4. Connect Foxglove

🟢 **Run** — T1 (laptop container)

```bash
ros2 launch foxglove_bridge foxglove_bridge_launch.xml port:=8765
```

On your laptop: open Foxglove → **Open connection** → `ws://localhost:8765` → import `ch02_layout_v3.json` (same file as ch02).

Drive again — the robot model moves in the 3D panel, red lidar dots track real walls.

---

## Project B — Real SLAM

**Problem:** Build a map of a real room.
**Approach:** Same SLAM Toolbox launch as ch02. The lidar is real; everything else is identical.

### 1. Launch SLAM

Bringup (R1) and foxglove_bridge (T1) still running.

🟢 **Run** — T2

```bash
ros2 launch slam_toolbox online_async_launch.py
```

(Note the absence of `use_sim_time:=true` — on real hardware the system clock is the right clock.) Within seconds the map appears in Foxglove.

![Real-world SLAM map building in a robot visualizer](https://emanual.robotis.com/assets/images/platform/turtlebot3/slam/slam_map_real.png)

### 2. Drive and map

🔴 **Work** — map the full room; notice where SLAM struggles compared to sim.

```bash
ros2 run turtlebot3_teleop teleop_keyboard
```

Tips:
- **Slow.** < 0.15 m/s linear, < 0.4 rad/s angular. Scan matching fails if the robot moves faster than the lidar update rate (~5 Hz on Burger).
- **Avoid glass and mirrors.** Lidar bounces unpredictably.
- **Cover everything.** Unknown cells (grey) become obstacles for Nav2.
- **Revisit.** Driving through an area twice helps SLAM "close the loop" and correct accumulated drift.

What you'll see vs sim:
- More noise at edges — real lidar has measurement variance.
- Faster odometry drift — wheel slip on real flooring is much worse than the sim's perfect contact model.
- Loop closure visibly *snaps* the map when SLAM Toolbox recognizes a revisit and corrects.

### 3. Save the map

🟢 **Run** — T3

```bash
ros2 run nav2_map_server map_saver_cli -f ~/real_room_map
```

Produces `real_room_map.pgm` and `real_room_map.yaml`. Stop SLAM (Ctrl+C T2).

---

## Project C — Autonomous navigation

**Problem:** Send the robot to a goal in the real room.
**Approach:** Nav2 + AMCL with the saved map, same as ch02 Project C.

### 1. Launch Nav2

🟢 **Run** — T2

```bash
ros2 launch turtlebot3_navigation2 navigation2.launch.py \
  map:=$HOME/real_room_map.yaml
```

Wait for `Managed nodes are active`. AMCL is now running but uncertain — the particle cloud will be spread out across the map.

### 2. Seed the initial pose in Foxglove

In Foxglove's 3D panel, right-click the publish icon (arrow/hand, bottom of the right toolbar) → **Publish 2D pose estimate (/initialpose)**. Then:

1. **Click** the robot's actual physical position on the map. A magenta arrow anchors there.
2. **Move the cursor** in the direction the robot is currently facing. The arrow's tip follows.
3. **Click again** to publish.

The AMCL particle cloud collapses around the click point. If it's wildly wrong, click again — re-publishing replaces the previous estimate.

> **Knowing the actual position.** Stand the robot in a recognizable spot before launching Nav2 (a corner, against a wall) so you can confidently click that location on the map.

### 3. Send a goal from Foxglove

Right-click the publish icon → **Publish 2D pose (/goal_pose)**. Same gesture as step 2: click position, move cursor for heading, click again.

> The click must land on the **white interior** of the map. Goals in grey (unknown) or black (obstacle) cells are silently rejected by the planner.

The robot drives to the **base** of the magenta arrow (position), facing the **tip** direction (heading).

### 4. Send a goal from Python

🔴 **Work** — send the robot through two waypoints. Edit the coordinates to fit your map.

```python+collapsed resources/ros2/ch04/real_nav_goal.py
```

To find real coordinates: hover over points on the white interior in Foxglove's 3D panel — the bottom-right of the panel shows `(x, y)` in the map frame. Pick two reachable points and drop them into `waypoints`.

```bash
python3 /workspace/ros2/ch03/real_nav_goal.py
```

Watch the planned path appear in Foxglove and the robot execute it. If it stops or re-plans mid-route, the costmap detected an obstacle (person, chair) not in the map — that's Nav2's dynamic obstacle avoidance.

---

## Self-Check

1. ROS2 nodes on two machines don't see each other. First thing to check? — **Answer:** `ROS_DOMAIN_ID` matches on both, same network segment, multicast not blocked. Try `ros2 multicast receive` on one machine and `ros2 multicast send` on the other to isolate the network from the ROS2 config.
2. SLAM map has a "tear" — two hallways that should connect appear offset. Why? — **Answer:** Odometry drifted before SLAM closed the loop. Drive back through the area; SLAM Toolbox corrects it on overlapping scan data.
3. `nav.waitUntilNav2Active()` hangs forever. What's wrong? — **Answer:** Nav2 isn't running, or its lifecycle nodes haven't activated. Check the Nav2 launch terminal — usually a missing map file path or a transform not yet published.
4. The robot stops short of the goal. Why? — **Answer:** Goal tolerance — Nav2 controllers consider the goal reached within a few tens of cm (the exact value depends on the controller plugin). On real hardware some tolerance is necessary because odometry isn't perfect.
5. What's the main reason real SLAM is noisier than sim? — **Answer:** Real lidar has measurement noise, real floors cause wheel slip (odometry error), and reflective surfaces produce spurious returns. Sim has none of these by default.

---

## Common Mistakes

- **`ROS_DOMAIN_ID` mismatch**: Every shell, every machine, must export the same value. Put it in `.bashrc` on both sides.
- **WiFi blocks multicast**: Common on corporate/hotel networks. If discovery fails, try a phone hotspot before debugging ROS.
- **Sending a goal before AMCL converges**: The robot plans to where it *thinks* it is, which may not match reality. Always seed `/initialpose` first and watch the particle cloud collapse.
- **Driving too fast during SLAM**: Scan matching fails when the robot outruns the 5 Hz lidar. Stay under 0.15 m/s.
- **Goal click outside the map**: Foxglove publishes anyway, Nav2 silently drops it. Click on the white interior.

---

## Resources

1. [TurtleBot3 SBC Setup](https://emanual.robotis.com/docs/en/platform/turtlebot3/sbc_setup/) — flash the SD card, boot the Pi
2. [TurtleBot3 OpenCR Setup](https://emanual.robotis.com/docs/en/platform/turtlebot3/opencr_setup/) — flash the OpenCR firmware
3. [TurtleBot3 Bring-up](https://emanual.robotis.com/docs/en/platform/turtlebot3/bringup/) — official walkthrough for the on-robot launch
4. [TurtleBot3 SLAM (real)](https://emanual.robotis.com/docs/en/platform/turtlebot3/slam/) — official SLAM walkthrough on hardware
5. [TurtleBot3 Navigation (real)](https://emanual.robotis.com/docs/en/platform/turtlebot3/navigation/) — Nav2 on hardware
6. [Nav2 — Waypoint Following](https://navigation.ros.org/tutorials/docs/navigation2_with_waypoint_follower.html) — `followWaypoints` and friends
7. [ROS_DOMAIN_ID](https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Domain-ID.html) — why the safe range is 0–101
