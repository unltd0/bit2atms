# Chapter 2 — Reinforcement Learning

**Time:** 3–5 days
**Hardware:** GPU helpful (CPU works, training is slower)
**Prerequisites:** Chapter 1 (MuJoCo, FK, IK)

---

## What are we here for

You have a robot that can move. Now you want it to *learn* to reach a target without you
telling it exactly how. That's reinforcement learning: the agent tries things, gets rewards
when it does well, and gradually learns a **policy** — a function that maps what it sees
to what it should do.

RL is not always the right tool (Chapter 3 covers imitation learning, which is often
better for manipulation), but understanding it is essential. Reward shaping and HER (both
explained below) are techniques you'll reuse even when the primary algorithm is imitation
learning. And RL gives you intuition for what "exploration" means, which matters when your
policy fails.

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
| A | Train SAC with HER | Train a reaching policy and see it succeed |
| B | Reward Design Ablation | Measure how sparse vs. dense vs. HER rewards affect learning speed |
| C | Curriculum Learning | Stage training by distance; gate stages on success rate |

---

## Project A — Train SAC with HER

**Problem:** In RL, the agent takes random actions, gets rewards for doing the right thing, and trains a model to maximise those rewards — hoping it learns the correct behaviour. FetchReach-v4 is a MuJoCo sim of a [Fetch robot arm](https://robotics.farama.org/envs/fetch/reach/) whose only job is to move the gripper to a target point in space.

![Fetch robot reaching for a target](https://robotics.farama.org/_images/reach.gif)

*Fetch robot arm reaching for a randomly placed target — [gymnasium-robotics FetchReach-v4](https://robotics.farama.org/envs/fetch/reach/)*

The catch: it only gives reward when the gripper gets within 5 cm of the target — and **with truly random actions, that almost never happens**. The agent wanders forever without ever seeing a success.

**Approach:** Train SAC+HER on FetchReach. After training, the agent should reach the target >90% of the time.

### How the environment works

FetchReach-v4 is a pre-built robot environment from [gymnasium-robotics](https://robotics.farama.org/). MuJoCo simulates the physics (same as Chapter 1), gymnasium-robotics defines the Fetch robot model and reward, and **Gymnasium** provides the standard RL contract every library speaks:

```python
obs, info = env.reset()                                       # start episode
obs, reward, terminated, truncated, info = env.step(action)  # take one step
```

- **obs** — a snapshot of the environment: where the gripper is, where the target is, joint states. A `dict` with 3 keys: `observation` (10 robot state values), `desired_goal` (target x,y,z), `achieved_goal` (current gripper x,y,z). Called an *observation* rather than *state* because on a real robot you can't sense everything directly (e.g. internal joint torques).
- **action** — 4 floats in [-1, 1]: gripper velocity in x, y, z + open/close (open/close unused in reach)
- **reward** — `0.0` if within 5 cm of target, `-1.0` otherwise. This is *sparse*: no signal about whether the gripper is getting closer or farther, just pass/fail.
- **terminated** — `True` when goal reached
- **truncated** — `True` when 50-step limit hit

The goal is to learn a **policy**: `action = policy(obs)`. RL trains this by running episodes, collecting (obs, action, reward) tuples, and nudging the policy towards actions that led to more reward.

### SAC and HER

**SAC** (Soft Actor-Critic) is the go-to algorithm for continuous robot control — the policy outputs continuous numbers (e.g. move gripper 0.3 cm in x), not discrete choices (left/right/up), and SAC is built for that. It's stable, sample-efficient, and works out of the box with Stable Baselines 3. SAC has useful internals (replay buffer, entropy regularization, actor-critic architecture) that won't matter for this course — [read more here](https://spinningup.openai.com/en/latest/algorithms/sac.html) if curious.

**HER** (Hindsight Experience Replay) solves the sparse reward problem. Even when the agent fails to reach the goal, it *did* reach *somewhere*. HER relabels those failed trajectories as if that somewhere *was* the goal — suddenly you have useful learning signal from every episode, not just the rare successes. [Read more: HER paper](https://arxiv.org/abs/1707.01495)

### The code

Train SAC+HER on FetchReach for 200k steps. `EvalCallback` prints success rate every 5k steps so you can watch it improve — expect it to climb from ~0% to >90%. Models are saved to `./models/sac_her/`.

```python workspace/vla/ch02/train_sac_her.py
"""Train SAC+HER on FetchReach-v4 and report success rate."""
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

def train(save_path: str) -> None:
    env      = make_env()
    eval_env = make_env()  # separate env so evaluation doesn't interfere with training state

    # EvalCallback runs the current policy every eval_freq steps on eval_env,
    # prints mean success rate, and saves the best model seen so far.
    eval_cb = EvalCallback(
        eval_env,
        best_model_save_path=save_path,
        eval_freq=5_000,       # print progress every 5000 steps
        n_eval_episodes=20,    # average over 20 episodes for a stable success rate
        verbose=1,             # prints success rate so training doesn't feel stuck
    )

    model = SAC(
        "MultiInputPolicy", env,  # MultiInputPolicy handles dict observations (obs + goals)
        replay_buffer_class=HerReplayBuffer,
        replay_buffer_kwargs={
            "n_sampled_goal": 4,                    # relabel each transition with 4 fake goals
            "goal_selection_strategy": "future",    # pick relabel goals from later in the episode
        },
        verbose=0,
    )

    model.learn(total_timesteps=TOTAL_STEPS, callback=eval_cb)
    model.save(f"{save_path}/final_model")
    env.close()
    eval_env.close()
    print(f"\nTraining done. Best model saved to {save_path}/")

if __name__ == "__main__":
    # Expect ~5 min on GPU, ~20–40 min on CPU
    # Watch success_mean in the logs — it should climb from ~0% to >90%
    train(save_path="workspace/vla/ch02/models/sac_her")
```

**No GPU?** Reduce `TOTAL_STEPS = 50_000` and expect lower final success rate.
For a free GPU: open [Google Colab](https://colab.research.google.com), set runtime to GPU,
and paste the script there.

**What to observe:** Success rate starts near 0% and climbs to >90% within 50k steps. If it plateaus below 50%, check that `gym.register_envs(gymnasium_robotics)` is called before `gym.make()`.

### Visualise the trained policy

Once training is done, load the saved model and watch it run in MuJoCo. `render_mode="human"` opens a live window showing the robot arm moving.

```python workspace/vla/ch02/visualise.py
"""Load the trained SAC+HER model and watch it run in MuJoCo."""
import gymnasium as gym
import gymnasium_robotics
from stable_baselines3 import SAC

gym.register_envs(gymnasium_robotics)

MODEL_PATH = "workspace/vla/ch02/models/sac_her/best_model"
N_EPISODES = 5

env = gym.make("FetchReach-v4", render_mode="human")
model = SAC.load(MODEL_PATH, env=env)

for ep in range(N_EPISODES):
    obs, _ = env.reset()
    total_reward = 0.0
    for _ in range(50):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, _ = env.step(action)
        total_reward += reward
        if terminated or truncated:
            break
    print(f"Episode {ep+1}: total reward = {total_reward:.1f}")

env.close()
```

You should see the Fetch arm moving its gripper to the target marker. If the policy trained well, it reaches it most of the time.

---

## Project B — Reward Design Ablation

**Problem:** FetchReach's reward is sparse — pass/fail only. But there are other ways to design rewards, and the choice dramatically affects how fast (or whether) an agent learns. Understanding this is essential before you design rewards for any custom robot task.

**Approach:** Build a minimal 2D version of the reach task — simpler and faster to run than FetchReach, so the comparison is quick. Train SAC on three reward designs and compare success rates:

- **Sparse:** `0` when goal reached, `-1` every other step. Clean signal — but the agent rarely stumbles on success, so it rarely learns.
- **Dense:** `−distance` every step. Always informative — the agent always knows if it's getting closer. Can teach the wrong behaviour if distance isn't a perfect proxy for the real objective.
- **Sparse + HER:** relabels failed trajectories as successes for different goals. Best of both: clean objective, dense effective signal.

The script trains all three and prints final success rates side by side.

```python workspace/vla/ch02/reward_ablation.py
"""Compare sparse, dense, and HER rewards on a 2D reach task."""
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import SAC, HerReplayBuffer

class Reach2D(gym.Env):
    """
    Minimal 2D reach: agent moves a 2D point to a random goal.
    Simpler than FetchReach — same reward structure, runs in seconds.
    """

    def __init__(self, reward_type: str = "sparse"):
        super().__init__()
        self.reward_type = reward_type
        # HER requires a dict observation space with these exact keys
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
        # HER calls this internally to recompute rewards for relabelled goals
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

    # Evaluate: run 100 episodes with the trained policy, count successes
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
    print("Running reward ablation — takes a few minutes...")
    results = {
        "sparse":     run("sparse", use_her=False),
        "dense":      run("dense",  use_her=False),
        "sparse+HER": run("sparse", use_her=True),
    }
    print("\nResults:")
    for name, sr in results.items():
        print(f"  {name:15s}  success rate: {sr:.0%}")
```

**What to observe:** Dense and HER both outperform plain sparse. HER wins because it keeps the reward clean (sparse) while solving the learning signal problem — which is why it's the default for manipulation.

---

## Project C — Curriculum Learning

**Problem:** Even SAC+HER can struggle when goals are too hard from the start. If the target is always far away and random exploration almost never gets close, there's still no learning signal early on.

**Approach:** Start with goals very close to the agent (easy). Expand the goal range automatically once success rate crosses 80%. The agent builds skill incrementally instead of drowning in failure from step one.

The script prints `[curriculum] goal range → X.XX` each time difficulty increases — you'll see it step up as the agent improves.

```python workspace/vla/ch02/curriculum.py
"""Success-gated curriculum: expand goal range as success rate improves."""
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import SAC, HerReplayBuffer
from stable_baselines3.common.callbacks import BaseCallback

class CurriculumReach(gym.Env):
    """2D reach with adjustable goal range — same as Reach2D but difficulty is dynamic."""

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
        # track last 200 steps to compute a rolling success rate
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
    """Called by SB3 after every training step. Expands goal range when agent is ready."""

    def __init__(self, env: CurriculumReach, max_range: float = 0.8):
        super().__init__()
        self.env       = env
        self.max_range = max_range

    def _on_step(self) -> bool:
        if self.env.success_rate() > 0.8 and self.env.goal_range < self.max_range:
            self.env.goal_range = min(self.env.goal_range * 1.5, self.max_range)
            print(f"  [curriculum] goal range → {self.env.goal_range:.2f}")
        return True  # return False to stop training early

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

**What to observe:** Goal range expands in steps as success rate crosses 80%. Without curriculum, the same agent on full range typically converges much slower or not at all.

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
5. [SAC — Spinning Up](https://spinningup.openai.com/en/latest/algorithms/sac.html) — SAC internals if you want to go deeper
