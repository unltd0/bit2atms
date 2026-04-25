# Chapter 1 — MuJoCo & Robot Fundamentals

**Time:** 2–3 days
**Hardware:** Laptop only
**Prerequisites:** Python, NumPy basics

---

## What are we here for

Every chapter in this course runs inside MuJoCo — a fast, accurate physics simulator used
by DeepMind, Google, and most serious robot learning labs. Before you can train a policy,
collect demonstrations, or run IK, you need to be fluent with it: how to load a robot, step
the physics, read where things are, make joints move, and plan end-effector paths.

This chapter covers all of that in four projects. You'll load a real robot model, localize
objects using camera transforms, write a controller that holds a pose, and solve for joint
angles that put the hand wherever you want. These four skills appear in every subsequent
chapter.

**Install:** (run from the repo root)
```bash
# mujoco       — physics simulator engine
# numpy        — array math
# matplotlib   — plotting trajectories and images
# scipy        — scientific computing (Rotation, etc.)
# pin-pink     — inverse kinematics solver (NOT 'pink' which is a code formatter)
# pinocchio    — kinematics library that Pink builds on top of
# robot_descriptions — fetches robot URDF/XML models from GitHub
# quadprog     — quadratic programming backend for IK optimization
pip install mujoco numpy matplotlib scipy pin-pink pinocchio robot_descriptions quadprog
git clone https://github.com/google-deepmind/mujoco_menagerie workspace/ext/mujoco_menagerie
```

**Skip if you can answer:**
1. You load a Franka arm. How do you read the end-effector position in world space?
2. You set `data.ctrl[0] = 1.57` on a `position` actuator. What happens?
3. Your PD controller oscillates but doesn't settle. Which gain do you increase?
4. You want the hand at `[0.5, 0.0, 0.4]`. How do you find the joint angles?

---

## Projects

| # | Project | What you build |
|---|---------|---------------|
| A | Load a Robot, Read Its State | Load Franka Panda, print joint states and body poses in two configurations |
| B | Camera-to-World Transform | Localize a simulated cup from wrist-camera coordinates to world coordinates |
| C | PD Controller | Hold a target joint pose; plot four kp/kd combinations |
| D | IK Solver | Move the end-effector to any 3D target using Pink differential IK |

---

## Project A — Load a Robot, Read Its State

**Problem:** Before you can control a robot, you need to understand what MuJoCo gives you
and how to read the state of a loaded model.

**Approach:** Load the Franka Panda from Menagerie, open the interactive viewer, set two
joint configurations, and print the resulting body poses.

### MuJoCo's two core objects

MuJoCo splits everything into two objects:

- **`MjModel`** — the static description: geometry, masses, joint limits, actuator types. Load it once from an XML file; it never changes.
- **`MjData`** — the live state: joint positions, velocities, body poses, contact forces. Updated every call to `mj_step()`.

> **Quick note on two key functions:**
> - `mj_forward(model, data)` — recomputes derived quantities (body positions, rotation matrices) from current joint angles **without advancing time**. Use this when you just want to query poses.
> - `mj_step(model, data)` — advances physics by one timestep (integrates dynamics, applies gravity, handles collisions). Use this for simulation loops.

`mj_step(model, data)` advances physics by one timestep (default 2 ms): reads `data.ctrl`, computes forces, writes results back to `data`.

You can verify this yourself:

```python
import mujoco, os
xml = "workspace/ext/mujoco_menagerie/franka_emika_panda/scene.xml"
assert os.path.exists(xml), "Clone Menagerie first: git clone https://github.com/google-deepmind/mujoco_menagerie workspace/ext/mujoco_menagerie"
model = mujoco.MjModel.from_xml_path(xml)
data  = mujoco.MjData(model)
print(f"Time before step: {data.time:.4f}s")
mujoco.mj_step(model, data)
print(f"Time after step:  {data.time:.4f}s  (Δ = {model.opt.timestep*1000:.1f} ms)")
print(f"Joint 0 position: {data.qpos[0]:.4f} rad  (unchanged — no control signal yet)")
```

