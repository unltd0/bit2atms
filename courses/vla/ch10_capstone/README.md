# Chapter 10 — Capstone: Full Manipulation Pipelines

**Time:** 2–4 weeks
**Hardware:** Varies by capstone (see each option)
**Prerequisites:** Chapters 1–7 minimum. Chapter 9 for capstones A and C.

---

## What This Chapter Is About

The capstone ties everything together. You'll build a complete, end-to-end robot manipulation system from scratch — not a tutorial, not a demo from someone else's paper, but your own working system.

This is where real engineering happens: components that worked independently start interacting, failure modes multiply, and debugging requires understanding the whole stack.

**Choose one capstone.** Each is designed to take 2–4 weeks. Don't try to do more than one simultaneously.

---

## How to Choose

| Capstone | Hardware Needed | Core Skill | Difficulty |
|----------|----------------|-----------|-----------|
| A — Open-Vocabulary Pick-and-Place | SO-101 + RealSense D435 | Perception + integration | ★★★★ |
| B — Sim-to-Real Study | Simulation only (GPU) | Rigorous evaluation | ★★★ |
| C — VLA Fine-tuning at Scale | SO-101 + 16GB GPU | Data + training | ★★★★ |
| D — Bimanual Manipulation | 2× SO-101 or simulation | Multi-arm control | ★★★★★ |

**Start with B if:** you have no physical hardware or want to deepen simulation skills.
**Start with A if:** you have hardware and want the most satisfying end-to-end experience.

---

## Capstone A — Open-Vocabulary Pick-and-Place

### What You'll Build

A complete manipulation system that takes natural language commands and picks and places objects:

```
"Pick up the red cube" 
        ↓
  [Language parser]
        ↓
  [Grounded SAM 2 — visual grounding]
        ↓
  [RealSense depth → 3D position]
        ↓
  [Pink IK → trajectory]
        ↓
  [ACT policy → grasp execution]
        ↓
  Real robot picks the cube
```

### Hardware

- SO-101 or Koch v1.1 arm (~$250–300)
- Intel RealSense D435 depth camera (~$200)
- NVIDIA GPU 8+ GB
- Total additional cost: ~$200 (camera)

### Architecture

**Component 1: Visual Grounding**

Grounded SAM 2 takes a text description ("red cube") and an image and segments the object:

```python
from sam2.build_sam import build_sam2
from sam2.grounded_sam2 import GroundedSAM2

# Text-conditioned segmentation
segments = model.predict(
    image=rgb_frame,
    text_prompt="red cube",
)
# Returns: mask, bounding box, confidence
```

**Component 2: 3D Localization**

Use the RealSense depth image + camera intrinsics to get 3D position from the 2D mask centroid:

```python
def pixel_to_3d(u, v, depth_image, camera_intrinsics):
    """Convert pixel (u,v) + depth to 3D point in camera frame."""
    fx, fy = camera_intrinsics.fx, camera_intrinsics.fy
    cx, cy = camera_intrinsics.ppx, camera_intrinsics.ppy
    Z = depth_image[v, u] / 1000.0  # mm to meters
    X = (u - cx) * Z / fx
    Y = (v - cy) * Z / fy
    return np.array([X, Y, Z])
```

**Component 3: Camera-to-Robot Transform**

The 3D point is in the camera frame. You need it in the robot base frame.

This requires an **extrinsic calibration** (hand-eye calibration):
- Measure: where is the camera relative to the robot base?
- Result: a 4×4 transform `T_robot_to_camera`

Easiest approach for a mounted camera: place a known calibration target at known positions, measure with both camera and IK, solve for the transform.

**Component 4: IK + Trajectory**

Use the Pink IK solver (Chapter 3) to compute the grasp trajectory:
1. Pre-grasp: 15cm above the object
2. Descend to grasp height
3. Close gripper
4. Lift

**Component 5: Execution**

Two options:
- **Scripted execution:** Use IK + PD control directly (no learned policy needed for simple pick)
- **Policy execution:** Use ACT trained on pick demonstrations (better for deformable or variable objects)

### Implementation Milestones

**Week 1: Perception pipeline**
1. Get RealSense working: stream RGB + depth
2. Install Grounded SAM 2 and test on static images
3. Test on live camera feed: does it correctly segment "red cube"?
4. Test 3D localization: place cube at known positions, verify depth accuracy

