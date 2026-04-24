# Chapter 2 — Simulation with MuJoCo

**Time:** 3–5 days
**Hardware:** Any laptop, no GPU needed
**Prerequisites:** Chapter 1 (transforms), Python classes, basic physics intuition

---

## Why This Chapter Exists

All the learning algorithms in this curriculum — RL, imitation learning, sim-to-real — need a simulator to train in. MuJoCo is that simulator. But the gap most people hit isn't understanding physics — it's not knowing how to get a robot model into the sim, how to read joint states, how to apply control, or how to make the sim compatible with standard training libraries.

This chapter fills that operational gap. By the end you'll have a working Gymnasium environment wrapping a real robot model — the exact interface that Stable Baselines 3, LeRobot, and every other library expects. Everything from Chapter 3 onward builds directly on this.

---

## Part 1 — What MuJoCo Is and How It Works

### The Core Loop

MuJoCo runs a physics simulation in discrete timesteps. At each step:
1. Read control inputs (joint torques or positions you set)
2. Compute forces from contacts, joints, actuators
3. Integrate dynamics forward in time (default timestep: 2ms)
4. Update positions and velocities of all bodies

You interact with MuJoCo through two objects:
- **`mjModel`** — the static model (geometry, masses, joint limits). Doesn't change during simulation.
- **`mjData`** — the dynamic state (positions, velocities, forces). Changes every step.

### The MJCF Format

MuJoCo describes robots in XML called MJCF (MuJoCo Modeling Format). The key elements:

```xml
<mujoco>
  <worldbody>
    <body name="link1" pos="0 0 0">
      <joint name="joint1" type="hinge" axis="0 0 1"/>
      <geom type="capsule" size="0.05 0.2"/>
      <body name="link2" pos="0 0 0.4">
        <joint name="joint2" type="hinge" axis="0 1 0"/>
        <geom type="capsule" size="0.04 0.15"/>
      </body>
    </body>
  </worldbody>
  <actuator>
    <motor name="act1" joint="joint1" gear="100"/>
  </actuator>
</mujoco>
```

Key concepts:
- **`body`** — a rigid link. Nested bodies are connected by joints.
- **`joint`** — defines how a body can move relative to its parent (hinge=revolute, slide=prismatic, free=6-DOF)
- **`geom`** — the collision/visual shape attached to a body
- **`actuator`** — what generates forces (motor, position servo, etc.)

### Install

```bash
pip install mujoco gymnasium gymnasium-robotics
```

Verify:
```python
import mujoco
print(mujoco.__version__)  # should be 3.x
```

---

## Part 2 — Key MuJoCo API Concepts

### Loading and Stepping

```python
import mujoco
import mujoco.viewer

# Load from XML string
xml = """
<mujoco>
  <worldbody>
    <geom type="plane" size="1 1 0.1"/>
    <body name="box" pos="0 0 0.5">
      <freejoint/>
      <geom type="box" size="0.1 0.1 0.1" mass="1"/>
    </body>
  </worldbody>
</mujoco>
"""
model = mujoco.MjModel.from_xml_string(xml)
data = mujoco.MjData(model)

# Run 1 second of simulation
for _ in range(int(1.0 / model.opt.timestep)):
    mujoco.mj_step(model, data)

print(f"Box final height: {data.qpos[2]:.4f}")
```

### Reading State

```python
# Joint positions and velocities (for non-free joints)
qpos = data.qpos   # shape: (nq,)  — all generalized positions
qvel = data.qvel   # shape: (nv,)  — all generalized velocities

# Body positions in world frame
body_id = model.body('box').id
pos = data.xpos[body_id]   # [x, y, z]
rot = data.xmat[body_id]   # 3x3 rotation matrix (flattened to 9)

# End-effector site position (if you define a site in MJCF)
site_id = model.site('ee').id
ee_pos = data.site_xpos[site_id]
```

### Setting Control

```python
# For motor actuators: set torque
data.ctrl[0] = 10.0   # actuator 0 gets 10 Nm

# For position servo actuators (gear + kp defined in MJCF):
data.ctrl[0] = target_angle   # target joint position
```

