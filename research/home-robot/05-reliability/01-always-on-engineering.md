# Always-On Engineering

## The premise

A robot that doesn't auto-dock isn't an "always-on" robot. It's a project that lives on a wired tether and slowly stops being plugged in. **Docking is the most important sensor on the robot.** It's the one place the robot must touch every day. If docking is unreliable, nothing else matters.

## Top 5 things that matter

1. **AprilTag (tag36h11) + opennav_docking, not IR.** IR is sunlight-blinded and not debuggable.
2. **Mechanical funnelling, not millimetre vision.** Y-recess + magnetic pogos do the last 2 cm.
3. **Spring-loaded magnetic pogo pin contacts.** Brass strips oxidize; pogos last years.
4. **Hardware watchdog + RTC battery + read-only rootfs (or full data journaling + overlay).** Kills three of the top hobby-robot killers.
5. **Telemetry from day one.** A robot you can't observe will quietly die.

## Docking — the recommended approach

| Method | Cost | Reliability | Verdict |
|---|---|---|---|
| IR beacon | ₹2-4k | 85-95% clean env | Avoid — opaque, not debuggable, sunlight-blinded |
| ArUco | ₹50 print | ~95% good light | OK fallback |
| **AprilTag (tag36h11)** | ₹50 print | **~98%** good light | **Recommended** |
| LiDAR feature | ₹500 reflector | Industrial in clean env | Use as last-meter heading aid only |
| Magnetic / contact | ₹400 | ~100% if within 3cm | Always layer on top of vision |
| Inductive (Qi) | ₹600+ | High when aligned | <10W = won't keep up. Skip. |
| NN visual servoing | "Free" | Variable | Cool research, not week-4 reliable |

### Concrete recipe

- **Marker:** 110mm AprilTag (tag36h11), printed on adhesive paper (matches Stretch dock size).
- **Software:** `opennav_docking` ROS2 server with `apriltag_ros` detector.
- **Staging pose:** ~80cm in front of dock, robot pre-aligned within ±15°.
- **Final approach speed:** 15 cm/s (Nav2 default — slow on purpose).
- **Retry policy:** 3 attempts with re-stage between. After 3 failures → STRANDED state, push notification, give up gracefully.
- **Mechanical funnel:** Y-recess for caster + 30° flare guiding contacts together. 3D printed.

The Pi camera v3 wide at 1080p resolves a 110mm tag from ~3m comfortably.

## Charging — cheap-but-safe stack

For 3S Li-ion (10-12.6V, 2200mAh):

| Component | Role | ₹ |
|---|---|---|
| **3S BMS with balance** (Daly 10A or HX-3S-FL25A) | Cell balance, OC/UC, SC, OCP | 250 |
| **12.6V/2A bench charger brick in dock** | Provides regulated charging V | 500 |
| **Magnetic pogo pin pair** (4-pin 3A) | Contacts, polarity-keyed by magnets | 350 |
| **INA226** | I²C V + I monitor | 200 |
| **Reverse-polarity Schottky + TVS diode** | Protect against polarity mistakes | 50 |

**Pattern:** Dock = "dumb" 12.6V CC/CV brick + magnetic pogo female. Robot = pogo male + reverse-protection + BMS + INA226 reporting state of charge. Robot decides "done" by current dropping below ~100mA at 12.6V.

**Critical:** TP5100 is 1S/2S only — DO NOT use for 3S. Common hobbyist mistake → fires.

**Safety musts:**
- BMS with **per-cell balance**, not just pack-level. Unbalanced cells cause swelling at month 6.
- INA226 reading exposed to ROS as `sensor_msgs/BatteryState`.
- Hardware undervoltage cutoff at 9.0V (3.0V/cell), separate from software low-battery threshold.

## Battery state machine

```
IDLE_DOCKED ── new_task ──► UNDOCK ──► WORKING

WORKING ── battery<30% AND predicted_runtime > remaining ──► RETURNING
WORKING ── user_interacting ──► WORKING (defer until interaction ends, hard cap at 20%)

RETURNING ── nav2_failure ──► STRANDED (notify, low-power idle, do NOT retry forever)
RETURNING ── arrived_at_staging ──► DOCKING

DOCKING ── opennav_dock_success + charge_current_detected ──► CHARGING
DOCKING ── 3 retries failed ──► DOCK_BLOCKED (notify "cat?", wait 5min, retry)
DOCKING ── arrived but no charge_current after 30s ──► DIRTY_CONTACTS (wiggle off+on, then notify)

CHARGING ── full (current<100mA AND V≈12.6) ──► IDLE_DOCKED
CHARGING ── BMS trip / overtemp / undervoltage ──► FAULT (notify, don't auto-retry)

ANY ── battery<15% (critical) ──► EMERGENCY_PARK (stop, notify, sleep)
```

### Key thresholds

- **Return decision:** 30% remaining AND predicted task runtime > remaining capacity. Don't use a flat % alone.
- **Critical cutoff:** 15% — internal resistance spikes, motor pulses can crash Pi.
- **Hardware cutoff:** 9.0V via BMS — last line of defence.

### User interaction handling

If actively interacting (face within 1m for >5s OR audio command in last 30s), defer return until interaction ends, but **hard deadline at 20% battery** to avoid stranding mid-conversation.

