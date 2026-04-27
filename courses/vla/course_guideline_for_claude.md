# Course Guideline for Claude

Use this when reviewing or generating content for the VLA course.

---

## Course Goal

The destination: run a natural language command like `"pick up the red ball and place it in the bowl"` and have a **real robot arm execute it** — not by writing motion code, but by fine-tuning a Vision-Language-Action model on a small set of demonstrations and deploying it on hardware.

Every chapter exists to get the learner there without getting lost.

**Chapter arc:**

| Ch | Role |
|----|------|
| 1–2 | Sim foundations — MuJoCo, RL, the environment interface |
| 3 | **Core skill** — imitation learning (ACT, Diffusion Policy, failure analysis). Most important chapter. |
| 4 | VLA — fine-tune SmolVLA on a custom task; leverage what Ch3 built |
| 5 | Sim-to-real hardening — domain randomization, robustness |
| 6 | ROS 2 integration — connect policy to hardware |
| 7 | Real hardware — deploy on SO-101, iterate on real failures |
| 8 | Capstone — open-vocabulary pick-and-place and beyond |

**Reviewing a chapter:** ask whether it prepares the learner for Ch7's real-robot workflow. That is the right lens — not IL/RL/VLA completeness.

---

## Target Audience

Python-literate engineers or researchers who are **new to robotics and Physical AI**.
They know how to code, can read a paper, and want to build real things — not pass an exam.

Not the audience: ML researchers who want theory depth, or roboticists who already know ROS.

---

## Core Philosophy

**Project-driven learning.** Projects come first. Concepts are introduced inline, where they
are needed — not in theory sections before the work begins. The learner should encounter a
concept exactly when they need it to proceed.

**Practical over complete.** The goal is not to cover everything — it's to give the learner
enough real experience to build, break, and iterate on physical robot policies.

**Application before derivation.** Teach what a tool does and how to use it. Only explain
internals if not knowing them would block debugging or extension.

**Relate everything to value.** Every concept taught should answer: *"Why does a robot
manipulation engineer need this?"* If it can't, cut it.

**Projects are not exercises.** A project produces something real — a working sim, a trained
policy, a calibrated arm. "Build X from scratch to understand it" is a red flag. Use the
library; understand what it's doing and why.

**Latest tooling only.** Use what's current as of 2025–2026:
- MuJoCo (not PyBullet), LeRobot (not d3rlpy), SmolVLA (not Octo), ROS 2 Jazzy (not ROS 1), SO-101 (not SO-100)

---

## Tone

- Conversational, direct, no padding
- Define every term the first time it appears — never assume the reader knows jargon
- Explain the *why* before the *what* — don't just introduce a concept, say what gap it fills
- Short sentences. No filler. No "In this chapter, we will explore..."
- Don't leak guideline philosophy into content ("You don't need to derive X" is a red flag)

---

## Chapter Structure (mandatory, in this order)

```
# Chapter N — Title

**Time:** X–Y days
**Hardware:** [tier label]
**Prerequisites:** [prior chapters or skills]

---

## What are we here for

2–4 paragraphs: what problem this chapter solves, what you'll build, why it matters.
Include install/setup here if needed.

**Skip if you can answer:**
1. ...
2. ...
3. ...

---

## Projects

| # | Project | What you build |
|---|---------|---------------|
| A | Title   | one line      |

---

## Project A — Title

**Problem:** 1–2 sentences.
**Approach:** 1–2 sentences.

Step-by-step walkthrough with runnable code.
Introduce concepts inline as needed. Brief theory digressions OK — link out for depth.

---

## Project B — Title
...

---

## Self-Check

1. Question — **Answer:** answer
...5 questions total, answers always included.

---

## Common Mistakes

- **Mistake:** why it happens and how to fix it.

---

## Resources

1. [Title](url) — what to read and why it matters here.
```

---

## Hardware tier labels (use exactly)

- `Laptop only`
- `GPU helpful`
- `GPU 8 GB+`
- `GPU 16 GB+`
- `Physical robot`

---

## Code rules

- All code must be copy-paste-runnable — no pseudocode, no stubs
- Type hints on all function signatures
- Code block titles: use `` ```python title `` syntax (e.g. `` ```python read_robot_state.py ``)
- Error messages must include a troubleshooting hint
- Check `torch.cuda.is_available()` wherever GPU is relevant
- File paths: `workspace/vla/chXX/filename.py`
- **Depth markers:** tag every code block with one of three markers on the line immediately before the fence:
  - `🟢 **Run**` — just run it, glance the code, understand inputs and outputs. Don't dwell.
  - `🟡 **Know**` — know the API and structure, follow the flow. No need to deep-dive every line.
  - `🔴 **Work**` — modify it, experiment, get hands-on feel.
  - One marker per code block. Write the description contextually — don't copy-paste boilerplate. No legend section needed.

---

## Exclude

- ML theory derivations (backprop, loss landscapes, etc.)
- DH parameters, custom URDF/MJCF authoring
- Exhaustive API coverage — show the useful 20%, not everything
- Deprecated tools: PyBullet, ROS 1, Octo, SO-100, d3rlpy
- Training VLAs from scratch
- Meta-commentary about the course ("You don't need to...", "This chapter focuses on...")
