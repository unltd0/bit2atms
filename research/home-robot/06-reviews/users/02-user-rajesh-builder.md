# User Review — Rajesh, the Builder

**Persona:** Rajesh, 41, electrical engineer turned hobbyist + maker. Lives in a 2BHK in Pune with his wife (kids are at university). Has built two PrintRBot 3D printers, a CNC mill, an aquarium controller, a homemade smart-home stack on Home Assistant + ESPHome with 40+ devices. Spends ~20 hours a week on hobby projects. Has a workshop in the spare bedroom.

**Reading:** the full project docs.

---

## My read

This is the project I've been wanting to start for two years and kept not starting because every time I look at it, the integration looks like a 6-month time sink. You've documented why it's a 6-month time sink and made it look possible to actually finish.

This is *exactly* my kind of project. I have most of the parts in my workshop already (Pi 5 8GB, ESP32-S3, an old RPLidar A1, motors, wheels, more 18650 cells than I want to admit). I'd order the XVF3800, the Pi camera, the BMS, the pogo pins, the AprilTag stuff, and start this week.

Let me give you the honest feedback from someone who would actually build this.

## What's great

**The reliability chapter.** I have killed three Pi-based projects to SD card corruption. I've finally moved everything to NVMe and high-endurance SD as a backup. You named every failure mode I've personally hit. The watchdog + RTC + INA226 list is the difference between "fun project for a month" and "thing that runs in the workshop indefinitely." Anyone who has run a 24/7 Pi system for a year will read your reliability doc and nod.

**The split-brain architecture.** ESP32 for real-time + Pi for ROS + laptop for cognition is exactly how I'd build it. I've tried doing motor PID on a Pi and it's miserable. The micro-ROS Linorobot2 firmware is the right call.

**The skill registry shape.** I've been playing with rosa and ROSA and they're both heavyweight for what I want. Pydantic AI + a simple Python loop is the correct level of abstraction for a single-engineer build. The runtime-injected enum trick is the kind of detail you only learn after you've shipped one of these.

**Honest BOM at ₹72k.** I've watched too many projects on Hackster.io claim "$200 robot!" and the BOM doesn't include the laptop, the 3D printer, the spare parts, or the time. Yours is honest. I respect it.

## What I'd push back on

### 1. Everything cloud-LLM is a smell.

I run my whole home on local-only because I've watched too many cloud services get acquired/shut down/raise prices/leak data. Home Assistant + Frigate + local Ollama is my standard stack. Your default of "Claude Haiku 4.5 cloud as primary, local Qwen as fallback" is the wrong way around for the kind of person who builds this robot.

I'd ship with **local Qwen 2.5 7B (or 14B if your laptop has 24GB VRAM) as primary, cloud as fallback only when explicitly opted in.** The latency hit is worth the privacy/independence/no-API-key story. Most builders feel this way.

If your laptop is too weak for 7B locally, fine — but say so explicitly and recommend upgrading the laptop before relying on cloud.

### 2. The 3D printing dependency.

You note "outsourced 3D printed chassis parts ~₹1,800 via iamRapid." But honestly the chassis design is half the project and half the customization. If I'm building this, I'm designing the chassis to fit my robot's purpose and printing it on my Bambu A1 in PETG. It's not a generic chassis kit project.

I'd recommend providing **STL files + parameters in OnShape/FreeCAD** so builders can fork the chassis. iamRapid is fine for those who don't have a printer; the chassis source files are mandatory for the rest of us.

### 3. Linorobot2 firmware vs roll-your-own.

Linorobot2 is good, but I've found it opinionated about wiring and tuning. For a serious build, I'd rather have a documented "here's the micro-ROS skeleton, plug in your motor PID + encoder + IMU code." The Linorobot2 dependency couples your project to their decisions.

I think Linorobot2 is the right starting point but the firmware should be forkable and the doc should explain how to roll your own when needed.

### 4. The world model is too thin.

Your SQLite + Chroma + FastAPI is fine for a demo. After 30 days of operation, you'll have:
- Tens of thousands of events
- Hundreds of object observations
- Dozens of locations
- Real concurrency between event-writers and the LLM

SQLite handles concurrent writes badly. Chroma's persistence story has gotten better but isn't great. A FastAPI service running on a laptop that may be asleep is a single point of failure.

