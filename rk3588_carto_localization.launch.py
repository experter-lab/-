"""RK3588 + RPLIDAR S1 + Cartographer 2D 纯激光定位

加载 .pbstream 后由 Cartographer 持续发布 map -> odom -> base_link。
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

    pbstream = LaunchConfiguration("pbstream")
    start_lidar = LaunchConfiguration("start_lidar")
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
        condition=__import__("launch").conditions.IfCondition(start_lidar),
    )

    cartographer = Node(
        package="cartographer_ros",
        executable="cartographer_node",
        name="cartographer_node",
        output="screen",
        arguments=[
            "-configuration_directory", config_dir,
            "-configuration_basename", "rk3588_carto_localization.lua",
            "-load_state_filename", pbstream,
            "-load_frozen_state", "true",
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
        DeclareLaunchArgument(
            "pbstream",
            default_value="/mnt/sdcard/medicine_robot_data/maps/rk3588_carto.pbstream",
            description="Path to the saved Cartographer pbstream",
        ),
        DeclareLaunchArgument("start_lidar", default_value="true",
                              description="Whether to also start sllidar_node"),
        DeclareLaunchArgument("resolution", default_value="0.03"),
        DeclareLaunchArgument("publish_period_sec", default_value="1.0"),
        lidar_bringup,
        cartographer,
        occupancy_grid,
    ])