**Week 2: Robot integration**
1. Perform hand-eye calibration
2. Test camera-to-robot coordinate transform: point at cube, verify robot frame position
3. Execute scripted pick trajectory to camera-detected cube position
4. Success criterion: robot picks cube detected by camera 8/10 times

**Week 3: Language interface + ACT**
1. Collect 50 demonstrations of pick-and-place
2. Train ACT policy
3. Connect: language → visual grounding → 3D position → ACT execution
4. Test with 10 different object phrasings

**Week 4: Hardening**
1. Test with 5 different objects
2. Test with different lighting conditions
3. Test with occluded objects
4. Document failure modes

---

### Key Code: Perception Pipeline

Create `learning/ch10_capstone/capstone_a/perception.py`:

```python
"""
Complete perception pipeline for open-vocabulary pick-and-place.
Combines Grounded SAM 2 + RealSense D435.
"""
import numpy as np
import cv2
import pyrealsense2 as rs

# Install: pip install pyrealsense2
# Install Grounded SAM 2: follow https://github.com/IDEA-Research/Grounded-SAM-2


class RealSenseCamera:
    """Wrapper for Intel RealSense D435 RGB-D camera."""

    def __init__(self, width=640, height=480, fps=30):
        self.pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)
        config.enable_stream(rs.stream.color, width, height, rs.format.rgb8, fps)
        self.profile = self.pipeline.start(config)

        # Get camera intrinsics
        depth_sensor = self.profile.get_device().first_depth_sensor()
        self.depth_scale = depth_sensor.get_depth_scale()
        color_stream = self.profile.get_stream(rs.stream.color)
        self.intrinsics = color_stream.as_video_stream_profile().get_intrinsics()

        # Alignment object: align depth to color frame
        self.align = rs.align(rs.stream.color)

        print(f"Camera initialized: {width}×{height} @ {fps}fps")
        print(f"Depth scale: {self.depth_scale}")

    def get_frames(self):
        """Get aligned RGB and depth frames."""
        frames = self.pipeline.wait_for_frames()
        aligned = self.align.process(frames)
        color_frame = aligned.get_color_frame()
        depth_frame = aligned.get_depth_frame()

        if not color_frame or not depth_frame:
            return None, None

        rgb = np.asanyarray(color_frame.get_data())
        depth = np.asanyarray(depth_frame.get_data())  # uint16, in mm
        return rgb, depth

    def pixel_to_camera_3d(self, u, v, depth_mm):
        """Convert pixel coordinates and depth to 3D point in camera frame (meters)."""
        depth_m = depth_mm * self.depth_scale if self.depth_scale else depth_mm / 1000.0
        point_3d = rs.rs2_deproject_pixel_to_point(
            self.intrinsics, [u, v], depth_m)
        return np.array(point_3d)

    def get_object_3d_position(self, mask, depth_image):
        """
        Given a binary mask, return the 3D centroid of the masked region.
        """
        ys, xs = np.where(mask > 0)
        if len(xs) == 0:
            return None

        # Use median depth in the mask (robust to noise)
        depths = depth_image[ys, xs]
        valid = depths[(depths > 100) & (depths < 5000)]  # 10cm to 5m range
        if len(valid) < 10:
            return None

        median_depth = np.median(valid)
        cx = int(np.median(xs))
        cy = int(np.median(ys))

        return self.pixel_to_camera_3d(cx, cy, median_depth)

    def stop(self):
        self.pipeline.stop()


class ObjectDetector:
    """Open-vocabulary object detection using Grounded SAM 2."""

    def __init__(self):
        # Import here to avoid error if not installed
        try:
            from groundingdino.util.inference import load_model, predict
            self.grounding_dino_available = True
        except ImportError:
            print("Grounded SAM 2 not installed.")
            print("Install: https://github.com/IDEA-Research/Grounded-SAM-2")
            self.grounding_dino_available = False

    def detect(self, rgb_image, text_prompt, confidence_threshold=0.3):
        """
        Detect and segment object described by text_prompt.

        Returns:
            mask: binary numpy array HxW
            bbox: [x1, y1, x2, y2] or None
            confidence: float or None
        """
        if not self.grounding_dino_available:
            # Fallback: return center region (for testing without Grounded SAM 2)
            h, w = rgb_image.shape[:2]
            mask = np.zeros((h, w), dtype=np.uint8)
            mask[h//4:3*h//4, w//4:3*w//4] = 1
            return mask, [w//4, h//4, 3*w//4, 3*h//4], 0.5

        # Full implementation with Grounded SAM 2
        # Follow the Grounded SAM 2 example notebooks for this
        raise NotImplementedError("See Grounded SAM 2 documentation for full implementation")


class PickPipeline:
    """
    Complete perception pipeline:
    text instruction → 3D object position in robot base frame
    """

    def __init__(self, T_camera_to_robot: np.ndarray):
        """
        T_camera_to_robot: 4x4 transform from camera frame to robot base frame.
        Obtained from hand-eye calibration.
        """
        self.camera = RealSenseCamera()
        self.detector = ObjectDetector()
        self.T_camera_to_robot = T_camera_to_robot

    def localize(self, text_description: str):
        """
        Given a text description, return the 3D position of the object
        in the robot base frame.

        Returns: np.array([x, y, z]) or None if object not found
        """
        rgb, depth = self.camera.get_frames()
        if rgb is None:
            return None

        mask, bbox, confidence = self.detector.detect(rgb, text_description)
        if bbox is None or confidence < 0.3:
            print(f"Object '{text_description}' not detected (confidence={confidence:.2f})")
            return None

        # 3D position in camera frame
        pos_camera = self.camera.get_object_3d_position(mask, depth)
        if pos_camera is None:
            print("Could not get 3D position (depth failure)")
            return None

        # Transform to robot base frame
        pos_hom = np.append(pos_camera, 1.0)
        pos_robot = (self.T_camera_to_robot @ pos_hom)[:3]

        print(f"Detected '{text_description}': robot frame = {pos_robot.round(3)}")
        return pos_robot

    def stop(self):
        self.camera.stop()
```

