# Chapter 5 — Real Hardware

**Time:** 1–2 weeks
**Hardware:** Physical robot
**Prerequisites:** Chapter 4 (SmolVLA in sim, domain gap), Chapter 3 (failure analysis loop), Chapter 1 (IK for robot control)

---

## What are we here for

In Chapter 1 you learned what joint angles are. In Chapter 2 you saw RL hit its ceiling on manipulation tasks — 10k+ episodes for tasks that still needed careful reward shaping. In Chapter 3 you built the collect→train→eval→debug loop on sim. In Chapter 4 you fine-tuned a VLA that understood language — but it moved the arm in sim using synthetic MuJoCo renders, not real photos. The policy moved, but couldn't complete tasks. That's the domain gap.

This chapter closes it. You'll assemble a physical SO-101, collect real demonstrations, and fine-tune the same SmolVLA checkpoint on your own data — your camera, your lighting, your objects. By the end, typing "pick up the pink lego brick" will actually work on a real arm.

The full loop: **type instruction → real arm executes it.**

This is the payoff for everything before:
- **Ch1** gave you IK and robot control fundamentals — the SO-101's 6 joints move via the same `qpos`/`ctrl` concepts, translated by LeRobot under the hood
- **Ch2** showed why RL fails for manipulation — you're not doing reward engineering; you'll collect 100 demos instead of 10,000 episodes
- **Ch3** established the collect→train→eval→debug loop — Ch5 runs that exact loop on real hardware
- **Ch4** showed the domain gap in sim — Ch5 closes it with real data

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
3. You fine-tune on 100 demos using one instruction phrase. How do you test whether language conditioning generalised beyond that phrase?
4. Your real policy succeeds 40% of the time. What's the most efficient path to 70%?

---

## Projects

| # | Project | What you build |
|---|---------|---------------|
| A | Assemble, Calibrate & Teleoperate | Working SO-101, all joints calibrated and verified, leader/follower teleop running |
| B | Collect Demonstrations | 100 real pick-and-place demos with consistent lighting and setup |
| C | Fine-tune SmolVLA & Deploy | SmolVLA fine-tuned on your real data; evaluated over 20 real trials |
| D | Language Robustness Check | Instruction phrasing test confirming language conditioning works |
| E | Evaluate & Iterate | Failure categories identified; targeted demos collected; retrained to >70% |

---

## Project A — Assemble, Calibrate & Teleoperate

**Problem:** Get the hardware working end-to-end before collecting any data — with joints calibrated so commanded positions actually match physical positions.

**Approach:** Follow the SO-101 assembly guide, calibrate both arms, then verify all joints move correctly under teleoperation.

### Assembly tips

- Run motor detection before assembly to verify IDs: `lerobot-find-motors --port $FOLLOWER_PORT`
- Tighten all screws snug but don't overtorque — the plastic housing cracks
- Record the zero position of each joint before closing the arm body — you'll need it for calibration

### Why calibrate before teleop

Servos have manufacturing tolerances — the software "zero" doesn't match the physical zero. Without calibration, commanded positions are systematically off. Calibrate once, at the start, and don't touch it until the project is complete. Re-calibrating mid-collection changes the joint zero reference, making early and late demos inconsistent.

