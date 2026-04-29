# Improving Sim-to-Real Gap in Ch4

## The Problem
The SmolVLA checkpoint was trained on real SO-101 photos with:
- **Objects**: Pink lego brick (2x2 studs) + transparent plastic box
- **Cameras**: Top-down "up" and side "side" views
- **Instruction**: "pink lego brick into the transparent box"

Current MuJoCo scene has a generic green box → domain gap.

## Solution: Create Matching MuJoCo Scene

### Step 1: Model the Correct Objects

Add to the SO-101 MuJoCo XML (or create a separate scene):

```xml
<!-- Pink Lego Brick (2x2 studs: ~32mm x 32mm x 19mm) -->
<body name="lego_brick" pos="0.25 0.1 0.02">
  <geom type="box" size="0.016 0.016 0.0095" 
        rgba="0.9 0.2 0.3 1.0"  <!-- pink -->
        friction="1.0 0.5 0.5"
        mass="0.002"/>
  <!-- Lego studs (optional, for realism) -->
  <site name="lego_grasp" pos="0 0 0.01" size="0.01"/>
</body>

<!-- Transparent Box (e.g., 100mm cube with thin walls) -->
<body name="transparent_box" pos="0.35 0.1 0.05">
  <geom type="box" size="0.05 0.05 0.05"
        rgba="0.8 0.9 1.0 0.3"  <!-- transparent blue-tint -->
        contype="0" conaffinity="0"  <!-- no collision, visual only -->
        mass="0.05"/>
  <!-- Inner region where brick should go -->
  <site name="box_center" pos="0 0 0.05" size="0.01"/>
</body>
```

### Step 2: Match Camera Poses

The current `interact_so101.py` has:
```python
"up":   pos=[0.25, 0.1, 0.9]   lookat=[0.25, 0.1, 0.0]   # top-down
"side": pos=[0.7, -0.5, 0.4]   lookat=[0.15, 0.05, 0.15]  # side
```

These should match the real SO-101 camera calibration. If you have the real robot:
1. Measure camera positions relative to robot base
2. Update `CAM_CONFIGS` in `interact_so101.py`

### Step 3: Improve Render Realism

In `interact_so101.py`, the renderer could be enhanced:

```python
# Add realistic rendering options
renderer = mujoco.Renderer(model, height=IMG_H, width=IMG_W)
# Enable shadow, better lighting in XML:
# <visual>
#   <quality shadowsize="4096"/>
#   <global offwidth="800" offheight="800"/>
# </visual>
```

### Step 4: Test the Improved Scene

```bash
cd workspace/vla/ch04
# Modify interact_so101.py to use new scene XML with lego + box
uv run --extra smolvla python interact_so101.py
# Type: "pink lego brick into the transparent box"
```

## Expected Improvement

| Gap Type | Before | After |
|----------|--------|-------|
| Object matching | ❌ Green box | ✅ Pink lego + transparent box |
| Camera pose | ⚠️ Approximate | ✅ Matched to real |
| Visual realism | ❌ Pure CG | ⚠️ Better materials |
| Photo realism | ❌ Synthetic | ❌ Still synthetic |

**Result**: The arm should perform *better* but may still fail due to the remaining visual gap (real photos vs synthetic renders). This is actually a great teaching moment for Ch5 (real hardware).

## Alternative: Domain Randomization (Advanced)

For full sim-to-real transfer, fine-tune with domain-randomized synthetic data:

```python
# During fine-tuning, randomize:
# - Lighting conditions
# - Object colors/textures  
# - Camera noise
# - Background variations
```

This requires modifying Project C (fine-tuning) in Ch4.

## Recommendation for Course

1. **Quick fix**: Update the MuJoCo scene with correct objects (pink lego + transparent box)
2. **Keep the narrative**: Even with better objects, sim won't match real perfectly → motivates Ch5
3. **Teaching moment**: Show that object matching helps, but visual domain gap remains

The current approach (Ch4 sim, Ch5 real) is pedagogically sound. The sim demonstrates the *interface* works (arm moves purposefully), while real hardware closes the gap completely.
