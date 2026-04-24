# Chapter 3 — Robot Kinematics & Motion Planning

**Time:** 3–4 days
**Hardware:** Any laptop, no GPU
**Prerequisites:** Chapters 1–2 (MuJoCo basics, PD control)

---

## Why This Chapter Exists

In Chapter 2 you wrote a PD controller that holds a target joint angle. That's useful, but the moment you want to do anything practical — move the hand to a target position, follow a trajectory, execute a pick — you need to work in Cartesian space (X, Y, Z) and convert automatically to joint angles. That conversion is IK.

The deeper gap this fills: learned policies (Chapter 5 onward) output actions in Cartesian space. To execute them on a real or simulated robot, something has to turn those Cartesian targets into joint commands. That something is what you build here.

### If you can answer these, you can skip this chapter

1. A robot arm has 6 joints. Its end-effector is at position `p` in world space. You want to move it 2 cm in the +X direction. How do you compute the required change in joint angles without solving the full geometric IK?
2. What is a kinematic singularity, and what actually goes wrong when you're near one?

---

## Part 1 — Forward Kinematics (Quick Recap)

You already used FK in Chapter 1: `mj_forward()` takes joint angles and gives you body
positions in world space via `data.xpos`. That's FK — nothing more.

For IK we need the inverse: given a desired end-effector position, find the joint angles.
Pink handles this. But to use it well, you need to understand the Jacobian — the bridge
between joint space and Cartesian space.

---

## Part 2 — Inverse Kinematics

### Why IK Is Hard

You want the end-effector at position `p*`. What joint angles produce that?

Problems:
1. **Multiple solutions:** A 6-DOF arm can often reach a point in multiple configurations (elbow up vs. elbow down, shoulder front vs. shoulder back). There are infinitely many for redundant 7-DOF arms.
2. **No solution:** The target might be outside the reachable workspace.
3. **Singularities:** At certain configurations, small end-effector motions require infinite joint velocities.
4. **Nonlinearity:** The FK equations are nonlinear trig functions → no closed-form inverse in general.

### Two Approaches to IK

**Analytical IK:** Closed-form solution for specific robot geometries (Puma 560, Franka with special structure). Fast, finds all solutions. Not general.

**Numerical (Differential) IK:** Iterative gradient-based approach. Works for any robot. This is what Pink uses.

The iterative approach:
1. Start from current joint angles `q`
2. Compute FK to get current EE pose
3. Compute the error between current and target
4. Compute the Jacobian `J`
5. Update: `Δq = J⁺ · Δx` where `J⁺` is the pseudoinverse of J
6. Repeat until error < threshold

---

## Part 3 — The Jacobian (The Most Important Tool in Robot Control)

### What the Jacobian Is

The Jacobian `J` is a 6×n matrix (for a 6-DOF task space and n joints) that maps joint velocities to end-effector velocity:

```
ẋ = J(q) · q̇
```

Where:
- `ẋ = [vx, vy, vz, ωx, ωy, ωz]` — 6D end-effector velocity (linear + angular)
- `q̇ = [q̇1, ..., q̇n]` — joint velocities

### Why the Jacobian Matters

1. **Cartesian velocity control:** If you want the EE to move at velocity `ẋ`, compute `q̇ = J⁺ · ẋ`
2. **IK updates:** `Δq = J⁺ · Δx` (linearized FK inverse)
3. **Singularity detection:** When `det(J·Jᵀ)` → 0, the robot is near a singularity
4. **Force control:** Transpose Jacobian maps task-space forces to joint torques: `τ = Jᵀ · F`

### The Pseudoinverse

For a non-square matrix J (6×7 for a 7-DOF arm), the Moore-Penrose pseudoinverse is:
```
J⁺ = Jᵀ(JJᵀ)⁻¹
```

This gives the minimum-norm joint velocity solution. For redundant arms (more joints than DOF), there are extra DOFs you can use for secondary tasks (joint limit avoidance, singularity avoidance).

### Damped Pseudoinverse (Near Singularities)

Near singularities, `J⁺` blows up. The damped pseudoinverse:
```
J⁺_damped = Jᵀ(JJᵀ + λ²I)⁻¹
```

Where λ (damping factor) prevents division by near-zero values. Typically `λ = 0.01` to `0.1`.

---

## Part 4 — Pink: The IK Library

Pink is a differential IK library built on Pinocchio (a rigid body dynamics library). It formulates IK as a Quadratic Program (QP) — an optimization problem that you can add constraints to.

### Why Pink Over Writing Your Own?

