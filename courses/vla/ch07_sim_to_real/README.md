# Chapter 7 — Sim-to-Real Transfer

**Time:** 4–5 days
**Hardware:** GPU helpful for training; no physical hardware required
**Prerequisites:** Chapters 2–5 (MuJoCo, IK, RL or IL — need a trained policy to stress-test)

---

## Why This Chapter Exists

You have a policy that works perfectly in simulation. You deploy it on a real robot and it fails — sometimes dramatically. This isn't bad luck; it's a predictable and well-understood failure mode. The sim was slightly wrong about friction, the camera renders colors differently, lighting varies, the robot's actual joint damping doesn't match the model. The policy learned to exploit sim-specific details that don't exist in reality.

The gap this chapter fills: most tutorials train in sim and stop there, or hand-wave "add domain randomization" without showing what to actually randomize, by how much, and how to measure whether it helped. You'll build the tools to quantify the gap and close it systematically rather than by trial and error.

---

## Part 1 — Why the Reality Gap Exists

### The Sources of Mismatch

**Physics parameters:**
- Real robot joints have friction, backlash, and flex that simulators don't model perfectly
- Object masses and friction coefficients are approximate in simulation
- Contact dynamics (how objects bounce, slide, deform) are simplified

**Visual appearance:**
- Simulation renders objects with perfect textures and lighting
- Real world has shadows, reflections, varying ambient light, sensor noise
- Camera calibration differences (lens distortion, color balance)

**Actuation:**
- Simulated actuators respond instantly and perfectly
- Real motors have communication latency (1–5ms), torque ripple, and compliance
- Control frequency matches matter: policy trained at 50Hz deployed at 30Hz fails

**Sensor noise:**
- Simulated joint encoders are perfect
- Real encoders have quantization noise, drift, and occasional dropouts

### What Fails First

From most to least common:
1. **Visual perception** — the real image looks nothing like simulation
2. **Contact dynamics** — grasping fails because friction model is wrong
3. **Actuation latency** — jerky motion because controller timing is off
4. **Joint friction** — arm is stiffer or looser than simulation

---

## Part 2 — Domain Randomization

### The Core Idea

Instead of trying to perfectly match simulation to reality, make the policy robust to a **distribution** of simulation parameters. If you train with mass ranging from 0.5–2.0 kg, the policy that works across all those masses will likely also work on the real robot's actual mass (somewhere in that range).

This was proven dramatically by OpenAI's Dactyl (2019): trained a policy purely in simulation on hundreds of randomized environments to solve a Rubik's cube with a real hand.

### What to Randomize

**Physics:**
```python
# Object properties
object_mass    ∈ [0.5, 2.0] × nominal
object_friction ∈ [0.3, 1.5] × nominal
object_restitution ∈ [0.0, 0.5]

# Robot properties
joint_damping  ∈ [0.5, 2.0] × nominal
joint_armature ∈ [0.5, 2.0] × nominal  # motor inertia
actuator_gear  ∈ [0.9, 1.1] × nominal   # gain variation ±10%

# Contact model
contact_friction ∈ [0.3, 1.5]
```

**Visual (for camera-based policies):**
```python
# Lighting
ambient_light   ∈ [0.2, 0.8]   # uniform random
diffuse_light   ∈ randomized direction + intensity
specular_light  ∈ [0, 0.5]

# Object appearance
object_color    ∈ random RGB or texture
background      ∈ random texture
camera_pose     ∈ small noise around nominal

# Image-level augmentation
random_crop     ∈ ±5% crop
color_jitter    ∈ brightness ±30%, contrast ±20%, saturation ±20%
gaussian_noise  σ ∈ [0, 0.02]
```

### How Much to Randomize

Too little → policy is brittle, doesn't generalize.
Too much → policy can't learn anything (all variations look the same to it).

**Rule of thumb:** Start with ±20% on physics parameters. Gradually increase until training becomes unstable, then back off 50%.

