# Vision-Language-Action — Curriculum Guide

## The goal

By the end of this course, you'll be able to run a command like:

```
"pick up the red ball and place it in the bowl"
```

— and have a real robot arm execute it. Not by writing motion code. Not by hard-coding waypoints. By fine-tuning a Vision-Language-Action model on a small set of demonstrations, then deploying it on hardware.

VLAs are models that take a camera image and a natural language instruction as input, and output robot joint actions directly. They're pretrained on large datasets of robot demonstrations and internet-scale vision-language data — so they already understand what "pick up" means, what a ball looks like, and roughly how arms move. Your job is to fine-tune them for your specific robot and task, evaluate whether they work, and debug when they don't.

That's the destination. The chapters before it build the foundations you'll need to get there without getting lost.

**Who this is for:** Python-literate, basic ML intuition, no robotics background needed.
**Time:** 3–5 weeks at 2–4 hours/day.
**Hardware:** Ch.1–4 laptop only. Ch.5 needs ~$620 in hardware (SO-101 arm + camera + lighting).

---

## Environment Setup

Do this once before starting.

```bash
# Python 3.10–3.12 recommended
python3 -m venv bit2atms-env
source bit2atms-env/bin/activate   # macOS / Linux

# Ch.1 — MuJoCo & Robot Fundamentals
pip install mujoco numpy matplotlib scipy pin-pink pinocchio robot_descriptions quadprog
git clone https://github.com/google-deepmind/mujoco_menagerie workspace/ext/mujoco_menagerie

# Ch.2 — Reinforcement Learning (add when you reach Ch.2)
pip install stable-baselines3[extra] gymnasium gymnasium-robotics

# Ch.3–4 — Imitation Learning + VLA (add when you reach Ch.3)
git clone https://github.com/huggingface/lerobot workspace/ext/lerobot
cd workspace/ext/lerobot && pip install -e ".[pusht,training,smolvla]"
```

Each chapter's README also lists its installs at the top.

## Workspace Setup

Your working files go in `workspace/vla/chXX/`. Run this once to create the folder structure with empty placeholder files for every chapter:

```bash
bash scripts/reset_workspace.sh
```

If `workspace/vla/` already has files, the script backs them up to `workspace_old/<timestamp>.zip` before resetting. The backup directory is gitignored — it never gets committed.

As you work through each chapter, copy the code from the reader into the corresponding file in your workspace. The reader shows the save path above each code block (e.g. `workspace/vla/ch01/read_robot_state.py`).

---

## Chapters

| # | Chapter | Tech | Computer | Robot | Time |
|---|---------|------|----------|-------|------|
| 1 | [MuJoCo & Robot Fundamentals](ch01_mujoco/README.md) | MuJoCo, Pinocchio, Pink | Laptop | Simulated SO-101 | 1 day |
| 2 | [Reinforcement Learning](ch02_rl/README.md) | SAC+HER, Gymnasium | Laptop (GPU helpful) | Simulated SO-101 | 1 day |
| 3 | [Imitation Learning](ch03_il/README.md) | ACT, LeRobot | Laptop GPU 8 GB+ or Colab | Simulated SO-101 (gym_pusht) | 1–2 days |
| 4 | [Vision-Language-Action Models](ch04_vla/README.md) | SmolVLA (450M), LeRobot | GPU 16 GB+ or Colab | Simulated SO-101 (MuJoCo) | 1–2 days |
| 5 | [Real Hardware](ch05_hardware/README.md) | SmolVLA, LeRobot, lerobot teleoperate | Laptop GPU 8 GB+ | Physical SO-101 (~$620) | 1–2 weeks |

---

## Chapter Summaries

### Chapter 1 — MuJoCo & Robot Fundamentals
Load a real robot, read its state, write a PD controller, and solve IK with Pink. These three projects build the foundations used in every subsequent chapter.

**Install:** `pip install mujoco pin-pink pinocchio robot_descriptions quadprog`

**Projects:** Load robot + read state · PD controller gains · IK solver

---

### Chapter 2 — Reinforcement Learning
Train SAC+HER on a robotic reach task. Understand the RL loop, sparse rewards, and HER. Closes with why RL hits its limits on real manipulation — and what that motivates in Chapter 3 and 4.

**Install:** `pip install stable-baselines3[extra] gymnasium gymnasium-robotics`

**Projects:** Train SAC+HER

---

### Chapter 3 — Imitation Learning
Collect demonstrations, train ACT, do failure analysis. Builds the collect → train → eval → debug loop used in every chapter after. Diffusion Policy covered as optional context for multimodal tasks.

**Install:**
```bash
git clone https://github.com/huggingface/lerobot workspace/ext/lerobot && cd workspace/ext/lerobot
pip install -e ".[pusht]"
```

