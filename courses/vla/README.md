# Vision-Language-Action — Curriculum Guide

Go from zero to building real robot manipulation systems. Focus is on *applying* modern ML,
not deriving it.

**Who this is for:** Python-literate, basic ML intuition, no robotics background needed.
**Time:** 4–8 weeks at 2–4 hours/day. Chapters 1–5 are laptop-only.
**Hardware:** Ch.1–5 laptop only. Ch.6 needs Ubuntu/Docker. Ch.7 needs ~$370 in hardware.

---

## Environment Setup

Do this once before starting.

```bash
# Python 3.10–3.12 recommended
python3 -m venv bit2atms-env
source bit2atms-env/bin/activate   # macOS / Linux

# Ch.1 — MuJoCo & Robot Fundamentals
pip install mujoco numpy matplotlib scipy pink pin robot_descriptions quadprog
git clone https://github.com/google-deepmind/mujoco_menagerie workspace/ext/mujoco_menagerie

# Ch.2 — Reinforcement Learning (add when you reach Ch.2)
pip install stable-baselines3[extra] gymnasium gymnasium-robotics

# Ch.3 — Imitation Learning (add when you reach Ch.3)
# git clone https://github.com/huggingface/lerobot workspace/ext/lerobot && cd workspace/ext/lerobot && pip install -e ".[simulation]"
```

Each chapter's README also lists its installs at the top.

---

## Chapters

| # | Chapter | Time |
|---|---------|------|
| 1 | [MuJoCo & Robot Fundamentals](ch01_mujoco/README.md) | 2–3 days |
| 2 | [Reinforcement Learning](ch02_rl/README.md) | 3–5 days |
| 3 | [Imitation Learning](ch03_il/README.md) | 5–7 days |
| 4 | [Vision-Language-Action Models](ch04_vla/README.md) | 4–5 days |
| 5 | [Sim-to-Real Transfer](ch05_sim2real/README.md) | 4–5 days |
| 6 | [ROS 2 & System Integration](ch06_ros2/README.md) | 3–4 days |
| 7 | [Physical Hardware](ch07_hardware/README.md) | 1–2 weeks |
| 8 | [Capstone Projects](ch08_capstone/README.md) | 2–4 weeks |

---

## Chapter Summaries

### Chapter 1 — MuJoCo & Robot Fundamentals
Load a real robot, read its state, localize objects with camera transforms, write a PD
controller, and solve IK with Pink. These four skills are used in every subsequent chapter.

**Install:** `pip install mujoco pink pin robot_descriptions quadprog`

**Projects:** Load robot + read state · Camera-to-world transform · PD controller gains · IK solver

---

### Chapter 2 — Reinforcement Learning
Train SAC with HER on a robotic reach task. Explore reward shaping and curriculum learning.
RL intuition transfers to IL debugging and reward design in custom tasks.

**Install:** `pip install stable-baselines3[extra] gymnasium gymnasium-robotics`

**Projects:** Explore env · Train SAC+HER · Reward ablation · Curriculum learning

---

### Chapter 3 — Imitation Learning ← most important
Collect demonstrations, train ACT and Diffusion Policy, compare them, and do data scaling
and failure analysis. This is the core skill for robot manipulation.

**Install:**
```bash
git clone https://github.com/huggingface/lerobot workspace/ext/lerobot && cd workspace/ext/lerobot
pip install -e ".[simulation]"
```

**Projects:** Collect demos · Inspect dataset · Train ACT · Train Diffusion Policy · Data scaling · Failure analysis

---

### Chapter 4 — Vision-Language-Action Models
Run SmolVLA zero-shot, probe language conditioning, fine-tune on a custom task, and measure
data efficiency vs. ACT from scratch.

**Install:** `pip install -e ".[smolvla]"` (inside lerobot)

**Projects:** SmolVLA inference · Language conditioning probe · Fine-tune SmolVLA · Data efficiency comparison

---

### Chapter 5 — Sim-to-Real Transfer
Measure and close the reality gap using physics and visual domain randomization. Build a
robustness heatmap to identify brittle axes before real deployment.

