# RK3588 ELF 2 智能送药小车 Docker 部署说明（Ubuntu 22.04 + ROS 2 Humble）

本文记录如何把当前电脑端 `medicine_robot_ws` 项目打包为兼容 **RK3588 ELF 2 / Ubuntu 22.04 / ROS 2 Humble / ARM64** 的 Docker 镜像。

当前 PC 端开发环境是：

```text
Ubuntu 24.04 / WSL2
ROS 2 Jazzy
工作区：~/medicine_robot_ws
```

RK3588 目标环境是：

```text
RK3588 ELF 2
Ubuntu 22.04
ROS 2 Humble
CPU 架构：aarch64 / arm64
```

---

## 1. 总体结论

当前项目可以迁移到 RK3588 Docker，但要注意：

```text
PC/WSL: Ubuntu 24.04 + ROS 2 Jazzy + x86_64
RK3588: Ubuntu 22.04 + ROS 2 Humble + aarch64
```

所以 Docker 镜像必须使用：

```text
ROS 2 Humble
Ubuntu 22.04 Jammy
ARM64/aarch64
```

推荐先做 **基础业务镜像**，不强依赖 AIKit SDK：

```text
网页仪表盘
任务管理
语音命令调度
M2 串口桥接
雷达/底盘接口预留
```

AIKit SDK 后续只有在确认有 **ARM64 版 libaikit.so** 后再加入镜像。

---

## 2. 推荐部署路线

### 2.1 第一阶段：基础业务镜像

优先实现：

```text
medicine_robot_bringup
medicine_interfaces
medicine_task_manager
medicine_voice_interaction
medicine_web_dashboard
M2 串口桥接
网页访问 http://RK3588_IP:8080
```

启动时关闭 AIKit：

```bash
enable_aikit_esr:=false
```

如果 M2 语音模块通过串口输出识别结果，打开：

```bash
enable_m2_voice_bridge:=true
m2_serial_port:=/dev/ttyACM0
```

### 2.2 第二阶段：接入雷达和底盘

接入设备：

```text
A1/RPLIDAR：/dev/rplidar 或 /dev/ttyUSBx
AET-H743 Basic ArduPilot：/dev/ttyS9，115200，只读 MAVLink heartbeat 已验证
底盘控制输出：暂不启用，先保持 ardupilot_readonly=true、ardupilot_control_enabled=false
里程计来源：无轮速编码器，暂继续使用 rf2o_laser_odometry 输出 /odom
IMU：/dev/ttyUSBx 或 I2C/SPI
```

真实飞控接入时，先只接 MAVLink 遥测串口并做 heartbeat 验证：

```text
AET-H743 TELEM/UART TX -> RK3588 RX
AET-H743 TELEM/UART RX -> RK3588 TX
GND -> GND
确认电平为 3.3V TTL；不要把 5V 电源线误接到 RK3588 串口信号脚
```

ArduPilot 侧需要确认对应 `SERIALx` 参数：

```text
SERIALx_PROTOCOL=MAVLink2
SERIALx_BAUD=115 或等效 115200
```

RK3588 接线后执行严格只读 heartbeat 验证：

```bash
/mnt/sdcard/rk3588_verify_ardupilot_heartbeat.sh /dev/ttyS9 115200
```

### 2.3 第三阶段：可选接入 AIKit

只有满足下面条件后再启用：

```text
存在 ARM64/aarch64 版 AIKit SDK
libaikit.so 能在 RK3588 上运行
音频输入可通过 ALSA/PulseAudio 正常采集
```

---

## 3. RK3588 上的前置检查

在 RK3588 Ubuntu 22.04 上执行：

```bash
uname -m
lsb_release -a
```

期望：

```text
aarch64
Ubuntu 22.04.x LTS
```

如果当前输出类似下面内容：

```text
NAME=Buildroot
VERSION_ID=2021.11
PRETTY_NAME="Buildroot 2021.11"
```

说明当前板子运行的是 **Buildroot**，不是 Ubuntu 22.04。此时不要继续安装 Docker，也不要按本文后续步骤构建 ROS2 镜像。需要先烧录或切换到厂家提供的 **Ubuntu 22.04 Desktop / Jammy** 系统镜像，再继续本文步骤。

当前实机已经确认切换成功：

```text
uname -m: aarch64
Ubuntu 22.04.5 LTS
VERSION_CODENAME=jammy
```

检查 Docker：

```bash
docker --version
```

