# RK3588 Nav2 现场记忆

更新时间：2026-06-14

## 固定原则

- 任何定位、Nav2、建图前先确认 `BRAKE_STATUS_SAFE`。
- `Start Nav2 RViz2` 只允许启动定位/Nav2 规划链路，不授权底盘。
- `启用Nav2驱动` 是唯一运动授权入口，必须输入大写 `ENABLE`。
- 运动测试只从 0.2 到 0.3m 短目标开始。
- 只要 `/scan` 不贴地图、TF 异常、或 odom 掉线，立即安全停止，不继续点目标。

## 反复问题 1：雷达服务 active 但 `/scan` 没有数据

现象：

- `rk3588-lidar.service` 显示 `active`。
- `/scan` topic 存在，publisher count = 1。
- 但 `ros2 topic hz /scan` 收不到消息。
- RF2O 启动失败，日志出现：

```text
[rf2o-odom] ERROR: no scan messages on /scan
```

结论：

- 不能只看 systemd active 或 topic publisher。
- `/scan` 必须实际有约 10Hz 数据流。

处理：

```bash
echo elf | sudo -S systemctl restart rk3588-lidar.service
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash
ros2 topic info /scan
timeout 8 ros2 topic hz /scan
```

验收：

- `/scan` publisher count = 1。
- `/scan` 约 10Hz。
- `/scan` frame_id = `laser`。

## 反复问题 2：Nav2/RViz 启动失败后留下半启动状态

现象：

- Nav2/Cartographer 进程还在。
- 但 RF2O、`rk3588_guarded_odom`、EKF 不在。
- `/odom` publisher count = 0。
- `/rf2o/odom_raw` 或 `/odom_rf2o_guarded` 不存在。

结论：

- 这种状态不能授权运动。
- 必须清理后完整重启，不要在半启动状态上继续点 goal。

处理：

```bash
/mnt/sdcard/rk3588_safe_stop.sh
/mnt/sdcard/rk3588_clean_nav_runtime.sh
/mnt/sdcard/rk3588_start_nav2_carto.sh
```

验收：

- `/rf2o/odom_raw` publisher = 1。
- `/odom_rf2o_guarded` publisher = 1。
- `/odom` publisher = 1。
- `map -> odom -> base_link -> laser` 正常。
- `BRAKE_STATUS_SAFE` 仍通过。

## 反复问题 3：`启用Nav2驱动` 卡在健康检查

现象：

- 黑色终端显示一堆 `OK node ...` 后长时间不进入 `ENABLE` 输入提示。

历史原因：

- 旧脚本调用完整 `rk3588_check_nav2_status.sh`，某些 lifecycle/tf/action 检查可能慢或卡住。

当前修复：

- `/mnt/sdcard/nomachine_enable_nav2_drive.sh` 已改为短超时关键项检查。
- 检查通过后才显示：

```text
Type exactly: ENABLE
```

注意：

- 输入 `yes` 会取消。
- 必须输入大写 `ENABLE`。

## 反复问题 4：点 Nav2 goal 后车不动

先判断：

- 如果 `emergency_stop=True` 或 `control_authorized=False`，车不动是正常结果。
- 如果 Nav2 日志有 `Begin navigating` / `Received a goal`，但底盘未授权，最后会报：

```text
Failed to make progress
```

处理顺序：

1. 确认 RViz 中 scan/map/footprint 对齐。
2. 双击 `启用Nav2驱动`。
3. 输入大写 `ENABLE`。
4. 确认：

```text
emergency_stop=False
control_authorized=True
mode=MANUAL
```

5. 再点 0.2 到 0.3m 短目标。

## 反复问题 5：电机响但车不动

已观测事实：

- Nav2 曾输出：

```text
/cmd_vel linear.x = 0.02
throttle_pwm = 1480
```

- 这只有约 20us PWM 偏移，可能低于电机静摩擦死区。

已调整：

```text
min_vel_x: 0.06
min_speed_xy: 0.06
trans_stopped_velocity: 0.04
velocity_smoother deadband_velocity x: 0.04
max_vel_x: 0.12
```

验证：

- 改参数后必须重启 Nav2 进程本身。
- 如果仍然只响不动，下一步不是继续调 Nav2，而是测试底盘实际起步 PWM 死区，并在底盘桥做最小 PWM 补偿。

## 反复问题 6：`base_link` 红轴方向疑似反了

标准：

- `base_link` 红轴 X+ = 小车车头 / 前进方向。
- `base_link` 绿轴 Y+ = 小车左侧。
- `base_link` 蓝轴 Z+ = 向上。

已确认事实：

- 用户观察到点 Nav2 后小车现实中能向前走。
- 所以 `/cmd_vel linear.x > 0` 到底盘运动方向基本不是反的。

结论：

- 暂时不要改 TF。
- 如果怀疑方向，必须做最小正向验证，而不是看截图猜。

验证方法：

- 授权后只发短时 `linear.x > 0`。
- 如果现实中车向前，底盘控制方向正确。
- 如果 RViz 里 `base_link` 往反方向移动，再查 TF/odom。

## 正常恢复流程

1. 上电后执行安全停止：

```bash
/mnt/sdcard/rk3588_safe_stop.sh
/mnt/sdcard/rk3588_check_brake_status.sh
```

2. 检查 `/scan`：

```bash
ros2 topic info /scan
timeout 8 ros2 topic hz /scan
```

3. 如果 `/scan` 无频率，先重启雷达服务。

4. 启动 Nav2 只规划链路：

```bash
/mnt/sdcard/rk3588_start_nav2_carto.sh
```

5. 看 RViz 对齐。

6. 双击 `启用Nav2驱动`，输入 `ENABLE`。

