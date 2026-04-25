# Student Review Loop — Iteration 1
**Date:** 2026-04-25
**Chapters reviewed:** ch01, ch02, ch03 (partial read of ch04–ch08 in prior session)

---

## STUDENT HAT — Pain Points While Following Along

### ch01 — MuJoCo & Robot Fundamentals

**Pain 1 — Install block is silent about where to run it**
`git clone ... workspace/ext/mujoco_menagerie` — there's no instruction saying "run
these commands from the repo root." A student who opens the chapter inside `courses/vla/ch01_mujoco/`
will clone menagerie into the wrong place and hit the assert immediately. The inline snippet
even says "Run from the repo root" but the install block doesn't.

**Pain 2 — Pink install version silence**
`pip install pink` installs the package named `pink` (unrelated). The correct package is
`pinocchio` and `pink` from PyPI is actually `pin`. The install block says `pinocchio` which
is correct, but there's no mention that `pip install pink` by itself would fail / install the
wrong thing. A student who just reads "pip install pink" and googles will find the wrong package.
*Wait — actually the install block says `pip install mujoco numpy matplotlib scipy pink pinocchio
robot_descriptions quadprog`. `pink` here IS the correct PyPI package name for the IK library
(it was renamed from `pin`). But this needs a check — is `pink` currently the correct PyPI name?*
**→ Need to verify: `pip install pink` vs `pip install pin` — which is current?**

**Pain 3 — Project B has no "run this script" instruction**
Projects A, C, D each say "run from the repo root" or give a clear script path. Project B
(`camera_to_world.py`) just shows the code fence with no explicit "how to run" cue. Students
guess and often run from the wrong directory.

**Pain 4 — Project D: Pink docs link is dead**
`https://jmirabel.github.io/pink/` — this may redirect or 404. The current Pink docs are at
`https://pink-robotics.readthedocs.io/en/latest/` (need to verify).
**→ Need to verify current Pink docs URL.**

**Pain 5 — No "expected output" for Project B**
Projects A, C, D all have "What to observe" that includes expected terminal output or a plot.
Project B only says "The same cup maps to different world positions" — no expected numbers,
no sanity check value is surfaced in the prose (the code has a sanity check but the README
doesn't tell you to run it or what you'll see).

**Pain 6 — `camera_to_world.py` is not shown in code — student doesn't know where to create it**
Project A and C say "The code:" with a live-fetched file. Project B also does this, but unlike
A/C the student has no model to follow for creating their own version. The file is fetched from
`courses/vla/ch01_mujoco/code/camera_to_world.py` — that exists. But there's a disconnect:
the README says "Approach: Read the wrist body's transform... apply it to cup position" as if
the student should build this, but then just shows the finished code. The project doesn't give
a clear "now you try" moment.

---

### ch02 — Reinforcement Learning

**Pain 7 — `gym.register_envs(gymnasium_robotics)` — not in the install block, not explained**
The code does `import gymnasium_robotics` then `gym.register_envs(gymnasium_robotics)`.
The install block is `pip install stable-baselines3[extra] gymnasium gymnasium-robotics`.
A student who reads the install block and then runs `explore_env.py` directly (without the
`register_envs` call) will get `NameNotFound`. But the call IS in the code — so it's fine
as long as they use the code. However: the README code is inline (not a runnable file in
`code/`), so students have to create `workspace/vla/ch02/explore_env.py` themselves.
**There are no instructions telling students to create the workspace files.**

**Pain 8 — Workspace path `workspace/vla/ch02/` is mentioned in code fence headers but never explained**
Every code fence says `python workspace/vla/ch02/explore_env.py` in the header but:
- There's no instruction to create `workspace/vla/ch02/`
- There's no instruction to copy or create the files
- Unlike ch01 which has a `code/` folder with actual files, ch02–ch08 just show inline code
- Student doesn't know: are these files to create? To download? Does the repo include them?

