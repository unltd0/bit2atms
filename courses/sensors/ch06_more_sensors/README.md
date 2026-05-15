# Chapter 06 — More Sensors Worth Knowing

**Time:** ~15 min
**Hardware:** Laptop only
**Prerequisites:** ROS2 course ch01–ch02

---

The first five chapters cover the sensors that show up on most mobile robots and most manipulators. This chapter is a *map of the territory* — a quick reference to other sensor families a robot might need.

Each item gets a few lines: what it senses, what it outputs, the ROS2 msg type if there is one, a one-line failure mode, a typical use case, and a representative product or two. No deep dives — if any of these turn out to matter for your robot, the linked pages are the rabbit hole.

---

## Environmental sensors

**What.** Temperature, humidity, barometric pressure, gas concentrations (CO2, VOCs — Volatile Organic Compounds, such as evaporated solvents and cleaning products), particulate matter.

**Output.** Scalar values at 1–10 Hz over I2C/SPI/UART.

**ROS2.** `sensor_msgs/Temperature`, `sensor_msgs/RelativeHumidity`, `sensor_msgs/FluidPressure`. No standard msg for gas / air quality — use vendor or custom.

**Limitation.** Slow response (seconds for temperature to equilibrate). Drift over time. Chemical gas sensors gradually degrade — repeated exposure to the gases they measure damages the sensing element.

**Use cases.** HVAC inspection robots, agricultural drones, lab automation, indoor air-quality monitoring, search-and-rescue (look for trapped people via CO2).

