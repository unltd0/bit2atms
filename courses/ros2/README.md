# ROS2 — Getting a Hang

**Time:** 2–3 days total
**Hardware:** Laptop only (ch01–ch02) · Physical robot (ch03)
**Prerequisites:** Python, comfort with the terminal

---

## What this course is

Three chapters. After them, ROS2 should feel like something you know — not a mystery. You'll have run real nodes, built a map in simulation, and driven a real robot autonomously.

This is not a reference manual. You won't cover everything. You'll touch the parts that matter and have enough context to go deeper when you need to.

---

## Chapter arc

| Ch | Title | What you do |
|----|-------|-------------|
| 01 | Fundamentals | Install ROS2, write nodes, use topics/services, write a launch file |
| 02 | Simulation | Spawn a robot in Gazebo, run SLAM, send autonomous Nav2 goals |
| 03 | Hardware | Bring up a real TurtleBot, SLAM with real lidar, navigate autonomously |

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
- Real robot experience — same commands, real sensors
- Enough vocabulary to read ROS2 docs and know what to look for
