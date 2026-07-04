#!/usr/bin/env bash
# 视觉配置快速切换工具

PROFILE="$1"
CONFIG_DIR="/mnt/sdcard/medicine_robot_data/config"

show_usage() {
    echo "用法: $0 {low_cpu|balanced|720p|fast|list}"
    echo ""
    echo "可用配置:"
    echo "  low_cpu   - 低功耗模式 (CPU 56%, 推荐生产环境)"
    echo "  balanced  - 平衡模式 (CPU 65%, 开发调试)"
    echo "  720p      - 高分辨率模式 (CPU 76%, 高精度需求)"
    echo "  fast      - 快速模式"
    echo "  list      - 列出所有配置文件"
}

list_configs() {
    echo "当前可用的视觉配置文件:"
    ls -lh /mnt/sdcard/rk3588_vision_*.yaml 2>/dev/null | awk '{print "  " $9}' | sed 's|/mnt/sdcard/||'
}

if [ -z "$PROFILE" ]; then
    show_usage
    exit 1
fi

case "$PROFILE" in
    low_cpu)
        CONFIG="rk3588_vision_unified_yolo_low_cpu.yaml"
        DESC="低功耗模式 (CPU 56%)"
        ;;
    balanced)
        CONFIG="rk3588_vision_unified_yolo_balanced.yaml"
        DESC="平衡模式 (CPU 65%)"
        ;;
    720p)
        CONFIG="rk3588_vision_unified_yolo_720p.yaml"
        DESC="高分辨率模式 (CPU 76%)"
        ;;
    fast)
        CONFIG="rk3588_vision_unified_yolo_fast.yaml"
        DESC="快速模式"
        ;;
    list)
        list_configs
        exit 0
        ;;
    *)
        echo "错误: 未知配置 '$PROFILE'"
        show_usage
        exit 1
        ;;
esac

SOURCE="/mnt/sdcard/$CONFIG"
TARGET="${CONFIG_DIR}/current_vision_config.yaml"

if [ ! -f "$SOURCE" ]; then
    echo "错误: 配置文件不存在: $SOURCE"
    exit 1
fi

mkdir -p "$CONFIG_DIR"
ln -sf "$SOURCE" "$TARGET"

echo "? 已切换到: $DESC"
echo "  配置文件: $CONFIG"
echo "  链接: $TARGET -> $SOURCE"
echo ""
echo "提示: 需要重启视觉节点才能生效"