I'd push to:
- DuckDB or PostgreSQL for the structured side (DuckDB for analytical queries; Postgres if you want concurrency)
- Qdrant or LanceDB instead of Chroma (better persistence)
- The world model as a separate Docker container that runs on the robot (Pi 5) so it doesn't depend on laptop being awake

This is the kind of decision that shows up at week 6, not week 1.

### 5. The XVF3800 is bleeding edge for an India build.

You note Fab.to.Lab has it in stock at ₹7,388. I'd hedge with the v3.0 alternative because:
- Fab.to.Lab stock churns
- Driver maturity for XVF3800 in 2026 is OK but not battle-tested
- v3.0 is well-documented in HA Wyoming community

The v3.0 is ₹8,729 — more expensive, but more reliable. I'd recommend v3.0 as the default and XVF3800 as the upgrade for builders who want the latest.

## What's missing

**A simulation environment.** I want to test the agent loop before driving the actual robot into furniture. Gazebo Garden + ros2_control + a URDF of the robot is a weekend's work and saves you a month of debugging on real hardware. Hello Robot's stretch_ai ships with one. Yours doesn't even mention it.

**A failure injection mode.** A way to artificially fail Nav2, fail STT, simulate dock-blocked, etc., to test the agent's recovery paths. Without this, you only catch failures by experiencing them.

**A "the robot is alive" health dashboard.** You note MQTT telemetry to phone. I'd want a Grafana board showing: battery cycles, dock attempts/successes, STT failures, LLM latency p95, Nav2 failures. A robot that's been running 6 weeks should be observable like a server.

**A backup-and-restore story.** What happens when my SD card dies in month 8? Can I image a new one and restore the world model + map + config? I want this to be 1 command. Without it, every SD failure is a project death.

**A "second user" feature flag.** Right now everything is built around me, the primary user. What about my wife? She doesn't want to enroll her face. She wants the robot to know her name and respond, not record her face. There needs to be a "guest mode" that's first-class.

## My personal questions

Not for the doc, just for me building it:

- **What chassis dimensions actually fit through standard Indian apartment doorways?** Standard interior door is 75-80cm. Robot has to be < 50cm wide. Yours is implied diff-drive at maybe 25cm — fine, but document it.
- **How does the robot handle Indian-style threshold transitions?** Bathroom thresholds are 5-8cm. Bedroom thresholds are sometimes 2-3cm. Will the robot get stuck?
- **What about sari hems and dupattas hanging off chairs?** This is a real LiDAR + costmap problem.
- **What about the maid moving the dock?** Dock has to be findable even if it's 30cm off where you left it.
- **What's the noise level?** I have an upstairs bedroom. If this thing whirs at night I'm in trouble.

## What I'd actually do

If I were building this:

1. **Order parts this weekend.** Tier A BOM, all in. ~₹72k.
2. **Spend week 1 on chassis** in CAD + 3D printing. Skip acrylic kit, design my own.
3. **Week 2-3** on micro-ROS firmware, basic teleop.
4. **Week 4-5** on Nav2 + slam_toolbox in my home.
5. **Week 6-7** on Wyoming voice satellite + speaker recognition (face-rec).
6. **Week 8-10** on agent loop + world model + first 2 use cases.
7. **Week 11-12** on docking + reliability + telemetry.
8. **Week 13+** living with it.

That's ~3 months at ~12-15 hours/week of evenings/weekends. Realistic for me.

## What this is missing for me, specifically

- **Local-first as the default**, cloud as opt-in
- **Forkable chassis** with STL + CAD source
- **Containerized world model** on the robot, not on the laptop
- **Sim environment** for testing the agent loop
- **Backup/restore** as a first-class operation
- **Robot-grade health dashboard**
- **A second user experience** that doesn't require enrollment

Add those and it's the project I'd recommend to anyone who's built more than 5 hobby projects.

## Score from me

Would I build this: 9/10
At ₹72k: 8/10 (it's a lot, but it's fair)
3-month build time estimate: 8/10 (matches my estimate)
Architecture: 9/10
Reliability work: 10/10
Privacy story: 8/10 (push more on local-first)
Documentation quality: 9/10

Best honest hobby home robot writeup I've seen this year. Now I want to actually build it.
