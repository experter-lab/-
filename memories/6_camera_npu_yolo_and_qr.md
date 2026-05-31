# 记忆库备份：摄像头采集、NPU YOLO 目标检测与二维码识别 (Camera, NPU YOLO and QR Recognition)

## 1. 摄像头物理设备
- **摄像头节点**：单摄像头多功能集成节点 `drug_info_detector_node.py`（避免多节点争抢摄像头物理句柄）。
- **物理接口**：挂载于 `/dev/video21`（标准 UVC 协议免驱摄像头）。
- **帧率与格式**：`1280x720` 分辨率，`MJPG` 编码格式，物理帧率稳定在 `15fps`。

## 2. 扫码校验功能 (zxingcpp)
- **解码库**：使用 C++ 强力硬解码库 `zxingcpp` 的 Python 绑定。
- **条码类型**：主要支持医院药品标签上的 QR 码与一维条码解码。
- **采集频率**：扫码识别线程与视频采集流解耦，运行频率控制在 `1.0Hz`，避免高频调用造成 CPU 过载。
- **扫码应用**：
  - 在装药（Loading）与派发（Dispensing）环节对药盒追溯条码进行逐一解码，核验成功后才允许推进状态。

## 3. RK3588 NPU 神经网络加速 (Radxa YOLOv8 RKNN)
- **NPU 运行库**：`rknn-toolkit-lite2` (版本 `2.3.2`)，板载驱动运行版本为 `librknnrt 2.1.0`。
- **YOLO 模型**：
  - **模型路径**：`/mnt/sdcard/medicine_robot_data/models/yolov8n_rk3588.rknn`。
  - **推理耗时**：在 RK3588 的 NPU 三核并行硬件加速下，YOLOv8 模型单帧推理及前/后处理总延迟仅为 `17.9ms ~ 23.7ms`。
- **ROS 2 输出话题**：
  - 发布 `/medicine/vision_detections` 目标检测数据。
  - 发布 `/medicine/yolo_rknn_status` NPU 健康指标（包含前向推理延迟统计）。
  - 检测结果与状态流转自动同步合并发布到 `/medicine/drug_recognition_status`。

## 4. 极致低功耗巡航优化 (Low CPU Cruising Mode)
为解决高频 YOLO 推理、二维码检索与实时 MJPEG 网页流预览并发导致的 CPU 负载过高问题（曾高达约 76%），深度重构并引入了低功耗巡航参数：
- **配置文件**：`/mnt/sdcard/medicine_robot_data/config/rk3588_vision_unified_yolo_low_cpu.yaml`。
- **核心优化参数**：
  - `camera_read_period_sec = 0.07`（锁帧约 14 FPS）
  - `preview_quality = 35`（降低压缩预览图分辨率与画质）
  - `preview_stream_period_sec = 0.3`（网页预览视频刷新限制在约 3.3Hz）
  - `preview_encode_period_sec = 0.3`（在没有浏览器客户端接入预览服务时，**自动跳过并彻底关闭 JPEG 编码与图像渲染叠加**，零占用编码 CPU）
  - `qr_recognition_period_sec = 1.0`
  - `yolo_detection_period_sec = 0.2`（YOLO 帧率约 5Hz）
- **性能优化结果**：
  - NPU YOLO 运行频率约 `4.3Hz`，QR 扫码扫描频率稳定在 `1.0Hz`。
  - **主检测进程 CPU 占用率从 76% 骤降至 56%**，显著降低了开发板的发热量，保障了系统的长期不间断运行稳定性。
