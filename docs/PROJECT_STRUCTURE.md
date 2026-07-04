# 项目目录结构

本仓库按“工程代码、部署脚本、配置文件、文档资料、测试验证”进行归类，便于比赛评审和后续维护。

## 顶层目录

| 目录 | 内容 |
| --- | --- |
| `board_sync/` | RK3588 板端 ROS 2 功能包同步源码，包括 Web Dashboard、药品视觉识别、语音桥接等。 |
| `patient_web/` | 患者端前端工程。 |
| `src/` | 根目录镜像出来的核心 Python/C++ 辅助源码，例如 Dashboard 镜像、数据库集成、雷达驱动补丁等。 |
| `scripts/` | 部署、启动、同步、调试脚本，按 RK3588 功能域继续细分。 |
| `configs/` | YAML、systemd、RViz、udev、桌面快捷方式等配置文件。 |
| `docs/` | 项目说明、比赛材料、部署指南、阶段报告和实验资料。 |
| `tests/` | 验证脚本、探针脚本、测试夹具。 |
| `maps/` | SLAM/导航地图文件。 |
| `tools/` | 本地辅助工具，例如 RK3588 备份/恢复和 Codex 历史导出。 |
| `memories/` | 项目长期记忆与开发上下文摘要。 |

## scripts 子目录

| 目录 | 内容 |
| --- | --- |
| `scripts/rk3588/startup/` | RK3588 端各模块启动脚本。 |
| `scripts/rk3588/navigation/` | Cartographer/Nav2/定位/建图/雷达诊断脚本。 |
| `scripts/rk3588/chassis/` | 底盘、ArduPilot、串口、舵机、安全停靠相关脚本。 |
| `scripts/rk3588/vision/` | 摄像头、OCR、二维码/条码、RKNN/ONNX 视觉调试脚本。 |
| `scripts/rk3588/voice/` | ASR/TTS、讯飞/DashScope、语音运行时检测脚本。 |
| `scripts/rk3588/misc/` | RK3588 板端通用维护脚本。 |
| `scripts/sync/` | Windows/本地到 RK3588 的同步和备份脚本。 |
| `scripts/nomachine/` | NoMachine 远程桌面快捷操作脚本。 |
| `scripts/local/` | 本地开发与临时辅助脚本。 |

## configs 子目录

| 目录 | 内容 |
| --- | --- |
| `configs/navigation/` | Nav2、Cartographer、AMCL、站点等导航配置。 |
| `configs/vision/` | 药品识别、YOLO/RKNN、视觉低负载配置。 |
| `configs/chassis/` | 底盘桥接和串口模板配置。 |
| `configs/systemd/` | RK3588 systemd 服务文件。 |
| `configs/rviz/` | RViz 视图配置。 |
| `configs/desktop/` | NoMachine/桌面快捷方式。 |
| `configs/udev/` | 雷达等设备 udev 规则。 |
| `configs/voice/` | 语音 SDK/运行时配置。 |
| `configs/packages/` | ROS 包元数据或迁移保留配置。 |

## docs 子目录

| 目录 | 内容 |
| --- | --- |
| `docs/competition/` | 比赛设计报告等提交材料。 |
| `docs/guides/` | 部署、运行、移植和雷达导航指南。 |
| `docs/reports/` | 阶段总结、优化报告、数据库部署报告等。 |
| `docs/experiments/` | 课程/实验记录和电路实验资料。 |
| `docs/notes/` | 零散操作记录和远程运行说明。 |

## 当前顶层跟踪文件数量

- `board_sync/`: 28 个文件
- `configs/`: 41 个文件
- `docs/`: 28 个文件
- `maps/`: 5 个文件
- `memories/`: 12 个文件
- `patient_web/`: 52 个文件
- `scripts/`: 182 个文件
- `src/`: 19 个文件
- `tests/`: 29 个文件
- `tools/`: 3 个文件
