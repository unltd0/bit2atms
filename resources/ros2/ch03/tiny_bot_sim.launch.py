# tiny_bot_sim.launch.py — bring up tiny_bot in headless Gazebo.
#
# Starts:
#   1. Gazebo Sim (server-only, headless) with tiny_world.sdf
#   2. robot_state_publisher with the expanded tiny_bot URDF
#   3. ros_gz_sim "create" — spawns tiny_bot.sdf at origin
#   4. ros_gz_bridge with tiny_bot_bridge.yaml (clock, odom, joint_states, tf,
#      ir_front, cmd_vel)
#   5. world_map_publisher.py — publishes tiny_world's walls as /map so
#      Foxglove can render them (Gazebo doesn't bridge its scene graph).
#
# Run with:
#   ros2 launch /workspace/ros2/ch03/tiny_bot_sim.launch.py
#
# Then in separate shells:
#   ros2 launch foxglove_bridge foxglove_bridge_launch.xml port:=8765
#   python3 /workspace/ros2/ch03/car_mover.py
#   python3 /workspace/ros2/ch03/obstacle_stop.py
import os
import subprocess

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    this_dir = os.path.dirname(os.path.abspath(__file__))
    world_file = os.path.join(this_dir, 'tiny_world.sdf')
    robot_sdf = os.path.join(this_dir, 'tiny_bot.sdf')
    urdf_xacro = os.path.join(this_dir, 'tiny_bot.urdf.xacro')
    bridge_yaml = os.path.join(this_dir, 'tiny_bot_bridge.yaml')

    # Expand xacro at launch time so we don't need a manual generation step.
    robot_desc = subprocess.check_output(['xacro', urdf_xacro]).decode()

    ros_gz_sim = get_package_share_directory('ros_gz_sim')

    gz_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            # -r run on start, -s server only (headless), -v2 verbose
            'gz_args': f'-r -s -v2 {world_file}',
            'on_exit_shutdown': 'true',
        }.items(),
    )

    robot_state_publisher = Node(
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

    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'tiny_bot',
            '-file', robot_sdf,
            # SDF model already lifts itself to z=0.15 (chassis centre) via
            # its own <pose>. Spawn at world z=0 so it lands on the ground.
            '-x', '0', '-y', '0', '-z', '0',
        ],
        output='screen',
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['--ros-args', '-p', f'config_file:={bridge_yaml}'],
        output='screen',
    )

    # Publish the static walls as nav_msgs/OccupancyGrid on /map so Foxglove
    # can render them. Gazebo's scene graph isn't bridged to ROS2, so the
    # walls would otherwise be invisible to anything outside Gazebo.
    world_map_pub = ExecuteProcess(
        cmd=['python3', os.path.join(this_dir, 'world_map_publisher.py')],
        output='screen',
    )

    ld = LaunchDescription()
    ld.add_action(gz_server)
    ld.add_action(robot_state_publisher)
    ld.add_action(spawn)
    ld.add_action(bridge)
    ld.add_action(world_map_pub)
    return ld
