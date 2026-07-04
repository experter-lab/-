import json
import re
import threading
import time

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import String

try:
    import serial
except ImportError:
    serial = None


DEFAULT_COMMAND_MAP = json.dumps({
    "\u9001\u836f\u5230A\u75c5\u623f": "delivery_to_ward_a",
    "\u53bbA\u75c5\u623f": "delivery_to_ward_a",
    "A\u75c5\u623f": "delivery_to_ward_a",
    "\u9001\u836f\u5230B\u75c5\u623f": "delivery_to_ward_b",
    "\u53bbB\u75c5\u623f": "delivery_to_ward_b",
    "B\u75c5\u623f": "delivery_to_ward_b",
    "\u9001\u836f\u5230C\u75c5\u623f": "delivery_to_ward_c",
    "\u53bbC\u75c5\u623f": "delivery_to_ward_c",
    "C\u75c5\u623f": "delivery_to_ward_c",
    "\u9001\u836f\u5230\u62a4\u58eb\u7ad9": "delivery_to_nurse_station",
    "\u53bb\u62a4\u58eb\u7ad9": "delivery_to_nurse_station",
    "\u62a4\u58eb\u7ad9": "delivery_to_nurse_station",
    "\u53d6\u6d88\u4efb\u52a1": "cancel_task",
    "\u505c\u6b62\u4efb\u52a1": "cancel_task",
    "\u67e5\u8be2\u72b6\u6001": "query_status",
    "\u4efb\u52a1\u72b6\u6001": "query_status",
    "\u8fd4\u56de\u836f\u623f": "return_to_pharmacy",
    "\u56de\u5230\u836f\u623f": "return_to_pharmacy"
}, ensure_ascii=False)


