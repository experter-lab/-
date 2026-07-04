#!/usr/bin/env python3
from pathlib import Path
import re

p = Path("/mnt/sdcard/medicine_robot_ws/src/medicine_robot_bringup/launch/rk3588_lidar_bringup.launch.py")
t = p.read_text(encoding="utf-8")

if 'LaunchConfiguration("range_min_filter")' not in t:
    t = t.replace(
        '    scan_frequency = LaunchConfiguration("scan_frequency")',
        '    scan_frequency = LaunchConfiguration("scan_frequency")\n    range_min_filter = LaunchConfiguration("range_min_filter")',
    )

if 'DeclareLaunchArgument("range_min_filter"' not in t:
    t = t.replace(
        '        DeclareLaunchArgument("scan_frequency", default_value="10.0"),',
        '        DeclareLaunchArgument("scan_frequency", default_value="10.0"),\n        DeclareLaunchArgument("range_min_filter", default_value="0.35"),',
    )
else:
    t = re.sub(
        r'DeclareLaunchArgument\("range_min_filter", default_value="[^"]+"\)',
        'DeclareLaunchArgument("range_min_filter", default_value="0.35")',
        t,
        count=1,
    )

if '"range_min_filter": ParameterValue(range_min_filter, value_type=float)' not in t:
    t = t.replace(
        '                "scan_frequency": ParameterValue(scan_frequency, value_type=float),',
        '                "scan_frequency": ParameterValue(scan_frequency, value_type=float),\n                "range_min_filter": ParameterValue(range_min_filter, value_type=float),',
    )

p.write_text(t, encoding="utf-8")
print("range_min_filter launch patch applied")
