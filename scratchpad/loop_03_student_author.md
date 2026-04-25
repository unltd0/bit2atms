# Loop 3 — Student + Author Review

## Student pass

### courses/vla/README.md
- `pip install pink pin` — installs isort wrapper, not the IK library. PAIN: silent breakage.
- `[simulation]` extra in three places — doesn't include gym_pusht in current lerobot.
- Tools reference table says `pink` not `pin-pink`.

### courses/vla/ch07_hardware/README.md
**Critical**: Every single CLI command is broken against current lerobot.
- `python lerobot/scripts/control_robot.py` no longer exists. Replaced by entry points.
- `--robot-path lerobot/configs/robot/so101.yaml` no longer exists. Replaced by `--robot.type=so101_follower` inline args.
- `--calibration-path` flag gone; calibration is auto-saved to `~/.cache/lerobot/calibration/`.
- `python lerobot/scripts/train.py` → `lerobot-train`
- `python lerobot/scripts/visualize_dataset.py` → `lerobot-dataset-viz`
- Motor detection snippet uses `lerobot.motors.feetech.FeetechMotorsBus` — this may still exist but no longer used directly by students.
- `check_workspace.py` uses `SOFollower` from `lerobot.robots.so_follower` — class is now `SO101Follower` from `lerobot.robots.so101_follower`.
- Eval is now done by running `lerobot-record` with `--policy.path` (not a separate eval command for hardware).

## Author decisions

### Fixed this loop
- courses/vla/README.md: `pink` → `pin-pink` in all three locations; `[simulation]` → `[pusht]`
- ch07: install extra `[feetech]` → `[hardware]` (the correct new extra)
- ch07: All CLI commands rewritten to use new entry points
  - `lerobot-teleoperate`, `lerobot-calibrate`, `lerobot-record`, `lerobot-train`, `lerobot-dataset-viz`
  - robot type: `so101` → `so101_follower`, leader: `so101_leader`
  - No more YAML config paths; all inline args
  - Calibration note: auto-saved to `~/.cache/lerobot/calibration/`
  - Deploy: `lerobot-record --policy.path=...` (hardware eval uses record script)
- ch07 `check_workspace.py`: updated to `SO101Follower` + `SO101FollowerConfig`

### Resolved this pass
- W5-a (`SO101FollowerConfig`): Added caveat in ch07 install block noting the dataclass name is version-dependent and students should verify against their installed `workspace/ext/lerobot`.
- W5-b (`lerobot-train` args): Added inline comment above the command pointing to `lerobot train --help`. Also added a general CLI note in the install block.
- W6 (ch03 image normalization): Added Common Mistakes entry noting that div-255 may conflict with policies expecting pre-normalized images via dataset transform.
- L2-W7 (ch06 colcon guidance): Strengthened Project B note to explicitly say "read the code and skip the build" for students who just want the pattern.

## Status table (all items)

| ID | Chapter | Issue | Status |
|----|---------|-------|--------|
| L1-1 | ch01 | `pip install pink` wrong package | Fixed loop 1 |
| L1-2 | ch01 | Pink docs URL dead | Fixed loop 1 |
| L1-3 | ch02 | No GPU fallback for training | Fixed loop 1 |
| L1-4 | ch03 | `[simulation]` extra wrong | Fixed loop 1 |
| L1-5 | ch03 | oracle KeyError on block_pos | Fixed loop 1 |
| L1-6 | ch03 | LeRobot module paths broken | Fixed loop 1 |
| L2-1 | ch03 | `episode_data_index` removed | Fixed loop 2 |
| L2-2 | ch03 | `save_episode(task=...)` removed | Fixed loop 2 |
| L2-3 | ch04 | SmolVLA import path broken | Fixed loop 2 |
| L2-4 | ch04 | `[smolvla]` missing pusht | Fixed loop 2 |
| L2-5 | ch05 | redundant mj_forward | Fixed loop 2 |
| L2-6 | ch05 | torchvision missing from install | Fixed loop 2 |
| L2-7 | ch06 | body("panda_hand") wrong | Fixed loop 2 |
| L2-8 | ch06 | FRANKA_XML path wrong for Docker | Fixed loop 2 |
| L2-9 | ch06 | ros-jazzy-moveit unused dep | Fixed loop 2 |
| L3-1 | README | pink/pin-pink wrong in 3 places | Fixed loop 3 |
| L3-2 | README | [simulation] → [pusht] | Fixed loop 3 |
| L3-3 | ch07 | All CLI commands broken (control_robot.py gone) | Fixed loop 3 |
| L3-4 | ch07 | Robot type so101 → so101_follower | Fixed loop 3 |
| L3-5 | ch07 | check_workspace.py import broken | Fixed loop 3 |
| W5-a | ch07 | SO101FollowerConfig dataclass name | Resolved: caveat added to install block |
| W5-b | ch07 | lerobot-train exact arg names | Resolved: inline comment + CLI note in install block |
| W6 | ch03 | image normalization in eval | Resolved: Common Mistakes entry added |
| L2-W7 | ch06 | colcon guidance for Project B | Resolved: stronger "skip if reading only" note |
| S1 | README | workspace workflow note | Deferred (minor — course-level note, low impact) |
