# Chapter 4 — Reinforcement Learning for Robots (Applied)

**Time:** 4–5 days
**Hardware:** Laptop; GPU optional but cuts training time 5–10×
**Prerequisites:** Chapters 1–3 (especially the Gymnasium env from Ch.2)

---

## Why This Chapter Exists

RL is not the dominant approach for robot manipulation in 2025 — imitation learning is. So why is this chapter here?

Because without having trained an RL agent yourself, you won't understand two things that keep mattering later: (1) why reward design is so hard and why IL sidesteps it, and (2) what a "policy" actually is — a function that maps observations to actions, trained to maximize some objective. Every chapter after this uses that concept.

The specific gap this fills: understanding why sparse rewards fail, what HER does to fix them, and when RL is genuinely the right tool (contact-rich dynamics, tasks without easy demonstrations). That judgment call comes up in Chapter 7 (sim-to-real) and Chapter 10 (capstone).

### If you can answer these, you can skip this chapter

1. You're training a robot to reach a target. Your reward is `+1` when it touches the target, `0` otherwise. Training doesn't converge after 500k steps. What's wrong, and what are two ways to fix it?
2. What does HER (Hindsight Experience Replay) do, and why does it help for sparse-reward manipulation tasks?
3. Why would you choose RL over imitation learning for a locomotion task but prefer imitation learning for a pick-and-place task?

**What you'll build:** Train a robot arm to reach, push, and eventually solve harder tasks using SAC with HER. You'll compare reward designs and see directly why bad rewards fail.

---

## Part 1 — Core RL Concepts (Applied, Not Theoretical)

### The Setup

At each timestep:
1. Robot is in state `s` (joint positions, velocities, object positions)
2. Policy outputs action `a` (joint torques or target positions)
3. Environment transitions to state `s'` and returns reward `r`
4. Policy updates to maximize cumulative reward

That's it. Everything else is implementation details.

### What You Control

As an applied roboticist, you control three things:

**1. Observation design** — what the robot sees
- Include: joint positions, velocities, object positions, target positions
- Normalize: always normalize observations to roughly [-1, 1]
- Don't include: raw RGB images (too complex for basic RL — use IL instead)

**2. Action design** — what the robot can do
- Absolute joint angles (position control) → easiest to learn
- Joint torques → more physical but harder to stabilize
- End-effector deltas → often best for manipulation

**3. Reward design** — what the robot is optimized for
- This is where 80% of the difficulty lives

### The Two Algorithms You Need

**SAC (Soft Actor-Critic):** Off-policy, sample efficient, handles continuous actions well. Standard choice for manipulation. Use this for everything in this chapter.

**PPO (Proximal Policy Optimization):** On-policy, more stable but needs more samples. Better for locomotion and multi-agent. Mention it here; you'll encounter it elsewhere.

Why SAC for manipulation:
- Works with replay buffer (sample efficient)
- Entropy regularization → explores well without needing curriculum tricks
- Handles continuous action spaces cleanly

---

## Part 2 — Reward Design (The Hard Part)

### Dense vs. Sparse Rewards

**Sparse:** reward = 1 if goal reached, 0 otherwise.
- Clean to define
- Extremely hard to learn (robot never stumbles onto the goal)
- Works only with HER (see below)

**Dense:** reward = -distance_to_goal (plus shaping terms)
- Robot gets signal everywhere, learns faster
- Risk: robot learns to game the reward, not solve the task

**Shaped example for reach task:**
```python
def compute_reward(ee_pos, target_pos, action):
    dist = np.linalg.norm(ee_pos - target_pos)
    reward = -dist                          # distance penalty
    reward -= 0.001 * np.sum(action**2)    # action regularization (smooth motion)
    if dist < 0.05:
        reward += 1.0                       # goal bonus
    return reward
```

### Common Reward Mistakes

**Mistake 1: Wrong scale.** If reward is -1000 (because you forgot to normalize), gradients explode.
Fix: mean reward across a random policy should be roughly -1 to 0.

**Mistake 2: Wrong horizon.** Reward accumulated over 500 steps with γ=0.99 discounts the last steps heavily.
Fix: for short-horizon tasks (reach), γ=0.95 is better than 0.99.

**Mistake 3: Reward hacking.** The robot finds a weird exploit — stays near the goal boundary to collect the bonus repeatedly.
Fix: add time penalty, or use terminal state detection.