### Hand-Eye Calibration Procedure

Create `learning/ch10_capstone/capstone_a/calibrate_camera.py`:

```python
"""
Hand-eye calibration: determine transform from camera to robot base.
Method: move robot to N known positions, record camera observations of a marker.

Setup:
1. Attach an ArUco marker to the robot end-effector
2. Place the camera so it can see the marker at multiple robot poses
3. Run this script: move robot to each pose, record
"""
import numpy as np
import cv2
import cv2.aruco as aruco

ARUCO_DICT = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
ARUCO_PARAMS = aruco.DetectorParameters()

def detect_aruco_pose(rgb_image, camera_matrix, dist_coeffs, marker_size_m=0.05):
    """Detect ArUco marker and return its pose in camera frame."""
    gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
    corners, ids, _ = aruco.detectMarkers(gray, ARUCO_DICT, parameters=ARUCO_PARAMS)

    if ids is None or len(ids) == 0:
        return None, None

    rvecs, tvecs, _ = aruco.estimatePoseSingleMarkers(
        corners, marker_size_m, camera_matrix, dist_coeffs)

    # Return pose of first detected marker
    rvec, tvec = rvecs[0][0], tvecs[0][0]
    R, _ = cv2.Rodrigues(rvec)
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = tvec
    return T, (corners[0], ids[0])


def calibrate_hand_eye(robot_ee_poses, camera_marker_poses):
    """
    Solve AX = XB hand-eye calibration.

    robot_ee_poses: list of 4x4 transforms (robot base → EE) for each calibration pose
    camera_marker_poses: list of 4x4 transforms (camera → marker) for each pose

    Returns: T_camera_to_robot (4x4)
    """
    # Use OpenCV's hand-eye calibration
    R_gripper2base = [T[:3, :3] for T in robot_ee_poses]
    t_gripper2base = [T[:3, 3] for T in robot_ee_poses]
    R_target2cam = [T[:3, :3] for T in camera_marker_poses]
    t_target2cam = [T[:3, 3] for T in camera_marker_poses]

    R_cam2base, t_cam2base = cv2.calibrateHandEye(
        R_gripper2base, t_gripper2base,
        R_target2cam, t_target2cam,
        method=cv2.CALIB_HAND_EYE_TSAI
    )

    T_camera_to_robot = np.eye(4)
    T_camera_to_robot[:3, :3] = R_cam2base
    T_camera_to_robot[:3, 3] = t_cam2base.flatten()

    return T_camera_to_robot


def interactive_calibration():
    """
    Interactive procedure for hand-eye calibration.
    Guides user through collecting calibration poses.
    """
    print("=== Hand-Eye Calibration ===")
    print("Attach ArUco marker (4x4, ID 0) to robot end-effector.")
    print("You need camera_matrix and dist_coeffs from camera calibration.")
    print("\nProcedure:")
    print("1. Move robot to a pose where camera can see the ArUco marker")
    print("2. Press Enter to record the pose")
    print("3. Repeat for at least 8 different poses (vary position AND orientation)")
    print("4. Press 'q' to finish and compute calibration\n")

    # These come from camera intrinsic calibration (OpenCV calibrateCamera)
    # Placeholder values — run actual camera calibration first
    camera_matrix = np.array([
        [615.0, 0.0, 320.0],
        [0.0,   615.0, 240.0],
        [0.0,   0.0,   1.0]
    ])
    dist_coeffs = np.zeros(5)

    robot_poses = []
    camera_poses = []

    # In a real implementation, integrate with robot API to read current EE pose
    print("NOTE: This is a template. Integrate with your robot's pose reading API.")
    print("For SO-101: use LeRobot's robot.get_ee_pose() method.")

    # ... integration code here ...

    if len(robot_poses) < 6:
        print(f"Need at least 6 poses, got {len(robot_poses)}. Skipping calibration.")
        return None

    T = calibrate_hand_eye(robot_poses, camera_poses)
    np.save("T_camera_to_robot.npy", T)
    print(f"\nCalibration result saved to T_camera_to_robot.npy")
    print(f"T_camera_to_robot:\n{T.round(4)}")
    return T


if __name__ == "__main__":
    interactive_calibration()
```

