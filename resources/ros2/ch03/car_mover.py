"""car_mover.py — the fake human at the joystick.

Publishes a pre-canned drive pattern on /cmd_vel_in: forward, turn, forward, stop,
on a loop. obstacle_stop forwards to /cmd_vel; Gazebo's DiffDrive plugin (or a
real motor driver, on hardware) picks it up.

This is the equivalent of teleop_twist_keyboard or a Nav2 controller — anything
that produces geometry_msgs/Twist. Swap this out for a teleop node or Nav2 and
the downstream stack wouldn't know the difference. That's the contract.

Run with:
    python3 /workspace/ros2/ch03/car_mover.py
"""
import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node

# Drive pattern as (linear_x [m/s], angular_z [rad/s], duration [s]) tuples.
# Tweak freely — the motor driver will integrate whatever you publish.
#
# When obstacle_stop blocks the forward phase, the spin phase still goes
# through. Spin rate × duration is sized so the robot turns ~180° per
# spin attempt — enough to clear whichever wall it's facing.
PATTERN = [
    (0.20, 0.0, 4.0),   # forward 0.2 m/s for 4 s  (covers the room)
    (0.0,  1.5, 2.0),   # spin left 1.5 rad/s for 2 s  (~180°)
    (0.20, 0.0, 4.0),   # forward again
    (0.0,  0.0, 1.0),   # brief stop
]


class CarMover(Node):
    def __init__(self) -> None:
        super().__init__("car_mover")
        # Publish on /cmd_vel_in (not /cmd_vel). obstacle_stop.py sits between
        # us and the motor driver, forwarding to /cmd_vel unless the IR says
        # something's too close. If you're running without obstacle_stop, just
        # remap this topic back to /cmd_vel.
        self.pub = self.create_publisher(Twist, "/cmd_vel_in", 10)

        # Walk the pattern in step with a 10 Hz timer.
        self.step_idx = 0
        self.step_elapsed = 0.0
        self.tick_dt = 0.1
        self.create_timer(self.tick_dt, self.tick)

    def tick(self) -> None:
        vx, wz, duration = PATTERN[self.step_idx]

        msg = Twist()
        msg.linear.x = vx
        msg.angular.z = wz
        self.pub.publish(msg)

        self.step_elapsed += self.tick_dt
        if self.step_elapsed >= duration:
            self.step_elapsed = 0.0
            self.step_idx = (self.step_idx + 1) % len(PATTERN)
            self.get_logger().info(
                f"next step: vx={PATTERN[self.step_idx][0]:.2f} "
                f"wz={PATTERN[self.step_idx][1]:.2f}"
            )


def main() -> None:
    rclpy.init()
    rclpy.spin(CarMover())
    rclpy.shutdown()


if __name__ == "__main__":
    main()
