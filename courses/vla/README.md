# Robotics Learning Curriculum

**Goal:** Go from zero to building real robot manipulation systems — covering simulation, movement, manipulation, imitation learning, and sim-to-real transfer — with a focus on *applying* modern ML, not deriving it.

**Who this is for:** Someone with programming experience (Python), basic ML intuition, but no robotics background.

**Time estimate:** 4–8 weeks at 2–4 hours/day. Chapters 1–7 are laptop-only.

**Hardware cost:** Chapters 1–7 require only a laptop (GPU helpful for Ch.5+). Ch.8 is Docker-friendly on Mac. Ch.9 requires ~$250–$500 in hardware.

---

## Environment Setup

Do this once before starting Chapter 1.

```bash
# Create a virtual environment
python3 -m venv bit2atms-env

# Activate it
source bit2atms-env/bin/activate   # macOS / Linux
# bit2atms-env\Scripts\activate    # Windows

# Verify you're in the env
which python                       # should point inside bit2atms-env/
```

Keep the env active whenever you work through this curriculum. All `pip install` commands
in each chapter install into it. To deactivate: `deactivate`.

---

## Curriculum Map

```
Chapter 1  → Foundations (Python math, coordinate systems, rigid body transforms)
Chapter 2  → Simulation with MuJoCo
Chapter 3  → Robot Kinematics & Motion Planning
Chapter 4  → Reinforcement Learning for Robots (applied)
Chapter 5  → Imitation Learning (ACT, Diffusion Policy) ← most important
Chapter 6  → Vision + Language + Action (VLA Models)
Chapter 7  → Sim-to-Real Transfer
Chapter 8  → ROS 2 & System Integration
Chapter 9  → Physical Hardware (Low-Cost Robots)
Chapter 10 → Capstone: Full Manipulation Pipelines
```

---

## Chapter 1 — Foundations

**Time:** 2–3 days

---

### Requirements

**Knowledge Prerequisites**

You should be comfortable with:
- Python (functions, classes, NumPy basics)
- High-school linear algebra (vectors, matrix multiplication)
- Basic trigonometry (sin, cos, what an angle means)

