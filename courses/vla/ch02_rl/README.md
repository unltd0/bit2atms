# Chapter 2 — Reinforcement Learning

**Time:** 3–5 days
**Hardware:** GPU helpful (CPU works, training is slower)
**Prerequisites:** Chapter 1 (MuJoCo, FK, IK)

---

## What are we here for

You have a robot that can move. Now you want it to *learn* to reach a target without you
telling it exactly how. That's reinforcement learning: the agent tries things, gets rewards
when it does well, and gradually learns a **policy** — a function that maps observations
to actions.

RL is not always the right tool (Chapter 3 covers imitation learning, which is often
better for manipulation), but understanding it is essential. Reward shaping and HER are
techniques you'll reuse even when the primary algorithm is IL. And RL gives you intuition
for what "exploration" means, which matters when your IL policy fails.

This chapter uses Stable Baselines 3 and the `gymnasium-robotics` FetchReach environment —
a standard robotic reach task with sparse rewards. You'll explore it, train on it, ablate
reward designs, and implement curriculum learning.

**Install:**
```bash
pip install stable-baselines3[extra] gymnasium gymnasium-robotics
```

**Working directory:** Create `workspace/vla/ch02/` for your files — this folder is your
scratchpad and is gitignored. Copy each code block below into a `.py` file there as you
work through the projects.

**Skip if you can answer:**
1. What does `env.step(action)` return? What does each element mean?
2. What is the difference between sparse and dense rewards? When does each work?
3. What problem does HER solve, and how does it solve it?
4. Your SAC policy doesn't improve after 100k steps. What do you check first?

---

## Projects

| # | Project | What you build |
|---|---------|---------------|
| A | Explore the Environment | Understand obs/action spaces, visualize random rollouts before training |
| B | Train SAC with HER | Train a reaching policy; compare with and without HER |
| C | Reward Design Ablation | Measure how sparse vs. dense vs. HER rewards affect learning speed |
| D | Curriculum Learning | Stage training by distance; gate stages on success rate |

---

## Project A — Explore the Environment

**Problem:** Before training, you need to understand what the environment gives you —
observation shape, action range, reward structure. Blind training without this wastes time.

**Approach:** Load `FetchReach-v4`, run random rollouts, and print everything.

### RL concepts you need

An RL environment has a simple contract (the **Gymnasium interface**):

```python
obs, info  = env.reset()             # start a new episode, get first observation
obs, reward, terminated, truncated, info = env.step(action)  # take an action
```

- **observation:** what the agent sees (joint positions, goal position, etc.)
- **action:** what the agent does (joint velocities or torques)
- **reward:** scalar feedback — positive when doing well, zero or negative otherwise
- **terminated:** episode ended (goal reached or robot fell)
- **truncated:** episode hit the time limit

A **policy** is a function: `action = policy(observation)`. RL learns this function by
maximizing cumulative reward over an episode.

### The code

```python workspace/vla/ch02/explore_env.py
"""Explore FetchReach-v4 before training: spaces, rewards, and random rollouts."""
import numpy as np
import gymnasium as gym
import gymnasium_robotics

gym.register_envs(gymnasium_robotics)

def explore(env_id: str = "FetchReach-v4", n_episodes: int = 5) -> None:
    env = gym.make(env_id, render_mode=None)

    print(f"Observation space: {env.observation_space}")
    print(f"Action space:      {env.action_space}")
    print(f"  action low:  {env.action_space.low}")
    print(f"  action high: {env.action_space.high}")

    rewards_per_ep = []
    for ep in range(n_episodes):
        obs, _ = env.reset()
        ep_reward = 0.0
        for step in range(50):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            ep_reward += reward
            if terminated or truncated:
                break
        rewards_per_ep.append(ep_reward)
        print(f"Episode {ep+1}: total reward = {ep_reward:.1f}  "
              f"(success={info.get('is_success', False)})")

    print(f"\nMean reward over {n_episodes} random episodes: {np.mean(rewards_per_ep):.2f}")
    print("With random actions, success rate is ~0%. That's why we need RL.")

    obs, _ = env.reset()
    print(f"\nSample observation keys: {list(obs.keys())}")
    for k, v in obs.items():
        print(f"  {k}: shape={np.array(v).shape}  values={np.round(v, 3)}")

    env.close()

if __name__ == "__main__":
    explore()
```

