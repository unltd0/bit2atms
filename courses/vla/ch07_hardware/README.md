# Chapter 7 — Physical Hardware

**Time:** 1–2 weeks
**Hardware:** 2× SO-101 arm kits (~$500 total) + USB camera + lighting
**Prerequisites:** Chapter 3 (trained a policy), Chapter 1 (MuJoCo basics)

---

## What are we here for

Everything in sim is perfect: no calibration drift, no cable drag, no lighting variation.
The real world is none of those things. This chapter takes everything you've built and
deploys it on a physical robot arm.

You'll use the **SO-101** — a low-cost, open-source 6-DOF arm by The Robot Studio. It's
the arm used in LeRobot's official hardware tutorials and the most practical entry point
in the $250–$500 range. You'll assemble it, calibrate it, collect real demonstrations,
train a policy, and deploy it.

**You need two arm kits.** LeRobot uses a leader/follower teleoperation setup: you hold
the leader arm and move it by hand; the follower arm mirrors your movements and records
the demonstration. One kit is not enough to collect data. Order two before starting.

**Hardware shopping list:**

| Item | Cost | Notes |
|------|------|-------|
| SO-101 arm kit (follower) | ~$250 | The robot arm that executes |
| SO-101 arm kit (leader) | ~$250 | The arm you hold to teleoperate — required for data collection |
| USB camera (e.g. Logitech C920) | ~$80 | |
| LED lighting panel | ~$40 | |
| **Total** | ~$620 | Leader arm is reusable across projects |

**Install:**
```bash
cd workspace/ext/lerobot
pip install -e ".[hardware]"   # includes feetech, cameras, and hardware scripts
```

**Working directory:** Create `workspace/vla/ch07/` for your scripts and data.

> **Note on LeRobot CLI commands below:** The entry points (`lerobot-teleoperate`,
> `lerobot-calibrate`, `lerobot-record`, `lerobot-train`) replace the old Python script
> paths. If any command fails with "command not found" or unexpected args, check your
> installed LeRobot version — the CLI interface may have shifted between releases.
> The dataclass name for SO-101 config (`SO101FollowerConfig`) is also subject to change
> in future versions; verify against `workspace/ext/lerobot` if it doesn't import.

**Skip if you can answer:**
1. What is backlash in a servo, and how does it affect policy performance?
2. You collect 50 demos but your policy fails consistently. What's the first thing to check?
3. Why does lighting matter for visual policies on real robots?
4. Your real policy succeeds 40% of the time. What's the most efficient way to get to 70%?

---

## Projects

| # | Project | What you build |
|---|---------|---------------|
| A | Assemble and Teleoperate | Assembled SO-101, verified all joints, teleoperated leader/follower |
| B | Calibration | Calibrated motors; documented workspace limits |
| C | Collect Demonstrations | 100 real pick-and-place demonstrations |
| D | Train and Deploy | ACT policy trained on real data; evaluated over 20 real trials |
| E | Failure Analysis and Iteration | Failure categories identified; targeted demos collected; retrained |

---

## Project A — Assemble and Teleoperate

**Problem:** Get the hardware working end-to-end before collecting any data.

**Approach:** Follow the SO-101 assembly guide, connect to LeRobot, verify all joints
move correctly, and run teleoperation with a leader arm.

### Why teleoperation first

Teleop confirms the hardware stack works before you invest in data collection. If a motor
is mis-configured or a cable is loose, you'll catch it here rather than after 50 failed
demos.

```bash workspace/vla/ch07/teleoperate.sh
# Find serial ports:
#   Linux:  ls /dev/ttyUSB*
#   macOS:  ls /dev/tty.usbmodem*
# Replace FOLLOWER_PORT and LEADER_PORT with your actual ports.
FOLLOWER_PORT=/dev/ttyUSB0
LEADER_PORT=/dev/ttyUSB1

# Run teleoperation (leader/follower)
# Note: teleop requires two arms — a leader arm (you hold) and a follower arm (the robot).
# The SO-101 kit ships as a follower; you need a second arm kit configured as the leader.
lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port=$FOLLOWER_PORT \
  --robot.id=my_follower \
  --teleop.type=so101_leader \
  --teleop.port=$LEADER_PORT \
  --teleop.id=my_leader \
  --display_data=true
```

**What to observe:** All 6 joints respond to leader arm movement without jerking or
stalling. If a joint doesn't move, check the motor ID in the config and the cable
connection.

### SO-101 assembly tips

- Tighten all screws but don't overtorque — the plastic housing cracks
- Run motor detection (`feetech_find_motors.py`) before assembly to verify IDs
- Confirm the zero position of each joint before closing the arm body

---

## Project B — Calibration

**Problem:** Servos have manufacturing tolerances — the "zero" position in software
doesn't match the physical zero. Without calibration, commanded positions are off.

**Approach:** Run LeRobot's calibration procedure for each joint. Record workspace limits
— positions where the arm hits itself or the table.

