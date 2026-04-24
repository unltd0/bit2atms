# Chapter 9 — Physical Hardware

**Time:** 1–2 weeks
**Hardware:** SO-101 arm (~$250) + USB camera + laptop with GPU
**Prerequisites:** Chapter 5 (imitation learning, LeRobot). Chapter 8 (ROS 2) helpful.

---

## Why This Chapter Exists

Every chapter before this one could be completed with zero physical hardware. That's deliberate — you built up the full conceptual stack first. But simulation has a ceiling: it doesn't teach you how a policy actually behaves when cable friction varies mid-demo, when the camera white-balances unexpectedly, or when the robot's real joint stiffness disagrees with the MJCF model.

The gap this fills: the difference between understanding imitation learning and actually shipping a policy that works on a physical robot. That gap is larger than most people expect, and it's almost entirely operational — calibration, data quality, lighting consistency, failure diagnosis. This chapter makes that gap explicit and walks you through closing it systematically.

---

## Part 1 — Choosing Your Hardware

### The Recommended Stack (2025-2026)

**SO-101 (by The Robot Studio)**

The current recommended budget arm for LeRobot work. Successor to the deprecated SO-100.

- Cost: ~$250 (single arm) or ~$500 (leader + follower bimanual setup)
- 6 degrees of freedom
- Servo motors: Feetech STS3215
- Native LeRobot integration
- Build time: 3–5 hours
- Max payload: ~500g

Why SO-101 over alternatives:
- Designed specifically for imitation learning with LeRobot
- Best documentation for this workflow
- Large community support
- Cheapest entry point that actually works

**Koch v1.1**

Alternative if you want Dynamixel servos (more precise, better ecosystem, more expensive).
- Cost: ~$300
- 6 DOF, Dynamixel XL330/XL430 servos
- LeRobot supported
- Better repeatability than SO-101

**WidowX 250 S**

If you have a ~$3k budget and want a more "research grade" arm.
- Used in OpenVLA and Octo papers for evaluation
- 6 DOF, Dynamixel X-series servos
- Better accuracy and repeatability
- InterbotixROS software ecosystem

**Skip if you have < $3k:** ALOHA 2 ($20k+), Kinova ($15k+). These are for labs.

### What Else You Need

| Item | Cost | Purpose |
|------|------|---------|
| USB camera (Logitech C920/C930) | $60–100 | Visual observations |
| **Or** Intel RealSense D435 | $200–300 | Depth + RGB, better quality |
| Laptop dock / USB hub | $30 | Multiple USB connections |
| Non-reflective table surface | — | Consistent visual background |
| Consistent lighting (LED panels) | $30–60 | Critical for visual policies |
| Small objects to manipulate | — | Colored blocks, cups, etc. |

---

## Part 2 — Critical Success Factors for Real Robots

Read this section before touching any hardware.

### 1. Lighting Is Everything for Visual Policies

The single most common reason real robot policies fail when the simulation policy worked: inconsistent lighting.

- Use the same camera position every time
- Use fixed artificial lighting (LED panels, not window light which changes throughout the day)
- Minimize reflections: use matte surfaces, not glossy
- If using an overhead camera: mount it rigidly, not handheld

**Test:** Take 50 photos of your scene over 2 days at different times. If the images look different, your policy will fail on the days it wasn't trained on.

### 2. Calibration Is Not Optional

Before collecting any data:
1. Calibrate motors (every SO-101/Koch needs this)
2. Calibrate camera (intrinsics, distortion)
3. Set consistent home position before every episode
4. Verify teleoperation works smoothly before recording

An uncalibrated arm produces noisy, inconsistent demonstrations that a policy cannot learn from.

### 3. Demonstration Quality > Demonstration Quantity

50 clean, consistent demonstrations are worth more than 200 noisy ones.

"Clean" means:
- Smooth, purposeful motion (no hesitations or corrections)
- Consistent start position every episode
- Consistent object placement (within 1 cm of same position)
- Successful completion of the task

Delete failed demonstrations immediately. Even 10% failed demonstrations significantly degrade policy performance.

