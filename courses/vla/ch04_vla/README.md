# Chapter 4 — Vision-Language-Action Models

**Time:** 3–4 days
**Hardware:** GPU required for fine-tuning (T4 16 GB works; inference runs on any GPU or CPU)
**Prerequisites:** Chapter 3 (Imitation Learning, LeRobot)

---

## What are we here for

ACT and Diffusion Policy are trained per-task: collect demos, train, deploy. They have no
prior knowledge of the world — no concept of "red ball" or "pick up." A **Vision-Language-Action (VLA) model** is different. It's a large pretrained model that has seen millions of robot demonstrations across hundreds of tasks and robots. You give it a language instruction and an image; it outputs robot actions.

The practical payoff: instead of collecting 200 demos and training from scratch, you can
fine-tune a pretrained VLA on 20–50 demos and get better generalization. This chapter uses
**SmolVLA** — a 450M-parameter VLA from HuggingFace that's small enough to fine-tune on a
single A100.

You'll run inference, probe how language conditioning works, and fine-tune on the same pusht
task from Ch3 to see the gap between zero-shot and fine-tuned.

**Hardware by project:**

| Project | What runs | Where |
|---------|-----------|-------|
| A — Inference | SmolVLA forward pass (450M params) | CPU or MPS works; slow but functional. CUDA recommended. |
| B — Language probe | Same as A, repeated across instructions | CPU or MPS works |
| C — Fine-tuning | Full backward pass, 50k steps | **CUDA required.** Colab free T4 (16 GB) works at batch_size=16. MPS and CPU will OOM or take days. |
| C — Eval | Inference only | CPU or MPS works |

**Install:** (inside the LeRobot repo)
```bash
cd workspace/ext/lerobot
pip install -e ".[smolvla,pusht]"
```

**Working directory:** Create `workspace/vla/ch04/` for your files.

**Skip if you can answer:**
1. What does a VLA take as input and produce as output?
2. Why fine-tune a pretrained VLA rather than train ACT from scratch on the same data?
3. You fine-tune SmolVLA on "pick up the red cube." It fails on "grab the red block." Why?

---

## Projects

| # | Project | What you build |
|---|---------|---------------|
| A | Run SmolVLA Inference | Load SmolVLA, run zero-shot on gym_pusht with language instructions |
| B | Probe Language Conditioning | Same environment, different phrasings — measure behavioral change |
| C | Fine-tune SmolVLA | Fine-tune on pusht demos; compare zero-shot vs. fine-tuned success rate |

---

## Project A — Run SmolVLA Inference

**Problem:** You need to understand what a VLA does before you can use or fine-tune one.
Running inference is the fastest way to build that intuition.

**Approach:** Load SmolVLA from HuggingFace Hub and run it in `gym_pusht` with a natural
language instruction. Observe what actions it generates and whether zero-shot works.

### What a VLA is

A VLA has three parts:
1. **Vision encoder** — extracts features from camera images (usually a ViT)
2. **Language encoder** — encodes the instruction string into a token sequence
3. **Action decoder** — takes combined vision+language features and outputs robot actions

SmolVLA is built on SmolVLM-256M (vision-language model) with an action decoder head.
It was pretrained on the Open X-Embodiment dataset — ~1M robot demonstrations from
22 robot types across 50+ institutions. That pretraining is why it can generalize: it has
seen thousands of "push object to target" tasks on real robots, even if it's never seen
gym_pusht specifically.

> 🟢 **Run** — load SmolVLA and check zero-shot success across three instruction phrasings.

