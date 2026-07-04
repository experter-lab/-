#!/usr/bin/env python3
"""
离线增强 pipeline 测试: 拿一张 vision preview, 跑 4 种增强 x 3 种解码器组合
目标: 至少解出 1 个码 (DataMatrix 或一维条码)
"""
import sys, os, time, json, subprocess, tempfile
import cv2
import numpy as np

import zxingcpp
try:
    from pylibdmtx.pylibdmtx import decode as dmtx_decode
except Exception as e:
    print("pylibdmtx import fail:", e); dmtx_decode=None

# zbarimg 命令行
def zbar_decode(image):
    if image is None: return []
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        cv2.imwrite(f.name, image); path=f.name
    try:
        r = subprocess.run(["zbarimg","-q","--raw",path],
                          capture_output=True, text=True, timeout=4)
        codes = [l for l in r.stdout.splitlines() if l.strip()]
    except Exception as e:
        codes = []
    finally:
        os.unlink(path)
    return codes

def zxing_decode(image):
    try:
        cs = zxingcpp.read_barcodes(image)
        return [(str(c.format).split(".")[-1], c.text if isinstance(c.text,str) else c.text.decode("utf8","replace")) for c in cs]
    except Exception as e:
        return []

def dmtx_dec(image):
    if dmtx_decode is None: return []
    try:
        gray = image if len(image.shape)==2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        res = dmtx_decode(gray, timeout=2000)
        return [(b"dmtx", r.data.decode("utf8","replace")) for r in res]
    except Exception as e:
        return []

# ---- 图像增强 ----
def enh_raw(img):
    return img.copy()

def enh_clahe(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape)==3 else img
    return cv2.createCLAHE(2.0, (8,8)).apply(gray)

def enh_clahe_unsharp(img):
    gray = enh_clahe(img)
    blur = cv2.GaussianBlur(gray, (0,0), 2.0)
    return cv2.addWeighted(gray, 1.6, blur, -0.6, 0)

def enh_otsu(img):
    g = enh_clahe(img)
    return cv2.threshold(g, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]

def enh_adaptive(img):
    g = enh_clahe(img)
    return cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, 31, 5)

# ---- ROI 检测 (找疑似码区) ----
def find_roi_candidates(img, min_size=50, max_size=600):
    """找可能含 DataMatrix/QR/Barcode 的矩形 ROI"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape)==3 else img
    # 用 Sobel/morph 找高纹理密集区
    sx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    sy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.convertScaleAbs(cv2.magnitude(sx, sy))
    _, thr = cv2.threshold(mag, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (15,15))
    closed = cv2.morphologyEx(thr, cv2.MORPH_CLOSE, k)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rois = []
    h, w = gray.shape
    for c in contours:
        x, y, cw, ch = cv2.boundingRect(c)
        if cw < min_size or ch < min_size: continue
        if cw > max_size and ch > max_size: continue
        if cw/ch > 6 or ch/cw > 6: continue   # 太细长不是码
        # 加 padding 后裁出来
        pad = 10
        x0,y0 = max(0,x-pad), max(0,y-pad)
        x1,y1 = min(w,x+cw+pad), min(h,y+ch+pad)
        rois.append((x0,y0,x1,y1, img[y0:y1, x0:x1]))
    return rois

# ---- 主流程 ----
def main():
    if len(sys.argv) >= 2:
        img = cv2.imread(sys.argv[1])
    else:
        img = cv2.imread("/tmp/now_clean.jpg")
    if img is None:
        print("ERROR: no image"); return
    print(f"image: {img.shape}")

    enhancers = [("raw", enh_raw), ("clahe", enh_clahe),
                 ("clahe+unsharp", enh_clahe_unsharp),
                 ("otsu", enh_otsu), ("adapt_thresh", enh_adaptive)]
    decoders = [("zxing", zxing_decode), ("dmtx", dmtx_dec), ("zbar", zbar_decode)]

    print("\n=== 全帧扫描 ===")
    for ename, efn in enhancers:
        e = efn(img)
        for scale in [1.0, 2.0, 3.0]:
            x = cv2.resize(e, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC) if scale!=1.0 else e
            for dname, dfn in decoders:
                t0 = time.monotonic()
                r = dfn(x)
                dt = (time.monotonic()-t0)*1000
                if r:
                    print(f"  [+] {ename:14s} x{scale:.1f} {dname:5s}  {dt:5.0f}ms  {r}")

    print("\n=== ROI 检测 + 各 ROI 上采样扫描 ===")
    rois = find_roi_candidates(img)
    print(f"  发现 {len(rois)} 个候选 ROI")
    rois_keep = []
    for i, (x0,y0,x1,y1,patch) in enumerate(rois[:20]):
        h, w = patch.shape[:2]
        # 抽样: 太小的不重要, 主要看中等大小
        if max(h,w) < 60: continue
        rois_keep.append((i,x0,y0,x1,y1,patch))
    print(f"  保留 {len(rois_keep)} 个 ROI 测试")

    found = False
    for i,x0,y0,x1,y1,patch in rois_keep:
        h,w = patch.shape[:2]
        for ename, efn in [("raw", enh_raw), ("clahe+unsharp", enh_clahe_unsharp), ("adapt_thresh", enh_adaptive)]:
            e = efn(patch)
            # ROI 一律放大到长边 400
            ratio = 400.0 / max(h, w)
            if ratio > 1.0:
                ex = cv2.resize(e, None, fx=ratio, fy=ratio, interpolation=cv2.INTER_CUBIC)
            else:
                ex = e
            for dname, dfn in decoders:
                r = dfn(ex)
                if r:
                    print(f"  [+] ROI#{i} ({x0},{y0})-({x1},{y1}) {w}x{h}  {ename:14s} {dname:5s}  {r}")
                    found = True

    if not found:
        print("  无 ROI 命中")
        # 保存所有 ROI 候选给视觉确认
        out = img.copy()
        for i,x0,y0,x1,y1,_ in rois_keep:
            cv2.rectangle(out, (x0,y0),(x1,y1), (0,255,0), 2)
            cv2.putText(out, str(i), (x0,y0-5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
        cv2.imwrite("/tmp/rois.jpg", out)
        print(f"  /tmp/rois.jpg 标记了 {len(rois_keep)} 个 ROI 可视化")

if __name__ == "__main__":
    main()
