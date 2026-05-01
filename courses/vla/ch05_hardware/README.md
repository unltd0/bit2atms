# Chapter 5 — Real Hardware

**Time:** 1–2 weeks
**Hardware:** Physical robot
**Prerequisites:** Chapter 4 (SmolVLA in sim, domain gap), Chapter 3 (failure analysis loop), Chapter 1 (IK for robot control)

---

## What are we here for

Ch4 fine-tuned SmolVLA in sim — the arm moved, but couldn't complete tasks. That's the domain gap — sim vs. real. Synthetic MuJoCo renders look nothing like a real camera feed. The policy learned to act on images it will never see again at deploy time.

This chapter closes it. A pretrained pick-and-place checkpoint already exists (`lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace`) — trained on real SO-101 data, real lighting, real camera. You'll assemble the hardware, run inference with that checkpoint, and watch it work. No fine-tuning required for pick-and-place. That's the loop closed.

Then you'll go further: collect 50 demonstrations for a new task and fine-tune SmolVLA for it. This shows the full workflow for any task you want to teach the arm.

**The full loop: type a pick-and-place instruction → real arm executes it.**

Everything before built toward this:
- **Ch1** gave you IK and robot control fundamentals — the SO-101's 6 joints move via the same `qpos`/`ctrl` concepts, translated by LeRobot under the hood
- **Ch2** showed why RL fails for manipulation — you're not doing reward engineering; you'll collect 50 demos instead of 10,000 episodes
- **Ch3** established the collect→train→eval→debug loop — Ch5 runs that exact loop on real hardware
- **Ch4** showed the domain gap in sim — Ch5 closes it with real data

---

## Why the SO-101 specifically

`smolvla_base` was pretrained on 481 community datasets uploaded to the LeRobot Hub — ~23K episodes of tabletop manipulation, predominantly SO-100 arm. Not Open X-Embodiment (the million-trajectory multi-institution corpus that OpenVLA and RT-2 trained on). Real people's SO-100 demos, collected in real labs with real cameras. That's what the action expert's priors are built from.

The paper's own limitation: *"Our pretraining currently uses datasets collected from a single robot type (SO100). Although we demonstrate that the model can be fine-tuned to different robots...we argue incorporating training data from multiple robot embodiments is likely to prove critical."*

SmolVLA does transfer to other hardware after fine-tuning — it achieves 87.3% on LIBERO (Franka Panda) and 57.3% on Meta-World (Sawyer), both in simulation. So it's not SO-100 locked. But for those arms, you'd need to collect your own demos and fine-tune from scratch.

The SO-101 is an updated SO-100 — same kinematic structure, same joint count, same form factor. It transfers with minimal bridging: the Edinburgh team fine-tuned on just 50 real SO-101 pick-and-place episodes (human teleoperated, ~60–90 min of collection) to produce the checkpoint you'll run in Project B.

**Why not a cheaper arm?** The SO-101 is the cheapest arm with a ready-made checkpoint you can run today. For any other arm — even one that SmolVLA could in principle transfer to — you'd need to collect your own demos and fine-tune. That's doable, but you lose the "works on day one" shortcut that makes this chapter's Project B possible.

---

## How general is SmolVLA — and what does fine-tuning actually do?

SmolVLA is a 450M parameter vision-language-action model. Its architecture has two parts:

- **VLM backbone** (SmolVLM-2 + SigLIP, ~400M params) — frozen during fine-tuning. This is the language and vision understanding: what "pink lego brick" means, what a transparent box looks like, how pick-and-place motions generally work. It was pretrained on internet-scale vision-language data.
- **Action expert** (~50M params) — the only part that gets fine-tuned. It learns to translate VLM features into joint-angle commands for *your specific* task, camera, and lighting.

This split matters. When you fine-tune SmolVLA for a new task, you're not retraining the model's understanding of language or objects — you're teaching the action expert new motion patterns on top of frozen understanding. 50 demos, ~60 minutes on a T4. That's it.

**How general is the base model?**