**Projects:** Collect & inspect demos · Train ACT · Failure analysis

---

### Chapter 4 — Vision-Language-Action Models
Run SmolVLA zero-shot on a simulated SO-101 arm, probe how language conditioning affects joint trajectories, and fine-tune on a sim task to see the before/after difference. Exposes the domain gap: the checkpoint was trained on real photos, but the sim renders synthetic images — the arm moves but not accurately. That gap is what Ch.5 closes.

**Install:** `pip install -e ".[smolvla]"` (inside lerobot)

**Projects:** Interactive SmolVLA sim · Language conditioning probe · Fine-tune SmolVLA

---

### Chapter 5 — Real Hardware
Deploy everything on a real SO-101 arm: assemble, calibrate, collect 100 real demonstrations, fine-tune SmolVLA on your data, and iterate on failures. Closes the domain gap you saw in Ch.4 — the model now sees real images of your robot and your task.

Language robustness eval is included: test the same task with 3 different phrasings (10 trials each) to measure how brittle language conditioning is before and after fine-tuning.

**Hardware:** SO-101 arm kit (~$500) + USB camera (~$80) + LED lighting (~$40) = ~$620

**Install:** `pip install lerobot` (already installed from Ch.3–4)

**Projects:** Assemble + calibrate + teleoperate · Collect demos · Fine-tune SmolVLA + deploy · Language robustness check · Evaluate & iterate

---

## Schedule

Time estimates per chapter are in the Chapters table above. This schedule assumes 2–4 hours/day.

| Week | Chapters | What you build |
|------|---------|----------------|
| 1 | Ch.1–3 | Sim robot, IK, RL, IL pipeline |
| 2 | Ch.4 | SmolVLA in sim, language probe |
| 3–6 | Ch.5 | Real arm, fine-tuned SmolVLA, deploy |

---

## Getting Unstuck

**Sim is slow** — run headless (no viewer), or use Genesis for parallelized training.

**RL policy doesn't learn** — check reward scale (~1.0 mean), add HER, verify obs normalization.

**IL overfits** — more diverse demos, color jitter + random crop, try Diffusion Policy over ACT.

**Real robot erratic** — calibration first, then camera latency, then action frequency mismatch.

**SmolVLA arm barely moves in sim** — expected: domain gap from real photos → synthetic renders. Collect real demos (Ch.5) to fix it.

**Wrong camera key names** — `ValueError: All image features are missing`. Check `observation.images.up` and `observation.images.side`.

**Fine-tuning OOM** — reduce `--batch-size` or switch from MPS/CPU to a GPU with `--device cuda`.

---

## Hardware Buying Guide

| Item | Where to buy | Cost |
|------|-------------|------|
| SO-101 arm kit | [The Robot Studio](https://www.therobotstudio.com/) | ~$500 |
| USB camera (Logitech C920) | Amazon | ~$80 |
| LED lighting panel | Amazon | ~$40 |

**Total: ~$620**

> Domain randomization (varied lighting, backgrounds) and ROS 2 integration are covered as callout boxes in Ch.5 for learners who want to go further — neither requires extra hardware.

---

## Tools Reference

| Library | Purpose | Install |
|---------|---------|---------|
| `mujoco` | Physics simulation | `pip install mujoco` |
| `gymnasium` | RL/IL environment interface | `pip install gymnasium` |
| `stable-baselines3` | SAC, PPO, TQC | `pip install stable-baselines3[extra]` |
| `lerobot` | ACT, Diffusion Policy, SmolVLA | `git clone + pip install -e .` |
| `pin-pink` + `pinocchio` | Differential IK | `pip install pin-pink pinocchio` |

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

## Where to Go Next

After Ch.5 you have a working VLA pipeline on real hardware. Options for going further:

- **More tasks** — collect demos for a new task, fine-tune, deploy. The pipeline is the same.
- **Bimanual manipulation** — SO-101 supports two arms; LeRobot's dataset format handles multi-arm observations.
- **Open-vocabulary pick-and-place** — add a perception module (Grounding DINO + SAM) upstream of SmolVLA for zero-shot object detection.
- **Larger models** — π0, OpenVLA, or RoboVLMs trained on Open X-Embodiment scale better to novel tasks.
- **ROS 2 integration** — wrap your fine-tuned policy in a ROS 2 node for integration with navigation, perception, and multi-robot stacks.
- **Domain randomization** — vary lighting, backgrounds, and object positions in MuJoCo sim to reduce the real-to-sim gap before collecting real demos.

---

## What's Not Covered

- Legged robots / whole-body control — different skill tree
- SLAM / navigation — not needed for manipulation
- ML theory derivations — apply before you derive
- Custom URDF/MJCF modeling — learn on demand from docs
