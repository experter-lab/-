import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    from rknnlite.api import RKNNLite
except Exception:
    RKNNLite = None

try:
    import zxingcpp
except Exception:
    zxingcpp = None

try:
    from pylibdmtx.pylibdmtx import decode as dmtx_decode
except Exception:
    dmtx_decode = None

try:
    import pytesseract
except Exception:
    pytesseract = None

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from medicine_interfaces.msg import DrugInfo
from medicine_vision_detector.yolo_rknn_detector_node import COCO_LABELS, YoloRknnDetector

try:
    from medicine_vision_detector.ppocr_onnx_runner import PPOcrOnnxRunner
except Exception:
    PPOcrOnnxRunner = None


def normalize_external_position(position, scale=1.0):
    if position is None:
        return []
    points = []
    for name in ("top_left", "top_right", "bottom_right", "bottom_left"):
        if not hasattr(position, name):
            continue
        point = getattr(position, name)
        if hasattr(point, "x") and hasattr(point, "y"):
            points.append((int(point.x / scale), int(point.y / scale)))
        elif isinstance(point, (tuple, list)) and len(point) >= 2:
            points.append((int(point[0] / scale), int(point[1] / scale)))
    return points


def decode_zxing_files(manifest_path):
    if cv2 is None or zxingcpp is None:
        print("[]")
        return 0
    try:
        with open(manifest_path, "r", encoding="utf-8") as manifest_file:
            items = json.load(manifest_file)
    except Exception:
        print("[]")
        return 1
    decoded = []
    for item in items:
        image = cv2.imread(str(item.get("path", "")), cv2.IMREAD_UNCHANGED)
        if image is None:
            continue
        scale = float(item.get("scale", 1.0) or 1.0)
        try:
            if hasattr(zxingcpp, "read_barcodes"):
                barcodes = zxingcpp.read_barcodes(image)
            else:
                barcode = zxingcpp.read_barcode(image)
                barcodes = [barcode] if barcode is not None else []
        except Exception:
            continue
        for barcode in barcodes:
            text = getattr(barcode, "text", "")
            if isinstance(text, bytes):
                text = text.decode("utf-8", errors="replace")
            if not text:
                continue
            format_name = str(getattr(barcode, "format", "barcode")).split(".")[-1].lower()
            decoded.append({
                "text": text,
                "points": normalize_external_position(getattr(barcode, "position", None), scale),
                "format": format_name,
                "backend": "zxingcpp",
                "method": str(item.get("method", "")),
            })
    print(json.dumps(decoded, ensure_ascii=False))
    return 0


