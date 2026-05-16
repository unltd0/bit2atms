# Chapter 04 — Proximity & Contact

**Time:** ~20 min
**Hardware:** Laptop only
**Prerequisites:** ROS2 course ch01–ch02

---

The iRobot Roomba navigates a house using mostly bump switches and IR cliff detectors. Tens of millions of them are sold. You don't always need a LiDAR — sometimes you just need to know "did I hit something" or "is something within arm's reach."

This chapter covers the *close-range* family: sensors that work within a couple of meters, often within a few centimeters. They're cheap, simple, and they fill the gaps that depth cameras and LiDAR leave behind — especially for safety, grasping, and contact.

---

## Ultrasonic distance sensor

Emits a short burst of ultrasound (~40 kHz), times the echo, returns a single distance reading (0.02–4 m typical, up to 20 Hz). Wired via two GPIO pins on the host — one sends a 10 μs trigger, the other receives an echo whose pulse-width is proportional to distance (~58 μs/cm). Outputs `sensor_msgs/Range`.

**Limitations.**
- **Wide cone (~15–30°), no angular resolution.** Tells you *something* is in front, not where. Two objects in the cone → reading is the nearer one.
- **Soft surfaces** (curtains, foam) absorb sound and return nothing.
- **Glancing angles miss** — a flat wall at a steep angle reflects sound away.
- **Blind zone <2 cm** — the echo arrives before the speaker stops vibrating.
- **Multiple sensors interfere** — two HC-SR04s firing at once hear each other. Schedule them.

**Representative products.**

![SparkFun HC-SR04 — SparkFun](assets/products/sparkfun_hcsr04.jpg)