### Contacts

```python
# After mj_step, contact forces are in data.contact
for i in range(data.ncon):
    contact = data.contact[i]
    force = np.zeros(6)
    mujoco.mj_contactForce(model, data, i, force)
    print(f"Contact {i}: force={force[:3]}")
```

---

## Part 3 — Actuator Types

Understanding the difference is important — it changes how you write controllers.

**`motor`** — applies raw torque. You control force directly.
```xml
<actuator>
  <motor joint="joint1" gear="1"/>
</actuator>
```
```python
data.ctrl[0] = 5.0  # 5 Nm torque
```

**`position`** — built-in PD servo. You set a target angle, the actuator drives there.
```xml
<actuator>
  <position joint="joint1" kp="100" kv="10"/>
</actuator>
```
```python
data.ctrl[0] = 1.57  # target angle in radians
```

**`velocity`** — set target joint velocity.

For learning, position actuators are easiest to start with. For real robot control research, torque (motor) actuators give you more physical accuracy.

---

## Part 4 — The PD Controller

When using `motor` actuators you implement your own controller. The standard is a PD (Proportional-Derivative) controller:

```
torque = kp * (target_angle - current_angle) - kd * current_velocity
```

- `kp` (proportional gain): how hard to push toward the target. Too low → slow. Too high → oscillation.
- `kd` (derivative gain): damping. Prevents overshoot by resisting velocity.

Good starting values for a robot arm joint:
- `kp = 100` (in simulation units; depends on link mass and length)
- `kd = 10`

---

## External Resources

1. **MuJoCo Documentation — Programming Guide**
   The primary reference. Read "Getting Started" and "Simulation" sections.
   → https://mujoco.readthedocs.io/en/stable/programming/index.html

2. **MuJoCo MJCF XML Reference**
   Every XML element and attribute. Bookmark this — you'll use it constantly.
   → https://mujoco.readthedocs.io/en/stable/XMLreference.html

3. **MuJoCo Tutorial Notebooks (Colab)**
   Interactive notebooks from DeepMind covering key features.
   → Search "MuJoCo tutorial colab deepmind" — the official tutorial set

4. **Gymnasium Documentation**
   The interface all RL and IL libraries expect. Read "Basic Usage" and "Creating Environments".
   → https://gymnasium.farama.org/

5. **MuJoCo Model Zoo (GitHub)**
   Pre-built MJCF models of real robots (Franka Panda, UR5, IIWA, etc.)
   → https://github.com/google-deepmind/mujoco_menagerie

---

## Project 2A — Build a Physics Scene

Create `learning/ch02_mujoco/01_basic_scene.py`:

```python
import mujoco
import mujoco.viewer
import numpy as np
import time

XML = """
<mujoco model="basic_scene">
  <option timestep="0.002" gravity="0 0 -9.81"/>

  <visual>
    <headlight ambient="0.3 0.3 0.3"/>
  </visual>

  <worldbody>
    <!-- Ground plane -->
    <geom name="floor" type="plane" size="2 2 0.1" rgba="0.8 0.8 0.8 1"/>

    <!-- A falling box -->
    <body name="box1" pos="0 0 1.0">
      <freejoint name="box1_joint"/>
      <geom type="box" size="0.1 0.1 0.1" mass="1" rgba="0.2 0.5 0.8 1"/>
    </body>

    <!-- A falling sphere, offset -->
    <body name="sphere1" pos="0.3 0 1.5">
      <freejoint name="sphere1_joint"/>
      <geom type="sphere" size="0.08" mass="0.5" rgba="0.8 0.3 0.2 1"/>
    </body>
  </worldbody>
</mujoco>
"""

def run_scene():
    model = mujoco.MjModel.from_xml_string(XML)
    data = mujoco.MjData(model)

    print(f"Timestep: {model.opt.timestep}s")
    print(f"Bodies: {model.nbody}")
    print(f"Geoms: {model.ngeom}")

    with mujoco.viewer.launch_passive(model, data) as viewer:
        start = time.time()
        while viewer.is_running() and time.time() - start < 10.0:
            mujoco.mj_step(model, data)

            # Print contact info every 200 steps
            if data.time % 0.4 < model.opt.timestep:
                if data.ncon > 0:
                    print(f"t={data.time:.2f}s  contacts={data.ncon}")
                    for i in range(data.ncon):
                        force = np.zeros(6)
                        mujoco.mj_contactForce(model, data, i, force)
                        print(f"  contact {i}: normal_force={np.linalg.norm(force[:3]):.2f}N")

            viewer.sync()

if __name__ == "__main__":
    run_scene()
```

