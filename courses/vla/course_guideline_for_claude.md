# Course Guideline for Claude

Use this when reviewing or generating content for the VLA course.

---

## Target Audience

Python-literate engineers or researchers who are **new to robotics and Physical AI**.
They know how to code, can read a paper, and want to build real things — not pass an exam.

Not the audience: ML researchers who want theory depth, or roboticists who already know ROS.

---

## Core Philosophy

**Practical over complete.** The goal is not to cover everything — it's to give the learner
enough real experience to build, break, and iterate on physical robot policies.

**Application before derivation.** Teach what a tool does and how to use it. Only explain
internals if not knowing them would block debugging or extension.

**Relate everything to value.** Every concept taught should answer: *"Why does a robot
manipulation engineer need this?"* If it can't, cut it.

**Projects are not exercises.** A project should produce something the learner will actually
use — a working sim, a trained policy, a calibrated arm. "Build X from scratch to understand
it" is a red flag. Use the library; understand what it's doing and why.

**Latest tooling only.** Use what's current as of 2025–2026:
- MuJoCo (not PyBullet), LeRobot (not d3rlpy), SmolVLA (not Octo), ROS 2 Jazzy (not ROS 1), SO-101 (not SO-100)

---

## Tone

- Conversational, direct, no padding
- Explain the *why* before the *what* — don't just introduce a concept, say what gap it fills
- Be honest about what to skip and why: "You don't need to implement this; libraries handle it"
- Short sentences. No filler. No "In this chapter, we will explore..."

---

## Content Rules

**Include:**
- Working, runnable code — not pseudocode, not stubs
- Curated external resources with context on *what* to read (not just links)
- Explicit hardware and time requirements
- What to do when things break (failure modes matter)

**Exclude:**
- ML theory derivations (backprop, loss landscapes, etc.)
- DH parameters, custom URDF/MJCF authoring
- Exhaustive API coverage — show the useful 20%, not everything
- Deprecated tools: PyBullet, ROS 1, Octo, SO-100, d3rlpy
- Training VLAs from scratch (not practical without TPU-scale compute)

---

## What "Done" Looks Like for a Chapter

The learner can run real code, has a working artifact (a trained policy, a working sim, a
calibrated arm), and knows what to try next. They don't need to have memorized theory —
they need to have *done the thing*.
