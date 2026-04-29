# Chapter 5 — Real Hardware

**Time:** 1–2 weeks
**Hardware:** 2× SO-101 arm kits (~$500 total) + USB camera + lighting
**Prerequisites:** Chapter 4 (SmolVLA in sim), Chapter 1 (MuJoCo, IK)

---

## What are we here for

In Chapter 4 you typed an instruction and watched a simulated SO-101 arm move — using a
checkpoint trained on real robot data. The arm moved, but not accurately. The reason was
the domain gap: the model saw synthetic MuJoCo renders, not real camera images.

This chapter closes that gap. You'll assemble a physical SO-101, collect real
demonstrations, and fine-tune the same SmolVLA checkpoint on your own data. By the end,
the model will have seen real images of your robot and your task — and performance will
improve measurably.

The full loop: **type instruction → real arm executes it.**

**Hardware shopping list:**

| Item | Cost | Notes |
|------|------|-------|
| SO-101 arm kit (follower) | ~$250 | The arm that executes |
| SO-101 arm kit (leader) | ~$250 | The arm you hold to teleoperate — required for data collection |
| USB camera (e.g. Logitech C920) | ~$80 | |
| LED lighting panel | ~$40 | |
| **Total** | ~$620 | Leader arm is reusable across future projects |

**Install:**
```bash
cd workspace/ext/lerobot
pip install -e ".[smolvla,hardware]"
```

**Working directory:** `workspace/vla/ch05/`

> **Note on LeRobot CLI commands:** Entry points (`lerobot-teleoperate`, `lerobot-calibrate`,
> `lerobot-record`, `lerobot-train`) may shift between LeRobot releases. If a command fails,
> check `lerobot <command> --help` against your installed version.

**Skip if you can answer:**
1. What is backlash in a servo, and how does it affect a trained policy?
2. You fine-tuned SmolVLA on 100 demos but it still fails. What do you check first?
3. Why does lighting matter more for VLA policies than for ACT?
4. Your real policy succeeds 40% of the time. What's the most efficient path to 70%?

---

## Projects

| # | Project | What you build |
|---|---------|---------------|
| A | Assemble & Teleoperate | Working SO-101, all joints verified, leader/follower teleop running |
| B | Calibrate | Calibrated motors, documented workspace limits |
| C | Collect Demonstrations | 100 real pick-and-place demos with consistent lighting and setup |
| D | Fine-tune SmolVLA & Deploy | SmolVLA fine-tuned on your real data; evaluated over 20 real trials |
| E | Evaluate & Iterate | Failure categories identified; targeted demos collected; retrained |

---

## Project A — Assemble & Teleoperate

**Problem:** Get the hardware working end-to-end before collecting any data.

**Approach:** Follow the SO-101 assembly guide, connect to LeRobot, verify all joints move
correctly, and run teleoperation with a leader arm.

### Why teleoperation first

Teleop confirms the full hardware stack works before you invest in data collection. A
mis-configured motor or a loose cable caught here saves hours of debugging after the fact.

```bash workspace/vla/ch05/teleoperate.sh
# Find your serial ports:
#   Linux:  ls /dev/ttyUSB*
#   macOS:  ls /dev/tty.usbmodem*
FOLLOWER_PORT=/dev/ttyUSB0
LEADER_PORT=/dev/ttyUSB1

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
stalling. If a joint doesn't move, check its motor ID in the config and the cable
connection at that joint.

### Assembly tips

- Run motor detection before assembly to verify IDs: `lerobot-find-motors --port $FOLLOWER_PORT`
- Tighten all screws snug but don't overtorque — the plastic housing cracks
- Record the zero position of each joint before closing the arm body — you'll need it for calibration

---

## Project B — Calibrate

**Problem:** Servos have manufacturing tolerances — the software "zero" doesn't match the
physical zero. Without calibration, commanded positions are systematically off.

**Approach:** Run LeRobot's calibration procedure for each joint. Then document workspace
limits — positions where the arm hits itself or the table. These limits define where you
can safely place objects for your task.

```bash workspace/vla/ch05/calibrate.sh
FOLLOWER_PORT=/dev/ttyUSB0
LEADER_PORT=/dev/ttyUSB1

lerobot-calibrate \
  --robot.type=so101_follower \
  --robot.port=$FOLLOWER_PORT \
  --robot.id=my_follower

