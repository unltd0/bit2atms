"""obstacle_stop.py — business logic: don't crash into stuff.

Sits between car_mover and the motor driver. Forwards every /cmd_vel_in Twist
to /cmd_vel unchanged — unless the latest /ir_front reading is below the stop
threshold, in which case we publish a zero Twist instead.

This is pure application logic. It has no idea whether the IR data came from
a real Arduino, a Gazebo plugin, or anywhere else, and no idea whether the
motors below are real or simulated. That's the whole point — when you swap
the sim's IR ray sensor for a real-hardware sensor driver on an Arduino car,
this file ships unchanged.

About the message type: Gazebo's ray sensor publishes LaserScan, even when
configured with one ray (which is what tiny_bot's IR sensor is — a single
point distance). LaserScan with samples=1 is a common pattern for point-
distance sensors in sim. For our purposes, msg.ranges[0] is the distance.
On real hardware with a typical IR driver, you'd subscribe to sensor_msgs/Range
instead, but the same business-logic shape applies.

Run with:
    python3 /workspace/ros2/ch03/obstacle_stop.py
"""
import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

STOP_DISTANCE = 0.30   # metres — closer than this and we halt


class ObstacleStop(Node):
    def __init__(self) -> None:
        super().__init__("obstacle_stop")

        # Latest IR reading. Start at "far away" so we don't false-trip
        # before the sensor publishes anything.
        self.latest_ir = float("inf")

        self.create_subscription(LaserScan, "/ir_front", self.on_ir, 10)
        self.create_subscription(Twist, "/cmd_vel_in", self.on_cmd_in, 10)
        self.pub = self.create_publisher(Twist, "/cmd_vel", 10)

    def on_ir(self, msg: LaserScan) -> None:
        # Single ray — just the first (and only) range value.
        # NaN or inf means "out of range / no hit" — treat as "far away."
        r = msg.ranges[0] if msg.ranges else float("inf")
        self.latest_ir = r if math.isfinite(r) else float("inf")

    def on_cmd_in(self, msg: Twist) -> None:
        if self.latest_ir < STOP_DISTANCE:
            # Too close. Drop the command, publish a zero Twist instead.
            self.pub.publish(Twist())
            return
        # Path is clear. Pass the command through unchanged.
        self.pub.publish(msg)


def main() -> None:
    rclpy.init()
    rclpy.spin(ObstacleStop())
    rclpy.shutdown()


if __name__ == "__main__":
    main()