**Pain 9 — ch02 Project B `train_sac_her.py` takes 20–40 min on CPU**
The comment says "~5 min on GPU, ~20–40 min on CPU" but this is training TWO policies
sequentially. Total real time is 40–80 min on CPU. The chapter says "GPU helpful" but
students without GPUs will hit a wall here. No guidance on what to do if you don't have a GPU
(Colab link, reduced `TOTAL_STEPS`, etc.).

**Pain 10 — Project D curriculum: `CurriculumCallback` accesses `self.env` directly**
In SB3, `EvalCallback` and custom callbacks don't share the training env reference directly.
`CurriculumCallback(env)` stores the env, but SB3 may wrap it in a `VecEnv`. The callback
would then be updating `goal_range` on the unwrapped env while SB3 trains on the wrapped
version. **This is a subtle bug — needs verification.**

---

### ch03 — Imitation Learning

**Pain 11 — Install says `pip install -e ".[simulation]"` but `gym_pusht` is a separate package**
The LeRobot install with `[simulation]` may not include `gym_pusht` in current versions.
Students will hit `ModuleNotFoundError: No module named 'gym_pusht'`. They need
`pip install gym-pusht` separately. **→ Needs verification.**

**Pain 12 — `oracle_action` uses `obs["block_pos"]` and `obs["goal_pos"]`**
The `gym_pusht/PushT-v0` env with `obs_type="pixels_agent_pos"` returns:
`{"pixels": ..., "agent_pos": ...}` — there is NO `block_pos` or `goal_pos` key.
`oracle_action` will immediately KeyError. **This is a real bug.**

**Pain 13 — `LeRobotDataset.create()` `features` format for images**
The current LeRobot `features` dict for image observations uses `"dtype": "image"` which
may not be the current API. Recent LeRobot uses `VideoFrame` type descriptors.
**→ Needs verification against current LeRobot source.**

**Pain 14 — `dataset.finalize()` vs `dataset.consolidate()`**
We verified `finalize()` still exists in current LeRobot. OK.

**Pain 15 — `inspect_dataset.py` uses `dataset.episode_data_index["from"]` / `["to"]`**
This API may have changed. In recent LeRobot the episode index structure changed.
**→ Needs verification.**

**Pain 16 — `eval_policy.py` uses `policy.select_action()` with raw tensor inputs**
The current LeRobot ACTPolicy may expect preprocessed inputs via a `processor` object, not
raw tensors with manual `.permute(2,0,1).unsqueeze(0) / 255.0`. **→ Needs verification.**

**Pain 17 — Project D says "change import to DiffusionPolicy" but doesn't show how**
The single line "change policy path and import to `DiffusionPolicy`" is too vague for a
student who just trained their first model. No import path given, no eval code shown.

**Pain 18 — Project E `data_scaling.sh` uses bash `seq` with `$(())` — not portable**
`"[$(seq -s, 0 $((N-1)))]"` — the `seq` command and bash arithmetic works on Linux/macOS
but the quoting/expansion inside a Python argument may fail depending on the shell.
Student on Windows or zsh with different quoting will hit errors.

---

### ch04–ch08 — Not yet reviewed in student role. Defer to next iteration.

---

## AUTHOR HAT — Analysis & Decisions

### Clear fixes (do now):

**F1 — ch01: Add "from repo root" to the install block** (1 line change)
`# Run from repo root:` before the install commands.

**F2 — ch01: Add expected output snippet to Project B prose**
Tell students what to expect: "You'll see two lines like `Cup in world frame: [0.52, 0.08, 0.43]`."
Add the sanity check instruction: "Set cup_in_camera = [0, 0, 0] to verify — output should
match the hand's world position."

**F3 — ch01: Verify and fix Pink docs URL**
Check `https://pink-robotics.readthedocs.io` vs the current URL in README.

**F4 — ch02: Add workspace setup instruction**
Ch02 and all subsequent chapters need a one-liner like:
"Create your working files in `workspace/vla/ch02/` — this folder is your scratchpad and
is gitignored."

