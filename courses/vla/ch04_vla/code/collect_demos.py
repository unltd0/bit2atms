"""
Collect scripted SO-101 grip demos in MuJoCo for SmolVLA finetuning.

A classical controller moves the arm to the green box and closes the gripper.
50 episodes are saved as a LeRobot dataset that lerobot-train can consume directly.

Usage:
    cd workspace/vla/ch04
    python collect_demos.py

Output: workspace/vla/ch04/sim_grip_data/  (~50 MB, ~50s on Mac)
"""
import os
import sys
import math
import shutil
import numpy as np
import mujoco
from lerobot.datasets.lerobot_dataset import LeRobotDataset

# ── paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT    = os.path.realpath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))
MENAGERIE    = os.path.join(REPO_ROOT, "workspace", "ext",
                             "mujoco_menagerie", "robotstudio_so101")
SCENE_XML    = os.path.join(SCRIPT_DIR, "..", "assets", "scene_grip.xml")
OUT_DIR      = os.path.join(REPO_ROOT, "workspace", "vla", "ch04", "sim_grip_data")
OUT_DIR      = os.path.realpath(OUT_DIR)

# ── episode config ─────────────────────────────────────────────────────────────
TASK       = "grip the green box"
N_EPISODES = 50
FPS        = 30
EP_STEPS   = 180          # 6 s per episode at 30 fps
IMG_H      = 480
IMG_W      = 640

# ── scripted trajectory waypoints ─────────────────────────────────────────────
# joint order: shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper
HOME        = np.zeros(6)
PICKUP_ARM  = np.array([0.0, 0.000382, 0.473496, 1.17717, 1.58437, 0.0])   # arm over box
GRIP_CLOSED = np.array([0.0, 0.000382, 0.473496, 1.17717, 1.58437, 1.6])   # gripper shut
BOX_POS     = np.array([0.219, 0.024, 0.020])   # matches scene_grip.xml

# ── camera positions (same as interact_so101.py) ───────────────────────────────
CAM_CONFIGS = {
    "up":   {"pos": np.array([0.25, 0.1,  0.9]),  "lookat": np.array([0.25, 0.1,  0.0])},
    "side": {"pos": np.array([0.7,  -0.5, 0.4]),  "lookat": np.array([0.15, 0.05, 0.15])},
}


def _make_cam(pos, lookat):
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    diff = pos - lookat
    cam.lookat[:] = lookat
    cam.distance  = float(np.linalg.norm(diff))
    cam.azimuth   = math.degrees(math.atan2(diff[1], diff[0]))
    cam.elevation = -math.degrees(
        math.atan2(diff[2], math.sqrt(diff[0]**2 + diff[1]**2))
    )
    return cam


def scripted_target(step: int) -> np.ndarray:
    """
    Two-phase trajectory:
      0–55% of episode : interpolate arm from home to grasp position (gripper open)
      55–100%          : hold arm, close gripper
    """
    t = step / EP_STEPS
    if t < 0.55:
        return HOME + (t / 0.55) * (PICKUP_ARM - HOME)
    ctrl = PICKUP_ARM.copy()
    ctrl[5] = ((t - 0.55) / 0.45) * 1.6
    return ctrl


def main():
    if not os.path.isdir(MENAGERIE):
        sys.exit(
            f"Menagerie not found at {MENAGERIE}\n"
            "Run: git clone https://github.com/google-deepmind/mujoco_menagerie "
            "workspace/ext/mujoco_menagerie"
        )
    if not os.path.isfile(SCENE_XML):
        sys.exit(f"Scene XML not found: {SCENE_XML}")

    # Copy scene XML into menagerie dir so MuJoCo can resolve the so101.xml include
    scene_in_menagerie = os.path.join(MENAGERIE, "scene_grip.xml")
    shutil.copy(SCENE_XML, scene_in_menagerie)
    os.chdir(MENAGERIE)
    m = mujoco.MjModel.from_xml_path("scene_grip.xml")
    d = mujoco.MjData(m)
    renderer = mujoco.Renderer(m, height=IMG_H, width=IMG_W)
    cameras  = {n: _make_cam(c["pos"], c["lookat"]) for n, c in CAM_CONFIGS.items()}

    features = {
        "observation.images.up":   {
            "dtype": "image", "shape": (IMG_H, IMG_W, 3),
            "names": ["height", "width", "channels"],
        },
        "observation.images.side": {
            "dtype": "image", "shape": (IMG_H, IMG_W, 3),
            "names": ["height", "width", "channels"],
        },
        "observation.state": {
            "dtype": "float32", "shape": (6,),
            "names": ["shoulder_pan.pos", "shoulder_lift.pos", "elbow_flex.pos",
                      "wrist_flex.pos", "wrist_roll.pos", "gripper.pos"],
        },
        "action": {
            "dtype": "float32", "shape": (6,),
            "names": ["shoulder_pan.pos", "shoulder_lift.pos", "elbow_flex.pos",
                      "wrist_flex.pos", "wrist_roll.pos", "gripper.pos"],
        },
    }

    if os.path.exists(OUT_DIR):
        shutil.rmtree(OUT_DIR)

    dataset = LeRobotDataset.create(
        repo_id="local/sim_grip",
        fps=FPS,
        features=features,
        root=OUT_DIR,
        robot_type="so101",
        use_videos=False,
    )

    print(f"Collecting {N_EPISODES} episodes → {OUT_DIR}")
    for ep in range(N_EPISODES):
        mujoco.mj_resetData(m, d)
        d.qpos[:6]   = HOME
        d.qpos[6:9]  = BOX_POS
        d.qpos[9:13] = [1, 0, 0, 0]
        d.ctrl[:6]   = HOME
        mujoco.mj_forward(m, d)

        for step in range(EP_STEPS):
            target = scripted_target(step)
            d.ctrl[:6] = target

            frames = {}
            for name, cam in cameras.items():
                renderer.update_scene(d, camera=cam)
                frames[name] = renderer.render().copy()

            dataset.add_frame({
                "observation.images.up":   frames["up"],
                "observation.images.side": frames["side"],
                "observation.state":       d.qpos[:6].astype(np.float32),
                "action":                  target.astype(np.float32),
                "task":                    TASK,
            })
            mujoco.mj_step(m, d)

        dataset.save_episode()
        if (ep + 1) % 10 == 0:
            print(f"  {ep+1}/{N_EPISODES} episodes done")

    dataset.finalize()
    print(f"\nDone. {dataset.num_episodes} episodes, {dataset.num_frames} frames")
    print(f"Dataset: {OUT_DIR}")


if __name__ == "__main__":
    main()
