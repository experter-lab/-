#!/usr/bin/env bash
set -e
echo '--- start script refs ---'
grep -n -E 'ai_voice_chat_bridge|medicine_voice_interaction|python3|ros2 run' /mnt/sdcard/rk3588_start_m2_voice.sh | head -100 || true
echo '--- source files ---'
find /mnt/sdcard/medicine_robot_ws -path '*ai_voice_chat_bridge_node.py' -printf '%p %s %TY-%Tm-%Td %TH:%TM\n' 2>/dev/null | head -30
