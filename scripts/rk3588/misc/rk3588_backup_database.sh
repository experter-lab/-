#!/usr/bin/env bash
# 数据库自动备份脚本

DB_PATH="/mnt/sdcard/medicine_robot_data/delivery.db"
BACKUP_DIR="/mnt/sdcard/medicine_robot_data/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/delivery_${DATE}.db"

echo "=== 数据库备份 ==="
echo "时间: $(date)"
echo "源文件: ${DB_PATH}"
echo "备份到: ${BACKUP_FILE}"

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

# 检查数据库文件是否存在
if [ ! -f "${DB_PATH}" ]; then
    echo "错误: 数据库文件不存在"
    exit 1
fi

# 备份数据库
cp "${DB_PATH}" "${BACKUP_FILE}"

if [ $? -eq 0 ]; then
    echo "? 备份成功"
    
    # 显示备份文件大小
    SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "备份大小: ${SIZE}"
    
    # 清理 30 天前的旧备份
    find "${BACKUP_DIR}" -name "delivery_*.db" -mtime +30 -delete
    echo "? 已清理 30 天前的旧备份"
    
    # 显示当前备份数量
    COUNT=$(ls -1 "${BACKUP_DIR}"/delivery_*.db 2>/dev/null | wc -l)
    echo "当前备份数量: ${COUNT}"
else
    echo "? 备份失败"
    exit 1
fi
