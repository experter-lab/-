import copy
import io
import json
import math
import os
import re
import subprocess
import threading
import time
import tempfile
import urllib.error
import urllib.request
from collections import deque
from http.server import ThreadingHTTPServer

import rclpy
from ament_index_python.packages import get_package_share_directory
from rclpy.duration import Duration
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
import yaml

try:
    from PIL import Image, ImageFilter, ImageOps
except Exception:
    Image = None
    ImageFilter = None
    ImageOps = None

from medicine_interfaces.msg import DeliveryState, DrugInfo
from medicine_interfaces.srv import (
    CancelDeliveryTask,
    CreateDeliveryTask,
    VerifyDeliveryTask,
)
from std_msgs.msg import String
from std_srvs.srv import SetBool

GPU_DEVFREQ_PATH = "/sys/class/devfreq/fb000000.gpu"
NPU_DEVFREQ_PATH = "/sys/class/devfreq/fdab0000.npu"


def _read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read().strip()
    except OSError:
        return ""


def _read_int(path):
    text = _read_text(path)
    try:
        return int(text)
    except (TypeError, ValueError):
        return 0


def _parse_devfreq_load(text):
    if not text:
        return 0.0
    raw = text.split("@", 1)[0].strip()
    try:
        return max(0.0, min(100.0, float(raw)))
    except ValueError:
        return 0.0

try:
    from sensor_msgs.msg import LaserScan
except ImportError:
    LaserScan = None

try:
    import tf2_ros
except ImportError:
    tf2_ros = None

try:
    from .delivery_database import DeliveryDatabase

    DB_AVAILABLE = True
except ImportError:
    try:
        from delivery_database import DeliveryDatabase

        DB_AVAILABLE = True
    except ImportError:
        DB_AVAILABLE = False
        print("Warning: delivery_database not available")


try:
    from .dashboard_assets import PATIENT_MEDICATION_ORDERS
except ImportError:
    from dashboard_assets import PATIENT_MEDICATION_ORDERS

try:
    from .dashboard_http import create_dashboard_handler
except ImportError:
    from dashboard_http import create_dashboard_handler

try:
    from .patient_http import create_patient_handler
except ImportError:
    from patient_http import create_patient_handler

try:
    from .vision_webrtc import VisionWebRTCService
except ImportError:
    from vision_webrtc import VisionWebRTCService

try:
    from .patient_state_store import PatientStateStore

    PATIENT_STORE_AVAILABLE = True
except ImportError:
    try:
        from patient_state_store import PatientStateStore

        PATIENT_STORE_AVAILABLE = True
    except ImportError:
        PATIENT_STORE_AVAILABLE = False
        print("Warning: patient_state_store not available; IM data will not persist")

try:
    from .dashboard_navigation import (
        build_navigation_map_payload,
        list_navigation_maps,
        resolve_navigation_map_asset,
    )
except ImportError:
    from dashboard_navigation import (
        build_navigation_map_payload,
        list_navigation_maps,
        resolve_navigation_map_asset,
    )

try:
    from .dashboard_delivery_batch import DeliveryBatchMixin
except ImportError:
    from dashboard_delivery_batch import DeliveryBatchMixin

try:
    from .dashboard_reports import (
        build_delivery_batch_report as build_report,
        build_delivery_batch_report_csv as build_report_csv,
    )
except ImportError:
    from dashboard_reports import (
        build_delivery_batch_report as build_report,
        build_delivery_batch_report_csv as build_report_csv,
    )



