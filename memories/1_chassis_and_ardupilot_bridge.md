# 记忆库备份：底盘硬件与 ArduPilot 桥接 (Chassis and ArduPilot Bridge)

## 1. 硬件规格与拓扑
- **底盘硬件**：飞蛋科技 AeroEggTech AET-H743 Basic。
- **固件体系**：ArduPilot (ArduRover)。
- **底盘结构**：四轮差速（skid-steering）。
- **编码器状态**：无轮速编码器。
- **定位/里程计方案**：现阶段继续使用 `rf2o_laser_odometry` 的雷达激光里程计发布 `/odom` 话题，待底盘可用后可选择融合 IMU。

## 2. 串口连接与参数配置
- **板端物理串口**：`/dev/ttyS9`（板载 UART 接口）。
- **默认波特率**：`115200`。
- **ArduPilot 地面站 (Mission Planner) 参数要求**：
  - `SERIALx_PROTOCOL = 2` (MAVLink2)
  - `SERIALx_BAUD = 115` (115200)

## 3. 安全优先默认参数
底盘节点在启动和日常干跑时，必须始终强制满足以下安全只读限制，防止误发控制指令或触发未标定的底盘运动：
- `publish_odom = false`（不发布底盘自带的 Odom 话题）
- `publish_tf = false`（不发布 Odom 到 base_link 的变换）
- `emergency_stop = true`（默认启用软件急停）
- `ardupilot_readonly = true`（强制只读模式，不发送控制命令）
- `ardupilot_control_enabled = false`（控制未使能）

## 4. 关键配置文件与 ROS2 参数
- **参数文件**：`/mnt/sdcard/medicine_robot_ws/src/medicine_chassis_bridge/config/chassis_bridge_ardupilot_serial_readonly.yaml`
- **核心逻辑**：`medicine_chassis_bridge` 中的 `chassis_bridge_node`：
  - 订阅 `Nav2` 发布的 `/cmd_vel`。
  - 在只读和急停解除、安全限速闸门标定后（最大线速度 `0.2 m/s`，角速度 `0.5 rad/s`），才可向下发 MAVLink。
  - 内置 Watchdog：如果 `/cmd_vel` 停止发布超过安全时长，触发 `cmd_timed_out = true` 并自动将目标速度回零。

## 5. 网页端底盘安全状态可视化 (Web Dashboard Card)
- **前端展示**：在“单任务调试”页面新增了“底盘安全状态”卡片。
- **数据源**：`medicine_web_dashboard` 节点订阅 `/medicine/chassis_status`（std_msgs/String JSON），并暴露 REST API `GET /api/chassis_status`。
- **显示指标**：
  - `emergency_stop`（急停状态，红色/绿色角标）
  - `readonly` & `control_enabled`（安全模式标识）
  - `heartbeat_ok` & `heartbeat_count` & `heartbeat_age_sec`（飞控心跳状态及延迟）
  - `system_id` & `component_id` & `mavlink_version` & `autopilot`（飞控身份及版本标识）
  - `cmd_timed_out`（控制超时状态）
  - `target_linear` / `target_angular`（目标速度）
  - `current_linear` / `current_angular`（当前实际速度反馈）
  - `port` / `baudrate`（连接串口信息）

## 6. 测试与运维验证脚本
- **串口数据模拟测试**（在未接真实飞控时模拟 MAVLink 心跳）：
  - HEX 循环发送 MAVLink v1 HEARTBEAT 报文：`FE 09 00 01 01 00 00 00 00 00 0A 03 00 03 03 00 00`。
  - 通过 `/dev/ttyS9` 模拟输入，验证 `heartbeat_ok = true`，各种 MAVLink 元数据解析正确。
- **`/cmd_vel` 安全限速与 Watchdog 测试**：
  - 运行 `/mnt/sdcard/rk3588_chassis_cmd_vel_safety_test.sh /dev/ttyS9 115200`
  - 测试结果：`RESULT PASS`。验证了急停拦截速度、速度限速、以及停止发布后速度自动归零的逻辑。
- **真实飞控只读心跳严格验证**：
  - 运行 `/mnt/sdcard/rk3588_verify_ardupilot_heartbeat.sh /dev/ttyS9 115200`
  - 逻辑：通过独立 `ROS_DOMAIN_ID` 启动只读桥接，在规定超时内等待真实 Heartbeat 传入。若匹配通过则输出 `RESULT PASS real ArduPilot heartbeat verified` 并解析输出身份标识。
