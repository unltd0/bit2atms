# Chapter 8 — ROS 2 & System Integration

**Time:** 3–4 days
**Hardware:** Ubuntu 24.04 recommended; macOS users use Docker (fully supported)
**Prerequisites:** Chapters 1–3 (transforms, MuJoCo, kinematics). Chapters 4–7 helpful but not required.

---

## Why This Chapter Exists

Everything you've built so far is self-contained Python scripts. The moment you work with real hardware, that changes: the camera runs in one process, the controller in another, the perception stack in a third, and they need to communicate reliably in real time. ROS 2 is the industry-standard way to do this — and virtually all robot hardware (arms, grippers, cameras, force sensors) ships with ROS 2 drivers.

The gap this fills: you could skip ROS 2 entirely for simulation-only work, but the moment you touch physical hardware or read any recent robotics paper, ROS 2 vocabulary (topics, services, actions, TF2) appears constantly. This chapter gives you enough fluency to not be lost — and a working MuJoCo bridge so you can test ROS 2 code without a physical robot.

**If you're doing simulation-only work with no hardware plans**, you can skip this chapter and return when needed.

---

## Part 1 — ROS 2 Concepts

### Why ROS 2 Exists

In a real robot system, you have:
- A camera node publishing images at 30 Hz
- A joint state publisher at 500 Hz
- A perception node consuming images and publishing detected objects
- A motion planner subscribing to object positions and planning trajectories
- A controller subscribing to trajectories and commanding joints

Each of these runs as a separate process. They need to communicate reliably, at real-time frequencies, with type-safe messages. ROS 2 provides this infrastructure.

### ROS 2 vs. ROS 1

| Feature | ROS 1 | ROS 2 |
|---------|-------|-------|
| Status | EOL May 2025 | Active |
| Transport | Custom rosmaster | DDS (industry standard) |
| Real-time | No | Yes (with real-time OS) |
| Language support | Python, C++ | Python, C++, others |
| Security | None | DDS Security |
| Multi-robot | Difficult | Native |

Always use ROS 2. ROS 1 is dead.

### Core Concepts

**Node:** A single executable process. Each node does one thing (publishes sensor data, runs a controller, processes images).

**Topic:** A named channel. Nodes publish messages to topics; other nodes subscribe to receive them. Asynchronous, one-to-many.

**Service:** A request-response interface. One node calls a service; the service node responds. Synchronous, one-to-one. Use for IK queries, parameter lookups.

**Action:** Like a service but with ongoing feedback. Use for motion planning (long-running, need progress updates).

**Message type:** Typed data structures (e.g., `sensor_msgs/JointState`, `geometry_msgs/PoseStamped`). Ensures type safety.

**QoS (Quality of Service):** Controls reliability (best-effort vs. reliable), history, and deadline. Sensor data: best-effort. Commands: reliable.

### DDS Communication Model

ROS 2 uses DDS (Data Distribution Service) as the transport layer. The key property: nodes discover each other automatically on the network — no central master needed. This makes ROS 2 suitable for distributed and multi-machine systems.

---

## Part 2 — Install ROS 2 Jazzy

### Ubuntu 24.04 (Recommended)

```bash
# Set up sources
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | \
  sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# Install
sudo apt update
sudo apt install ros-jazzy-desktop ros-jazzy-ros-dev-tools

# Source (add to ~/.bashrc)
source /opt/ros/jazzy/setup.bash
```

### macOS (Docker)

```bash
docker pull osrf/ros:jazzy-desktop
# Run with display forwarding (XQuartz required on Mac):
docker run -it --rm \
  -e DISPLAY=host.docker.internal:0 \
  -v $(pwd):/workspace \
  osrf/ros:jazzy-desktop \
  bash
```

### Verify

```bash
# Open two terminals
# Terminal 1:
ros2 run demo_nodes_py talker
# Terminal 2:
ros2 run demo_nodes_py listener
```

You should see "Hello World" messages flowing between them.

---

## Part 3 — Key Standard Message Types

These are the message types you'll use constantly:

