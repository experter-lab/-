import cv2

from medicine_vision_detector.ppocr_onnx_runner import PPOcrOnnxRunner


image_path = "/mnt/sdcard/medicine_robot_data/models/ppocr/current_camera.jpg"
img = cv2.imread(image_path)
print("image", image_path, None if img is None else img.shape)
runner = PPOcrOnnxRunner(
    "/mnt/sdcard/medicine_robot_data/models/ppocr",
    "/mnt/sdcard/medicine_robot_data/models/ppocr/ppocrv4_det.onnx",
    "/mnt/sdcard/medicine_robot_data/models/ppocr/ppocrv4_rec.onnx",
)
result = runner.run(img)
print("text", result.text)
print("confidence", result.confidence)
print("boxes", len(result.boxes))
print("elapsed_ms", result.elapsed_ms)
