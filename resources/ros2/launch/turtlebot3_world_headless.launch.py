# Headless variant of turtlebot3_gazebo/launch/turtlebot3_world.launch.py
# Changes vs. upstream:
#   1. gzclient_cmd (the GUI) is not added — Gazebo runs server-only (headless).
#   2. robot_state_publisher is launched directly (not via the package's
#      launch file) so we can pass frame_prefix='' literally. The packaged
#      launch hardcodes `frame_prefix + '/'`, producing tf2-invalid frame
#      IDs like `/base_scan` that break Foxglove's TF resolution.
#   3. The robot is spawned from our patched SDF (turtlebot3_burger_gt.sdf)
#      which adds the PosePublisher plugin — Gazebo's exact pose is published
#      to /model/turtlebot3_burger/pose and bridged to ROS2 as /ground_truth_pose.
#   4. The ros_gz_bridge uses our patched config (turtlebot3_burger_bridge.yaml)
#      which bridges cmd_vel as geometry_msgs/Twist (not TwistStamped), so Nav2's
#      default velocity output drives the robot without extra configuration.
#
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    tb3_model = os.environ.get('TURTLEBOT3_MODEL', 'burger')
    tb3_share = get_package_share_directory('turtlebot3_gazebo')
    ros_gz_sim = get_package_share_directory('ros_gz_sim')

    world = os.path.join(tb3_share, 'worlds', 'turtlebot3_world.world')
    urdf_path = os.path.join(tb3_share, 'urdf', f'turtlebot3_{tb3_model}.urdf')
    with open(urdf_path, 'r') as f:
        robot_desc = f.read()

    # Patched SDF adds PosePublisher plugin for ground truth pose topic.
    # Resolved relative to this file's directory — works whether launched from
    # resources/ros2/launch/ or workspace/ros2/launch/.
    this_dir = os.path.dirname(os.path.abspath(__file__))
    patched_sdf = os.path.normpath(os.path.join(this_dir, '..', 'turtlebot3_burger_gt.sdf'))

    gzserver_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': ['-r -s -v2 ', world],
            'on_exit_shutdown': 'true',
        }.items(),
    )

    robot_state_publisher_cmd = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'robot_description': robot_desc,
            'frame_prefix': '',
        }],
    )

    # Spawn from our patched SDF (adds PosePublisher for ground truth)
    spawn_turtlebot_cmd = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', tb3_model,
            '-file', patched_sdf,
            '-x', '-2.0',
            '-y', '-0.5',
            '-z', '0.01',
        ],
        output='screen',
    )

    # Bridge the standard topics using our patched config (cmd_vel as Twist, not
    # TwistStamped, so Nav2's default output drives the robot without extra params).
    bridge_params = os.path.join(this_dir, '..', 'turtlebot3_burger_bridge.yaml')
    ros_gz_bridge_cmd = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['--ros-args', '-p', f'config_file:={bridge_params}'],
        output='screen',
    )

    # Bridge Gazebo ground truth pose → ROS2 /ground_truth_pose
    ground_truth_bridge_cmd = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            f'/model/{tb3_model}/pose@geometry_msgs/msg/PoseArray[gz.msgs.Pose_V',
        ],
        remappings=[
            (f'/model/{tb3_model}/pose', '/ground_truth_pose'),
        ],
        output='screen',
    )

    # Relay: republishes /ground_truth_pose with frame_id='map' so Foxglove
    # can render it in the 3D scene. Gazebo's PosePublisher uses the Gazebo
    # world name ("default") as frame_id, which isn't in the ROS2 TF tree.
    ground_truth_relay_cmd = ExecuteProcess(
        cmd=['python3', os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     '..', 'ground_truth_relay.py')],
        output='screen',
    )

    ld = LaunchDescription()
    ld.add_action(gzserver_cmd)
    ld.add_action(robot_state_publisher_cmd)
    ld.add_action(spawn_turtlebot_cmd)
    ld.add_action(ros_gz_bridge_cmd)
    ld.add_action(ground_truth_bridge_cmd)
    ld.add_action(ground_truth_relay_cmd)
    return ld