```python workspace/vla/ch04/run_inference.py
"""Run SmolVLA zero-shot inference in gym_pusht. Observe action quality."""
import numpy as np
import gymnasium as gym
import gym_pusht
import torch
from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy

INSTRUCTIONS = [
    "push the T block into the target area",
    "move the block to the goal position",
    "push the object",
]

def run_episode(policy: SmolVLAPolicy, env: gym.Env,
                instruction: str, max_steps: int = 200) -> bool:
    obs, _ = env.reset()
    device = next(policy.parameters()).device

    for _ in range(max_steps):
        with torch.no_grad():
            action = policy.select_action({
                "observation.image": torch.tensor(obs["pixels"]).permute(2, 0, 1)
                                     .unsqueeze(0).float().to(device) / 255.0,
                "observation.state": torch.tensor(obs["agent_pos"]).unsqueeze(0).float().to(device),
                "task": [instruction],
            })
        obs, _, terminated, truncated, info = env.step(action.cpu().numpy()[0])
        if terminated or truncated:
            return bool(info.get("is_success", False))
    return False

if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    policy = SmolVLAPolicy.from_pretrained("lerobot/smolvla_base").to(device)
    policy.eval()

    env = gym.make("gym_pusht/PushT-v0", obs_type="pixels_agent_pos", render_mode=None)

    for instruction in INSTRUCTIONS:
        successes = sum(run_episode(policy, env, instruction) for _ in range(10))
        print(f"'{instruction}':  {successes}/10 success")

    env.close()
```

**What to observe:** Zero-shot success rate is likely low on gym_pusht — SmolVLA wasn't
pretrained on this exact env. But the policy should produce *plausible* motions — it
understands "push" and "block" from pretraining. That's what pretraining buys you: a
reasonable prior even on unseen environments. Fine-tuning closes the rest of the gap.

---

## Project B — Probe Language Conditioning

**Problem:** Does the language instruction actually change the policy's behavior, or is it
passed through and ignored?

**Approach:** Run the same environment with semantically different and similar instructions
and measure whether behavior changes. On gym_pusht zero-shot the differences may be subtle
— the model is already out of distribution. The point is to see *whether* language has any
effect before fine-tuning pins the connection.

> 🟡 **Know** — read the structure and instruction groups; run it and note which group shows the most variation.

```python workspace/vla/ch04/probe_language.py
"""Test how sensitive SmolVLA is to instruction phrasing."""
import gymnasium as gym
import gym_pusht
import torch
from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy

INSTRUCTION_GROUPS = {
    "correct task (paraphrases)": [
        "push the T block into the target area",
        "move the T-shaped block to the goal",
        "get the block to the highlighted region",
    ],
    "wrong task": [
        "pick up the block",
        "rotate the block 90 degrees",
        "do nothing",
    ],
    "ambiguous": [
        "go",
        "block",
        "target",
    ],
}

def eval_instruction(policy: SmolVLAPolicy, env: gym.Env,
                     instruction: str, n_trials: int = 10) -> float:
    successes = 0
    device = next(policy.parameters()).device
    for _ in range(n_trials):
        obs, _ = env.reset()
        for _ in range(200):
            with torch.no_grad():
                action = policy.select_action({
                    "observation.image": torch.tensor(obs["pixels"]).permute(2,0,1).unsqueeze(0).float().to(device) / 255.0,
                    "observation.state": torch.tensor(obs["agent_pos"]).unsqueeze(0).float().to(device),
                    "task": [instruction],
                })
            obs, _, term, trunc, info = env.step(action.cpu().numpy()[0])
            if term or trunc:
                successes += int(info.get("is_success", False))
                break
    return successes / n_trials

if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else "cpu"
    policy = SmolVLAPolicy.from_pretrained("lerobot/smolvla_base").to(device)
    policy.eval()
    env = gym.make("gym_pusht/PushT-v0", obs_type="pixels_agent_pos", render_mode=None)

    for group, instructions in INSTRUCTION_GROUPS.items():
        print(f"\n{group}:")
        for instr in instructions:
            sr = eval_instruction(policy, env, instr)
            print(f"  '{instr}': {sr:.0%}")

    env.close()
```

