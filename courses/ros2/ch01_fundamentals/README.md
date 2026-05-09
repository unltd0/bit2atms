# Chapter 1 — Fundamentals

**Time:** Half day
**Hardware:** Laptop only
**Prerequisites:** Python, terminal comfort

---

## What are we here for

A robot has many moving parts: a camera, a lidar, motors *(hardware)* — and a navigation algorithm, a path planner, a state estimator *(software)*. In a normal program you'd wire these together with function calls — but that breaks down fast. The camera runs at 30 Hz, the planner runs at 10 Hz, the motors need commands at 50 Hz. They need to run concurrently, possibly on different computers, and you need to be able to swap one out without rewriting the rest.

Yes, this sounds like a generic messaging problem — Kafka, gRPC, or ZeroMQ could do it. What makes ROS2 different is that it's built *for robots specifically*. In ch02 and ch03 you'll see what that means concretely: standard message types for sensor data (`LaserScan`, `Odometry`, `Twist`), a coordinate transform system (TF) that automatically tracks the position/orientation of every robot part or sensor in 3D space, letting you convert data between different frames (e.g., lidar readings → robot base frame) without manual math, a navigation stack (Nav2), and a simulator (Gazebo) — all speaking the same language out of the box. In ch01 you'll use simple types to learn the patterns; the robot-specific pieces land once the plumbing makes sense.

🟡 **Know**: We’ll see TF in action for the first time in ch2 when we launch a simulated robot, and explain the full TF tree structure there.

ROS2 solves the wiring problem. Each piece of the robot is represented as a **node** — an independent process (a running program). Hardware gets a driver node that wraps it; software just runs as a node directly. Nodes don't call each other directly. Instead they communicate through a shared message bus.

**Where does hardware fit?** A driver node sits between the physical device and the rest of the system. The lidar driver node reads raw serial data from the sensor and publishes it as a `LaserScan` message — 360 distance readings in a standard format every other node understands. The motor driver node subscribes to `Twist` messages (linear and angular velocity) and writes them to the motor board. The rest of the system never touches hardware directly — it just talks to driver nodes.

```
[lidar hardware] → lidar_driver node → /scan topic → slam node → /map topic
[motor hardware] ← motor_driver node ← /cmd_vel topic ← nav2 node
```

**The three communication patterns:**

**Topics** — streaming, fire-and-forget. A node publishes messages; any number of nodes can subscribe. The publisher doesn't know or care who's listening.