7. 只测 0.2 到 0.3m 近目标。
## Recurrent issue 7: RF2O raw forward sign is reversed

Observed:

- A positive `/cmd_vel linear.x=0.06` made the chassis move forward physically.
- RF2O raw odometry reported negative X.
- After sign correction, official `/odom` reported positive X:

```text
/odom x ~= +0.065m
/odom y ~= -0.006m
/rf2o/odom_raw x remained negative
```

Fix:

- `rk3588_guarded_odom.py` supports:

```text
raw_x_sign=-1.0
raw_y_sign=-1.0
```

- `rk3588_start_odom_fusion.sh` passes these signs to the guarded odom node.
- Do not change `base_link -> laser` or chassis command direction for this symptom.

Validation:

- With safe-stop active, `/odom` stayed frozen for 20s.
- `/odom` is now owned by EKF only.

## Recurrent issue 8: Nav2 startup can fail if localization restarts odom fusion

Observed:

- `rk3588_start_nav2_carto.sh` started odom fusion.
- Then `rk3588_start_carto_localization.sh` restarted odom fusion again.
- The second restart killed RF2O/guard/EKF while Nav2 startup was waiting for Cartographer.
- Symptom:

```text
[nav2-carto] ERROR: cartographer_node not ready
[odom-fusion] ERROR: /ekf_filter_node is not visible
```

Fix:

- `rk3588_start_carto_localization.sh` now supports:

```text
START_ODOM_FUSION=0
```

- `rk3588_start_nav2_carto.sh` launches localization with `START_ODOM_FUSION=0` after it starts odom fusion itself.

Validation:

- `rk3588_start_nav2_carto.sh` completed successfully with `NAV2_ENABLE_DRIVE=0`.
- `/scan`, `/imu`, `/rf2o/odom_raw`, `/odom_rf2o_guarded`, `/odom`, `/map`, `/map_static`, global costmap, and local costmap each had one publisher.
- `/navigate_to_pose` and `/compute_path_to_pose` each had one action server.
- TF chain was present:

```text
map -> odom -> base_link -> laser
```

- Final chassis state remained:

```text
BRAKE_STATUS_SAFE
emergency_stop=True
control_authorized=False
```

## Recurrent issue 9: Power-cycle Nav2 lifecycle stall and manual recovery

Observed on 2026-06-16 after the board came back online:

- The baseline demo stack was running (`medicine_chassis_bridge`, `pc_delivery_demo.launch.py`, `sllidar_node`, task manager, voice dispatcher, web dashboard).
- `/scan` was healthy at about 10 Hz, but Nav2 was not really up.
- `/navigate_to_pose` had only clients and no action server before recovery.
- Starting `NAV2_ENABLE_DRIVE=0 bash /mnt/sdcard/rk3588_start_nav2_carto.sh` can outlive the SSH timeout. Treat a client-side timeout as unknown, then check board-side processes and logs instead of assuming the start failed.

Safe recovery order:

```bash
bash /mnt/sdcard/rk3588_safe_stop.sh
bash /mnt/sdcard/rk3588_check_brake_status.sh
NAV2_ENABLE_DRIVE=0 bash /mnt/sdcard/rk3588_start_nav2_carto.sh
```

The safe stop must report:

```text
BRAKE_STATUS_SAFE
emergency_stop=True
control_authorized=False
mode=HOLD
PWM 1500/1500
```

After startup, verify these before any motion authorization:

```bash
ps -ef | grep -E 'rf2o|rk3588_guarded_odom|ekf_node|cartographer|static_map_server|navigation_launch'
tail -n 80 /tmp/rk3588_odom_fusion.log
tail -n 120 /tmp/rk3588_carto_localization.log
tail -n 120 /tmp/rk3588_nav2_carto_navigation.log
ros2 action info /navigate_to_pose
ros2 lifecycle get /controller_server
ros2 lifecycle get /planner_server
ros2 lifecycle get /bt_navigator
ros2 lifecycle get /behavior_server
ros2 lifecycle get /waypoint_follower
ros2 lifecycle get /velocity_smoother
```

Lifecycle failure pattern:

- `navigation_launch.py` may start Nav2 nodes, but lifecycle manager can time out on `/controller_server/change_state`.
- Example log symptom: `failed to send response to /controller_server/change_state (timeout)`.
- Initial state can be: `controller_server inactive [2]`, other Nav2 lifecycle nodes `unconfigured [1]`, while `static_map_server` is already `active [3]`.
- Manual `ros2 lifecycle set /planner_server configure` and `activate` worked in this state.
- Manual activation of `bt_navigator` printed `Transitioning failed` and remained `inactive [2]`, but `/navigate_to_pose` action server appeared from `/bt_navigator`. Re-check this exact state before sending a goal; do not assume fully healthy drive readiness from action server presence alone.

Correct PowerShell + plink pattern for remote lifecycle loops:

```powershell
@'
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash
for node in bt_navigator behavior_server waypoint_follower velocity_smoother; do
  echo "BEFORE:$node"
  ros2 lifecycle get "/$node" || true
  echo "CONFIG:$node"
  timeout 30 ros2 lifecycle set "/$node" configure || true
  echo "ACT:$node"
  timeout 30 ros2 lifecycle set "/$node" activate || true
  echo "AFTER:$node"
  ros2 lifecycle get "/$node" || true
done
echo ACTION
timeout 10 ros2 action info /navigate_to_pose || true
'@ | & 'D:\Program Files\PuTTY\plink.exe' -batch -ssh elf@192.168.31.125 -pw <password> "bash -s"
```

Do not authorize chassis until:

- `BRAKE_STATUS_SAFE` has been verified after startup.
- `/scan`, RF2O, guarded odom, EKF `/odom`, Cartographer localization, `/map_static`, and TF are healthy.
- `/navigate_to_pose` has an action server.
- Lifecycle state has been rechecked, especially `bt_navigator` and `controller_server`.
- RViz/Web alignment looks correct.

## Recurrent issue 10: Short-goal test must be relative and must parse action status

Observed on 2026-06-17:

- Nav2/Cartographer came up cleanly after `NAV2_ENABLE_DRIVE=0`.
- User visually confirmed scan/map alignment.
- First real drive authorization worked and the script always returned the chassis to:

```text
BRAKE_STATUS_SAFE
emergency_stop=True
control_authorized=False
mode=HOLD
PWM 1500/1500
```

Problem:

- `/mnt/sdcard/rk3588_nav2_short_goal_test.sh` used fixed absolute `map` coordinates by default:

```text
x=0.05 y=-0.164 yaw=-0.02
```

- This is not a relative short move. Once the robot pose changes, the same defaults can become a larger or invalid goal.
- One retry to `x=0.50 y=-0.01` moved the robot, but Nav2 still finished with `ABORTED`.
- `ros2 action send_goal` returned process rc `0` even when the action result text said `Goal finished with status: ABORTED`; scripts must parse the result text, not trust the shell rc alone.

Important observations:

- Failed absolute goal:

```text
GridBased: failed to create plan with tolerance 0.10
Planning algorithm GridBased failed to generate a valid path
Goal finished with status: ABORTED
```

- Earlier large/old goal from RViz/task context showed:

```text
Failed to make progress
Goal failed
```

- After motion, Cartographer constraints improved into roughly 60-80% local scores, and current pose became about:

```text
map -> base_link x ~= 1.00 y ~= 0.43 yaw ~= 1 deg
/odom x ~= 0.664 y ~= 0.483
```

Fix applied:

- Local and board `/mnt/sdcard/rk3588_nav2_short_goal_test.sh` now compute a relative target from live `map -> base_link`.
- Defaults are conservative:

```text
distance=0.12m lateral=0.00m yaw_delta=0.00rad
```

- Oversized relative requests are refused:

```text
abs(distance) > 0.20
abs(lateral) > 0.10
abs(yaw_delta) > 0.35
```

- Added `--dry-run` mode to compute and print the target without enabling drive or sending a goal.
- Added action-result parsing: only `Goal finished with status: SUCCEEDED` counts as success. `ABORTED` now makes the script fail.

Validation:

```bash
/mnt/sdcard/rk3588_nav2_short_goal_test.sh --dry-run 0.12 0.00 0.00
```

produced a target about 12 cm ahead of the current `map -> base_link` pose and did not authorize drive.

Next motion rule:

- Do not send another autonomous goal until the operator is ready and the area is clear.
- Prefer the fixed relative script with `--dry-run` first, then run the real command only after checking the generated target in RViz/Web.

## Recurrent issue 11: BackUp can succeed while global localization jumps

Observed on 2026-06-17:

- A `/backup` test with target `x=-0.12`, speed `0.04m/s`, time allowance 8s was accepted but aborted:

```text
Exceeded time allowance before reaching the DriveOnHeading goal
backup failed
Goal finished with status: ABORTED
```

- A smaller `/backup` test with target `x=-0.05`, speed `0.06m/s`, time allowance 5s succeeded:

```text
Goal finished with status: SUCCEEDED
max feedback distance_traveled ~= 0.0775m
```

- However, the dashboard/global `map -> base_link` pose jumped much more than the commanded 5cm:

```text
before x ~= 0.1726 y ~= 0.3321 yaw ~= -2.675
after  x ~= -0.1277 y ~= 0.4073 yaw ~= -2.729
delta euclid ~= 0.31m
```

This means the action behavior can report success while Cartographer/global pose is still settling or jumping. Do not treat one successful BackUp action as proof that full Nav2 closed-loop delivery is ready.

Next rule:

- Stop after the successful 5cm backup and verify physical motion and RViz scan/map alignment manually.
- Do not continue with larger goals until the `map -> base_link` pose is stable for at least several seconds while the robot is stationary.
- For near-term chassis dead-zone tests, compare physical movement, `/odom`, `/backup` feedback, and `map -> base_link`; do not rely on only one signal.

## Recurrent issue 12: Manual RViz initial pose recovers Cartographer after drift

Observed on 2026-06-17 after backup tests:

- User reported scan/map no longer aligned and sent a screenshot showing obvious drift.
- Immediate action was safe stop; chassis confirmed:

```text
BRAKE_STATUS_SAFE
emergency_stop=True
control_authorized=False
mode=HOLD
PWM 1500/1500
```

- Drifted pose before recovery:

```text
map -> base_link x ~= 0.17 y ~= 3.57 yaw ~= 97.6 deg
trajectory states: [0 frozen, 1/2/3 finished or inactive states, 3 active before recovery]
```

Manual recovery flow:

```bash
nohup env INITIALPOSE_KEEP_ALIVE=0 INITIALPOSE_YAW_OFFSET_DEG=0 \
  python3 /mnt/sdcard/medicine_robot_data/scripts/carto_initialpose_once.py \
  > /tmp/carto_initialpose_once_manual.log 2>&1 < /dev/null &
```

Then the operator used RViz `2D Pose Estimate` at the visually correct robot pose.

Confirmed result:

```text
received /initialpose: x=1.143 y=0.046 yaw=1.7 deg
finish trajectory 3: code=0 message='Finished trajectory 3.'
start trajectory: id=4 code=0 message='Success.'
trajectory states include active trajectory 4
map -> base_link x ~= 1.14 y ~= 0.04 yaw ~= 1 deg
```

Rule:

- After any visible localization drift, do not send more motion goals.
- Safe stop first, then recover with RViz `2D Pose Estimate` through `carto_initialpose_once.py`.
- Only consider motion again after the user visually confirms scan/map alignment and `map -> base_link` remains stable while stationary.

## Recurrent issue 13: Static drift came from Cartographer map->odom, not chassis motion

Observed on 2026-06-17 after manual relocalization:

- The chassis stayed safe and uncommanded:

```text
BRAKE_STATUS_SAFE
emergency_stop=True
control_authorized=False
target/current velocity=0
```

- `odom -> base_link` stayed stable around `x=0.736 y=0.417 yaw=2.73 deg`.
- But `map -> odom` moved from about `x=0.393 y=-0.351 yaw=-1.34 deg` to `x=0.827 y=-1.504 yaw=-7.17 deg`.
- Dashboard `map -> base_link` moved from about `x=1.14 y=0.047 yaw=1.3 deg` to `x=1.61 y=-1.18 yaw=-4.7 deg` while the robot was stationary.

Conclusion:

- The drift source was Cartographer localization, not a real chassis move.
- The localization config was too permissive for post-initialpose stability.

Tightened settings on 2026-06-17:

- `optimize_every_n_nodes = 60`
- `max_constraint_distance = 1.0`
- `min_score = 0.70`
- `global_localization_min_score = 0.72`
- `global_sampling_ratio = 0.03`
- `constraint_builder.sampling_ratio = 0.30`
- `fast_correlative_scan_matcher` window reduced from `8m / 180deg` to `1m / 20deg`

Applied to both:

- `/mnt/sdcard/medicine_robot_ws/src/medicine_robot_bringup/config/rk3588_carto_localization.lua`
- `/mnt/sdcard/medicine_robot_ws/install/medicine_robot_bringup/share/medicine_robot_bringup/config/rk3588_carto_localization.lua`

Next rule:

- Restart Cartographer localization before the next motion test, then verify a few minutes of static `map -> base_link` stability again.

## Recurrent issue 14: BackUp can be a false positive when RF2O/odom drifts

Observed on 2026-06-17 after power recovery and tightened Cartographer localization:

- Pre-test brake state was safe:

```text
BRAKE_STATUS_SAFE
emergency_stop=True
control_authorized=False
mode=HOLD
PWM 1500/1500
```

- A 3 cm `/backup` action was run:

```bash
ros2 action send_goal /backup nav2_msgs/action/BackUp \
  "{target: {x: -0.03, y: 0.0, z: 0.0}, speed: 0.06, time_allowance: {sec: 4, nanosec: 0}}" \
  --feedback
```

- Action result:

```text
Goal finished with status: SUCCEEDED
max feedback distance_traveled ~= 0.03065 m
total_elapsed_time ~= 1.80 s
```

- `map -> base_link` around the test:

```text
before       x=0.244981 y= 0.012730 yaw=4.781 deg
after_action x=0.233292 y=-0.021798 yaw=4.287 deg
after_safe   x=0.226077 y=-0.021607 yaw=3.989 deg
```

- The final safe stop returned to:

```text
BRAKE_STATUS_SAFE
emergency_stop=True
control_authorized=False
mode=HOLD
PWM 1500/1500
```

- 60 s stationary observation after safe stop:

```text
start x=0.222985 y=-0.021851 yaw=5.100 deg
end   x=0.221891 y=-0.024613 yaw=4.016 deg
max_xy_delta ~= 0.0030 m
max_yaw_delta ~= 1.084 deg
```

Important correction:

- The operator reported that the car did not physically move during this 3 cm BackUp.
- Therefore this was not a successful chassis motion proof.
- It was a false positive: Nav2 `/backup` judged progress from `/odom`, and `/odom` comes from RF2O/guarded odom/EKF, not wheel encoders.
- RF2O/Cartographer can drift or scan-match by a few centimeters while the chassis is stationary, causing `/backup` to return `SUCCEEDED`.

Additional checks after the report:

- The system was safe after the test:

```text
BRAKE_STATUS_SAFE
emergency_stop=True
control_authorized=False
mode=HOLD
PWM 1500/1500
```

- Enabling drive without nonzero `/cmd_vel` successfully changed ArduPilot to MANUAL/armed state:

```text
base_mode=193
custom_mode=0
custom_mode_name=MANUAL
system_status=4
```

- Safe stop returned it to HOLD/disarmed:

```text
base_mode=1
custom_mode=4
custom_mode_name=HOLD
system_status=3
```

Conclusion:

- `/backup` action success alone must not be treated as physical movement.
- For this no-encoder robot, any motion validation must include operator visual confirmation and live chassis command evidence.
- The next diagnostic should capture `/cmd_vel`, `/medicine/chassis_status`, ArduPilot RC override/servo outputs, and `/odom` at the same time during a very short controlled command.

Suggested next step:

- Do not run another Nav2 action as proof of movement.
- If the operator is ready and the area is clear, run an instrumented low-speed manual `/cmd_vel` pulse or Nav2 BackUp with concurrent logging:
  - `/cmd_vel`
  - `/medicine/chassis_status`
  - nested ArduPilot `custom_mode`, `base_mode`, `rc_override`, and `servo_outputs`
  - `/odom` and `map -> base_link`
- Abort immediately with `rk3588_safe_stop.sh`.

## Recurrent issue 15: Tiny cmd_vel reaches RC input but does not change servo outputs

Observed on 2026-06-17 after the false-positive BackUp:

- Ran an instrumented tiny reverse pulse on the already running system:

```text
linear.x = -0.035 m/s
angular.z = 0.0
duration ~= 0.8 s
```

- Safety sequence worked:

```text
before: BRAKE_STATUS_SAFE, HOLD, emergency_stop=True, control_authorized=False
enabled: MANUAL, base_mode=193, system_status=4, emergency_stop=False, control_authorized=True
after: BRAKE_STATUS_SAFE, HOLD, emergency_stop=True, control_authorized=False
```

- During the pulse, `chassis_bridge` did receive and process the command:

```text
target=(-0.035, 0.0)
current=(-0.035, 0.0)
cmd_count increased from 1850 to 1868
cmd_timed_out=False during the pulse
```

- The bridge produced a non-neutral RC override:

```text
rc_override last_throttle_pwm=1535
rc_override last_steering_pwm=1500
rc_channels chan1_raw=1500
rc_channels chan3_raw=1535
```

- But reported servo outputs stayed neutral:

```text
servo7_raw=1500
servo8_raw=1500
```

- `/odom` still moved slightly even though this does not prove physical motion:

```text
odom x,y roughly changed from -0.0047,-0.0131 to -0.0057,-0.0179
```

Conclusion:

- The command path up to ArduPilot RC input is alive.
- The missing physical motion is likely downstream of RC input:
  - PWM 1535 may be too small and inside the chassis/controller deadband, or
  - ArduPilot mode/output/mixer/servo function is not driving the motor outputs from RC3 in this configuration, or
  - the motor output channels being watched (`servo7/8`) are not the actual drive outputs.

Next diagnostic:

- Do not rely on `/odom` for movement proof.
- Query or inspect ArduPilot output mapping and parameters, especially actual motor/servo output channels, before sending larger commands.
- If the area is clear and the operator is watching, the next live test should be a stepped `/cmd_vel` pulse with physical confirmation and live `rc_channels` + `servo_outputs`, starting low and increasing only enough to leave the known deadband.

## Recurrent issue 16: A short +0.05 cmd_vel pulse did not leave neutral outputs

Observed on 2026-06-17 after the forward step probe:

- Drive enable sequence succeeded:

```text
authorize_control=true -> control_authorized=True
set_emergency_stop=false -> estop=False
set_mode=true -> MANUAL, base_mode=65
arm=true -> MANUAL, base_mode=193, system_status=4
```

- Pre-test status showed the expected safe baseline:

```text
BRAKE_STATUS_SAFE
emergency_stop=True
control_authorized=False
mode=HOLD
throttle_pwm=1500
steering_pwm=1500
```

- During the short `+0.05 m/s` probe, the bridge status never showed a nonzero target/current, and the reported outputs stayed neutral:

```text
target_linear=0.0
current_linear=0.0
rc_override last_throttle_pwm=1500
rc_override last_steering_pwm=1500
servo7_raw=1500
servo8_raw=1500
```

- The step probe ended safely:

```text
BRAKE_STATUS_SAFE
emergency_stop=True
control_authorized=False
mode=HOLD
base_mode=1
```

Conclusion:

- The latest probe did not produce evidence of a real motor command beyond neutral outputs.
- Either the pulse missed the controller timing window, or the path from `/cmd_vel` to ArduPilot output is more fragile than expected.
- For the next test, use a single-process publisher/observer if possible, and capture the exact timestamped `/cmd_vel` payload together with `rc_override` and `servo_outputs`.

Correction / follow-up:

- The next single-process publisher/observer proved the previous short pulse likely missed the timing/discovery window.

## Recurrent issue 17: Single-process +0.05 probe proves command reaches S7/S8

Observed on 2026-06-17:

- A single Python process handled:
  - service calls,
  - `/cmd_vel` publisher discovery,
  - `+0.05 m/s` publishing for 2.0 s,
  - live `/medicine/chassis_status` observation,
  - and final safe stop.

- Before the pulse:

```text
BRAKE_STATUS_SAFE
emergency_stop=True
control_authorized=False
mode=HOLD
rc1/3=(1500,1500)
servo7/8=(1500,1500)
```

- Drive enable reached:

```text
control_authorized=True
emergency_stop=False
mode=MANUAL
base_mode=193
system_status=4
```

- During `linear.x=+0.05`:

```text
target_linear=0.05
current_linear=0.05
cmd_count_delta=96
rc_override=(1450,1500)
rc1/3=(1500,1450)
servo7/8=(1568,1568)
max_rc3_delta=50
max_servo7_delta=68
max_servo8_delta=68
```

- After publishing zero and safe stop:

```text
rc1/3=(1500,1500)
servo7/8=(1500,1500)
BRAKE_STATUS_SAFE
emergency_stop=True
control_authorized=False
mode=HOLD
```

Conclusion:

- The ROS `/cmd_vel` -> chassis_bridge -> ArduPilot RC override -> ArduPilot S7/S8 output chain is working for `+0.05 m/s`.
- Nav2 and RF2O are not the current blocker for physical motion.
- If the robot still does not move while `servo7/8` leave neutral, the problem is downstream of ArduPilot S7/S8 output:
  - S7/S8 wiring,
  - motor driver enable,
  - motor power,
  - driver input mode,
  - PWM deadband,
  - or mechanical/electrical chassis issue.

Next diagnostic:

- Ask the operator whether the wheels or chassis moved during the successful single-process `+0.05` probe.
- If not, check hardware after S7/S8 before more Nav2 tests.

Operator confirmation:

- The operator reported that the car did move during the single-process `+0.05 m/s` probe.
- Therefore the full forward chain is proven on the real chassis, not only in telemetry.

## Recurrent issue 18: Reverse output is much weaker than forward output

Observed on 2026-06-17:

- A single-process `-0.05 m/s` reverse pulse was run with the same reliable method as the forward probe.
- Drive enable reached:

```text
control_authorized=True
emergency_stop=False
mode=MANUAL
base_mode=193
system_status=4
```