```
sensor_msgs/JointState
  - name: ["joint1", "joint2", ...]    # joint names
  - position: [q1, q2, ...]            # radians
  - velocity: [dq1, dq2, ...]          # rad/s
  - effort: [tau1, tau2, ...]          # Nm

geometry_msgs/PoseStamped
  - header.stamp                        # timestamp
  - pose.position.{x, y, z}           # meters
  - pose.orientation.{x, y, z, w}     # quaternion

sensor_msgs/Image
  - height, width
  - encoding: "rgb8" or "bgr8"
  - data: flat byte array

trajectory_msgs/JointTrajectory
  - joint_names: [...]
  - points[i].positions: [...]
  - points[i].time_from_start: Duration
```

---

## External Resources

1. **ROS 2 Jazzy Official Tutorials**
   Do ALL beginner CLI tutorials before writing any code. ~2 hours.
   → https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools.html

2. **ROS 2 Jazzy Client Library Tutorials (Python)**
   Publisher, subscriber, service, parameter server — all in Python.
   → https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries.html

3. **ROS 2 Concepts Reference**
   DDS, QoS, nodes, topics, services — the definitive explanations.
   → https://docs.ros.org/en/jazzy/Concepts.html

4. **MoveIt 2 Documentation**
   Motion planning for robot arms. Works with any URDF-described robot.
   → https://moveit.picknik.ai/main/index.html

5. **RViz2 User Guide**
   Visualization tool for robot state, sensor data, planned trajectories.
   → https://github.com/ros2/rviz/tree/ros2/rviz2

6. **ros2_control Documentation**
   The standard way to interface hardware controllers with ROS 2.
   → https://control.ros.org/jazzy/index.html

---

## Project 8A — Publisher and Subscriber Nodes

First, create a ROS 2 package:

```bash
cd learning/ch08_ros2
mkdir -p robot_basics/robot_basics
touch robot_basics/robot_basics/__init__.py
```

Create `learning/ch08_ros2/robot_basics/setup.py`:

```python
from setuptools import find_packages, setup

package_name = 'robot_basics'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    install_requires=['setuptools'],
    entry_points={
        'console_scripts': [
            'joint_publisher = robot_basics.joint_publisher:main',
            'joint_subscriber = robot_basics.joint_subscriber:main',
            'ik_service = robot_basics.ik_service:main',
            'ik_client = robot_basics.ik_client:main',
        ],
    },
)
```

Create `learning/ch08_ros2/robot_basics/robot_basics/joint_publisher.py`:

```python
"""
Node that publishes simulated joint states at 100 Hz.
In a real system, this would read from actual encoders.
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import numpy as np
import math


class JointPublisher(Node):
    def __init__(self):
        super().__init__('joint_publisher')

        self.publisher_ = self.create_publisher(JointState, 'joint_states', 10)
        self.timer = self.create_timer(0.01, self.publish_joint_states)  # 100 Hz

        self.joint_names = [f'joint_{i+1}' for i in range(7)]
        self.t = 0.0

        self.get_logger().info('Joint publisher started — publishing at 100 Hz')

    def publish_joint_states(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.joint_names

        # Simulate oscillating joint motion (sinusoidal)
        positions = [
            0.5 * math.sin(self.t * 0.3 + i * 0.5)
            for i in range(7)
        ]
        velocities = [
            0.5 * 0.3 * math.cos(self.t * 0.3 + i * 0.5)
            for i in range(7)
        ]
        efforts = [0.0] * 7  # simulated zero torque

        msg.position = positions
        msg.velocity = velocities
        msg.effort = efforts

        self.publisher_.publish(msg)
        self.t += 0.01


def main(args=None):
    rclpy.init(args=args)
    node = JointPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

Create `learning/ch08_ros2/robot_basics/robot_basics/joint_subscriber.py`:

```python
"""
Node that subscribes to joint states and computes forward kinematics.
Prints end-effector position at 10 Hz.
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import numpy as np
import math


def simple_fk(joint_positions):
    """
    Simple FK for a planar arm approximation.
    Replace with Pinocchio-based FK for real robot.
    """
    L = [0.4, 0.35, 0.25, 0.18, 0.12, 0.08, 0.04]  # approximate Franka link lengths
    x, y, z = 0.0, 0.0, 0.33  # base height

    cumulative_angle = 0.0
    for i, (q, l) in enumerate(zip(joint_positions[:3], L[:3])):
        cumulative_angle += q
        x += l * math.cos(cumulative_angle)
        z += l * math.sin(cumulative_angle) * 0.5

    return x, y, z


class JointSubscriber(Node):
    def __init__(self):
        super().__init__('joint_subscriber')

        self.subscription = self.create_subscription(
            JointState, 'joint_states', self.joint_callback, 10)

        self.last_print = 0.0
        self.msg_count = 0

        self.get_logger().info('Joint subscriber started')

    def joint_callback(self, msg):
        self.msg_count += 1

        # Compute FK (simplified)
        if len(msg.position) >= 3:
            x, y, z = simple_fk(list(msg.position))

        # Print at 10 Hz
        now = self.get_clock().now().nanoseconds / 1e9
        if now - self.last_print > 0.1:
            self.get_logger().info(
                f"[msg #{self.msg_count}] "
                f"q={[f'{p:.3f}' for p in msg.position[:3]]}  "
                f"EE_approx=({x:.3f}, {y:.3f}, {z:.3f})"
            )
            self.last_print = now


def main(args=None):
    rclpy.init(args=args)
    node = JointSubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

Build and run:
```bash
cd learning/ch08_ros2
colcon build --packages-select robot_basics
source install/setup.bash

# Terminal 1:
ros2 run robot_basics joint_publisher

# Terminal 2:
ros2 run robot_basics joint_subscriber

# Terminal 3 — verify topic:
ros2 topic echo /joint_states
ros2 topic hz /joint_states    # should show ~100 Hz
```

---

## Project 8B — IK Service

Create `learning/ch08_ros2/robot_basics/robot_basics/ik_service.py`:

```python
"""
ROS 2 service that solves IK on request.
Client sends target position → server returns joint angles.

Uses a custom service type. For simplicity, we use a standard
service with position in the request and joint angles in the response.
"""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from sensor_msgs.msg import JointState
import numpy as np

# We'll use a simple IK (Jacobian iteration) without external deps
# Replace with Pink for full quality


class IKServiceNode(Node):
    def __init__(self):
        super().__init__('ik_service')

        from rclpy.qos import QoSProfile
        # Use SetParameters service or a custom action
        # Here: use a topic-based request-response for simplicity
        # (A real service would use a custom .srv file)
        self.target_sub = self.create_subscription(
            Point, '/ik_target', self.ik_callback, 10)
        self.solution_pub = self.create_publisher(JointState, '/ik_solution', 10)

        self.get_logger().info('IK service node ready. Send targets to /ik_target')

    def ik_callback(self, target_msg):
        target = np.array([target_msg.x, target_msg.y, target_msg.z])

        # Simple analytical IK for a 2D projection (placeholder)
        # In practice: use Pink + Pinocchio
        q_solution = self._solve_ik_simple(target)

        response = JointState()
        response.header.stamp = self.get_clock().now().to_msg()
        response.name = [f'joint_{i+1}' for i in range(7)]
        response.position = q_solution.tolist()

        self.solution_pub.publish(response)
        self.get_logger().info(
            f"IK for target {target.round(3)} → q={q_solution.round(3)}")

    def _solve_ik_simple(self, target):
        """Simplified IK — replace with Pink for real use."""
        # Just return angles that roughly point toward target
        horizontal_dist = np.sqrt(target[0]**2 + target[1]**2)
        q1 = np.arctan2(target[1], target[0])
        q2 = -0.5  # reasonable elbow angle
        q3 = 0.0
        q4 = np.arctan2(target[2] - 0.33, horizontal_dist) - 0.5
        q5, q6, q7 = 0.0, 1.57, 0.78
        return np.array([q1, q2, q3, q4, q5, q6, q7])


def main(args=None):
    rclpy.init(args=args)
    node = IKServiceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

---

## Project 8C — MuJoCo ↔ ROS 2 Bridge

This is the most important project in this chapter. It makes your MuJoCo simulation look like real hardware from ROS 2's perspective.

Create `learning/ch08_ros2/robot_basics/robot_basics/mujoco_ros2_bridge.py`:

```python
"""
Bidirectional bridge between MuJoCo simulation and ROS 2.

