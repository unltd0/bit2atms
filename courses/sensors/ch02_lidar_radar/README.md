# Chapter 02 — LiDAR & Radar

**Time:** ~25 min
**Hardware:** Laptop only
**Prerequisites:** ROS2 course ch01–ch02

---

A $100 RPLidar and an $80,000 Velodyne both measure distance by timing a reflected pulse. The 800× price gap is almost entirely about how many pulses per second, how precisely you can time them, and how well the device behaves when it rains.

LiDAR fires light, radar fires radio waves. Both time the bounce, divide by twice the speed of the wave, and call the result distance. Light has a very short wavelength (≈905 nm typical for LiDAR), so you can tell two nearby objects apart by direction (good *angular resolution*) — but the beam is easily blocked by dust, rain, and fog. Radio waves are millimeter-to-centimeter wavelength (24–81 GHz for automotive radar), so they punch through weather but blur small objects together.

![LiDAR / time-of-flight principle — Wikimedia Commons (CC0)](assets/tof_principle.svg)

Everything below is variations on this theme — how many lasers, mechanical vs solid-state scanning, pulsed vs frequency-modulated continuous-wave (FMCW), 2D vs 3D.

---

## 2D Spinning LiDAR

Spins a single laser horizontally and returns a 360° slice of (angle, distance) pairs at 5–15 Hz. Outputs `sensor_msgs/LaserScan`. Drivers: `rplidar_ros` / `sllidar_ros2` for Slamtec, `urg_node2` for Hokuyo.

Cheap units use *laser triangulation* (measure the angle at which the reflection lands on a small internal sensor) — accurate only out to ~6 m. ToF (time-of-flight) units hold accuracy to 25–30 m but cost 3–4× more.

**Limitations.**
- **Sunlight** saturates the IR detector; outdoor performance drops sharply.
- **Mirrors, dark matte surfaces, and glass** all fail differently — mirrors return weird angles, black foam absorbs the pulse, glass is invisible.
- **2D only.** Anything above or below the scan plane doesn't exist — stairs, tables, low cables are invisible.

**Representative products.**

![Slamtec RPLIDAR A1 — Adafruit](assets/products/slamtec_rplidar_a1.jpg) ![Hokuyo UST-10LX — Hokuyo USA](assets/products/hokuyo_ust10lx.jpg)

