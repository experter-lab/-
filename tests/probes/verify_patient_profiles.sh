python3 - <<'PY'
import json, urllib.request, time
for bed in ['A-01','B-01','C-01']:
    url='http://127.0.0.1:8081/patient/api/delivery?bed=' + bed
    for _ in range(8):
        try:
            data=json.loads(urllib.request.urlopen(url, timeout=5).read().decode('utf-8'))
            d=data.get('data') or {}
            print(bed, d.get('patient_name'), d.get('ward'), 'age=', d.get('age'), 'gender=', d.get('gender'), 'height=', d.get('height_cm'), 'weight=', d.get('weight_kg'))
            break
        except Exception as e:
            err = e
            time.sleep(1)
    else:
        print(bed, 'ERR', repr(err))
PY
