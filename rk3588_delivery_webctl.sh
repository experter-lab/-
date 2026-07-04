#!/usr/bin/env bash
set -euo pipefail
PORT=8085
LOG_FILE=/tmp/rk3588_delivery_batch_web_8085.log
START_SCRIPT=/mnt/sdcard/rk3588_start_delivery_batch_web_8085.sh
is_listening() {
  ss -ltn | grep -q ":${PORT} "
}
status() {
  if is_listening; then
    echo "RUNNING port=${PORT}"
    ss -ltnp | grep ":${PORT}" || true
    ps -ef | grep -E 'pc_delivery_demo.launch.py|web_dashboard_node|task_manager_node|voice_command_dispatcher_node' | grep -v grep || true
  else
    echo "STOPPED port=${PORT}"
  fi
}
start() {
  if is_listening; then
    status
    exit 0
  fi
  nohup "${START_SCRIPT}" > "${LOG_FILE}" 2>&1 < /dev/null &
  sleep 3
  status
  tail -n 20 "${LOG_FILE}" || true
}
collect_pids() {
  local pids=""
  local found=""
  for pattern in \
    "pc_delivery_demo.launch.py.*web_port:=${PORT}" \
    "medicine_web_dashboard/lib/medicine_web_dashboard/web_dashboard_node" \
    "medicine_task_manager/lib/medicine_task_manager/task_manager_node" \
    "medicine_voice_interaction/lib/medicine_voice_interaction/voice_command_dispatcher_node"; do
    found="$(pgrep -f "${pattern}" || true)"
    if [ -n "${found}" ]; then
      pids="${pids} ${found}"
    fi
  done
  echo "${pids}" | tr ' ' '\n' | grep -E '^[0-9]+$' | sort -u | tr '\n' ' '
}
stop() {
  local pids
  pids="$(collect_pids)"
  if [ -n "${pids// /}" ]; then
    kill ${pids} || true
    for _ in {1..10}; do
      if ! is_listening; then
        break
      fi
      sleep 0.5
    done
    if is_listening; then
      kill -9 ${pids} || true
      sleep 1
    fi
  fi
  status
}
restart() {
  stop
  start
}
log() {
  tail -n "${2:-60}" "${LOG_FILE}" || true
}
case "${1:-status}" in
  start) start ;;
  stop) stop ;;
  restart) restart ;;
  status) status ;;
  log) log "$@" ;;
  *) echo "Usage: $0 {start|stop|restart|status|log [lines]}"; exit 2 ;;
esac
