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

### 2026-06-08 实车覆盖值
- 当前实车底盘桥接串口为 `/dev/ttyS9 @ 921600`，网页状态卡已经按这个值显示。
- 飞控输出实际接线为 `S7/S8`。不要再使用早期针对 `SERVO1/SERVO3` 的修复脚本，尤其不要运行 `fix_servo_function_1_3.py`。
- 桥接端 `source_system=255` 已被飞控接受，可以正常收到 MAVLink heartbeat。

## 3. 安全优先默认参数
底盘节点在启动和日常干跑时，必须始终强制满足以下安全只读限制，防止误发控制指令或触发未标定的底盘运动：
- `publish_odom = false`（不发布底盘自带的 Odom 话题）
- `publish_tf = false`（不发布 Odom 到 base_link 的变换）
- `emergency_stop = true`（默认启用软件急停）
- `ardupilot_readonly = true`（强制只读模式，不发送控制命令）
- `ardupilot_control_enabled = false`（控制未使能）

### 2026-06-08 实车安全策略
- 急停功能曾经影响 Nav2 实车调试，后续调试中已将软件急停默认关闭到 `emergency_stop: false`；真正的运动闸门改为依赖 `ardupilot_control_enabled`。
- 实车导航启动脚本默认使用 `NAV2_ENABLE_DRIVE=0`，启动 Cartographer/Nav2/Web 后仍保持 `control_authorized=false`，只有明确要测试运动时才调用 `/mnt/sdcard/rk3588_enable_nav2_drive.sh`。
- 最近一次安全收尾状态：`control_authorized=false`，`emergency_stop=false`，防止远程误动作。

## 4. 关键配置文件与 ROS2 参数
- **参数文件**：`/mnt/sdcard/medicine_robot_ws/src/medicine_chassis_bridge/config/chassis_bridge_ardupilot_serial_readonly.yaml`
- **核心逻辑**：`medicine_chassis_bridge` 中的 `chassis_bridge_node`：
  - 订阅 `Nav2` 发布的 `/cmd_vel`。
  - 在只读和急停解除、安全限速闸门标定后（最大线速度 `0.2 m/s`，角速度 `0.5 rad/s`），才可向下发 MAVLink。
  - 内置 Watchdog：如果 `/cmd_vel` 停止发布超过安全时长，触发 `cmd_timed_out = true` 并自动将目标速度回零。

### 2026-06-08 速度与转向标定
- 直行/后退速度已整体压低：`max_linear_speed=0.05`，油门 PWM 约为 `1435 / 1500 / 1565`。
- 转向力度单独增强：`max_angular_speed=0.15`，转向 PWM 约为 `1370 / 1500 / 1630`。
- 键盘遥控调过多轮：前进/后退最终较慢，转向相对更强。后续若觉得 Nav2 起步无力，先查授权、`/cmd_vel`、PWM 输出和接线，不要先盲目加速度。

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
- 2026-06-10 braking policy: safe state is `HOLD`, `control_authorized=false`, `emergency_stop=true`, zero target/current velocity, and RC override centered at throttle/steering PWM 1500. `rk3588_safe_stop.sh` now sends a short zero `/cmd_vel` burst, commands HOLD, DISARM, software emergency stop, and authorization revoke. `rk3588_check_brake_status.sh` is the read-only gate before/after any motion test. Control authorization TTL is 60s and `/cmd_vel` timeout is 0.2s in the deployed chassis config.
- 2026-06-10 lifted-wheel brake test passed. With wheels raised, a real nonzero `/cmd_vel` publisher drove `current_linear=0.0200` and RC PWM `(throttle=1474, steering=1500)` in `MANUAL`; applying `rk3588_safe_stop.sh` while the publisher was active returned to `HOLD`, `emergency_stop=true`, `control_authorized=false`, zero velocity, and PWM `(1500,1500)`. A publisher-stop timeout test also returned velocity/PWM to zero/mid before the final safe stop.
- 2026-06-10 drive-output diagnostic after the user observed no wheel motion: bridge diagnostics now expose `rc_channels` and `servo_outputs` in `/medicine/chassis_status`. A `+0.05 m/s` command reached the bridge and ArduPilot: `current_linear=0.05`, RC override `chan3_raw=1435`, and `SERVO_OUTPUT_RAW servo7_raw=1600, servo8_raw=1600`; safe stop returned `chan3_raw=1500` and `servo7/8=1500`. If wheels still do not move, the fault is downstream of ArduPilot output, likely S7/S8 wiring, motor driver enable/power, PWM deadband, or output-channel mapping.
- 2026-06-20 Nav2/ArduPilot enable lesson: do not trust the `/chassis_bridge/set_mode` service response alone. A direct Python service sequence once returned `mode command sent: MANUAL` while status still showed `HOLD`, so S7/S8 stayed neutral. For motion tests, use `/mnt/sdcard/rk3588_enable_nav2_drive.sh --confirm`, then verify `/medicine/chassis_status` has `ardupilot.custom_mode_name=MANUAL`, `ardupilot.base_mode=193`, top-level `emergency_stop=false`, and top-level `control_authorized=true` before sending `/cmd_vel` or Nav2 goals. In the confirmed MANUAL state, a Nav2 short forward goal produced RC3 and S7/S8 output and the user confirmed the robot moved.
- 2026-06-20 status JSON shape: `/medicine/chassis_status` stores ArduPilot mode fields under the nested `ardupilot` object, not at top level. A fixed-point navigation test initially aborted before sending any task because the checker looked for top-level `custom_mode_name/base_mode`; the correct ready check is nested `status["ardupilot"]["custom_mode_name"]` and `status["ardupilot"]["base_mode"]`.
