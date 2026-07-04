#!/usr/bin/env python3
"""滑窗分块解码: 专攻小 DataMatrix/QR。把帧切成重叠 tile, 每块增强+上采样后多解码器扫。"""
import sys, os, time, subprocess, tempfile
import cv2, numpy as np
import zxingcpp
try:
    from pylibdmtx.pylibdmtx import decode as dmtx_decode
except Exception:
    dmtx_decode = None

def clahe_unsharp(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape)==3 else img
    g = cv2.createCLAHE(2.0,(8,8)).apply(g)
    blur = cv2.GaussianBlur(g,(0,0),2.0)
    return cv2.addWeighted(g,1.6,blur,-0.6,0)

def zxing_dec(im):
    try:
        return [(str(c.format).split(".")[-1], c.text if isinstance(c.text,str) else c.text.decode("utf8","replace")) for c in zxingcpp.read_barcodes(im)]
    except Exception: return []

def dmtx_dec(im):
    if dmtx_decode is None: return []
    try:
        g = im if len(im.shape)==2 else cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        return [("dmtx", r.data.decode("utf8","replace")) for r in dmtx_decode(g, timeout=1500, max_count=4)]
    except Exception: return []

def zbar_dec(im):
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        cv2.imwrite(f.name, im); p=f.name
    try:
        r = subprocess.run(["zbarimg","-q","--raw",p], capture_output=True, text=True, timeout=4)
        return [("zbar", l) for l in r.stdout.splitlines() if l.strip()]
    finally: os.unlink(p)

def main():
    img = cv2.imread(sys.argv[1] if len(sys.argv)>1 else "/tmp/now_clean.jpg")
    print("image", img.shape)
    H,W = img.shape[:2]
    found = {}
    t_start = time.monotonic()

    # tile 网格: 4列 x 3行, 50% 重叠
    cols, rows = 4, 3
    tw, th = W//cols, H//rows
    ox, oy = tw//2, th//2
    tiles = []
    for gy in range(rows*2-1):
        for gx in range(cols*2-1):
            x0, y0 = gx*ox, gy*oy
            x1, y1 = min(x0+tw, W), min(y0+th, H)
            if x1-x0 < 40 or y1-y0 < 40: continue
            tiles.append((x0,y0,x1,y1))
    print(f"tiles: {len(tiles)}")

    for (x0,y0,x1,y1) in tiles:
        patch = img[y0:y1, x0:x1]
        h,w = patch.shape[:2]
        ratio = 360.0/max(h,w)
        e = clahe_unsharp(patch)
        ex = cv2.resize(e, None, fx=ratio, fy=ratio, interpolation=cv2.INTER_CUBIC) if ratio>1.0 else e
        for dname, dfn in [("zxing",zxing_dec),("dmtx",dmtx_dec),("zbar",zbar_dec)]:
            for fmt, txt in dfn(ex):
                key=(fmt,txt)
                if key not in found:
                    found[key]=(x0,y0,x1,y1,dname)
                    print(f"  [+] tile({x0},{y0})-({x1},{y1}) {dname:5s} fmt={fmt} text={txt!r}")
    dt = time.monotonic()-t_start
    print(f"\n=== 共解出 {len(found)} 个唯一码, 耗时 {dt:.1f}s ===")
    for (fmt,txt),(x0,y0,x1,y1,dn) in found.items():
        print(f"  {fmt:18s} via {dn:5s}: {txt!r}")

if __name__=="__main__":
    main()
