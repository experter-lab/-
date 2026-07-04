#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
if [ -f /mnt/sdcard/medicine_robot_ws/install/setup.bash ]; then
  source /mnt/sdcard/medicine_robot_ws/install/setup.bash
fi

OUT_DIR="${1:-/mnt/sdcard/medicine_robot_data/logs}"
STAMP="$(date +%Y%m%d_%H%M%S)"
CASE_DIR="${OUT_DIR}/rk3588_logs_${STAMP}"
mkdir -p "${CASE_DIR}"

run_capture() {
  local name="$1"
  shift
  echo "collect ${name}"
  { "$@"; } >"${CASE_DIR}/${name}.txt" 2>&1 || true
}

copy_if_exists() {
  local src="$1"
  local dst_name="$2"
  if [ -e "$src" ]; then
    cp -a "$src" "${CASE_DIR}/${dst_name}" || true
  fi
}

run_capture date date
run_capture uname uname -a
run_capture uptime uptime
run_capture disk df -h
run_capture memory free -h
run_capture ip_addr ip addr
run_capture rplidar_device bash -c 'ls -l /dev/rplidar /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || true'
run_capture ps_top bash -c 'ps -eo pid,ppid,pcpu,pmem,cmd --sort=-pcpu | head -80'
run_capture ros_nodes ros2 node list
run_capture ros_topics ros2 topic list -t
run_capture ros_scan_info ros2 topic info /scan
run_capture ros_odom_info ros2 topic info /odom
run_capture ros_map_info ros2 topic info /map
run_capture ros_amcl_pose_info ros2 topic info /amcl_pose
run_capture map_server_lifecycle ros2 lifecycle get /map_server
run_capture amcl_lifecycle ros2 lifecycle get /amcl
run_capture scan_once timeout 8s ros2 topic echo /scan --once
run_capture odom_once timeout 8s ros2 topic echo /odom --once
run_capture amcl_pose_once timeout 8s ros2 topic echo /amcl_pose --once
run_capture tf_map_odom timeout 6s ros2 run tf2_ros tf2_echo map odom
run_capture tf_odom_base timeout 6s ros2 run tf2_ros tf2_echo odom base_link
run_capture tf_base_laser timeout 6s ros2 run tf2_ros tf2_echo base_link laser

copy_if_exists /tmp/rk3588_lidar_bringup.log rk3588_lidar_bringup.log
copy_if_exists /tmp/rk3588_rf2o.log rk3588_rf2o.log
copy_if_exists /tmp/rk3588_map_server.log rk3588_map_server.log
copy_if_exists /tmp/rk3588_amcl.log rk3588_amcl.log
copy_if_exists /tmp/amcl.log amcl.log
copy_if_exists /mnt/sdcard/rk3588_start_localization_stack.sh rk3588_start_localization_stack.sh
copy_if_exists /mnt/sdcard/rk3588_start_map_server.sh rk3588_start_map_server.sh
copy_if_exists /mnt/sdcard/rk3588_start_amcl.sh rk3588_start_amcl.sh
copy_if_exists /mnt/sdcard/medicine_robot_data/config/rk3588_amcl_localization.yaml rk3588_amcl_localization.yaml
copy_if_exists /mnt/sdcard/medicine_robot_data/maps/a1_handheld_map_latest.yaml a1_handheld_map_latest.yaml

ARCHIVE="${CASE_DIR}.tar.gz"
tar czf "${ARCHIVE}" -C "${OUT_DIR}" "$(basename "${CASE_DIR}")"
echo "LOG_DIR=${CASE_DIR}"
echo "ARCHIVE=${ARCHIVE}"