lerobot-calibrate \
  --teleop.type=so101_leader \
  --teleop.port=$LEADER_PORT \
  --teleop.id=my_leader

# Calibration saves to ~/.cache/lerobot/calibration/
# Verify: run teleop again — motion should be smooth and accurate
lerobot-teleoperate \
  --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=my_follower \
  --teleop.type=so101_leader  --teleop.port=$LEADER_PORT  --teleop.id=my_leader \
  --display_data=true
```

**What to observe:** Post-calibration, the arm should reach any commanded position
accurately. If it still drifts, re-run calibration. Document the joint ranges where
the arm operates safely — this defines your task workspace.

---

## Project C — Collect Demonstrations

**Problem:** Collect 100 high-quality real pick-and-place demonstrations.

**Approach:** Teleoperate the robot through the task using the leader arm. Use the same
task the SmolVLA checkpoint was trained on: **pick up the pink lego brick and place it
in the transparent box.** This maximises the value of fine-tuning — you're adding real
data for a task the model already has priors for.

### What makes a good demo

**Lighting** is the single biggest factor for visual policies. LED panels, fixed position,
no windows (sunlight changes throughout the day). Once you set up lighting for collection,
photograph it — you must replicate it exactly for evaluation.

**Consistency:** Same object placement, same camera angle, same arm start position for
every episode. Variation in your *demonstrations* is good. Variation in your *setup* is bad.

**Quality over quantity:** 50 clean demos beat 100 sloppy ones. Watch each demo before
saving and delete failed attempts immediately.

```bash workspace/vla/ch05/collect_demos.sh
FOLLOWER_PORT=/dev/ttyUSB0
LEADER_PORT=/dev/ttyUSB1
HF_USER=local   # or your HuggingFace username to push to hub

lerobot-record \
  --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=my_follower \
  --teleop.type=so101_leader  --teleop.port=$LEADER_PORT  --teleop.id=my_leader \
  --dataset.repo_id=$HF_USER/real_pickplace \
  --dataset.num_episodes=100 \
  --dataset.single_task="pink lego brick into the transparent box" \
  --display_data=true
```

**After each session:**
- Review demos: `lerobot-dataset-viz --repo-id local/real_pickplace`
- Delete any episodes where the arm missed or the object was out of position
- Photograph your lighting and object placement setup — you'll need to recreate it for eval

---

## Project D — Fine-tune SmolVLA & Deploy

**Problem:** The base checkpoint (`lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace`)
was trained on someone else's setup — different lighting, different camera position, different
lego brick placement. Fine-tuning adapts it to your specific setup.

**Approach:** Fine-tune on your 100 real demos, then deploy on the physical arm and evaluate
over 20 trials.

### Why SmolVLA fine-tuning over training ACT from scratch

ACT from scratch on 100 demos is competitive — but SmolVLA brings pretrained priors: it
already understands what "pink lego brick" means, roughly how pick-and-place motions look,
and what a transparent box is. Fine-tuning adapts these priors to your camera and lighting.
With 100 demos, SmolVLA fine-tuning typically outperforms ACT from scratch.

With more data (200+ demos) the gap narrows and ACT catches up. At 100, SmolVLA wins.

### Camera setup

The checkpoint expects two cameras: `up` (top-down wrist view) and `side` (front overview).
Mount them to match as closely as possible the positions used in Chapter 4's sim:

```
up camera:   above and slightly in front of the arm, pointing straight down
side camera: ~70 cm in front of the arm, at ~40 cm height, angled slightly down
```

Use fixed mounting points — tape down cables, use a tripod or clamp. Any camera movement
between collection and evaluation degrades performance.

```bash workspace/vla/ch05/finetune_smolvla.sh
cd workspace/ext/lerobot

uv run --extra smolvla --extra training --extra dataset \
  lerobot-train \
    --policy.path=lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace \
    --dataset.repo_id=local/real_pickplace \
    --batch_size=16 \
    --steps=20000 \
    --policy.push_to_hub=false \
    --output_dir=outputs/smolvla_real_ft
```

**Training time:** ~60–90 min on a T4. On CPU: not recommended (days). On MPS: will OOM
on the backward pass. Use Colab free T4 if you don't have a local GPU.

### Deploy

```bash workspace/vla/ch05/deploy.sh
FOLLOWER_PORT=/dev/ttyUSB0

