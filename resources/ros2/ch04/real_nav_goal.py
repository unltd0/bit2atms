from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator
import rclpy


def make_pose(x: float, y: float, w: float = 1.0) -> PoseStamped:
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.orientation.w = w
    return pose


def main() -> None:
    rclpy.init()
    nav = BasicNavigator()
    nav.waitUntilNav2Active()

    # Edit these to match real coordinates from your map.
    # In Foxglove's 3D panel, hover over a point on the white interior;
    # the bottom-right shows the (x, y) in the map frame.
    waypoints = [
        make_pose(1.0, 0.0),
        make_pose(1.0, 1.0),
    ]

    nav.followWaypoints(waypoints)
    while not nav.isTaskComplete():
        feedback = nav.getFeedback()
        if feedback:
            wp = feedback.current_waypoint
            print(f'Heading to waypoint {wp + 1}/{len(waypoints)}')

    print('Result:', nav.getResult())
    rclpy.shutdown()


if __name__ == '__main__':
    main()
