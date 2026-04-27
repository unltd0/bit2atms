> **TODO: Review post Ch3 closure** — Ch3 was restructured (6 projects → 3; Data Scaling cut; Collect+Inspect merged; ACT+Diffusion merged into one project). Review Ch4 Project D (Data Efficiency comparison vs ACT from scratch) for redundancy or tightening.

# Chapter 4 — Vision-Language-Action Models

**Time:** 4–5 days
**Hardware:** GPU 16 GB+ for fine-tuning (Colab A100 works; inference runs on 8 GB)
**Prerequisites:** Chapter 3 (Imitation Learning, LeRobot)

---

## What are we here for

ACT and Diffusion Policy are trained per-task: collect demos, train, deploy. They have no
prior knowledge of the world. A **Vision-Language-Action (VLA) model** is different — it's
a large pretrained model that has seen millions of robot demonstrations across hundreds of
tasks and robots. You give it a language instruction and an image; it outputs robot actions.

The practical payoff: instead of collecting 200 demos and training from scratch, you can
fine-tune a pretrained VLA on 20–50 demos and get better generalization. This chapter uses
**SmolVLA** — a 450M-parameter VLA from HuggingFace that's small enough to fine-tune on a
single A100.

You'll run inference, probe how language conditioning works, fine-tune on a custom task,
and measure how many demos fine-tuning actually needs.

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
4. What is the Open X-Embodiment dataset and why does it matter for VLAs?

---

## Projects

| # | Project | What you build |
|---|---------|---------------|
| A | Run SmolVLA Inference | Load SmolVLA, run zero-shot on gym_pusht with language instructions |
| B | Probe Language Conditioning | Same environment, different phrasings — measure behavioral change |
| C | Fine-tune SmolVLA | Fine-tune on a custom task; compare zero-shot vs. fine-tuned success rate |
| D | Data Efficiency | How many demos does fine-tuning need vs. ACT from scratch? |

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
22 robot types across 50+ institutions.

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
                                     .unsqueeze(0).to(device) / 255.0,
                "observation.state": torch.tensor(obs["agent_pos"]).unsqueeze(0).to(device),
                "task": [instruction],
            })
        obs, _, terminated, truncated, info = env.step(action.cpu().numpy()[0])
        if terminated or truncated:
            return bool(info.get("is_success", False))
    return False

if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # Check the SmolVLA blog post for the current Hub model ID — it may differ from below
    policy = SmolVLAPolicy.from_pretrained("lerobot/smolvla_base").to(device)
    policy.eval()

    env = gym.make("gym_pusht/PushT-v0", obs_type="pixels_agent_pos", render_mode=None)

    for instruction in INSTRUCTIONS:
        successes = sum(run_episode(policy, env, instruction) for _ in range(10))
        print(f"'{instruction}':  {successes}/10 success")

    env.close()
```

**What to observe:** Zero-shot success rate is likely low on gym_pusht (SmolVLA wasn't
pretrained on this exact env). But the policy should produce *plausible* motions — it
understands "push" and "block." That's the value of pretraining.

---

## Project B — Probe Language Conditioning

**Problem:** Does the language instruction actually change the policy's behavior, or is it
just passed through and ignored?

**Approach:** Run the same environment with semantically different and similar instructions,
and measure whether the policy behavior (trajectory shape, success rate) changes.

```python workspace/vla/ch04/probe_language.py
"""Test how sensitive SmolVLA is to instruction phrasing."""
import numpy as np
import gymnasium as gym
import gym_pusht
import torch
from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy

# Groups: semantically equivalent phrasings vs. semantically different tasks
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