class DrugInfoDetector(Node):
    def __init__(self):
        super().__init__("medicine_vision_detector")
        default_drug_catalog = json.dumps({
            "drug_001": {"drug_name": "降压药", "drug_type": "tablet", "loaded": True},
            "drug_002": {"drug_name": "消炎药", "drug_type": "capsule", "loaded": True},
            "drug_003": {"drug_name": "感冒药", "drug_type": "box", "loaded": True},
        }, ensure_ascii=False)
        self.declare_parameter("drug_id", "drug_001")
        self.declare_parameter("drug_name", "降压药")
        self.declare_parameter("drug_type", "tablet")
        self.declare_parameter("confidence", 0.98)
        self.declare_parameter("loaded", True)
        self.declare_parameter("source", "mock")
        self.declare_parameter("publish_period_sec", 1.0)
        self.declare_parameter("drug_info_topic", "/medicine/drug_info")
        self.declare_parameter("status_topic", "/medicine/drug_recognition_status")
        self.declare_parameter("control_topic", "/medicine/vision_control")
        self.declare_parameter("input_mode", "mock")
        self.declare_parameter("camera_device", "/dev/video0")
        self.declare_parameter("camera_width", 640)
        self.declare_parameter("camera_height", 480)
        self.declare_parameter("camera_fps", 30)
        self.declare_parameter("camera_fourcc", "MJPG")
        self.declare_parameter("camera_reconnect_period_sec", 2.0)
        self.declare_parameter("camera_read_period_sec", 0.05)
        self.declare_parameter("enable_preview_server", True)
        self.declare_parameter("preview_host", "0.0.0.0")
        self.declare_parameter("preview_port", 8090)
        self.declare_parameter("preview_quality", 80)
        self.declare_parameter("preview_draw_overlay", True)
        self.declare_parameter("preview_sharpen_enabled", True)
        self.declare_parameter("preview_sharpen_amount", 0.55)
        self.declare_parameter("preview_sharpen_sigma", 1.0)
        self.declare_parameter("preview_stream_period_sec", 0.005)
        self.declare_parameter("preview_encode_period_sec", 0.0)
        self.declare_parameter("preview_idle_timeout_sec", 1.0)
        self.declare_parameter("enable_qr_recognition", True)
        self.declare_parameter("enable_datamatrix_recognition", True)
        self.declare_parameter("enable_zxingcpp_recognition", True)
        self.declare_parameter("enable_pylibdmtx_recognition", False)
        self.declare_parameter("qr_recognition_period_sec", 0.1)
        self.declare_parameter("qr_fast_mode", True)
        self.declare_parameter("qr_scale_factor", 1.5)
        self.declare_parameter("qr_extra_scale_factors", "1.5,2.0")
        self.declare_parameter("external_decoder_period_sec", 0.35)
        self.declare_parameter("external_decoder_timeout_sec", 1.5)
        self.declare_parameter("enable_isolated_zxingcpp_recognition", True)
        self.declare_parameter("enable_opencv_curved_qr_recognition", False)
        self.declare_parameter("enable_qr_unsharp", True)
        self.declare_parameter("enable_zbar_recognition", True)
        self.declare_parameter("zbar_timeout_sec", 1.5)
        self.declare_parameter("enable_barcode_enhancement", True)
        self.declare_parameter("barcode_scale_x", 2.0)
        self.declare_parameter("barcode_scale_y", 1.2)
        self.declare_parameter("barcode_roi_scan_only", True)
        self.declare_parameter("barcode_roi_enabled", True)
        self.declare_parameter("barcode_roi_x", 0.30)
        self.declare_parameter("barcode_roi_y", 0.42)
        self.declare_parameter("barcode_roi_w", 0.42)
        self.declare_parameter("barcode_roi_h", 0.38)
        # pylibdmtx + zbar 这两个重 backend 单独节流, 默认 3s 一次, 不要拖累主 QR 频率
        self.declare_parameter("heavy_decoder_period_sec", 3.0)
        self.declare_parameter("qr_detector_eps_x", 0.2)
        self.declare_parameter("qr_detector_eps_y", 0.2)
        self.declare_parameter("recognized_code_hold_sec", 0.0)
        self.declare_parameter("enable_ocr_recognition", False)
        self.declare_parameter("ocr_backend", "ppocr_rknn")
        self.declare_parameter("ppocr_root", "/mnt/sdcard/medicine_robot_data/models/ppocr")
        self.declare_parameter(
            "ppocr_det_model_path",
            "/mnt/sdcard/medicine_robot_data/models/ppocr/ppocrv4_det_rk3588.rknn",
        )
        self.declare_parameter(
            "ppocr_rec_model_path",
            "/mnt/sdcard/medicine_robot_data/models/ppocr/ppocrv4_rec_rk3588.rknn",
        )
        self.declare_parameter("ppocr_max_boxes", 12)
        self.declare_parameter("ocr_isolate_ppocr", True)
        self.declare_parameter("ocr_isolated_timeout_sec", 4.0)
        self.declare_parameter("ocr_recognition_period_sec", 2.0)
        self.declare_parameter("ocr_language", "eng")
        self.declare_parameter("ocr_psm", 6)
        self.declare_parameter("ocr_scale_factor", 2.0)
        self.declare_parameter("ocr_min_confidence", 35.0)
        self.declare_parameter("ocr_timeout_sec", 1.2)
        self.declare_parameter("ocr_max_chars", 500)
        self.declare_parameter("ocr_hold_last_good_sec", 12.0)
        self.declare_parameter("recognition_stability_window_size", 5)
        self.declare_parameter("recognition_stability_min_count", 2)
        self.declare_parameter("recognition_stability_ttl_sec", 18.0)
        self.declare_parameter("ocr_roi_enabled", True)
        self.declare_parameter("ocr_roi_x", 0.14)
        self.declare_parameter("ocr_roi_y", 0.28)
        self.declare_parameter("ocr_roi_w", 0.72)
        self.declare_parameter("ocr_roi_h", 0.52)
        self.declare_parameter("enable_yolo_rknn_detection", False)
        self.declare_parameter("yolo_model_path", "")
        self.declare_parameter("yolo_label_file", "")
        self.declare_parameter("yolo_labels", ",".join(COCO_LABELS))
        self.declare_parameter("yolo_class_filter", "person")
        self.declare_parameter("yolo_input_size", 640)
        self.declare_parameter("yolo_detection_period_sec", 0.2)
        self.declare_parameter("yolo_confidence_threshold", 0.2)
        self.declare_parameter("yolo_nms_threshold", 0.45)
        self.declare_parameter("yolo_detections_topic", "/medicine/vision_detections")
        self.declare_parameter("yolo_status_topic", "/medicine/yolo_rknn_status")
        self.declare_parameter("yolo_rknn_core_mask", "auto")
        self.declare_parameter("yolo_publish_empty_detections", True)
        self.declare_parameter("yolo_letterbox_pad_value", 0)
        self.declare_parameter("yolo_draw_overlay", True)
        self.declare_parameter("drug_catalog_json", default_drug_catalog)

        self.drug_info_topic = self.get_parameter("drug_info_topic").get_parameter_value().string_value
        self.status_topic = self.get_parameter("status_topic").get_parameter_value().string_value
        self.control_topic = self.get_parameter("control_topic").get_parameter_value().string_value
        self.publisher = self.create_publisher(DrugInfo, self.drug_info_topic, 10)
        self.status_publisher = self.create_publisher(String, self.status_topic, 10)
        self.yolo_detections_publisher = self.create_publisher(
            String,
            self.get_string_parameter("yolo_detections_topic"),
            10,
        )
        self.yolo_status_publisher = self.create_publisher(
            String,
            self.get_string_parameter("yolo_status_topic"),
            10,
        )
        self.frame_lock = threading.Lock()
        self.control_lock = threading.Lock()
        self.drug_catalog = self.load_drug_catalog()
        self.qr_detector = cv2.QRCodeDetector() if cv2 is not None else None
        self.qr_clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)) if cv2 is not None else None
        self.configure_qr_detector()
        self.detected_drug_info = None
        self.last_code_text = ""
        self.last_code_type = ""
        self.last_code_method = ""
        self.last_code_points = []
        self.last_trace_code = ""
        self.last_trace_source = ""
        self.last_trace_method = ""
        self.last_trace_time = 0.0
        self.last_barcode_label_fields = {}
        self.last_qr_text = ""
        self.last_qr_time = 0.0
        self.last_qr_points = []
        self.last_qr_error = ""
        self.last_qr_method = ""
        self.last_qr_detected = False
        self.last_qr_decode_failed = False
        self.last_qr_attempt_time = 0.0
        self.qr_attempt_count = 0
        self.qr_skip_count = 0
        self.qr_success_count = 0
        self.last_qr_candidate_count = 0
        self.last_external_decode_attempt_time = 0.0
        self.last_heavy_decode_attempt_time = 0.0
        # QR async worker: 把 250ms 的 QR pipeline 从 33ms 主循环里拆出去
        self.qr_worker_thread = None
        self.qr_worker_stop = threading.Event()
        self.qr_worker_lock = threading.Lock()
        self.qr_pending_frame = None
        self.qr_pending_seq = 0
        self.qr_processed_seq = 0
        self.qr_worker_drop_count = 0
        self.qr_worker_busy_ms = 0.0
        self.external_decode_attempt_count = 0
        self.external_decode_skip_count = 0
        self.external_decode_busy_count = 0
        self.external_decode_complete_count = 0
        self.external_decode_timeout_count = 0
        self.pending_external_decoded = []
        self.isolated_zxing_process = None
        self.isolated_zxing_temp_dir = ""
        self.isolated_zxing_started_at = 0.0
        self.last_ocr_text = ""
        self.last_ocr_confidence = 0.0
        self.last_ocr_time = 0.0
        self.last_ocr_error = ""
        self.last_good_ocr_text = ""
        self.last_good_ocr_confidence = 0.0
        self.last_good_ocr_time = 0.0
        self.last_ocr_held = False
        self.last_ocr_attempt_time = 0.0
        self.recognition_stability_history = []
        self.last_recognition_stability = {
            "stable": False,
            "count": 0,
            "required": 2,
            "signature": "",
            "drug_name": "",
            "recognition_channel": "",
            "trace_code": "",
            "product_code": "",
            "confidence": 0.0,
            "age_sec": -1.0,
        }
        self.ocr_attempt_count = 0
        self.ocr_skip_count = 0
        self.ocr_success_count = 0
        self.ppocr_runner = None
        self.ppocr_backend_loaded = False
        self.qr_scan_enabled_runtime = bool(self.get_bool_parameter("enable_qr_recognition"))
        self.ocr_scan_enabled_runtime = False
        self.ocr_single_shot_requested = False
        self.vision_control_message = ""
        self.ocr_worker_stop = threading.Event()
        self.ocr_worker_lock = threading.Lock()
        self.ocr_pending_frame = None
        self.ocr_pending_seq = 0
        self.ocr_processed_seq = 0
        self.ocr_worker_drop_count = 0
        self.ocr_worker_busy_ms = 0.0
        self.last_ocr_roi_rect = []
        self.last_ocr_roi_frame_size = []
        self.last_barcode_roi_rect = []
        self.last_barcode_roi_frame_size = []
        self.yolo_rknn = None
        self.yolo_helper = None
        self.yolo_model_loaded = False
        self.yolo_status = "disabled"
        self.yolo_message = ""
        self.yolo_labels = self.load_yolo_labels()
        self.yolo_class_filter = self.load_yolo_class_filter()
        self.yolo_last_output_shapes = []
        self.yolo_last_inference_ms = 0.0
        self.yolo_last_detection_count = 0
        self.yolo_last_detections = []
        self.yolo_last_frame_shape = []
        self.yolo_last_attempt_time = 0.0
        self.yolo_attempt_count = 0
        self.yolo_skip_count = 0
        self.yolo_success_count = 0
        self.yolo_error = ""
        self.capture = None
        self.latest_frame_jpeg = None
        self.last_preview_encode_time = 0.0
        self.preview_client_lock = threading.Lock()
        self.preview_client_request_count = 0
        self.preview_last_client_time = 0.0
        self.last_camera_open_attempt = 0.0
        self.camera_ok = False
        self.frame_count = 0
        self.frame_width = 0
        self.frame_height = 0
        self.frame_timestamps = []
        self.camera_actual_fps = 0.0
        self.last_camera_error = ""
        period = self.get_parameter("publish_period_sec").get_parameter_value().double_value
        camera_read_period = self.get_parameter("camera_read_period_sec").get_parameter_value().double_value
        self.preview_server = None
        self.preview_server_thread = None
        self.create_timer(max(camera_read_period, 0.005), self.update_camera_state)
        self.create_timer(max(period, 0.1), self.publish_drug_info)
        self.control_subscription = self.create_subscription(
            String, self.control_topic, self.handle_vision_control, 10
        )
        if self.get_parameter("enable_preview_server").get_parameter_value().bool_value:
            self.start_preview_server()
        self.initialize_yolo_runtime()
        self.qr_worker_thread = threading.Thread(target=self.qr_worker_loop, name="qr_worker", daemon=True)
        self.qr_worker_thread.start()
        self.ocr_worker_thread = threading.Thread(target=self.ocr_worker_loop, name="ocr_worker", daemon=True)
        self.ocr_worker_thread.start()
        self.get_logger().info(f"Medicine vision detector started. Publishing {self.drug_info_topic}")

    def get_string_parameter(self, name):
        return self.get_parameter(name).get_parameter_value().string_value

    def get_int_parameter(self, name):
        return self.get_parameter(name).get_parameter_value().integer_value

    def get_float_parameter(self, name):
        return self.get_parameter(name).get_parameter_value().double_value

    def get_bool_parameter(self, name):
        return self.get_parameter(name).get_parameter_value().bool_value

    def handle_vision_control(self, msg):
        try:
            payload = json.loads(msg.data or "{}")
        except json.JSONDecodeError:
            payload = {"action": str(msg.data or "").strip()}
        action = str(payload.get("action") or "").strip().lower()
        with self.control_lock:
            if action == "qr":
                enabled = bool(payload.get("enabled"))
                self.qr_scan_enabled_runtime = enabled
                self.vision_control_message = f"qr {'enabled' if enabled else 'disabled'}"
            elif action == "ocr":
                mode = str(payload.get("mode") or "single").strip().lower()
                if mode in {"continuous", "on"}:
                    self.ocr_scan_enabled_runtime = True
                    self.ocr_single_shot_requested = False
                    self.vision_control_message = "ocr continuous enabled"
                elif mode in {"off", "stop"}:
                    self.ocr_scan_enabled_runtime = False
                    self.ocr_single_shot_requested = False
                    self.vision_control_message = "ocr disabled"
                else:
                    self.ocr_single_shot_requested = True
                    self.vision_control_message = "ocr single requested"
            else:
                self.vision_control_message = f"unknown action: {action or '-'}"

    def get_float_list_parameter(self, name, fallback):
        text = self.get_string_parameter(name)
        values = []
        for item in text.replace(";", ",").split(","):
            item = item.strip()
            if not item:
                continue
            try:
                value = float(item)
            except ValueError:
                continue
            if value > 0.0 and all(abs(value - old) > 0.01 for old in values):
                values.append(value)
        return values or list(fallback)

    def configure_qr_detector(self):
        if self.qr_detector is None:
            return
        if hasattr(self.qr_detector, "setEpsX"):
            self.qr_detector.setEpsX(float(self.get_float_parameter("qr_detector_eps_x")))
        if hasattr(self.qr_detector, "setEpsY"):
            self.qr_detector.setEpsY(float(self.get_float_parameter("qr_detector_eps_y")))

    def load_drug_catalog(self):
        try:
            data = json.loads(self.get_string_parameter("drug_catalog_json"))
        except json.JSONDecodeError as exc:
            self.get_logger().warn(f"Invalid drug_catalog_json: {exc}")
            return {}
        if not isinstance(data, dict):
            return {}
        catalog = {}
        for drug_id, value in data.items():
            if not isinstance(value, dict):
                continue
            catalog[str(drug_id)] = {
                "drug_id": str(value.get("drug_id") or drug_id),
                "drug_name": str(value.get("drug_name") or value.get("name") or drug_id),
                "drug_type": str(value.get("drug_type") or value.get("type") or "unknown"),
                "confidence": float(value.get("confidence", 1.0)),
                "loaded": self.normalize_bool(value.get("loaded", True), True),
                "recognition_source": f"qr_catalog:{drug_id}",
            }
        return catalog

    def load_yolo_labels(self):
        label_file = self.get_string_parameter("yolo_label_file")
        if label_file and os.path.exists(label_file):
            try:
                with open(label_file, "r", encoding="utf-8") as file:
                    values = [line.strip() for line in file if line.strip()]
                    if values:
                        return values
            except OSError:
                pass
        raw = self.get_string_parameter("yolo_labels")
        values = [item.strip() for item in raw.split(",") if item.strip()]
        return values or list(COCO_LABELS)

    def load_yolo_class_filter(self):
        raw = self.get_string_parameter("yolo_class_filter")
        return {item.strip() for item in raw.split(",") if item.strip()}

    def initialize_yolo_runtime(self):
        if not self.get_bool_parameter("enable_yolo_rknn_detection"):
            self.yolo_status = "disabled"
            self.yolo_message = "YOLO RKNN detection disabled"
            self.publish_yolo_status()
            return
        if cv2 is None:
            self.yolo_status = "opencv_missing"
            self.yolo_message = "python3-opencv is not available"
            self.publish_yolo_status()
            return
        if np is None:
            self.yolo_status = "numpy_missing"
            self.yolo_message = "numpy is not available"
            self.publish_yolo_status()
            return
        if RKNNLite is None:
            self.yolo_status = "rknnlite_missing"
            self.yolo_message = "rknn-toolkit-lite2 is not available"
            self.publish_yolo_status()
            return
        model_path = self.get_string_parameter("yolo_model_path")
        if not model_path:
            self.yolo_status = "model_missing"
            self.yolo_message = "parameter yolo_model_path is empty"
            self.publish_yolo_status()
            return
        if not os.path.exists(model_path):
            self.yolo_status = "model_missing"
            self.yolo_message = f"yolo_model_path does not exist: {model_path}"
            self.publish_yolo_status()
            return
        self.model_path = model_path
        self.input_size = self.get_int_parameter("yolo_input_size")
        self.confidence_threshold = self.get_float_parameter("yolo_confidence_threshold")
        self.nms_threshold = self.get_float_parameter("yolo_nms_threshold")
        self.rknn_core_mask = self.get_string_parameter("yolo_rknn_core_mask")
        self.publish_empty_detections = self.get_bool_parameter("yolo_publish_empty_detections")
        self.letterbox_pad_value = self.get_int_parameter("yolo_letterbox_pad_value")
        self.labels = list(self.yolo_labels)
        self.class_filter = set(self.yolo_class_filter)
        try:
            self.yolo_rknn = RKNNLite()
            ret = self.yolo_rknn.load_rknn(model_path)
            if ret != 0:
                self.yolo_status = "model_load_failed"
                self.yolo_message = f"RKNNLite.load_rknn returned {ret}"
                self.publish_yolo_status()
                return
            ret = self.init_yolo_rknn_runtime()
            if ret != 0:
                self.yolo_status = "runtime_init_failed"
                self.yolo_message = f"RKNNLite.init_runtime returned {ret}"
                self.publish_yolo_status()
                return
        except Exception as exc:
            self.yolo_status = "runtime_init_failed"
            self.yolo_message = f"{type(exc).__name__}: {exc}"
            self.yolo_error = self.yolo_message
            self.publish_yolo_status()
            return
        self.yolo_model_loaded = True
        self.yolo_status = "ready"
        self.yolo_message = f"model loaded: {model_path}"
        self.yolo_error = ""
        self.publish_yolo_status()

    def init_yolo_rknn_runtime(self):
        core_mask = self.resolve_yolo_core_mask()
        try:
            if core_mask is None:
                return self.yolo_rknn.init_runtime()
            return self.yolo_rknn.init_runtime(core_mask=core_mask)
        except TypeError:
            return self.yolo_rknn.init_runtime()

    def resolve_yolo_core_mask(self):
        if RKNNLite is None:
            return None
        value = self.get_string_parameter("yolo_rknn_core_mask").strip().lower()
        mapping = {
            "0": "NPU_CORE_0",
            "1": "NPU_CORE_1",
            "2": "NPU_CORE_2",
            "0_1": "NPU_CORE_0_1",
            "0_1_2": "NPU_CORE_0_1_2",
            "all": "NPU_CORE_0_1_2",
            "auto": "NPU_CORE_AUTO",
        }
        attr = mapping.get(value, "NPU_CORE_AUTO")
        return getattr(RKNNLite, attr, None)

    def update_yolo_detection(self, frame):
        if not self.get_bool_parameter("enable_yolo_rknn_detection"):
            return
        if not self.yolo_model_loaded or self.yolo_rknn is None:
            return
        now = time.monotonic()
        period = max(self.get_float_parameter("yolo_detection_period_sec"), 0.02)
        if now - self.yolo_last_attempt_time < period:
            self.yolo_skip_count += 1
            return
        self.yolo_last_attempt_time = now
        self.yolo_attempt_count += 1
        self.input_size = self.get_int_parameter("yolo_input_size")
        self.confidence_threshold = self.get_float_parameter("yolo_confidence_threshold")
        self.nms_threshold = self.get_float_parameter("yolo_nms_threshold")
        self.publish_empty_detections = self.get_bool_parameter("yolo_publish_empty_detections")
        self.letterbox_pad_value = self.get_int_parameter("yolo_letterbox_pad_value")
        self.class_filter = self.load_yolo_class_filter()
        try:
            network_input, meta = YoloRknnDetector.letterbox(self, frame)
            rgb = cv2.cvtColor(network_input, cv2.COLOR_BGR2RGB)
            input_data = np.expand_dims(rgb, axis=0)
            start = time.monotonic()
            outputs = self.yolo_rknn.inference(inputs=[input_data])
            self.yolo_last_inference_ms = (time.monotonic() - start) * 1000.0
            self.yolo_last_output_shapes = [list(np.array(output).shape) for output in outputs]
            detections = YoloRknnDetector.decode_outputs(self, outputs, meta, frame.shape)
        except Exception as exc:
            self.yolo_status = "inference_failed"
            self.yolo_message = f"{type(exc).__name__}: {exc}"
            self.yolo_error = self.yolo_message
            self.publish_yolo_status()
            return
        self.yolo_last_frame_shape = list(frame.shape)
        self.yolo_last_detections = detections
        self.yolo_last_detection_count = len(detections)
        self.yolo_success_count += 1
        self.yolo_status = "running"
        self.yolo_message = f"detections={len(detections)}, inference_ms={self.yolo_last_inference_ms:.1f}"
        self.yolo_error = ""
        self.publish_yolo_detections(detections)
        self.publish_yolo_status()

    def publish_yolo_detections(self, detections):
        if detections or self.get_bool_parameter("yolo_publish_empty_detections"):
            payload = {
                "ok": True,
                "backend": "rknnlite",
                "model_path": self.get_string_parameter("yolo_model_path"),
                "camera_device": self.get_string_parameter("camera_device"),
                "frame_shape": self.yolo_last_frame_shape,
                "input_size": self.get_int_parameter("yolo_input_size"),
                "output_shapes": self.yolo_last_output_shapes,
                "inference_ms": self.yolo_last_inference_ms,
                "detection_count": len(detections),
                "detections": detections,
                "stamp": time.time(),
            }
            self.yolo_detections_publisher.publish(String(data=json.dumps(payload, ensure_ascii=False)))

    def publish_yolo_status(self):
        payload = {
            "status": self.yolo_status,
            "message": self.yolo_message,
            "model_path": self.get_string_parameter("yolo_model_path"),
            "model_loaded": self.yolo_model_loaded,
            "camera_device": self.get_string_parameter("camera_device"),
            "camera_ok": self.camera_ok,
            "rknnlite_available": RKNNLite is not None,
            "opencv_available": cv2 is not None,
            "numpy_available": np is not None,
            "npu_render_node": "/dev/dri/renderD129" if os.path.exists("/dev/dri/renderD129") else "",
            "output_shapes": self.yolo_last_output_shapes,
            "frame_shape": self.yolo_last_frame_shape,
            "inference_ms": self.yolo_last_inference_ms,
            "detection_count": self.yolo_last_detection_count,
            "attempt_count": self.yolo_attempt_count,
            "skip_count": self.yolo_skip_count,
            "success_count": self.yolo_success_count,
            "error": self.yolo_error,
            "stamp": time.time(),
        }
        self.yolo_status_publisher.publish(String(data=json.dumps(payload, ensure_ascii=False)))

    def release_yolo_runtime(self):
        if self.yolo_rknn is not None:
            try:
                self.yolo_rknn.release()
            except Exception:
                pass
            self.yolo_rknn = None
        self.yolo_model_loaded = False

    def is_model_zoo_yolov8_output(self, outputs):
        return YoloRknnDetector.is_model_zoo_yolov8_output(self, outputs)

    def decode_model_zoo_yolov8(self, outputs, meta, frame_shape):
        return YoloRknnDetector.decode_model_zoo_yolov8(self, outputs, meta, frame_shape)

    def model_zoo_flatten(self, value):
        return YoloRknnDetector.model_zoo_flatten(self, value)

    def model_zoo_box_process(self, position):
        return YoloRknnDetector.model_zoo_box_process(self, position)

    def model_zoo_dfl(self, position):
        return YoloRknnDetector.model_zoo_dfl(self, position)

    def softmax(self, value, axis):
        return YoloRknnDetector.softmax(self, value, axis)

    def decode_single_output(self, output, meta, frame_shape):
        return YoloRknnDetector.decode_single_output(self, output, meta, frame_shape)

    def decode_end2end(self, data, meta, frame_shape):
        return YoloRknnDetector.decode_end2end(self, data, meta, frame_shape)

    def decode_yolo_predictions(self, data, meta, frame_shape):
        return YoloRknnDetector.decode_yolo_predictions(self, data, meta, frame_shape)

    def make_detection(self, class_id, score, x1, y1, x2, y2, meta, frame_shape, xyxy):
        return YoloRknnDetector.make_detection(self, class_id, score, x1, y1, x2, y2, meta, frame_shape, xyxy)

    def nms(self, detections):
        return YoloRknnDetector.nms(self, detections)

    def normalize_bool(self, value, default=False):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y", "loaded", "已装药"}
        return default

    def get_decoder_backend_names(self):
        if not self.qr_scan_enabled_runtime:
            return []
        backends = []
        if self.qr_detector is not None and self.qr_scan_enabled_runtime:
            backends.append("opencv_qr")
        if self.get_bool_parameter("enable_datamatrix_recognition"):
            if zxingcpp is not None and self.get_bool_parameter("enable_zxingcpp_recognition"):
                backends.append("zxingcpp")
            if dmtx_decode is not None and self.get_bool_parameter("enable_pylibdmtx_recognition"):
                backends.append("pylibdmtx")
        if self.get_bool_parameter("enable_zbar_recognition"):
            backends.append("zbar")
        return backends

    def get_ocr_backend_name(self):
        backend = self.get_string_parameter("ocr_backend").strip().lower()
        if backend in {"ppocr_rknn", "rknn", "ppocr-rknn"}:
            return "ppocr_rknn"
        if backend in {"ppocr", "ppocr_onnx", "ppocr-onnx"}:
            return "ppocr_onnx"
        if pytesseract is not None:
            return "pytesseract"
        return ""

    def parse_label_fields(self, text):
        stripped = text.strip()
        compact = re.sub(r"\s+", "", stripped)
        # Generated medicine Code128 labels may encode a plain
        # "product_code / trace_id" payload instead of a JSON-like label.
        # Example: "C600510 / TRACE-P006-001".  Split it into normal label
        # fields so downstream batch matching can compare product and trace
        # independently instead of treating the whole string as one trace id.
        if (
            "/" in compact
            and not (compact.startswith("{") and compact.endswith("}"))
            and not re.search(r"[\u4e00-\u9fff]", compact)
        ):
            parts = [part.strip() for part in compact.split("/") if part.strip()]
            if len(parts) == 2:
                return {
                    "pc": parts[0],
                    "pdi": parts[1],
                    "trace_id": parts[1],
                }
        if not stripped.startswith("{") or not stripped.endswith("}"):
            return {}
        fields = {}
        for item in stripped[1:-1].split(","):
            if ":" not in item:
                continue
            key, value = item.split(":", 1)
            key = key.strip()
            value = value.strip()
            if not key:
                continue
            if value.lower() in {"null", "none"}:
                value = ""
            fields[key] = value
        if not any(key in fields for key in ("on", "pc", "pm", "qty", "pdi")):
            return {}
        return fields

    def build_label_drug_info(self, text, fields, source_type):
        drug_id = fields.get("pc") or fields.get("on") or text
        drug_name = fields.get("pm") or fields.get("mc") or drug_id
        return {
            "drug_id": drug_id,
            "drug_name": drug_name,
            "drug_type": "material_label",
            "confidence": 0.9,
            "loaded": True,
            "recognition_source": f"{source_type}_label:{drug_id}",
            "label_fields": fields,
            "raw_code_text": text,
        }

    def normalize_ocr_text(self, text):
        cleaned = str(text or "").replace("\u3000", " ")
        cleaned = re.sub(r"[|｜]+", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def extract_ocr_fields(self, text):
        cleaned = self.normalize_ocr_text(text)
        compact = re.sub(r"\s+", "", cleaned)
        fields = {
            "drug_name": "",
            "spec": "",
            "manufacturer": "",
            "approval_no": "",
            "drug_name_candidates": [],
            "drug_name_score": 0,
            "raw_text": cleaned,
        }
        if not cleaned:
            return fields

        approval_match = re.search(r"\u56fd\u836f\u51c6\u5b57\s*[A-ZHZSBJTF]\s*\d{8}", cleaned, re.IGNORECASE)
        if approval_match:
            fields["approval_no"] = re.sub(r"\s+", "", approval_match.group(0).upper())

        manufacturer_match = re.search(r"[\u4e00-\u9fffA-Za-z0-9\uff08\uff09()\u00b7]{2,32}(?:\u5236\u836f|\u836f\u4e1a|\u533b\u836f|\u751f\u7269|\u96c6\u56e2)?(?:\u6709\u9650\u8d23\u4efb\u516c\u53f8|\u6709\u9650\u516c\u53f8|\u80a1\u4efd\u6709\u9650\u516c\u53f8|\u5236\u836f\u5382|\u836f\u5382)", cleaned)
        if manufacturer_match:
            fields["manufacturer"] = manufacturer_match.group(0)

        spec_match = re.search(
            r"(?:(?:\u89c4\u683c|\u89c4\s*\u683c|\u51c0\u542b\u91cf|\u88c5\u91cf)[:\uff1a]?\s*)?"
            r"\d+(?:\.\d+)?\s*(?:mg|g|ml|mL|ML|\u03bcg|ug|IU|%)"
            r"(?:\s*[x\u00d7*]\s*\d+\s*(?:\u7247|\u7c92|\u888b|\u8d34|\u652f|\u74f6|\u76d2|\u677f|\u679a|\u5305))?",
            cleaned,
            re.IGNORECASE,
        )
        if spec_match:
            fields["spec"] = spec_match.group(0).strip()

        def accept_direct_drug_name(value, score=96):
            value = str(value or "").strip()
            value = re.sub(r"^[\s:?,??;?|?-]+", "", value)
            value = re.split(r"(?:\s+|?[:?]?|?[:?]?|??[:?]?|???[:?]?|???[:?]?|Code\s*128|code\s*128)", value, maxsplit=1, flags=re.IGNORECASE)[0]
            value = re.sub(r"[xX?*]?\d+\s*(?:?|?|?|?|?|?|?|?|?|?)?(?:?)?$", "", value)
            value = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9???()]+$", "", value).strip()
            if 2 <= len(value) <= 20 and re.search(r"[\u4e00-\u9fff]", value):
                fields["drug_name"] = value
                fields["drug_name_candidates"] = [value]
                fields["drug_name_score"] = int(score)
                return True
            return False

        labeled_name_match = re.search(
            r"(?:??|??|??|??|????|????)\s*[:?]?\s*([\u4e00-\u9fffA-Za-z0-9???()xX?*]{2,32})",
            cleaned,
            re.IGNORECASE,
        )
        if labeled_name_match and accept_direct_drug_name(labeled_name_match.group(1), 98):
            return fields

        for generic_name in ("???", "???", "???", "???", "???", "???", "????"):
            if generic_name in compact:
                fields["drug_name"] = generic_name
                fields["drug_name_candidates"] = [generic_name]
                fields["drug_name_score"] = 95
                return fields

        # Prefer known catalog names if they appear in the OCR text.
        for drug_id, value in self.drug_catalog.items():
            candidate_name = str(value.get("drug_name") or value.get("name") or drug_id).strip()
            name_compact = re.sub(r"\s+", "", candidate_name)
            if name_compact and name_compact in compact:
                fields["drug_name"] = candidate_name
                fields["drug_name_candidates"] = [candidate_name]
                fields["drug_name_score"] = 100
                return fields

        # Then extract name-like Chinese medicine/product names ending with common dosage/form suffixes.
        name_suffixes = (
            "\u7247", "\u80f6\u56ca", "\u9897\u7c92", "\u53e3\u670d\u6db2", "\u6ce8\u5c04\u6db2", "\u4e38", "\u6563", "\u818f", "\u4e73\u818f", "\u8f6f\u818f",
            "\u51dd\u80f6", "\u8d34", "\u8d34\u818f", "\u521b\u53ef\u8d34", "\u6ef4\u773c\u6db2", "\u6ef4\u4e38", "\u7cd6\u6d46", "\u55b7\u96fe\u5242", "\u6813",
            "\u6d17\u5242", "\u914a", "\u8336", "\u836f",
        )
        stop_words = {
            "\u6b62\u8840", "\u9547\u75db", "\u6b62\u75db", "\u6d88\u708e", "\u6108\u521b", "\u6108\u5408", "\u9002\u7528", "\u7528\u6cd5", "\u7528\u91cf",
            "\u7981\u5fcc", "\u6ce8\u610f", "\u6709\u6548\u671f", "\u751f\u4ea7\u65e5\u671f", "\u6279\u53f7", "\u89c4\u683c", "\u5382\u5bb6", "\u8bf4\u660e\u4e66",
            "\u5916\u7528", "\u5185\u670d", "\u6279\u51c6\u6587\u53f7", "\u56fd\u836f\u51c6\u5b57", "\u751f\u4ea7\u4f01\u4e1a", "\u751f\u4ea7\u5382\u5bb6", "\u8d2e\u85cf",
            "\u6210\u4efd", "\u6027\u72b6", "\u9002\u5e94\u75c7", "\u4e0d\u826f\u53cd\u5e94", "\u7981\u7528", "\u614e\u7528", "\u513f\u7ae5", "\u5b55\u5987",
            "\u8001\u5e74", "\u8bf7\u4ed4\u7ec6", "\u8be6\u89c1", "\u5305\u88c5", "\u5546\u6807", "\u672c\u54c1", "\u7528\u4e8e", "\u8d34\u4e8e",
            "\u88c5", "\u76d2", "\u6761\u7801", "\u4e8c\u7ef4\u7801", "\u8ffd\u6eaf\u7801", "\u670d\u52a1\u70ed\u7ebf",
        }
        hard_reject_words = {
            "\u6709\u9650\u516c\u53f8", "\u80a1\u4efd\u6709\u9650\u516c\u53f8", "\u6709\u9650\u8d23\u4efb\u516c\u53f8", "\u5236\u836f\u5382", "\u836f\u5382", "\u751f\u4ea7\u4f01\u4e1a",
            "\u751f\u4ea7\u5382\u5bb6", "\u6279\u51c6\u6587\u53f7", "\u56fd\u836f\u51c6\u5b57", "\u89c4\u683c", "\u6709\u6548\u671f", "\u751f\u4ea7\u65e5\u671f", "\u6279\u53f7",
            "\u8bf4\u660e\u4e66", "\u4e8c\u7ef4\u7801", "\u6761\u7801", "\u8ffd\u6eaf\u7801",
        }
        strong_medicine_terms = {
            "\u5934\u5b62", "\u963f\u83ab\u897f\u6797", "\u5e03\u6d1b\u82ac", "\u5bf9\u4e59\u9170\u6c28\u57fa\u915a", "\u82ef\u78fa\u9178", "\u6c28\u6c2f\u5730\u5e73",
            "\u785d\u82ef\u5730\u5e73", "\u4e8c\u7532\u53cc\u80cd", "\u963f\u53f8\u5339\u6797", "\u6c2f\u5421\u683c\u96f7", "\u5965\u7f8e\u62c9\u5511", "\u8499\u8131\u77f3",
            "\u4e91\u5357\u767d\u836f", "\u767d\u836f", "\u521b\u53ef\u8d34", "\u80f6\u56ca", "\u9897\u7c92", "\u53e3\u670d\u6db2", "\u6ce8\u5c04\u6db2", "\u6ef4\u773c\u6db2",
            "\u7247", "\u4e38", "\u818f", "\u8d34",
        }

        def normalize_candidate(value):
            value = str(value or "")
            value = re.sub(r"^(?:OTC|otc|RX|Rx)+", "", value)
            value = re.sub(r"^[^\u4e00-\u9fffA-Za-z0-9]+", "", value)
            # OCR may glue the tail of an approval number/count before or after the real name.
            value = re.sub(r"^\d{1,2}(?=[\u4e00-\u9fff])", "", value)
            value = re.sub(r"\d+(?:\u7247|\u7c92|\u888b|\u8d34|\u652f|\u74f6|\u76d2|\u677f|\u679a|\u5305|\u4e38)(?:\u88c5)?$", "", value)
            value = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9\u00b7\uff08\uff09()]+$", "", value)
            return value.strip()

        def score_ocr_drug_candidate(value, suffix):
            value = normalize_candidate(value)
            if len(value) < 2 or len(value) > 30:
                return None
            if re.fullmatch(r"\d+(?:\u7247|\u7c92|\u888b|\u8d34|\u652f|\u74f6|\u76d2|\u677f|\u679a|\u5305|\u4e38|\u76d2\u88c5|\u7247\u88c5)", value):
                return None
            if re.search(r"\d", value) and not any(word in value for word in {"\u7ef4B", "B\u65cf", "\u7ef4C"}):
                return None
            if sum(ch.isdigit() for ch in value) > 2:
                return None
            if re.search(r"[A-ZHZSBJTF]\d{6,}", value, re.IGNORECASE):
                return None
            if any(word in value for word in hard_reject_words):
                return None
            # Slogan/function phrases are useful context, but should not become drug names.
            noise_hits = sum(1 for word in stop_words if word in value)
            score = len(value)
            if suffix in {"\u521b\u53ef\u8d34", "\u53e3\u670d\u6db2", "\u6ce8\u5c04\u6db2", "\u80f6\u56ca", "\u9897\u7c92", "\u6ef4\u773c\u6db2"}:
                score += 18
            elif suffix in {"\u7247", "\u4e38", "\u6563", "\u818f", "\u8d34"}:
                score += 10
            elif suffix == "\u836f":
                score -= 6
            score += sum(12 for word in strong_medicine_terms if word in value)
            score -= noise_hits * 18
            if re.match(r"^(?:\u6b62\u8840|\u9547\u75db|\u6b62\u75db|\u6d88\u708e|\u6108\u521b|\u6108\u5408|\u9002\u7528|\u7528\u4e8e|\u5916\u7528|\u5185\u670d)", value):
                score -= 24
            if value.endswith("\u836f") and not any(word in value for word in strong_medicine_terms):
                score -= 12
            if noise_hits >= 2 and not any(word in value for word in {"\u4e91\u5357\u767d\u836f", "\u521b\u53ef\u8d34"}):
                return None
            if score < 12:
                return None
            return score, value

        scored_by_value = {}
        for suffix in name_suffixes:
            pattern = rf"[\u4e00-\u9fffA-Za-z0-9\u00b7\uff08\uff09()]{{1,24}}{re.escape(suffix)}"
            for match in re.finditer(pattern, compact):
                raw_value = match.group(0)
                variants = {raw_value}
                # OCR often glues field labels/approval numbers before the drug name.
                # Try shorter suffix-ending tails so noisy long text can still yield the medicine name.
                for start_index in range(1, len(raw_value)):
                    tail = raw_value[start_index:]
                    if 2 <= len(tail) <= 18 and tail.endswith(suffix):
                        variants.add(tail)
                for variant in variants:
                    scored = score_ocr_drug_candidate(variant, suffix)
                    if scored is None:
                        continue
                    score, value = scored
                    if value not in scored_by_value or score > scored_by_value[value]:
                        scored_by_value[value] = score
        candidates = sorted(
            ((score, value) for value, score in scored_by_value.items()),
            key=lambda item: item[0],
            reverse=True,
        )
        if candidates:
            fields["drug_name_candidates"] = [value for _, value in candidates[:5]]
            fields["drug_name_score"] = int(candidates[0][0])
            fields["drug_name"] = candidates[0][1]
            return fields

        return fields

    def update_last_good_ocr(self, text, confidence, now):
        cleaned = str(text or "").strip()
        if not cleaned:
            return
        self.last_good_ocr_text = cleaned
        self.last_good_ocr_confidence = float(confidence or 0.0)
        self.last_good_ocr_time = now
        self.last_ocr_held = False

    def hold_last_good_ocr_if_available(self, now):
        hold_sec = max(float(self.get_float_parameter("ocr_hold_last_good_sec")), 0.0)
        if hold_sec <= 0.0 or not self.last_good_ocr_text or self.last_good_ocr_time <= 0.0:
            self.last_ocr_held = False
            return False
        age = now - self.last_good_ocr_time
        if age > hold_sec:
            self.last_ocr_held = False
            return False
        self.last_ocr_text = self.last_good_ocr_text
        self.last_ocr_confidence = self.last_good_ocr_confidence
        self.last_ocr_time = self.last_good_ocr_time
        self.last_ocr_held = True
        return True

    def build_ocr_drug_info(self):
        text = str(self.last_ocr_text or "").strip()
        if not text or not self.is_meaningful_ocr_text(text):
            return None
        confidence = float(self.last_ocr_confidence or 0.0)
        min_confidence = max(float(self.get_float_parameter("ocr_min_confidence")) / 100.0, 0.05)
        if confidence < min_confidence:
            return None

        label_fields = self.parse_label_fields(text)
        if label_fields:
            drug_info = self.build_label_drug_info(text, label_fields, "ocr")
            drug_info["confidence"] = max(min(confidence, 0.95), 0.55)
            drug_info["recognition_channel"] = "ocr"
            drug_info["ocr_match_text"] = text
            drug_info["ocr_extracted_fields"] = self.extract_ocr_fields(text)
            drug_info["needs_review"] = False
            return drug_info

        extracted_fields = self.extract_ocr_fields(text)
        extracted_drug_name = extracted_fields.get("drug_name", "").strip()
        compact = re.sub(r"\s+", "", extracted_drug_name or text)
        for drug_id, value in self.drug_catalog.items():
            candidate_id = str(value.get("drug_id") or drug_id)
            candidate_name = str(value.get("drug_name") or value.get("name") or candidate_id)
            candidate_type = str(value.get("drug_type") or value.get("type") or "unknown")
            name_compact = re.sub(r"\s+", "", candidate_name)
            id_compact = re.sub(r"\s+", "", candidate_id)
            if (
                (name_compact and name_compact in compact)
                or (compact and len(compact) >= 2 and compact in name_compact)
                or (id_compact and id_compact in compact)
            ):
                return {
                    "drug_id": candidate_id,
                    "drug_name": candidate_name,
                    "drug_type": candidate_type,
                    "confidence": max(min(confidence, 0.95), 0.60),
                    "loaded": self.normalize_bool(value.get("loaded", True), True),
                    "recognition_source": f"ocr_catalog:{candidate_id}",
                    "recognition_channel": "ocr",
                    "ocr_match_text": extracted_drug_name or text,
                    "ocr_extracted_fields": extracted_fields,
                    "needs_review": False,
                    "label_fields": {},
                    "raw_code_text": "",
                }

        if not extracted_drug_name:
            return None
        if confidence < 0.45:
            return None

        candidate = re.sub(r"\s+", "", extracted_drug_name)[:80] or extracted_drug_name[:80]
        return {
            "drug_id": f"ocr:{candidate}",
            "drug_name": extracted_drug_name[:80],
            "drug_type": "ocr_candidate",
            "confidence": min(confidence, 0.75),
            "loaded": False,
            "recognition_source": "ocr_text:unmatched",
            "recognition_channel": "ocr",
            "ocr_match_text": extracted_drug_name,
            "ocr_extracted_fields": extracted_fields,
            "needs_review": True,
            "label_fields": {},
            "raw_code_text": "",
        }

    def parse_qr_payload(self, qr_text, code_type="qr"):
        text = qr_text.strip()
        if not text:
            return None
        source_type = (code_type or "qr").lower()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = None
        if isinstance(data, dict):
            drug_id = str(data.get("drug_id") or data.get("id") or text)
            return {
                "drug_id": drug_id,
                "drug_name": str(data.get("drug_name") or data.get("name") or drug_id),
                "drug_type": str(data.get("drug_type") or data.get("type") or "unknown"),
                "confidence": float(data.get("confidence", 1.0)),
                "loaded": self.normalize_bool(data.get("loaded", True), True),
                "recognition_source": f"{source_type}_json:{drug_id}",
            }
        label_fields = self.parse_label_fields(text)
        if label_fields:
            return self.build_label_drug_info(text, label_fields, source_type)
        if text in self.drug_catalog:
            drug_info = dict(self.drug_catalog[text])
            drug_info["recognition_source"] = f"{source_type}_catalog:{text}"
            return drug_info
        return {
            "drug_id": text,
            "drug_name": text,
            "drug_type": "unknown",
            "confidence": 0.9,
            "loaded": True,
            "recognition_source": f"{source_type}_raw:{text}",
        }

    def normalize_qr_points(self, points, scale=1.0):
        if points is None:
            return []
        try:
            return [(int(point[0] / scale), int(point[1] / scale)) for point in points.reshape(-1, 2)]
        except (AttributeError, TypeError, ValueError):
            return []

    def normalize_external_points(self, position, scale=1.0):
        return normalize_external_position(position, scale)

    def offset_points(self, points, offset_x=0, offset_y=0):
        adjusted = []
        for point in points or []:
            try:
                x, y = point
            except (TypeError, ValueError):
                continue
            adjusted.append((int(x + offset_x), int(y + offset_y)))
        return adjusted

    def rect_to_points(self, rect, scale=1.0):
        if rect is None:
            return []
        left = getattr(rect, "left", 0)
        top = getattr(rect, "top", 0)
        width = getattr(rect, "width", 0)
        height = getattr(rect, "height", 0)
        return [
            (int(left / scale), int(top / scale)),
            (int((left + width) / scale), int(top / scale)),
            (int((left + width) / scale), int((top + height) / scale)),
            (int(left / scale), int((top + height) / scale)),
        ]

    def build_qr_candidates(self, frame):
        fast_mode = self.get_bool_parameter("qr_fast_mode")
        candidates = []
        seen = set()
        height, width = frame.shape[:2]
        source_frame = frame
        offset_x = 0
        offset_y = 0
        if self.qr_scan_enabled_runtime and self.get_bool_parameter("barcode_roi_scan_only"):
            roi_rect = self.get_barcode_roi_rect(frame)
            if roi_rect is not None:
                x1, y1, x2, y2 = roi_rect
                source_frame = frame[y1:y2, x1:x2].copy()
                offset_x = x1
                offset_y = y1
                height, width = source_frame.shape[:2]
        gray = cv2.cvtColor(source_frame, cv2.COLOR_BGR2GRAY)

        def add(name, image, scale):
            key = (name, image.shape[:2])
            if key in seen:
                return
            seen.add(key)
            candidates.append((name, image, scale, offset_x, offset_y))

        primary_scale = max(1.0, float(self.get_float_parameter("qr_scale_factor")))
        configured_scales = self.get_float_list_parameter("qr_extra_scale_factors", [primary_scale])
        scale_values = []
        for value in [1.0, primary_scale] + configured_scales:
            if value > 0.0 and all(abs(value - old) > 0.01 for old in scale_values):
                scale_values.append(value)

        for scale in scale_values:
            if scale <= 1.01:
                scaled = source_frame
                scaled_gray = gray
                scale_name = "1.0x"
            else:
                new_width = max(int(width * scale), 1)
                new_height = max(int(height * scale), 1)
                scaled = cv2.resize(source_frame, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
                scaled_gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
                scale_name = f"{scale:.2f}".rstrip("0").rstrip(".") + "x"

            enable_unsharp = self.get_bool_parameter("enable_qr_unsharp")

            if scale <= 1.01:
                add("raw", scaled, scale)
                add("gray", scaled_gray, scale)
                if self.qr_clahe is not None:
                    clahe_img = self.qr_clahe.apply(scaled_gray)
                    add("clahe", clahe_img, scale)
                    if enable_unsharp:
                        blur = cv2.GaussianBlur(clahe_img, (0, 0), 2.0)
                        add("clahe_unsharp", cv2.addWeighted(clahe_img, 1.6, blur, -0.6, 0), scale)
                continue

            if not fast_mode:
                add(f"scaled_raw_{scale_name}", scaled, scale)
            add(f"scaled_gray_{scale_name}", scaled_gray, scale)
            if self.qr_clahe is not None:
                clahe_img = self.qr_clahe.apply(scaled_gray)
                add(f"scaled_clahe_{scale_name}", clahe_img, scale)
                if enable_unsharp:
                    blur = cv2.GaussianBlur(clahe_img, (0, 0), 2.0)
                    add(f"scaled_clahe_unsharp_{scale_name}", cv2.addWeighted(clahe_img, 1.6, blur, -0.6, 0), scale)
        if self.get_bool_parameter("enable_barcode_enhancement"):
            barcode_scale_x = max(1.0, float(self.get_float_parameter("barcode_scale_x")))
            barcode_scale_y = max(1.0, float(self.get_float_parameter("barcode_scale_y")))
            barcode_width = max(int(width * barcode_scale_x), 1)
            barcode_height = max(int(height * barcode_scale_y), 1)
            barcode_gray = cv2.resize(gray, (barcode_width, barcode_height), interpolation=cv2.INTER_CUBIC)
            barcode_scale = max(barcode_scale_x, barcode_scale_y)
            add("barcode_gray", barcode_gray, barcode_scale)
            if self.qr_clahe is not None:
                barcode_clahe = self.qr_clahe.apply(barcode_gray)
                add("barcode_clahe", barcode_clahe, barcode_scale)
                blur = cv2.GaussianBlur(barcode_clahe, (0, 0), 1.2)
                barcode_unsharp = cv2.addWeighted(barcode_clahe, 1.8, blur, -0.8, 0)
                add("barcode_unsharp", barcode_unsharp, barcode_scale)
                _, barcode_binary = cv2.threshold(
                    barcode_unsharp, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )
                add("barcode_binary", barcode_binary, barcode_scale)
        return candidates

    def detect_qr_candidate(self, image, scale):
        qr_text, points, _ = self.qr_detector.detectAndDecode(image)
        normalized_points = self.normalize_qr_points(points, scale)
        if qr_text:
            return qr_text, normalized_points, bool(normalized_points)
        if self.get_bool_parameter("enable_opencv_curved_qr_recognition") and hasattr(self.qr_detector, "detectAndDecodeCurved"):
            qr_text, points, _ = self.qr_detector.detectAndDecodeCurved(image)
            curved_points = self.normalize_qr_points(points, scale)
            if qr_text:
                return qr_text, curved_points, bool(curved_points)
            if curved_points:
                normalized_points = curved_points
        return "", normalized_points, bool(normalized_points)

    def decode_zxing_candidate(self, image, scale):
        if zxingcpp is None or not self.get_bool_parameter("enable_datamatrix_recognition"):
            return []
        if not self.get_bool_parameter("enable_zxingcpp_recognition"):
            return []
        try:
            image = image.copy()
            if hasattr(zxingcpp, "read_barcodes"):
                barcodes = zxingcpp.read_barcodes(image)
            else:
                barcode = zxingcpp.read_barcode(image)
                barcodes = [barcode] if barcode is not None else []
        except Exception as exc:
            self.last_qr_error = f"zxingcpp: {exc}"
            return []
        decoded = []
        for barcode in barcodes:
            text = getattr(barcode, "text", "")
            if isinstance(text, bytes):
                text = text.decode("utf-8", errors="replace")
            if not text:
                continue
            format_name = str(getattr(barcode, "format", "barcode")).split(".")[-1].lower()
            points = self.normalize_external_points(getattr(barcode, "position", None), scale)
            decoded.append((text, points, format_name, "zxingcpp"))
        return decoded

    def cleanup_isolated_zxing_process(self):
        if self.isolated_zxing_process is not None:
            try:
                if self.isolated_zxing_process.poll() is None:
                    self.isolated_zxing_process.kill()
                    self.isolated_zxing_process.wait(timeout=0.2)
            except Exception:
                pass
            self.isolated_zxing_process = None
        if self.isolated_zxing_temp_dir:
            shutil.rmtree(self.isolated_zxing_temp_dir, ignore_errors=True)
            self.isolated_zxing_temp_dir = ""
        self.isolated_zxing_started_at = 0.0

    def start_zxing_candidates_isolated(self, candidates):
        if zxingcpp is None or not self.get_bool_parameter("enable_datamatrix_recognition"):
            return False
        if not self.get_bool_parameter("enable_zxingcpp_recognition"):
            return False
        if self.isolated_zxing_process is not None:
            return False
        try:
            temp_dir = tempfile.mkdtemp(prefix="medicine_zxing_")
            items = []
            for index, candidate in enumerate(candidates):
                method, image, scale = candidate[:3]
                offset_x = candidate[3] if len(candidate) > 3 else 0
                offset_y = candidate[4] if len(candidate) > 4 else 0
                image_path = os.path.join(temp_dir, f"candidate_{index}.png")
                try:
                    ok = cv2.imwrite(image_path, image)
                except Exception:
                    ok = False
                if ok:
                    items.append({
                        "path": image_path,
                        "method": method,
                        "scale": scale,
                        "offset_x": offset_x,
                        "offset_y": offset_y,
                    })
            if not items:
                shutil.rmtree(temp_dir, ignore_errors=True)
                return False
            manifest_path = os.path.join(temp_dir, "manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as manifest_file:
                json.dump(items, manifest_file, ensure_ascii=False)
            self.isolated_zxing_process = subprocess.Popen(
                [sys.executable, __file__, "--decode-zxing-files", manifest_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.isolated_zxing_temp_dir = temp_dir
            self.isolated_zxing_started_at = time.monotonic()
            return True
        except Exception as exc:
            self.last_qr_error = f"zxingcpp isolated: {exc}"
            if "temp_dir" in locals():
                shutil.rmtree(temp_dir, ignore_errors=True)
            self.cleanup_isolated_zxing_process()
            return False

    def poll_zxing_candidates_isolated(self):
        if self.isolated_zxing_process is None:
            return []
        timeout_sec = max(float(self.get_float_parameter("external_decoder_timeout_sec")), 0.1)
        now = time.monotonic()
        if now - self.isolated_zxing_started_at > timeout_sec:
            self.external_decode_timeout_count += 1
            self.last_qr_error = "zxingcpp isolated: timeout"
            self.cleanup_isolated_zxing_process()
            return []
        if self.isolated_zxing_process.poll() is None:
            return []
        result = self.isolated_zxing_process
        stdout, stderr = result.communicate()
        if result.returncode != 0:
            self.last_qr_error = f"zxingcpp isolated exit {result.returncode}"
            self.cleanup_isolated_zxing_process()
            return []
        try:
            payload = json.loads(stdout.strip() or "[]")
        except json.JSONDecodeError as exc:
            self.last_qr_error = f"zxingcpp isolated json: {exc}"
            self.cleanup_isolated_zxing_process()
            return []
        decoded = []
        for item in payload:
            text = str(item.get("text", ""))
            if not text:
                continue
            points = item.get("points") or []
            offset_x = int(float(item.get("offset_x") or 0))
            offset_y = int(float(item.get("offset_y") or 0))
            method = str(item.get("method") or "candidate")
            code_type = str(item.get("format") or "barcode")
            backend = str(item.get("backend") or "zxingcpp")
            decoded.append((text, self.offset_points(points, offset_x, offset_y), code_type, f"{method}:{backend}"))
        self.external_decode_complete_count += 1
        self.cleanup_isolated_zxing_process()
        return decoded

    def decode_dmtx_candidate(self, image, scale):
        if dmtx_decode is None or not self.get_bool_parameter("enable_datamatrix_recognition"):
            return []
        if not self.get_bool_parameter("enable_pylibdmtx_recognition"):
            return []
        decode_image = image
        if len(image.shape) == 3:
            decode_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        decode_image = decode_image.copy()
        try:
            # YOLO 关后, dmtx 单 candidate 跑, 600ms 覆盖大部分顽固码且不卡死 status 1Hz publisher
            results = dmtx_decode(decode_image, timeout=600, max_count=2)
        except TypeError:
            results = dmtx_decode(decode_image)
        except Exception as exc:
            self.last_qr_error = f"pylibdmtx: {exc}"
            return []
        decoded = []
        for result in results:
            data = getattr(result, "data", b"")
            text = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else str(data)
            if not text:
                continue
            points = self.rect_to_points(getattr(result, "rect", None), scale)
            decoded.append((text, points, "datamatrix", "pylibdmtx"))
        return decoded

    def decode_zbar_candidate(self, image, scale):
        if not self.get_bool_parameter("enable_zbar_recognition"):
            return []
        timeout = max(float(self.get_float_parameter("zbar_timeout_sec")), 0.2)
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name
            ok = cv2.imwrite(tmp_path, image)
            if not ok:
                os.unlink(tmp_path)
                return []
            try:
                result = subprocess.run(
                    ["zbarimg", "-q", "--raw", tmp_path],
                    capture_output=True, text=True, timeout=timeout,
                )
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
        except subprocess.TimeoutExpired:
            self.last_qr_error = "zbar: timeout"
            return []
        except FileNotFoundError:
            self.last_qr_error = "zbar: zbarimg not installed"
            return []
        except Exception as exc:
            self.last_qr_error = f"zbar: {exc}"
            return []
        decoded = []
        for line in result.stdout.splitlines():
            text = line.strip()
            if not text:
                continue
            decoded.append((text, [], "barcode", "zbar"))
        return decoded

    def decode_external_candidate(self, image, scale):
        decoded = self.decode_zxing_candidate(image, scale)
        if decoded:
            return decoded
        decoded = self.decode_dmtx_candidate(image, scale)
        if decoded:
            return decoded
        return self.decode_zbar_candidate(image, scale)

    def decode_external_candidates(self, candidates):
        decoded = []
        if self.get_bool_parameter("enable_isolated_zxingcpp_recognition"):
            decoded = self.poll_zxing_candidates_isolated()
            if not decoded and self.isolated_zxing_process is None:
                if self.start_zxing_candidates_isolated(candidates):
                    self.external_decode_attempt_count += 1
                else:
                    self.external_decode_busy_count += 1
            elif self.isolated_zxing_process is not None:
                self.external_decode_busy_count += 1
        else:
            for candidate in candidates:
                method, image, scale, offset_x, offset_y = candidate[:5]
                for code_text, points, code_type, backend in self.decode_zxing_candidate(image, scale):
                    decoded.append((code_text, self.offset_points(points, offset_x, offset_y), code_type, f"{method}:{backend}"))
                if decoded:
                    return decoded
        if decoded:
            return decoded
        # pylibdmtx + zbar 是重 backend, 各自 600ms+, 用 heavy_decoder_period_sec 单独节流
        # 避免每次主 QR period 都跑导致主循环掉 fps
        now = time.monotonic()
        heavy_period = max(float(self.get_float_parameter("heavy_decoder_period_sec")), 0.5)
        if now - self.last_heavy_decode_attempt_time < heavy_period:
            return decoded
        # 挑 scale 最大的 candidate, 优先 clahe_unsharp/clahe 增强变体
        best = None
        if candidates:
            def _cand_rank(c):
                method, _img, scale = c[:3]
                prio = 0
                if "clahe_unsharp" in method: prio = 3
                elif "clahe" in method: prio = 2
                elif "gray" in method: prio = 1
                return (scale, prio)
            best = max(candidates, key=_cand_rank)
        if best is None:
            return decoded
        self.last_heavy_decode_attempt_time = now
        method, image, scale, offset_x, offset_y = best[:5]
        if dmtx_decode is not None and self.get_bool_parameter("enable_pylibdmtx_recognition"):
            for code_text, points, code_type, backend in self.decode_dmtx_candidate(image, scale):
                decoded.append((code_text, self.offset_points(points, offset_x, offset_y), code_type, f"{method}:{backend}"))
            if decoded:
                return decoded
        if self.get_bool_parameter("enable_zbar_recognition"):
            for code_text, points, code_type, backend in self.decode_zbar_candidate(image, scale):
                decoded.append((code_text, self.offset_points(points, offset_x, offset_y), code_type, f"{method}:{backend}"))
        return decoded

    def accept_decoded_code(self, code_text, points, method, code_type):
        drug_info = self.parse_qr_payload(code_text, code_type)
        if drug_info is None:
            return False
        barcode_label_fields = drug_info.get("label_fields") or {}
        trace_code = (
            barcode_label_fields.get("pdi")
            or barcode_label_fields.get("trace_id")
            or barcode_label_fields.get("pc")
            or code_text
        )
        self.last_code_text = code_text
        self.last_code_type = code_type
        self.last_code_method = method
        self.last_code_points = points
        self.last_trace_code = str(trace_code or "").strip()
        self.last_trace_source = str(code_type or "barcode")
        self.last_trace_method = method
        self.last_trace_time = time.monotonic()
        self.last_barcode_label_fields = dict(barcode_label_fields)
        self.last_qr_text = code_text
        self.last_qr_time = time.monotonic()
        self.last_qr_points = points
        self.last_qr_method = method
        self.last_qr_error = ""
        self.qr_success_count += 1
        return True

    def update_qr_recognition(self, frame):
        if cv2 is None:
            self.last_qr_points = []
            return
        if not self.qr_scan_enabled_runtime:
            self.last_qr_points = []
            return
        now = time.monotonic()
        period = max(float(self.get_float_parameter("qr_recognition_period_sec")), 0.05)
        if now - self.last_qr_attempt_time < period:
            self.qr_skip_count += 1
            return
        self.last_qr_attempt_time = now
        self.qr_attempt_count += 1
        self.last_qr_error = ""
        self.last_qr_detected = False
        self.last_qr_decode_failed = False
        best_points = []
        candidates = self.build_qr_candidates(frame)
        self.last_qr_candidate_count = len(candidates)
        external_period = max(float(self.get_float_parameter("external_decoder_period_sec")), period)
        allow_external_decode = now - self.last_external_decode_attempt_time >= external_period
        if allow_external_decode:
            self.last_external_decode_attempt_time = now
        else:
            self.external_decode_skip_count += 1
        primary_scale = max(1.0, float(self.get_float_parameter("qr_scale_factor")))
        for candidate in candidates:
            method, image, scale, offset_x, offset_y = candidate[:5]
            allow_opencv_decode = scale <= 1.01 or abs(scale - primary_scale) <= 0.01
            if allow_opencv_decode and self.qr_detector is not None and self.qr_scan_enabled_runtime:
                try:
                    qr_text, points, detected = self.detect_qr_candidate(image, scale)
                except cv2.error as exc:
                    self.last_qr_error = str(exc)
                    continue
                points = self.offset_points(points, offset_x, offset_y)
                if points and not best_points:
                    best_points = points
                if detected:
                    self.last_qr_detected = True
                if qr_text and self.accept_decoded_code(qr_text, points, method, "qr"):
                    return
        if allow_external_decode:
            for code_text, points, code_type, method in self.decode_external_candidates(candidates):
                if points and not best_points:
                    best_points = points
                if self.accept_decoded_code(code_text, points, method, code_type):
                    return
        if best_points:
            self.last_qr_points = best_points
            self.last_code_points = best_points
        self.last_qr_decode_failed = self.last_qr_detected

    def qr_worker_loop(self):
        last_seen_seq = 0
        while not self.qr_worker_stop.is_set():
            frame = None
            with self.qr_worker_lock:
                if self.qr_pending_seq != last_seen_seq and self.qr_pending_frame is not None:
                    frame = self.qr_pending_frame
                    last_seen_seq = self.qr_pending_seq
            if frame is None:
                self.qr_worker_stop.wait(0.02)
                continue
            t0 = time.monotonic()
            try:
                self.update_qr_recognition(frame)
            except Exception as exc:
                self.last_qr_error = f"qr_worker: {exc}"
            self.qr_worker_busy_ms = (time.monotonic() - t0) * 1000.0
            self.qr_processed_seq = last_seen_seq

    def destroy_node(self):
        try:
            self.qr_worker_stop.set()
            if self.qr_worker_thread is not None:
                self.qr_worker_thread.join(timeout=2.0)
        except Exception:
            pass
        try:
            self.ocr_worker_stop.set()
            if self.ocr_worker_thread is not None:
                self.ocr_worker_thread.join(timeout=2.0)
        except Exception:
            pass
        return super().destroy_node()

    def build_ocr_image(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        scale = max(float(self.get_float_parameter("ocr_scale_factor")), 1.0)
        if scale > 1.01:
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        if self.qr_clahe is not None:
            gray = self.qr_clahe.apply(gray)
        return cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    def get_ocr_roi_rect(self, frame):
        return self.get_ratio_roi_rect(frame, "ocr_roi")

    def get_barcode_roi_rect(self, frame):
        return self.get_ratio_roi_rect(frame, "barcode_roi")

    def get_ratio_roi_rect(self, frame, prefix):
        if frame is None or not self.get_bool_parameter(f"{prefix}_enabled"):
            return None
        height, width = frame.shape[:2]
        if width <= 1 or height <= 1:
            return None
        x_ratio = min(max(float(self.get_float_parameter(f"{prefix}_x")), 0.0), 0.98)
        y_ratio = min(max(float(self.get_float_parameter(f"{prefix}_y")), 0.0), 0.98)
        w_ratio = min(max(float(self.get_float_parameter(f"{prefix}_w")), 0.02), 1.0)
        h_ratio = min(max(float(self.get_float_parameter(f"{prefix}_h")), 0.02), 1.0)
        x1 = int(round(width * x_ratio))
        y1 = int(round(height * y_ratio))
        x2 = int(round(width * min(x_ratio + w_ratio, 1.0)))
        y2 = int(round(height * min(y_ratio + h_ratio, 1.0)))
        if x2 - x1 < 16 or y2 - y1 < 16:
            return None
        return (x1, y1, x2, y2)

    def crop_ocr_frame(self, frame):
        rect = self.get_ocr_roi_rect(frame)
        if rect is None:
            self.last_ocr_roi_rect = []
            if frame is not None:
                height, width = frame.shape[:2]
                self.last_ocr_roi_frame_size = [int(width), int(height)]
            return frame
        x1, y1, x2, y2 = rect
        height, width = frame.shape[:2]
        self.last_ocr_roi_rect = [int(x1), int(y1), int(x2 - x1), int(y2 - y1)]
        self.last_ocr_roi_frame_size = [int(width), int(height)]
        return frame[y1:y2, x1:x2].copy()

    def update_ocr_roi_state(self, frame):
        if frame is None:
            self.last_ocr_roi_rect = []
            self.last_ocr_roi_frame_size = []
            return None
        height, width = frame.shape[:2]
        self.last_ocr_roi_frame_size = [int(width), int(height)]
        rect = self.get_ocr_roi_rect(frame)
        if rect is None:
            self.last_ocr_roi_rect = []
            return None
        x1, y1, x2, y2 = rect
        self.last_ocr_roi_rect = [int(x1), int(y1), int(x2 - x1), int(y2 - y1)]
        return rect

    def update_barcode_roi_state(self, frame):
        if frame is None:
            self.last_barcode_roi_rect = []
            self.last_barcode_roi_frame_size = []
            return None
        height, width = frame.shape[:2]
        self.last_barcode_roi_frame_size = [int(width), int(height)]
        rect = self.get_barcode_roi_rect(frame)
        if rect is None:
            self.last_barcode_roi_rect = []
            return None
        x1, y1, x2, y2 = rect
        self.last_barcode_roi_rect = [int(x1), int(y1), int(x2 - x1), int(y2 - y1)]
        return rect

    def is_meaningful_ocr_text(self, text):
        normalized = re.sub(r"\s+", "", str(text or ""))
        if len(normalized) < 2:
            return False
        if re.search(r"[\u4e00-\u9fff]", normalized):
            return True
        alnum_count = sum(1 for char in normalized if char.isalnum())
        return len(normalized) >= 4 and alnum_count / max(len(normalized), 1) >= 0.65

    def submit_ocr_frame(self, frame):
        if not self.get_bool_parameter("enable_ocr_recognition"):
            return
        with self.control_lock:
            single_requested = self.ocr_single_shot_requested
            continuous_enabled = self.ocr_scan_enabled_runtime
            if not single_requested and not continuous_enabled:
                return
            if single_requested:
                self.ocr_single_shot_requested = False
        now = time.monotonic()
        period = max(float(self.get_float_parameter("ocr_recognition_period_sec")), 0.2)
        if not single_requested and now - self.last_ocr_attempt_time < period:
            self.ocr_skip_count += 1
            return
        with self.ocr_worker_lock:
            if self.ocr_pending_frame is not None and self.ocr_pending_seq != self.ocr_processed_seq:
                self.ocr_worker_drop_count += 1
            self.ocr_pending_frame = frame.copy()
            self.ocr_pending_seq += 1
        self.last_ocr_attempt_time = now

    def ocr_worker_loop(self):
        last_seen_seq = 0
        while not self.ocr_worker_stop.is_set():
            with self.ocr_worker_lock:
                if self.ocr_pending_seq == last_seen_seq or self.ocr_pending_frame is None:
                    frame = None
                else:
                    frame = self.ocr_pending_frame
                    last_seen_seq = self.ocr_pending_seq
            if frame is None:
                time.sleep(0.05)
                continue
            t0 = time.monotonic()
            try:
                self.update_ocr_recognition(frame)
            except Exception as exc:
                self.last_ocr_error = f"ocr_worker: {exc}"
            self.ocr_worker_busy_ms = (time.monotonic() - t0) * 1000.0
            self.ocr_processed_seq = last_seen_seq

    def update_ocr_recognition(self, frame):
        if not self.get_bool_parameter("enable_ocr_recognition"):
            return
        if cv2 is None:
            self.last_ocr_error = "python3-opencv is not available"
            return
        backend = self.get_string_parameter("ocr_backend").strip().lower()
        ppocr_backends = {"ppocr", "ppocr_onnx", "ppocr-onnx", "ppocr_rknn", "ppocr-rknn", "rknn"}
        if pytesseract is None:
            if backend not in ppocr_backends:
                self.last_ocr_error = "pytesseract is not available"
                return
        now = time.monotonic()
        self.ocr_attempt_count += 1
        ocr_frame = self.crop_ocr_frame(frame)
        if backend in ppocr_backends:
            if self.update_ppocr_onnx_recognition(ocr_frame, now):
                return
            if pytesseract is None:
                return
        image = self.build_ocr_image(ocr_frame)
        language = self.get_string_parameter("ocr_language").strip()
        psm = self.get_int_parameter("ocr_psm")
        min_confidence = float(self.get_float_parameter("ocr_min_confidence"))
        timeout_sec = max(float(self.get_float_parameter("ocr_timeout_sec")), 0.2)
        config = f"--psm {psm}"
        kwargs = {
            "config": config,
            "output_type": pytesseract.Output.DICT,
            "timeout": timeout_sec,
        }
        if language:
            kwargs["lang"] = language
        try:
            data = pytesseract.image_to_data(image, **kwargs)
        except Exception as exc:
            self.last_ocr_error = f"pytesseract: {exc}"
            return
        words = []
        confidences = []
        for index, text in enumerate(data.get("text", [])):
            text = str(text).strip()
            if not text:
                continue
            try:
                confidence = float(data.get("conf", [])[index])
            except (IndexError, TypeError, ValueError):
                confidence = -1.0
            if confidence < min_confidence:
                continue
            if not self.is_meaningful_ocr_text(text):
                continue
            words.append(text)
            confidences.append(confidence)
        ocr_text = " ".join(words).strip()
        max_chars = max(int(self.get_int_parameter("ocr_max_chars")), 1)
        if ocr_text:
            self.last_ocr_text = ocr_text[:max_chars]
            self.last_ocr_confidence = sum(confidences) / max(len(confidences), 1) / 100.0
            self.last_ocr_time = now
            self.update_last_good_ocr(self.last_ocr_text, self.last_ocr_confidence, now)
            self.last_ocr_error = ""
            self.ocr_success_count += 1
        else:
            if not self.hold_last_good_ocr_if_available(now):
                self.last_ocr_error = ""

    def get_ppocr_runner(self):
        if PPOcrOnnxRunner is None:
            self.last_ocr_error = "ppocr_onnx_runner is not available"
            return None
        if self.ppocr_runner is None:
            self.ppocr_runner = PPOcrOnnxRunner(
                ppocr_root=self.get_string_parameter("ppocr_root"),
                det_model_path=self.get_string_parameter("ppocr_det_model_path"),
                rec_model_path=self.get_string_parameter("ppocr_rec_model_path"),
                target="rk3588",
                max_boxes=self.get_int_parameter("ppocr_max_boxes"),
            )
        return self.ppocr_runner

    def update_ppocr_onnx_recognition(self, frame, now):
        backend = self.get_string_parameter("ocr_backend").strip().lower()
        if backend in {"ppocr_rknn", "ppocr-rknn", "rknn"} and self.get_bool_parameter("ocr_isolate_ppocr"):
            return self.update_ppocr_isolated_recognition(frame, now)
        runner = self.get_ppocr_runner()
        if runner is None:
            return False
        try:
            result = runner.run(frame)
        except Exception as exc:
            self.last_ocr_error = f"{self.get_ocr_backend_name()}: {type(exc).__name__}: {exc}"
            return False
        self.ppocr_backend_loaded = True
        self.ocr_worker_busy_ms = result.elapsed_ms
        if result.text:
            self.last_ocr_text = result.text[: max(int(self.get_int_parameter("ocr_max_chars")), 1)]
            self.last_ocr_confidence = float(result.confidence)
            self.last_ocr_time = now
            self.update_last_good_ocr(self.last_ocr_text, self.last_ocr_confidence, now)
            self.last_ocr_error = ""
            self.ocr_success_count += 1
        else:
            held = self.hold_last_good_ocr_if_available(now)
            suffix = "held_last_good" if held else "no_cache"
            self.last_ocr_error = f"{self.get_ocr_backend_name()}: no text, boxes={len(result.boxes)}, elapsed_ms={result.elapsed_ms:.1f}, {suffix}"
        return True

    def update_ppocr_isolated_recognition(self, frame, now):
        if cv2 is None:
            self.last_ocr_error = "isolated ppocr: python3-opencv is not available"
            return False
        temp_path = ""
        try:
            with tempfile.NamedTemporaryFile(prefix="medicine_ocr_", suffix=".jpg", delete=False) as temp_file:
                temp_path = temp_file.name
            if not cv2.imwrite(temp_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95]):
                self.last_ocr_error = "isolated ppocr: failed to write temp image"
                return False
            timeout_sec = max(float(self.get_float_parameter("ocr_isolated_timeout_sec")), 0.5)
            command = [
                sys.executable,
                "-m",
                "medicine_vision_detector.ppocr_isolated_runner",
                "--image",
                temp_path,
                "--ppocr-root",
                self.get_string_parameter("ppocr_root"),
                "--det-model",
                self.get_string_parameter("ppocr_det_model_path"),
                "--rec-model",
                self.get_string_parameter("ppocr_rec_model_path"),
                "--target",
                "rk3588",
                "--max-boxes",
                str(self.get_int_parameter("ppocr_max_boxes")),
            ]
            start = time.monotonic()
            completed = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_sec,
            )
            elapsed_ms = (time.monotonic() - start) * 1000.0
        except subprocess.TimeoutExpired:
            self.last_ocr_error = f"isolated ppocr: timeout after {self.get_float_parameter('ocr_isolated_timeout_sec'):.1f}s"
            return False
        except Exception as exc:
            self.last_ocr_error = f"isolated ppocr: {type(exc).__name__}: {exc}"
            return False
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip().splitlines()
            tail = stderr[-1] if stderr else ""
            self.last_ocr_error = f"isolated ppocr exited {completed.returncode}: {tail}".strip()
            return False
        try:
            payload = json.loads((completed.stdout or "").strip().splitlines()[-1])
        except Exception as exc:
            self.last_ocr_error = f"isolated ppocr invalid json: {exc}"
            return False
        if not payload.get("ok", False):
            self.last_ocr_error = f"isolated ppocr: {payload.get('error', 'unknown error')}"
            return False
        self.ppocr_backend_loaded = True
        self.ocr_worker_busy_ms = float(payload.get("elapsed_ms") or elapsed_ms)
        text = str(payload.get("text") or "").strip()
        confidence = float(payload.get("confidence") or 0.0)
        boxes = payload.get("boxes") if isinstance(payload.get("boxes"), list) else []
        if text:
            self.last_ocr_text = text[: max(int(self.get_int_parameter("ocr_max_chars")), 1)]
            self.last_ocr_confidence = confidence
            self.last_ocr_time = now
            self.update_last_good_ocr(self.last_ocr_text, self.last_ocr_confidence, now)
            self.last_ocr_error = ""
            self.ocr_success_count += 1
        else:
            held = self.hold_last_good_ocr_if_available(now)
            suffix = "held_last_good" if held else "no_cache"
            self.last_ocr_error = f"isolated {self.get_ocr_backend_name()}: no text, boxes={len(boxes)}, elapsed_ms={self.ocr_worker_busy_ms:.1f}, {suffix}"
        return True

    def normalize_stability_text(self, value):
        text = str(value or "").strip().lower()
        text = re.sub(r"\s+", "", text)
        text = re.sub(r"[^\w\u4e00-\u9fff]+", "", text)
        return text

    def build_recognition_stability_signature(self, drug_info, label_fields=None):
        label_fields = label_fields or {}
        channel = str(drug_info.get("recognition_channel") or "").strip()
        trace_code = str(
            drug_info.get("trace_code")
            or label_fields.get("pdi")
            or label_fields.get("trace_id")
            or drug_info.get("raw_code_text")
            or ""
        ).strip()
        product_code = str(
            label_fields.get("product_code")
            or label_fields.get("product_id")
            or drug_info.get("code_text")
            or ""
        ).strip()
        drug_name = self.normalize_stability_text(drug_info.get("drug_name"))
        source = str(drug_info.get("recognition_source") or "").strip()
        if trace_code:
            return f"code:{trace_code}", trace_code, product_code, drug_name
        if product_code:
            return f"product:{product_code}", trace_code, product_code, drug_name
        if channel == "ocr" and drug_name:
            return f"ocr:{drug_name}", trace_code, product_code, drug_name
        if source and drug_name:
            return f"source:{source}:{drug_name}", trace_code, product_code, drug_name
        return "", trace_code, product_code, drug_name

    def update_recognition_stability(self, drug_info, label_fields=None):
        now = time.monotonic()
        required = max(int(self.get_int_parameter("recognition_stability_min_count")), 1)
        window_size = max(int(self.get_int_parameter("recognition_stability_window_size")), required)
        ttl_sec = max(float(self.get_float_parameter("recognition_stability_ttl_sec")), 1.0)
        signature, trace_code, product_code, drug_name = self.build_recognition_stability_signature(drug_info, label_fields)
        history = [item for item in self.recognition_stability_history if now - item.get("time", 0.0) <= ttl_sec]
        if signature:
            history.append({
                "signature": signature,
                "time": now,
                "drug_name": str(drug_info.get("drug_name") or ""),
                "recognition_channel": str(drug_info.get("recognition_channel") or ""),
                "trace_code": trace_code,
                "product_code": product_code,
                "confidence": float(drug_info.get("confidence", 0.0) or 0.0),
            })
        if len(history) > window_size:
            history = history[-window_size:]
        self.recognition_stability_history = history
        count = sum(1 for item in history if item.get("signature") == signature) if signature else 0
        stable = bool(signature and count >= required)
        first_match_time = None
        for item in history:
            if item.get("signature") == signature:
                first_match_time = item.get("time", now)
                break
        age_sec = max(0.0, now - first_match_time) if first_match_time is not None else -1.0
        self.last_recognition_stability = {
            "stable": stable,
            "count": int(count),
            "required": int(required),
            "signature": signature,
            "drug_name": str(drug_info.get("drug_name") or ""),
            "recognition_channel": str(drug_info.get("recognition_channel") or ""),
            "trace_code": trace_code,
            "product_code": product_code,
            "confidence": float(drug_info.get("confidence", 0.0) or 0.0),
            "age_sec": float(age_sec),
        }
        return dict(self.last_recognition_stability)

    def get_current_drug_info(self):
        if self.detected_drug_info is not None:
            return dict(self.detected_drug_info)
        ocr_drug_info = self.build_ocr_drug_info()
        if ocr_drug_info is not None:
            return ocr_drug_info
        return {
            "drug_id": self.get_string_parameter("drug_id"),
            "drug_name": self.get_string_parameter("drug_name"),
            "drug_type": self.get_string_parameter("drug_type"),
            "confidence": float(self.get_float_parameter("confidence")),
            "loaded": bool(self.get_bool_parameter("loaded")),
            "recognition_source": "",
            "label_fields": {},
            "raw_code_text": "",
            "code_type": "",
            "code_method": "",
        }

    def open_camera(self):
        if cv2 is None:
            self.camera_ok = False
            self.last_camera_error = "python3-opencv is not available"
            return False

        now = time.monotonic()
        reconnect_period = max(self.get_float_parameter("camera_reconnect_period_sec"), 0.5)
        if now - self.last_camera_open_attempt < reconnect_period:
            return False
        self.last_camera_open_attempt = now

        camera_device = self.get_string_parameter("camera_device")
        camera_target = int(camera_device) if camera_device.isdigit() else camera_device
        capture = cv2.VideoCapture(camera_target, cv2.CAP_V4L2)
        width = self.get_int_parameter("camera_width")
        height = self.get_int_parameter("camera_height")
        fps = self.get_int_parameter("camera_fps")
        fourcc = self.get_string_parameter("camera_fourcc")

        if fourcc:
            normalized_fourcc = fourcc[:4].ljust(4)
            capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*normalized_fourcc))
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        capture.set(cv2.CAP_PROP_FPS, fps)

        if not capture.isOpened():
            capture.release()
            self.capture = None
            self.camera_ok = False
            self.last_camera_error = f"failed to open {camera_device}"
            self.get_logger().warn(self.last_camera_error)
            return False

        self.capture = capture
        self.last_camera_error = ""
        self.get_logger().info(
            f"Camera opened: device={camera_device}, width={width}, height={height}, fps={fps}, fourcc={fourcc}"
        )
        return True

    def close_camera(self):
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        self.camera_ok = False

    def encode_preview_frame(self, frame):
        if cv2 is None:
            return
        if not self.get_bool_parameter("enable_preview_server"):
            return
        if not self.has_recent_preview_client():
            return
        encode_period = max(self.get_float_parameter("preview_encode_period_sec"), 0.0)
        now = time.monotonic()
        if encode_period > 0.0 and now - self.last_preview_encode_time < encode_period:
            return
        self.last_preview_encode_time = now
        preview = frame
        ocr_roi_rect = self.update_ocr_roi_state(frame)
        barcode_roi_rect = self.update_barcode_roi_state(frame)
        if self.get_bool_parameter("preview_draw_overlay"):
            preview = frame.copy()
            input_mode = self.get_string_parameter("input_mode").lower()
            drug_info = self.get_current_drug_info()
            source = self.build_drug_source(input_mode, drug_info)
            drug_name = drug_info["drug_name"]
            confidence = drug_info["confidence"]
            loaded = drug_info["loaded"]
            if len(self.last_qr_points) >= 4:
                for index, point in enumerate(self.last_qr_points):
                    next_point = self.last_qr_points[(index + 1) % len(self.last_qr_points)]
                    cv2.line(preview, point, next_point, (0, 255, 255), 3)
            if ocr_roi_rect is not None:
                x1, y1, x2, y2 = ocr_roi_rect
                cv2.rectangle(preview, (x1, y1), (x2, y2), (64, 255, 64), 2)
                cv2.putText(
                    preview,
                    "OCR ROI",
                    (x1, max(y1 - 8, 16)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (64, 255, 64),
                    2,
                    cv2.LINE_AA,
                )
            if barcode_roi_rect is not None:
                x1, y1, x2, y2 = barcode_roi_rect
                cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 224, 255), 2)
                cv2.putText(
                    preview,
                    "BARCODE ROI",
                    (x1, max(y1 - 8, 16)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (0, 224, 255),
                    2,
                    cv2.LINE_AA,
                )
            if self.get_bool_parameter("yolo_draw_overlay"):
                for detection in self.yolo_last_detections:
                    bbox = detection.get("bbox_xyxy", [])
                    if len(bbox) != 4:
                        continue
                    x1, y1, x2, y2 = [int(round(value)) for value in bbox]
                    label = str(detection.get("label", "object"))
                    score = float(detection.get("confidence", 0.0))
                    cv2.rectangle(preview, (x1, y1), (x2, y2), (255, 128, 0), 2)
                    cv2.putText(
                        preview,
                        f"{label} {score:.2f}",
                        (max(x1, 0), max(y1 - 8, 16)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (255, 128, 0),
                        2,
                        cv2.LINE_AA,
                    )
            cv2.rectangle(preview, (0, 0), (preview.shape[1], 134), (0, 0, 0), -1)
            cv2.putText(
                preview,
                f"{drug_name} confidence={confidence:.2f} loaded={loaded}",
                (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                preview,
                f"{source} frame={self.frame_count}",
                (12, 58),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
            cv2.putText(
                preview,
                f"code={self.last_code_text or '-'} type={self.last_code_type or '-'} method={self.last_code_method or '-'}",
                (12, 88),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 255),
                1,
                cv2.LINE_AA,
            )
            if self.get_bool_parameter("enable_yolo_rknn_detection"):
                cv2.putText(
                    preview,
                    f"npu_yolo={self.yolo_status} det={self.yolo_last_detection_count} infer={self.yolo_last_inference_ms:.1f}ms",
                    (12, 118),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 128, 0),
                    1,
                    cv2.LINE_AA,
                )
        if self.get_bool_parameter("preview_sharpen_enabled"):
            amount = max(0.0, min(self.get_float_parameter("preview_sharpen_amount"), 1.5))
            sigma = max(0.1, min(self.get_float_parameter("preview_sharpen_sigma"), 5.0))
            if amount > 0.0:
                if preview is frame:
                    preview = frame.copy()
                blurred = cv2.GaussianBlur(preview, (0, 0), sigma)
                preview = cv2.addWeighted(preview, 1.0 + amount, blurred, -amount, 0)
        quality = max(10, min(self.get_int_parameter("preview_quality"), 100))
        ok, encoded = cv2.imencode(".jpg", preview, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        if ok:
            with self.frame_lock:
                self.latest_frame_jpeg = encoded.tobytes()

    def get_latest_frame_jpeg(self):
        with self.frame_lock:
            return self.latest_frame_jpeg

    def mark_preview_client_active(self, count_request=False):
        with self.preview_client_lock:
            if count_request:
                self.preview_client_request_count += 1
            self.preview_last_client_time = time.monotonic()

    def has_recent_preview_client(self):
        timeout = max(self.get_float_parameter("preview_idle_timeout_sec"), 0.0)
        with self.preview_client_lock:
            if self.preview_client_request_count <= 0:
                return False
            if timeout <= 0.0:
                return True
            return time.monotonic() - self.preview_last_client_time <= timeout

    def get_preview_client_status(self):
        with self.preview_client_lock:
            last_client_time = self.preview_last_client_time
            client_request_count = self.preview_client_request_count
        age_sec = 0.0
        if last_client_time > 0.0:
            age_sec = time.monotonic() - last_client_time
        return client_request_count, age_sec, self.has_recent_preview_client()

    def start_preview_server(self):
        host = self.get_string_parameter("preview_host")
        port = self.get_int_parameter("preview_port")
        handler = self.make_preview_handler()
        try:
            self.preview_server = ThreadingHTTPServer((host, port), handler)
        except OSError as exc:
            self.get_logger().warn(f"Could not start camera preview server on {host}:{port}: {exc}")
            return
        self.preview_server_thread = threading.Thread(target=self.preview_server.serve_forever, daemon=True)
        self.preview_server_thread.start()
        self.get_logger().info(f"Camera preview started: http://localhost:{port}/")

    def stop_preview_server(self):
        if self.preview_server is not None:
            self.preview_server.shutdown()
            self.preview_server.server_close()
            self.preview_server = None

    def make_preview_handler(self):
        detector = self

        class PreviewRequestHandler(BaseHTTPRequestHandler):
            def log_message(self, format_text, *args):
                return

            def do_GET(self):
                path = urlparse(self.path).path
                if path in {"/", "/index.html"}:
                    self.write_html()
                    return
                if path == "/snapshot.jpg":
                    self.write_snapshot()
                    return
                if path == "/stream.mjpg":
                    self.write_stream()
                    return
                self.send_response(404)
                self.end_headers()

            def write_html(self):
                html = b'<!doctype html><html><head><meta charset="utf-8"><title>Camera Preview</title></head><body style="margin:0;background:#111;"><img src="/stream.mjpg" style="width:100%;height:auto;display:block;"></body></html>'
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html)))
                self.end_headers()
                self.wfile.write(html)

            def write_snapshot(self):
                detector.mark_preview_client_active(count_request=True)
                frame = detector.get_latest_frame_jpeg()
                if frame is None:
                    self.send_response(503)
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(frame)))
                self.end_headers()
                self.wfile.write(frame)

            def write_stream(self):
                detector.mark_preview_client_active(count_request=True)
                self.send_response(200)
                self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Pragma", "no-cache")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                while True:
                    detector.mark_preview_client_active()
                    frame = detector.get_latest_frame_jpeg()
                    if frame is None:
                        time.sleep(0.2)
                        continue
                    try:
                        self.wfile.write(b"--frame\r\n")
                        self.wfile.write(b"Content-Type: image/jpeg\r\n")
                        self.wfile.write(f"Content-Length: {len(frame)}\r\n\r\n".encode("ascii"))
                        self.wfile.write(frame)
                        self.wfile.write(b"\r\n")
                        self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError):
                        break
                    stream_period = max(detector.get_float_parameter("preview_stream_period_sec"), 0.005)
                    time.sleep(stream_period)

        return PreviewRequestHandler

    def update_camera_state(self):
        input_mode = self.get_string_parameter("input_mode").lower()
        if input_mode != "camera":
            if self.capture is not None:
                self.close_camera()
            self.camera_ok = False
            self.last_camera_error = ""
            self.frame_timestamps = []
            self.camera_actual_fps = 0.0
            with self.frame_lock:
                self.latest_frame_jpeg = None
            return

        if self.capture is None and not self.open_camera():
            return

        ok, frame = self.capture.read()
        if not ok or frame is None:
            self.close_camera()
            self.last_camera_error = "failed to read camera frame"
            self.get_logger().warn(self.last_camera_error)
            return

        self.camera_ok = True
        self.last_camera_error = ""
        self.frame_count += 1
        self.frame_height, self.frame_width = frame.shape[:2]
        now = time.monotonic()
        self.frame_timestamps.append(now)
        cutoff = now - 2.0
        self.frame_timestamps = [stamp for stamp in self.frame_timestamps if stamp >= cutoff]
        if len(self.frame_timestamps) >= 2:
            elapsed = self.frame_timestamps[-1] - self.frame_timestamps[0]
            self.camera_actual_fps = (len(self.frame_timestamps) - 1) / elapsed if elapsed > 0 else 0.0
        else:
            self.camera_actual_fps = 0.0
        self.update_ocr_roi_state(frame)
        self.update_barcode_roi_state(frame)
        # QR pipeline 异步: 仅在手动开启时喂帧, 避免空闲时占用 CPU
        if self.qr_scan_enabled_runtime:
            with self.qr_worker_lock:
                if self.qr_pending_frame is not None and self.qr_pending_seq != self.qr_processed_seq:
                    self.qr_worker_drop_count += 1  # worker 还没消费旧帧, 直接丢, 永远扫"最新"
                self.qr_pending_frame = frame
                self.qr_pending_seq += 1
        self.update_yolo_detection(frame)
        self.encode_preview_frame(frame)
        self.submit_ocr_frame(frame)

    def build_source(self, input_mode):
        if input_mode == "camera":
            camera_device = self.get_string_parameter("camera_device")
            if self.camera_ok:
                return f"camera:{camera_device}"
            return f"camera_waiting:{camera_device}"
        return self.get_string_parameter("source")

    def build_drug_source(self, input_mode, drug_info):
        base_source = self.build_source(input_mode)
        recognition_source = drug_info.get("recognition_source") or ""
        if recognition_source:
            return f"{recognition_source}@{base_source}"
        return base_source

    def publish_drug_info(self):
        input_mode = self.get_string_parameter("input_mode").lower()
        drug_info = self.get_current_drug_info()

        msg = DrugInfo()
        msg.drug_id = drug_info["drug_id"]
        msg.drug_name = drug_info["drug_name"]
        msg.drug_type = drug_info["drug_type"]
        msg.confidence = float(drug_info["confidence"])
        msg.loaded = bool(drug_info["loaded"])
        msg.source = self.build_drug_source(input_mode, drug_info)
        msg.stamp = self.get_clock().now().to_msg()
        self.publisher.publish(msg)
        qr_age_sec = 0.0
        if self.last_qr_time > 0.0:
            qr_age_sec = time.monotonic() - self.last_qr_time
        ocr_age_sec = 0.0
        if self.last_ocr_time > 0.0:
            ocr_age_sec = time.monotonic() - self.last_ocr_time
        ocr_extracted_fields = self.extract_ocr_fields(self.last_ocr_text)
        if float(self.last_ocr_confidence or 0.0) < 0.45:
            ocr_extracted_fields = dict(ocr_extracted_fields)
            ocr_extracted_fields["drug_name"] = ""
        label_fields = dict(drug_info.get("label_fields") or {})
        barcode_label_fields = dict(self.last_barcode_label_fields or {})
        for key, value in barcode_label_fields.items():
            if value:
                label_fields[key] = value
        trace_code = self.last_trace_code or label_fields.get("pdi", "")
        stability = self.update_recognition_stability(drug_info, label_fields)

        preview_request_count, preview_client_age_sec, preview_encoding_active = self.get_preview_client_status()

        status = {
            "drug_id": msg.drug_id,
            "drug_name": msg.drug_name,
            "drug_type": msg.drug_type,
            "confidence": msg.confidence,
            "loaded": msg.loaded,
            "source": msg.source,
            "recognition_channel": drug_info.get("recognition_channel") or "",
            "needs_review": bool(drug_info.get("needs_review", False)),
            "recognition_stable": bool(stability.get("stable", False)),
            "recognition_stable_count": int(stability.get("count", 0) or 0),
            "recognition_stable_required": int(stability.get("required", 0) or 0),
            "recognition_stable_signature": stability.get("signature", ""),
            "stable_drug_name": stability.get("drug_name", ""),
            "stable_recognition_channel": stability.get("recognition_channel", ""),
            "stable_trace_code": stability.get("trace_code", ""),
            "stable_product_code": stability.get("product_code", ""),
            "stable_confidence": float(stability.get("confidence", 0.0) or 0.0),
            "stable_age_sec": float(stability.get("age_sec", -1.0) or -1.0),
            "ocr_match_text": drug_info.get("ocr_match_text") or "",
            "ocr_extracted_fields": drug_info.get("ocr_extracted_fields") or ocr_extracted_fields,
            "ocr_drug_name": (drug_info.get("ocr_extracted_fields") or ocr_extracted_fields).get("drug_name", ""),
            "ocr_spec": (drug_info.get("ocr_extracted_fields") or ocr_extracted_fields).get("spec", ""),
            "ocr_manufacturer": (drug_info.get("ocr_extracted_fields") or ocr_extracted_fields).get("manufacturer", ""),
            "ocr_approval_no": (drug_info.get("ocr_extracted_fields") or ocr_extracted_fields).get("approval_no", ""),
            "input_mode": input_mode,
            "camera_device": self.get_string_parameter("camera_device"),
            "camera_ok": self.camera_ok,
            "frame_count": self.frame_count,
            "frame_width": self.frame_width,
            "frame_height": self.frame_height,
            "camera_fps": self.get_int_parameter("camera_fps"),
            "camera_actual_fps": self.camera_actual_fps,
            "camera_read_period_sec": self.get_float_parameter("camera_read_period_sec"),
            "last_camera_error": self.last_camera_error,
            "preview_quality": self.get_int_parameter("preview_quality"),
            "preview_draw_overlay": self.get_bool_parameter("preview_draw_overlay"),
            "preview_sharpen_enabled": self.get_bool_parameter("preview_sharpen_enabled"),
            "preview_sharpen_amount": self.get_float_parameter("preview_sharpen_amount"),
            "preview_sharpen_sigma": self.get_float_parameter("preview_sharpen_sigma"),
            "preview_stream_period_sec": self.get_float_parameter("preview_stream_period_sec"),
            "preview_encode_period_sec": self.get_float_parameter("preview_encode_period_sec"),
            "preview_idle_timeout_sec": self.get_float_parameter("preview_idle_timeout_sec"),
            "preview_client_request_count": preview_request_count,
            "preview_client_age_sec": preview_client_age_sec,
            "preview_encoding_active": preview_encoding_active,
            "vision_control_topic": self.control_topic,
            "vision_control_message": self.vision_control_message,
            "qr_enabled": self.qr_scan_enabled_runtime,
            "qr_worker_busy_ms": self.qr_worker_busy_ms,
            "qr_worker_drop_count": self.qr_worker_drop_count,
            "qr_worker_processed_seq": self.qr_processed_seq,
            "qr_worker_pending_seq": self.qr_pending_seq,
            "qr_text": self.last_qr_text,
            "qr_age_sec": qr_age_sec,
            "qr_points": self.last_qr_points,
            "qr_method": self.last_qr_method,
            "qr_detected": self.last_qr_detected,
            "qr_decode_failed": self.last_qr_decode_failed,
            "code_text": self.last_code_text,
            "code_type": self.last_code_type,
            "code_method": self.last_code_method,
            "code_points": self.last_code_points,
            "raw_code_text": drug_info.get("raw_code_text") or self.last_code_text,
            "trace_code": trace_code,
            "trace_source": self.last_trace_source,
            "trace_method": self.last_trace_method,
            "label_fields": label_fields,
            "label_order_no": label_fields.get("on", ""),
            "label_product_code": label_fields.get("pc", ""),
            "label_product_model": label_fields.get("pm", ""),
            "label_quantity": label_fields.get("qty", ""),
            "label_material_code": label_fields.get("mc", ""),
            "label_control_code": label_fields.get("cc", ""),
            "label_trace_id": trace_code,
            "label_holder": label_fields.get("hp", ""),
            "datamatrix_enabled": self.get_bool_parameter("enable_datamatrix_recognition"),
            "zxingcpp_enabled": self.get_bool_parameter("enable_zxingcpp_recognition"),
            "pylibdmtx_enabled": self.get_bool_parameter("enable_pylibdmtx_recognition"),
            "barcode_enhancement_enabled": self.get_bool_parameter("enable_barcode_enhancement"),
            "barcode_scale_x": self.get_float_parameter("barcode_scale_x"),
            "barcode_scale_y": self.get_float_parameter("barcode_scale_y"),
            "barcode_roi_enabled": self.get_bool_parameter("barcode_roi_enabled"),
            "barcode_roi_rect": self.last_barcode_roi_rect,
            "barcode_roi_frame_size": self.last_barcode_roi_frame_size,
            "decoder_backends": self.get_decoder_backend_names(),
            "qr_attempt_count": self.qr_attempt_count,
            "qr_skip_count": self.qr_skip_count,
            "qr_success_count": self.qr_success_count,
            "qr_candidate_count": self.last_qr_candidate_count,
            "qr_recognition_period_sec": self.get_float_parameter("qr_recognition_period_sec"),
            "external_decoder_period_sec": self.get_float_parameter("external_decoder_period_sec"),
            "external_decoder_timeout_sec": self.get_float_parameter("external_decoder_timeout_sec"),
            "external_decode_attempt_count": self.external_decode_attempt_count,
            "external_decode_skip_count": self.external_decode_skip_count,
            "external_decode_busy_count": self.external_decode_busy_count,
            "external_decode_complete_count": self.external_decode_complete_count,
            "external_decode_timeout_count": self.external_decode_timeout_count,
            "isolated_zxingcpp_enabled": self.get_bool_parameter("enable_isolated_zxingcpp_recognition"),
            "opencv_curved_qr_enabled": self.get_bool_parameter("enable_opencv_curved_qr_recognition"),
            "qr_fast_mode": self.get_bool_parameter("qr_fast_mode"),
            "qr_scale_factor": self.get_float_parameter("qr_scale_factor"),
            "qr_extra_scale_factors": self.get_string_parameter("qr_extra_scale_factors"),
            "recognized_code_hold_sec": self.get_float_parameter("recognized_code_hold_sec"),
            "ocr_enabled": self.get_bool_parameter("enable_ocr_recognition"),
            "ocr_runtime_enabled": self.ocr_scan_enabled_runtime,
            "ocr_single_shot_pending": self.ocr_single_shot_requested,
            "ocr_available": pytesseract is not None,
            "ocr_backend": self.get_ocr_backend_name(),
            "ocr_selected_backend": self.get_string_parameter("ocr_backend"),
            "ppocr_backend_loaded": self.ppocr_backend_loaded,
            "ocr_text": self.last_ocr_text,
            "ocr_confidence": self.last_ocr_confidence,
            "ocr_held": self.last_ocr_held,
            "ocr_hold_last_good_sec": self.get_float_parameter("ocr_hold_last_good_sec"),
            "ocr_last_good_age_sec": (time.monotonic() - self.last_good_ocr_time) if self.last_good_ocr_time > 0.0 else -1.0,
            "ocr_language": self.get_string_parameter("ocr_language"),
            "ocr_age_sec": ocr_age_sec,
            "ocr_error": self.last_ocr_error,
            "ocr_attempt_count": self.ocr_attempt_count,
            "ocr_skip_count": self.ocr_skip_count,
            "ocr_success_count": self.ocr_success_count,
            "ocr_worker_drop_count": self.ocr_worker_drop_count,
            "ocr_worker_busy_ms": self.ocr_worker_busy_ms,
            "ocr_recognition_period_sec": self.get_float_parameter("ocr_recognition_period_sec"),
            "ocr_min_confidence": self.get_float_parameter("ocr_min_confidence"),
            "ocr_timeout_sec": self.get_float_parameter("ocr_timeout_sec"),
            "ocr_roi_enabled": self.get_bool_parameter("ocr_roi_enabled"),
            "ocr_roi_rect": self.last_ocr_roi_rect,
            "ocr_roi_frame_size": self.last_ocr_roi_frame_size,
            "yolo_rknn_enabled": self.get_bool_parameter("enable_yolo_rknn_detection"),
            "yolo_rknn_status": self.yolo_status,
            "yolo_rknn_message": self.yolo_message,
            "yolo_model_path": self.get_string_parameter("yolo_model_path"),
            "yolo_model_loaded": self.yolo_model_loaded,
            "yolo_inference_ms": self.yolo_last_inference_ms,
            "yolo_detection_count": self.yolo_last_detection_count,
            "yolo_detections": self.yolo_last_detections,
            "yolo_output_shapes": self.yolo_last_output_shapes,
            "yolo_attempt_count": self.yolo_attempt_count,
            "yolo_skip_count": self.yolo_skip_count,
            "yolo_success_count": self.yolo_success_count,
            "yolo_error": self.yolo_error,
            "recognition_source": drug_info.get("recognition_source") or "",
            "last_qr_error": self.last_qr_error,
        }
        status_msg = String()
        status_msg.data = json.dumps(status, ensure_ascii=False)
        self.status_publisher.publish(status_msg)

    def destroy_node(self):
        self.cleanup_isolated_zxing_process()
        self.release_yolo_runtime()
        self.stop_preview_server()
        self.close_camera()
        super().destroy_node()


def main():
    rclpy.init()
    node = DrugInfoDetector()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--decode-zxing-files":
        raise SystemExit(decode_zxing_files(sys.argv[2]))
    main()
