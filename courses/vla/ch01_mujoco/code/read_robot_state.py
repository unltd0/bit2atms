"""Load the Franka Panda, read joint states and body poses in two configurations."""
import numpy as np
import mujoco
import mujoco.viewer
import os

# Resolve from cwd (repo root) — run this script from the repo root regardless of where you saved it.
FRANKA_XML = "workspace/ext/mujoco_menagerie/franka_emika_panda/scene.xml"

def print_robot_info(model: mujoco.MjModel) -> None:
    print(f"Bodies: {model.nbody}  Joints: {model.njnt}  Actuators: {model.nu}")
    print("\nJoint names and limits:")
    for i in range(model.njnt):
        name = model.joint(i).name
        lo, hi = model.jnt_range[i]
        print(f"  [{i}] {name:30s}  [{np.degrees(lo):.0f}°, {np.degrees(hi):.0f}°]")

def read_body_poses(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    """Print all body positions. Assumes mj_forward has already been called."""
    print("\nBody positions (world frame):")
    for i in range(1, model.nbody):
        print(f"  {model.body(i).name:30s}  {np.round(data.xpos[i], 3)}")

def demo_two_configurations(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    ee_id = model.body("hand").id

    mujoco.mj_resetData(model, data)
    # qpos[:7] = the 7 joint angles in radians, one per DOF (shoulder → wrist)
    data.qpos[:7] = [0, -0.785, 0, -2.356, 0, 1.571, 0.785]
    mujoco.mj_forward(model, data)
    print(f"\nNeutral pose  — EE: {np.round(data.xpos[ee_id], 3)}")
    read_body_poses(model, data)

    data.qpos[:7] = [0.785, -0.785, 0, -2.356, 0, 1.571, 0.785]
    mujoco.mj_forward(model, data)
    print(f"\nRotated pose  — EE: {np.round(data.xpos[ee_id], 3)}")
    read_body_poses(model, data)

    print("\nSame arm, joint 0 rotated 45° → different EE position. That's FK.")

if __name__ == "__main__":
    if not os.path.exists(FRANKA_XML):
        print("Could not find Menagerie. Run from the repo root and clone it first:")
        print("  git clone https://github.com/google-deepmind/mujoco_menagerie workspace/ext/mujoco_menagerie")
        print("Then run:  python courses/vla/ch01_mujoco/code/read_robot_state.py")
        raise SystemExit(1)

    model = mujoco.MjModel.from_xml_path(FRANKA_XML)
    data  = mujoco.MjData(model)
    print_robot_info(model)
    demo_two_configurations(model, data)

    print("\nLaunching viewer. Double-click a body to select it, use right-panel sliders to move joints.")
    print("(Skip the viewer block if running headless/SSH — the printed output above is the deliverable.)")
    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            mujoco.mj_step(model, data)  # no ctrl set — arm falls under gravity; that's expected
            viewer.sync()
