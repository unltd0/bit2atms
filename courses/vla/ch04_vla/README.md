# Chapter 4 — Vision-Language-Action Models

**Time:** 1–2 days
**Hardware:** GPU 16 GB+
**Prerequisites:** Chapter 3 (Imitation Learning, LeRobot), Chapter 1 (MuJoCo, viewer)

---

## What are we here for

ACT and Diffusion Policy are trained per-task: collect demos, train, deploy. They have
no concept of language — no idea what "red ball" or "pick up" means. A **Vision-Language-Action (VLA) model** is different. It's a large pretrained model that has seen millions of robot
demonstrations across hundreds of tasks and robots. You give it a natural language instruction
and a camera image; it outputs robot joint targets.

This chapter uses **SmolVLA** — a 450M-parameter VLA from HuggingFace. It was pretrained on
the [Open X-Embodiment dataset](https://arxiv.org/abs/2310.08864) — ~1M demonstrations from
22 robot types across 50+ institutions — then fine-tuned on real [SO-101 pick-and-place data](https://huggingface.co/datasets/lerobot/svla_so101_pickplace).

![SO-101 performing pick-and-place — asynchronous counting, synchronous counting, under perturbations, and lego brick generalization](https://cdn-uploads.huggingface.co/production/uploads/640e21ef3c82bd463ee5a76d/S-3vvVCulChREwHDkquoc.gif)

These are actual frames from the training data — top-down and side cameras, real SO-101, pink lego brick, orange taped target box:

<table><tr>
<td><img src="assets/so101_up.gif" width="100%" alt="Top-down camera — pink lego brick, orange target box"></td>
<td><img src="assets/so101_side.gif" width="100%" alt="Side camera — arm approaching the lego brick"></td>
</tr></table>

**What you'll build:** Type a language instruction → watch a simulated SO-101 arm try to
execute it in MuJoCo → understand the VLA interface before using a real robot in Ch5.

**Hardware by project:**

| Project | What runs | Where |
|---------|-----------|-------|
| A — Interactive sim | SmolVLA forward pass (~2 GB VRAM) | CPU, MPS, or any CUDA GPU |
| B — Probe language | Same as A, repeated across instructions | CPU, MPS, or any CUDA GPU |
| C — Fine-tune SmolVLA | Full backward pass | MPS 16 GB+ Mac (~10 min) · Colab free T4 (~60 min) |

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
4. You fine-tune SmolVLA on 50 sim demos. Will it work on a real robot? Why or why not?

---

## Projects

| # | Project | What you build |
|---|---------|---------------|
| A | Interactive Sim | Type instruction → SO-101 arm moves in MuJoCo |
| B | Probe Language | Measure whether instruction phrasing changes behavior |
| C | Fine-tune SmolVLA | Adapt SmolVLA to sim data; compare zero-shot vs fine-tuned behavior |

---

## Project A — Interactive Sim

**Problem:** A VLA takes three things in and produces robot actions out:

| Input | Where it comes from |
|-------|---------------------|
| **Vision** — camera images | Simulated by MuJoCo, or real photos from a robot's cameras |
| **Language** — what you want to happen | You type it: "pick up the pink lego brick" |
| **State** — where the robot currently is | Joint angles read from the simulator |

| Output | What it means |
|--------|---------------|
| **Action** — joint targets | Tells each motor how much to rotate this step |

The best way to build intuition is to see all three inputs and the output in one interactive
loop: simulate camera views → type an instruction → watch the arm move.

**Approach:** Load a SmolVLA checkpoint fine-tuned on real SO-101 pick-and-place data. Set up
two virtual cameras in a MuJoCo SO-101 scene. Each sim step: render both cameras → tokenize
the instruction → feed everything to policy → apply the output joint targets → step the sim.

### What a VLA is

A VLA has three parts:

1. **Vision encoder** — extracts features from camera images (a ViT inside SmolVLM-500M)
2. **Language encoder** — tokenizes your instruction string into a token sequence
3. **Action decoder** — takes the combined vision+language+state features and outputs joint targets

The checkpoint used here (`lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace`) was
fine-tuned on 50 real SO-101 episodes of a pick-and-place task. It expects:

- **Two cameras:** `observation.images.up` (top-down) and `observation.images.side` (front)
- **Image shape:** 480 × 640, float32, normalised to [0, 1]
- **Joint state:** 6 current joint positions in radians
- **Language:** pre-tokenized to `observation.language.tokens` (int64) and `observation.language.attention_mask` (bool)
- **Output:** 6 joint targets in radians — shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper

### Domain gap — set expectations before you run

> ⚠️ **The arm will move but won't complete the task.** This is expected — not a bug.
>
> Two reasons: (1) the checkpoint was trained on **real robot photos** — MuJoCo renders synthetic images the model has never seen; (2) the scene has a **generic green box**, not the pink lego brick and transparent box from training. The objects don't match, and the images don't match. Don't spend time debugging it — it won't work in sim. That's exactly what Ch5 fixes.
>
> What *is* worth watching: the arm responds to language, moves purposefully, and produces different trajectories for different instructions. That's the interface working correctly.

### Data flow

```
# inputs to policy.select_action()
up_frame           np.array (480,640,3) uint8  → permute → unsqueeze → /255.0 → tensor (1,3,480,640) float32
side_frame         np.array (480,640,3) uint8  → permute → unsqueeze → /255.0 → tensor (1,3,480,640) float32
data.qpos[:6]      np.array (6,)        float64 → unsqueeze → .float32()      → tensor (1,6)          float32
instruction        str                          → tokenizer(max_length=48)     → tensor (1,48)          int64

# output
select_action()  →  tensor (1,6)  float32  [on device]
.cpu().numpy()   →  np.array (1,6) float32
[0]              →  np.array (6,)  float32  ← data.ctrl[:] expects this
```

The tokenizer lives at `policy.model.vlm_with_expert.processor.tokenizer` — it converts
the instruction string to integer token IDs the language encoder understands.
The `[0]` strips the batch dimension — the policy always outputs one action per batch item,
even when batch size is 1.

### Cameras

MuJoCo free cameras are positioned by `lookat` + `distance` + `azimuth` + `elevation`.
These positions approximate the wrist-cam and overview-cam used during SO-101 data collection:

```
up:   pos=[0.25, 0.1, 0.9]   lookat=[0.25, 0.1, 0.0]   — top-down wrist view
side: pos=[0.7, -0.5, 0.4]   lookat=[0.15, 0.05, 0.15]  — front-side overview
```

> ⚠️ **Before you run:** the arm will move but won't complete the pick-and-place. That's expected — synthetic sim images don't match the real photos the model was trained on. Don't debug it. Watch the motion, probe language conditioning, then move to Ch5 for the real thing.

> 🟢 **Run** — start the interactive sim, type an instruction, watch the arm move.

The script opens a live MuJoCo viewer window. It prompts for an instruction, runs 100 sim
steps with the policy, then prompts again. Press `q` or close the window to exit.
The scene XML (box at reachable position) is copied in automatically.

The menagerie must be cloned into `workspace/ext/` first:
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
    python workspace/vla/ch04/interact_so101.py

Requirements:
    mujoco, torch, lerobot (with smolvla extra)
"""

import os, sys, math, shutil
import numpy as np
import mujoco, mujoco.viewer
import torch

# Override via env: CHECKPOINT=path/to/ckpt python interact_so101.py
# Resolve to absolute path immediately — os.chdir later would break relative paths
_ckpt = os.environ.get("CHECKPOINT", "lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace")
CHECKPOINT = os.path.abspath(_ckpt) if os.path.exists(_ckpt) else _ckpt

CAM_CONFIGS = {
    "up":   {"pos": np.array([0.25, 0.1,  0.9]),  "lookat": np.array([0.25, 0.1,  0.0])},
    "side": {"pos": np.array([0.7,  -0.5, 0.4]),  "lookat": np.array([0.15, 0.05, 0.15])},
}
IMG_H, IMG_W = 480, 640

# ... (full source at courses/vla/ch04_vla/code/interact_so101.py)
# Key setup in main():
#   - copies scene_grip.xml into menagerie dir (box at reachable position)
#   - loads SmolVLAPolicy from CHECKPOINT
#   - loops: render → policy.select_action → mj_step → viewer.sync
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

**Suggested instructions to try:**
```
grip the green box
pink lego brick into the transparent box
pick up the block
do nothing
```

The first (`"grip the green box"`) is the same task used in Project C — try it here
zero-shot, then compare after finetuning in Project C to see the difference.

---

## Project B — Does Your Model Understand the Semantics of Instructions?

**Problem:** Your model might not produce perfect results yet — but does it at least understand
the *meaning* of instructions? A model that understands instruction semantics should generate
*similar actions for similar instructions* and *different actions for different ones*. That's a
meaningful sanity check you can run right now, before you ever worry about accuracy.

**Approach:** Feed the same image and robot state to the policy, swap only the instruction,
and compare the **action chunks** the policy produces. If language conditioning is working,
paraphrases of the trained task should produce similar action sequences (high cosine
similarity) while unrelated instructions should diverge (lower similarity). No simulation
needed — we use a synthetic image and zero state, which is enough to see the signal.

> 🟢 **Run** — load the policy, run inference per instruction, compare action chunks.

```python courses/vla/ch04_vla/code/probe_language.py
"""
Probe SmolVLA action conditioning — does swapping the instruction change the actions?

Feeds the same synthetic image and robot state to the policy with different instructions
and compares the resulting action chunks via cosine similarity.  Paraphrases of the
trained task should produce similar action sequences; unrelated instructions should diverge.

Usage:
    cd workspace/vla/ch04
    python probe_language.py
"""
import torch
import torch.nn.functional as F
from lerobot.policies.smolvla import SmolVLAPolicy
from lerobot.utils.constants import OBS_LANGUAGE_TOKENS, OBS_LANGUAGE_ATTENTION_MASK, OBS_STATE

CHECKPOINT = "lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace"

ANCHOR = "pink lego brick into the transparent box"
PAIRS = [
    ("same",        ANCHOR),
    ("paraphrase",  "place the pink block in the box"),
    ("paraphrase",  "pick up the lego and put it in the container"),
    ("unrelated",   "wave hello"),
    ("unrelated",   "open the drawer"),
    ("unrelated",   "move the arm to the left"),
]

GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
RESET  = "\033[0m"

def label_color(label):
    return {"same": GREEN, "paraphrase": YELLOW, "unrelated": RED}[label]

def similarity_bar(sim):
    filled = round(sim * 20)
    return "█" * filled + "░" * (20 - filled)

def get_action_vector(policy, tokenizer, cfg, instruction, img, device):
    enc = tokenizer(
        instruction + "\n",
        padding="max_length",
        max_length=cfg.tokenizer_max_length,
        return_tensors="pt",
        truncation=True,
    )
    batch = {}
    for key in list(cfg.image_features.keys()):
        batch[key] = img.clone().to(device)
    batch[OBS_STATE] = torch.zeros(1, cfg.robot_state_feature.shape[0],
                                   dtype=torch.float32, device=device)
    batch[OBS_LANGUAGE_TOKENS]         = enc["input_ids"].to(device)
    batch[OBS_LANGUAGE_ATTENTION_MASK] = enc["attention_mask"].bool().to(device)
    policy.reset()
    with torch.no_grad():
        chunk = policy.predict_action_chunk(batch)
    return F.normalize(chunk.reshape(1, -1), dim=-1)

if __name__ == "__main__":
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Loading {CHECKPOINT} on {device} ...")
    policy = SmolVLAPolicy.from_pretrained(CHECKPOINT).to(device)
    policy.eval()
    tokenizer = policy.model.vlm_with_expert.processor.tokenizer
    cfg = policy.config
    print("Policy ready.\n")

    torch.manual_seed(7)
    img = (torch.randn(1, 3, 480, 640) * 0.2 + 0.45).clamp(0, 1)

    cache = {}
    all_instrs = {ANCHOR} | {b for _, b in PAIRS}
    for instr in all_instrs:
        print(f"  running: {instr[:70]}")
        cache[instr] = get_action_vector(policy, tokenizer, cfg, instr, img, device)
    print()

    print(f"  {'':11s}  {'anchor':38s}  {'comparison':38s}  {'sim':>4}  bar")
    print("  " + "-" * 106)
    for label, b in PAIRS:
        sim = (cache[ANCHOR] * cache[b]).sum().item()
        pct = int(sim * 100)
        color = label_color(label)
        bar   = similarity_bar(sim)
        print(f"  {color}[{label:10s}]{RESET}  {ANCHOR[:36]:36s}  {b[:36]:36s}  {pct:3d}%  {color}{bar}{RESET}")
```

**Expected output** (tested on CPU, ~2–3 min — colors show green/yellow/red in terminal):

```
               anchor                                comparison                           sim  bar
  [same      ]  pink lego brick into the transparen  pink lego brick into the transparen  100%  ████████████████████
  [paraphrase]  pink lego brick into the transparen  place the pink block in the box       88%  █████████████████░░░
  [paraphrase]  pink lego brick into the transparen  pick up the lego and put it in the   97%  ███████████████████░
  [unrelated ]  pink lego brick into the transparen  wave hello                            67%  █████████████░░░░░░░
  [unrelated ]  pink lego brick into the transparen  open the drawer                       78%  ████████████████░░░░
  [unrelated ]  pink lego brick into the transparen  move the arm to the left              84%  █████████████████░░░
```

**What to observe:** Same instruction scores 100% (baseline). Paraphrases of the trained task
land at **88–97%** — the action chunk barely changes when you rephrase the same intent.
Unrelated instructions drop to **67–84%**. That gap is the action head responding to
instruction semantics: the model isn't just executing a fixed motion, it's conditioning on
what you asked it to do.

---

## Project C — Collect Sim Demos + Fine-tune

**The idea:** The zero-shot checkpoint fails in sim because it was trained on real robot
photos — MuJoCo renders synthetic images it has never seen. What if we collect 50 demos
*in sim* and fine-tune on those? The model already knows how SO-101 moves from real training
— we're just correcting the visual domain shift.

Task: `"grip the green box"` — arm reaches the box and closes the gripper. Simple enough
to script reliably, clear enough to show a before/after signal.

**Before vs after:**

<table><tr>
<td><img src="assets/before_after_grip.png" width="100%" alt="Left: zero-shot arm ignores box. Right: finetuned arm grips box."></td>
</tr></table>

*Left: zero-shot SmolVLA after 120 steps — arm collapses flat, nowhere near the box.
Right: finetuned on 50 sim demos (300 steps, ~10 min on MPS) — arm rises and positions
directly over the box. Same model, same weights except the action head.*

### Step 1 — Collect demos (~50s on Mac)

The modified scene XML (`assets/scene_grip.xml`) places the box at a position the arm can
reach. The script copies it into the menagerie directory automatically.

> 🟢 **Run** — collect 50 scripted grip episodes (~50 seconds, CPU only).

```python courses/vla/ch04_vla/code/collect_demos.py
"""
Collect scripted SO-101 grip demos in MuJoCo for SmolVLA finetuning.

A classical controller moves the arm to the green box and closes the gripper.
50 episodes → LeRobot dataset that lerobot-train can consume directly.

Usage:
    python courses/vla/ch04_vla/code/collect_demos.py

Output: workspace/vla/ch04/sim_grip_data/  (~100 MB, ~50s on Mac)
"""
import os, sys, math, shutil
import numpy as np
import mujoco
from lerobot.datasets.lerobot_dataset import LeRobotDataset

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT  = os.path.realpath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))
MENAGERIE  = os.path.join(REPO_ROOT, "workspace", "ext",
                           "mujoco_menagerie", "robotstudio_so101")
SCENE_XML  = os.path.join(SCRIPT_DIR, "..", "assets", "scene_grip.xml")
OUT_DIR    = os.path.join(REPO_ROOT, "workspace", "vla", "ch04", "sim_grip_data")

TASK, N_EPISODES, FPS, EP_STEPS = "grip the green box", 50, 30, 180
HOME       = np.zeros(6)
PICKUP_ARM = np.array([0.0, 0.000382, 0.473496, 1.17717, 1.58437, 0.0])
BOX_POS    = np.array([0.219, 0.024, 0.020])

# Copy scene XML into menagerie so MuJoCo can resolve so101.xml includes
shutil.copy(SCENE_XML, os.path.join(MENAGERIE, "scene_grip.xml"))
os.chdir(MENAGERIE)
m = mujoco.MjModel.from_xml_path("scene_grip.xml")
# ... (see full file for episode loop)
```

**Expected output:**
```
Collecting 50 episodes → workspace/vla/ch04/sim_grip_data
  10/50 episodes done
  20/50 episodes done
  ...
Done. 50 episodes, 9000 frames
```

### Step 2a — Fine-tune on Apple Silicon (~10 min)

> 🟢 **Run** — fine-tune the action head only, VLM frozen (~10 min on MPS).
>
> Run `warmup_mps.py` once first if you haven't already (see Apple Silicon section below).

```python courses/vla/ch04_vla/code/finetune_mps.py
"""
Finetune SmolVLA action head on sim grip demos — Apple Silicon (MPS).

Freezes the VLM backbone (448M params), trains only the action head (1.64M).
300 steps takes ~10 min on MPS after the one-time warmup (see warmup_mps.py).

Usage:
    python courses/vla/ch04_vla/code/finetune_mps.py

Output: workspace/vla/ch04/smolvla_sim_grip_ft/
"""
# ... loads policy, freezes VLM, trains action head 300 steps on MPS
```

**Expected output:**
```
Loading policy to MPS ...
Trainable params: 1.64M (action head only, VLM frozen)
Finetuning 300 steps on MPS ...
  step 1/300  loss=0.9947  step_time=1.7s  eta=12.8min
  step 2/300  loss=0.3461  step_time=1.0s  eta=11.2min
  step 50/300  loss=0.1045  step_time=1.2s  eta=8.4min
  step 150/300  loss=0.0439  step_time=0.9s  eta=4.8min
  step 300/300  loss=0.0534  step_time=1.0s  eta=0.0min

Done in 9.3min.
Loss: 0.2606 → 0.0524
Checkpoint: workspace/vla/ch04/smolvla_sim_grip_ft/
```

### Step 2b — Fine-tune on Colab T4 (~60 min, full 5000 steps)

For a more thorough finetune, upload `workspace/vla/ch04/sim_grip_data/` to Colab:

> 🟢 **Run** — fine-tune SmolVLA on your sim demos (~60 min on T4).

```bash courses/vla/ch04_vla/code/finetune_smolvla.sh
#!/usr/bin/env bash
# Fine-tune SmolVLA on sim grip demos collected by collect_demos.py.
# Hardware: CUDA GPU. Colab free T4 works with --batch_size=16.

set -euo pipefail
cd workspace/ext/lerobot

uv run --extra smolvla --extra training --extra dataset \
  lerobot-train \
    --policy.path=lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace \
    --dataset.repo_id=local/sim_grip \
    --dataset.root=sim_grip_data \
    --batch_size=16 \
    --steps=5000 \
    --policy.push_to_hub=false \
    --output_dir=outputs/smolvla_sim_grip_ft
```

### Step 3 — Compare before vs after

Run the sim twice — once with the original checkpoint, once with your finetuned one.

**Zero-shot (original checkpoint):**

```bash
CHECKPOINT=lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace \
  python workspace/vla/ch04/interact_so101.py
```

When prompted, type: `grip the green box`

**Finetuned (your checkpoint):**

```bash
CHECKPOINT=workspace/vla/ch04/smolvla_sim_grip_ft \
  python workspace/vla/ch04/interact_so101.py
```

When prompted, type: `grip the green box`

**What to observe:** Zero-shot — the arm collapses flat, going nowhere near the box. It has
never seen sim images, so the pretrained prior outputs near-zero actions for an unfamiliar
scene. Finetuned (300 steps, ~10 min) — the arm rises and positions directly over the box.
Same model, same 448M VLM — only the 1.64M action head changed.

This is the adaptation loop in miniature: **pretrained prior + domain-specific demos →
targeted behavior.** Ch5 runs the same loop on a real arm, where it actually matters.

---

## Self-Check

1. You run `interact_so101.py` and the arm barely moves for any instruction. What are two
   likely causes?
   **Answer:** (a) The sim images look so different from training (domain gap) that the model
   outputs near-zero actions. (b) `policy.reset()` is missing — stale temporal state from a
   previous run is leaking into the action chunk buffer.

2. In Project B, paraphrases of the trained task score 88–97% action similarity while
   unrelated instructions drop to 67–84%. What does that tell you, and what is the limitation
   of this test?
   **Answer:** The model's action head is responding to instruction meaning — the same intent
   rephrased produces nearly identical action chunks. The limitation: we used a synthetic
   noise image, not a real scene. The gap would likely be sharper on a real image because the
   model has more visual signal to condition on. It's a sanity check, not a full eval.

3. The checkpoint expects `observation.images.up` and `observation.images.side`. You pass
   `observation.image` instead. What happens?
   **Answer:** The policy raises a `KeyError` or `ValueError` — it can't find any of the
   expected camera keys. Key names are part of the model's interface contract.

4. Why do you call `policy.reset()` between instructions in `interact_so101.py`?
   **Answer:** SmolVLA uses action chunking — it buffers a sequence of predicted actions and
   replays them over several steps. `reset()` clears this buffer. Without it, the tail of the
   previous instruction's chunk bleeds into the next run.

5. You want to adapt SmolVLA to a completely new task on a different robot. How many demos
   do you need, roughly, and why less than ACT from scratch?
   **Answer:** 20–50 demos is a reasonable starting point. SmolVLA already has pretrained
   priors for robot motion, spatial reasoning, and language-action mapping from millions of
   demonstrations. Fine-tuning adapts those priors — ACT from scratch must learn everything
   from your demos alone.

---

## Common Mistakes

- **`python interact_so101.py` crashes with a display error on Mac:** MuJoCo's interactive
  viewer needs special window server access on macOS. Use `mjpython` instead of `python`:
  ```bash
  mjpython workspace/vla/ch04/interact_so101.py
  ```
  `mjpython` ships with the `mujoco` pip package. On Linux and Windows, plain `python` works fine.

- **Wrong camera key names:** `observation.image` will fail. The checkpoint expects exactly
  `observation.images.up` and `observation.images.side`. Check `policy.config.input_features`
  for the expected keys if you use a different checkpoint.

- **Expecting zero-shot to complete the task in sim:** It won't — the domain gap between
  synthetic MuJoCo renders and real robot photos is too large. The point of Project A is
  to understand the interface and observe motion, not to achieve task success.

- **Forgetting `policy.reset()` between episodes:** Stale action chunks from a previous
  run leak into the next. Always reset before a new episode or instruction.

- **Running fine-tuning on Apple Silicon (MPS):** The first time you move a 450M-parameter
  model to MPS, Metal compiles ~thousands of GPU shaders just-in-time. This takes 60–90 min
  on first run but caches permanently. See the Apple Silicon section below for how to handle
  this. CPU finetuning takes days — use Colab T4 if you don't want to wait for the MPS warmup.

- **Skipping `os.chdir` before loading the XML:** MuJoCo resolves STL asset paths relative
  to the XML file's directory. If the working directory is wrong, it raises errors about
  missing mesh files.

---

## Apple Silicon — Fine-tuning on MPS

> **One-time setup:** Run `warmup_mps.py` once (60–90 min). After that, 300-step finetune takes ~10 min.

### The problem: Metal compiles shaders on first use

PyTorch on Mac (MPS) doesn't pre-compile GPU code. Instead, it compiles shaders *the first time* each operation runs. SmolVLA has thousands of operations, so the first run takes 60–90 min. After that, the compiled shaders cache permanently.

**Good news:** The cache is saved at `~/Library/Caches/com.apple.metal/` — future runs skip compilation entirely.

**Bad news:** The cache is per-machine. Each Mac must warm up once.

### Timings (tested on 32 GB MPS Mac)

| What | Time |
|------|------|
| One-time warmup | 60–90 min (once) |
| Load model to MPS (after warmup) | ~15 sec |
| 300-step finetune, VLM frozen | **~10 min** (~1s/step) |
| 5000-step finetune | ~90 min |

### Why warmup is slow (~21s/step) but finetune is fast (~1s/step)

The warmup script runs the FULL 448M-parameter model. Even with `requires_grad=False`,
PyTorch still runs the forward pass — that's ~21s/step on MPS.

But `finetune_mps.py` (the actual finetune) automatically reduces the VLM to
16 layers on MPS to fit in memory. That's why 300 steps takes ~10 min (~1s/step),
not 105 min (~21s/step).

| What | Model size | Speed |
|------|-----------|-------|
| `warmup_mps.py` (one-time) | Full 448M | ~21s/step |
| `finetune_mps.py` (actual work) | 16 layers | ~1s/step |

**Bottom line:** For 5000-step finetunes, use Colab T4 (~0.5s/step). For quick 300-step experiments, MPS works fine.

### One-time warmup

Run this once and walk away:

```bash
mjpython courses/vla/ch04_vla/code/warmup_mps.py
```

Expected output (first run only):
```
Warmup complete in 67.3 min.
Subsequent MPS runs will be fast.
```
