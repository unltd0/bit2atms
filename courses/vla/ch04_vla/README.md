# Chapter 4 — Vision-Language-Action Models

**Time:** 2–3 days
**Hardware:** CPU or MPS for inference · CUDA (T4 16 GB) for fine-tuning
**Prerequisites:** Chapter 3 (Imitation Learning, LeRobot)

---

## What are we here for

ACT and Diffusion Policy are trained per-task: collect demos, train, deploy. They have
no concept of language — no idea what "red ball" or "pick up" means. A **Vision-Language-Action (VLA) model** is different. It's a large pretrained model that has seen millions of robot
demonstrations across hundreds of tasks and robots. You give it a natural language instruction
and a camera image; it outputs robot joint targets.

This chapter uses **SmolVLA** — a 450M-parameter VLA from HuggingFace. It was pretrained on
the [Open X-Embodiment dataset](https://arxiv.org/abs/2310.08864) — ~1M demonstrations from
22 robot types across 50+ institutions — then fine-tuned on real SO-101 pick-and-place data.

**What you'll build:** Type a language instruction → watch a simulated SO-101 arm try to
execute it in MuJoCo → understand the VLA interface before using a real robot in Ch5.

**Hardware by project:**

| Project | What runs | Where |
|---------|-----------|-------|
| A — Interactive sim | SmolVLA forward pass (~2 GB VRAM) | CPU, MPS, or any CUDA GPU |
| B — Probe language | Same as A, repeated across instructions | CPU, MPS, or any CUDA GPU |
| C — Fine-tune (optional) | Full backward pass, 50k steps | **CUDA required** · Colab free T4 works |

**Install:**
```bash
cd workspace/ext/lerobot
pip install -e ".[smolvla]"
```

**Working directory:** `workspace/vla/ch04/`

**Skip if you can answer:**
1. What does a VLA take as input and produce as output?
2. Why fine-tune a pretrained VLA rather than train ACT from scratch on the same data?
3. A VLA trained on real robot photos is loaded into a MuJoCo sim. What do you expect?

---

## Projects

| # | Project | What you build |
|---|---------|---------------|
| A | Interactive Sim | Type instruction → SO-101 arm moves in MuJoCo |
| B | Probe Language | Measure whether instruction phrasing changes behavior |
| C | Fine-tune (optional) | Adapt SmolVLA to new data; compare with zero-shot |

---

## Project A — Interactive Sim

**Problem:** A **VLA** (Vision-Language-Action model) takes three things in and produces robot actions out:

| Input | Where it comes from |
|-------|--------------------|
| **Vision** — camera images | Simulated by MuJoCo, or real photos from a robot's cameras |
| **Language** — what you want to happen | You type it: "pick up the red block" |
| **State** — where the robot currently is | Joint angles read from the simulator |

| Output | What it means |
|--------|---------------|
| **Action** — joint targets | Tells each motor how much to turn this step |

The best way to build intuition for how a VLA works is to see all three inputs and the output in one interactive loop: simulate camera views → type an instruction → watch the arm move.

**Approach:** Load a SmolVLA checkpoint fine-tuned on real SO-101 pick-and-place data. Set up two virtual cameras in a MuJoCo SO-101 scene. Each sim step: render both cameras → feed to policy → apply the output joint targets → step the sim → repeat.

### What a VLA is

A VLA has three parts:

1. **Vision encoder** — extracts features from camera images (a ViT inside SmolVLM-256M)
2. **Language encoder** — encodes your instruction string into a token sequence
3. **Action decoder** — takes the combined vision+language features and outputs joint targets

The checkpoint used here (`lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace`) was
fine-tuned on 50 real SO-101 episodes of a pick-and-place task. It expects:

- **Two cameras:** `observation.images.up` (top-down) and `observation.images.side` (front)
- **Image shape:** 480 × 640, float32, normalised to [0, 1]
- **Output:** 6 joint targets in radians — shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper

### Honest domain gap callout

The checkpoint was trained on **real robot photos**. MuJoCo renders **synthetic images**.
The model will move the arm — often purposefully — but won't reliably complete the task
because the image distribution doesn't match training. This is called the **sim-to-real gap**,
and here you're running it in reverse: real-to-sim.

The useful thing to observe is the *interface* — how language and images flow into the model,
how joint targets come out, and what "following an instruction" looks like at the action level.
Closing the gap is Ch5 (real hardware) and the optional fine-tune section below.

### Data flow

```
# inputs to policy.select_action()
up_frame            np.array (480,640,3) uint8  → permute → unsqueeze → /255.0  → tensor (1,3,480,640) float32
side_frame          np.array (480,640,3) uint8  → permute → unsqueeze → /255.0  → tensor (1,3,480,640) float32
data.qpos[:6]       np.array (6,)        float64 → unsqueeze → float32          → tensor (1,6)          float32
instruction         str                          → wrap in list                  → ["pink lego brick..."]

# output
select_action()  →  tensor (1,6)  float32  [on device]
.cpu().numpy()   →  np.array (1,6) float32
[0]              →  np.array (6,)  float32  ← data.ctrl[:] expects this
```

The `[0]` strips the batch dimension — the policy always outputs one action per batch item,
even when batch size is 1.

### Cameras

MuJoCo free cameras are positioned by `lookat` + `distance` + `azimuth` + `elevation`.
The two camera positions below approximate the wrist-cam and overview-cam used during
SO-101 training data collection:

```
up:   pos=[0.25, 0.1, 0.9]   lookat=[0.25, 0.1, 0.0]   — top-down wrist view
side: pos=[0.7, -0.5, 0.4]   lookat=[0.15, 0.05, 0.15]  — front-side overview
```

> 🟢 **Run** — start the interactive sim, type an instruction, watch the arm move.

The script opens a live MuJoCo viewer window. It prompts for an instruction, runs 100 sim
steps with the policy, then prompts again. Press `q` or close the window to exit.

The menagerie must be cloned into `workspace/ext/`:
```bash
git clone https://github.com/google-deepmind/mujoco_menagerie workspace/ext/mujoco_menagerie
```

```python courses/vla/ch04_vla/code/interact_so101.py
"""
Interactive SmolVLA + SO-101 MuJoCo sim.

Type a language instruction → watch the arm try to execute it → repeat.

NOTE: Domain gap is real. The checkpoint was trained on real robot photos;
MuJoCo renders synthetic images. The arm will move, but not accurately.
That's expected — Ch5 is where you close the gap on real hardware.

Usage:
    cd workspace/vla/ch04
    uv run --extra smolvla python interact_so101.py

Requirements:
    mujoco, torch, lerobot (with smolvla extra), Pillow
"""

import os
import sys
import math
import numpy as np
import mujoco
import mujoco.viewer
import torch
from PIL import Image

# ── checkpoint ────────────────────────────────────────────────────────────────
# Fine-tuned on 50 real SO-101 pick-and-place episodes.
# Task phrasing it understands: "pink lego brick into the transparent box"
CHECKPOINT = "lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace"

# Camera positions that give the model views similar to its training setup.
# up:   top-down wrist cam        side: front-side overview cam
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


# ── camera helper ─────────────────────────────────────────────────────────────
def _make_mjv_camera(pos: np.ndarray, lookat: np.ndarray) -> mujoco.MjvCamera:
    """Build a free MuJoCo camera aimed from pos toward lookat."""
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE

    diff = pos - lookat
    dist = float(np.linalg.norm(diff))
    azimuth   = math.degrees(math.atan2(diff[1], diff[0]))
    elevation = math.degrees(math.atan2(diff[2], math.sqrt(diff[0]**2 + diff[1]**2)))

    cam.lookat[:] = lookat
    cam.distance   = dist
    cam.azimuth    = azimuth
    cam.elevation  = -elevation   # MuJoCo elevation sign convention
    return cam


def render_camera(model, data, renderer: mujoco.Renderer,
                  cam: mujoco.MjvCamera) -> np.ndarray:
    """Return (H, W, 3) uint8 RGB frame from a free camera."""
    renderer.update_scene(data, camera=cam)
    return renderer.render()   # (H, W, 3) uint8


# ── tensor helper ─────────────────────────────────────────────────────────────
def frame_to_tensor(frame: np.ndarray, device) -> torch.Tensor:
    """(H, W, 3) uint8 → (1, 3, H, W) float32 [0, 1]"""
    return (
        torch.tensor(frame, dtype=torch.float32)
             .permute(2, 0, 1)   # HWC → CHW
             .unsqueeze(0)       # → (1, C, H, W)
             .to(device)
        / 255.0
    )


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    # device
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    print(f"Device: {device}")

    # MuJoCo — must chdir so relative STL paths inside the XML resolve
    menagerie_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "ext",
        "mujoco_menagerie", "robotstudio_so101"
    )
    menagerie_dir = os.path.realpath(menagerie_dir)
    if not os.path.isdir(menagerie_dir):
        sys.exit(f"Menagerie not found at {menagerie_dir}\n"
                 "Run:  git clone https://github.com/google-deepmind/mujoco_menagerie "
                 "workspace/ext/mujoco_menagerie")

    os.chdir(menagerie_dir)
    model = mujoco.MjModel.from_xml_path("scene_box.xml")
    data  = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    # off-screen renderer for the two virtual cameras
    renderer = mujoco.Renderer(model, height=IMG_H, width=IMG_W)
    cameras = {
        name: _make_mjv_camera(cfg["pos"], cfg["lookat"])
        for name, cfg in CAM_CONFIGS.items()
    }

    # SmolVLA policy
    print(f"Loading {CHECKPOINT} …")
    from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
    policy = SmolVLAPolicy.from_pretrained(CHECKPOINT).to(device)
    policy.eval()
    print("Policy ready.\n")

    # live viewer (opens a window; Ctrl-C or close window to exit)
    print("Opening MuJoCo viewer … close the window or press Ctrl-C to quit.\n")

    STEPS_PER_INSTRUCTION = 100   # how many sim steps per instruction

    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            try:
                instruction = input(
                    "Instruction (Enter for default, q to quit): "
                ).strip()
            except (EOFError, KeyboardInterrupt):
                break

            if instruction.lower() in ("q", "quit", "exit"):
                break
            if not instruction:
                instruction = "pink lego brick into the transparent box"
            print(f"Running: '{instruction}'  ({STEPS_PER_INSTRUCTION} steps)")

            policy.reset()   # clear any temporal state between instructions

            for step in range(STEPS_PER_INSTRUCTION):
                up_frame   = render_camera(model, data, renderer, cameras["up"])
                side_frame = render_camera(model, data, renderer, cameras["side"])

                # current joint positions (6,) → (1, 6) float32
                joint_state = torch.tensor(
                    data.qpos[:6], dtype=torch.float32
                ).unsqueeze(0).to(device)

                with torch.no_grad():
                    action = policy.select_action({
                        "observation.images.up":   frame_to_tensor(up_frame,   device),
                        "observation.images.side": frame_to_tensor(side_frame, device),
                        "observation.state":       joint_state,
                        "task": [instruction],
                    })

                # action: tensor (1, 6) → numpy (6,) joint targets [rad]
                joint_targets = action.cpu().numpy()[0]
                data.ctrl[:] = joint_targets
                mujoco.mj_step(model, data)
                viewer.sync()

            print(f"Done. Joint positions: {data.qpos[:6].round(3)}\n")

    print("Viewer closed.")


if __name__ == "__main__":
    main()
```

**What to observe:**

- The arm moves in response to your instruction — even across phrasings it hasn't seen, it
  produces *something* purposeful. That's the pretrained prior at work.
- The motion won't complete the pick-and-place accurately. Images look wrong to the model
  (synthetic vs. real). This is the gap Ch5 closes.
- Try: `"pick up the block"`, `"open gripper"`, `"do nothing"` — notice how different
  instructions produce different joint trajectories even without task completion.
- `policy.reset()` between instructions clears the action chunk buffer. Without it, leftover
  temporal state from the previous run bleeds into the next.

**Known instructions the checkpoint was trained on:**
```
"pink lego brick into the transparent box"
```
Other phrasings will be interpreted via language similarity — results will vary.

---

## Project B — Probe Language Conditioning

**Problem:** Does the language instruction actually change the policy's behavior, or is it
passed through and ignored?

**Approach:** Run the interactive sim with semantically different instructions and observe
whether the joint trajectories diverge. You can't measure "success" here (no ground truth
in free-form sim), so measure joint displacement instead — how far did the arm move, and
in which direction?