**Projects:** Physics DR · Robust vs. non-robust · Visual DR · Robustness report

---

### Chapter 6 — ROS 2 & System Integration
Build the communication layer that connects policy, hardware, and visualization.

**Install (Ubuntu):** `sudo apt install ros-jazzy-desktop`
**Install (macOS):** `docker pull osrf/ros:jazzy-desktop`

**Projects:** Joint state pub/sub · IK service · MuJoCo↔ROS2 bridge · RViz2

---

### Chapter 7 — Physical Hardware
Deploy everything on a real SO-101 arm: assemble, calibrate, collect 100 real demos, train,
deploy, and iterate on failures.

**Hardware:** SO-101 (~$250) + camera (~$80) + lighting (~$40) = ~$370

**Projects:** Assemble + teleoperate · Calibrate · Collect demos · Train + deploy · Failure analysis

---

### Chapter 8 — Capstone Projects
Four options: open-vocabulary pick-and-place (VLA + perception), sim-to-real study
(no hardware), VLA fine-tuning at scale (500 real demos), or bimanual manipulation.

---

## Schedule

Time estimates per chapter are in the Chapters table above. This schedule assumes 2–4 hours/day.

| Week | Chapters | Approx. time |
|------|---------|-------------|
| 1 | Ch.1–2 (sim, RL) | 5–8 days |
| 2 | Ch.3 (imitation learning) | 5–7 days |
| 3 | Ch.4–5 (VLA, sim-to-real) | 8–10 days |
| 4 | Ch.6–7 (ROS 2, hardware setup) | 4–6 days |
| 5–8 | Ch.8 capstone | 2–4 weeks |

---

## Getting Unstuck

**Sim is slow** — run headless (no viewer), or use Genesis for parallelized training.

**RL policy doesn't learn** — check reward scale (~1.0 mean), add HER, verify obs normalization.

**IL overfits** — more diverse demos, color jitter + random crop, try Diffusion Policy over ACT.

**Sim-to-real fails visually** — visual DR + aggressive augmentation during training. Fix lighting on the real robot.

**IK doesn't converge** — check joint limits in MJCF, add a posture task to stay near neutral.

**Real robot erratic** — calibration first, then camera latency, then action frequency mismatch.

---

## Hardware Buying Guide

| Item | Where to buy | Cost |
|------|-------------|------|
| SO-101 arm kit | [The Robot Studio](https://www.therobotstudio.com/) | ~$250 |
| USB camera (Logitech C920) | Amazon | ~$80 |
| LED lighting panel | Amazon | ~$40 |
| RealSense D435 (Capstone A only) | Intel / Amazon | ~$200 |

---

## Tools Reference

| Library | Purpose | Install |
|---------|---------|---------|
| `mujoco` | Physics simulation | `pip install mujoco` |
| `gymnasium` | RL/IL environment interface | `pip install gymnasium` |
| `stable-baselines3` | SAC, PPO, TQC | `pip install stable-baselines3[extra]` |
| `lerobot` | ACT, Diffusion Policy, SmolVLA | `git clone + pip install -e .` |
| `pink` + `pin` | Differential IK | `pip install pink pin` |

---

## Key Papers

1. [ACT](https://arxiv.org/abs/2304.13705) — Action Chunking with Transformers
2. [Diffusion Policy](https://arxiv.org/abs/2303.04137)
3. [SmolVLA](https://huggingface.co/blog/smolvla)
4. [OpenVLA](https://arxiv.org/abs/2406.09246)
5. [π0](https://arxiv.org/abs/2410.24164)
6. [Open X-Embodiment](https://arxiv.org/abs/2310.08864)
7. [Domain Randomization](https://arxiv.org/abs/1703.06907)
8. [HER](https://arxiv.org/abs/1707.01495)

---

## What's Not Covered

- Legged robots / whole-body control — different skill tree
- SLAM / navigation — not needed for manipulation
- ML theory derivations — apply before you derive
- Custom URDF/MJCF modeling — learn on demand from docs
