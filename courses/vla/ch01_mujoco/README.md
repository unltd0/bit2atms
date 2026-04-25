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

**Install:**
```bash
pip install mujoco numpy matplotlib scipy pink pin robot_descriptions quadprog
git clone https://github.com/google-deepmind/mujoco_menagerie ~/mujoco_menagerie
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

- **`mjModel`** — the static description: geometry, masses, joint limits, actuator types.
  Loaded once from an XML file. Never changes during simulation.
- **`mjData`** — the live state: joint positions, velocities, contact forces, body poses.
  Updated every call to `mj_step()`.

```python
import mujoco

model = mujoco.MjModel.from_xml_path("scene.xml")  # load once
data  = mujoco.MjData(model)                        # mutable state
mujoco.mj_step(model, data)                         # advance physics one timestep
```

Default timestep is 2 ms. At each step MuJoCo reads `data.ctrl`, computes forces,
integrates dynamics, and writes new positions/velocities into `data`.

### Coordinate frames

A **frame** is a coordinate system attached to a body — an origin `[x, y, z]` plus three
axes (X, Y, Z). Every link in a robot has one. It answers: *where is this body?* and
*which way is it facing?*

MuJoCo gives you `data.xpos[body_id]` (the origin) and `data.xmat[body_id]` (a 3×3
rotation matrix stored flat as 9 numbers — reshape to use it). These are computed by
**forward kinematics** — chaining all the joint transforms from base to tip.

Use `mj_forward()` to recompute poses from the current joint angles without advancing time:

```python
mujoco.mj_forward(model, data)
body_id = model.body("panda_hand").id
pos = data.xpos[body_id]          # [x, y, z] world frame
R   = data.xmat[body_id].reshape(3, 3)
```

### The code

```python workspace/vla/ch01/read_robot_state.py
"""Load the Franka Panda, read joint states and body poses in two configurations."""
import numpy as np
import mujoco
import mujoco.viewer
import os

FRANKA_XML = os.path.expanduser("~/mujoco_menagerie/franka_emika_panda/scene.xml")

def print_robot_info(model: mujoco.MjModel) -> None:
    print(f"Bodies: {model.nbody}  Joints: {model.njnt}  Actuators: {model.nu}")
    print("\nJoint names and limits:")
    for i in range(model.njnt):
        name = model.joint(i).name
        lo, hi = model.jnt_range[i]
        print(f"  [{i}] {name:30s}  [{np.degrees(lo):.0f}°, {np.degrees(hi):.0f}°]")

