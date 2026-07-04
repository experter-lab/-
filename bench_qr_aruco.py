#!/usr/bin/env python3
"""bench QRCodeDetectorAruco vs QRCodeDetector detect-only on current camera"""
import cv2, time, sys, urllib.request

# 试从板子 preview 拿当前画面
path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/cur.jpg"
frame = cv2.imread(path)
print(f"loaded {path}: {frame.shape}")

print(f"\nframe: {frame.shape}")

# Aruco-based detector
aruco_det = cv2.QRCodeDetectorAruco()
# Standard detector
std_det = cv2.QRCodeDetector()

def bench(name, fn, n=30):
    for _ in range(3): fn()
    t0 = time.monotonic()
    for _ in range(n): r = fn()
    dt = (time.monotonic() - t0) / n * 1000
    return dt, r

print("\n=== Detect only (no decode) ===")
t, (ok, points) = bench("Aruco", lambda: aruco_det.detect(frame))
print(f"  Aruco: {t:.2f}ms  detected={ok}  points_shape={None if points is None else points.shape}")

t, (ok, points) = bench("Standard", lambda: std_det.detect(frame))
print(f"  Standard: {t:.2f}ms  detected={ok}  points_shape={None if points is None else points.shape}")

print("\n=== Multi (detect multiple QRs) ===")
try:
    t, (ok, points) = bench("Aruco multi", lambda: aruco_det.detectMulti(frame))
    print(f"  Aruco detectMulti: {t:.2f}ms  ok={ok}  points={None if points is None else points.shape}")
except Exception as e:
    print(f"  Aruco detectMulti err: {e}")

try:
    t, (ok, points) = bench("Standard multi", lambda: std_det.detectMulti(frame))
    print(f"  Standard detectMulti: {t:.2f}ms  ok={ok}  points={None if points is None else points.shape}")
except Exception as e:
    print(f"  Standard detectMulti err: {e}")
