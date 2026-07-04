import argparse
import json
import sys

import cv2

from medicine_vision_detector.ppocr_onnx_runner import PPOcrOnnxRunner


def main():
    parser = argparse.ArgumentParser(description="Run PPOCR in an isolated process.")
    parser.add_argument("--image", required=True)
    parser.add_argument("--ppocr-root", required=True)
    parser.add_argument("--det-model", required=True)
    parser.add_argument("--rec-model", required=True)
    parser.add_argument("--target", default="rk3588")
    parser.add_argument("--max-boxes", type=int, default=12)
    args = parser.parse_args()

    frame = cv2.imread(args.image, cv2.IMREAD_COLOR)
    if frame is None:
        print(json.dumps({"ok": False, "error": f"cannot read image: {args.image}"}, ensure_ascii=False))
        return 2

    runner = PPOcrOnnxRunner(
        ppocr_root=args.ppocr_root,
        det_model_path=args.det_model,
        rec_model_path=args.rec_model,
        target=args.target,
        max_boxes=args.max_boxes,
    )
    result = runner.run(frame)
    print(
        json.dumps(
            {
                "ok": True,
                "text": result.text,
                "confidence": result.confidence,
                "boxes": result.boxes,
                "elapsed_ms": result.elapsed_ms,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))
        raise SystemExit(1)
