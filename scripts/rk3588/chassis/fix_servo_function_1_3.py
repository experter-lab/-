#!/usr/bin/env python3
import sys
import time

from pymavlink import mavutil

PORT = "/dev/ttyS9"
BAUD = 921600
TARGET_SYSTEM = 1
TARGET_COMPONENT = 1

TARGETS = {
    "SERVO1_FUNCTION": 73.0,  # ThrottleLeft
    "SERVO3_FUNCTION": 74.0,  # ThrottleRight
    "SERVO7_FUNCTION": 0.0,
    "SERVO8_FUNCTION": 0.0,
}


def read_param(conn, name, timeout=2.0):
    conn.mav.param_request_read_send(
        TARGET_SYSTEM, TARGET_COMPONENT, name.encode("ascii"), -1
    )
    deadline = time.time() + timeout
    while time.time() < deadline:
        msg = conn.recv_match(type="PARAM_VALUE", blocking=True, timeout=0.25)
        if msg and msg.param_id.strip("\x00") == name:
            return msg.param_value
    return None


def set_param(conn, name, value, timeout=2.5):
    conn.mav.param_set_send(
        TARGET_SYSTEM,
        TARGET_COMPONENT,
        name.encode("ascii"),
        float(value),
        mavutil.mavlink.MAV_PARAM_TYPE_REAL32,
    )
    deadline = time.time() + timeout
    while time.time() < deadline:
        msg = conn.recv_match(type="PARAM_VALUE", blocking=True, timeout=0.25)
        if msg and msg.param_id.strip("\x00") == name:
            return msg.param_value
    return None


def main():
    print(f"connect {PORT}@{BAUD}")
    conn = mavutil.mavlink_connection(
        PORT, baud=BAUD, source_system=255, source_component=0
    )
    hb = conn.wait_heartbeat(timeout=8)
    if not hb:
        print("no heartbeat")
        return 1
    print(
        "heartbeat "
        f"src={hb.get_srcSystem()}/{hb.get_srcComponent()} "
        f"base_mode={hb.base_mode} custom_mode={hb.custom_mode}"
    )

    print("before:")
    for name in TARGETS:
        print(f"  {name}={read_param(conn, name)}")

    print("set:")
    ok = True
    for name, value in TARGETS.items():
        ack = set_param(conn, name, value)
        print(f"  {name} -> {value}, ack={ack}")
        ok = ok and ack == value

    print("after:")
    for name, value in TARGETS.items():
        actual = read_param(conn, name)
        print(f"  {name}={actual}")
        ok = ok and actual == value

    conn.close()
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
