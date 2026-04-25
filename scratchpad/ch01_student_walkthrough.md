# Ch01 Student Walkthrough — Fresh SWE, First Time in Physical AI

**Date:** April 25, 2026 at 4:09 PM  
**Student profile:** 3-yr backend SWE (Python, Node.js). Comfortable with git, pip, reading docs. Never touched ROS, MuJoCo, or robot kinematics before. No ML background beyond "I know what a neural network is."

---

## Install — 2 blockers

### B1: `pin-pink` vs `pink` confusion
```bash
pip install mujoco numpy matplotlib scipy pin-pink pinocchio robot_descriptions quadprog
```
**Blocker:** I Googled "pink python" and the first result is a code formatter. The package name `pin-pink` looks weird — why not just `pink`? There's no explanation of what each package does. As a student, I'd want to know:
- What does `mujoco` do? (physics sim)
- What does `pinocchio` do? (kinematics library)
- What does `pin-pink` do? (IK solver on top of pinocchio)
- What is `robot_descriptions`? (seems like a utility package — what for?)

**Fix:** Add one-liner descriptions next to each package in the install block. Or add a "What you're installing" preamble.

### B2: No version constraints, no known-good setup note
**Blocker:** `pinocchio` and `mujoco` are C-extension packages that can be finicky on macOS (Apple Silicon especially). There's zero guidance about Python version compatibility or known-working setups. If I hit a compilation error during pip install, I have no idea whether it's my machine, the wrong Python version, or a broken package.

**Fix:** Add "Tested with Python 3.10–3.12 on macOS/Ubuntu" note. Maybe link to a Colab option for people who can't get local installs working.

---

## Project A — Load a Robot, Read Its State

### B3: Run-path ambiguity
README says "Run from the repo root." But `read_robot_state.py` has:
```python
FRANKA_XML = os.path.join(os.path.dirname(__file__), "../../../../workspace/ext/mujoco_menagerie/franka_emika_panda/scene.xml")
```

The script is at `courses/vla/ch01_mujoco/code/read_robot_state.py`. Four levels up from there lands at repo root. So the path works **only if you run the script directly** (`python courses/vla/ch01_mujoco/code/read_robot_state.py`), not if you cd into the code dir and do `python read_robot_state.py`.

But Project B says "Run it: `python courses/vla/ch01_mujoco/code/camera_to_world.py` from the repo root." — this is consistent. Still, a student might try `cd courses/vla/ch01_mujoco/code && python read_robot_state.py` and get a confusing path error.

**Fix:** Either:
- Add explicit run instructions per project ("Run from repo root: `python courses/vla/ch01_mujoco/code/read_robot_state.py`")
- Or change the code to use an absolute/relative-from-repo-root path so it works regardless of cwd

### B4: "Franka Panda" — who?
The chapter never explains what a Franka Panda is. I see `franka_emika_panda` in paths and assume it's some model name, but I have no context. Is this a real robot? A simulation-only thing? Why this one?

**Fix:** One sentence: "Franka Panda — a 7-DOF collaborative arm by Franka Engineering, widely used in research."

### B5: Viewer requires display — no headless fallback guidance
The code has `mujoco.viewer.launch_passive()` which opens an interactive window. The README mentions "Headless / no display?" but only says to comment out the block. A student on a remote server or WSL without X11 forwarding would hit this immediately and might not know what's happening (silent crash? frozen terminal?).

**Fix:** Add a try/except around the viewer block in the code, with a clear message: "No display detected — skipping viewer. Printed output above is your deliverable."

### B6: `mj_forward()` vs `mj_step()` introduced late
The distinction between these two functions is critical but only explained in the Self-Check section (question 1). A student reading Project D later would encounter both and wonder why one uses `mj_forward()` and another uses `mj_step()`.

**Fix:** Add a small callout box after the first mention of `mj_forward()` explaining: "This recomputes poses without advancing physics. Use `mj_step()` when you want to simulate dynamics (gravity, collisions)."

---

## Project B — Camera-to-World Transform

### B7: No numpy reminder for matrix math
The 4×4 transform section explains the math beautifully but assumes familiarity with homogeneous coordinates and matrix multiplication (`T @ [px, py, pz, 1]`). For an SWE who hasn't done robotics, this is a conceptual leap. The code uses `np.append(p, 1.0)` and `(T @ ...)[:3]` — both numpy operations that work but the math intuition isn't built up enough for someone to modify it themselves.

