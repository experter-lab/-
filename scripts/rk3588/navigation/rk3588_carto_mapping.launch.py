"""RK3588 + RPLIDAR S1 + Cartographer 2D 建图

包含：
  - sllidar_node（雷达，复用 rk3588_lidar_bringup.launch.py 的参数化方式）
  - base_link -> laser 静态 TF
  - cartographer_node + occupancy grid
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = get_package_share_directory("medicine_robot_bringup")
    config_dir = os.path.join(pkg_share, "config")

    start_lidar = LaunchConfiguration("start_lidar")
    laser_yaw = LaunchConfiguration("laser_yaw")
    resolution = LaunchConfiguration("resolution")
    publish_period_sec = LaunchConfiguration("publish_period_sec")

    lidar_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("medicine_robot_bringup"),
                "launch",
                "rk3588_lidar_bringup.launch.py",
            ])
        ),
        launch_arguments={
            "serial_port": "/dev/rplidar",
            "serial_baudrate": "256000",
            "frame_id": "laser",
            "enable_static_tf": "true",
            "base_frame_id": "base_link",
            "laser_x": "0.15",
            "laser_y": "0.00",
            "laser_z": "0.12",
            "laser_roll": "0.0",
            "laser_pitch": "0.0",
            "laser_yaw": laser_yaw,
            "range_min_filter": "0.55",
            "range_max_filter": "10.0",
        }.items(),
        condition=__import__("launch").conditions.IfCondition(start_lidar),
    )

    cartographer = Node(
        package="cartographer_ros",
        executable="cartographer_node",
        name="cartographer_node",
        output="screen",
        arguments=[
            "-configuration_directory", config_dir,
            "-configuration_basename", "rk3588_carto_mapping.lua",
        ],
        remappings=[
            ("scan", "/scan"),
            ("imu", "/imu"),
        ],
    )

    occupancy_grid = Node(
        package="cartographer_ros",
        executable="cartographer_occupancy_grid_node",
        name="cartographer_occupancy_grid_node",
        output="screen",
        arguments=[
            "-resolution", resolution,
            "-publish_period_sec", publish_period_sec,
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument("start_lidar", default_value="true",
                              description="Whether to also start sllidar_node"),
        DeclareLaunchArgument("laser_yaw", default_value="0.0"),
        DeclareLaunchArgument("resolution", default_value="0.03"),
        DeclareLaunchArgument("publish_period_sec", default_value="1.0"),
        lidar_bringup,
        cartographer,
        occupancy_grid,
    ])