Pink handles:
- Joint limits (hard constraints)
- Multiple simultaneous tasks (position + orientation + joint posture)
- Velocity limits
- Singularity handling (damped QP automatically)
- Works with any robot (reads URDF or MJCF via Pinocchio)

### Core Pink Concepts

```python
import pink
from pink import solve_ik
from pink.tasks import FrameTask, PostureTask

# Build a configuration from a robot model
configuration = pink.Configuration(robot.model, robot.data, q0)

# Define tasks
end_effector_task = FrameTask(
    "panda_hand",           # frame name in the model
    position_cost=1.0,      # weight for position error
    orientation_cost=0.1,   # weight for orientation error
)

posture_task = PostureTask(
    cost=1e-3               # small weight: prefer staying near default pose
)

# Set targets
end_effector_task.set_target(target_SE3)  # pin.SE3 object
posture_task.set_target(q_default)

# Solve: returns joint velocity
velocity = solve_ik(
    configuration,
    [end_effector_task, posture_task],
    dt=0.01,
    solver="quadprog"
)

# Integrate to get new q
q_new = configuration.integrate(velocity, dt=0.01)
```

### Install

```bash
pip install pin pink quadprog
```

Verify:
```bash
python -c "import pink; print('pink OK')"
```

---

## Part 5 — Kinematic Singularities

### What Is a Singularity?

A configuration where the Jacobian loses rank — the robot loses one or more degrees of freedom. You can no longer move the end-effector in certain directions no matter how you move the joints.

**Common singularities:**
- **Wrist singularity:** All wrist joints aligned (common in Franka, UR5)
- **Shoulder singularity:** Arm fully extended
- **Elbow singularity:** Elbow joint at 0° (arm coplanar)

### Detecting Singularities

The **manipulability measure** (Yoshikawa, 1985):
```
w = sqrt(det(J·Jᵀ))
```

- `w` > 0.1: well-conditioned, robot is nimble
- `w` → 0: near singularity, control becomes unreliable

In practice, monitor this and warn the operator or avoid the configuration during planning.

---

## External Resources

1. **Modern Robotics Textbook — Chapters 4, 5, 6 (free online)**
   Covers FK (Ch.4), velocity kinematics and Jacobians (Ch.5), and IK (Ch.6).
   Dense but definitive. Read Ch.5 on Jacobians carefully.
   → https://hades.mech.northwestern.edu/index.php/Modern_Robotics

2. **Pink documentation and examples**
   → https://github.com/stephane-caron/pink
   Especially: look at the `examples/` folder for real robot usage.

3. **Pinocchio documentation**
   Pink is built on Pinocchio. If you need lower-level FK/Jacobian computation:
   → https://gepettoweb.laas.fr/doc/stack-of-tasks/pinocchio/master/doxygen-html/

4. **MuJoCo Menagerie — Franka Panda model**
   The robot you'll use for projects:
   → https://github.com/google-deepmind/mujoco_menagerie/tree/main/franka_emika_panda

5. **Introduction to Robotics (Craig) — Chapter 3**
   Classic textbook treatment of FK/DH parameters. Good second reference.
   Available as PDF through most university libraries.

---

## Project 3A — IK Solver: Reach Any Target

This project uses Pink with the Franka Panda MJCF model. We'll solve IK to reach targets in 3D space.

Create `learning/ch03_kinematics/01_ik_solver.py`:

```python
import numpy as np
import mujoco
import mujoco.viewer
import pinocchio as pin
import pink
from pink.tasks import FrameTask, PostureTask
import time
import os

# -- Setup Pinocchio model from MJCF --
# Pink needs a URDF or Pinocchio model. For Franka, use the standard URDF.
# Download: https://github.com/frankaemika/franka_ros/tree/develop/franka_description
# Or install: pip install robot_descriptions
from robot_descriptions.loaders.pinocchio import load_robot_description

def load_panda():
    """Load Franka Panda via robot_descriptions (auto-downloads URDF)."""
    robot = load_robot_description("panda_description")
    return robot

def solve_ik_to_target(robot, q0, target_pos, target_quat=None, dt=0.01, max_iter=200):
    """
    Solve IK to move end-effector to target_pos.
    Returns final joint angles q.
    """
    configuration = pink.Configuration(robot.model, robot.data, q0)

    ee_task = FrameTask(
        "panda_hand",
        position_cost=50.0,
        orientation_cost=1.0,
    )
    posture_task = PostureTask(cost=1e-3)

    # Set position target (keep current orientation if none given)
    if target_quat is None:
        # Keep current orientation
        current_SE3 = configuration.get_transform_frame_to_world("panda_hand")
        target_SE3 = pin.SE3(current_SE3.rotation, target_pos)
    else:
        R = pin.Quaternion(target_quat).toRotationMatrix()
        target_SE3 = pin.SE3(R, target_pos)

    ee_task.set_target(target_SE3)
    posture_task.set_target(q0)

    q = q0.copy()
    for i in range(max_iter):
        configuration = pink.Configuration(robot.model, robot.data, q)
        vel = pink.solve_ik(
            configuration,
            [ee_task, posture_task],
            dt=dt,
            solver="quadprog"
        )
        q = configuration.integrate(vel, dt)

        # Check convergence
        current_pos = configuration.get_transform_frame_to_world("panda_hand").translation
        error = np.linalg.norm(current_pos - target_pos)
        if error < 0.005:
            print(f"Converged in {i+1} iterations, error={error*1000:.1f}mm")
            return q, True

    print(f"Did not converge after {max_iter} iters, final error={error*1000:.1f}mm")
    return q, False


def demo_ik():
    """Install robot_descriptions first: pip install robot_descriptions"""
    try:
        robot = load_panda()
    except Exception:
        print("Install robot_descriptions: pip install robot_descriptions")
        print("Then re-run this script.")
        return

    # Default neutral pose (joints in radians)
    q0 = np.array([0, -0.785, 0, -2.356, 0, 1.571, 0.785, 0.04, 0.04])

    # Test targets
    targets = [
        np.array([0.4, 0.0, 0.4]),
        np.array([0.3, 0.3, 0.3]),
        np.array([0.5, -0.2, 0.5]),
        np.array([0.4, 0.0, 0.6]),
    ]

    q = q0.copy()
    for i, target in enumerate(targets):
        print(f"\nTarget {i+1}: {target}")
        q, success = solve_ik_to_target(robot, q, target)
        if success:
            print(f"Joint angles: {np.round(q[:7], 3)}")
        else:
            print("IK failed for this target")

if __name__ == "__main__":
    demo_ik()
```

Install dependency:
```bash
pip install robot_descriptions
```

---

## Project 3B — Real-Time Target Tracking

Create `learning/ch03_kinematics/02_realtime_tracking.py`:

```python
import numpy as np
import mujoco
import mujoco.viewer
import pinocchio as pin
import pink
from pink.tasks import FrameTask, PostureTask
from robot_descriptions.loaders.pinocchio import load_robot_description
import time
import os

MENAGERIE_PATH = os.path.expanduser("~/mujoco_menagerie")
FRANKA_XML = os.path.join(MENAGERIE_PATH, "franka_emika_panda/scene.xml")

def make_circle_target(t, radius=0.15, height=0.4, center=np.array([0.4, 0.0, 0.5])):
    """Target moves in a circle over time."""
    return center + np.array([
        radius * np.cos(t * 0.5),
        radius * np.sin(t * 0.5),
        0.05 * np.sin(t * 2.0)
    ])

def run_tracking():
    robot = load_robot_description("panda_description")
    mj_model = mujoco.MjModel.from_xml_path(FRANKA_XML)
    mj_data = mujoco.MjData(mj_model)

    q = np.array([0, -0.785, 0, -2.356, 0, 1.571, 0.785, 0.04, 0.04])
    q_pin = q.copy()

    kp, kd = 300.0, 30.0

    print("Running real-time circle tracking. Close the viewer to stop.")
    with mujoco.viewer.launch_passive(mj_model, mj_data) as viewer:
        t_start = time.time()
        prev_q_target = q[:7].copy()

        while viewer.is_running():
            t = time.time() - t_start
            target_pos = make_circle_target(t)

            # Solve IK (1 iteration per control step for real-time)
            configuration = pink.Configuration(robot.model, robot.data, q_pin)
            ee_task = FrameTask("panda_hand", position_cost=50.0, orientation_cost=1.0)
            posture_task = PostureTask(cost=1e-3)

            current_SE3 = configuration.get_transform_frame_to_world("panda_hand")
            ee_task.set_target(pin.SE3(current_SE3.rotation, target_pos))
            posture_task.set_target(q_pin)

            dt = 0.02
            vel = pink.solve_ik(configuration, [ee_task, posture_task],
                                dt=dt, solver="quadprog")
            q_pin = configuration.integrate(vel, dt)

            # Track IK solution with PD controller in MuJoCo
            q_mj = mj_data.qpos[:7]
            dq_mj = mj_data.qvel[:7]
            torques = kp * (q_pin[:7] - q_mj) - kd * dq_mj
            mj_data.ctrl[:7] = np.clip(torques, -87, 87)

            # Move visual target marker (mocap)
            if mj_model.nmocap > 0:
                mj_data.mocap_pos[0] = target_pos

            for _ in range(10):
                mujoco.mj_step(mj_model, mj_data)

            viewer.sync()

            # Print tracking error every second
            if int(t) > int(t - dt):
                ee_pos = configuration.get_transform_frame_to_world("panda_hand").translation
                err = np.linalg.norm(ee_pos - target_pos)
                print(f"t={t:.1f}s  tracking error={err*1000:.1f}mm  target={target_pos}")

if __name__ == "__main__":
    run_tracking()
```