Run from the repo root.

### Coordinate frames

A **frame** is a coordinate system attached to a body — an origin `[x, y, z]` plus three
axes (X, Y, Z). Every link in a robot has one. It answers: *where is this body?* and
*which way is it facing?*

> **Franka Panda** — a 7-DOF collaborative arm by Franka Engineering, widely used in
> robotics research. The Menagerie model (`franka_emika_panda`) is the official simulation
> description from Google DeepMind.

MuJoCo gives you `data.xpos[body_id]` (the origin) and `data.xmat[body_id]` (a 3×3
rotation matrix stored flat as 9 numbers — reshape to use it). These are computed by
**forward kinematics** — chaining all the joint transforms from base to tip.

Use `mj_forward()` to recompute poses from the current joint angles without advancing time:

```python
mujoco.mj_forward(model, data)
body_id = model.body("hand").id
pos = data.xpos[body_id]          # [x, y, z] world frame
R   = data.xmat[body_id].reshape(3, 3)
```

### The code

```python courses/vla/ch01_mujoco/code/read_robot_state.py
```

**What to observe:** The terminal prints EE and body positions for the neutral pose then
the rotated pose — that's **forward kinematics (FK)**. Same joints, different angles,
different EE position.

**What to expect in the viewer:** The arm launches in the rotated pose with no control
signal and falls under gravity — that's expected. To explore poses: double-click a body
to select it, then use the joint sliders in the right UI panel. Ctrl+drag on a selected
body applies an external force perturbation (not joint control).

**Headless / no display?** Comment out the `with mujoco.viewer...` block at the bottom
of the script. The EE and body position printouts from `demo_two_configurations` are the
actual deliverable.

---

## Project B — Camera-to-World Transform

**Problem:** A wrist-mounted camera sees a cup at a known position in camera space.
The controller needs the cup's position in *world* space to plan a grasp.

**Approach:** Read the wrist body's transform from MuJoCo (`xpos` + `xmat`) and apply
it to the cup's camera-frame position. MuJoCo has already done the FK — you just use it.

In a real pipeline the cup position in camera space would come from a depth camera or
object detector. Here we hardcode it (`cup_in_camera = [0.05, -0.12, 0.31]`) to focus on
the transform math without needing real hardware. The math is identical either way.

### The 4×4 transform matrix

Papers and libraries bundle position + orientation into a single 4×4 matrix:

```text 4×4 transform
T = [[R00, R01, R02, tx],   ← rotation (3×3)  |  tx = x position
     [R10, R11, R12, ty],                      |  ty = y position
     [R20, R21, R22, tz],                      |  tz = z position
     [0,   0,   0,   1 ]]   ← always this row (math convention for chaining)
```

To convert a point from one frame to another: `p_world = T @ [px, py, pz, 1]`.
Think of it as "apply the arm's rotation then shift by its position" — the matrix bundles
both operations into one multiplication. The appended `1` is a math convention that makes the matrix multiply handle both rotation
and translation in one step. The result's last element is always 1 — discard it to get back
to `[x, y, z]`. That's what `transform_point()` does with `[:3]`.

To chain two transforms (A→B→C): `T_AC = T_AB @ T_BC`

### Quaternions (brief note)

MuJoCo also stores orientation as a **quaternion** in `data.xquat`: `[w, x, y, z]`.
A quaternion is a compact 4-number rotation representation. `[x, y, z]` is the rotation
axis; `w` encodes magnitude. Identity (no rotation) = `[1, 0, 0, 0]`. Use
`scipy.spatial.transform.Rotation` to convert — but watch the convention: MuJoCo is
`[w, x, y, z]`, scipy and ROS 2 are `[x, y, z, w]`. You won't need this conversion until
Chapter 6 (ROS 2), but keep it in mind — mixing conventions causes silent bugs.

