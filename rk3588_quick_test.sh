#!/usr/bin/env bash
# RK3588 快速健康检查

echo "=== RK3588 快速健康检查 ==="
echo "时间: $(date)"
echo ""

FAILED=0

# 测试 1: Web Dashboard
echo -n "[1/8] Web Dashboard... "
if curl -f -s http://127.0.0.1:8085/api/health > /dev/null 2>&1; then
    echo "? PASS"
else
    echo "? FAIL"
    FAILED=$((FAILED + 1))
fi

# 测试 2: ROS2 工作空间
echo -n "[2/8] ROS2 工作空间... "
if [ -d /mnt/sdcard/medicine_robot_ws/install ]; then
    echo "? PASS"
else
    echo "? FAIL"
    FAILED=$((FAILED + 1))
fi

# 测试 3: 底盘串口
echo -n "[3/8] 底盘串口 /dev/ttyS9... "
if [ -e /dev/ttyS9 ]; then
    echo "? PASS"
else
    echo "? FAIL"
    FAILED=$((FAILED + 1))
fi

# 测试 4: 摄像头
echo -n "[4/8] 摄像头 /dev/video21... "
if [ -e /dev/video21 ]; then
    echo "? PASS"
else
    echo "? FAIL"
    FAILED=$((FAILED + 1))
fi

# 测试 5: 磁盘空间
echo -n "[5/8] 磁盘空间... "
DISK_USED=$(df /mnt/sdcard 2>/dev/null | tail -1 | awk '{print $5}' | sed 's/%//')
if [ -n "$DISK_USED" ] && [ "$DISK_USED" -lt 90 ]; then
    echo "? PASS (使用 ${DISK_USED}%)"
else
    echo "? FAIL"
    FAILED=$((FAILED + 1))
fi

# 测试 6: ROS2 节点
echo -n "[6/8] ROS2 节点运行... "
source /opt/ros/humble/setup.bash 2>/dev/null
source /mnt/sdcard/medicine_robot_ws/install/setup.bash 2>/dev/null
if ros2 node list 2>/dev/null | grep -q medicine; then
    echo "? PASS"
else
    echo "? FAIL"
    FAILED=$((FAILED + 1))
fi

# 测试 7: 核心话题
echo -n "[7/8] ROS2 核心话题... "
if ros2 topic list 2>/dev/null | grep -q /medicine/delivery_state; then
    echo "? PASS"
else
    echo "? FAIL"
    FAILED=$((FAILED + 1))
fi

# 测试 8: 系统负载
echo -n "[8/8] 系统负载... "
LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
echo "? PASS (负载: $LOAD)"

echo ""
echo "================================"
if [ "$FAILED" -eq 0 ]; then
    echo "结果: ? 所有测试通过"
    exit 0
else
    echo "结果: ? 失败 $FAILED 个测试"
    exit 1
fi