如果没有 Docker：

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

允许当前用户运行 Docker：

```bash
sudo usermod -aG docker $USER
newgrp docker
```

验证：

```bash
docker run --rm hello-world
```

---

## 4. 项目目录要求

推荐在 RK3588 上放置：

```bash
~/medicine_robot_ws
```

目录结构：

```text
medicine_robot_ws
├── src
│   ├── medicine_interfaces
│   ├── medicine_task_manager
│   ├── medicine_voice_interaction
│   ├── medicine_web_dashboard
│   ├── medicine_robot_bringup
│   └── wheeltec_aikit_esr              # 基础镜像中可以跳过编译
└── docker
    └── rk3588_humble
        ├── Dockerfile
        └── entrypoint.sh
```

从 PC/WSL 拷贝到 RK3588 时，不要拷贝这些目录：

```text
build
install
log
```

推荐同步命令示例：

```bash
rsync -av --delete \
  --exclude build \
  --exclude install \
  --exclude log \
  ~/medicine_robot_ws/ rk3588@RK3588_IP:~/medicine_robot_ws/
```

---

## 5. 创建 Docker 文件

在 RK3588 或 PC 工程根目录执行：

```bash
cd ~/medicine_robot_ws
mkdir -p docker/rk3588_humble
```

### 5.1 `docker/rk3588_humble/Dockerfile`

创建文件：

```bash
nano docker/rk3588_humble/Dockerfile
```

写入：

```dockerfile
FROM ros:humble-ros-base-jammy

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=humble
ENV WORKSPACE=/ros_ws

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    curl \
    python3-pip \
    python3-serial \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-setuptools \
    python3-wheel \
    libasound2-dev \
    libpulse-dev \
    ros-humble-ament-cmake \
    ros-humble-rclcpp \
    ros-humble-rclpy \
    ros-humble-std-msgs \
    ros-humble-geometry-msgs \
    ros-humble-nav-msgs \
    ros-humble-sensor-msgs \
    ros-humble-tf2 \
    ros-humble-tf2-ros \
    ros-humble-launch \
    ros-humble-launch-ros \
    && rm -rf /var/lib/apt/lists/*

WORKDIR ${WORKSPACE}

COPY src ./src

RUN . /opt/ros/humble/setup.sh && \
    colcon build \
      --symlink-install \
      --packages-skip wheeltec_aikit_esr

COPY docker/rk3588_humble/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["ros2", "launch", "medicine_robot_bringup", "pc_delivery_demo.launch.py", "enable_aikit_esr:=false", "enable_m2_voice_bridge:=false"]
```

说明：

```text
ros:humble-ros-base-jammy 是 Ubuntu 22.04 + ROS 2 Humble。
在 RK3588 本机 build 时会自动使用 ARM64 镜像层。
基础镜像先跳过 wheeltec_aikit_esr，因为 AIKit SDK 必须确认 ARM64 版本后才能进入镜像。
```

### 5.2 `docker/rk3588_humble/entrypoint.sh`

创建文件：

```bash
nano docker/rk3588_humble/entrypoint.sh
```

写入：

```bash
#!/bin/bash
set -e

source /opt/ros/humble/setup.bash
source /ros_ws/install/setup.bash

exec "$@"
```

---

## 6. 创建 `.dockerignore`

在工作区根目录创建：

```bash
nano .dockerignore
```

写入：

```text
build
install
log
.git
*.bag
*.db3
__pycache__
*.pyc
.cache
```

---

## 7. 在 RK3588 上构建镜像

进入工作区：

```bash
cd ~/medicine_robot_ws
```

构建：

```bash
docker build \
  -f docker/rk3588_humble/Dockerfile \
  -t medicine_robot:humble-rk3588 \
  .
```

查看镜像：

```bash
docker images | grep medicine_robot
```

期望：

```text
medicine_robot   humble-rk3588   ...
```

---

## 8. 在 PC 上交叉构建 ARM64 镜像（可选）

更推荐在 RK3588 上直接构建。如果必须在 x86_64 PC 上构建 ARM64 镜像，需要 Docker Buildx：

```bash
docker buildx create --use --name arm_builder
docker buildx inspect --bootstrap
```

构建 ARM64 镜像：

```bash
cd ~/medicine_robot_ws

docker buildx build \
  --platform linux/arm64 \
  -f docker/rk3588_humble/Dockerfile \
  -t medicine_robot:humble-rk3588 \
  --load \
  .
```

