# India Sourcing — May 2026

Detailed retailer-by-retailer reality check.

## Retailer ranking

| Tier | Retailer | Best for | Caveat |
|---|---|---|---|
| **A** | **Robu.in** | Catalog breadth, LDRobot/Slamtec, batteries, chassis | Stock churns; phone support inconsistent |
| **A** | **Robocraze** | Pi 5 / Jetson (authorised), drivers, sensors, polished UX | Aggressive urgency banners; stock churn |
| **A−** | **Hubtronics** | Pi 5 + accessories, Bangalore, fast for South India | Smaller catalog |
| **B+** | **Fab.to.Lab** | Niche Seeed gear (XVF3800), RealSense | Long restock waits |
| **B+** | **Robokits India** | Honest pricing on motor drivers, IMUs, encoders | Older site UI |
| **B+** | **ThinkRobotics** | NVIDIA Jetson, Orbbec | Expensive; slow ship |
| **B** | **MG Super Labs** | RealSense, niche industrial parts | Usually backorder |
| **B** | **ElectronicsComp** | Cheap individual components | Single-unit stock |
| **D** | **IndiaMART listings** | Last-resort | Phone-call sales; counterfeit risk |
| **D** | **Random Amazon.in third-party** | Convenience for non-critical | Component lottery |

## Per-component sourcing notes

### Compute

- **Pi 5 8GB**: Robocraze ₹19,849 (authorised, 40 in stock). Avoid sub-₹14k listings — counterfeit/4GB-relabelled risk.
- **Pi 5 27W PSU**: Robocraze ₹1,255 (often OOS). Hubtronics has alternate.
- **Pi 5 active cooler**: Robocraze ₹544.
- **NVMe HAT+**: Hubtronics ₹1,200-1,500. Geekworm X1001 cheaper.
- **256GB NVMe (2280)**: Local Amazon WD/Crucial ₹2-3.5k.
- **ESP32-S3-DevKitC-1-N8R8**: Robu ₹2,200, genuine. Avoid no-name "ESP32-S3 38-pin" boards.

### LiDAR

- **RPLidar C1**: Amazon.in via WayPonDEV, Robu listing ~₹15,000.
- **LDRobot D500 (= LD19 hardware, rebranded)**: Robu, ~₹8-9k. Cheapest viable option.
- **LD19 by exact name**: Not stocked. Import from AliExpress lands ~₹15-16k after duty — same as RPLidar C1, with worse warranty.
- **RPLidar A1M8**: Robocraze ₹8,874 (often OOS).

### Microphones

- **ReSpeaker XVF3800 USB**: Fab.to.Lab ₹7,388, **in stock as of May 2026**.
- **ReSpeaker Mic Array v3.0 (XVF3000)**: Robocraze ₹8,729 (often OOS).
- **ReSpeaker 4-Mic HAT (AC108)**: AVOID. Driver unmaintained on Bookworm/Trixie kernels.
- **INMP441 I2S MEMS mic**: Robocraze ₹450 (in stock). For DIY array fallback.

### Cameras

- **Pi Camera Module 3 standard**: Robocraze ₹3,099.
- **Pi Camera Module 3 Wide**: ₹3,400-3,800.
- **Logitech C270 USB**: Amazon ₹1,099. Fine fallback.
- **ESP32-CAM (OV2640)**: Robokits ₹400 (genuine AI-Thinker).
- **RealSense D435i**: MG Super Labs ₹40,499 (backorder). Skip.
- **Orbbec Femto Bolt**: ThinkRobotics ₹48,999 (OOS). Skip.

### Motors

- **N20 metal-gear w/ encoder**: ElectronicsComp ₹509+GST. **Pay the premium for all-metal-gear** (Robokits GA12 or ElectronicsComp's all-metal listing). Cheap variants have plastic 1st-stage gear that shears.
- **TT motors**: Robu ₹80-120/pair. No encoders, no good.
- **Pololu metal-gear motors**: Not stocked locally; landed ~₹3,500/motor. Skip unless research-grade.
- **TB6612FNG**: Robokits ₹284 genuine, Robocraze ₹145 (clones, often work but quality lottery).
- **DRV8833**: Robocraze ₹71-90.
- **L298N**: Avoid — 2V dropout is awful for low-speed encoder control.

### Power

- **Samsung 30Q 18650**: Robu ₹613. Counterfeit endemic — Robu authenticates.
- **3S 2200mAh pack + 3S 20A BMS**: ~₹1,500 combined.
- **3S LiPo (Orange/Bonka)**: Robocraze ₹1,399. Needs balance charger.
- **Pololu D24V50F5 5V 5A buck**: Not stocked. Import ₹2,500. Worth it for Pi 5 sustained loads.
- **Generic LM2596 buck**: Robu ₹80-250. Quality lottery; most can't do 5A continuous.

### Reliability components

- **Pi 5 RTC battery (Panasonic ML-2020)**: Cytron / Robu ₹400.
- **High-endurance microSD (SanDisk Endurance / Samsung PRO Endurance 64GB)**: Amazon ₹800-1,200.
- **INA226 / INA219**: Robu ₹150-300.
- **Magnetic pogo pin contacts (4-pin, 3A)**: Robu ₹200-400.
- **AprilTag**: Print on adhesive paper, ₹50.
- **Cliff IR pair + microswitch bumper**: ~₹250 in parts.
- **JST-XH + JST-PH + XT60 connector kit**: Robu/Amazon ~₹400.

### Mechanical

- **2WD/4WD acrylic chassis kit**: Robu ₹250-1,400.
- **3D print service**: iamRapid ₹6/g, Makenica ₹8-12/g, ~₹1,200-1,800 for typical 200g chassis.
- **65mm rubber wheels + 3mm shaft pair**: Robu ₹150-250.
- **Caster wheel**: ₹60-100.
- **M3 standoff/screw kit**: Robu ₹350-600.

### Misc

- **WS2812B 16-LED ring**: Robocraze ₹85.
- **MAX98357A I2S amp**: Robocraze ₹185, Robokits ₹89.
- **MPU6050 IMU**: Robokits ₹96.
- **Speaker (4Ω 3W, 50mm)**: ₹150 local.

## Don't-buy list

- Sub-₹6,500 "Pi 5 8GB" anywhere — counterfeit/relabel
- Generic Amazon "ESP32-S3" without explicit `-N8R8` / `-N16R8` markings
- MPU9250 from random sellers (discontinued by InvenSense; many are fakes — use BMI270 or LSM6DSOX)
- L298N for anything with encoders
- AC108-based ReSpeaker 4-Mic HAT (driver unmaintained)
- Generic LM2596 "5V 5A" for Pi 5 (actually 1.5A continuous)
- "Samsung 30Q" cells under ₹400 (counterfeit)
- YDLIDAR X2L (lacks proper ROS2 driver upstream)
- OV2640 ESP32-CAMs without "AI-Thinker" silkscreen
- "3S 18650 packs" without BMS

## Lead time reality

- Robocraze, Robu, Hubtronics: 2-5 days.
- ThinkRobotics, Fab.to.Lab: 7-14 days, often backorder.
- AliExpress import: 2-4 weeks for Cainiao, plus 2-7 days clearance + 31% landed duty.
- Yahboom direct: 3-4 weeks plus 28% IGST.

Plan the build with **two retailer orders, two weeks apart** to absorb stock churn.

## Total realistic landed for Strong tier: ~₹72,000

Buffered for restocks, replacements, and "first build breaks something" — this is not a quoted price; it's a budget.
