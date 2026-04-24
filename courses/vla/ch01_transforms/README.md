# Chapter 1 — Foundations: Math, Coordinates, and Rigid Body Transforms

**Time:** 2–3 days
**Hardware:** Any laptop, no GPU
**Prerequisites:** Python, high-school linear algebra and trig

---

## Why This Chapter Exists

Every robotics library — MuJoCo, Pink, ROS 2, LeRobot — constantly passes around 4×4 matrices, quaternions, and named coordinate frames. If you don't have a concrete mental model of what these represent, you'll hit a wall in every subsequent chapter: you won't know why a policy output is in end-effector space vs. joint space, why a transform is inverted before being applied, or what it means to "express a point in the camera frame."

This chapter fills that gap before it becomes a blocker. You build the math from scratch so that when you encounter it later in a library, a paper, or a debugging session, it's recognition — not confusion.

### If you can answer these, you can skip this chapter

1. A wrist-mounted camera sees a cup at `[0.1, 0, 0.3]` in camera frame. You have the 4×4 wrist-to-world transform `T`. How do you get the cup's world position?
2. You have two rotation matrices `R_A` and `R_B`. What does `R_A @ R_B` represent — and does the order matter?
3. Why do robotics libraries prefer quaternions over Euler angles for representing orientation?

---

## Part 1 — Coordinate Frames

### What Is a Coordinate Frame?

A coordinate frame is an origin point plus three orthogonal axes (X, Y, Z). Everything in robotics is described relative to some frame.

There is always a **world frame** — the fixed reference. Then there are frames attached to each robot link, each object, and the camera. When you say "the cup is at position (0.3, 0.1, 0.05)", you always mean relative to some frame.

**Convention (robotics standard):**
- X axis → forward (red)
- Y axis → left (green)
- Z axis → up (blue)

This is called the right-hand coordinate system. If your right thumb points along X and your index finger along Y, your middle finger points along Z.

### Why Multiple Frames?

Consider a robot arm. The shoulder joint has a frame. The elbow has a frame. The wrist has a frame. The camera has a frame. When the arm moves, all these frames move with it.

To know where the end-effector is in the world, you chain the transforms: world → base → shoulder → elbow → wrist → end-effector.

This is the core operation you will implement.

---

## Part 2 — Rotation Matrices

### The Problem With Euler Angles

You might think: just store rotation as three angles (roll, pitch, yaw). This works for display but has problems for computation:
- Gimbal lock: at certain orientations you lose a degree of freedom
- Order matters: rotate X then Y is different from rotate Y then X
- Hard to chain: how do you compose two Euler angle rotations?

Rotation matrices solve all of these.

### What Is a Rotation Matrix?

A 3×3 matrix `R` that rotates a vector. If `v` is a vector in frame A, then `R @ v` is the same vector expressed in frame B.

Properties of a valid rotation matrix:
- `R.T @ R = I` (orthogonal: columns are unit vectors, mutually orthogonal)
- `det(R) = +1` (right-handed, not a reflection)

### Elementary Rotations

Rotation around the **Z axis** by angle θ:
```
Rz(θ) = [[cos θ, -sin θ, 0],
          [sin θ,  cos θ, 0],
          [0,      0,     1]]
```

Rotation around the **Y axis** by angle θ:
```
Ry(θ) = [[ cos θ, 0, sin θ],
          [ 0,     1, 0    ],
          [-sin θ, 0, cos θ]]
```

Rotation around the **X axis** by angle θ:
```
Rx(θ) = [[1, 0,      0    ],
          [0, cos θ, -sin θ],
          [0, sin θ,  cos θ]]
```

### Composing Rotations

To rotate by Rz first, then Ry: `R = Ry @ Rz`

**Important:** matrix multiplication is not commutative. Order matters. `Ry @ Rz ≠ Rz @ Ry`.

The combined rotation `R = R1 @ R2` means: first apply R2, then apply R1 (right-to-left).

### Euler Angles to Rotation Matrix

Roll-Pitch-Yaw (RPY) convention (used in robotics):
- Roll (φ): rotation around X
- Pitch (θ): rotation around Y
- Yaw (ψ): rotation around Z

`R_rpy = Rz(ψ) @ Ry(θ) @ Rx(φ)`