🟢 **Run** — calibrates both arms and saves offsets to `~/.cache/lerobot/calibration/`

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
```

### Why teleoperation after calibration

Teleop confirms the full hardware stack works before you invest in data collection. A mis-configured motor or a loose cable caught here saves hours of debugging after the fact. Post-calibration, motion should be smooth and accurate — if the arm still drifts, re-run calibration.

🟢 **Run** — verify all 6 joints respond cleanly to leader arm movement

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

**What to observe:** All 6 joints respond to leader arm movement without jerking or stalling. Document the joint ranges where the arm operates safely — this defines your task workspace. If a joint doesn't move, check its motor ID in the config and the cable connection at that joint.

> **IK under the hood:** In Ch1 you used inverse kinematics to map Cartesian targets to joint angles. LeRobot's `lerobot-record` does the same translation automatically during data collection — your teleoperated demonstrations are stored as joint-angle trajectories, and the policy learns to reproduce those. You don't write IK code here; knowing it exists explains why calibration matters: IK solutions are only accurate if the joint zeros are correct.

---

## Project B — Collect Demonstrations

**Problem:** Collect 100 high-quality real pick-and-place demonstrations.

**Approach:** Teleoperate the robot through the task using the leader arm. Use the same task the SmolVLA checkpoint was trained on: **pick up the pink lego brick and place it in the transparent box.** This maximises the value of fine-tuning — you're adding real data for a task the model already has priors for.

### What makes a good demo

**Lighting** is the single biggest factor for visual policies. LED panels, fixed position, no windows (sunlight changes throughout the day). Once you set up lighting for collection, photograph it — you must replicate it exactly for evaluation.

**Consistency:** Same object placement, same camera angle, same arm start position for every episode. Variation in your *demonstrations* is good. Variation in your *setup* is bad.

**Quality over quantity:** 50 clean demos beat 100 sloppy ones. Watch each demo before saving and delete failed attempts immediately. Noisy demos teach the model that wrong behaviour is acceptable.

🟢 **Run** — records 100 teleoperated episodes to `local/real_pickplace`

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

## Project C — Fine-tune SmolVLA & Deploy

**Problem:** The base checkpoint (`lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace`)
was trained on someone else's setup — different lighting, different camera position, different
lego brick placement. Fine-tuning adapts it to your specific setup.

**Approach:** Fine-tune on your 100 real demos, then deploy on the physical arm and evaluate over 20 trials.

### Pipeline smoke test — do this first

Before fine-tuning your full 100 demos, collect 10 and run the complete pipeline end to end: collect → fine-tune → deploy → 5 eval trials. Verify it works, then collect the remaining 90. A misconfigured camera key or GPU OOM caught at 10 demos costs an hour. Caught at 100 demos, it costs a day.

### Why SmolVLA fine-tuning over training ACT from scratch

Recall Chapter 3: ACT trained from scratch on 206 pusht demos achieved ~62% success after 80k steps. That's a clean sim task with consistent visuals and no domain gap.

On real hardware, ACT from scratch on 100 demos is competitive — but SmolVLA brings pretrained priors from the [Open X-Embodiment dataset](https://arxiv.org/abs/2310.08864) (~1M demos across 22 robot types):

- It already understands what "pink lego brick" means (language prior)
- It knows roughly how pick-and-place motions look (manipulation prior)
- It recognizes what a transparent box is (visual prior)

Fine-tuning adapts these priors to *your* camera and lighting. With 100 demos, SmolVLA fine-tuning typically outperforms ACT from scratch (expect 40–65% vs 20–40% on first deployment).

With more data (200+ demos) the gap narrows and ACT catches up. At 100, SmolVLA wins. This is why Ch4's domain gap matters — the pretrained priors are only useful if the images look similar enough to training.

### Camera setup

The checkpoint expects two cameras: `up` (top-down wrist view) and `side` (front overview). Mount them to match as closely as possible the positions used in Chapter 4's sim:

```
up camera:   above and slightly in front of the arm, pointing straight down
side camera: ~70 cm in front of the arm, at ~40 cm height, angled slightly down
```

Use fixed mounting points — tape down cables, use a tripod or clamp. Any camera movement between collection and evaluation degrades performance.

🟢 **Run** — fine-tunes for 20k steps (~60–90 min on T4); checkpoint saved to `outputs/smolvla_real_ft`

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

**Training time:** ~60–90 min on a T4. On CPU: not recommended (days). On MPS: will OOM on the backward pass. Use Colab free T4 if you don't have a local GPU.

### Deploy

🟢 **Run** — runs 20 evaluation trials and records results to `local/eval_smolvla_real`

```bash workspace/vla/ch05/deploy.sh
FOLLOWER_PORT=/dev/ttyUSB0

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

**What to expect:** First deployment typically lands 40–65% success.

- **Lower than 40%?** Usually a lighting or camera mismatch — the image distribution shifted from training. This is the domain gap from Ch4, still present. Check: are your lights in the same position? Did the camera move? Check calibration second (gripper zero position especially).
- **Higher than 65%?** Your setup is very consistent — that's the main thing to optimise.
- **Contrast with Ch2:** RL needed 15k+ sim steps and careful reward shaping for FetchReach. You're getting 40–65% success from 100 real demos and no reward engineering. That's imitation learning + pretrained priors.

