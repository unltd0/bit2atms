# Chapter 6 — ROS 2 & System Integration

**Time:** 3–4 days
**Hardware:** Ubuntu 24.04 or Docker on Mac (ROS 2 doesn't run natively on macOS)
**Prerequisites:** Chapter 1 (MuJoCo, IK)

---

## What are we here for

Everything so far has been self-contained Python scripts. Real robot deployments need
something more: multiple processes communicating in real time — a camera node publishing
images, a policy node consuming them and publishing actions, a hardware driver node
executing those actions on the motors. **ROS 2** is the standard middleware for this.

ROS 2 handles the plumbing: message passing, timing, process lifecycle. It's what lets
your LeRobot policy from Chapter 3 actually talk to a physical arm in Chapter 7.

This chapter builds up from scratch: a publisher/subscriber pair, an IK service, a
MuJoCo↔ROS 2 bridge, and visualization in RViz2. By the end you can run a policy in
sim with the same interface it'll use on hardware.

**Install (Ubuntu 24.04):**
```bash
sudo apt install ros-jazzy-desktop ros-jazzy-moveit
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

**Install (macOS — Docker):**
```bash
docker pull osrf/ros:jazzy-desktop

# Mount your workspace so files persist; -e DISPLAY is needed for RViz2 via XQuartz
docker run -it --rm \
  -v ~/code/unltd/bit2atms/workspace:/workspace \
  -e DISPLAY=host.docker.internal:0 \
  osrf/ros:jazzy-desktop bash

# Inside the container:
source /opt/ros/jazzy/setup.bash
cd /workspace/vla/ch06
```

For RViz2 on macOS you'll also need [XQuartz](https://www.xquartz.org/) installed and running,
with "Allow connections from network clients" enabled in XQuartz preferences.

**Skip if you can answer:**
1. What is a ROS 2 topic, and how does it differ from a service?
2. A node publishes `/joint_states` at 100 Hz. How do you verify this from the command line?
3. You want the policy node to call IK and get a joint target back. Topic or service? Why?
4. Your MuJoCo sim and ROS 2 node are running at different rates. What breaks?

---

## Projects

| # | Project | What you build |
|---|---------|---------------|
| A | Publisher/Subscriber | Joint state publisher at 100 Hz; FK computed on subscriber side |
| B | IK Service | Wrap Pink IK as a ROS 2 service; call it with a target pose |
| C | MuJoCo ↔ ROS 2 Bridge | Sim publishes joint states, receives joint commands |
| D | Visualize in RViz2 | Live TF tree, camera feed, robot model from a running sim |

---

## Project A — Publisher/Subscriber

**Problem:** The most basic ROS 2 communication pattern — one node continuously publishes
data, another subscribes and processes it. You'll use this pattern everywhere.

**Approach:** Publish simulated joint states from a MuJoCo model at 100 Hz; subscribe and
compute forward kinematics on the subscriber side.

### ROS 2 core concepts

- **Node:** a process that communicates over ROS 2
- **Topic:** a named channel for continuous data streams (sensor readings, joint states)
  — fire-and-forget, no response
- **Service:** a request/response call — one node asks, another answers
- **Action:** a long-running service with progress feedback (used for motion planning)
- **Message type:** the data structure passed over a topic or service (e.g. `sensor_msgs/JointState`)

```python workspace/vla/ch06/joint_state_publisher.py
"""Publish MuJoCo joint states as ROS 2 JointState messages at 100 Hz."""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import mujoco
import numpy as np
import os

FRANKA_XML = os.path.join(os.path.dirname(__file__), "./workspace/ext/mujoco_menagerie/franka_emika_panda/scene.xml")

class JointStatePublisher(Node):
    def __init__(self):
        super().__init__("joint_state_publisher")
        self.pub = self.create_publisher(JointState, "/joint_states", 10)
        self.timer = self.create_timer(0.01, self.publish_cb)  # 100 Hz

        self.model = mujoco.MjModel.from_xml_path(FRANKA_XML)
        self.data  = mujoco.MjData(self.model)
        self.data.qpos[:7] = [0, -0.785, 0, -2.356, 0, 1.571, 0.785]
        mujoco.mj_forward(self.model, self.data)

        self.joint_names = [self.model.joint(i).name for i in range(self.model.njnt)]
        self.get_logger().info(f"Publishing {len(self.joint_names)} joints at 100 Hz")

    def publish_cb(self) -> None:
        mujoco.mj_step(self.model, self.data)
        msg = JointState()
        msg.header.stamp    = self.get_clock().now().to_msg()
        msg.name            = self.joint_names
        msg.position        = self.data.qpos[:self.model.njnt].tolist()
        msg.velocity        = self.data.qvel[:self.model.njnt].tolist()
        self.pub.publish(msg)

def main():
    rclpy.init()
    node = JointStatePublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
```

```python workspace/vla/ch06/fk_subscriber.py
"""Subscribe to /joint_states and compute FK. Prints EE position at each update."""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import mujoco
import numpy as np
import os

FRANKA_XML = os.path.join(os.path.dirname(__file__), "./workspace/ext/mujoco_menagerie/franka_emika_panda/scene.xml")

class FKSubscriber(Node):
    def __init__(self):
        super().__init__("fk_subscriber")
        self.sub = self.create_subscription(JointState, "/joint_states",
                                             self.cb, 10)
        self.model = mujoco.MjModel.from_xml_path(FRANKA_XML)
        self.data  = mujoco.MjData(self.model)
        self.ee_id = self.model.body("panda_hand").id

    def cb(self, msg: JointState) -> None:
        n = min(len(msg.position), self.model.njnt)
        self.data.qpos[:n] = msg.position[:n]
        mujoco.mj_forward(self.model, self.data)
        ee_pos = np.round(self.data.xpos[self.ee_id], 3)
        self.get_logger().info(f"EE position: {ee_pos}")

def main():
    rclpy.init()
    node = FKSubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
```

**Run it:**
```bash
# Terminal 1
python joint_state_publisher.py
# Terminal 2
python fk_subscriber.py
# Terminal 3 — verify rate
ros2 topic hz /joint_states
```

---

## Project B — IK Service

**Problem:** You want nodes to request IK solutions on demand — a policy node asks "given
this target pose, what are the joint angles?" and gets a response.

**Approach:** Wrap Pink IK as a ROS 2 service. The service takes a 3D target position
and returns joint angles.

### Custom service definition

> **Note:** Using a custom `.srv` requires creating a ROS 2 package and running `colcon build`
> to generate the Python bindings. The service creation line is commented out below —
> this project is a working template that needs a package scaffold to fully run.
> See the [ROS 2 custom interfaces tutorial](https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Custom-ROS2-Interfaces.html)
> for the setup steps. Projects A, C, and D do not require this.

First define the service interface:

```text workspace/vla/ch06/srv/IKSolve.srv
# Request
float64[3] target_position
---
# Response
float64[] joint_positions
bool success
string message
```

```python workspace/vla/ch06/ik_service.py
"""ROS 2 service node: accepts a 3D target, returns joint angles via Pink IK."""
import rclpy
from rclpy.node import Node
import numpy as np
import mujoco
import pink
from pink.tasks import FrameTask
import pinocchio as pin
from robot_descriptions.loaders.pinocchio import load_robot_description
import os

# Import auto-generated service (after colcon build)
# from vla_msgs.srv import IKSolve

FRANKA_XML = os.path.join(os.path.dirname(__file__), "./workspace/ext/mujoco_menagerie/franka_emika_panda/scene.xml")

class IKServiceNode(Node):
    def __init__(self):
        super().__init__("ik_service")
        # self.srv = self.create_service(IKSolve, "/ik_solve", self.handle_ik)

        robot = load_robot_description("panda_description")
        self.configuration = pink.Configuration(robot.model, robot.data, robot.q0)
        self.ee_task = FrameTask("panda_hand", position_cost=1.0, orientation_cost=0.0)
        self.get_logger().info("IK service ready at /ik_solve")

    def handle_ik(self, request, response):
        target = pin.SE3.Identity()
        target.translation = np.array(request.target_position)
        self.ee_task.set_target(target)

        # Run IK for 100 steps to converge
        dt = 0.01
        for _ in range(100):
            vel = pink.solve_ik(self.configuration, [self.ee_task], dt, solver="quadprog")
            self.configuration.integrate_inplace(vel, dt)

        response.joint_positions = self.configuration.q[:7].tolist()
        response.success = True
        response.message = "OK"
        return response

def main():
    rclpy.init()
    node = IKServiceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
```

**What to observe:** From another terminal: `ros2 service call /ik_solve vla_msgs/srv/IKSolve "{target_position: [0.5, 0.1, 0.4]}"` — the service returns joint angles that put the hand at that position.

---

## Project C — MuJoCo ↔ ROS 2 Bridge

**Problem:** You want to run your sim in a ROS 2 ecosystem — publish sim state as ROS 2
topics and receive commands from ROS 2 nodes, just like a real robot driver would.

**Approach:** A single bridge node runs the MuJoCo sim, publishes joint states, and
subscribes to joint commands.

```python workspace/vla/ch06/mujoco_ros2_bridge.py
"""
MuJoCo ↔ ROS 2 bridge. Publishes joint states; subscribes to joint commands.
Same interface as a real robot driver — swap this node for the hardware driver
when moving from sim to real.
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray
import mujoco
import numpy as np
import os

FRANKA_XML = os.path.join(os.path.dirname(__file__), "./workspace/ext/mujoco_menagerie/franka_emika_panda/scene.xml")
SIM_HZ     = 500   # simulation steps per second
PUB_HZ     = 100   # joint state publish rate

class MuJoCoROS2Bridge(Node):
    def __init__(self):
        super().__init__("mujoco_bridge")
        self.pub = self.create_publisher(JointState, "/joint_states", 10)
        self.sub = self.create_subscription(Float64MultiArray, "/joint_commands",
                                             self.command_cb, 10)
        self.pub_timer = self.create_timer(1.0 / PUB_HZ, self.publish_cb)
        self.sim_timer = self.create_timer(1.0 / SIM_HZ, self.step_cb)

        self.model = mujoco.MjModel.from_xml_path(FRANKA_XML)
        self.data  = mujoco.MjData(self.model)
        self.data.qpos[:7] = [0, -0.785, 0, -2.356, 0, 1.571, 0.785]
        self.joint_names = [self.model.joint(i).name for i in range(self.model.njnt)]
        self.get_logger().info("MuJoCo bridge running")

    def step_cb(self) -> None:
        mujoco.mj_step(self.model, self.data)

    def publish_cb(self) -> None:
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name         = self.joint_names
        msg.position     = self.data.qpos[:self.model.njnt].tolist()
        msg.velocity     = self.data.qvel[:self.model.njnt].tolist()
        self.pub.publish(msg)

    def command_cb(self, msg: Float64MultiArray) -> None:
        n = min(len(msg.data), self.model.nu)
        self.data.ctrl[:n] = msg.data[:n]

def main():
    rclpy.init()
    node = MuJoCoROS2Bridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
```

**What to observe:** `ros2 topic echo /joint_states` shows live sim data. Publish a
command with `ros2 topic pub /joint_commands std_msgs/Float64MultiArray "{data: [0.5, 0, 0, 0, 0, 0, 0]}"` and watch the sim respond.

---

## Project D — Visualize in RViz2

**Problem:** You want to see the robot model, TF tree, and camera feed in RViz2 — the
standard robotics visualization tool.

**Approach:** Publish TF transforms from your bridge node; add a robot model display in
RViz2; visualize from a running sim.

```python workspace/vla/ch06/tf_publisher.py
"""Publish TF transforms for each robot link from MuJoCo xpos/xquat."""
import rclpy
from rclpy.node import Node
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped
import mujoco
import numpy as np
import os

FRANKA_XML = os.path.join(os.path.dirname(__file__), "./workspace/ext/mujoco_menagerie/franka_emika_panda/scene.xml")

class TFPublisher(Node):
    def __init__(self):
        super().__init__("tf_publisher")
        self.br    = TransformBroadcaster(self)
        self.timer = self.create_timer(0.02, self.publish_cb)  # 50 Hz
        self.model = mujoco.MjModel.from_xml_path(FRANKA_XML)
        self.data  = mujoco.MjData(self.model)
        self.data.qpos[:7] = [0, -0.785, 0, -2.356, 0, 1.571, 0.785]
        mujoco.mj_forward(self.model, self.data)

    def publish_cb(self) -> None:
        mujoco.mj_step(self.model, self.data)
        now = self.get_clock().now().to_msg()
        for i in range(1, self.model.nbody):
            t = TransformStamped()
            t.header.stamp    = now
            t.header.frame_id = "world"
            t.child_frame_id  = self.model.body(i).name
            pos  = self.data.xpos[i]
            quat = self.data.xquat[i]  # [w, x, y, z]
            t.transform.translation.x = pos[0]
            t.transform.translation.y = pos[1]
            t.transform.translation.z = pos[2]
            t.transform.rotation.w = quat[0]
            t.transform.rotation.x = quat[1]
            t.transform.rotation.y = quat[2]
            t.transform.rotation.z = quat[3]
            self.br.sendTransform(t)

def main():
    rclpy.init()
    node = TFPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
```

**Run RViz2:**
```bash
rviz2
# Add: RobotModel (URDF), TF (show all frames), Image (camera topic)
```

---

## Self-Check

1. What is the difference between a ROS 2 topic and a service?
   **Answer:** Topics are one-way continuous streams (publish/subscribe). Services are
   request/response — one node calls, another answers. Use topics for sensor data and
   state; use services for on-demand computations like IK.

2. `ros2 topic hz /joint_states` reports 50 Hz but you expected 100 Hz. What do you check?
   **Answer:** Check the `create_timer` interval in your publisher node. Also check system
   load — if the process is CPU-bound, the timer may not fire at the requested rate.

3. You want the MuJoCo bridge to run at 500 Hz but publish joint states at 100 Hz. How?
   **Answer:** Use two timers: one at 500 Hz for `mj_step()`, one at 100 Hz for
   publishing. Don't step the sim in the publish callback.

4. Your policy node publishes commands to `/joint_commands` but the bridge doesn't respond.
   What do you check?
   **Answer:** Verify topic names match exactly. Run `ros2 topic list` and `ros2 topic info
   /joint_commands` to check publishers and subscribers. Check message types match.

5. Why does MuJoCo use `[w, x, y, z]` quaternions but ROS 2 uses `[x, y, z, w]`?
   **Answer:** Different historical conventions. Always explicitly reorder when passing
   quaternions between MuJoCo and ROS 2 — mixing them silently produces wrong orientations.

---

## Common Mistakes

- **Not sourcing the ROS 2 setup:** If `rclpy` isn't found, you forgot
  `source /opt/ros/jazzy/setup.bash`. Add it to `~/.bashrc`.

- **Running on macOS without Docker:** ROS 2 Jazzy doesn't support macOS natively.
  Use the `osrf/ros:jazzy-desktop` Docker image.

- **Timer rate exceeds system capability:** A 500 Hz Python timer won't actually fire at
  500 Hz on most systems. For real-time control, use the C++ rclcpp client library.

- **Quaternion sign ambiguity:** Both `q` and `-q` represent the same rotation. When
  comparing or interpolating quaternions, always check the sign convention.

---

## Resources

1. [ROS 2 Jazzy documentation](https://docs.ros.org/en/jazzy/) — core concepts and Python client library
2. [ROS 2 tutorials](https://docs.ros.org/en/jazzy/Tutorials.html) — start with "Beginner: CLI tools" and "Beginner: Client libraries"
3. [tf2 tutorials](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Tf2/Introduction-To-Tf2.html) — coordinate frame broadcasting
4. [RViz2 user guide](https://github.com/ros2/rviz) — display types and configuration