def eval_instruction(policy, env, instruction: str, n_trials: int = 10) -> float:
    successes = 0
    device = next(policy.parameters()).device
    for _ in range(n_trials):
        obs, _ = env.reset()
        for _ in range(200):
            with torch.no_grad():
                action = policy.select_action({
                    "observation.image": torch.tensor(obs["pixels"]).permute(2,0,1).unsqueeze(0).to(device) / 255.0,
                    "observation.state": torch.tensor(obs["agent_pos"]).unsqueeze(0).to(device),
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

**What to observe:** Paraphrases of the correct task should give similar success rates.
Completely wrong instructions should produce different (lower) success rates. If
they're all the same, the model is ignoring language — a sign it needs fine-tuning.

---

## Project C — Fine-tune SmolVLA

**Problem:** Zero-shot SmolVLA doesn't perform well on your specific task. Fine-tune it
on your demonstration data and measure the improvement.

**Approach:** Fine-tune SmolVLA using LeRobot's training script with your pusht demos from
Chapter 3. Compare zero-shot vs. fine-tuned success rate.

### Why fine-tuning works

Pretraining gives the model a strong prior about robot motion, spatial reasoning, and
language-action mapping. Fine-tuning adapts these representations to your specific task,
robot, and environment. With 50 demos you're teaching the *what* and *where*, not the
basic *how* — the pretraining already handles that.

```bash workspace/vla/ch04/finetune_smolvla.sh
cd workspace/ext/lerobot
# Fine-tuning 50 epochs on an A100 takes ~30–60 min depending on dataset size
python lerobot/scripts/train.py \
  --policy.type=smolvla \
  --policy.pretrained_model_name_or_path=lerobot/smolvla_base \
  --dataset.repo_id=local/pusht_demos \
  --dataset.root=./data/pusht_demos \
  --training.batch_size=32 \
  --training.steps=50000 \
  --output_dir=./outputs/smolvla_finetuned
```

Then evaluate with the same `run_episode()` function from Project A, pointing to your
fine-tuned checkpoint. Print zero-shot vs. fine-tuned side-by-side.

**What to observe:** Fine-tuned success rate should jump significantly over zero-shot,
even with only 50 demos. If it doesn't, check that your demo quality is high and that
the task language instruction matches what you used in training.

---

## Project D — Data Efficiency

**Problem:** Fine-tuning is faster than training from scratch — but by how much? And
how does the data scaling curve compare?

**Approach:** Train ACT from scratch and fine-tune SmolVLA on 10, 25, 50 demos each.
Plot both curves.

```python workspace/vla/ch04/data_efficiency.py
"""Compare data efficiency: ACT from scratch vs. SmolVLA fine-tuning."""
import json
import matplotlib.pyplot as plt

DEMO_COUNTS = [10, 25, 50]

# Fill these in from your experiments before running this script:
# act_results    — from Ch03 Project E: run train_and_eval(10), train_and_eval(25), train_and_eval(50)
# smolvla_results — from Project C: re-run finetune_smolvla.sh with --dataset.num_episodes=10/25/50
#                   then eval each checkpoint with run_episode()
act_results    = {10: 0.0, 25: 0.0, 50: 0.0}
smolvla_results = {10: 0.0, 25: 0.0, 50: 0.0}

def plot(act: dict, smolvla: dict) -> None:
    counts = sorted(act.keys())
    plt.plot(counts, [act[n] for n in counts], "o-", label="ACT (from scratch)")
    plt.plot(counts, [smolvla[n] for n in counts], "s-", label="SmolVLA (fine-tuned)")
    plt.xlabel("Number of demonstrations")
    plt.ylabel("Success rate")
    plt.title("Data efficiency: ACT vs. SmolVLA fine-tuning")
    plt.legend()
    plt.grid(True)
    plt.savefig("data_efficiency.png")
    print("Saved data_efficiency.png")

if __name__ == "__main__":
    plot(act_results, smolvla_results)
    for n in DEMO_COUNTS:
        delta = smolvla_results[n] - act_results[n]
        print(f"{n:3d} demos: ACT={act_results[n]:.0%}  SmolVLA={smolvla_results[n]:.0%}  Δ={delta:+.0%}")
```

**What to observe:** SmolVLA fine-tuning typically outperforms ACT from scratch at low
demo counts (10–25 demos). At 200+ demos, the gap narrows. This tells you when pretraining
is worth the overhead.

---

## Self-Check

1. What does a VLA take as input and produce as output?
   **Answer:** Input: one or more camera images + a natural language instruction string.
   Output: robot actions (joint positions or velocities) for the next timestep or chunk.

2. Why can fine-tuning a pretrained VLA outperform training ACT from scratch on the same demos?
   **Answer:** The pretrained model already understands robot motion, spatial relationships,
   and language-action mappings from millions of demonstrations. Fine-tuning adapts this
   prior to your task; training from scratch must learn everything from your small dataset.

3. Your fine-tuned SmolVLA succeeds on "pick up the red cube" but fails on "grab the red block."
   Why?
   **Answer:** Language conditioning is learned during fine-tuning. If you always used
   "pick up the red cube" in training, the model didn't learn to generalize the instruction.
   Use varied phrasings in demonstrations to get instruction robustness.

4. What is Open X-Embodiment and why does it matter?
   **Answer:** A dataset of ~1M robot demonstrations from 22 robot types and 50+
   institutions, curated for cross-embodiment training. It's the pretraining data that gives
   VLAs their strong priors — without it, SmolVLA would be just another small transformer.

5. Inference with SmolVLA is too slow for your 10 Hz control loop. What do you try?
   **Answer:** Use a smaller chunk size (predict fewer steps per call), use `torch.compile`
   or `float16` precision, or run the vision encoder at lower frequency than the action
   decoder (most VLA frameworks support this).

---

## Common Mistakes

- **Fine-tuning with inconsistent task instructions:** Use the same instruction phrasing
  in all your training demos, and use that exact phrasing at eval time.

- **Expecting zero-shot to work well on novel envs:** SmolVLA was trained on real robots
  and different sims. Zero-shot on gym_pusht will be mediocre — fine-tuning is expected.

- **Running fine-tuning on CPU:** This takes days. Use Colab A100 or a local GPU.

- **Comparing zero-shot and fine-tuned at different eval conditions:** Same environment,
  same instruction, same number of trials — otherwise the comparison is meaningless.

---

## Resources

1. [SmolVLA blog post](https://huggingface.co/blog/smolvla) — architecture overview and benchmark results
2. [OpenVLA paper](https://arxiv.org/abs/2406.09246) — the design decisions behind open-weight VLAs
3. [Open X-Embodiment paper](https://arxiv.org/abs/2310.08864) — the pretraining dataset
4. [π0 paper](https://arxiv.org/abs/2410.24164) — state-of-art VLA for dexterous manipulation (read for context)