---

## Project 3C — Cartesian Control and Pick Trajectory

Create `learning/ch03_kinematics/03_pick_trajectory.py`:

```python
import numpy as np
import mujoco
import mujoco.viewer
import pinocchio as pin
import pink
from pink.tasks import FrameTask, PostureTask
from robot_descriptions.loaders.pinocchio import load_robot_description
import time
import os

FRANKA_XML = os.path.expanduser("~/mujoco_menagerie/franka_emika_panda/scene.xml")

def interpolate_waypoints(waypoints, n_steps_each=100):
    """
    Linearly interpolate between a list of 3D waypoints.
    Returns array of shape (N, 3).
    """
    all_points = []
    for i in range(len(waypoints) - 1):
        start = np.array(waypoints[i])
        end = np.array(waypoints[i+1])
        pts = np.linspace(start, end, n_steps_each)
        all_points.append(pts)
    return np.vstack(all_points)

def run_pick_trajectory():
    robot = load_robot_description("panda_description")
    mj_model = mujoco.MjModel.from_xml_path(FRANKA_XML)
    mj_data = mujoco.MjData(mj_model)

    q_pin = np.array([0, -0.785, 0, -2.356, 0, 1.571, 0.785, 0.04, 0.04])
    kp, kd = 400.0, 40.0

    # Pick trajectory waypoints:
    # 1. Start (above object)
    # 2. Pre-grasp (approach from above)
    # 3. Grasp (at object height)
    # 4. Lift (straight up)
    # 5. Place pre (above destination)
    # 6. Place (at destination)
    # 7. Retract

    object_pos = np.array([0.45, 0.0, 0.05])
    place_pos  = np.array([0.45, 0.3, 0.05])
    hover_h    = 0.25

    waypoints = [
        [0.4,  0.0,  0.4 ],   # home
        object_pos + [0, 0, hover_h],  # above object
        object_pos + [0, 0, 0.02],     # at object (grasp)
        object_pos + [0, 0, hover_h],  # lift
        place_pos  + [0, 0, hover_h],  # above place
        place_pos  + [0, 0, 0.02],     # place
        place_pos  + [0, 0, hover_h],  # retract
    ]

    trajectory = interpolate_waypoints(waypoints, n_steps_each=80)
    print(f"Trajectory: {len(trajectory)} waypoints across {len(waypoints)-1} segments")

    phase_names = ["HOME→ABOVE", "ABOVE→GRASP", "GRASP→LIFT",
                   "LIFT→ABOVE_PLACE", "ABOVE_PLACE→PLACE", "PLACE→RETRACT"]

    with mujoco.viewer.launch_passive(mj_model, mj_data) as viewer:
        for step_idx, target_pos in enumerate(trajectory):
            phase = min(step_idx // 80, len(phase_names)-1)
            if step_idx % 80 == 0:
                print(f"\nPhase: {phase_names[phase]}")

            configuration = pink.Configuration(robot.model, robot.data, q_pin)
            ee_task = FrameTask("panda_hand", position_cost=50.0, orientation_cost=1.0)
            posture_task = PostureTask(cost=1e-3)

            current_SE3 = configuration.get_transform_frame_to_world("panda_hand")
            ee_task.set_target(pin.SE3(current_SE3.rotation, target_pos))
            posture_task.set_target(q_pin)

            dt = 0.02
            vel = pink.solve_ik(configuration, [ee_task, posture_task],
                                dt=dt, solver="quadprog")
            q_pin = configuration.integrate(vel, dt)

            q_mj = mj_data.qpos[:7]
            dq_mj = mj_data.qvel[:7]
            torques = kp * (q_pin[:7] - q_mj) - kd * dq_mj
            mj_data.ctrl[:7] = np.clip(torques, -87, 87)

            for _ in range(10):
                mujoco.mj_step(mj_model, mj_data)
            viewer.sync()

        print("\nTrajectory complete.")
        time.sleep(2.0)

if __name__ == "__main__":
    run_pick_trajectory()
```

