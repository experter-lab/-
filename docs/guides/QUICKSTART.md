# 🚀 5分钟快速开始指南

欢迎使用 RK3588 智能送药机器人系统！本指南将帮助你在 **5 分钟内** 启动系统并完成第一次配送测试。

---

## 📋 前置条件

在开始之前，请确认：

- ✅ RK3588 已上电并连接网络
- ✅ RK3588 IP地址：`192.168.31.125`
- ✅ 你的PC可以SSH连接到RK3588
- ✅ 用户名：`elf`，密码：`elf`

---

## ⚡ 3条命令启动系统

### 步骤 1：SSH 登录（10秒）

```bash
ssh elf@192.168.31.125
# 密码: elf
```

### 步骤 2：启动完整系统（30秒）

```bash
# 使用统一控制脚本启动
bash /mnt/sdcard/rk3588_control.sh start

# 或者使用快捷命令
/mnt/sdcard/rk3588_delivery_webctl.sh start
```

等待输出：
```
✓ 系统启动完成
访问地址: http://192.168.31.125:8085
```

### 步骤 3：健康检查（10秒）

```bash
bash /mnt/sdcard/rk3588_control.sh health
```

看到 `✓ 所有测试通过` 即表示系统正常。

---

## 🌐 访问 Web 界面（1分钟）

在浏览器中打开：

```
http://192.168.31.125:8085
```

你将看到：
- 📊 **配送批次** 页面 - 管理配送任务
- 🧪 **单任务调试** 页面 - 测试单个任务
- 📷 **药品识别** 页面 - 查看摄像头识别结果

---

## 🎯 测试配送流程（3分钟）

### 方式 1：使用演示批次（推荐）

1. **打开配送批次页面**
   - 点击顶部 "配送批次" 标签

2. **查看演示批次**
   - 系统已预置演示批次
   - 包含 A病房、B病房、C病房
   - 共6位患者，10项药品

3. **装药扫码**
   - 点击 "扫码装药" 按钮
   - 输入产品编码：`43043` 或 `C177248`
   - 输入追溯编号：`202011444`
   - 点击 "确认装药"

4. **开始配送**
   - 所有药品装药完成后
   - 点击 "开始配送" 按钮
   - 系统自动导航到第一个病房

5. **到站交付**
   - 等待导航完成（模拟模式约10秒）
   - 点击 "扫码取药" 按钮
   - 再次扫码确认
   - 点击 "确认交付"

6. **完成配送**
   - 系统自动进入下一病房
   - 重复交付流程
   - 全部完成后返回药房

### 方式 2：使用单任务调试

1. **打开单任务调试页面**
   - 点击顶部 "单任务调试" 标签

2. **选择患者**
   - 患者ID：`patient_001`
   - 患者姓名：`张三`
   - 病房：`A病房 (ward_a)`

3. **添加药品**
   - 药品名称：`降压药`
   - 产品编码：`C177248`
   - 追溯编号：`202011444`

4. **创建任务**
   - 点击 "创建送药任务" 按钮
   - 观察任务状态变化

5. **扫码确认**
   - 装药阶段：点击 "装药扫码确认"
   - 输入产品编码和追溯编号
   - 取药阶段：点击 "取药扫码确认"

6. **完成任务**
   - 任务状态变为 "已完成"
   - 可以创建下一个任务

---

## 🔍 验证系统功能

### 检查 ROS2 节点

```bash
ros2 node list
```

应该看到：
```
/medicine_task_manager
/medicine_web_dashboard
/medicine_voice_command_dispatcher
```

### 检查数据库

```bash
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('/mnt/sdcard/medicine_robot_data/delivery.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM scan_records")
print(f"扫码记录数: {cursor.fetchone()[0]}")
conn.close()
EOF
```

### 查看系统状态

```bash
bash /mnt/sdcard/rk3588_control.sh status
```

---

## 🎨 常用操作

### 重启 Web Dashboard

```bash
bash /mnt/sdcard/rk3588_control.sh restart
```

### 停止所有服务

```bash
bash /mnt/sdcard/rk3588_control.sh stop
```

### 查看磁盘空间

```bash
bash /mnt/sdcard/rk3588_control.sh
# 选择 14. 查看磁盘空间
```

### 备份数据库

```bash
bash /mnt/sdcard/rk3588_backup_database.sh
```

### 切换视觉配置

```bash
bash /mnt/sdcard/rk3588_control.sh
# 选择 15. 切换视觉配置
# 推荐：low_cpu（生产环境）
```

---

## ❓ 常见问题（FAQ）

### Q1: Web Dashboard 打不开？

**检查服务状态**：
```bash
curl http://127.0.0.1:8085/api/health
```

