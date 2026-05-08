"""Republishes /ground_truth_pose with frame_id corrected to 'map'.

Gazebo's PosePublisher uses the world name ("default") as frame_id.
That frame isn't in the TF tree, so Foxglove can't render it.
This node relays the message with frame_id overridden to 'map'.
"""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseArray

class GroundTruthRelay(Node):
    def __init__(self):
        super().__init__('ground_truth_relay')
        self.pub = self.create_publisher(PoseArray, '/ground_truth_pose_map', 10)
        self.create_subscription(PoseArray, '/ground_truth_pose', self.cb, 10)

    def cb(self, msg: PoseArray):
        msg.header.frame_id = 'map'
        self.pub.publish(msg)

def main():
    rclpy.init()
    rclpy.spin(GroundTruthRelay())
    rclpy.shutdown()

if __name__ == '__main__':
    main()