| Product | Tier | Method | Range | Price (USD) | Pick when |
|---|---|---|---|---|---|
| [Slamtec RPLidar A1](https://www.slamtec.com/en/lidar/a1) | Hobby | Triangulation | 12 m | ~$99 | 2D SLAM on a $300 robot, don't care about >6 m accuracy |
| [Slamtec RPLidar A2M12](https://www.slamtec.com/en/lidar/a2) | Hobby+ | Triangulation | 12 m | ~$229 | A1 but quieter, thinner |
| [Slamtec RPLidar S2](https://www.slamtec.com/en/s2) | Prosumer | ToF | 30 m | ~$399 | Indoor + outdoor mixed, IP65, dark-surface detection |
| [Hokuyo URG-04LX](https://www.hokuyo-aut.jp/) | Prosumer | ToF | 4 m | ~$1,200 | Lab-grade reliability for indoor research robots |
| [Hokuyo UST-10LX](https://www.hokuyo-usa.com/products/lidar-obstacle-detection/ust-10lx) | Industrial | ToF | 10 m / 20 m | ~$2,000 | AGV (Automated Guided Vehicle) or AMR (Autonomous Mobile Robot) with safety requirements; 270° field of view (FoV), 0.25° angular resolution |

*Prices verified May 2026 from Slamtec, DFRobot, Hokuyo, and ROS Components.*

---

## 3D Spinning LiDAR

Stacks 16–128 lasers vertically and spins them, producing a full 3D point cloud 10–20× per second — millions of points per second. Outputs `sensor_msgs/PointCloud2` over Ethernet. Drivers: `velodyne_driver`, `ouster-ros`, `livox_ros_driver2`.

Each point carries (x, y, z, intensity, ring, timestamp) — *intensity* is return strength, *ring* tells you which of the stacked laser channels fired it.

**Limitations.**
- **Cost.** Cheapest 3D units start ~$1k; automotive units run $5k–$80k+.
- **Rain, snow, fog, dust.** Light scatters off airborne particles, filling the cloud with phantom returns.
- **Dark surfaces** (black cars, dark asphalt) return weakly — dropouts at long range.
- **Mechanical wear.** The spinning unit has bearings; lifetime is years of continuous operation, not decades.
- **Vertical field of view is narrow** (15°–90°). Don't expect to see the sky.
- **Motion compensation.** At speed, the robot moves during one revolution and the cloud comes out skewed unless you feed the driver odometry / IMU data. Otherwise your [SLAM](../ch01_cameras/README.md) map wobbles.

**Representative products.**

![Livox Mid-360 — Livox](assets/products/livox_mid360.jpg) ![Ouster OS family — Ouster](assets/products/ouster_os1.png) ![Velodyne VLP-16 — Ouster](assets/products/velodyne_vlp16.jpg)

| Product | Tier | Channels | Range | Price (USD) | Pick when |
|---|---|---|---|---|---|
| [Livox Mid-360](https://www.livoxtech.com/mid-360) | Prosumer | Hybrid solid-state, 360° H × 59° V | 40 m | ~$1,000 | 3D on a hobbyist budget, don't need highest density |
| [Ouster OS0](https://ouster.com/products/hardware/os0-lidar-sensor) | Industrial | 32–128 | 35 m, 90° V FoV | ~$8k–$15k | Indoor AMRs, low-speed AVs needing wide vertical FoV |
| [Ouster OS1](https://ouster.com/products/hardware/os1-lidar-sensor) | Industrial | 32–128 | 120–200 m | ~$10k–$24k | Workhorse for outdoor robots, mapping, security |
| [Velodyne VLP-16 (Puck)](https://ouster.com/products/hardware/vlp-16) | Industrial (legacy) | 16 | 100 m | ~$4k used / $8k new | Maintaining an existing stack; new builds use Ouster/Livox |
| [Hesai Pandar / AT128](https://www.hesaitech.com/) | Automotive | 128 | 200 m+ | ~$5k–$20k | AV development at scale |

*Prices verified May 2026. 3D LiDAR pricing varies wildly by channel count, distributor, and volume — these are order-of-magnitude.*

---

## Solid-State LiDAR

Same job as spinning LiDAR, but with no moving parts — the beam is steered electronically (MEMS mirrors, optical phased arrays, or flash illumination depending on vendor). Outputs `sensor_msgs/PointCloud2`.

Most are forward-facing only (120° or so) — full 360° means stitching multiple units. Not automatically cheaper than spinning; volume drives price more than the physics. Newer category, so the ROS2 driver ecosystem is thinner.

Pick when you can't tolerate a spinning mechanism — drones with tight weight budgets, automotive integration, or anywhere bearings would fail.

---

## FMCW LiDAR

Transmits a continuous laser whose frequency ramps up and down instead of pulsing. The frequency shift of the reflected light gives **distance and velocity per point simultaneously** via the Doppler effect (same effect you hear when an ambulance siren passes — higher pitch coming toward you, lower moving away).

Bleeding edge — few products, $10k+, mostly automotive (Aeva, Aurora). Per-point velocity is the killer feature for highway driving; for most robotics work, pulsed time-of-flight is the right answer.

---

## Radar (mmWave / FMCW radar)

Same FMCW trick as FMCW LiDAR, but with radio waves (typically 60 GHz or 76–81 GHz) instead of light. Returns distance, velocity, and angle per detected target.

![FMCW chirp pattern — frequency vs time](assets/fmcw_chirp.svg)

Drivers: `ti_mmwave_rospkg` for TI chips. The ROS2 ecosystem is thinner than for LiDAR.

**Limitations.**
- **Poor angular resolution.** A typical automotive mmWave radar says "a thing is at 50 m, moving 20 m/s, somewhere in this 5° cone." Much fuzzier than LiDAR.
- **Multipath and clutter.** Radio bounces off everything — ground, walls, chain-link fences swamp the target you care about.
- **Doppler-only filtering throws away stationary objects.** A real Tesla-failure-mode for years; modern radars track stationary too but it costs processing.
- **Cross-interference** — many radars in the same space blind each other. A growing problem in automotive.

**Representative products.**

| Product | Tier | Frequency | Output | Price (USD) | Pick when |
|---|---|---|---|---|---|
| [TI IWR6843ISK](https://www.ti.com/tool/IWR6843ISK) | Dev kit | 60 GHz | Tracked objects via UART | ~$200 | Prototyping indoor presence/gesture/proximity radar |
| [TI AWR1843BOOST](https://www.ti.com/tool/AWR1843BOOST) | Dev kit | 77 GHz | Tracked objects + raw data | ~$350 | Automotive-band experiments, longer range |
| [Infineon BGT60TR13C (Position2Go)](https://www.infineon.com/) | Dev kit | 60 GHz | Doppler, presence | ~$200 | Compact integration, gesture-style apps |
| [Continental ARS548](https://www.continental.com/) | Automotive | 77 GHz | Full radar cube on CAN/Ethernet | ~$1k–$2k+ | Production automotive, ADAS development |
| [Smartmicro UMRR-96](https://www.smartmicro.com/) | Automotive | 79 GHz | Object list | ~$2k+ | High-resolution automotive radar |

*Prices verified May 2026. Radar pricing varies by region and volume — automotive units rarely have public pricing.*

---

## LiDAR + camera fusion

LiDAR knows *where* an obstacle is to centimeter accuracy. A camera knows *what* it is. Every automotive stack uses both: project LiDAR points into the camera image, run object detection in the image, assign points falling inside a detection box to that object.

The hard part is time-syncing the two streams and calibrating the geometric relationship between them. If the camera frame and LiDAR sweep are off by 50 ms at 20 m/s, every detection is off by a meter.

---

## Going Deeper

- [Slamtec RPLidar product line](https://www.slamtec.com/en/lidar) — datasheets for A1/A2/C1/S2/S2L/S3
- [Ouster OS family overview](https://ouster.com/os-overview)
- [Livox Mid-360 specs](https://www.livoxtech.com/mid-360/specs)
- [Hokuyo industrial 2D LiDARs](https://www.hokuyo-aut.jp/)
- [TI mmWave radar SDK](https://www.ti.com/tool/MMWAVE-SDK)
- [Radar Tutorial — FMCW basics](https://www.radartutorial.eu/02.basics/Frequency%20Modulated%20Continuous%20Wave%20Radar.en.html)
- [Why is chirp used in radar?](https://resources.system-analysis.cadence.com/blog/why-is-chirp-used-in-radar)
- [Mainstreet Autonomy — All about automotive lidar (2025)](https://mainstreetautonomy.com/blog/2025-08-29-all-about-automotive-lidar/) — the best single overview of automotive LiDAR trade-offs

https://www.youtube.com/watch?v=EYbhNSUnIdU

(Above: Real Engineering — "How LiDAR works", great primer on the physics)
