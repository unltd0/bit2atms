# ROS2 — Getting a Hang

**Time:** 3–4 days total
**Hardware:** Laptop only (ch01–ch03) · Physical robot (ch04)
**Prerequisites:** Python, comfort with the terminal

---

## What this course is

Four chapters. After them, ROS2 should feel like something you know — not a mystery. You'll have written real nodes, driven a simulated robot, modelled your own robot from scratch, and driven a real TurtleBot autonomously.

This is not a reference manual. You won't cover everything. You'll touch the parts that matter and have enough context to go deeper when you need to.

---

## Chapter arc

| Ch | Title | What you do |
|----|-------|-------------|
| 01 | Fundamentals | Install ROS2, write nodes, use topics/services, write a launch file |
| 02 | Simulation | Spawn a TurtleBot in Gazebo, run SLAM, send autonomous Nav2 goals |
| 03 | Build your own robot | Author a URDF for a tiny Arduino-style car, simulate it in Gazebo, then trace exactly what swaps when you wire the real Arduino |
| 04 | Hardware | Bring up a real TurtleBot, SLAM with real lidar, navigate autonomously |

---

## Setup

**Mac (recommended path):** Docker Desktop. All chapters include the exact `docker run` command.

**Linux:** Native ROS2 Jazzy install. Faster, no overhead.

```bash
# Verify your install works (after ch01 setup)
ros2 run demo_nodes_py talker
```

---

## What you'll walk away with

- Mental model of ROS2: nodes, topics, services, TF, launch files
- Hands-on feel for the Nav2 stack and SLAM
- Ability to describe a new robot to ROS2 (URDF / xacro) and stand up a Gazebo sim for it
- Clarity on what swaps between sim and real, and what ships unchanged across the gap
- Real robot experience — same commands, real sensors
- Enough vocabulary to read ROS2 docs and know what to look for
