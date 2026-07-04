#!/usr/bin/env python3
import cv2, zxingcpp, urllib.request, numpy as np, sys
data = urllib.request.urlopen("http://127.0.0.1:8090/snapshot.jpg").read()
open("/tmp/now.jpg","wb").write(data)
img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
print("shape", img.shape)
# 裁掉顶部 overlay (134px)
clean = img[134:, :, :]
cv2.imwrite("/tmp/now_clean.jpg", clean)
print("=== zxingcpp 全帧多倍率 ===")
for scale in [1.0, 1.5, 2.0, 2.5, 3.0]:
    x = cv2.resize(clean, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC) if scale!=1.0 else clean
    codes = zxingcpp.read_barcodes(x)
    print(f"  scale={scale} shape={x.shape[:2]} found {len(codes)}")
    for c in codes:
        t = c.text if isinstance(c.text,str) else c.text.decode("utf8","replace")
        print(f"    fmt={c.format} text={t!r}")
