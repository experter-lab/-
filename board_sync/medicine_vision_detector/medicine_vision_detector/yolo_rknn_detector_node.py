import json
import os
import time

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

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


COCO_LABELS = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
    "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake",
    "chair", "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop",
    "mouse", "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
    "toothbrush",
]


class YoloRknnDetector(Node):
    def __init__(self):
        super().__init__("medicine_yolo_rknn_detector")
        self.declare_parameter("model_path", "")
        self.declare_parameter("label_file", "")
        self.declare_parameter("labels", ",".join(COCO_LABELS))
        self.declare_parameter("class_filter", "person,bottle,box,package,medicine,drug,label")
        self.declare_parameter("camera_device", "/dev/video21")
        self.declare_parameter("camera_width", 1280)
        self.declare_parameter("camera_height", 1024)
        self.declare_parameter("camera_fps", 15)
        self.declare_parameter("camera_fourcc", "MJPG")
        self.declare_parameter("input_size", 640)
        self.declare_parameter("detection_period_sec", 0.3)
        self.declare_parameter("confidence_threshold", 0.25)
        self.declare_parameter("nms_threshold", 0.45)
        self.declare_parameter("detections_topic", "/medicine/vision_detections")
        self.declare_parameter("status_topic", "/medicine/yolo_rknn_status")
        self.declare_parameter("rknn_core_mask", "auto")
        self.declare_parameter("publish_empty_detections", True)
        self.declare_parameter("letterbox_pad_value", 0)

        self.model_path = self.get_string_parameter("model_path")
        self.camera_device = self.get_string_parameter("camera_device")
        self.camera_width = self.get_int_parameter("camera_width")
        self.camera_height = self.get_int_parameter("camera_height")
        self.camera_fps = self.get_int_parameter("camera_fps")
        self.camera_fourcc = self.get_string_parameter("camera_fourcc")
        self.input_size = self.get_int_parameter("input_size")
        self.detection_period_sec = self.get_float_parameter("detection_period_sec")
        self.confidence_threshold = self.get_float_parameter("confidence_threshold")
        self.nms_threshold = self.get_float_parameter("nms_threshold")
        self.rknn_core_mask = self.get_string_parameter("rknn_core_mask")
        self.publish_empty_detections = self.get_bool_parameter("publish_empty_detections")
        self.letterbox_pad_value = self.get_int_parameter("letterbox_pad_value")
        self.labels = self.load_labels()
        self.class_filter = self.load_class_filter()
        self.detections_pub = self.create_publisher(
            String,
            self.get_string_parameter("detections_topic"),
            10,
        )
        self.status_pub = self.create_publisher(
            String,
            self.get_string_parameter("status_topic"),
            10,
        )

        self.rknn = None
        self.cap = None
        self.model_loaded = False
        self.camera_ok = False
        self.status = "starting"
        self.message = ""
        self.last_output_shapes = []
        self.last_inference_ms = 0.0
        self.last_detection_count = 0
        self.last_frame_shape = []

        self.initialize_runtime()
        self.timer = self.create_timer(max(self.detection_period_sec, 0.02), self.on_timer)
        self.status_timer = self.create_timer(1.0, self.publish_status)

    def get_string_parameter(self, name):
        return str(self.get_parameter(name).value or "")

    def get_int_parameter(self, name):
        return int(self.get_parameter(name).value)

    def get_float_parameter(self, name):
        return float(self.get_parameter(name).value)

    def get_bool_parameter(self, name):
        return bool(self.get_parameter(name).value)

    def load_labels(self):
        label_file = self.get_string_parameter("label_file")
        if label_file and os.path.exists(label_file):
            with open(label_file, "r", encoding="utf-8") as file:
                values = [line.strip() for line in file if line.strip()]
                if values:
                    return values
        raw = self.get_string_parameter("labels")
        values = [item.strip() for item in raw.split(",") if item.strip()]
        return values or COCO_LABELS

    def load_class_filter(self):
        raw = self.get_string_parameter("class_filter")
        return {item.strip() for item in raw.split(",") if item.strip()}

    def initialize_runtime(self):
        if cv2 is None:
            self.status = "opencv_missing"
            self.message = "python3-opencv is not available"
            self.publish_status()
            return
        if np is None:
            self.status = "numpy_missing"
            self.message = "numpy is not available"
            self.publish_status()
            return
        if RKNNLite is None:
            self.status = "rknnlite_missing"
            self.message = "rknn-toolkit-lite2 is not available"
            self.publish_status()
            return
        if not self.model_path:
            self.status = "model_missing"
            self.message = "parameter model_path is empty"
            self.publish_status()
            return
        if not os.path.exists(self.model_path):
            self.status = "model_missing"
            self.message = f"model_path does not exist: {self.model_path}"
            self.publish_status()
            return
        self.rknn = RKNNLite()
        ret = self.rknn.load_rknn(self.model_path)
        if ret != 0:
            self.status = "model_load_failed"
            self.message = f"RKNNLite.load_rknn returned {ret}"
            self.publish_status()
            return
        ret = self.init_rknn_runtime()
        if ret != 0:
            self.status = "runtime_init_failed"
            self.message = f"RKNNLite.init_runtime returned {ret}"
            self.publish_status()
            return
        self.model_loaded = True
        self.open_camera()

    def init_rknn_runtime(self):
        core_mask = self.resolve_core_mask()
        try:
            if core_mask is None:
                return self.rknn.init_runtime()
            return self.rknn.init_runtime(core_mask=core_mask)
        except TypeError:
            return self.rknn.init_runtime()

    def resolve_core_mask(self):
        if RKNNLite is None:
            return None
        value = self.rknn_core_mask.strip().lower()
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

    def open_camera(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.cap = cv2.VideoCapture(self.camera_device, cv2.CAP_V4L2)
        if self.camera_fourcc:
            fourcc = cv2.VideoWriter_fourcc(*self.camera_fourcc[:4])
            self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)
        self.cap.set(cv2.CAP_PROP_FPS, self.camera_fps)
        self.camera_ok = bool(self.cap.isOpened())
        if self.camera_ok:
            self.status = "ready"
            self.message = (
                f"model loaded, camera opened: {self.camera_device} "
                f"{int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x"
                f"{int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}"
            )
        else:
            self.status = "camera_open_failed"
            self.message = f"failed to open camera: {self.camera_device}"
        self.publish_status()

    def on_timer(self):
        if not self.model_loaded or not self.camera_ok or self.cap is None:
            return
        ok, frame = self.cap.read()
        if not ok or frame is None:
            self.camera_ok = False
            self.status = "camera_read_failed"
            self.message = f"failed to read frame from {self.camera_device}"
            self.publish_status()
            return
        self.last_frame_shape = list(frame.shape)
        network_input, meta = self.letterbox(frame)
        rgb = cv2.cvtColor(network_input, cv2.COLOR_BGR2RGB)
        input_data = np.expand_dims(rgb, axis=0)
        start = time.monotonic()
        try:
            outputs = self.rknn.inference(inputs=[input_data])
        except Exception as exc:
            self.status = "inference_failed"
            self.message = f"{type(exc).__name__}: {exc}"
            self.publish_status()
            return
        self.last_inference_ms = (time.monotonic() - start) * 1000.0
        self.last_output_shapes = [list(np.array(output).shape) for output in outputs]
        detections = self.decode_outputs(outputs, meta, frame.shape)
        self.last_detection_count = len(detections)
        if detections or self.publish_empty_detections:
            payload = {
                "ok": True,
                "backend": "rknnlite",
                "model_path": self.model_path,
                "camera_device": self.camera_device,
                "frame_shape": self.last_frame_shape,
                "input_size": self.input_size,
                "output_shapes": self.last_output_shapes,
                "inference_ms": self.last_inference_ms,
                "detection_count": len(detections),
                "detections": detections,
                "stamp": time.time(),
            }
            self.detections_pub.publish(String(data=json.dumps(payload, ensure_ascii=False)))
        self.status = "running"
        self.message = f"detections={len(detections)}, inference_ms={self.last_inference_ms:.1f}"

    def letterbox(self, frame):
        height, width = frame.shape[:2]
        size = int(self.input_size)
        scale = min(size / float(width), size / float(height))
        resized_width = int(round(width * scale))
        resized_height = int(round(height * scale))
        resized = cv2.resize(frame, (resized_width, resized_height), interpolation=cv2.INTER_LINEAR)
        pad_x = (size - resized_width) / 2.0
        pad_y = (size - resized_height) / 2.0
        left = int(round(pad_x - 0.1))
        right = int(round(pad_x + 0.1))
        top = int(round(pad_y - 0.1))
        bottom = int(round(pad_y + 0.1))
        image = cv2.copyMakeBorder(
            resized,
            top,
            bottom,
            left,
            right,
            cv2.BORDER_CONSTANT,
            value=(self.letterbox_pad_value, self.letterbox_pad_value, self.letterbox_pad_value),
        )
        return image, {
            "scale": scale,
            "pad_x": left,
            "pad_y": top,
            "input_size": size,
            "original_width": width,
            "original_height": height,
        }

    def decode_outputs(self, outputs, meta, frame_shape):
        arrays = [np.array(output) for output in outputs]
        if self.is_model_zoo_yolov8_output(arrays):
            return self.decode_model_zoo_yolov8(arrays, meta, frame_shape)
        all_detections = []
        for output in arrays:
            detections = self.decode_single_output(output, meta, frame_shape)
            all_detections.extend(detections)
        return self.nms(all_detections)

    def is_model_zoo_yolov8_output(self, outputs):
        if len(outputs) < 6 or len(outputs) % 3 != 0:
            return False
        pair_per_branch = len(outputs) // 3
        for index in range(3):
            box_index = pair_per_branch * index
            class_index = box_index + 1
            if class_index >= len(outputs):
                return False
            box_output = np.squeeze(outputs[box_index])
            class_output = np.squeeze(outputs[class_index])
            if box_output.ndim != 3 or class_output.ndim != 3:
                return False
            if box_output.shape[0] % 4 != 0:
                return False
            if class_output.shape[0] < 2:
                return False
        return True

    def decode_model_zoo_yolov8(self, outputs, meta, frame_shape):
        boxes = []
        classes_conf = []
        pair_per_branch = len(outputs) // 3
        for index in range(3):
            box_output = np.array(outputs[pair_per_branch * index], dtype=np.float32)
            class_output = np.array(outputs[pair_per_branch * index + 1], dtype=np.float32)
            boxes.append(self.model_zoo_box_process(box_output))
            classes_conf.append(class_output)
        boxes = [self.model_zoo_flatten(value) for value in boxes]
        classes_conf = [self.model_zoo_flatten(value) for value in classes_conf]
        boxes = np.concatenate(boxes)
        classes_conf = np.concatenate(classes_conf)
        class_scores = np.max(classes_conf, axis=-1)
        classes = np.argmax(classes_conf, axis=-1)
        keep = np.where(class_scores >= self.confidence_threshold)[0]
        detections = []
        for index in keep:
            detection = self.make_detection(
                int(classes[index]),
                float(class_scores[index]),
                float(boxes[index][0]),
                float(boxes[index][1]),
                float(boxes[index][2]),
                float(boxes[index][3]),
                meta,
                frame_shape,
                True,
            )
            if detection is not None:
                detections.append(detection)
        return self.nms(detections)

    def model_zoo_flatten(self, value):
        value = np.squeeze(value)
        channels = value.shape[0]
        value = value.transpose(1, 2, 0)
        return value.reshape(-1, channels)

    def model_zoo_box_process(self, position):
        position = np.array(position, dtype=np.float32)
        if position.ndim == 3:
            position = np.expand_dims(position, axis=0)
        grid_h, grid_w = position.shape[2:4]
        col, row = np.meshgrid(np.arange(0, grid_w), np.arange(0, grid_h))
        col = col.reshape(1, 1, grid_h, grid_w)
        row = row.reshape(1, 1, grid_h, grid_w)
        grid = np.concatenate((col, row), axis=1).astype(np.float32)
        stride = np.array(
            [self.input_size / float(grid_w), self.input_size / float(grid_h)],
            dtype=np.float32,
        ).reshape(1, 2, 1, 1)
        position = self.model_zoo_dfl(position)
        box_xy = grid + 0.5 - position[:, 0:2, :, :]
        box_xy2 = grid + 0.5 + position[:, 2:4, :, :]
        return np.concatenate((box_xy * stride, box_xy2 * stride), axis=1)

    def model_zoo_dfl(self, position):
        n, channels, height, width = position.shape
        p_num = 4
        mc = channels // p_num
        value = position.reshape(n, p_num, mc, height, width)
        value = self.softmax(value, axis=2)
        weights = np.arange(mc, dtype=np.float32).reshape(1, 1, mc, 1, 1)
        return (value * weights).sum(axis=2)

    def softmax(self, value, axis):
        value = value - np.max(value, axis=axis, keepdims=True)
        exp = np.exp(value)
        return exp / np.sum(exp, axis=axis, keepdims=True)

    def decode_single_output(self, output, meta, frame_shape):
        data = np.squeeze(output)
        if data.ndim != 2:
            return []
        if data.shape[0] < data.shape[1] and data.shape[0] in (6, 7, 84, 85, len(self.labels) + 4, len(self.labels) + 5):
            data = data.T
        if data.shape[1] in (6, 7):
            return self.decode_end2end(data, meta, frame_shape)
        if data.shape[1] >= 7:
            return self.decode_yolo_predictions(data, meta, frame_shape)
        return []

    def decode_end2end(self, data, meta, frame_shape):
        detections = []
        for row in data:
            values = row.astype(float)
            if len(values) >= 6 and 0.0 <= values[4] <= 1.0:
                x1, y1, x2, y2, score, class_id = values[:6]
            elif len(values) >= 6 and 0.0 <= values[1] <= 1.0:
                class_id, score, x1, y1, x2, y2 = values[:6]
            else:
                continue
            if score < self.confidence_threshold:
                continue
            detection = self.make_detection(class_id, score, x1, y1, x2, y2, meta, frame_shape, True)
            if detection is not None:
                detections.append(detection)
        return detections

    def decode_yolo_predictions(self, data, meta, frame_shape):
        detections = []
        class_count_v8 = data.shape[1] - 4
        class_count_v5 = data.shape[1] - 5
        use_v8 = class_count_v8 == len(self.labels) or data.shape[1] <= 84
        for row in data:
            values = row.astype(float)
            if use_v8:
                box = values[:4]
                class_scores = values[4:]
                if len(class_scores) == 0:
                    continue
                class_id = int(np.argmax(class_scores))
                score = float(class_scores[class_id])
            else:
                box = values[:4]
                objectness = float(values[4])
                class_scores = values[5:]
                if len(class_scores) == 0:
                    continue
                class_id = int(np.argmax(class_scores))
                score = objectness * float(class_scores[class_id])
            if score < self.confidence_threshold:
                continue
            x_center, y_center, width, height = box
            if max(abs(x_center), abs(y_center), abs(width), abs(height)) <= 2.0:
                x_center *= meta["input_size"]
                y_center *= meta["input_size"]
                width *= meta["input_size"]
                height *= meta["input_size"]
            x1 = x_center - width / 2.0
            y1 = y_center - height / 2.0
            x2 = x_center + width / 2.0
            y2 = y_center + height / 2.0
            detection = self.make_detection(class_id, score, x1, y1, x2, y2, meta, frame_shape, False)
            if detection is not None:
                detections.append(detection)
        return detections

    def make_detection(self, class_id, score, x1, y1, x2, y2, meta, frame_shape, xyxy):
        class_id = int(class_id)
        label = self.labels[class_id] if 0 <= class_id < len(self.labels) else str(class_id)
        if self.class_filter and label not in self.class_filter and str(class_id) not in self.class_filter:
            return None
        if xyxy and max(abs(x1), abs(y1), abs(x2), abs(y2)) <= 2.0:
            x1 *= meta["input_size"]
            y1 *= meta["input_size"]
            x2 *= meta["input_size"]
            y2 *= meta["input_size"]
        x1 = (x1 - meta["pad_x"]) / meta["scale"]
        y1 = (y1 - meta["pad_y"]) / meta["scale"]
        x2 = (x2 - meta["pad_x"]) / meta["scale"]
        y2 = (y2 - meta["pad_y"]) / meta["scale"]
        original_height, original_width = frame_shape[:2]
        x1 = float(np.clip(x1, 0, original_width - 1))
        y1 = float(np.clip(y1, 0, original_height - 1))
        x2 = float(np.clip(x2, 0, original_width - 1))
        y2 = float(np.clip(y2, 0, original_height - 1))
        if x2 <= x1 or y2 <= y1:
            return None
        return {
            "class_id": class_id,
            "label": label,
            "confidence": float(score),
            "bbox_xyxy": [x1, y1, x2, y2],
            "bbox_xywh": [x1, y1, x2 - x1, y2 - y1],
        }

    def nms(self, detections):
        if not detections:
            return []
        boxes = [detection["bbox_xywh"] for detection in detections]
        scores = [float(detection["confidence"]) for detection in detections]
        indices = cv2.dnn.NMSBoxes(boxes, scores, self.confidence_threshold, self.nms_threshold)
        if len(indices) == 0:
            return []
        flattened = np.array(indices).reshape(-1).tolist()
        return [detections[index] for index in flattened]

    def publish_status(self):
        payload = {
            "status": self.status,
            "message": self.message,
            "model_path": self.model_path,
            "model_loaded": self.model_loaded,
            "camera_device": self.camera_device,
            "camera_ok": self.camera_ok,
            "rknnlite_available": RKNNLite is not None,
            "opencv_available": cv2 is not None,
            "numpy_available": np is not None,
            "npu_render_node": "/dev/dri/renderD129" if os.path.exists("/dev/dri/renderD129") else "",
            "output_shapes": self.last_output_shapes,
            "frame_shape": self.last_frame_shape,
            "inference_ms": self.last_inference_ms,
            "detection_count": self.last_detection_count,
            "stamp": time.time(),
        }
        self.status_pub.publish(String(data=json.dumps(payload, ensure_ascii=False)))

    def destroy_node(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if self.rknn is not None:
            try:
                self.rknn.release()
            except Exception:
                pass
            self.rknn = None
        super().destroy_node()


def main():
    rclpy.init()
    node = YoloRknnDetector()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
