# Chapter 1 — MuJoCo Fundamentals

**Time:** 1–2 days
**Hardware:** Any laptop, no GPU
**Prerequisites:** Python, basic physics intuition (what is a joint, what is a frame)

---

## Why This Chapter Exists

Every chapter in this curriculum runs inside MuJoCo. Before you can train a policy, run IK,
or collect robot demonstrations, you need to be fluent with the simulator: how to load a
robot, step the physics, read joint states and body positions, and write a basic controller.

This chapter gets you there. You'll also pick up the coordinate frame and transform concepts
you need — but grounded in a running simulation, not abstract math.

### If you can answer these, you can skip this chapter

1. You load a Franka arm in MuJoCo. How do you read the end-effector position in world space?
2. What is the difference between `model` and `data` in MuJoCo?
3. You set `data.ctrl[0] = 1.57`. What happens, and what type of actuator does that assume?

---

---

## Part 1 — The MuJoCo Mental Model

### model and data

MuJoCo splits everything into two objects:

- **`mjModel`** — the static description: geometry, masses, joint limits, actuator types.
  Loaded once from XML. Never changes during simulation.
- **`mjData`** — the live state: joint positions, velocities, contact forces, body poses.
  Updated every call to `mj_step()`.

```python
import mujoco

model = mujoco.MjModel.from_xml_string(XML)  # load once
data  = mujoco.MjData(model)                 # mutable state

mujoco.mj_step(model, data)  # advance physics by one timestep
```

Default timestep is 2ms. At each step MuJoCo reads `data.ctrl`, computes forces,
integrates dynamics, and writes new positions/velocities into `data`.

### The MJCF format

Robots are described in XML called MJCF. The key structure:

```xml
<mujoco>
  <worldbody>
    <body name="link1" pos="0 0 0">
      <joint name="joint1" type="hinge" axis="0 0 1"/>
      <geom type="capsule" size="0.04 0.2"/>
      <body name="link2" pos="0 0 0.4">
        <joint name="joint2" type="hinge" axis="0 1 0"/>
        <geom type="capsule" size="0.03 0.15"/>
      </body>
    </body>
  </worldbody>
  <actuator>
    <motor name="act1" joint="joint1" gear="100"/>
  </actuator>
</mujoco>
```

- **`body`** — a rigid link. Nested bodies are connected by joints to their parent.
- **`joint`** — how a body moves relative to its parent (`hinge` = revolute, `slide` = prismatic)
- **`geom`** — collision and visual shape attached to a body
- **`actuator`** — what generates force (`motor` = raw torque, `position` = servo)

---

## Part 2 — Coordinate Frames and Transforms

### Coordinate frames

A **frame** is just a coordinate system — an origin point plus three axes (X, Y, Z) that define
directions. Every body in a robot has one: it tells you "where is this link, and which way is it
pointing?" relative to something else.

For example, the wrist frame of a robot arm might be represented as:
- **origin:** `[0.4, 0.0, 0.6]` — where the wrist joint is in the world (in meters)
- **orientation:** a 3×3 rotation matrix describing which way it's facing

In MuJoCo, `data.xpos[body_id]` gives you the origin and `data.xmat[body_id]` gives you the
orientation — together they fully describe that body's frame in world space.

Every body in MuJoCo has a position and orientation in **world space** — the fixed global frame
anchored at the origin. When the arm moves, each link's frame moves with it.

```
world → base → shoulder → elbow → wrist → end-effector
```

Each arrow is a **transform** — a position (x, y, z) plus an orientation. MuJoCo computes
this chain automatically every time you call `mj_step()` or `mj_forward()`.

### Reading body poses from MuJoCo

```python
body_id = model.body('link2').id

pos = data.xpos[body_id]          # [x, y, z] in world frame
mat = data.xmat[body_id]          # 9 numbers — a 3×3 rotation matrix, row-major
R   = mat.reshape(3, 3)           # readable form
```

`data.xpos` and `data.xmat` are the outputs of forward kinematics — MuJoCo has already
chained all the joint transforms for you.

### What a 4×4 transform is

Papers and libraries pass around 4×4 matrices that bundle position + orientation together:

```
T = [[R00, R01, R02, tx],
     [R10, R11, R12, ty],
     [R20, R21, R22, tz],
     [0,   0,   0,   1 ]]
```

To convert a point `p` from one frame to another: `p_world = T @ [px, py, pz, 1]`.

To chain two transforms (go from frame A → B → C): `T_AC = T_AB @ T_BC`.

You'll see this in LeRobot, ROS 2, and policy papers. The math is just matrix multiplication.

### Quaternions

Orientation is also stored as quaternions in MuJoCo (`data.xquat`): `[w, x, y, z]`.

The only thing you need to know now: **convention varies by library**.
- MuJoCo: `[w, x, y, z]`
- ROS 2 / scipy: `[x, y, z, w]`

Always check before converting. Use `scipy.spatial.transform.Rotation` to convert between
quaternions, rotation matrices, and Euler angles:

```python
from scipy.spatial.transform import Rotation as R

quat_mujoco = data.xquat[body_id]          # [w, x, y, z]
quat_scipy  = quat_mujoco[[1, 2, 3, 0]]   # reorder to [x, y, z, w] for scipy
rot = R.from_quat(quat_scipy)
euler = rot.as_euler('xyz', degrees=True)
```

---

## Part 3 — Forward Kinematics

Forward kinematics (FK) answers: given joint angles, where is the end-effector?

You've been using it already — `data.xpos` after `mj_step()` or `mj_forward()` *is* the
result of FK. MuJoCo chains the transforms across every link and gives you the result.

```python
mujoco.mj_forward(model, data)   # compute FK without stepping physics
ee_id = model.body('end_effector').id
ee_pos = data.xpos[ee_id]        # world-frame EE position
```

Use `mj_forward()` (not `mj_step()`) when you want to query poses without advancing time —
useful for IK solvers, debugging, and computing observations.

---

## External Resources

1. **MuJoCo Documentation — Getting Started**
   Read "Installation", "Programming Guide", and the "mjModel / mjData" sections.
   → https://mujoco.readthedocs.io/en/stable/programming/index.html

2. **MuJoCo Tutorial Notebooks (DeepMind Colab)**
   Interactive notebooks covering the viewer, XML format, and key APIs.
   Search: "MuJoCo tutorial colab deepmind"

3. **MuJoCo Menagerie — real robot models**
   Pre-built MJCF models for Franka, UR5, SO-101, and others. You'll use these throughout.
   → https://github.com/google-deepmind/mujoco_menagerie

---

## The Problem

A robot arm has a wrist-mounted camera. It sees a cup. The controller needs to know where
the cup is in **world space** to plan a grasp — but the camera only knows where the cup is
relative to itself.

To solve this you need to know the transform from camera to world, which means you need to
know the pose of every link in the chain between them. MuJoCo gives you all of this via
`data.xpos` and `data.xmat` after `mj_forward()`.

The two projects below build up to solving this using a real robot model.

---

## Project 1A — Load a Robot, Read Its State

**What you're building:** Load the Franka Panda from MuJoCo Menagerie, open the interactive
viewer, move joints to different configurations, and read the resulting body poses. This is
the workflow you'll use in every subsequent chapter.

Create `learning/ch01_mujoco/read_robot_state.py`:

```python
"""
Load a real robot model and read joint states + body poses.
This is the first thing you do in any MuJoCo-based project.
"""
import numpy as np
import mujoco
import mujoco.viewer
import time
import os

FRANKA_XML = os.path.expanduser("~/mujoco_menagerie/franka_emika_panda/scene.xml")

def print_robot_info(model: mujoco.MjModel) -> None:
    print(f"Bodies  : {model.nbody}")
    print(f"Joints  : {model.njnt}")
    print(f"Actuators: {model.nu}")
    print("\nJoint names and limits:")
    for i in range(model.njnt):
        name = model.joint(i).name
        lo, hi = model.jnt_range[i]
        print(f"  [{i}] {name:30s}  range: [{np.degrees(lo):.0f}°, {np.degrees(hi):.0f}°]")

def read_body_poses(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    mujoco.mj_forward(model, data)  # compute FK without stepping physics
    print("\nBody positions in world frame:")
    for i in range(1, model.nbody):  # skip world body (index 0)
        name = model.body(i).name
        pos  = data.xpos[i]
        print(f"  {name:30s}  pos: {np.round(pos, 3)}")

def demo_two_configurations(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    # Configuration A: neutral pose
    mujoco.mj_resetData(model, data)
    data.qpos[:7] = [0, -0.785, 0, -2.356, 0, 1.571, 0.785]
    mujoco.mj_forward(model, data)
    ee_id = model.body("panda_hand").id
    print(f"\nNeutral pose — EE position: {np.round(data.xpos[ee_id], 3)}")

    # Configuration B: arm extended forward
    data.qpos[:7] = [0, 0, 0, -1.57, 0, 1.57, 0]
    mujoco.mj_forward(model, data)
    print(f"Extended pose — EE position: {np.round(data.xpos[ee_id], 3)}")

    print("\nNotice: same robot, different joint angles → different EE position.")
    print("This is forward kinematics. MuJoCo computed it for you.")

if __name__ == "__main__":
    if not os.path.exists(FRANKA_XML):
        print("Clone MuJoCo Menagerie first:")
        print("  git clone https://github.com/google-deepmind/mujoco_menagerie ~/mujoco_menagerie")
        exit(1)

    model = mujoco.MjModel.from_xml_path(FRANKA_XML)
    data  = mujoco.MjData(model)

    print_robot_info(model)
    read_body_poses(model, data)
    demo_two_configurations(model, data)

    print("\nLaunching viewer — move the joints with Ctrl+drag. Close to exit.")
    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            mujoco.mj_step(model, data)
            viewer.sync()
```

Run it:
```bash
cd learning/ch01_mujoco
python read_robot_state.py
```

**What to observe:** The EE position changes between the two configurations. Open the viewer,
use Ctrl+drag to move joints, and watch the printed positions update.

---

## Project 1B — Camera-to-World Transform

