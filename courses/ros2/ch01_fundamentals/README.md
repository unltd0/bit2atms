# Chapter 1 — Fundamentals

**Time:** Half day
**Hardware:** Laptop only
**Prerequisites:** Python, terminal comfort

---

## What are we here for

A robot has many moving parts: a camera, a lidar, motors *(hardware)* — and a navigation algorithm, a path planner, a state estimator *(software)*. In a normal program you'd wire these together with function calls — but that breaks down fast. The camera runs at 30 Hz, the planner runs at 10 Hz, the motors need commands at 50 Hz. They need to run concurrently, possibly on different computers, and you need to be able to swap one out without rewriting the rest.

Yes, this sounds like a generic messaging problem — Kafka, gRPC, or ZeroMQ could do it. What makes ROS2 different is that it's built *for robots specifically*. In ch02 and ch03 you'll see what that means concretely: standard message types for sensor data (`LaserScan`, `Odometry`, `Twist`), a coordinate transform system (TF) that tracks where every part of the robot is in 3D space, a navigation stack (Nav2), and a simulator (Gazebo) — all speaking the same language out of the box. In ch01 you'll use simple types to learn the patterns; the robot-specific pieces land once the plumbing makes sense.

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

**Mac users:** You'll use Docker. Every command that needs ROS2 runs inside a container. Linux users install natively.

**Skip if you can answer:**
1. What's the difference between a topic and a service?
2. You have two nodes. How does node B know when node A publishes something?
3. What does `colcon build` do and why do you need it?

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

**Approach:** Docker on Mac, native install on Linux. Then run the built-in demo nodes before writing your own.

### Install

**Mac (Docker):**

🟢 **Run** — pulls the official ROS2 image and drops you into a shell

```bash
docker pull --platform linux/amd64 osrf/ros:jazzy-desktop
docker run -it --rm \
  --platform linux/amd64 \
  --name ros2 \
  -v $(pwd)/workspace/ros2:/workspace/ros2 \
  osrf/ros:jazzy-desktop \
  bash
```

The `--platform linux/amd64` flag is required on Apple Silicon (M1/M2/M3) — without it Docker runs the image anyway but prints a platform mismatch warning. Performance is fine for this course via Rosetta emulation.

Inside the container, source the install:

```bash
source /opt/ros/jazzy/setup.bash
```

Add it to `.bashrc` so you don't have to do this every time:

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
```

**Linux (native):**

```bash
# Add ROS2 apt repo
sudo apt install -y software-properties-common curl
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
sudo sh -c 'echo "deb http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/ros2.list'
sudo apt update
sudo apt install -y ros-jazzy-desktop python3-colcon-common-extensions
source /opt/ros/jazzy/setup.bash
```

### Verify with demo nodes

Open two terminals (two Docker shells if on Mac: `docker exec -it ros2 bash`).

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

# 3. Entry point — spin keeps the node alive and processes callbacks
def main() -> None:
    rclpy.init()
    node = CounterPublisher()
    rclpy.spin(node)
    rclpy.shutdown()

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
    rclpy.spin(CounterSubscriber())
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

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

**Approach:** Build one node that exposes all three. Poke it with CLI tools — no extra node needed.

| Pattern | Use when | Example |
|---------|----------|---------|
| Topic | Continuous stream, many listeners | sensor data, odometry |
| Service | One-shot request/reply | query state, trigger action |
| Action | Long-running task with feedback | navigate to goal, run SLAM |

### A node with all three

This node publishes its status as a topic, serves a reset service, and exposes a count-to-N action.

Data flow:
```
timer → /status topic (streaming)
client → /reset service → reply
client → /count_to action → feedback stream → result
```

🔴 **Work** — run it, then call each pattern from the CLI

ROS2 doesn't have a built-in "count to N" action type — action types are message definitions, like topics. For demo purposes we use `example_interfaces/action/Fibonacci` which ships with ROS2. Its `order` field is the input (how many steps), and `partial_sequence` is the feedback. The name is irrelevant — what matters is the pattern: goal in, feedback stream, result out.

🔴 **Work** — run it, then call each pattern from the CLI

```python workspace/ros2/ch01/multi_pattern_node.py
# workspace/ros2/ch01/multi_pattern_node.py
import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from std_msgs.msg import String
from std_srvs.srv import Empty
from example_interfaces.action import Fibonacci