The VLM backbone understands arbitrary manipulation instructions — it's not limited to pick-and-place. SmolVLA achieves 87.3% on the LIBERO benchmark (40 diverse manipulation tasks) and 57.3% on Meta-World (50 tasks), outperforming much larger models like OpenVLA-7B (76.5% LIBERO) and Octo-90M (75.1% LIBERO). Scale isn't the main lever — pretraining data diversity is. SmolVLA was pretrained on 481 community datasets across 22 robot types.

**But zero-shot deployment on a new task still fails.** The language backbone understands the instruction; the action expert doesn't know how to move *your* arm in *your* environment to execute it. Fine-tune-per-task is the current standard across the entire field.

**What about Pi0 and OpenVLA?**

They have the same constraint. Pi0 (Physical Intelligence) trains on 10,000+ hours across 7 robot types and 68 tasks — impressive scale, but task-specific fine-tuning is still required for real deployment. OpenVLA-7B has stronger language understanding (7B vs 450M), but without fine-tuning it also fails on novel task setups. Pi0.5 (2025) is the closest breakout: it generalises to entirely new homes without fine-tuning — but that works because it trained on 100+ diverse *environments*, not because it solved the fine-tune-per-task problem architecturally.

**Camera viewpoint brittleness** is also field-wide. All major VLAs — SmolVLA, OpenVLA, Octo — drop from ~95% to below 30% success under modest camera shifts. This isn't a SmolVLA weakness; it's the current ceiling. AnyCamVLA (2026) is the first model to address this via zero-shot view synthesis.

**What you can realistically expect:**

| Scenario | Expected success |
|----------|-----------------|
| Run existing pick-place checkpoint, matched setup | 70–90% |
| Run existing checkpoint, camera/lighting shifted | 20–40% |
| Fine-tune on 50 demos for new task | 50–70% first deployment |
| Fine-tune on 50 demos, then iterate to dominant failure mode | 70–85% |

For a new task, always fine-tune from `smolvla_base` — not from the pick-place checkpoint. The pick-place checkpoint has a task-specific action expert; fine-tuning it for a different task fights that prior. Starting from `smolvla_base` gives you the pretrained language+vision understanding with a clean action expert.

---

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
1. Why does fine-tuning SmolVLA on a new task start from `smolvla_base` rather than from a task-specific checkpoint?
2. You run the pick-place checkpoint and get 30% success. What do you check first?
3. You fine-tune on 50 demos using one instruction phrase. How do you test whether language conditioning generalised beyond that phrase?
4. Your real policy succeeds 40% of the time. What's the most efficient path to 70%?
5. What is backlash in a servo, and how does it affect a trained policy?

---

## Projects

| # | Project | What you build |
|---|---------|---------------|
| A | Assemble, Calibrate & Teleoperate | Working SO-101, all joints calibrated and verified, leader/follower teleop running |
| B | Run Inference — Close the Loop | Pick-and-place running on real hardware with the pretrained checkpoint |
| C | Language Robustness Check | Instruction phrasing test confirming language conditioning works |
| D | Fine-tune for a New Task | 50 demos collected; SmolVLA fine-tuned from `smolvla_base`; new task evaluated |
| E | Evaluate & Iterate | Failure categories identified; targeted demos collected; retrained to >70% |

---

## Project A — Assemble, Calibrate & Teleoperate

**Problem:** Get the hardware working end-to-end before running any inference — with joints calibrated so commanded positions actually match physical positions.

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

Teleop confirms the full hardware stack works before you invest in inference or data collection. A mis-configured motor or a loose cable caught here saves hours of debugging later. Post-calibration, motion should be smooth and accurate — if the arm still drifts, re-run calibration.

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

> **IK under the hood:** In Ch1 you used inverse kinematics to map Cartesian targets to joint angles. LeRobot's `lerobot-record` does the same translation automatically during data collection — your teleoperated demonstrations are stored as joint-angle trajectories, and the policy learns to reproduce those. Calibration matters here: IK solutions are only accurate if the joint zeros are correct.

---

## Project B — Run Inference — Close the Loop

**Problem:** Verify that the pretrained pick-and-place checkpoint works on your real hardware — without any fine-tuning.

**Approach:** Set up the camera to match the checkpoint's training setup, run inference, and evaluate over 20 trials. This is the domain gap closed: real images, real arm, pretrained checkpoint.

