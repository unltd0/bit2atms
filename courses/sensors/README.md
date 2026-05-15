# Sensors

**Time:** Half a day
**Hardware:** Laptop only
**Prerequisites:** ROS2 course [ch01](../ros2/ch01_fundamentals/README.md) and [ch02](../ros2/ch02_simulation/README.md). You should already be comfortable with ROS2 topics, message types, the TF (transform) tree, QoS (Quality of Service) profiles, and the `sensor_msgs` package.

---

Tesla ships cars with 8 cameras and no LiDAR. Waymo's self-driving taxis carry 5 LiDARs and 29 cameras. Both ship to paying customers. The reason isn't that one of them is wrong — it's that every sensor fails in its own way, and the right stack depends on which failures you can tolerate.

This course is a tour of the sensors a robot actually uses. For each family — cameras, LiDAR, radar, IMU, GPS, proximity, audio — you get a structured reference: **what it senses, what it emits, how to integrate it, and what to watch out for**. Not a textbook. Not a product catalog. A map of the territory.

---

## What you'll get out of this

After reading, you should be able to:

- Read a sensor datasheet without your eyes glazing over
- Pick a sensor for a robot you're designing — and defend the choice
- Recognize a sensor's failure mode in the wild before it costs you a week of debugging
- Know what ROS2 driver package and message type to look for when adding a new sensor

You will **not** become an expert in any one sensor. That's what the linked datasheets, papers, and teardowns are for.

---

## Course map

| # | Chapter | Covers |
|---|---|---|
| 01 | [Cameras — 2D & Depth](ch01_cameras/README.md) | RGB cameras, depth cameras (stereo, time-of-flight, structured light), plus event and thermal cameras |
| 02 | [LiDAR & Radar](ch02_lidar_radar/README.md) | LiDAR (spinning, solid-state, and FMCW — frequency-modulated continuous-wave); millimeter-wave (mmWave) radar |
| 03 | [IMU, GNSS & Wheel Odometry](ch03_imu_gnss_odom/README.md) | The dead-reckoning trio — each drifts differently, so they fuse well |
| 04 | [Proximity & Contact](ch04_proximity_contact/README.md) | Ultrasonic, IR ToF, bumpers, force-torque, tactile |
| 05 | [Audio](ch05_audio/README.md) | Single mics, mic arrays, direction-of-arrival, beamforming |
| 06 | [More sensors worth knowing](ch06_more_sensors/README.md) | Environmental, battery, hall, RFID, fiducials, UWB — the discovery list |

---

## How each chapter is structured

Each sensor in a chapter gets the same block:

- **What it does** — 1–2 sentences
- **Senses** — the physical quantity it picks up
- **Input** — power, trigger, config
- **Output** — the data shape that comes out
- **Integration** — physical interface, ROS2 driver + message type, and non-ROS SDK (Software Development Kit) options
- **Limitations to watch out for** — failure modes that bite in the field
- **Why & how it works** — *only* where the physics changes how you use it
- **Representative products** — 3–6 examples across hobby / prosumer / industrial, with prices and links

Each chapter ends with a short *"how to choose"* decision guide and a *"going deeper"* list of vendor pages, datasheets, and one or two teardown videos.

---

## What this course is not

- **Not a product catalog.** Three to six examples per sensor, not a hundred. Pricing dates rot; the date stamps tell you when they were last verified.
- **Not a physics textbook.** Equations only when they pay off. Most of the time the takeaway is *"it works, here's what comes out, here's what breaks it."*
- **Not a ROS2 tutorial.** That's the [ROS2 course](../ros2/README.md). This one assumes you already know what a topic is.
- **Not about actuators.** Motors, encoders, servos, and drivers belong in a separate course (TBD). This one is purely sensors.

---

## Start here

→ [Chapter 01 — Cameras](ch01_cameras/README.md)
