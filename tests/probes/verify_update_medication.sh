python3 - <<'PY'
import json, urllib.request, time
headers={'Content-Type':'application/json','X-Requested-With':'medicine-dashboard'}
url='http://127.0.0.1:8085/api/delivery_batch/update_medication'
def post(dose):
    payload={'product_code':'MED-ATORVASTATIN-20MG','dose':dose}
    req=urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    return urllib.request.urlopen(req, timeout=8).read().decode('utf-8','ignore')
def getdose():
    d=json.loads(urllib.request.urlopen('http://127.0.0.1:8081/patient/api/delivery?bed=B-01', timeout=5).read().decode('utf-8'))
    for item in (d.get('data') or {}).get('drugs') or []:
        if '?????' in item.get('drug_name',''):
            return item.get('dose'), item.get('drug_name')
    return None
print('set21=', post('21 mg')[:220])
time.sleep(1)
print('dose after set21=', getdose())
print('set20=', post('20 mg')[:220])
time.sleep(1)
print('dose after restore=', getdose())
PY