MuJoCo → ROS 2:
  - Publishes joint states (position, velocity, effort) at 500 Hz
  - Publishes camera image at 30 Hz

ROS 2 → MuJoCo:
  - Subscribes to /cmd_joint_position for joint position targets
  - Implements a PD controller to track commanded positions

This makes MuJoCo behave exactly like real hardware from ROS 2's perspective.
The same nodes that command this simulated robot will command the real robot.
"""
import os
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState, Image
from std_msgs.msg import Float64MultiArray
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup
import mujoco
import threading
import time


FRANKA_XML = os.path.expanduser("~/mujoco_menagerie/franka_emika_panda/scene.xml")

JOINT_NAMES = [f'panda_joint{i}' for i in range(1, 8)]


class MuJoCoROSBridge(Node):
    def __init__(self):
        super().__init__('mujoco_ros2_bridge')

        self.callback_group = ReentrantCallbackGroup()

        # Load MuJoCo model
        if not os.path.exists(FRANKA_XML):
            self.get_logger().error(f"MuJoCo model not found: {FRANKA_XML}")
            self.get_logger().error("Clone mujoco_menagerie and update FRANKA_XML path")
            raise FileNotFoundError(FRANKA_XML)

        self.mj_model = mujoco.MjModel.from_xml_path(FRANKA_XML)
        self.mj_data = mujoco.MjData(self.mj_model)
        self.mj_lock = threading.Lock()

        # Default neutral pose
        self.q_target = np.array([0, -0.785, 0, -2.356, 0, 1.571, 0.785])
        self.kp = np.array([400, 400, 400, 400, 250, 150, 50])
        self.kd = np.array([40,  40,  40,  40,  25,  15,  5 ])

        # Publishers
        self.joint_state_pub = self.create_publisher(
            JointState, '/joint_states', 10)
        self.image_pub = self.create_publisher(
            Image, '/camera/image_raw', 10)

        # Subscribers
        self.cmd_sub = self.create_subscription(
            Float64MultiArray, '/cmd_joint_position',
            self.cmd_callback, 10,
            callback_group=self.callback_group)

        # Timers
        self.physics_timer = self.create_timer(
            0.002, self.physics_step,  # 500 Hz physics
            callback_group=self.callback_group)
        self.js_pub_timer = self.create_timer(
            0.002, self.publish_joint_states,  # 500 Hz
            callback_group=self.callback_group)
        self.img_timer = self.create_timer(
            1.0/30.0, self.publish_camera,  # 30 Hz
            callback_group=self.callback_group)

        # MuJoCo renderer for camera images
        self.renderer = mujoco.Renderer(self.mj_model, height=480, width=640)

        self.get_logger().info('MuJoCo-ROS2 bridge started')
        self.get_logger().info(f'  Physics: 500 Hz | Joint states: 500 Hz | Camera: 30 Hz')
        self.get_logger().info(f'  Subscribe: /cmd_joint_position')
        self.get_logger().info(f'  Publish: /joint_states, /camera/image_raw')

    def cmd_callback(self, msg):
        """Receive joint position command from ROS 2 and update target."""
        if len(msg.data) >= 7:
            with self.mj_lock:
                self.q_target = np.array(msg.data[:7])

    def physics_step(self):
        """Run one physics step with PD control."""
        with self.mj_lock:
            q = self.mj_data.qpos[:7]
            dq = self.mj_data.qvel[:7]
            torques = self.kp * (self.q_target - q) - self.kd * dq
            self.mj_data.ctrl[:7] = np.clip(torques, -87, 87)
            mujoco.mj_step(self.mj_model, self.mj_data)

    def publish_joint_states(self):
        """Publish current joint states."""
        with self.mj_lock:
            q = self.mj_data.qpos[:7].copy()
            dq = self.mj_data.qvel[:7].copy()
            tau = self.mj_data.actuator_force[:7].copy()

        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = JOINT_NAMES
        msg.position = q.tolist()
        msg.velocity = dq.tolist()
        msg.effort = tau.tolist()
        self.joint_state_pub.publish(msg)

    def publish_camera(self):
        """Render and publish camera image from MuJoCo."""
        with self.mj_lock:
            self.renderer.update_scene(self.mj_data, camera=0)
            pixels = self.renderer.render()  # HxWx3 uint8

        msg = Image()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.height = pixels.shape[0]
        msg.width = pixels.shape[1]
        msg.encoding = 'rgb8'
        msg.step = pixels.shape[1] * 3
        msg.data = pixels.tobytes()
        self.image_pub.publish(msg)

    def destroy_node(self):
        self.renderer.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    bridge = MuJoCoROSBridge()
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(bridge)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    bridge.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

Run the bridge:
```bash
ros2 run robot_basics mujoco_ros2_bridge

# In another terminal — command the robot:
ros2 topic pub /cmd_joint_position std_msgs/Float64MultiArray \
  "data: [0.0, -1.0, 0.0, -2.0, 0.0, 1.5, 0.785]"

# Verify:
ros2 topic hz /joint_states          # should show ~500 Hz
ros2 topic hz /camera/image_raw      # should show ~30 Hz
```

---

## Project 8D — Visualize in RViz2

Create `learning/ch08_ros2/launch/visualize.launch.py`:

```python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Robot state publisher (broadcasts TF transforms from URDF)
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': open(
                '/path/to/panda.urdf').read()}],  # update path
        ),

        # Our MuJoCo bridge
        Node(
            package='robot_basics',
            executable='mujoco_ros2_bridge',
        ),

        # RViz2 for visualization
        Node(
            package='rviz2',
            executable='rviz2',
        ),
    ])
```

In RViz2:
1. Add display: `RobotModel` → subscribe to `/robot_description`
2. Add display: `JointState` → topic `/joint_states`
3. Add display: `Image` → topic `/camera/image_raw`
4. Fixed frame: `panda_link0`

You should see the Franka arm moving in RViz2 with the MuJoCo physics running in the background.

---

## Self-Check Questions

Before moving to Chapter 9:

1. What is the difference between using a ROS 2 topic vs. a service for joint commands?
2. Your bridge publishes joint states at 500 Hz but your policy node can only run at 30 Hz. How does ROS 2 handle this mismatch?
3. Why use `MultiThreadedExecutor` in the bridge node?
4. What is the purpose of the QoS (Quality of Service) setting `BEST_EFFORT` vs. `RELIABLE`?
5. The `mj_lock` mutex in the bridge — what would happen if you removed it?

**Answers:**
1. Topic: asynchronous, broadcast, no response confirmation. Service: synchronous, one-to-one, caller waits for response. Use topics for streaming data (joint states, commands). Use services for queries with results (IK request, parameter lookup).
2. ROS 2 subscribers have a queue. The policy node simply reads the latest message in its queue and ignores older ones (use `qos_profile.depth=1` and `BEST_EFFORT` to always get the freshest data).
3. Multiple callbacks need to run concurrently: physics step timer, joint state publisher, camera publisher, command subscriber. Without `MultiThreadedExecutor`, they'd be serialized and some would miss their timing.
4. `BEST_EFFORT` drops messages if the network is congested — fine for sensor data where stale data is useless anyway. `RELIABLE` retransmits — necessary for commands where missing one could leave the robot in a wrong state.
5. The physics thread and ROS callbacks would race on `mj_data` — undefined behavior. The lock ensures only one thread accesses MuJoCo at a time. This is the most common bug in ROS 2 node implementations.

---

## What's Next

Chapter 9 replaces the MuJoCo bridge with a real robot. The same ROS 2 infrastructure you built here (publisher/subscriber pattern, command topics, camera topics) will work on physical hardware — that's the whole point of this chapter.
