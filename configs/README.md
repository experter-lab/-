# 📋 配置文件说明

本目录包含 RK3588 智能送药机器人的各种配置文件。本文档帮助你快速选择合适的配置。

---

## 🎯 视觉检测配置对比

### 配置文件列表

| 配置文件 | 使用场景 | CPU占用 | 帧率 | 识别延迟 | 推荐度 |
|---------|---------|---------|------|---------|--------|
| **rk3588_vision_unified_yolo_low_cpu.yaml** | **生产环境（推荐）** | 56% | 14fps | ~20ms | ⭐⭐⭐ |
| rk3588_vision_unified_yolo_balanced.yaml | 开发调试 | 65% | 20fps | ~18ms | ⭐⭐ |
| rk3588_vision_unified_yolo_720p.yaml | 高精度需求 | 76% | 15fps | ~24ms | ⭐⭐ |
| rk3588_vision_unified_yolo_fast.yaml | 快速响应 | 70% | 25fps | ~15ms | ⭐ |
| rk3588_vision_1280_low_load.yaml | 低负载模式 | 45% | 10fps | ~25ms | ⭐ |
| rk3588_vision_low_load.yaml | 极低负载 | 40% | 8fps | ~30ms | ⭐ |
| rk3588_vision_scan_boost.yaml | 扫码加速 | 60% | 18fps | ~17ms | ⭐⭐ |

### 详细说明

#### 1. low_cpu（生产环境推荐）⭐⭐⭐

**文件**: `rk3588_vision_unified_yolo_low_cpu.yaml`

**特点**:
- CPU占用最优化（56%）
- 稳定的帧率（14fps）
- 良好的识别精度
- 长时间运行不过热

**适用场景**:
- ✅ 生产环境24/7运行
- ✅ 需要长期稳定运行
- ✅ 对功耗有要求
- ✅ 温度敏感环境

**配置参数**:
```yaml
resolution: 640x480
format: MJPEG
fps: 15
yolo_enabled: true
yolo_confidence: 0.5
qr_recognition_period: 1.0
```

**切换命令**:
```bash
bash /mnt/sdcard/rk3588_switch_vision_config.sh low_cpu
```

---

#### 2. balanced（开发调试）⭐⭐

**文件**: `rk3588_vision_unified_yolo_balanced.yaml`

**特点**:
- 性能与功耗平衡
- 较高帧率（20fps）
- 适合开发测试

**适用场景**:
- ✅ 开发调试阶段
- ✅ 功能验证测试
- ✅ 性能评估

**配置参数**:
```yaml
resolution: 640x480
format: MJPEG
fps: 20
yolo_enabled: true
yolo_confidence: 0.45
qr_recognition_period: 0.8
```

**切换命令**:
```bash
bash /mnt/sdcard/rk3588_switch_vision_config.sh balanced
```

---

#### 3. 720p（高精度需求）⭐⭐

**文件**: `rk3588_vision_unified_yolo_720p.yaml`

**特点**:
- 高分辨率（1280x720）
- 更高的识别精度
- CPU占用较高（76%）

**适用场景**:
- ✅ 需要高精度识别
- ✅ 远距离扫码
- ✅ 小字体识别
- ❌ 不适合长时间运行

**配置参数**:
```yaml
resolution: 1280x720
format: MJPEG
fps: 15
yolo_enabled: true
yolo_confidence: 0.5
qr_recognition_period: 1.2
```

**切换命令**:
```bash
bash /mnt/sdcard/rk3588_switch_vision_config.sh 720p
```

---

#### 4. fast（快速响应）⭐

**文件**: `rk3588_vision_unified_yolo_fast.yaml`

**特点**:
- 最高帧率（25fps）
- 最低延迟（~15ms）
- CPU占用较高（70%）

**适用场景**:
- ✅ 需要快速响应
- ✅ 实时预览重要
- ✅ 短时间测试
- ❌ 不适合长时间运行

**配置参数**:
```yaml
resolution: 640x480
format: MJPEG
fps: 30
yolo_enabled: true
yolo_confidence: 0.4
qr_recognition_period: 0.5
```

**切换命令**:
```bash
bash /mnt/sdcard/rk3588_switch_vision_config.sh fast
```

---

## 🗺️ 导航配置

### Nav2 参数配置

**文件**: `rk3588_nav2_params.yaml`

**关键参数**:
```yaml
controller_server:
  controller_frequency: 5.0
  max_vel_x: 0.15  # 最大线速度 (m/s)
  max_vel_theta: 0.5  # 最大角速度 (rad/s)
  xy_goal_tolerance: 0.20  # 位置容差 (m)
  yaw_goal_tolerance: 0.30  # 角度容差 (rad)

planner_server:
  expected_planner_frequency: 1.0
  planner_patience: 5.0
```

**使用场景**:
- ✅ 真实 Nav2 导航
- ✅ 跨站点路径规划
- ✅ 动态避障

**启动命令**:
```bash
bash /mnt/sdcard/rk3588_start_nav2_stack.sh
```

---

### AMCL 定位配置

**文件**: `rk3588_amcl_localization.yaml`

**关键参数**:
```yaml
amcl:
  min_particles: 500
  max_particles: 2000
  update_min_d: 0.2  # 最小移动距离触发更新
  update_min_a: 0.5  # 最小旋转角度触发更新
```

