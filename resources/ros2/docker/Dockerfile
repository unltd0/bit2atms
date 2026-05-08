FROM osrf/ros:jazzy-desktop

# Everything ch01 + ch02 + ch03 need, installed once at build time
RUN apt-get update && apt-get install -y \
      ros-jazzy-turtlebot3 \
      ros-jazzy-turtlebot3-simulations \
      ros-jazzy-turtlebot3-gazebo \
      ros-jazzy-turtlebot3-teleop \
      ros-jazzy-nav2-bringup \
      ros-jazzy-slam-toolbox \
      ros-jazzy-rviz2 \
      ros-jazzy-tf2-tools \
      ros-jazzy-tf2-ros \
      ros-jazzy-foxglove-bridge \
      python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 8765

# Auto-source ROS2 + set TurtleBot3 model in every shell
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc \
 && echo "export TURTLEBOT3_MODEL=burger" >> /root/.bashrc \
 && echo "[ -f /workspace/ros2/ch01/install/setup.bash ] && source /workspace/ros2/ch01/install/setup.bash" >> /root/.bashrc

WORKDIR /workspace/ros2
CMD ["bash"]
