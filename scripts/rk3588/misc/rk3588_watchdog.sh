#!/usr/bin/env bash
# RK3588 监控告警守护进程
# 功能：监控CPU温度、磁盘、内存、关键服务、ROS2节点
# 用法：
#   bash rk3588_watchdog.sh        # 单次检查
#   bash rk3588_watchdog.sh --daemon  # 后台守护模式（每30秒检查）
#   bash rk3588_watchdog.sh --json   # JSON输出（用于Web Dashboard）

set -eo pipefail

# ============ 阈值配置 ============
CPU_TEMP_WARN=70           # CPU温度警告阈值 (°C)
CPU_TEMP_CRIT=80           # CPU温度严重阈值 (°C)
DISK_WARN=80               # 磁盘使用警告 (%)
DISK_CRIT=90               # 磁盘使用严重 (%)
MEM_WARN=85                # 内存使用警告 (%)
MEM_CRIT=95                # 内存使用严重 (%)
LOAD_WARN=4.0              # 负载警告
CHECK_INTERVAL=30          # 守护模式检查间隔 (秒)

# ============ 路径 ============
ALERT_LOG="/mnt/sdcard/medicine_robot_data/logs/watchdog_alerts.log"
STATUS_FILE="/tmp/rk3588_watchdog_status.json"
HISTORY_FILE="/tmp/rk3588_watchdog_history.log"

mkdir -p "$(dirname "$ALERT_LOG")"

# ============ 工具函数 ============
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

log_alert() {
    local level="$1"
    local item="$2"
    local message="$3"
    local ts
    ts=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$ts] [$level] $item: $message" >> "$ALERT_LOG"
    echo "[$ts] [$level] $item: $message" >> "$HISTORY_FILE"
}

# ============ 检查项 ============

check_cpu_temp() {
    local temp_milli temp status msg
    if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
        temp_milli=$(cat /sys/class/thermal/thermal_zone0/temp)
        temp=$((temp_milli / 1000))
    else
        echo "CPU_TEMP|UNKNOWN|N/A|温度传感器不可用"
        return
    fi

    if [ "$temp" -ge "$CPU_TEMP_CRIT" ]; then
        status="CRIT"
        msg="${temp}°C 超过严重阈值${CPU_TEMP_CRIT}°C"
        log_alert "CRIT" "CPU温度" "$msg"
    elif [ "$temp" -ge "$CPU_TEMP_WARN" ]; then
        status="WARN"
        msg="${temp}°C 超过警告阈值${CPU_TEMP_WARN}°C"
        log_alert "WARN" "CPU温度" "$msg"
    else
        status="OK"
        msg="${temp}°C 正常"
    fi
    echo "CPU_TEMP|$status|$temp|$msg"
}

check_disk() {
    local mount="$1"
    local usage status msg
    if ! df "$mount" &>/dev/null; then
        echo "DISK_${mount}|UNKNOWN|N/A|挂载点不存在"
        return
    fi
    usage=$(df "$mount" | tail -1 | awk '{print $5}' | sed 's/%//')

    if [ "$usage" -ge "$DISK_CRIT" ]; then
        status="CRIT"
        msg="${mount} 使用率 ${usage}% 超过严重阈值"
        log_alert "CRIT" "磁盘" "$msg"
    elif [ "$usage" -ge "$DISK_WARN" ]; then
        status="WARN"
        msg="${mount} 使用率 ${usage}% 超过警告阈值"
        log_alert "WARN" "磁盘" "$msg"
    else
        status="OK"
        msg="${mount} 使用率 ${usage}% 正常"
    fi
    echo "DISK_${mount}|$status|$usage|$msg"
}

check_memory() {
    local total used usage status msg
    total=$(free | awk '/^Mem:/ {print $2}')
    used=$(free | awk '/^Mem:/ {print $3}')
    usage=$((used * 100 / total))

    if [ "$usage" -ge "$MEM_CRIT" ]; then
        status="CRIT"
        msg="内存使用率 ${usage}% 超过严重阈值"
        log_alert "CRIT" "内存" "$msg"
    elif [ "$usage" -ge "$MEM_WARN" ]; then
        status="WARN"
        msg="内存使用率 ${usage}% 超过警告阈值"
        log_alert "WARN" "内存" "$msg"
    else
        status="OK"
        msg="内存使用率 ${usage}% 正常"
    fi
    echo "MEMORY|$status|$usage|$msg"
}

check_load() {
    local load1 status msg
    load1=$(awk '{print $1}' /proc/loadavg)
    # 用bc或awk比较浮点数
    if awk -v a="$load1" -v b="$LOAD_WARN" 'BEGIN{exit !(a>=b)}'; then
        status="WARN"
        msg="1分钟负载 ${load1} 偏高"
        log_alert "WARN" "系统负载" "$msg"
    else
        status="OK"
        msg="1分钟负载 ${load1} 正常"
    fi
    echo "LOAD|$status|$load1|$msg"
}

