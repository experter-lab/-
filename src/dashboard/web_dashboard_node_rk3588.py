import copy
import json
import math
import os
import threading
import time
from http.server import ThreadingHTTPServer

import rclpy
from ament_index_python.packages import get_package_share_directory
from rclpy.duration import Duration
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
import yaml

from medicine_interfaces.msg import DeliveryState, DrugInfo
from medicine_interfaces.srv import (
    CancelDeliveryTask,
    CreateDeliveryTask,
    VerifyDeliveryTask,
)
from std_msgs.msg import String

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
            "delivery_batch_state_file",
            os.path.expanduser(
                "~/.local/share/medicine_robot/delivery_batch_state.json"
            ),
        )

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
        self.delivery_batch_state_file = (
            self.get_parameter("delivery_batch_state_file")
            .get_parameter_value()
            .string_value
        )
        self.state_lock = threading.Lock()
        self.drug_info_lock = threading.Lock()
        self.chassis_status_lock = threading.Lock()
        self.scan_status_lock = threading.Lock()
        self.latest_state = self.empty_state()
        self.latest_drug_info = self.empty_drug_info()
        self.latest_recognition_status = {}
        self.latest_chassis_status = self.empty_chassis_status()
        self.latest_scan_status = self.empty_scan_status()
        self._last_scan_status_update = 0.0
        self.tf_buffer = None
        self.tf_listener = None
        if self.enable_tf_listener and tf2_ros is not None:
            self.tf_buffer = tf2_ros.Buffer()
            self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        self.stations = self.load_stations(self.stations_file)
        self.delivery_batch_lock = threading.Lock()
        self.delivery_db_lock = threading.Lock()
        self.delivery_db = self.init_delivery_database()
        self.delivery_batch = self.load_delivery_batch_state()
        self.create_task_client = self.create_client(
            CreateDeliveryTask, "/medicine/create_delivery_task"
        )
        self.cancel_task_client = self.create_client(
            CancelDeliveryTask, "/medicine/cancel_delivery_task"
        )
        self.verify_task_client = self.create_client(
            VerifyDeliveryTask, "/medicine/verify_delivery_task"
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
            "ocr_enabled": False,
            "ocr_available": False,
            "ocr_text": "",
            "ocr_confidence": 0.0,
            "ocr_language": "",
            "ocr_backend": "",
            "ocr_error": "",
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

    def get_state(self):
        with self.state_lock:
            return dict(self.latest_state)

    def get_drug_info(self):
        with self.drug_info_lock:
            data = dict(self.latest_drug_info)
            status = dict(self.latest_recognition_status)
            label_fields = (
                status.get("label_fields")
                if isinstance(status.get("label_fields"), dict)
                else {}
            )
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
                    "ocr_enabled": bool(status.get("ocr_enabled", False)),
                    "ocr_available": bool(status.get("ocr_available", False)),
                    "ocr_text": status.get("ocr_text", ""),
                    "ocr_confidence": float(status.get("ocr_confidence", 0.0) or 0.0),
                    "ocr_language": status.get("ocr_language", ""),
                    "ocr_backend": status.get("ocr_backend", ""),
                    "ocr_error": status.get("ocr_error", ""),
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
                        "label_trace_id", label_fields.get("pdi", "")
                    ),
                }
            )
            return data

    def get_chassis_status(self):
        with self.chassis_status_lock:
            return copy.deepcopy(self.latest_chassis_status)

    def start_web_server(self):
        handler = create_dashboard_handler(self)
        self.server = ThreadingHTTPServer((self.host, self.port), handler)
        self.server_thread = threading.Thread(
            target=self.server.serve_forever, daemon=True
        )
        self.server_thread.start()
        self.get_logger().info(f"Web dashboard started: http://localhost:{self.port}")

    def stop_web_server(self):
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None

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

def main():
    rclpy.init()
    node = MedicineWebDashboard()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    node.start_web_server()
    try:
        executor.spin()
    finally:
        node.close_delivery_database()
        node.stop_web_server()
        executor.remove_node(node)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