- During `linear.x=-0.05`:

```text
target_linear=-0.05
current_linear=-0.05
cmd_count_delta=85
rc_override=(1550,1500)
rc1/3=(1500,1550)
servo7/8=(1488,1488)
max_rc3_delta=50
max_servo7_delta=12
max_servo8_delta=12
```

- Compare with the earlier forward `+0.05` probe:

```text
forward +0.05:
rc1/3=(1500,1450)
servo7/8=(1568,1568)
max_servo7_delta=68
max_servo8_delta=68

reverse -0.05:
rc1/3=(1500,1550)
servo7/8=(1488,1488)
max_servo7_delta=12
max_servo8_delta=12
```

- The test ended with:

```text
BRAKE_STATUS_SAFE
emergency_stop=True
control_authorized=False
mode=HOLD
rc1/3=(1500,1500)
servo7/8=(1500,1500)
```

Conclusion:

- Reverse command reaches ArduPilot and S7/S8, but the output magnitude is far weaker than forward.
- This likely explains why Nav2 `/backup` did not visibly move the chassis: the reverse S7/S8 PWM delta was only about 12.
- The issue is probably ArduPilot/motor-output mixing, throttle curve/deadband, reverse limiting, or driver behavior for reverse PWM, not ROS topic delivery.

Next diagnostic:

- Read ArduPilot parameters for RC3/SERVO7/SERVO8 and rover throttle/reverse limits.
- Specifically compare RC3 input range/deadzone with SERVO7/8 min/max/trim/function and any reverse throttle limits.

## Recurrent issue 19: ArduPilot params explain weak reverse near deadzone

Observed on 2026-06-17:

- A short maintenance window stopped `chassis_bridge`, read ArduPilot params directly from `/dev/ttyS9 @ 921600`, then restarted `chassis_bridge`.
- Post-maintenance output was safe:

```text
emergency_stop=True
control_authorized=False
target/current=0
mode=HOLD
rc1/3=(1500,1500)
servo7/8=(1500,1500)
```

- Note: after bridge restart, `rk3588_check_brake_status.sh` can show `throttle_pwm=None` and `steering_pwm=None` because `last_rc_*` has not yet been populated; actual `rc_channels` and `servo_outputs` were neutral.

Relevant ArduPilot parameters:

```text
FRAME_CLASS=1
FRAME_TYPE=0
PILOT_STEER_TYPE=0
RCMAP_ROLL=1
RCMAP_THROTTLE=3
RCMAP_PITCH=2
RCMAP_YAW=4

RC1_MIN=1240
RC1_MAX=1760
RC1_TRIM=1495
RC1_DZ=30

RC3_MIN=1288
RC3_MAX=1700
RC3_TRIM=1514
RC3_DZ=30

SERVO7_FUNCTION=73
SERVO7_MIN=1100
SERVO7_MAX=1900
SERVO7_TRIM=1500
SERVO7_REVERSED=0

SERVO8_FUNCTION=74
SERVO8_MIN=1100
SERVO8_MAX=1900
SERVO8_TRIM=1500
SERVO8_REVERSED=0

SERVO1_FUNCTION=0
SERVO3_FUNCTION=0
MOT_THR_MIN=0
MOT_THR_MAX=100
MOT_STR_THR_MIX=0.5
MOT_SLEWRATE=100
CRUISE_SPEED=2.0
CRUISE_THROTTLE=50
ATC_ACCEL_MAX=1.0
ATC_DECEL_MAX=0.0
FS_THR_ENABLE=1
FS_THR_VALUE=910
FS_ACTION=2
BRD_SAFETY_DEFLT=0
```

Interpretation:

- `SERVO7_FUNCTION=73` and `SERVO8_FUNCTION=74` confirm S7/S8 are the active left/right throttle outputs.
- `RC3_TRIM=1514` and `RC3_DZ=30` explain the weak reverse response:
  - Forward probe sent RC3 around `1450`, which is about 64 below trim and well outside deadzone.
  - Reverse probe sent RC3 around `1550`, which is only about 36 above trim, just barely outside the 30 us deadzone.
  - That produced only `servo7/8 ~= 1488`, a 12 us output delta.
- The bridge currently assumes `ardupilot_rc_pwm_mid=1500`, but ArduPilot throttle trim is actually 1514. This asymmetry biases small commands.

Likely fix direction:

- Align `ardupilot_rc_pwm_mid` with `RC3_TRIM=1514`, or separately support throttle mid distinct from steering mid.
- After changing the bridge mapping, retest:
  - `+0.05 m/s`
  - `-0.05 m/s`
  - compare `servo7/8` deltas and physical motion.

## Recurrent issue 20: ardupilot_rc_pwm_mid changed to 1514 and reverse improved

Applied on 2026-06-17:

- Changed `ardupilot_rc_pwm_mid` from `1500` to `1514` to match ArduPilot `RC3_TRIM=1514`.
- Applied to:

```text
D:\A1\chassis_bridge_ardupilot_serial_readonly.yaml
/mnt/sdcard/medicine_robot_ws/src/medicine_chassis_bridge/config/chassis_bridge_ardupilot_serial_readonly.yaml
/mnt/sdcard/medicine_robot_ws/install/medicine_chassis_bridge/share/medicine_chassis_bridge/config/chassis_bridge_ardupilot_serial_readonly.yaml
```

- Remote backups were created:

```text
.../chassis_bridge_ardupilot_serial_readonly.yaml.bak_mid1514_20260617_171958
```

- Live bridge parameter after restart:

```text
ardupilot_rc_pwm_min=1380
ardupilot_rc_pwm_mid=1514
ardupilot_rc_pwm_max=1620
ardupilot_rc_steering_pwm_mid=1500
```