### Stranded state design

If Nav2 fails to get home, **do not retry indefinitely** — drains battery faster. Park, push notify, blink LED, accept human rescue. Roomba's "I'm lost" beep is exactly this.

## Reliability investment list

The ₹2,650-beyond-base-BOM list. Each entry has a known failure mode it prevents.

| # | Investment | ₹ | Failure avoided |
|---|---|---|---|
| 1 | Pi 5 RTC battery (Panasonic ML-2020) | 400 | Time loss on power cycle → broken TLS, broken cron, confused SLAM bag timestamps |
| 2 | High-endurance microSD (SanDisk Endurance / Samsung PRO Endurance 64GB) | 800 | SD corruption from power loss — *the* most-cited Pi reliability killer |
| 3 | Hardware watchdog enabled (`dtparam=watchdog=on`, `RuntimeWatchdogSec=14`) | 0 | Silent ROS2 hangs requiring manual reboot |
| 4 | Read-only rootfs OR ext4 full data journaling + overlay | 0 | SD corruption; safe power-yank |
| 5 | INA226 battery monitor on I²C | 200 | Flying blind on charge state |
| 6 | 3S BMS with per-cell balance leads | 250 | Pack swelling (year-1 killer), fire risk |
| 7 | Magnetic pogo pin charging contacts (4-pin, 3A) | 350 | Brass strip oxidation; misalignment retries |
| 8 | XT60 / JST-XH / JST-PH connector standardization kit | 400 | Year-2 unrecoverable serviceability |
| 9 | Mechanical bumper + cliff IR pair | 250 | Wedge-under-couch death; stair death |
| 10 | MQTT health telemetry to phone (Home Assistant or ntfy) | 0 (sw) | Robot dies silently in a corner |
| 11 | Modular battery hatch + screw-not-glue construction | 0 (design) | Year-2 battery replacement turning into "project's dead now" |
| 12 | Docker-compose for ROS2 stack with pinned image tags | 0 (sw) | `apt upgrade` breaking Nav2 the day before a demo |

**Total extra cost: ~₹2,650.** Difference between a robot that works for 30 days and one that quietly dies in week 3.

## The 30-day list — what kills home robots that demo well

Confirmed by Roomba field reports, Pi forum threads, hobby-robot postmortems:

- **Dirty charging contacts** — *the* most-cited Roomba docking failure. Brass oxidizes; pet hair bridges. Wipe weekly or use pogo pins.
- **Sunlight blinding IR docks** — afternoon-only failures, confusing.
- **SD card corruption from power loss** — Hackaday, Pi forums agree. Solution: HW watchdog + UPS or read-only root.
- **Carpet fibres in encoders / wheels** — visible on every Roomba teardown.
- **Pet hair on optical sensors** — Roomba "Error 9" famously caused by pet hair.
- **WiFi disconnects under load** — Pi 5 WiFi degrades when CPU is busy; SSH drops mid-debug.
- **Bearing wear on cheap motors** — N20s typically last 100-300 hours of duty before lash develops.
- **LiDAR motor:** LD19 rated 10,000+ hours brushless — not the bottleneck.
- **Battery degradation:** 3S Li-ion at 1 cycle/day = ~2 years to 80% capacity. Plan replacement at year 2.
- **Map drift:** SLAM maps degrade as furniture moves. Re-mapping cadence (monthly).
- **Software updates breaking things:** `apt upgrade` on working ROS2 = Russian roulette. Pin versions or use Docker.
- **Serviceability:** Robots that need full disassembly to replace a battery die at first battery swap.

## The demo→daily-use gap

What Roomba has that hobbyist robots don't, that's not obvious from a teardown:

- **A bumper.** Robots without physical contact bumpers wedge under couches and stall.
- **A cliff sensor.** Stairs end most non-Roomba hobby robots in week 1.
- **Scheduled "lost" recovery behavior.** Roomba beeps for help and parks. Most hobby robots loop or brick.
- **A power button you can find** with the lid closed, in the dark, while it's running into a wall.
- **A factory reset path** that doesn't require flashing an SD card.
- **Compliance / overload protection in drivetrain.** Roomba slips on stuck conditions; hobby gear motors strip teeth.
- **20 years of edge-case-tuning.** Every Roomba "wiggle to align" is a bug-fix dressed as a feature.

## The three habits that matter

1. **Observability beats cleverness.** A robot with a janky AprilTag dock + Telegram health-bot survives. Roomba's "I am stuck near a stair" voice is a billion-dollar feature pretending to be a beep.

2. **Mechanical conservatism.** Vision is luxury on top of geometry. Y-funnel, cliff sensors, magnetic pogo alignment — none clever, all bulletproof. Hobby robots fail because they trust software where geometry would be cheaper and 100% reliable.

3. **Plan for the second battery, not the first demo.** Year-1 hobby robots fail because: (a) SD card corrupted at week 6, (b) battery swelled at month 8, (c) brass contacts oxidized at month 4, (d) `apt upgrade` broke Nav2 at month 5, (e) wedged under furniture at week 2 and burnt out a motor. Each has a ₹200-500 fix that nobody designs in until they've been bitten.