check_service_port() {
    local name="$1"
    local port="$2"
    if netstat -tln 2>/dev/null | grep -qE ":$port[[:space:]]"; then
        echo "${name}|OK|$port|端口监听正常"
    else
        echo "${name}|CRIT|$port|端口未监听"
        log_alert "CRIT" "$name" "端口 $port 未监听"
    fi
}

check_web_dashboard() {
    if curl -fs --max-time 3 http://127.0.0.1:8085/api/health > /dev/null 2>&1; then
        echo "WEB_DASHBOARD|OK|8085|健康检查通过"
    else
        echo "WEB_DASHBOARD|CRIT|8085|健康检查失败"
        log_alert "CRIT" "Web Dashboard" "健康检查失败 (http://127.0.0.1:8085/api/health)"
    fi
}

check_ros_nodes() {
    local expected=("medicine_task_manager" "medicine_web_dashboard")
    local missing=()
    local node_list

    # ROS2 node list 需要先source
    if ! command -v ros2 &>/dev/null; then
        source /opt/ros/humble/setup.bash 2>/dev/null || true
        source /mnt/sdcard/medicine_robot_ws/install/setup.bash 2>/dev/null || true
    fi

    node_list=$(timeout 5 ros2 node list 2>/dev/null || echo "")

    for node in "${expected[@]}"; do
        if ! echo "$node_list" | grep -q "$node"; then
            missing+=("$node")
        fi
    done

    if [ ${#missing[@]} -eq 0 ]; then
        echo "ROS_NODES|OK|${#expected[@]}|全部 ${#expected[@]} 个核心节点运行正常"
    else
        echo "ROS_NODES|CRIT|${#missing[@]}|缺失节点: ${missing[*]}"
        log_alert "CRIT" "ROS2节点" "缺失节点: ${missing[*]}"
    fi
}

check_database() {
    local db_file="/mnt/sdcard/medicine_robot_data/delivery.db"
    if [ -f "$db_file" ]; then
        local size_kb
        size_kb=$(du -k "$db_file" | cut -f1)
        echo "DATABASE|OK|${size_kb}KB|数据库文件存在"
    else
        echo "DATABASE|CRIT|0|数据库文件不存在"
        log_alert "CRIT" "数据库" "delivery.db 文件不存在"
    fi
}

# ============ 输出格式 ============

run_all_checks() {
    check_cpu_temp
    check_disk "/"
    check_disk "/mnt/sdcard"
    check_memory
    check_load
    check_service_port "SSH" "22"
    check_service_port "NoMachine" "4000"
    check_web_dashboard
    check_database
    check_ros_nodes
}

print_text() {
    local checks
    checks=$(run_all_checks)
    local total=0 ok=0 warn=0 crit=0

    echo "========================================"
    echo "  RK3588 系统监控报告"
    echo "  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "========================================"

    while IFS='|' read -r name status value msg; do
        total=$((total + 1))
        case "$status" in
            OK)   echo -e "  ${GREEN}✓${NC} $name: $msg"; ok=$((ok + 1)) ;;
            WARN) echo -e "  ${YELLOW}⚠${NC} $name: $msg"; warn=$((warn + 1)) ;;
            CRIT) echo -e "  ${RED}✗${NC} $name: $msg"; crit=$((crit + 1)) ;;
            *)    echo -e "  ? $name: $msg" ;;
        esac
    done <<< "$checks"

    echo "========================================"
    echo "  总计: $total | OK: $ok | 警告: $warn | 严重: $crit"
    echo "========================================"

    if [ "$crit" -gt 0 ]; then
        return 2
    elif [ "$warn" -gt 0 ]; then
        return 1
    fi
    return 0
}

print_json() {
    local checks
    checks=$(run_all_checks)
    local first=1
    echo "{"
    echo "  \"timestamp\": \"$(date -Iseconds)\","
    echo "  \"hostname\": \"$(hostname)\","
    echo "  \"checks\": ["
    while IFS='|' read -r name status value msg; do
        [ $first -eq 0 ] && echo ","
        first=0
        printf '    {"name": "%s", "status": "%s", "value": "%s", "message": "%s"}' \
            "$name" "$status" "$value" "$msg"
    done <<< "$checks"
    echo ""
    echo "  ]"
    echo "}"
}

# ============ 主流程 ============

main() {
    case "${1:-}" in
        --json)
            print_json | tee "$STATUS_FILE"
            ;;
        --daemon)
            echo "进入守护模式，每 ${CHECK_INTERVAL} 秒检查一次"
            while true; do
                print_json > "$STATUS_FILE" 2>/dev/null || true
                sleep "$CHECK_INTERVAL"
            done
            ;;
        --alerts)
            echo "=== 最近告警 (最后20条) ==="
            tail -20 "$ALERT_LOG" 2>/dev/null || echo "无告警记录"
            ;;
        *)
            print_text
            ;;
    esac
}

main "$@"
