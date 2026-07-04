#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

MAP_DIR="/mnt/sdcard/medicine_robot_data/maps"
NAME="${1:-rk3588_carto_latest}"
PBSTREAM="$MAP_DIR/${NAME}.pbstream"
YAMLPGM_BASE="$MAP_DIR/${NAME}"
STAMP="$(date +%Y%m%d_%H%M%S)"
MAP_RESOLUTION="${MAP_RESOLUTION:-0.03}"

mkdir -p "$MAP_DIR"

echo "[save] map dir: $MAP_DIR"
echo "[save] name:    $NAME"
echo "[save] resolution: ${MAP_RESOLUTION} m/cell"

for ext in pbstream yaml pgm; do
  if [[ -f "$MAP_DIR/${NAME}.${ext}" ]]; then
    cp "$MAP_DIR/${NAME}.${ext}" "$MAP_DIR/${NAME}.${ext}.bak_${STAMP}"
  fi
done

echo "[save] step 1/3: finish active Cartographer trajectories"
python3 /mnt/sdcard/medicine_robot_data/scripts/carto_finish_active_trajectories.py

echo "[save] step 2/3: write pbstream -> $PBSTREAM"
ros2 service call /write_state cartographer_ros_msgs/srv/WriteState \
  "{filename: '$PBSTREAM', include_unfinished_submaps: true}" || {
    echo "[save] ERROR: write_state failed"
    exit 1
}

echo "[save] step 3/3: export yaml/pgm from the same pbstream -> ${YAMLPGM_BASE}.{yaml,pgm}"
/opt/ros/humble/lib/cartographer_ros/cartographer_pbstream_to_ros_map \
  -pbstream_filename="$PBSTREAM" \
  -map_filestem="$YAMLPGM_BASE" \
  -resolution="$MAP_RESOLUTION" || {
    echo "[save] ERROR: pbstream_to_ros_map failed"
    exit 1
}

echo "[save] done. files:"
ls -lh "$PBSTREAM" "${YAMLPGM_BASE}.yaml" "${YAMLPGM_BASE}.pgm"
