#!/usr/bin/env bash
set -o pipefail

LOG=/tmp/chassis_wake_keepalive.log
echo "[$(date '+%F %T')] auto-wake disabled: chassis stays locked until an explicit shortcut confirmation" | tee -a "$LOG"
exit 0