**What to observe:** Objects fall, bounce, and generate contact forces. The contact normal force spikes on impact and settles to the object's weight.

---

## Project 2B — Load and Control a Robot Arm

First, download the Franka Panda model from MuJoCo Menagerie:
```bash
git clone https://github.com/google-deepmind/mujoco_menagerie.git
```

Create `learning/ch02_mujoco/02_robot_arm.py`:

```python
import mujoco
import mujoco.viewer
import numpy as np
import time
import os

# Path to Franka model — adjust to your menagerie location
FRANKA_XML = os.path.expanduser("~/mujoco_menagerie/franka_emika_panda/scene.xml")

def run_arm():
    model = mujoco.MjModel.from_xml_path(FRANKA_XML)
    data = mujoco.MjData(model)

    print(f"Robot: {model.nbody} bodies, {model.njnt} joints, {model.nu} actuators")
    print("Joint names:")
    for i in range(model.njnt):
        print(f"  [{i}] {model.joint(i).name}  range: {model.jnt_range[i]}")

    # Target: hold a neutral pose
    neutral_pose = np.array([0, -0.785, 0, -2.356, 0, 1.571, 0.785])

    # PD gains
    kp = np.array([400, 400, 400, 400, 250, 150, 50])
    kd = np.array([40,  40,  40,  40,  25,  15,  5 ])

    mujoco.mj_resetDataKeyframe(model, data, 0)  # use default keyframe if exists

    with mujoco.viewer.launch_passive(model, data) as viewer:
        start = time.time()
        while viewer.is_running() and time.time() - start < 15.0:
            # PD controller
            q = data.qpos[:7]
            dq = data.qvel[:7]
            torques = kp * (neutral_pose - q) - kd * dq
            data.ctrl[:7] = np.clip(torques, -87, 87)  # Franka torque limits

            mujoco.mj_step(model, data)
            viewer.sync()

            if data.time % 1.0 < model.opt.timestep:
                ee_site = model.site('attachment_site').id if 'attachment_site' in [
                    model.site(i).name for i in range(model.nsite)] else None
                if ee_site is not None:
                    ee_pos = data.site_xpos[ee_site]
                    print(f"t={data.time:.1f}s  EE pos: {ee_pos}")

if __name__ == "__main__":
    run_arm()
```

---

## Project 2C — PD Controller Deep Dive

Create `learning/ch02_mujoco/03_pd_controller.py` to study how PD gains affect behavior:

```python
import mujoco
import numpy as np
import matplotlib.pyplot as plt

# Simple 1-DOF pendulum to study PD behavior
PENDULUM_XML = """
<mujoco model="pendulum">
  <option timestep="0.002"/>
  <worldbody>
    <body name="link" pos="0 0 0">
      <joint name="hinge" type="hinge" axis="0 1 0" range="-3.14 3.14"/>
      <geom type="capsule" size="0.04" fromto="0 0 0 0 0 -0.5" mass="1"/>
      <body name="mass" pos="0 0 -0.5">
        <geom type="sphere" size="0.05" mass="2"/>
      </body>
    </body>
  </worldbody>
  <actuator>
    <motor joint="hinge" gear="1" ctrllimited="true" ctrlrange="-20 20"/>
  </actuator>
</mujoco>
"""

def simulate_pd(kp, kd, target_angle=1.0, duration=5.0):
    model = mujoco.MjModel.from_xml_string(PENDULUM_XML)
    data = mujoco.MjData(model)

    times, angles, targets = [], [], []

    steps = int(duration / model.opt.timestep)
    for _ in range(steps):
        q = data.qpos[0]
        dq = data.qvel[0]
        torque = kp * (target_angle - q) - kd * dq
        data.ctrl[0] = np.clip(torque, -20, 20)
        mujoco.mj_step(model, data)
        times.append(data.time)
        angles.append(q)
        targets.append(target_angle)

    return np.array(times), np.array(angles)

def compare_gains():
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    configs = [
        (10,  0.1,  "Low kp, low kd — slow, underdamped"),
        (10,  5.0,  "Low kp, high kd — slow, overdamped"),
        (200, 1.0,  "High kp, low kd — fast, oscillates"),
        (200, 30.0, "High kp, high kd — fast, well-damped (good)"),
    ]

    for ax, (kp, kd, title) in zip(axes.flatten(), configs):
        t, q = simulate_pd(kp, kd)
        ax.plot(t, q, label=f'angle', color='steelblue')
        ax.axhline(1.0, color='red', linestyle='--', label='target')
        ax.set_title(f'{title}\nkp={kp}, kd={kd}')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Joint angle (rad)')
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.suptitle('PD Gain Effects on Joint Control', y=1.02, fontsize=14)
    plt.savefig('pd_gains.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("Saved pd_gains.png")

if __name__ == "__main__":
    compare_gains()
```

**What to observe:** High kp + low kd causes oscillation. High kd overdamps (too slow). The well-tuned bottom-right case reaches target quickly without oscillating.

---

## Project 2D — Build a Gymnasium Environment

Create `learning/ch02_mujoco/04_gym_env.py`:

```python
import numpy as np
import mujoco
import gymnasium as gym
from gymnasium import spaces

REACH_XML = """
<mujoco model="reach">
  <option timestep="0.002"/>

  <worldbody>
    <geom name="floor" type="plane" size="1 1 0.1" rgba="0.9 0.9 0.9 1"/>

    <!-- Simple 2-DOF planar arm -->
    <body name="base" pos="0 0 0.1">
      <geom type="cylinder" size="0.05 0.05" rgba="0.5 0.5 0.5 1"/>
      <body name="link1" pos="0 0 0.05">
        <joint name="joint1" type="hinge" axis="0 0 1" range="-3.14 3.14"/>
        <geom type="capsule" size="0.03" fromto="0 0 0 0.3 0 0" rgba="0.2 0.5 0.8 1" mass="0.5"/>
        <body name="link2" pos="0.3 0 0">
          <joint name="joint2" type="hinge" axis="0 0 1" range="-2.5 2.5"/>
          <geom type="capsule" size="0.025" fromto="0 0 0 0.25 0 0" rgba="0.2 0.7 0.5 1" mass="0.3"/>
          <site name="ee" pos="0.25 0 0" size="0.02"/>
        </body>
      </body>
    </body>

    <!-- Target sphere (we'll move this programmatically) -->
    <body name="target" pos="0.4 0.1 0.1" mocap="true">
      <geom type="sphere" size="0.03" rgba="1 0.2 0.2 0.7"/>
    </body>
  </worldbody>

  <actuator>
    <motor name="act1" joint="joint1" gear="10" ctrllimited="true" ctrlrange="-5 5"/>
    <motor name="act2" joint="joint2" gear="10" ctrllimited="true" ctrlrange="-5 5"/>
  </actuator>
</mujoco>
"""

class ReachEnv(gym.Env):
    metadata = {'render_modes': ['human', 'rgb_array'], 'render_fps': 50}

    def __init__(self, render_mode=None):
        self.render_mode = render_mode
        self.model = mujoco.MjModel.from_xml_string(REACH_XML)
        self.data = mujoco.MjData(self.model)

        self.ee_site_id = self.model.site('ee').id
        self.target_body_id = self.model.body('target').id

        # Observation: [joint1_pos, joint2_pos, joint1_vel, joint2_vel, ee_x, ee_y, target_x, target_y]
        obs_low  = np.array([-np.pi, -2.5, -10, -10, -1, -1, -1, -1], dtype=np.float32)
        obs_high = np.array([ np.pi,  2.5,  10,  10,  1,  1,  1,  1], dtype=np.float32)
        self.observation_space = spaces.Box(obs_low, obs_high, dtype=np.float32)

        # Action: torques for 2 joints
        self.action_space = spaces.Box(
            low=np.array([-5.0, -5.0], dtype=np.float32),
            high=np.array([5.0, 5.0], dtype=np.float32)
        )

        self._target_pos = np.array([0.4, 0.1])
        self._max_steps = 500
        self._step_count = 0

        if render_mode == 'human':
            self._viewer = mujoco.viewer.launch_passive(self.model, self.data)

    def _get_obs(self):
        q = self.data.qpos[:2].copy()
        dq = self.data.qvel[:2].copy()
        ee_pos = self.data.site_xpos[self.ee_site_id][:2].copy()
        return np.concatenate([q, dq, ee_pos, self._target_pos]).astype(np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)

        # Randomize initial joint angles
        self.data.qpos[:2] = self.np_random.uniform(-1.0, 1.0, size=2)

        # Randomize target position (reachable workspace)
        r = self.np_random.uniform(0.15, 0.5)
        theta = self.np_random.uniform(-np.pi/2, np.pi/2)
        self._target_pos = np.array([r * np.cos(theta), r * np.sin(theta)])

        # Move the mocap target body
        self.data.mocap_pos[0, :2] = self._target_pos

        mujoco.mj_forward(self.model, self.data)
        self._step_count = 0
        return self._get_obs(), {}

    def step(self, action):
        self.data.ctrl[:2] = action
        for _ in range(5):  # 5 physics steps per env step (10ms per env step)
            mujoco.mj_step(self.model, self.data)

        self._step_count += 1
        obs = self._get_obs()

        ee_pos = self.data.site_xpos[self.ee_site_id][:2]
        dist = np.linalg.norm(ee_pos - self._target_pos)

        # Reward: negative distance + bonus for being very close
        reward = -dist
        if dist < 0.05:
            reward += 1.0

        terminated = dist < 0.03  # success if within 3cm
        truncated = self._step_count >= self._max_steps

        if self.render_mode == 'human':
            self._viewer.sync()

        return obs, reward, terminated, truncated, {'distance': dist}

    def close(self):
        if self.render_mode == 'human' and hasattr(self, '_viewer'):
            self._viewer.close()


def test_env():
    env = ReachEnv()
    obs, _ = env.reset()
    print(f"Observation space: {env.observation_space}")
    print(f"Action space: {env.action_space}")
    print(f"Initial obs shape: {obs.shape}")

    total_reward = 0
    for step in range(200):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        if terminated or truncated:
            print(f"Episode ended at step {step+1}, total reward: {total_reward:.2f}")
            obs, _ = env.reset()
            total_reward = 0

    print("Environment test passed.")
    env.close()

if __name__ == "__main__":
    test_env()
```

Test it:
```bash
python 04_gym_env.py
```

---

## Self-Check Questions

Before moving to Chapter 3, answer these:

1. What is the difference between `model` and `data` in MuJoCo, and why are they separate?
2. What is the difference between position control and torque control for a robot joint? When would you choose each?
3. What happens if your PD controller's `kp` is too high? What do you see in the simulation?
4. Your environment's `step()` runs 5 MuJoCo steps per call. What is the effective control frequency if MuJoCo's timestep is 2ms?
5. What is a `freejoint` and when would you use it?
6. What does `mj_forward()` do that `mj_step()` doesn't?
7. You see joint positions oscillating around the target, never converging. Which gain do you increase?

**Answer to Q2:** Position control (via `position` actuator or PD controller) is simpler — you command an angle and the actuator drives there. Torque control (`motor` actuator) lets you command raw force — more physically accurate, required for force-sensitive tasks, but harder to stabilize. Use position control for learning; torque control for research or when you need compliance.
**Answer to Q4:** 5 × 2ms = 10ms per env step → 100 Hz control frequency.
**Answer to Q7:** Increase `kd` (damping). The oscillation is underdamped behavior.

---

## What's Next

In Chapter 3 you'll load a full 6-DOF robot arm into MuJoCo and use the Pink IK library to compute joint angles that put the end-effector at any target position — the foundation for all manipulation.