**What to observe:** Sparse reward — almost every step gives -1. Success rate with random
actions is effectively 0. This tells you why HER (below) is critical.

---

## Project B — Train SAC with HER

**Problem:** FetchReach has sparse rewards — the agent only gets a non-negative reward
when it actually reaches the goal. With random exploration, this almost never happens,
so the agent never learns.

**Approach:** Train SAC (Soft Actor-Critic) with Hindsight Experience Replay (HER).
Then train without HER and compare the learning curves.

### SAC and why it works for robotics

**SAC** (Soft Actor-Critic) is an off-policy RL algorithm that:
- Learns from a replay buffer (efficient data reuse)
- Maximizes both reward *and* entropy (encourages exploration)
- Works well in continuous action spaces like robot joint control

**HER** (Hindsight Experience Replay) solves the sparse reward problem. Idea: even when
the agent fails to reach the goal, it *did* reach *somewhere*. Relabel those failed
trajectories as if that somewhere was the goal — suddenly you have dense learning signal.
[Read more: HER paper](https://arxiv.org/abs/1707.01495)

### The code

```python workspace/vla/ch02/train_sac_her.py
"""Train SAC with and without HER on FetchReach-v4. Save and plot learning curves."""
import numpy as np
import matplotlib.pyplot as plt
from stable_baselines3 import SAC, HerReplayBuffer
from stable_baselines3.common.callbacks import EvalCallback
import gymnasium as gym
import gymnasium_robotics

gym.register_envs(gymnasium_robotics)

TOTAL_STEPS = 200_000
ENV_ID      = "FetchReach-v4"

def make_env() -> gym.Env:
    return gym.make(ENV_ID)

def train(use_her: bool, save_path: str) -> list[float]:
    env      = make_env()
    eval_env = make_env()

    eval_cb = EvalCallback(
        eval_env,
        best_model_save_path=save_path,
        eval_freq=5000,
        n_eval_episodes=20,
        verbose=0,
    )

    if use_her:
        model = SAC(
            "MultiInputPolicy", env,
            replay_buffer_class=HerReplayBuffer,
            replay_buffer_kwargs={"n_sampled_goal": 4, "goal_selection_strategy": "future"},
            verbose=0,
        )
    else:
        model = SAC("MultiInputPolicy", env, verbose=0)

    model.learn(total_timesteps=TOTAL_STEPS, callback=eval_cb)
    model.save(f"{save_path}/final_model")
    env.close(); eval_env.close()

    # evaluations_results shape: (n_evals, n_eval_episodes) — mean across episodes per eval
    if hasattr(eval_cb, "evaluations_results"):
        return [float(np.mean(r)) for r in eval_cb.evaluations_results]
    return []

if __name__ == "__main__":
    # Each run is 200k steps — expect ~5 min on GPU, ~20–40 min on CPU
    print("Training SAC + HER...")
    train(use_her=True,  save_path="./models/sac_her")
    print("Training SAC (no HER)...")
    train(use_her=False, save_path="./models/sac_no_her")
    print("Done. Compare models/sac_her vs models/sac_no_her in TensorBoard:")
    print("  tensorboard --logdir ./models")
```

**No GPU?** Reduce `TOTAL_STEPS = 50_000` and expect lower final success rate.
For a free A100 GPU: open [Google Colab](https://colab.research.google.com), set runtime
to GPU, and paste the script there.

**What to observe:** SAC+HER typically reaches >90% success on FetchReach within 50k
steps. SAC without HER may never learn meaningful behavior. This gap is HER's contribution.

---

## Project C — Reward Design Ablation

**Problem:** You want to understand how reward shaping affects learning speed and final
performance — a skill critical for any custom robot task.

**Approach:** Train the same SAC agent on three reward variants and compare.

### Dense vs. sparse rewards

- **Sparse:** reward = 0 if goal reached, -1 otherwise. Clean, unbiased — but hard to learn.
- **Dense:** reward = −distance to goal. Always informative — but can teach the wrong behavior
  if the shaping conflicts with the true objective.
- **HER:** sparse reward + trajectory relabeling. Best of both: clean objective, dense signal.

```python workspace/vla/ch02/reward_ablation.py
"""Compare sparse, dense, and HER rewards on a 2D reach task."""
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import SAC, HerReplayBuffer
import matplotlib.pyplot as plt

class Reach2D(gym.Env):
    """Minimal 2D reach: agent moves a point to a random goal."""

    def __init__(self, reward_type: str = "sparse"):
        super().__init__()
        self.reward_type = reward_type
        self.observation_space = spaces.Dict({
            "observation": spaces.Box(-1, 1, (2,), np.float32),
            "desired_goal": spaces.Box(-1, 1, (2,), np.float32),
            "achieved_goal": spaces.Box(-1, 1, (2,), np.float32),
        })
        self.action_space = spaces.Box(-0.1, 0.1, (2,), np.float32)
        self.pos  = np.zeros(2, dtype=np.float32)
        self.goal = np.zeros(2, dtype=np.float32)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.pos  = self.np_random.uniform(-0.5, 0.5, 2).astype(np.float32)
        self.goal = self.np_random.uniform(-0.5, 0.5, 2).astype(np.float32)
        return self._obs(), {}

    def step(self, action):
        self.pos = np.clip(self.pos + action, -1, 1)
        dist = float(np.linalg.norm(self.pos - self.goal))
        success = dist < 0.05
        if self.reward_type == "dense":
            reward = -dist
        else:
            reward = 0.0 if success else -1.0
        return self._obs(), reward, success, False, {"is_success": success}

    def _obs(self):
        return {"observation": self.pos.copy(),
                "desired_goal": self.goal.copy(),
                "achieved_goal": self.pos.copy()}

    def compute_reward(self, achieved, desired, info):
        dist = np.linalg.norm(achieved - desired, axis=-1)
        if self.reward_type == "dense":
            return -dist
        return np.where(dist < 0.05, 0.0, -1.0).astype(np.float32)

def run(reward_type: str, use_her: bool, steps: int = 50_000) -> float:
    env = Reach2D(reward_type=reward_type)
    kwargs = {}
    if use_her:
        kwargs = {"replay_buffer_class": HerReplayBuffer,
                  "replay_buffer_kwargs": {"n_sampled_goal": 4,
                                           "goal_selection_strategy": "future"}}
    model = SAC("MultiInputPolicy", env, verbose=0, **kwargs)
    model.learn(steps)
    # Eval
    successes = 0
    for _ in range(100):
        obs, _ = env.reset()
        for _ in range(50):
            action, _ = model.predict(obs, deterministic=True)
            obs, _, term, trunc, info = env.step(action)
            if term or trunc:
                successes += info.get("is_success", False)
                break
    return successes / 100

if __name__ == "__main__":
    results = {
        "sparse":      run("sparse", use_her=False),
        "dense":       run("dense",  use_her=False),
        "sparse+HER":  run("sparse", use_her=True),
    }
    for name, sr in results.items():
        print(f"{name:15s}  success rate: {sr:.0%}")
```

**What to observe:** Dense reward and HER typically both outperform plain sparse, but via
different mechanisms. HER is usually the practical choice for manipulation.

---

## Project D — Curriculum Learning

**Problem:** Even with HER, very long-horizon or high-precision tasks are hard to learn
from scratch. Curriculum learning starts easy and increases difficulty as the agent succeeds.

**Approach:** Implement success-gated curriculum on the 2D reach task — start with targets
close to the agent, expand the range only when success rate crosses a threshold.

```python workspace/vla/ch02/curriculum.py
"""Success-gated curriculum: expand goal range as success rate improves."""
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import SAC, HerReplayBuffer
from stable_baselines3.common.callbacks import BaseCallback

class CurriculumReach(gym.Env):
    """2D reach with adjustable goal range."""

    def __init__(self):
        super().__init__()
        self.goal_range = 0.1   # start easy: goals close to start
        self.observation_space = spaces.Dict({
            "observation": spaces.Box(-1, 1, (2,), np.float32),
            "desired_goal": spaces.Box(-1, 1, (2,), np.float32),
            "achieved_goal": spaces.Box(-1, 1, (2,), np.float32),
        })
        self.action_space = spaces.Box(-0.1, 0.1, (2,), np.float32)
        self.pos  = np.zeros(2, dtype=np.float32)
        self.goal = np.zeros(2, dtype=np.float32)
        self.recent_successes: list[bool] = []

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.pos  = np.zeros(2, dtype=np.float32)
        offset    = self.np_random.uniform(-self.goal_range, self.goal_range, 2)
        self.goal = np.clip(offset.astype(np.float32), -1, 1)
        return self._obs(), {}

    def step(self, action):
        self.pos  = np.clip(self.pos + action, -1, 1)
        dist      = float(np.linalg.norm(self.pos - self.goal))
        success   = dist < 0.05
        self.recent_successes.append(success)
        if len(self.recent_successes) > 200:
            self.recent_successes.pop(0)
        return self._obs(), (0.0 if success else -1.0), success, False, {"is_success": success}

    def _obs(self):
        return {"observation": self.pos.copy(),
                "desired_goal": self.goal.copy(),
                "achieved_goal": self.pos.copy()}

    def compute_reward(self, achieved, desired, info):
        dist = np.linalg.norm(achieved - desired, axis=-1)
        return np.where(dist < 0.05, 0.0, -1.0).astype(np.float32)

    def success_rate(self) -> float:
        if not self.recent_successes:
            return 0.0
        return sum(self.recent_successes) / len(self.recent_successes)

class CurriculumCallback(BaseCallback):
    """Expand goal range when success rate > 80%."""
    def __init__(self, env: CurriculumReach, max_range: float = 0.8):
        super().__init__()
        self.env       = env
        self.max_range = max_range

    def _on_step(self) -> bool:
        if self.env.success_rate() > 0.8 and self.env.goal_range < self.max_range:
            self.env.goal_range = min(self.env.goal_range * 1.5, self.max_range)
            print(f"  [curriculum] goal range → {self.env.goal_range:.2f}")
        return True

if __name__ == "__main__":
    env = CurriculumReach()
    cb  = CurriculumCallback(env)
    model = SAC(
        "MultiInputPolicy", env, verbose=1,
        replay_buffer_class=HerReplayBuffer,
        replay_buffer_kwargs={"n_sampled_goal": 4, "goal_selection_strategy": "future"},
    )
    model.learn(total_timesteps=100_000, callback=cb)
    print(f"\nFinal goal range: {env.goal_range:.2f}")
```

**What to observe:** Goal range expands as the agent improves. Without curriculum, the
same agent on the hard task (full range) typically converges slower or not at all.

---

## Self-Check

1. What does `env.step(action)` return?
   **Answer:** A tuple of `(observation, reward, terminated, truncated, info)`. `terminated`
   means the episode ended naturally (goal reached, robot fell). `truncated` means the time
   limit was hit.

2. FetchReach uses sparse rewards. Why does this make learning hard?
   **Answer:** With random actions the agent almost never reaches the goal, so almost every
   step gives -1 and the agent receives no gradient signal about what's working.

3. How does HER generate extra learning signal without changing the environment?
   **Answer:** After each failed episode, HER relabels the trajectory — treating whatever
   position the agent actually reached as if it *were* the goal. This creates successful
   transitions from failed rollouts.

4. Your SAC agent trains for 500k steps but success rate stays at 5%. What do you check?
   **Answer:** Check reward scale (mean reward should be ~-1, not -100), verify obs
   normalization, check that the goal is included in the observation, and try adding HER
   if not already using it.

5. Why start curriculum with easy goals rather than the full task?
   **Answer:** With hard goals and sparse rewards, early exploration almost never succeeds.
   Easy goals guarantee early successes, giving the agent a gradient signal to build on
   before the task difficulty increases.

---

## Common Mistakes

- **Forgetting to register gymnasium-robotics:** Call `gym.register_envs(gymnasium_robotics)`
  before `gym.make()` or you'll get a `gym.error.NameNotFound`.

- **Using `obs` directly with HER in dict-obs envs:** SB3 HER requires `MultiInputPolicy`,
  not `MlpPolicy`. Dict observations need the multi-input policy.

- **Reward scale too large:** If your dense reward is `-distance * 100`, gradients explode.
  Keep rewards in the range [-1, 1] or normalize.

- **Evaluating during training with the training env:** Use a separate `eval_env` for
  `EvalCallback`. Evaluating in the training env can corrupt the replay buffer or stats.

---

## Resources

1. [Stable Baselines 3 docs](https://stable-baselines3.readthedocs.io/) — SAC and HER configuration
2. [HER paper](https://arxiv.org/abs/1707.01495) — read abstract + Section 3 (the algorithm)
3. [Gymnasium docs](https://gymnasium.farama.org/) — environment interface and wrappers
4. [gymnasium-robotics](https://robotics.farama.org/) — FetchReach and other robot envs