### Camera setup

The checkpoint was trained with two cameras: `up` (top-down view) and `side` (front overview). Mount yours to match as closely as possible:

```
up camera:   above and slightly in front of the arm, pointing straight down
side camera: ~70 cm in front of the arm, at ~40 cm height, angled slightly down
```

Photograph this setup. You'll need to recreate it exactly every time. Any camera movement degrades performance — this is the field-wide camera brittleness described in the intro, not a calibration issue.

### The task

The checkpoint was trained on: **pick up the pink lego brick and place it in the transparent box.** Use exactly this object and setup. The lighting from the checkpoint's training environment was LED panels, fixed position — replicate it as closely as you can.

🟢 **Run** — runs 20 evaluation trials with the pretrained checkpoint

```bash workspace/vla/ch05/run_inference.sh
FOLLOWER_PORT=/dev/ttyUSB0

lerobot-record \
  --robot.type=so101_follower \
  --robot.port=$FOLLOWER_PORT \
  --robot.id=my_follower \
  --policy.path=lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace \
  --dataset.repo_id=local/eval_pretrained \
  --dataset.num_episodes=20 \
  --dataset.single_task="pink lego brick into the transparent box" \
  --display_data=true
```

**What to expect:** 70–90% success if your camera and lighting setup matches the training environment. If you're seeing 20–40%, the image distribution has shifted — lighting is the first thing to check, camera position second. This is exactly the domain gap from Ch4, except now you're on the right side of it: real images in, real images trained on.

**Contrast with Ch4:** In sim, the same checkpoint failed because MuJoCo renders look nothing like a real camera feed. Here, the images match. That's the only thing that changed — and it's enough.

### Deployment checklist

Before each eval session:
- [ ] Lighting matches the checkpoint's training setup (use LED panels, fixed position)
- [ ] Camera positions match your photograph from setup
- [ ] Pink lego brick and transparent box in consistent starting position
- [ ] Calibration file untouched since initial calibration

---

## Project C — Language Robustness Check

**Problem:** Does the model actually understand language, or did it memorise the exact instruction string from training?

**Approach:** Run 10 trials with each of 3 instruction phrasings. This is the direct payoff of the language conditioning work from Ch4 — the VLM backbone understands natural language; now verify it.

| Instruction | Expected | Rationale |
|-------------|----------|-----------|
| `"pink lego brick into the transparent box"` | Best | Exact training phrase |
| `"place the pink block in the box"` | Good | Paraphrase |
| `"pick up the lego and put it in the container"` | Weaker | More distant phrasing |

**Interpreting results:**

- **All three perform similarly** — language conditioning is working. The frozen VLM backbone is doing its job.
- **Only the exact phrase works** — the action expert memorised the phrase rather than the semantics. Fix: in the next collection round, vary the phrasing across demos.
- **Performance drops sharply at distant phrasing** — acceptable. Even the 7B OpenVLA struggles here. The language prior helps but doesn't give unlimited generalisation.

This test takes 30 minutes and tells you whether your next move is more data or better data variety.

---

## Project D — Fine-tune for a New Task

**Problem:** Pick-and-place works with the pretrained checkpoint. Now teach the arm a new task — one it has no checkpoint for.

**Approach:** Pick a simple, distinct manipulation task. Collect 50 demonstrations via teleoperation. Fine-tune from `smolvla_base` — not from the pick-place checkpoint. Evaluate.

### Choosing a task

Pick something visually distinct from pick-and-place and executable in a single smooth motion:
- Push the red cube to the left side of the table
- Knock the block off the pedestal
- Slide the card into the slot

Avoid multi-step tasks (grasp + transport + place with a lid) for a first fine-tune — they need more demos and longer episodes.

### Why fine-tune from `smolvla_base`

The pick-place checkpoint's action expert was trained to produce pick-and-place motions. Fine-tuning it for a push task creates a conflict — the expert's weights are strongly biased toward pick-place trajectories. Starting from `smolvla_base` gives you the frozen language+vision backbone (identical) with a fresh action expert. You lose nothing; you avoid fighting the prior.

### What makes a good demo

**Consistency beats quantity.** 50 clean demos of one strategy beat 80 demos of mixed approaches. The action expert learns what the demos show — noise in the demos becomes noise in the policy.