### 4. Task Design Matters

Choose your first task wisely:
- **Good:** Pick a colored block from a fixed position and place it in a fixed bin
- **Good:** Push an object to a target
- **Too hard for start:** Pick and place with varying object positions (do this after mastering the fixed case)
- **Too hard for start:** Opening a bag, inserting a USB plug, folding cloth

Start simple. Succeed completely. Then add variation.

---

## Part 3 — The LeRobot Hardware Workflow

LeRobot provides a complete end-to-end workflow for real robot learning:

```
calibrate → teleoperate → record → train → evaluate → improve
```

All of this runs through the LeRobot CLI and Python scripts.

### Install LeRobot for Hardware

```bash
# Full install with hardware support
pip install -e ".[feetech]"     # for SO-101
# or
pip install -e ".[dynamixel]"   # for Koch v1.1
```

### Motor Configuration

Each servo motor needs an ID assigned before first use. This is done via LeRobot's calibration tool.

---

## External Resources

1. **SO-101 Official Build Guide and BOM**
   Step-by-step assembly with photos. Follow exactly — order of assembly matters.
   → https://github.com/TheRobotStudio/SO-ARM100
   → Look for the SO-101 folder specifically (not SO-100)

2. **LeRobot Hardware Documentation**
   Calibration, teleoperation, data collection, training — the official guide for SO-101.
   → https://huggingface.co/docs/lerobot/robots/so101
   → https://huggingface.co/docs/lerobot/index

3. **LeRobot SO-101 Video Tutorial (HuggingFace)**
   Watch the full setup video before starting.
   → Search: "LeRobot SO-101 tutorial" on YouTube (HuggingFace official channel)

4. **Koch v1.1 Documentation**
   Alternative arm with Dynamixel servos.
   → https://github.com/jess-moss/koch-v1-1

5. **OpenCV Camera Calibration**
   For camera intrinsic calibration.
   → https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html

6. **Feetech SDK Documentation**
   Motor SDK for SO-101 servos.
   → https://github.com/TheRobotStudio/feetech_ros

---

## Project 9A — Build and Verify Hardware

This is a physical project. Follow the SO-101 build guide from start to finish.

**Checklist after assembly:**

```
[ ] All 12 motors assembled (6 per arm in leader-follower config)
[ ] Motor IDs assigned correctly (1-6 on each arm)
[ ] Cables routed and secured (loose cables cause dropout faults)
[ ] USB connections verified (leader and follower on separate ports)
[ ] Power supply connected (12V, 5A minimum)
[ ] LeRobot detects both arms:
    python -m lerobot.scripts.find_motors_bus_port
```

Create `learning/ch09_hardware/01_hardware_check.py`:

```python
"""
Hardware verification script.
Run this before any calibration or data collection.
"""
import time
import numpy as np

def check_so101_connection():
    """Verify SO-101 leader and follower are connected and responding."""
    try:
        from lerobot.common.robot_devices.motors.feetech import FeetechMotorsBus

        # Update these ports to match your system
        # Linux: /dev/ttyACM0, /dev/ttyACM1
        # macOS: /dev/cu.usbmodem... (check with ls /dev/cu.*)
        leader_port = "/dev/ttyACM0"
        follower_port = "/dev/ttyACM1"

        print(f"Testing leader arm on {leader_port}...")
        leader_bus = FeetechMotorsBus(
            port=leader_port,
            motors={f"joint_{i}": (i, "sts3215") for i in range(1, 7)}
        )
        leader_bus.connect()
        positions = leader_bus.read("Present_Position")
        print(f"  Leader connected. Positions: {positions}")
        leader_bus.disconnect()

        print(f"\nTesting follower arm on {follower_port}...")
        follower_bus = FeetechMotorsBus(
            port=follower_port,
            motors={f"joint_{i}": (i, "sts3215") for i in range(1, 7)}
        )
        follower_bus.connect()
        positions = follower_bus.read("Present_Position")
        print(f"  Follower connected. Positions: {positions}")
        follower_bus.disconnect()

        print("\nHardware check PASSED.")
        return True

    except Exception as e:
        print(f"Hardware check FAILED: {e}")
        print("\nTroubleshooting:")
        print("  1. Check USB connections")
        print("  2. Check power supply is on")
        print("  3. Run: ls /dev/tty* to find correct ports")
        print("  4. Check motor IDs are set correctly")
        return False


def check_camera():
    """Verify USB camera is accessible."""
    import cv2
    cap = cv2.VideoCapture(0)  # try camera index 0
    if not cap.isOpened():
        cap = cv2.VideoCapture(1)  # try index 1
    if not cap.isOpened():
        print("Camera check FAILED: no camera found at index 0 or 1")
        return False

    ret, frame = cap.read()
    if not ret:
        print("Camera check FAILED: could not read frame")
        cap.release()
        return False

    print(f"Camera check PASSED. Resolution: {frame.shape[1]}x{frame.shape[0]}")
    cap.release()
    return True


if __name__ == "__main__":
    print("=== Hardware Verification ===\n")
    arm_ok = check_so101_connection()
    cam_ok = check_camera()

    if arm_ok and cam_ok:
        print("\nAll hardware checks passed. Proceed to calibration.")
    else:
        print("\nFix the above issues before proceeding.")
```

