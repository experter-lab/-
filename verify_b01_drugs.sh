python3 - <<'PY'
import json, urllib.request
d=json.loads(urllib.request.urlopen('http://127.0.0.1:8081/patient/api/delivery?bed=B-01', timeout=5).read().decode('utf-8'))
for item in (d.get('data') or {}).get('drugs') or []:
    print(json.dumps({'drug_id':item.get('drug_id'), 'drug_name':item.get('drug_name'), 'dose':item.get('dose'), 'usage_text':item.get('usage_text'), 'frequency':item.get('frequency')}, ensure_ascii=False))
PY