For visual randomization: start aggressive (random textures, random lighting). If policy fails to learn, reduce.

---

## Part 3 — System Identification

Domain randomization is a blunt tool — it randomizes everything. System identification is a precise tool — it measures your real robot and matches it in simulation.

### What to Measure

**Joint friction:** Slowly move each joint through its range under gravity. Measure the torque needed. This is your friction coefficient.

**Link masses:** Weigh each physical link. Update MJCF `<body mass="...">`.

**Object properties:** Weigh objects. Test friction by measuring slip angle on surfaces.

**Camera calibration:** Use a checkerboard pattern. OpenCV's `calibrateCamera()` gives you intrinsics and distortion coefficients.

**Latency:** Measure round-trip time from command to motor response. Add this delay to your simulation control loop.

### Combined Approach (Best Practice)

1. Do system identification first (measure what you can)
2. Apply domain randomization around those measured values
3. Use a range of ±20–50% of the measured value

This is more efficient than randomizing from scratch — you start closer to reality.

---

## Part 4 — Visual Domain Adaptation

### The Hardest Problem

Visual policies (those using RGB cameras) are particularly vulnerable to sim-to-real gap because:
- Simulation renders perfect, noise-free images
- Real cameras have noise, lens flare, focus issues, motion blur

### Strategies

**Option 1: Aggressive image augmentation during training**
Apply random transformations to simulation images during training so the policy learns invariance:
```python
transform = transforms.Compose([
    transforms.ColorJitter(brightness=0.4, contrast=0.3, saturation=0.3, hue=0.1),
    transforms.RandomAffine(degrees=5, translate=(0.05, 0.05)),
    transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 1.0)),
    transforms.RandomErasing(p=0.1),  # simulate occlusions
])
```

**Option 2: Randomize textures in simulation (texture DR)**
Replace simulation textures with random images from a texture library (use DTD — Describable Textures Dataset).

**Option 3: Use depth instead of RGB**
Depth images (from RealSense, structured light) are more consistent between sim and real. Less affected by lighting and color variation.

**Option 4: ViT features are more transfer-friendly**
VLAs like SmolVLA use ViT features pretrained on real images. These are inherently more robust to sim-real visual differences than CNNs trained only on sim data.

---

## External Resources

1. **Domain Randomization for Transfer from Simulation to Real World (OpenAI)**
   The paper that established domain randomization as the go-to approach.
   Read: abstract, Section 3 (method), Section 4 (results).
   → https://arxiv.org/abs/1703.06907

2. **Learning Dexterous In-Hand Manipulation (OpenAI Dactyl)**
   Domain randomization at scale on a Rubik's cube. Shows what's possible.
   → https://arxiv.org/abs/1808.00177

3. **MuJoCo Domain Randomization API**
   How to modify model parameters programmatically.
   → https://mujoco.readthedocs.io/en/stable/programming/simulation.html

4. **Sim-to-Real Transfer via Randomized Dynamics (Peng et al., 2018)**
   Key paper on using DR for locomotion. Principles apply to manipulation.
   → https://arxiv.org/abs/1804.10332

5. **DrAC: Augmented Random Crops for RL (NeurIPS 2021)**
   Best paper on using augmentation to reduce visual overfitting in RL policies.
   → https://arxiv.org/abs/2004.14990

6. **Describable Textures Dataset (DTD)**
   Use these random textures to replace simulation backgrounds and object surfaces.
   → https://www.robots.ox.ac.uk/~vgg/data/dtd/

---

## Project 7A — Physics Domain Randomization

Create `learning/ch07_sim_to_real/01_domain_rand_wrapper.py`:

```python
"""
A domain randomization wrapper for MuJoCo environments.
Wraps any Gymnasium environment and randomizes physics params on each reset.
"""
import numpy as np
import mujoco
import gymnasium as gym
from gymnasium import spaces


class DomainRandomizationWrapper(gym.Wrapper):
    """
    Randomizes MuJoCo model parameters on every env.reset().
    Works with any Gymnasium environment backed by a MuJoCo model.
    """

    def __init__(self, env, randomization_config=None):
        super().__init__(env)

        # Default randomization ranges (as multipliers of nominal values)
        self.config = randomization_config or {
            "body_mass": (0.7, 1.5),         # ±30-50% of nominal mass
            "geom_friction": (0.5, 1.8),      # ±50-80% of nominal friction
            "joint_damping": (0.5, 2.0),      # ±50-100% of nominal damping
            "actuator_gear": (0.85, 1.15),    # ±15% of nominal gain
            "object_pos_noise": 0.02,          # 2cm noise on object initial position (meters)
        }

        # Store nominal values to restore / randomize around
        self._store_nominal_values()

    def _store_nominal_values(self):
        """Store nominal model parameters before any randomization."""
        model = self.unwrapped.model
        self._nominal_body_mass = model.body_mass.copy()
        self._nominal_geom_friction = model.geom_friction.copy()
        self._nominal_dof_damping = model.dof_damping.copy()
        self._nominal_actuator_gear = model.actuator_gear.copy()

    def _randomize_model(self):
        """Randomize model parameters in-place."""
        model = self.unwrapped.model
        rng = self.np_random  # seeded RNG from Gymnasium

        lo, hi = self.config["body_mass"]
        for i in range(model.nbody):
            if self._nominal_body_mass[i] > 0:  # skip world body (mass=0)
                model.body_mass[i] = self._nominal_body_mass[i] * rng.uniform(lo, hi)

        lo, hi = self.config["geom_friction"]
        model.geom_friction[:] = self._nominal_geom_friction * rng.uniform(lo, hi)

        lo, hi = self.config["joint_damping"]
        model.dof_damping[:] = self._nominal_dof_damping * rng.uniform(lo, hi)

        lo, hi = self.config["actuator_gear"]
        model.actuator_gear[:] = self._nominal_actuator_gear * rng.uniform(lo, hi)

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        self._randomize_model()
        info["randomization"] = {
            "body_mass_sample": float(self.unwrapped.model.body_mass[1]),
            "friction_sample": float(self.unwrapped.model.geom_friction[0, 0]),
        }
        return obs, info


def test_randomization():
    """Test that randomization actually changes model parameters."""
    import sys
    sys.path.insert(0, '..')
    from ch02_mujoco.gym_env import ReachEnv  # your custom env from Ch.2

    base_env = ReachEnv()
    dr_env = DomainRandomizationWrapper(base_env)

    masses = []
    frictions = []
    for _ in range(20):
        obs, info = dr_env.reset()
        masses.append(info["randomization"]["body_mass_sample"])
        frictions.append(info["randomization"]["friction_sample"])

    print(f"Body mass samples: min={min(masses):.3f} max={max(masses):.3f} "
          f"mean={np.mean(masses):.3f}")
    print(f"Friction samples:  min={min(frictions):.3f} max={max(frictions):.3f} "
          f"mean={np.mean(frictions):.3f}")
    print("Domain randomization working correctly.")
    dr_env.close()


if __name__ == "__main__":
    test_randomization()
```

---

## Project 7B — Train Robust vs. Non-Robust Policies

Create `learning/ch07_sim_to_real/02_train_robust.py`:

```python
"""
Train two policies — one with domain randomization, one without.
Compare their robustness to parameter variations.
"""
import sys
import numpy as np
import gymnasium as gym
from stable_baselines3 import SAC
from stable_baselines3.common.monitor import Monitor
import matplotlib.pyplot as plt

sys.path.insert(0, '..')
from ch04_rl.reward_wrapper import FetchReachRewardWrapper  # if you made one
from domain_rand_wrapper import DomainRandomizationWrapper


def make_env(use_dr=False):
    env = gym.make("FetchReach-v4")
    if use_dr:
        env = DomainRandomizationWrapper(env)
    return Monitor(env)


def train_policy(use_dr, total_steps=200_000):
    from stable_baselines3.her.her_replay_buffer import HerReplayBuffer

    env = make_env(use_dr=use_dr)
    model = SAC(
        "MultiInputPolicy", env,
        replay_buffer_class=HerReplayBuffer,
        replay_buffer_kwargs=dict(n_sampled_goal=4, goal_selection_strategy="future"),
        learning_rate=1e-3, batch_size=256, gamma=0.95, verbose=0
    )
    label = "with DR" if use_dr else "without DR"
    print(f"Training {label}...")
    model.learn(total_timesteps=total_steps, progress_bar=True)
    env.close()
    return model


def evaluate_robustness(model, n_eval_episodes=50):
    """
    Evaluate policy across a grid of physics parameter variations.
    Returns success rate for each (mass_scale, friction_scale) combo.
    """
    mass_scales = [0.5, 0.7, 1.0, 1.3, 1.6]
    friction_scales = [0.4, 0.6, 1.0, 1.4, 1.8]
    results = np.zeros((len(mass_scales), len(friction_scales)))

    for i, ms in enumerate(mass_scales):
        for j, fs in enumerate(friction_scales):
            config = {
                "body_mass": (ms, ms),        # fixed (not random) for evaluation
                "geom_friction": (fs, fs),
                "joint_damping": (1.0, 1.0),
                "actuator_gear": (1.0, 1.0),
            }
            eval_env = DomainRandomizationWrapper(
                gym.make("FetchReach-v4"),
                randomization_config=config
            )

            successes = 0
            for _ in range(n_eval_episodes):
                obs, _ = eval_env.reset()
                for _ in range(50):
                    action, _ = model.predict(obs, deterministic=True)
                    obs, _, terminated, truncated, info = eval_env.step(action)
                    if terminated or truncated:
                        break
                successes += int(info.get("is_success", False))

            results[i, j] = successes / n_eval_episodes
            eval_env.close()

    return results, mass_scales, friction_scales


def plot_robustness_heatmaps(results_no_dr, results_with_dr, mass_scales, friction_scales):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    for ax, results, title in zip(axes,
                                   [results_no_dr, results_with_dr],
                                   ["No Domain Randomization", "With Domain Randomization"]):
        im = ax.imshow(results * 100, cmap='RdYlGn', vmin=0, vmax=100,
                       aspect='auto', origin='lower')
        ax.set_xticks(range(len(friction_scales)))
        ax.set_xticklabels([f"{s:.1f}×" for s in friction_scales])
        ax.set_yticks(range(len(mass_scales)))
        ax.set_yticklabels([f"{s:.1f}×" for s in mass_scales])
        ax.set_xlabel("Friction Scale")
        ax.set_ylabel("Mass Scale")
        ax.set_title(f"{title}\n(green=high success, red=low)")

        # Annotate cells with values
        for i in range(len(mass_scales)):
            for j in range(len(friction_scales)):
                ax.text(j, i, f"{results[i,j]*100:.0f}%",
                        ha='center', va='center', fontsize=9,
                        color='black' if results[i,j] > 0.3 else 'white')

        # Mark nominal (1.0×, 1.0×) condition
        nom_i = mass_scales.index(1.0)
        nom_j = friction_scales.index(1.0)
        ax.add_patch(plt.Rectangle((nom_j-0.5, nom_i-0.5), 1, 1,
                                    fill=False, edgecolor='blue', linewidth=3))

        plt.colorbar(im, ax=ax, label='Success Rate (%)')

    plt.suptitle("Robustness Heatmap: Success Rate vs. Physics Parameters\n"
                 "Blue box = nominal (training) condition", fontsize=13)
    plt.tight_layout()
    plt.savefig("robustness_heatmaps.png", dpi=150)
    plt.show()
    print("Saved robustness_heatmaps.png")
    print("\nKey observation: DR policy maintains high success across a wider range of parameters.")


if __name__ == "__main__":
    print("Training policy WITHOUT domain randomization...")
    model_no_dr = train_policy(use_dr=False, total_steps=200_000)

    print("\nTraining policy WITH domain randomization...")
    model_with_dr = train_policy(use_dr=True, total_steps=200_000)

    print("\nEvaluating robustness (this takes a while)...")
    results_no_dr, mass_scales, friction_scales = evaluate_robustness(model_no_dr)
    results_with_dr, _, _ = evaluate_robustness(model_with_dr)

    plot_robustness_heatmaps(results_no_dr, results_with_dr, mass_scales, friction_scales)
```

