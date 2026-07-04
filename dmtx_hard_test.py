#!/usr/bin/env python3
"""死磕 DataMatrix: 裁区域, 大倍率 x 多二值化 x 旋转 x pylibdmtx长超时"""
import sys, time
import cv2, numpy as np
import zxingcpp
from pylibdmtx.pylibdmtx import decode as dmtx_decode

img = cv2.imread("/tmp/now_clean.jpg")
H,W = img.shape[:2]
print("image", img.shape)

crops = {
    "dm_tight": img[60:175, 455:585],
    "dm_wide":  img[40:200, 420:620],
}

def variants(patch):
    g = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
    out = []
    clahe = cv2.createCLAHE(3.0,(8,8)).apply(g)
    out.append(("clahe", clahe))
    blur = cv2.GaussianBlur(clahe,(0,0),2.0)
    out.append(("clahe_unsharp", cv2.addWeighted(clahe,1.8,blur,-0.8,0)))
    out.append(("otsu", cv2.threshold(clahe,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]))
    out.append(("adapt", cv2.adaptiveThreshold(clahe,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,25,4)))
    k = cv2.getStructuringElement(cv2.MORPH_RECT,(2,2))
    out.append(("otsu_close", cv2.morphologyEx(out[2][1],cv2.MORPH_CLOSE,k)))
    return out

def try_decode(im, tag):
    hits=[]
    try:
        for c in zxingcpp.read_barcodes(im):
            t=c.text if isinstance(c.text,str) else c.text.decode("utf8","replace")
            hits.append((f"zxing/{str(c.format).split('.')[-1]}", t))
    except Exception: pass
    try:
        g = im if len(im.shape)==2 else cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
        for r in dmtx_decode(g, timeout=4000, max_count=2):
            hits.append(("dmtx", r.data.decode("utf8","replace")))
    except Exception: pass
    for h in hits:
        print(f"    [+] {tag}  {h}")
    return hits

found=[]
t0=time.monotonic()
for cname, crop in crops.items():
    if crop.size==0: continue
    print(f"\n=== crop {cname} {crop.shape} ===")
    cv2.imwrite(f"/tmp/{cname}.png", crop)
    for vname, v in variants(crop):
        for scale in [3.0, 5.0, 8.0]:
            vx = cv2.resize(v, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            for rot in [0, 90, 180, 270]:
                if rot:
                    vr = cv2.rotate(vx, {90:cv2.ROTATE_90_CLOCKWISE,180:cv2.ROTATE_180,270:cv2.ROTATE_90_COUNTERCLOCKWISE}[rot])
                else:
                    vr = vx
                h = try_decode(vr, f"{cname}/{vname}/x{scale}/r{rot}")
                found += h
print(f"\n=== 死磕结果: {len(found)} 命中, 耗时 {time.monotonic()-t0:.1f}s ===")
