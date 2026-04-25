# Chapter 3 — Imitation Learning

**Time:** 5–7 days
**Hardware:** GPU 8 GB+ strongly recommended (CPU is very slow for ACT/Diffusion training)
**Prerequisites:** Chapter 1 (MuJoCo), Chapter 2 (RL basics optional but helpful)

---

## What are we here for

RL requires millions of environment steps and carefully shaped rewards. For manipulation —
pick-and-place, folding, insertion — it's often faster and more reliable to just show the
robot what to do. That's **imitation learning (IL)**: learn a policy from human demonstrations.

This chapter focuses on two IL algorithms that currently dominate robot manipulation:

- **ACT** (Action Chunking with Transformers) — predicts a chunk of future actions at once,
  which reduces compounding errors from behavioral cloning
- **Diffusion Policy** — models the action distribution as a denoising process, which
  handles multi-modal behavior (multiple valid ways to do a task)

You'll collect demonstrations, train both algorithms, compare them, and study how data
quantity affects performance. These skills directly transfer to Chapter 7 (real hardware).

**Install:** (run from the repo root)
```bash
git clone https://github.com/huggingface/lerobot workspace/ext/lerobot
cd workspace/ext/lerobot
pip install -e ".[pusht]"
```

**Working directory:** Create `workspace/vla/ch03/` for your files — copy each code block
into a `.py` or `.sh` file there as you work through the projects.

**Skip if you can answer:**
1. What is distributional shift, and why does behavioral cloning fail because of it?
2. What problem does ACT's action chunking solve?
3. You trained on 50 demos and got 60% success. You collect 50 more. What do you expect?
4. Your policy succeeds in training conditions but fails when you move the camera 5 cm. Why?

---

## Projects

| # | Project | What you build |
|---|---------|---------------|
| A | Collect Demonstrations | 50 scripted oracle demos in gym_pusht using LeRobot |
| B | Inspect Your Dataset | Visualize trajectories, action distributions, and coverage |
| C | Train ACT | Train and evaluate ACT; measure success rate over 50 trials |
| D | Train Diffusion Policy | Train Diffusion Policy; compare head-to-head with ACT |
| E | Data Scaling | Train on 10/25/50/100/200 demos; plot success vs. data size |
| F | Failure Analysis | Cluster failures by type; fix the dominant failure mode |

---

## Project A — Collect Demonstrations

**Problem:** IL needs demonstrations. Before you can train, you need a dataset of
(observation, action) pairs showing the task being solved.

**Approach:** Use LeRobot's `gym_pusht` environment with a scripted oracle policy to
generate 50 demonstrations automatically, saved in LeRobot's dataset format.

### What is gym_pusht?

`gym_pusht` is a 2D push-T task: a disk (end-effector) must push a T-shaped block into
a target region. It's fast to simulate, visually clear, and widely used for IL benchmarks.

### LeRobot's dataset format

LeRobot stores demonstrations as a `LeRobotDataset` — a structured collection of episodes,
each containing observations (images + state) and actions at each timestep. This format
is what ACT and Diffusion Policy expect as input.

