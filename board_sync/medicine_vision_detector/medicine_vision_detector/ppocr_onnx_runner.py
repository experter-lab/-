import os
import sys
import time
from dataclasses import dataclass
from types import SimpleNamespace

import cv2
import numpy as np


@dataclass
class PPOCRResult:
    text: str
    confidence: float
    boxes: list
    elapsed_ms: float


class PPOcrOnnxRunner:
    def __init__(
        self,
        ppocr_root,
        det_model_path,
        rec_model_path,
        target="rk3588",
        max_boxes=12,
    ):
        self.ppocr_root = ppocr_root
        self.det_model_path = det_model_path
        self.rec_model_path = rec_model_path
        self.target = target
        self.max_boxes = max(1, int(max_boxes))
        self.detector = None
        self.recognizer = None
        self.loaded = False
        self.error = ""

    def load(self):
        if self.loaded:
            return
        self.error = ""
        if not os.path.exists(self.det_model_path):
            raise FileNotFoundError(self.det_model_path)
        if not os.path.exists(self.rec_model_path):
            raise FileNotFoundError(self.rec_model_path)

        zoo_root = os.path.join(self.ppocr_root, "rknn_model_zoo")
        det_python = os.path.join(
            zoo_root, "examples", "PPOCR", "PPOCR-Det", "python"
        )
        rec_python = os.path.join(
            zoo_root, "examples", "PPOCR", "PPOCR-Rec", "python"
        )
        for path in (zoo_root, det_python, rec_python):
            if path not in sys.path:
                sys.path.insert(0, path)

        from ppocr_det import TextDetector
        from ppocr_rec import TextRecognizer

        det_args = SimpleNamespace(
            model_path=self.det_model_path,
            target=self.target,
            device_id=None,
        )
        rec_args = SimpleNamespace(
            model_path=self.rec_model_path,
            target=self.target,
            device_id=None,
        )
        cwd = os.getcwd()
        try:
            os.chdir(det_python)
            self.detector = TextDetector(det_args)
            os.chdir(rec_python)
            self.recognizer = TextRecognizer(rec_args)
        finally:
            os.chdir(cwd)
        self.loaded = True

    def run(self, frame):
        start = time.monotonic()
        self.load()
        det_frame = cv2.resize(frame, (480, 480))
        boxes = self.detector.run(det_frame)
        scale_x = frame.shape[1] / 480.0
        scale_y = frame.shape[0] / 480.0
        ranked_boxes = sorted(
            [self._scale_box(np.array(box, dtype=np.float32), scale_x, scale_y) for box in boxes],
            key=self._box_sort_key,
        )[: self.max_boxes]
        texts = []
        confidences = []
        serializable_boxes = []
        for box in ranked_boxes:
            crop = self._crop_quad(frame, box)
            if crop is None or crop.size == 0:
                continue
            rec_input = cv2.resize(crop, (320, 48))
            rec_output = self.recognizer.run(rec_input)
            for text, score in rec_output:
                text = str(text).strip()
                score = float(score)
                if not text:
                    continue
                texts.append(text)
                confidences.append(score)
                serializable_boxes.append(box.astype(float).tolist())
        elapsed_ms = (time.monotonic() - start) * 1000.0
        return PPOCRResult(
            text=" ".join(texts).strip(),
            confidence=(sum(confidences) / len(confidences)) if confidences else 0.0,
            boxes=serializable_boxes,
            elapsed_ms=elapsed_ms,
        )

    @staticmethod
    def _scale_box(box, scale_x, scale_y):
        scaled = box.copy()
        scaled[:, 0] *= float(scale_x)
        scaled[:, 1] *= float(scale_y)
        return scaled

    @staticmethod
    def _box_sort_key(box):
        ys = box[:, 1]
        xs = box[:, 0]
        return (float(np.min(ys)), float(np.min(xs)))

    @staticmethod
    def _crop_quad(frame, box):
        width_a = np.linalg.norm(box[0] - box[1])
        width_b = np.linalg.norm(box[2] - box[3])
        height_a = np.linalg.norm(box[0] - box[3])
        height_b = np.linalg.norm(box[1] - box[2])
        width = max(int(max(width_a, width_b)), 8)
        height = max(int(max(height_a, height_b)), 8)
        if width <= 0 or height <= 0:
            return None
        destination = np.array(
            [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
            dtype=np.float32,
        )
        matrix = cv2.getPerspectiveTransform(box.astype(np.float32), destination)
        return cv2.warpPerspective(frame, matrix, (width, height))