**What to observe:** If paraphrases of the correct task cluster together and wrong-task
instructions differ, language conditioning is working. If all groups give the same rate,
the model is ignoring language on this env — which is fine, it's out of distribution.
After fine-tuning (Project C), re-run this and compare: fine-tuning should sharpen the
language signal.

---

## Project C — Fine-tune SmolVLA

**Problem:** Zero-shot SmolVLA performs poorly on gym_pusht. Fine-tune it on the same
pusht demonstrations you used in Ch3 and measure the improvement.

**Approach:** Use LeRobot's training script to fine-tune SmolVLA on `lerobot/pusht`.
Then evaluate zero-shot vs. fine-tuned side-by-side.

### Why fine-tuning works

Pretraining gives the model a strong prior about robot motion, spatial reasoning, and
language-action mapping. Fine-tuning adapts these representations to your specific task,
robot, and environment. With the pusht dataset you're teaching the *what* and *where* for
this task — the basic *how* of pushing was already learned during pretraining.

SmolVLA inference uses ~2 GB VRAM — runs anywhere. Fine-tuning needs a CUDA GPU; Colab free T4 (16 GB) works with `--batch_size=16`. MPS and CPU will OOM.

> 🟢 **Run** — kick off fine-tuning; come back when it's done (~60–90 min on a T4).

```bash workspace/vla/ch04/finetune_smolvla.sh
cd workspace/ext/lerobot

lerobot-train \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id=lerobot/pusht \
  --batch_size=16 \
  --steps=50000 \
  --output_dir=outputs/smolvla_pusht
```

Now evaluate zero-shot vs. fine-tuned using the `run_episode()` function from Project A.
Point `from_pretrained` at your checkpoint:

> 🔴 **Work** — fill in your checkpoint path and run; interpret the gap.

Before the code: policy loads from a local checkpoint directory (the `pretrained_model`
subfolder inside your output dir). The loop runs 20 episodes for each variant and prints
success rate side by side.

```python workspace/vla/ch04/compare_zeroshot_finetuned.py
"""Compare zero-shot vs. fine-tuned SmolVLA on gym_pusht."""
import gymnasium as gym
import gym_pusht
import torch
from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
import pathlib

# Update this path to your actual checkpoint
FINETUNED_PATH = "workspace/vla/ch04/outputs/smolvla_pusht/checkpoints/050000/pretrained_model"

INSTRUCTION = "push the T block into the target area"
N_TRIALS = 20

def run_episode(policy: SmolVLAPolicy, env: gym.Env, instruction: str) -> bool:
    obs, _ = env.reset()
    device = next(policy.parameters()).device
    for _ in range(300):
        with torch.no_grad():
            action = policy.select_action({
                "observation.image": torch.tensor(obs["pixels"]).permute(2,0,1).unsqueeze(0).float().to(device) / 255.0,
                "observation.state": torch.tensor(obs["agent_pos"]).unsqueeze(0).float().to(device),
                "task": [instruction],
            })
        obs, _, term, trunc, info = env.step(action.cpu().numpy()[0])
        if term or trunc:
            return bool(info.get("is_success", False))
    return False

def eval_policy(policy: SmolVLAPolicy, env: gym.Env, label: str) -> None:
    successes = sum(run_episode(policy, env, INSTRUCTION) for _ in range(N_TRIALS))
    print(f"{label}: {successes}/{N_TRIALS} ({successes/N_TRIALS:.0%})")

if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else "cpu"
    env = gym.make("gym_pusht/PushT-v0", obs_type="pixels_agent_pos", render_mode=None)

    zeroshot = SmolVLAPolicy.from_pretrained("lerobot/smolvla_base").to(device)
    zeroshot.eval()
    eval_policy(zeroshot, env, "zero-shot")

    finetuned = SmolVLAPolicy.from_pretrained(
        str(pathlib.Path(FINETUNED_PATH).resolve())
    ).to(device)
    finetuned.eval()
    eval_policy(finetuned, env, "fine-tuned (50k steps)")

    env.close()
```

