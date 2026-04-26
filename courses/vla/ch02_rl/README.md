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

This chapter uses **Stable Baselines 3** (a library of ready-to-use RL algorithms — you
call `SAC(...)` and it handles all the math) and the `gymnasium-robotics` FetchReach
environment — a simulated robot arm whose only job is to move its hand to a target point.

You'll train a reaching policy, compare how different reward designs affect learning speed,
and implement curriculum learning (starting with easy goals, graduating to hard ones).

**Install:**
```bash
pip install "stable-baselines3[extra]" gymnasium gymnasium-robotics
```

**Working directory:** `workspace/vla/ch02/` — copy each code block into a `.py` file
there as you work through the projects.

**Skip if you can answer:**
1. What does `env.step(action)` return? What does each element mean?
2. What is the difference between sparse and dense rewards? When does each work?
3. Your SAC policy doesn't improve after 100k steps. What do you check first?

---

## Projects

| # | Project | What you build |
|---|---------|---------------|
| A | Train SAC with HER | Train a reaching policy; compare with and without HER |
| B | Reward Design Ablation | Measure how sparse vs. dense vs. HER rewards affect learning speed |
| C | Curriculum Learning | Stage training by distance; gate stages on success rate |

---

## Project A — Train SAC with HER

**Problem:** In RL, the agent takes random actions, gets rewards for doing the right thing, and trains a model to maximise those rewards — hoping it learns the correct behaviour. FetchReach-v4 is a MuJoCo sim of a [Fetch robot arm](https://robotics.farama.org/envs/fetch/reach/) whose only job is to move the gripper to a target point in space.

![Fetch robot reaching for a target](https://robotics.farama.org/_images/reach.gif)

*Fetch robot arm reaching for a randomly placed target — [gymnasium-robotics FetchReach-v4](https://robotics.farama.org/envs/fetch/reach/)*

The catch: it only gives reward when the gripper gets within 5 cm of the target — and **with truly random actions, that almost never happens**. The agent wanders forever without ever seeing a success.

**Approach:** Train SAC (Soft Actor-Critic) with Hindsight Experience Replay (HER), which
turns failed attempts into useful training signal. Then train without HER and compare.

### The Gym contract

FetchReach-v4 is a pre-built robot environment from [gymnasium-robotics](https://robotics.farama.org/). MuJoCo simulates the physics (same as Chapter 1), gymnasium-robotics defines the Fetch robot model and reward, and **Gymnasium** provides the standard RL contract every library speaks:

```python
obs, info = env.reset()                                       # start episode
obs, reward, terminated, truncated, info = env.step(action)  # take one step
```

- **obs** — `dict` with 3 keys: `observation` (10 robot state values), `desired_goal` (target x,y,z), `achieved_goal` (gripper x,y,z)
- **action** — 4 floats in [-1, 1]: gripper velocity in x, y, z + open/close (open/close unused in reach)
- **reward** — `0.0` if within 5 cm of target, `-1.0` otherwise — this is a *sparse* reward: the agent gets no signal about whether it's getting closer or farther, just pass/fail
- **terminated** — `True` when goal reached
- **truncated** — `True` when 50-step limit hit

**obs** is a snapshot of the environment at that moment — where the gripper is, where the target is, joint states. It's called an *observation* rather than *state* because the agent may not see everything (a real robot can't directly sense its own internal torques, for example).

The goal is to learn a **policy** — a function that maps what the robot sees to what it should do: `action = policy(obs)`. RL trains this by running many episodes and nudging the policy towards actions that led to more reward:

```python
action = policy(obs)                   # predict: what should I do given what I see?
obs, reward, done, _, _ = env.step(action)  # execute: apply action, get new obs + reward
model.learn(...)                       # improve: adjust policy to favour higher-reward actions
```

SAC and HER handle the `model.learn()` step — you don't implement it manually.

### SAC and HER

**SAC** (Soft Actor-Critic) is the go-to algorithm for continuous robot control — the policy outputs continuous numbers (e.g. move gripper 0.3 cm in x), not discrete choices (left/right/up), and SAC is built for that. It's stable, sample-efficient, and works out of the box with Stable Baselines 3. SAC has useful internals (replay buffer, entropy regularization, actor-critic architecture) that won't matter for this course — [read more here](https://spinningup.openai.com/en/latest/algorithms/sac.html) if curious.

**HER** (Hindsight Experience Replay) solves the sparse reward problem. Even when the agent
fails to reach the goal, it *did* reach *somewhere*. HER relabels those failed trajectories
as if that somewhere *was* the goal — suddenly you have useful learning signal from every
episode, not just the rare successes.
[Read more: HER paper](https://arxiv.org/abs/1707.01495)

### The code

```python workspace/vla/ch02/train_sac_her.py
"""Train SAC with and without HER on FetchReach-v4. Compare learning curves."""
import numpy as np
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
            "MultiInputPolicy", env,           # MultiInputPolicy handles dict observations
            replay_buffer_class=HerReplayBuffer,
            replay_buffer_kwargs={
                "n_sampled_goal": 4,           # relabel each transition with 4 fake goals
                "goal_selection_strategy": "future",  # pick goals from later in same episode
            },
            verbose=0,
        )
    else:
        model = SAC("MultiInputPolicy", env, verbose=0)

    model.learn(total_timesteps=TOTAL_STEPS, callback=eval_cb)
    model.save(f"{save_path}/final_model")
    env.close()
    eval_env.close()

    # evaluations_results: (n_evals, n_eval_episodes) — take mean per eval checkpoint
    if hasattr(eval_cb, "evaluations_results"):
        return [float(np.mean(r)) for r in eval_cb.evaluations_results]
    return []

if __name__ == "__main__":
    # Each run is 200k steps — expect ~5 min on GPU, ~20–40 min on CPU
    print("Training SAC + HER...")
    train(use_her=True,  save_path="./models/sac_her")
    print("Training SAC (no HER)...")
    train(use_her=False, save_path="./models/sac_no_her")
    print("Done. Inspect results:")
    print("  tensorboard --logdir ./models")
```

**No GPU?** Reduce `TOTAL_STEPS = 50_000` and expect lower final success rate.
For a free GPU: open [Google Colab](https://colab.research.google.com), set runtime to GPU,
and paste the script there.

**What to observe:** SAC+HER typically reaches >90% success on FetchReach within 50k steps.
SAC without HER may never learn. That gap is entirely HER's contribution.

---

## Project B — Reward Design Ablation

**Problem:** You want to understand how reward design affects learning speed — a skill
critical for any custom robot task.

**Approach:** Build a minimal 2D version of the reach task (easier to reason about than
FetchReach) and train SAC on three reward designs side-by-side.

### Two ways to give feedback

- **Sparse reward:** `0` when goal reached, `-1` every other step. Clean signal — but the
  agent rarely stumbles on success, so it rarely learns.
- **Dense reward:** `−distance` every step. Always informative — the agent always knows
  if it's getting closer. Can teach the wrong behavior if distance isn't a perfect proxy.
- **HER:** sparse reward + relabeling. Best of both: clean objective, dense effective signal.

```python workspace/vla/ch02/reward_ablation.py
"""Compare sparse, dense, and HER rewards on a 2D reach task."""
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import SAC, HerReplayBuffer

class Reach2D(gym.Env):
    """Minimal 2D reach: agent moves a point to a random goal."""

    def __init__(self, reward_type: str = "sparse"):
        super().__init__()
        self.reward_type = reward_type
        self.observation_space = spaces.Dict({
            "observation":   spaces.Box(-1, 1, (2,), np.float32),
            "desired_goal":  spaces.Box(-1, 1, (2,), np.float32),
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
        dist     = float(np.linalg.norm(self.pos - self.goal))
        success  = dist < 0.05
        reward   = -dist if self.reward_type == "dense" else (0.0 if success else -1.0)
        return self._obs(), reward, success, False, {"is_success": success}

    def _obs(self):
        return {"observation":   self.pos.copy(),
                "desired_goal":  self.goal.copy(),
                "achieved_goal": self.pos.copy()}

    def compute_reward(self, achieved, desired, info):
        dist = np.linalg.norm(achieved - desired, axis=-1)
        if self.reward_type == "dense":
            return -dist
        return np.where(dist < 0.05, 0.0, -1.0).astype(np.float32)

def run(reward_type: str, use_her: bool, steps: int = 50_000) -> float:
    env    = Reach2D(reward_type=reward_type)
    kwargs = {}
    if use_her:
        kwargs = {"replay_buffer_class": HerReplayBuffer,
                  "replay_buffer_kwargs": {"n_sampled_goal": 4,
                                           "goal_selection_strategy": "future"}}
    model = SAC("MultiInputPolicy", env, verbose=0, **kwargs)
    model.learn(steps)

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
        "sparse":     run("sparse", use_her=False),
        "dense":      run("dense",  use_her=False),
        "sparse+HER": run("sparse", use_her=True),
    }
    for name, sr in results.items():
        print(f"{name:15s}  success rate: {sr:.0%}")
```

**What to observe:** Dense and HER both outperform plain sparse, but via different
mechanisms. HER is usually the practical choice for manipulation.

---

## Project C — Curriculum Learning

**Problem:** Even with HER, high-precision or long-horizon tasks are hard to learn from
scratch. With random starting positions and hard goals, early exploration almost never
succeeds — no gradient signal, no learning.

**Approach:** Start with goals close to the agent. Expand the goal range only when success
rate crosses a threshold. The agent builds skill incrementally instead of drowning in failure.

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
        self.goal_range = 0.1  # start easy: goals within 0.1 units of origin
        self.observation_space = spaces.Dict({
            "observation":   spaces.Box(-1, 1, (2,), np.float32),
            "desired_goal":  spaces.Box(-1, 1, (2,), np.float32),
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
        self.pos = np.clip(self.pos + action, -1, 1)
        dist     = float(np.linalg.norm(self.pos - self.goal))
        success  = dist < 0.05
        self.recent_successes.append(success)
        if len(self.recent_successes) > 200:
            self.recent_successes.pop(0)
        return self._obs(), (0.0 if success else -1.0), success, False, {"is_success": success}

    def _obs(self):
        return {"observation":   self.pos.copy(),
                "desired_goal":  self.goal.copy(),
                "achieved_goal": self.pos.copy()}

    def compute_reward(self, achieved, desired, info):
        dist = np.linalg.norm(achieved - desired, axis=-1)
        return np.where(dist < 0.05, 0.0, -1.0).astype(np.float32)

    def success_rate(self) -> float:
        if not self.recent_successes:
            return 0.0
        return sum(self.recent_successes) / len(self.recent_successes)

class CurriculumCallback(BaseCallback):
    """Expand goal range by 1.5x whenever success rate exceeds 80%."""

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
    env   = CurriculumReach()
    cb    = CurriculumCallback(env)
    model = SAC(
        "MultiInputPolicy", env, verbose=1,
        replay_buffer_class=HerReplayBuffer,
        replay_buffer_kwargs={"n_sampled_goal": 4, "goal_selection_strategy": "future"},
    )
    model.learn(total_timesteps=100_000, callback=cb)
    print(f"\nFinal goal range: {env.goal_range:.2f}")
```

**What to observe:** Goal range expands as the agent improves. Without curriculum, the same
agent on the full range typically converges much slower or not at all.

---

## Self-Check

1. What does `env.step(action)` return?
   **Answer:** A tuple of `(observation, reward, terminated, truncated, info)`. `terminated`
   means the episode ended naturally (goal reached). `truncated` means the time limit was hit.

2. FetchReach uses sparse rewards. Why does this make learning hard?
   **Answer:** With random actions the agent almost never reaches the goal, so almost every
   step gives -1 and the agent receives no signal about what's working.

3. How does HER generate extra learning signal without changing the environment?
   **Answer:** After each failed episode, HER relabels the trajectory — treating whatever
   position the agent actually reached as if it *were* the goal. This creates successful
   transitions from failed rollouts.

4. Your SAC agent trains for 500k steps but success rate stays at 5%. What do you check?
   **Answer:** Check reward scale (mean reward should be ~-1, not -100), verify the goal
   is included in the observation, and try adding HER if not already using it.

5. Why start curriculum with easy goals rather than the full task?
   **Answer:** With hard goals and sparse rewards, early exploration almost never succeeds.
   Easy goals guarantee early successes, giving the agent a gradient signal to build on
   before difficulty increases.

---

## Common Mistakes

- **Forgetting to register gymnasium-robotics:** Call `gym.register_envs(gymnasium_robotics)`
  before `gym.make()` or you'll get `gym.error.NameNotFound`.

- **Using `MlpPolicy` with HER:** SB3 HER requires `MultiInputPolicy` for dict observations.
  `MlpPolicy` expects a flat array and will error.

- **Reward scale too large:** If your dense reward is `-distance * 100`, gradients explode.
  Keep rewards in [-1, 1].

- **Evaluating with the training env:** Use a separate `eval_env` for `EvalCallback`.
  Evaluating in the training env can corrupt replay buffer statistics.

---

## Resources

1. [Stable Baselines 3 docs](https://stable-baselines3.readthedocs.io/) — SAC and HER configuration
2. [HER paper](https://arxiv.org/abs/1707.01495) — read abstract + Section 3 (the algorithm)
3. [Gymnasium docs](https://gymnasium.farama.org/) — environment interface and wrappers
4. [gymnasium-robotics](https://robotics.farama.org/) — FetchReach and other robot envs
