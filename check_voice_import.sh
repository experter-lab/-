#!/usr/bin/env bash
set -e
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash || true
python3 - <<'PY'
import medicine_voice_interaction.ai_voice_chat_bridge_node as m
from pathlib import Path
p=Path(m.__file__)
s=p.read_text(encoding='utf-8')
print('import_file=', p)
print('qmarks3=', s.count('???'))
print('xiao_prompt=', s.count('Xiao Yao Zhu'))
print('guard_method=', s.count('capability_boundary_guard'))
PY
