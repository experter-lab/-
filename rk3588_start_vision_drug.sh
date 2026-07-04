#!/usr/bin/env bash
set -eo pipefail

WS="${MEDICINE_ROBOT_WS:-/mnt/sdcard/medicine_robot_ws}"
CAMERA_DEVICE="${VISION_CAMERA_DEVICE:-/dev/video21}"
CAMERA_WIDTH="${VISION_CAMERA_WIDTH:-1280}"
CAMERA_HEIGHT="${VISION_CAMERA_HEIGHT:-960}"
CAMERA_FPS="${VISION_CAMERA_FPS:-60}"
CAMERA_READ_PERIOD_SEC="${VISION_CAMERA_READ_PERIOD_SEC:-0.016}"
PREVIEW_PORT="${VISION_PREVIEW_PORT:-8090}"
PREVIEW_QUALITY="${VISION_PREVIEW_QUALITY:-100}"
PREVIEW_DRAW_OVERLAY="${VISION_PREVIEW_DRAW_OVERLAY:-false}"
PREVIEW_STREAM_PERIOD_SEC="${VISION_PREVIEW_STREAM_PERIOD_SEC:-0.016}"
PREVIEW_SHARPEN_ENABLED="${VISION_PREVIEW_SHARPEN_ENABLED:-true}"
PREVIEW_SHARPEN_AMOUNT="${VISION_PREVIEW_SHARPEN_AMOUNT:-0.55}"
PREVIEW_SHARPEN_SIGMA="${VISION_PREVIEW_SHARPEN_SIGMA:-1.0}"
CAMERA_SHARPNESS="${VISION_CAMERA_SHARPNESS:-100}"
CAMERA_CONTRAST="${VISION_CAMERA_CONTRAST:-58}"
INPUT_MODE="${VISION_INPUT_MODE:-camera}"
ENABLE_QR="${VISION_ENABLE_QR:-false}"
ENABLE_BARCODE_ENHANCEMENT="${VISION_ENABLE_BARCODE_ENHANCEMENT:-true}"
BARCODE_SCALE_X="${VISION_BARCODE_SCALE_X:-2.0}"
BARCODE_SCALE_Y="${VISION_BARCODE_SCALE_Y:-1.2}"
BARCODE_ROI_SCAN_ONLY="${VISION_BARCODE_ROI_SCAN_ONLY:-true}"
BARCODE_ROI_ENABLED="${VISION_BARCODE_ROI_ENABLED:-true}"
BARCODE_ROI_X="${VISION_BARCODE_ROI_X:-0.08}"
BARCODE_ROI_Y="${VISION_BARCODE_ROI_Y:-0.08}"
BARCODE_ROI_W="${VISION_BARCODE_ROI_W:-0.84}"
BARCODE_ROI_H="${VISION_BARCODE_ROI_H:-0.60}"
ENABLE_ZBAR="${VISION_ENABLE_ZBAR:-false}"
ENABLE_ISOLATED_ZXINGCPP="${VISION_ENABLE_ISOLATED_ZXINGCPP:-false}"
EXTERNAL_DECODER_PERIOD_SEC="${VISION_EXTERNAL_DECODER_PERIOD_SEC:-0.15}"
ZBAR_TIMEOUT_SEC="${VISION_ZBAR_TIMEOUT_SEC:-0.3}"
ENABLE_OCR="${VISION_ENABLE_OCR:-true}"
OCR_BACKEND="${VISION_OCR_BACKEND:-ppocr_rknn}"
OCR_LANGUAGE="${VISION_OCR_LANGUAGE:-chi_sim+eng}"
OCR_PERIOD_SEC="${VISION_OCR_PERIOD_SEC:-5.0}"
OCR_MIN_CONFIDENCE="${VISION_OCR_MIN_CONFIDENCE:-35.0}"
OCR_SCALE_FACTOR="${VISION_OCR_SCALE_FACTOR:-2.0}"
OCR_TIMEOUT_SEC="${VISION_OCR_TIMEOUT_SEC:-1.2}"
PPOCR_DET_MODEL_PATH="${VISION_PPOCR_DET_MODEL_PATH:-/mnt/sdcard/medicine_robot_data/models/ppocr/ppocrv4_det_rk3588.rknn}"
PPOCR_REC_MODEL_PATH="${VISION_PPOCR_REC_MODEL_PATH:-/mnt/sdcard/medicine_robot_data/models/ppocr/ppocrv4_rec_rk3588.rknn}"
OCR_ROI_ENABLED="${VISION_OCR_ROI_ENABLED:-true}"
OCR_ROI_X="${VISION_OCR_ROI_X:-0.25}"
OCR_ROI_Y="${VISION_OCR_ROI_Y:-0.34}"
OCR_ROI_W="${VISION_OCR_ROI_W:-0.50}"
OCR_ROI_H="${VISION_OCR_ROI_H:-0.30}"
ENABLE_YOLO_RKNN="${VISION_ENABLE_YOLO_RKNN:-false}"
YOLO_MODEL_PATH="${VISION_YOLO_MODEL_PATH:-/mnt/sdcard/medicine_robot_data/models/yolov8n_rk3588.rknn}"
YOLO_CLASS_FILTER="${VISION_YOLO_CLASS_FILTER:-person,bottle,cup,book}"
YOLO_PERIOD_SEC="${VISION_YOLO_PERIOD_SEC:-0.2}"
YOLO_CONFIDENCE="${VISION_YOLO_CONFIDENCE:-0.25}"
YOLO_CORE_MASK="${VISION_YOLO_CORE_MASK:-auto}"