# Run the fine-tuned policy on hardware — 20 evaluation trials
lerobot-record \
  --robot.type=so101_follower \
  --robot.port=$FOLLOWER_PORT \
  --robot.id=my_follower \
  --policy.path=outputs/smolvla_real_ft \
  --dataset.repo_id=local/eval_smolvla_real \
  --dataset.num_episodes=20 \
  --dataset.single_task="pink lego brick into the transparent box" \
  --display_data=true
```

### Deployment checklist

Before each eval session:
- [ ] Lighting matches collection setup exactly (use your photograph)
- [ ] Camera positions haven't moved
- [ ] Object placement consistent with training
- [ ] Calibration file matches current arm zero positions
- [ ] Action frequency (fps) matches training

**What to expect:** First deployment typically lands 40–65% success. Lower than 40% usually
means a lighting or camera mismatch. Higher than 65% on first try means your setup is
very consistent — that's the main thing to optimise.

---

## Project E — Evaluate & Iterate

**Problem:** Your policy has a 50% success rate. You want 80%.

**Approach:** Record 20 failure trials. Categorize each. Collect targeted demos for the
dominant failure mode. Retrain and measure the improvement.

### Failure taxonomy

```python workspace/vla/ch05/failure_log.py
"""Log and categorize real-robot eval failures for targeted retraining."""
from dataclasses import dataclass, field
from typing import Literal
import json