**Knowledge Check — answer these before starting:**
1. What does multiplying two matrices represent geometrically? → [3Blue1Brown: Linear transformations (ep. 3)](https://www.youtube.com/watch?v=kYB8IZa5AuE)
2. What is the dot product of two unit vectors, and what does it tell you? → [3Blue1Brown: Dot products (ep. 9)](https://www.youtube.com/watch?v=LyGKycYT2v0)
3. What's the difference between a vector and a point in 3D space? → [3Blue1Brown: Vectors (ep. 1)](https://www.youtube.com/watch?v=fNk_zzaMoSs)
4. If I rotate a point 90° around the Z-axis, where does (1, 0, 0) end up? → [3Blue1Brown: Linear transformations (ep. 3)](https://www.youtube.com/watch?v=kYB8IZa5AuE)

Can't answer these? Watch [3Blue1Brown: Essence of Linear Algebra](https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab) episodes 1–5 (≈2 hours total) before starting.

**Hardware Requirements**

- Any laptop or desktop with Python 3.12+
- No GPU needed
- No special hardware

---

### What You Need to Know

- **Coordinate frames** — world frame vs. robot base frame vs. end-effector frame
- **Rigid body transforms** — rotation matrices (3×3), homogeneous transforms (4×4)
- **Quaternions** — how robots represent orientation without gimbal lock
- **SE(3)** — the mathematical space robots move in (3D position + 3D orientation)
- **Forward kinematics** — given joint angles, compute where the end-effector is

You don't need to derive proofs. You need to recognize and use these representations confidently.

---

### Read

- [Modern Robotics — Ch. 2 and 3 (free online)](https://hades.mech.northwestern.edu/index.php/Modern_Robotics) — configuration space and rigid body motion
- [3Blue1Brown: Essence of Linear Algebra](https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab) — episodes 1–5 if needed

---

### Build: Project 1A — Transforms from Scratch

Build a small Python library (no robotics imports) that:

1. Creates rotation matrices from Euler angles (roll, pitch, yaw)
2. Creates 4×4 homogeneous transforms (rotation + translation combined)
3. Chains transforms (multiply them to compose)
4. Converts between quaternions and rotation matrices
5. Visualizes a coordinate frame in matplotlib (3 colored arrows, one per axis)

**Why:** Every robotics library wraps these internally. Build them once and you'll never be confused by them again.

```
learning/ch01_transforms/
  transforms.py       # your math library
  visualize.py        # plot coordinate frames
  test_transforms.py  # sanity checks (rotate, chain, invert)
```

---

### Build: Project 1B — Animate a 2D Robot Arm

Using only matplotlib + your transform library:
1. Implement forward kinematics for a 3-link planar (2D) arm
2. Draw the arm as connected lines in matplotlib
3. Animate it sweeping through a range of joint angles
4. Add a target point; compute which joint angles get the end-effector closest

```
learning/ch01_transforms/
  arm_fk.py       # forward kinematics
  arm_animate.py  # animation
```

---

### Chapter 1 Outcome

After finishing this chapter you will:
- Understand and implement 3D coordinate transforms from scratch
- Know the difference between rotation matrices, Euler angles, and quaternions — and when each is used
- Have implemented forward kinematics for a planar arm without any library
- Be able to read and reason about 4×4 transform matrices in any robotics codebase

---

## Chapter 2 — Simulation with MuJoCo

**Time:** 3–5 days

---

### Requirements

**Knowledge Prerequisites**

- Completed Chapter 1 (transforms, FK)
- Python classes and inheritance
- Basic understanding of physics: forces, torques, friction

**Knowledge Check — answer these before starting:**
1. What is the difference between a joint and a body in a rigid body simulation? → [MuJoCo Overview (2 min read)](https://mujoco.readthedocs.io/en/stable/overview.html)
2. What does a torque do vs. a force? → [Khan Academy: Torque (5 min)](https://www.khanacademy.org/science/physics/torque-angular-momentum/torque-tutorial/v/introduction-to-torque)

**Hardware Requirements**

- Laptop or desktop, any OS
- GPU not required (MuJoCo runs on CPU efficiently)
- 4 GB RAM minimum

**Install:**
```bash
pip install mujoco gymnasium gymnasium-robotics
```

---

### What MuJoCo Is

MuJoCo (Multi-Joint dynamics with Contact) is the industry-standard physics simulator for robot learning. It is fast, numerically accurate for contact physics, and is used by DeepMind, Google, and most research labs. Free and open-source since 2022.

---

### Read

- [MuJoCo Getting Started](https://mujoco.readthedocs.io/en/stable/programming/index.html) — first 3 sections
- [MuJoCo MJCF XML Reference](https://mujoco.readthedocs.io/en/stable/XMLreference.html) — skim; you'll return to this constantly
- [Gymnasium Docs](https://gymnasium.farama.org/) — the interface all RL and IL frameworks expect

---

### Build: Project 2A — Your First MuJoCo Scene

Build an interactive scene:
1. A ground plane + a box that falls, bounces, and slides
2. Add a second object; observe collisions
3. Apply forces programmatically and observe dynamics
4. Read back contact forces between objects

```
learning/ch02_mujoco/
  01_basic_scene.xml    # your first MJCF model
  01_basic_scene.py     # load and simulate
  02_contacts.py        # detect and print contact forces
```

---

### Build: Project 2B — Load and Control a Robot Arm

Use the Franka Panda MJCF model (included in MuJoCo examples):
1. Load the arm in MuJoCo
2. Run position control: move each joint to a target angle
3. Implement a PD controller for smooth, damped motion
4. Read joint states: position, velocity, applied torque

```
learning/ch02_mujoco/
  03_robot_arm.py       # load Franka, visualize
  04_pd_controller.py   # smooth joint control
```

---

### Build: Project 2C — Gymnasium Environment Wrapper

Wrap your arm scene as a Gymnasium `Env`:
- `reset()` → randomize initial joint angles, return observation
- `step(action)` → apply joint torques, return (obs, reward, terminated, truncated, info)
- `observation_space` and `action_space` defined
- Simple reward: negative distance from end-effector to a target sphere

This is the interface all RL and imitation learning libraries expect. Getting this right matters for every future chapter.

```
learning/ch02_mujoco/
  05_gym_env.py       # custom Gym environment
  05_test_env.py      # run random policy to verify
```

---

### Chapter 2 Outcome

After finishing this chapter you will:
- Build and run physics scenes from MuJoCo XML (MJCF)
- Load real robot models and control them with position and torque commands
- Implement a basic PD controller
- Wrap any simulation as a Gymnasium environment — the universal interface for robot learning
- Understand how contact forces work in simulation

---

## Chapter 3 — Robot Kinematics & Motion Planning

**Time:** 3–4 days

---

### Requirements

**Knowledge Prerequisites**

- Chapters 1 and 2 complete
- Comfortable with matrix math, especially matrix inversion and the concept of rank
- Some calculus intuition (what a derivative is geometrically)

**Knowledge Check — answer these before starting:**
1. Given a 4×4 homogeneous transform, what does each part (rotation block, translation column) represent? → Chapter 1, Part 3
2. In your MuJoCo Gymnasium env from Chapter 2, what does `data.qpos` contain and what does `data.ctrl` do? → Chapter 2, Projects 2B and 2D

**Hardware Requirements**

- Any laptop, no GPU
- ~1 GB additional disk for Pinocchio

**Install:**
```bash
pip install pink pin  # Pink (IK) + Pinocchio (rigid body dynamics)
```

---

### What You Need to Know

- **Forward Kinematics (FK):** joint angles → end-effector pose
- **Inverse Kinematics (IK):** target end-effector pose → joint angles (may have multiple or no solutions)
- **Jacobian:** maps joint velocities to end-effector velocity; central to real-time control
- **Motion planning:** how to move from A to B without colliding with anything
- **Singularities:** configurations where the robot loses degrees of freedom

You will use a library (Pink) for IK, not implement it from scratch — but you need to understand what it's solving.

---

### Read

- [Modern Robotics — Ch. 4–6](https://hades.mech.northwestern.edu/index.php/Modern_Robotics) — FK, velocity kinematics, inverse kinematics
- [Pink docs and examples](https://github.com/stephane-caron/pink) — the standard differential IK library in 2025-2026
- [MuJoCo motion planning tutorial](https://mujoco.readthedocs.io/en/stable/programming/index.html)

---

### Build: Project 3A — IK Solver: Reach Any Target

Using Pink + MuJoCo with a Franka Panda:
1. Define a target end-effector position (3D point in space)
2. Solve IK using Pink's differential IK to find joint angles
3. Visualize the result in MuJoCo
4. Track a moving target (circle trajectory) in real time at 50 Hz

```
learning/ch03_kinematics/
  01_ik_solver.py             # IK with Pink
  02_trajectory_tracking.py   # real-time target following
```

---

### Build: Project 3B — Real-Time Target Tracking

Drive the arm to follow a moving target in real time:
1. Define a target that moves on a circle trajectory at 0.5 Hz
2. Run Pink IK at 50 Hz, update target each step
3. Plot tracking error over time
4. Tune: compare position-only vs. full pose (position + orientation) targets

```
learning/ch03_kinematics/
  03_realtime_tracking.py
```

---

### Build: Project 3C — Cartesian Control and Pick Trajectory

Implement operational space control and a full pick sequence:
1. Compute the Jacobian at each timestep
2. Map desired Cartesian velocity → joint velocity via pseudoinverse Jacobian
3. Move the end-effector in a straight line from A to B
4. Implement a pick trajectory: move above → descend → grasp → lift

```
learning/ch03_kinematics/
  04_cartesian_control.py
  05_pick_trajectory.py
```

---

### Build: Project 3D — Singularity Detection

1. Deliberately drive the arm toward a singularity
2. Detect near-singularity using the manipulability measure (det of J·Jᵀ)
3. Add a damped pseudoinverse to handle it gracefully
4. Visualize how the joint velocities blow up near singularities

```
learning/ch03_kinematics/
  06_singularity_demo.py
```

---

### Chapter 3 Outcome

After finishing this chapter you will:
- Move a simulated robot arm to any reachable 3D target using IK
- Understand the Jacobian and use it for real-time Cartesian control
- Implement smooth pick trajectories in Cartesian space
- Detect and handle kinematic singularities
- Have the motion control fundamentals needed to execute learned policies

---

## Chapter 4 — Reinforcement Learning for Robots (Applied)

**Time:** 4–5 days

---

### Requirements

**Knowledge Prerequisites**

- Chapters 1–3 complete (especially the Gymnasium env from Ch. 2)
- Understand what a neural network is and roughly how it learns (gradient descent)
- Know what a reward function is conceptually
- Basic familiarity with Python training loops

**Knowledge Check — answer these before starting:**
1. What is the difference between a policy, a value function, and a reward? → [Spinning Up: Key Concepts (10 min)](https://spinningup.openai.com/en/latest/spinningup/rl_intro.html)
2. What is the exploration-exploitation tradeoff? → [Spinning Up: Key Concepts (10 min)](https://spinningup.openai.com/en/latest/spinningup/rl_intro.html)
3. Does your Gymnasium env from Chapter 2 work correctly? Can you run a random policy through 100 episodes? → Chapter 2, Project 2D

If you can't answer 1 or 2, read [Spinning Up — Key Concepts](https://spinningup.openai.com/en/latest/spinningup/rl_intro.html) first (20 min). Reward design and sparse rewards are taught in this chapter — no prior knowledge needed.

**Hardware Requirements**

- Laptop with or without GPU (CPU training works, just slower)
- GPU (NVIDIA, 4 GB VRAM+) cuts training time from hours to minutes
- No special hardware

**Install:**
```bash
pip install stable-baselines3[extra] gymnasium-robotics
```

---

### Philosophy

You don't need to implement RL algorithms. You need to know:
- When RL is the right tool (short horizon, dense reward, easy to reset)
- How to design reward functions that actually work
- How to debug a policy that isn't learning

---

### Read

- [Spinning Up in Deep RL — Part 1](https://spinningup.openai.com/en/latest/spinningup/rl_intro.html) — key concepts only, not the math derivations
- [Stable Baselines 3 Quickstart](https://stable-baselines3.readthedocs.io/en/master/guide/quickstart.html)
- [HER paper abstract](https://arxiv.org/abs/1707.01495) — Hindsight Experience Replay, crucial for robotics

---

### Build: Project 4A — Explore the Environment

Use `FetchReach-v4` from gymnasium-robotics:
1. Run with a random policy to understand observations and actions
2. Print observation and action space shapes, sample a few transitions
3. Visualize: render the env and watch what random actions do
4. Confirm your Gymnasium install works before training anything

```
learning/ch04_rl/
  01_explore_env.py    # inspect obs/action spaces
```

---

### Build: Project 4B — Train SAC with HER on FetchReach

Train on FetchReach-v4 with sparse rewards:
1. Train SAC alone (no HER) — watch it fail to learn
2. Add HER — watch it succeed
3. Plot learning curves: success rate vs. timesteps for both
4. Evaluate: render the trained policy

```
learning/ch04_rl/
  02_train_sac_her.py
  03_evaluate.py
```

---

### Build: Project 4C — Reward Design Ablation

Take the Gymnasium env from Chapter 2 and study reward design:
1. Implement four reward modes: sparse, dense-distance, dense+action-penalty, HER
2. Train each for the same number of steps
3. Plot all four learning curves on the same graph
4. Write a short conclusion: which reward signal was most sample-efficient and why

```
learning/ch04_rl/
  04_reward_ablation.py
```

---

### Build: Project 4D — Curriculum Learning

Implement a simple success-gated curriculum:
- Stage 1: target 5 cm from start
- Stage 2: target 15 cm from start
- Stage 3: target anywhere in 30×30 cm workspace
- Auto-advance when success rate > 80% over last 100 episodes

```
learning/ch04_rl/
  05_curriculum.py
```

---

### Chapter 4 Outcome

After finishing this chapter you will:
- Train RL agents on robot tasks using SAC and PPO
- Design and debug reward functions (the most important practical RL skill)
- Apply Hindsight Experience Replay to tackle sparse rewards
- Implement a simple curriculum to solve harder tasks
- Know the limits of RL for robotics: when to use it vs. imitation learning

---

## Chapter 5 — Imitation Learning

**Time:** 5–7 days

**This is the most important chapter.** Modern robot manipulation in 2025-2026 is dominated by imitation learning — learning from human demonstrations rather than reward signals. ACT and Diffusion Policy are deployed in real labs worldwide.

---

### Requirements

**Knowledge Prerequisites**

- Chapters 1–3 complete; Chapter 4 helpful but not required
- Know what a Transformer architecture is conceptually (encoder, attention, decoder)
- Know what a training/validation split is and what overfitting means
- GPU is strongly recommended — CPU training is possible but very slow

**Knowledge Check — answer these before starting:**
1. What is overfitting, and what is the difference between training loss and validation loss? → [fast.ai: Overfitting (5 min)](https://www.fast.ai/posts/2017-11-13-validation-sets.html)
2. What is a Transformer at a conceptual level — what problem does attention solve? → [3Blue1Brown: Attention (22 min)](https://www.youtube.com/watch?v=eMlx5fFNoYc)
3. Does your LeRobot install work? Can you run `python -c "import lerobot; print(lerobot.__version__)"`? → Chapter 5 install instructions

Behavioral cloning, ACT, Diffusion Policy, and distributional shift are all taught inside this chapter — no prior knowledge of them required.

**Hardware Requirements**

- NVIDIA GPU with 8+ GB VRAM strongly recommended (RTX 3060 or better)
- 16+ GB RAM
- ACT trains in ~30 minutes on RTX 3060/4060 for small datasets
- Free Google Colab A100 works for experiments if no local GPU

**Install:**
```bash
git clone https://github.com/huggingface/lerobot
cd lerobot
pip install -e ".[simulation]"
```

Note: LeRobot requires Python 3.12+ and PyTorch 2.3+. As of v0.5.0 (2025-2026), it uses Transformers v5.

---

### What the Stack Is

**LeRobot (Hugging Face)** is the 2025-2026 standard for imitation learning. It implements:
- **ACT** (Action Chunking with Transformers) — fast to train, great for precise short-horizon tasks
- **Diffusion Policy** — better generalization, handles multimodal behavior (multiple valid ways to do a task)
- **VQ-BeT** — good for long-horizon tasks
- **Pi0-FAST** — new in v0.5.0, autoregressive VLA-style policy

---

### Read

- [ACT paper](https://arxiv.org/abs/2304.13705) — abstract + intro + results (~15 min)
- [Diffusion Policy paper](https://arxiv.org/abs/2303.04137) — same approach; focus on Figure 1 and results
- [LeRobot docs](https://huggingface.co/docs/lerobot/index)

---

### Build: Project 5A — Collect Demonstrations in gym_pusht

Using LeRobot's built-in simulation (`gym_pusht` or `gym_aloha`):
1. Understand the demonstration format: episodes of (observation, action) tuples
2. Collect 50 demonstrations using a scripted oracle policy
3. Save in LeRobot HuggingFace dataset format

```
learning/ch05_imitation/
  01_collect_demos.py
```

---

### Build: Project 5B — Inspect Your Dataset

1. Load your LeRobot dataset and print its structure
2. Visualize 5 episodes: plot end-effector trajectories
3. Plot action distributions: are they unimodal or multimodal?
4. Identify bad demonstrations and remove them

```
learning/ch05_imitation/
  02_inspect_dataset.py
```

---

### Build: Project 5C — Train ACT

1. Train ACT on your 50 demonstrations (~30 min on GPU)
2. Evaluate: run 50 trials, measure success rate
3. Visualize attention maps: what does the model focus on?

```
learning/ch05_imitation/
  03_train_act.py
  04_evaluate_act.py
```

---

### Build: Project 5D — Train Diffusion Policy and Compare

1. Train Diffusion Policy on the same dataset
2. Compare ACT vs. Diffusion Policy success rates
3. Test on a harder version: add noise to object positions
4. Write a short markdown comparing the two: when does each win?

Key insight to discover: Diffusion Policy handles multimodality better. ACT is faster and more precise on single-mode tasks.

```
learning/ch05_imitation/
  05_train_diffusion.py
  06_compare_policies.py
  07_analysis.md
```

---

### Build: Project 5E — Data Scaling Analysis

How much does data quantity matter?
1. Train ACT on 10, 25, 50, 100, 200 demonstrations
2. Plot success rate vs. demo count — find the knee of the curve
3. Repeat with Diffusion Policy — do they scale the same way?

```
learning/ch05_imitation/
  08_data_scaling.py
```

---

### Build: Project 5F — Understanding Why Policies Fail

Systematic failure analysis:
1. Run 100 evaluation trials and log every failure with its state
2. Cluster failures by type: wrong grasp, slip during lift, missed placement
3. Plot failure distribution: which failure mode dominates?
4. Propose and test one targeted fix (more demos near failure cases, or augmentation)

```
learning/ch05_imitation/
  09_failure_analysis.py
  10_failure_report.md
```

---

### Chapter 5 Outcome

After finishing this chapter you will:
- Collect, inspect, and manage robot demonstration datasets in LeRobot format
- Train ACT and Diffusion Policy from scratch on simulation environments
- Evaluate policies rigorously (success rate over many trials, not just visual inspection)
- Reason about data quality vs. quantity tradeoffs
- Know when to use ACT vs. Diffusion Policy
- Understand why imitation learning has largely replaced RL for manipulation

---

## Chapter 6 — Vision-Language-Action Models (VLA)

**Time:** 4–5 days

---

### Requirements

**Knowledge Prerequisites**

- Chapter 5 complete (imitation learning foundations)
- Know what a language model is and roughly how attention works
- Familiarity with HuggingFace Transformers library (loading models, tokenizers)
- Strong GPU required for fine-tuning; inference is lighter

**Knowledge Check — answer these before starting:**
1. Can you load a pretrained model from HuggingFace Hub and run inference? → [HuggingFace: Quick Tour (10 min)](https://huggingface.co/docs/transformers/quicktour)
2. What is a language model at a conceptual level — what does it take as input and produce as output? → [3Blue1Brown: GPT (27 min)](https://www.youtube.com/watch?v=wjZofJX0v4M)
3. Did you complete Chapter 5? Can you train ACT on a simulation dataset and evaluate it? → Chapter 5

VLAs, pretraining, language conditioning, and Open X-Embodiment are all explained inside this chapter.

**Hardware Requirements**

- For inference only (running pretrained): 8+ GB VRAM (RTX 3070+), or free Colab
- For fine-tuning SmolVLA (450M params): 16+ GB VRAM, or Colab A100 (free tier)
- For fine-tuning OpenVLA (7B params): A100 80GB recommended; use Colab paid tier or Lambda Labs

**Relevance note:** Octo (previously recommended as starting VLA) is no longer the go-to. Use **SmolVLA** (HuggingFace, 450M params, 2025) for fine-tuning experiments and **OpenVLA** for larger-scale work. Both integrate with LeRobot.

---

### What VLAs Are

VLAs combine:
- A **vision encoder** (processes camera images)
- A **language model** (understands instructions like "pick up the red cup")
- An **action head** (outputs robot joint commands)

You give them a language instruction + camera images → they output actions. This is the frontier of robot learning in 2025-2026.

**Current landscape (2025-2026):**
| Model | Params | Best For |
|-------|--------|----------|
| SmolVLA | 450M | Fine-tuning experiments, learning |
| OpenVLA | 7B | Research, multi-task generalization |
| π0 / π0.5 | Large | State-of-art dexterous manipulation |
| Gemini Robotics | Large | Google ecosystem, dexterous tasks |

---

### Read

- [SmolVLA blog post (HuggingFace)](https://huggingface.co/blog/smolvla) — the accessible starting point
- [OpenVLA paper](https://arxiv.org/abs/2406.09246) — intro + results (~20 min)
- [Open X-Embodiment](https://robotics-transformer-x.github.io/) — understand the pretraining data

---

### Build: Project 6A — Run SmolVLA Inference in Simulation

Using SmolVLA in a LeRobot simulation:
1. Load the pretrained checkpoint from HuggingFace
2. Run inference on a standard environment (gym_aloha)
3. Give different language commands and observe behavior
4. Test failure modes: nonsense commands, out-of-distribution objects

```
learning/ch06_vla/
  01_vla_inference.py
```

---

### Build: Project 6B — Probe Language Conditioning

Understand what language actually does inside the model:
1. Same environment, different command phrasings — does behavior change?
2. Test compositionality: "first pick the cube, then place it in the bowl"
3. Test object attributes: "the larger one", "the one on the left"
4. Document: what generalizes, what doesn't

```
learning/ch06_vla/
  02_language_experiments.py
  03_generalization_report.md
```

---

### Build: Project 6C — Fine-tune SmolVLA on a Custom Task

1. Record 100 demonstrations of a simple pick-place task (in sim)
2. Fine-tune SmolVLA on your dataset
3. Compare: zero-shot (pretrained) vs. fine-tuned success rate

```
learning/ch06_vla/
  04_finetune_smolvla.py
  05_evaluate_finetuned.py
```

---

### Build: Project 6D — Data Efficiency: How Many Demos Does Fine-tuning Need?

1. Fine-tune SmolVLA on 10, 25, 50, 100 demonstrations
2. Plot success rate vs. demo count
3. Compare to ACT trained from scratch on the same data
4. Conclusion: when does a pretrained VLA win over training from scratch?

```
learning/ch06_vla/
  06_data_efficiency.py
  07_vla_vs_act_comparison.md
```

---

### Chapter 6 Outcome

After finishing this chapter you will:
- Run and fine-tune a Vision-Language-Action model in simulation
- Understand how pretraining on large robot datasets (Open X-Embodiment) enables zero-shot generalization
- Know the tradeoffs between small VLAs (SmolVLA) and large ones (OpenVLA, π0)
- Have intuition for VLA failure modes: when language conditioning helps vs. confuses
- Understand when to use a VLA vs. a task-specific ACT/Diffusion Policy

---

## Chapter 7 — Sim-to-Real Transfer

**Time:** 4–5 days

---

### Requirements

**Knowledge Prerequisites**

- Chapters 2–5 complete
- Have a trained policy (from Ch. 4 or Ch. 5) to stress-test
- Understanding of what causes distribution shift

**Knowledge Check — answer these before starting:**
1. Do you have a trained policy from Chapter 4 or Chapter 5 that you can evaluate? → Chapter 4 Project 4B or Chapter 5 Project 5B
2. What is distributional shift? (one sentence) → Chapter 5 Part 1 — Behavioral Cloning section

Reality gap, domain randomization, system identification, and visual transfer are all taught inside this chapter.

**Hardware Requirements**

- Any laptop/desktop with GPU (training with randomization)
- No physical hardware needed for this chapter
- Real robot helpful for Project 7C but not required

---

### Core Techniques

1. **Domain Randomization (DR)** — randomize physics and visual parameters in sim so the policy must generalize
2. **System Identification** — measure the real robot's physical parameters and match them in sim
3. **Sim-to-Real Co-training** — mix small amounts of real data with sim data during training
4. **Visual Domain Adaptation** — train a perception module to make sim images look real

---

### Read

- [Domain Randomization for Transfer from Simulation to Real World](https://arxiv.org/abs/1703.06907) — the foundational paper; intro + results only
- [MuJoCo domain randomization docs](https://mujoco.readthedocs.io/en/stable/programming/simulation.html)
- [Sim-to-Real: Learning Agile Locomotion (2023)](https://arxiv.org/abs/2304.09805) — how quadrupeds are deployed; same principles apply to arms

---

### Build: Project 7A — Physics Domain Randomization

Take your RL or imitation learning policy and make it robust:
1. Randomize: object mass (±30%), friction (±50%), joint damping (±20%)
2. Randomize: object initial position (within 10 cm radius)
3. Train with DR on vs. off — compare success rate on held-out parameter combinations
4. Measure: what's the largest variation your policy can handle?

```
learning/ch07_sim_to_real/
  01_domain_rand.py         # wrapper that randomizes on reset()
  02_train_robust.py        # train with DR
  03_evaluate_transfer.py   # test on unseen param combos
```

---

### Build: Project 7B — Train Robust vs. Non-Robust Policies

Quantify the benefit of domain randomization:
1. Train policy A: no DR (fixed physics)
2. Train policy B: with physics DR (randomize mass, friction, damping)
3. Evaluate both on held-out parameter combinations never seen during training
4. Plot: how much does DR hurt in-distribution performance vs. gain out-of-distribution?

```
learning/ch07_sim_to_real/
  02_train_robust.py
  03_evaluate_transfer.py
```

---

### Build: Project 7C — Visual Domain Randomization

The hardest sim-to-real gap is visual:
1. Add random textures and lighting to your MuJoCo scene
2. Apply image augmentation (color jitter, noise, blur) during training
3. Train a visual policy with vs. without visual DR
4. Evaluate robustness to unseen visual conditions (different backgrounds, different lighting)

```
learning/ch07_sim_to_real/
  04_visual_dr.py
  05_image_augmentation.py
  06_visual_robustness.py
```

---

### Build: Project 7D — Robustness Analysis Report Tool

Build a script that automatically stress-tests a policy:
1. Define a grid of parameter variations (mass × friction × lighting)
2. Evaluate success rate at each grid point
3. Identify biggest failure modes (which parameters break the policy first)
4. Produce a structured report: "robust to X, brittle to Y"

This is what robotics engineering teams do before deploying.

```
learning/ch07_sim_to_real/
  07_robustness_grid.py
  08_transfer_report.py
```

---

### Chapter 7 Outcome

After finishing this chapter you will:
- Apply domain randomization to physics and visual parameters in MuJoCo
- Train policies that are meaningfully more robust to variation
- Quantify where a policy breaks (not just whether it works)
- Understand the visual reality gap and how image augmentation addresses it
- Have the analytical tools used by robotics teams before real-world deployment

---

## Chapter 8 — ROS 2 & System Integration

**Time:** 3–4 days

**Note:** ROS 1 (Noetic) reached end-of-life May 2025. ROS 2 Jazzy (2024 LTS, supported until 2029) is the current standard. ROS 2 Lyrical Luth arrives May 2026 as the next LTS. Use Jazzy now.

---

### Requirements

**Knowledge Prerequisites**

- Chapters 1–3 complete (robots, kinematics, simulation)
- Linux (Ubuntu 24.04) preferred; macOS users use Docker
- Comfortable with terminal, environment variables, building packages
- Basic understanding of publish/subscribe messaging patterns

**Knowledge Check — answer these before starting:**
1. Is ROS 2 Jazzy installed and working? Run: `ros2 run demo_nodes_py talker` in one terminal and `ros2 run demo_nodes_py listener` in another. Do you see messages flowing? → [ROS 2 Jazzy install guide](https://docs.ros.org/en/jazzy/Installation.html) (or Docker setup above)
2. Are you comfortable in a Linux terminal — environment variables, running background processes, `source`-ing files? → If not: [Linux command line basics (30 min)](https://ubuntu.com/tutorials/command-line-for-beginners)

Topics, services, nodes, DDS, launch files — all explained inside this chapter. Do the ROS 2 beginner CLI tutorials (listed in the Read section) as your first task.

**Hardware Requirements**

- Ubuntu 24.04 preferred; macOS with Docker works
- 8+ GB RAM
- No GPU needed
- No physical robot needed (MuJoCo bridge is the "hardware")

**Install (Ubuntu 24.04):**
```bash
sudo apt install ros-jazzy-desktop ros-jazzy-moveit
```

**Install (macOS via Docker):**
```bash
docker pull osrf/ros:jazzy-desktop
```

---

### What ROS 2 Is

ROS 2 is middleware — a communication backbone between robot components. It handles:
- Sensor data (cameras, force sensors, IMUs) as **topics**
- Commands and requests as **services** and **actions**
- Multi-node systems with lifecycle management and parameter servers

You don't control the robot through ROS 2 directly — you use it to connect your perception, planning, and control components.

---

### Read

- [ROS 2 Jazzy Tutorials — Beginner: CLI Tools](https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools.html) — do all 5
- [ROS 2 Concepts](https://docs.ros.org/en/jazzy/Concepts.html) — nodes, topics, services, actions
- [MoveIt 2 Quickstart](https://moveit.picknik.ai/main/doc/tutorials/quickstart_in_rviz/quickstart_in_rviz_tutorial.html)

---

### Build: Project 8A — Publisher and Subscriber Nodes

1. Write a publisher node: publishes joint states at 100 Hz as `sensor_msgs/JointState`
2. Write a subscriber node: receives them, computes and prints FK result
3. Add a launch file that starts both nodes together
4. Use `ros2 topic echo` and `ros2 topic hz` to inspect the data flow

```
learning/ch08_ros2/
  joint_publisher/     # ROS 2 package
  launch/              # launch files
```

---

### Build: Project 8B — IK Service

Write a ROS 2 service that wraps Pink IK:
1. Define a custom service: request is a 3D target position, response is joint angles
2. Implement the service using Pink + your Ch3 IK code
3. Call the service from a client node
4. Test: give it reachable and unreachable targets

```
learning/ch08_ros2/
  ik_service/          # ROS 2 package with Pink integration
```

---

### Build: Project 8C — MuJoCo ↔ ROS 2 Bridge

Connect your MuJoCo simulation to ROS 2:
1. MuJoCo node: runs physics, publishes joint states as `sensor_msgs/JointState`
2. Subscribe to `/cmd_joint_position` to receive control commands
3. Publish camera images as `sensor_msgs/Image`
4. Run a MoveIt 2 motion plan and execute it in MuJoCo

This makes your simulation behave like real hardware from ROS 2's perspective — the same code will later run on a physical robot.

```
learning/ch08_ros2/
  mujoco_bridge/       # MuJoCo ↔ ROS 2 bridge node
  moveit_demo/         # motion planning through MoveIt 2
```

---

### Build: Project 8D — Visualize in RViz2

1. Stream joint states from your MuJoCo bridge to RViz2
2. Load the Franka URDF in RViz2 and watch it move
3. Display the camera image feed as an overlay
4. Add a TF tree visualization: see all coordinate frames live

```
learning/ch08_ros2/
  rviz_config/         # RViz2 configuration file
  tf_publisher/        # TF frame broadcaster
```

---

### Chapter 8 Outcome

After finishing this chapter you will:
- Build multi-node ROS 2 systems with topics, services, and launch files
- Bridge a MuJoCo simulation to ROS 2 so it looks like real hardware
- Use MoveIt 2 for motion planning and execute plans in simulation
- Have the integration layer needed to deploy learned policies to physical robots
- Understand why ROS 2 replaced ROS 1 (DDS, lifecycle, security, real-time support)

---

## Chapter 9 — Physical Hardware

**Time:** 1–2 weeks (hardware-dependent)

---

### Requirements

**Knowledge Prerequisites**

- Chapter 5 complete (imitation learning) — you'll deploy these policies to real hardware
- Chapter 8 recommended (ROS 2) but not strictly required for LeRobot hardware
- Patience: real hardware has issues that simulation never does (loose cables, backlash, lighting)

**Knowledge Check — answer these before starting:**
1. What is backlash in a servo motor? → [Servo motor basics — backlash explained (5 min)](https://www.youtube.com/watch?v=1-7kHj9OIqI) *(hardware concept not covered in prior chapters)*
2. Did you complete Chapter 5 and successfully train an ACT policy in simulation? → Chapter 5 self-check
3. Have you read the SO-101 build guide before buying parts? → [SO-101 Build Guide](https://github.com/TheRobotStudio/SO-ARM100)

Why real policies fail, what lighting matters, leader-follower teleoperation, and motor calibration are all covered in detail inside this chapter.

**Hardware Requirements**

| Option | Cost | Notes |
|--------|------|-------|
| **SO-101** (recommended) | ~$250 | LeRobot native, best for 2025-2026. SO-100 is deprecated — get SO-101. |
| **Koch v1.1** | ~$300 | Dynamixel-based, LeRobot supported |
| **WidowX 250 S** | ~$3k | Standard research arm, OpenVLA/Octo support |
| **ALOHA 2** | ~$20k | Bimanual, state-of-art research platform |

Start with SO-101. It is designed specifically for LeRobot and is the current recommended entry point.

- Laptop with USB-C / USB-A ports
- USB camera (or webcam) for visual observations
- 16+ GB RAM, NVIDIA GPU 8+ GB VRAM for training

---

### Read

- [SO-101 Build Guide](https://github.com/TheRobotStudio/SO-ARM100) — assembly and wiring
- [LeRobot Hardware Docs](https://huggingface.co/docs/lerobot/robots) — calibration, teleoperation, data collection

---

### Build: Project 9A — Build and Verify Hardware

1. Assemble SO-101 (leader + follower configuration) following the build guide
2. Connect to your laptop; run LeRobot's hardware check script
3. Teleoperate: move the leader arm and have the follower mirror it
4. Verify all joints move correctly; identify any mechanical issues

```
learning/ch09_hardware/
  01_hardware_check.py
  02_teleop.py
```

---

### Build: Project 9B — Calibration

1. Run LeRobot's motor calibration procedure for each joint
2. Verify calibration: move to known positions and measure error
3. Test workspace limits: find the arm's reachable workspace
4. Document any joints with backlash or calibration issues

```
learning/ch09_hardware/
  03_calibration.py
```

---

### Build: Project 9C — Collect Demonstrations

1. Set up a repeatable scene: same table, consistent lighting, fixed camera position
2. Collect 100 demonstrations of a pick-and-place task (real object, real table)
3. Inspect the dataset: visualize trajectories, check for bad episodes
4. Remove failed or inconsistent demonstrations before training

```
learning/ch09_hardware/
  04_collect_data.py
  05_inspect_real_data.py
```

---

### Build: Project 9D — Train on Real Data and Deploy

1. Train ACT on your 100 real demonstrations (~45 min on GPU)
2. Deploy the policy to the real arm using LeRobot inference mode
3. Run 20 trials: count successes, note failure modes
4. Failure analysis: lighting? Object position variation? Speed?

```
learning/ch09_hardware/
  06_train_on_real.py
  07_deploy_policy.py
  08_evaluate_real.py
```

---

### Build: Project 9E — Failure Analysis and Iteration

Close the loop:
1. Categorize each failure from Project 9D: grasp failure, placement miss, drop
2. Collect 100 targeted demonstrations that specifically cover failure cases
3. Retrain and re-evaluate — measure improvement per failure category
4. Document in a structured failure report

```
learning/ch09_hardware/
  09_failure_analysis.py
  10_iteration_report.md
```

---

### Chapter 9 Outcome

After finishing this chapter you will:
- Build, calibrate, and teleoperate a physical robot arm
- Collect high-quality human demonstration datasets on real hardware
- Train a manipulation policy on real data and deploy it to a physical robot
- Run rigorous real-world evaluation (success rate over many trials)
- Do failure analysis: identify and fix real-world failure modes
- Understand the full loop: collect → train → deploy → evaluate → improve

---

## Chapter 10 — Capstone: Full Manipulation Pipelines

**Time:** 2–3 weeks (ongoing)

---

### Requirements

**Knowledge Prerequisites**

- Chapters 1–7 complete minimum
- Chapter 9 (real hardware) if doing Capstones A or C
- Choose based on your interests and available hardware

**Knowledge Check — answer these before starting:**
1. Can you trace the data flow from a camera image to a joint torque command in your system?
2. What are the three most common failure modes you've seen across your projects?
3. How would you debug a policy that succeeds 80% of the time but fails 20% in a specific configuration?
4. What is the difference between in-distribution and out-of-distribution failure?

**Hardware Requirements**

Depends on capstone chosen — see each option below.

---

### Capstone A — Open-Vocabulary Pick-and-Place

**Hardware:** SO-101 + RealSense D435 depth camera (~$150) + GPU 8+ GB

Build a system that takes any natural language instruction and executes manipulation:
1. **Perception:** Grounded SAM 2 for open-vocabulary object detection ("the red cup", "the box on the left")
2. **Localization:** RealSense D435 depth camera for 3D position from 2D detection
3. **Motion:** Pink (IK) + LeRobot trajectory execution
4. **Policy:** ACT or Diffusion Policy for grasp execution
5. **Integration:** full pipeline: say a phrase → robot picks the object

**Stack:** Grounded SAM 2 + OpenCV + Pink + LeRobot + optional ROS 2

---

### Capstone B — Rigorous Sim-to-Real Transfer Study

**Hardware:** Real robot optional; simulation-only is valid

Pick a manipulation task and systematically study transfer:
1. Train in Isaac Sim (photorealistic) and MuJoCo (fast)
2. Apply domain randomization in both
3. Deploy to real robot (or held-out sim parameter set)
4. Quantify the transfer gap with and without DR
5. Write a 3-page technical report: what closed the gap, what didn't

---

### Capstone C — Fine-tune a VLA for Your Robot

**Hardware:** SO-101 + GPU 16+ GB VRAM or Colab A100

1. Collect 500 real demonstrations across 5 task variations
2. Fine-tune SmolVLA on your data
3. Test zero-shot generalization: new objects, new positions, new instructions
4. Compare SmolVLA vs. ACT trained on the same data — when does pretraining help?
5. Document your findings with quantitative results

---

### Capstone D — Bimanual Manipulation (ALOHA-style)

**Hardware:** 2× SO-101 (~$500) or ALOHA 2 (~$20k)

Build a bimanual system in simulation + optionally real:
1. Set up a bimanual MuJoCo environment (ALOHA 2 model is open-source)
2. Design a task requiring two arms (fold a cloth, open a jar)
3. Collect bimanual demonstrations via leader-follower teleoperation
4. Train ACT-bimanual (LeRobot v0.5.0 supports this)
5. Evaluate arm coordination: do both arms behave consistently?

---

### Chapter 10 Outcome

After completing a capstone you will:
- Have a complete end-to-end robot system you built from scratch
- Have debugged real engineering problems (not tutorial problems)
- Have a portfolio artifact — a GitHub repo with results, a technical write-up, or a demo video
- Be ready to contribute to a robotics research lab or startup, or go deeper into any specialization

---

## Tools Reference

### Core Stack (2025-2026)

| Library | Purpose | Install |
|---------|---------|---------|
| `mujoco` | Physics simulation | `pip install mujoco` |
| `gymnasium` | RL environment interface | `pip install gymnasium` |
| `gymnasium-robotics` | Pre-built robot envs (FetchReach etc.) | `pip install gymnasium-robotics` |
| `stable-baselines3` | RL algorithms: SAC, PPO, TQC | `pip install stable-baselines3[extra]` |
| `lerobot` | Imitation learning: ACT, Diffusion Policy, SmolVLA | `git clone + pip install -e .` |
| `pink` | Differential IK solver | `pip install pink pin` |

### Simulators

| Simulator | Status | Use Case |
|-----------|--------|----------|
| **MuJoCo** | Active, standard | Primary learning simulator — fast, accurate |
| **Isaac Sim** | Active (NVIDIA) | GPU-parallelized, photorealistic, ROS 2 native |
| **Genesis** | Production-ready (2025) | Extreme parallelization (43M FPS on RTX 4090) |
| **PyBullet** | Legacy | Avoid for new work |

### VLA Models

| Model | Params | Status |
|-------|--------|--------|
| **SmolVLA** | 450M | Best for fine-tuning experiments (2025-2026) |
| **OpenVLA** | 7B | Research-grade multi-task generalization |
| **π0 / π0.5** | Large | State-of-art dexterous manipulation |
| **Octo** | 27M–93M | Lightweight but superseded by SmolVLA |

### Key Papers (in reading order)

1. [ACT: Action Chunking with Transformers](https://arxiv.org/abs/2304.13705)
2. [Diffusion Policy](https://arxiv.org/abs/2303.04137)
3. [SmolVLA (HuggingFace blog)](https://huggingface.co/blog/smolvla)
4. [OpenVLA](https://arxiv.org/abs/2406.09246)
5. [π0: A Vision-Language-Action Flow Model](https://arxiv.org/abs/2410.24164)
6. [Open X-Embodiment](https://arxiv.org/abs/2310.08864)
7. [Domain Randomization for Transfer](https://arxiv.org/abs/1703.06907)
8. [Hindsight Experience Replay](https://arxiv.org/abs/1707.01495)

---

## Suggested Weekly Schedule

### Week 1 — Foundations + Simulation
- Days 1–2: Chapter 1 (transforms, FK)
- Days 3–5: Chapter 2 (MuJoCo, Gymnasium wrapper)
- Days 6–7: Chapter 3 (IK, Cartesian control)

### Week 2 — Learning Algorithms
- Days 1–2: Chapter 4 (RL: SAC, reward shaping, HER)
- Days 3–5: Chapter 5A–5B (demos, train ACT)
- Days 6–7: Chapter 5C–5D (Diffusion Policy, augmentation)

### Week 3 — VLA + Sim-to-Real
- Days 1–3: Chapter 6 (SmolVLA inference + fine-tuning)
- Days 4–6: Chapter 7 (domain randomization, robustness analysis)
- Day 7: Review + buffer

### Week 4 — Integration + Hardware
- Days 1–3: Chapter 8 (ROS 2, MuJoCo bridge)
- Days 4–7: Chapter 9 (hardware setup, real data collection, ACT deployment)

### Weeks 5–8 — Capstone
- Choose one Capstone from Chapter 10
- Build end-to-end; document results; do a demo

---

## Getting Unstuck

**Simulation is slow:** Run MuJoCo headless (no viewer), reduce simulation timestep, or use Genesis for parallelized training.

**Policy doesn't learn (RL):** Check reward scale (~1.0 mean), add reward shaping, verify observation normalization, add HER.

**Imitation learning overfits:** Collect more diverse demos. Add color jitter + random crop. Switch from ACT to Diffusion Policy.

**Sim-to-real fails on vision:** Apply visual domain randomization and aggressive color jitter during training. Consistent lighting on the real robot also helps enormously.

**IK fails to converge:** Check joint limits in your MJCF. Add a nullspace task to keep the robot near a neutral pose.

**Real robot moves erratically:** Check motor calibration first. Then check observation lag (camera latency). Then check action frequency mismatch (policy trained at 30 Hz deployed at 50 Hz).

---

## What's Not Covered (Deliberately)

- **Legged robots / whole-body control** — different skill tree; start with arms
- **SLAM / autonomous navigation** — separate domain; not needed for manipulation
- **Grasp planning from scratch** — AnyGrasp or Contact-GraspNet when you need it
- **Custom URDF/MJCF modeling** — learnable on demand from docs
- **ML theory** — deliberately omitted; apply before you derive

When you finish Chapter 10, you'll have the foundation to go deep on any of these.