**What to observe:** Fine-tuned success rate should jump significantly over zero-shot —
even with 50k steps on a public dataset, the model learns the pusht task geometry. If it
doesn't improve, check that your `FINETUNED_PATH` points to a valid checkpoint and that
the instruction string exactly matches what the model saw during fine-tuning.

**On data efficiency:** SmolVLA fine-tuning outperforms ACT trained from scratch at low
demo counts (10–25 demos) because pretraining already handles the basic mechanics of pushing.
At 200+ demos the gap narrows — at that scale, ACT catches up. This is the practical rule:
use a VLA when you have few demos; ACT is competitive when you have many.

---

## Self-Check

1. You load SmolVLA zero-shot on gym_pusht and get 5% success. After fine-tuning on 206 pusht demos for 50k steps you get 60%. What explains the gap?
   **Answer:** Zero-shot SmolVLA has never seen this specific environment or task geometry. Fine-tuning adapts the pretrained priors to the exact observation space, action scale, and task. The pretrained model already knows how to "push" — fine-tuning teaches it *where* and *how far* in this env.

2. In Project B, all three instruction groups give the same success rate. What does that tell you?
   **Answer:** The model is ignoring language on this env — it's out of distribution and falling back on visual patterns alone. After fine-tuning, re-running the probe should show language starting to matter: correct-task phrasings should outperform wrong-task ones.

3. You fine-tune SmolVLA on "push the T block into the target area." At eval you pass "move block to goal." What do you expect?
   **Answer:** Likely degraded performance. Language conditioning is learned from the fine-tuning data. If only one phrasing appeared in training, the model didn't learn to generalize the instruction. Use varied phrasings in fine-tuning data or stick to the exact training phrasing at eval.

4. The fine-tune script uses `lerobot/pusht` — the same dataset as Ch3 ACT training. Why does SmolVLA fine-tune faster (fewer steps) than ACT trained from scratch?
   **Answer:** SmolVLA already has pretrained weights from millions of robot demonstrations. It's adapting an existing prior, not learning robot motion from zero. ACT from scratch has to learn everything from the 206 pusht episodes alone.

5. Your fine-tuned SmolVLA runs at 2 Hz — too slow for a 10 Hz control loop. What do you try first?
   **Answer:** Switch to `float16` precision (`policy.half()` or `torch.autocast`). Then check if the vision encoder is re-running every step — caching it at lower frequency (e.g., 5 Hz) while running the action decoder at 10 Hz is a common optimization in VLA deployments.

---

## Common Mistakes

- **Mismatched instruction at eval:** The phrasing you pass at eval must match (or be close to) what appeared in fine-tuning. If fine-tuning used "push the T block into the target area" and eval uses "move block," performance drops.

- **Expecting zero-shot to work well on novel envs:** SmolVLA was trained on real robots and different sims. Zero-shot on gym_pusht will be mediocre — fine-tuning is the expected workflow, not an optional step.

- **Running fine-tuning on CPU or MPS:** SmolVLA fine-tuning requires CUDA — MPS will OOM, CPU will take days. Use Colab (free T4) with `--batch_size=16` if you don't have a local GPU.

- **Comparing zero-shot and fine-tuned at different eval conditions:** Same environment, same instruction string, same number of trials — otherwise the comparison is meaningless.

---

## Resources

1. [SmolVLA blog post](https://huggingface.co/blog/smolvla) — architecture overview and benchmark results; check here for the current Hub model ID
2. [OpenVLA paper](https://arxiv.org/abs/2406.09246) — the design decisions behind open-weight VLAs
3. [Open X-Embodiment paper](https://arxiv.org/abs/2310.08864) — the pretraining dataset that gives SmolVLA its priors
4. [π0 paper](https://arxiv.org/abs/2410.24164) — state-of-art VLA for dexterous manipulation (read for context on where the field is going)