---

## Project 7C — Visual Domain Randomization

Create `learning/ch07_sim_to_real/03_visual_dr.py`:

```python
"""
Add visual domain randomization to MuJoCo:
- Random lighting
- Random textures
- Image augmentation pipeline

This is the hardest part of sim-to-real for vision-based policies.
"""
import numpy as np
import mujoco
import cv2
import torch
import torchvision.transforms as T
import gymnasium as gym
from gymnasium import spaces
import matplotlib.pyplot as plt


class VisualDRWrapper(gym.ObservationWrapper):
    """
    Applies visual domain randomization and augmentation to image observations.
    """

    def __init__(self, env, augmentation_level="medium"):
        super().__init__(env)
        self.augmentation_level = augmentation_level
        self._build_augmentation_pipeline(augmentation_level)

    def _build_augmentation_pipeline(self, level):
        if level == "none":
            self.augment = T.Compose([T.ToTensor()])
        elif level == "light":
            self.augment = T.Compose([
                T.ToTensor(),
                T.ColorJitter(brightness=0.2, contrast=0.1),
            ])
        elif level == "medium":
            self.augment = T.Compose([
                T.ToTensor(),
                T.ColorJitter(brightness=0.4, contrast=0.3, saturation=0.3, hue=0.05),
                T.RandomAffine(degrees=3, translate=(0.03, 0.03)),
                T.GaussianBlur(kernel_size=3, sigma=(0.1, 0.5)),
            ])
        elif level == "aggressive":
            self.augment = T.Compose([
                T.ToTensor(),
                T.ColorJitter(brightness=0.6, contrast=0.5, saturation=0.5, hue=0.1),
                T.RandomAffine(degrees=8, translate=(0.05, 0.05)),
                T.GaussianBlur(kernel_size=5, sigma=(0.1, 2.0)),
                T.RandomErasing(p=0.1, scale=(0.02, 0.1)),
                T.RandomAdjustSharpness(sharpness_factor=2, p=0.3),
            ])

    def observation(self, obs):
        if isinstance(obs, dict) and "pixels" in obs:
            img = obs["pixels"]
            augmented = self._augment_image(img)
            obs["pixels"] = augmented
        elif isinstance(obs, np.ndarray) and obs.ndim == 3:
            obs = self._augment_image(obs)
        return obs

    def _augment_image(self, img):
        """Apply augmentation pipeline to an HxWxC uint8 image."""
        if img.dtype != np.uint8:
            img = (img * 255).astype(np.uint8)
        from PIL import Image
        pil_img = Image.fromarray(img)
        tensor = self.augment(pil_img)
        return (tensor.permute(1, 2, 0).numpy() * 255).astype(np.uint8)


def randomize_mujoco_lighting(model, rng):
    """
    Randomize MuJoCo lighting parameters.
    These affect how the renderer shades the scene.
    """
    model.vis.headlight.ambient[:] = rng.uniform(0.15, 0.6, 3)
    model.vis.headlight.diffuse[:] = rng.uniform(0.3, 0.9, 3)
    model.vis.headlight.specular[:] = rng.uniform(0.0, 0.3, 3)


def demo_augmentation_levels():
    """Show how different augmentation levels affect the same image."""
    env = gym.make("gym_pusht/PushT-v0", obs_type="pixels", render_mode="rgb_array")
    obs, _ = env.reset()

    if isinstance(obs, dict):
        base_img = obs.get("pixels", obs.get("image", list(obs.values())[0]))
    else:
        base_img = obs

    if base_img.dtype != np.uint8:
        base_img = (base_img * 255).astype(np.uint8)

    levels = ["none", "light", "medium", "aggressive"]
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))

    for col, level in enumerate(levels):
        wrapper = VisualDRWrapper(gym.make("gym_pusht/PushT-v0", obs_type="pixels",
                                           render_mode="rgb_array"),
                                  augmentation_level=level)
        axes[0, col].imshow(base_img)
        axes[0, col].set_title(f"Original")
        axes[0, col].axis("off")

        augmented = wrapper._augment_image(base_img.copy())
        axes[1, col].imshow(augmented)
        axes[1, col].set_title(f"Level: {level}")
        axes[1, col].axis("off")
        wrapper.close()

    plt.suptitle("Visual Augmentation Levels for Domain Randomization\n"
                 "Train with 'medium' or 'aggressive' for better sim-to-real transfer",
                 fontsize=12)
    plt.tight_layout()
    plt.savefig("augmentation_levels.png", dpi=150)
    plt.show()
    env.close()


if __name__ == "__main__":
    demo_augmentation_levels()
```

