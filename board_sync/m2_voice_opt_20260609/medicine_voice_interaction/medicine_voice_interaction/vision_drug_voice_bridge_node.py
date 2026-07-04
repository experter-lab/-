import json
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from medicine_interfaces.msg import DrugInfo


class VisionDrugVoiceBridgeNode(Node):
    def __init__(self):
        super().__init__("medicine_vision_drug_voice_bridge")
        self.declare_parameter("drug_info_topic", "/medicine/drug_info")
        self.declare_parameter("recognition_status_topic", "/medicine/drug_recognition_status")
        self.declare_parameter("voice_topic", "/medicine/voice_text")
        self.declare_parameter("ai_context_topic", "/medicine/vision_drug_context")
        self.declare_parameter("min_confidence", 0.50)
        self.declare_parameter("announce_cooldown_sec", 0.0)
        self.declare_parameter("context_cooldown_sec", 8.0)
        self.declare_parameter("announce_loaded_only", False)
        self.declare_parameter("announce_repeat_same_drug", False)
        self.declare_parameter("publish_ai_context", True)
        self.declare_parameter("enable_voice_announce", True)

        self.voice_pub = self.create_publisher(String, self.string_param("voice_topic"), 10)
        self.ai_context_pub = self.create_publisher(String, self.string_param("ai_context_topic"), 10)
        self.create_subscription(DrugInfo, self.string_param("drug_info_topic"), self.on_drug_info, 10)
        self.create_subscription(String, self.string_param("recognition_status_topic"), self.on_status, 10)

        self.min_confidence = float(self.get_parameter("min_confidence").value)
        self.announce_cooldown_sec = float(self.get_parameter("announce_cooldown_sec").value)
        self.context_cooldown_sec = float(self.get_parameter("context_cooldown_sec").value)
        self.announce_loaded_only = bool(self.get_parameter("announce_loaded_only").value)
        self.announce_repeat_same_drug = bool(self.get_parameter("announce_repeat_same_drug").value)
        self.publish_ai_context = bool(self.get_parameter("publish_ai_context").value)
        self.enable_voice_announce = bool(self.get_parameter("enable_voice_announce").value)
        self.last_key = ""
        self.last_context_key = ""
        self.last_announce_at = 0.0
        self.last_context_at = 0.0
        self.latest_status = {}

        self.get_logger().info(
            "Vision drug voice bridge started. "
            f"drug_info={self.string_param('drug_info_topic')}, voice={self.string_param('voice_topic')}"
        )

    def string_param(self, name):
        return self.get_parameter(name).get_parameter_value().string_value

    def on_status(self, msg):
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        if isinstance(payload, dict):
            self.latest_status = payload

    def on_drug_info(self, msg):
        drug_name = str(msg.drug_name or "").strip()
        if not drug_name or drug_name == "-":
            return
        confidence = float(msg.confidence)
        if confidence < self.min_confidence:
            return
        if self.announce_loaded_only and not bool(msg.loaded):
            return

        product_code = str(self.latest_status.get("label_product_code") or "").strip()
        product_model = str(self.latest_status.get("label_product_model") or "").strip()
        ocr_text = str(self.latest_status.get("ocr_text") or "").strip()
        key = "|".join([drug_name, str(msg.drug_type or ""), product_code, product_model])
        now = time.monotonic()

        if self.publish_ai_context and (
            key != self.last_context_key or now - self.last_context_at >= self.context_cooldown_sec
        ):
            self.publish_context(msg, product_code, product_model, ocr_text)
            self.last_context_key = key
            self.last_context_at = now

        should_announce = key != self.last_key
        if self.announce_repeat_same_drug and self.announce_cooldown_sec > 0:
            should_announce = should_announce or now - self.last_announce_at >= self.announce_cooldown_sec
        if self.enable_voice_announce and should_announce:
            self.publish_announcement(msg, product_code)
            self.last_announce_at = now
            self.last_key = key

    def publish_context(self, msg, product_code, product_model, ocr_text):
        parts = [f"摄像头当前识别到药品：{msg.drug_name}"]
        if msg.drug_type:
            parts.append(f"类型：{msg.drug_type}")
        if product_code:
            parts.append(f"产品编码：{product_code}")
        if product_model:
            parts.append(f"产品型号：{product_model}")
        if ocr_text:
            parts.append(f"OCR识别文字：{ocr_text[:160]}")
        parts.append("如果用户追问“这个药”，请优先按这个药品理解，并结合知识库做安全科普。")
        payload = String()
        payload.data = "；".join(parts)
        self.ai_context_pub.publish(payload)
        self.get_logger().info(f"Vision context published: {payload.data}")

    def publish_announcement(self, msg, product_code):
        if product_code:
            text = f"识别到{msg.drug_name}，产品编码{product_code}，请核对患者和用法用量。"
        else:
            text = f"识别到{msg.drug_name}，请核对患者和用法用量。"
        payload = String()
        payload.data = text
        self.voice_pub.publish(payload)
        self.get_logger().info(f"Vision voice announced: {text}")


def main(args=None):
    rclpy.init(args=args)
    node = VisionDrugVoiceBridgeNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
