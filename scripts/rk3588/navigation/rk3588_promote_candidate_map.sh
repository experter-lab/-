#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

MAP_DIR="/mnt/sdcard/medicine_robot_data/maps"
POSE_FILE="/mnt/sdcard/medicine_robot_data/config/carto_initial_pose.json"
ORIGIN_POSE_SCRIPT="/mnt/sdcard/rk3588_write_origin_initial_pose.sh"
STAMP="$(date +%Y%m%d_%H%M%S)"
NAME="${1:-}"
MAP_RESOLUTION="${MAP_RESOLUTION:-0.03}"
CREATE_ORIGIN_INITIAL_POSE="${CREATE_ORIGIN_INITIAL_POSE:-1}"

if [[ -z "$NAME" ]]; then
  echo "[promote-map] ERROR: usage: /mnt/sdcard/rk3588_promote_candidate_map.sh rk3588_carto_candidate_YYYYMMDD_HHMMSS"
  exit 2
fi

NAME="${NAME##*/}"
NAME="${NAME%.pbstream}"

if [[ "$NAME" != rk3588_carto_candidate_* ]]; then
  echo "[promote-map] ERROR: candidate name must start with rk3588_carto_candidate_"
  exit 2
fi

CANDIDATE_PB="$MAP_DIR/${NAME}.pbstream"
for path in "$CANDIDATE_PB" "$MAP_DIR/${NAME}.yaml" "$MAP_DIR/${NAME}.pgm"; do
  if [[ ! -s "$path" ]]; then
    echo "[promote-map] ERROR: missing or empty candidate file: $path"
    exit 1
  fi
done

echo "[promote-map] applying safe stop before map switch"
/mnt/sdcard/rk3588_safe_stop.sh || true
/mnt/sdcard/rk3588_check_brake_status.sh

echo "[promote-map] stopping localization/navigation/mapping runtime"
/mnt/sdcard/rk3588_clean_nav_runtime.sh

echo "[promote-map] backing up current latest maps"
for ext in pbstream yaml pgm; do
  if [[ -f "$MAP_DIR/rk3588_carto_latest.${ext}" ]]; then
    cp "$MAP_DIR/rk3588_carto_latest.${ext}" \
      "$MAP_DIR/rk3588_carto_latest.${ext}.before_candidate_${STAMP}"
  fi
done
for ext in yaml pgm; do
  if [[ -f "$MAP_DIR/rk3588_carto_latest_static.${ext}" ]]; then
    cp "$MAP_DIR/rk3588_carto_latest_static.${ext}" \
      "$MAP_DIR/rk3588_carto_latest_static.${ext}.before_candidate_${STAMP}"
  fi
done

echo "[promote-map] promoting candidate pbstream to rk3588_carto_latest.pbstream"
cp "$CANDIDATE_PB" "$MAP_DIR/rk3588_carto_latest.pbstream"
echo "[promote-map] export resolution: ${MAP_RESOLUTION} m/cell"

echo "[promote-map] exporting latest yaml/pgm from promoted pbstream"
/opt/ros/humble/lib/cartographer_ros/cartographer_pbstream_to_ros_map \
  -pbstream_filename="$MAP_DIR/rk3588_carto_latest.pbstream" \
  -map_filestem="$MAP_DIR/rk3588_carto_latest" \
  -resolution="$MAP_RESOLUTION"

echo "[promote-map] exporting latest_static yaml/pgm from promoted pbstream"
/opt/ros/humble/lib/cartographer_ros/cartographer_pbstream_to_ros_map \
  -pbstream_filename="$MAP_DIR/rk3588_carto_latest.pbstream" \
  -map_filestem="$MAP_DIR/rk3588_carto_latest_static" \
  -resolution="$MAP_RESOLUTION"

if [[ -f "$POSE_FILE" ]]; then
  echo "[promote-map] backing up and removing old initial pose"
  cp "$POSE_FILE" "${POSE_FILE}.before_new_map_${STAMP}"
  rm -f "$POSE_FILE"
fi

if [[ "$CREATE_ORIGIN_INITIAL_POSE" = "1" ]]; then
  echo "[promote-map] writing fixed-origin initial pose for latest map"
  if [[ -x "$ORIGIN_POSE_SCRIPT" ]]; then
    "$ORIGIN_POSE_SCRIPT" \
      "$MAP_DIR/rk3588_carto_latest.pbstream" \
      "$MAP_DIR/rk3588_carto_latest_static.yaml" \
      "$POSE_FILE"
  else
    echo "[promote-map] WARN: origin pose script is missing or not executable: $ORIGIN_POSE_SCRIPT"
    echo "[promote-map] WARN: run it manually after deployment if this map was built from the fixed physical start."
  fi
else
  echo "[promote-map] fixed-origin initial pose creation disabled"
fi

echo "[promote-map] promoted hashes:"
sha256sum \
  "$MAP_DIR/rk3588_carto_latest.pbstream" \
  "$MAP_DIR/rk3588_carto_latest.yaml" \
  "$MAP_DIR/rk3588_carto_latest.pgm" \
  "$MAP_DIR/rk3588_carto_latest_static.yaml" \
  "$MAP_DIR/rk3588_carto_latest_static.pgm"

echo "[promote-map] RESULT OK: candidate promoted to latest."
echo "[promote-map] Next: start localization-only and create/verify a new initial pose for this new map."