def read_body_poses(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    mujoco.mj_forward(model, data)
    print("\nBody positions (world frame):")
    for i in range(1, model.nbody):
        print(f"  {model.body(i).name:30s}  {np.round(data.xpos[i], 3)}")

def demo_two_configurations(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    ee_id = model.body("panda_hand").id

    mujoco.mj_resetData(model, data)
    # qpos[:7] = the 7 joint angles in radians, one per DOF (shoulder → wrist)
    data.qpos[:7] = [0, -0.785, 0, -2.356, 0, 1.571, 0.785]
    mujoco.mj_forward(model, data)
    print(f"\nNeutral pose  — EE: {np.round(data.xpos[ee_id], 3)}")

    data.qpos[:7] = [0.785, -0.785, 0, -2.356, 0, 1.571, 0.785]
    mujoco.mj_forward(model, data)
    print(f"Rotated pose  — EE: {np.round(data.xpos[ee_id], 3)}")
    print("\nSame arm, joint 0 rotated 45° → different EE position. That's FK.")

if __name__ == "__main__":
    if not os.path.exists(FRANKA_XML):
        print("Troubleshooting: clone Menagerie first:")
        print("  git clone https://github.com/google-deepmind/mujoco_menagerie ~/mujoco_menagerie")
        raise SystemExit(1)

    model = mujoco.MjModel.from_xml_path(FRANKA_XML)
    data  = mujoco.MjData(model)
    print_robot_info(model)
    read_body_poses(model, data)
    demo_two_configurations(model, data)

    print("\nLaunching viewer — Ctrl+drag to move joints. Close to exit.")
    print("(Skip the viewer block if running headless/SSH — the printed output above is the deliverable.)")
    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            mujoco.mj_step(model, data)
            viewer.sync()
```

**What to observe:** The EE position changes between the two joint configurations —
that's **forward kinematics (FK)**. Open the viewer, drag joints, watch the printed
positions update.

**Headless / no display?** Comment out the `with mujoco.viewer...` block. The two
`print(f"... pose — EE: ...")` lines above it are the actual deliverable.

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

To convert a point from one frame to another: `p_world = T @ [px, py, pz, 1]`

The appended `1` is a math convention that makes the matrix multiply handle both rotation
and translation in one step. The result's last element is always 1 — discard it to get back
to `[x, y, z]`. That's what `transform_point()` does with `[:3]`.

To chain two transforms (A→B→C): `T_AC = T_AB @ T_BC`

### Quaternions (brief note)

MuJoCo also stores orientation as a **quaternion** in `data.xquat`: `[w, x, y, z]`.
A quaternion is a compact 4-number rotation representation. `[x, y, z]` is the rotation
axis; `w` encodes magnitude. Identity (no rotation) = `[1, 0, 0, 0]`. Use
`scipy.spatial.transform.Rotation` to convert — but watch the convention: MuJoCo is
`[w, x, y, z]`, scipy and ROS 2 are `[x, y, z, w]`.

### The code

```python workspace/vla/ch01/camera_to_world.py
"""
Given a cup position in camera (wrist) frame, compute its world-frame position.
The core transform computation used in every pick-and-place pipeline.
"""
import numpy as np
import mujoco
import os

FRANKA_XML = os.path.expanduser("~/mujoco_menagerie/franka_emika_panda/scene.xml")

def make_T(pos: np.ndarray, mat_flat: np.ndarray) -> np.ndarray:
    """Build a 4×4 homogeneous transform from MuJoCo xpos and xmat."""
    T = np.eye(4)
    T[:3, :3] = mat_flat.reshape(3, 3)
    T[:3, 3]  = pos
    return T

def transform_point(T: np.ndarray, p: np.ndarray) -> np.ndarray:
    return (T @ np.append(p, 1.0))[:3]

def localize_cup(model: mujoco.MjModel, data: mujoco.MjData,
                 cup_in_camera: np.ndarray) -> np.ndarray:
    mujoco.mj_forward(model, data)
    hand_id = model.body("panda_hand").id
    T_world_camera = make_T(data.xpos[hand_id], data.xmat[hand_id])
    return transform_point(T_world_camera, cup_in_camera)

if __name__ == "__main__":
    if not os.path.exists(FRANKA_XML):
        print("Troubleshooting: clone Menagerie first.")
        raise SystemExit(1)

    model = mujoco.MjModel.from_xml_path(FRANKA_XML)
    data  = mujoco.MjData(model)
    cup_in_camera = np.array([0.05, -0.12, 0.31])

    data.qpos[:7] = [0, -0.785, 0, -2.356, 0, 1.571, 0.785]
    print(f"Neutral pose  → cup in world: {np.round(localize_cup(model, data, cup_in_camera), 3)}")

    data.qpos[:7] = [0.785, -0.785, 0, -2.356, 0, 1.571, 0.785]
    print(f"Rotated pose  → cup in world: {np.round(localize_cup(model, data, cup_in_camera), 3)}")

    print("\nSame cup in camera space. Different world positions.")
    print("Try: set cup_in_camera = [0,0,0] → you get panda_hand's exact world position.")
```

---

## Project C — PD Controller: Tune the Gains

**Problem:** You need the robot to hold a target joint configuration using `motor`
actuators — which means you write the control loop yourself.

**Approach:** Build a minimal 2-DOF arm with motor actuators, implement a PD controller,
run it with four gain combinations, and plot the trajectories.

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

```python workspace/vla/ch01/pd_controller.py
"""
PD controller on a 2-DOF arm. Run 4 kp/kd combinations and plot trajectories.
Shows how gain tuning changes stability.
"""
import os
import numpy as np
import matplotlib.pyplot as plt
import mujoco

ARM_XML = """
<mujoco>
  <option timestep="0.002"/>
  <worldbody>
    <body name="link1" pos="0 0 0">
      <joint name="j1" type="hinge" axis="0 0 1" range="-3.14 3.14"/>
      <geom type="capsule" size="0.04 0.2" pos="0 0 0.2"/>
      <body name="link2" pos="0 0 0.4">
        <joint name="j2" type="hinge" axis="0 1 0" range="-3.14 3.14"/>
        <geom type="capsule" size="0.03 0.15" pos="0 0 0.15"/>
      </body>
    </body>
  </worldbody>
  <actuator>
    <motor name="m1" joint="j1" ctrllimited="true" ctrlrange="-10 10"/>
    <motor name="m2" joint="j2" ctrllimited="true" ctrlrange="-10 10"/>
  </actuator>
</mujoco>
"""

TARGET       = np.array([0.5, -0.3])
SIM_DURATION = 3.0

def run_pd(kp: float, kd: float) -> tuple[np.ndarray, np.ndarray]:
    model = mujoco.MjModel.from_xml_string(ARM_XML)
    data  = mujoco.MjData(model)
    steps = int(SIM_DURATION / model.opt.timestep)
    time  = np.zeros(steps)
    q     = np.zeros((steps, 2))
    for i in range(steps):
        data.ctrl[:2] = kp * (TARGET - data.qpos[:2]) - kd * data.qvel[:2]
        mujoco.mj_step(model, data)
        time[i] = data.time
        q[i]    = data.qpos[:2]
    return time, q

if __name__ == "__main__":
    configs = [
        (50,  1,  "kp=50  kd=1   underdamped"),
        (50,  10, "kp=50  kd=10  well-tuned"),
        (200, 1,  "kp=200 kd=1   oscillates"),
        (200, 30, "kp=200 kd=30  well-tuned high stiffness"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("PD Controller — joint 1 trajectory")
    for ax, (kp, kd, label) in zip(axes.flat, configs):
        time, q = run_pd(kp, kd)
        ax.plot(time, np.degrees(q[:, 0]))
        ax.axhline(np.degrees(TARGET[0]), color="r", linestyle="--", label="target")
        ax.set_title(label); ax.set_xlabel("time (s)"); ax.set_ylabel("angle (deg)")
        ax.legend()
    plt.tight_layout()
    out = os.path.join(os.path.dirname(__file__), "pd_gains.png")
    plt.savefig(out)
    print(f"Saved {out}")
```

**What to observe:** Underdamped configs oscillate; well-tuned ones converge smoothly.
Scale gains up ~4× for a heavier arm like the Franka Panda.

---

## Project D — IK Solver: Reach Any Target

**Problem:** Given a desired end-effector position in world space, find the joint angles
that put the hand there — this is **inverse kinematics (IK)**.

**Approach:** Use Pink, a differential IK library. At each timestep Pink solves for the
joint velocity that moves the end-effector toward the target, then integrates it.

Pink uses **Pinocchio** — a separate kinematics library — internally. So you load the
robot twice: once into MuJoCo for physics and visualization, once into Pinocchio for IK.
Pink computes new joint angles; you copy them into MuJoCo's `qpos` each step to keep the
viewer in sync. Both models must describe the same robot — `panda_description` and the
Menagerie Franka match on the 7 arm joints used here.

### Why IK needs a library

FK is just matrix multiplication along the chain. IK is harder:
- Many joint configs can reach the same position (redundancy)
- Some positions are unreachable
- Near **singularities** (configurations where the arm loses a degree of freedom), naive
  approaches explode

Pink uses the **Jacobian** — a matrix mapping joint velocities to end-effector velocity —
to solve a constrained optimization problem at each step. It handles joint limits,
singularities, and multiple simultaneous tasks. [Read more: Pink docs](https://jmirabel.github.io/pink/)

### The code

```python workspace/vla/ch01/ik_solver.py
"""
Pink IK solver on the Franka Panda. Move the end-effector to any 3D target.
"""
import numpy as np
import mujoco
import mujoco.viewer
import pink
from pink.tasks import FrameTask
import pinocchio as pin
from robot_descriptions.loaders.pinocchio import load_robot_description
import os, time as time_module

FRANKA_XML = os.path.expanduser("~/mujoco_menagerie/franka_emika_panda/scene.xml")

if __name__ == "__main__":
    if not os.path.exists(FRANKA_XML):
        print("Troubleshooting: clone Menagerie first.")
        raise SystemExit(1)

    # Load into MuJoCo
    mj_model = mujoco.MjModel.from_xml_path(FRANKA_XML)
    mj_data  = mujoco.MjData(mj_model)
    mj_data.qpos[:7] = [0, -0.785, 0, -2.356, 0, 1.571, 0.785]
    mujoco.mj_forward(mj_model, mj_data)

    # Load into Pink/Pinocchio for IK
    robot = load_robot_description("panda_description")
    configuration = pink.Configuration(robot.model, robot.data, robot.q0)

    # IK task: reach target position
    ee_task = FrameTask("panda_hand", position_cost=1.0, orientation_cost=0.0)
    target = pin.SE3.Identity()
    target.translation = np.array([0.5, 0.1, 0.4])   # ← change this
    ee_task.set_target(target)

    dt = mj_model.opt.timestep

    with mujoco.viewer.launch_passive(mj_model, mj_data) as viewer:
        while viewer.is_running():
            velocity = pink.solve_ik(configuration, [ee_task], dt, solver="quadprog")
            configuration.integrate_inplace(velocity, dt)
            mj_data.qpos[:7] = configuration.q[:7]   # Pinocchio q may include finger joints; take arm DOFs only
            mujoco.mj_forward(mj_model, mj_data)
            viewer.sync()
            time_module.sleep(dt)
```

**Experiment:** Change `target.translation` to different positions. Try `[0.8, 0.0, 0.3]`
(near workspace edge) and watch how the arm reaches — or stops when it can't.

---

## Self-Check

1. You call `mj_forward()` vs `mj_step()`. What's the difference?
   **Answer:** `mj_forward()` recomputes all derived quantities (xpos, xmat) from the
   current `qpos` without advancing time or physics. `mj_step()` also integrates dynamics
   by one timestep. Use `mj_forward()` for pose queries; `mj_step()` for simulation.

2. You set `data.qpos[:7]` then immediately read `data.xpos`. Why might values be stale?
   **Answer:** `data.xpos` only updates after `mj_forward()` or `mj_step()`. Setting
   `qpos` directly skips recomputation — always follow with `mj_forward()`.

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

1. [MuJoCo Programming Guide](https://mujoco.readthedocs.io/en/stable/programming/index.html) — read the mjModel/mjData and Simulation sections
2. [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie) — all robot models used in this course
3. [Pink documentation](https://jmirabel.github.io/pink/) — task definitions and solver API
4. [MuJoCo Tutorial Colab (DeepMind)](https://colab.research.google.com/github/deepmind/mujoco/blob/main/python/tutorial.ipynb) — interactive walkthrough of viewer and core API
