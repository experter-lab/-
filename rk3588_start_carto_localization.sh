#!/usr/bin/env bash
# RK3588 Cartographer 纯激光定位启动脚本
# 用法: bash rk3588_start_carto_localization.sh [pbstream_path]
# 不用 set -u: ROS setup.bash 会引用未绑定变量
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

PBSTREAM="${1:-/mnt/sdcard/medicine_robot_data/maps/rk3588_carto.pbstream}"
START_ODOM_FUSION="${START_ODOM_FUSION:-1}"

topic_pub_count() {
  ros2 topic info "$1" 2>/dev/null | awk '/Publisher count:/ {print $3; found=1} END {if (!found) print 0}'
}

node_exists() {
  ros2 node list 2>/dev/null | grep -Fxq "$1"
}

process_exists() {
  pgrep -f "$1" >/dev/null 2>&1
}

odom_fusion_running() {
  process_exists "rf2o_laser_odometry_node" &&
    process_exists "rk3588_guarded_odom.py" &&
    node_exists /ekf_filter_node &&
    [[ "$(topic_pub_count /rf2o/odom_raw)" = "1" ]] &&
    [[ "$(topic_pub_count /odom_rf2o_guarded)" = "1" ]] &&
    [[ "$(topic_pub_count /odom)" = "1" ]]
}

if [[ ! -f "$PBSTREAM" ]]; then
  echo "[carto-loc] ERROR: pbstream not found: $PBSTREAM"
  echo "[carto-loc] 先用 rk3588_start_carto_mapping.sh 建图，再用 rk3588_save_carto_map.sh 保存"
  exit 1
fi

LOG=/tmp/rk3588_carto_localization.log
echo "[carto-loc] pbstream: $PBSTREAM"
echo "[carto-loc] log file: $LOG"
echo "[carto-loc] WARN: 不要同时启动 AMCL（map->odom 会冲突）"
echo "[carto-loc] start_lidar=false; /scan 应由 rk3588_start_lidar.sh 单独提供"
if [[ "$START_ODOM_FUSION" = "0" ]]; then
  echo "[carto-loc] START_ODOM_FUSION=0; reusing existing /odom and odom->base_link"
elif odom_fusion_running; then
  echo "[carto-loc] odom fusion already running; reusing existing /odom and odom->base_link"
else
  echo "[carto-loc] ensuring odom fusion provides /odom and odom->base_link"
  /mnt/sdcard/rk3588_start_odom_fusion.sh
fi
exec ros2 launch medicine_robot_bringup rk3588_carto_localization.launch.py \
  pbstream:="$PBSTREAM" \
  start_lidar:=false 2>&1 | tee "$LOG"