Different conventions exist (ZYX, XYZ, etc.). Always check which convention a library uses.

---

## Part 3 — Homogeneous Transforms

### The Problem With Rotation Alone

A rotation matrix can rotate a point but can't translate it. To fully describe the position and orientation of one frame relative to another, you need both rotation **and** translation.

### The 4×4 Homogeneous Transform

Pack rotation (3×3) and translation (3×1) into a single 4×4 matrix:

```
T = [[R00, R01, R02, tx],
     [R10, R11, R12, ty],
     [R20, R21, R22, tz],
     [0,   0,   0,   1 ]]
```

To transform a point `p = [x, y, z]`, represent it as `[x, y, z, 1]` (homogeneous coordinates) and multiply:

```
p_new = T @ [x, y, z, 1]
```

The `1` in the last row of `T` ensures the translation is applied correctly.

### Chaining Transforms

To go from frame A to frame C, via frame B:
```
T_A_to_C = T_A_to_B @ T_B_to_C
```

This is just matrix multiplication. Chains of 10 or 20 transforms reduce to a single matrix multiplication.

### Inverse Transform

If `T` transforms from frame A to frame B, then `T_inv` transforms from B to A:

```python
def invert_transform(T):
    R = T[:3, :3]
    t = T[:3, 3]
    T_inv = np.eye(4)
    T_inv[:3, :3] = R.T
    T_inv[:3, 3] = -R.T @ t
    return T_inv
```

This is faster and more numerically stable than `np.linalg.inv(T)`.

---

## Part 4 — Quaternions

### Why Quaternions?

Rotation matrices are great for computation but use 9 numbers to store 3 degrees of freedom. Quaternions use 4 numbers, are faster to compose, and don't have gimbal lock.

Most real-time robot systems store orientations as quaternions internally.

### What Is a Quaternion?

A quaternion `q = [w, x, y, z]` where:
- `w` is the scalar part
- `[x, y, z]` is the vector part
- `||q|| = 1` for unit quaternions (all rotations are unit quaternions)

Geometrically: a rotation of angle θ around unit axis `[ax, ay, az]`:
```
q = [cos(θ/2), ax·sin(θ/2), ay·sin(θ/2), az·sin(θ/2)]
```

### Quaternion to Rotation Matrix

```python
def quat_to_rot(q):
    w, x, y, z = q
    return np.array([
        [1-2*(y**2+z**2),  2*(x*y-w*z),    2*(x*z+w*y)  ],
        [2*(x*y+w*z),      1-2*(x**2+z**2), 2*(y*z-w*x)  ],
        [2*(x*z-w*y),      2*(y*z+w*x),    1-2*(x**2+y**2)]
    ])
```

### Rotation Matrix to Quaternion

