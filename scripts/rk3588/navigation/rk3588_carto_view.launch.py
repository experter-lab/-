"""启动 RViz2 查看 Cartographer 建图/定位实时效果

Fixed Frame=map，显示 /map、/scan、/tf、/trajectory_node_list、/constraint_list。
俯视正交相机，适合 2D 建图查看。
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("medicine_robot_bringup")
    default_rviz = os.path.join(pkg_share, "config", "rk3588_carto_view.rviz")

    rviz_config = LaunchConfiguration("rviz_config")

    return LaunchDescription([
        DeclareLaunchArgument(
            "rviz_config",
            default_value=default_rviz,
            description="Path to .rviz config file",
        ),
        Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2_carto_view",
            output="screen",
            arguments=["-d", rviz_config],
        ),
    ])
