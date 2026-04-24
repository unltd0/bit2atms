# Robotics Learning Curriculum — Quick Navigation

Each chapter has its own full course material. Start from Ch.01 and work forward.

---

## Chapters

| # | Chapter | Hardware | Time | File |
|---|---------|----------|------|------|
| 1 | MuJoCo Fundamentals | Laptop only | 1–2 days | [ch01_transforms/README.md](ch01_transforms/README.md) |
| 2 | Control & Gymnasium | Laptop only | 2–3 days | [ch02_mujoco/README.md](ch02_mujoco/README.md) |
| 3 | Kinematics & Motion Planning | Laptop only | 3–4 days | [ch03_kinematics/README.md](ch03_kinematics/README.md) |
| 4 | Reinforcement Learning (Applied) | GPU helpful | 4–5 days | [ch04_rl/README.md](ch04_rl/README.md) |
| 5 | Imitation Learning (ACT + Diffusion) | GPU needed | 5–7 days | [ch05_imitation/README.md](ch05_imitation/README.md) |
| 6 | Vision-Language-Action Models | 16GB GPU | 4–5 days | [ch06_vla/README.md](ch06_vla/README.md) |
| 7 | Sim-to-Real Transfer | GPU helpful | 4–5 days | [ch07_sim_to_real/README.md](ch07_sim_to_real/README.md) |
| 8 | ROS 2 & System Integration | Docker/Linux | 3–4 days | [ch08_ros2/README.md](ch08_ros2/README.md) |
| 9 | Physical Hardware (SO-101) | ~$250 arm + camera | 1–2 weeks | [ch09_hardware/README.md](ch09_hardware/README.md) |
| 10 | Capstone Projects | Varies | 2–4 weeks | [ch10_capstone/README.md](ch10_capstone/README.md) |

---

## Full Curriculum Reference

The full curriculum plan (all chapters, requirements, outcomes, schedule) is in [README.md](README.md).

---

## What Each Chapter File Contains

Each `chXX/README.md` is a **self-sufficient course document** with:

- **Concept explanations** — the theory you actually need, explained clearly
- **Why it matters** — how it connects to the bigger picture
- **External resources** — specific papers, docs, and videos with context on what to read
- **Complete project code** — working Python files you can run immediately
- **Self-check questions** — with worked answers, to verify understanding before moving on
- **What NOT to do** — explicitly flags topics that waste time at this stage
- **What's next** — how this chapter's skills are used in the next

---

## Core Tools (Install Before Starting)

```bash
# Chapter 1 — MuJoCo basics
pip install mujoco numpy matplotlib

# Chapter 2 — simulation
pip install mujoco gymnasium gymnasium-robotics

# Chapter 3 — kinematics
pip install pink pin quadprog robot_descriptions

# Chapter 4 — RL
pip install stable-baselines3[extra]

# Chapter 5 — imitation learning
git clone https://github.com/huggingface/lerobot
cd lerobot && pip install -e ".[simulation]"

# Chapter 6 — VLA
# Already covered by lerobot install above
# SmolVLA: lerobot/smolvla_base on HuggingFace

# Chapter 8 — ROS 2
# Ubuntu: sudo apt install ros-jazzy-desktop
# macOS: docker pull osrf/ros:jazzy-desktop

# Chapter 9 — hardware
pip install -e ".[feetech]"  # in lerobot directory

# Chapter 10 — capstone A extras
pip install pyrealsense2 opencv-python
# Grounded SAM 2: https://github.com/IDEA-Research/Grounded-SAM-2
```

---

## Hardware Buying Guide

Chapters 1–7 need only your laptop. Chapter 8 needs Docker. Chapter 9 needs hardware.

If buying hardware, get in this order:
1. **SO-101 arm** (~$250) — core of Chapter 9
2. **USB camera or Logitech C930** (~$80) — needed for visual policies
3. **LED lighting panel** (~$40) — critical for consistent visual policies
4. **Intel RealSense D435** (~$200) — needed only for Capstone A depth-based picking

Total minimum for Chapter 9: ~$370
Total for Capstone A: ~$570

---

## Decisions: What This Curriculum Deliberately Excludes

| Topic | Why Excluded | When to Add |
|-------|-------------|-------------|
| ML theory / derivations | Apply before deriving | After completing the curriculum |
| DH parameter derivation | Libraries handle it; reading MJCF matters more | If you need to model a new robot |
| Custom URDF/MJCF modeling | Learn on demand | When you acquire new hardware |
| Whole-body control / legged robots | Different skill tree | Separate curriculum |
| SLAM / autonomous navigation | Not needed for manipulation | Nav2 tutorial when needed |
| RRT/PRM motion planning | MoveIt 2 handles this; IL avoids it entirely | If you need obstacle avoidance |
| Multi-agent RL | Not standard for manipulation yet | Bimanual capstone if desired |
| Training VLAs from scratch | Requires TPU-scale compute | Lab setting only |
| PyBullet | Legacy; replaced by MuJoCo | Never |
| ROS 1 | EOL May 2025 | Never |
| Octo VLA | Superseded by SmolVLA | For legacy code only |
| SO-100 arm | Deprecated; use SO-101 | Never |
