# Chapter 3 — Imitation Learning

**Time:** 5–7 days
**Hardware:** GPU 8 GB+
**Prerequisites:** Chapter 1 (MuJoCo), Chapter 2 (RL basics)

---

## What are we here for

RL needs millions of environment steps and a carefully designed reward function. For manipulation — pick-and-place, insertion, folding — that's often impractical. A faster path: just show the robot what to do. That's **imitation learning (IL)**: train a policy directly from human (or scripted) demonstrations.

This chapter builds the core workflow you'll use in every chapter after this:

1. Collect demonstrations and store them in LeRobot's dataset format
2. Train a policy (ACT or Diffusion Policy) on that dataset
3. Evaluate it, watch it fail, and fix the dominant failure mode

That loop — collect, train, eval, debug — is exactly what Ch7 (real hardware) and Ch8 (capstone) run on a real SO-101 arm. The only difference there is that the demonstrations come from a human teleoperating the arm, not a scripted oracle.

Two algorithms dominate robot manipulation IL today:

- **ACT** (Action Chunking with Transformers) — predicts a chunk of future actions at once, reducing compounding errors from single-step behavioral cloning
- **Diffusion Policy** — models the action distribution as a denoising process, which handles multi-modal behavior (multiple valid ways to complete a task)

**Install:**
```bash
git clone https://github.com/huggingface/lerobot workspace/ext/lerobot
cd workspace/ext/lerobot
pip install -e ".[pusht]"
```

