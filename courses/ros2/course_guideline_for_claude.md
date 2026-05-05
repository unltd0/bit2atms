# Course Guideline for Claude — ROS2

Use this when reviewing or generating content for the ROS2 course.

---

## Course Goal

After three chapters, ROS2 should feel like a known concept — not a mystery. The learner has run nodes, built a real map, and navigated a physical robot. They're not an expert; they know where to look and what to try.

**Chapter arc:**

| Ch | Role |
|----|------|
| 1 | Fundamentals — install, nodes, topics/services/actions, launch files, bags |
| 2 | Simulation — Gazebo, SLAM in sim, Nav2 autonomous navigation |
| 3 | Hardware — real TurtleBot, real SLAM, real Nav2 goal |

**Reviewing a chapter:** ask whether a S/W engineer with no robotics background could run every project and understand what they just did. That is the right lens — not ROS2 completeness.

---

## Target Audience

Python-literate software engineers with no robotics background. They know how to code, use terminals, and want to touch real things — not pass a certification.

Mac users are a primary audience — Docker is their path. Every chapter must include exact Docker commands where needed.

---

## Core Philosophy

Same as the VLA course:

**Project-driven.** Projects come first. Concepts introduced inline when needed, not in theory sections beforehand.

**Practical over complete.** Cover the useful 20%. If it can't be justified by "a S/W engineer building a robot thing needs this," cut it.

**Application before derivation.** Show what a tool does and how to use it. Only explain internals if not knowing them would block debugging.

**Relate to value.** Every concept needs to answer: *"Why does someone working with a robot need this?"*

---

## Tone

- Conversational, direct, no filler
- Define every term the first time it appears
- Short sentences. No "In this section we will explore..."
- Don't meta-comment on the course ("you don't need to understand X deeply")

---

## Chapter Structure (mandatory, in this order)

```
# Chapter N — Title

**Time:** X
**Hardware:** [tier label]
**Prerequisites:** [prior chapters or skills]

---

## What are we here for

2–4 paragraphs. What problem this chapter solves, what you'll build.
Include Mac Docker note if relevant.

**Skip if you can answer:**
1. ...

---

## Projects

| # | Project | What you build |
|---|---------|----------------|

---

## Project A — Title

**Problem:** 1–2 sentences.
**Approach:** 1–2 sentences.

Step-by-step with runnable commands and code.

---

## Self-Check

5 questions, answers always included inline.

---

## Common Mistakes

- **Mistake:** why it happens and how to fix it.

---

## Resources

1. [Title](url) — what to read and why.
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

- All code must be copy-paste-runnable
- Type hints on all function signatures
- Code block titles: `` ```python title filename.py ``
- File paths: `workspace/ros2/chXX/filename.py`
- **Depth markers** on every code block:
  - `🟢 **Run**` — just run it, understand inputs/outputs
  - `🟡 **Know**` — understand the API and structure
  - `🔴 **Work**` — modify it, experiment

For `🔴 **Work**` blocks: add a prose paragraph before the code describing the overall flow, then numbered walkthrough comments inside matching execution order (not line order).

---

## Images

Pull real images from official sources where they add genuine value — a screenshot of Gazebo, an RViz map view, the TF tree visualization. Don't add images just to have them.

Good sources:
- `emanual.robotis.com` — TurtleBot3 official docs, has screenshots for every step
- `navigation.ros.org` — Nav2 official docs with RViz screenshots
- `docs.ros.org` — ROS2 official docs

Format: standard Markdown `![alt text](url)`. Alt text should describe what's visible.

---

## Mac-specific rules

- Docker is the primary Mac path — include the `docker run` command at the start of each chapter
- Display forwarding (XQuartz + `xhost`) is required for Gazebo and RViz — explain it once in ch02, reference it in ch03
- Every terminal command that needs ROS2 must note that Mac users run it inside the Docker container

---

## Exclude

- ROS1 anything
- C++ nodes — Python only
- Custom `.msg` or `.srv` files — use built-in types
- Advanced DDS configuration (QoS profiles beyond basic, FastDDS tuning)
- microROS, ROS2 Control, MoveIt
- URDF authoring from scratch
- Exhaustive Nav2 parameter tuning
- Meta-commentary ("You don't need to understand X in detail")