```bash workspace/vla/ch07/calibrate.sh
FOLLOWER_PORT=/dev/ttyUSB0
LEADER_PORT=/dev/ttyUSB1

# Calibrate follower arm
lerobot-calibrate \
  --robot.type=so101_follower \
  --robot.port=$FOLLOWER_PORT \
  --robot.id=my_follower

# Calibrate leader arm
lerobot-calibrate \
  --teleop.type=so101_leader \
  --teleop.port=$LEADER_PORT \
  --teleop.id=my_leader

# Calibration is saved automatically to ~/.cache/lerobot/calibration/
# Verify calibration — run teleop again; motion should be smooth and accurate:
lerobot-teleoperate \
  --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=my_follower \
  --teleop.type=so101_leader  --teleop.port=$LEADER_PORT  --teleop.id=my_leader \
  --display_data=true
```

```python workspace/vla/ch07/check_workspace.py
"""Move to a grid of joint angles and record which are reachable without collision.
The SO-101 has 6 DOF (joint_1 through joint_6).
Run after calibration to map the safe task space.
"""
import numpy as np
from lerobot.robots.so101_follower import SO101Follower, SO101FollowerConfig

def check_workspace(port: str, robot_id: str) -> None:
    config = SO101FollowerConfig(port=port, id=robot_id)
    robot  = SO101Follower(config)
    robot.connect()

    test_positions = np.linspace(-1.5, 1.5, 7)
    reachable = []

    for q1 in test_positions:
        for q2 in test_positions:
            try:
                robot.send_action({"joint_1": q1, "joint_2": q2,
                                   "joint_3": 0, "joint_4": 0,
                                   "joint_5": 0, "joint_6": 0})
                reachable.append((q1, q2, True))
            except Exception as e:
                reachable.append((q1, q2, False))
                print(f"  Unreachable: q1={q1:.1f} q2={q2:.1f}  ({e})")

    robot.disconnect()
    n_reach = sum(r[2] for r in reachable)
    print(f"\n{n_reach}/{len(reachable)} positions reachable")
    print("Record workspace limits — they define the valid task space for demonstrations.")

if __name__ == "__main__":
    check_workspace(port="/dev/ttyUSB0", robot_id="my_follower")
```

**What to observe:** The workspace limits tell you where to place objects for the task.
If limits are tighter than expected, check calibration offsets.

---

## Project C — Collect Demonstrations

**Problem:** Collect 100 high-quality real pick-and-place demonstrations.

**Approach:** Teleoperate the robot through the task using the leader arm. Focus on demo
quality: consistent start positions, smooth motions, high success rate.

### What makes a good demo

**Lighting:** Fixed, bright, shadow-free lighting is the single biggest factor for visual
policies. LED panels work well. Avoid windows — sunlight changes throughout the day.

**Consistency:** Same object placement, same camera angle, same arm start position.
Variation in the demonstrations is good; variation in the setup (accidental) is bad.

**Quality over quantity:** 50 clean demos beat 100 sloppy ones. Watch each demo before
saving — delete failed attempts immediately.

```bash workspace/vla/ch07/collect_demos.sh
FOLLOWER_PORT=/dev/ttyUSB0
LEADER_PORT=/dev/ttyUSB1
HF_USER=local   # or your HuggingFace username to push to hub

# Record 100 demonstrations
lerobot-record \
  --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=my_follower \
  --teleop.type=so101_leader  --teleop.port=$LEADER_PORT  --teleop.id=my_leader \
  --dataset.repo_id=$HF_USER/real_pickplace \
  --dataset.num_episodes=100 \
  --dataset.single_task="Pick and place the cube" \
  --display_data=true
```

**After each session:**
- Review demos: `lerobot-dataset-viz --repo-id local/real_pickplace`
- Delete any episodes where the arm missed or the object was out of position
- Log lighting and object setup photos — you'll need to replicate this for eval

---

## Project D — Train and Deploy

**Problem:** Train an ACT policy on your real data and evaluate it on the physical robot.

**Approach:** Train with LeRobot's training script, then run the policy on hardware and
count successes over 20 trials.

```bash workspace/vla/ch07/train_real.sh
cd workspace/ext/lerobot
# Note: exact arg names (e.g. --policy.type, --training.steps) may vary by LeRobot version.
# If these fail, check `lerobot train --help` in your installed version.
lerobot-train \
  --policy.type=act \
  --dataset.repo_id=local/real_pickplace \
  --training.batch_size=32 \
  --training.steps=100000 \
  --output_dir=outputs/act_real
```

```bash workspace/vla/ch07/deploy.sh
FOLLOWER_PORT=/dev/ttyUSB0

# Run policy on hardware — 20 evaluation trials
# Record with policy driving the robot (no teleop needed for eval)
lerobot-record \
  --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=my_follower \
  --policy.path=outputs/act_real \
  --dataset.repo_id=local/eval_real \
  --dataset.num_episodes=20 \
  --dataset.single_task="Pick and place the cube" \
  --display_data=true
```

