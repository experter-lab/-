#!/usr/bin/env bash
# RK3588 智能送药机器人统一控制脚本
# 版本: 1.0.0
# 日期: 2026-05-31

set -e

SCRIPT_DIR="/mnt/sdcard"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_banner() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  RK3588 送药机器人控制台 v1.0${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

show_menu() {
    echo "请选择操作："
    echo ""
    echo -e "${GREEN}[系统管理]${NC}"
    echo "  1. 启动完整系统"
    echo "  2. 停止所有服务"
    echo "  3. 重启 Web Dashboard"
    echo "  4. 系统健康检查"
    echo ""
    echo -e "${GREEN}[导航定位]${NC}"
    echo "  5. 启动定位栈（雷达+AMCL）"
    echo "  6. 启动导航栈（Nav2）"
    echo "  7. 检查定位状态"
    echo "  8. 检查 Nav2 状态"
    echo ""
    echo -e "${GREEN}[底盘控制]${NC}"
    echo "  9. 底盘心跳验证"
    echo " 10. 底盘安全测试"
    echo ""
    echo -e "${GREEN}[运维工具]${NC}"
    echo " 11. 采集系统日志"
    echo " 12. 备份数据库"
    echo " 13. 备份资产文件"
    echo " 14. 查看磁盘空间"
    echo ""
    echo -e "${GREEN}[配置管理]${NC}"
    echo " 15. 切换视觉配置"
    echo " 16. 查看当前配置"
    echo ""
    echo "  0. 退出"
    echo ""
    echo -n "请输入选项 [0-16]: "
}

start_full_system() {
    echo -e "${YELLOW}启动完整系统...${NC}"

    # 检查是否已经运行
    if pgrep -f "web_dashboard_node" > /dev/null; then
        echo -e "${YELLOW}系统已在运行中${NC}"
        return
    fi

    # 启动定位栈
    if [ -f "$SCRIPT_DIR/rk3588_start_localization_stack.sh" ]; then
        bash "$SCRIPT_DIR/rk3588_start_localization_stack.sh"
        sleep 5
    fi

    # 启动 Web Dashboard
    if [ -f "$SCRIPT_DIR/rk3588_delivery_webctl.sh" ]; then
        bash "$SCRIPT_DIR/rk3588_delivery_webctl.sh" start
    fi

    echo -e "${GREEN}✓ 系统启动完成${NC}"
    echo "访问地址: http://192.168.31.125:8085"
}

stop_all_services() {
    echo -e "${YELLOW}停止所有服务...${NC}"

    # 停止 Web Dashboard
    if [ -f "$SCRIPT_DIR/rk3588_delivery_webctl.sh" ]; then
        bash "$SCRIPT_DIR/rk3588_delivery_webctl.sh" stop
    fi

    # 停止 ROS2 节点
    pkill -f "ros2 launch" || true
    pkill -f "sllidar_node" || true
    pkill -f "amcl" || true
    pkill -f "map_server" || true

    echo -e "${GREEN}✓ 所有服务已停止${NC}"
}

restart_web_dashboard() {
    echo -e "${YELLOW}重启 Web Dashboard...${NC}"

    if [ -f "$SCRIPT_DIR/rk3588_delivery_webctl.sh" ]; then
        bash "$SCRIPT_DIR/rk3588_delivery_webctl.sh" restart
        echo -e "${GREEN}✓ Web Dashboard 已重启${NC}"
    else
        echo -e "${RED}✗ 脚本不存在${NC}"
    fi
}

health_check() {
    echo -e "${YELLOW}执行系统健康检查...${NC}"
    echo ""

    if [ -f "$SCRIPT_DIR/rk3588_quick_test.sh" ]; then
        bash "$SCRIPT_DIR/rk3588_quick_test.sh"
    else
        echo -e "${RED}✗ 健康检查脚本不存在${NC}"
    fi
}

start_localization() {
    echo -e "${YELLOW}启动定位栈...${NC}"

    if [ -f "$SCRIPT_DIR/rk3588_start_localization_stack.sh" ]; then
        bash "$SCRIPT_DIR/rk3588_start_localization_stack.sh"
        echo -e "${GREEN}✓ 定位栈已启动${NC}"
    else
        echo -e "${RED}✗ 脚本不存在${NC}"
    fi
}

start_nav2() {
    echo -e "${YELLOW}启动导航栈...${NC}"

    if [ -f "$SCRIPT_DIR/rk3588_start_nav2_stack.sh" ]; then
        bash "$SCRIPT_DIR/rk3588_start_nav2_stack.sh"
        echo -e "${GREEN}✓ 导航栈已启动${NC}"
    else
        echo -e "${RED}✗ 脚本不存在${NC}"
    fi
}

check_localization() {
    echo -e "${YELLOW}检查定位状态...${NC}"
    echo ""

    if [ -f "$SCRIPT_DIR/rk3588_check_localization_status.sh" ]; then
        bash "$SCRIPT_DIR/rk3588_check_localization_status.sh"
    else
        echo -e "${RED}✗ 检查脚本不存在${NC}"
    fi
}

check_nav2() {
    echo -e "${YELLOW}检查 Nav2 状态...${NC}"
    echo ""

    if [ -f "$SCRIPT_DIR/rk3588_check_nav2_status.sh" ]; then
        bash "$SCRIPT_DIR/rk3588_check_nav2_status.sh"
    else
        echo -e "${RED}✗ 检查脚本不存在${NC}"
    fi
}

verify_chassis_heartbeat() {
    echo -e "${YELLOW}验证底盘心跳...${NC}"
    echo ""

    if [ -f "$SCRIPT_DIR/rk3588_verify_ardupilot_heartbeat.sh" ]; then
        bash "$SCRIPT_DIR/rk3588_verify_ardupilot_heartbeat.sh" /dev/ttyS9 115200
    else
        echo -e "${RED}✗ 验证脚本不存在${NC}"
    fi
}

test_chassis_safety() {
    echo -e "${YELLOW}执行底盘安全测试...${NC}"
    echo ""

    if [ -f "$SCRIPT_DIR/rk3588_chassis_cmd_vel_safety_test.sh" ]; then
        bash "$SCRIPT_DIR/rk3588_chassis_cmd_vel_safety_test.sh" /dev/ttyS9 115200
    else
        echo -e "${RED}✗ 测试脚本不存在${NC}"
    fi
}

collect_logs() {
    echo -e "${YELLOW}采集系统日志...${NC}"

    if [ -f "$SCRIPT_DIR/rk3588_collect_logs.sh" ]; then
        bash "$SCRIPT_DIR/rk3588_collect_logs.sh"
        echo -e "${GREEN}✓ 日志已采集${NC}"
    else
        echo -e "${RED}✗ 采集脚本不存在${NC}"
    fi
}

backup_database() {
    echo -e "${YELLOW}备份数据库...${NC}"

    if [ -f "$SCRIPT_DIR/rk3588_backup_database.sh" ]; then
        bash "$SCRIPT_DIR/rk3588_backup_database.sh"
        echo -e "${GREEN}✓ 数据库已备份${NC}"
    else
        echo -e "${RED}✗ 备份脚本不存在${NC}"
    fi
}

backup_assets() {
    echo -e "${YELLOW}备份资产文件...${NC}"

    if [ -f "$SCRIPT_DIR/backup_rk3588_assets.sh" ]; then
        bash "$SCRIPT_DIR/backup_rk3588_assets.sh"
        echo -e "${GREEN}✓ 资产已备份${NC}"
    else
        echo -e "${RED}✗ 备份脚本不存在${NC}"
    fi
}

show_disk_space() {
    echo -e "${YELLOW}磁盘空间使用情况：${NC}"
    echo ""
    df -h / /mnt/sdcard 2>/dev/null || df -h /
    echo ""
}

switch_vision_config() {
    echo ""
    echo "可用的视觉配置："
    echo "  1. low_cpu     - 低功耗模式（生产推荐）"
    echo "  2. balanced    - 平衡模式"
    echo "  3. 720p        - 高精度模式"
    echo "  4. fast        - 快速模式"
    echo ""
    echo -n "请选择配置 [1-4]: "
    read -r choice

    case "$choice" in
        1) profile="low_cpu" ;;
        2) profile="balanced" ;;
        3) profile="720p" ;;
        4) profile="fast" ;;
        *) echo -e "${RED}无效选项${NC}"; return ;;
    esac

    if [ -f "$SCRIPT_DIR/rk3588_switch_vision_config.sh" ]; then
        bash "$SCRIPT_DIR/rk3588_switch_vision_config.sh" "$profile"
    else
        echo -e "${RED}✗ 切换脚本不存在${NC}"
    fi
}