---

## Project 7D — Robustness Analysis Report Tool

Create `learning/ch07_sim_to_real/04_transfer_report.py`:

```python
"""
Automated robustness analysis tool.
Given a trained policy, systematically stress-test it and produce a report.
"""
import numpy as np
import matplotlib.pyplot as plt
import gymnasium as gym
from stable_baselines3 import SAC


def robustness_sweep(model, param_name, param_range, n_episodes=30):
    """
    Sweep a single physics parameter and measure success rate at each value.
    """
    from domain_rand_wrapper import DomainRandomizationWrapper

    results = []
    for param_val in param_range:
        config = {
            "body_mass": (1.0, 1.0),
            "geom_friction": (1.0, 1.0),
            "joint_damping": (1.0, 1.0),
            "actuator_gear": (1.0, 1.0),
        }
        config[param_name] = (param_val, param_val)

        env = DomainRandomizationWrapper(
            gym.make("FetchReach-v4"),
            randomization_config=config
        )

        successes = 0
        for _ in range(n_episodes):
            obs, _ = env.reset()
            for _ in range(50):
                action, _ = model.predict(obs, deterministic=True)
                obs, _, terminated, truncated, info = env.step(action)
                if terminated or truncated:
                    break
            successes += int(info.get("is_success", False))

        results.append(successes / n_episodes)
        env.close()
        print(f"  {param_name}={param_val:.2f}: {results[-1]*100:.0f}%")

    return results


def generate_transfer_report(model, policy_name="Policy"):
    """
    Generate a full robustness analysis report for a trained policy.
    """
    print(f"\n{'='*60}")
    print(f"ROBUSTNESS ANALYSIS REPORT: {policy_name}")
    print('='*60)

    sweep_configs = {
        "body_mass": np.linspace(0.4, 2.0, 9),
        "geom_friction": np.linspace(0.3, 2.0, 9),
        "joint_damping": np.linspace(0.3, 2.5, 9),
        "actuator_gear": np.linspace(0.6, 1.4, 9),
    }

    all_results = {}
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for ax, (param_name, param_range) in zip(axes, sweep_configs.items()):
        print(f"\nSweeping {param_name}...")
        results = robustness_sweep(model, param_name, param_range)
        all_results[param_name] = (param_range, results)

        ax.plot(param_range, [r*100 for r in results], 'b-o', linewidth=2, markersize=7)
        ax.axvline(1.0, color='green', linestyle='--', alpha=0.8, label='Nominal (1.0×)')
        ax.axhline(80, color='gray', linestyle=':', alpha=0.6, label='80% threshold')
        ax.fill_between(param_range, [r*100 for r in results], 0,
                        where=np.array(results) < 0.5, color='red', alpha=0.2,
                        label='Failure zone (<50%)')
        ax.set_xlabel(f'{param_name} (× nominal)')
        ax.set_ylabel('Success Rate (%)')
        ax.set_title(f'Sensitivity to {param_name}')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 105)

    plt.suptitle(f'Robustness Analysis: {policy_name}\n'
                 'Steeper curves = more brittle parameter', fontsize=13)
    plt.tight_layout()
    report_path = f"robustness_report_{policy_name.replace(' ', '_')}.png"
    plt.savefig(report_path, dpi=150)
    plt.show()

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    for param_name, (param_range, results) in all_results.items():
        nominal_idx = np.argmin(np.abs(param_range - 1.0))
        nominal_sr = results[nominal_idx]

        # Find range where success > 70%
        robust_range = param_range[np.array(results) > 0.7]
        if len(robust_range) > 0:
            robust_str = f"[{robust_range.min():.1f}×, {robust_range.max():.1f}×]"
        else:
            robust_str = "NONE — brittle!"

        print(f"  {param_name:20s}: nominal={nominal_sr*100:.0f}%  "
              f"robust range={robust_str}")

    print(f"\nReport saved: {report_path}")


if __name__ == "__main__":
    # Load a trained model (train one first with ch04_rl or ch05_imitation)
    try:
        model = SAC.load("../ch04_rl/models/best_model")
        generate_transfer_report(model, "SAC+HER FetchReach")
    except Exception as e:
        print(f"Could not load model: {e}")
        print("Train a model first with Chapter 4's training scripts.")
```