Post-change comparison:

```text
forward +0.05:
rc1/3=(1500,1458)
servo7/8=(1552,1552)
max_rc3_delta=42
max_servo7_delta=52
max_servo8_delta=52

reverse -0.05:
rc1/3=(1500,1558)
servo7/8=(1468,1468)
max_rc3_delta=58
max_servo7_delta=32
max_servo8_delta=32
```

Before the change, reverse `-0.05` only reached `servo7/8=(1488,1488)`, about 12 us from neutral. After the change it reached about 32 us from neutral, so reverse is stronger but still weaker than forward.

Safe final state after the comparison:

```text
BRAKE_STATUS_SAFE
emergency_stop=True
control_authorized=False
mode=HOLD
throttle_pwm=1514
steering_pwm=1500
```

Next diagnostic:

- Retest a very small `/backup` goal with concurrent RC/SERVO logging.
- Treat action success as insufficient by itself; require physical observation plus servo output evidence.

## Recurrent issue 21: Reverse -0.08 produces clearly stronger S7/S8 output

Observed on 2026-06-17 after the operator reported that the 3 cm `/backup` movement was still not obvious:

- Ran a single-process manual reverse pulse:

```text
linear.x=-0.08
duration=1.3 s
```

- During the pulse:

```text
target_linear=-0.08
current_linear=-0.08
rc1/3=(1500,1585)
servo7/8=(1396,1396)
max_rc3_delta_from_1514=71
max_servo7_delta=104
max_servo8_delta=104
```

- Final state:

```text
BRAKE_STATUS_SAFE
emergency_stop=True
control_authorized=False
mode=HOLD
throttle_pwm=1514
steering_pwm=1500
```

Interpretation:

- Reverse at `-0.05` after the mid fix produced `servo7/8=(1468,1468)`, about 32 us from neutral.
- Reverse at `-0.08` produced `servo7/8=(1396,1396)`, about 104 us from neutral.
- If `-0.05` is still visually weak, use around `-0.08` as the next practical reverse test magnitude.

Next diagnostic:

- Ask the operator whether the `-0.08` pulse was visibly backward.
- If yes, tune Nav2 `/backup` to command roughly this effective reverse output.

## Recurrent issue 22: Guarded odom should use cmd_vel direction for reverse

Observed on 2026-06-17:

- After the reverse-movement work, a `/backup` test with `target.x=-0.06` and `speed=0.08` succeeded.
- The feedback distance was about `0.0778 m`.
- More importantly, `/odom` now moved in the correct reverse direction:

```text
/odom x ~= -0.102 m
/odom y ~= -0.000 m
```

- Before this fix, reverse tests could still look wrong or drift because the guarded odom was trusting RF2O raw direction too much.

Fix:

- `rk3588_guarded_odom.py` now has:

```text
force_linear_direction_from_cmd=True
```

- When a clear linear command is present, the node keeps RF2O distance magnitude but uses the commanded forward/backward direction.
- `raw_x_sign=-1.0` and `raw_y_sign=-1.0` remain in place.

Validation:

- `BRAKE_STATUS_SAFE` after the test:

```text
emergency_stop=True
control_authorized=False
mode=HOLD
throttle_pwm=1514
steering_pwm=1500
```

- TF reads after the test:

```text
map -> base_link  x ~= 0.060  y ~= -0.017  yaw ~= 10.8 deg
odom -> base_link x ~= -0.101 y ~= -0.000 yaw ~= 0.2 deg
map -> odom       x ~= 0.158  y ~= 0.003  yaw ~= 11.0 deg
```

- Static 30 s observation showed `map -> base_link` stayed stable within about `0.001 m` and `0.024 deg` from the first sample.

Next rule:

- Keep this guarded-odom direction override unless a later full end-to-end test proves the board-side reverse sign can be trusted again.
- For now, use the new reverse behavior as the baseline for Nav2 `/backup` and short retreat tests.

## Recurrent issue 23: Cartographer was over-locked and could not correct reverse drift

Observed on 2026-06-17 after repeated "scan shifted forward" reports:

- The board-side static lidar TF was already correct for this session:

```text
LIDAR_LASER_YAW=3.14159
base_link -> laser yaw = 180 deg
```

- Cartographer localization was still too rigid:

```text
real_time_correlative_scan_matcher.linear_search_window = 0.03
motion_filter.max_distance_meters = 0.03
POSE_GRAPH.optimize_every_n_nodes = 100000
POSE_GRAPH.constraint_builder.min_score = 0.95
POSE_GRAPH.global_sampling_ratio = 0.0
```

- Logs showed repeated:

```text
0 computations resulted in 0 additional constraints
Motion filter reduced the number of nodes to ~1-2%
```

Interpretation:

- After a short reverse motion, Cartographer was not really re-locking on scan.
- It was mostly trusting `/odom`, so the map overlay could stay consistently off even when TF and safe-stop looked correct.

Fix applied:

- Relaxed the localization profile to let scan matching actually correct several centimeters of drift:

```text
linear_search_window = 0.12
angular_search_window = 5 deg
motion_filter.max_distance_meters = 0.01
motion_filter.max_time_seconds = 0.5
optimize_every_n_nodes = 30
min_score = 0.72
global_localization_min_score = 0.78
constraint_builder.sampling_ratio = 0.30
fast_correlative_scan_matcher.linear_search_window = 0.60
fast_correlative_scan_matcher.angular_search_window = 10 deg
```

Validation:

- The new config was synced to both source and install paths.
- A new active trajectory was started with the updated localization config.
- The robot remained in `BRAKE_STATUS_SAFE` throughout.

Next rule:

- Stop treating this as a pose-nudge problem.
- First validate whether the relaxed Cartographer profile now keeps scan/map aligned after a short reverse motion; only then return to fine pose tuning if needed.

