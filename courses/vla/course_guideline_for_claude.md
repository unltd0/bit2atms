# Course Guideline for Claude

Use this when reviewing or generating content for the VLA course.

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
  - `🟢 **Know** — just run it, see what happens.` (orientation code; learner doesn't need to modify it)
  - `🟡 **Feel** — read through and understand the flow.` (important pattern; learner should follow the logic)
  - `🔴 **Work** — make changes and observe the impact.` (core skill; learner must write or modify this)
  - One marker per code block. No legend section — the label is self-explanatory inline.

---

## Exclude

- ML theory derivations (backprop, loss landscapes, etc.)
- DH parameters, custom URDF/MJCF authoring
- Exhaustive API coverage — show the useful 20%, not everything
- Deprecated tools: PyBullet, ROS 1, Octo, SO-100, d3rlpy
- Training VLAs from scratch
- Meta-commentary about the course ("You don't need to...", "This chapter focuses on...")
