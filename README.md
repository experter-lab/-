# 智能送药机器人

本仓库为基于 RK3588 / ROS 2 的智能送药机器人项目代码开源仓库，包含送药任务流程、Web 管理端、患者端、药品识别、语音交互、底盘安全与导航调试脚本等主体任务代码。

## 开源仓库地址

- GitHub: https://github.com/experter-lab/-.git

## 快速查看

- [项目目录结构](docs/PROJECT_STRUCTURE.md)
- [比赛设计报告 PDF](docs/competition/智能送药机器人_作品设计报告.pdf)
- [演示视频：7月9日.mp4](docs/competition/videos/7月9日.mp4)
- [快速开始指南](docs/guides/QUICKSTART.md)

## 主要目录

| 目录 | 说明 |
| --- | --- |
| `board_sync/` | RK3588 板端 ROS 2 功能包源码，包含 Dashboard、视觉识别、语音交互、语音桥接等。 |
| `patient_web/` | 患者端 Web 前端工程。 |
| `src/` | Dashboard 镜像代码、数据库集成、雷达驱动补丁等核心辅助源码。 |
| `scripts/` | RK3588 启动、导航、视觉、语音、底盘、安全、同步脚本。 |
| `configs/` | 导航、视觉、底盘、systemd、RViz、udev、桌面快捷方式等配置。 |
| `docs/` | 比赛材料、部署指南、项目报告、实验资料。 |
| `tests/` | 验证脚本、硬件探针、接口测试脚本。 |
| `maps/` | SLAM/导航地图文件。 |
| `tools/` | RK3588 备份/恢复、Codex 上下文导出等本地工具。 |
| `memories/` | 项目长期记忆和开发上下文摘要。 |

## 核心模块

- `board_sync/medicine_web_dashboard/`：8085 护士/管理端与 8081 患者端 Web 服务代码。
- `board_sync/medicine_vision_detector/`：药品视觉识别、OCR、条码/追溯码识别相关节点。
- `board_sync/m2_voice_opt_20260609/`：语音交互、ASR/TTS、语音知识库与桥接节点。
- `patient_web/`：患者端前端工程。
- `scripts/rk3588/startup/`：RK3588 端核心服务启动脚本。
- `scripts/rk3588/navigation/`：Cartographer / Nav2 / 雷达建图定位调试脚本。
- `scripts/rk3588/chassis/`：底盘安全、ArduPilot、串口、舵机与急停相关脚本。
- `configs/navigation/`、`configs/vision/`、`configs/chassis/`：主要运行配置。

## 设计与演示资料

- [智能送药机器人_作品设计报告.pdf](docs/competition/智能送药机器人_作品设计报告.pdf)
- [演示视频：7月9日.mp4](docs/competition/videos/7月9日.mp4)

## 说明

- 仓库已排除本地备份、私密配置、运行日志、大型 SDK/课程资料、模型中间文件和生成产物。
- 演示视频通过 Git LFS 管理。