**Fix:** Add one line: "If you're new to robotics transforms: think of this as 'apply the arm's rotation then shift by its position.' The 4×4 matrix bundles both into one multiplication."

### B8: Quaternion convention mismatch — no practical guidance
The note says MuJoCo is `[w, x, y, z]` and ROS 2 is `[x, y, z, w]`. But a student doesn't know when they'd actually need to convert. This feels like a "you'll regret this later" warning without context for *when* it matters in this chapter.

**Fix:** Either remove it (not relevant until Ch6 ROS) or add: "You won't need this conversion until Chapter 6, but keep it in mind — mixing conventions causes silent bugs."

---

## Project C — PD Controller

### B9: No explanation of what a DOF is
"2-DOF arm" appears without defining Degrees of Freedom. For someone new to robotics, this term is opaque.

**Fix:** First mention should say "2-DOF (degrees of freedom = 2 independently controllable joints)"

### B10: Output file location ambiguity
The script saves `pd_gains.png` but doesn't specify where. If run from repo root, it goes to repo root. If run from the code dir, it goes there. The README says "Open it" but doesn't say where to find it.

**Fix:** Either save to a known path like `outputs/pd_gains.png` or explicitly state: "This saves pd_gains.png in your current working directory."

### B11: Why not use the Franka?
The text says "We use a custom 2-DOF arm here, not the Franka" but doesn't explain *why* until later. A student might wonder why we're building a toy arm instead of using the real robot model they just loaded in Project A.

**Fix:** Move the explanation (about `motor` vs `position` actuators) earlier, right before introducing the custom XML.

---

## Project D — IK Solver

### B12: Loading the robot twice is confusing
```python
# Load into MuJoCo
mj_model = mujoco.MjModel.from_xml_path(FRANKA_XML)

# Load into Pink/Pinocchio for IK
robot = load_robot_description("panda_description")
```

Two different loading mechanisms, two different APIs. The README says "Pink uses Pinocchio internally" but doesn't explain why we can't just use MuJoCo's built-in kinematics. This is a fundamental architectural question that a curious student would ask.

**Fix:** Add one paragraph: "MuJoCo handles physics simulation; Pink/Pinocchio handle inverse kinematics optimization. They're separate libraries with different APIs, so we load the robot into both."

### B13: `configuration.q` — what type is this?
```python
mj_data.qpos[:7] = configuration.q[:7]
```
The code uses `configuration.q` but never explains that it's an array-like object from Pinocchio. A student might try to inspect it and get confused by the Pinocchio data structure.

**Fix:** Add a comment: "Pinocchio stores joint angles in `.q` (array-like, includes all DOFs including fingers)"

### B14: No explanation of what a singularity is
"IK diverging near singularities" appears in Common Mistakes but `singularity` is never defined. For someone new to robotics, this term means nothing.

**Fix:** Add: "A singularity is an arm configuration where it loses the ability to move in certain directions (like fully extending a straight arm). Near these points, IK math breaks down."

### B15: Passive viewer blocks terminal
`mujoco.viewer.launch_passive()` opens a window and blocks. There's no way to interact with the script while the viewer is open — you can't print debug info or type commands. The README doesn't mention this limitation.

**Fix:** Add note: "The viewer runs in the foreground. To add debug prints, run without the viewer block (comment it out) and use `mj_forward()` + manual prints."

---

## General / Structural Issues

### B16: No troubleshooting section
There's no "If things go wrong" section anywhere. Common issues a student would hit:
- `ModuleNotFoundError: No module named 'mujoco'` → forgot to install or wrong venv
- Path errors for FRANKA_XML → Menagerie not cloned or run from wrong directory
- Display errors with viewer → headless environment
- Import errors for pink/pinocchio → version incompatibility

**Fix:** Add a Troubleshooting section at the end of Chapter 1 (or per-project) covering these.

### B17: No "what comes next" bridge
After finishing all four projects, there's no summary connecting them to what they'll need in later chapters. A student might not realize that FK (Project A), transforms (B), control (C), and IK (D) are the four foundational skills used everywhere else.

