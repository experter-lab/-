python3 - <<'PY'
import json, urllib.request, time
headers={'Content-Type':'application/json','X-Requested-With':'medicine-dashboard'}
def post(age):
    payload={'bed_no':'B-01','patient_id':'P-B01-001','age':str(age)}
    req=urllib.request.Request('http://127.0.0.1:8085/api/delivery_batch/update_patient', data=json.dumps(payload).encode(), headers=headers)
    return urllib.request.urlopen(req, timeout=8).read().decode('utf-8','ignore')
print('set77=', post(77)[:180])
time.sleep(1)
d=json.loads(urllib.request.urlopen('http://127.0.0.1:8081/patient/api/delivery?bed=B-01', timeout=5).read().decode('utf-8'))
print('age after set77=', (d.get('data') or {}).get('age'))
print('set76=', post(76)[:180])
time.sleep(1)
d=json.loads(urllib.request.urlopen('http://127.0.0.1:8081/patient/api/delivery?bed=B-01', timeout=5).read().decode('utf-8'))
print('age after restore=', (d.get('data') or {}).get('age'), 'note=', (d.get('data') or {}).get('nursing_note'))
PY
