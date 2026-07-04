python3 - <<'PY'
import json, urllib.request, time
headers={'Content-Type':'application/json','X-Requested-With':'medicine-dashboard'}
payload = {
  'bed_no': 'B-01',
  'patient_id': 'P-B01-001',
  'nursing_note': '??????????????????????????8085???????'
}
req = urllib.request.Request('http://127.0.0.1:8085/api/delivery_batch/update_patient', data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), headers=headers)
try:
    print('update=', urllib.request.urlopen(req, timeout=8).read().decode('utf-8')[:500])
except Exception as e:
    print('update_err=', repr(e))
    raise
time.sleep(1)
d=json.loads(urllib.request.urlopen('http://127.0.0.1:8081/patient/api/delivery?bed=B-01', timeout=5).read().decode('utf-8'))
print(json.dumps({k:(d.get('data') or {}).get(k) for k in ['patient_name','bed','diagnosis','allergies','nursing_note']}, ensure_ascii=False))
PY