class M2VoiceBridgeNode(Node):
    def __init__(self):
        super().__init__("medicine_m2_voice_bridge")
        self.declare_parameter("serial_port", "/dev/ttyACM0")
        self.declare_parameter("baudrate", 115200)
        self.declare_parameter("expected_user_id", 0x01)
        self.declare_parameter("command_topic", "/medicine/voice_command")
        self.declare_parameter("raw_topic", "/medicine/m2_voice_raw")
        self.declare_parameter("publish_raw", True)
        self.declare_parameter("publish_unmapped_text", False)
        self.declare_parameter("publish_unframed_bytes", True)
        self.declare_parameter("raw_hex_max_bytes", 64)
        self.declare_parameter("command_map_json", DEFAULT_COMMAND_MAP)
        self.declare_parameter("read_timeout_sec", 0.1)
        self.declare_parameter("reconnect_interval_sec", 2.0)
        self.declare_parameter("deduplicate_window_sec", 1.0)
        self.declare_parameter("max_frame_length", 4096)

        self.serial_port = self.get_parameter("serial_port").get_parameter_value().string_value
        self.baudrate = self.get_parameter("baudrate").get_parameter_value().integer_value
        self.expected_user_id = self.get_parameter("expected_user_id").get_parameter_value().integer_value
        self.command_topic = self.get_parameter("command_topic").get_parameter_value().string_value
        self.raw_topic = self.get_parameter("raw_topic").get_parameter_value().string_value
        self.publish_raw = self.get_parameter("publish_raw").get_parameter_value().bool_value
        self.publish_unmapped_text = self.get_parameter("publish_unmapped_text").get_parameter_value().bool_value
        self.publish_unframed_bytes = self.get_parameter("publish_unframed_bytes").get_parameter_value().bool_value
        self.raw_hex_max_bytes = self.get_parameter("raw_hex_max_bytes").get_parameter_value().integer_value
        self.read_timeout_sec = self.get_parameter("read_timeout_sec").get_parameter_value().double_value
        self.reconnect_interval_sec = self.get_parameter("reconnect_interval_sec").get_parameter_value().double_value
        self.deduplicate_window_sec = self.get_parameter("deduplicate_window_sec").get_parameter_value().double_value
        self.max_frame_length = self.get_parameter("max_frame_length").get_parameter_value().integer_value
        self.command_map = self.load_command_map(
            self.get_parameter("command_map_json").get_parameter_value().string_value
        )

        self.command_publisher = self.create_publisher(String, self.command_topic, 10)
        self.raw_publisher = self.create_publisher(String, self.raw_topic, 10) if self.publish_raw else None
        self.running = True
        self.serial_handle = None
        self.buffer = bytearray()
        self.last_command = ""
        self.last_command_time = 0.0
        self.worker = threading.Thread(target=self.serial_worker, daemon=True)

        if serial is None:
            self.get_logger().error("pyserial is not installed. Please install python3-serial before using M2 voice bridge.")
            return

        self.worker.start()
        self.get_logger().info(
            f"M2 voice bridge started. port={self.serial_port}, baudrate={self.baudrate}, command_topic={self.command_topic}"
        )

    def load_command_map(self, text):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            self.get_logger().warn(f"Invalid command_map_json: {exc}")
            return {}
        if not isinstance(data, dict):
            self.get_logger().warn("command_map_json must be a JSON object")
            return {}
        return {str(key): str(value) for key, value in data.items()}

    def serial_worker(self):
        while self.running and rclpy.ok():
            if self.serial_handle is None:
                self.open_serial()
                if self.serial_handle is None:
                    time.sleep(self.reconnect_interval_sec)
                    continue
            try:
                data = self.serial_handle.read(256)
                if data:
                    self.buffer.extend(data)
                    self.parse_buffer()
            except Exception as exc:
                self.get_logger().warn(f"M2 serial read failed: {exc}")
                self.close_serial()
                time.sleep(self.reconnect_interval_sec)

    def open_serial(self):
        try:
            self.serial_handle = serial.Serial(
                self.serial_port,
                self.baudrate,
                timeout=max(0.01, float(self.read_timeout_sec)),
            )
            self.buffer.clear()
            self.get_logger().info(f"Connected to M2 voice module: {self.serial_port}")
        except Exception as exc:
            self.serial_handle = None
            self.get_logger().warn(f"Could not open M2 serial port {self.serial_port}: {exc}")

    def close_serial(self):
        if self.serial_handle is not None:
            try:
                self.serial_handle.close()
            except Exception:
                pass
        self.serial_handle = None

    def parse_buffer(self):
        while len(self.buffer) >= 8:
            sync_index = self.buffer.find(b"\xA5")
            if sync_index < 0:
                self.handle_unframed_bytes(bytes(self.buffer))
                self.buffer.clear()
                return
            if sync_index > 0:
                self.handle_unframed_bytes(bytes(self.buffer[:sync_index]))
                del self.buffer[:sync_index]
            if len(self.buffer) < 8:
                return

            if self.expected_user_id >= 0 and self.buffer[1] != self.expected_user_id:
                dropped = bytes(self.buffer[:min(len(self.buffer), self.raw_hex_max_bytes)])
                bad_uid = self.buffer[1]
                del self.buffer[0]
                self.publish_raw_bytes("invalid_user_id_frame", dropped)
                self.get_logger().warn(f"Dropped M2 frame with unexpected user id: 0x{bad_uid:02X}")
                continue

            msg_len = self.buffer[3] | (self.buffer[4] << 8)
            frame_len = 7 + msg_len + 1
            if frame_len > self.max_frame_length:
                dropped = bytes(self.buffer[:min(len(self.buffer), self.raw_hex_max_bytes)])
                bad = self.buffer.pop(0)
                self.publish_raw_bytes("invalid_frame_header", dropped)
                self.get_logger().warn(f"Dropped invalid M2 frame sync byte: 0x{bad:02X}")
                continue
            if len(self.buffer) < frame_len:
                return

            frame = bytes(self.buffer[:frame_len])
            del self.buffer[:frame_len]
            if not self.checksum_ok(frame):
                self.publish_raw_bytes("invalid_checksum_frame", frame)
                self.get_logger().warn("Dropped M2 frame with invalid checksum")
                continue
            msg_type = frame[2]
            content = frame[7:-1]
            self.handle_payload(msg_type, content, frame)

    def checksum_ok(self, frame):
        expected = ((~sum(frame[:-1])) & 0xFF) + 1
        expected &= 0xFF
        return expected == frame[-1]

    def handle_unframed_bytes(self, data):
        if self.publish_unframed_bytes:
            self.publish_raw_bytes("unframed_bytes", data)

    def handle_payload(self, msg_type, payload, frame):
        text = self.decode_payload(payload)
        if text:
            self.handle_text(text, msg_type, frame)
            return
        self.publish_raw_bytes(f"frame_type_0x{msg_type:02X}", frame)

    def decode_payload(self, payload):
        text = ""
        for encoding in ("utf-8", "gb18030", "gbk"):
            try:
                text = payload.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        if not text:
            return ""
        text = text.strip()
        if not text:
            return ""
        printable_count = sum(1 for char in text if char.isprintable() or char in "\r\n\t")
        if printable_count / max(1, len(text)) < 0.8:
            return ""
        return text

    def handle_text(self, text, msg_type=None, frame=None):
        prefix = f"frame_type=0x{msg_type:02X}; " if msg_type is not None else ""
        self.get_logger().info(f"M2 raw feedback: {prefix}{text}")
        if self.raw_publisher is not None:
            self.raw_publisher.publish(String(data=f"{prefix}{text}"))

        command = self.text_to_command(text)
        if command:
            self.publish_command(command)
            return
        if self.publish_unmapped_text:
            normalized = self.clean_text(text)
            if normalized:
                self.publish_command(normalized)

    def text_to_command(self, text):
        candidates = self.extract_candidates(text)
        for candidate in candidates:
            normalized = self.normalize_text(candidate)
            for phrase, command in self.command_map.items():
                if self.normalize_text(phrase) in normalized:
                    return command
        return ""

    def extract_candidates(self, text):
        candidates = [text]
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return candidates
        self.collect_strings(data, candidates)
        return candidates

    def collect_strings(self, value, output):
        if isinstance(value, str):
            output.append(value)
            return
        if isinstance(value, dict):
            for item in value.values():
                self.collect_strings(item, output)
            return
        if isinstance(value, list):
            for item in value:
                self.collect_strings(item, output)

    def clean_text(self, text):
        if text.startswith("{"):
            candidates = [item for item in self.extract_candidates(text) if item != text]
            return candidates[0].strip() if candidates else ""
        return text.strip()

    def normalize_text(self, text):
        return re.sub(r"\s+", "", text).lower()

    def publish_raw_bytes(self, label, data):
        if self.raw_publisher is None:
            return
        if not data:
            return
        limit = max(1, int(self.raw_hex_max_bytes))
        shown = data[:limit]
        hex_text = " ".join(f"{byte:02X}" for byte in shown)
        suffix = "" if len(data) <= limit else f" ... ({len(data)} bytes total)"
        self.raw_publisher.publish(String(data=f"{label}: {hex_text}{suffix}"))

    def publish_command(self, command):
        now = time.monotonic()
        if command == self.last_command and now - self.last_command_time < self.deduplicate_window_sec:
            self.get_logger().warn(f"Skipped duplicate voice command: {command}")
            return
        self.last_command = command
        self.last_command_time = now
        self.command_publisher.publish(String(data=command))
        self.get_logger().info(f"Published voice command: {command}")

    def destroy_node(self):
        self.running = False
        self.close_serial()
        if self.worker.is_alive():
            self.worker.join(timeout=1.0)
        super().destroy_node()


def main():
    rclpy.init()
    node = M2VoiceBridgeNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        try:
            if rclpy.ok():
                rclpy.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    main()
