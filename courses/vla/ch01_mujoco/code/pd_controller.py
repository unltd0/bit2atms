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

# Target joint angles in radians [j1, j2]
TARGET_QPOS  = np.array([0.5, -0.3])
SIM_DURATION = 3.0

def run_pd(kp: float, kd: float) -> tuple[np.ndarray, np.ndarray]:
    model      = mujoco.MjModel.from_xml_string(ARM_XML)
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
    configs = [
        (50,  1,  "kp=50  kd=1   underdamped"),
        (50,  10, "kp=50  kd=10  well-tuned"),
        (200, 1,  "kp=200 kd=1   oscillates"),
        (200, 30, "kp=200 kd=30  well-tuned high stiffness"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("PD Controller — joint j1 trajectory")
    for ax, (kp, kd, label) in zip(axes.flat, configs):
        timestamps, q = run_pd(kp, kd)
        ax.plot(timestamps, np.degrees(q[:, 0]))
        ax.axhline(np.degrees(TARGET_QPOS[0]), color="r", linestyle="--", label="target")
        ax.set_title(label); ax.set_xlabel("time (s)"); ax.set_ylabel("angle (deg)")
        ax.legend()
    plt.tight_layout()
    fig.savefig("pd_gains.png")
    print("Saved pd_gains.png")