**Lighting:** Same LED panels, same position, no windows. Photograph it.

**Same start position every episode.** Variation in your demonstrations (slight angle differences, slight speed differences) is fine. Variation in your *setup* (object moved, camera shifted) is not.

🟢 **Run** — records 50 teleoperated episodes for your new task

```bash workspace/vla/ch05/collect_new_task.sh
FOLLOWER_PORT=/dev/ttyUSB0
LEADER_PORT=/dev/ttyUSB1
HF_USER=local

TASK="push the red cube to the left"   # your instruction string — keep it consistent

lerobot-record \
  --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=my_follower \
  --teleop.type=so101_leader  --teleop.port=$LEADER_PORT  --teleop.id=my_leader \
  --dataset.repo_id=$HF_USER/new_task \
  --dataset.num_episodes=50 \
  --dataset.single_task="$TASK" \
  --display_data=true
```

**After each session:** review with `lerobot-dataset-viz --repo-id local/new_task`. Delete failed episodes immediately — sloppy demos teach the model that wrong behaviour is acceptable.

### Pipeline smoke test — do this first

Collect 10 demos, fine-tune, deploy, run 5 trials. Verify the pipeline works before collecting all 50. A misconfigured camera key caught at 10 demos costs an hour. Caught at 50 demos, it costs a day.

🟢 **Run** — fine-tunes for 20k steps (~60–90 min on T4)

```bash workspace/vla/ch05/finetune_new_task.sh
cd workspace/ext/lerobot

uv run --extra smolvla --extra training --extra dataset \
  lerobot-train \
    --policy.path=lerobot/smolvla_base \
    --dataset.repo_id=local/new_task \
    --batch_size=16 \
    --steps=20000 \
    --policy.push_to_hub=false \
    --output_dir=outputs/smolvla_new_task_ft
```

**Training time:** ~60–90 min on a T4. On CPU: not recommended. On MPS: will OOM on the backward pass. Use Colab free T4 if you don't have a local GPU.

🟢 **Run** — evaluates over 20 trials

```bash workspace/vla/ch05/deploy_new_task.sh
FOLLOWER_PORT=/dev/ttyUSB0
TASK="push the red cube to the left"

lerobot-record \
  --robot.type=so101_follower \
  --robot.port=$FOLLOWER_PORT \
  --robot.id=my_follower \
  --policy.path=outputs/smolvla_new_task_ft \
  --dataset.repo_id=local/eval_new_task \
  --dataset.num_episodes=20 \
  --dataset.single_task="$TASK" \
  --display_data=true
```

**What to expect:** 50–70% on first deployment. Lower than 40% usually means a lighting or camera mismatch — the image distribution shifted from training.

---

## Project E — Evaluate & Iterate

**Problem:** Your policy has ~50% success. You want 70%+.

**Approach:** Record 20 failure trials. Categorize each. Collect targeted demos for the dominant failure mode. Retrain and measure.

This is the loop from Ch3, Project B — on real hardware. The process is identical; failures just cost time instead of sim seconds.

### Failure taxonomy

🔴 **Work** — fill in your trial failures, run the script, use the output to decide what demos to collect next

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
    "language_wrong",  # arm moves but toward wrong goal
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
    # 1. Fill these in from your video review of the 20 failure trials
    log = FailureLog()
    log.add(1,  "grasp_miss",     "arm 2 cm too far right")
    log.add(2,  "approach_wrong", "went to wrong side of object")
    log.add(3,  "grasp_miss")
    # ... add all failures

    # 2. Save → ranked breakdown tells you which demos to collect next
    log.save("workspace/vla/ch05/failure_log.json")
```

### Iteration loop

```
record 20 failures → categorize → top failure mode?
    ↓
collect 20–30 demos targeting that sub-task
    ↓
retrain from smolvla_base (same steps, same config) → re-eval 20 trials
    ↓
