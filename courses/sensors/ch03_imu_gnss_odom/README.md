# Chapter 03 — IMU, GNSS & Wheel Odometry

**Time:** ~25 min
**Hardware:** Laptop only
**Prerequisites:** ROS2 course ch01–ch02

---

The three sensors in this chapter share one job: tell you where the robot is and how it's moving. They all do it badly — but each fails in a *different* direction, which is exactly why they get fused together.

- **IMU** drifts in time. Stand still and the estimated heading will slowly walk away from reality.
- **GNSS** drifts in space. Your antenna gets confused by buildings, trees, and clouds; the position skitters around the true location.
- **Wheel odometry** drifts when wheels slip. A skid for one second on a polished floor adds a permanent error to your position estimate.

The trick of every robot localization stack is to combine them so each sensor's strengths cover the others' weaknesses. The end of the chapter explains that fusion at the right level — no Kalman filter derivations, just the intuition.

---

## Inertial Measurement Unit (IMU)

**What it does.** Reports linear acceleration and angular velocity in three axes. Higher-end units also report magnetic field (a 9-axis or "9-DoF" IMU) and run on-chip sensor fusion to output orientation directly.

**Senses.**
- **Accelerometer** — proof-mass on tiny springs; deflection under acceleration (including gravity)
- **Gyroscope** — vibrating MEMS structure; Coriolis force on a rotating frame shifts the vibration
- **Magnetometer** — Hall effect or magnetoresistance against Earth's magnetic field (acts as a compass)

A 6-axis IMU measures the three orthogonal linear axes and three rotational axes (roll, pitch, yaw). A 9-axis adds three magnetometer axes for absolute heading.

![Roll, pitch, yaw — Wikimedia Commons (CC BY-SA 3.0)](assets/roll_pitch_yaw.svg)

**Input.** 3.3 V power, I2C/SPI clock, optional interrupt pin for "new data ready."

**Output.** Three streams at 100–1000 Hz: accel (m/s²), gyro (rad/s), and on 9-axis units mag (μT). Fusion-on-chip units also output quaternion orientation directly.

**Integration.**
- **Physical interface:** I2C (most hobby breakouts), SPI (faster), UART (industrial)
- **ROS2:** `bno055` (Bosch BNO055), `ros2_mpu6050_driver`, `xsens_mti_ros2_driver`, `microstrain_inertial_driver` → `sensor_msgs/Imu` and `sensor_msgs/MagneticField`
- **Non-ROS:** Bosch BNO055 driver libraries, InvenSense MotionLink, Xsens MT Software Suite, Adafruit CircuitPython libraries (one-liners for breakouts)

**Limitations to watch out for.**
- **Gyro drift.** Integrating angular velocity gives orientation — and any bias on the rate becomes unbounded heading drift over time. Hobby units drift 1–10° per minute when stationary. Industrial units drift <0.1°/hour.
- **Accel noise + bias.** Integrating acceleration twice to get position is *catastrophically* bad. Position estimate from accel alone diverges in seconds. Never do this without external aiding.
- **Magnetometer interference.** Anything ferrous (motors, speakers, steel rebar in floors) warps the local magnetic field. Indoor heading from a magnetometer is often unreliable; calibrate in situ and don't trust it near actuators.
- **Temperature sensitivity.** Bias drifts with temperature. Industrial IMUs include calibration tables; hobby units don't.
- **Sample-rate mismatch.** If your control loop runs at 50 Hz and the IMU runs at 1000 Hz, you're either downsampling (losing info) or buffering (adding latency). Decide deliberately.
- **"9-DoF" doesn't mean "9 reliable degrees."** Mag axis is much worse than accel and gyro indoors.

### Why & how it works

A MEMS gyro is a tiny silicon tuning fork vibrating at fixed frequency. When the substrate rotates, the Coriolis force pushes the tines sideways — proportional to angular velocity. Capacitive sensors detect the sideways shift, and you get a rate gyro on a chip that costs cents. The accelerometer is conceptually simpler: a small proof mass on silicon springs, with capacitive sensing of its deflection.

