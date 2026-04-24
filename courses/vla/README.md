# Vision-Language-Action — Curriculum Guide

Go from zero to building real robot manipulation systems. Focus is on *applying* modern ML,
not deriving it.

**Who this is for:** Python-literate, basic ML intuition, no robotics background needed.
**Time:** 4–8 weeks at 2–4 hours/day. Chapters 1–7 are laptop-only.
**Hardware:** Ch.1–7 laptop only. Ch.8 needs Docker. Ch.9 needs ~$250–$500 in hardware.

---

## Environment Setup

Do this once before starting.

```bash
# Python 3.10–3.12 recommended
python3 -m venv bit2atms-env
source bit2atms-env/bin/activate   # macOS / Linux

# Base packages (Ch.1 onward)
pip install mujoco numpy matplotlib scipy
```

Additional installs are listed in each chapter below.

---

## Chapters

| # | Chapter |
|---|---------|
| 1 | [MuJoCo Fundamentals](ch01_transforms/README.md) |
| 2 | [Control & Gymnasium](ch02_mujoco/README.md) |
| 3 | [Kinematics & Motion Planning](ch03_kinematics/README.md) |
| 4 | [Reinforcement Learning (Applied)](ch04_rl/README.md) |
| 5 | [Imitation Learning (ACT + Diffusion)](ch05_imitation/README.md) |
| 6 | [Vision-Language-Action Models](ch06_vla/README.md) |
| 7 | [Sim-to-Real Transfer](ch07_sim_to_real/README.md) |
| 8 | [ROS 2 & System Integration](ch08_ros2/README.md) |
| 9 | [Physical Hardware (SO-101)](ch09_hardware/README.md) |
| 10 | [Capstone Projects](ch10_capstone/README.md) |

---

## Chapter 1 — MuJoCo Fundamentals

**Prerequisites:** Python, basic physics intuition.

**Skip if you can answer:**
1. How do you read end-effector position in world space from a loaded MuJoCo model?
2. What is the difference between `model` and `data`?
3. You set `data.ctrl[0] = 1.57`. What happens?

**Projects**
- **1A** — Load a real robot, read joint states and body poses in two configurations
- **1B** — Camera-to-world transform: localize an object using wrist body transforms

---

## Chapter 2 — Control & Gymnasium

**Prerequisites:** Chapter 1.

**Skip if you can answer:**
1. What is the difference between a `motor` and `position` actuator?
2. Your PD controller oscillates. Which gain do you increase?
3. What does `env.step(action)` return?

**Install:** `pip install gymnasium`

**Projects**
- **2A** — PD controller: simulate and plot four kp/kd combinations
- **2B** — Hold a target pose on the Franka Panda with a PD controller
- **2C** — Wrap a 2-DOF reach task as a Gymnasium environment

---

## Chapter 3 — Kinematics & Motion Planning

**Prerequisites:** Chapters 1–2.

**Skip if you can answer:**
1. You want the end-effector to move 2 cm in +X. How do you compute the required joint velocity change?
2. What is a kinematic singularity, and what breaks when you're near one?

**Install:** `pip install pink pin robot_descriptions`

**Projects**
- **3A** — IK solver: reach any 3D target using Pink
- **3B** — Real-time target tracking: arm follows a circle trajectory
- **3C** — Pick trajectory: above → grasp → lift → place
- **3D** — Singularity detection: visualize manipulability vs. joint angle

---

## Chapter 4 — Reinforcement Learning (Applied)

**Prerequisites:** Chapters 1–3, basic understanding of neural networks and gradient descent.

**Skip if you can answer:**
1. What is the difference between a policy, a value function, and a reward?
2. What is the exploration-exploitation tradeoff?

**Install:** `pip install stable-baselines3[extra] gymnasium-robotics`

