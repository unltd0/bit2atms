from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator
import rclpy

def main() -> None:
    rclpy.init()
    nav = BasicNavigator()

    goal = PoseStamped()
    goal.header.frame_id = 'map'  # coordinates are in the map frame
    goal.pose.position.x = 1.0   # meters from map origin (see my_map.yaml)
    goal.pose.position.y = 0.5
    goal.pose.orientation.w = 1.0  # w=1 = no rotation (facing +x)

    nav.goToPose(goal)
    while not nav.isTaskComplete():
        feedback = nav.getFeedback()
        if feedback:
            print(f'Distance remaining: {feedback.distance_remaining:.2f} m')

    print('Result:', nav.getResult())
    rclpy.shutdown()

if __name__ == '__main__':
    main()
