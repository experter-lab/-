#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash
pkill -f carto_relocalize_bridge.py 2>/dev/null
sleep 1
nohup python3 /mnt/sdcard/medicine_robot_data/scripts/carto_relocalize_bridge.py > /tmp/carto_reloc.log 2>&1 &
echo "started PID=$!"
sleep 3
echo '=== log ==='
cat /tmp/carto_reloc.log