show_current_config() {
    echo -e "${YELLOW}当前系统配置：${NC}"
    echo ""

    # 显示 Web Dashboard 状态
    if curl -f -s http://127.0.0.1:8085/api/health > /dev/null 2>&1; then
        echo -e "Web Dashboard: ${GREEN}运行中${NC} (http://192.168.31.125:8085)"
    else
        echo -e "Web Dashboard: ${RED}未运行${NC}"
    fi

    # 显示 ROS2 节点
    echo ""
    echo "ROS2 节点："
    ros2 node list 2>/dev/null | head -10 || echo "  无节点运行"

    echo ""
}

# 主程序
main() {
    if [ "$1" != "" ]; then
        # 命令行模式
        case "$1" in
            start) start_full_system ;;
            stop) stop_all_services ;;
            restart) restart_web_dashboard ;;
            health) health_check ;;
            status) show_current_config ;;
            *) echo "用法: $0 {start|stop|restart|health|status}" ;;
        esac
        exit 0
    fi

    # 交互模式
    while true; do
        clear
        show_banner
        show_menu
        read -r choice

        case "$choice" in
            1) start_full_system ;;
            2) stop_all_services ;;
            3) restart_web_dashboard ;;
            4) health_check ;;
            5) start_localization ;;
            6) start_nav2 ;;
            7) check_localization ;;
            8) check_nav2 ;;
            9) verify_chassis_heartbeat ;;
            10) test_chassis_safety ;;
            11) collect_logs ;;
            12) backup_database ;;
            13) backup_assets ;;
            14) show_disk_space ;;
            15) switch_vision_config ;;
            16) show_current_config ;;
            0) echo "退出"; exit 0 ;;
            *) echo -e "${RED}无效选项${NC}" ;;
        esac

        echo ""
        echo -n "按回车键继续..."
        read -r
    done
}

main "$@"