---

## Project 3D — Singularity Detection

Create `learning/ch03_kinematics/04_singularity.py`:

```python
import numpy as np
import pinocchio as pin
from robot_descriptions.loaders.pinocchio import load_robot_description
import matplotlib.pyplot as plt

def compute_manipulability(robot, q):
    """Yoshikawa manipulability measure: sqrt(det(J·Jᵀ))."""
    pin.computeJointJacobians(robot.model, robot.data, q)
    pin.framesForwardKinematics(robot.model, robot.data, q)

    frame_id = robot.model.getFrameId("panda_hand")
    J = pin.getFrameJacobian(robot.model, robot.data, frame_id,
                              pin.LOCAL_WORLD_ALIGNED)[:3, :]  # position only

    JJT = J @ J.T
    det_val = np.linalg.det(JJT)
    return np.sqrt(max(det_val, 0))

def sweep_manipulability():
    robot = load_robot_description("panda_description")
    q_neutral = np.array([0, -0.785, 0, -2.356, 0, 1.571, 0.785, 0.04, 0.04])

    # Sweep joint 2 (elbow) from -pi to pi
    angles = np.linspace(-np.pi, np.pi, 200)
    manipulabilities = []

    for angle in angles:
        q = q_neutral.copy()
        q[2] = angle  # vary joint 3 (shoulder rotation)
        w = compute_manipulability(robot, q)
        manipulabilities.append(w)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(np.degrees(angles), manipulabilities, color='steelblue', linewidth=2)
    ax.axhline(0.05, color='red', linestyle='--', label='Singularity threshold (w<0.05)')
    ax.fill_between(np.degrees(angles), 0, manipulabilities,
                    where=np.array(manipulabilities) < 0.05,
                    color='red', alpha=0.3, label='Near-singular region')
    ax.set_xlabel('Joint 3 angle (degrees)')
    ax.set_ylabel('Manipulability w = sqrt(det(J·Jᵀ))')
    ax.set_title('Manipulability vs. Joint Angle\n'
                 'Red regions: near-singular configurations to avoid')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('manipulability.png', dpi=150)
    plt.show()
    print("Saved manipulability.png")

    # Find singularities
    sing_angles = [np.degrees(angles[i]) for i, w in enumerate(manipulabilities) if w < 0.05]
    if sing_angles:
        print(f"\nNear-singular configurations at joint-3 angles: {sing_angles[:5]} degrees")

if __name__ == "__main__":
    sweep_manipulability()
```

---

## Self-Check Questions

Before moving to Chapter 4:

1. You want the end-effector to move at 5 cm/s in the +X direction. How do you compute the required joint velocities?
2. What does it mean that a 7-DOF arm is "redundant"? What can you do with the extra DOF?
3. Your IK solver gives you a solution, but the arm hits itself. What constraint do you add to the QP?
4. The manipulability measure is 0.001. What does this mean practically? What should your controller do?
5. Why does the damped pseudoinverse prevent singularity blow-up? What's the tradeoff?
6. You're doing Cartesian-space velocity control. What happens when you try to move the end-effector perpendicular to a singular direction?

**Answer to Q1:**
```python
desired_ee_vel = np.array([0.05, 0, 0, 0, 0, 0])  # [vx, vy, vz, wx, wy, wz]
J = get_jacobian(robot, q)  # 6×7
J_pinv = np.linalg.pinv(J)  # pseudoinverse
q_dot = J_pinv @ desired_ee_vel  # joint velocities
```

---

## What's Not Needed Here

**DH parameter derivation:** The robot XML encodes geometry directly. Pink/Pinocchio read
it automatically. You never need to derive or read a DH table.

**Gradient-based IK from scratch:** Pink handles joint limits, velocity limits, and
singularity avoidance correctly. Rolling your own only makes sense if you need custom
constraints — which you don't at this stage.

**Motion planning with obstacle avoidance (RRT, PRM):** Not needed for imitation learning
(Chapter 5) because the policy outputs actions directly. If you need it later, MoveIt 2
(Chapter 8) handles this.

---

## What's Next

Chapter 4 uses RL to learn control policies. The motion stack you now have — IK computes target joint angles, PD controller (from Chapter 2) executes them — is exactly what runs at deployment. A learned policy outputs target EE positions; this stack converts them to robot motion.