### The code

```python courses/vla/ch01_mujoco/code/camera_to_world.py
```

**Run it:** `python courses/vla/ch01_mujoco/code/camera_to_world.py` from the repo root.

**What to observe:** You'll see two lines like:
```
Cup world position (neutral pose):  [0.52  0.08  0.43]
Cup world position (rotated pose):  [0.38  0.23  0.41]
```
Same cup, same camera offset, different world positions — because the arm is pointing
somewhere different. Sanity check: set `cup_in_camera = [0, 0, 0]` in the script and rerun —
the output should exactly match the hand's world position printed above it.

---

## Project C — PD Controller: Tune the Gains

**Problem:** You need the robot to hold a target joint configuration using `motor`
actuators — which means you write the control loop yourself.

**Approach:** Build a minimal 2-DOF (degrees of freedom = independently controllable joints)
arm with motor actuators, implement a PD controller, run it with four gain combinations,
and plot the trajectories.

We use a custom 2-DOF arm here, not the Franka. The Franka Menagerie model uses
`position` actuators (built-in PD servo — MuJoCo does the control for you). To write and
tune a PD controller yourself you need `motor` actuators, so we define a simple arm in XML.
The principle transfers directly to any motor-actuated hardware.

### Actuators

An **actuator** is what makes a joint move — the motor attached to it. In MuJoCo you
declare it in XML and command it via `data.ctrl`. Three types:

- **`motor`** — applies raw torque. You stabilize the joint yourself.
- **`position`** — built-in PD servo. Set a target angle; MuJoCo drives there.
- **`velocity`** — set a target joint velocity.

For this project you use `motor` so you implement the full control loop.

### PD control

**P (proportional):** push toward target in proportion to the error.
**D (derivative):** brake in proportion to current velocity — prevents overshoot.

```text PD formula
torque = kp × (target_angle − current_angle) − kd × current_velocity
```

- Too little `kp` → slow response
- Too much `kp` → oscillation
- `kd` damps the oscillation

### The code

```python courses/vla/ch01_mujoco/code/pd_controller.py
```

**What to observe:** The script saves `pd_gains.png` in your working directory. Open it
to see the four trajectories side by side — underdamped configs oscillate, well-tuned ones
converge smoothly. Scale gains up ~4× for a heavier arm like the Franka Panda.

---

## Project D — IK Solver: Reach Any Target

**Problem:** Given a desired end-effector position in world space, find the joint angles
that put the hand there — this is **inverse kinematics (IK)**.

**Approach:** Use Pink, a differential IK library. At each timestep Pink solves for the
joint velocity that moves the end-effector toward the target, then integrates it.

### Why two separate loads?

MuJoCo handles physics simulation (gravity, collisions, dynamics). Pink/Pinocchio handle
inverse kinematics optimization (finding joint angles for a target pose). They're separate
libraries with different APIs and data structures, so we load the robot into both.

Pink uses **Pinocchio** — a separate kinematics library — internally. So you load the
robot twice: once into MuJoCo for physics and visualization, once into Pinocchio for IK.
Pink computes new joint angles; you copy them into MuJoCo's `qpos` each step to keep the
viewer in sync. Both models must describe the same robot — `panda_description` and the
Menagerie Franka match on the 7 arm joints used here.

### Why IK needs a library

FK is just matrix multiplication along the chain. IK is harder:
- Many joint configs can reach the same position (redundancy)
- Some positions are unreachable
- Near **singularities** — configurations where the arm loses a degree of freedom
  (like fully extending a straight arm) — naive approaches explode into infinite joint velocities

