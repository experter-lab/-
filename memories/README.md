# 送药智能机器人工作区迁移：记忆库 (Memories Index)

此目录包含了截至 **2026年5月31日** 智能送药小车项目在科大讯飞 M2、易百纳 RK3588、ArduPilot AET-H743 底盘和 ROS 2 Humble 下调试通过的全部核心运行记忆与关键技术细节。

在工作区迁移或重连新主板、重新部署新 Cascade Agent 时，可将此目录作为冷启动参考，让 AI 快速、精准地接管上下文。

## 记忆备份文件清单

| 序号 | 备份文件名称 | 涵盖技术范围 | 关键诊断、测试结论与参数 |
|:---:|:---|:---|:---|
| 1 | [1_chassis_and_ardupilot_bridge.md](./1_chassis_and_ardupilot_bridge.md) | 底盘参数、MAVLink 心跳、安全门控、命令模拟与严格只读心跳脚本 | 急停限速 `RESULT PASS`；心跳验证脚本支持一键自动测试；默认禁控；/dev/ttyS9 @ 115200 |
| 2 | [2_rk3588_board_and_connection.md](./2_rk3588_board_and_connection.md) | 易百纳 RK3588 宿主机参数、SSH 用户、IP 分配、自启守护与隔离调试规范 | IP: `192.168.31.125` (SSID: `Xiaomi_AD81`)；默认账户 `elf`；正式服务 8085，临时调试使用 8095 |
| 3 | [3_medication_delivery_task_flow.md](./3_medication_delivery_task_flow.md) | 医院配送层级结构（批次-停靠点-患者-条码）、扫码校验 API、双导航后端 | 支持 simulated/nav2 切换；导航支持 `/distance_remaining` 进度条输出；120s 自动挂起异常 |
| 4 | [4_lidar_mapping_and_localization.md](./4_lidar_mapping_and_localization.md) | A1 雷达静态 TF、rf2o 二维激光里程计、Slam Toolbox、地图元数据、AMCL 与健康自检工具 | 地图保存至 `/mnt/sdcard/` 根目录；自检脚本 `check_localization_status.sh` 全程闭环验证 |
| 5 | [5_voice_m2_microphone_aikit.md](./5_voice_m2_microphone_aikit.md) | 科大讯飞 M2 麦克风硬件、离线 AIKit ESR、鉴权纠错与分发逻辑映射 | 彻底纠正科大讯飞 offline 授权 AppID/APISecret/APIKey 纠错历史；支持一句话离线创建配送任务 |
| 6 | [6_camera_npu_yolo_and_qr.md](./6_camera_npu_yolo_and_qr.md) | 单视频流多路并发、zxingcpp 扫码校验、Radxa YOLOv8 NPU 推理与极致功耗优化 | YOLO 推理 `17.9ms` ~ `23.7ms`；通过空闲时跳过 JPEG 编码技术，CPU 占用由 `76%` 降至 `56%` |

## 迁移冷启动指南
在新环境启动时，只需将本目录下的 Markdown 文件内容喂给新的 AI Assistant，或在工作区建立以下系统级记忆（Memory System）：
1. 复制本目录内文件或内容作为长期记忆挂载。
2. 运行 `ros2 run` 之前，参考文件内记载的默认参数、隔离波特率及端口指令。