The robust method (Shepperd's method):
```python
def rot_to_quat(R):
    trace = R[0,0] + R[1,1] + R[2,2]
    if trace > 0:
        s = 0.5 / np.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (R[2,1] - R[1,2]) * s
        y = (R[0,2] - R[2,0]) * s
        z = (R[1,0] - R[0,1]) * s
    else:
        # handle other cases (largest diagonal element)
        # ... (see full implementation in transforms.py)
    return np.array([w, x, y, z])
```

---

## Part 5 — Forward Kinematics

### What Is Forward Kinematics?

Given joint angles `[θ1, θ2, ..., θn]`, compute the position and orientation of the end-effector in the world frame.

For a simple 2D 3-link arm in the XY plane:
- Link 1: length L1, joint angle θ1 from world X axis
- Link 2: length L2, joint angle θ2 relative to link 1
- Link 3: length L3, joint angle θ3 relative to link 2

End-effector position:
```
x = L1·cos(θ1) + L2·cos(θ1+θ2) + L3·cos(θ1+θ2+θ3)
y = L1·sin(θ1) + L2·sin(θ1+θ2) + L3·sin(θ1+θ2+θ3)
```

Using transforms, this is cleaner and extends to 3D:
```python
T_world_to_ee = T01 @ T12 @ T23
```

Where each `Tij` is a 4×4 transform from joint i to joint j, parameterized by joint angle θ.

---

## External Resources

These are worth reading alongside this chapter:

1. **3Blue1Brown — Essence of Linear Algebra (YouTube)**
   Episodes 1–5 cover vectors, linear transformations, and matrices visually.
   Watch if you're rusty on what matrix multiplication means geometrically.
   → Search "3blue1brown essence of linear algebra" on YouTube

2. **Modern Robotics Textbook — Chapter 2 and 3 (free online)**
   The most rigorous treatment of configuration space and rigid body motion.
   Use as reference when you want the formal derivation.
   → https://hades.mech.northwestern.edu/index.php/Modern_Robotics

3. **Quaternions and 3D Rotation (interactive)**
   Visualize quaternion rotations interactively.
   → Search "quaternion visualization eater.net" or "3blue1brown quaternions"

---

## Project 1A — Build Your Transform Library

Create `learning/ch01_transforms/transforms.py`:

```python
import numpy as np

def rot_x(angle):
    """Rotation matrix around X axis."""
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[1, 0,  0],
                     [0, c, -s],
                     [0, s,  c]])

def rot_y(angle):
    """Rotation matrix around Y axis."""
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[ c, 0, s],
                     [ 0, 1, 0],
                     [-s, 0, c]])

def rot_z(angle):
    """Rotation matrix around Z axis."""
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, -s, 0],
                     [s,  c, 0],
                     [0,  0, 1]])

def rpy_to_rot(roll, pitch, yaw):
    """Roll-Pitch-Yaw to rotation matrix (ZYX convention)."""
    return rot_z(yaw) @ rot_y(pitch) @ rot_x(roll)

def make_transform(R, t):
    """Create 4x4 homogeneous transform from rotation matrix and translation."""
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = t
    return T

def invert_transform(T):
    """Efficiently invert a homogeneous transform."""
    R = T[:3, :3]
    t = T[:3, 3]
    T_inv = np.eye(4)
    T_inv[:3, :3] = R.T
    T_inv[:3, 3] = -R.T @ t
    return T_inv

def transform_point(T, p):
    """Apply transform T to 3D point p."""
    p_hom = np.append(p, 1.0)
    return (T @ p_hom)[:3]

def quat_to_rot(q):
    """Convert unit quaternion [w, x, y, z] to rotation matrix."""
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([
        [1-2*(y**2+z**2),  2*(x*y-w*z),    2*(x*z+w*y)   ],
        [2*(x*y+w*z),      1-2*(x**2+z**2), 2*(y*z-w*x)   ],
        [2*(x*z-w*y),      2*(y*z+w*x),    1-2*(x**2+y**2)]
    ])

def rot_to_quat(R):
    """Convert rotation matrix to unit quaternion [w, x, y, z]."""
    trace = R[0,0] + R[1,1] + R[2,2]
    if trace > 0:
        s = 2.0 * np.sqrt(trace + 1.0)
        w = 0.25 * s
        x = (R[2,1] - R[1,2]) / s
        y = (R[0,2] - R[2,0]) / s
        z = (R[1,0] - R[0,1]) / s
    elif R[0,0] > R[1,1] and R[0,0] > R[2,2]:
        s = 2.0 * np.sqrt(1.0 + R[0,0] - R[1,1] - R[2,2])
        w = (R[2,1] - R[1,2]) / s
        x = 0.25 * s
        y = (R[0,1] + R[1,0]) / s
        z = (R[0,2] + R[2,0]) / s
    elif R[1,1] > R[2,2]:
        s = 2.0 * np.sqrt(1.0 + R[1,1] - R[0,0] - R[2,2])
        w = (R[0,2] - R[2,0]) / s
        x = (R[0,1] + R[1,0]) / s
        y = 0.25 * s
        z = (R[1,2] + R[2,1]) / s
    else:
        s = 2.0 * np.sqrt(1.0 + R[2,2] - R[0,0] - R[1,1])
        w = (R[1,0] - R[0,1]) / s
        x = (R[0,2] + R[2,0]) / s
        y = (R[1,2] + R[2,1]) / s
        z = 0.25 * s
    return np.array([w, x, y, z])
```

Create `learning/ch01_transforms/test_transforms.py`:

```python
import numpy as np
from transforms import rot_x, rot_y, rot_z, rpy_to_rot, make_transform
from transforms import invert_transform, transform_point, quat_to_rot, rot_to_quat

def test_rotation_orthogonality():
    for angle in [0, 0.5, 1.0, np.pi/2, np.pi]:
        for R_fn in [rot_x, rot_y, rot_z]:
            R = R_fn(angle)
            assert np.allclose(R.T @ R, np.eye(3), atol=1e-10), f"Not orthogonal: {R_fn}"
            assert np.isclose(np.linalg.det(R), 1.0, atol=1e-10), f"Det != 1: {R_fn}"
    print("PASS: rotation matrices are orthogonal with det=1")

def test_rot_z_90():
    R = rot_z(np.pi / 2)
    p = np.array([1.0, 0.0, 0.0])
    result = R @ p
    assert np.allclose(result, [0.0, 1.0, 0.0], atol=1e-10), f"Got {result}"
    print("PASS: rot_z(90°) maps [1,0,0] to [0,1,0]")

def test_transform_chain():
    T1 = make_transform(rot_z(np.pi/2), np.array([1.0, 0.0, 0.0]))
    T2 = make_transform(np.eye(3), np.array([1.0, 0.0, 0.0]))
    T_chain = T1 @ T2
    result = transform_point(T_chain, np.zeros(3))
    assert np.allclose(result, [1.0, 1.0, 0.0], atol=1e-10), f"Got {result}"
    print("PASS: transform chain works")

def test_invert_transform():
    R = rot_z(0.7)
    t = np.array([1.0, 2.0, 3.0])
    T = make_transform(R, t)
    T_inv = invert_transform(T)
    assert np.allclose(T @ T_inv, np.eye(4), atol=1e-10)
    print("PASS: invert_transform")

def test_quat_roundtrip():
    R = rpy_to_rot(0.3, 0.5, 1.2)
    q = rot_to_quat(R)
    R_back = quat_to_rot(q)
    assert np.allclose(R, R_back, atol=1e-10), f"Roundtrip failed"
    print("PASS: quaternion roundtrip")

if __name__ == "__main__":
    test_rotation_orthogonality()
    test_rot_z_90()
    test_transform_chain()
    test_invert_transform()
    test_quat_roundtrip()
    print("\nAll tests passed.")
```

---

## Project 1B — Visualize Coordinate Frames

Create `learning/ch01_transforms/visualize.py`:

```python
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from transforms import make_transform, rpy_to_rot

def draw_frame(ax, T, scale=0.2, label=""):
    """Draw a coordinate frame as 3 colored arrows."""
    origin = T[:3, 3]
    x_axis = T[:3, 0]
    y_axis = T[:3, 1]
    z_axis = T[:3, 2]
    ax.quiver(*origin, *x_axis, color='red',   length=scale, normalize=True)
    ax.quiver(*origin, *y_axis, color='green',  length=scale, normalize=True)
    ax.quiver(*origin, *z_axis, color='blue',   length=scale, normalize=True)
    if label:
        ax.text(*(origin + 0.05), label, fontsize=9)

def demo_frames():
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    # World frame at origin
    T_world = np.eye(4)
    draw_frame(ax, T_world, label="World")

    # Frame 1: translated and rotated
    T1 = make_transform(rpy_to_rot(0, 0, np.pi/4), np.array([0.5, 0.0, 0.0]))
    draw_frame(ax, T1, label="Frame1")

    # Frame 2: relative to Frame 1
    T_rel = make_transform(rpy_to_rot(0, np.pi/6, 0), np.array([0.3, 0.0, 0.0]))
    T2 = T1 @ T_rel
    draw_frame(ax, T2, label="Frame2")

    ax.set_xlim(-0.2, 1.2)
    ax.set_ylim(-0.5, 0.5)
    ax.set_zlim(-0.3, 0.5)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('Coordinate Frames\nRed=X, Green=Y, Blue=Z')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    demo_frames()
```

Run it:
```bash
cd learning/ch01_transforms
python visualize.py
```

You should see three coordinate frames: the world origin, a rotated+translated frame, and a third frame relative to the second.

---

## Project 1C — Animate a 2D Robot Arm

Create `learning/ch01_transforms/arm_fk.py`:

```python
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Arm parameters
L1, L2, L3 = 1.0, 0.7, 0.4  # link lengths

def forward_kinematics_2d(theta1, theta2, theta3):
    """
    Compute joint positions for a 3-link 2D arm.
    Returns: list of [x, y] positions: base, joint1, joint2, end-effector
    """
    x0, y0 = 0.0, 0.0

    a1 = theta1
    x1 = x0 + L1 * np.cos(a1)
    y1 = y0 + L1 * np.sin(a1)

    a2 = theta1 + theta2
    x2 = x1 + L2 * np.cos(a2)
    y2 = y1 + L2 * np.sin(a2)

    a3 = theta1 + theta2 + theta3
    x3 = x2 + L3 * np.cos(a3)
    y3 = y2 + L3 * np.sin(a3)

    return [(x0,y0), (x1,y1), (x2,y2), (x3,y3)]

def animate_arm():
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(-2.5, 2.5)
    ax.set_ylim(-2.5, 2.5)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.axhline(0, color='k', linewidth=0.5)
    ax.axvline(0, color='k', linewidth=0.5)
    ax.set_title('3-Link Planar Arm — Forward Kinematics\n'
                 'Animating joint angles over time')

    line, = ax.plot([], [], 'o-', lw=3, color='steelblue', markersize=10)
    ee_trace, = ax.plot([], [], '.', color='red', markersize=2, alpha=0.5)
    ee_x, ee_y = [], []

    t_values = np.linspace(0, 4 * np.pi, 400)

    def update(frame):
        t = t_values[frame]
        theta1 = 0.5 * np.sin(t * 0.5)
        theta2 = 1.0 * np.sin(t * 0.7 + 0.5)
        theta3 = 0.8 * np.cos(t * 0.3)

        pts = forward_kinematics_2d(theta1, theta2, theta3)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        line.set_data(xs, ys)

        ee_x.append(xs[-1])
        ee_y.append(ys[-1])
        ee_trace.set_data(ee_x, ee_y)
        return line, ee_trace

    anim = animation.FuncAnimation(fig, update, frames=len(t_values),
                                   interval=20, blit=True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    print("Demonstrating forward kinematics on a 2D 3-link arm.")
    print("The red dots trace the end-effector path.")
    animate_arm()
```

Run it:
```bash
python arm_fk.py
```

You should see an animated robot arm with the red trace showing where the end-effector has been.

---

## Self-Check Questions

Before moving to Chapter 2, you should be able to answer:

1. What is the difference between a rotation matrix and a homogeneous transform?
2. If `T_AB` transforms from frame B to frame A, how do you get from frame A to frame B?
3. You have a point `p = [1, 0, 0]` in frame B. Frame B is rotated 90° around Z and translated by `[2, 0, 0]` relative to frame A. What is `p` in frame A? (Compute it.)
4. Why does order matter when composing rotations?
5. What breaks if you use `np.linalg.inv(T)` instead of `invert_transform(T)`? When would you see the difference?
6. A rotation matrix has `det(R) = -1`. What does this mean geometrically?

**Worked answer to Q3:**
```python
T_AB = make_transform(rot_z(np.pi/2), np.array([2, 0, 0]))
p_B = np.array([1, 0, 0])
p_A = transform_point(T_AB, p_B)
# Result: [2, 1, 0]
# The point [1,0,0] in B → rotated 90° it becomes [0,1,0] → then translated by [2,0,0] → [2,1,0]
```

---

## Common Mistakes

**Mistake:** Applying translation before rotation.
`T = make_transform(R, t)` applies `R` first, then `t`. If you want to translate first, you need `T = make_transform(I, t) @ make_transform(R, [0,0,0])`.

**Mistake:** Mixing up active vs. passive rotation.
Active: the point moves. Passive: the frame moves. `R @ p` rotates point p actively. Most robotics uses active rotation of the coordinate frame (passive rotation of the points). Be consistent.

**Mistake:** Forgetting the quaternion convention. Some libraries use `[x, y, z, w]`, others use `[w, x, y, z]`. Always check.

---

## What's Next

Chapter 2 uses MuJoCo, which internally represents all robot links as bodies with positions and orientations — exactly the transforms you just built. When you see a 4×4 matrix in MuJoCo's `data.xmat`, you'll know exactly what it means.
