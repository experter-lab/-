# 智能送药机器人

本仓库为基于 RK3588 / ROS 2 的智能送药机器人项目代码开源仓库，包含送药任务流程、Web 管理端、患者端、药品识别、语音交互、底盘安全与导航调试脚本等主体任务代码。

## 开源仓库地址

- GitHub: https://github.com/experter-lab/-.git

## 主要模块

- `board_sync/medicine_web_dashboard/`：8085 护士/管理端与 8081 患者端 Web 服务代码。
- `board_sync/medicine_vision_detector/`：药品视觉识别、OCR、条码/追溯码识别相关节点。
- `patient_web/`：患者端前端工程。
- `rk3588_start_*.sh`、`rk3588_*nav*`、`carto_*`：RK3588 端启动、导航、建图和定位脚本。
- `chassis_bridge_node.py`、`chassis_bridge*.yaml`：底盘安全桥接与配置。
- `tools/`：备份、恢复和 Codex 上下文导出工具。

## 设计资料

- [智能送药机器人_作品设计报告.pdf](docs/competition/智能送药机器人_作品设计报告.pdf)

## 说明

- 仓库已排除本地备份、私密配置、运行日志、大型 SDK/课程资料、模型中间文件和生成产物。
- 演示视频资料后续可补充到仓库说明或提交平台链接中。
