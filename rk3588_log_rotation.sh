#!/usr/bin/env bash
# RK3588 日志轮转和清理脚本
# 功能：压缩旧日志、删除过期日志、限制总大小
# 用法：bash rk3588_log_rotation.sh [--dry-run]
# 建议 crontab：每天凌晨1点执行
#   0 1 * * * /mnt/sdcard/rk3588_log_rotation.sh >> /tmp/log_rotation.log 2>&1

set -eo pipefail

# ============ 配置 ============
ROS_LOG_DIR="$HOME/.ros/log"
TMP_LOG_PATTERN="/tmp/rk3588_*.log"
WEBCTL_LOG="/tmp/rk3588_delivery_webctl_boot.log"
DB_BACKUP_DIR="/mnt/sdcard/medicine_robot_data/backups"

# 保留策略
ROS_LOG_KEEP_DAYS=7        # ROS2日志：7天前的压缩
ROS_LOG_DELETE_DAYS=30     # ROS2日志：30天前的删除
ROS_LOG_MAX_COUNT=100      # ROS2日志：最多保留100个会话目录
TMP_LOG_MAX_SIZE_MB=50     # /tmp单个日志最大50MB（超过截断）
DB_BACKUP_KEEP_DAYS=30     # 数据库备份保留30天

DRY_RUN=0
if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN=1
    echo "[DRY-RUN MODE] 不会实际删除/压缩文件"
fi

# ============ 工具函数 ============
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

run_cmd() {
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "  [DRY-RUN] $*"
    else
        eval "$@"
    fi
}

# ============ 1. ROS2 日志轮转 ============
rotate_ros_logs() {
    log_info "=== ROS2 日志轮转 ==="

    if [ ! -d "$ROS_LOG_DIR" ]; then
        log_info "ROS日志目录不存在，跳过"
        return
    fi

    local before_size before_count
    before_size=$(du -sh "$ROS_LOG_DIR" 2>/dev/null | awk '{print $1}')
    before_count=$(find "$ROS_LOG_DIR" -maxdepth 1 -type d | wc -l)
    log_info "清理前：${before_size} / ${before_count} 个目录"

    # 1.1 压缩7天前未压缩的日志目录（保留原文件）
    local compressed=0
    while IFS= read -r dir; do
        [ -z "$dir" ] && continue
        local archive="${dir}.tar.gz"
        if [ ! -f "$archive" ]; then
            run_cmd "tar -czf '$archive' -C '$(dirname "$dir")' '$(basename "$dir")' 2>/dev/null"
            run_cmd "rm -rf '$dir'"
            compressed=$((compressed + 1))
        fi
    done < <(find "$ROS_LOG_DIR" -maxdepth 1 -type d -mtime +${ROS_LOG_KEEP_DAYS} 2>/dev/null | grep -v "^$ROS_LOG_DIR$" || true)
    log_info "压缩了 ${compressed} 个旧日志目录"

    # 1.2 删除30天前的压缩包
    local deleted=0
    while IFS= read -r file; do
        [ -z "$file" ] && continue
        run_cmd "rm -f '$file'"
        deleted=$((deleted + 1))
    done < <(find "$ROS_LOG_DIR" -maxdepth 1 -name "*.tar.gz" -mtime +${ROS_LOG_DELETE_DAYS} 2>/dev/null || true)
    log_info "删除了 ${deleted} 个过期压缩包"

    # 1.3 如果会话目录仍超过100个，删除最旧的
    local current_count
    current_count=$(find "$ROS_LOG_DIR" -maxdepth 1 -type d | wc -l)
    if [ "$current_count" -gt "$ROS_LOG_MAX_COUNT" ]; then
        local excess=$((current_count - ROS_LOG_MAX_COUNT))
        log_info "目录数 ${current_count} 超过上限 ${ROS_LOG_MAX_COUNT}，删除最旧的 ${excess} 个"
        # shellcheck disable=SC2012
        ls -1dt "$ROS_LOG_DIR"/*/ 2>/dev/null | tail -n "$excess" | while read -r d; do
            run_cmd "rm -rf '$d'"
        done
    fi

    local after_size after_count
    after_size=$(du -sh "$ROS_LOG_DIR" 2>/dev/null | awk '{print $1}')
    after_count=$(find "$ROS_LOG_DIR" -maxdepth 1 -type d | wc -l)
    log_info "清理后：${after_size} / ${after_count} 个目录"
}

# ============ 2. /tmp 日志大小限制 ============
truncate_tmp_logs() {
    log_info "=== /tmp 日志大小检查 ==="

    local max_bytes=$((TMP_LOG_MAX_SIZE_MB * 1024 * 1024))
    for f in $TMP_LOG_PATTERN; do
        [ ! -f "$f" ] && continue
        local size
        size=$(stat -c%s "$f" 2>/dev/null || echo 0)
        if [ "$size" -gt "$max_bytes" ]; then
            log_info "$f 超过 ${TMP_LOG_MAX_SIZE_MB}MB ($(du -h "$f" | cut -f1))，截断保留末尾"
            if [ "$DRY_RUN" -eq 0 ]; then
                # 保留最后10000行
                tail -n 10000 "$f" > "${f}.tmp" && mv "${f}.tmp" "$f"
            fi
        fi
    done
}

# ============ 3. 数据库备份清理 ============
clean_db_backups() {
    log_info "=== 数据库备份清理 ==="

    if [ ! -d "$DB_BACKUP_DIR" ]; then
        log_info "备份目录不存在，跳过"
        return
    fi

    local before_count
    before_count=$(find "$DB_BACKUP_DIR" -name "*.db" -type f | wc -l)

    local deleted=0
    while IFS= read -r file; do
        [ -z "$file" ] && continue
        run_cmd "rm -f '$file'"
        deleted=$((deleted + 1))
    done < <(find "$DB_BACKUP_DIR" -name "*.db" -type f -mtime +${DB_BACKUP_KEEP_DAYS} 2>/dev/null || true)

    local after_count
    after_count=$(find "$DB_BACKUP_DIR" -name "*.db" -type f | wc -l)
    log_info "数据库备份：删除 ${deleted} 个过期文件，当前 ${after_count} 个"
}

# ============ 4. 显示总览 ============
show_summary() {
    log_info "=== 磁盘使用总览 ==="
    df -h /mnt/sdcard / 2>/dev/null | head -3
    echo ""
    log_info "ROS2日志: $(du -sh "$ROS_LOG_DIR" 2>/dev/null | awk '{print $1}') ($(find "$ROS_LOG_DIR" -maxdepth 1 -type d | wc -l) 目录)"
    log_info "数据库备份: $(du -sh "$DB_BACKUP_DIR" 2>/dev/null | awk '{print $1}') ($(find "$DB_BACKUP_DIR" -name "*.db" -type f 2>/dev/null | wc -l) 文件)"
}

# ============ 主流程 ============
main() {
    log_info "========== RK3588 日志轮转开始 =========="
    rotate_ros_logs
    truncate_tmp_logs
    clean_db_backups
    show_summary
    log_info "========== 日志轮转完成 =========="
}

main "$@"
