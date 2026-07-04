#!/usr/bin/env bash
set -eo pipefail

CONFIG_DIR="/mnt/sdcard/medicine_robot_data/config"
ENV_FILE="$CONFIG_DIR/lidar_mount.env"
VALUE="${1:-}"

case "$VALUE" in
  0|0.0|normal)
    YAW="0.0"
    LABEL="normal"
    ;;
  pi|3.14159|reverse|reversed|180)
    YAW="3.14159"
    LABEL="reversed-180"
    ;;
  *)
    echo "[lidar-yaw] ERROR: usage: /mnt/sdcard/rk3588_set_lidar_yaw.sh normal|reverse"
    exit 2
    ;;
esac

mkdir -p "$CONFIG_DIR"
cat > "$ENV_FILE" <<EOF
LIDAR_LASER_YAW=$YAW
EOF

echo "[lidar-yaw] set $LABEL yaw: $YAW"
echo "[lidar-yaw] config: $ENV_FILE"
echo "[lidar-yaw] restarting lidar processes; systemd service should bring them back"
pkill -f "rk3588_lidar_bringup.launch.py" || true
pkill -f "sllidar_node" || true
pkill -f "static_transform_publisher.*base_to_laser_tf" || true
sleep 5

echo "[lidar-yaw] current lidar processes:"
pgrep -af "rk3588_lidar_bringup.launch.py|sllidar_node|base_to_laser_tf" || true
