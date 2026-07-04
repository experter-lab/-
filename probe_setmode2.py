#!/usr/bin/env python3
"""第二次尝试: 用 MAV_CMD_DO_SET_MODE 强切 MANUAL,看 ACK,再发 throttle 看 SERVO。"""
import sys, time
from pymavlink import mavutil

PORT = "/dev/ttyS9"; BAUD = 921600
m = mavutil.mavlink_connection(PORT, baud=BAUD, source_system=255, source_component=0)
hb = m.wait_heartbeat(timeout=5)
print(f"start: armed={'Y' if hb.base_mode & 0x80 else 'N'} cm={hb.custom_mode} st={hb.system_status}")

m.mav.request_data_stream_send(m.target_system, m.target_component,
                                mavutil.mavlink.MAV_DATA_STREAM_ALL, 10, 1)
m.mav.request_data_stream_send(m.target_system, m.target_component,
                                mavutil.mavlink.MAV_DATA_STREAM_RC_CHANNELS, 10, 1)

# 1s 中位喂熟 throttle (1500 NOT failsafe)
print("==> 1s 中位 RC override 喂熟")
t0 = time.time()
while time.time() - t0 < 1.0:
    chans = [65535]*8
    chans[0] = 1500   # steering
    chans[2] = 1500   # throttle
    m.mav.rc_channels_override_send(m.target_system, m.target_component, *chans)
    time.sleep(0.1)

# 方法 A: MAV_CMD_DO_SET_MODE 切 MANUAL
print("==> MAV_CMD_DO_SET_MODE → MANUAL (custom_mode=0)")
base_mode = mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED
m.mav.command_long_send(
    m.target_system, m.target_component,
    mavutil.mavlink.MAV_CMD_DO_SET_MODE,
    0, base_mode, 0, 0, 0, 0, 0, 0)

# 抓 ACK
t0 = time.time()
while time.time() - t0 < 2.0:
    msg = m.recv_match(blocking=True, timeout=0.3)
    if msg is None: continue
    if msg.get_type() == "COMMAND_ACK" and msg.command == mavutil.mavlink.MAV_CMD_DO_SET_MODE:
        print(f"   ACK: result={msg.result} (0=ACCEPTED,1=TEMP_REJ,2=DENIED,3=UNSUPPORTED,4=FAILED)")
        break

# 等心跳确认
for _ in range(20):
    msg = m.recv_match(type="HEARTBEAT", blocking=True, timeout=0.3)
    if msg:
        hb = msg
        print(f"   HB: cm={hb.custom_mode} base=0x{hb.base_mode:02x} armed={'Y' if hb.base_mode & 0x80 else 'N'} st={hb.system_status}")
        if hb.custom_mode == 0: break

# 看 STATUSTEXT (飞控可能发了拒绝原因)
print("==> 读 3s 内的 STATUSTEXT (飞控自描述)")
t0 = time.time()
while time.time() - t0 < 3.0:
    msg = m.recv_match(blocking=True, timeout=0.3)
    if msg is None: continue
    if msg.get_type() == "STATUSTEXT":
        print(f"   [{msg.severity}] {msg.text}")

# 再来一次,边喂 throttle 中位边看模式
print("==> 持续 throttle=1500 喂 2s 再切")
t0 = time.time()
while time.time() - t0 < 2.0:
    chans = [65535]*8
    chans[0] = 1500
    chans[2] = 1500
    m.mav.rc_channels_override_send(m.target_system, m.target_component, *chans)
    time.sleep(0.1)

# 这次试 set_mode_send 用 custom_mode 字段
print("==> set_mode_send(base_mode=0x81, custom_mode=0) ← 保留 ARMED")
m.mav.set_mode_send(m.target_system, 0x81, 0)
time.sleep(0.5)
for _ in range(15):
    msg = m.recv_match(type="HEARTBEAT", blocking=True, timeout=0.3)
    if msg:
        hb = msg
        if hb.custom_mode == 0:
            print(f"   ✓ MANUAL! base=0x{hb.base_mode:02x}")
            break

# 实测 throttle 1300 全速看 SERVO
ch_raw=[None]*8; servo_raw=[None]*8
print("==> 4s throttle=1300 (全速前进)")
print("    t   CH1  CH3    SERVO7 SERVO8   cm armed")
ts = time.time(); last_send=0; last_p=0
while time.time()-ts < 4.0:
    now=time.time()
    if now-last_send >= 0.1:
        chans=[65535]*8; chans[0]=1500; chans[2]=1300
        m.mav.rc_channels_override_send(m.target_system,m.target_component,*chans)
        last_send=now
    msg = m.recv_match(blocking=True, timeout=0.05)
    if msg:
        t=msg.get_type()
        if t=="RC_CHANNELS":
            for i in range(1,9): ch_raw[i-1]=getattr(msg,f"chan{i}_raw",None)
        elif t=="SERVO_OUTPUT_RAW":
            for i in range(1,9): servo_raw[i-1]=getattr(msg,f"servo{i}_raw",None)
        elif t=="HEARTBEAT": hb=msg
        elif t=="STATUSTEXT": print(f"   [STX] {msg.text}")
    if now-last_p >= 0.4:
        last_p=now
        print(f"  {now-ts:4.1f} {ch_raw[0]} {ch_raw[2]}    {servo_raw[6]}   {servo_raw[7]}    cm={hb.custom_mode} armed={'Y' if hb.base_mode & 0x80 else 'N'}")

# release
m.mav.rc_channels_override_send(m.target_system, m.target_component, 0,0,0,0,0,0,0,0)
print("done")
