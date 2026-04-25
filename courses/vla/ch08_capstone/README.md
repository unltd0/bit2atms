# Chapter 8 — Capstone Projects

**Time:** 2–4 weeks depending on capstone choice
**Hardware:** Varies by capstone (see each option)
**Prerequisites:** Chapters 1–7 (or at least the chapters relevant to your chosen capstone)

---

## What are we here for

You've built up every component: sim, control, IK, RL, IL, VLA, sim-to-real, ROS 2,
and hardware. The capstone is where you integrate them into a complete system that solves
a real manipulation problem end-to-end.

Pick one capstone based on your hardware access and interests. Each is designed to take
2–4 weeks and produce something you can demo and put in a portfolio.

**How to choose:**

| Capstone | Hardware | Core skills exercised |
|----------|----------|----------------------|
| A — Open-Vocab Pick-and-Place | SO-101 + camera + GPU | VLA + perception + IK |
| B — Sim-to-Real Study | No real robot, GPU | DR + policy evaluation |
| C — VLA Fine-tuning at Scale | SO-101 + GPU 16 GB+ | Data collection + fine-tuning |
| D — Bimanual Manipulation | 2× SO-101 | Coordination + IL |

---

## Capstone A — Open-Vocabulary Pick-and-Place

**Problem:** A robot arm picks up objects specified by natural language ("pick up the red
cube", "move the blue bottle") from an unstructured scene.

**Hardware:** SO-101 + RealSense D435 depth camera + GPU 8 GB+

### Architecture

```text
language instruction
      ↓
 Grounded SAM 2 ── RGB image ──→ segmentation mask
      ↓
  depth image ──────────────────→ 3D object position
      ↓
   IK (Pink) ──────────────────→ joint angles
      ↓
  LeRobot policy ─────────────→ grasp + place execution
```

### Milestones

**Week 1 — Perception pipeline**
- Set up RealSense D435; verify depth-RGB alignment
- Run Grounded SAM 2 on live RGB stream; verify segmentation for your object set
- Implement depth-to-3D conversion using camera intrinsics

**Week 2 — Grasp planning**
- Integrate perception output with Pink IK
- Build a MuJoCo sim version of the pipeline (use virtual camera)
- Test in sim: "pick up the red cube" → correct 3D position → IK → motion

**Week 3 — Real robot integration**
- Deploy on SO-101 hardware; run perception → IK → execute loop
- Hand-eye calibration: compute camera-to-robot-base transform
- Test 10 pick attempts for 3 different objects

**Week 4 — Evaluation**
- Run 50 trials across 5 objects and 3 positions each
- Measure success rate, identify failure modes, iterate

### Key code — perception pipeline

```python workspace/vla/ch08/perception.py
"""
Grounded SAM 2 + RealSense depth → 3D object position.
Used in Capstone A perception pipeline.
"""
import numpy as np
import pyrealsense2 as rs

def get_3d_position(mask: np.ndarray, depth_frame, intrinsics) -> np.ndarray:
    """Convert a 2D segmentation mask to a 3D centroid using depth."""
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None

    cx, cy = int(xs.mean()), int(ys.mean())
    depth   = depth_frame.get_distance(cx, cy)

    if depth == 0:
        # Fallback: median of non-zero depth in mask region
        depths = [depth_frame.get_distance(x, y) for x, y in zip(xs, ys)
                  if depth_frame.get_distance(x, y) > 0]
        depth = np.median(depths) if depths else 0.5

    point_3d = rs.rs2_deproject_pixel_to_point(intrinsics, [cx, cy], depth)
    return np.array(point_3d)

def run_realsense_pipeline():
    """Start RealSense pipeline. Returns pipeline and aligned streams."""
    pipeline = rs.pipeline()
    config   = rs.config()
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16,  30)
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

    profile  = pipeline.start(config)
    align    = rs.align(rs.stream.color)
    return pipeline, align, profile

if __name__ == "__main__":
    pipeline, align, profile = run_realsense_pipeline()
    print("RealSense pipeline running. Press Ctrl+C to stop.")
    try:
        while True:
            frames        = pipeline.wait_for_frames()
            aligned       = align.process(frames)
            color_frame   = aligned.get_color_frame()
            depth_frame   = aligned.get_depth_frame()
            if not color_frame or not depth_frame:
                continue
            intrinsics = depth_frame.profile.as_video_stream_profile().intrinsics
            print(f"Frame: {np.array(color_frame.get_data()).shape}  "
                  f"depth at center: {depth_frame.get_distance(320, 240):.3f}m")
    except KeyboardInterrupt:
        pipeline.stop()
```

### Hand-eye calibration

The camera is mounted on or near the robot. To convert object positions from camera frame
to robot base frame you need the camera-to-base transform. Procedure:

1. Move the end-effector to 10 known positions (use IK to command them)
2. At each position, detect a calibration target (checkerboard) in the camera image
3. Use `cv2.calibrateHandEye()` to solve for the camera-to-base transform
4. Save the transform; apply it in `get_3d_position()` before passing to IK

---

## Capstone B — Sim-to-Real Transfer Study

**Problem:** Quantify the sim-to-real gap for a manipulation policy and measure what
techniques close it.

**Hardware:** GPU (no real robot required)

### Experimental design

Train the same base policy (ACT on gym_pusht or a custom MuJoCo task) under five
conditions:

| Condition | Description |
|-----------|-------------|
| Baseline | Trained in nominal sim, evaluated in nominal sim |
| Sim DR | Trained with physics DR, evaluated in nominal sim |
| Visual DR | Trained with image augmentation, evaluated in nominal sim |
| Sim+Visual DR | Both DR types |
| Simulated reality gap | Evaluate baseline in a modified sim (different mass, different textures) |

### Milestones

**Week 1:** Choose task (gym_pusht or custom MuJoCo reach/push task). Train baseline.
Establish eval protocol: 100 trials, fixed seed range.

**Week 2:** Train DR variants. Document training time and nominal performance for each.

**Week 3:** Evaluate all conditions on the "simulated real" environment.
Build comparison table.

**Week 4:** Write a concise study report: what DR buys, what it costs, recommendations for
real deployment. Include learning curves and robustness heatmaps.

### Deliverable

A 2-page report + figures:
- Learning curves for all 5 conditions
- Robustness heatmap (mass × damping) for baseline and best DR condition
- Success rate table: nominal vs. simulated reality gap
- Recommendation: which DR strategy to use and why

---

## Capstone C — VLA Fine-tuning at Scale

**Problem:** Fine-tune SmolVLA on a real-robot task with enough data and task variation
to get robust generalization.

**Hardware:** SO-101 + GPU 16 GB+ (Colab A100 works)

### Task design

Pick a task with 5 variations (different object colors, positions, or target locations).
Collect 100 demos per variation = 500 total.

| Variation | Description | Demos |
|-----------|-------------|-------|
| V1 | Red cube, left of center | 100 |
| V2 | Red cube, right of center | 100 |
| V3 | Blue cube, center | 100 |
| V4 | Mixed colors, left | 100 |
| V5 | Mixed colors, right | 100 |

### Eval protocol

| Metric | How |
|--------|-----|
| In-distribution success | 20 trials per variation = 100 total |
| OOD generalization | 5 novel object colors × 20 trials |
| Language robustness | 3 paraphrases per instruction × 20 trials |

### Milestones

**Week 1–2:** Collect 500 demonstrations across 5 variations.
Review dataset: verify balance, quality, and language instruction consistency.

**Week 2–3:** Fine-tune SmolVLA. Experiment with checkpoint frequency.
Compare 50-demo vs. 500-demo fine-tuning.

**Week 3–4:** Evaluate against protocol. Compare with ACT trained on same data.

---

## Capstone D — Bimanual Manipulation

**Problem:** Some tasks require two arms — folding, assembly, handing off objects.
Build a bimanual system from sim through real deployment.

**Hardware:** 2× SO-101 + GPU 8 GB+

### What bimanual adds

Bimanual coordination introduces new challenges: the two arms must be synchronized, the
action space doubles, and demonstrations require two simultaneous teleoperation inputs.
LeRobot supports bimanual configs natively.

### Milestones

**Week 1 — Sim setup:**
- Build a bimanual MuJoCo environment (two arms, shared workspace)
- Implement a scripted oracle for a simple handoff task
- Collect 50 sim demos; verify the dataset has both arm observations

**Week 2 — Policy training:**
- Train ACT-bimanual on sim demos
- Verify both arms execute coordinated actions
- Identify failure modes specific to bimanual (timing, collision)

**Week 3 — Real hardware:**
- Set up dual SO-101 with leader/follower teleoperation for both arms
- Collect 100 real bimanual demos
- Train and deploy

**Week 4 — Evaluation:**
- 20 real trials; measure success rate and failure breakdown
- Ablation: what happens with single-arm policy on bimanual task?

### Bimanual MuJoCo template

```python workspace/vla/ch08/bimanual_env.py
"""
Two SO-101 arms in a shared MuJoCo workspace for bimanual tasks.
Placeholder — fill in actual arm MJCF paths from Menagerie.
"""
import numpy as np
import mujoco

BIMANUAL_XML = """
<mujoco>
  <option timestep="0.002"/>
  <worldbody>
    <body name="left_base"  pos="-0.3 0 0">
      <!-- left arm: include SO-101 MJCF here -->
    </body>
    <body name="right_base" pos=" 0.3 0 0">
      <!-- right arm: include SO-101 MJCF here -->
    </body>
    <body name="object" pos="0 0.3 0.05">
      <freejoint/>
      <geom type="box" size="0.03 0.03 0.03"/>
    </body>
  </worldbody>
</mujoco>
"""

if __name__ == "__main__":
    model = mujoco.MjModel.from_xml_string(BIMANUAL_XML)
    data  = mujoco.MjData(model)
    print(f"Bodies: {model.nbody}  Joints: {model.njnt}  Actuators: {model.nu}")
```

---

## Self-Check (all capstones)

1. You reach 70% success rate on your capstone task. What's your next step?
   **Answer:** Run failure analysis — record 30 failures, categorize them, identify the
   dominant failure mode, collect targeted data for it. Random data collection has
   diminishing returns at this success rate.

2. Your capstone involves a novel object the policy hasn't seen. What technique helps most?
   **Answer:** For ACT/Diffusion: collect demos with that object. For SmolVLA fine-tuning:
   add the object to your training variation set. There's no substitute for demonstration
   coverage of the test distribution.

3. Your system works in controlled conditions but fails in a demo when someone walks by.
   Why, and how do you fix it?
   **Answer:** Visual distraction — the policy attends to motion or appearance changes in
   the background. Fix: crop observations to the relevant region, or add background
   randomization during training.

4. You want to add a second camera for better depth estimation. What changes in your pipeline?
   **Answer:** You need a new observation key in the dataset, retrain the policy with
   the additional input, and re-collect demos with both cameras active. Policy architecture
   may also need updating to handle multi-camera input.

5. Describe the full data flow from camera image to joint torque in your system.
   **Answer:** Camera → image preprocessing (resize, normalize) → policy network
   (vision encoder + action decoder) → predicted joint positions/velocities → position
   actuator or motor PD controller → joint torques → motors.

---

## Common Mistakes

- **Skipping the sim version of a capstone:** Always build and validate in sim first,
  even for hardware capstones. Sim is free; real-robot debugging time is not.

- **Collecting all demos before testing the pipeline:** Collect 10 demos, train, deploy.
  Verify the pipeline end-to-end before investing in full data collection.

- **Inconsistent eval protocol:** Same object setup, same lighting, same number of trials
  — every time. If conditions drift, your success rate numbers are meaningless.

- **Ignoring latency:** Real deployment has latency — camera → processing → action. If
  your policy was trained at 30 fps but inference takes 50 ms, you're effectively running
  at 20 fps. Measure and match.

---

## Resources

1. [LeRobot hardware examples](https://huggingface.co/docs/lerobot) — complete real-robot pipelines
2. [Grounded SAM 2](https://github.com/IDEA-Research/Grounded-SAM-2) — open-vocabulary segmentation
3. [Intel RealSense SDK](https://github.com/IntelRealSense/librealsense) — depth camera Python API
4. [ACT paper](https://arxiv.org/abs/2304.13705) — bimanual experiments in Section 5