**Projects**
- **4A** — Explore FetchReach-v4: understand obs/action spaces before training
- **4B** — Train SAC with and without HER; compare learning curves
- **4C** — Reward design ablation: sparse vs. dense vs. HER on your Ch.2 env
- **4D** — Curriculum learning: success-gated target distance stages

---

## Chapter 5 — Imitation Learning ← most important

**Prerequisites:** Chapters 1–3. GPU strongly recommended (8+ GB VRAM).

**Skip if you can answer:**
1. What is distributional shift, and why does it make behavioral cloning fail?
2. What problem does ACT's action chunking solve?

**Install:**
```bash
git clone https://github.com/huggingface/lerobot && cd lerobot
pip install -e ".[simulation]"
```

**Projects**
- **5A** — Collect 50 demonstrations in gym_pusht using a scripted oracle
- **5B** — Inspect dataset: visualize trajectories, check action distributions
- **5C** — Train ACT; evaluate success rate over 50 trials
- **5D** — Train Diffusion Policy; compare with ACT on same data
- **5E** — Data scaling: train on 10/25/50/100/200 demos, plot the curve
- **5F** — Failure analysis: cluster failures by type, fix the dominant one

---

## Chapter 6 — Vision-Language-Action Models

**Prerequisites:** Chapter 5. GPU 16+ GB for fine-tuning (Colab A100 works).

**Skip if you can answer:**
1. What does a VLA take as input and produce as output?
2. Why fine-tune a pretrained VLA rather than train ACT from scratch?

**Projects**
- **6A** — Run SmolVLA inference in sim; test different language commands
- **6B** — Probe language conditioning: same env, different phrasings
- **6C** — Fine-tune SmolVLA on a custom task; compare zero-shot vs. fine-tuned
- **6D** — Data efficiency: how many demos does fine-tuning need vs. ACT from scratch?

---

## Chapter 7 — Sim-to-Real Transfer

**Prerequisites:** Chapters 2–5 and a trained policy to stress-test.

**Skip if you can answer:**
1. What is the reality gap, and what are its two main components?
2. What does domain randomization do, and what's the tradeoff?

**Projects**
- **7A** — Physics DR: randomize mass, friction, damping; measure success on unseen params
- **7B** — Robust vs. non-robust: quantify what DR gains and costs
- **7C** — Visual DR: random textures, lighting, image augmentation
- **7D** — Robustness report: sweep a parameter grid, identify brittle axes

---

## Chapter 8 — ROS 2 & System Integration

**Prerequisites:** Chapters 1–3. Ubuntu 24.04 or Docker on Mac.

**Skip if you can answer:**
1. What is the difference between a ROS 2 topic, service, and action?
2. What does `ros2 topic hz` tell you?

**Install (Ubuntu):** `sudo apt install ros-jazzy-desktop ros-jazzy-moveit`
**Install (macOS):** `docker pull osrf/ros:jazzy-desktop`

**Projects**
- **8A** — Publisher/subscriber: joint states at 100 Hz, FK on the subscriber side
- **8B** — IK service: wrap Pink IK as a ROS 2 service
- **8C** — MuJoCo ↔ ROS 2 bridge: sim publishes joint states, receives commands
- **8D** — Visualize in RViz2: live TF tree, camera feed, robot model

---

## Chapter 9 — Physical Hardware

