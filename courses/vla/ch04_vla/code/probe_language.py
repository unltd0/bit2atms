"""
Probe SmolVLA language conditioning on the SO-101 MuJoCo sim.
Runs each instruction for 50 steps and prints final joint positions.
Compare groups to see whether language changes the trajectory.
"""
import os
import math
import numpy as np
import mujoco
import torch

CHECKPOINT = "lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace"
IMG_H, IMG_W = 480, 640
STEPS = 50

CAM_CONFIGS = {
    "up":   {"pos": np.array([0.25, 0.1, 0.9]),  "lookat": np.array([0.25, 0.1, 0.0])},
    "side": {"pos": np.array([0.7, -0.5, 0.4]),  "lookat": np.array([0.15, 0.05, 0.15])},
}

INSTRUCTION_GROUPS = {
    "trained task (paraphrases)": [
        "pink lego brick into the transparent box",
        "place the pink block in the box",
        "pick up the lego and put it in the container",
    ],
    "different task": [
        "wave hello",
        "do nothing",
        "move left",
    ],
}


def _make_cam(pos, lookat):
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    diff = pos - lookat
    dist = float(np.linalg.norm(diff))
    cam.lookat[:] = lookat
    cam.distance  = dist
    cam.azimuth   = math.degrees(math.atan2(diff[1], diff[0]))
    cam.elevation = -math.degrees(math.atan2(diff[2], math.sqrt(diff[0]**2 + diff[1]**2)))
    return cam


def img_tensor(frame, device):
    """(H,W,3) uint8 → (1,3,H,W) float32 [0,1]"""
    return torch.tensor(frame, dtype=torch.float32).permute(2,0,1).unsqueeze(0).to(device) / 255.0


def run_instruction(model, data, renderer, cameras, policy, tokenizer, max_len,
                    instruction, device):
    mujoco.mj_resetData(model, data)
    mujoco.mj_forward(model, data)
    policy.reset()

    enc = tokenizer(
        instruction + "\n",
        padding="max_length",
        max_length=max_len,
        return_tensors="pt",
        truncation=True,
    )
    lang_tokens = enc["input_ids"].to(device)
    lang_mask   = enc["attention_mask"].bool().to(device)

    for _ in range(STEPS):
        frames = {}
        for name, cam in cameras.items():
            renderer.update_scene(data, camera=cam)
            frames[name] = renderer.render()

        obs = {
            "observation.images.up":               img_tensor(frames["up"],   device),
            "observation.images.side":             img_tensor(frames["side"], device),
            "observation.state":                   torch.tensor(
                                                       data.qpos[:6], dtype=torch.float32
                                                   ).unsqueeze(0).to(device),
            "observation.language.tokens":         lang_tokens,
            "observation.language.attention_mask": lang_mask,
        }

        with torch.no_grad():
            action = policy.select_action(obs)
        data.ctrl[:] = action.cpu().numpy()[0]
        mujoco.mj_step(model, data)

    return data.qpos[:6].copy()


if __name__ == "__main__":
    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")

    menagerie_dir = os.path.realpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "ext",
                     "mujoco_menagerie", "robotstudio_so101")
    )
    os.chdir(menagerie_dir)
    model    = mujoco.MjModel.from_xml_path("scene_box.xml")
    data     = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, height=IMG_H, width=IMG_W)
    cameras  = {n: _make_cam(c["pos"], c["lookat"]) for n, c in CAM_CONFIGS.items()}

    from lerobot.policies.smolvla import SmolVLAPolicy
    policy = SmolVLAPolicy.from_pretrained(CHECKPOINT).to(device)
    policy.eval()

    tokenizer = policy.model.vlm_with_expert.processor.tokenizer
    max_len   = policy.config.tokenizer_max_length

    for group, instructions in INSTRUCTION_GROUPS.items():
        print(f"\n── {group} ──")
        for instr in instructions:
            qpos = run_instruction(model, data, renderer, cameras,
                                   policy, tokenizer, max_len, instr, device)
            print(f"  '{instr}'")
            print(f"    joints (rad): {qpos.round(3)}")