**What to observe:** Expect 40–70% success rate on first deployment. Lower than 40%
likely means a calibration or demo quality issue. Higher than 70% on first try is
excellent — you have a good setup.

### Deployment checklist

Before each eval session:
- [ ] Lighting matches training setup exactly
- [ ] Camera position hasn't moved
- [ ] Object placement consistent with training
- [ ] Calibration file matches current arm zero positions
- [ ] Action frequency (fps) matches training

---

## Project E — Failure Analysis and Iteration

**Problem:** Your policy has a 50% success rate. You want 80%. What to do?

**Approach:** Record 20 failure trials on video. Categorize failures. Collect targeted
demos for the dominant failure mode. Retrain and measure improvement.

```python workspace/vla/ch07/failure_log.py
"""Log failure categories from real-robot eval. Structured for targeted retraining."""
from dataclasses import dataclass, field
from typing import Literal
import json

FailureType = Literal[
    "grasp_miss",       # arm reaches but fingers miss object
    "approach_wrong",   # arm goes to wrong position
    "drop_early",       # grasps but drops before placement
    "place_miss",       # reaches placement but misses
    "timeout",          # episode too slow
    "other",
]

@dataclass
class FailureLog:
    failures: list[dict] = field(default_factory=list)

    def add(self, trial: int, failure_type: FailureType, note: str = "") -> None:
        self.failures.append({"trial": trial, "type": failure_type, "note": note})

    def summary(self) -> dict:
        from collections import Counter
        counts = Counter(f["type"] for f in self.failures)
        total  = len(self.failures)
        return {k: {"count": v, "pct": v/total} for k, v in counts.most_common()}

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump({"failures": self.failures, "summary": self.summary()}, f, indent=2)
        print(f"Saved {len(self.failures)} failures to {path}")
        print("\nFailure breakdown:")
        for k, v in self.summary().items():
            print(f"  {k:20s}  {v['count']:3d}  ({v['pct']:.0%})")

if __name__ == "__main__":
    log = FailureLog()
    # Fill in from your video review:
    log.add(1, "grasp_miss", "arm 2cm too far right")
    log.add(2, "approach_wrong", "went to wrong side of object")
    log.add(3, "grasp_miss")
    # ... add all 20 failure trials
    log.save("./failure_log.json")
    print("\nNext step: collect 20–30 targeted demos for the top failure category.")
```

**What to observe:** The top 1–2 failure categories usually account for >60% of failures.
Collect 20–30 targeted demos specifically for those situations and retrain.

---

## Self-Check

1. What is backlash in a servo, and how does it affect a trained policy?
   **Answer:** Backlash is mechanical play in the gears — when you reverse direction,
   the output doesn't move until the play is taken up. This means commanded positions
   don't translate to exact physical positions, which causes systematic errors in
   pick-and-place tasks.

2. Your real policy succeeds 30% of the time but sim policy was 85%. What do you check first?
   **Answer:** Check calibration (especially gripper zero position), then lighting (does
   it match training?), then camera position. If all three match, the issue is likely
   the visual domain gap — collect real demos and retrain.

3. Why do you need 100 demos for a real task when 50 worked in sim?
   **Answer:** Real robot demos have more variation — motor noise, slight calibration
   drift, lighting changes between sessions. More demos cover this variation better.
   Also, teleop quality is lower than scripted oracle quality.

4. Your success rate drops from 65% to 40% after moving the lighting 30 cm. What went wrong?
   **Answer:** The visual policy is sensitive to lighting angle and shadows. The policy
   learned features specific to the training lighting setup. Fix: standardize lighting
   between train and eval, or add visual augmentation during training.

5. You retrain on 20 targeted demos for grasp_miss failures and success rate goes from 50% to 55%.
   Why might the gain be small?
   **Answer:** The targeted demos may not be diverse enough, or another failure mode is
   now limiting. Check whether a different failure category became more frequent.

---

## Common Mistakes

- **Inconsistent object placement between train and eval:** Even 2 cm of variation
  in object position significantly degrades grasp success. Mark object position with tape.

- **Demo collection with bad lighting:** Collect a few demos, deploy immediately, and
  check performance before collecting all 100. Catch lighting issues early.

- **Not reviewing demos before training:** Corrupted or failed demos in the training set
  degrade performance. Watch every episode before consolidating the dataset.

- **Calibration mismatch between sessions:** Recalibrate whenever you reassemble the arm
  or the day after it was last used (servos can drift thermally).

- **Evaluating at different fps than training:** If you train at 30 fps and eval at 10 fps,
  the policy's timing is off. Match fps exactly.

---

## Resources

1. [LeRobot hardware docs](https://huggingface.co/docs/lerobot/en/so101) — SO-101 assembly and calibration guide
2. [SO-101 by The Robot Studio](https://github.com/TheRobotStudio/SO-ARM100) — hardware files and sourcing
3. [Feetech motor documentation](http://www.feetechrc.com/) — STS3215 servo specs and calibration