注意：

```text
x86_64 PC 上通过 QEMU 构建 ARM64 镜像会比较慢。
涉及硬件测试时仍然必须在 RK3588 上运行。
```

---

## 9. 基础镜像运行方式

### 9.1 无语音、无硬件，仅运行网页和任务管理

```bash
docker run -it --rm \
  --name medicine_robot \
  --net=host \
  medicine_robot:humble-rk3588
```

容器默认执行：

```bash
ros2 launch medicine_robot_bringup pc_delivery_demo.launch.py \
  enable_aikit_esr:=false \
  enable_m2_voice_bridge:=false
```

网页访问：

```text
http://RK3588_IP:8080
```

查看 RK3588 IP：

```bash
hostname -I
```

### 9.2 显式启动无语音 Demo

```bash
docker run -it --rm \
  --name medicine_robot \
  --net=host \
  medicine_robot:humble-rk3588 \
  ros2 launch medicine_robot_bringup pc_delivery_demo.launch.py \
    enable_aikit_esr:=false \
    enable_m2_voice_bridge:=false
```

---

## 10. M2 串口语音模块运行方式

### 10.1 RK3588 主机检查设备

在 RK3588 主机上执行：

```bash
lsusb
ls -l /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
```

M2 CH9102/CDC ACM 常见设备：

```text
1a86:55d4 QinHeng Electronics USB Single Serial
/dev/ttyACM0
```

如果没有 `/dev/ttyACM0`，加载 CDC ACM 驱动：

```bash
sudo modprobe cdc_acm
ls -l /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
```

临时授权：

```bash
sudo chmod 666 /dev/ttyACM0
```

长期建议把用户加入串口组：

```bash
sudo usermod -aG dialout $USER
```

重新登录后生效。

### 10.2 运行容器并挂载 M2 串口

如果 M2 是 `/dev/ttyACM0`：

```bash
docker run -it --rm \
  --name medicine_robot \
  --net=host \
  --device=/dev/ttyACM0:/dev/ttyACM0 \
  medicine_robot:humble-rk3588 \
  ros2 launch medicine_robot_bringup pc_delivery_demo.launch.py \
    enable_aikit_esr:=false \
    enable_m2_voice_bridge:=true \
    m2_serial_port:=/dev/ttyACM0
```

如果设备是 `/dev/ttyUSB0`：

```bash
docker run -it --rm \
  --name medicine_robot \
  --net=host \
  --device=/dev/ttyUSB0:/dev/ttyUSB0 \
  medicine_robot:humble-rk3588 \
  ros2 launch medicine_robot_bringup pc_delivery_demo.launch.py \
    enable_aikit_esr:=false \
    enable_m2_voice_bridge:=true \
    m2_serial_port:=/dev/ttyUSB0
```

---

## 11. A1/RPLIDAR 雷达设备挂载

A1/RPLIDAR 常见 USB 串口芯片：

```text
10c4:ea60 Silicon Labs CP210x
```

主机检查：

```bash
lsusb
ls -l /dev/ttyUSB* /dev/rplidar 2>/dev/null
```

如果已配置 udev 规则，推荐使用：

```text
/dev/rplidar
```

容器运行示例：

```bash
docker run -it --rm \
  --name medicine_robot \
  --net=host \
  --device=/dev/ttyACM0:/dev/ttyACM0 \
  --device=/dev/rplidar:/dev/rplidar \
  medicine_robot:humble-rk3588 \
  ros2 launch medicine_robot_bringup pc_delivery_demo.launch.py \
    enable_aikit_esr:=false \
    enable_m2_voice_bridge:=true \
    m2_serial_port:=/dev/ttyACM0
```

如果没有 `/dev/rplidar`，临时用实际设备：

```bash
--device=/dev/ttyUSB0:/dev/ttyUSB0
```

---

## 12. AET-H743 Basic ArduPilot 串口只读检查

当前底盘飞控计划使用 **AET-H743 Basic + ArduPilot + 四轮差速**。在不能直接接飞控前，已经完成 PC 串口助手模拟验证：

```text
PC 串口助手 HEX 循环发送
-> RK3588 /dev/ttyS9 @ 115200
-> medicine_chassis_bridge 只读解析 MAVLink HEARTBEAT
-> /medicine/chassis_status
```

已验证 heartbeat：