source /opt/ros/humble/setup.bash
source "${WS}/install/setup.bash"

if pgrep -af "medicine_vision_detector.*drug_info_detector_node|drug_info_detector_node" >/tmp/rk3588_vision_drug_pids.txt 2>/dev/null; then
  awk '{print $1}' /tmp/rk3588_vision_drug_pids.txt | sort -u | while read -r pid; do
    if [ -n "$pid" ] && [ "$pid" != "$$" ]; then
      kill "$pid" 2>/dev/null || true
    fi
  done
  sleep 2
fi

: > /tmp/medicine_vision_detector.log

if command -v v4l2-ctl >/dev/null 2>&1; then
  v4l2-ctl -d "${CAMERA_DEVICE}" --set-ctrl=sharpness="${CAMERA_SHARPNESS}" >/dev/null 2>&1 || true
  v4l2-ctl -d "${CAMERA_DEVICE}" --set-ctrl=contrast="${CAMERA_CONTRAST}" >/dev/null 2>&1 || true
  v4l2-ctl -d "${CAMERA_DEVICE}" --set-ctrl=exposure_auto_priority=0 >/dev/null 2>&1 || true
fi

nohup ros2 run medicine_vision_detector drug_info_detector_node --ros-args \
  -p input_mode:="${INPUT_MODE}" \
  -p camera_device:="${CAMERA_DEVICE}" \
  -p camera_width:="${CAMERA_WIDTH}" \
  -p camera_height:="${CAMERA_HEIGHT}" \
  -p camera_fps:="${CAMERA_FPS}" \
  -p camera_read_period_sec:="${CAMERA_READ_PERIOD_SEC}" \
  -p enable_preview_server:=true \
  -p preview_port:="${PREVIEW_PORT}" \
  -p preview_quality:="${PREVIEW_QUALITY}" \
  -p preview_draw_overlay:="${PREVIEW_DRAW_OVERLAY}" \
  -p preview_stream_period_sec:="${PREVIEW_STREAM_PERIOD_SEC}" \
  -p preview_sharpen_enabled:="${PREVIEW_SHARPEN_ENABLED}" \
  -p preview_sharpen_amount:="${PREVIEW_SHARPEN_AMOUNT}" \
  -p preview_sharpen_sigma:="${PREVIEW_SHARPEN_SIGMA}" \
  -p enable_qr_recognition:="${ENABLE_QR}" \
  -p enable_barcode_enhancement:="${ENABLE_BARCODE_ENHANCEMENT}" \
  -p barcode_scale_x:="${BARCODE_SCALE_X}" \
  -p barcode_scale_y:="${BARCODE_SCALE_Y}" \
  -p barcode_roi_scan_only:="${BARCODE_ROI_SCAN_ONLY}" \
  -p barcode_roi_enabled:="${BARCODE_ROI_ENABLED}" \
  -p barcode_roi_x:="${BARCODE_ROI_X}" \
  -p barcode_roi_y:="${BARCODE_ROI_Y}" \
  -p barcode_roi_w:="${BARCODE_ROI_W}" \
  -p barcode_roi_h:="${BARCODE_ROI_H}" \
  -p enable_zbar_recognition:="${ENABLE_ZBAR}" \
  -p enable_isolated_zxingcpp_recognition:="${ENABLE_ISOLATED_ZXINGCPP}" \
  -p external_decoder_period_sec:="${EXTERNAL_DECODER_PERIOD_SEC}" \
  -p zbar_timeout_sec:="${ZBAR_TIMEOUT_SEC}" \
  -p enable_ocr_recognition:="${ENABLE_OCR}" \
  -p ocr_backend:="${OCR_BACKEND}" \
  -p ppocr_det_model_path:="${PPOCR_DET_MODEL_PATH}" \
  -p ppocr_rec_model_path:="${PPOCR_REC_MODEL_PATH}" \
  -p ocr_language:="${OCR_LANGUAGE}" \
  -p ocr_recognition_period_sec:="${OCR_PERIOD_SEC}" \
  -p ocr_min_confidence:="${OCR_MIN_CONFIDENCE}" \
  -p ocr_scale_factor:="${OCR_SCALE_FACTOR}" \
  -p ocr_timeout_sec:="${OCR_TIMEOUT_SEC}" \
  -p ocr_roi_enabled:="${OCR_ROI_ENABLED}" \
  -p ocr_roi_x:="${OCR_ROI_X}" \
  -p ocr_roi_y:="${OCR_ROI_Y}" \
  -p ocr_roi_w:="${OCR_ROI_W}" \
  -p ocr_roi_h:="${OCR_ROI_H}" \
  -p enable_yolo_rknn_detection:="${ENABLE_YOLO_RKNN}" \
  -p yolo_model_path:="${YOLO_MODEL_PATH}" \
  -p yolo_class_filter:="${YOLO_CLASS_FILTER}" \
  -p yolo_detection_period_sec:="${YOLO_PERIOD_SEC}" \
  -p yolo_confidence_threshold:="${YOLO_CONFIDENCE}" \
  -p yolo_rknn_core_mask:="${YOLO_CORE_MASK}" \
  > /tmp/medicine_vision_detector.log 2>&1 < /dev/null &

sleep 3
echo "[vision-drug] log:"
tail -30 /tmp/medicine_vision_detector.log || true