> CPU training is very slow for ACT and Diffusion Policy. Apple Silicon (M1/M2/M3) works via PyTorch MPS and is a reasonable option. For full speed, use a CUDA GPU or [Google Colab](https://colab.research.google.com) (free A100 tier).

**Working directory:** `workspace/vla/ch03/` — copy each code block into the corresponding file as you work through the projects.

**Skip if you can answer:**
1. What is distributional shift, and why does behavioral cloning fail because of it?
2. What problem does ACT's action chunking solve?
3. Your policy gets 60% success. You collect 50 more demos. What do you expect — and what would you do instead?
4. Your policy trains to low loss but achieves 20% success at eval. What do you check first?

---

## Projects

| # | Project | What you build |
|---|---------|---------------|
| A | Collect & Inspect Demonstrations | 50 oracle demos in gym_pusht; visualize dataset quality |
| B | Train ACT | Train ACT; establish success rate baseline |
| C | Failure Analysis | Categorize failures; collect targeted demos; retrain |

---

## Project A — Collect & Inspect Demonstrations

**Problem:** IL needs demonstrations. And training on bad demos gives bad policies — so you need to understand what's in your dataset before you commit to a long training run.

**Approach:** Use a scripted controller that reads exact simulator state (block position, angle) to collect 50 demos in `gym_pusht`, save them as a `LeRobotDataset`, then visualize the action distribution and trajectory coverage.

### What is gym_pusht?

`gym_pusht` is a 2D push-T task: a disk (the end-effector proxy) must push a T-shaped block into a target region. It's fast to simulate, visually clear, and widely used for IL benchmarks. The same LeRobot dataset format and training pipeline you use here works on real robot tasks in Ch7 — only the environment changes.

![PushT task — blue disk pushes gray T-block into the green target region](assets/pusht.gif)

### LeRobotDataset

LeRobot has a standard dataset format for storing robot demonstrations — each episode is a sequence of (observation, action) pairs, one per timestep, saved to disk with metadata. The Python class `LeRobotDataset` is the interface for creating, loading, and iterating over it. ACT, Diffusion Policy, and SmolVLA (Ch4) all consume this format directly — so you create the dataset once and reuse it across algorithms.

> 🟢 **Run** — glance the structure, then verify the printed episode and frame counts look right before moving on.

```python workspace/vla/ch03/collect_demos.py
"""Collect 50 oracle demonstrations in gym_pusht and save as a LeRobotDataset."""
import numpy as np
import gymnasium as gym
import gym_pusht
from lerobot.datasets import LeRobotDataset

N_DEMOS  = 50
REPO_ID  = "local/pusht_demos"
SAVE_DIR = "./data/pusht_demos"
TASK     = "push the T block into the target area"


def oracle_action(state: np.ndarray) -> np.ndarray:
    """Two-phase scripted policy: approach block, then push toward goal.
    state = [agent_x, agent_y, block_x, block_y, block_angle]
    """
    agent_pos  = state[:2]
    block_pos  = state[2:4]
    target_pos = np.array([256.0, 256.0])

    to_block = block_pos - agent_pos
    if np.linalg.norm(to_block) > 15:
        return np.clip(to_block * 0.05, -1, 1)

    to_goal = target_pos - block_pos
    return np.clip(to_goal * 0.03, -1, 1)


def collect(n_demos: int, save_dir: str) -> None:
    env = gym.make("gym_pusht/PushT-v0", obs_type="pixels_agent_pos", render_mode="rgb_array")

    dataset = LeRobotDataset.create(
        repo_id=REPO_ID,
        fps=10,
        root=save_dir,
        features={
            "observation.image": {"shape": (3, 96, 96), "dtype": "image"},  # CHW
            "observation.state": {"shape": (2,), "dtype": "float32"},
            "action":            {"shape": (2,), "dtype": "float32"},
        },
    )

    for ep in range(n_demos):
        obs, _ = env.reset()
        done   = False
        frames = []
        while not done:
            u     = env.unwrapped
            state = np.array([*u.agent.position, *u.block.position, u.block.angle % (2 * np.pi)])
            action = oracle_action(state)
            frames.append((obs, action))
            obs, _, terminated, truncated, _ = env.step(action)
            done = terminated or truncated

        for obs, action in frames:
            dataset.add_frame({
                "observation.image": obs["pixels"].transpose(2, 0, 1),  # HWC → CHW
                "observation.state": obs["agent_pos"],
                "action": action,
                "task":   TASK,
            })
        dataset.save_episode()
        if (ep + 1) % 10 == 0:
            print(f"Collected {ep + 1}/{n_demos} demos")

    dataset.finalize()
    env.close()
    print(f"\nSaved {save_dir}  |  episodes: {dataset.num_episodes}  frames: {dataset.num_frames}")


if __name__ == "__main__":
    collect(N_DEMOS, SAVE_DIR)
```

Now inspect what you collected. Bad demos — clustered actions, stuck episodes, low diversity — cause training to fail in ways that are hard to debug after the fact.

> 🟡 **Know** — read the plots before training. If actions cluster tightly or episode lengths spike, your oracle has a bug.

```python workspace/vla/ch03/inspect_dataset.py
"""Visualize a LeRobotDataset: action distribution, agent coverage, episode lengths."""
import numpy as np
import matplotlib.pyplot as plt
from lerobot.datasets import LeRobotDataset

SAVE_DIR = "./data/pusht_demos"


def inspect(root: str) -> None:
    dataset = LeRobotDataset(repo_id="local/pusht_demos", root=root)
    print(f"Episodes: {dataset.num_episodes}  |  Frames: {dataset.num_frames}")

    actions = np.array([dataset[i]["action"].numpy() for i in range(len(dataset))])
    states  = np.array([dataset[i]["observation.state"].numpy() for i in range(len(dataset))])
    ep_lengths = (
        dataset.hf_dataset.to_pandas()
        .groupby("episode_index").size().tolist()
    )

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    axes[0].hist2d(actions[:, 0], actions[:, 1], bins=40)
    axes[0].set_title("Action distribution (vx, vy)")

    axes[1].scatter(states[:, 0], states[:, 1], s=1, alpha=0.3)
    axes[1].set_title("Agent position coverage")

    axes[2].hist(ep_lengths, bins=20)
    axes[2].set_title("Episode length distribution")

    plt.tight_layout()
    plt.savefig("dataset_inspection.png")
    print("Saved dataset_inspection.png")
    print(f"Median episode length: {np.median(ep_lengths):.0f} steps")


if __name__ == "__main__":
    inspect(SAVE_DIR)
```

**What to look for:** Actions should spread across the 2D space, not cluster in one corner. Episode lengths should be roughly consistent — big outliers mean the oracle got stuck. Fix either issue before training.

---

## Project B — Train ACT

**Problem:** You have 50 demos. Now train a policy and see how well it actually works.

**Approach:** Train ACT to completion, evaluate it, and use the success rate as your baseline for Project C.

### What ACT does

**Behavioral cloning (BC)** predicts the next action given the current observation — supervised learning on demos. The problem: small prediction errors at test time push the robot into states it never saw in training, causing compounding drift (**distributional shift**).

**ACT** fixes this by predicting a *chunk* of future actions (e.g., 100 steps) at once, then executing them open-loop for a short window before re-predicting. Fewer policy queries = fewer opportunities for errors to compound. [ACT paper](https://arxiv.org/abs/2304.13705)

ACT is the algorithm you'll use again in Ch4 as the baseline against SmolVLA, and it's the default starting point for real tasks in Ch7. Learn it well here.

> The training scripts run from inside `workspace/ext/lerobot/`, so paths to your data and output use `../../vla/ch03/` to reach your workspace. Keep that in mind if you move files.

> 🟢 **Run** — takes ~30 min on GPU. Watch loss decrease steadily; plateau by 80k steps is expected.

```bash workspace/vla/ch03/train_act.sh
cd workspace/ext/lerobot
python lerobot/scripts/train.py \
  --policy.type=act \
  --dataset.repo_id=local/pusht_demos \
  --dataset.root=../../vla/ch03/data/pusht_demos \
  --training.batch_size=64 \
  --training.steps=80000 \
  --output_dir=../../vla/ch03/outputs/act_pusht
```

> 🔴 **Work** — run eval, record your success rate, and note where it fails. This number is your Project C baseline.

```python workspace/vla/ch03/eval_policy.py
"""Evaluate a trained LeRobot policy over N trials. Pass policy type and path as args."""
import sys
import torch
import numpy as np
import gymnasium as gym
import gym_pusht

POLICY_TYPE = sys.argv[1] if len(sys.argv) > 1 else "act"   # "act" or "diffusion"
POLICY_PATH = sys.argv[2] if len(sys.argv) > 2 else "./outputs/act_pusht"
N_TRIALS    = 50


def load_policy(policy_type: str, policy_path: str, device: str):
    if policy_type == "act":
        from lerobot.policies.act.modeling_act import ACTPolicy
        return ACTPolicy.from_pretrained(policy_path).to(device)
    elif policy_type == "diffusion":
        from lerobot.policies.diffusion.modeling_diffusion import DiffusionPolicy
        return DiffusionPolicy.from_pretrained(policy_path).to(device)
    else:
        raise ValueError(f"Unknown policy type: {policy_type}. Use 'act' or 'diffusion'.")


def evaluate(policy_type: str, policy_path: str, n_trials: int = 50) -> float:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    policy = load_policy(policy_type, policy_path, device)
    policy.eval()

    env = gym.make("gym_pusht/PushT-v0", obs_type="pixels_agent_pos", render_mode=None)
    successes = 0

    for trial in range(n_trials):
        obs, _ = env.reset()
        done   = False
        while not done:
            with torch.no_grad():
                action = policy.select_action({
                    "observation.image": torch.tensor(obs["pixels"]).permute(2, 0, 1).unsqueeze(0).to(device) / 255.0,
                    "observation.state": torch.tensor(obs["agent_pos"]).unsqueeze(0).to(device),
                })
            obs, _, term, trunc, info = env.step(action.cpu().numpy()[0])
            done = term or trunc
        successes += int(info.get("is_success", False))

    env.close()
    sr = successes / n_trials
    print(f"[{policy_type}] Success rate: {sr:.0%} ({successes}/{n_trials})")
    return sr


if __name__ == "__main__":
    evaluate(POLICY_TYPE, POLICY_PATH, N_TRIALS)
```

Run from `workspace/vla/ch03/`:
```bash
python eval_policy.py act ./outputs/act_pusht
```

**What to expect:** ACT typically reaches 50–80% on 50 demos in 80k steps. Below 40% — go back and check dataset quality (Project A).

### What about Diffusion Policy?

The other dominant IL algorithm is **Diffusion Policy** — it models the action distribution as a denoising process, which handles **multi-modal** tasks naturally. When there are multiple valid ways to solve something (approach from left or right), behavioral cloning averages the modes and produces invalid in-between actions. Diffusion Policy captures the full distribution. [Diffusion Policy paper](https://arxiv.org/abs/2303.04137)

It trains and runs slower than ACT. In this course, ACT is the practical default — it's what Ch4 and Ch7 build on. But if you hit a real task where the robot has several valid approach strategies and ACT keeps producing hesitant, averaged-out motions, that's the signal to reach for Diffusion Policy.

If you want to see it in action, the same training script works with `--policy.type=diffusion` and 20k steps is enough to compare:

```bash workspace/vla/ch03/train_diffusion.sh
cd workspace/ext/lerobot
python lerobot/scripts/train.py \
  --policy.type=diffusion \
  --dataset.repo_id=local/pusht_demos \
  --dataset.root=../../vla/ch03/data/pusht_demos \
  --training.batch_size=64 \
  --training.steps=20000 \
  --output_dir=../../vla/ch03/outputs/diffusion_pusht
```

Then run `eval_policy.py diffusion ./outputs/diffusion_pusht` to compare numbers. Don't let this detour you from Project C — it's optional.

More demos always help — but there are diminishing returns past ~100 for PushT. On a real task (Ch7), the knee of that curve is what tells you when to stop collecting and start debugging.

---

## Project C — Failure Analysis

**Problem:** Your policy has a 70% success rate. The 30% failures are not random — they cluster into a few categories. Fixing the dominant one is more efficient than collecting more data indiscriminately.

**Approach:** Run 100 trials, save failure frames, categorize failures manually, then collect targeted demos for the dominant failure mode and retrain.

This is the most transferable skill in this chapter. In Ch7 you'll run the exact same loop on the real arm.

> 🔴 **Work** — after running this, watch the saved failures and fill in your own category counts. Then collect 20–30 targeted demos for the top category and retrain.

```python workspace/vla/ch03/failure_analysis.py
"""Run N trials, save failure frames as PNGs, print categorization guide."""
import sys
import os
import torch
import numpy as np
import matplotlib.pyplot as plt
import gymnasium as gym
import gym_pusht

POLICY_TYPE = sys.argv[1] if len(sys.argv) > 1 else "act"
POLICY_PATH = sys.argv[2] if len(sys.argv) > 2 else "./outputs/act_pusht"
N_TRIALS    = 100
OUT_DIR     = "./failures"

FAILURE_CATEGORIES = [
    "A: never reached the block",
    "B: reached block but couldn't push it",
    "C: pushed block but missed the target region",
    "D: timeout — too slow",
    "E: other",
]


def load_policy(policy_type: str, policy_path: str, device: str):
    # Same helper as eval_policy.py
    if policy_type == "act":
        from lerobot.policies.act.modeling_act import ACTPolicy
        return ACTPolicy.from_pretrained(policy_path).to(device)
    elif policy_type == "diffusion":
        from lerobot.policies.diffusion.modeling_diffusion import DiffusionPolicy
        return DiffusionPolicy.from_pretrained(policy_path).to(device)
    else:
        raise ValueError(f"Unknown policy type: {policy_type}")


def analyze_failures(policy_type: str, policy_path: str, n_trials: int = 100) -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    policy = load_policy(policy_type, policy_path, device)
    policy.eval()

    env = gym.make("gym_pusht/PushT-v0", obs_type="pixels_agent_pos", render_mode="rgb_array")
    os.makedirs(OUT_DIR, exist_ok=True)

    n_failures = 0
    for trial in range(n_trials):
        obs, _ = env.reset()
        frames = [env.render()]
        done   = False
        while not done:
            with torch.no_grad():
                action = policy.select_action({
                    "observation.image": torch.tensor(obs["pixels"]).permute(2, 0, 1).unsqueeze(0).to(device) / 255.0,
                    "observation.state": torch.tensor(obs["agent_pos"]).unsqueeze(0).to(device),
                })
            obs, _, term, trunc, info = env.step(action.cpu().numpy()[0])
            frames.append(env.render())
            done = term or trunc

        if not info.get("is_success", False):
            # Save first, middle, last frame of the failure
            for label, frame in [("start", frames[0]), ("mid", frames[len(frames)//2]), ("end", frames[-1])]:
                plt.imsave(f"{OUT_DIR}/trial{trial:03d}_{label}.png", frame)
            n_failures += 1

    env.close()
    print(f"\n{n_failures} failures out of {n_trials} trials ({n_failures/n_trials:.0%} failure rate)")
    print(f"Failure frames saved to {OUT_DIR}/")
    print("\nWatch the saved frames and count failures by category:")
    for cat in FAILURE_CATEGORIES:
        print(f"  {cat}")
    print("\nFix the top category first — collect 20–30 targeted demos, retrain, re-eval.")


if __name__ == "__main__":
    analyze_failures(POLICY_TYPE, POLICY_PATH, N_TRIALS)
```

**What to observe:** Most failures cluster into 1–2 categories. Targeted demos for those categories typically improve success rate more than doubling the random dataset size. If you can't identify a pattern, your success rate is too low — go back and debug dataset quality first.

ACT and Diffusion Policy are task-specific: they have no language understanding and no prior knowledge of what "pick up" or "red ball" means. In Ch4 you'll add both by fine-tuning **SmolVLA** — same LeRobot dataset format, same eval loop, dramatically fewer demos needed.

---

## Self-Check

1. What is distributional shift, and why does it make behavioral cloning fail?
   **Answer:** BC trains only on states from demonstrations. Small errors at test time push the robot into unseen states — the policy makes worse decisions there, causing further drift. Errors compound.

2. What problem does ACT's action chunking solve?
   **Answer:** Querying the policy at every step compounds prediction errors. Chunking predicts a block of future actions at once and executes them open-loop briefly — fewer queries, fewer compounding steps.

3. When would you prefer Diffusion Policy over ACT?
   **Answer:** When the task has multi-modal behavior — multiple valid approaches (e.g., grasp from left or right). ACT averages over modes and produces invalid in-between actions. Diffusion Policy captures the full distribution.

4. Your policy trains to low loss but achieves 20% success at eval. What do you check first?
   **Answer:** Dataset quality — inconsistent demos mean low loss doesn't guarantee good behavior. Then check that eval conditions match training: obs normalization, image size, action scale.

5. You have 70% success rate and want 90%. What's more efficient — more random demos or failure analysis?
   **Answer:** Failure analysis. Identify the dominant failure mode and collect 20–30 targeted demos for it. Random data has diminishing returns at this scale.

---

## Common Mistakes

- **Skipping dataset inspection:** Always run `inspect_dataset.py` before training. Bad coverage causes failures that look mysterious but are obvious in the plots.

- **Using CPU for training:** Hours become days. Use Colab (free A100) if no local GPU.

- **Evaluating on a fixed random seed:** High success on one seed can mask overfitting to initial conditions. Always vary seeds across trials.

- **Treating all failures as equal:** 30% failure rate with 3 distinct modes is three separate problems. Fix the biggest one first.

- **Image normalization mismatch:** `eval_policy.py` divides pixels by 255.0 before `select_action()`. Some LeRobot versions apply normalization internally via dataset transforms — check if success rates look suspiciously low right out of training.

---

## Resources

1. [ACT paper](https://arxiv.org/abs/2304.13705) — read abstract + Section 3 (action chunking)
2. [Diffusion Policy paper](https://arxiv.org/abs/2303.04137) — read abstract + Section 4
3. [LeRobot documentation](https://huggingface.co/docs/lerobot) — training scripts and dataset format
4. [gym_pusht](https://github.com/huggingface/gym_pusht) — the simulation environment used here
