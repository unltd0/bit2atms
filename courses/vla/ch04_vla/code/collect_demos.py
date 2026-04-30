"""
Collect scripted SO-101 grip demos in MuJoCo for SmolVLA finetuning.

A classical controller moves the arm to the green box and closes the gripper.
50 episodes → LeRobot dataset that lerobot-train can consume directly.

Usage:
    python workspace/vla/ch04/collect_demos.py   # when in repo root
    python collect_demos.py                      # when inside workspace/vla/ch04/

Output: workspace/vla/ch04/sim_grip_data/  (~100 MB, ~50s on Mac)
"""
import os, sys, math, shutil
import numpy as np
import mujoco
from lerobot.datasets.lerobot_dataset import LeRobotDataset

# ── paths ───────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Auto-detect: student copies this to workspace/vla/ch04/
# courses/vla/ch04_vla/code/ → 4 levels | workspace/vla/ch04/ → 3 levels
if '/courses/' in SCRIPT_DIR:
    # Courseware location (not used by students, but kept for reference)
    REPO_ROOT = os.path.realpath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))
else:
    # Student workspace (scripts/ and assets/ are relative to repo root)
    REPO_ROOT = os.path.realpath(os.path.join(SCRIPT_DIR, "..", ".."))

MENAGERIE  = os.path.join(REPO_ROOT, "workspace", "ext",
                           "mujoco_menagerie", "robotstudio_so101")
SCENE_XML  = os.path.join(REPO_ROOT, "courses", "vla", "ch04_vla", "assets", "scene_grip.xml")
HOME       = np.zeros(6)
PICKUP_ARM = np.array([0.0, 0.000382, 0.473496, 1.17717, 1.58437, 0.0])
BOX_POS    = np.array([0.219, 0.024, 0.020])

# ── episode config ─────────────────────────────────────────────────────────
def make_episode_env():
    if not os.path.isdir(MENAGERIE):
        sys.exit(f"Menagerie not found at {MENAGERIE}\n"
                 "Run: git clone https://github.com/google-deepmind/mujoco_menagerie "
                 "workspace/ext/mujoco_menagerie")
    if not os.path.isfile(SCENE_XML):
        sys.exit(f"Scene XML not found: {SCENE_XML}")

    shutil.copy(SCENE_XML, os.path.join(MENAGERIE, "scene_grip.xml"))
    os.chdir(MENAGERIE)
    m = mujoco.MjModel.from_xml_path("scene_grip.xml")
    d = mujoco.MjData(m)
    mujoco.mj_forward(m, d)
    return m, d

# ── episode loop ────────────────────────────────────────────────────────────
def run_episode(m, d):
    d.qpos[:] = HOME
    mujoco.mj_forward(m, d)

    for step in range(EP_STEPS):
        # Move to box position
        if step == 50:
            d.qpos[:6] = PICKUP_ARM
            mujoco.mj_forward(m, d)
        # Close gripper
        if step == 100:
            d.ctrl[6] = -1.0  # gripper close
        mujoco.mj_step(m, d)
    return d

def main():
    print(f"Collecting {N_EPISODES} episodes → {OUT_DIR}")
    os.makedirs(OUT_DIR, exist_ok=True)

    dataset = LeRobotDataset.create(
        "local/sim_grip",
        root=OUT_DIR,
        fps=FPS,
        features={
            "observation.image": {"dtype": "float32", "shape": (480, 640, 3)},
            "observation.state": {"dtype": "float32", "shape": (6,)},
            "action": {"dtype": "float32", "shape": (6,)},
        },
    )

    for ep in range(N_EPISODES):
        m, d = make_episode_env()
        d = run_episode(m, d)

        # Save frames (simplified — full code in actual file)
        # ... (episode recording logic) ...

        if (ep + 1) % 10 == 0:
            print(f"  {ep+1}/{N_EPISODES} episodes done")

    print(f"\nDone. {N_EPISODES} episodes, {N_EPISODES * EP_STEPS} frames")
    print(f"Dataset: {OUT_DIR}")

if __name__ == "__main__":
    main()
