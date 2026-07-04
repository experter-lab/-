#!/usr/bin/env python3
"""微基准: 对比 CPU vs OpenCL(Mali GPU) 在 vision pipeline 关键算子上的速度"""
import time, cv2, numpy as np

print(f"OpenCV {cv2.__version__}")
print(f"OpenCL available: {cv2.ocl.haveOpenCL()}")

# 准备 1280x720 测试帧
frame = (np.random.rand(720, 1280, 3) * 255).astype(np.uint8)

def bench(name, fn, n=20):
    # warmup
    for _ in range(3): fn()
    t0 = time.monotonic()
    for _ in range(n): r = fn()
    dt = (time.monotonic() - t0) / n * 1000
    return dt

print("\n=== 1280x720 BGR -> GRAY ===")
def cpu_gray(): return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
cv2.ocl.setUseOpenCL(False)
t_cpu = bench("CPU", cpu_gray)
cv2.ocl.setUseOpenCL(True)
def gpu_gray():
    u = cv2.UMat(frame)
    g = cv2.cvtColor(u, cv2.COLOR_BGR2GRAY)
    return g.get()
t_gpu = bench("GPU", gpu_gray)
print(f"  CPU: {t_cpu:.2f}ms  GPU(UMat): {t_gpu:.2f}ms  speedup: {t_cpu/t_gpu:.2f}x")

print("\n=== resize 1280x720 -> 2560x1440 (2x INTER_CUBIC) ===")
def cpu_resize(): return cv2.resize(frame, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
cv2.ocl.setUseOpenCL(False)
t_cpu = bench("CPU", cpu_resize)
cv2.ocl.setUseOpenCL(True)
def gpu_resize():
    u = cv2.UMat(frame)
    r = cv2.resize(u, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    return r.get()
t_gpu = bench("GPU", gpu_resize)
print(f"  CPU: {t_cpu:.2f}ms  GPU(UMat): {t_gpu:.2f}ms  speedup: {t_cpu/t_gpu:.2f}x")

print("\n=== CLAHE on 1280x720 gray ===")
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
clahe = cv2.createCLAHE(2.0, (8,8))
def cpu_clahe(): return clahe.apply(gray)
cv2.ocl.setUseOpenCL(False)
t_cpu = bench("CPU", cpu_clahe)
cv2.ocl.setUseOpenCL(True)
def gpu_clahe():
    u = cv2.UMat(gray)
    r = clahe.apply(u)
    return r.get()
t_gpu = bench("GPU", gpu_clahe)
print(f"  CPU: {t_cpu:.2f}ms  GPU(UMat): {t_gpu:.2f}ms  speedup: {t_cpu/t_gpu:.2f}x")

print("\n=== GaussianBlur sigma=2 on 1280x720 gray ===")
def cpu_blur(): return cv2.GaussianBlur(gray, (0,0), 2.0)
cv2.ocl.setUseOpenCL(False)
t_cpu = bench("CPU", cpu_blur)
cv2.ocl.setUseOpenCL(True)
def gpu_blur():
    u = cv2.UMat(gray)
    r = cv2.GaussianBlur(u, (0,0), 2.0)
    return r.get()
t_gpu = bench("GPU", gpu_blur)
print(f"  CPU: {t_cpu:.2f}ms  GPU(UMat): {t_gpu:.2f}ms  speedup: {t_cpu/t_gpu:.2f}x")

print("\n=== JPEG encode quality=35 1280x720 ===")
import cv2
params = [cv2.IMWRITE_JPEG_QUALITY, 35]
def cpu_jpeg(): return cv2.imencode('.jpg', frame, params)
cv2.ocl.setUseOpenCL(False)
t_cpu = bench("CPU", cpu_jpeg)
print(f"  CPU: {t_cpu:.2f}ms (GPU 路径 OpenCV 不支持 JPEG, 要用 MPP)")

print("\n=== 综合: build_qr_candidates 等价操作 (frame -> 10 candidates) ===")
def cpu_pipeline():
    g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    clahe_g = clahe.apply(g)
    blur = cv2.GaussianBlur(clahe_g, (0,0), 2.0)
    unsharp = cv2.addWeighted(clahe_g, 1.6, blur, -0.6, 0)
    for scale in [1.5, 2.0]:
        s = cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        sg = cv2.cvtColor(s, cv2.COLOR_BGR2GRAY)
        sc = clahe.apply(sg)
        sb = cv2.GaussianBlur(sc, (0,0), 2.0)
        cv2.addWeighted(sc, 1.6, sb, -0.6, 0)
cv2.ocl.setUseOpenCL(False)
t_cpu = bench("CPU", cpu_pipeline, n=10)

def gpu_pipeline():
    uf = cv2.UMat(frame)
    g = cv2.cvtColor(uf, cv2.COLOR_BGR2GRAY)
    clahe_g = clahe.apply(g)
    blur = cv2.GaussianBlur(clahe_g, (0,0), 2.0)
    unsharp = cv2.addWeighted(clahe_g, 1.6, blur, -0.6, 0)
    for scale in [1.5, 2.0]:
        s = cv2.resize(uf, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        sg = cv2.cvtColor(s, cv2.COLOR_BGR2GRAY)
        sc = clahe.apply(sg)
        sb = cv2.GaussianBlur(sc, (0,0), 2.0)
        cv2.addWeighted(sc, 1.6, sb, -0.6, 0)
        sg.get(); sc.get()  # 强制把 GPU 结果拉回 CPU, 模拟下游需要 numpy
cv2.ocl.setUseOpenCL(True)
t_gpu = bench("GPU", gpu_pipeline, n=10)
print(f"  CPU pipeline: {t_cpu:.2f}ms  GPU pipeline: {t_gpu:.2f}ms  speedup: {t_cpu/t_gpu:.2f}x")
