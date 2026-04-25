# Student Review Loop — Iteration 2
**Date:** 2026-04-25
**Focus:** Verify deferred items from loop 1; student walkthrough ch05–ch08

---

## DEFERRED ITEM RESOLUTION

**W1 — ch02 CurriculumCallback env wrapping**
VERDICT: Non-issue. SB3 wraps in DummyVecEnv([lambda: env]) which captures the same
Python object. CurriculumCallback.env IS the same object the VecEnv wraps. success_rate()
works correctly. No fix needed.

**W2 — ch03 select_action API**
VERDICT: Fine. ACTPolicy.select_action(batch: dict[str, Tensor]) still exists and takes
a dict of tensors. The manual permute/unsqueeze/div-255 in eval_policy.py is correct at
the Python level. However — the normalization (div 255.0) may be wrong if the policy
expects pre-normalized images via a dataset transform. This is a subtle issue but not a
crash — just potentially wrong values. Mark as low-priority note in Common Mistakes.

**W3 — ch03 episode_data_index API**
VERDICT: BROKEN. `dataset.episode_data_index` is gone from current LeRobot. The current
API uses `dataset.hf_dataset` (a HuggingFace Dataset) which has an `episode_index` column.
Episode lengths must now be computed as:
  `ep_lengths = dataset.hf_dataset.to_pandas().groupby("episode_index").size().tolist()`
Or simpler: use `dataset.meta.episodes` parquet data.
FIX NEEDED in inspect_dataset.py episode length section.

---

## STUDENT HAT — ch05–ch08 walkthrough

### ch05 — Sim-to-Real Transfer

**Pain 19 — No workspace setup note**
Same issue as ch02–ch04. No instruction to create `workspace/vla/ch05/`.

**Pain 20 — `robustness_sweep.py` imports `from physics_dr import` — no guidance on how**
Comment says "Run from workspace/vla/ch05/" but there's no instruction telling the student
to first copy `physics_dr.py` there. Students will get ImportError and not know why.

**Pain 21 — `visual_dr.py` takes a `policy` argument but the main block just tests augmentation**
The `test_robustness()` function takes a `policy` arg but the `__main__` block only tests
the augmentation pipeline on a dummy image. Student who tries to actually use
`test_robustness()` has no example of how to connect it to a trained policy from Project A.
The function is incomplete as a standalone demo.

**Pain 22 — `stable-baselines3` missing from ch05 install but needed**
Install block: `pip install mujoco numpy stable-baselines3 gymnasium matplotlib`
stable-baselines3 IS listed. Good. But `torchvision` is needed for `visual_dr.py` and
is NOT in the install block.

### ch06 — ROS 2

**Pain 23 — No workspace setup note**
No instruction to create `workspace/vla/ch06/`.

**Pain 24 — Docker mount path mismatch**
Docker command mounts `~/code/unltd/bit2atms/workspace` to `/workspace`.
Then it says `cd /workspace/vla/ch06`. Scripts use:
`FRANKA_XML = os.path.join(os.path.dirname(__file__), "../../../ext/mujoco_menagerie/...")`
From `/workspace/vla/ch06/`, `../../../ext/` = `/ext/` which doesn't exist.
The correct path from `/workspace/vla/ch06/` should be `../../ext/` (two levels up to
`/workspace/`, then `ext/`).
**This is a real path bug introduced in our fix.** We fixed for the repo's structure
(`courses/vla/ch06_ros2/` → 3 levels up to repo root → `workspace/ext/`) but the
Docker context has scripts at `workspace/vla/ch06/` → 2 levels up → `workspace/ext/`.

**Pain 25 — `ros-jazzy-moveit` install — moveit not needed for ch06 projects**
`sudo apt install ros-jazzy-desktop ros-jazzy-moveit` — moveit is a large dependency
(several hundred MB) not used in any of the 4 projects. Red herring that slows install.

**Pain 26 — Project B IK service: student can't run it without colcon build**
The note says this is a template, but there's no path to actually running it. Students
who try to `python ik_service.py` get `ImportError` on the commented-out service import
(if they uncomment it) or a node that sits idle. Need clearer "this requires a full
ROS 2 package — skip the service creation for now, just read the code" message.

### ch07 — Hardware

**Pain 27 — No workspace setup note**
No instruction to create `workspace/vla/ch07/`.

**Pain 28 — `lerobot/scripts/control_robot.py` script may not exist in current LeRobot**
Current LeRobot restructured scripts. `lerobot/scripts/control_robot.py` may be at a
different path. Needs verification.

**Pain 29 — `so101.yaml` config path**
`lerobot/configs/robot/so101.yaml` — config paths may have changed in restructured repo.

### ch08 — Capstone

**Pain 30 — No workspace setup note**
No instruction to create `workspace/vla/ch08/`.

**Pain 31 — `pyrealsense2` not in any install block**
Capstone A uses `import pyrealsense2 as rs` with no install instruction. The chapter
has no install block at all.

**Pain 32 — Capstone B references ch03 + ch05 but no cross-reference links**
"Train the same base policy (ACT on gym_pusht or a custom MuJoCo task)" — student
doesn't know which scripts from ch03/ch05 to reuse. No file references.

---

## AUTHOR HAT — Decisions

### Fix now:

**F9 — ch03 inspect_dataset.py: fix episode_data_index → hf_dataset groupby**
Replace the episode length loop with the current API.

**F10 — ch05: add workspace note + torchvision to install**

**F11 — ch06: fix Docker FRANKA_XML path bug**
Scripts at `workspace/vla/ch06/` need `../../ext/` not `../../../ext/`.
But scripts in `courses/vla/ch06_ros2/` (the README source) need `../../../ext/`.
The README shows these as inline code students copy to workspace. So the path in
the README should be `../../ext/` (for where students actually run them).
→ Fix all 5 FRANKA_XML paths in ch06 README to `../../ext/`.

**F12 — ch06: remove ros-jazzy-moveit from install (not needed)**

**F13 — ch06: add workspace note**

**F14 — ch07: add workspace note**

**F15 — ch08: add install block for Capstone A (pyrealsense2, Grounded SAM 2)**

**F16 — ch08: add workspace note**

### Deferred:

**W5 — ch07 control_robot.py path / so101.yaml path**
Need to verify current LeRobot script locations. Check next iteration.

**W6 — ch03 eval_policy.py image normalization correctness**
Low-priority. The div-255 may be wrong but won't crash. Capture in Common Mistakes.
Check next iteration.

**W7 — ch06 Project B: add clearer "this needs colcon build" guidance**
The note exists but could be stronger. Improve next iteration.
