#!/usr/bin/env bash
# 开机自动唤醒底盘 + 每 20 分钟续期 authorize_control (30 min 过期前续上)
# 由 systemd 拉起,失败会自动重启

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

LOG=/tmp/chassis_wake_keepalive.log
log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }

log "=== wake_keepalive daemon starting ==="

# 1) 等 chassis_bridge 服务就绪 (最多 120s)
for i in $(seq 1 60); do
    if ros2 service list 2>/dev/null | grep -q /chassis_bridge/authorize_control; then
        log "chassis_bridge ready after ${i}*2s"
        break
    fi
    sleep 2
done

# 多等几秒让 ardupilot 链路 heartbeat 稳定
sleep 5

# 2) 4 步 wake
log "step 1/4 set_emergency_stop=false"
ros2 service call /chassis_bridge/set_emergency_stop std_srvs/srv/SetBool "{data: false}" 2>&1 | tail -1 | tee -a "$LOG"
sleep 1
log "step 2/4 authorize_control=true"
ros2 service call /chassis_bridge/authorize_control std_srvs/srv/SetBool "{data: true}" 2>&1 | tail -1 | tee -a "$LOG"
sleep 1
log "step 3/4 set_mode=true (MANUAL)"
ros2 service call /chassis_bridge/set_mode std_srvs/srv/SetBool "{data: true}" 2>&1 | tail -1 | tee -a "$LOG"
sleep 1
log "step 4/4 arm=true"
ros2 service call /chassis_bridge/arm std_srvs/srv/SetBool "{data: true}" 2>&1 | tail -1 | tee -a "$LOG"

log "initial wake done, entering keepalive loop (20 min interval)"

# 3) 续期循环 (idempotent - 失败/掉链路也会下一轮重试)
while true; do
    sleep 1200
    if ros2 service call /chassis_bridge/authorize_control std_srvs/srv/SetBool "{data: true}" 2>&1 | tail -1 | grep -q success; then
        log "keepalive OK"
    else
        log "keepalive FAILED - chassis_bridge may be down, re-attempting full wake"
        ros2 service call /chassis_bridge/set_emergency_stop std_srvs/srv/SetBool "{data: false}" >/dev/null 2>&1
        ros2 service call /chassis_bridge/authorize_control std_srvs/srv/SetBool "{data: true}" >/dev/null 2>&1
        ros2 service call /chassis_bridge/set_mode std_srvs/srv/SetBool "{data: true}" >/dev/null 2>&1
        ros2 service call /chassis_bridge/arm std_srvs/srv/SetBool "{data: true}" >/dev/null 2>&1
    fi
done