---

## Capstone B — Sim-to-Real Transfer Study

### What You'll Build

A rigorous experimental study of sim-to-real transfer:
1. Train policies in MuJoCo and Isaac Sim
2. Apply various domain randomization schemes
3. Evaluate on held-out parameter sets (simulating "real world" variation)
4. Write a 3-page technical report with quantitative results

This capstone is valuable even without physical hardware — you'll develop the analytical tools that robotics engineers use before any real deployment.

### Hardware

- GPU 8+ GB (RTX 3060 or better)
- No physical hardware required

### Experimental Design

**Baseline:** Train without DR on nominal parameters. Evaluate at nominal.

**Ablations:**
1. Physics DR only (mass, friction, damping)
2. Visual DR only (lighting, textures, colors)
3. Combined DR
4. Adaptive DR (curriculum: start small, grow range)

**Evaluation:** Grid of (mass_scale, friction_scale) combinations. Success rate heatmap at each combination.

**Metric:** "Transfer robustness score" = average success rate across all non-nominal parameter combinations (weighted by proximity to nominal).

### Week-by-Week Plan

**Week 1:** Baseline experiments
- Train SAC+HER on FetchReach, FetchPush, and your custom environment
- Measure robustness using the tool from Chapter 7
- Document: which environments transfer better and why?

**Week 2:** DR ablations
- Physics DR: mass ±50%, friction ±80%, damping ±100%
- Visual DR: color jitter, texture randomization, camera noise
- Combined: all together
- Measure robustness for each condition

**Week 3:** Adaptive curriculum DR
- Implement curriculum where DR range increases over training
- Compare: fixed DR vs. adaptive DR learning curves

**Week 4:** Report
- Quantitative comparison table
- Robustness heatmaps for each condition
- Analysis: which DR component matters most?

Create `learning/ch10_capstone/capstone_b/experiment_runner.py`:

```python
"""
Automated experiment runner for sim-to-real study.
Runs all ablations and collects results in a structured format.
"""
import json
import os
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

EXPERIMENTS = {
    "baseline": {
        "use_physics_dr": False,
        "use_visual_dr": False,
        "dr_scale": 0.0,
    },
    "physics_dr_small": {
        "use_physics_dr": True,
        "use_visual_dr": False,
        "dr_scale": 0.2,
    },
    "physics_dr_large": {
        "use_physics_dr": True,
        "use_visual_dr": False,
        "dr_scale": 0.5,
    },
    "visual_dr": {
        "use_physics_dr": False,
        "use_visual_dr": True,
        "dr_scale": 0.3,
    },
    "combined_dr": {
        "use_physics_dr": True,
        "use_visual_dr": True,
        "dr_scale": 0.4,
    },
}


def run_all_experiments(total_steps=200_000, output_dir="./capstone_b_results"):
    os.makedirs(output_dir, exist_ok=True)
    results = {}

    for exp_name, config in EXPERIMENTS.items():
        print(f"\n{'='*50}")
        print(f"Running experiment: {exp_name}")
        print(f"Config: {config}")

        # This calls your training + evaluation functions from Chapter 7
        # Integrate with train_robust.py and evaluate_robustness()
        result = {
            "nominal_success_rate": 0.0,  # fill with actual training
            "robustness_score": 0.0,
            "config": config,
            "timestamp": datetime.now().isoformat(),
        }
        results[exp_name] = result

    # Save results
    with open(f"{output_dir}/results.json", 'w') as f:
        json.dump(results, f, indent=2)

    # Generate comparison plots
    generate_comparison_plots(results, output_dir)
    return results


def generate_comparison_plots(results, output_dir):
    names = list(results.keys())
    nominal_srs = [r["nominal_success_rate"] for r in results.values()]
    robustness_scores = [r["robustness_score"] for r in results.values()]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    colors = plt.cm.Set2(np.linspace(0, 1, len(names)))

    axes[0].bar(names, [s*100 for s in nominal_srs], color=colors)
    axes[0].set_ylabel("Success Rate (%)")
    axes[0].set_title("Success at Nominal Parameters\n(all should be high)")
    axes[0].tick_params(axis='x', rotation=45)

    axes[1].bar(names, [s*100 for s in robustness_scores], color=colors)
    axes[1].set_ylabel("Robustness Score (%)")
    axes[1].set_title("Robustness Across Parameter Variations\n(key metric for sim-to-real)")
    axes[1].tick_params(axis='x', rotation=45)

    plt.suptitle("Sim-to-Real Transfer Study: Domain Randomization Ablations", fontsize=13)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/experiment_comparison.png", dpi=150)
    plt.show()


if __name__ == "__main__":
    run_all_experiments()
```

---

## Capstone C — VLA Fine-tuning at Scale

### What You'll Build

A systematic study of VLA fine-tuning:
1. Collect 500 demonstrations across 5 task variations (real or sim)
2. Fine-tune SmolVLA and compare to ACT baseline
3. Test zero-shot generalization (new objects, new positions, new instructions)
4. Quantify when pretraining helps and when it doesn't

### Hardware

- SO-101 arm (real data collection, optional — can use sim)
- GPU 16+ GB (RTX 4080, A100, or Colab)
- Total cost: ~$250 hardware (optional) + compute

### Task Variations (collect 100 demos each)

1. Pick red block → fixed position
2. Pick blue block → fixed position
3. Pick any block → randomized positions (10cm radius)
4. Pick block → place in bowl (new destination)
5. Pick block with obstacle present

### Evaluation Protocol

For each policy and condition, run 50 trials:

| Condition | SmolVLA (zero-shot) | SmolVLA (fine-tuned) | ACT |
|-----------|--------------------|--------------------|-----|
| Training distribution | ? | ? | ? |
| New object color | ? | ? | ? |
| New object position (+10cm) | ? | ? | ? |
| New target position | ? | ? | ? |
| New language phrasing | ? | ? | N/A |

The key question: **At what data size and task variation does the VLA pretraining advantage disappear?**

---

## Capstone D — Bimanual Manipulation

### What You'll Build

A bimanual manipulation system in simulation (+ optionally real):
1. Set up a two-arm MuJoCo environment (ALOHA-style)
2. Design a bimanual task requiring coordination
3. Collect bimanual demonstrations via dual teleoperation
4. Train ACT-bimanual and evaluate arm coordination quality

### Hardware

- Simulation only: any GPU
- Real hardware: 2× SO-101 (leader + follower × 2 arms = ~$500)