> 🟡 **Know** — read the structure; run `interact_so101.py` with each group and note the
> joint position printout after each run.

```python courses/vla/ch04_vla/code/probe_language.py
"""
Probe SmolVLA language conditioning on the SO-101 MuJoCo sim.
Runs each instruction for 50 steps and prints final joint positions.
Compare groups to see whether language changes the trajectory.
"""
import os, sys, math
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

def run_instruction(model, data, renderer, cameras, policy, instruction, device):
    mujoco.mj_resetData(model, data)
    mujoco.mj_forward(model, data)
    policy.reset()
    for _ in range(STEPS):
        frames = {}
        for name, cam in cameras.items():
            renderer.update_scene(data, camera=cam)
            frame = renderer.render()
            frames[name] = (
                torch.tensor(frame, dtype=torch.float32)
                     .permute(2,0,1).unsqueeze(0).to(device) / 255.0
            )
        joint_state = torch.tensor(
            data.qpos[:6], dtype=torch.float32
        ).unsqueeze(0).to(device)
        with torch.no_grad():
            action = policy.select_action({
                "observation.images.up":   frames["up"],
                "observation.images.side": frames["side"],
                "observation.state":       joint_state,
                "task": [instruction],
            })
        data.ctrl[:] = action.cpu().numpy()[0]
        mujoco.mj_step(model, data)
    return data.qpos[:6].copy()

if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")

    menagerie_dir = os.path.realpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "ext",
                     "mujoco_menagerie", "robotstudio_so101")
    )
    os.chdir(menagerie_dir)
    model    = mujoco.MjModel.from_xml_path("scene_box.xml")
    data     = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, height=IMG_H, width=IMG_W)
    cameras  = {n: _make_cam(c["pos"], c["lookat"]) for n, c in CAM_CONFIGS.items()}

    from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
    policy = SmolVLAPolicy.from_pretrained(CHECKPOINT).to(device)
    policy.eval()

    for group, instructions in INSTRUCTION_GROUPS.items():
        print(f"\n── {group} ──")
        for instr in instructions:
            qpos = run_instruction(model, data, renderer, cameras, policy, instr, device)
            print(f"  '{instr}'")
            print(f"    joints (rad): {qpos.round(3)}")
```