```python workspace/vla/ch03/collect_demos.py
"""Collect demonstrations in gym_pusht using a scripted oracle. Saves a LeRobotDataset."""
import numpy as np
from lerobot.datasets import LeRobotDataset
import gymnasium as gym
import gym_pusht

N_DEMOS    = 50
REPO_ID    = "local/pusht_demos"
SAVE_DIR   = "./data/pusht_demos"

def oracle_action(state: np.ndarray) -> np.ndarray:
    """Scripted policy: move toward block, then push toward goal.
    state = [agent_x, agent_y, block_x, block_y, block_angle] from env.unwrapped.
    """
    agent_pos  = state[:2]
    block_pos  = state[2:4]
    target_pos = np.array([256.0, 256.0])  # fixed goal center

    # Phase 1: approach block
    to_block = block_pos - agent_pos
    if np.linalg.norm(to_block) > 15:
        return np.clip(to_block * 0.05, -1, 1)

    # Phase 2: push block toward goal
    to_goal = target_pos - block_pos
    return np.clip(to_goal * 0.03, -1, 1)

def collect(n_demos: int, save_dir: str) -> None:
    # pixels_agent_pos gives {"pixels": HxWx3, "agent_pos": [x,y]} for the dataset.
    # Block position for the oracle comes from env.unwrapped body attributes.
    env = gym.make("gym_pusht/PushT-v0", obs_type="pixels_agent_pos", render_mode="rgb_array")

    dataset = LeRobotDataset.create(
        repo_id=REPO_ID,
        fps=10,
        root=save_dir,
        features={
            # Image shape is [C, H, W] — channels first
            "observation.image": {"shape": (3, 96, 96), "dtype": "image"},
            "observation.state": {"shape": (2,), "dtype": "float32"},
            "action": {"shape": (2,), "dtype": "float32"},
        },
    )

    TASK = "push the T block into the target area"

    for ep in range(n_demos):
        obs, _ = env.reset()
        done   = False
        frames = []
        while not done:
            # Build state vector for oracle from internal sim bodies (obs_type-independent)
            u = env.unwrapped
            state  = np.array([*u.agent.position, *u.block.position, u.block.angle % (2*np.pi)])
            action = oracle_action(state)
            frames.append((obs, action))
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

        for obs, action in frames:
            # "task" key is required by LeRobot — the language instruction for this episode
            dataset.add_frame({
                "observation.image": obs["pixels"].transpose(2, 0, 1),  # HWC → CHW
                "observation.state": obs["agent_pos"],
                "action": action,
                "task": TASK,
            })
        dataset.save_episode()
        if (ep + 1) % 10 == 0:
            print(f"Collected {ep+1}/{n_demos} demos")

    dataset.finalize()
    print(f"\nDataset saved to {save_dir}")
    print(f"Total episodes: {dataset.num_episodes}")
    print(f"Total frames:   {dataset.num_frames}")
    env.close()

if __name__ == "__main__":
    collect(N_DEMOS, SAVE_DIR)
```

**What to observe:** Watch the oracle push the T-block into place. Verify the dataset
has ~50 episodes. If success rate is low, the oracle needs tuning for your env version.

---

## Project B — Inspect Your Dataset

**Problem:** Training on bad data gives bad policies. Before training, understand what's
in your dataset: action distributions, trajectory diversity, and failure cases.

**Approach:** Load the dataset, plot action distributions and a sample of trajectories.

```python workspace/vla/ch03/inspect_dataset.py
"""Visualize a LeRobotDataset: action distributions, trajectory samples, coverage."""
import numpy as np
import matplotlib.pyplot as plt
from lerobot.datasets import LeRobotDataset

SAVE_DIR = "./data/pusht_demos"

def inspect(root: str) -> None:
    dataset = LeRobotDataset(repo_id="local/pusht_demos", root=root)
    print(f"Episodes: {dataset.num_episodes}  Frames: {dataset.num_frames}")
    print(f"Features: {list(dataset.features.keys())}")

    # Collect all actions
    actions = np.array([dataset[i]["action"].numpy() for i in range(len(dataset))])
    states  = np.array([dataset[i]["observation.state"].numpy() for i in range(len(dataset))])

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    # Action distribution
    axes[0].hist2d(actions[:, 0], actions[:, 1], bins=40)
    axes[0].set_title("Action distribution (x, y velocity)")
    axes[0].set_xlabel("action x"); axes[0].set_ylabel("action y")

    # State coverage
    axes[1].scatter(states[:, 0], states[:, 1], s=1, alpha=0.3)
    axes[1].set_title("Agent position coverage")
    axes[1].set_xlabel("x"); axes[1].set_ylabel("y")

    # Episode lengths
    ep_lengths = []
    for ep_idx in range(dataset.num_episodes):
        ep_data = dataset.episode_data_index
        start = ep_data["from"][ep_idx].item()
        end   = ep_data["to"][ep_idx].item()
        ep_lengths.append(end - start)
    axes[2].hist(ep_lengths, bins=20)
    axes[2].set_title("Episode length distribution")
    axes[2].set_xlabel("steps")

    plt.tight_layout()
    plt.savefig("dataset_inspection.png")
    print("Saved dataset_inspection.png")

    print(f"\nAction range:  x=[{actions[:,0].min():.2f}, {actions[:,0].max():.2f}]  "
          f"y=[{actions[:,1].min():.2f}, {actions[:,1].max():.2f}]")
    print(f"Median episode length: {np.median(ep_lengths):.0f} steps")

if __name__ == "__main__":
    inspect(SAVE_DIR)
```

