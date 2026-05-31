import os
import time
import cv2
import numpy as np

try:
    import zxingcpp
except Exception:
    zxingcpp = None

try:
    from pylibdmtx.pylibdmtx import decode as dmtx_decode
except Exception:
    dmtx_decode = None

OUT = "/tmp/rk3588_decode"
os.makedirs(OUT, exist_ok=True)

def save(name, image):
    path = os.path.join(OUT, name)
    cv2.imwrite(path, image)
    return path

def try_decode(name, image):
    results = []
    if zxingcpp is not None:
        try:
            barcodes = zxingcpp.read_barcodes(image)
        except Exception as exc:
            barcodes = []
            print("ZXING_ERR", name, repr(exc))
        for barcode in barcodes:
            text = getattr(barcode, "text", "")
            fmt = str(getattr(barcode, "format", ""))
            if text:
                results.append(("zxingcpp", fmt, text))
    if dmtx_decode is not None:
        try:
            dmtx = dmtx_decode(image, timeout=700)
        except TypeError:
            dmtx = dmtx_decode(image)
        except Exception as exc:
            dmtx = []
            print("DMTX_ERR", name, repr(exc))
        for item in dmtx:
            text = item.data.decode("utf-8", errors="replace") if isinstance(item.data, bytes) else str(item.data)
            if text:
                results.append(("pylibdmtx", "DataMatrix", text))
    if results:
        print("DECODED", name, results)
    else:
        print("NO_DECODE", name)
    return results

def add_variants(name, image, variants):
    variants.append((name, image))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    variants.append((name + "_gray", gray))
    for scale in (2, 3, 4, 6):
        up = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        variants.append((f"{name}_gray_x{scale}", up))
        _, otsu = cv2.threshold(up, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variants.append((f"{name}_otsu_x{scale}", otsu))
        adaptive = cv2.adaptiveThreshold(up, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 5)
        variants.append((f"{name}_adaptive_x{scale}", adaptive))

cap = cv2.VideoCapture("/dev/video21", cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1024)
cap.set(cv2.CAP_PROP_FPS, 30)
print("opened", cap.isOpened(), "width", cap.get(cv2.CAP_PROP_FRAME_WIDTH), "height", cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
frame = None
for i in range(20):
    ok, candidate = cap.read()
    if ok:
        frame = candidate
        print("read", i, candidate.shape)
    time.sleep(0.03)
cap.release()
if frame is None:
    raise SystemExit("no frame captured")

save("frame.jpg", frame)
variants = []
add_variants("full", frame, variants)

qr = cv2.QRCodeDetector()
try:
    text, points, _ = qr.detectAndDecode(frame)
except Exception as exc:
    print("opencv detect err", repr(exc))
    text, points = "", None
print("opencv_qr_text", repr(text), "points", None if points is None else points.reshape(-1, 2).astype(int).tolist())
if points is not None:
    pts = points.reshape(-1, 2).astype(np.float32)
    x, y, w, h = cv2.boundingRect(pts.astype(np.int32))
    pad = max(w, h, 30) // 2
    x0 = max(x - pad, 0)
    y0 = max(y - pad, 0)
    x1 = min(x + w + pad, frame.shape[1])
    y1 = min(y + h + pad, frame.shape[0])
    crop = frame[y0:y1, x0:x1]
    save("qr_bbox_crop.jpg", crop)
    add_variants("qr_bbox_crop", crop, variants)

for index, (name, image) in enumerate(variants):
    if index < 80:
        save(f"variant_{index:02d}_{name}.jpg", image)
    results = try_decode(name, image)
    if results:
        print("FIRST_SUCCESS", name, results)
        break
else:
    print("NO_SUCCESS")
print("output_dir", OUT)