**Examples:** [BME680](https://www.bosch-sensortec.com/products/environmental-sensors/gas-sensors/bme680/) (temp + humidity + pressure + VOC, ~$15), [SCD40 / SCD41](https://sensirion.com/) (CO2 measured by NDIR — Non-Dispersive Infrared, an optical technique that's much more reliable than chemical CO2 sensors, ~$50), [SGP40](https://sensirion.com/) (VOC, ~$15), [Plantower PMS5003](http://www.plantower.com/) (PM2.5 / PM10 dust — particle sizes in micrometers, ~$25).

---

## Barometric altimeter

**What.** Air pressure → altitude (via the standard atmosphere model).

**Output.** Pressure in Pa, derived altitude in m, at 1–100 Hz over I2C/SPI.

**ROS2.** `sensor_msgs/FluidPressure`.

**Limitation.** Altitude is *relative* to a reference; weather changes baseline by ±100 m over a day. Indoor HVAC air movement causes drift.

**Use cases.** Drone altitude hold (essential), indoor floor detection, weather-aware robots.

**Examples:** [MS5611](https://www.te.com/) (~$10), [BMP388 / BMP390](https://www.bosch-sensortec.com/) (~$15), [LPS22HB](https://www.st.com/) (~$10).

---

## Battery / current / power sensors

**What.** Measure current draw and battery voltage on the robot's power rails.

**Output.** Voltage, current, charge state (estimated or measured), temperature.

**ROS2.** `sensor_msgs/BatteryState` — published by motor controllers, BMS firmware, or a dedicated power-monitor node.

**Limitation.** Charge state (% remaining) is always an estimate. *Coulomb-counting* — adding up every bit of current that flows in or out of the battery — drifts as small measurement errors accumulate. Voltage-curve estimation is noisy under load.

**Use cases.** Every battery-powered robot. Triggers return-to-dock behavior. Detects stalled motors via current spikes.

**Examples:** [TI INA219](https://www.ti.com/product/INA219) (~$5 chip), [INA260](https://www.ti.com/product/INA260) (~$10 chip), Smart BMS modules from Daly / JBD (~$30–$100), [Mauch RC current sensors](https://www.mauch-electronic.com/) for drones.

---

## Light / lux / UV sensors

**What.** Ambient brightness in lux, or UV index.

**Output.** Scalar lux value at 1–100 Hz over I2C.

**ROS2.** `sensor_msgs/Illuminance`.

**Limitation.** *Cosine response* — a tilted sensor reads less light than one pointed straight at the source. Sunlight can saturate cheap sensors.

**Use cases.** Agricultural robots adjusting for plant exposure, smart-home automation, camera auto-exposure outside the camera.

**Examples:** [TSL2591](https://www.adafruit.com/product/1980) (~$10), [VEML7700](https://www.adafruit.com/product/4162) (~$5), [VEML6075](https://www.vishay.com/) (UV, ~$10).

---

## Hall-effect sensors

**What.** Detects magnetic field presence or strength.

**Output.** Digital (switch open/closed) or analog (field strength).

**ROS2.** No standard msg — typically GPIO read or wheel encoder pulses; absorbed into joint-state or odom publishers.

**Limitation.** Sensitive to nearby magnets you didn't put there. Saturates near strong fields.

**Use cases.** Cheap proximity (door open / lid closed), BLDC (Brushless DC) motor commutation — three hall sensors per motor tell the controller which winding to energize next, universal in BLDCs — wheel rotation counters, end-stops on 3D printers.

**Examples:** [A3144](https://www.allegromicro.com/) (~$0.50, digital switch), [DRV5053](https://www.ti.com/product/DRV5053) (analog, ~$1), AS5048 (magnetic absolute encoder, ~$15).

---

## Photoelectric / break-beam sensors

**What.** An IR LED and a photodiode pair. The receiver detects when the beam is interrupted.

**Output.** Digital signal (beam intact / interrupted).

**ROS2.** GPIO read; published as a custom `Bool` topic or absorbed into a state machine.

**Limitation.** Beam range and alignment matter. Strong ambient IR (sunlight, halogen lamps) can saturate.

**Use cases.** Conveyor-belt object counting, gripper "is something in the jaws," safety light curtains, drone ground-truth on test rigs.

**Examples:** [Adafruit IR break-beam pair](https://www.adafruit.com/product/2168) (~$5), Banner Engineering industrial photoelectric (~$50–$500).

---

## Line / IR reflectance arrays

**What.** A row of IR LED + phototransistor pairs reading reflectance off the surface below.

**Output.** Per-channel reflectance value (analog or digital).

**ROS2.** Custom topic; typically a microcontroller publishes a small array of floats.

**Limitation.** Surface dependent — black tape on white is easy; black tape on dark wood is impossible.

**Use cases.** Line-following robots, edge detection on tabletop robots, conveyor-position feedback.

**Examples:** [Pololu QTR-8RC](https://www.pololu.com/category/123/qtr-reflectance-sensors) (~$15), TCRT5000 single sensors (~$1).

---

## RFID / NFC readers

**What.** Reads passive tags via near-field RF coupling at 13.56 MHz (NFC) or 125 kHz (LF RFID), or UHF (860–960 MHz) for longer range.

**Output.** Tag ID string (typically hex), occasionally with small read/write data payloads.

**ROS2.** No standard msg — custom string topic, or absorbed into a docking/inventory action.

**Limitation.** Short range (cm for NFC, tens of cm for HF, m for UHF). Metal nearby reduces range.

**Use cases.** Warehouse robots reading tagged inventory, docking targets, tool identification, access control.

**Examples:** [PN532](https://www.adafruit.com/product/364) (NFC, ~$30), [RC522](https://www.amazon.com/) (cheap clone, ~$3), Impinj / Zebra UHF RFID readers (~$1k+ for warehouse-grade).

---

## Joint position sensors

**What.** Measure the angle or position of a robot joint. Different tech than wheel encoders — usually direct, often absolute.

**Output.** Joint angle in radians; published via the motor controller or a `joint_state_publisher` node.

**ROS2.** `sensor_msgs/JointState`.

**Limitation.** Potentiometers wear out and are analog-noisy. Absolute magnetic encoders are precise but need careful magnet placement.

**Use cases.** Every robot arm joint. Steering position on Ackermann vehicles. Pan-tilt mechanisms.

**Examples:** [AS5048](https://www.austriamicrosystems.com/) (magnetic absolute encoder, ~$15), [AksIM](https://www.rls.si/) (industrial absolute encoder, ~$300+), 10-turn potentiometers (~$5).

*Note: joint actuation will be covered in a future Actuators course — this entry is here so you know the sensing side exists.*

---

## Strain gauges and load cells

**What.** Foil resistors bonded to a deforming surface. When the surface stretches or compresses, resistance changes proportionally.

**Output.** Force / weight via a *Wheatstone bridge* (a four-resistor circuit that turns tiny resistance changes into a measurable voltage) plus an ADC (Analog-to-Digital Converter). Typically reported in kg or N at 10–1000 Hz.

**ROS2.** Custom topic; sometimes `geometry_msgs/WrenchStamped` for single-axis force.

**Limitation.** Drifts with temperature, needs calibration, very low signal levels (mV-range before amplification).

**Use cases.** Gripper-finger force sensing, weight measurement, robot-foot ground reaction force, scale automation.

**Examples:** [HX711 + bar load cell](https://www.sparkfun.com/products/13879) (~$10 kit), [Futek button load cells](https://www.futek.com/) (~$200–$1,000 for precision).

---

## Color sensors

**What.** Senses RGB or full spectrum of incident light. Like a 1-pixel camera, but with calibrated color response.

**Output.** R, G, B values (and on better sensors, clear / IR channels) over I2C.

**ROS2.** No standard msg — custom or absorbed into a sorting controller.

**Limitation.** Field of view is wide; you measure the average color of a patch, not a precise point. Ambient light affects readings unless the sensor has its own illuminator.

**Use cases.** Sorting (red M&Ms vs green), simple object ID, light-stage detection.

**Examples:** [TCS34725](https://www.adafruit.com/product/1334) (~$8), AS7341 (11-channel spectral, ~$15).

---

## Gas / chemical sensors

**What.** Detect specific gases — methane, propane, CO, CO2, NH3, alcohol, etc. — via catalytic combustion (MQ-series), electrochemistry (industrial), or NDIR (CO2).

**Output.** Analog voltage or an I2C value in ppm (parts per million) at 1–10 Hz.

**ROS2.** Custom topic; no standard msg.

**Limitation.** **Cross-sensitivity** — an "alcohol sensor" responds to many gases, just more to alcohol. Quantitative numbers from cheap sensors are barely qualitative. Lifetime is months to a year of continuous operation for the cheap MQ-series.

**Use cases.** Search-and-rescue (CO detection), hazmat robots, agricultural NH3/CH4 monitoring, food-quality stations.

**Examples:** [MQ-series modules](https://www.amazon.com/) (~$3 each, qualitative), [Sensirion SGP series](https://sensirion.com/) (~$15, calibrated VOC), Figaro and SGX Sensortech (industrial, $50–$500).

---

## Radiation / Geiger counters

**What.** Detects ionizing radiation — alpha, beta, gamma.

**Output.** Pulse rate (counts per minute) or dose rate (μSv/h).

**ROS2.** Custom topic; usually a `Float32` publisher.

**Limitation.** Geiger tubes need high voltage (300–500 V) — handle with care. Cheap units count gross radiation; they don't tell you what isotope.

**Use cases.** Nuclear-facility inspection robots, post-disaster mapping (Fukushima used several), space rovers, citizen science.

**Examples:** [RadiationD-v1.1 (CAJOE)](https://www.amazon.com/) (~$70 hobbyist), [Mirion RDS-31](https://www.mirion.com/) (industrial, $$$).

---

## Flow sensors

**What.** Measure volume per unit time of a liquid or gas passing through a tube. Various physics — turbine, ultrasonic, thermal mass-flow, differential pressure.

**Output.** Volume rate (mL/min) via pulse counting or I2C.

**ROS2.** Custom topic.

**Limitation.** Calibrated for one fluid; viscosity changes shift the calibration.

**Use cases.** Liquid-handling robots, lab automation, irrigation drones, chemical dispensing.

**Examples:** Adafruit / Seeed turbine flow sensors (~$10–$30 each), Sensirion SLF3S-1300F (precision microfluidics, ~$300).

---

## Fiducial markers

**What.** A printable QR-style tag (AprilTag, ArUco) that any RGB camera can detect and recover the marker's 6-DoF pose from a single frame.

**Output.** Pose of the marker in the camera frame, via a fiducial detection node.

**ROS2.** `apriltag_ros` → `apriltag_msgs/AprilTagDetectionArray`, plus TF transforms.

**Limitation.** Needs decent lighting and a non-grazing camera angle (the camera shouldn't see the tag at too sharp a slant). Tags wear out and get dirty in industrial settings.

**Use cases.** Cheap absolute localization indoors (print tags on walls). Robot-arm tool calibration. Multi-robot relative localization. Ground-truth in research.

**Examples:** [AprilTag](https://github.com/AprilRobotics/apriltag) (open-source, $0 — just a printer), [ArUco](https://docs.opencv.org/4.x/d5/dae/tutorial_aruco_detection.html) (OpenCV's version, also free).

---

## UWB anchors (Ultra-WideBand)

**What.** A small radio transceiver that exchanges short pulses with anchor radios installed in the environment. From time-of-flight to each anchor, the receiver solves its (x, y, z) position.

**Output.** Position in a local coordinate frame, at 1–100 Hz, at ~10 cm accuracy.

**ROS2.** Vendor drivers (Decawave, Nooploop) → `geometry_msgs/PoseStamped`.

**Limitation.** Needs anchors installed in the space — typically 3–4 anchors for 2D, 4+ for 3D. Walls absorb UWB; line-of-sight gives best results.

**Use cases.** Indoor positioning where GPS doesn't work. Drone swarms in a flight arena. Warehouse robots with installed infrastructure.

**Examples:** [Decawave DWM1001-DEV](https://www.qorvo.com/products/p/DWM1001-DEV) (~$30 per module), Nooploop LinkTrack (~$200/set), Pozyx (~$500/set).

---

## Quick reference — if you need X, look at Y

| If you need... | Look at | Chapter |
|---|---|---|
| "Did I hit something?" | Bump switch, contact sensor | [Ch 04](../ch04_proximity_contact/README.md) |
| Distance, short-range cheap | Ultrasonic (HC-SR04) | [Ch 04](../ch04_proximity_contact/README.md) |
| Distance, short-range accurate | IR ToF (VL53L1X) | [Ch 04](../ch04_proximity_contact/README.md) |
| 360° distance scan | 2D LiDAR | [Ch 02](../ch02_lidar_radar/README.md) |
| 3D environment | 3D LiDAR or depth camera | [Ch 01](../ch01_cameras/README.md) / [Ch 02](../ch02_lidar_radar/README.md) |
| What is it (semantics) | Camera + ML | [Ch 01](../ch01_cameras/README.md) |
| Heading, orientation | IMU | [Ch 03](../ch03_imu_gnss_odom/README.md) |
| Outdoor position | GNSS | [Ch 03](../ch03_imu_gnss_odom/README.md) |
| Indoor position | UWB anchors or fiducial markers | this chapter |
| Voice commands | Microphone array | [Ch 05](../ch05_audio/README.md) |
| "How hard am I pressing?" | F/T sensor or motor-current proxy | [Ch 04](../ch04_proximity_contact/README.md) |
| Surface texture / slip | Tactile sensor (GelSight, DIGIT) | [Ch 04](../ch04_proximity_contact/README.md) |
| Robot joint angle | Magnetic absolute encoder | this chapter |
| Battery state | Power monitor (INA219, BMS) | this chapter |
| Hot object detection | Thermal camera | [Ch 01](../ch01_cameras/README.md) |
| Microsecond motion capture | Event camera | [Ch 01](../ch01_cameras/README.md) |
| Gas / chemical presence | Gas sensor | this chapter |
| Robot altitude (drone) | Barometric altimeter | this chapter |
| Identify tagged object | RFID / NFC reader | this chapter |
| Print-on-paper localization | AprilTag / ArUco | this chapter |
| See through smoke | Thermal camera or radar | [Ch 01](../ch01_cameras/README.md) / [Ch 02](../ch02_lidar_radar/README.md) |
| Find moving thing in fog | Radar | [Ch 02](../ch02_lidar_radar/README.md) |

---

## Going Deeper

- [Adafruit sensor catalog](https://www.adafruit.com/category/35) — a browse of hobby breakouts will expose many of these
- [SparkFun sensor catalog](https://www.sparkfun.com/categories/23) — same, with strong tutorials
- [Sensirion environmental sensors](https://sensirion.com/) — the high end of hobby+ environmental
- [AprilTag project](https://github.com/AprilRobotics/apriltag)
- [Decawave UWB documentation](https://www.qorvo.com/products/p/DWM1001C) — best free intro to UWB positioning
- [TI INA219 power monitor app note](https://www.ti.com/lit/an/sboa342/sboa342.pdf) — surprisingly readable
- [ROS Index sensor_msgs reference](https://docs.ros.org/en/rolling/p/sensor_msgs/) — the canonical list of standard msgs and which sensor they fit