---

## Project 9B — Calibration

LeRobot has a built-in calibration script. You must run this before any data collection.

```bash
# Calibrate the SO-101 robot
python -m lerobot.scripts.control_robot \
  --robot-path lerobot/configs/robot/so101.yaml \
  --robot-overrides '~cameras' \
  --control.type=calibrate
```

**What calibration does:**
1. Moves each joint through its full range of motion
2. Records the raw encoder values at the limits
3. Maps encoder values to joint angles in radians
4. Saves calibration file to `~/.cache/huggingface/lerobot/calibration/`

**Repeat calibration if:**
- You disassemble and reassemble any joint
- The arm behaves unexpectedly after a crash
- You get "joint out of range" errors

Create `learning/ch09_hardware/02_verify_calibration.py`:

```python
"""
After calibration, verify that teleoperation is smooth and accurate.
Move the leader arm slowly — the follower should mirror it without lag.
"""
import time
import numpy as np

def run_teleoperation_test(duration_seconds=30):
    """
    Run leader-follower teleoperation for a test period.
    Observe for:
    - Smooth tracking (no jerks or lag)
    - Full range of motion
    - No motor error beeps
    - No cable snags
    """
    from lerobot.common.robot_devices.robots.factory import make_robot
    from lerobot.common.robot_devices.utils import busy_wait
    import hydra
    from omegaconf import OmegaConf

    # Use LeRobot's robot config
    print("Starting teleoperation test...")
    print("Move the LEADER arm slowly. The FOLLOWER should mirror it.")
    print("Observe: is the motion smooth? Any lag? Any unexpected positions?")
    print(f"Running for {duration_seconds} seconds. Press Ctrl+C to stop early.\n")

    try:
        robot = make_robot("so101")
        robot.connect()

        start = time.time()
        step = 0
        while time.time() - start < duration_seconds:
            t0 = time.perf_counter()

            # Read leader, command follower
            observation, action = robot.teleop_step(record_data=False)

            # Print every 100 steps (~2 sec at 50 Hz)
            if step % 100 == 0:
                print(f"t={time.time()-start:.1f}s  leader={action[:3].round(3)}")

            step += 1
            busy_wait(1/50 - (time.perf_counter() - t0))  # 50 Hz control

    except KeyboardInterrupt:
        print("\nTeleoperation test stopped by user.")
    finally:
        robot.disconnect()
        print("Test complete.")


if __name__ == "__main__":
    run_teleoperation_test()
```

---

## Project 9C — Collect Demonstrations

Create `learning/ch09_hardware/03_collect_demonstrations.py`:

```python
"""
Collect human demonstration data using leader-follower teleoperation.
Record visual observations + proprioception + actions.

Setup before running:
1. Place object at consistent position (mark it with tape)
2. Set up consistent lighting
3. Position camera with full view of workspace
4. Do 3-5 practice runs to get comfortable with the task
"""
import subprocess
import sys
import os
import time


def collect_dataset(
    task_name="pick_place_block",
    n_episodes=100,
    episode_time_s=30,
    fps=30,
    camera_index=0,
    leader_port="/dev/ttyACM0",
    follower_port="/dev/ttyACM1",
):
    """
    Collect demonstrations using LeRobot's record script.
    """
    repo_id = f"local/{task_name}"
    root = f"./data/{task_name}"

    os.makedirs(root, exist_ok=True)

    cmd = [
        sys.executable, "-m", "lerobot.scripts.control_robot",
        "--robot-path", "lerobot/configs/robot/so101.yaml",
        f"--robot-overrides",
        f"leader_arms.main.port={leader_port}",
        f"follower_arms.main.port={follower_port}",
        "--control.type=record",
        f"--control.repo_id={repo_id}",
        f"--control.root={root}",
        f"--control.fps={fps}",
        f"--control.single_task={task_name}",
        f"--control.num_episodes={n_episodes}",
        f"--control.episode_time_s={episode_time_s}",
        "--control.push_to_hub=false",
    ]

    print("=== DEMONSTRATION COLLECTION ===")
    print(f"Task: {task_name}")
    print(f"Target: {n_episodes} episodes × {episode_time_s}s = "
          f"{n_episodes * episode_time_s / 60:.0f} min of recording\n")
    print("BEFORE STARTING:")
    print("  1. Object placed at marked position")
    print("  2. Camera is fixed and focused")
    print("  3. Lighting is consistent")
    print("  4. You've practiced the task 3-5 times\n")

    input("Press Enter when ready to start recording...")

    subprocess.run(cmd, check=False)


def review_and_clean_dataset(task_name="pick_place_block"):
    """
    Review collected episodes and mark/delete failed ones.
    """
    from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
    import cv2
    import numpy as np

    root = f"./data/{task_name}"
    dataset = LeRobotDataset(f"local/{task_name}", root=root)

    print(f"\n=== Dataset Review ===")
    print(f"Total episodes: {dataset.num_episodes}")
    print(f"Total frames: {len(dataset)}")

    episodes_to_delete = []

    for ep_idx in range(dataset.num_episodes):
        ep_data = dataset.get_episode(ep_idx)
        n_frames = len(ep_data)

        # Get first and last frame for review
        first_frame = ep_data[0]['observation.images.top'].numpy()
        last_frame = ep_data[-1]['observation.images.top'].numpy()

        print(f"\nEpisode {ep_idx}: {n_frames} frames ({n_frames/30:.1f}s)")

        # Show episode
        fig_title = f"Episode {ep_idx} — Press 'k' to keep, 'd' to delete"
        cv2.imshow("First frame", cv2.cvtColor(first_frame, cv2.COLOR_RGB2BGR))
        cv2.imshow("Last frame", cv2.cvtColor(last_frame, cv2.COLOR_RGB2BGR))
        cv2.setWindowTitle("First frame", fig_title)

        key = cv2.waitKey(0) & 0xFF
        if key == ord('d'):
            episodes_to_delete.append(ep_idx)
            print(f"  Marked for deletion")
        else:
            print(f"  Keeping")

    cv2.destroyAllWindows()

    kept = dataset.num_episodes - len(episodes_to_delete)
    print(f"\nKeeping {kept}/{dataset.num_episodes} episodes")
    print(f"Deleting: {episodes_to_delete}")

    if len(episodes_to_delete) > 0 and input("Confirm deletion? (y/n): ") == 'y':
        # LeRobot doesn't directly support episode deletion yet
        # Workaround: filter dataset when training
        print("Mark these episode indices for exclusion during training.")
        with open(f"{root}/excluded_episodes.txt", "w") as f:
            f.write("\n".join(map(str, episodes_to_delete)))
        print(f"Saved exclusion list to {root}/excluded_episodes.txt")

    return kept


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--collect", action="store_true")
    parser.add_argument("--review", action="store_true")
    parser.add_argument("--task", default="pick_place_block")
    parser.add_argument("--episodes", type=int, default=100)
    args = parser.parse_args()

    if args.collect:
        collect_dataset(task_name=args.task, n_episodes=args.episodes)
    if args.review:
        review_and_clean_dataset(task_name=args.task)
```

