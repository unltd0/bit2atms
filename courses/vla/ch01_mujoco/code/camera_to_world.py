"""
Given a cup position in camera (wrist) frame, compute its world-frame position.
The core transform computation used in every pick-and-place pipeline.
"""
import numpy as np
import mujoco
import os

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FRANKA_XML = os.path.join(_SCRIPT_DIR, "../../../../workspace/ext/mujoco_menagerie/franka_emika_panda/scene.xml")

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
    hand_id = model.body("hand").id
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
    print("Try: set cup_in_camera = [0,0,0] → you get hand's exact world position.")
