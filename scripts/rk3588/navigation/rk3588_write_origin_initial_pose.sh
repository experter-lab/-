#!/usr/bin/env bash
set -eo pipefail

PBSTREAM="${1:-/mnt/sdcard/medicine_robot_data/maps/rk3588_carto_latest.pbstream}"
MAP_YAML="${2:-/mnt/sdcard/medicine_robot_data/maps/rk3588_carto_latest_static.yaml}"
POSE_FILE="${3:-/mnt/sdcard/medicine_robot_data/config/carto_initial_pose.json}"

if [[ ! -s "$PBSTREAM" ]]; then
  echo "[origin-pose] ERROR: missing pbstream: $PBSTREAM"
  exit 1
fi
if [[ ! -s "$MAP_YAML" ]]; then
  echo "[origin-pose] ERROR: missing static map yaml: $MAP_YAML"
  exit 1
fi

mkdir -p "$(dirname "$POSE_FILE")"

python3 - "$PBSTREAM" "$MAP_YAML" "$POSE_FILE" <<'PY'
import hashlib
import json
import os
import sys
import time

pbstream, map_yaml, pose_file = sys.argv[1:4]

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

data = {
    "child_frame_id": "base_link",
    "frame_id": "map",
    "initial_pose_source": "fixed_mapping_origin",
    "map_yaml": map_yaml,
    "map_yaml_sha256": sha256_file(map_yaml),
    "pbstream": pbstream,
    "pbstream_sha256": sha256_file(pbstream),
    "qw": 1.0,
    "qx": 0.0,
    "qy": 0.0,
    "qz": 0.0,
    "saved_unix_time": time.time(),
    "x": 0.0,
    "y": 0.0,
    "yaw_deg": 0.0,
    "z": 0.0,
}

tmp = pose_file + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, sort_keys=True)
    f.write("\n")
os.replace(tmp, pose_file)
print(f"[origin-pose] wrote fixed origin pose: {pose_file}")
print(f"[origin-pose] pbstream_sha256: {data['pbstream_sha256']}")
print(f"[origin-pose] map_yaml_sha256: {data['map_yaml_sha256']}")
PY

cat "$POSE_FILE"
