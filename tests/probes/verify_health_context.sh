python3 - <<'PY'
import json, urllib.request, time
for bed in ['A-01','B-01','C-01']:
    url='http://127.0.0.1:8081/patient/api/delivery?bed=' + bed
    data=json.loads(urllib.request.urlopen(url, timeout=5).read().decode('utf-8'))
    d=data.get('data') or {}
    print(bed, d.get('patient_name'), 'diagnosis=', d.get('diagnosis'), 'allergies=', d.get('allergies'), 'contra=', bool(d.get('contraindications')), 'note=', bool(d.get('nursing_note')))
PY
