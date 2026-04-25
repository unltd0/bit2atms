# Chapter 5 — Sim-to-Real Transfer

**Time:** 4–5 days
**Hardware:** GPU helpful (CPU works for most experiments)
**Prerequisites:** Chapter 3 (trained a policy in sim), Chapter 1 (MuJoCo)

---

## What are we here for

You trained a policy in simulation. It works great. You deploy it on a real robot and it
fails immediately. This is the **reality gap** — the mismatch between simulation and the
real world.

The reality gap has two components:
- **Physics mismatch:** sim uses idealized rigid-body dynamics; the real robot has joint
  friction, motor backlash, and contact noise that the sim doesn't model accurately
- **Visual mismatch:** sim renders clean, perfectly-lit synthetic images; the real world
  has varying lighting, shadows, and camera noise

This chapter teaches you how to measure and close both gaps. The core technique is
**domain randomization** — randomize simulation parameters during training so the policy
learns to be robust to variation, rather than memorizing the exact sim physics.

**Install:**
```bash
pip install mujoco numpy stable-baselines3 gymnasium matplotlib
```

**Skip if you can answer:**
1. What is the reality gap? Name its two main components.
2. What does domain randomization do, and what's the tradeoff?
3. Your policy succeeds in sim but fails when you change the table surface. Which type of
   randomization should you add?
4. You add mass randomization but sim performance drops 20%. What do you check?

---

## Projects

| # | Project | What you build |
|---|---------|---------------|
| A | Physics Domain Randomization | Train a policy with randomized mass, friction, damping; test on unseen params |
| B | Robust vs. Non-Robust | Quantify what DR gains and costs on a reach task |
| C | Visual Domain Randomization | Add random textures, lighting, and image augmentation |
| D | Robustness Report | Sweep a parameter grid and identify the brittle axes |

---

## Project A — Physics Domain Randomization

**Problem:** A policy trained at exactly one set of physics parameters (mass, friction,
damping) will fail when any of those differ — and they always will on a real robot.

**Approach:** Build a MuJoCo environment wrapper that randomizes physics parameters at
each episode reset. Train a reach policy with and without randomization. Test both on
out-of-distribution parameters.

### Domain randomization