| Product | Tier | Range | Price (USD) | Pick when |
|---|---|---|---|---|
| [HC-SR04](https://www.sparkfun.com/ultrasonic-distance-sensor-hc-sr04.html) | Hobby | 0.02–4 m | ~$4 | Cheapest possible "did I hit a wall" sensor |
| [MaxBotix MB7389](https://maxbotix.com/) | Prosumer | 0.3–7.65 m | ~$100 | Outdoor use, weatherproof |
| [SRF08 / SRF10](https://www.robot-electronics.co.uk/) | Hobby+ | 0.03–6 m | ~$30 | I2C, on-board temperature comp, cleaner data |

*Prices verified May 2026.*

---

## IR time-of-flight distance sensor

Same idea as ultrasonic, but with an infrared laser pulse instead of sound. Much faster, narrower beam, higher accuracy at short range. Distance in millimeters at 10–100 Hz over I2C. Outputs `sensor_msgs/Range`. Newer multi-zone variants (VL53L5CX) return an 8×8 grid of distances — a tiny depth image — as `sensor_msgs/Image`.

**Limitations.**
- **Outdoor performance limited.** Direct sunlight reduces range; fine in shade.
- **Dark / matte surfaces** absorb the laser pulse — reduced range.
- **Range cap ~4 m** — past that, you're in 2D LiDAR territory.

**Representative products.**

![ST VL53L1X breakout — Adafruit](assets/products/st_vl53l1x.jpg)

| Product | Tier | Range | Beam | Price (USD) | Pick when |
|---|---|---|---|---|---|
| [Sharp GP2Y0A21](https://global.sharp/products/device/lineup/selection/opto/haca/index.html) | Hobby (analog) | 0.1–0.8 m | Narrow | ~$10 | Cheap analog distance; legacy hobby projects |
| [ST VL53L0X](https://www.adafruit.com/product/3317) | Hobby | 0.03–1 m | Narrow | ~$15 (breakout) | Tiny package, I2C |
| [ST VL53L1X](https://www.adafruit.com/product/3967) | Hobby+ | 0.03–4 m | Narrow | ~$15 (breakout) | Longer range, programmable region-of-interest |
| [ST VL53L5CX](https://www.pololu.com/product/3417) | Prosumer | 0.02–4 m | 8×8 grid | ~$25 (breakout) | "Mini depth camera" for cheap |
| [Garmin LIDAR-Lite v3HP](https://www.garmin.com/en-US/p/557294) | Prosumer | 0.05–40 m | Narrow | ~$140 | Long-range pinpoint distance, drone altimetry |

*Prices verified May 2026.*

---

## Bump switches and contact sensors

A mechanical switch closes when something hits it — one digital GPIO pin per switch, binary on/off. The cheapest, fastest, most reliable obstacle sensor in robotics. The Roomba's whole worldview.

**Limitations.**
- **Bouncing.** Mechanical switches chatter for a few ms on contact. *Debounce* — ignore changes for the first 10–20 ms after each transition.
- **Binary only.** Yes/no, no force value.
- **Coverage gaps.** A switch only detects contact at the switch itself. Most robots use a *skirt* with multiple switches.

---

## Force-torque sensors (F/T)

Reads forces and torques along all 6 axes (3 linear + 3 rotational) — six floats (Fx, Fy, Fz, Tx, Ty, Tz) at 100–1000 Hz. Used at robot wrists and on grippers. Outputs `geometry_msgs/WrenchStamped`. Drivers: `ati_force_torque_sensor_driver`, `robotiq_ft_sensor`.

Under the hood: tiny metal beams (*flexures*) bend under load; *strain gauges* (resistors that change resistance when stretched) measure the bending.

**Limitations.**
- **Cost.** Real F/T sensors start at ~$2,000 and go to $15,000+. There is no $50 version that works.
- **Temperature drift.** Re-zero periodically.
- **Crosstalk.** Force along one axis bleeds into reported torques on other axes. Calibration matrices help.
- **Overload damages** the flexures permanently. Always pick a unit with headroom.
- **Hard to detect <0.1 N reliably** — sensor noise dominates.

### Cheap alternative: motor-current sensing

A common substitute on smart actuators (Dynamixel servos, ODrive) is to estimate torque from motor current: current × motor's torque constant ≈ output torque. Much noisier than a real F/T sensor, ignores friction and inertia, but free if you already have the servo.

**Representative products.**

| Product | Tier | Range | Accuracy | Price (USD) | Pick when |
|---|---|---|---|---|---|
| [Robotiq FT 300-S](https://robotiq.com/products/ft-300-force-torque-sensor) | Cobot (collaborative robot) integration | ±300 N | ~0.5% of full scale | ~$3,000–$5,000 | Universal Robots / collaborative-robot cell, plug-and-play |
| [ATI Mini40 / Nano17](https://www.ati-ia.com/products/ft/) | Research | ±40 N / ±17 N | High | ~$5,000–$10,000 | Research-grade precision, small form factor |
| [Bota Systems Medusa](https://www.botasys.com/) | Research | ±100–500 N | High | ~$3,000–$6,000 | Lightweight, modern alternative to ATI |
| Motor current sensing | Hobby/cheap | varies | very rough | "free" with servo | Hobby manipulation, cost-sensitive grippers |

*Prices verified May 2026; F/T sensor pricing rarely public — figures are typical quotes.*

---

## Tactile sensors

Reads contact distribution across a surface — like skin. Some types also read *shear* (sliding) forces. Output is a 2D pressure map; optical tactile sensors additionally see surface texture and slip. Different vendors, different message types — no universal standard.

Tech varies: optical (a camera looking at a deformable gel), capacitive (electrode arrays), piezoresistive (pressure-sensitive ink), MEMS.

**Limitations.**
- **Bulky** — GelSight Mini is a fingertip plus a small camera. Doesn't fit everywhere.
- **Wear.** Gel surfaces scratch and degrade; replacement parts cost real money.
- **Data hard to use.** A 320×240 tactile image is huge; most code wants summary stats (contact area, centroid, normal force).
- **Sim-to-real gap.** Tactile simulation is much less mature than visual or LiDAR.

**Representative products.**

![GelSight Mini — GelSight](assets/products/gelsight_mini.png)

| Product | Tier | Tech | Output | Price (USD) | Pick when |
|---|---|---|---|---|---|
| [GelSight Mini](https://www.gelsight.com/gelsightmini/) | Research | Optical (camera + gel) | Tactile image | ~$500 | Out-of-the-box optical tactile for grasping research |
| [Meta DIGIT](https://www.gelsight.com/product/digit-tactile-sensor/) | Research / open | Optical (open-source) | Tactile image | ~$300 (DIY) | Open hardware, research-friendly |
| [BioTac (Syntouch)](https://www.syntouchinc.com/) | Research (legacy) | Capacitive + thermal + vibration | Multi-modal | ~$3,000+ | Discontinued but ubiquitous in older grasping papers |
| Resistive pressure mats (e.g., Velostat) | Hobby | Piezoresistive | Pressure array | <$50 DIY | Cheap pressure mapping for prototypes |

*Prices verified May 2026.*

---

## Going Deeper

- [ST VL53L1X datasheet](https://www.st.com/en/imaging-and-photonics-solutions/vl53l1x.html)
- [Robotiq FT 300-S product page](https://robotiq.com/products/ft-300-force-torque-sensor)
- [ATI Industrial Automation F/T overview](https://www.ati-ia.com/products/ft/)
- [GelSight Mini documentation](https://www.gelsight.com/gelsightmini/)
- [Meta AI DIGIT sensor](https://digit.ml/) — open hardware tactile sensor
- [PyTouch library](https://github.com/facebookresearch/PyTouch) — tactile ML toolkit
- [Mason — *Mechanics of Robotic Manipulation*](https://mitpress.mit.edu/9780262133968/mechanics-of-robotic-manipulation/) — the standard reference for contact in manipulation
