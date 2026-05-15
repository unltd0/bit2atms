# Chapter 3 — Build your own robot

**Time:** Half-to-full day
**Hardware:** Laptop only
**Prerequisites:** Chapters 1–2

---

## What are we here for

Chapter 2 had you driving someone else's robot — TurtleBot3 in Gazebo, fully wired before you arrived. The wheels, the lidar, the bringup launch, the URDF — all done for you. Now you're going to **build your own**.

Concretely: imagine you have an **Arduino-driven 4-wheel car** — the kind of $25 hobbyist chassis kit that's everywhere. Four DC motors, an Arduino controlling them through a small motor-driver board, and a single front-facing IR distance sensor. The Arduino plugs into a laptop with a USB cable; over that cable, the laptop's operating system gives you a virtual *serial port* — so the ROS2 code on the laptop just opens `/dev/ttyACM0` and writes text commands, and the Arduino sees them coming in on its serial pin. *That's the robot.* Cheap, common, the kind of thing hobbyists actually build. You won't build the physical one in this chapter — but you'll model it in ROS2, drive it in a Gazebo physics sim with real walls, and at the end see exactly which files swap (and which stay byte-for-byte identical) when the real Arduino is wired in.

The deeper question: **is simulation in robotics there to replicate reality and test your behaviour code — the same way unit tests do in regular software?** Yes — with a fidelity caveat. Sim handles the kinematics (where the robot moves under a given command), the topic/message plumbing, and the rough shape of sensor data well. It only approximates the messy physics — motor inertia, friction, sensor noise patterns. Real teams develop algorithms in sim, tune the rough parts against measured hardware when stakes are high, then validate on the real robot. For us, the takeaway is stronger: **sim and real share so much code that your behaviour code (we'll call it *business logic*) ships unchanged across the gap.** Only the hardware-facing driver swaps.

By the end of this chapter you'll have a clean answer to: *"If I built this Arduino car for real, what code would I write, what would I install, and what would stay identical to what I just wrote?"*

### Notation used in this chapter

Every ROS2 entity in prose is tagged with a prefix word so you never have to guess what category it belongs to:

| Prefix | Means | Example |
|---|---|---|
| `topic ...` | a named channel messages flow over | `topic /cmd_vel` |
| `msg ...` | a message type (the data shape) | `msg Twist`, `msg LaserScan` |
| `node ...` | a ROS2 node / a script that runs as one | `node car_mover.py` |
| `pkg ...` | a ROS2 package | `pkg ros2_control` |
| `tf ...` | a TF frame name | `tf base_link` |

### Setup

All commands run inside the same `ros2` Docker container from ch02 (`docker exec -it ros2 bash`). Foxglove on your laptop, `pkg foxglove_bridge` running inside the container — same setup as ch02.

**Before you start**, make sure `workspace/ros2/ch03/` on your host is populated. If you ran the workspace seed step from the **Docker image** sidebar resource at any point, you're good — the chapter's resource files live under `/workspace/ros2/ch03/` inside the container. If you haven't seeded yet, run once from the repo root:

```bash
bash scripts/reset_workspace.sh --add-only
```

Then in a container shell:

```bash
# T1 — leave foxglove_bridge running
ros2 launch foxglove_bridge foxglove_bridge_launch.xml port:=8765
```

Open Foxglove, connect to `ws://localhost:8765`, load the new `ch03_layout.json` (Layouts panel → Import → `resources/ros2/foxglove/ch03_layout.json` from your local clone).

---

## Projects

| # | Project | What you build |
|---|---------|----------------|
| A | Describe your robot | A URDF for the 4-wheel Arduino car; `tiny_bot` appears in Foxglove |
| B | Simulate it | Spawn `tiny_bot` in a Gazebo world with walls; drive it; have it stop before hitting things |
| C | Wire the real Arduino | Concept-level: what swaps, what stays, when you go to real hardware |

---

## Project A — Describe your robot

**Goal:** model `tiny_bot`'s mechanical layout in a URDF and see it appear in Foxglove. No physics, no motors yet — just a shape on the screen with the right coordinate frames.

URDF (Unified Robot Description Format) is the standard way every ROS2 robot describes itself: what links exist (chassis, wheels, sensor mounts), how they connect, where each one sits. `node robot_state_publisher` reads the URDF and broadcasts the resulting coordinate-frame tree as TF transforms — `tf_static` for the fixed parts (sensor mounts), `tf` for the moving parts (wheel joints, once something publishes their angles). Every other tool in the ecosystem can then ask *"where is the IR sensor mounted relative to the chassis?"* and get a real answer.

🟢 **Run** — three commands in any container shell:

```bash
# 1. xacro preprocesses ${variables} and <macros> into plain URDF (one-shot)
ros2 run xacro xacro /workspace/ros2/ch03/tiny_bot.urdf.xacro \
    > /workspace/ros2/ch03/tiny_bot.urdf

# 2. publish the URDF + broadcast fixed-joint TF transforms (long-running)
ros2 run robot_state_publisher robot_state_publisher \
    /workspace/ros2/ch03/tiny_bot.urdf
```

In a second shell:

```bash
# 3. publish zero angles for the non-fixed joints (the wheels). On a real
# robot the motor driver does this; with no driver running yet, this stand-in
# keeps the TF tree complete so Foxglove can render.
ros2 run joint_state_publisher joint_state_publisher
```

In Foxglove (with `ch03_layout.json` loaded), the 3D panel's display frame is `base_link`. You should see `tiny_bot`: chassis box, four wheel cylinders (one at each corner), a small orange block at the front (the IR sensor), a small green block at the back, a small dark cylinder on top. The green block is an *IMU* (inertial measurement unit) frame and the dark cylinder is a *lidar* mount — placeholder frames matching what a real hobbyist Arduino car often has bolted on. We don't drive them in this chapter; they're there so the URDF looks like a real-robot URDF and you have somewhere to wire those sensors in later.

> **Don't see the model?** Foxglove caches `topic /robot_description` per session. Re-import the layout to force a refetch.

### Read the file

The whole URDF is ~120 lines. Open it side-by-side and skim:

```xml+collapsed resources/ros2/ch03/tiny_bot.urdf.xacro
```

Three things to notice — that's all you need from URDF for this chapter:

1. **Links** (`<link name="...">`) — rigid bodies. Chassis, wheels, sensors. Each has a `<visual>` (what Foxglove draws), an optional `<collision>` (what a physics sim hit-tests), and an `<inertial>` (mass + inertia — what a sim or `pkg ros2_control` reads to do dynamics).

2. **Joints** (`<joint type="...">`) — connections between links. `fixed` means bolted on (sensor mounts). `continuous` means free rotation (wheels). `revolute` and `prismatic` exist too (arm joints, sliders). A joint says *child sits at this offset and can move in this way relative to parent*.

3. **Frame names matter** — `tf base_scan` for a 2D lidar, `tf imu_link` for an IMU, `tf base_link` for the chassis. These are [REP-105](https://www.ros.org/reps/rep-0105.html) conventions. Stock SLAM and Nav2 expect them. Invent your own names and you'll be writing remap flags forever.

URDF describes the **mechanical structure**. It does *not* describe behavior — nothing in the file says how fast a wheel should spin, what a lidar measures, or how an IMU reports gravity. Those are runtime concerns. Drivers and physics engines fill them in. Project B does both.

**Side note on xacro.** The file extension is `.urdf.xacro`, not `.urdf`. `xacro` is a preprocessor that adds two things plain URDF lacks: constants (`<xacro:property name="wheel_radius" value="0.05"/>`, used as `${wheel_radius}`) and macros (`<xacro:macro name="wheel" params="prefix reflect">...`, called as `<xacro:wheel prefix="left" reflect="1"/>`). Constants and functions. Everyone uses it because plain URDF makes you copy-paste.

---

## Project B — Simulate it

**Goal:** put `tiny_bot` in a real physics sim with walls, drive it, and have it stop before it crashes. URDF showed the *structure*; this project gives it *behaviour* — wheels that spin under torque, sensors that see actual geometry, a world with mass and friction.

We're not going to hand-roll any of that. **Gazebo Sim** does it for us — ch02 already used it to drive the TurtleBot. (Gazebo is a separate project from ROS2; we use *Harmonic*, the release officially paired with ROS2 Jazzy. The container has both installed already.) We just need to:

1. Tell Gazebo *what* the robot is — a parallel description file covering the parts of the URDF we want physics on (chassis, four wheels, IR sensor; the placeholder IMU and lidar frames from the URDF are skipped — no point simulating what we don't drive), plus a couple of Gazebo plugins (a "diff-drive" plugin that consumes Twist and moves the wheels, a "ray" sensor for the IR distance reading). This file is in **SDF** (Simulation Description Format) — URDF's Gazebo-flavoured cousin.
2. Tell Gazebo *where* the robot lives — a small world (also SDF) with walls.
3. Bridge Gazebo's native topics to ROS2 topics — `pkg ros_gz_bridge` does this with a YAML config.
4. Launch all of it.

Each of those is a small file (the robot SDF, the world SDF, the bridge YAML, the launch). They live in `resources/ros2/ch03/`. Read them once at your leisure; we'll point at the interesting bits inline. The launch file is the only piece you need to *run* directly.

### The contract you're about to use

Before deriving what runs in this project, the standard handshake every mobile robot uses:

> *Across the entire ROS2 ecosystem, "tell a wheeled robot how to move" means one thing: publish a `msg Twist` on `topic /cmd_vel`.*
>
> *`msg Twist` is the message type — six numbers (`linear.x/y/z`, `angular.x/y/z`) describing a desired velocity. `topic /cmd_vel` is the named channel those messages flow on. The combination — `msg Twist` on `topic /cmd_vel` — is the de-facto handshake for mobile robots. Nav2 publishes there. Every teleop tool publishes there. Every motor driver in the ecosystem subscribes there. It's not enforced by ROS2; it's enforced by the fact that everything else assumes it.*

Now derive what's needed for the contract to do something useful.

**1. Something needs to consume `msg Twist` on `topic /cmd_vel` and turn it into wheel motion.** In sim, that's Gazebo's `gz-sim-diff-drive-system` plugin (attached to `tiny_bot.sdf`). It reads the Twist, computes each wheel's target angular velocity, drives the simulated wheel joints at those velocities, and publishes back `msg Odometry` on `topic /odom` plus the `tf odom → base_link` transform — exactly what a real motor driver would publish. **On real hardware, this slot is replaced by an Arduino-talking ROS2 node (more in Project C). Same ROS2 contract, different innards.**

→ **Driver:** Gazebo's diff-drive plugin (in sim) / your Arduino driver (on real hardware).

**2. Something needs to read the IR sensor and publish what it sees.** In sim, Gazebo's `<sensor type="gpu_lidar">` (configured as a single-ray scanner — a one-beam laser is the standard way to sim a point-distance sensor) raycasts against world geometry every 100 ms and publishes `msg LaserScan` on `topic /ir_front`. On real hardware, a small ROS2 node would read your Arduino's analog pin via serial and publish the same shape (typically `msg Range`, but `LaserScan` with one ray works too). *Same ROS2 contract, different innards.*

→ **Sensor driver:** Gazebo's ray sensor (in sim) / your Arduino sensor driver (on real hardware).

**3. Something needs to publish the Twists** — to decide *what* the robot should do. Today that's a scripted pattern in `node car_mover.py`. Tomorrow it could be teleop, Nav2, or an AI policy.

→ **Business logic (commander):** `node car_mover.py`.

**4. Something needs to decide what to do with the IR reading** — "if the wall is close, stop the robot." Pure behaviour, hardware-agnostic.

→ **Business logic (safety):** `node obstacle_stop.py`. Sits between `car_mover` and the sim by intercepting Twists on `topic /cmd_vel_in` and forwarding to `topic /cmd_vel` only if the IR is far enough.

### The two layers — name them once

This is the chapter's central conceptual move. The two layers we just named keep showing up:

- **Drivers** — the bottom of the stack. Hardware-facing in real life; physics-engine-facing in sim. Speak standard ROS2 messages outward, and motor signals / sensor reads inward. **Replaced wholesale when you swap sim for real.**
- **Business logic** — the top of the stack. Application-facing. Decides what the robot should do. Speaks the same ROS2 messages. **Stays identical between sim and real.**

In Project B, *every* "driver" is provided by Gazebo plugins. The only code you'll read or modify — `car_mover.py` and `obstacle_stop.py` — is business logic. Project C will show that those two files survive unchanged when you swap Gazebo for an Arduino.

### Read the files

🟡 **Know** — five files, two of them code, three of them XML/YAML config. Skim each.

**The Gazebo model** — `tiny_bot.sdf`. The chassis, four wheels, and IR-sensor link (the same parts of the URDF that we actually want physics on — the URDF's placeholder IMU and lidar frames are skipped here, no point simulating something we don't drive), plus three Gazebo plugin blocks at the bottom: the diff-drive plugin (wiring wheel joints to `topic /cmd_vel`), a joint-state publisher (so `joint_states` reports actual wheel angles), and a `<sensor type="gpu_lidar">` with `samples=1` on the `ir_front` link.

```xml+collapsed resources/ros2/ch03/tiny_bot.sdf
```

**The world** — `tiny_world.sdf`. Ground plane, ambient light, four walls forming a ~3 m × 3 m room. `tiny_bot` spawns at origin facing +x; the front wall sits at x = 1.5 m. (At 0.2 m/s the robot would reach it in about 7 seconds — but in practice `obstacle_stop` halts forward motion well before that, when the IR drops below 0.5 m.)

```xml+collapsed resources/ros2/ch03/tiny_world.sdf
```

**The bridge yaml** — `tiny_bot_bridge.yaml`. Tells `pkg ros_gz_bridge` which Gazebo topics to copy to ROS2 and which way data flows. `cmd_vel` is ROS→GZ (Gazebo subscribes); `odom`, `joint_states`, `tf`, `clock`, `ir_front` are GZ→ROS (we read them).

```yaml+collapsed resources/ros2/ch03/tiny_bot_bridge.yaml
```

**The launch file** — `tiny_bot_sim.launch.py`. Starts Gazebo headless with the world, runs `robot_state_publisher` (with the URDF, so Foxglove can render the model), spawns the SDF, and runs the bridge. ~70 lines. You don't need to read it in detail; just know it orchestrates the four things above.

```python+collapsed resources/ros2/ch03/tiny_bot_sim.launch.py
```

**The business logic** — `car_mover.py` (publishes the Twist pattern) and `obstacle_stop.py` (the IR-aware filter). Both are simple.

```python+collapsed resources/ros2/ch03/car_mover.py
```

```python+collapsed resources/ros2/ch03/obstacle_stop.py
```

### Run it

🟢 **Run** — four shells.

First, if you have `joint_state_publisher` still running from Project A, **Ctrl+C it**. Gazebo's diff-drive plugin is about to take over `topic /joint_states`; only one source can be authoritative. Same for `robot_state_publisher` from Project A — the launch file starts its own; kill the standalone one.

```bash
# T1: Gazebo sim (world + robot + bridge + robot_state_publisher)
ros2 launch /workspace/ros2/ch03/tiny_bot_sim.launch.py

# T2: foxglove_bridge (if not already running)
ros2 launch foxglove_bridge foxglove_bridge_launch.xml port:=8765

# T3: business logic — drive pattern publisher
python3 /workspace/ros2/ch03/car_mover.py

# T4: business logic — IR-aware safety filter
python3 /workspace/ros2/ch03/obstacle_stop.py
```

In Foxglove (display frame set to `tf odom` to keep the camera still while the robot moves), `tiny_bot` should:

1. Drive forward at 0.2 m/s.
2. As it approaches the front wall, the `/ir_front` plot drops from ~1.5 m to below 0.50 m.
3. `obstacle_stop` intercepts the forward command: on the `/cmd_vel` plot, **`linear.x` drops to zero**. Robot halts.
4. `car_mover`'s pattern continues — its next phase is *spin left* (`linear.x = 0, angular.z = 1.5`). With no forward component there's no collision risk, so `obstacle_stop` lets it through unchanged: **`angular.z` goes to 1.5 on the plot**. Robot pivots in place.
5. After pivoting, the IR no longer sees the wall, and `obstacle_stop` resumes forwarding the next forward Twist unmodified. Robot drives off in the new direction.

### What just happened

**Two of the four moving parts you ran are business logic that doesn't know it's in sim:**

- `car_mover.py` published Twists. It doesn't care whether Gazebo's diff-drive plugin is integrating them in a physics engine, or whether a real Arduino is reading them off a USB cable and driving real motors.
- `obstacle_stop.py` subscribed to `/ir_front` and made a stop/go decision. It doesn't care that the LaserScan reading came from a ray-cast in a simulated world. Real IR sensor data would have the same shape.

**The other two moving parts are drivers, all provided by Gazebo:**

- The diff-drive plugin in `tiny_bot.sdf` plays the motor driver's role.
- The `<sensor type="gpu_lidar">` plays the IR sensor driver's role.

Project C is what happens when both drivers swap for real hardware.

> **Note: a single-ray LaserScan is not the *most* canonical type for a point-distance sensor.** In production, an IR-driver package would typically publish `msg sensor_msgs/Range` (one number — distance + min/max range + frame_id). We use `LaserScan` here because Gazebo's stock ray sensor publishes that, and writing a tiny adapter just to convert one to the other adds clutter without teaching anything new. If you swap in a real IR driver, expect `Range`; if you swap in Nav2 expecting LaserScan, you'll need to either keep the LaserScan or convert. Either way, the business logic in `obstacle_stop.py` ships with a one-line type swap.

---

## Project C — Wire the real Arduino

🟡 **Know** — *no code to run here.* The goal is the mental model: now that you have a real physics sim running with business logic on top, what *exactly* changes when you build the real Arduino car? Where does the simulation end and the hardware begin?

The architecture stays the same shape:

```
   ┌──────────────────────────────────────────┐         ┌──────────────────┐
   │  Business logic                          │         │  Foxglove        │
   │  (car_mover, obstacle_stop, Nav2)        │         │  Desktop         │
   │                                          │         │  (your laptop)   │
   │  + robot_state_publisher                 │         │                  │
   │  + foxglove_bridge ──────────────────────┼──── ws://host:8765 ────────┤  subscribes to:  │
   └──────────────────────────────────────────┘                            │   /tf, /tf_static│
                    │                                                      │   /joint_states  │
       msg Twist on topic /cmd_vel_in / /cmd_vel                           │   /odom          │
                    │                                                      │   /ir_front      │
                    ▼                                                      │   /robot_descrip…│
   ┌──────────────────────────────────────────┐                            └──────────────────┘
   │  Drivers                                 │   STAYS UNCHANGED
   │  In sim: Gazebo diff-drive plugin +      │   sim ↔ real (the business
   │          gpu_lidar ray sensor            │   logic and Foxglove)
   │  In real: Arduino-talking ROS2 nodes     │
   │                                          │   SWAPS WHOLESALE
   │  publish ──► /joint_states, /odom,       │   sim → real (the drivers)
   │              /tf (odom→base_link),       │
   │              /ir_front                   │
   └──────────────────────────────────────────┘
                    │
              motor signals / sensor reads
                    │
                    ▼
              [ real hardware ]
```

Only the bottom box (drivers) changes. Everything above ships unchanged. Foxglove doesn't know it was talking to Gazebo in the first place — it asked `pkg foxglove_bridge` for `topic /odom`, and got whatever was currently being published there. When the real Arduino driver replaces Gazebo's plugin, `/odom` carries dead-reckoned encoder data instead of physics-simulated pose. Foxglove just sees different numbers.

### 1. The serial protocol

Between the laptop (running ROS2 + business logic) and the Arduino (driving motors, reading the IR pin) there's a USB cable carrying a serial stream. You can invent any line-based protocol; here's a dead-simple one for `tiny_bot`:

```
Laptop → Arduino:   V <left_rad_per_s> <right_rad_per_s>\n
                    e.g.  V 4.0 -2.0\n

Arduino → Laptop:   E <left_ticks> <right_ticks> <ir_raw>\n   (at 50 Hz)
                    e.g.  E 1234 1198 487\n
```

That's the contract between the two sides. Everything else in this project is just two halves of fulfilling it.

### 2. The motor-driver replacement (ROS2 side)

A real ROS2 motor-driver node subscribes to `topic /cmd_vel`, computes the same per-wheel split Gazebo's diff-drive plugin computes internally — and then writes the result to the serial port instead of solving wheel physics. Reads encoder lines back, derives `msg JointState`, `msg Odometry`, and `tf odom → base_link` from real measurements.

Sketch (not runnable — illustrative):

```python
class ArduinoMotorDriver(Node):
    def __init__(self):
        super().__init__("arduino_motor_driver")
        self.serial = serial.Serial("/dev/ttyACM0", 115200)
        self.create_subscription(Twist, "/cmd_vel", self.on_cmd_vel, 10)
        # ... publishers for /joint_states, /odom, plus a TransformBroadcaster ...
        self.create_timer(0.02, self.tick)   # 50 Hz read loop

    def on_cmd_vel(self, msg):
        v_left  = msg.linear.x - msg.angular.z * (WHEEL_SEPARATION / 2)
        v_right = msg.linear.x + msg.angular.z * (WHEEL_SEPARATION / 2)
        # ↓ THE LINE THAT REPLACES GAZEBO'S PHYSICS INTEGRATION
        self.serial.write(f"V {v_left/WHEEL_RADIUS} {v_right/WHEEL_RADIUS}\n".encode())

    def tick(self):
        line = self.serial.readline().decode().strip()
        if not line.startswith("E "):
            return
        _, left_ticks, right_ticks, ir_raw = line.split()
        # ↑ THE LINE THAT REPLACES THE RAY-CAST + WHEEL-SIM
        # ... convert ticks to angles, publish JointState + Odometry + TF ...
```

The diff-drive math is unchanged — same Twist → per-wheel velocity split that Gazebo's plugin does internally. The two lines highlighted are the swap: the **`serial.write`** replaces Gazebo's "apply force to simulated joint" math; the **encoder parse** replaces Gazebo's "read back the joint's velocity after physics step." The ROS2-side contract — Twist in, JointState + Odometry + TF out — is byte-for-byte identical to what Gazebo's plugin produces. **The business logic above doesn't notice the change.**

### 3. The Arduino-side firmware

This is the part sim doesn't have. In sim, Gazebo's physics engine simulates the motors. On real hardware, the chip runs its own program:

```c
// Tiny Arduino sketch — sized down for illustration.
// In: V <vl> <vr>    Out: E <left_ticks> <right_ticks> <ir_raw>

void setup() {
  Serial.begin(115200);
  pinMode(LEFT_PWM, OUTPUT);  pinMode(LEFT_DIR, OUTPUT);
  pinMode(RIGHT_PWM, OUTPUT); pinMode(RIGHT_DIR, OUTPUT);
  // ... encoder interrupts attached on rising edges ...
}

void loop() {
  // Read incoming command, if any
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    if (line.startsWith("V ")) {
      float vl, vr;
      sscanf(line.c_str(), "V %f %f", &vl, &vr);
      setMotorPwm(LEFT_PWM, LEFT_DIR, vl);
      setMotorPwm(RIGHT_PWM, RIGHT_DIR, vr);
    }
  }

  // Once per 20 ms, report state back
  if (millis() - lastReport >= 20) {
    int ir_raw = analogRead(IR_PIN);
    Serial.print("E "); Serial.print(left_ticks);
    Serial.print(' '); Serial.print(right_ticks);
    Serial.print(' '); Serial.println(ir_raw);
    lastReport = millis();
  }
}
```

~25 lines of Arduino C. Same protocol; just the other side of the wire. **Gazebo's `gz-sim-diff-drive-system` pretends to be this entire sketch + the motors + the world's friction + the encoders.** When you swap fake for real, this code starts running on the chip and Gazebo retires.

The IR sensor follows the same shape — a small ROS2 node parses the `<ir_raw>` field out of every `E` line, scales it to metres using whatever calibration the chip's datasheet specifies, and publishes `msg Range` (or `msg LaserScan` with one ray) on `topic /ir_front`. Drop-in replacement for Gazebo's ray sensor. **`obstacle_stop.py` doesn't notice — except possibly a one-line type change if you switch to `Range`.**

### 4. Off-the-shelf alternative: `pkg ros2_control`

Writing the serial-talking ROS2 node yourself works. But for anything beyond a teaching exercise, the community-standard path is `pkg ros2_control` — a framework that hosts the diff-drive math, the JointState publishing, and the controller loop, leaving you to write only the small bit that talks to your specific hardware. The Arduino-car case is well-trodden; the `pkg ros2_control` demos include a `diffbot` example that's almost exactly this setup.

You'd add a `<ros2_control>` block to your URDF naming the wheel joints and pointing at a hardware-interface plugin, write a YAML listing `diff_drive_controller` and `joint_state_broadcaster`, and launch the whole thing. The framework does the rest. *No kinematics code in your codebase.*

Pointer: [gz_ros2_control demos](https://github.com/ros-controls/gz_ros2_control/tree/master/gz_ros2_control_demos), especially `diffbot`. (Same `pkg ros2_control` framework can target either Gazebo or real hardware — you just swap the hardware-interface plugin. So if you graduate `tiny_bot` to `ros2_control` in sim, the upgrade path to hardware is *also* just a plugin swap.)

### 5. The contract, end to end

So when you're standing in your kitchen watching the real Arduino car drive a square, your laptop's Foxglove window is **the same view you've been using in sim — same map of where the robot thinks it is, same IR distance plot, same `cmd_vel` trace.** Same `car_mover.py` publishing the pattern. Same `obstacle_stop.py` halting it. The only thing that's different is what's behind the `/cmd_vel`, `/odom`, `/joint_states`, `/ir_front` topic boundary. That's the contract earning its keep.

---

## The reality gap, briefly

Sim and real share a lot — but not everything. Worth knowing where the gap is.

**Sim handles well:** algorithm development, message contracts, kinematics, sensor *shape* (a simulated LaserScan has the right number of rays in roughly the right ranges). Gazebo's physics gives you contact, friction, mass, basic motor dynamics — enough to develop and debug most behaviour without ever wiring real hardware.

**Sim approximates crudely:** the *characteristics* of motor dynamics (real motors have inertia, deadband, PWM nonlinearity, voltage sag under load — Gazebo's models are coarse), friction surface details (carpet vs hardwood vs concrete produces different trajectories from the same Twist), sensor noise *patterns* (real lidar noise is bursty and wavelength-dependent; sim noise is usually clean Gaussian), and timing jitter (real driver topics arrive late, sometimes out of order; sim is metronomic).

**How real teams cope:** algorithm work in sim (cheap, fast, reproducible), calibrate model parameters against measured hardware data when stakes are high (`pkg ros2_control` exposes plenty of dials), domain randomisation for ML-driven robots (train on many perturbed sims so the policy survives the gap), and always validate on hardware before declaring done.

For a beginner course, the takeaway is simpler — and it's the thesis of this whole chapter:

> ***Business logic ships unchanged across the gap. Drivers swap. That's the contract — and that's why ROS2.***

---

## Self-Check

1. What's the standard handshake for telling a wheeled robot to move? — **Answer:** Publish `msg Twist` on `topic /cmd_vel`. It's a convention, not enforced by ROS2 itself, but every teleop tool, every motor driver, and every autonomy stack assumes it.

2. In Project B, which two files were business logic and which two were drivers? — **Answer:** Business logic: `car_mover.py` (publishes the Twist pattern) and `obstacle_stop.py` (IR-aware safety filter). Drivers: Gazebo's `gz-sim-diff-drive-system` plugin (consumes Twist, moves wheels, publishes odom) and Gazebo's `<sensor type="gpu_lidar">` (raycasts against the world, publishes LaserScan on `/ir_front`).

3. Why does `obstacle_stop.py` subscribe to `topic /cmd_vel_in` instead of `topic /cmd_vel`? — **Answer:** Because it needs to *intercept* the commander's output and re-publish (possibly modified) on `/cmd_vel`, which is the canonical name the motor driver subscribes to. `car_mover.py` publishes to `/cmd_vel_in`; `obstacle_stop` forwards to `/cmd_vel` unless the IR is too close.

4. On a real Arduino car, what swaps and what stays the same? — **Answer:** Two drivers swap: the motor driver (Gazebo's diff-drive plugin → an Arduino-talking ROS2 node) and the sensor driver (Gazebo's ray sensor → a serial-parsing IR node). Two business-logic files stay identical: `car_mover.py`, `obstacle_stop.py`. Plus `robot_state_publisher`, `foxglove_bridge`, your URDF — all unchanged.

5. Why use Gazebo at all if your business logic doesn't care whether it's in sim? — **Answer:** Because Gazebo handles real physics (collision, friction, mass, motor dynamics), real geometry (walls the IR can actually see), and provides driver-equivalent plugins for free. Without it you'd have to hand-roll all of that — which buys you nothing the framework doesn't already give you.

---

## Common Mistakes

- **Both `joint_state_publisher` (from Project A) and Gazebo running:** wheels jitter or stop responding because two sources fight over `topic /joint_states`. Kill the placeholder before launching sim.
- **Both `robot_state_publisher` (from Project A) and the launch file running:** two instances both try to publish `topic /robot_description`. Kill the standalone one — the launch file starts its own.
- **Commander publishes to `/cmd_vel` instead of `/cmd_vel_in`:** `obstacle_stop` is bypassed; the IR sensor reports proximity, nothing acts on it, robot crashes into the wall. The shipped `car_mover.py` publishes to `/cmd_vel_in` correctly — only an issue if you swap in `teleop_twist_keyboard` (which publishes to `/cmd_vel` by default; use `--ros-args -r /cmd_vel:=/cmd_vel_in` to fix).
- **Display frame stuck on `tf base_link`:** the camera follows the robot, which is fine in Project A but disorienting in Project B (robot looks stationary while the world slides). Switch to `tf odom` for sim.
- **Foxglove showing stale URDF:** Foxglove caches `topic /robot_description`. Re-import the layout to force refetch.
- **Gazebo "couldn't open render engine: ogre2":** Docker container is missing a GL library. On Apple Silicon, headless mode (the launch file uses `-s`) avoids this; if you somehow ended up with a GUI mode, force headless.

---

## Resources

1. [REP-105 — Coordinate Frames for Mobile Platforms](https://www.ros.org/reps/rep-0105.html) — the convention for `tf base_link`, `tf odom`, `tf map`, `tf base_scan`, `tf imu_link`.
2. [URDF tutorial (Jazzy)](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/URDF-Main.html) — full walkthrough beyond what this chapter covers.
3. [xacro user guide](https://github.com/ros/xacro/wiki) — properties, macros, conditionals.
4. [Gazebo Sim (Harmonic) tutorials](https://gazebosim.org/docs/harmonic/tutorials) — sensors, plugins, world authoring.
5. [ros_gz_bridge docs](https://github.com/gazebosim/ros_gz/tree/ros2/ros_gz_bridge) — the YAML bridge format used here.
6. [`pkg ros2_control` docs](https://control.ros.org/jazzy/index.html) — the production-grade framework that subsumes both Gazebo's plugins and real-hardware drivers behind one interface.
7. [gz_ros2_control demos — `diffbot`](https://github.com/ros-controls/gz_ros2_control/tree/master/gz_ros2_control_demos) — a working sim diff-drive robot wired through `pkg ros2_control`. The natural next step.
8. [`pkg teleop_twist_keyboard`](https://github.com/ros2/teleop_twist_keyboard) — keyboard joystick. Plug into `topic /cmd_vel_in` and drive `tiny_bot` manually.