**Mistake 4: Too sparse.** No learning signal — robot wanders randomly forever.
Fix: add shaped reward or use HER.

### Hindsight Experience Replay (HER) — The Key to Sparse Rewards

The core insight of HER (Andrychowicz et al., 2017):

After a failed episode (robot reached position X instead of goal G), relabel the experience as if X was the goal. The robot succeeded at reaching X — even though that wasn't the actual goal. Now you have a successful trajectory to learn from.

Over many episodes, HER creates a dense stream of success data from failed attempts.

**In practice:**
- HER only works with goal-conditioned environments (observation includes the goal)
- Stable Baselines 3 has HER built in as a wrapper
- Almost always use HER for manipulation with sparse rewards

---

## Part 3 — Stable Baselines 3 Quickstart

### Install

```bash
pip install stable-baselines3[extra] gymnasium-robotics
```

### Minimal SAC Training Loop

```python
from stable_baselines3 import SAC
from stable_baselines3.common.env_util import make_vec_env
import gymnasium as gym

env = gym.make("FetchReach-v4")
model = SAC("MlpPolicy", env, verbose=1, learning_rate=1e-3)
model.learn(total_timesteps=200_000)
model.save("sac_reach")
```

That's the entire training loop. SB3 handles replay buffer, network updates, entropy tuning, etc.

### With HER

```python
from stable_baselines3 import SAC
from stable_baselines3.her.her_replay_buffer import HerReplayBuffer
import gymnasium as gym

env = gym.make("FetchReach-v4")
model = SAC(
    "MultiInputPolicy",    # for dict observation spaces (obs + achieved_goal + desired_goal)
    env,
    replay_buffer_class=HerReplayBuffer,
    replay_buffer_kwargs=dict(
        n_sampled_goal=4,          # relabel 4 goals per transition
        goal_selection_strategy="future",  # use future states as relabeled goals
    ),
    verbose=1,
    learning_rate=1e-3,
    batch_size=256,
    gamma=0.95,
)
model.learn(total_timesteps=500_000)
```

### Evaluation

```python
from stable_baselines3.common.evaluation import evaluate_policy

mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=50)
print(f"Mean reward: {mean_reward:.2f} ± {std_reward:.2f}")
```

---

## External Resources

1. **Spinning Up in Deep RL (OpenAI)**
   Best applied intro to RL for robotics. Read "Introduction" and "Key Concepts".
   Skip the math proofs — focus on the intuition.
   → https://spinningup.openai.com/en/latest/spinningup/rl_intro.html

2. **Stable Baselines 3 Documentation**
   → https://stable-baselines3.readthedocs.io/en/master/
   Especially: SAC guide, HER guide, custom environments

3. **HER Paper (Hindsight Experience Replay)**
   Read abstract + intro + the "relabeling" section (Section 3).
   Understanding HER is more important than any algorithm.
   → https://arxiv.org/abs/1707.01495

4. **Gymnasium-Robotics Environments**
   FetchReach, FetchPush, FetchSlide — standard robot RL benchmarks.
   → https://robotics.farama.org/

5. **Reward Shaping Pitfalls (blog)**
   Practical guide to what goes wrong with rewards.
   Search "reward hacking examples RL" for concrete cautionary tales.

---

## Project 4A — Explore the Environment

Before training anything, understand what you're working with.

Create `learning/ch04_rl/01_explore_env.py`:

```python
import gymnasium as gym
import numpy as np

def explore_fetch_reach():
    env = gym.make("FetchReach-v4", render_mode="human")
    obs, info = env.reset()

    print("=== FetchReach-v4 Environment ===")
    print(f"\nObservation space: {env.observation_space}")
    print(f"\nObservation keys and shapes:")
    for key, val in obs.items():
        print(f"  {key}: shape={val.shape}  min={val.min():.3f}  max={val.max():.3f}")

    print(f"\nAction space: {env.action_space}")
    print(f"  Action = 4D delta: [dx, dy, dz, dgrasp]")
    print(f"  Range: {env.action_space.low} to {env.action_space.high}")

    print("\nRunning random policy for 5 episodes...")
    for episode in range(5):
        obs, _ = env.reset()
        total_reward = 0
        success = False
        for step in range(50):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            if info.get('is_success', False):
                success = True
                break
        goal = obs['desired_goal']
        achieved = obs['achieved_goal']
        dist = np.linalg.norm(goal - achieved)
        print(f"  Episode {episode+1}: reward={total_reward:.1f}  success={success}  "
              f"final_dist={dist*100:.1f}cm")

    env.close()
    print("\nKey insight: random policy almost never succeeds (sparse reward).")
    print("This is why we need HER.")

if __name__ == "__main__":
    explore_fetch_reach()
```

