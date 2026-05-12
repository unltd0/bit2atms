# BOM — three tiers

All prices INR landed, May 2026. Sources in `02-sourcing-india.md`.

## Tier A — Strong (recommended)

The honest "this works" build.

| Item | ₹ |
|---|---|
| Raspberry Pi 5 8GB (Robocraze authorised) | 19,849 |
| Pi 5 27W official PSU (IN plug) | 1,500 |
| Pi 5 active cooler | 544 |
| 256GB NVMe + Pi 5 NVMe HAT+ | 4,800 |
| 32GB high-endurance microSD (boot/backup) | 800 |
| **Pi 5 RTC battery (Panasonic ML-2020)** | 400 |
| RPLidar C1 (Robu/Amazon WayPonDEV) | 15,000 |
| ReSpeaker XVF3800 USB 4-mic (Fab.to.Lab) | 7,388 |
| Pi Camera Module 3 (standard) | 3,099 |
| ESP32-S3-DevKitC-1-N8R8 (Robu, genuine) | 2,200 |
| 4× N20 metal-gear motors w/ encoder (quality) | 2,800 |
| TB6612FNG motor driver (Robokits, genuine Toshiba) | 284 |
| 3S Li-ion 2200mAh pack + 3S 20A BMS w/ balance | 1,500 |
| INA226 battery monitor | 200 |
| Pololu D24V50F5 5V 5A buck (or quality alternate) | 1,200 |
| MPU6050 IMU | 165 |
| MAX98357A I2S amp + 4Ω 3W speaker | 350 |
| WS2812B 16-LED ring | 85 |
| **Magnetic pogo pin charging contacts (4-pin, 3A)** | 350 |
| **AprilTag printed on adhesive paper** | 100 |
| **Cliff IR pair + microswitch bumper kit** | 250 |
| **XT60 + JST-XH + JST-PH connector kit** | 400 |
| 4WD acrylic chassis + wheels + casters | 1,500 |
| M3 hardware kit | 500 |
| Outsourced 3D printed chassis parts (~150g via iamRapid) | 1,800 |
| Wires, USB cables, microSD reader | 1,200 |
| Shipping (3-4 retailer shipments) | 600 |
| **Subtotal** | **~₹68,500** |
| 5% buffer for restocks/replacements | 3,500 |
| **TOTAL** | **~₹72,000** |

This is the build that runs reliably for 30 days, auto-docks, and uses the XVF3800 mic array. Fewer compromises, more headroom.

## Tier B — Compromised

Trim non-essentials. Capability cost documented.

| Item | ₹ | Capability cost |
|---|---|---|
| Raspberry Pi 5 4GB | 13,000 | Tighter RAM headroom; offload more to laptop |
| Pi 5 27W PSU + cooler | 2,000 | — |
| 64GB high-endurance microSD (no NVMe) | 1,200 | Slower IO, shorter SD lifespan |
| Pi 5 RTC battery | 400 | — |
| RPLidar A1M8 (₹8,874 OOS) or LD19 D500 from Robu | 8,500 | Older sensor, more drift, 6m vs 12m range |
| ReSpeaker Mic Array v3.0 (Robocraze) | 8,729 | Older XVF3000 chip, similar 4-mic DOA |
| Pi Camera Module 3 | 3,099 | — |
| ESP32-S3-DevKitC-1-N8R8 | 2,200 | — |
| 4× cheap N20 motors w/ encoder | 1,400 | Quality lottery — buy 6, expect 1-2 to fail |
| TB6612FNG | 284 | — |
| 3S Li-ion + BMS | 1,500 | — |
| INA226 | 200 | — |
| MPU6050 | 165 | — |
| Speaker + amp | 350 | — |
| LED ring | 85 | — |
| Pogo pins + AprilTag + cliff IR + bumper | 700 | — |
| Connectors | 400 | — |
| Acrylic chassis kit | 1,500 | Fragile, prone to crack |
| Misc | 1,800 | — |
| Shipping + buffer | 1,500 | — |
| **TOTAL** | **~₹48,000** |

Capability impact:
- SLAM is rougher (older A1M8 has more drift)
- 4GB RAM means LLM offload is mandatory; can't even dabble with on-Pi small models
- Motor reliability lottery — plan for replacements
- No NVMe means SD card is the only storage; back up frequently

This is shippable but it bleeds. Not recommended unless budget is the absolute hard constraint.

## Tier C — Buy a base, extend

Skip the chassis/motors integration entirely.

| Item | ₹ |
|---|---|
| Yahboom Rosmaster X3 (Pi 5 variant), Amazon import or ex-Yahboom | ~75,000 |
| ReSpeaker XVF3800 USB | 7,388 |
| Speaker + amp | 350 |
| Pogo pin contacts + AprilTag dock | 450 |
| INA226 (if not included) | 200 |
| Pi 5 RTC battery | 400 |
| Misc | 1,000 |
| Shipping + buffer | 2,000 |
| **TOTAL** | **~₹87,000** |

Saves integration time (chassis comes built, lidar pre-mounted). Costs ~₹15k more. Recommended only if integration time is genuinely the bottleneck. Verify ROS2 maturity for the specific X3 SKU before committing — Yahboom's X3 *Plus* with arm is ROS1-only as of May 2026 per their forum.

## Tier comparison

| | Strong (A) | Compromised (B) | Buy-base (C) |
|---|---|---|---|
| Total | ₹72,000 | ₹48,000 | ₹87,000 |
| Pi RAM | 8GB | 4GB | varies |
| LiDAR | RPLidar C1 (12m) | A1M8 / LD19 D500 (6-12m) | included |
| Mic array | XVF3800 (latest) | v3.0 (older) | XVF3800 added |
| NVMe | Yes | No | varies |
| Auto-dock | Yes (built-in) | Yes (built-in) | Yes (added) |
| Reliability adds | All present | All present | All present |
| Integration weeks | 4-6 | 4-6 | 1-2 |
| Capability ceiling | High | Medium | High |
| Recommended for | Most builds | Tight budget | Time-poor builds |

## What we are NOT buying

- Jetson Orin Nano (₹38,609) — overkill, eats whole budget alone
- Intel RealSense D435i (₹40,499) — sunsetted by Intel, expensive, depth not needed if LiDAR works
- TurtleBot 4 Lite (₹190,999) — out of scope
- Husarion ROSbot (₹3.7L+) — out of scope
- Reachy Mini (₹50k landed) — doesn't move
- Anything from AliExpress that has a ₹15k+ landed cost without saving anything (LD19 by name)

## Decision: Tier A (Strong) is the project's official BOM

Reasons:
- Tier B's RAM and SD card constraints will be a daily annoyance
- Tier C costs more for less learning value
- The reliability adds (RTC, INA226, pogos, AprilTag, cliff IR, bumper, connectors) are non-negotiable; trying to save ₹2-3k on them is a false economy

Final number: **~₹72,000 landed** for a single robot. Build one to learn, refine, then decide whether to build a second.
