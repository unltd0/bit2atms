"""
Interactive SmolVLA + SO-101 MuJoCo sim.

Type a language instruction → watch the arm try to execute it → repeat.

NOTE: Domain gap is real. The checkpoint was trained on real robot photos;
MuJoCo renders synthetic images. The arm will move, but not accurately.
That's expected — Ch5 is where you close the gap on real hardware.

Usage:
    cd workspace/vla/ch04
    python interact_so101.py

Requirements:
    mujoco, torch, lerobot (with smolvla extra)
"""

import os
import sys
import math
import numpy as np
import mujoco
import mujoco.viewer
import torch

# Override via env: CHECKPOINT=path/to/ckpt python interact_so101.py
CHECKPOINT = os.environ.get(
    "CHECKPOINT",
    "lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace",
)

# Camera positions that approximate the wrist-cam and overview-cam used during training.
CAM_CONFIGS = {
    "up": {
        "pos":    np.array([0.25, 0.1,  0.9]),
        "lookat": np.array([0.25, 0.1,  0.0]),
    },
    "side": {
        "pos":    np.array([0.7,  -0.5, 0.4]),
        "lookat": np.array([0.15, 0.05, 0.15]),
    },
}
IMG_H, IMG_W = 480, 640   # shape the checkpoint expects


def _make_mjv_camera(pos: np.ndarray, lookat: np.ndarray) -> mujoco.MjvCamera:
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    diff = pos - lookat
    dist = float(np.linalg.norm(diff))
    cam.lookat[:] = lookat
    cam.distance   = dist
    cam.azimuth    = math.degrees(math.atan2(diff[1], diff[0]))
    cam.elevation  = -math.degrees(math.atan2(diff[2], math.sqrt(diff[0]**2 + diff[1]**2)))
    return cam


def render_camera(renderer, data, cam) -> np.ndarray:
    """Return (H, W, 3) uint8 RGB."""
    renderer.update_scene(data, camera=cam)
    return renderer.render()


def make_obs(data, frames, lang_tokens, lang_mask, device):
    """Build the batch dict that policy.select_action() expects."""
    def img_tensor(frame):
        # (H,W,3) uint8 → (1,3,H,W) float32 [0,1]
        return (
            torch.tensor(frame, dtype=torch.float32)
                 .permute(2, 0, 1).unsqueeze(0).to(device) / 255.0
        )
    return {
        "observation.images.up":              img_tensor(frames["up"]),
        "observation.images.side":            img_tensor(frames["side"]),
        # current joint positions: (6,) float64 → (1,6) float32
        "observation.state":                  torch.tensor(
                                                  data.qpos[:6], dtype=torch.float32
                                              ).unsqueeze(0).to(device),
        "observation.language.tokens":        lang_tokens.to(device),
        "observation.language.attention_mask": lang_mask.to(device),
    }


def main():
    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
    print(f"Device: {device}")

    # MuJoCo — chdir so STL asset paths relative to the XML resolve correctly
    menagerie_dir = os.path.realpath(os.path.join(
        os.path.dirname(__file__), "..", "..", "ext",
        "mujoco_menagerie", "robotstudio_so101"
    ))
    if not os.path.isdir(menagerie_dir):
        sys.exit(
            f"Menagerie not found at {menagerie_dir}\n"
            "Run:  git clone https://github.com/google-deepmind/mujoco_menagerie "
            "workspace/ext/mujoco_menagerie"
        )

    os.chdir(menagerie_dir)
    model = mujoco.MjModel.from_xml_path("scene_box.xml")
    data  = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    renderer = mujoco.Renderer(model, height=IMG_H, width=IMG_W)
    cameras  = {n: _make_mjv_camera(c["pos"], c["lookat"]) for n, c in CAM_CONFIGS.items()}

    # SmolVLA policy
    print(f"Loading {CHECKPOINT} …")
    from lerobot.policies.smolvla import SmolVLAPolicy
    policy = SmolVLAPolicy.from_pretrained(CHECKPOINT).to(device)
    policy.eval()

    # Tokenizer lives inside the VLM component
    tokenizer = policy.model.vlm_with_expert.processor.tokenizer
    max_len   = policy.config.tokenizer_max_length
    print("Policy ready.\n")

    def tokenize(instruction: str):
        enc = tokenizer(
            instruction + "\n",       # trailing newline matches training format
            padding="max_length",
            max_length=max_len,
            return_tensors="pt",
            truncation=True,
        )
        return enc["input_ids"], enc["attention_mask"].bool()

    STEPS_PER_INSTRUCTION = 100

    print("Opening MuJoCo viewer … close the window or press Ctrl-C to quit.\n")
    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            try:
                instruction = input("Instruction (Enter for default, q to quit): ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if instruction.lower() in ("q", "quit", "exit"):
                break
            if not instruction:
                instruction = "pink lego brick into the transparent box"
            print(f"Running: '{instruction}'  ({STEPS_PER_INSTRUCTION} steps)")

            lang_tokens, lang_mask = tokenize(instruction)
            policy.reset()

            for _ in range(STEPS_PER_INSTRUCTION):
                frames = {
                    name: render_camera(renderer, data, cam)
                    for name, cam in cameras.items()
                }
                obs = make_obs(data, frames, lang_tokens, lang_mask, device)

                with torch.no_grad():
                    action = policy.select_action(obs)

                # action: tensor (1,6) → numpy (6,) joint targets [rad]
                data.ctrl[:] = action.cpu().numpy()[0]
                mujoco.mj_step(model, data)
                viewer.sync()

            print(f"Done. Joint positions: {data.qpos[:6].round(3)}\n")

    print("Viewer closed.")


if __name__ == "__main__":
    main()
