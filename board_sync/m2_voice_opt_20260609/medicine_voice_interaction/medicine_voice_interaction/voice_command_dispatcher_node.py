import re
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from medicine_interfaces.msg import DeliveryState
from medicine_interfaces.srv import CancelDeliveryTask, CreateDeliveryTask


class VoiceCommandDispatcherNode(Node):
    def __init__(self):
        super().__init__("medicine_voice_command_dispatcher")
        self.declare_parameter("voice_words_topic", "/voice_words")
        self.declare_parameter("command_topic", "/medicine/voice_command")
        self.declare_parameter("voice_topic", "/medicine/voice_text")
        self.declare_parameter("source_station", "pharmacy")
        self.declare_parameter("default_medicine", "\u5e38\u89c4\u836f\u54c1")
        self.declare_parameter("default_patient", "")
        self.declare_parameter("deduplicate_window_sec", 1.0)
        self.declare_parameter("service_timeout_sec", 2.0)

        self.voice_words_topic = self.get_parameter("voice_words_topic").get_parameter_value().string_value
        self.command_topic = self.get_parameter("command_topic").get_parameter_value().string_value
        self.voice_topic = self.get_parameter("voice_topic").get_parameter_value().string_value
        self.source_station = self.get_parameter("source_station").get_parameter_value().string_value
        self.default_medicine = self.get_parameter("default_medicine").get_parameter_value().string_value
        self.default_patient = self.get_parameter("default_patient").get_parameter_value().string_value
        self.deduplicate_window_sec = self.get_parameter("deduplicate_window_sec").get_parameter_value().double_value
        self.service_timeout_sec = self.get_parameter("service_timeout_sec").get_parameter_value().double_value

        self.voice_pub = self.create_publisher(String, self.voice_topic, 10)
        self.create_task_client = self.create_client(CreateDeliveryTask, "/medicine/create_delivery_task")
        self.cancel_task_client = self.create_client(CancelDeliveryTask, "/medicine/cancel_delivery_task")
        self.state_sub = self.create_subscription(DeliveryState, "/medicine/delivery_state", self.on_delivery_state, 10)

        self.text_subscriptions = []
        self.text_subscriptions.append(self.create_subscription(String, self.voice_words_topic, self.on_text_command, 10))
        if self.command_topic != self.voice_words_topic:
            self.text_subscriptions.append(self.create_subscription(String, self.command_topic, self.on_text_command, 10))

        self.last_key = ""
        self.last_time = 0.0
        self.latest_state = None
        self.station_names = {
            "ward_a": "A\u75c5\u623f",
            "ward_b": "B\u75c5\u623f",
            "ward_c": "C\u75c5\u623f",
            "nurse_station": "\u62a4\u58eb\u7ad9",
            "pharmacy": "\u836f\u623f",
        }
        self.get_logger().info(
            f"Voice command dispatcher started. voice_words_topic={self.voice_words_topic}, command_topic={self.command_topic}"
        )

    def on_delivery_state(self, msg):
        self.latest_state = msg

    def on_text_command(self, msg):
        text = (msg.data or "").strip()
        if not text:
            return
        action = self.parse_command(text)
        if action is None:
            self.get_logger().info(f"Ignored unmapped voice text: {text}")
            return
        key = f"{action[0]}:{action[1] if len(action) > 1 else ''}"
        now = time.monotonic()
        if key == self.last_key and now - self.last_time < self.deduplicate_window_sec:
            return
        self.last_key = key
        self.last_time = now
        self.dispatch(action, text)

    def parse_command(self, text):
        normalized = self.normalize(text)
        if normalized in {"delivery_to_ward_a", "deliverytowarda"}:
            return ("create", "ward_a")
        if normalized in {"delivery_to_ward_b", "deliverytowardb"}:
            return ("create", "ward_b")
        if normalized in {"delivery_to_ward_c", "deliverytowardc"}:
            return ("create", "ward_c")
        if normalized in {"delivery_to_nurse_station", "deliverytonursestation"}:
            return ("create", "nurse_station")
        if normalized in {"return_to_pharmacy", "returntopharmacy"}:
            return ("create", "pharmacy")
        if normalized in {"cancel_task", "canceltask"}:
            return ("cancel", "")
        if normalized in {"query_status", "querystatus"}:
            return ("query", "")
        if self.contains_any(normalized, ["\u9001\u836f\u5230a\u75c5\u623f", "\u53bba\u75c5\u623f", "a\u75c5\u623f", "\u9001\u836f\u5230a", "\u53bba"]):
            return ("create", "ward_a")
        if self.contains_any(normalized, ["\u9001\u836f\u5230b\u75c5\u623f", "\u53bbb\u75c5\u623f", "b\u75c5\u623f", "\u9001\u836f\u5230b", "\u53bbb"]):
            return ("create", "ward_b")
        if self.contains_any(normalized, ["\u9001\u836f\u5230c\u75c5\u623f", "\u53bbc\u75c5\u623f", "c\u75c5\u623f", "\u9001\u836f\u5230c", "\u53bbc"]):
            return ("create", "ward_c")
        if self.contains_any(normalized, ["\u9001\u836f\u5230\u62a4\u58eb\u7ad9", "\u53bb\u62a4\u58eb\u7ad9", "\u62a4\u58eb\u7ad9"]):
            return ("create", "nurse_station")
        if self.contains_any(normalized, ["\u8fd4\u56de\u836f\u623f", "\u56de\u5230\u836f\u623f", "\u53bb\u836f\u623f", "\u836f\u623f"]):
            return ("create", "pharmacy")
        if self.contains_any(normalized, ["\u53d6\u6d88\u4efb\u52a1", "\u505c\u6b62\u4efb\u52a1", "\u7ec8\u6b62\u4efb\u52a1", "\u53d6\u6d88\u9001\u836f"]):
            return ("cancel", "")
        if self.contains_any(normalized, ["\u67e5\u8be2\u72b6\u6001", "\u4efb\u52a1\u72b6\u6001", "\u73b0\u5728\u72b6\u6001", "\u5f53\u524d\u72b6\u6001"]):
            return ("query", "")
        if self.contains_any(normalized, ["\u786e\u8ba4\u53d6\u836f", "\u5df2\u7ecf\u53d6\u836f", "\u53d6\u836f\u5b8c\u6210"]):
            return ("ack", "")
        return None

    def normalize(self, text):
        text = text.lower()
        return re.sub(r"[\s,.;:!?\u3002\uff0c\uff1b\uff1a\uff01\uff1f\u3001\uff08\uff09()\[\]{}<>\u300a\u300b\"'`]+", "", text)

    def contains_any(self, text, phrases):
        return any(self.normalize(phrase) in text for phrase in phrases)

    def dispatch(self, action, original_text):
        kind = action[0]
        if kind == "create":
            self.create_delivery_task(action[1], original_text)
            return
        if kind == "cancel":
            self.cancel_delivery_task()
            return
        if kind == "query":
            self.publish_status()
            return
        if kind == "ack":
            self.publish_voice("\u53d6\u836f\u786e\u8ba4\u9700\u8981\u626b\u7801\u6821\u9a8c\uff0c\u8bf7\u626b\u63cf\u836f\u54c1\u7801")

    def create_delivery_task(self, target_station, original_text):
        if not self.create_task_client.wait_for_service(timeout_sec=self.service_timeout_sec):
            self.publish_voice("\u9001\u836f\u4efb\u52a1\u670d\u52a1\u672a\u542f\u52a8")
            return
        request = CreateDeliveryTask.Request()
        request.target_station = target_station
        request.source_station = self.source_station
        request.medicine_name = self.default_medicine
        request.patient_id = self.default_patient
        request.product_code = ""
        request.product_model = ""
        request.quantity = ""
        request.trace_id = ""
        request.order_no = ""
        future = self.create_task_client.call_async(request)
        future.add_done_callback(lambda fut: self.on_create_task_done(fut, target_station, original_text))

    def on_create_task_done(self, future, target_station, original_text):
        try:
            response = future.result()
        except Exception as exc:
            self.get_logger().error(f"Create delivery task failed: {exc}")
            self.publish_voice("\u521b\u5efa\u9001\u836f\u4efb\u52a1\u5931\u8d25")
            return
        target_name = self.station_names.get(target_station, target_station)
        if response.accepted:
            self.get_logger().info(f"Voice command accepted: {original_text} -> {target_station}, task_id={response.task_id}")
            self.publish_voice(f"\u5df2\u521b\u5efa\u9001\u836f\u5230{target_name}\u7684\u4efb\u52a1")
        else:
            self.get_logger().warn(f"Voice command rejected: {response.message}")
            self.publish_voice(response.message or "\u9001\u836f\u4efb\u52a1\u672a\u63a5\u53d7")

    def cancel_delivery_task(self):
        if not self.cancel_task_client.wait_for_service(timeout_sec=self.service_timeout_sec):
            self.publish_voice("\u53d6\u6d88\u4efb\u52a1\u670d\u52a1\u672a\u542f\u52a8")
            return
        request = CancelDeliveryTask.Request()
        request.task_id = ""
        future = self.cancel_task_client.call_async(request)
        future.add_done_callback(self.on_cancel_task_done)

    def on_cancel_task_done(self, future):
        try:
            response = future.result()
        except Exception as exc:
            self.get_logger().error(f"Cancel delivery task failed: {exc}")
            self.publish_voice("\u53d6\u6d88\u9001\u836f\u4efb\u52a1\u5931\u8d25")
            return
        self.publish_voice(response.message or ("\u9001\u836f\u4efb\u52a1\u5df2\u53d6\u6d88" if response.success else "\u5f53\u524d\u6ca1\u6709\u53ef\u53d6\u6d88\u7684\u4efb\u52a1"))

    def publish_status(self):
        if self.latest_state is None:
            self.publish_voice("\u6682\u65f6\u6ca1\u6709\u4efb\u52a1\u72b6\u6001")
            return
        self.publish_voice(self.latest_state.message or self.latest_state.state)

    def publish_voice(self, text):
        msg = String()
        msg.data = text
        self.voice_pub.publish(msg)
        self.get_logger().info(f"VOICE: {text}")


def main():
    rclpy.init()
    node = VoiceCommandDispatcherNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