# 1. Node wires up all three patterns in __init__
class MultiPatternNode(Node):
    def __init__(self) -> None:
        super().__init__('multi_pattern')
        self.count = 0

        # 1.1 Topic — publish status every second
        self.pub = self.create_publisher(String, '/status', 10)
        self.create_timer(1.0, self.publish_status)

        # 1.2 Service — reset the counter on demand
        self.create_service(Empty, '/reset', self.handle_reset)

        # 1.3 Action — count to N steps, send feedback each step
        self._action_server = ActionServer(
            self, Fibonacci, '/count_to', self.handle_count
        )
        self.get_logger().info('Node ready')

    # 2. Topic callback — fires every second
    def publish_status(self) -> None:
        msg = String()
        msg.data = f'count={self.count}'
        self.pub.publish(msg)

    # 3. Service callback — resets counter, returns immediately
    def handle_reset(self, _request: Empty.Request, response: Empty.Response) -> Empty.Response:
        self.count = 0
        self.get_logger().info('Counter reset')
        return response

    # 4. Action callback — runs for goal.order steps, streams feedback
    def handle_count(self, goal_handle) -> Fibonacci.Result:
        target: int = goal_handle.request.order  # how many steps to count
        feedback = Fibonacci.Feedback()
        for i in range(target):
            self.count = i
            feedback.partial_sequence = [i]       # current step as feedback
            goal_handle.publish_feedback(feedback)
            time.sleep(0.5)
        goal_handle.succeed()
        result = Fibonacci.Result()
        result.sequence = list(range(target))     # final list as result
        return result

def main() -> None:
    rclpy.init()
    rclpy.spin(MultiPatternNode())
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

With the node running, poke each pattern from a second terminal:

🟢 **Run**

```bash
# Watch the topic stream
ros2 topic echo /status

# Call the service (resets counter)
ros2 service call /reset std_srvs/srv/Empty "{}"

# Send an action goal (count to 5 steps, watch feedback arrive)
ros2 action send_goal /count_to example_interfaces/action/Fibonacci \
  "{order: 5}" --feedback
```

Useful inspection commands to keep handy:

🟡 **Know**

```bash
ros2 node list                    # all running nodes
ros2 node info /multi_pattern     # topics/services/actions a node exposes
ros2 topic list                   # all active topics
ros2 topic hz /status             # publish rate
ros2 service list
ros2 action list
```

---

## Project C — Launch Files & Bags

**Problem:** Starting nodes one-by-one doesn't scale. You also want to capture and replay data.

**Approach:** Write a launch file that starts publisher + subscriber together. Record a bag, replay it.

### Launch file

A launch file is a Python script that returns a list of nodes to start. Install the launch tools first if not already present:

🟢 **Run**

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
ros2 launch workspace/ros2/ch01/my_launch.py
```

Both nodes start together. Ctrl+C kills them both.

### Record and replay a bag

A bag records all topic messages to disk. You can replay them later — useful for testing offline or debugging.

🟢 **Run**

```bash
# Start talker in one terminal
ros2 run demo_nodes_py talker

# Record /chatter topic in another terminal (Ctrl+C to stop)
ros2 bag record /chatter -o my_bag

# Stop the talker. Now replay:
ros2 bag play my_bag

# In a third terminal — listener sees replayed messages
ros2 run demo_nodes_py listener
```

Note: `ros2 bag record` creates a folder called `my_bag/`, not a single file. `ros2 bag play my_bag` plays everything in that folder. The listener receives the recorded messages as if the talker were running live.

---

## Self-Check

1. What's the difference between a topic and a service? — **Answer:** Topics are one-to-many streams (publishers/subscribers); services are one-to-one request/reply. Use topics for continuous data, services for on-demand queries.
2. You call `ros2 topic echo /chatter` and see nothing. What's wrong? — **Answer:** Either no node is publishing to `/chatter`, or the topic name is wrong. Check `ros2 topic list`.
3. What does `colcon build` produce? — **Answer:** A compiled `install/` directory. You must `source install/setup.bash` after building for ROS2 to find your packages.
4. Why use an action instead of a service for navigation? — **Answer:** Navigation takes seconds to minutes. Actions support progress feedback and cancellation; services block until complete with no visibility.
5. You replay a bag but the listener gets nothing. Why? — **Answer:** The listener node may not be running, or the topic names don't match. Check `ros2 topic list` while the bag is playing.

---

## Common Mistakes

- **Forgetting to source setup.bash**: ROS2 commands won't find your packages. Add `source /opt/ros/jazzy/setup.bash` to `.bashrc`.
- **Wrong queue size**: A queue of 1 drops messages if the subscriber is slow. Use 10 as a default; reduce only when memory is a constraint.
- **Topic name typos**: `/status` and `/Status` are different topics. `ros2 topic list` is your first debugging step.
- **Mac: `docker exec` vs new terminal**: On Mac, a new terminal window doesn't have ROS2. Use `docker exec -it ros2 bash` to get a shell inside the running container.

---

## Resources

1. [ROS2 Jazzy docs — Concepts](https://docs.ros.org/en/jazzy/Concepts.html) — mental model for nodes, topics, services, actions
2. [Writing a simple publisher/subscriber (Python)](https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Publisher-And-Subscriber.html) — official step-by-step
3. [Understanding ROS2 actions](https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Actions/Understanding-ROS2-Actions.html) — when and why to use actions