![Topic: one publisher, one subscriber](https://docs.ros.org/en/jazzy/_images/Topic-SinglePublisherandSingleSubscriber.gif)

Use topics for continuous data: sensor readings, robot pose, camera frames.

**Services** — request/reply, one-to-one. A client sends a request; the server processes it and sends back a response. Blocks until the reply arrives.

![Nodes communicating via topics and services](https://docs.ros.org/en/jazzy/_images/Nodes-TopicandService.gif)

Use services for on-demand queries: "what's the current battery level?", "reset this counter".

**Actions** — like a service, but long-running. The client sends a goal; the server sends back a stream of feedback while it works, then a final result. The client can cancel mid-way.

![Action client and server](https://docs.ros.org/en/jazzy/_images/Action-SingleActionClient.gif)

Use actions for anything that takes time: navigate to a point, run a calibration routine, execute a pick-and-place.

That's the whole mental model. Everything else in this chapter — launch files, CLI tools, bags — is plumbing on top of this.

**The `ros2` CLI** is the one command you'll type all day. It's a dispatcher — `ros2 <verb> <subcommand>` — and a handful of verbs cover ~90% of what you need:

| Command | What it does |
|---|---|
| `ros2 run <pkg> <exe>` | Start a single node from a package. |
| `ros2 launch <pkg> <file>` | Start many nodes (with params/remaps) from a launch file. Use this once you have a system, not just one node. |
| `ros2 node list` / `info <node>` | See what nodes are alive; inspect their pubs/subs/services. |
| `ros2 topic list` / `echo <topic>` / `hz <topic>` / `info <topic>` | Inspect the message bus — what's being published, the data, the rate, the type. |
| `ros2 service list` / `call <srv> <type> <args>` | List services; invoke one from the shell. |
| `ros2 param list` / `get` / `set` | Read and tweak node parameters live. |
| `ros2 bag record <topic>` / `play <bag>` | Record topic traffic to disk and replay it later. |
| `ros2 pkg list` / `prefix <pkg>` | What packages are installed and where. |

Tab-completion works for verbs, subcommands, and live topic/node names — lean on it. `ros2 <verb> --help` is always available.

**Mac and Windows:** Use Docker — every command that needs ROS2 runs inside a container. Linux users can install natively or use Docker.

**Skip if you can answer:**
1. What's the difference between a topic and a service?
2. You have two nodes. How does node B know when node A publishes something?
3. What does `colcon build` do and why do you need it?

---

## Where do these nodes run?

Driver nodes — the ones that actually talk to motors and sensors — have to run on a machine that's physically wired to the robot. That's either:

- the robot's **MCU** (microcontroller — e.g. ESP32, Teensy, Arduino, RP2040, STM32) itself, running [micro-ROS](https://micro.ros.org/) firmware that participates in the ROS2 graph directly, or
- an **SBC** (single-board computer like a Raspberry Pi or Jetson) connected to the MCU over USB serial, running a driver node that translates between the MCU's wire protocol and ROS2 topics.

Everything else — planners, SLAM, visualization, ML policies — is **just OS processes**. They can live on any number of **host VMs** on the same network as the SBC: a laptop on your desk, a Linux server in another room, a fleet operator's machine. They join the ROS2 graph over WiFi/Ethernet via DDS (the wire protocol under ROS2): same `ROS_DOMAIN_ID`, same network, no further config.

```
   ┌── LAPTOP / VM ┐  ┌── GPU SERVER ──┐  ┌── (any host) ──┐
   │  Foxglove     │  │  perception    │  │      …         │
   │  nav2, slam   │  │  policy        │  │                │
   └───────────────┘  └────────────────┘  └────────────────┘
          ▲                  ▲                   ▲
          └──────────────────┴── DDS over WiFi/Ethernet ──┐
                                                          │
              ┌── SBC (RPi/Jetson) ────────────────────┐  │
              │   driver nodes (own the USB)           │◄─┘
              └────────────────────────────────────────┘
                                │ USB serial
                                ▼
                          ┌── MCU ──┐
                          │ motors  │  (or runs micro-ROS,
                          │ sensors │   joining the graph
                          └─────────┘   directly)
```

Two notes:
- **Mobile robots** put the SBC on the chassis (TurtleBot3 = RPi onboard). **Desk robots** can skip the SBC entirely — a VM (your laptop, a Linux server, whatever you have) gets USB-cabled to the MCU and runs the driver nodes itself, alongside everything else (planner, visualization, application logic) on the same machine (SO-101 = USB cable to your laptop). Same architecture; the SBC is just packaging when wires can't reach.
- **In ch02** you'll run everything in one Docker container on a single VM (your laptop is fine) — sim only, no robot. The architecture above starts mattering in ch03.

Deeper background (micro-ROS in detail, what ROS2 ships vs what you write, per-layer placement table): see [Appendix — Deployment, the longer version](#appendix-deployment-the-longer-version).

**Skip the rest if you can answer:**
1. Why does the driver node need to run on the machine that's USB-cabled to the MCU?
2. What does the MCU do that Linux can't?
3. If the vendor doesn't ship a ROS2 driver for your sensor, what's your job?

---

## Projects

| # | Project | What you build |
|---|---------|----------------|
| A | Install & First Nodes | ROS2 running, publisher + subscriber talking |
| B | Topics, Services, Actions | One node using all three patterns; poke it with CLI |
| C | Launch Files & Bags | A launch file that starts multiple nodes; record and replay |

---

## Project A — Install & First Nodes

**Problem:** Get ROS2 running and verify two nodes can communicate.

**Approach:** Docker (Mac/Windows/Linux) or native install on Linux. Build and start the container using the **Docker image** resource in the sidebar — it covers build, run, and verify steps for all chapters. Come back here once you have a shell with `ros2` working.

### Verify with demo nodes

Open two terminals (two Docker shells if on Mac: `docker exec -it ros2 bash`).

`ros2 run <package> <executable>` is the standard way to start a node. Here:
- `demo_nodes_py` — a package that ships with ROS2, contains demo nodes
- `talker` / `listener` — the specific node to run from that package

Terminal 1 — talker:

🟢 **Run**

```bash
ros2 run demo_nodes_py talker
```

Terminal 2 — listener:

🟢 **Run**

```bash
ros2 run demo_nodes_py listener
```

You should see `[listener]: I heard: Hello World: N` streaming in terminal 2.

Try killing the talker with Ctrl+C and restarting it. Notice:
- The listener keeps running without restarting — it just paused and resumed. That's pub/sub: subscribers don't care who's publishing or when.
- The counter resets to 0 on restart, but the listener likely misses message 0 and picks up from 1 or 2. ROS2 uses a networking layer called DDS (Data Distribution Service) to discover nodes on the network — when the talker restarts, DDS takes ~1 second to rediscover it, and the first few messages are already gone. Topics are fire-and-forget with no delivery guarantee. If you need guaranteed delivery, that's what services and actions are for.

Kill both with Ctrl+C when done.

### Write your own nodes

For now, run nodes as plain Python scripts — no package needed. Save files to `workspace/ros2/ch01/` and run them with `python3`.

Write a publisher. This streams a counter to the `/count` topic at 1 Hz.

🔴 **Work** — run it, then change the message type to `String` and publish your name

```python workspace/ros2/ch01/publisher.py
# workspace/ros2/ch01/publisher.py
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32

# 1. Node setup — inherit from Node, create publisher in __init__
class CounterPublisher(Node):
    def __init__(self) -> None:
        super().__init__('counter_publisher')
        # 1.1 Publisher on /count, queue size 10 (how many messages to buffer)
        self.pub = self.create_publisher(Int32, '/count', 10)
        self.count = 0
        # 1.2 Timer fires publish() every 1.0 seconds
        self.create_timer(1.0, self.publish)

    # 2. Callback — runs every timer tick
    def publish(self) -> None:
        msg = Int32()
        msg.data = self.count
        self.pub.publish(msg)
        self.get_logger().info(f'Publishing: {self.count}')
        self.count += 1

# 1. Entry point — spin keeps the node alive and processes callbacks
def main() -> None:
    rclpy.init()
    node = CounterPublisher()
    rclpy.spin(node)    # blocks here — runs the timer/subscription callbacks until Ctrl+C
    rclpy.shutdown()    # clean up after Ctrl+C exits spin

if __name__ == '__main__':
    main()
```

Write a subscriber:

🟡 **Know**

```python workspace/ros2/ch01/subscriber.py
# workspace/ros2/ch01/subscriber.py
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32

class CounterSubscriber(Node):
    def __init__(self) -> None:
        super().__init__('counter_subscriber')
        self.create_subscription(Int32, '/count', self.callback, 10)

    def callback(self, msg: Int32) -> None:
        self.get_logger().info(f'Got: {msg.data}')

def main() -> None:
    rclpy.init()
    rclpy.spin(CounterSubscriber())  # blocks — delivers incoming messages to callback until Ctrl+C
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

This is a **topic** example — one publisher, one subscriber, streaming. Services and actions come in Project B.

Run each in a separate terminal. On Mac, each terminal needs its own Docker shell (`docker exec -it ros2 bash`).

```bash
# Terminal 1 (inside container)
python3 workspace/ros2/ch01/publisher.py

# Terminal 2 (inside container)
python3 workspace/ros2/ch01/subscriber.py
```

Note: `rclpy` is not a `pip install` — it's part of ROS2 and only available after sourcing `/opt/ros/jazzy/setup.bash`. Running these scripts outside the container will fail with `ModuleNotFoundError: No module named 'rclpy'`.

---

## Project B — Topics, Services, Actions

**Problem:** Understand when to use each communication pattern.

**Approach:** Build a package with a custom action type, then one node that exposes all three patterns. Poke it with CLI tools — no extra node needed.

| Pattern | Use when | Example |
|---------|----------|---------|
| Topic | Continuous stream, many listeners | sensor data, odometry |
| Service | One-shot request/reply | query state, trigger action |
| Action | Long-running task with feedback | navigate to goal, run SLAM |

### Step 1 — Create two packages

All three patterns need a type definition. For topics and services, primitives from `std_msgs` and `std_srvs` cover simple cases — `String`, `Int32`, `Empty` — and those ship with ROS2. Actions are different: their type must have three sections (goal / result / feedback) and no built-in type fits, so you always define your own.

Compiling a custom action type requires `ament_cmake`. But your node code is Python, which uses `ament_python`. These two build types can't live in the same package — so you need two:

- **`ch01_interfaces`** — cmake package, defines and compiles `CountTo.action`
- **`ch01_ros2package`** — python package, contains the node, imports from `ch01_interfaces`

🟢 **Run** — skip any folder that already exists

```bash
cd /workspace/ros2/ch01
ros2 pkg create --build-type ament_cmake ch01_interfaces
ros2 pkg create --build-type ament_python ch01_ros2package
```

### Step 2 — Define the action type in ch01_interfaces

An action type is a plain text file with three sections separated by `---`:

```
<goal fields>      # what the client sends to kick off the action
---
<result fields>    # what the server sends once when done
---
<feedback fields>  # what the server streams while running
```

Each field is `<type> <name>`, same syntax as a ROS2 message.

🔴 **Work** — read the fields, then add `float32 delay_max` to the goal so callers can control the random delay

```bash
mkdir -p /workspace/ros2/ch01/ch01_interfaces/action

cat > /workspace/ros2/ch01/ch01_interfaces/action/CountTo.action << 'EOF'
string name       # label for this counter — shows up in every feedback message
int32 target      # count from 0 up to this number
---
string summary    # sent once when done, e.g. "alice done: 0..10"
---
string progress   # sent at each step, e.g. "alice-3"
EOF
```

Replace `/workspace/ros2/ch01/ch01_interfaces/package.xml` with:

```xml
<?xml version="1.0"?>
<package format="3">
  <name>ch01_interfaces</name>
  <version>0.0.1</version>
  <description>ROS2 ch01 custom action types</description>
  <maintainer email="you@example.com">you</maintainer>
  <license>Apache-2.0</license>

  <buildtool_depend>ament_cmake</buildtool_depend>
  <buildtool_depend>rosidl_default_generators</buildtool_depend>

  <depend>action_msgs</depend>

  <exec_depend>rosidl_default_runtime</exec_depend>
  <member_of_group>rosidl_interface_packages</member_of_group>

  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
```

Replace `/workspace/ros2/ch01/ch01_interfaces/CMakeLists.txt` with:

```cmake
cmake_minimum_required(VERSION 3.8)
project(ch01_interfaces)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(action_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "action/CountTo.action"
  DEPENDENCIES action_msgs
)

ament_package()
```

Replace `/workspace/ros2/ch01/ch01_ros2package/package.xml` with:

```xml
<?xml version="1.0"?>
<package format="3">
  <name>ch01_ros2package</name>
  <version>0.0.1</version>
  <description>ROS2 ch01 — topics, services, actions</description>
  <maintainer email="you@example.com">you</maintainer>
  <license>Apache-2.0</license>

  <buildtool_depend>ament_python</buildtool_depend>

  <depend>rclpy</depend>
  <depend>std_msgs</depend>
  <depend>std_srvs</depend>
  <depend>ch01_interfaces</depend>

  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
```

Replace `/workspace/ros2/ch01/ch01_ros2package/setup.py` with:

```python
from setuptools import find_packages, setup

package_name = 'ch01_ros2package'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'multi_pattern_node = ch01_ros2package.multi_pattern_node:main',
        ],
    },
)
```

Build both packages — `ch01_interfaces` must build first since `ch01_ros2package` depends on it:

🟢 **Run**

```bash
# run from /workspace/ros2/ch01
cd /workspace/ros2/ch01
colcon build
source /workspace/ros2/ch01/install/setup.bash
```

`colcon build` (no `--packages-select`) builds both in dependency order. `ch01_interfaces` compiles `CountTo.action` into a Python module; `ch01_ros2package` installs the node. You must `source install/setup.bash` after every build.

Verify the type compiled:

```bash
# ros2 interface show <package>/<type>
# Prints the fields of any message, service, or action type
# Works from any directory — sourcing install/setup.bash registers the package
# into the shell session so all ros2 commands can find it regardless of cwd
ros2 interface show ch01_interfaces/action/CountTo
```

### Step 3 — Build the node

This node exposes all three patterns: a status topic, a reset service, and the `CountTo` action. Multiple clients can run the action concurrently — each gets its own named counter.

Data flow:
```
timer  → /status topic  (streams all active counters)
client → /reset service → reply  (clears all counters)
client → /count_to action → feedback stream → result
```

Save this to `/workspace/ros2/ch01/ch01_ros2package/ch01_ros2package/multi_pattern_node.py`:

🔴 **Work** — run it, then call each pattern from the CLI

```python
import random
import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from std_msgs.msg import String
from std_srvs.srv import Empty
from ch01_interfaces.action import CountTo

class MultiPatternNode(Node):
    def __init__(self) -> None:
        super().__init__('multi_pattern')
        self.active: dict[str, int] = {}  # name → current count for all running actions

        # Topic — publish a summary of all active counters every second
        # create_publisher(type, topic_name, queue_size)
        # queue_size: messages to buffer if the subscriber is slow; 10 is a safe default
        self.pub = self.create_publisher(String, '/status', 10)
        self.create_timer(1.0, self.publish_status)

        # Service — create_service(type, service_name, callback)
        self.create_service(Empty, '/reset', self.handle_reset)

        # Action — ActionServer(node, type, action_name, callback, callback_group)
        # ReentrantCallbackGroup: allows multiple goals to execute concurrently
        self._action_server = ActionServer(
            self, CountTo, '/count_to',
            self.handle_count,
            callback_group=ReentrantCallbackGroup(),
        )
        self.get_logger().info('Node ready')

    def publish_status(self) -> None:
        summary = '  '.join(f'{n}={v}' for n, v in self.active.items()) or 'idle'
        msg = String()
        msg.data = summary
        self.pub.publish(msg)

    # Service callback — _req is ignored (Empty has no fields), but must be in the signature
    def handle_reset(self, _req: Empty.Request, res: Empty.Response) -> Empty.Response:
        self.active.clear()
        self.get_logger().info('All counters reset')
        return res

    # Action callback — called once per goal, runs until done, streams feedback
    def handle_count(self, goal_handle) -> CountTo.Result:
        name: str   = goal_handle.request.name    # from the client's goal message
        target: int = goal_handle.request.target

        feedback = CountTo.Feedback()
        for i in range(target + 1):
            self.active[name] = i
            feedback.progress = f'{name}-{i}'         # e.g. "alice-3"
            goal_handle.publish_feedback(feedback)    # sends to the client immediately
            self.get_logger().info(feedback.progress)
            if i < target:
                time.sleep(random.uniform(0.1, 3.0))

        del self.active[name]
        goal_handle.succeed()                         # marks the action as successfully completed
        result = CountTo.Result()
        result.summary = f'{name} done: 0..{target}'
        return result

def main() -> None:
    rclpy.init()
    node = MultiPatternNode()
    # MultiThreadedExecutor runs callbacks on a thread pool
    # needed here so concurrent action goals don't block each other
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    executor.spin()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

Build and run:

🟢 **Run**

```bash
# run from /workspace/ros2/ch01
cd /workspace/ros2/ch01
colcon build --packages-select ch01_ros2package && source /workspace/ros2/ch01/install/setup.bash
ros2 run ch01_ros2package multi_pattern_node
```

### Step 4 — Poke each pattern

Open a second terminal (`docker exec -it ros2 bash` on Mac), then `source /workspace/ros2/ch01/install/setup.bash`.

🟢 **Run**

```bash
# ros2 topic echo <topic>
# Subscribes and prints every message published to /status
ros2 topic echo /status
```

Expected output — `ros2 topic echo` separates each message with `---`:

```text
data: idle
---
data: alice=2
---
data: alice=3  bob=0
---
data: alice=4  bob=1
---
```

```bash
# ros2 service call <service> <type> "<yaml args>"
# Sends one request and prints the response. "{}" = no fields (Empty has none)
ros2 service call /reset std_srvs/srv/Empty "{}"
```

Expected output:

```text
requester: making request: std_srvs.srv.Empty_Request()

response:
std_srvs.srv.Empty_Response()
```

```bash
# ros2 action send_goal <action> <type> "<yaml goal>" --feedback
# Sends a goal; --feedback prints each feedback message as it arrives, then prints the result
ros2 action send_goal /count_to ch01_interfaces/action/CountTo \
  "{name: alice, target: 5}" --feedback
```

Expected output:

```text
Sending goal:
     name: alice
     target: 5

Feedback:
    progress: alice-0

Feedback:
    progress: alice-1

Feedback:
    progress: alice-2

Feedback:
    progress: alice-3

Feedback:
    progress: alice-4

Feedback:
    progress: alice-5

Result:
    summary: alice done: 0..5

Goal finished with status: SUCCEEDED
```

Open a third terminal and fire a second goal while the first is still running:

```bash
ros2 action send_goal /count_to ch01_interfaces/action/CountTo \
  "{name: bob, target: 8}" --feedback
```

Watch `/status` in the topic terminal — `alice` and `bob` both appear, advancing at their own random pace. That's `MultiThreadedExecutor` + `ReentrantCallbackGroup` giving each goal its own thread.

Useful inspection commands:

🟡 **Know**

```bash
ros2 node list                                     # all running nodes
ros2 node info /multi_pattern                      # topics/services/actions this node exposes
ros2 topic list                                    # all active topics
ros2 topic hz /status                              # measured publish rate (should be ~1 Hz)
ros2 service list
ros2 action list
ros2 interface show ch01_interfaces/action/CountTo   # inspect the action type fields
```

`ros2 node info /multi_pattern` returns a long list — but only three lines come from your code. Everything else is framework boilerplate that every ROS2 node gets automatically.

**The three things you wrote:**

| Section | Entry | Created by |
|---------|-------|------------|
| Publishers | `/status` (`std_msgs/msg/String`) | `self.create_publisher(String, '/status', 10)` |
| Service Servers | `/reset` (`std_srvs/srv/Empty`) | `self.create_service(Empty, '/reset', ...)` |
| Action Servers | `/count_to` (`ch01_interfaces/action/CountTo`) | `ActionServer(self, CountTo, '/count_to', ...)` |

The action server entry is also confirmation that your custom `ch01_interfaces` package built and registered correctly — the type name `ch01_interfaces/action/CountTo` only appears here if rosidl generated it.

**Everything else is auto-added by ROS2:**

- `/parameter_events` and `/rosout` publishers — every node publishes parameter changes and log lines on these standard topics. That's why `ros2 topic echo /rosout` shows logs from any node without setup.
- The seven `/multi_pattern/*_parameters` services — every node exposes these so commands like `ros2 param get /multi_pattern <name>` work without you wiring anything up.
- Empty `Subscribers` / `Service Clients` / `Action Clients` — your node only serves; it doesn't consume.

---

## Project C — Launch Files & Bags

**Two separate problems, two separate tools:**

1. **Starting many nodes is tedious.** A real robot system has 5–20 nodes. You don't want to open 20 terminals and type 20 commands. **Launch files** start a list of nodes with one command.

2. **Robot data is expensive to collect.** A real robot run requires hardware, a specific environment, and time. You want to record sensor data once and replay it as if the robot were still running — so you can iterate on your code offline, reproduce bugs, or share recordings. **Bags** record topic messages to disk and play them back.

**Approach:** Write a launch file that starts publisher + subscriber together. Record a bag from one terminal, replay it into a listener.

### Launch file

A launch file is a Python script that returns a list of nodes to start.

The launch tools are already included in `osrf/ros:jazzy-desktop` (Mac/Docker). On a fresh Linux install where you only installed `ros-jazzy-ros-base`, you may need to add them:

🟢 **Run** — Linux only, skip if launch tools already work

```bash
sudo apt install -y ros-jazzy-launch ros-jazzy-launch-ros
```

🔴 **Work** — add a third node to the launch file

```python workspace/ros2/ch01/my_launch.py
# workspace/ros2/ch01/my_launch.py
from launch import LaunchDescription
from launch_ros.actions import Node

# 1. LaunchDescription lists everything to start
def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([
        # 1.1 Publisher node
        Node(
            package='demo_nodes_py',
            executable='talker',
            name='my_talker',
            output='screen',
        ),
        # 1.2 Subscriber node
        Node(
            package='demo_nodes_py',
            executable='listener',
            name='my_listener',
            output='screen',
        ),
    ])
```

Run it by pointing `ros2 launch` at the file directly:

🟢 **Run**

```bash
ros2 launch /workspace/ros2/ch01/my_launch.py
```

Both nodes start together. Ctrl+C kills them both.

### Record and replay a bag

A bag records topic messages to disk. You can replay them later — useful for testing offline or debugging.

We'll record the `/chatter` topic — that's the topic the built-in `demo_nodes_py talker` publishes to (and `listener` subscribes to). The name `/chatter` isn't special; it's just hardcoded into the demo node. You can confirm it's live with `ros2 topic list` while the talker runs.

🟢 **Run**

```bash
# Start the demo talker in one terminal — it publishes "Hello World: N" to /chatter
ros2 run demo_nodes_py talker

# In a second terminal — record the /chatter topic into a folder named my_bag (Ctrl+C to stop)
ros2 bag record /chatter -o my_bag

# Stop the talker (Ctrl+C in the first terminal). Now replay the recording:
ros2 bag play my_bag

# In a third terminal — start a listener; it receives the replayed messages as if talker were live
ros2 run demo_nodes_py listener
```

Note: `ros2 bag record` creates a folder called `my_bag/`, not a single file. `ros2 bag play my_bag` plays everything in that folder. The listener doesn't know or care that the messages came from a recording — that's the whole point of pub/sub.

---

## Self-Check

1. What's the difference between a topic and a service? — **Answer:** Topics are one-to-many streams (publishers/subscribers); services are one-to-one request/reply. Use topics for continuous data, services for on-demand queries.
2. You call `ros2 topic echo /chatter` and see nothing. What's wrong? — **Answer:** Either no node is publishing to `/chatter`, or the topic name is wrong. Check `ros2 topic list`.
3. What does `colcon build` produce? — **Answer:** A compiled `install/` directory. For packages with `.action` files (like `ch01_interfaces`), it generates the Python module (e.g. `ch01_interfaces.action.CountTo`). You must `source install/setup.bash` after every build for ROS2 to find them.
4. Why use an action instead of a service for navigation? — **Answer:** Navigation takes seconds to minutes. Actions support progress feedback and cancellation; services block until complete with no visibility.
5. You replay a bag but the listener gets nothing. Why? — **Answer:** The listener node may not be running, or the topic names don't match. Check `ros2 topic list` while the bag is playing.

---

## Common Mistakes

- **Forgetting to source ROS2**: `source /opt/ros/jazzy/setup.bash` must be run in every new terminal (or added to `.bashrc`). Without it, `ros2` commands don't exist.
- **Forgetting to source after colcon build**: After every `colcon build`, run `source /workspace/ros2/ch01/install/setup.bash`. Without it, ROS2 can't find your package or generated types even if the build succeeded.
- **Wrong queue size**: A queue of 1 drops messages if the subscriber is slow. Use 10 as a default; reduce only when memory is a constraint.
- **Topic name typos**: `/status` and `/Status` are different topics. `ros2 topic list` is your first debugging step.
- **`docker exec` vs new terminal**: A new terminal window on your machine doesn't have ROS2. Use `docker exec -it ros2 bash` to get a shell inside the running container.

---

## Resources

1. [ROS2 Jazzy docs — Concepts](https://docs.ros.org/en/jazzy/Concepts.html) — mental model for nodes, topics, services, actions
2. [Writing a simple publisher/subscriber (Python)](https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Publisher-And-Subscriber.html) — official step-by-step
3. [Understanding ROS2 actions](https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Actions/Understanding-ROS2-Actions.html) — when and why to use actions

---

## Appendix — Deployment, the longer version

Extra detail for [Where do these nodes run?](#where-do-these-nodes-run). Read this when you're deploying onto real hardware (ch03 onwards) or staring at "where should this node run?".

### micro-ROS: when the MCU itself runs ROS2

Default architecture: the MCU speaks a custom serial protocol; a driver node on the SBC translates. **micro-ROS** is the alternative — a stripped-down ROS2 client library that runs on the MCU itself. The MCU then publishes/subscribes to real ROS2 topics directly. A small `micro_ros_agent` process on a host bridges micro-ROS's serial transport to standard DDS so the rest of the network sees normal topics.

```
default:    MCU ──serial protocol──► driver node ──► ROS2 graph
micro-ROS:  MCU ──ROS2 topics (XRCE-DDS over serial)──► agent ──► ROS2 graph
```

Use it when **you control the MCU firmware** and want to skip writing a custom protocol + driver-node pair (the agent is generic). Skip it when you're using a robot with vendor-supplied firmware — you can't run micro-ROS on the OpenCR or on Dynamixel servos. ([micro.ros.org](https://micro.ros.org/))

### What ROS2 gives you, what you still write

ROS2 ships:
- **DDS auto-discovery** across machines on the same network and `ROS_DOMAIN_ID`.
- **Standard message types** (`sensor_msgs`, `geometry_msgs`, `nav_msgs`…) so nodes from different vendors interoperate.
- **Transport** — TCP/UDP/shared-memory, chosen by DDS based on whether peers are local or remote.

You still write:
- **Driver nodes**, if the vendor doesn't ship one. For TurtleBot3, ROBOTIS ships `turtlebot3_node` (host side) + OpenCR firmware (MCU side) — you don't write either. For an off-brand lidar, you'd wrap its serial protocol in a node.
- **Application logic** — nodes that decide *what the robot does* given the sensor stream.
- **MCU firmware**, only if you built the robot yourself. Existing robots come with firmware.

### Per-layer placement table (TurtleBot3 example)

A worked example. The pattern (drivers next to hardware, heavy compute next to GPU/CPU, viz next to the human) generalizes.

| Layer | Pinned to | Why |
|---|---|---|
| Sensor & motor drivers | Robot SBC (RPi/Jetson) | Drivers need direct USB/serial access to the physical hardware. Streaming raw sensor frames over the network is too much bandwidth and too much latency. |
| Real-time motor control | OpenCR MCU | The SBC runs Linux (non-real-time). kHz-rate closed-loop wheel control needs deterministic timing — that has to live on the microcontroller. The SBC just sends `Twist`-style velocity commands and the MCU translates them to motor voltages. |
| Planning, SLAM, Nav2 | A VM on the network (laptop, Linux server, GPU server, or the SBC if it's powerful enough) | CPU/RAM-hungry, but don't care about a few ms of WiFi latency. Almost always easier to iterate on a beefy box than to redeploy to a Pi every change. |
| Perception nets, ML policies | GPU server (or any VM with a GPU) | Need a GPU. Run on whichever machine in your network has one. |
| Visualization (Foxglove, rviz2) | Wherever the human is | The robot has no monitor. Foxglove subscribes to topics over the same DDS network and renders them on your screen. |
| Recording (`ros2 bag`) | Anywhere with disk space | Most teams record on the SBC for the rawest data, then copy bags off later. Some record on a host VM. |
