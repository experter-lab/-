#!/usr/bin/env python3
from pathlib import Path
p = Path('/mnt/sdcard/medicine_robot_ws/src/medicine_robot_bringup/launch/rk3588_lidar_bringup.launch.py')
t = p.read_text(encoding='utf-8')

t = t.replace(
    '    laser_yaw = LaunchConfiguration("laser_yaw")',
    '    laser_yaw = LaunchConfiguration("laser_yaw")\n    range_max_filter = LaunchConfiguration("range_max_filter")'
)
t = t.replace(
    '        DeclareLaunchArgument("laser_yaw", default_value="0.0"),',
    '        DeclareLaunchArgument("laser_yaw", default_value="0.0"),\n        DeclareLaunchArgument("range_max_filter", default_value="10.0"),'
)
t = t.replace(
    '                "scan_frequency": ParameterValue(scan_frequency, value_type=float),',
    '                "scan_frequency": ParameterValue(scan_frequency, value_type=float),\n                "range_max_filter": ParameterValue(range_max_filter, value_type=float),'
)

p.write_text(t, encoding='utf-8')
print('OK')