**使用场景**:
- ✅ 基于地图的定位
- ✅ 粒子滤波定位
- ✅ 与 Nav2 配合使用

---

## 🤖 底盘控制配置

### ArduPilot 串口配置（只读模式）

**文件**: `medicine_chassis_bridge/config/chassis_bridge_ardupilot_serial_readonly.yaml`

**关键参数**:
```yaml
ardupilot_port: /dev/ttyS9
ardupilot_baudrate: 115200
ardupilot_readonly: true  # 只读模式（安全）
ardupilot_control_enabled: false  # 控制未使能
emergency_stop: true  # 默认急停
max_linear_speed: 0.2  # 最大线速度限制
max_angular_speed: 0.5  # 最大角速度限制
```

**安全机制**:
- 🛡️ 三级安全确认
- 🛡️ 速度限制
- 🛡️ Watchdog 超时保护

**使用场景**:
- ✅ 底盘心跳验证
- ✅ 安全测试
- ❌ 不发送控制命令

---

## 🔄 配置切换指南

### 方式 1：使用统一控制脚本（推荐）

```bash
bash /mnt/sdcard/rk3588_control.sh
# 选择 15. 切换视觉配置
# 选择配置类型
```

### 方式 2：使用专用脚本

```bash
# 切换到低功耗模式
bash /mnt/sdcard/rk3588_switch_vision_config.sh low_cpu

# 列出所有配置
bash /mnt/sdcard/rk3588_switch_vision_config.sh list
```

### 方式 3：手动修改 launch 文件

编辑 `medicine_robot_bringup/launch/pc_delivery_demo.launch.py`:

```python
DeclareLaunchArgument(
    'vision_config',
    default_value='low_cpu',  # 修改这里
    description='Vision configuration profile'
),
```

---

## 📊 性能调优建议

### 降低 CPU 占用

1. **降低帧率**
   - 从 20fps → 15fps 可降低 10% CPU
   - 从 15fps → 10fps 可降低 15% CPU

2. **降低分辨率**
   - 从 1280x720 → 640x480 可降低 20% CPU

3. **增加识别间隔**
   - `qr_recognition_period: 1.0` → `2.0` 可降低 5% CPU

4. **禁用 YOLO**
   - `yolo_enabled: false` 可降低 15% CPU
   - 但会失去物体检测能力

### 提高识别精度

1. **提高分辨率**
   - 使用 720p 配置
   - 适合远距离或小字体

2. **降低置信度阈值**
   - `yolo_confidence: 0.5` → `0.4`
   - 会增加误检率

3. **增加识别频率**
   - `qr_recognition_period: 1.0` → `0.5`
   - 会增加 CPU 占用

### 提高响应速度

1. **提高帧率**
   - 使用 fast 配置（25fps）

2. **减少识别间隔**
   - `qr_recognition_period: 1.0` → `0.5`

3. **使用 MJPEG 格式**
   - 比 YUYV 延迟更低

---

## 🔍 故障排查

### 问题 1：CPU 占用过高

**症状**: CPU 持续 >80%

**解决方案**:
1. 切换到 low_cpu 配置
2. 降低帧率
3. 增加识别间隔
4. 检查是否有其他进程占用 CPU

### 问题 2：识别率低

**症状**: 二维码识别失败率高

**解决方案**:
1. 切换到 720p 配置
2. 检查摄像头焦距
3. 改善光照条件
4. 降低置信度阈值

### 问题 3：帧率不稳定

**症状**: 帧率波动大

**解决方案**:
1. 切换到 balanced 配置
2. 检查 CPU 温度
3. 关闭其他占用资源的进程
4. 检查摄像头连接

### 问题 4：导航不准确

**症状**: 机器人偏离路径

**解决方案**:
1. 检查 AMCL 定位精度
2. 调整 `xy_goal_tolerance`
3. 重新建图
4. 检查雷达数据质量

---

## 📝 配置文件位置

### 本地配置（PC端）
```
D:\A1\
├── rk3588_vision_*.yaml
├── rk3588_nav2_params.yaml
└── rk3588_amcl_localization.yaml
```

### RK3588 配置
```
/mnt/sdcard/medicine_robot_data/config/
├── rk3588_nav2_params.yaml
└── stations.yaml
```

### ROS2 包配置
```
/mnt/sdcard/medicine_robot_ws/src/
├── medicine_vision_detector/config/
├── medicine_chassis_bridge/config/
└── medicine_robot_bringup/config/
```

---

## 🆘 获取帮助

如果你在配置过程中遇到问题：

1. **查看日志**
   ```bash
   bash /mnt/sdcard/rk3588_delivery_webctl.sh log 100
   ```

2. **健康检查**
   ```bash
   bash /mnt/sdcard/rk3588_control.sh health
   ```

3. **查看文档**
   - `QUICKSTART.md` - 快速开始
   - `OPTIMIZATION_COMPLETION_REPORT.md` - 优化报告
   - `memories/` - 技术细节

4. **联系支持**
   - GitHub Issues
   - Email: support@example.com

---

## ✅ 配置检查清单

切换配置后，验证：
- [ ] CPU 占用在预期范围内
- [ ] 帧率稳定
- [ ] 识别功能正常
- [ ] 系统温度正常
- [ ] 没有错误日志

---

**文档版本**: 1.0  
**更新日期**: 2026-05-31  
**维护者**: Kiro AI