```text
FE 09 00 01 01 00 00 00 00 00 0A 03 00 03 03 00 00
heartbeat_ok=true
system_id=1
component_id=1
mavlink_version=1
type=10
autopilot=3
system_status=3
```

真实飞控接入前，继续保持：

```text
publish_odom=false
publish_tf=false
emergency_stop=true
ardupilot_readonly=true
ardupilot_control_enabled=false
```

主机侧只读串口检查：

```bash
/mnt/sdcard/rk3588_check_ardupilot_serial.sh /dev/ttyS9 115200
```

真实飞控接线后，优先执行严格 heartbeat 验证：

```bash
/mnt/sdcard/rk3588_verify_ardupilot_heartbeat.sh /dev/ttyS9 115200
```

只有同时满足以下条件才算接线和参数初步通过：

```text
RESULT PASS real ArduPilot heartbeat verified
emergency_stop=true
ardupilot.readonly=true
ardupilot.control_enabled=false
ardupilot.heartbeat_ok=true
ardupilot.heartbeat_count > 0
ardupilot.port=/dev/ttyS9
ardupilot.baudrate=115200
```

若返回 `RESULT FAIL real ArduPilot heartbeat not verified`，优先检查：TELEM 口对应的 `SERIALx_PROTOCOL/SERIALx_BAUD`、TX/RX 是否交叉、GND 是否共地、串口电平是否为 3.3V TTL、`/dev/ttyS9` 是否被其他进程占用、飞控是否上电并运行 ArduPilot。

不接飞控时，可先做 `/cmd_vel` 安全链路测试：

```bash
/mnt/sdcard/rk3588_chassis_cmd_vel_safety_test.sh /dev/ttyS9 115200
```

这个测试只检查限速、急停、watchdog 超时和状态发布，不会向 ArduPilot 输出控制命令。

2026-05-19 已在 RK3588 上运行该脚本，结果：

```text
RESULT PASS
急停开启时 /cmd_vel 不会进入目标速度
解除急停后 target/current 被限制在 max_linear_speed=0.2、max_angular_speed=0.5
停止发布 /cmd_vel 后 watchdog 触发 cmd_timed_out=true，target/current 回零
测试结束后 emergency_stop=true
全程 ardupilot_readonly=true、ardupilot_control_enabled=false
```

测试后已恢复 `/dev/ttyS9 @ 115200` 只读桥接后台运行。当前未接真实飞控/未持续输入 heartbeat 时，`heartbeat_ok=false` 属正常状态。

已将只读底盘桥接接入 `medicine_robot_bringup/launch/pc_delivery_demo.launch.py`，默认不启用。需要随业务 bringup 一起观察底盘状态时，显式增加：

```bash
enable_chassis_bridge:=true \
chassis_ardupilot_port:=/dev/ttyS9 \
chassis_ardupilot_baudrate:=115200 \
chassis_emergency_stop:=true
```

该 bringup 接入会强制覆盖为安全只读状态：

```text
mode=ardupilot
ardupilot_readonly=true
ardupilot_control_enabled=false
serial_enabled=false
publish_odom=false
publish_tf=false
```

2026-05-19 已在 RK3588 隔离 `ROS_DOMAIN_ID` 中验证：

```text
默认 enable_chassis_bridge=false 时，不启动 /chassis_bridge
显式 enable_chassis_bridge=true 时，启动 /chassis_bridge 并打开 /dev/ttyS9 @ 115200
/medicine/chassis_status 显示 emergency_stop=true、readonly=true、control_enabled=false
```

Web Dashboard 已接入底盘状态只读可视化：

```text
medicine_web_dashboard 订阅 /medicine/chassis_status
新增 GET /api/chassis_status
前端“单任务调试”页新增“底盘安全状态”卡片
展示急停、只读、控制输出、MAVLink 心跳、飞控身份、watchdog、目标速度和当前速度
```

本地隔离 `ROS_DOMAIN_ID` 端到端验证已通过：未收到底盘状态时 `/api/chassis_status` 返回 `received=false`；模拟发布状态后 API 返回完整 JSON，页面可用于远程观察只读底盘桥接安全状态。RK3588 隔离端口 `8095` 实机验证也已通过：`/api/health` 返回 `{"ok": true}`，`/api/chassis_status` 返回只读底盘状态 JSON，页面包含“底盘安全状态”，`/medicine/chassis_status` 可 echo 到实时状态；测试后已清理临时 `8095` launch，正式 `8085` 服务保持运行。

