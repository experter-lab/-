#!/usr/bin/env bash
set -e
python3 -m py_compile /mnt/sdcard/medicine_robot_ws/src/medicine_voice_interaction/medicine_voice_interaction/ai_voice_chat_bridge_node.py
python3 - <<'PY'
from pathlib import Path
p=Path('/mnt/sdcard/medicine_robot_ws/src/medicine_voice_interaction/medicine_voice_interaction/ai_voice_chat_bridge_node.py')
s=p.read_text(encoding='utf-8')
items = {
  'qmarks3': s.count('???'),
  'xiao_prompt': s.count('Xiao Yao Zhu'),
  'guard_method': s.count('capability_boundary_guard'),
  'bad_raw_prompt': s.count('????'),
  'bed_voice_assistant': s.count('??????'),
  'robot_cannot_do': s.count('??????'),
}
for k,v in items.items():
    print(f'{k}={v}')
PY