measure delta — repeat until >70%
```

Random additional demos have diminishing returns past 50 — targeted demos beat volume. Top 1–2 failure categories typically account for >60% of all failures. Fix those first.

---

## You built this

A real robot arm that responds to natural language instructions — not by writing motion code, but by running a pretrained VLA on real hardware and fine-tuning it for new tasks with 50 demonstrations. The same collect→train→eval→debug loop from Ch3, now running on hardware.

The pick-and-place loop is closed. The fine-tuning workflow is yours to reuse: choose a task, collect 50 demos, fine-tune from `smolvla_base`, iterate on failures.

---

## Self-Check

1. In Ch4, the SmolVLA checkpoint failed in sim despite being fine-tuned on sim data. You ran the same checkpoint on real hardware here and it worked. What's the single thing that changed?
   **Answer:** The image distribution matched. The checkpoint was trained on real SO-101 camera feeds. In Ch4, it saw synthetic MuJoCo renders — a different distribution entirely. On real hardware, the images match training, so the policy can act correctly.

2. Why do you fine-tune from `smolvla_base` for a new task instead of from the pick-place checkpoint?
   **Answer:** The pick-place checkpoint's action expert is strongly biased toward pick-and-place trajectories. Fine-tuning it for a different task fights that prior. `smolvla_base` has the same frozen language+vision backbone but a clean action expert — no prior to fight.

3. SmolVLA (450M) outperforms OpenVLA (7B) on LIBERO. Why doesn't scale win here?
   **Answer:** Pretraining data diversity matters more than parameter count. SmolVLA was pretrained on 481 community datasets across 22 robot types. A larger model trained on narrower data doesn't generalise better — it just memorises more of the same distribution.

4. Your fine-tuned new-task policy succeeds 30% of the time. What do you check first?
   **Answer:** Lighting and camera position — if they don't exactly match your collection setup, the image distribution shifted and the model sees something different from training. Check calibration second.

5. After fine-tuning on 50 demos with one instruction phrase, paraphrases only succeed 20% of the time. What does that tell you, and what do you fix?
   **Answer:** The action expert memorised the phrase rather than the semantics. Fix: in the next collection round, vary the instruction phrasing across demos — record some episodes with each paraphrase as the task label.

---

## Common Mistakes

- **Camera position inconsistency:** Even 1 cm of camera drift between collection and eval significantly degrades performance. Use fixed mounts; photograph the exact position.

- **Re-calibrating mid-collection:** If you calibrate between collection sessions, the joint zero reference changes — early and late demos become inconsistent. Calibrate once, at the start.

- **Fine-tuning from the task-specific checkpoint for a new task:** The pick-place action expert fights a different task's motions. Always start new tasks from `smolvla_base`.

- **Skipping the pipeline smoke test:** Collect 10 demos, fine-tune, deploy — verify the full pipeline before collecting all 50. A misconfigured dataset format caught at 10 demos costs an hour; caught at 50, it costs a day.

- **Evaluating at different fps than training:** If you train at 30 fps but inference takes 60 ms per step, you're running at ~16 fps. Actions expect the world to have moved a 30-fps-step's worth, but it hasn't. Measure and match.

- **Mixed demo strategies:** 50 demos of one consistent grasping approach beats 80 demos of mixed techniques. The action expert learns exactly what the demos show.

---

## Resources

1. [LeRobot SO-101 hardware guide](https://huggingface.co/docs/lerobot/en/so101) — assembly, calibration, and record/train/eval pipeline
2. [SO-101 hardware files](https://github.com/TheRobotStudio/SO-ARM100) — sourcing and mechanical drawings
3. [smolvla_svla_so101_pickplace checkpoint](https://huggingface.co/lerobot-edinburgh-white-team/smolvla_svla_so101_pickplace) — the pretrained checkpoint used in Project B
4. [SmolVLA paper](https://arxiv.org/abs/2506.01844) — architecture details, benchmark numbers, fine-tuning strategy
5. [π₀.5 paper](https://arxiv.org/abs/2504.16054) — the closest thing to task-general zero-shot deployment; understand what it took to get there
6. [LIBERO-Plus robustness analysis](https://arxiv.org/abs/2510.13626) — evidence that camera brittleness affects all VLAs equally
7. [lerobot/svla_so101_pickplace dataset](https://huggingface.co/datasets/lerobot/svla_so101_pickplace) — 50 real SO-101 episodes to study before collecting your own
