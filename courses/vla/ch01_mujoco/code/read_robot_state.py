"""FK demo: set joint angles, read end-effector position. No physics simulation."""
import numpy as np
import mujoco

# Run from repo root: python courses/vla/ch01_mujoco/code/read_robot_state.py
FRANKA_XML = "workspace/ext/mujoco_menagerie/franka_emika_panda/scene.xml"

model = mujoco.MjModel.from_xml_path(FRANKA_XML)
data  = mujoco.MjData(model)
ee_id = model.body("hand").id

# Config 1 — neutral pose
data.qpos[:7] = [0, -0.785, 0, -2.356, 0, 1.571, 0.785]
mujoco.mj_forward(model, data)          # FK: compute all body positions from qpos
ee1 = data.xpos[ee_id].copy()
print(f"Config 1  qpos[0]=0 rad      EE={np.round(ee1, 3)}")

# Config 2 — rotate base joint 45°, everything else identical
# Comment out the next line → qpos stays as Config 1 → EE won't move
data.qpos[0] = 0.785                    # <-- comment this out to see no change
mujoco.mj_forward(model, data)
ee2 = data.xpos[ee_id].copy()
print(f"Config 2  qpos[0]=0.785 rad  EE={np.round(ee2, 3)}")

delta = ee2 - ee1
print(f"\nEE moved by {np.round(delta, 3)}  ({np.linalg.norm(delta):.3f} m)")
print("One joint angle changed → EE moved. That's forward kinematics.")

# Viewer: shows the final pose. On macOS: mjpython courses/vla/ch01_mujoco/code/read_robot_state.py
import mujoco.viewer
try:
    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            data.ctrl[:7] = data.qpos[:7]   # hold pose — counteracts gravity
            mujoco.mj_step(model, data)
            viewer.sync()
except RuntimeError:
    print("Viewer requires mjpython on macOS — printed output above is the deliverable.")