Docker 容器如需访问板载串口，需要挂载设备：

```bash
--device=/dev/ttyS9:/dev/ttyS9
```

---

## 13. 调试和验证命令

### 13.1 进入正在运行的容器

```bash
docker exec -it medicine_robot bash
```

进入后环境已经由 `entrypoint.sh` source 好。如果需要手动 source：

```bash
source /opt/ros/humble/setup.bash
source /ros_ws/install/setup.bash
```

### 13.2 查看 ROS2 包

```bash
ros2 pkg list | grep medicine
```

期望看到：

```text
medicine_interfaces
medicine_robot_bringup
medicine_task_manager
medicine_voice_interaction
medicine_web_dashboard
```

### 13.3 查看话题

```bash
ros2 topic list
```

常见话题：

```text
/medicine/delivery_state
/medicine/voice_text
/voice_words
```

### 13.4 模拟语音命令

进入容器或另开一个同网络 ROS2 环境，执行：

```bash
ros2 topic pub --once /voice_words std_msgs/msg/String "{data: 送药到A病房}"
```

B 病房：

```bash
ros2 topic pub --once /voice_words std_msgs/msg/String "{data: 送药到B病房}"
```

取消任务：

```bash
ros2 topic pub --once /voice_words std_msgs/msg/String "{data: 取消任务}"
```

### 13.5 查看任务状态

```bash
ros2 topic echo /medicine/delivery_state
```

### 13.6 查看语音播报文本

```bash
ros2 topic echo /medicine/voice_text
```

---

## 14. Docker Compose 可选方案

创建：

```bash
nano docker-compose.rk3588.yml
```

写入：

```yaml
services:
  medicine_robot:
    image: medicine_robot:humble-rk3588
    container_name: medicine_robot
    network_mode: host
    restart: unless-stopped
    devices:
      - /dev/ttyACM0:/dev/ttyACM0
    command:
      - ros2
      - launch
      - medicine_robot_bringup
      - pc_delivery_demo.launch.py
      - enable_aikit_esr:=false
      - enable_m2_voice_bridge:=true
      - m2_serial_port:=/dev/ttyACM0
```

启动：

```bash
docker compose -f docker-compose.rk3588.yml up
```

后台启动：

```bash
docker compose -f docker-compose.rk3588.yml up -d
```

查看日志：

```bash
docker logs -f medicine_robot
```

停止：

```bash
docker compose -f docker-compose.rk3588.yml down
```

---

## 15. AIKit SDK 可选打包方案

基础镜像默认跳过：

```bash
--packages-skip wheeltec_aikit_esr
```

原因是 AIKit SDK 必须匹配 RK3588 架构。

### 15.1 检查 SDK 架构

在有 SDK 的机器上执行：

```bash
file aikit_sdk/libs/libaikit.so
```

如果输出包含：

```text
x86-64
```

不能用于 RK3588。

如果输出包含：

```text
ARM aarch64
```

可以用于 RK3588。

### 15.2 ARM64 AIKit 镜像思路

假设 ARM64 SDK 放在：

```text
third_party/aikit_sdk_arm64
```

Dockerfile 中增加：

```dockerfile
COPY third_party/aikit_sdk_arm64 /opt/aikit_sdk

RUN . /opt/ros/humble/setup.sh && \
    colcon build \
      --symlink-install \
      --cmake-args -DAIKIT_SDK_DIR=/opt/aikit_sdk
```

运行时挂载私有凭据，不要写入镜像：

```bash
-v ~/.config/medicine_robot/aikit.env:/root/.config/medicine_robot/aikit.env:ro
```

如果使用 ALSA 采音，还要挂载声卡：

```bash
--device=/dev/snd
```

启动示例：

```bash
docker run -it --rm \
  --name medicine_robot \
  --net=host \
  --device=/dev/snd \
  -v ~/.config/medicine_robot/aikit.env:/root/.config/medicine_robot/aikit.env:ro \
  medicine_robot:humble-rk3588-aikit \
  ros2 launch medicine_robot_bringup pc_delivery_demo.launch.py \
    enable_aikit_esr:=true \
    aikit_audio_backend:=alsa \
    aikit_record_device:=plughw:1,0 \
    enable_m2_voice_bridge:=false
```

---

## 16. Humble 兼容注意事项

### 16.1 Python 版本

Jazzy/Ubuntu 24.04 常见：

```text
Python 3.12
```

Humble/Ubuntu 22.04 常见：

