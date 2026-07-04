#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash || true
python3 - <<'PY'
import medicine_voice_interaction.ai_voice_chat_bridge_node as m
from pathlib import Path
p=Path(m.__file__)
s=p.read_text(encoding='utf-8')
print('import_file', p)
for token in ['high_risk_missed_dose_guard','??????','text = self.high_risk_missed_dose_guard(text)']:
    print(token, s.count(token))
start=s.find('def clean_answer')
print(s[start:start+700])
PY