**Fix:** Add a "What you just learned" summary box at the end:
- Project A → reading robot state (used in every chapter)
- Project B → camera-to-world transforms (used for perception pipelines)
- Project C → PD control (used when writing custom controllers)
- Project D → IK (used for motion planning and teleoperation)

### B18: Self-check answers are inline — might spoil before students try
The self-check questions have answers immediately below each one. A student who reads ahead would see the answers before attempting them.

**Fix:** Move answers to a collapsible section or at the very end of the chapter, or add "Try answering these before reading on" callout.

---

## Severity Summary

| ID | Blocker | Severity | Effort to fix |
|----|---------|----------|---------------|
| B1 | Package names unexplained | Medium | 2 min (add descriptions) |
| B2 | No Python/version guidance | Low-Medium | 5 min (add note) |
| **B3** | **Run-path ambiguity** | **High** | 10 min (explicit instructions or fix paths) |
| B4 | "Franka Panda" unexplained | Low | 1 line |
| **B5** | **No headless fallback in code** | **High** | 5 min (try/except around viewer) |
| **B6** | `mj_forward` vs `mj_step` explained too late | Medium-High | 3 min (add callout box) |
| B7 | Transform math conceptual leap | Low-Medium | 1-2 lines |
| B8 | Quaternion warning premature | Low | Remove or reword |
| **B9** | DOF undefined | Medium | 1 line |
| **B10** | Output file location ambiguous | Medium | 1 line |
| B11 | Why custom arm? (order) | Low-Medium | Move existing text earlier |
| **B12** | Two robot loads unexplained | Medium-High | 3-4 lines |
| B13 | `configuration.q` type unclear | Low | 1 comment |
| **B14** | Singularity undefined | Medium | 1 line |
| B15 | Passive viewer blocks terminal | Low-Medium | 2 lines |
| **B16** | No troubleshooting section | High | 15-20 min (add section) |
| **B17** | No "what comes next" bridge | Medium | 3-4 lines |
| B18 | Self-check answers spoil | Low-Medium | Move to end or collapsible |

### Top 5 fixes to make before students start using this:
1. **B3** — Explicit run-path instructions (or fix code paths)
2. **B5** — Add try/except around viewer with clear message
3. **B6** — Explain `mj_forward()` vs `mj_step()` when first introduced
4. **B16** — Add Troubleshooting section
5. **B17** — Add "What you just learned" summary connecting projects to later chapters

---

## Fixes Applied (April 25, 2026)

| ID | Fix | Where |
|----|-----|-------|
| B1 | Added one-liner descriptions for all 8 packages in install block | README.md install section |
| B3 | Fixed cwd-independent paths: `os.path.dirname(os.path.abspath(__file__))` | All 3 code files with FRANKA_XML |
| B4 | Added Franka Panda context box (7-DOF collaborative arm, Franka Engineering) | README.md coordinate frames |
| B6 | Added "Quick note on two key functions" callout for mj_forward vs mj_step | README.md MjModel/MjData section |
| B7 | Added transform intuition: "apply the arm's rotation then shift by its position" | README.md 4x4 transform matrix |
| B8 | Added timing note: quaternion conversion not needed until Ch6, but watch for silent bugs | README.md quaternions |
| B9 | Defined DOF inline: "degrees of freedom = independently controllable joints" | README.md Project C approach |
| B11 | Moved actuators section before PD control (right after custom arm explanation) | README.md Project C |
| B12 | Added "Why two separate loads?" subsection explaining MuJoCo vs Pink/Pinocchio roles | README.md Project D |
| B13 | Enhanced comment: "Pinocchio stores joint angles in .q (array-like, includes all DOFs including fingers)" | ik_solver.py |
| B14 | Expanded singularity definition with concrete example (fully extending a straight arm) | README.md IK section |
| B15 | Added debugging tip callout about viewer blocking terminal | README.md Project D code note |

### Still deferred (per user decision)
- **B2** — No Python/version guidance (ignored)
- **B5** — No headless fallback in code (ignored)
- **B10** — Output file location ambiguous (ignored)
- **B16** — No troubleshooting section (ignored, basic SWE skills)
- **B17** — No "what comes next" bridge (ignored)
- **B18** — Self-check answers spoil (ignored)
