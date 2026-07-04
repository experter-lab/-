
import json, urllib.request
for url in ['http://127.0.0.1:8085/api/health_check','http://127.0.0.1:8085/']:
    try:
        data=urllib.request.urlopen(url, timeout=5).read().decode('utf-8','replace')
        print('URL', url, 'LEN', len(data))
        if url.endswith('/api/health_check'):
            obj=json.loads(data)
            print('status', obj.get('status'), 'summary', obj.get('summary'))
            for k,v in (obj.get('checks') or {}).items():
                print(k, v.get('status'), v.get('message'))
        else:
            print('contains health api call', '/api/health_check' in data)
            print('contains health_8085', 'health_8085' in data)
    except Exception as e:
        print('ERROR', url, repr(e))