The reason orientation drifts is integration. The gyro measures *rate*; orientation is the integral. Any bias in the rate (even 0.01°/s, which is excellent for hobby parts) accumulates into 0.6° of heading error per minute, 36° per hour. After an hour stationary your "heading" is meaningless.

This is why every serious IMU is **fused with something else** — magnetometer (yaw reference), GNSS (position reference), wheel odom (velocity reference), or visual odometry (everything reference).

**Representative products.**

![Bosch BNO055 IMU — Adafruit](assets/products/bosch_bno055.jpg) ![Bosch BNO085 IMU — Adafruit](assets/products/bosch_bno085.jpg)

| Product | Tier | DoF | Fusion | Price (USD) | Pick when |
|---|---|---|---|---|---|
| [InvenSense MPU6050](https://invensense.tdk.com/products/motion-tracking/6-axis/mpu-6050/) | Hobby | 6 (no mag) | None | ~$3 (chip), ~$10 breakout | You want the cheapest IMU and will fuse externally |
| [Bosch BNO055](https://www.bosch-sensortec.com/products/smart-sensor-systems/bno055/) | Hobby+ | 9 | On-chip quaternion fusion | ~$25 (Adafruit breakout) | Plug-and-play orientation without writing a filter |
| [Bosch BNO085](https://www.adafruit.com/product/4754) | Hobby+ | 9 | On-chip + better algorithms | ~$25 | BNO055 but more accurate; newer chip |
| [InvenSense ICM-20948](https://invensense.tdk.com/products/motion-tracking/9-axis/icm-20948/) | Hobby+ | 9 | Optional DMP firmware | ~$15 (Adafruit breakout) | Hackable; lots of community support |
| [Xsens MTi-630](https://www.xsens.com/products/sensor-modules/xsens-mti-600-series-flexible-reliable-imus-for-all-design-needs) | Industrial | 9 + on-chip fusion (AHRS) | Factory-calibrated | ~$1,500–$3,000 | Robot needs 0.2° pitch/roll accuracy and you trust the heading indoors |
| [VectorNav VN-100](https://www.vectornav.com/products/detail/vn-100) | Industrial | 9 + AHRS | Factory-calibrated | ~$800–$1,500 | Drone or marine vehicle; rugged casing |

*Prices verified May 2026 from Adafruit, Mouser, DigiKey, Xsens, VectorNav.*

---

## GNSS / GPS

**What it does.** Reports the antenna's position on Earth (latitude, longitude, altitude) by triangulating from satellites.

**Senses.** Time-of-arrival of microwave signals from 4+ orbiting satellites. The receiver solves for its own (x, y, z, clock-bias) position.

**Input.** 3.3 V power, antenna (active patch or external).

**Output.**
- **Standard GNSS:** position to ±2–5 m, updated 1–10 Hz, NMEA strings or binary protocols
- **RTK GNSS:** position to ±2 cm — but only with a nearby base station (or NTRIP correction service)
- **Multi-constellation** (GPS + GLONASS + Galileo + BeiDou) helps in urban canyons

**Integration.**
- **Physical interface:** UART (NMEA), USB, I2C on small modules; some industrial units use Ethernet
- **ROS2:** `nmea_navsat_driver` (any NMEA receiver), `ublox_dgnss` / `ublox_gps` for u-blox modules → `sensor_msgs/NavSatFix`, `sensor_msgs/TimeReference`
- **Non-ROS:** u-blox u-center (config + visualization), `gpsd` on Linux, RTKLIB (open-source RTK processing)

**Limitations to watch out for.**
- **No indoor coverage.** Walls block GHz signals. Inside a building, GPS is dead.
- **Urban canyons.** Tall buildings reflect signals, giving you "multipath" — position skitters by 10–50 m.
- **Tree cover, weather.** Forests reduce accuracy 2–5×.
- **Cold start time.** First fix from power-on can take 30 seconds to several minutes if the receiver doesn't have recent almanac data.
- **RTK needs a base station.** Either yours, NTRIP from a public network, or a paid commercial service. A standalone "RTK rover" with no base is just a normal receiver.
- **Antenna placement matters more than people expect.** A patch antenna under your robot's metal chassis sees 30% of the sky and performs accordingly.
- **GPS time ≠ wall-clock time.** Be careful when fusing — GPS uses its own epoch; your computer uses UTC plus a leap-second table.

### Why & how it works

Each satellite broadcasts its own ID and the time the signal left. The receiver measures arrival time, multiplies by *c*, and gets the distance to that satellite. Four distances pin down the receiver's (x, y, z, time-bias). The math wants four satellites; in practice, 8+ are usually visible, and the extras give redundancy and better geometry.

RTK ("Real-Time Kinematic") works by having a second receiver — a base station — at a *known* location nearby. The base sees the same satellites and computes its own error. Since both receivers see the same atmosphere, the rover can subtract the base's error in real time, going from ±3 m to ±2 cm.

**Representative products.**

![u-blox simpleRTK2B / ZED-F9P — Ardusimple](assets/products/ublox_simplertk2b.jpg)

| Product | Tier | Accuracy | Constellations | Price (USD) | Pick when |
|---|---|---|---|---|---|
| [u-blox NEO-M9N](https://www.u-blox.com/en/product/neo-m9n-module) | Hobby | ~2 m | GPS+GLONASS+Galileo+BeiDou | ~$70 (SparkFun board) | Outdoor robot, ±2 m good enough |
| [u-blox ZED-F9P](https://www.u-blox.com/en/product/zed-f9p-module) | Prosumer | ~2 cm with RTK | Multi-band, multi-constellation | ~$200 (chip), ~$300 (Ardusimple board) | You need cm-level outdoor positioning |
| [Ardusimple simpleRTK2B](https://www.ardusimple.com/product/simplertk2b/) | Prosumer | ~2 cm with RTK | F9P-based | ~$300 | Ready-to-use RTK board with helpful tooling |
| [Emlid Reach M2](https://emlid.com/reach/) | Prosumer | ~2 cm with RTK | Multi-band | ~$1,000 | Drone surveying, photogrammetry |
| [Septentrio AsteRx-i3](https://www.septentrio.com/) | Industrial | mm + integrated INS | All bands | ~$5k–$15k | Survey-grade or autonomous vehicle navigation |

*Prices verified May 2026 from SparkFun, Ardusimple, Emlid.*

---

## Wheel odometry

**What it does.** Counts wheel rotations and converts to estimated robot travel.

**Senses.** Rotations of a wheel (via an encoder bolted to the motor shaft or wheel axle). Not really a separate sensor — usually a property of the actuator stack.

**Input.** Encoder pulses (digital), motor controller usually does the counting.

**Output.** Distance traveled per wheel → robot pose (x, y, θ) via the platform's kinematic model. For a differential-drive robot: average the two wheel velocities to get linear velocity; subtract them and divide by wheelbase to get angular velocity; integrate to get pose. Ackermann (car-like) and omnidirectional bases use different formulas.

**Integration.**
- **Physical interface:** Quadrature encoder signals (digital), or absolute encoder (SPI/I2C/SSI). Read by motor controller or microcontroller, often relayed to the host over USB/UART/CAN.
- **ROS2:** A motor-controller node (e.g., `ros2_control` differential drive controller, `roboclaw_driver`, `odrive_ros2_control`) → `nav_msgs/Odometry` and a TF transform from `odom` to `base_link`
- **Non-ROS:** Counted in firmware on the motor controller; exposed to host as a register read

**Limitations to watch out for.**
- **Wheel slip.** Polished floors, gravel, tight turns, sudden acceleration — anything that breaks contact between tire and ground adds a permanent error.
- **Wheel diameter drift.** Tire wear, inflation, weight loading change the effective diameter by a few percent. Over time, miles add up to meters of error.
- **Differential-drive yaw error.** A 1% wheel-circumference mismatch between left and right wheels causes ~6° per meter of heading error. Calibrate.
- **No absolute reference.** Pure wheel odom is dead reckoning. Errors only ever accumulate; they never self-correct.
- **It's not really 6-DoF.** Wheel odom gives you (x, y, θ) on a plane. If the robot's pitching over a bump, the planar projection of motion is wrong.

**Pick when:** you have wheels and motor encoders. This is essentially free — every wheeled robot publishes odometry. The interesting question isn't *whether* to use it, but *how to fuse it* with IMU and GNSS, which is the next section.

---

## How they fuse — the dead-reckoning trio

This is the payoff. Each sensor fails in a *different* dimension:

| Sensor | Drifts in | Time-to-divergence | Bounded by |
|---|---|---|---|
| IMU | time (orientation), seconds (position) | seconds | nothing (open-loop integration) |
| GNSS | space (multipath, geometry) | always present | satellite geometry |
| Wheel odom | wheel-slip events | accumulates with distance | nothing |

The standard fusion is an **Extended Kalman Filter (EKF)** — an algorithm that maintains a best-estimate state plus uncertainty, and updates both whenever a new measurement arrives. It runs all three sensors through one model. Conceptually:

1. **Predict** the robot's next state using IMU + wheel odom (these are fast, low-latency)
2. **Correct** the prediction whenever a GNSS measurement arrives (this is slow, but absolute)
3. Repeat at 50–200 Hz

In ROS2 this is almost always [`robot_localization`](http://docs.ros.org/en/noetic/api/robot_localization/html/) — a community-maintained EKF/UKF node that subscribes to any combination of `sensor_msgs/Imu`, `nav_msgs/Odometry`, `sensor_msgs/NavSatFix`, and publishes a fused `nav_msgs/Odometry` on a unified TF tree. You configure it with a YAML matrix specifying which fields of which input topics are trusted.

The headline outputs:
- **`odom` → `base_link`** — continuous, smooth, but drifts over hours (good for control loops)
- **`map` → `odom`** — corrected by GNSS or visual landmarks, jumps when corrections arrive (good for navigation goals)

This two-frame setup is the standard ROS2 convention (REP-105). Your control loop reads from `odom`; your global plan reads from `map`.

---

## How to choose

- **Indoor robot, no GPS coverage:** IMU + wheel odom + (eventually) visual odometry or LiDAR-based SLAM. Skip GNSS entirely.
- **Outdoor robot, m-level accuracy OK:** consumer GPS (NEO-M9N) + IMU + wheel odom. Fuse with `robot_localization`.
- **Outdoor robot, cm-level accuracy needed:** RTK GPS (ZED-F9P or Emlid) + industrial IMU + wheel odom.
- **Drone:** industrial IMU + RTK GPS + barometer. Wheel odom not applicable.
- **Robot arm (no mobile base):** IMU only matters if the base moves. Joint encoders on the arm are different — those are in a future actuators course.
- **Underwater / GPS-denied:** IMU + DVL (Doppler velocity log) + acoustic positioning. Out of scope here.
- **You just need orientation, not position:** a 9-DoF IMU with on-chip fusion (BNO055, BNO085) is the easiest path.

---

## Going Deeper

- [`robot_localization` documentation](https://docs.ros.org/en/noetic/api/robot_localization/html/) — the canonical ROS2 fusion node
- [REP-105 — Coordinate Frames for Mobile Platforms](https://www.ros.org/reps/rep-0105.html) — the `map`/`odom`/`base_link` convention
- [u-blox ZED-F9P integration manual](https://content.u-blox.com/sites/default/files/ZED-F9P_IntegrationManual_UBX-18010802.pdf) — surprisingly readable RTK reference
- [Xsens MTi product selector](https://www.xsens.com/sensor-modules/xsens-mti-product-selector)
- [Madgwick filter paper (2010)](https://www.x-io.co.uk/res/doc/madgwick_internal_report.pdf) — the most-cited IMU fusion algorithm
- [Probabilistic Robotics — Thrun, Burgard, Fox](http://www.probabilistic-robotics.org/) — the textbook for the EKF math when you want to go deeper
- [SparkFun GPS tutorial](https://learn.sparkfun.com/tutorials/gps-basics) — accessible intro to how GPS actually works

https://www.youtube.com/watch?v=eqZgxR6eRjo

(Above: 3Blue1Brown-style intuition for Kalman filtering — the math without the trauma)