**What you're building:** Simulate the cup-localization problem. The wrist camera sees a cup
at a known position in camera space. Compute where it is in world space by chaining the
transforms MuJoCo gives you.

This is the exact computation that runs inside any pick-and-place policy.

Create `learning/ch01_mujoco/camera_to_world.py`:

```python
"""
Given: cup position in camera frame.
Goal:  cup position in world frame.
Method: chain body transforms from MuJoCo (xpos + xmat).
"""
import numpy as np
import mujoco
import os

FRANKA_XML = os.path.expanduser("~/mujoco_menagerie/franka_emika_panda/scene.xml")

def make_T(pos: np.ndarray, mat_flat: np.ndarray) -> np.ndarray:
    """Build a 4x4 transform from MuJoCo xpos and xmat."""
    T = np.eye(4)
    T[:3, :3] = mat_flat.reshape(3, 3)
    T[:3, 3]  = pos
    return T

def transform_point(T: np.ndarray, p: np.ndarray) -> np.ndarray:
    return (T @ np.append(p, 1.0))[:3]

def localize_cup(model: mujoco.MjModel, data: mujoco.MjData,
                 cup_in_camera: np.ndarray) -> np.ndarray:
    """
    The camera is mounted at the wrist (panda_hand).
    MuJoCo already knows where panda_hand is in world space.
    We just read that transform and apply it to the cup position.
    """
    mujoco.mj_forward(model, data)

    hand_id = model.body("panda_hand").id
    T_world_camera = make_T(data.xpos[hand_id], data.xmat[hand_id])

    return transform_point(T_world_camera, cup_in_camera)

if __name__ == "__main__":
    if not os.path.exists(FRANKA_XML):
        print("Clone MuJoCo Menagerie first.")
        exit(1)

    model = mujoco.MjModel.from_xml_path(FRANKA_XML)
    data  = mujoco.MjData(model)

    cup_in_camera = np.array([0.05, -0.12, 0.31])

    # ── Pose A: neutral arm ──────────────────────────────────────────────────
    data.qpos[:7] = [0, -0.785, 0, -2.356, 0, 1.571, 0.785]
    cup_world_A = localize_cup(model, data, cup_in_camera)
    print(f"Neutral pose  → cup in world: {np.round(cup_world_A, 3)}")

    # ── Pose B: arm rotated left 45° ─────────────────────────────────────────
    data.qpos[:7] = [0.785, -0.785, 0, -2.356, 0, 1.571, 0.785]
    cup_world_B = localize_cup(model, data, cup_in_camera)
    print(f"Arm rotated   → cup in world: {np.round(cup_world_B, 3)}")

    print()
    print("Same cup in camera space. Different world positions.")
    print("The camera moved — so the world-frame answer changed.")
    print("This is the bug you'll hit in Chapter 9 if the transform chain is wrong.")
```

Run it:
```bash
python camera_to_world.py
```

**Experiment:** Try changing `cup_in_camera` to `[0, 0, 0]` — that's the camera origin itself.
You'll get back the exact position of `panda_hand` in world space, which you can verify
against `data.xpos[hand_id]`.

---

## Self-Check

1. You call `mj_forward()` vs `mj_step()`. What's the difference?

   **Answer:** `mj_forward()` computes all derived quantities (xpos, xmat, FK) from the
   current `qpos` without advancing time. `mj_step()` also advances the physics by one
   timestep and updates velocities. Use `mj_forward()` when you want to query poses without
   simulating.

2. `data.xmat[body_id]` returns 9 numbers. What are they?

   **Answer:** A 3×3 rotation matrix stored row-major as a flat array. Reshape with
   `.reshape(3, 3)` to use it.

3. You move joint 0 from 0° to 45°. Which body poses change?

   **Answer:** All bodies downstream of joint 0 in the kinematic chain. Any link attached
   to or descended from that joint moves.

4. The cup-localization script gives a wrong world position. You suspect the joint angles
   are off. How do you debug it?

   **Answer:** Print `data.xpos[hand_id]` and verify visually in the viewer that the hand
   is where you expect. Then check that `data.qpos` matches what you set before calling
   `mj_forward()`.

5. A policy outputs a target end-effector position in world frame. The robot needs it in
   base frame. What do you do?

   **Answer:** Read `T_world_base` from `data.xpos` and `data.xmat` for the base body.
   Invert it, then apply to the world-frame target:
   `p_base = transform_point(np.linalg.inv(T_world_base), p_world)`.

---

## Common Mistakes

**Forgetting `mj_forward()` after setting `qpos`.** If you set `data.qpos` directly and
read `data.xpos` without calling `mj_forward()`, you get stale values from the previous step.

**Quaternion convention mismatch.** MuJoCo `data.xquat` is `[w, x, y, z]`. scipy and ROS 2
use `[x, y, z, w]`. Always reorder before passing to external libraries.

**Reading `xmat` as a 3×3 directly.** It's stored flat (9 values). Always `.reshape(3, 3)`.

---

## What's Next

Chapter 2 puts the sim to work: you'll write a PD controller to hold a joint at a target
angle, tune the gains, and wrap everything into a Gymnasium environment — the interface
every RL and IL library expects.
