#!/usr/bin/env python3
"""Quick test: open serial port, listen for MAVLink, report results."""
import sys
from pymavlink import mavutil

def cmd(port, baud):
    conn = mavutil.mavlink_connection(port, baud=baud, autoreconnect=False)
    print(f"OPENED {port} @ {baud}")
    i = 0
    while i < 100:
        msg = conn.recv_match(blocking=True, timeout=0.5)
        if msg is None:
            i += 1
            if i % 4 == 0:
                print(f"  idle {i*0.5:.0f}s ...")
            continue
        if msg.get_type() == "BAD_DATA":
            continue
        print(f"[{i*0.5:.1f}s] {msg.get_type()} sys={msg.get_srcSystem()} comp={msg.get_srcComponent()}")
        if msg.get_type() == "HEARTBEAT":
            print(f"  HEARTBEAT: type={msg.type} autopilot={msg.autopilot} base_mode={msg.base_mode} "
                  f"custom_mode={msg.custom_mode} system_status={msg.system_status} mavlink={msg.mavlink_version}")
        i += 1
        if i >= 100:
            break
    if i == 0:
        print("NO DATA within timeout")
    conn.close()
    print("DONE")

if __name__ == "__main__":
    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyS9"
    baud = int(sys.argv[2]) if len(sys.argv) > 2 else 921600
    cmd(port, baud)
