#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

MAP_DIR="/mnt/sdcard/medicine_robot_data/maps"
STAMP="$(date +%Y%m%d_%H%M%S)"
NAME="${1:-rk3588_carto_candidate_${STAMP}}"
MAP_RESOLUTION="${MAP_RESOLUTION:-0.03}"

if [[ "$NAME" != rk3588_carto_candidate_* ]]; then
  echo "[candidate-save] ERROR: candidate name must start with rk3588_carto_candidate_"
  exit 2
fi

echo "[candidate-save] applying safe stop before finishing the map"
/mnt/sdcard/rk3588_safe_stop.sh || true
/mnt/sdcard/rk3588_check_brake_status.sh

echo "[candidate-save] saving candidate map: $NAME"
echo "[candidate-save] resolution: ${MAP_RESOLUTION} m/cell"
MAP_RESOLUTION="$MAP_RESOLUTION" /mnt/sdcard/rk3588_save_carto_map.sh "$NAME"

echo "[candidate-save] hashes:"
sha256sum \
  "$MAP_DIR/${NAME}.pbstream" \
  "$MAP_DIR/${NAME}.yaml" \
  "$MAP_DIR/${NAME}.pgm"

echo "[candidate-save] candidate saved:"
ls -lh "$MAP_DIR/${NAME}.pbstream" "$MAP_DIR/${NAME}.yaml" "$MAP_DIR/${NAME}.pgm"
echo "[candidate-save] verify this candidate in RViz before promoting it to latest."
echo "[candidate-save] promote command:"
echo "[candidate-save]   /mnt/sdcard/rk3588_promote_candidate_map.sh $NAME"
