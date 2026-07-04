python3 - <<'PY'
import json, os
path = '/home/elf/.local/share/medicine_robot/delivery_batch_state.json'
profiles = {
    'A-01': {
        'diagnosis': '\u9ad8\u8840\u538b\uff0c\u672c\u6b21\u5408\u5e76\u547c\u5438\u9053\u611f\u67d3\u7528\u836f',
        'allergies': '\u65e0\u660e\u786e\u836f\u7269\u8fc7\u654f\u53f2',
        'contraindications': '\u670d\u7528\u5934\u5b62\u671f\u95f4\u7981\u9152\uff1b\u82e5\u51fa\u73b0\u76ae\u75b9\u3001\u547c\u5438\u56f0\u96be\u7acb\u5373\u547c\u53eb\u62a4\u58eb',
        'nursing_note': '\u8001\u5e74\u9ad8\u8840\u538b\u60a3\u8005\uff0c\u5efa\u8bae\u8d77\u8eab\u6162\u4e00\u70b9\uff0c\u7559\u610f\u5934\u6655\u548c\u8840\u538b\u53d8\u5316\u3002',
    },
    'B-01': {
        'diagnosis': '2\u578b\u7cd6\u5c3f\u75c5\uff0c\u9ad8\u8102\u8840\u75c7',
        'allergies': '\u78fa\u80fa\u7c7b\u836f\u7269\u8fc7\u654f\u53f2',
        'contraindications': '\u4e8c\u7532\u53cc\u80cd\u5efa\u8bae\u968f\u9910\u6216\u9910\u540e\u670d\uff1b\u82e5\u660e\u663e\u4e4f\u529b\u3001\u6076\u5fc3\u6216\u4f4e\u8840\u7cd6\u8868\u73b0\u8981\u8054\u7cfb\u533b\u62a4',
        'nursing_note': '\u8001\u5e74\u7cd6\u5c3f\u75c5\u60a3\u8005\uff0c\u63d0\u9192\u89c4\u5f8b\u8fdb\u9910\uff0c\u4e0d\u8981\u81ea\u884c\u52a0\u51cf\u836f\u91cf\u3002',
    },
    'C-01': {
        'diagnosis': '\u80c3\u98df\u7ba1\u53cd\u6d41\uff0c\u8179\u6cfb\u5f85\u89c2\u5bdf',
        'allergies': '\u9752\u9709\u7d20\u8fc7\u654f\u53f2',
        'contraindications': '\u8499\u8131\u77f3\u6563\u4e0e\u5176\u4ed6\u836f\u7269\u5efa\u8bae\u95f4\u9694\u670d\u7528\uff1b\u8179\u6cfb\u52a0\u91cd\u6216\u4fbf\u8840\u8981\u7acb\u5373\u8054\u7cfb\u533b\u62a4',
        'nursing_note': '\u6ce8\u610f\u8865\u6c34\uff0c\u89c2\u5bdf\u8179\u75db\u3001\u53d1\u70ed\u548c\u5927\u4fbf\u6027\u72b6\u53d8\u5316\u3002',
    },
}
if not os.path.exists(path):
    print('missing', path)
    raise SystemExit(0)
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)
changed = 0
for stop in data.get('stops', []) or []:
    for patient in stop.get('patients', []) or []:
        bed = str(patient.get('bed_no') or '').strip()
        if bed not in profiles:
            continue
        for k, v in profiles[bed].items():
            if patient.get(k) != v:
                patient[k] = v
                changed += 1
with open(path + '.tmp', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
os.replace(path + '.tmp', path)
print('patched health context fields=', changed)
PY