```text
Python 3.10
```

避免使用 Python 3.11/3.12 才有的特性，例如：

```text
tomllib
新版本 typing 特性
只在 3.12 行为正常的 setuptools 配置
```

### 16.2 Launch API

以下 API 在 Humble 可用：

```python
DeclareLaunchArgument
LaunchConfiguration
Node
IfCondition
SetEnvironmentVariable
```

当前 launch 文件大概率兼容 Humble。

### 16.3 C++ 包

Humble 支持 C++17。CMake 中建议使用：

```cmake
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
```

### 16.4 构建失败处理

如果 `wheeltec_aikit_esr` 因 SDK 不存在或架构不对失败，基础镜像中先跳过：

```bash
colcon build --symlink-install --packages-skip wheeltec_aikit_esr
```

当前 `pc_delivery_demo.launch.py` 已做无 AIKit 镜像兼容：

```text
enable_aikit_esr:=false 时，允许 wheeltec_aikit_esr 未安装。
enable_aikit_esr:=true 时，仍然需要 wheeltec_aikit_esr 和 ARM64 AIKit SDK。
```

如果某个包缺依赖，进入容器后查：

```bash
rosdep check --from-paths src --ignore-src -r
```

安装缺失依赖后重建镜像。

---

## 17. 常见问题

### 17.1 网页打不开

确认容器使用了 host 网络：

```bash
--net=host
```

确认节点监听 8080：

```bash
ss -ltnp | grep 8080
```

浏览器访问：

```text
http://RK3588_IP:8080
```

### 17.2 容器里看不到串口

主机先确认：

```bash
ls -l /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
```

运行容器时必须加：

```bash
--device=/dev/ttyACM0:/dev/ttyACM0
```

或：

```bash
--device=/dev/ttyUSB0:/dev/ttyUSB0
```

### 17.3 M2 设备没有生成 `/dev/ttyACM0`

主机执行：

```bash
lsusb
sudo modprobe cdc_acm
ls -l /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
```

M2 CH9102/CDC ACM 不建议强行绑定 generic `usbserial`，优先使用 `cdc_acm`。

### 17.4 ROS2 节点无法互相发现

容器运行加：

```bash
--net=host
```

如果多机通信，检查：

```bash
echo $ROS_DOMAIN_ID
```

必要时统一设置：

```bash
export ROS_DOMAIN_ID=0
```

### 17.5 端口被占用

查看：

```bash
ss -ltnp | grep 8080
```

停止旧容器：

```bash
docker ps
docker stop medicine_robot
```

### 17.6 需要长期运行

推荐用 Compose 后台启动：

```bash
docker compose -f docker-compose.rk3588.yml up -d
```

开机自启可以后续用 systemd 管理 Docker Compose。

---

## 18. 推荐最终运行命令

### 18.1 当前最稳：网页 + 任务 + M2 串口

```bash
docker run -it --rm \
  --name medicine_robot \
  --net=host \
  --device=/dev/ttyACM0:/dev/ttyACM0 \
  medicine_robot:humble-rk3588 \
  ros2 launch medicine_robot_bringup pc_delivery_demo.launch.py \
    enable_aikit_esr:=false \
    enable_m2_voice_bridge:=true \
    m2_serial_port:=/dev/ttyACM0
```

网页访问：

```text
http://RK3588_IP:8080
```

### 18.2 无硬件调试

```bash
docker run -it --rm \
  --name medicine_robot \
  --net=host \
  medicine_robot:humble-rk3588 \
  ros2 launch medicine_robot_bringup pc_delivery_demo.launch.py \
    enable_aikit_esr:=false \
    enable_m2_voice_bridge:=false
```

然后模拟任务：

```bash
docker exec -it medicine_robot bash
ros2 topic pub --once /voice_words std_msgs/msg/String "{data: 送药到A病房}"
```

---

## 19. 当前建议

当前 RK3588 只能使用 Ubuntu 22.04 + ROS 2 Humble，因此推荐：

```text
1. 先构建 medicine_robot:humble-rk3588 基础镜像
2. 先不启用 wheeltec_aikit_esr
3. 使用 M2 串口桥接作为语音输入主方案
4. 网页、任务管理、状态显示先跑通
5. 再接入雷达、底盘、Nav2
6. 最后确认 ARM64 AIKit SDK 后再做 AIKit 镜像
```

这样可以最大限度降低 RK3588 迁移风险。
