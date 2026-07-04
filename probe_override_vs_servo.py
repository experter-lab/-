#!/usr/bin/env python3
"""单进程独占 ttyS9：
- 一边以 10Hz 发 RC_CHANNELS_OVERRIDE（CH3=throttle 偏 -40，CH1=steering 中位）
- 一边读 SERVO_OUTPUT_RAW 和 RC_CHANNELS
- 实时打印 → 看 CH3 / SERVO7 / SERVO8 的实际值

先 kill chassis_bridge_node 再运行。
"""
import sys, time
from pymavlink import mavutil

PORT = "/dev/ttyS9"
BAUD = 921600

# 想下发的 PWM (chassis_bridge 实测刚才发的就是这个组合)
THROTTLE_PWM = 1460   # 前进偏移 -40 (因为 invert_throttle=true → 实际飞控看到 -40)
STEERING_PWM = 1500   # 直行

# RCMAP
RC_THROTTLE_CH = 3
RC_STEERING_CH = 1

print(f"==> connect {PORT}@{BAUD}")
m = mavutil.mavlink_connection(PORT, baud=BAUD,
                                source_system=255, source_component=0)
print("==> wait heartbeat (5s)")
hb = m.wait_heartbeat(timeout=5)
if not hb:
    print("NO HEARTBEAT"); sys.exit(1)
print(f"  sys={m.target_system} comp={m.target_component}")
print(f"  armed={'Y' if hb.base_mode & 0x80 else 'N'}  custom_mode={hb.custom_mode}  status={hb.system_status}")

# 启 SERVO_OUTPUT_RAW 数据流 5Hz
m.mav.request_data_stream_send(m.target_system, m.target_component,
                                mavutil.mavlink.MAV_DATA_STREAM_ALL, 10, 1)
m.mav.request_data_stream_send(m.target_system, m.target_component,
                                mavutil.mavlink.MAV_DATA_STREAM_RC_CHANNELS, 10, 1)

# 先持续发 1500/1500 覆盖（防 FS_THR），同时切到 MANUAL 模式
print("==> 先持续发 1500 中位 1 秒（喂熟 FS_THR），再 SET_MODE → MANUAL")
t0 = time.time()
while time.time() - t0 < 1.0:
    chans = [65535]*8
    chans[RC_THROTTLE_CH-1] = 1500
    chans[RC_STEERING_CH-1] = 1500
    m.mav.rc_channels_override_send(m.target_system, m.target_component, *chans)
    time.sleep(0.1)

# SET_MODE → MANUAL (0)，base_mode 必须带 CUSTOM_MODE_ENABLED 并保留 ARMED 位
base_mode = mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED
if hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED:
    base_mode |= mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
m.mav.set_mode_send(m.target_system, base_mode, 0)
print("    SET_MODE → MANUAL(0) sent")
time.sleep(0.5)

# 再等心跳确认 mode 切了
for _ in range(10):
    msg = m.recv_match(type="HEARTBEAT", blocking=True, timeout=0.3)
    if msg and msg.custom_mode == 0:
        hb = msg
        print(f"    ✓ mode confirmed MANUAL, base_mode=0x{hb.base_mode:02x}")
        break
else:
    print(f"    ✗ mode 没切到 MANUAL,当前 custom_mode={msg.custom_mode if msg else '?'}")

# 字段缓存
ch_raw = [None]*8
servo_raw = [None]*8
sys_status_v = None

def send_override(throttle, steering):
    chans = [65535]*8
    chans[RC_THROTTLE_CH-1] = throttle
    chans[RC_STEERING_CH-1] = steering
    m.mav.rc_channels_override_send(m.target_system, m.target_component,
                                     *chans)

print()
print("==> 开始: 持续发 throttle=%d steering=%d, 10Hz" % (THROTTLE_PWM, STEERING_PWM))
print("    time   CH1   CH3       SERVO7 SERVO8     mode   status")
t_start = time.time()
last_send = 0
last_print = 0
while time.time() - t_start < 6.0:
    # 10Hz 下发
    now = time.time()
    if now - last_send >= 0.1:
        send_override(THROTTLE_PWM, STEERING_PWM)
        last_send = now

    # 持续读
    msg = m.recv_match(blocking=True, timeout=0.05)
    if msg is not None:
        t = msg.get_type()
        if t == "RC_CHANNELS":
            for i in range(1, 9):
                ch_raw[i-1] = getattr(msg, f"chan{i}_raw", None)
        elif t == "SERVO_OUTPUT_RAW":
            for i in range(1, 9):
                servo_raw[i-1] = getattr(msg, f"servo{i}_raw", None)
        elif t == "HEARTBEAT":
            hb = msg

    # 4Hz 打印
    if now - last_print >= 0.25:
        last_print = now
        print(f"  {now-t_start:5.2f}  {ch_raw[0]} {ch_raw[2]}      {servo_raw[6]}   {servo_raw[7]}     "
              f"cm={hb.custom_mode if hb else '?'}  st={hb.system_status if hb else '?'}  "
              f"armed={'Y' if hb and (hb.base_mode & 0x80) else 'N'}")

# 收尾：发 release (chans=0)
print()
print("==> 收尾: 发 release override (全 0)")
m.mav.rc_channels_override_send(m.target_system, m.target_component,
                                 0,0,0,0,0,0,0,0)
time.sleep(0.5)
print("done")
