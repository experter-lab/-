#!/usr/bin/env bash
# 让 Nav2 global_costmap.static_layer 改用 /map (carto 实时) 而不是 /map_static (旧 PGM)
set -euo pipefail
YAML=/mnt/sdcard/medicine_robot_data/config/rk3588_nav2_params.yaml
BAK="${YAML}.bak.$(date +%Y%m%d_%H%M%S)"
cp "$YAML" "$BAK"
echo "==> 备份: $BAK"

sed -i 's|map_topic: /map_static|map_topic: /map|' "$YAML"

echo
echo "==> 改后:"
grep -nE 'map_topic|map_subscribe_transient' "$YAML"
