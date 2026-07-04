python3 - <<'PY'
import json, os
path = '/home/elf/.local/share/medicine_robot/delivery_batch_state.json'
text = '\u8001\u5e74\u7cd6\u5c3f\u75c5\u60a3\u8005\uff0c\u63d0\u9192\u89c4\u5f8b\u8fdb\u9910\uff0c\u4e0d\u8981\u81ea\u884c\u52a0\u51cf\u836f\u91cf\u3002'
if os.path.exists(path):
    data=json.load(open(path,encoding='utf-8'))
    for stop in data.get('stops',[]) or []:
        for patient in stop.get('patients',[]) or []:
            if patient.get('bed_no') == 'B-01':
                patient['nursing_note'] = text
    with open(path+'.tmp','w',encoding='utf-8') as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
    os.replace(path+'.tmp',path)
    print('restored B-01 nursing_note')
PY
