
import urllib.request, re
html=urllib.request.urlopen('http://127.0.0.1:8081/patient/', timeout=5).read().decode('utf-8','replace')
print('8081 html length', len(html), 'patient_assets', '/patient/assets/' in html)
paths=re.findall(r"/patient/assets/[^\"']+", html)
for path in paths:
    url='http://127.0.0.1:8081'+path
    r=urllib.request.urlopen(url, timeout=5)
    print('asset', path, r.status, r.getheader('Content-Type'))
req=urllib.request.Request('http://127.0.0.1:8081/patient/api/voice/announce', data=b'{}', headers={'Content-Type':'application/json'}, method='POST')
try:
    r=urllib.request.urlopen(req, timeout=5)
    print('voice announce', r.status, r.read().decode('utf-8','replace'))
except Exception as e:
    body=getattr(e, 'read', lambda: b'')().decode('utf-8','replace')
    print('voice announce error', getattr(e, 'code', '?'), body)
page=urllib.request.urlopen('http://127.0.0.1:8085/', timeout=5).read().decode('utf-8','replace')
for key in ['????','health_8085','health_check_badge','????','?????']:
    print('8085 contains', key, key in page)