---

## Project 9D — Train on Real Data and Deploy

Create `learning/ch09_hardware/04_train_and_deploy.py`:

```python
"""
Train ACT on real robot data and deploy the policy.
"""
import subprocess
import sys
import os
import time


def train_on_real_data(task_name="pick_place_block", n_steps=80_000, batch_size=32):
    """Train ACT policy on real robot demonstrations."""
    output_dir = f"./outputs/act_real_{task_name}"

    cmd = [
        sys.executable, "-m", "lerobot.scripts.train",
        "policy=act_so101_main",  # SO-101 specific config
        f"dataset_repo_id=local/{task_name}",
        f"training.offline_steps={n_steps}",
        f"training.batch_size={batch_size}",
        f"hydra.run.dir={output_dir}",
        "device=cuda",
        "wandb.enable=false",
    ]

    print(f"=== Training ACT on real data ===")
    print(f"Task: {task_name}")
    print(f"Steps: {n_steps:,}")
    print(f"Estimated time: ~{n_steps/1000:.0f} min on RTX 3060\n")
    subprocess.run(cmd, check=False)
    return output_dir


def deploy_policy(
    policy_path,
    task_name="pick_place_block",
    n_eval_episodes=20,
    leader_port="/dev/ttyACM0",
    follower_port="/dev/ttyACM1",
):
    """
    Deploy trained policy on real robot and evaluate.
    """
    cmd = [
        sys.executable, "-m", "lerobot.scripts.control_robot",
        "--robot-path", "lerobot/configs/robot/so101.yaml",
        f"--robot-overrides",
        f"follower_arms.main.port={follower_port}",
        "--control.type=eval",
        f"--control.policy.path={policy_path}",
        f"--control.num_episodes={n_eval_episodes}",
        "--control.push_to_hub=false",
    ]

    print(f"=== Deploying Policy ===")
    print(f"Policy: {policy_path}")
    print(f"Evaluating {n_eval_episodes} episodes\n")
    print("SAFETY CHECK:")
    print("  1. Clear workspace of obstructions")
    print("  2. Keep hand near emergency stop")
    print("  3. Start with max_speed reduced (in SO-101 config)")
    print("  4. Observe first 3 episodes carefully\n")

    input("Press Enter to start evaluation...")
    subprocess.run(cmd, check=False)


def run_evaluation_with_logging(
    policy_path,
    n_trials=20,
):
    """
    Manual evaluation logging template.
    Fill in success/failure for each trial.
    """
    results = []
    failure_notes = []

    print(f"\n=== Manual Evaluation Log ===")
    print(f"Policy: {policy_path}")
    print("For each trial: observe carefully and log success/failure.\n")

    for trial in range(1, n_trials + 1):
        print(f"--- Trial {trial}/{n_trials} ---")
        input("Press Enter to start trial...")

        # Policy would be running here
        time.sleep(5)  # placeholder for policy execution

        result = input("Success? (y/n): ").lower().strip()
        success = result == 'y'
        results.append(success)

        if not success:
            note = input("Failure mode (briefly): ")
            failure_notes.append((trial, note))

        sr = sum(results) / len(results)
        print(f"Running success rate: {sr*100:.0f}% ({sum(results)}/{len(results)})\n")

    # Summary
    final_sr = sum(results) / len(results)
    print(f"\n=== EVALUATION SUMMARY ===")
    print(f"Success rate: {final_sr*100:.0f}% ({sum(results)}/{n_trials})")
    print(f"\nFailure modes:")
    for trial, note in failure_notes:
        print(f"  Trial {trial}: {note}")

    # Save results
    with open(f"eval_results_{policy_path.replace('/', '_')}.txt", 'w') as f:
        f.write(f"Policy: {policy_path}\n")
        f.write(f"Success rate: {final_sr*100:.0f}%\n")
        f.write(f"Failures:\n")
        for trial, note in failure_notes:
            f.write(f"  Trial {trial}: {note}\n")

    return final_sr, failure_notes


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", action="store_true")
    parser.add_argument("--deploy", action="store_true")
    parser.add_argument("--task", default="pick_place_block")
    parser.add_argument("--steps", type=int, default=80_000)
    args = parser.parse_args()

    if args.train:
        output_dir = train_on_real_data(task_name=args.task, n_steps=args.steps)
        policy_path = f"{output_dir}/checkpoints/last/pretrained_model"

    if args.deploy:
        policy_path = f"./outputs/act_real_{args.task}/checkpoints/last/pretrained_model"
        sr, failures = run_evaluation_with_logging(policy_path)

        if sr < 0.7:
            print("\nSuccess rate below 70%. Suggested improvements:")
            print("1. Collect more demonstrations (aim for 200)")
            print("2. Review failure modes — are they consistent?")
            print("3. Add augmentation: random crop, color jitter")
            print("4. Check lighting — is it consistent?")
```