### Why does the gap persist?

You've given the model real images and it's better — but not perfect. The remaining gap comes from:

- **Calibration error** — commanded joint angles don't match physical joint angles exactly
- **Cable drag** — cables add resistance not in the model's training data
- **Camera position drift** — even 1 cm of camera movement changes the image distribution
- **Lighting variation** — shadows shift as the day progresses

Domain randomisation (training with varied lighting, textures, and physics parameters) is the systematic approach to making policies robust to these factors. It's most useful before you have real data — once you have 100 real demos, fine-tuning on them directly is more efficient than DR. If you want to go deeper on DR: [Domain Randomization paper](https://arxiv.org/abs/1703.06907).

---

## Project D — Language Robustness Check

**Problem:** Fine-tuning on 100 demos with one instruction phrase may cause the model to memorise the phrase rather than learn general language conditioning. You need to know which happened before iterating.

**Approach:** Run 10 trials with each of 3 instruction phrasings. This is the direct payoff of all the language conditioning work from Chapter 4 — does the model understand the instruction, or just pattern-match the exact string?

| Instruction | Expected | Rationale |
|-------------|----------|-----------|
| `"pink lego brick into the transparent box"` | Best | Exact training phrase |
| `"place the pink block in the box"` | Good | Paraphrase |
| `"pick up the lego and put it in the container"` | Weaker | More distant phrasing |

**Interpreting results:**

- **All three perform similarly** — language conditioning is working. The model generalised.
- **Only the exact phrase works** — your dataset had too little instruction variation. In the next collection round, vary the phrasing across demos (record some episodes with each paraphrase as the task label).
- **Performance drops sharply at "distant phrasing"** — acceptable. The model has a language prior but not unlimited generalisation. Collect a few demos with that phrasing to close the gap.

This test takes 30 minutes and tells you whether your next move is more data or better data variety. Run it before the full iteration loop.

---

## Project E — Evaluate & Iterate

**Problem:** Your policy has a 50% success rate. You want 80%.

**Approach:** Record 20 failure trials. Categorize each. Collect targeted demos for the dominant failure mode. Retrain and measure the improvement.

This is exactly the loop from Chapter 3, Project B — but now on real hardware where failures cost time, not just sim seconds. In Ch3 you categorized pusht failures as "never reached block", "pushed wrong direction", and so on. Now you're doing the same for real robot failures. The process is identical.

### Failure taxonomy

🔴 **Work** — fill in your trial failures, run the script, use the output to decide what demos to collect next

The script takes a log of per-trial failures and produces a ranked breakdown. The top 1–2 failure categories typically account for >60% of all failures — fix those first.

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
    # 1. Entry point — fill these in from your video review of the 20 failure trials
    log = FailureLog()
    log.add(1,  "grasp_miss",     "arm 2 cm too far right")
    log.add(2,  "approach_wrong", "went to wrong side of object")
    log.add(3,  "grasp_miss")
    # ... add all failures

    # 2. Save and print ranked breakdown → use top category to decide next demo collection
    log.save("workspace/vla/ch05/failure_log.json")