### Bimanual MuJoCo Setup

The ALOHA 2 MuJoCo model is publicly available:

```bash
git clone https://github.com/aloha2/aloha2_mujoco  # check current repo
```

Or build your own two-arm scene:

```xml
<mujoco>
  <worldbody>
    <!-- Left arm -->
    <body name="left_base" pos="-0.3 0 0">
      <!-- ... left arm links ... -->
    </body>
    <!-- Right arm -->
    <body name="right_base" pos="0.3 0 0">
      <!-- ... right arm links ... -->
    </body>
    <!-- Shared workspace -->
    <geom name="table" type="box" size="0.4 0.3 0.01" pos="0 0.3 0"/>
  </worldbody>
</mujoco>
```

### Tasks Suitable for Bimanual

**Tier 1 (start here):**
- Handoff: left arm picks object, transfers to right arm
- Stabilize-and-insert: one arm holds a container, other arm inserts an object
- Two-handed lift: both arms lift an object too large for one arm

**Tier 2 (after Tier 1 works):**
- Cloth folding (requires coordination and tactile sensing)
- Jar opening (asymmetric forces)
- Tool use requiring two hands

### LeRobot Bimanual Support

LeRobot v0.5.0 supports bimanual collection and training:

```bash
# Data collection with dual SO-101
python -m lerobot.scripts.control_robot \
  --robot-path lerobot/configs/robot/so101_bimanual.yaml \
  --control.type=record \
  --control.num_episodes=100

# Training with bimanual ACT
python -m lerobot.scripts.train \
  policy=act_so101_bimanual \
  dataset_repo_id=local/bimanual_task
```

---

## Final Project Deliverables

Regardless of which capstone you choose, produce these:

**1. GitHub Repository**
```
capstone/
  README.md          # project overview, results, how to reproduce
  data/              # dataset samples or links
  configs/           # training configs
  scripts/           # all code
  results/           # evaluation logs, plots
  docs/              # technical write-up
```

**2. Technical Write-up (2–4 pages)**
- Problem statement: what task, why it's challenging
- Approach: architecture, training procedure, data collection
- Results: success rate tables, failure analysis
- Analysis: what worked, what didn't, what surprised you
- Next steps: what would you do with more time

**3. Demo Video (if real hardware)**
- 2–3 minute video
- Show: successful trials, failure cases, system overview
- Narrate what's happening

**4. Failure Analysis**

This is the most important part. For every failure mode:
- What's the failure?
- What causes it?
- What would fix it?

A write-up that honestly documents failures and their causes demonstrates deeper understanding than a write-up that only shows successes.

---

## Self-Check Questions for Chapter 10

1. Your open-vocabulary system detects the correct object but grasps 5cm off. What's the most likely cause?
2. Your bimanual policy succeeds 70% in simulation but the two arms don't coordinate well on real hardware. What's causing the asymmetry?
3. You fine-tune SmolVLA on 100 demos and get 85% success. ACT on 200 demos gets 88%. Should you switch to ACT?
4. In your sim-to-real study, combining physics DR + visual DR performs *worse* than either alone. Why might this happen?
5. How do you know when to stop collecting data and start deploying?

**Answers:**
1. Most likely: hand-eye calibration error. The camera's 3D position estimate is off by 5cm because the T_camera_to_robot transform is inaccurate. Fix: redo hand-eye calibration with more poses.
2. Real arm hardware differences: one motor has more backlash than its simulation model. Or: each arm's calibration has different systematic error. Fix: system identification for each arm separately; add small amounts of real data for each arm.
3. Depends on your use case. SmolVLA with 100 demos ≈ ACT with 200 demos → SmolVLA is 2× more sample efficient. If collecting data is expensive (real robot), SmolVLA is better. If data is cheap (simulation), ACT at large scale may eventually match.
4. Combined DR creates a much harder training distribution. The policy must be invariant to both physics and visual variation simultaneously → optimization harder → learns a more conservative policy → lower peak performance. Fix: use curriculum DR (start with no DR, gradually increase both separately).
5. Rule of thumb: when adding more data gives < 2% improvement per 50 additional demos over 2 consecutive rounds. At that point, data quality matters more than quantity — improve the setup, lighting, task consistency.
