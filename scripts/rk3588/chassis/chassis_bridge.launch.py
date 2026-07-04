from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    params_file = LaunchConfiguration("params_file")

    return LaunchDescription([
        DeclareLaunchArgument(
            "params_file",
            default_value=PathJoinSubstitution([
                FindPackageShare("medicine_chassis_bridge"),
                "config",
                "chassis_bridge_mock.yaml",
            ]),
        ),
        Node(
            package="medicine_chassis_bridge",
            executable="chassis_bridge_node",
            name="chassis_bridge",
            output="screen",
            parameters=[params_file],
        ),
    ])
