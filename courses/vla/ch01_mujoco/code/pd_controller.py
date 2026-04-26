"""
PD controller on a 2-DOF arm. Run 4 kp/kd combinations and plot trajectories.
Shows how gain tuning changes stability.
"""
import numpy as np
import matplotlib.pyplot as plt
import mujoco

# Create the arm XML inline
ARM_XML = """<?xml version="1.0"?>
<mujoco>
  <compiler angle="radian"/>
  <option timestep="0.002" gravity="0 0 0"/>
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
    <motor name="m1" joint="j1" ctrllimited="true" ctrlrange="-100 100"/>
    <motor name="m2" joint="j2" ctrllimited="true" ctrlrange="-100 100"/>
  </actuator>
</mujoco>
"""

# Module-level constants shared across all runs
TARGET_QPOS  = np.array([0.5, -0.3])  # target joint angles in radians [j1, j2]
SIM_DURATION = 10.0                    # seconds

def run_pd(model: mujoco.MjModel, kp: float, kd: float) -> tuple[np.ndarray, np.ndarray]:
    data       = mujoco.MjData(model)
    steps      = int(SIM_DURATION / model.opt.timestep)
    timestamps = np.zeros(steps)
    q          = np.zeros((steps, 2))
    for i in range(steps):
        data.ctrl[:2] = kp * (TARGET_QPOS - data.qpos[:2]) - kd * data.qvel[:2]
        mujoco.mj_step(model, data)
        timestamps[i] = data.time
        q[i]          = data.qpos[:2]
    return timestamps, q

if __name__ == "__main__":
    model = mujoco.MjModel.from_xml_string(ARM_XML)
    configs = [
        (5,  2, "kp=5   kd=2   slow — kp too low"),
        (30, 1, "kp=30  kd=1   well-tuned — fast, smooth"),
        (30, 5, "kp=30  kd=5   overshoot — kd too high"),
        (80, 5, "kp=80  kd=5   aggressive — kp too high, big overshoot"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("PD Controller — joint j1  (target = 28.6°, dashed red)")
    for ax, (kp, kd, label) in zip(axes.flat, configs):
        timestamps, q = run_pd(model, kp, kd)
        ax.plot(timestamps, np.degrees(q[:, 0]))
        ax.axhline(np.degrees(TARGET_QPOS[0]), color="r", linestyle="--", label="target")
        ax.set_title(label); ax.set_xlabel("time (s)"); ax.set_ylabel("angle (deg)")
        ax.legend()
    plt.tight_layout()
    fig.savefig("pd_gains.png")
    print("Saved pd_gains.png")