class MedicineWebDashboard(DeliveryBatchMixin, Node):
    def __init__(self):
        super().__init__("medicine_web_dashboard")
        default_stations_file = (
            get_package_share_directory("medicine_task_manager")
            + "/config/stations.yaml"
        )
        self.declare_parameter("host", "0.0.0.0")
        self.declare_parameter("port", 8080)
        self.declare_parameter("stations_file", default_stations_file)
        self.declare_parameter("service_timeout_sec", 5.0)
        self.declare_parameter("scan_max_age_sec", 8.0)
        self.declare_parameter("chassis_status_topic", "/medicine/chassis_status")
        self.declare_parameter("chassis_estop_service", "/chassis_bridge/set_emergency_stop")
        self.declare_parameter("scan_topic", "/scan")
        self.declare_parameter("enable_scan_listener", False)
        self.declare_parameter("scan_status_period_sec", 1.0)
        self.declare_parameter("navigation_map_directory", "/mnt/sdcard/medicine_robot_data/maps")
        self.declare_parameter("navigation_map_frame", "map")
        self.declare_parameter("navigation_base_frame", "base_link")
        self.declare_parameter("enable_tf_listener", False)
        self.declare_parameter(
            "api_write_token", os.environ.get("MEDICINE_DASHBOARD_API_TOKEN", "")
        )
        self.declare_parameter("max_request_body_bytes", 262144)
        self.declare_parameter(
            "health_event_file",
            "/mnt/sdcard/medicine_robot_data/health_events.json",
        )
        self.declare_parameter(
            "delivery_batch_state_file",
            os.path.expanduser(
                "~/.local/share/medicine_robot/delivery_batch_state.json"
            ),
        )
        self.declare_parameter(
            "pending_delivery_batch_file",
            os.path.expanduser(
                "~/.local/share/medicine_robot/pending_delivery_batch.json"
            ),
        )
        self.declare_parameter(
            "delivery_safety_self_test_file",
            os.path.expanduser(
                "~/.local/share/medicine_robot/delivery_safety_self_test.json"
            ),
        )

        # 病人侧 web (patient_web) 第二个 HTTP server, 与现有 dashboard 共用 host
        self.declare_parameter("patient_port", 8081)
        self.declare_parameter(
            "patient_web_dist_dir",
            "/mnt/sdcard/medicine_robot_data/patient_web/dist",
        )
        self.declare_parameter("patient_call_topic", "/medicine/patient_call")
        self.declare_parameter("patient_message_topic", "/medicine/patient_message")
        self.declare_parameter("voice_text_topic", "/medicine/voice_text")
        self.declare_parameter("asr_control_topic", "/medicine/asr_control")
        self.declare_parameter("patient_voice_context_topic", "/medicine/patient_voice_context")
        self.declare_parameter("vision_control_topic", "/medicine/vision_control")
        self.declare_parameter("patient_message_max", 200)
        self.declare_parameter("patient_history_days", 7)
        self.declare_parameter(
            "patient_access_secret",
            os.environ.get("MEDICINE_PATIENT_ACCESS_SECRET", ""),
        )
        # 病人 IM/override 持久化文件 (断电恢复用), 空串=禁用
        self.declare_parameter(
            "patient_state_db",
            "/mnt/sdcard/medicine_robot_data/patient_state.db",
        )
        self.declare_parameter("patient_message_keep_days", 30)
        # 闭环 #6: 机器人到位后 N 秒病人没确认 → 推系统消息告警医护
        self.declare_parameter("patient_arrived_timeout_sec", 180)
        # 扫描周期 (0=禁用监控)
        self.declare_parameter("patient_arrived_check_period_sec", 30)

        self.host = self.get_parameter("host").get_parameter_value().string_value
        self.port = self.get_parameter("port").get_parameter_value().integer_value
        self.stations_file = (
            self.get_parameter("stations_file").get_parameter_value().string_value
        )
        self.service_timeout_sec = (
            self.get_parameter("service_timeout_sec").get_parameter_value().double_value
        )
        self.scan_max_age_sec = max(
            0.0,
            self.get_parameter("scan_max_age_sec").get_parameter_value().double_value,
        )
        self.chassis_status_topic = (
            self.get_parameter("chassis_status_topic")
            .get_parameter_value()
            .string_value
        )
        self.chassis_estop_service = (
            self.get_parameter("chassis_estop_service")
            .get_parameter_value()
            .string_value
        )
        self.scan_topic = (
            self.get_parameter("scan_topic").get_parameter_value().string_value
        )
        self.enable_scan_listener = (
            self.get_parameter("enable_scan_listener")
            .get_parameter_value()
            .bool_value
        )
        self.scan_status_period_sec = max(
            0.1,
            self.get_parameter("scan_status_period_sec").get_parameter_value().double_value,
        )
        self.navigation_map_directory = (
            self.get_parameter("navigation_map_directory")
            .get_parameter_value()
            .string_value
        )
        if not os.path.isdir(self.navigation_map_directory):
            local_maps = os.path.join(os.getcwd(), "maps")
            if os.path.isdir(local_maps):
                self.navigation_map_directory = local_maps
        self.navigation_map_frame = (
            self.get_parameter("navigation_map_frame")
            .get_parameter_value()
            .string_value
        )
        self.navigation_base_frame = (
            self.get_parameter("navigation_base_frame")
            .get_parameter_value()
            .string_value
        )
        self.enable_tf_listener = (
            self.get_parameter("enable_tf_listener")
            .get_parameter_value()
            .bool_value
        )
        self.api_write_token = (
            self.get_parameter("api_write_token").get_parameter_value().string_value
        )
        self.max_request_body_bytes = max(
            self.get_parameter("max_request_body_bytes")
            .get_parameter_value()
            .integer_value,
            1024,
        )
        self.health_event_file = (
            self.get_parameter("health_event_file").get_parameter_value().string_value
        )
        self.delivery_batch_state_file = (
            self.get_parameter("delivery_batch_state_file")
            .get_parameter_value()
            .string_value
        )
        self.pending_delivery_batch_file = (
            self.get_parameter("pending_delivery_batch_file")
            .get_parameter_value()
            .string_value
        )
        self.delivery_safety_self_test_file = (
            self.get_parameter("delivery_safety_self_test_file")
            .get_parameter_value()
            .string_value
        )
        self.patient_port = (
            self.get_parameter("patient_port").get_parameter_value().integer_value
        )
        self.patient_web_dist_dir = (
            self.get_parameter("patient_web_dist_dir")
            .get_parameter_value()
            .string_value
        )
        self.patient_call_topic = (
            self.get_parameter("patient_call_topic")
            .get_parameter_value()
            .string_value
        )
        self.patient_message_topic = (
            self.get_parameter("patient_message_topic")
            .get_parameter_value()
            .string_value
        )
        self.voice_text_topic = (
            self.get_parameter("voice_text_topic").get_parameter_value().string_value
        )
        self.asr_control_topic = (
            self.get_parameter("asr_control_topic").get_parameter_value().string_value
        )
        self.patient_voice_context_topic = (
            self.get_parameter("patient_voice_context_topic")
            .get_parameter_value()
            .string_value
        )
        self.vision_control_topic = (
            self.get_parameter("vision_control_topic").get_parameter_value().string_value
        )
        self.patient_message_max = max(
            10,
            self.get_parameter("patient_message_max")
            .get_parameter_value()
            .integer_value,
        )
        self.patient_history_days = max(
            1,
            self.get_parameter("patient_history_days")
            .get_parameter_value()
            .integer_value,
        )
        self.patient_access_secret = (
            self.get_parameter("patient_access_secret")
            .get_parameter_value()
            .string_value
        )
        self.patient_state_db_path = (
            self.get_parameter("patient_state_db")
            .get_parameter_value()
            .string_value
        )
        self.patient_message_keep_days = max(
            1,
            self.get_parameter("patient_message_keep_days")
            .get_parameter_value()
            .integer_value,
        )
        self.patient_arrived_timeout_sec = max(
            10,
            self.get_parameter("patient_arrived_timeout_sec")
            .get_parameter_value()
            .integer_value,
        )
        self.patient_arrived_check_period_sec = max(
            0,
            self.get_parameter("patient_arrived_check_period_sec")
            .get_parameter_value()
            .integer_value,
        )
        self.state_lock = threading.Lock()
        self.drug_info_lock = threading.Lock()
        self.chassis_status_lock = threading.Lock()
        self.scan_status_lock = threading.Lock()
        self.latest_state = self.empty_state()
        self.latest_drug_info = self.empty_drug_info()
        self.latest_recognition_status = {}
        self.dashboard_ocr_status = {
            "active": False,
            "continuous": False,
            "single_pending": False,
            "ocr_enabled": True,
            "ocr_available": True,
            "ocr_runtime_enabled": False,
            "ocr_single_shot_pending": False,
            "ocr_backend": "dashboard_tesseract",
            "ocr_language": "chi_sim+eng",
            "ocr_text": "",
            "ocr_confidence": 0.0,
            "ocr_error": "",
            "ocr_worker_busy_ms": 0.0,
            "ocr_age_sec": 0.0,
            "ocr_updated_at": 0.0,
        }
        self.dashboard_ocr_thread = None
        self.latest_chassis_status = self.empty_chassis_status()
        self.latest_scan_status = self.empty_scan_status()
        self._last_scan_status_update = 0.0
        self.system_load_lock = threading.Lock()
        self._last_cpu_times = None
        self._last_system_load = self.empty_system_load()
        # patient_web 二号 server + 呼叫 publisher
        self.patient_server = None
        self.patient_server_thread = None
        self.patient_call_publisher = self.create_publisher(
            String, self.patient_call_topic, 10
        )
        self.voice_text_publisher = self.create_publisher(
            String, self.voice_text_topic, 10
        )
        self.asr_control_publisher = self.create_publisher(
            String, self.asr_control_topic, 10
        )
        self.patient_voice_context_publisher = self.create_publisher(
            String, self.patient_voice_context_topic, 10
        )
        self.vision_control_publisher = self.create_publisher(
            String, self.vision_control_topic, 10
        )
        # 病人留言
        self.patient_messages_lock = threading.Lock()
        self.patient_messages = deque(maxlen=self.patient_message_max)
        self.patient_message_seq = 0
        self.patient_message_publisher = self.create_publisher(
            String, self.patient_message_topic, 10
        )
        # 病人 IM/override 持久化 store (断电恢复)
        self.patient_state_store = None
        self.patient_status_overrides = {}
        self.patient_history_log = []
        if PATIENT_STORE_AVAILABLE and self.patient_state_db_path:
            try:
                self.patient_state_store = PatientStateStore(
                    db_path=self.patient_state_db_path,
                    message_keep_days=self.patient_message_keep_days,
                    logger=self.get_logger(),
                )
            except Exception as exc:
                self.get_logger().warn(
                    f"patient_state_store init exception: {exc} (memory-only)"
                )
                self.patient_state_store = None
        # 闭环 #6: 机器人到位等待病人确认的超时追踪
        # key = (task_id, bed_no), value = {"arrived_at": ts, "alerted": bool}
        self.patient_arrival_lock = threading.Lock()
        self.patient_arrival_tracker = {}
        self.patient_arrival_timer = None  # ROS Timer, 由 main 启动后注册
        # 回灌历史数据 (重启后让医护/病人立即看到上次断电前的状态)
        if self.patient_state_store and self.patient_state_store.ok:
            try:
                restored = self.patient_state_store.load_all_messages(
                    limit=self.patient_message_max
                )
                for m in restored:
                    self.patient_messages.append(m)
                # seq 推进到时间戳后, 避免重启后 id 重复
                self.patient_message_seq = max(
                    self.patient_message_seq, len(restored)
                )
                self.patient_status_overrides = (
                    self.patient_state_store.load_all_overrides()
                )
                self.patient_history_log = self.patient_state_store.load_history(
                    limit=50
                )
                self.get_logger().info(
                    f"patient_state restored: {len(restored)} messages, "
                    f"{len(self.patient_status_overrides)} overrides, "
                    f"{len(self.patient_history_log)} history entries"
                )
            except Exception as exc:
                self.get_logger().warn(f"patient_state restore failed: {exc}")
        self.tf_buffer = None
        self.tf_listener = None
        if self.enable_tf_listener and tf2_ros is not None:
            self.tf_buffer = tf2_ros.Buffer()
            self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        self.stations = self.load_stations(self.stations_file)
        self.delivery_batch_lock = threading.Lock()
        self.delivery_db_lock = threading.Lock()
        self.delivery_db = self.init_delivery_database()
        self.pending_delivery_batch = None
        self.delivery_batch = self.load_delivery_batch_state()
        self.pending_delivery_batch = self.load_pending_delivery_batch_state()
        self.create_task_client = self.create_client(
            CreateDeliveryTask, "/medicine/create_delivery_task"
        )
        self.cancel_task_client = self.create_client(
            CancelDeliveryTask, "/medicine/cancel_delivery_task"
        )
        self.verify_task_client = self.create_client(
            VerifyDeliveryTask, "/medicine/verify_delivery_task"
        )
        self.chassis_estop_client = self.create_client(
            SetBool, self.chassis_estop_service
        )
        self.create_subscription(
            DeliveryState, "/medicine/delivery_state", self.on_delivery_state, 10
        )
        self.create_subscription(DrugInfo, "/medicine/drug_info", self.on_drug_info, 10)
        self.create_subscription(
            String,
            "/medicine/drug_recognition_status",
            self.on_drug_recognition_status,
            10,
        )
        self.create_subscription(
            String, self.chassis_status_topic, self.on_chassis_status, 10
        )
        if self.enable_scan_listener and LaserScan is not None:
            self.create_subscription(
                LaserScan, self.scan_topic, self.on_scan, qos_profile_sensor_data
            )
        self.server = None
        self.server_thread = None
        self.vision_webrtc = VisionWebRTCService(logger=self.get_logger())

    def empty_state(self):
        return {
            "task_id": "",
            "state": "IDLE",
            "message": "等待送药任务",
            "current_station": "pharmacy",
            "target_station": "",
            "medicine_name": "",
            "patient_id": "",
            "patient_name": "",
            "ward_id": "",
            "bed_no": "",
            "product_code": "",
            "product_model": "",
            "quantity": "",
            "trace_id": "",
            "order_no": "",
            "medications_json": "[]",
            "medication_total_count": 0,
            "medication_loaded_count": 0,
            "medication_dispensed_count": 0,
            "load_confirmed": False,
            "load_confirmed_at": "",
            "dispense_confirmed": False,
            "dispense_confirmed_at": "",
            "last_verification_stage": "",
            "last_verification_passed": False,
            "last_verification_message": "",
            "verification_records": [],
            "progress": 0.0,
            "stamp": 0.0,
        }

    def empty_drug_info(self):
        return {
            "drug_id": "",
            "drug_name": "",
            "drug_type": "",
            "confidence": 0.0,
            "loaded": False,
            "source": "",
            "stamp": 0.0,
            "web_received_at": 0.0,
            "recognition_received_at": 0.0,
            "scan_age_sec": 0.0,
            "raw_code_text": "",
            "code_text": "",
            "code_type": "",
            "code_method": "",
            "trace_code": "",
            "trace_source": "",
            "trace_method": "",
            "recognition_source": "",
            "recognition_channel": "",
            "needs_review": False,
            "ocr_match_text": "",
            "ocr_extracted_fields": {},
            "ocr_drug_name": "",
            "ocr_spec": "",
            "ocr_manufacturer": "",
            "ocr_approval_no": "",
            "ocr_enabled": False,
            "ocr_available": False,
            "ocr_text": "",
            "ocr_confidence": 0.0,
            "ocr_language": "",
            "ocr_backend": "",
            "ocr_error": "",
            "ocr_worker_busy_ms": 0.0,
            "ocr_age_sec": 0.0,
            "ocr_roi_enabled": False,
            "ocr_roi_rect": [],
            "ocr_roi_frame_size": [],
            "barcode_roi_enabled": False,
            "barcode_roi_rect": [],
            "barcode_roi_frame_size": [],
            "camera_fps": 0,
            "camera_actual_fps": 0.0,
            "ppocr_backend_loaded": False,
            "label_order_no": "",
            "label_product_code": "",
            "label_product_model": "",
            "label_quantity": "",
            "label_trace_id": "",
        }

    def empty_chassis_status(self):
        return {
            "ok": False,
            "received": False,
            "message": "no chassis status received",
            "topic": self.chassis_status_topic,
            "web_received_at": 0.0,
        }

    def empty_scan_status(self):
        return {
            "ok": False,
            "received": False,
            "topic": self.scan_topic,
            "message": "no scan received",
            "web_received_at": 0.0,
        }

    def empty_system_load(self):
        return {
            "ok": False,
            "cpu_percent": 0.0,
            "gpu_percent": 0.0,
            "npu_percent": 0.0,
            "gpu_freq_mhz": 0.0,
            "npu_freq_mhz": 0.0,
            "updated_at": 0.0,
        }

    def read_cpu_times(self):
        lines = _read_text("/proc/stat").splitlines()
        if not lines:
            return None
        parts = lines[0].split()
        if len(parts) < 5 or parts[0] != "cpu":
            return None
        try:
            values = [int(value) for value in parts[1:]]
        except ValueError:
            return None
        idle = values[3] + (values[4] if len(values) > 4 else 0)
        return sum(values), idle

    def read_cpu_percent(self):
        current = self.read_cpu_times()
        if current is None:
            return 0.0
        if self._last_cpu_times is None:
            self._last_cpu_times = current
            return 0.0
        total_delta = current[0] - self._last_cpu_times[0]
        idle_delta = current[1] - self._last_cpu_times[1]
        self._last_cpu_times = current
        if total_delta <= 0:
            return 0.0
        return max(0.0, min(100.0, 100.0 * (total_delta - idle_delta) / total_delta))

    def read_devfreq_load(self, root_path):
        return {
            "percent": _parse_devfreq_load(_read_text(os.path.join(root_path, "load"))),
            "freq_mhz": _read_int(os.path.join(root_path, "cur_freq")) / 1_000_000.0,
        }

    def get_system_load(self):
        with self.system_load_lock:
            gpu = self.read_devfreq_load(GPU_DEVFREQ_PATH)
            npu = self.read_devfreq_load(NPU_DEVFREQ_PATH)
            self._last_system_load = {
                "ok": True,
                "cpu_percent": self.read_cpu_percent(),
                "gpu_percent": gpu["percent"],
                "npu_percent": npu["percent"],
                "gpu_freq_mhz": gpu["freq_mhz"],
                "npu_freq_mhz": npu["freq_mhz"],
                "updated_at": time.time(),
            }
            return dict(self._last_system_load)

    def load_stations(self, stations_file):
        with open(stations_file, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
        stations = []
        for station_id, value in sorted((data.get("stations") or {}).items()):
            stations.append(
                {
                    "id": station_id,
                    "name": value.get("name", station_id),
                    "x": float(value.get("x", 0.0)),
                    "y": float(value.get("y", 0.0)),
                    "yaw": float(value.get("yaw", 0.0)),
                }
            )
        return stations







    def init_delivery_database(self):
        if not DB_AVAILABLE:
            self.get_logger().warn("delivery_database module unavailable; SQLite audit disabled")
            return None
        try:
            database = DeliveryDatabase()
            database.log_system_event(
                "INFO",
                "web_dashboard",
                "medicine_web_dashboard SQLite audit initialized",
            )
            return database
        except Exception as exc:
            self.get_logger().error(f"failed to initialize delivery database: {exc}")
            return None

    def save_batch_to_db_locked(self, batch):
        if self.delivery_db is None:
            return
        summary = batch.get("summary", {}) if isinstance(batch.get("summary"), dict) else {}
        route = batch.get("route")
        if not isinstance(route, list):
            route = [stop.get("target_station", "") for stop in batch.get("stops", [])]
        batch_data = {
            "batch_id": batch.get("batch_id", ""),
            "status": batch.get("route_status", batch.get("status", "")),
            "source_station": batch.get("source_station", "pharmacy"),
            "route": route,
            "operator_id": batch.get("operator_id", ""),
            "total_stops": summary.get("stop_total_count", 0),
            "total_patients": summary.get("patient_total_count", 0),
            "total_medications": summary.get("medication_total_count", 0),
            "completed_medications": summary.get("medication_dispensed_count", 0),
            "failed_medications": summary.get("medication_exception_count", 0)
            + summary.get("medication_returned_count", 0),
            "notes": batch.get("notes", ""),
        }
        try:
            with self.delivery_db_lock:
                self.delivery_db.save_batch(batch_data)
        except Exception as exc:
            self.get_logger().error(f"failed to save batch to database: {exc}")

    def save_scan_to_db_locked(
        self,
        batch,
        stage,
        product_code,
        trace_id,
        result,
        stop=None,
        patient=None,
        medication=None,
        notes="",
    ):
        if self.delivery_db is None:
            return
        patient = patient or {}
        medication = medication or {}
        stop = stop or {}
        try:
            with self.delivery_db_lock:
                self.delivery_db.save_scan_record(
                    batch_id=batch.get("batch_id", ""),
                    stage=stage,
                    product_code=product_code,
                    trace_id=trace_id,
                    result=result,
                    patient_id=patient.get("patient_id"),
                    patient_name=patient.get("patient_name"),
                    medication_name=medication.get("medicine_name"),
                    expected_product_code=medication.get("product_code"),
                    expected_trace_id=medication.get("trace_id"),
                    operator=batch.get("operator_id", "system"),
                    station=stop.get("target_station") or batch.get("current_station"),
                    notes=notes,
                )
        except Exception as exc:
            self.get_logger().error(f"failed to save scan record to database: {exc}")

    def save_exception_to_db_locked(
        self,
        batch,
        exception_type,
        description,
        stop=None,
        patient=None,
        medication=None,
    ):
        if self.delivery_db is None:
            return
        patient = patient or {}
        medication = medication or {}
        stop = stop or {}
        try:
            with self.delivery_db_lock:
                self.delivery_db.save_exception(
                    batch_id=batch.get("batch_id", ""),
                    exception_type=exception_type,
                    description=description,
                    patient_id=patient.get("patient_id"),
                    medication_id=medication.get("id"),
                    station=stop.get("target_station") or batch.get("current_station"),
                )
        except Exception as exc:
            self.get_logger().error(f"failed to save exception record to database: {exc}")


























    def on_delivery_state(self, msg):
        # 闭环 #6: 追踪 "到位时刻", 用于超时未确认告警
        try:
            self._update_arrival_tracker(
                task_id=str(msg.task_id),
                bed_no=str(msg.bed_no),
                task_state=str(msg.state),
            )
        except Exception as exc:
            self.get_logger().warn(f"update_arrival_tracker failed: {exc}")
        with self.state_lock:
            self.latest_state = {
                "task_id": msg.task_id,
                "state": msg.state,
                "message": msg.message,
                "current_station": msg.current_station,
                "target_station": msg.target_station,
                "medicine_name": msg.medicine_name,
                "patient_id": msg.patient_id,
                "patient_name": msg.patient_name,
                "ward_id": msg.ward_id,
                "bed_no": msg.bed_no,
                "product_code": msg.product_code,
                "product_model": msg.product_model,
                "quantity": msg.quantity,
                "trace_id": msg.trace_id,
                "order_no": msg.order_no,
                "medications_json": msg.medications_json,
                "medication_total_count": int(msg.medication_total_count),
                "medication_loaded_count": int(msg.medication_loaded_count),
                "medication_dispensed_count": int(msg.medication_dispensed_count),
                "load_confirmed": bool(msg.load_confirmed),
                "load_confirmed_at": msg.load_confirmed_at,
                "dispense_confirmed": bool(msg.dispense_confirmed),
                "dispense_confirmed_at": msg.dispense_confirmed_at,
                "last_verification_stage": msg.last_verification_stage,
                "last_verification_passed": bool(msg.last_verification_passed),
                "last_verification_message": msg.last_verification_message,
                "verification_records": list(msg.verification_records),
                "progress": float(msg.progress),
                "stamp": float(msg.stamp.sec)
                + float(msg.stamp.nanosec) / 1_000_000_000.0,
            }

    def on_drug_info(self, msg):
        with self.drug_info_lock:
            self.latest_drug_info = {
                "drug_id": msg.drug_id,
                "drug_name": msg.drug_name,
                "drug_type": msg.drug_type,
                "confidence": float(msg.confidence),
                "loaded": bool(msg.loaded),
                "source": msg.source,
                "stamp": float(msg.stamp.sec)
                + float(msg.stamp.nanosec) / 1_000_000_000.0,
                "web_received_at": time.time(),
            }

    def on_drug_recognition_status(self, msg):
        try:
            status = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        if isinstance(status, dict):
            status["web_received_at"] = time.time()
        with self.drug_info_lock:
            self.latest_recognition_status = status if isinstance(status, dict) else {}

    def on_chassis_status(self, msg):
        try:
            status = json.loads(msg.data)
        except json.JSONDecodeError:
            status = {
                "ok": False,
                "received": True,
                "message": "invalid chassis status json",
                "raw": msg.data,
            }
        if not isinstance(status, dict):
            status = {
                "ok": False,
                "received": True,
                "message": "chassis status payload is not an object",
            }
        status["received"] = True
        status["web_received_at"] = time.time()
        status.setdefault("ok", True)
        status.setdefault("topic", self.chassis_status_topic)
        with self.chassis_status_lock:
            self.latest_chassis_status = status

    def on_scan(self, msg):
        now = time.time()
        if now - self._last_scan_status_update < self.scan_status_period_sec:
            return
        self._last_scan_status_update = now
        valid_count = sum(
            1
            for value in msg.ranges
            if math.isfinite(value) and msg.range_min <= value <= msg.range_max
        )
        status = {
            "ok": True,
            "received": True,
            "topic": self.scan_topic,
            "frame_id": msg.header.frame_id,
            "stamp_sec": float(msg.header.stamp.sec)
            + float(msg.header.stamp.nanosec) / 1_000_000_000.0,
            "web_received_at": now,
            "range_min": float(msg.range_min),
            "range_max": float(msg.range_max),
            "count": len(msg.ranges),
            "valid_count": valid_count,
        }
        with self.scan_status_lock:
            self.latest_scan_status = status

    def get_navigation_maps(self):
        maps = list_navigation_maps(self.navigation_map_directory)
        return {
            "maps": maps,
            "default_map": maps[-1]["yaml"] if maps else "",
            "map_directory": self.navigation_map_directory,
        }

    def get_navigation_map(self, name):
        return build_navigation_map_payload(self.navigation_map_directory, name or None)

    def get_navigation_map_file(self, file_name):
        return resolve_navigation_map_asset(self.navigation_map_directory, file_name)

    def get_navigation_status(self):
        now = time.time()
        chassis = self.get_chassis_status()
        state = self.get_state()
        scan = self.build_scan_check(now)
        tf_status, robot_pose = self.build_tf_check()
        graph = self.build_ros_graph_check()
        chassis_check = self.build_chassis_check(chassis, now)
        localization = graph["localization"]
        nav2 = graph["nav2"]
        costmap = graph["costmap"]
        return {
            "mode": "real",
            "generated_at": now,
            "overall_ok": bool(scan["ok"] and tf_status["ok"] and nav2["ok"]),
            "scan": scan,
            "tf": tf_status,
            "robot_pose": robot_pose,
            "localization": localization,
            "nav2": nav2,
            "costmap": costmap,
            "chassis_check": chassis_check,
            "chassis": chassis,
            "delivery_state": state,
        }

    def get_navigation_snapshot(self, map_name=""):
        snapshot = {
            "snapshot_version": 1,
            "created_at": time.time(),
            "robot": "rk3588_medicine_robot",
            "mode": "real",
            "navigation_status": self.get_navigation_status(),
            "maps": self.get_navigation_maps(),
            "selected_map": None,
            "ros_graph": self.get_ros_graph_snapshot(),
            "notes": [
                "This snapshot is read-only diagnostic data.",
                "It does not include commands and does not control the chassis.",
            ],
        }
        try:
            snapshot["selected_map"] = self.get_navigation_map(map_name)
        except Exception as exc:
            snapshot["selected_map_error"] = str(exc)
        return snapshot

    def get_ros_graph_snapshot(self):
        try:
            actions = [
                {"name": name, "types": types}
                for name, types in self.get_action_names_and_types()
            ]
        except Exception:
            actions = []
        return {
            "nodes": sorted(self.get_node_names()),
            "topics": [
                {"name": name, "types": types}
                for name, types in sorted(self.get_topic_names_and_types())
            ],
            "actions": sorted(actions, key=lambda item: item["name"]),
            "expected": {
                "scan_topic": self.scan_topic,
                "chassis_status_topic": self.chassis_status_topic,
                "map_frame": self.navigation_map_frame,
                "base_frame": self.navigation_base_frame,
                "nav2_action": "/navigate_to_pose",
            },
        }

    def build_scan_check(self, now):
        with self.scan_status_lock:
            scan = copy.deepcopy(self.latest_scan_status)
        if not scan.get("received"):
            scan_pub_ok = any(
                name == self.scan_topic
                for name, _types in self.get_topic_names_and_types()
            )
            return {
                "name": "/scan",
                "ok": scan_pub_ok,
                "summary": (
                    f"{self.scan_topic} publisher present"
                    if scan_pub_ok
                    else f"{self.scan_topic} publisher missing"
                ),
            }
        age = now - float(scan.get("web_received_at", 0.0) or 0.0)
        ok = age <= 2.0
        return {
            "name": "/scan",
            "ok": ok,
            "summary": (
                f"{scan.get('topic')} frame={scan.get('frame_id')} "
                f"age={age:.2f}s points={scan.get('valid_count')}/{scan.get('count')}"
            ),
            "raw": scan,
        }

    def build_tf_check(self):
        if self.tf_buffer is None:
            if not self.enable_tf_listener:
                return (
                    {
                        "name": "TF display",
                        "ok": True,
                        "summary": "web TF listener disabled to reduce load",
                    },
                    {"ok": False},
                )
            return (
                {
                    "name": "TF",
                    "ok": False,
                    "summary": "web TF listener disabled",
                },
                {"ok": False},
            )
        try:
            transform = self.tf_buffer.lookup_transform(
                self.navigation_map_frame,
                self.navigation_base_frame,
                Time(),
                timeout=Duration(seconds=0.05),
            )
        except Exception as exc:
            return (
                {
                    "name": "TF",
                    "ok": False,
                    "summary": (
                        f"{self.navigation_map_frame}->{self.navigation_base_frame} "
                        f"unavailable: {exc}"
                    ),
                },
                {"ok": False},
            )
        translation = transform.transform.translation
        rotation = transform.transform.rotation
        yaw = self.quaternion_to_yaw(rotation)
        return (
            {
                "name": "TF",
                "ok": True,
                "summary": (
                    f"{self.navigation_map_frame}->{self.navigation_base_frame} "
                    f"x={translation.x:.2f} y={translation.y:.2f} yaw={yaw:.2f}"
                ),
            },
            {
                "ok": True,
                "frame": self.navigation_map_frame,
                "child_frame": self.navigation_base_frame,
                "x": float(translation.x),
                "y": float(translation.y),
                "yaw": float(yaw),
            },
        )

    def build_ros_graph_check(self):
        node_names = set(self.get_node_names())
        topics = {name for name, _ in self.get_topic_names_and_types()}
        try:
            actions = {name for name, _ in self.get_action_names_and_types()}
        except Exception:
            actions = set()
        normalized_node_names = set(node_names)
        normalized_node_names.update(
            name[1:] for name in node_names if name.startswith("/")
        )
        normalized_node_names.update(
            f"/{name}" for name in node_names if not name.startswith("/")
        )
        cartographer_ok = any("cartographer" in name for name in node_names)
        nav2_nodes_ok = all(
            node_name in normalized_node_names
            for node_name in (
                "/controller_server",
                "/planner_server",
                "/bt_navigator",
                "/velocity_smoother",
            )
        )
        nav2_ok = "/navigate_to_pose" in actions or nav2_nodes_ok
        local_costmap_ok = any("local_costmap" in name for name in topics)
        global_costmap_ok = any("global_costmap" in name for name in topics)
        return {
            "localization": {
                "name": "Cartographer",
                "ok": cartographer_ok,
                "summary": (
                    "cartographer node present"
                    if cartographer_ok
                    else "cartographer node not seen"
                ),
            },
            "nav2": {
                "name": "Nav2",
                "ok": nav2_ok,
                "summary": (
                    "/navigate_to_pose action available"
                    if "/navigate_to_pose" in actions
                    else (
                        "Nav2 lifecycle nodes present; action not visible to dashboard node"
                        if nav2_nodes_ok
                        else "/navigate_to_pose action not seen"
                    )
                ),
            },
            "costmap": {
                "name": "Costmap",
                "ok": local_costmap_ok or global_costmap_ok,
                "summary": (
                    f"local={local_costmap_ok} global={global_costmap_ok}"
                ),
            },
        }

    def build_chassis_check(self, chassis, now):
        if not chassis.get("received"):
            return {
                "name": "Chassis",
                "ok": False,
                "summary": "chassis status not received",
            }
        age = now - float(chassis.get("web_received_at", 0.0) or 0.0)
        control_authorized = bool(chassis.get("control_authorized", False))
        emergency_stop = bool(chassis.get("emergency_stop", False))
        return {
            "name": "Chassis",
            "ok": age <= 2.0,
            "summary": (
                f"age={age:.2f}s auth={control_authorized} estop={emergency_stop}"
            ),
        }

    @staticmethod
    def quaternion_to_yaw(rotation):
        siny_cosp = 2.0 * (rotation.w * rotation.z + rotation.x * rotation.y)
        cosy_cosp = 1.0 - 2.0 * (rotation.y * rotation.y + rotation.z * rotation.z)
        return math.atan2(siny_cosp, cosy_cosp)




    def _probe_local_http(self, url, timeout=0.45):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                status = int(getattr(response, "status", 0) or response.getcode() or 0)
                return {
                    "ok": 200 <= status < 400,
                    "status_code": status,
                    "message": f"HTTP {status}",
                }
        except Exception as exc:
            return {
                "ok": False,
                "status_code": 0,
                "message": str(exc),
            }

    def load_health_events(self):
        path = getattr(self, "health_event_file", "") or ""
        if not path:
            return []
        try:
            if not os.path.isfile(path):
                return []
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            items = data.get("events", data) if isinstance(data, dict) else data
            if not isinstance(items, list):
                return []
            return [item for item in items if isinstance(item, dict)][-50:]
        except Exception as exc:
            try:
                self.get_logger().warn(f"load health events failed: {exc}")
            except Exception:
                pass
            return []

    def persist_health_events_locked(self):
        path = getattr(self, "health_event_file", "") or ""
        if not path:
            return
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp_path = f"{path}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "updated_at": time.time(),
                        "events": list(self.health_events),
                    },
                    handle,
                    ensure_ascii=False,
                    indent=2,
                )
            os.replace(tmp_path, path)
        except Exception as exc:
            try:
                self.get_logger().warn(f"persist health events failed: {exc}")
            except Exception:
                pass

    def ensure_health_event_state(self):
        if not hasattr(self, "health_event_lock"):
            self.health_event_lock = threading.Lock()
        if not hasattr(self, "health_events"):
            self.health_events = deque(self.load_health_events(), maxlen=50)
        if not hasattr(self, "_last_health_signature"):
            self._last_health_signature = ""

    def build_health_signature(self, status, summary):
        summary = summary or {}
        return f"{status}:{int(summary.get('bad') or 0)}:{int(summary.get('warn') or 0)}"

    def record_health_event_if_changed(self, status, summary, checks):
        self.ensure_health_event_state()
        summary = summary or {}
        signature = self.build_health_signature(status, summary)
        with self.health_event_lock:
            if not self._last_health_signature:
                self._last_health_signature = signature
                return
            if signature == self._last_health_signature:
                return
            previous = self._last_health_signature
            self._last_health_signature = signature
            problem_labels = []
            for item in (checks or {}).values():
                if item.get("status") != "ok":
                    problem_labels.append(str(item.get("label") or ""))
            if status == "ok":
                message = "\u6240\u6709\u81ea\u68c0\u9879\u6062\u590d\u6b63\u5e38"
            else:
                message = "\uff1b".join(x for x in problem_labels if x) or "\u6709\u81ea\u68c0\u9879\u9700\u786e\u8ba4"
            self.health_events.appendleft(
                {
                    "time": time.time(),
                    "status": status,
                    "summary": {
                        "ok": int(summary.get("ok") or 0),
                        "warn": int(summary.get("warn") or 0),
                        "bad": int(summary.get("bad") or 0),
                    },
                    "message": message,
                    "previous_signature": previous,
                    "signature": signature,
                }
            )
            self.persist_health_events_locked()

    def get_health_events(self):
        self.ensure_health_event_state()
        with self.health_event_lock:
            return list(self.health_events)

    def get_health_check(self):
        now = time.time()
        checks = {}

        def add(key, label, status, message, details=None, actions=None):
            checks[key] = {
                "label": label,
                "status": status,
                "ok": status == "ok",
                "message": message,
                "details": details or {},
                "actions": actions or [],
            }

        add(
            "dashboard",
            "8085 \u5de5\u4f5c\u53f0",
            "ok" if self.server is not None else "bad",
            f"\u7aef\u53e3 {self.port} \u5df2\u8fd0\u884c" if self.server is not None else "\u5de5\u4f5c\u53f0 HTTP \u670d\u52a1\u672a\u8fd0\u884c",
            {"port": self.port},
            [{"label": "\u5237\u65b0\u81ea\u68c0", "action": "refresh_health"}],
        )

        patient_index = os.path.join(self.patient_web_dist_dir, "index.html")
        patient_dist_ok = os.path.isfile(patient_index)
        patient_probe = self._probe_local_http(
            f"http://127.0.0.1:{self.patient_port}/patient/"
        )
        patient_ok = bool(self.patient_server is not None and patient_dist_ok and patient_probe.get("ok"))
        if patient_ok:
            patient_status = "ok"
            patient_message = f"\u7aef\u53e3 {self.patient_port} \u53ef\u8bbf\u95ee"
        elif self.patient_server is not None and patient_dist_ok:
            patient_status = "warn"
            patient_message = f"\u670d\u52a1\u5df2\u542f\u52a8\uff0c\u4f46\u672c\u673a\u63a2\u6d4b\u5931\u8d25\uff1a{patient_probe.get('message', '')}"
        elif self.patient_server is None:
            patient_status = "bad"
            patient_message = "\u75c5\u4eba\u7aef HTTP \u670d\u52a1\u672a\u8fd0\u884c"
        else:
            patient_status = "bad"
            patient_message = "\u75c5\u4eba\u7aef dist \u7f3a\u5c11 index.html"
        add(
            "patient_web",
            "8081 \u75c5\u4eba\u7aef",
            patient_status,
            patient_message,
            {
                "port": self.patient_port,
                "dist_dir": self.patient_web_dist_dir,
                "dist_ready": patient_dist_ok,
                "probe": patient_probe,
            },
            [
                {"label": "\u6253\u5f00\u75c5\u4eba\u7aef", "action": "open_patient"},
                {"label": "\u5237\u65b0\u81ea\u68c0", "action": "refresh_health"},
            ],
        )

        asr_subscribers = int(self.asr_control_publisher.get_subscription_count())
        tts_subscribers = int(self.voice_text_publisher.get_subscription_count())
        voice_status = "ok" if (asr_subscribers > 0 or tts_subscribers > 0) else "warn"
        add(
            "voice",
            "\u8bed\u97f3\u94fe\u8def",
            voice_status,
            f"ASR \u63a7\u5236\u8ba2\u9605 {asr_subscribers}\uff0cTTS \u8ba2\u9605 {tts_subscribers}",
            {
                "asr_topic": self.asr_control_topic,
                "tts_topic": self.voice_text_topic,
                "asr_subscribers": asr_subscribers,
                "tts_subscribers": tts_subscribers,
            },
            [
                {"label": "\u67e5\u770b\u75c5\u4eba\u54a8\u8be2", "action": "switch_tab", "tab": "messages"},
                {"label": "\u6253\u5f00\u8bed\u97f3\u5bf9\u8bdd", "action": "focus", "tab": "batch", "target": "voice-listen-60"},
            ],
        )

        drug = self.get_drug_info()
        recognition_age = float(drug.get("scan_age_sec") or drug.get("ocr_age_sec") or 0.0)
        has_recent_recognition = bool(
            drug.get("drug_name")
            or drug.get("ocr_drug_name")
            or drug.get("trace_code")
            or drug.get("label_product_code")
            or drug.get("raw_code_text")
            or drug.get("code_text")
        )
        vision_ready = bool(
            drug.get("ocr_available")
            or drug.get("ppocr_backend_loaded")
            or drug.get("qr_enabled")
            or drug.get("decoder_backends")
        )
        if has_recent_recognition:
            vision_status = "ok"
            vision_message = "\u6700\u8fd1\u6709\u8bc6\u522b\u7ed3\u679c"
        elif vision_ready:
            vision_status = "warn"
            vision_message = "\u8bc6\u522b\u540e\u7aef\u53ef\u7528\uff0c\u6682\u65e0\u6700\u8fd1\u7ed3\u679c"
        else:
            vision_status = "warn"
            vision_message = "\u6682\u65e0\u8bc6\u522b\u540e\u7aef\u72b6\u6001"
        add(
            "vision",
            "\u836f\u54c1\u8bc6\u522b",
            vision_status,
            vision_message,
            {
                "backend": drug.get("ocr_backend", ""),
                "ppocr_backend_loaded": bool(drug.get("ppocr_backend_loaded", False)),
                "camera_actual_fps": drug.get("camera_actual_fps", 0),
                "scan_age_sec": recognition_age,
            },
            [
                {"label": "\u67e5\u770b\u836f\u54c1\u8bc6\u522b", "action": "switch_tab", "tab": "vision"},
                {"label": "\u6267\u884c OCR \u4e00\u6b21", "action": "focus", "tab": "vision", "target": "vision-ocr-once"},
            ],
        )

        chassis = self.get_chassis_status()
        chassis_received = bool(chassis.get("received"))
        chassis_age = (
            max(0.0, now - float(chassis.get("web_received_at") or 0.0))
            if chassis.get("web_received_at")
            else None
        )
        if chassis_received and (chassis_age is None or chassis_age < 5.0):
            chassis_status = "ok"
            chassis_message = f"\u72b6\u6001\u5b9e\u65f6 {chassis_age:.1f}s" if chassis_age is not None else "\u72b6\u6001\u5b9e\u65f6"
        elif chassis_received:
            chassis_status = "warn"
            chassis_message = f"\u72b6\u6001\u5ef6\u8fdf {chassis_age:.1f}s" if chassis_age is not None else "\u72b6\u6001\u5ef6\u8fdf"
        else:
            chassis_status = "warn"
            chassis_message = chassis.get("message") or "\u672a\u6536\u5230\u5e95\u76d8\u72b6\u6001"
        add(
            "chassis",
            "\u5e95\u76d8 / ROS2",
            chassis_status,
            chassis_message,
            {
                "received": chassis_received,
                "age_sec": chassis_age,
                "emergency_stop": chassis.get("emergency_stop"),
            },
            [
                {"label": "\u67e5\u770b\u5e95\u76d8\u72b6\u6001", "action": "switch_tab", "tab": "monitor"},
                {"label": "\u5237\u65b0\u81ea\u68c0", "action": "refresh_health"},
            ],
        )

        try:
            batch = self.get_delivery_batch()
        except Exception:
            batch = {}
        batch_id = str(batch.get("batch_id") or "").strip() if isinstance(batch, dict) else ""
        if batch_id:
            batch_summary = batch.get("summary") or {}
            batch_message = f"{batch_id} \u00b7 {batch.get('route_status') or batch.get('status') or '-'}"
            batch_status = "ok"
        else:
            batch_summary = {}
            batch_message = "\u6682\u65e0\u53ef\u6267\u884c\u6279\u6b21"
            batch_status = "warn"
        add(
            "delivery_batch",
            "\u914d\u9001\u6279\u6b21",
            batch_status,
            batch_message,
            {"summary": batch_summary},
            [
                {"label": "\u67e5\u770b\u914d\u9001\u6279\u6b21", "action": "switch_tab", "tab": "batch"},
                {"label": "\u5bfc\u5165\u6279\u6b21 JSON", "action": "focus", "tab": "batch", "target": "batch_import_text"},
            ],
        )

        try:
            safety_latest = self.get_delivery_safety_self_test_result()
        except Exception as exc:
            safety_latest = {"ok": False, "available": False, "message": str(exc), "result": None}
        safety_result = safety_latest.get("result") if isinstance(safety_latest, dict) else None
        if safety_result:
            tested_text = str(safety_result.get("tested_at") or "")
            safety_ok = bool(safety_result.get("ok"))
            safety_status = "ok" if safety_ok else "bad"
            safety_message = f"{safety_result.get('passed', 0)}/{safety_result.get('total', 0)} 项通过"
            if tested_text:
                safety_message += f" · {tested_text}"
        else:
            tested_text = ""
            safety_status = "warn"
            safety_message = "尚未执行安全门自测"
        add(
            "safety_self_test",
            "安全门自测",
            safety_status,
            safety_message,
            {"latest": safety_result, "available": bool(safety_result), "tested_at": tested_text},
            [
                {"label": "运行安全门自测", "action": "focus", "tab": "batch", "target": "safety-self-test"},
                {"label": "查看配送批次", "action": "switch_tab", "tab": "batch"},
            ],
        )

        load = self.get_system_load()
        cpu = float(load.get("cpu_percent") or 0.0)
        npu = float(load.get("npu_percent") or 0.0)
        add(
            "system_load",
            "\u786c\u4ef6\u8d1f\u8f7d",
            "warn" if cpu >= 85.0 else "ok",
            f"CPU {cpu:.0f}% \u00b7 NPU {npu:.0f}%",
            load,
            [
                {"label": "\u67e5\u770b\u786c\u4ef6\u8d1f\u8f7d", "action": "switch_tab", "tab": "monitor"},
                {"label": "\u5237\u65b0\u81ea\u68c0", "action": "refresh_health"},
            ],
        )

        bad_count = sum(1 for item in checks.values() if item.get("status") == "bad")
        warn_count = sum(1 for item in checks.values() if item.get("status") == "warn")
        overall = "bad" if bad_count else ("warn" if warn_count else "ok")
        default_actions = [
            {"label": "\u5237\u65b0\u81ea\u68c0", "action": "refresh_health"},
            {"label": "\u6253\u5f00\u75c5\u4eba\u7aef", "action": "open_patient"},
            {"label": "\u67e5\u770b\u914d\u9001\u6279\u6b21", "action": "switch_tab", "tab": "batch"},
        ]
        summary = {
            "bad": bad_count,
            "warn": warn_count,
            "ok": sum(1 for item in checks.values() if item.get("status") == "ok"),
        }
        self.record_health_event_if_changed(overall, summary, checks)
        return {
            "ok": bad_count == 0,
            "status": overall,
            "updated_at": now,
            "summary": summary,
            "checks": checks,
            "actions": default_actions,
            "events": self.get_health_events(),
        }

    def get_state(self):
        with self.state_lock:
            return dict(self.latest_state)

    def get_drug_info(self):
        with self.drug_info_lock:
            data = dict(self.latest_drug_info)
            status = dict(self.latest_recognition_status)
            dashboard_ocr = dict(self.dashboard_ocr_status)
            dashboard_ocr_recent = (
                bool(dashboard_ocr.get("active"))
                or bool(dashboard_ocr.get("ocr_text"))
                or bool(dashboard_ocr.get("ocr_error"))
            )
            if dashboard_ocr_recent:
                updated_at = float(dashboard_ocr.get("ocr_updated_at") or 0.0)
                if updated_at:
                    dashboard_ocr["ocr_age_sec"] = max(0.0, time.time() - updated_at)
                status.update(
                    {
                        "ocr_enabled": bool(dashboard_ocr.get("ocr_enabled", True)),
                        "ocr_available": bool(dashboard_ocr.get("ocr_available", True)),
                        "ocr_runtime_enabled": bool(dashboard_ocr.get("ocr_runtime_enabled", False)),
                        "ocr_single_shot_pending": bool(dashboard_ocr.get("ocr_single_shot_pending", False)),
                        "ocr_backend": dashboard_ocr.get("ocr_backend", "dashboard_tesseract"),
                        "ocr_language": dashboard_ocr.get("ocr_language", "chi_sim+eng"),
                        "ocr_text": dashboard_ocr.get("ocr_text", ""),
                        "ocr_confidence": float(dashboard_ocr.get("ocr_confidence", 0.0) or 0.0),
                        "ocr_error": dashboard_ocr.get("ocr_error", ""),
                        "ocr_worker_busy_ms": float(dashboard_ocr.get("ocr_worker_busy_ms", 0.0) or 0.0),
                        "ocr_age_sec": float(dashboard_ocr.get("ocr_age_sec", 0.0) or 0.0),
                        "ocr_match_text": dashboard_ocr.get("ocr_text", ""),
                        "ocr_extracted_fields": dashboard_ocr.get("ocr_extracted_fields", {}),
                        "ocr_drug_name": dashboard_ocr.get("ocr_drug_name", ""),
                        "ppocr_backend_loaded": False,
                    }
                )
            label_fields = (
                status.get("label_fields")
                if isinstance(status.get("label_fields"), dict)
                else {}
            )
            recognition_channel_hint = str(
                status.get("recognition_channel") or status.get("recognition_source") or ""
            ).strip()
            # The detector can keep its demo/default drug_001 (???) even when
            # the current camera frame only has a raw barcode and no real drug
            # identification channel.  Do not present that stale default as a
            # recognized medicine on the dashboard.
            if (
                str(data.get("drug_id") or "") == "drug_001"
                and str(data.get("drug_name") or "") == "降压药"
                and not recognition_channel_hint
                and "camera" in str(data.get("source") or status.get("source") or "").lower()
            ):
                data["drug_id"] = ""
                data["drug_name"] = ""
                data["drug_type"] = ""
                data["confidence"] = 0.0
                data["loaded"] = False
            recognition_received_at = float(
                status.get("web_received_at") or data.get("web_received_at") or 0.0
            )
            scan_age_sec = (
                max(0.0, time.time() - recognition_received_at)
                if recognition_received_at
                else 0.0
            )
            data.update(
                {
                    "recognition_received_at": recognition_received_at,
                    "scan_age_sec": scan_age_sec,
                    "raw_code_text": status.get("raw_code_text", ""),
                    "code_text": status.get("code_text", ""),
                    "code_type": status.get("code_type", ""),
                    "code_method": status.get("code_method", ""),
                    "trace_code": status.get("trace_code", ""),
                    "trace_source": status.get("trace_source", ""),
                    "trace_method": status.get("trace_method", ""),
                    "recognition_source": status.get("recognition_source", ""),
                    "recognition_channel": status.get("recognition_channel", ""),
                    "needs_review": bool(status.get("needs_review", False)),
                    "recognition_stable": bool(status.get("recognition_stable", False)),
                    "recognition_stable_count": int(status.get("recognition_stable_count", 0) or 0),
                    "recognition_stable_required": int(status.get("recognition_stable_required", 0) or 0),
                    "recognition_stable_signature": status.get("recognition_stable_signature", ""),
                    "stable_drug_name": status.get("stable_drug_name", ""),
                    "stable_recognition_channel": status.get("stable_recognition_channel", ""),
                    "stable_trace_code": status.get("stable_trace_code", ""),
                    "stable_product_code": status.get("stable_product_code", ""),
                    "stable_confidence": float(status.get("stable_confidence", 0.0) or 0.0),
                    "stable_age_sec": float(status.get("stable_age_sec", -1.0) or -1.0),
                    "ocr_match_text": status.get("ocr_match_text", ""),
                    "ocr_extracted_fields": status.get("ocr_extracted_fields", {}),
                    "ocr_drug_name": status.get("ocr_drug_name", ""),
                    "ocr_drug_name_candidates": (
                        status.get("ocr_extracted_fields", {}).get("drug_name_candidates", [])
                        if isinstance(status.get("ocr_extracted_fields"), dict)
                        else []
                    ),
                    "ocr_drug_name_score": (
                        status.get("ocr_extracted_fields", {}).get("drug_name_score", 0)
                        if isinstance(status.get("ocr_extracted_fields"), dict)
                        else 0
                    ),
                    "ocr_spec": status.get("ocr_spec", ""),
                    "ocr_manufacturer": status.get("ocr_manufacturer", ""),
                    "ocr_approval_no": status.get("ocr_approval_no", ""),
                    "ocr_enabled": bool(status.get("ocr_enabled", False)),
                    "ocr_available": bool(status.get("ocr_available", False)),
                    "ocr_text": status.get("ocr_text", ""),
                    "ocr_confidence": float(status.get("ocr_confidence", 0.0) or 0.0),
                    "ocr_held": bool(status.get("ocr_held", False)),
                    "ocr_hold_last_good_sec": float(status.get("ocr_hold_last_good_sec", 0.0) or 0.0),
                    "ocr_last_good_age_sec": float(status.get("ocr_last_good_age_sec", -1.0) or -1.0),
                    "ocr_language": status.get("ocr_language", ""),
                    "ocr_backend": status.get("ocr_backend", ""),
                    "ocr_error": status.get("ocr_error", ""),
                    "ocr_worker_busy_ms": float(status.get("ocr_worker_busy_ms", 0.0) or 0.0),
                    "ocr_age_sec": float(status.get("ocr_age_sec", 0.0) or 0.0),
                    "ocr_roi_enabled": bool(status.get("ocr_roi_enabled", False)),
                    "ocr_roi_rect": status.get("ocr_roi_rect", []),
                    "ocr_roi_frame_size": status.get("ocr_roi_frame_size", []),
                    "barcode_roi_enabled": bool(status.get("barcode_roi_enabled", False)),
                    "barcode_roi_rect": status.get("barcode_roi_rect", []),
                    "barcode_roi_frame_size": status.get("barcode_roi_frame_size", []),
                    "camera_fps": int(status.get("camera_fps", 0) or 0),
                    "camera_actual_fps": float(status.get("camera_actual_fps", 0.0) or 0.0),
                    "ppocr_backend_loaded": bool(status.get("ppocr_backend_loaded", False)),
                    "qr_enabled": bool(status.get("qr_enabled", False)),
                    "qr_attempt_count": int(status.get("qr_attempt_count", 0) or 0),
                    "qr_success_count": int(status.get("qr_success_count", 0) or 0),
                    "qr_candidate_count": int(status.get("qr_candidate_count", 0) or 0),
                    "qr_worker_busy_ms": float(status.get("qr_worker_busy_ms", 0.0) or 0.0),
                    "qr_worker_drop_count": int(status.get("qr_worker_drop_count", 0) or 0),
                    "decoder_backends": status.get("decoder_backends", []),
                    "last_qr_error": status.get("last_qr_error", ""),
                    "barcode_enhancement_enabled": bool(status.get("barcode_enhancement_enabled", False)),
                    "ocr_runtime_enabled": bool(status.get("ocr_runtime_enabled", False)),
                    "ocr_single_shot_pending": bool(status.get("ocr_single_shot_pending", False)),
                    "yolo_rknn_enabled": bool(status.get("yolo_rknn_enabled", False)),
                    "yolo_rknn_status": status.get("yolo_rknn_status", ""),
                    "yolo_rknn_message": status.get("yolo_rknn_message", ""),
                    "yolo_model_loaded": bool(status.get("yolo_model_loaded", False)),
                    "yolo_model_path": status.get("yolo_model_path", ""),
                    "yolo_inference_ms": float(status.get("yolo_inference_ms", 0.0) or 0.0),
                    "yolo_detection_count": int(status.get("yolo_detection_count", 0) or 0),
                    "yolo_detections": status.get("yolo_detections", []),
                    "label_fields": label_fields,
                    "label_order_no": status.get(
                        "label_order_no", label_fields.get("on", "")
                    ),
                    "label_product_code": status.get(
                        "label_product_code", label_fields.get("pc", "")
                    ),
                    "label_product_model": status.get(
                        "label_product_model", label_fields.get("pm", "")
                    ),
                    "label_quantity": status.get(
                        "label_quantity", label_fields.get("qty", "")
                    ),
                    "label_trace_id": status.get(
                        "label_trace_id", status.get("trace_code", label_fields.get("pdi", ""))
                    ),
                }
            )
            ocr_name = str(data.get("ocr_drug_name") or "").strip()
            if ocr_name and not re.search(r"[\u4e00-\u9fff]", ocr_name):
                data["ocr_drug_name"] = ""
                ocr_name = ""
            if not ocr_name:
                fallback_name, matched_code = self.lookup_drug_name_from_label_codes(
                    data.get("raw_code_text", ""),
                    data.get("code_text", ""),
                    data.get("product_code", ""),
                    data.get("label_product_code", ""),
                    data.get("trace_code", ""),
                    data.get("label_trace_id", ""),
                    data.get("ocr_text", ""),
                    data.get("ocr_match_text", ""),
                )
                if fallback_name:
                    data["ocr_drug_name"] = fallback_name
                    data["ocr_match_text"] = f"{matched_code} -> {fallback_name}" if matched_code else fallback_name
                    data["ocr_drug_name_candidates"] = [{
                        "text": fallback_name,
                        "score": 0.95,
                        "source": "barcode_catalog_code_fallback",
                        "matched_code": matched_code,
                    }]
                    data["ocr_drug_name_score"] = 0.95
            clean_ocr_candidates = []
            raw_ocr_candidates = data.get("ocr_drug_name_candidates", [])
            if isinstance(raw_ocr_candidates, list):
                for item in raw_ocr_candidates:
                    if isinstance(item, dict):
                        candidate_text = str(item.get("text") or "").strip()
                    else:
                        candidate_text = str(item or "").strip()
                    if not candidate_text or not re.search(r"[\u4e00-\u9fff]", candidate_text):
                        continue
                    if re.search(r"^(code|code128|barcode|trace)$", candidate_text, re.I):
                        continue
                    clean_ocr_candidates.append(candidate_text)
            data["ocr_drug_name_candidates"] = clean_ocr_candidates[:5]
            final_ocr_name = str(data.get("ocr_drug_name") or "").strip()
            if final_ocr_name:
                final_lookup_name, final_matched_code = self.lookup_drug_name_from_label_codes(
                    data.get("raw_code_text", ""),
                    data.get("code_text", ""),
                    data.get("product_code", ""),
                    data.get("label_product_code", ""),
                    data.get("trace_code", ""),
                    data.get("label_trace_id", ""),
                    data.get("ocr_text", ""),
                    data.get("ocr_match_text", ""),
                )
                current_match_text = str(data.get("ocr_match_text") or "").strip()
                current_match_is_noise = bool(current_match_text) and not re.search(r"[\u4e00-\u9fff]", current_match_text)
                if final_lookup_name == final_ocr_name and final_matched_code and (not current_match_text or current_match_is_noise):
                    data["ocr_match_text"] = f"{final_matched_code} -> {final_ocr_name}"
            if not clean_ocr_candidates and not data.get("ocr_drug_name"):
                data["ocr_drug_name_score"] = 0
            return data

    def get_chassis_status(self):
        with self.chassis_status_lock:
            return copy.deepcopy(self.latest_chassis_status)

    def announce_voice_text(self, payload):
        text = str(
            payload.get("text")
            or payload.get("message")
            or payload.get("content")
            or ""
        ).strip()
        if not text:
            return {"ok": False, "message": "missing voice text"}
        if len(text) > 160:
            text = text[:160]
        self.voice_text_publisher.publish(String(data=text))
        subscribers = self.voice_text_publisher.get_subscription_count()
        self.get_logger().info(
            f"voice announce requested via web: {text!r}, subscribers={subscribers}"
        )
        return {
            "ok": True,
            "topic": self.voice_text_topic,
            "text": text,
            "subscribers": subscribers,
        }

    def publish_patient_voice_context(self, payload):
        if not isinstance(payload, dict):
            payload = {}
        data = dict(payload)
        data.setdefault("created_at", time.time())
        msg = String()
        msg.data = json.dumps(data, ensure_ascii=False)
        self.patient_voice_context_publisher.publish(msg)
        subscribers = self.patient_voice_context_publisher.get_subscription_count()
        bed = data.get("bed") or ""
        self.get_logger().info(
            f"patient voice context published: bed={bed}, subscribers={subscribers}"
        )
        return {
            "ok": True,
            "topic": self.patient_voice_context_topic,
            "subscribers": subscribers,
        }
    def set_chassis_emergency_stop(self, payload):
        enable = bool(payload.get("enabled", payload.get("emergency_stop", True)))
        if not self.chassis_estop_client.wait_for_service(
            timeout_sec=self.service_timeout_sec
        ):
            return {
                "ok": False,
                "emergency_stop": None,
                "message": "?????????",
                "service": self.chassis_estop_service,
                "chassis_status": self.get_chassis_status(),
            }
        request = SetBool.Request()
        request.data = enable
        future = self.chassis_estop_client.call_async(request)
        response = self.wait_future(future)
        if response is None:
            return {
                "ok": False,
                "emergency_stop": None,
                "message": "??????????",
                "service": self.chassis_estop_service,
                "chassis_status": self.get_chassis_status(),
            }
        deadline = time.monotonic() + 1.0
        latest = self.get_chassis_status()
        while time.monotonic() < deadline:
            latest = self.get_chassis_status()
            if latest.get("emergency_stop") is enable:
                break
            time.sleep(0.05)
        return {
            "ok": bool(response.success),
            "emergency_stop": enable,
            "message": response.message or ("?????" if enable else "?????"),
            "service": self.chassis_estop_service,
            "chassis_status": latest,
        }

    def start_voice_listen(self, payload):
        try:
            duration = int(payload.get("duration_sec") or payload.get("seconds") or 300)
        except Exception:
            duration = 300
        duration = max(1, min(duration, 300))
        command = {"action": "listen", "duration_sec": duration}
        self.asr_control_publisher.publish(
            String(data=json.dumps(command, ensure_ascii=False))
        )
        subscribers = self.asr_control_publisher.get_subscription_count()
        self.get_logger().info(
            f"voice listen requested via web: {duration}s, subscribers={subscribers}"
        )
        return {
            "ok": True,
            "topic": self.asr_control_topic,
            "duration_sec": duration,
            "subscribers": subscribers,
        }

    def set_vision_qr(self, payload):
        enabled = bool(payload.get("enabled"))
        command = {"action": "qr", "enabled": enabled}
        self.vision_control_publisher.publish(
            String(data=json.dumps(command, ensure_ascii=False))
        )
        subscribers = self.vision_control_publisher.get_subscription_count()
        self.get_logger().info(
            f"vision QR control requested via web: enabled={enabled}, subscribers={subscribers}"
        )
        return {
            "ok": True,
            "topic": self.vision_control_topic,
            "enabled": enabled,
            "subscribers": subscribers,
        }

    def trigger_vision_ocr(self, payload):
        mode = str(payload.get("mode") or "single").strip().lower()
        if mode not in {"single", "continuous", "on", "off", "stop"}:
            mode = "single"
        if mode in {"off", "stop"}:
            with self.drug_info_lock:
                self.dashboard_ocr_status.update(
                    {
                        "active": False,
                        "continuous": False,
                        "single_pending": False,
                        "ocr_runtime_enabled": False,
                        "ocr_single_shot_pending": False,
                        "ocr_text": "",
                        "ocr_confidence": 0.0,
                        "ocr_error": "",
                        "ocr_extracted_fields": {},
                        "ocr_drug_name": "",
                        "ocr_updated_at": time.time(),
                    }
                )
        else:
            continuous = mode in {"continuous", "on"}
            with self.drug_info_lock:
                self.dashboard_ocr_status.update(
                    {
                        "active": True,
                        "continuous": continuous,
                        "single_pending": not continuous,
                        "ocr_runtime_enabled": continuous,
                        "ocr_single_shot_pending": not continuous,
                        "ocr_backend": "dashboard_tesseract",
                        "ocr_language": "chi_sim+eng",
                        "ocr_error": "",
                        "ocr_updated_at": time.time(),
                    }
                )
            self.ensure_dashboard_ocr_worker()
        subscribers = 0
        self.get_logger().info(f"dashboard OCR requested via web: mode={mode}")
        return {
            "ok": True,
            "topic": "dashboard_tesseract",
            "mode": mode,
            "subscribers": subscribers,
        }

    def ensure_dashboard_ocr_worker(self):
        if self.dashboard_ocr_thread and self.dashboard_ocr_thread.is_alive():
            return
        self.dashboard_ocr_thread = threading.Thread(
            target=self.dashboard_ocr_worker_loop,
            name="dashboard_ocr_worker",
            daemon=True,
        )
        self.dashboard_ocr_thread.start()

    def dashboard_ocr_worker_loop(self):
        while rclpy.ok():
            with self.drug_info_lock:
                active = bool(self.dashboard_ocr_status.get("active"))
                continuous = bool(self.dashboard_ocr_status.get("continuous"))
                single_pending = bool(self.dashboard_ocr_status.get("single_pending"))
            if not active:
                time.sleep(0.2)
                continue
            if continuous or single_pending:
                self.run_dashboard_ocr_once()
                if single_pending:
                    with self.drug_info_lock:
                        self.dashboard_ocr_status["single_pending"] = False
                        self.dashboard_ocr_status["ocr_single_shot_pending"] = False
                        self.dashboard_ocr_status["ocr_runtime_enabled"] = False
                time.sleep(5.0 if continuous else 0.2)
            else:
                time.sleep(0.2)

    def run_dashboard_ocr_once(self):
        started = time.monotonic()
        temp_path = ""
        try:
            with urllib.request.urlopen("http://127.0.0.1:8090/snapshot.jpg", timeout=2.5) as response:
                image_bytes = response.read()
            if not image_bytes:
                raise RuntimeError("empty camera snapshot")
            image_bytes = self.prepare_dashboard_ocr_image(image_bytes)
            with tempfile.NamedTemporaryFile(prefix="dashboard_ocr_", suffix=".png", delete=False) as temp_file:
                temp_file.write(image_bytes)
                temp_path = temp_file.name
            command = [
                "tesseract",
                temp_path,
                "stdout",
                "-l",
                "chi_sim+eng",
                "--psm",
                "6",
                "tsv",
            ]
            completed = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=6.0,
            )
            if completed.returncode != 0:
                raise RuntimeError((completed.stderr or "tesseract failed").strip())
            text, confidence = self.parse_tesseract_tsv(completed.stdout)
            fields = self.extract_dashboard_ocr_fields(text)
            elapsed_ms = (time.monotonic() - started) * 1000.0
            with self.drug_info_lock:
                self.dashboard_ocr_status.update(
                    {
                        "ocr_text": text[:240],
                        "ocr_confidence": confidence,
                        "ocr_error": "" if text else "dashboard_tesseract: no text",
                        "ocr_worker_busy_ms": elapsed_ms,
                        "ocr_updated_at": time.time(),
                        "ocr_extracted_fields": fields,
                        "ocr_drug_name": fields.get("drug_name", ""),
                    }
                )
        except Exception as exc:
            elapsed_ms = (time.monotonic() - started) * 1000.0
            with self.drug_info_lock:
                self.dashboard_ocr_status.update(
                    {
                        "ocr_error": f"dashboard_tesseract: {exc}",
                        "ocr_worker_busy_ms": elapsed_ms,
                        "ocr_updated_at": time.time(),
                    }
                )
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

    def parse_tesseract_tsv(self, output):
        lines = [line for line in str(output or "").splitlines() if line.strip()]
        if not lines:
            return "", 0.0
        header = lines[0].split("\t")
        try:
            text_idx = header.index("text")
            conf_idx = header.index("conf")
        except ValueError:
            return "", 0.0
        words = []
        confidences = []
        for line in lines[1:]:
            parts = line.split("\t")
            if len(parts) <= max(text_idx, conf_idx):
                continue
            word = parts[text_idx].strip()
            if not word:
                continue
            try:
                conf = float(parts[conf_idx])
            except ValueError:
                conf = -1.0
            if conf < 20:
                continue
            words.append(word)
            confidences.append(conf)
        text = " ".join(words).strip()
        confidence = (sum(confidences) / max(len(confidences), 1) / 100.0) if confidences else 0.0
        return text, confidence

    def normalize_label_code_for_lookup(self, value):
        text = str(value or "").strip().upper()
        if not text:
            return ""
        text = text.replace("?", "C").replace("?", "C")
        text = re.sub(r"[\s\"'`???;?:,]+", "", text)
        return text

    def iter_catalog_medications_for_lookup(self):
        seen = set()
        def emit(med):
            if not isinstance(med, dict):
                return None
            name = str(med.get("medicine_name") or med.get("drug_name") or med.get("name") or "").strip()
            if not name:
                return None
            key = (name, str(med.get("product_code") or ""), str(med.get("trace_id") or med.get("label_trace_id") or ""))
            if key in seen:
                return None
            seen.add(key)
            return med

        # Current/adopted external batch has priority, because real use will
        # import a flexible batch before loading medicines.
        try:
            with self.delivery_batch_lock:
                batch = copy.deepcopy(self.delivery_batch)
        except Exception:
            batch = None
        for container in [batch]:
            if not isinstance(container, dict):
                continue
            for med in container.get("medications") or []:
                item = emit(med)
                if item is not None:
                    yield item
            for stop in container.get("stops") or []:
                if not isinstance(stop, dict):
                    continue
                for patient in stop.get("patients") or []:
                    if not isinstance(patient, dict):
                        continue
                    for med in patient.get("medications") or []:
                        item = emit(med)
                        if item is not None:
                            yield item

        # Built-in patient medication orders are the local demo/catalog fallback.
        for order in PATIENT_MEDICATION_ORDERS:
            if not isinstance(order, dict):
                continue
            for med in order.get("medications") or []:
                item = emit(med)
                if item is not None:
                    yield item

    def build_label_code_name_map(self):
        mapping = {}
        for med in self.iter_catalog_medications_for_lookup():
            name = str(med.get("medicine_name") or med.get("drug_name") or med.get("name") or "").strip()
            if not name:
                continue
            code_keys = [
                med.get("product_code"),
                med.get("trace_id"),
                med.get("label_trace_id"),
                med.get("order_no"),
                med.get("id"),
            ]
            for key in code_keys:
                normalized = self.normalize_label_code_for_lookup(key)
                if normalized:
                    mapping.setdefault(normalized, name)
                    # OCR often drops the leading C or reads it as a currency sign.
                    if normalized.startswith("C") and len(normalized) > 2:
                        mapping.setdefault(normalized[1:], name)
        return mapping

    def lookup_drug_name_from_label_codes(self, *values):
        mapping = self.build_label_code_name_map()
        if not mapping:
            return "", ""
        haystacks = []
        for value in values:
            normalized = self.normalize_label_code_for_lookup(value)
            if normalized:
                haystacks.append(normalized)
                # Also split compound scan strings such as C300210/TRACE-P003-001.
                haystacks.extend(
                    self.normalize_label_code_for_lookup(part)
                    for part in re.split(r"[/|\\]+", str(value or ""))
                    if str(part or "").strip()
                )
        for haystack in haystacks:
            if not haystack:
                continue
            if haystack in mapping:
                return mapping[haystack], haystack
            for code, name in sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True):
                if len(code) >= 5 and code in haystack:
                    return name, code
        return "", ""

    def extract_dashboard_ocr_fields(self, text):
        raw = str(text or "").strip()
        compact = re.sub(r"\s+", "", raw)
        fields = {
            "drug_name": "",
            "spec": "",
            "manufacturer": "",
            "approval_no": "",
            "drug_name_candidates": [],
            "drug_name_score": 0.0,
            "raw_text": raw,
        }
        if not compact:
            return fields

        # Keep these strings as unicode escapes. Direct Chinese literals in this
        # file have been corrupted by Windows/PowerShell deploy scripts before.
        non_medicine_terms = {
            "\u6761\u5f62\u7801",        # ???
            "\u4e8c\u7ef4\u7801",        # ???
            "\u8ffd\u6eaf\u7801",        # ???
            "\u836f\u54c1\u6761\u5f62\u7801",  # ?????
            "\u836f\u54c1",              # ??
            "\u6807\u7b7e",              # ??
            "\u6279\u53f7",              # ??
            "\u5382\u5bb6",              # ??
            "code128",
            "code",
            "barcode",
        }
        known_names = [
            "\u9000\u70e7\u836f",        # ???
            "\u964d\u538b\u836f",        # ???
            "\u964d\u7cd6\u836f",        # ???
            "\u6b62\u75db\u836f",        # ???
            "\u611f\u5192\u836f",        # ???
            "\u6d88\u708e\u836f",        # ???
            "\u6297\u8fc7\u654f\u836f",  # ????
            "\u5934\u5b62\u544b\u8f9b\u916f\u7247",  # ??????
            "\u82ef\u78fa\u9178\u6c28\u6c2f\u5730\u5e73\u7247",  # ????????
            "\u4e91\u5357\u767d\u836f\u521b\u53ef\u8d34",  # ???????
            "\u53f3\u7f8e\u6c99\u82ac\u53e3\u670d\u6eb6\u6db2",  # ????????
        ]
        lowered_compact = compact.lower()
        for term in non_medicine_terms:
            if lowered_compact == term.lower():
                return fields

        # Some labels print the medicine name in small Chinese characters that
        # Tesseract may read poorly, while the same OCR crop still reads the
        # product/trace code.  Use the current batch/catalog code map as a
        # generic fallback instead of hard-coding one demo medicine.
        fallback_name, matched_code = self.lookup_drug_name_from_label_codes(compact, raw)
        if fallback_name:
            fields["drug_name"] = fallback_name
            fields["drug_name_candidates"] = [{
                "text": fallback_name,
                "score": 0.92,
                "source": "dashboard_tesseract_catalog_code_fallback",
                "matched_code": matched_code,
            }]
            fields["drug_name_score"] = 0.92
            return fields

        for name in known_names:
            if name and name in compact:
                fields["drug_name"] = name
                fields["drug_name_candidates"] = [{"text": name, "score": 1.0, "source": "dashboard_tesseract"}]
                fields["drug_name_score"] = 1.0
                return fields

        # Prefer explicit labels on boxes/bottles, e.g. ??????X1 / ??: xxx.
        label_pattern = r"(?:\u836f\u54c1|\u836f\u540d|\u540d\u79f0|\u54c1\u540d)[:\uff1a]?([\u4e00-\u9fffA-Za-z0-9]{2,20})"
        match = re.search(label_pattern, compact)
        if match:
            candidate = re.sub(r"[xX\u00d7*]?\d+.*$", "", match.group(1)).strip()
            normalized_candidate = candidate.lower()
            if (
                len(candidate) >= 2
                and normalized_candidate not in non_medicine_terms
                and re.search(r"[\u4e00-\u9fff]", candidate)
            ):
                fields["drug_name"] = candidate
                fields["drug_name_candidates"] = [{"text": candidate, "score": 0.8, "source": "dashboard_tesseract"}]
                fields["drug_name_score"] = 0.8
                return fields

        # Last-resort generic Chinese medicine-name candidate. Do not create a
        # candidate from Latin-only OCR noise such as "Nu AL".
        generic_candidates = []
        for candidate in re.findall(r"[\u4e00-\u9fff]{2,12}(?:\u836f|\u7247|\u80f6\u56ca|\u9897\u7c92|\u8d34)", compact):
            if candidate in non_medicine_terms:
                continue
            if any(term in candidate for term in non_medicine_terms):
                continue
            generic_candidates.append(candidate)
        if generic_candidates:
            candidate = max(generic_candidates, key=len)
            fields["drug_name"] = candidate
            fields["drug_name_candidates"] = [{"text": candidate, "score": 0.62, "source": "dashboard_tesseract"}]
            fields["drug_name_score"] = 0.62
        return fields

    def prepare_dashboard_ocr_image(self, image_bytes):
        if Image is None:
            return image_bytes
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            crop_box = self.get_dashboard_ocr_crop_box(image.size)
            if crop_box:
                image = image.crop(crop_box)
                # The OCR frame on barcode labels often includes the barcode in
                # its upper half.  Tesseract mistakes barcode stripes for text,
                # so prefer the lower text band inside the green OCR frame.
                if image.width >= image.height and image.height >= 120:
                    top = int(image.height * 0.34)
                    image = image.crop((0, top, image.width, image.height))
            # Tesseract is much faster and less noisy on a cropped high-contrast
            # text region than on the full 1280x960 camera frame.
            image = ImageOps.grayscale(image)
            image = ImageOps.autocontrast(image)
            scale = 3
            image = image.resize((max(1, image.width * scale), max(1, image.height * scale)))
            if ImageFilter is not None:
                image = image.filter(ImageFilter.SHARPEN)
            out = io.BytesIO()
            image.save(out, format="PNG")
            return out.getvalue()
        except Exception:
            return image_bytes

    def get_dashboard_ocr_crop_box(self, image_size):
        width, height = image_size
        if width <= 0 or height <= 0:
            return None
        with self.drug_info_lock:
            status = dict(self.latest_recognition_status)
        rect = status.get("ocr_roi_rect")
        frame_size = status.get("ocr_roi_frame_size")
        if not (isinstance(rect, list) and len(rect) >= 4):
            return None
        if isinstance(frame_size, list) and len(frame_size) >= 2:
            source_w = float(frame_size[0] or width)
            source_h = float(frame_size[1] or height)
        else:
            source_w = float(width)
            source_h = float(height)
        if source_w <= 0 or source_h <= 0:
            return None
        x, y, w, h = [float(value or 0) for value in rect[:4]]
        scale_x = width / source_w
        scale_y = height / source_h
        pad_x = max(8, int(w * scale_x * 0.06))
        pad_y = max(8, int(h * scale_y * 0.10))
        left = max(0, int(round(x * scale_x)) - pad_x)
        top = max(0, int(round(y * scale_y)) - pad_y)
        right = min(width, int(round((x + w) * scale_x)) + pad_x)
        bottom = min(height, int(round((y + h) * scale_y)) + pad_y)
        if right - left < 24 or bottom - top < 24:
            return None
        return (left, top, right, bottom)

    # ---- 闭环 #6: 到位等待病人确认的超时监控 ----

    # 状态机里被认为"已到位等待确认"的状态名
    # task_manager 真实状态: WAITING_DISPENSE_CONFIRMATION
    # 后面几个是兼容历史命名 / 别的子系统

    def get_vision_webrtc_status(self):
        return self.vision_webrtc.status()

    def create_vision_webrtc_answer(self, payload):
        return self.vision_webrtc.create_answer(payload)

    _ARRIVED_STATES = (
        "WAITING_DISPENSE_CONFIRMATION",
        "ARRIVED",
        "AT_TARGET",
        "WAITING_CONFIRM",
    )

    # 批次任务 bed_no = "A-01、A-02"; 拆开分床跟踪
    _BED_SPLIT_RE = re.compile(r"[、,，;；\s]+")

    def _split_beds(self, bed_no):
        raw = (bed_no or "").strip()
        if not raw:
            return []
        parts = [b.strip() for b in self._BED_SPLIT_RE.split(raw) if b.strip()]
        return parts or [raw]

    def _update_arrival_tracker(self, task_id, bed_no, task_state):
        """on_delivery_state 调用; 维护 "到位时刻" 字典。
        状态切到非 ARRIVED 或 task_id 变更 → 清掉记录, 避免误报。
        批次任务 bed_no 形如 "A-01、A-02", 需要拆开按单床记录。"""
        task_id = (task_id or "").strip()
        if not task_id:
            return
        beds = self._split_beds(bed_no)
        if not beds:
            return
        is_arrived = task_state in self._ARRIVED_STATES
        with self.patient_arrival_lock:
            for bed in beds:
                key = (task_id, bed)
                existing = self.patient_arrival_tracker.get(key)
                if is_arrived:
                    if existing is None:
                        self.patient_arrival_tracker[key] = {
                            "arrived_at": time.time(),
                            "alerted": False,
                        }
                    # 已存在就保留 arrived_at, 不要刷新计时
                else:
                    # 任务状态已离开 ARRIVED, 清空
                    if existing is not None:
                        self.patient_arrival_tracker.pop(key, None)

    def _check_arrival_timeouts(self):
        """ROS Timer 周期回调: 扫描所有"已到位"任务, N 秒未确认就推系统消息。"""
        if self.patient_arrived_check_period_sec <= 0:
            return
        now = time.time()
        threshold = self.patient_arrived_timeout_sec
        # 拷一份, 避免长时间锁
        with self.patient_arrival_lock:
            snapshot = list(self.patient_arrival_tracker.items())
        for (task_id, bed_no), info in snapshot:
            if info.get("alerted"):
                continue
            if now - info["arrived_at"] < threshold:
                continue
            # 病人这边已经 confirmed/rejected? 跳过
            ovr = (self.patient_status_overrides or {}).get(bed_no)
            if ovr and ovr.get("status") in ("confirmed", "rejected"):
                with self.patient_arrival_lock:
                    if (task_id, bed_no) in self.patient_arrival_tracker:
                        self.patient_arrival_tracker[(task_id, bed_no)]["alerted"] = True
                continue
            minutes = int(threshold // 60) or 1
            content = (
                f"⏰ 机器人已到位 {minutes} 分钟仍未确认收药, "
                f"请联系床位 {bed_no} 的患者 (派送 {task_id})"
            )
            try:
                self.append_system_message(bed_no, content, delivery_id=task_id)
            except Exception as exc:
                self.get_logger().warn(f"timeout system message failed: {exc}")
            # 同时把 override 设成 timeout (医护端配送批次卡片可据此变橙色)
            try:
                self.patient_status_overrides[bed_no] = {
                    "status": "timeout",
                    "eta": None,
                    "reason": "病人长时间未确认收药",
                }
                if self.patient_state_store is not None:
                    self.patient_state_store.upsert_override(
                        bed_no, "timeout", "病人长时间未确认收药", task_id
                    )
            except Exception as exc:
                self.get_logger().warn(f"timeout override failed: {exc}")
            with self.patient_arrival_lock:
                if (task_id, bed_no) in self.patient_arrival_tracker:
                    self.patient_arrival_tracker[(task_id, bed_no)]["alerted"] = True

    def start_arrival_timeout_timer(self):
        """注册 ROS Timer; 在 main 里 spin 之前调用。"""
        if self.patient_arrived_check_period_sec <= 0:
            self.get_logger().info("arrival timeout monitor disabled")
            return
        try:
            self.patient_arrival_timer = self.create_timer(
                float(self.patient_arrived_check_period_sec),
                self._check_arrival_timeouts,
            )
            self.get_logger().info(
                f"arrival timeout monitor: timeout={self.patient_arrived_timeout_sec}s, "
                f"check_period={self.patient_arrived_check_period_sec}s"
            )
        except Exception as exc:
            self.get_logger().warn(f"create_timer for arrival monitor failed: {exc}")

    # ---- 病人 ⇄ 护士 双向咨询 ----
    def _find_batch_patient_by_bed_locked(self, batch, bed):
        bed = str(bed or "").strip()
        if not bed:
            return None, None
        for stop in batch.get("stops", []) or []:
            for patient in stop.get("patients", []) or []:
                if str(patient.get("bed_no") or "").strip() == bed:
                    return stop, patient
        return None, None

    def record_patient_message_audit(self, bed, action, content="", delivery_id="", nurse_name=""):
        """\u628a\u75c5\u4eba\u54a8\u8be2\u7684\u5df2\u8bfb/\u56de\u590d\u5199\u5165\u5f53\u524d\u914d\u9001\u6279\u6b21\u5ba1\u8ba1\u3002\u5931\u8d25\u4e0d\u5f71\u54cd\u6d88\u606f\u529f\u80fd\u3002"""
        bed = str(bed or "").strip()
        action = str(action or "").strip()
        content = str(content or "").strip()
        delivery_id = str(delivery_id or "").strip()
        nurse_name = str(nurse_name or "").strip() or "web_operator"
        if not bed or not action:
            return {"ok": False, "message": "\u7f3a\u5c11 bed \u6216 action"}
        try:
            with self.delivery_batch_lock:
                batch = self.delivery_batch
                stop, patient = self._find_batch_patient_by_bed_locked(batch, bed)
                patient_name = patient.get("patient_name", "") if patient else ""
                patient_id = patient.get("patient_id", "") if patient else ""
                ward_name = (
                    (patient.get("ward_name", "") if patient else "")
                    or (stop.get("display_name", "") if stop else "")
                    or (stop.get("target_station", "") if stop else "")
                )
                event = "patient_message_reply" if action == "reply" else "patient_message_read"
                if action == "reply":
                    preview = content[:80]
                    message = f"\u62a4\u58eb\u56de\u590d\u75c5\u4eba\u54a8\u8be2\uff1a{bed} {patient_name or ''}\uff0c{preview}"
                else:
                    message = f"\u62a4\u58eb\u5df2\u8bfb\u75c5\u4eba\u54a8\u8be2\uff1a{bed} {patient_name or ''}"
                self.append_batch_audit(
                    batch,
                    event,
                    message,
                    "ok",
                    {
                        "bed_no": bed,
                        "patient_id": patient_id,
                        "patient_name": patient_name,
                        "ward_name": ward_name,
                        "delivery_id": delivery_id,
                        "operator_id": nurse_name,
                        "content_preview": content[:120],
                    },
                )
                self.save_delivery_batch_state_locked(batch)
                self.save_batch_to_db_locked(batch)
                return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}
        except Exception as exc:
            try:
                self.get_logger().warn(f"patient message audit failed: {exc}")
            except Exception:
                pass
            return {"ok": False, "message": str(exc)}

    def _append_message(
        self,
        bed,
        content,
        sender,
        delivery_id="",
        nurse_name="",
    ):
        """内部: 记录一条消息(病人或护士)并 publish ROS topic。"""
        bed = (str(bed or "")).strip()
        content = (str(content or "")).strip()
        delivery_id = (str(delivery_id or "")).strip()
        nurse_name = (str(nurse_name or "")).strip()
        sender = sender if sender in ("patient", "nurse", "system") else "patient"
        if not bed or not content:
            return None
        if len(content) > 500:
            content = content[:500]
        with self.patient_messages_lock:
            self.patient_message_seq += 1
            msg = {
                "id": f"msg-{int(time.time())}-{self.patient_message_seq}",
                "bed": bed,
                "sender": sender,
                "nurse_name": nurse_name if sender == "nurse" else "",
                "content": content,
                "delivery_id": delivery_id,
                "created_at": time.time(),
                # 病人是否已看到这条 (对护士/系统消息有意义)
                "read_by_patient": sender == "patient",
                # 护士是否已看到这条 (对病人消息有意义; system 也算未读以引起护士注意)
                "read_by_nurse": sender == "nurse",
            }
            self.patient_messages.append(msg)
            payload = dict(msg)
        # 持久化 (落盘, 断电恢复用); 失败不影响内存
        if self.patient_state_store is not None:
            try:
                self.patient_state_store.insert_message(payload)
            except Exception as exc:
                self.get_logger().warn(f"patient_state insert_message failed: {exc}")
        try:
            self.patient_message_publisher.publish(
                String(data=json.dumps(payload, ensure_ascii=False))
            )
        except Exception as exc:
            self.get_logger().warn(f"patient_message publish failed: {exc}")
        return payload

    def append_patient_message(self, bed, content, delivery_id=""):
        """病人发起一条消息。"""
        return self._append_message(
            bed=bed, content=content, sender="patient", delivery_id=delivery_id
        )

    def append_system_message(self, bed, content, delivery_id=""):
        """系统事件 (例如病人确认/拒绝/反馈) 写入会话, 让医护立刻看到。
        计为未读 (read_by_nurse=False), 触发病人咨询 tab 红色徽章。"""
        return self._append_message(
            bed=bed, content=content, sender="system", delivery_id=delivery_id
        )

    def append_nurse_reply(self, bed, content, delivery_id="", nurse_name=""):
        """护士回复一条消息。同时把该床位所有未读病人消息标记为护士已读。"""
        msg = self._append_message(
            bed=bed,
            content=content,
            sender="nurse",
            delivery_id=delivery_id,
            nurse_name=nurse_name,
        )
        if msg is not None:
            try:
                self.mark_all_messages_read_by_nurse(bed=bed, audit=False)
            except Exception:
                pass
            try:
                audit_result = self.record_patient_message_audit(
                    bed=bed,
                    action="reply",
                    content=content,
                    delivery_id=delivery_id,
                    nurse_name=nurse_name,
                )
                msg["audit_recorded"] = bool(audit_result.get("ok"))
            except Exception:
                msg["audit_recorded"] = False
        return msg

    @staticmethod
    def _is_hidden_patient_message(msg):
        """Hide internal control events from the nurse consultation inbox."""
        try:
            content = str((msg or {}).get("content") or "")
            sender = str((msg or {}).get("sender") or "")
        except Exception:
            return False
        voice_listen_marker = "\u75c5\u4eba\u5df2\u5f00\u542f\u8bed\u97f3\u5bf9\u8bdd"
        return sender == "system" and voice_listen_marker in content

    def get_patient_messages(self, bed=""):
        """Return patient messages in reverse chronological order."""
        bed = (str(bed or "")).strip()
        with self.patient_messages_lock:
            items = [
                m for m in self.patient_messages
                if not self._is_hidden_patient_message(m)
            ]
        if bed:
            items = [m for m in items if m.get("bed") == bed]
        items.sort(key=lambda m: m.get("created_at", 0.0), reverse=True)
        return items

    def mark_message_read_by_nurse(self, message_id, read=True):
        """护士端点击某条病人消息标记已读。"""
        message_id = str(message_id or "")
        if not message_id:
            return False
        hit = False
        with self.patient_messages_lock:
            for m in self.patient_messages:
                if m.get("id") == message_id:
                    m["read_by_nurse"] = bool(read)
                    hit = True
                    break
        if hit and self.patient_state_store is not None:
            try:
                self.patient_state_store.mark_message_read(
                    message_id, by_nurse=True, read=bool(read)
                )
            except Exception as exc:
                self.get_logger().warn(f"patient_state mark_message_read failed: {exc}")
        return hit

    def mark_all_messages_read_by_nurse(self, bed="", audit=True, nurse_name="web_operator"):
        """\u62a4\u58eb\u7aef\u5168\u90e8\u5df2\u8bfb (\u53ef\u6309 bed \u8fc7\u6ee4)\u3002"""
        bed = (str(bed or "")).strip()
        changed_beds = set()
        with self.patient_messages_lock:
            for m in self.patient_messages:
                if bed and m.get("bed") != bed:
                    continue
                if not m.get("read_by_nurse", False) and m.get("sender") in ("patient", "system"):
                    changed_beds.add(str(m.get("bed") or "").strip())
                m["read_by_nurse"] = True
        if self.patient_state_store is not None:
            try:
                self.patient_state_store.mark_thread_read(bed=bed, by_nurse=True)
            except Exception as exc:
                self.get_logger().warn(f"patient_state mark_thread_read(nurse) failed: {exc}")
        audit_result = None
        if audit:
            targets = [bed] if bed else sorted(x for x in changed_beds if x)
            if not targets and bed:
                targets = [bed]
            for target_bed in targets:
                audit_result = self.record_patient_message_audit(
                    bed=target_bed,
                    action="read",
                    nurse_name=nurse_name,
                )
        return {"ok": True, "changed_beds": sorted(changed_beds), "audit": audit_result}

    def mark_thread_read_by_patient(self, bed):
        """病人端打开会话时,该床位所有护士消息标记已读。"""
        bed = (str(bed or "")).strip()
        if not bed:
            return 0
        n = 0
        with self.patient_messages_lock:
            for m in self.patient_messages:
                if m.get("bed") == bed and not m.get("read_by_patient", False):
                    m["read_by_patient"] = True
                    n += 1
        if n > 0 and self.patient_state_store is not None:
            try:
                self.patient_state_store.mark_thread_read(bed=bed, by_nurse=False)
            except Exception as exc:
                self.get_logger().warn(f"patient_state mark_thread_read(patient) failed: {exc}")
        return n

    def clear_status_override(self, bed=""):
        """清除取药状态 override。bed='' 时清全部, 否则清单床。
        内存 dict 和 SQLite 同步更新; 返回被清除的 bed 列表。"""
        bed = (str(bed or "")).strip()
        cleared = []
        with self.patient_messages_lock:
            if bed:
                if bed in self.patient_status_overrides:
                    self.patient_status_overrides.pop(bed, None)
                    cleared.append(bed)
            else:
                cleared = list(self.patient_status_overrides.keys())
                self.patient_status_overrides.clear()
        if self.patient_state_store is not None:
            try:
                if bed:
                    self.patient_state_store.delete_override(bed)
                else:
                    for b in cleared:
                        self.patient_state_store.delete_override(b)
            except Exception as exc:
                self.get_logger().warn(f"clear_status_override DB sync failed: {exc}")
        return cleared

    def start_web_server(self):
        self.vision_webrtc.start()
        handler = create_dashboard_handler(self)
        self.server = ThreadingHTTPServer((self.host, self.port), handler)
        self.server_thread = threading.Thread(
            target=self.server.serve_forever, daemon=True
        )
        self.server_thread.start()
        self.get_logger().info(f"Web dashboard started: http://localhost:{self.port}")

    def stop_web_server(self):
        self.vision_webrtc.stop()
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None

    def start_patient_server(self):
        """启动病人侧 web 二号 server (端口 patient_port), serve dist/ + /patient/api/*"""
        handler = create_patient_handler(self, self.patient_web_dist_dir)
        self.patient_server = ThreadingHTTPServer(
            (self.host, self.patient_port), handler
        )
        self.patient_server_thread = threading.Thread(
            target=self.patient_server.serve_forever, daemon=True
        )
        self.patient_server_thread.start()
        self.get_logger().info(
            f"Patient web served at http://{self.host}:{self.patient_port}/patient/"
        )

    def stop_patient_server(self):
        if self.patient_server is not None:
            try:
                self.patient_server.shutdown()
                self.patient_server.server_close()
            finally:
                self.patient_server = None
                self.patient_server_thread = None

    def create_task(self, payload):
        if not self.create_task_client.wait_for_service(
            timeout_sec=self.service_timeout_sec
        ):
            return {"accepted": False, "task_id": "", "message": "创建任务服务不可用"}
        request = CreateDeliveryTask.Request()
        request.medicine_name = str(payload.get("medicine_name") or "常规药品")
        request.source_station = str(payload.get("source_station") or "pharmacy")
        request.target_station = str(payload.get("target_station") or "")
        request.patient_id = str(payload.get("patient_id") or "")
        request.patient_name = str(payload.get("patient_name") or "")
        request.ward_id = str(payload.get("ward_id") or "")
        request.bed_no = str(payload.get("bed_no") or "")
        request.product_code = str(payload.get("product_code") or "")
        request.product_model = str(payload.get("product_model") or "")
        request.quantity = str(payload.get("quantity") or "")
        request.trace_id = str(payload.get("trace_id") or "")
        request.order_no = str(payload.get("order_no") or "")
        request.medications_json = str(payload.get("medications_json") or "")
        future = self.create_task_client.call_async(request)
        response = self.wait_future(future)
        if response is None:
            return {"accepted": False, "task_id": "", "message": "创建任务服务超时"}
        return {
            "accepted": bool(response.accepted),
            "task_id": response.task_id,
            "message": response.message,
        }

    def verify_delivery_task(self, payload):
        if not self.verify_task_client.wait_for_service(
            timeout_sec=self.service_timeout_sec
        ):
            return {"verified": False, "message": "扫码校验服务不可用"}
        request = VerifyDeliveryTask.Request()
        request.task_id = str(payload.get("task_id") or "")
        request.product_code = str(payload.get("product_code") or "")
        request.trace_id = str(payload.get("trace_id") or "")
        request.stage = str(payload.get("stage") or "scan")
        future = self.verify_task_client.call_async(request)
        response = self.wait_future(future)
        if response is None:
            return {"verified": False, "message": "扫码校验服务超时"}
        return {
            "verified": bool(response.verified),
            "product_code_matched": bool(response.product_code_matched),
            "trace_id_matched": bool(response.trace_id_matched),
            "expected_product_code": response.expected_product_code,
            "expected_trace_id": response.expected_trace_id,
            "scanned_product_code": response.scanned_product_code,
            "scanned_trace_id": response.scanned_trace_id,
            "message": response.message,
            "stage": response.stage,
            "state_changed": bool(response.state_changed),
            "task_state": response.task_state,
            "confirmed_at": response.confirmed_at,
            "matched_medicine_name": response.matched_medicine_name,
            "medication_total_count": int(response.medication_total_count),
            "medication_verified_count": int(response.medication_verified_count),
            "medications_json": response.medications_json,
        }

    def get_patient_orders(self):
        return {"orders": PATIENT_MEDICATION_ORDERS}

    def build_delivery_batch_report(self):
        batch = self.get_delivery_batch()
        return build_report(batch, self.now_text())

    def build_delivery_batch_report_csv(self):
        report = self.build_delivery_batch_report()
        return build_report_csv(report)

    def cancel_task(self, payload):
        if not self.cancel_task_client.wait_for_service(
            timeout_sec=self.service_timeout_sec
        ):
            return {"success": False, "message": "取消任务服务不可用"}
        request = CancelDeliveryTask.Request()
        request.task_id = str(payload.get("task_id") or "")
        future = self.cancel_task_client.call_async(request)
        response = self.wait_future(future)
        if response is None:
            return {"success": False, "message": "取消任务服务超时"}
        return {"success": bool(response.success), "message": response.message}

    def wait_future(self, future):
        deadline = time.monotonic() + self.service_timeout_sec
        while time.monotonic() < deadline:
            if future.done():
                return future.result()
            time.sleep(0.02)
        return None

    def close_delivery_database(self):
        if self.delivery_db is None:
            return
        try:
            with self.delivery_db_lock:
                self.delivery_db.close()
        except Exception as exc:
            self.get_logger().error(f"failed to close delivery database: {exc}")
        finally:
            self.delivery_db = None

    def close_patient_state_store(self):
        if getattr(self, "patient_state_store", None) is None:
            return
        try:
            self.patient_state_store.close()
        except Exception as exc:
            self.get_logger().warn(f"close patient_state_store failed: {exc}")
        finally:
            self.patient_state_store = None

def main():
    rclpy.init()
    node = MedicineWebDashboard()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    node.start_web_server()
    node.start_patient_server()
    node.start_arrival_timeout_timer()
    try:
        executor.spin()
    finally:
        node.close_delivery_database()
        node.close_patient_state_store()
        node.stop_web_server()
        node.stop_patient_server()
        executor.remove_node(node)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