**F5 — ch02: Add Colab/reduced-steps fallback for no-GPU students**
In Project B, add: "No GPU? Reduce `TOTAL_STEPS = 50_000` and use Colab (free A100)
at colab.research.google.com."

**F6 — ch03: Fix `oracle_action` — `block_pos` / `goal_pos` KeyError**
`obs_type="pixels_agent_pos"` does not include block/goal positions. Need to use
`obs_type="state"` or `obs_type="pixels_agent_pos"` and get block pos from `env.unwrapped`.
**→ Verify gym_pusht observation keys before fixing.**

**F7 — ch03: Fix `gym_pusht` install**
Add `pip install gym-pusht` to the install block.

### Needs more information before fixing:

**W1 — ch02 curriculum callback env wrapping bug (Pain 10)**
Need to test whether SB3 wraps the env in VecEnv before calling `env.reset()`. If it does,
`CurriculumCallback.env` points to the wrong object. May need `model.env.envs[0]` or
`model.get_env().envs[0]`. Wait for next iteration to verify.

**W2 — ch03 `select_action` API (Pain 16)**
Current LeRobot ACTPolicy inference API may require a processor. This is a big potential
breakage. Need to check LeRobot `examples/` for current inference pattern. Wait for next iteration.

**W3 — ch03 `features` format and `episode_data_index` API (Pains 13, 15)**
These depend on exact LeRobot version. Need to check current `LeRobotDataset` source.
Wait for next iteration.

**W4 — Pink PyPI package name `pink` vs `pin` (Pain 2)**
Quick to verify but worth a dedicated check. Wait for next iteration with a pip lookup.

### Structural observation (no fix yet, capture for later):

**S1 — ch02–ch08 inline code vs ch01 live-fetched code creates inconsistency**
ch01 has actual runnable files. ch02+ have inline code that students must manually create.
There's no guidance on this workflow difference. Options:
  a) Add `code/` folders to ch02–ch08 (big work, high value)
  b) Add a sentence to each chapter: "Copy the code blocks below into `workspace/vla/chXX/`"
  c) Add a top-level "How to use this course" note once in the course README
Option (c) is cheapest and good enough for now. Do in next iteration.

**S2 — No "check your work" moment for Projects B/D in ch03**
Projects C, E, F all have eval scripts. Project B (inspect) and D (diffusion compare)
don't have a clear "you're done when you see X" signal. Low priority.

---

## Status

| Finding | Action | Status |
|---------|--------|--------|
| F1 ch01 install block missing "repo root" | Fix now | DONE |
| F2 ch01 Project B expected output | Fix now | DONE |
| F3 ch01 Pink docs URL | Verified dead → fixed to stephane-caron.github.io/pink/ | DONE |
| F3b ch01 `pink` PyPI name is wrong package | `pip install pink` = code formatter. Fixed to `pin-pink` | DONE |
| F4 ch02 workspace setup instructions | Fix now | DONE |
| F5 ch02 no-GPU fallback | Fix now | DONE |
| F6 ch03 oracle_action KeyError | Verified: pixels_agent_pos has no block_pos. Fixed via env.unwrapped body attributes | DONE |
| F7 ch03 gym_pusht install | Fixed: `[simulation]` → `[pusht]` | DONE |
| F8 ch04 workspace note + pusht extra | Added | DONE |
| W1 ch02 curriculum callback env wrapping | Resolved: SB3 wraps same object, no fix needed | RESOLVED |
| W2 ch03 select_action API / image normalization | Resolved: Common Mistakes entry added (loop 4) | RESOLVED |
| W3 ch03 features/episode_data_index API | Fixed in loop 2 commit | FIXED |
| S1 ch02–ch08 workspace setup prose | ch02/ch03/ch04 done, ch05–ch08 next iteration | PARTIAL |
| S2 ch03 no "done" signal for B/D | Low priority | BACKLOG |
