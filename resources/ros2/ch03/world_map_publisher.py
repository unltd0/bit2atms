"""world_map_publisher.py — publish tiny_world.sdf's walls as /map for Foxglove.

Gazebo's scene graph (worlds, models, walls) is *not* bridged to ROS2 by
default — there's no Gazebo topic that says "here's where the walls are."
So Foxglove, which only ever sees ROS2 topics, renders tiny_bot driving
through what looks like empty space.

This node hand-authors an OccupancyGrid that matches tiny_world.sdf:
a 3.4 m x 3.4 m grid at 5 cm/cell, with the four perimeter walls (each
0.1 m thick, at x=±1.5 and y=±1.5) marked occupied. Publishes once at
startup on /map (latched via TRANSIENT_LOCAL QoS, so Foxglove gets it
whenever it connects), then republishes at 1 Hz as a heartbeat.

Frame: odom — same as the diff-drive plugin's odom frame, so the map
sits at the world origin where tiny_bot spawns. No SLAM, no AMCL; the
walls are known geometry, not estimated.
"""
import rclpy
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile

# Match tiny_world.sdf.
WALL_X = 1.5              # wall distance from origin
WALL_THICKNESS = 0.10     # box <size> 0.1 ... in tiny_world.sdf
RESOLUTION = 0.05         # 5 cm per grid cell
EXTENT = 1.7              # half-side of the map (a bit beyond the walls)


def build_grid() -> OccupancyGrid:
    side = int(round(2 * EXTENT / RESOLUTION))   # cells per axis
    data = [0] * (side * side)

    def mark_box(x_min: float, x_max: float, y_min: float, y_max: float) -> None:
        for iy in range(side):
            y = -EXTENT + (iy + 0.5) * RESOLUTION
            if not (y_min <= y <= y_max):
                continue
            for ix in range(side):
                x = -EXTENT + (ix + 0.5) * RESOLUTION
                if x_min <= x <= x_max:
                    data[iy * side + ix] = 100   # 100 = occupied

    t = WALL_THICKNESS / 2
    # Four perimeter walls.
    mark_box(WALL_X - t,  WALL_X + t,  -WALL_X, WALL_X)   # front (+x)
    mark_box(-WALL_X - t, -WALL_X + t, -WALL_X, WALL_X)   # back  (-x)
    mark_box(-WALL_X, WALL_X,  WALL_X - t,  WALL_X + t)   # left  (+y)
    mark_box(-WALL_X, WALL_X, -WALL_X - t, -WALL_X + t)   # right (-y)

    grid = OccupancyGrid()
    grid.header.frame_id = "odom"
    grid.info.resolution = RESOLUTION
    grid.info.width = side
    grid.info.height = side
    grid.info.origin.position.x = -EXTENT
    grid.info.origin.position.y = -EXTENT
    grid.info.origin.position.z = 0.0
    grid.info.origin.orientation.w = 1.0
    grid.data = data
    return grid


class WorldMapPublisher(Node):
    def __init__(self) -> None:
        super().__init__("world_map_publisher")

        # TRANSIENT_LOCAL: late-joining subscribers (Foxglove, after the
        # student loads the layout) still receive the last published map.
        qos = QoSProfile(depth=1)
        qos.durability = QoSDurabilityPolicy.TRANSIENT_LOCAL

        self.pub = self.create_publisher(OccupancyGrid, "/map", qos)
        self.grid = build_grid()

        # Publish once immediately + every 1 s as a heartbeat.
        self.tick()
        self.create_timer(1.0, self.tick)

        self.get_logger().info(
            f"world_map_publisher ready: {self.grid.info.width}x{self.grid.info.height} "
            f"cells, {RESOLUTION:.2f} m/cell, 4 walls at ±{WALL_X:.2f} m"
        )

    def tick(self) -> None:
        self.grid.header.stamp = self.get_clock().now().to_msg()
        self.pub.publish(self.grid)


def main() -> None:
    rclpy.init()
    rclpy.spin(WorldMapPublisher())
    rclpy.shutdown()


if __name__ == "__main__":
    main()