**Prerequisites:** Chapter 5 (you'll deploy real policies). Chapter 8 recommended.

**Skip if you can answer:**
1. What is backlash in a servo, and how does it affect policy performance?
2. Have you assembled the SO-101 and verified all joints move?

**Hardware:**
| Option | Cost |
|--------|------|
| SO-101 (recommended) | ~$250 |
| + USB camera | ~$80 |
| + LED lighting panel | ~$40 |

**Install:** `pip install -e ".[feetech]"` (inside lerobot directory)

**Projects**
- **9A** — Assemble, connect, teleoperate SO-101 leader/follower
- **9B** — Motor calibration; verify workspace limits
- **9C** — Collect 100 real pick-and-place demonstrations
- **9D** — Train ACT on real data; deploy and run 20 trials
- **9E** — Failure analysis: categorize, collect targeted demos, retrain

---

## Chapter 10 — Capstone Projects

**Prerequisites:** Chapters 1–7 minimum. Ch.9 for Capstones A and C.

**Skip if you can answer:**
1. Can you trace the full data flow from camera image to joint torque in your system?
2. What are the three most common failure modes you've hit across your projects?

**Capstone A — Open-Vocabulary Pick-and-Place**
SO-101 + RealSense D435 + GPU. Language instruction → Grounded SAM 2 detection → depth localization → IK + LeRobot execution.

**Capstone B — Sim-to-Real Transfer Study**
No real robot required. Train in Isaac Sim and MuJoCo, apply DR, quantify the transfer gap.

**Capstone C — Fine-tune a VLA for Your Robot**
SO-101 + GPU 16+ GB. 500 real demos across 5 task variations, fine-tune SmolVLA, compare to ACT.

**Capstone D — Bimanual Manipulation**
2× SO-101. Bimanual MuJoCo env, leader-follower teleoperation, ACT-bimanual training.

---

## Tools Reference

### Stack

| Library | Purpose | Install |
|---------|---------|---------|
| `mujoco` | Physics simulation | `pip install mujoco` |
| `gymnasium` | RL/IL environment interface | `pip install gymnasium` |
| `gymnasium-robotics` | FetchReach and other robot envs | `pip install gymnasium-robotics` |
| `stable-baselines3` | SAC, PPO, TQC | `pip install stable-baselines3[extra]` |
| `lerobot` | ACT, Diffusion Policy, SmolVLA | `git clone + pip install -e .` |
| `pink` + `pin` | Differential IK | `pip install pink pin` |

### VLA Models

| Model | Params | Use |
|-------|--------|-----|
| SmolVLA | 450M | Fine-tuning experiments |
| OpenVLA | 7B | Multi-task research |
| π0 / π0.5 | Large | State-of-art dexterous manipulation |

### Key Papers

1. [ACT](https://arxiv.org/abs/2304.13705) — Action Chunking with Transformers
2. [Diffusion Policy](https://arxiv.org/abs/2303.04137)
3. [SmolVLA](https://huggingface.co/blog/smolvla)
4. [OpenVLA](https://arxiv.org/abs/2406.09246)
5. [π0](https://arxiv.org/abs/2410.24164)
6. [Open X-Embodiment](https://arxiv.org/abs/2310.08864)
7. [Domain Randomization](https://arxiv.org/abs/1703.06907)
8. [HER](https://arxiv.org/abs/1707.01495)

---

## Schedule

| Week | Chapters |
|------|---------|
| 1 | Ch.1–3 (sim, control, IK) |
| 2 | Ch.4–5 (RL, imitation learning) |
| 3 | Ch.6–7 (VLA, sim-to-real) |
| 4 | Ch.8–9 (ROS 2, hardware) |
| 5–8 | Ch.10 capstone |

---

## Getting Unstuck

**Sim is slow** — run headless (no viewer), or use Genesis for parallelized training.

**RL policy doesn't learn** — check reward scale (~1.0 mean), add HER, verify obs normalization.

**IL overfits** — more diverse demos, color jitter + random crop, try Diffusion Policy over ACT.

**Sim-to-real fails visually** — visual DR + aggressive augmentation during training. Fix lighting on the real robot.

**IK doesn't converge** — check joint limits in MJCF, add a posture task to stay near neutral.

**Real robot erratic** — calibration first, then camera latency, then action frequency mismatch.

---

## What's Not Covered

- Legged robots / whole-body control — different skill tree
- SLAM / navigation — not needed for manipulation
- ML theory derivations — apply before you derive
- Custom URDF/MJCF modeling — learn on demand from docs