## Recurrent issue 24: Do not call localization-only "all nodes started"

Observed on 2026-06-18:

- After starting `/mnt/sdcard/rk3588_start_localization_only.sh`, the graph had:

```text
/cartographer_node
/cartographer_occupancy_grid_node
/sllidar_node
/base_to_laser_tf
/CLaserOdometry2DNode
/rk3588_guarded_odom
/ekf_filter_node
/static_map_server
```

- But the full Nav2 navigation stack was missing:

```text
/controller_server
/planner_server
/bt_navigator
/behavior_server
/waypoint_follower
/velocity_smoother
```

- The mistake was describing the state as if the nodes were fully started. That is misleading: localization-only is not full Nav2.

Rule:

- Always explicitly distinguish:

```text
localization-only: lidar + Cartographer + odom fusion + static_map_server
full Nav2: localization-only plus controller/planner/bt_navigator/behavior/waypoint/velocity_smoother
```

- Before saying "nodes are started" or "startup is complete", run or mentally check both groups.
- If only localization is running, say "定位栈已启动，Nav2 导航栈未启动".
- Starting full Nav2 does not mean authorizing chassis motion; keep `NAV2_ENABLE_DRIVE=0` unless explicitly testing motion.

## Recurrent issue 25: Over-relaxed Cartographer localization can jump the map frame

Observed on 2026-06-19 during a real `/backup` 2 cm validation:

- `/backup` itself succeeded: feedback reached about `0.021 m`, and `odom -> base_link` moved about `-0.022 m`.
- The robot was returned to `BRAKE_STATUS_SAFE`.
- But the relaxed localization profile from issue 23 let Cartographer keep adding broad constraints while stationary, and `map -> base_link` jumped to meter-scale wrong poses such as:

```text
map -> base_link ~= x -0.630, y 5.321, yaw 57 deg
map -> odom      ~= x 0.38, y 4.27, yaw -35 to -55 deg
```

Interpretation:

- The `/backup` behavior and guarded odom chain worked for a tiny movement.
- The localization profile was too loose for continued safe validation: low `min_score`, large `max_constraint_distance`, and nonzero global sampling allowed false constraints to pull `map -> odom`.

Fix direction:

- Keep short-range local scan matching available, but make pose graph constraints conservative again:

```text
optimize_every_n_nodes = 90
max_constraint_distance = 0.25
min_score = 0.82
global_localization_min_score = 0.88
global_sampling_ratio = 0.0
constraint_builder.sampling_ratio = 0.08
fast_correlative_scan_matcher.linear_search_window = 0.25
fast_correlative_scan_matcher.angular_search_window = 5 deg
```

Rule:

- After any real movement test, validate both `odom -> base_link` and `map -> base_link`.
- If `odom` looks correct but `map` jumps, stop motion testing immediately, safe-stop, and treat it as Cartographer pose-graph instability rather than a chassis problem.

## Recurrent issue 26: After power loss, /scan frequency can look fine while lidar data is bad

Observed on 2026-06-19 after battery/power loss and restart:

- `/scan` existed and reported about `10 Hz`, but the scan was visually unstable and did not fit the map.
- Raw scan quality showed only about `27-112` valid points out of `1080` angles, later even no new frames, although USB did not show repeated disconnects.
- A stale one-off diagnostic Python node (`/scan_quality_probe`) remained subscribed to `/scan` with RELIABLE QoS after a timed-out check.
- A partial lidar restart created duplicate `/sllidar_node` and duplicate `/base_to_laser_tf`, causing ROS warnings and confusing graph state.

Recovery that worked:

```text
- kill stale diagnostic Python process
- clear ROS daemon cache only for CLI graph freshness
- stop all lidar wrappers and children:
  rk3588_start_lidar.sh
  rk3588_lidar_bringup.launch.py
  sllidar_node
  static_transform_publisher base_link -> laser
- confirm /dev/ttyUSB0 is no longer held
- start exactly one /mnt/sdcard/rk3588_start_lidar.sh
- verify one /sllidar_node and one /base_to_laser_tf
- verify raw scan quality, not only Hz
```

Good recovered scan quality in the same scene:

```text
/scan ~= 10 Hz
valid points ~= 924-949 / 1080
age ~= 0.10 s
single /sllidar_node
single /base_to_laser_tf
```

Rule:

- After power loss or lidar restart, do not trust `/scan` just because `ros2 topic hz /scan` is around `10 Hz`.
- Always check valid point count and duplicate node count before judging localization.
- Avoid leaving one-off Python/RCLPY scan probes running; wrap them with short timeouts and verify no `/scan_probe*` or `/scan_quality*` node remains.
- If scan quality was bad while Cartographer was running, restart Cartographer/Nav2 after lidar recovery so localization does not continue from bad scan state.

Follow-up from the same incident:

- Stopping Nav2/Cartographer/RF2O alone did not recover scan quality.
- Temporarily stopping `medicine_web_dashboard` and clean-restarting lidar made `/scan` stable for 30 seconds at about `774-806 / 1080` valid points.
- Starting full Nav2/Cartographer again while keeping `medicine_web_dashboard` down kept `/scan` stable at about `773-817 / 1080`.
- Starting RViz without the Web dashboard also kept `/scan` stable at about `787-862 / 1080`, even though RViz was CPU-heavy.

Interpretation:

- Do not blame RViz first. In this incident, RViz alone was acceptable.
- The suspicious trigger is the Web dashboard's RELIABLE `/scan` subscription plus high CPU load.
- For navigation debugging, keep `medicine_web_dashboard` stopped until its scan subscription is made lighter, BEST_EFFORT, throttled, or disabled.
