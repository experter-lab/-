#!/usr/bin/env python3
import time

import serial

port = "/dev/ttyS9"
baudrate = 115200
end_time = time.time() + 20.0
received = bytearray()

ser = serial.Serial(port, baudrate, timeout=0.1)
print(f"PY_SERIAL_OPEN {port} {baudrate}", flush=True)
while time.time() < end_time and len(received) < 256:
    chunk = ser.read(256)
    if chunk:
        received.extend(chunk)
        print("CHUNK", chunk.hex(" "), flush=True)
ser.close()
print(f"TOTAL_BYTES {len(received)}", flush=True)
if received:
    print(received.hex(" "), flush=True)
