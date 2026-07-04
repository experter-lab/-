python3 - <<'PY'
import json, os
path = '/home/elf/.local/share/medicine_robot/delivery_batch_state.json'
profiles = {
    'A-01': {'age': 68, 'gender': '\u7537', 'height_cm': 170, 'weight_kg': 72},
    'B-01': {'age': 76, 'gender': '\u5973', 'height_cm': 158, 'weight_kg': 61},
    'C-01': {'age': 52, 'gender': '\u5973', 'height_cm': 162, 'weight_kg': 58},
}
if not os.path.exists(path):
    raise SystemExit('missing ' + path)
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)
changed = 0
for stop in data.get('stops', []) or []:
    for patient in stop.get('patients', []) or []:
        bed = str(patient.get('bed_no') or '').strip()
        if bed in profiles:
            for k, v in profiles[bed].items():
                if patient.get(k) != v:
                    patient[k] = v
                    changed += 1
with open(path + '.tmp', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
os.replace(path + '.tmp', path)
print('patched', path, 'changed_fields=', changed)
print([(p.get('bed_no'), p.get('patient_name'), p.get('age'), p.get('gender'), p.get('height_cm'), p.get('weight_kg')) for s in data.get('stops',[]) for p in s.get('patients',[]) if p.get('bed_no') in profiles])
PY