---

## Project 9E — Failure Analysis and Iteration

Create `learning/ch09_hardware/05_failure_analysis.md`:

```markdown
# Real Robot Failure Analysis Template

## Evaluation Run: [date] [task_name] [policy_name]

### Summary
- Success rate: X/Y trials = Z%
- Policy trained on: N demonstrations
- Test conditions: [describe lighting, object position, etc.]

### Failure Categories

| Category | Count | Description |
|----------|-------|-------------|
| Grasp failure | | Robot doesn't close fingers in time |
| Positioning error | | Robot misses object by >2cm |
| Speed mismatch | | Too fast/slow vs. demonstration |
| Lighting drift | | Different from training conditions |
| Object variation | | Object in slightly different position |

### Root Cause Analysis

**Most common failure:**

**Hypothesis:** 

**Fix:** 

### Next Steps

- [ ] Collect N more demos targeting [specific failure]
- [ ] Change [lighting/camera/setup] to [fix]
- [ ] Retrain with [augmentation/different policy]
- [ ] Test [specific hypothesis]

### Learning

What surprised you about how the real policy failed?
What would you do differently on the next task?
```

---

## Self-Check Questions

Before moving to Chapter 10:

1. You have 100 demonstrations, 82% success in training, 45% on real robot. Enumerate 5 possible causes in order of likelihood.
2. Your policy succeeds when the object is in the training position (marked spot) but fails 5cm away. What's the fix?
3. Motor error beeps appear during policy execution. What's happening and what do you check?
4. Your 30 Hz policy causes jerky motion on the robot. The arm seems to "teleport" between positions. What's happening?
5. You want to improve from 60% to 90% success rate. You have time for either: (a) collecting 100 more demos, or (b) fixing the lighting to be more consistent. Which do you try first?

**Answers:**
1. (1) Lighting difference — train vs. test. (2) Camera position shifted. (3) Object position slightly different from training distribution. (4) Action frequency mismatch (policy Hz ≠ deployment Hz). (5) Overfitting — policy not generalizing.
2. Add positional variation to your training data: place the object at 5–10 different positions within a 10cm region and collect demos from each. The policy needs to see variation to handle it.
3. Motor beeps = torque limit hit or position error limit exceeded. Check: (a) policy is commanding positions within joint limits, (b) policy is not commanding positions that require too-fast motion, (c) motor cables are not snagged, (d) reduce max speed in config.
4. Action chunk execution. The policy predicts `k` future actions (chunk), executes them, then predicts again. If chunk size is large and motion is fast, you see discrete "jumps" at chunk boundaries. Fix: reduce chunk size or use temporal ensembling (average overlapping chunks).
5. Fix lighting first. Lighting issues cause complete failure regardless of data quantity. Adding more demos under inconsistent lighting just adds more noise to a broken setup. Fix the environment, then add data.

---

## What's Next

Chapter 10 is your capstone — building a complete end-to-end system using everything you've learned. Pick the project that matches your interests and available hardware.