**What to observe:** If trained-task paraphrases cluster to similar joint positions and
different-task instructions diverge, language conditioning is working. If all groups produce
nearly identical trajectories, the model is relying on visual features alone and ignoring
language — possible given the sim-to-real gap.

---

## Project C — Fine-tune (optional)

**Why bother fine-tuning here?** The pretrained checkpoint already "knows" the SO-101
pick-and-place task. Fine-tuning on new data makes sense when you have a *different* task or
robot. This section shows the mechanics — run it if you want hands-on experience with the
LeRobot training pipeline, or skip to Ch5 (real hardware).

### The dataset

[`lerobot/svla_so101_pickplace`](https://huggingface.co/datasets/lerobot/svla_so101_pickplace)
— 50 real SO-101 pick-and-place episodes, task: "pink lego brick into the transparent box."
This is the same data the checkpoint was trained on — fine-tuning here is mostly a pipeline
exercise, not a new capability.

SmolVLA inference uses ~2 GB VRAM — runs anywhere. Fine-tuning needs a CUDA GPU; Colab
free T4 (16 GB) works with `--batch_size=16`. MPS and CPU will OOM.

> 🟢 **Run** — kick off fine-tuning (~60–90 min on a T4); inspect the loss curve.

```bash courses/vla/ch04_vla/code/finetune_smolvla.sh
cd workspace/ext/lerobot

uv run --extra smolvla --extra training --extra dataset \
  lerobot-train \
    --policy.path=lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace \
    --dataset.repo_id=lerobot/svla_so101_pickplace \
    --batch_size=16 \
    --steps=10000 \
    --policy.push_to_hub=false \
    --output_dir=outputs/smolvla_so101_ft
```

> 🔴 **Work** — compare zero-shot (base checkpoint) vs. fine-tuned using `probe_language.py`:
> point `CHECKPOINT` at your new checkpoint and run both; compare joint trajectories.

**What to observe:** With only 50 episodes, fine-tuning mainly reinforces the task phrasing
and timing — don't expect a dramatic change. The value here is understanding the pipeline:
dataset → training loop → checkpoint → evaluation.

---

## Self-Check

1. You run `interact_so101.py` and the arm barely moves for any instruction. What are two
   likely causes?
   **Answer:** (a) The sim images look so different from training (domain gap) that the model
   is uncertain and outputs near-zero actions. (b) `policy.reset()` is missing — stale
   temporal state from a previous run is leaking in and confusing the decoder.

2. In Project B, trained-task paraphrases and different-task instructions produce nearly
   identical joint trajectories. What does that tell you?
   **Answer:** The model is relying on visual features alone and ignoring the language token
   sequence — likely because the image distribution (synthetic) is so far from training
   (real) that the vision encoder dominates. On real hardware this gap disappears.

3. The checkpoint expects `observation.images.up` and `observation.images.side`. You pass
   `observation.image` instead. What happens?
   **Answer:** The policy raises `ValueError: All image features are missing` — it can't find
   any of the expected camera keys. Key names are part of the model's interface contract, not
   flexible.

4. Why do you call `policy.reset()` between instructions in `interact_so101.py`?
   **Answer:** SmolVLA uses action chunking — it buffers a sequence of predicted actions and
   replays them over several steps. `reset()` clears this buffer. Without it, the tail of the
   previous instruction's action sequence bleeds into the next run.

5. You want to adapt SmolVLA to a completely new task on a different robot. How many demos
   do you need, roughly, and why less than ACT from scratch?
   **Answer:** 20–50 demos is a reasonable starting point. SmolVLA already has pretrained
   priors for robot motion, spatial reasoning, and language-action mapping from millions of
   demonstrations. Fine-tuning adapts those priors to your task — ACT from scratch must
   learn everything from your demos alone.

---

## Common Mistakes

- **Wrong camera key names:** `observation.image` will fail. The checkpoint expects exactly
  `observation.images.up` and `observation.images.side`. Check `policy.config` for the
  expected keys if you use a different checkpoint.

- **Expecting zero-shot to complete the task in sim:** It won't — the domain gap between
  synthetic MuJoCo renders and real robot photos is too large. The point of Project A is
  to understand the interface and observe motion, not to achieve task success.

- **Forgetting `policy.reset()` between episodes:** Stale action chunks from a previous
  run leak into the next. Always reset before a new episode or instruction.

- **Running fine-tuning on MPS or CPU:** MPS will OOM during the backward pass. CPU will
  take days. Use a CUDA GPU — Colab free T4 with `--batch_size=16` is the minimum viable
  setup.

- **Skipping `os.chdir` before loading the XML:** MuJoCo resolves STL asset paths relative
  to the XML file's directory. If the working directory is wrong, it raises
  `mujoco._structs.MjModel` errors about missing mesh files.

---

## Resources

1. [SmolVLA blog post](https://huggingface.co/blog/smolvla) — architecture overview and benchmark results
2. [OpenVLA paper](https://arxiv.org/abs/2406.09246) — design decisions behind open-weight VLAs
3. [Open X-Embodiment paper](https://arxiv.org/abs/2310.08864) — the pretraining dataset that gives SmolVLA its priors
4. [π0 paper](https://arxiv.org/abs/2410.24164) — state-of-art VLA for dexterous manipulation
5. [MuJoCo Menagerie SO-101](https://github.com/google-deepmind/mujoco_menagerie/tree/main/robotstudio_so101) — the robot model used in this chapter