---

## Project 4B — Train SAC with HER on FetchReach

Create `learning/ch04_rl/02_train_sac_her.py`:

```python
import gymnasium as gym
import numpy as np
from stable_baselines3 import SAC
from stable_baselines3.her.her_replay_buffer import HerReplayBuffer
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback
from stable_baselines3.common.monitor import Monitor
import matplotlib.pyplot as plt
import os

def train_fetch_reach(total_steps=300_000, save_dir="./models"):
    os.makedirs(save_dir, exist_ok=True)

    # Training env
    env = Monitor(gym.make("FetchReach-v4"))
    # Eval env
    eval_env = Monitor(gym.make("FetchReach-v4"))

    model = SAC(
        "MultiInputPolicy",
        env,
        replay_buffer_class=HerReplayBuffer,
        replay_buffer_kwargs=dict(
            n_sampled_goal=4,
            goal_selection_strategy="future",
        ),
        verbose=1,
        learning_rate=1e-3,
        batch_size=256,
        gamma=0.95,
        tau=0.05,
        buffer_size=1_000_000,
        learning_starts=1000,
        tensorboard_log="./tb_logs/",
    )

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=save_dir,
        log_path=save_dir,
        eval_freq=10_000,
        n_eval_episodes=50,
        deterministic=True,
        verbose=1
    )

    print(f"Training SAC+HER for {total_steps:,} steps...")
    model.learn(total_timesteps=total_steps, callback=eval_callback, progress_bar=True)
    model.save(os.path.join(save_dir, "sac_her_reach_final"))

    env.close()
    eval_env.close()
    return model

def evaluate_and_render(model_path="./models/best_model"):
    env = gym.make("FetchReach-v4", render_mode="human")
    model = SAC.load(model_path)

    print("\nEvaluating trained policy (20 episodes)...")
    successes = 0
    for episode in range(20):
        obs, _ = env.reset()
        for step in range(50):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                break
        if info.get('is_success', False):
            successes += 1
            print(f"  Episode {episode+1}: SUCCESS")
        else:
            print(f"  Episode {episode+1}: failed")

    print(f"\nSuccess rate: {successes}/20 = {successes/20*100:.0f}%")
    env.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "eval":
        evaluate_and_render()
    else:
        train_fetch_reach()
        evaluate_and_render()
```

Run training:
```bash
python 02_train_sac_her.py
# After training:
python 02_train_sac_her.py eval
```

Expected: ~80–95% success rate after 300k steps.

---

## Project 4C — Reward Design Ablation

This is the most educational project. You'll train the same environment with 4 different reward designs and compare learning curves.

Create `learning/ch04_rl/03_reward_ablation.py`:

```python
import gymnasium as gym
import numpy as np
from gymnasium import spaces
from stable_baselines3 import SAC
from stable_baselines3.her.her_replay_buffer import HerReplayBuffer
from stable_baselines3.common.monitor import Monitor
import matplotlib.pyplot as plt

class FetchReachRewardWrapper(gym.Wrapper):
    """
    Wraps FetchReach to use a custom reward function.
    """
    def __init__(self, env, reward_mode="sparse"):
        super().__init__(env)
        self.reward_mode = reward_mode

    def step(self, action):
        obs, _, terminated, truncated, info = self.env.step(action)
        goal = obs['desired_goal']
        achieved = obs['achieved_goal']
        dist = np.linalg.norm(goal - achieved)
        success = dist < 0.05

        if self.reward_mode == "sparse":
            reward = 0.0 if success else -1.0

        elif self.reward_mode == "dense":
            reward = -dist  # negative distance always

        elif self.reward_mode == "dense_bonus":
            reward = -dist
            if success:
                reward += 5.0  # large success bonus

        elif self.reward_mode == "badly_shaped":
            # Common mistake: reward for moving, not for reaching goal
            reward = np.linalg.norm(action)  # bigger action = more reward (WRONG)

        info['is_success'] = success
        return obs, reward, terminated, truncated, info


def train_with_reward(reward_mode, total_steps=200_000):
    base_env = gym.make("FetchReach-v4")
    env = Monitor(FetchReachRewardWrapper(base_env, reward_mode=reward_mode))

    use_her = (reward_mode == "sparse")

    if use_her:
        model = SAC(
            "MultiInputPolicy", env,
            replay_buffer_class=HerReplayBuffer,
            replay_buffer_kwargs=dict(n_sampled_goal=4, goal_selection_strategy="future"),
            learning_rate=1e-3, batch_size=256, gamma=0.95, verbose=0
        )
    else:
        model = SAC("MultiInputPolicy", env, learning_rate=1e-3,
                    batch_size=256, gamma=0.95, verbose=0)

    model.learn(total_timesteps=total_steps, progress_bar=True)

    # Quick evaluation
    eval_env = FetchReachRewardWrapper(gym.make("FetchReach-v4"), reward_mode=reward_mode)
    successes = 0
    for _ in range(50):
        obs, _ = eval_env.reset()
        for _ in range(50):
            action, _ = model.predict(obs, deterministic=True)
            obs, _, terminated, truncated, info = eval_env.step(action)
            if terminated or truncated:
                break
        if info.get('is_success', False):
            successes += 1

    env.close()
    eval_env.close()
    return successes / 50

def run_ablation():
    modes = ["sparse", "dense", "dense_bonus", "badly_shaped"]
    results = {}

    print("Running reward design ablation (this takes ~30 min)...")
    for mode in modes:
        print(f"\nTraining with reward_mode='{mode}'...")
        sr = train_with_reward(mode)
        results[mode] = sr
        print(f"  Success rate: {sr*100:.0f}%")

    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['steelblue', 'green', 'orange', 'red']
    bars = ax.bar(modes, [results[m]*100 for m in modes], color=colors)

    for bar, mode in zip(bars, modes):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f"{results[mode]*100:.0f}%", ha='center', fontsize=12, fontweight='bold')

    ax.set_ylabel('Success Rate (%)', fontsize=12)
    ax.set_title('Reward Design Ablation: FetchReach\n'
                 '"badly_shaped" shows reward hacking; '
                 '"sparse+HER" and "dense" both work', fontsize=12)
    ax.set_ylim(0, 110)
    ax.grid(True, axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('reward_ablation.png', dpi=150)
    plt.show()

    print("\n=== Summary ===")
    for mode, sr in results.items():
        print(f"  {mode:20s}: {sr*100:.0f}% success")

if __name__ == "__main__":
    run_ablation()
```

**What you'll observe:**
- `badly_shaped` → robot moves a lot but never reaches the goal
- `sparse` without HER → barely learns
- `sparse` + HER → works well
- `dense` → works, and is often faster than HER
- `dense_bonus` → best of both worlds

---

## Project 4D — Curriculum Learning

Create `learning/ch04_rl/04_curriculum.py`:

```python
import gymnasium as gym
import numpy as np
from gymnasium import spaces
from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor

class CurriculumReachEnv(gym.Wrapper):
    """
    FetchReach with curriculum: start with close targets, gradually increase distance.
    """
    def __init__(self, env):
        super().__init__(env)
        self.stage = 0
        self.stage_distances = [0.05, 0.15, 0.30]  # max target distance per stage
        self.stage_names = ["easy (5cm)", "medium (15cm)", "hard (30cm)"]
        self.recent_successes = []
        self.advance_threshold = 0.75  # advance at 75% success rate
        self.window = 100

    @property
    def current_max_dist(self):
        return self.stage_distances[min(self.stage, len(self.stage_distances)-1)]

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        # Clamp the goal to be within current stage's max distance
        ee_pos = obs['observation'][:3]
        goal = obs['desired_goal']
        direction = goal - ee_pos
        dist = np.linalg.norm(direction)
        if dist > self.current_max_dist:
            direction = direction / dist * self.current_max_dist
            obs['desired_goal'] = ee_pos + direction
        return obs, info

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        success = info.get('is_success', False)
        self.recent_successes.append(float(success))
        if len(self.recent_successes) > self.window:
            self.recent_successes.pop(0)

        # Check stage advancement
        if (len(self.recent_successes) == self.window and
                np.mean(self.recent_successes) >= self.advance_threshold and
                self.stage < len(self.stage_distances) - 1):
            self.stage += 1
            self.recent_successes = []
            print(f"\n>>> CURRICULUM ADVANCE to stage {self.stage}: "
                  f"{self.stage_names[self.stage]} <<<")

        info['curriculum_stage'] = self.stage
        info['success_rate'] = np.mean(self.recent_successes) if self.recent_successes else 0
        return obs, reward, terminated, truncated, info


class CurriculumLogger(BaseCallback):
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.stages_over_time = []

    def _on_step(self):
        infos = self.locals.get('infos', [{}])
        stage = infos[0].get('curriculum_stage', 0)
        self.stages_over_time.append(stage)
        return True


def train_curriculum():
    base_env = gym.make("FetchReach-v4")
    env = Monitor(CurriculumReachEnv(base_env))

    from stable_baselines3.her.her_replay_buffer import HerReplayBuffer
    model = SAC(
        "MultiInputPolicy", env,
        replay_buffer_class=HerReplayBuffer,
        replay_buffer_kwargs=dict(n_sampled_goal=4, goal_selection_strategy="future"),
        learning_rate=1e-3, batch_size=256, gamma=0.95, verbose=1
    )

    logger = CurriculumLogger()
    print("Training with curriculum (easy → medium → hard)...")
    model.learn(total_timesteps=400_000, callback=logger, progress_bar=True)

    print(f"\nFinal curriculum stage reached: {max(logger.stages_over_time)}")
    import matplotlib.pyplot as plt
    plt.figure(figsize=(12, 4))
    plt.plot(logger.stages_over_time, alpha=0.7, color='steelblue')
    plt.xlabel('Training step')
    plt.ylabel('Curriculum stage (0=easy, 2=hard)')
    plt.title('Curriculum Progression Over Training')
    plt.grid(True, alpha=0.3)
    plt.yticks([0, 1, 2], ['Easy (5cm)', 'Medium (15cm)', 'Hard (30cm)'])
    plt.savefig('curriculum.png', dpi=150)
    plt.show()

if __name__ == "__main__":
    train_curriculum()
```

---

## Self-Check Questions

Before moving to Chapter 5:

1. SAC trains for 300k steps and the success rate is stuck at 5%. What are 3 things you check first?
2. You're using dense reward `-distance`. Training converges but the policy moves very jerkily. How do you fix it?
3. HER requires a "goal-conditioned" observation. What does that mean structurally?
4. You increase `gamma` from 0.95 to 0.999 for a 50-step episode. What changes in the learned behavior?
5. Why does off-policy SAC work here but not in environments with very long delays between action and reward?

**Answers:**
1. (a) Check reward scale — mean random-policy reward should be ~-1, not -1000. (b) Check observation normalization. (c) Add HER if reward is sparse.
2. Add action regularization: `reward -= 0.001 * np.sum(action**2)` to penalize large actions.
3. Observation is a dict with keys `observation`, `achieved_goal`, `desired_goal`. HER relabels by changing `desired_goal` to past `achieved_goal` values.
4. Higher gamma weights future rewards more → robot optimizes for longer-horizon success. For short episodes (50 steps), this can cause instability because discounting is weak → effectively infinite horizon.
5. SAC relies on rewards that correlate tightly with recent actions. Long delays break this assumption → Q-values become inaccurate.

---

## What You Should Skip in This Chapter

**RL theory / math derivations:** Bellman equations, policy gradient derivations, actor-critic proofs. Not needed. SB3 implements them correctly.

**Custom SAC implementation:** Don't write your own SAC. SB3's is better tested than anything you'll write in a week.

**Model-based RL (Dreamer, MBPO):** More sample efficient in theory, much harder to tune. Not standard in manipulation yet.

**Multi-agent RL:** Not needed until bimanual manipulation and even then, it's usually avoided.

---

## When To Use RL vs. Imitation Learning

| Situation | Prefer |
|-----------|--------|
| Can't easily demonstrate the task | RL |
| Need superhuman performance (speed/precision) | RL |
| Have human demonstration data | Imitation Learning |
| Short time to solution | Imitation Learning |
| Long-horizon, multi-step task | Imitation Learning |
| Novel environment not in training data | RL with DR |
| Need to transfer to real robot quickly | Imitation Learning |

Chapter 5 is where most real robot work actually happens.