**Domain randomization (DR)** makes the sim a *distribution* of environments rather than
a fixed one. If the real robot falls somewhere in that distribution, the policy handles it.
The tradeoff: wider randomization → more robust, but harder to train (the policy has to
solve a harder problem). Narrow to the point where the policy still learns; widen until
it covers the real robot. [Read more: Domain Randomization paper](https://arxiv.org/abs/1703.06907)

```python workspace/vla/ch05/physics_dr.py
"""
Domain-randomized reach environment. Randomizes mass, friction, and joint damping
each episode. Train with DR; test on fixed params outside the training range.
"""
import numpy as np
import mujoco
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import SAC

# 2-DOF arm XML with a target sphere
ARM_XML = """
<mujoco>
  <option timestep="0.002"/>
  <worldbody>
    <body name="link1">
      <joint name="j1" type="hinge" axis="0 0 1" range="-3.14 3.14"/>
      <inertial mass="1.0" diaginertia="0.01 0.01 0.01" pos="0 0 0.2"/>
      <geom type="capsule" size="0.04 0.2" pos="0 0 0.2"/>
      <body name="link2" pos="0 0 0.4">
        <joint name="j2" type="hinge" axis="0 1 0" range="-3.14 3.14"
               damping="0.1"/>
        <inertial mass="0.5" diaginertia="0.005 0.005 0.005" pos="0 0 0.15"/>
        <geom type="capsule" size="0.03 0.15" pos="0 0 0.15"/>
        <site name="ee" pos="0 0 0.3"/>
      </body>
    </body>
    <site name="target" pos="0.3 0 0.5" size="0.03"/>
  </worldbody>
  <actuator>
    <motor name="m1" joint="j1" ctrllimited="true" ctrlrange="-5 5"/>
    <motor name="m2" joint="j2" ctrllimited="true" ctrlrange="-5 5"/>
  </actuator>
</mujoco>
"""

class DRReachEnv(gym.Env):
    """2-DOF reach with physics domain randomization."""

    def __init__(self, use_dr: bool = True):
        super().__init__()
        self.use_dr = use_dr
        self.observation_space = spaces.Box(-np.inf, np.inf, (6,), np.float32)
        self.action_space      = spaces.Box(-1, 1, (2,), np.float32)
        self._load_model()

    def _load_model(self) -> None:
        self.model = mujoco.MjModel.from_xml_string(ARM_XML)
        self.data  = mujoco.MjData(self.model)

    def _randomize(self) -> None:
        if not self.use_dr:
            return
        # Randomize link masses ±50%
        self.model.body_mass[1] = np.random.uniform(0.5, 1.5)
        self.model.body_mass[2] = np.random.uniform(0.25, 0.75)
        # Randomize joint damping ±5×
        self.model.dof_damping[1] = np.random.uniform(0.02, 0.5)
        # Randomize friction ±3×
        self.model.geom_friction[:, 0] = np.random.uniform(0.3, 1.5)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)
        self._randomize()
        self.data.qpos[:2] = np.random.uniform(-1.0, 1.0, 2)
        mujoco.mj_forward(self.model, self.data)
        return self._obs(), {}

    def step(self, action: np.ndarray):
        self.data.ctrl[:2] = action
        for _ in range(5):
            mujoco.mj_step(self.model, self.data)
        obs    = self._obs()
        dist   = np.linalg.norm(obs[:3] - obs[3:])
        reward = -dist
        done   = dist < 0.05
        return obs, reward, done, False, {"distance": dist}

    def _obs(self) -> np.ndarray:
        ee_id     = self.model.site("ee").id
        tgt_id    = self.model.site("target").id
        mujoco.mj_forward(self.model, self.data)
        ee_pos    = self.data.site_xpos[ee_id]
        tgt_pos   = self.data.site_xpos[tgt_id]
        return np.concatenate([ee_pos, tgt_pos]).astype(np.float32)

def train_policy(use_dr: bool, steps: int = 100_000) -> SAC:
    env   = DRReachEnv(use_dr=use_dr)
    model = SAC("MlpPolicy", env, verbose=0)
    model.learn(steps)
    return model

def evaluate(model: SAC, mass_scale: float = 1.0, damping_scale: float = 1.0,
             n_trials: int = 50) -> float:
    env = DRReachEnv(use_dr=False)
    env.model.body_mass[1]    *= mass_scale
    env.model.dof_damping[1]  *= damping_scale
    successes = 0
    for _ in range(n_trials):
        obs, _ = env.reset()
        for _ in range(200):
            action, _ = model.predict(obs, deterministic=True)
            obs, _, term, trunc, _ = env.step(action)
            if term or trunc:
                successes += int(term)
                break
    return successes / n_trials

if __name__ == "__main__":
    print("Training without DR...")
    policy_no_dr = train_policy(use_dr=False)
    print("Training with DR...")
    policy_dr    = train_policy(use_dr=True)

    test_cases = [(1.0, 1.0, "nominal"), (2.0, 1.0, "2× mass"),
                  (0.5, 1.0, "0.5× mass"), (1.0, 5.0, "5× damping")]
    print(f"\n{'Test case':20s}  {'No DR':>8}  {'With DR':>8}")
    for mass, damp, label in test_cases:
        sr_no = evaluate(policy_no_dr, mass, damp)
        sr_dr = evaluate(policy_dr,    mass, damp)
        print(f"{label:20s}  {sr_no:>8.0%}  {sr_dr:>8.0%}")
```

**What to observe:** Without DR, the policy collapses immediately when mass or damping
changes. With DR, success rate degrades gracefully. The tradeoff: DR policy is slightly
worse at nominal params.

---

## Project B — Robust vs. Non-Robust

**Problem:** Quantify the robustness-performance tradeoff precisely, and find the
randomization range where you get robustness without sacrificing too much nominal performance.

**Approach:** Sweep DR range width (narrow / medium / wide) and measure both nominal
success rate and OOD (out-of-distribution) success rate.

```python workspace/vla/ch05/robustness_sweep.py
"""Sweep DR range width and measure nominal vs. OOD success rate.
Run from workspace/vla/ch05/ so the physics_dr import resolves.
"""
import numpy as np
from physics_dr import DRReachEnv, evaluate
from stable_baselines3 import SAC

DR_CONFIGS = {
    "none":   {"mass_range": (1.0, 1.0), "damp_range": (0.1, 0.1)},
    "narrow": {"mass_range": (0.8, 1.2), "damp_range": (0.05, 0.2)},
    "medium": {"mass_range": (0.5, 1.5), "damp_range": (0.02, 0.5)},
    "wide":   {"mass_range": (0.2, 2.0), "damp_range": (0.01, 1.0)},
}

results = {}
for name, cfg in DR_CONFIGS.items():
    print(f"Training {name} DR...")
    env   = DRReachEnv(use_dr=(name != "none"))
    model = SAC("MlpPolicy", env, verbose=0)
    model.learn(100_000)
    results[name] = {
        "nominal": evaluate(model, mass_scale=1.0, damping_scale=1.0),
        "ood_mass": evaluate(model, mass_scale=2.0, damping_scale=1.0),
        "ood_damp": evaluate(model, mass_scale=1.0, damping_scale=5.0),
    }

print(f"\n{'Config':10s}  {'Nominal':>8}  {'2× mass':>8}  {'5× damp':>8}")
for name, r in results.items():
    print(f"{name:10s}  {r['nominal']:>8.0%}  {r['ood_mass']:>8.0%}  {r['ood_damp']:>8.0%}")
```

**What to observe:** Nominal performance degrades as DR width increases, but OOD
robustness improves. Medium DR is usually the best practical choice.

---

## Project C — Visual Domain Randomization

**Problem:** Visual policies trained on clean sim images fail when lighting, background,
or camera position changes — the visual reality gap.

**Approach:** Add image augmentation to your training observations as a visual DR proxy.
Full texture/lighting randomization requires modifying the MuJoCo scene XML at each reset
(randomize `<light>` and `<material>` attributes). Image augmentation is the practical
starting point — it covers ~80% of the visual gap for most tasks.

### Visual DR strategies

- **Image augmentation:** Color jitter, random crops, Gaussian blur — applied to observations
  during training. This is what the code below implements.
- **Random background textures:** Replace floor/walls with random patterns at each episode
  reset — modify `model.mat_texid` and reload textures in `_randomize()`.
- **Random lighting:** Vary `model.light_pos` and `model.light_dir` at reset.
- **Random camera pose:** Small perturbations to `model.cam_pos` at reset.

To plug augmentation into your ACT training from Ch03: in LeRobot's training loop, images
are loaded via the dataset's `__getitem__`. Wrap the dataset with a transform that calls
`augment_obs()` on each `observation.image` tensor before it's fed to the policy.

```python workspace/vla/ch05/visual_dr.py
"""Apply image augmentation as a visual DR proxy. Measure robustness to visual shifts."""
import numpy as np
import torch
import torchvision.transforms as T
import gymnasium as gym
import gym_pusht

# Augmentation pipeline — applied to observations during training
TRAIN_AUGMENTATION = T.Compose([
    T.ToPILImage(),
    T.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.4, hue=0.1),
    T.RandomCrop(84, padding=8),
    T.ToTensor(),
])

EVAL_AUGMENTATION = T.Compose([
    T.ToPILImage(),
    T.ToTensor(),
])

def augment_obs(obs: np.ndarray, augment: bool = True) -> torch.Tensor:
    """Apply augmentation to an (H, W, 3) uint8 image."""
    img = torch.from_numpy(obs)
    pipeline = TRAIN_AUGMENTATION if augment else EVAL_AUGMENTATION
    return pipeline(img)

def test_robustness(env_id: str, policy, n_trials: int = 50,
                    apply_aug: bool = False) -> float:
    """Evaluate policy with optional visual augmentation at eval time."""
    env = gym.make(env_id, obs_type="pixels_agent_pos", render_mode=None)
    successes = 0
    device = next(policy.parameters()).device

    for _ in range(n_trials):
        obs, _ = env.reset()
        for _ in range(200):
            img = augment_obs(obs["pixels"], augment=apply_aug).unsqueeze(0).to(device)
            with torch.no_grad():
                action = policy.select_action({
                    "observation.image": img,
                    "observation.state": torch.tensor(obs["agent_pos"]).unsqueeze(0).to(device),
                })
            obs, _, term, trunc, info = env.step(action.cpu().numpy()[0])
            if term or trunc:
                successes += int(info.get("is_success", False))
                break
    env.close()
    return successes / n_trials

if __name__ == "__main__":
    # Verify augmentation pipeline works on a dummy image
    dummy = np.random.randint(0, 255, (96, 96, 3), dtype=np.uint8)
    aug   = augment_obs(dummy, augment=True)
    clean = augment_obs(dummy, augment=False)
    print(f"Input:  shape={dummy.shape}  dtype={dummy.dtype}")
    print(f"Augmented:  shape={aug.shape}  range=[{aug.min():.2f}, {aug.max():.2f}]")
    print(f"Clean:      shape={clean.shape}  range=[{clean.min():.2f}, {clean.max():.2f}]")
    print()
    print("Usage: wrap your ACT/Diffusion training loop with augment_obs(obs['pixels'], augment=True)")
    print("At eval time use augment=False (or apply_aug=True to test robustness to visual shift).")
```

---

## Project D — Robustness Report

**Problem:** Before deploying to a real robot, you want to know which axes of variation
your policy can tolerate and which will cause it to fail.

**Approach:** Systematically sweep a grid of physics parameters and produce a heatmap
showing success rate vs. (mass_scale, damping_scale).

```python workspace/vla/ch05/robustness_report.py
"""Sweep physics parameter grid and produce a robustness heatmap.
Run from workspace/vla/ch05/ so the physics_dr import resolves.
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from physics_dr import DRReachEnv, evaluate
from stable_baselines3 import SAC

MASS_SCALES  = [0.3, 0.5, 0.7, 1.0, 1.3, 1.7, 2.0]
DAMP_SCALES  = [0.1, 0.3, 0.5, 1.0, 2.0, 5.0, 10.0]

def build_heatmap(model: SAC) -> np.ndarray:
    grid = np.zeros((len(DAMP_SCALES), len(MASS_SCALES)))
    for i, damp in enumerate(DAMP_SCALES):
        for j, mass in enumerate(MASS_SCALES):
            grid[i, j] = evaluate(model, mass_scale=mass, damping_scale=damp, n_trials=20)
            print(f"  mass={mass:.1f}  damp={damp:.1f}  sr={grid[i,j]:.0%}")
    return grid

if __name__ == "__main__":
    env   = DRReachEnv(use_dr=True)
    model = SAC("MlpPolicy", env, verbose=0)
    model.learn(100_000)

    print("\nBuilding robustness heatmap...")
    grid = build_heatmap(model)

    plt.figure(figsize=(10, 7))
    plt.imshow(grid, vmin=0, vmax=1, aspect="auto", origin="lower")
    plt.colorbar(label="Success rate")
    plt.xticks(range(len(MASS_SCALES)), [f"{m:.1f}×" for m in MASS_SCALES])
    plt.yticks(range(len(DAMP_SCALES)), [f"{d:.1f}×" for d in DAMP_SCALES])
    plt.xlabel("Mass scale"); plt.ylabel("Damping scale")
    plt.title("Robustness heatmap — success rate across physics parameters")
    out = os.path.join(os.path.dirname(__file__), "robustness_heatmap.png")
    plt.savefig(out)
    print(f"Saved {out}")
    print(f"\nNominal (1.0, 1.0): {grid[DAMP_SCALES.index(1.0), MASS_SCALES.index(1.0)]:.0%}")
```

**What to observe:** The heatmap shows which parameter combinations break the policy.
Typically there are clear "brittle axes" — the policy tolerates mass variation well but
collapses with high damping (or vice versa). Add more DR along the brittle axes.

---

## Self-Check

1. What are the two main components of the reality gap?
   **Answer:** Physics mismatch (sim uses ideal rigid-body dynamics; real robot has
   friction, backlash, compliance) and visual mismatch (sim renders clean synthetic images;
   real world has variable lighting, noise, and background clutter).

2. Your policy works at mass 1.0 but fails at mass 1.5. You add DR with mass range [0.5, 2.0].
   Training performance drops 15%. Is this acceptable?
   **Answer:** Usually yes — this is the expected robustness-performance tradeoff. Verify
   the drop is only ~15% at nominal, and that OOD performance improved enough to justify it.
   If nominal drops 50%, the DR range is too wide.

3. You add color jitter augmentation but the policy still fails when you move the camera 5 cm.
   Why?
   **Answer:** Color jitter handles lighting/color variation but not geometric change.
   Camera pose shift changes the spatial arrangement of the scene. You need camera pose
   randomization or spatial augmentation (random crops / affine transforms).

4. Your robustness heatmap shows the policy collapses when damping > 3×. What do you do?
   **Answer:** Add damping randomization to the DR range — extend the upper bound beyond
   3× the nominal value. Retrain and re-sweep to confirm the brittle axis is covered.

5. Why test on parameters *outside* the training DR range when building the robustness report?
   **Answer:** Parameters inside the range are easy — the policy was trained on them.
   The report's value is knowing where the policy breaks *beyond* training conditions,
   which tells you whether the real robot (which may have parameters outside your range)
   will work.

---

## Common Mistakes

- **DR range too wide from the start:** If mass varies 10×, training becomes too hard and
  the policy may never converge. Start narrow (±30%) and widen after the policy learns
  the nominal task.

- **Only randomizing physics, ignoring visual gap:** Visual mismatch often dominates.
  Always include image augmentation for vision-based policies.

- **Evaluating robustness at the same seed as training:** The policy may have memorized
  the fixed initial conditions. Sweep diverse seeds and parameter combinations.

- **No baseline (no-DR policy):** Always train a non-randomized baseline to quantify
  what DR gains and costs. Without it, you can't measure the tradeoff.

---

## Resources

1. [Domain Randomization paper](https://arxiv.org/abs/1703.06907) — original OpenAI paper, read Section 3
2. [OpenAI Dactyl blog](https://openai.com/research/learning-dexterity) — real-world DR at scale
3. [MuJoCo XML reference — compiler section](https://mujoco.readthedocs.io/en/stable/XMLreference.html) — how to modify physics params programmatically