**What to observe:** If actions cluster in a small region, your oracle isn't diverse.
If episode lengths vary wildly, some demos may have gotten stuck. Both hurt training.

---

## Project C — Train ACT

**Problem:** Train ACT on your demonstrations and measure how well it generalizes.

**Approach:** Use LeRobot's training script with the ACT config. Evaluate over 50 trials.

### What ACT does

**Behavioral cloning (BC)** trains a policy by supervised learning: given an observation,
predict the next action. The problem is **distributional shift** — at test time, small
errors accumulate and drive the robot into states it never saw during training.

**ACT** (Action Chunking with Transformers) addresses this by predicting a *chunk* of
future actions (e.g., 100 steps) at once, then executing them open-loop for a short
window before re-predicting. This reduces the number of policy queries, reducing
compounding errors. [Read more: ACT paper](https://arxiv.org/abs/2304.13705)

```bash workspace/vla/ch03/train_act.sh
# Train ACT on pusht demos (~30 min on GPU, several hours on CPU)
cd workspace/ext/lerobot
python lerobot/scripts/train.py \
  --policy.type=act \
  --dataset.repo_id=local/pusht_demos \
  --dataset.root=./data/pusht_demos \
  --training.num_workers=4 \
  --training.batch_size=64 \
  --training.steps=80000 \
  --output_dir=./outputs/act_pusht
```

```python workspace/vla/ch03/eval_policy.py
"""Evaluate a trained LeRobot policy over N trials. Reports success rate."""
import numpy as np
from lerobot.policies.act.modeling_act import ACTPolicy
import gymnasium as gym
import gym_pusht
import torch

def evaluate(policy_path: str, n_trials: int = 50) -> float:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    policy = ACTPolicy.from_pretrained(policy_path).to(device)
    policy.eval()

    env = gym.make("gym_pusht/PushT-v0", obs_type="pixels_agent_pos", render_mode=None)
    successes = 0

    for trial in range(n_trials):
        obs, _ = env.reset()
        done   = False
        while not done:
            with torch.no_grad():
                action = policy.select_action({
                    "observation.image": torch.tensor(obs["pixels"]).permute(2,0,1).unsqueeze(0).to(device) / 255.0,
                    "observation.state": torch.tensor(obs["agent_pos"]).unsqueeze(0).to(device),
                })
            obs, _, term, trunc, info = env.step(action.cpu().numpy()[0])
            done = term or trunc
        successes += int(info.get("is_success", False))

    env.close()
    sr = successes / n_trials
    print(f"Success rate: {sr:.0%} ({successes}/{n_trials})")
    return sr

if __name__ == "__main__":
    evaluate("./outputs/act_pusht")
```

**What to observe:** After 80k steps on 50 demos, expect 50–80% success. Lower means
the policy overfit or the demos are insufficient.

---

## Project D — Train Diffusion Policy and Compare

**Problem:** How does Diffusion Policy compare to ACT on the same data?

**Approach:** Train Diffusion Policy with the same dataset and eval protocol, then plot
both learning curves.

### What Diffusion Policy does

Diffusion Policy models the action distribution as a **denoising diffusion process**: it
learns to denoise random noise into valid actions, conditioned on the observation. This
handles **multi-modal** behavior naturally — situations where multiple actions are correct
(e.g., approach from left or right). BC and ACT collapse these modes; Diffusion Policy
captures them. [Read more: Diffusion Policy paper](https://arxiv.org/abs/2303.04137)

```bash workspace/vla/ch03/train_diffusion.sh
# Diffusion Policy trains slower than ACT — ~1–2 hrs on GPU for 80k steps
cd workspace/ext/lerobot
python lerobot/scripts/train.py \
  --policy.type=diffusion \
  --dataset.repo_id=local/pusht_demos \
  --dataset.root=./data/pusht_demos \
  --training.batch_size=64 \
  --training.steps=80000 \
  --output_dir=./outputs/diffusion_pusht
```

Then evaluate with `eval_policy.py` (same script, change policy path and import to
`DiffusionPolicy`). Compare success rates and training time — Diffusion Policy is slower
to train and slower to run inference, but often higher quality on multi-modal tasks.

---

## Project E — Data Scaling

**Problem:** How many demonstrations do you actually need? This tells you how much data
to collect for a real-robot task.

**Approach:** Train ACT on 10, 25, 50, 100, 200 demos from the same dataset. Plot success
rate vs. data size.

This project is a manual experiment loop — run training five times, record each result,
then plot. The script below handles the training calls and plotting; you fill in results
as they come in.

**Step 1 — create subsets of your dataset.** LeRobot's `--dataset.episodes` flag lets
you limit which episodes are used. Run this five times:

```bash workspace/vla/ch03/data_scaling.sh
cd workspace/ext/lerobot
for N in 10 25 50 100 200; do
  python lerobot/scripts/train.py \
    --policy.type=act \
    --dataset.repo_id=local/pusht_demos \
    --dataset.root=./data/pusht_demos \
    --dataset.episodes="[$(seq -s, 0 $((N-1)))]" \
    --training.batch_size=64 \
    --training.steps=80000 \
    --output_dir=./outputs/act_scale_${N}
  echo "Done: $N demos → ./outputs/act_scale_${N}"
done
```

**Step 2 — evaluate each checkpoint** with `eval_policy.py` from Project C and record
the success rates.

**Step 3 — plot:**

```python workspace/vla/ch03/data_scaling_plot.py
"""Plot ACT data scaling curve. Fill in results after running the training loop above."""
import os
import json
import matplotlib.pyplot as plt

# Fill in after running eval_policy.py on each checkpoint:
results = {
    10:  0.0,   # replace with eval result for act_scale_10
    25:  0.0,   # replace with eval result for act_scale_25
    50:  0.0,   # replace with eval result for act_scale_50
    100: 0.0,   # replace with eval result for act_scale_100
    200: 0.0,   # replace with eval result for act_scale_200
}

counts = sorted(results.keys())
rates  = [results[n] for n in counts]

plt.figure(figsize=(8, 5))
plt.plot(counts, rates, "o-")
plt.xlabel("Number of demonstrations")
plt.ylabel("Success rate")
plt.title("ACT: data scaling on PushT")
plt.xscale("log")
plt.grid(True)
out = os.path.join(os.path.dirname(__file__), "scaling_curve.png")
plt.savefig(out)
print(f"Saved {out}")
for n, r in zip(counts, rates):
    print(f"  {n:4d} demos → {r:.0%}")
```

**What to observe:** Typically success rate rises steeply from 10→50 demos, then
flattens. The knee of the curve tells you the minimum viable dataset size for this task.

---

## Project F — Failure Analysis

**Problem:** Your policy has a 70% success rate. The 30% failures are not random — they
cluster into a few failure modes. Fixing the dominant one is more efficient than collecting
more data indiscriminately.

**Approach:** Run 100 trials, record videos of failures, categorize them manually, then
collect targeted demos for the dominant failure mode and retrain.

```python workspace/vla/ch03/failure_analysis.py
"""Run N trials, save failure videos, print a categorization prompt."""
import numpy as np
import gymnasium as gym
import gym_pusht
import torch
from lerobot.policies.act.modeling_act import ACTPolicy

FAILURE_CATEGORIES = [
    "A: never reached block",
    "B: reached block but couldn't push",
    "C: pushed block but missed target",
    "D: timeout — too slow",
    "E: other",
]

def collect_failures(policy_path: str, n_trials: int = 100) -> dict:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    policy = ACTPolicy.from_pretrained(policy_path).to(device)
    policy.eval()
    env = gym.make("gym_pusht/PushT-v0", obs_type="pixels_agent_pos", render_mode="rgb_array")

    failures = []
    for trial in range(n_trials):
        obs, _ = env.reset()
        frames = [env.render()]
        done   = False
        while not done:
            with torch.no_grad():
                action = policy.select_action({
                    "observation.image": torch.tensor(obs["pixels"]).permute(2,0,1).unsqueeze(0).to(device) / 255.0,
                    "observation.state": torch.tensor(obs["agent_pos"]).unsqueeze(0).to(device),
                })
            obs, _, term, trunc, info = env.step(action.cpu().numpy()[0])
            frames.append(env.render())
            done = term or trunc
        if not info.get("is_success", False):
            failures.append({"trial": trial, "frames": frames})

    env.close()
    print(f"\n{len(failures)} failures out of {n_trials} trials.")
    print("\nWatch the failure videos and categorize each:")
    for cat in FAILURE_CATEGORIES:
        print(f"  {cat}")
    print("\nFix the dominant category first — collect 20-50 targeted demos for it.")
    return {"n_failures": len(failures), "n_trials": n_trials}

if __name__ == "__main__":
    collect_failures("./outputs/act_pusht")
```

**What to observe:** Most failures cluster into 1–2 categories. Targeted data collection
for those categories typically improves success rate more than doubling the random dataset.

---

## Self-Check

1. What is distributional shift, and why does it make behavioral cloning fail?
   **Answer:** BC trains on states from demonstrations. At test time, small errors move the
   robot to new states not in the training distribution — the policy was never trained on
   these, so it makes worse decisions, causing further drift. Compounding errors snowball.

2. What problem does ACT's action chunking solve?
   **Answer:** Querying the policy at every step compounds errors. Chunking predicts a
   block of future actions at once and executes them open-loop briefly — fewer policy
   queries means fewer opportunities for compounding.

3. When would you prefer Diffusion Policy over ACT?
   **Answer:** When the task has multi-modal behavior — multiple valid ways to solve it
   (e.g., approach from left or right). BC and ACT average over modes, producing
   invalid actions. Diffusion Policy captures the full distribution.

4. Your Diffusion Policy trains to low loss but gets 20% success at eval. What do you check?
   **Answer:** Check that eval conditions match training (obs normalization, image size,
   action scale). Also verify demo quality — if demonstrations are inconsistent, low loss
   doesn't mean good policy.

5. You collect 200 demos and success rate is 85%. You want 95%. What's the most efficient next step?
   **Answer:** Run failure analysis first. Identify the dominant failure mode and collect
   30–50 targeted demos for it. Random data collection has diminishing returns at this scale.

---

## Common Mistakes

- **Training without checking dataset first:** Always run Project B before training.
  Bad demo coverage causes policies that fail in easily-detectable ways.

- **Using CPU for ACT/Diffusion training:** Training time goes from hours to days.
  Use Colab (free A100) if you don't have a local GPU.

- **Evaluating in the same random seed as training:** Always reset with varied seeds.
  High success rate on a fixed seed can mask overfitting to initial conditions.

- **Treating all failures as equal:** 30% failure rate with 3 distinct failure modes is
  three separate problems. Fix the biggest one first.

---

## Resources

1. [ACT paper](https://arxiv.org/abs/2304.13705) — read abstract + Section 3 (action chunking)
2. [Diffusion Policy paper](https://arxiv.org/abs/2303.04137) — read abstract + Section 4
3. [LeRobot documentation](https://huggingface.co/docs/lerobot) — training scripts and dataset format
4. [gym_pusht](https://github.com/huggingface/gym_pusht) — the simulation environment used here
