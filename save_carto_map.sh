#!/usr/bin/env bash
# 保存 Cartographer 建图结果: pbstream + pgm/yaml
set -eo pipefail
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

DATE=$(date +%Y%m%d_%H%M%S)
OUTDIR=/mnt/sdcard/medicine_robot_data/maps
mkdir -p "$OUTDIR"
PBSTREAM="$OUTDIR/rk3588_carto_${DATE}.pbstream"
PBSTREAM_LATEST="$OUTDIR/rk3588_carto_latest.pbstream"

echo "==> finishing trajectory 0..."
ros2 service call /finish_trajectory cartographer_ros_msgs/srv/FinishTrajectory "{trajectory_id: 0}" 2>&1 | head -3
sleep 2

echo "==> writing pbstream to $PBSTREAM..."
ros2 service call /write_state cartographer_ros_msgs/srv/WriteState "{filename: '$PBSTREAM', include_unfinished_submaps: true}" 2>&1 | head -3
sleep 3

if [[ -f "$PBSTREAM" ]]; then
    cp "$PBSTREAM" "$PBSTREAM_LATEST"
    echo "=> pbstream saved: $PBSTREAM ($(du -h "$PBSTREAM" | cut -f1))"
    echo "=> latest symlinked: $PBSTREAM_LATEST"
else
    echo "ERROR: pbstream not created at $PBSTREAM"
    exit 1
fi

echo
echo "==> also save pgm (via map_saver_cli)..."
PGM="$OUTDIR/rk3588_carto_${DATE}"
PGM_LATEST="$OUTDIR/rk3588_carto_latest"
timeout 10 ros2 run nav2_map_server map_saver_cli -f "$PGM" --ros-args -p map_subscribe_transient_local:=true 2>&1 | head -5 || echo "(pgm save timed out - ok, pbstream is primary)"
if [[ -f "${PGM}.pgm" ]]; then
    cp "${PGM}.pgm" "${PGM_LATEST}.pgm"
    cp "${PGM}.yaml" "${PGM_LATEST}.yaml"
    echo "=> pgm saved: ${PGM}.pgm (for backup, carto loc uses pbstream)"
fi

echo
echo "ls -la $OUTDIR:"
ls -la "$OUTDIR" | tail -10
echo
echo "==> DONE. pbstream = $PBSTREAM"
