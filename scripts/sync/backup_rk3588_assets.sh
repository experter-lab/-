#!/usr/bin/env bash
# RK3588 核心资产一键备份工具 (WSL/Linux 兼容版)

BOARD_IP="192.168.31.125"
BOARD_USER="elf"
BACKUP_DIR="/mnt/d/A1/backup"

echo "==================================================="
echo "       RK3588 核心资产一键备份与迁移工具 (Linux)"
echo "==================================================="
echo "目标开发板 IP: ${BOARD_IP}"
echo "登录用户名    : ${BOARD_USER}"
echo "本地备份目录  : ${BACKUP_DIR}"
echo "==================================================="

# 1. 检查网络连通性
echo "[*] 正在检测开发板网络连通性..."
if ! ping -c 2 "${BOARD_IP}" > /dev/null 2>&1; then
    echo "[ERROR] 无法连接到开发板 ${BOARD_IP}。"
    echo "[ERROR] 请确保开发板开机、联网，且 IP 正确。"
    exit 1
fi
echo "[OK] 开发板网络畅通！"

# 2. 创建本地备份目录
mkdir -p "${BACKUP_DIR}/maps"
mkdir -p "${BACKUP_DIR}/models"
mkdir -p "${BACKUP_DIR}/scripts"

echo ""
echo "==================================================="
echo "开始备份进程 (传输期间需要您输入板端的 SSH 登录密码)"
echo "==================================================="
echo ""

# 3. 备份语音离线授权
echo "[1/4] 正在拉取科大讯飞离线语音授权密钥 aikit.env..."
scp "${BOARD_USER}@${BOARD_IP}:~/.config/medicine_robot/aikit.env" "${BACKUP_DIR}/aikit.env"

# 4. 备份已建好的医院地图
echo "[2/4] 正在拉取板端扫好的 2D 栅格地图文件 (maps)..."
scp -r "${BOARD_USER}@${BOARD_IP}:/mnt/sdcard/medicine_robot_data/maps/*" "${BACKUP_DIR}/maps/"

# 5. 备份 NPU YOLO 离线模型
echo "[3/4] 正在拉取板端高精度 RKNN YOLOv8 神经网络模型..."
scp "${BOARD_USER}@${BOARD_IP}:/mnt/sdcard/medicine_robot_data/models/yolov8n_rk3588.rknn" "${BACKUP_DIR}/models/"

# 6. 备份定制的板端运维与一键启动脚本
echo "[4/4] 正在拉取板载一键自检与运维启动脚本 (*.sh)..."
scp "${BOARD_USER}@${BOARD_IP}:/mnt/sdcard/rk3588_*.sh" "${BACKUP_DIR}/scripts/"

echo "==================================================="
echo "                  备份任务全部结束！"
echo "==================================================="
echo "所有资产已成功保存至本地：${BACKUP_DIR}"
echo ""
