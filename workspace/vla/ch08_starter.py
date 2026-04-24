#!/usr/bin/env python3
"""
Chapter 08 — ROS 2 & Integration
workspace/vla/ch08_starter.py

Projects to complete (see courses/vla/ch08_ros2/README.md):
  1. Write a ROS 2 node that subscribes to joint states and publishes commands
  2. Bridge your policy to a ROS 2 action server
  3. Test the full pipeline with MoveIt 2 in simulation

Run inside a sourced ROS 2 workspace:
  ros2 run <your_package> ch08_starter
"""

import rclpy
from rclpy.node import Node

# Uncomment when ROS 2 messages are installed:
# from sensor_msgs.msg import JointState
# from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
# from std_msgs.msg import Float64MultiArray


# ── TODO 1: Joint state subscriber + command publisher ───────────────────
class ArmController(Node):
    def __init__(self):
        super().__init__('arm_controller')
        # TODO: create subscriber to /joint_states
        # TODO: create publisher to /joint_group_effort_controller/commands
        self.get_logger().info('ArmController started')

    def joint_state_callback(self, msg):
        # TODO: read current joint positions/velocities
        # TODO: compute control command
        # TODO: publish command
        raise NotImplementedError


# ── TODO 2: Policy action server ────────────────────────────────────────
# from rclpy.action import ActionServer
# from control_msgs.action import FollowJointTrajectory

class PolicyActionServer(Node):
    def __init__(self, policy):
        super().__init__('policy_action_server')
        self.policy = policy
        # TODO: create ActionServer
        raise NotImplementedError


# ── TODO 3: MoveIt 2 integration ────────────────────────────────────────
def plan_and_execute(target_pose_stamped):
    """Use MoveIt 2 Python bindings to plan and execute to target_pose."""
    # from moveit.planning import MoveItPy
    raise NotImplementedError


def main():
    rclpy.init()
    node = ArmController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