FailureType = Literal[
    "grasp_miss",      # arm reaches correctly but fingers miss the object
    "approach_wrong",  # arm goes to the wrong position entirely
    "drop_early",      # grasps but drops before reaching the box
    "place_miss",      # reaches the box but misses placement
    "language_wrong",  # arm moves but toward wrong goal (language not conditioning)
    "timeout",         # episode exceeds time limit
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
        return {k: {"count": v, "pct": f"{v/total:.0%}"} for k, v in counts.most_common()}

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump({"failures": self.failures, "summary": self.summary()}, f, indent=2)
        print(f"Saved {len(self.failures)} failures → {path}")
        print("\nFailure breakdown:")
        for k, v in self.summary().items():
            print(f"  {k:20s}  {v['count']:3d}  ({v['pct']})")
        print("\nNext: collect 20–30 targeted demos for the top failure category.")

if __name__ == "__main__":
    log = FailureLog()
    # Fill in from your video review of the 20 failure trials:
    log.add(1,  "grasp_miss",     "arm 2 cm too far right")
    log.add(2,  "approach_wrong", "went to wrong side of object")
    log.add(3,  "grasp_miss")
    # ... add all failures
    log.save("workspace/vla/ch05/failure_log.json")
```

### Language robustness check

After fine-tuning, run 10 trials each with 3 instruction phrasings. This tells you whether
the model generalised the language or memorised the exact training phrase.

| Instruction | Expected | Rationale |
|-------------|----------|-----------|
| `"pink lego brick into the transparent box"` | Best | Exact training phrase |
| `"place the pink block in the box"` | Good | Paraphrase |
| `"pick up the lego and put it in the container"` | Weaker | More distant phrasing |

If all three perform similarly, language conditioning is working. If only the exact phrase
works, your dataset had too little instruction variation — next collection round, vary the
phrasing across demos.

### Iteration loop

```
record 20 failures → categorize → top failure mode?
    ↓
grasp_miss or approach_wrong → collect 20–30 demos targeting that specific sub-task
    ↓
retrain (same steps, same config) → re-eval 20 trials
    ↓
measure delta — repeat until >70%
```

The top 1–2 failure categories typically account for >60% of failures. Fix those first.
Random additional demos have diminishing returns past 100 — targeted demos beat volume.

---

## Callout: Why Does the Real Gap Exist?

In Chapter 4 the model produced approximate motions in sim — it was trained on real photos
but saw synthetic renders. Now you've given it real images and it's better. The remaining
gap comes from:

- **Calibration error** — commanded joint angles don't match physical joint angles exactly
- **Cable drag** — cables add resistance not in the model's training data
- **Camera position drift** — even 1 cm of camera movement changes the image distribution
- **Lighting variation** — shadows shift as the day progresses

Domain randomisation (training with varied lighting, textures, and physics parameters)
is the systematic approach to making policies robust to these factors. It's most useful
before you have real data — once you have 100 real demos, fine-tuning on them directly
is more efficient than DR. If you want to go deeper on DR: [Domain Randomization paper](https://arxiv.org/abs/1703.06907).

---

## Callout: ROS 2 Integration

If you want to connect the SO-101 to other systems (sensor fusion, a navigation stack,
multi-robot coordination), ROS 2 is the standard middleware. LeRobot doesn't require ROS 2
for standalone operation — everything above runs without it. But if you need it:

- LeRobot has ROS 2 bridge examples in `workspace/ext/lerobot/examples/`
- Install: `sudo apt install ros-jazzy-desktop` (Ubuntu 24.04) or use Docker on macOS
- The key integration point: publish joint states as `sensor_msgs/JointState`, subscribe
  to joint commands as `trajectory_msgs/JointTrajectory`

---

## Self-Check

1. What is backlash in a servo, and how does it affect a trained policy?
   **Answer:** Backlash is mechanical play in the gears — when you reverse direction,
   the output shaft doesn't move until the play is taken up. Commanded positions don't
   translate to exact physical positions, causing systematic errors in grasp tasks.

2. Your fine-tuned SmolVLA succeeds 30% of the time but the sim version moved purposefully.
   What do you check first?
   **Answer:** Lighting and camera position. If they don't match collection setup, the
   image distribution shifted — the model sees something different from what it was trained
   on. Check calibration second (gripper zero position especially).

3. Why does lighting matter more for SmolVLA than for a position-based controller?
   **Answer:** SmolVLA predicts actions from images. Shadows, colour temperature, and
   brightness all change what the vision encoder sees. A position controller doesn't use
   images at all — it's immune to lighting. The visual policy is only as good as its
   image distribution match between train and eval.

4. You collect 100 demos. 60% are clean, 40% had small errors (arm slightly off, object
   shifted). Should you keep or delete the 40%?
   **Answer:** Delete them. Noisy demos teach the model that wrong behaviour is acceptable.
   50 clean demos reliably outperform 100 mixed demos.

5. After fine-tuning, the exact training phrase works 65% but paraphrases work 20%.
   What does that tell you, and what do you fix?
   **Answer:** The model memorised the phrase rather than learning general language
   conditioning. Fix: in the next collection round, vary the instruction phrasing across
   demos — record some episodes with each paraphrase as the task label.

---

## Common Mistakes

- **Camera position inconsistency:** Even 1 cm of camera drift between collection and eval
  significantly degrades performance. Use fixed mounts; photograph the exact position.

- **Collecting all 100 demos before testing the pipeline:** Collect 10, fine-tune, deploy.
  Verify the end-to-end pipeline before investing in the full dataset.

- **Re-calibrating mid-collection:** If you calibrate between collection sessions,
  the joint zero reference changes — early and late demos become inconsistent. Calibrate
  once, at the start, and don't touch it until the project is complete.

- **Evaluating at different fps than training:** If you train at 30 fps but inference
  takes 60 ms per step, you're running at ~16 fps. The policy's timing is off — actions
  expect the world to have moved a 30-fps-step's worth, but it hasn't. Measure and match.

- **Wrong instruction at eval:** The instruction string at eval must match (or closely
  paraphrase) what appeared in fine-tuning. If training used
  `"pink lego brick into the transparent box"` and eval uses `"pick up the block"`,
  you're testing generalisation, not deployment.

---

## Resources

1. [LeRobot SO-101 hardware guide](https://huggingface.co/docs/lerobot/en/so101) — assembly, calibration, and record/train/eval pipeline
2. [SO-101 hardware files](https://github.com/TheRobotStudio/SO-ARM100) — sourcing and mechanical drawings
3. [smolvla_svla_so101_pickplace checkpoint](https://huggingface.co/lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace) — the base checkpoint used in this chapter
4. [lerobot/svla_so101_pickplace dataset](https://huggingface.co/datasets/lerobot/svla_so101_pickplace) — 50 real SO-101 episodes to study before collecting your own
5. [Domain Randomization paper](https://arxiv.org/abs/1703.06907) — if you want to go deeper on sim-to-real robustness
