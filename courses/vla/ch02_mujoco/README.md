# Chapter 2 — Control & Gymnasium

**Time:** 2–3 days
**Hardware:** Any laptop, no GPU
**Prerequisites:** Chapter 1 (MuJoCo basics — model/data, viewer, reading body poses)

---

## Why This Chapter Exists

You can load a robot and read its state. Now you need to make it move — and do it in a way
that every training library can talk to.

This chapter covers two things. First: how to actually control a robot in MuJoCo, which
means understanding actuator types and writing a PD controller. Second: how to wrap a
simulation into a Gymnasium environment — the standard interface that Stable Baselines 3,
LeRobot, and every other RL/IL library expects. Everything from Chapter 4 onward builds
directly on this.

### If you can answer these, you can skip this chapter

1. What is the difference between a `motor` actuator and a `position` actuator in MuJoCo?
2. Your PD controller oscillates but eventually settles. Which gain do you increase?
3. What does `env.step(action)` return, and what does each element mean?

---

## Part 1 — Actuator Types

MuJoCo gives you three actuator types. The choice affects how you write your controller.

**`motor`** — applies raw torque. You are responsible for stabilizing the joint.
```xml
<actuator>
  <motor joint="joint1" gear="1"/>
</actuator>
```
```python
data.ctrl[0] = 5.0  # 5 Nm torque
```

**`position`** — built-in PD servo. Set a target angle; the actuator drives there.
```xml
<actuator>
  <position joint="joint1" kp="100" kv="10"/>
</actuator>
```
```python
data.ctrl[0] = 1.57  # target angle in radians
```

**`velocity`** — set a target joint velocity.

For learning, `position` actuators are the easiest starting point — you command where to go
and the sim handles stability. For research that needs physical accuracy (force control,
compliance, contact-rich manipulation), `motor` actuators give you more control but require
your own stabilizing controller.

---

## Part 2 — The PD Controller

When using `motor` actuators you implement the controller yourself. The standard is PD:

```
torque = kp × (target_angle − current_angle) − kd × current_velocity
```

- **kp** (proportional): how hard to push toward the target. Too low → slow. Too high → oscillates.
- **kd** (derivative): damping. Resists velocity, prevents overshoot.

Good starting values for a robot arm joint: `kp = 100`, `kd = 10`.
For a heavier arm like the Franka Panda: `kp = 400`, `kd = 40`.

Tuning intuition:
- Oscillates and doesn't settle → increase `kd`
- Settles too slowly → increase `kp` (then re-tune `kd` if it starts oscillating)
- Steady-state error remains → add integral term (rarely needed in sim)

---

## Part 3 — Gymnasium Environments

Gymnasium is the standard interface all RL and IL libraries use. Every environment has:

```python
obs, info        = env.reset()
obs, rew, term, trunc, info = env.step(action)
```

- **`obs`** — what the agent observes (joint angles, EE position, etc.)
- **`rew`** — scalar reward for this step
- **`term`** — True if the episode ended naturally (task succeeded or catastrophic failure)
- **`trunc`** — True if the episode hit the time limit
- **`action`** — what the agent sends (joint torques, target angles, etc.)

Your MuJoCo environment wraps the physics loop inside `step()` and defines the observation
and action spaces. This is the contract libraries like Stable Baselines 3 depend on.

---

## External Resources

1. **Gymnasium Documentation — Creating Environments**
   Read "Basic Usage" and "Creating Custom Environments".
   → https://gymnasium.farama.org/

2. **MuJoCo XML Reference — actuator section**
   Every actuator parameter explained. Bookmark it.
   → https://mujoco.readthedocs.io/en/stable/XMLreference.html#actuator

3. **Stable Baselines 3 — Getting Started**
   The RL library you'll use in Chapter 4. Shows how it consumes a Gym environment.
   → https://stable-baselines3.readthedocs.io/en/master/guide/quickstart.html

---

## Project 2A — PD Controller: Tune the Gains

**What you're building:** A single-joint pendulum with a `motor` actuator and your own PD
controller. You'll plot joint angle vs. time for four gain combinations to build intuition
for what kp/kd actually do.

This matters because in Chapter 3, IK hands you target joint angles — and a PD controller
is what executes them on the robot.

Create `learning/ch02_control/pd_gains.py`:

```python
"""
Visualize how PD gain choices affect joint control on a simple pendulum.
Run this before tuning gains on any real robot or more complex sim.
"""
import numpy as np
import mujoco
import matplotlib.pyplot as plt

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

def simulate_pd(kp: float, kd: float, target: float = 1.0, duration: float = 5.0):
    model = mujoco.MjModel.from_xml_string(PENDULUM_XML)
    data  = mujoco.MjData(model)
    times, angles = [], []
    for _ in range(int(duration / model.opt.timestep)):
        torque = kp * (target - data.qpos[0]) - kd * data.qvel[0]
        data.ctrl[0] = np.clip(torque, -20, 20)
        mujoco.mj_step(model, data)
        times.append(data.time)
        angles.append(data.qpos[0])
    return np.array(times), np.array(angles)

if __name__ == "__main__":
    configs = [
        (10,  0.5,  "Low kp, low kd — slow, underdamped"),
        (10,  8.0,  "Low kp, high kd — slow, overdamped"),
        (200, 1.0,  "High kp, low kd — fast but oscillates"),
        (200, 30.0, "High kp, high kd — fast and settled (good)"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, (kp, kd, title) in zip(axes.flatten(), configs):
        t, q = simulate_pd(kp, kd)
        ax.plot(t, q, color='steelblue', linewidth=2)
        ax.axhline(1.0, color='red', linestyle='--', label='target')
        ax.set_title(f"{title}\nkp={kp}, kd={kd}")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Joint angle (rad)")
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("pd_gains.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Saved pd_gains.png")
    print("\nTakeaway: high kp + high kd = fast settling without oscillation.")
    print("The bottom-right plot is your target behavior.")
```

Run it:
```bash
cd learning/ch02_control
python pd_gains.py
```

---

## Project 2B — Control a Real Robot Arm

**What you're building:** Load the Franka Panda, hold a target pose with a PD controller,
and watch the arm stabilize in the viewer. This is the same controller pattern used in
Chapter 3 to execute IK solutions.

```bash
git clone https://github.com/google-deepmind/mujoco_menagerie.git ~/mujoco_menagerie
```

Create `learning/ch02_control/hold_pose.py`:

```python
"""
Hold a target joint configuration with a PD controller on the Franka Panda.
The same pattern is used in Chapter 3 to track IK-computed target angles.
"""
import numpy as np
import mujoco
import mujoco.viewer
import time
import os

FRANKA_XML = os.path.expanduser("~/mujoco_menagerie/franka_emika_panda/scene.xml")

# Franka neutral pose (radians)
NEUTRAL = np.array([0, -0.785, 0, -2.356, 0, 1.571, 0.785])

# PD gains tuned for Franka's inertia — kp higher for shoulder joints
KP = np.array([400, 400, 400, 400, 250, 150, 50], dtype=float)
KD = np.array([ 40,  40,  40,  40,  25,  15,  5], dtype=float)

# Franka joint torque limits (Nm)
TORQUE_LIMITS = np.array([87, 87, 87, 87, 12, 12, 12], dtype=float)

def run(target: np.ndarray, duration: float = 10.0) -> None:
    model = mujoco.MjModel.from_xml_path(FRANKA_XML)
    data  = mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model, data, 0)

    with mujoco.viewer.launch_passive(model, data) as viewer:
        t_start = time.time()
        while viewer.is_running() and time.time() - t_start < duration:
            q  = data.qpos[:7]
            dq = data.qvel[:7]
            torques = KP * (target - q) - KD * dq
            data.ctrl[:7] = np.clip(torques, -TORQUE_LIMITS, TORQUE_LIMITS)
            mujoco.mj_step(model, data)
            viewer.sync()

            if data.time % 2.0 < model.opt.timestep:
                err = np.max(np.abs(target - data.qpos[:7]))
                print(f"t={data.time:.1f}s  max joint error: {np.degrees(err):.2f}°")

if __name__ == "__main__":
    if not os.path.exists(FRANKA_XML):
        print("Clone MuJoCo Menagerie first.")
        exit(1)
    print("Holding neutral pose. Watch the arm stabilize in the viewer.")
    run(NEUTRAL)
```

Run it, then try changing `NEUTRAL` to a different configuration and re-run.

---

## Project 2C — Build a Gymnasium Environment

**What you're building:** Wrap a 2-DOF planar reach task into a proper Gymnasium
environment. This is the interface Chapter 4 (RL) plugs straight into.

Create `learning/ch02_control/reach_env.py`:

```python
"""
2-DOF planar reach task as a Gymnasium environment.
Stable Baselines 3 and LeRobot both consume environments in this format.
"""
import numpy as np
import mujoco
import gymnasium as gym
from gymnasium import spaces

REACH_XML = """
<mujoco model="reach">
  <option timestep="0.002"/>
  <worldbody>
    <geom name="floor" type="plane" size="1 1 0.1" rgba="0.9 0.9 0.9 1"/>
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
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 50}

    def __init__(self, render_mode=None):
        self.render_mode = render_mode
        self.model = mujoco.MjModel.from_xml_string(REACH_XML)
        self.data  = mujoco.MjData(self.model)

        self._ee_site_id     = self.model.site("ee").id
        self._target_body_id = self.model.body("target").id
        self._target_pos     = np.array([0.4, 0.1])
        self._step_count     = 0

        # obs: [q1, q2, dq1, dq2, ee_x, ee_y, target_x, target_y]
        self.observation_space = spaces.Box(
            low  = np.array([-np.pi, -2.5, -10, -10, -1, -1, -1, -1], dtype=np.float32),
            high = np.array([ np.pi,  2.5,  10,  10,  1,  1,  1,  1], dtype=np.float32),
        )
        self.action_space = spaces.Box(
            low=-np.array([5.0, 5.0], dtype=np.float32),
            high=np.array([5.0, 5.0], dtype=np.float32),
        )

        if render_mode == "human":
            import mujoco.viewer
            self._viewer = mujoco.viewer.launch_passive(self.model, self.data)

    def _get_obs(self) -> np.ndarray:
        q   = self.data.qpos[:2].copy()
        dq  = self.data.qvel[:2].copy()
        ee  = self.data.site_xpos[self._ee_site_id][:2].copy()
        return np.concatenate([q, dq, ee, self._target_pos]).astype(np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)
        self.data.qpos[:2] = self.np_random.uniform(-1.0, 1.0, size=2)
        r     = self.np_random.uniform(0.15, 0.5)
        theta = self.np_random.uniform(-np.pi / 2, np.pi / 2)
        self._target_pos = np.array([r * np.cos(theta), r * np.sin(theta)])
        self.data.mocap_pos[0, :2] = self._target_pos
        mujoco.mj_forward(self.model, self.data)
        self._step_count = 0
        return self._get_obs(), {}

    def step(self, action):
        self.data.ctrl[:2] = action
        for _ in range(5):  # 5 × 2ms = 10ms per env step → 100 Hz
            mujoco.mj_step(self.model, self.data)
        self._step_count += 1

        ee   = self.data.site_xpos[self._ee_site_id][:2]
        dist = np.linalg.norm(ee - self._target_pos)

        reward     = -dist + (1.0 if dist < 0.05 else 0.0)
        terminated = dist < 0.03
        truncated  = self._step_count >= 500

        if self.render_mode == "human":
            self._viewer.sync()

        return self._get_obs(), reward, terminated, truncated, {"distance": float(dist)}

    def close(self):
        if self.render_mode == "human" and hasattr(self, "_viewer"):
            self._viewer.close()


if __name__ == "__main__":
    env = ReachEnv()
    obs, _ = env.reset()
    print(f"Observation space : {env.observation_space}")
    print(f"Action space      : {env.action_space}")
    print(f"Initial obs       : {obs}")

    total_reward = 0.0
    for step in range(300):
        action = env.action_space.sample()
        obs, rew, term, trunc, info = env.step(action)
        total_reward += rew
        if term or trunc:
            print(f"Episode ended at step {step + 1}  total reward: {total_reward:.2f}")
            obs, _ = env.reset()
            total_reward = 0.0

    env.close()
    print("Environment works. Plug this into Stable Baselines 3 in Chapter 4.")
```

Run it:
```bash
python reach_env.py
```

---

## Self-Check

1. What is the difference between `motor` and `position` actuators? When would you choose each?

   **Answer:** `motor` applies raw torque — you write the stabilizing controller. `position`
   has a built-in PD servo, you just command the target angle. Use `position` for learning
   experiments; `motor` when you need physical accuracy (force control, contact-rich tasks).

2. Your PD controller's joint angle oscillates around the target and never settles. Which
   gain do you increase and why?

   **Answer:** Increase `kd`. The oscillation is underdamped — the derivative term resists
   velocity and damps out the overshoot.

3. `env.step()` runs 5 MuJoCo steps. The sim timestep is 2ms. What is the control frequency?

   **Answer:** 5 × 2ms = 10ms per step → 100 Hz.

4. What does `terminated=True` mean vs `truncated=True`?

   **Answer:** `terminated` means the episode ended for task reasons (success or failure).
   `truncated` means the time limit was hit. RL algorithms treat these differently when
   computing value targets.

5. You want to add the wrist camera image to the observation. What changes in the env?

   **Answer:** Render an offscreen camera with `mujoco.Renderer`, add the pixel array to
   `_get_obs()`, and update `observation_space` to include a `Dict` or `Box` for image data.

---

## What's Next

Chapter 3 introduces inverse kinematics: given a target end-effector position in world space,
compute the joint angles to get there. The PD controller you just built is exactly what
executes those joint angle targets on the robot.
