#!/usr/bin/env python3
# Obstacle detection for SLAM map building.
# Publishes Twist to /cmd_vel — matches the patched bridge config in
# resources/ros2/turtlebot3_burger_bridge.yaml (which uses Twist instead of
# TwistStamped so Nav2's default cmd_vel output also drives the robot).

import random
from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data, QoSProfile
from sensor_msgs.msg import LaserScan

STOP_DISTANCE = 0.4   # metres
LINEAR_SPEED  = 0.15  # m/s — slow enough for clean SLAM scan matching
TURN_SPEED    = 0.5   # rad/s — gentle enough not to overshoot
TURN_DURATION = 1.5   # seconds — commit to a turn before re-evaluating


class ObstacleDetection(Node):

    def __init__(self):
        super().__init__('obstacle_detection')
        self.get_logger().info('Obstacle detection started — driving for SLAM map building')
        self.get_logger().info(f'Speed: {LINEAR_SPEED} m/s  Stop distance: {STOP_DISTANCE} m')

        self.scan_ranges = []
        self.has_scan = False
        self.turn_dir = 1.0
        self.turning_until = 0.0  # clock time when current turn ends

        qos = QoSProfile(depth=10)
        self.pub = self.create_publisher(Twist, 'cmd_vel', qos)
        self.create_subscription(LaserScan, 'scan', self.scan_cb, qos_profile_sensor_data)
        self.create_timer(0.1, self.timer_cb)

    def scan_cb(self, msg):
        self.scan_ranges = msg.ranges
        self.has_scan = True

    def timer_cb(self):
        if not self.has_scan:
            return

        now = self.get_clock().now().nanoseconds / 1e9
        n = len(self.scan_ranges)
        front = self.scan_ranges[:n // 4] + self.scan_ranges[n * 3 // 4:]
        valid = [r for r in front if r > 0.01]
        obstacle = min(valid) if valid else 999.0

        twist = Twist()

        if now < self.turning_until:
            # Still committed to current turn — don't re-evaluate
            twist.linear.x = 0.0
            twist.angular.z = TURN_SPEED * self.turn_dir
        elif obstacle < STOP_DISTANCE:
            # New obstacle — pick direction and commit for TURN_DURATION seconds
            self.turn_dir = random.choice([1.0, -1.0])
            self.turning_until = now + TURN_DURATION
            twist.linear.x = 0.0
            twist.angular.z = TURN_SPEED * self.turn_dir
            self.get_logger().info(
                f'Obstacle at {obstacle:.2f}m — turning {"left" if self.turn_dir > 0 else "right"} for {TURN_DURATION}s')
        else:
            twist.linear.x = LINEAR_SPEED
            twist.angular.z = 0.0

        self.pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleDetection()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