```

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

Steps:
1. Run 20 trials
2. Save video/pictures of each failure
3. Categorize using `FailureLog` above
4. Collect 20–30 targeted demos for the top failure category
5. Retrain and measure improvement

Random additional demos have diminishing returns past 100 — targeted demos beat volume. This is the single most transferable skill in this course, and the same pattern you used in Ch3.

---

## Callout: ROS 2 Integration

If you want to connect the SO-101 to other systems (sensor fusion, a navigation stack, multi-robot coordination), ROS 2 is the standard middleware. LeRobot doesn't require ROS 2 for standalone operation — everything above runs without it. But if you need it:

- LeRobot has ROS 2 bridge examples in `workspace/ext/lerobot/examples/`
- Install: `sudo apt install ros-jazzy-desktop` (Ubuntu 24.04) or use Docker on macOS
- The key integration point: publish joint states as `sensor_msgs/JointState`, subscribe to joint commands as `trajectory_msgs/JointTrajectory`

---

## You built this

A real robot arm that responds to natural language instructions — not by writing motion code, but by fine-tuning a pretrained VLA on 100 demonstrations you collected. The same collect→train→eval→debug loop from Ch3, now running on hardware. That's Physical AI.

**Next steps:** Try a new task — "place the lego in the blue cup." Collect 50 demos, fine-tune, evaluate. The loop is the same; the model just needs to see *your* task.

---

## Self-Check

1. You trained ACT from scratch in Ch3 on pusht (206 demos, ~62% success). You fine-tune SmolVLA on 100 real pick-place demos. Which should perform better on first deployment, and why?
   **Answer:** SmolVLA should outperform ACT on 100 demos because it brings pretrained priors from 1M+ demonstrations across many robots. ACT must learn everything from your 100 demos alone. The gap narrows at 200+ demos.

2. Your fine-tuned SmolVLA succeeds 30% of the time but in Ch4's sim it moved purposefully. What do you check first?
   **Answer:** Lighting and camera position — if they don't match collection setup, the image distribution shifted and the model sees something different from training. Check calibration second (gripper zero position especially).

3. Why does lighting matter more for SmolVLA than for a position-based controller?
   **Answer:** SmolVLA predicts actions from images. Shadows, colour temperature, and brightness all change what the vision encoder sees. A position controller doesn't use images at all — it's immune to lighting. The visual policy is only as good as its image distribution match between train and eval.

4. What is backlash in a servo, and how does it affect a trained policy?
   **Answer:** Backlash is mechanical play in the gears — when you reverse direction, the output shaft doesn't move until the play is taken up. Commanded positions don't translate to exact physical positions, causing systematic errors in grasp tasks.

5. After fine-tuning, the exact training phrase works 65% but paraphrases work 20%. What does that tell you, and what do you fix?
   **Answer:** The model memorised the phrase rather than learning general language conditioning. Fix: in the next collection round, vary the instruction phrasing across demos — record some episodes with each paraphrase as the task label.

---

## Common Mistakes

- **Forgetting the Ch3 iteration loop:** This chapter is 80% the same as Ch3 Project B — just on real hardware. If you're stuck on failure analysis, re-read the failure categorization section in Ch3. The `FailureLog` pattern, categorization, and targeted demo collection are identical.

- **Skipping the pipeline checkpoint:** Collect 10 demos, fine-tune, deploy — verify the full pipeline works before collecting 100. A misconfigured camera or dataset format mismatch caught at 10 demos costs an hour. Caught at 100 demos, it costs a day.

- **Camera position inconsistency:** Even 1 cm of camera drift between collection and eval significantly degrades performance. Use fixed mounts; photograph the exact position.

- **Re-calibrating mid-collection:** If you calibrate between collection sessions, the joint zero reference changes — early and late demos become inconsistent. Calibrate once, at the start, and don't touch it until the project is complete.

- **Evaluating at different fps than training:** If you train at 30 fps but inference takes 60 ms per step, you're running at ~16 fps. The policy's timing is off — actions expect the world to have moved a 30-fps-step's worth, but it hasn't. Measure and match.

- **Wrong instruction at eval:** The instruction string at eval must match (or closely paraphrase) what appeared in fine-tuning. If training used `"pink lego brick into the transparent box"` and eval uses `"pick up the block"`, you're testing generalisation, not deployment.

---

## Resources

1. [LeRobot SO-101 hardware guide](https://huggingface.co/docs/lerobot/en/so101) — assembly, calibration, and record/train/eval pipeline
2. [SO-101 hardware files](https://github.com/TheRobotStudio/SO-ARM100) — sourcing and mechanical drawings
3. [smolvla_svla_so101_pickplace checkpoint](https://huggingface.co/lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace) — the base checkpoint used in this chapter
4. [lerobot/svla_so101_pickplace dataset](https://huggingface.co/datasets/lerobot/svla_so101_pickplace) — 50 real SO-101 episodes to study before collecting your own
5. [Domain Randomization paper](https://arxiv.org/abs/1703.06907) — if you want to go deeper on sim-to-real robustness