Pink uses the **Jacobian** — a matrix mapping joint velocities to end-effector velocity —
to solve a constrained optimization problem at each step. It handles joint limits,
singularities, and multiple simultaneous tasks. [Read more: Pink docs](https://stephane-caron.github.io/pink/)

### The code

```python courses/vla/ch01_mujoco/code/ik_solver.py
```

**Note:** The loop uses `mj_forward()` not `mj_step()` — physics don't advance. The arm
teleports joint-by-joint to each IK solution. This is intentional: we're solving geometry,
not simulating dynamics. You'd add `mj_step()` when you need contact forces or inertia.

> **Debugging tip:** The viewer runs in the foreground and blocks the terminal. To add
> debug prints, comment out the viewer block and use manual `mj_forward()` + print calls.

**Experiment:** Change `target.translation` to different positions. Try `[0.8, 0.0, 0.3]`
(near workspace edge) and watch how the arm reaches — or stops when it can't.

---

## Self-Check

1. You call `mj_forward()` vs `mj_step()`. What's the difference?
   **Answer:** `mj_forward()` recomputes all derived quantities (xpos, xmat) from the
   current `qpos` without advancing time or physics. `mj_step()` also integrates dynamics
   by one timestep. Use `mj_forward()` for pose queries; `mj_step()` for simulation.

2. You run `mj_step()` with `data.ctrl` all zeros. What happens to the arm?
   **Answer:** With no control torques, gravity pulls every joint toward its lowest-energy
   position. The arm falls. This is why a viewer loop without control looks like a collapse —
   you need either a control signal or `position` actuators to hold a pose.

3. Your PD controller settles slowly without oscillation. What do you change first?
   **Answer:** Increase `kp`. If it then oscillates, increase `kd`. Tune in that order —
   `kp` sets the speed, `kd` damps the response.

4. `data.xmat[body_id]` returns 9 numbers. What are they and how do you use them?
   **Answer:** A 3×3 rotation matrix stored row-major as a flat array. Call `.reshape(3, 3)`.
   Each row is one of the body's local axes expressed in world coordinates.

5. In Project D you set `orientation_cost=0.0`. What does that mean for the IK solution?
   **Answer:** Pink ignores orientation — it only tries to match the position. The arm
   will reach the target but may arrive at any orientation. Set `orientation_cost > 0`
   and provide a full `SE3` target to also constrain how the hand faces.

---

## Common Mistakes

- **Forgetting `mj_forward()` after setting `qpos`:** `data.xpos` reflects the last
  computed state. Set `qpos`, then call `mj_forward()`.

- **Quaternion convention mismatch:** `data.xquat` is `[w, x, y, z]`. scipy and ROS 2
  expect `[x, y, z, w]`. Reorder with `q[[1,2,3,0]]` before passing to external libraries.

- **`xmat` used raw:** It's 9 flat values — always `.reshape(3, 3)` before matrix ops.

- **Copying PD gains between robots:** Gains depend on link mass and inertia. Start with
  `kp=100, kd=10` for a light arm; scale up 4–10× for a full Franka Panda.

- **IK diverging near singularities:** Add a `PostureTask` to keep the arm near a neutral
  configuration — this regularizes the IK and prevents runaway joint velocities.

- **MuJoCo and Pinocchio models out of sync (Project D):** `panda_description` and
  the Menagerie MJCF describe the same 7-DOF arm but may differ in finger joints or base
  frames. If the viewer shows wrong poses, print `configuration.q` length vs `mj_model.nq`
  and check the slice — you may need `[:7]` or a different offset.

---

## Resources

1. [MuJoCo Programming Guide](https://mujoco.readthedocs.io/en/stable/programming/index.html) — read the MjModel/MjData and Simulation sections
2. [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie) — all robot models used in this course
3. [Pink documentation](https://jmirabel.github.io/pink/) — task definitions and solver API
4. [MuJoCo Tutorial Colab (DeepMind)](https://colab.research.google.com/github/deepmind/mujoco/blob/main/python/tutorial.ipynb) — interactive walkthrough of viewer and core API
