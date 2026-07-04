#!/usr/bin/env bash
set -eo pipefail

export TTS_BACKEND="${TTS_BACKEND:-ci1302_serial}"
export ENABLE_M2_BRIDGE="${ENABLE_M2_BRIDGE:-false}"
export CI1302_SERIAL_PORT="${CI1302_SERIAL_PORT:-/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0}"
export CI1302_BAUDRATE="${CI1302_BAUDRATE:-115200}"
export CI1302_OPEN_DELAY_SEC="${CI1302_OPEN_DELAY_SEC:-8.0}"

exec /mnt/sdcard/rk3588_start_m2_voice.sh