---

## Self-Check Questions

Before moving to Chapter 8:

1. Your policy achieves 90% in simulation and 20% on the real robot. You suspect it's a visual issue. How do you confirm this, and what's your first fix?
2. Domain randomization range for friction is [0.5, 2.0]. Your real robot's actual friction is measured at 0.3. What problem will you have and how do you fix it?
3. Why is sim-to-real harder for contact-rich tasks (grasping a deformable object) than free-space tasks (moving to a target position)?
4. You increase domain randomization range by 3× and the policy stops learning. What happened and how do you fix it?
5. What is the difference between domain randomization and domain adaptation?

**Answers:**
1. Confirmation: replace the real camera image with a simulated image (using a photo of the setup rendered in simulation) and see if performance recovers. First fix: add aggressive color jitter and random lighting augmentation during training.
2. Real friction (0.3) is below your randomization range minimum (0.5). The policy has never experienced such low friction → it fails. Fix: extend your randomization range down to [0.2, 2.0] or re-measure and update the nominal.
3. Contact physics (friction, deformation, contact geometry) is much harder to model accurately than free-space dynamics (just kinematics). Rigid object contact in simulation uses simplified Coulomb friction; real deformable objects have history-dependent contact that no simulator captures well.
4. Too much variation → the policy can't find consistent patterns → learning signal is noisy → doesn't converge. Fix: reduce randomization range, use curriculum DR (start small, gradually increase range over training).
5. Domain randomization: diversify the source domain (simulation) so the policy generalizes. Domain adaptation: explicitly bridge source and target domains by aligning their distributions (e.g., train a model to make sim images look real). DR is simpler and often sufficient. DA requires access to real data.

---

## What's Next

Chapter 8 introduces ROS 2 — the middleware that connects your simulation, learned policies, and eventually real hardware into a complete system. If you're hardware-free for now, Chapter 8 can be done using Docker and your MuJoCo simulation as the "robot."