**重启服务**：
```bash
bash /mnt/sdcard/rk3588_delivery_webctl.sh restart
```

**查看日志**：
```bash
bash /mnt/sdcard/rk3588_delivery_webctl.sh log 50
```

---

### Q2: 雷达没有数据？

**检查设备**：
```bash
ls -l /dev/rplidar /dev/ttyUSB*
```

**检查话题**：
```bash
ros2 topic hz /scan
```

**重启定位栈**：
```bash
bash /mnt/sdcard/rk3588_start_localization_stack.sh
```

---

### Q3: 底盘不响应？

**检查安全状态**：
```bash
ros2 topic echo /medicine/chassis_status --once
```

**确认三级安全**：
- `emergency_stop`: 应为 `true`（默认急停）
- `control_authorized`: 应为 `false`（默认未授权）
- `hardware_estop_detected`: 应为 `false`

**授权控制**（仅在安全环境下）：
```bash
ros2 service call /chassis_bridge/authorize_control std_srvs/srv/SetBool "{data: true}"
```

---

### Q4: 数据库数据丢失？

**检查备份**：
```bash
ls -lh /mnt/sdcard/medicine_robot_data/backups/
```

**恢复备份**：
```bash
cp /mnt/sdcard/medicine_robot_data/backups/delivery_YYYYMMDD_HHMMSS.db \
   /mnt/sdcard/medicine_robot_data/delivery.db
```

**验证恢复**：
```bash
python3 /tmp/check_db.py
```

---

### Q5: 系统运行缓慢？

**检查资源使用**：
```bash
# CPU和内存
htop

# 磁盘空间
df -h /mnt/sdcard

# 进程数量
ps aux | grep python | wc -l
```

**清理日志**：
```bash
# 删除30天前的日志
find ~/.ros/log -mtime +30 -delete
```

---

## 📚 下一步学习

### 深入了解系统

1. **阅读完整文档**
   - `RK3588_ELF2_智能送药小车_项目进展与后续开发计划.md`
   - `DATABASE_DEPLOYMENT_GUIDE.md`
   - `OPTIMIZATION_COMPLETION_REPORT.md`

2. **查看技术细节**
   - `memories/` 目录 - 技术记忆库
   - `configs/` 目录 - 配置文件说明

3. **学习运维工具**
   - 统一控制脚本：`rk3588_control.sh`
   - 健康检查：`rk3588_check_localization_status.sh`
   - 日志采集：`rk3588_collect_logs.sh`

### 进阶操作

1. **接入真实底盘**
   - 连接 AET-H743 Basic 到 `/dev/ttyS9`
   - 验证 MAVLink heartbeat
   - 测试 `/cmd_vel` 控制

2. **启动 Nav2 导航**
   - 启动导航栈：`rk3588_start_nav2_stack.sh`
   - 切换导航模式：`navigation_backend:=nav2`
   - 测试跨站点导航

3. **开发新功能**
   - 修改 ROS2 包
   - 重新编译：`colcon build`
   - 运行测试

---

## 🆘 获取帮助

### 查看系统日志

```bash
# ROS2 日志
ls ~/.ros/log/latest/

# Web Dashboard 日志
bash /mnt/sdcard/rk3588_delivery_webctl.sh log 100

# 系统日志
journalctl -xe
```

### 联系支持

- 📧 Email: support@example.com
- 📱 电话: 123-456-7890
- 💬 GitHub Issues: https://github.com/your-repo/issues

---

## ✅ 快速检查清单

启动系统前，确认：
- [ ] RK3588 已上电
- [ ] 网络连接正常
- [ ] SSH 可以登录
- [ ] 磁盘空间充足（>1GB）

启动系统后，验证：
- [ ] Web Dashboard 可访问
- [ ] ROS2 节点运行正常
- [ ] 数据库文件存在
- [ ] 健康检查通过

测试配送后，确认：
- [ ] 任务创建成功
- [ ] 扫码记录保存
- [ ] 状态流转正常
- [ ] 数据持久化

---

## 🎉 恭喜！

你已经成功启动了智能送药机器人系统！

**系统现在可以**：
- ✅ 管理配送批次
- ✅ 扫码装药确认
- ✅ 自动导航到病房
- ✅ 扫码取药确认
- ✅ 记录完整审计日志
- ✅ 自动备份数据

**下一步建议**：
1. 熟悉 Web 界面的各个功能
2. 尝试创建自己的配送批次
3. 了解系统的配置选项
4. 学习故障排查方法

祝你使用愉快！🚀

---

**文档版本**: 1.0  
**更新日期**: 2026-05-31  
**适用系统**: RK3588 智能送药机器人 v1.0
