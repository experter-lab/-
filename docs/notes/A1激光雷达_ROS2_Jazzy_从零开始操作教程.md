# A1 激光雷达 + ROS 2 Jazzy 从零开始建图与导航操作教程

这份教程的目标是：**你不用再去翻 A1 文件夹里的 PDF、视频、说明书，直接照着本文一步一步操作。**

你的当前前提是：

- 已经有一台 Ubuntu 24.04 电脑
- 已经安装 ROS 2 Jazzy
- 手上有 A1 激光雷达
- 想完成：雷达出数据 -> 建图 -> 保存地图 -> 导航

本文默认你在 **Ubuntu 终端** 里执行命令，不是在 Windows PowerShell 里执行。

---

# 0. 先看结论：整个流程分 4 个阶段

你最终要完成的是这条链路：

```text
A1 激光雷达
  -> sllidar_ros2 驱动
  -> /scan 激光雷达话题
  -> slam_toolbox 建图
  -> 保存地图 a1_map.yaml + a1_map.pgm
  -> Nav2 加载地图导航
```

整个过程分成 4 个阶段：

```text
阶段 1：先让 A1 雷达在 ROS 2 中正常发布 /scan
阶段 2：确认机器人底盘有 /odom、/cmd_vel、TF
阶段 3：用 slam_toolbox 建图并保存地图
阶段 4：用 Nav2 加载地图并导航
```

**非常重要：A1 雷达只负责扫描环境。**

如果你只有一个雷达，没有移动底盘、没有里程计 `/odom`、没有速度控制 `/cmd_vel`，那你只能完成阶段 1，不能真正完成建图导航。

---

# 1. 本教程使用的资料来自哪里

我已经帮你从 `D:\A1` 文件夹里提取出真正有用的信息。

最关键的源码包是：

```text
D:\A1\附录\4.功能源码包\rplidar_ros2_ws.zip
```

这个压缩包里有 ROS 2 雷达驱动：

```text
sllidar_ros2
```

A1 雷达的关键参数是：

| 项目 | 值 |
|---|---|
| 驱动包 | `sllidar_ros2` |
| 雷达型号 | RPLIDAR A1 |
| 串口波特率 | `115200` |
| 默认串口 | `/dev/ttyUSB0` |
| 推荐固定设备名 | `/dev/rplidar` |
| 雷达话题 | `/scan` |
| 雷达坐标系 | `laser` |
| 消息类型 | `sensor_msgs/msg/LaserScan` |

你后面只需要围绕这些东西操作。

---

# 2. 第一次操作前，你需要准备什么

## 2.1 需要准备的硬件

你需要：

- A1 激光雷达
- A1 雷达的 USB 转接板或串口转 USB 模块
- Ubuntu 24.04 + ROS 2 Jazzy 电脑
- 如果要导航，还需要一台可移动机器人底盘

机器人底盘至少要能提供：

| 必需内容 | 说明 |
|---|---|
| `/odom` | 机器人里程计 |
| `odom -> base_link` | 里程计 TF |
| `/cmd_vel` | 速度控制话题 |
| `base_link` | 机器人底盘坐标系 |

如果你现在还没有底盘驱动，可以先做完雷达 `/scan` 测试。

## 2.2 需要准备的软件包

打开 Ubuntu 终端，先执行：

```bash
source /opt/ros/jazzy/setup.bash
```

检查 ROS 2 是否正常：

```bash
echo $ROS_DISTRO
ros2 topic list
```

你应该看到：

```text
jazzy
```

如果 `echo $ROS_DISTRO` 没输出 `jazzy`，说明你当前终端还没 source ROS 2。

安装后面要用的工具：

```bash
sudo apt update
sudo apt install -y \
  git \
  unzip \
  python3-colcon-common-extensions \
  python3-rosdep \
  ros-jazzy-rviz2 \
  ros-jazzy-tf2-ros \
  ros-jazzy-slam-toolbox \
  ros-jazzy-navigation2 \
  ros-jazzy-nav2-bringup \
  ros-jazzy-nav2-map-server
```

如果提示已经安装，没关系。

---

# 3. 创建工作区

以后所有 A1 雷达相关内容都放在这个工作区：

```bash
mkdir -p ~/a1_lidar_ws/src
cd ~/a1_lidar_ws
```

确认目录存在：

```bash
pwd
ls
```

你应该看到当前位置类似：

```text
/home/你的用户名/a1_lidar_ws
```

---

# 4. 获取 A1 雷达 ROS 2 驱动

你有两种方式。

推荐优先用 **方式 A：官方最新源码**。

如果你的 Ubuntu 不能联网，就用 **方式 B：A1 资料包里的本地源码**。

---

## 方式 A：从官方仓库下载驱动，推荐

在 Ubuntu 终端执行：

```bash
cd ~/a1_lidar_ws/src
git clone https://github.com/Slamtec/sllidar_ros2.git
```

执行后检查：

```bash
ls ~/a1_lidar_ws/src
```

你应该看到：

```text
sllidar_ros2
```

如果这一步成功，跳到第 5 章。

---

## 方式 B：使用 A1 文件夹里的本地源码包

你需要先把 Windows 里的这个文件复制到 Ubuntu：

```text
D:\A1\附录\4.功能源码包\rplidar_ros2_ws.zip
```

复制到 Ubuntu 后，建议放在：

```text
~/Downloads/rplidar_ros2_ws.zip
```

确认 Ubuntu 里能看到这个文件：

```bash
ls -lh ~/Downloads/rplidar_ros2_ws.zip
```

如果能看到文件大小，说明复制成功。

然后执行：

```bash
cd ~/a1_lidar_ws
mkdir -p /tmp/a1_rplidar_src
unzip ~/Downloads/rplidar_ros2_ws.zip -d /tmp/a1_rplidar_src
cp -r /tmp/a1_rplidar_src/rplidar_ros2_ws/src/sllidar_ros2 ~/a1_lidar_ws/src/
```

检查：

```bash
ls ~/a1_lidar_ws/src
```

你应该看到：

```text
sllidar_ros2
```

---

# 5. 编译 A1 雷达驱动

进入工作区：

```bash
cd ~/a1_lidar_ws
source /opt/ros/jazzy/setup.bash
```

安装依赖：

```bash
rosdep install --from-paths src --ignore-src -r -y
```

开始编译：

```bash
colcon build --symlink-install
```

编译成功后，你应该看到类似：

```text
Summary: 1 package finished
```

然后 source 当前工作区：

```bash
source ~/a1_lidar_ws/install/setup.bash
```

检查 ROS 2 是否能找到驱动包：

```bash
ros2 pkg list | grep sllidar
```

你应该看到：

```text
sllidar_ros2
```

再检查驱动节点是否存在：

```bash
ros2 pkg executables sllidar_ros2
```

你应该看到类似：

```text
sllidar_ros2 sllidar_node
sllidar_ros2 sllidar_client
```

如果这里能看到 `sllidar_node`，说明驱动编译成功。

---

# 6. 设置每次打开终端自动加载工作区

这一步不是必须，但推荐做。

执行：

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
echo "source ~/a1_lidar_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

之后你每次打开新终端，就不用重复输入 source 命令。

---

# 7. 连接 A1 雷达并确认系统识别

把 A1 雷达插到 Ubuntu 电脑 USB 口。

如果执行 `lsusb` 时提示：

```text
Command 'lsusb' not found
```

说明系统里还没有安装 USB 查看工具。先安装：

```bash
sudo apt update
sudo apt install -y usbutils
```

安装完成后再执行：

```bash
lsusb
```

你要找类似 Silicon Labs、CP210x、USB UART 的设备。

如果你暂时不想安装 `usbutils`，也可以先跳过 `lsusb`，直接执行下面的串口检查命令。

执行：

```bash
ls -l /dev/ttyUSB*
```

正常情况下你会看到类似：

```text
/dev/ttyUSB0
```

如果没有 `/dev/ttyUSB0`，执行：

```bash
dmesg | grep -i tty
```

如果系统完全没有识别到串口，优先检查：

- USB 线是否能传数据
- 雷达转接板是否供电
- 虚拟机是否把 USB 设备连接到了 Ubuntu
- 是否被 Windows 占用了 USB 设备

## 7.1 如果你用的是 WSL2，必须先把 USB 转发进 WSL

如果你的终端提示符类似：

```text
用户名@LAPTOP-xxxx:~/a1_lidar_ws$
```

并且 `lsusb` 只看到：

```text
Linux Foundation 2.0 root hub
Linux Foundation 3.0 root hub
```

同时 `/dev/ttyUSB*` 不存在，说明 WSL2 还没有接收到 A1 雷达 USB 设备。

这时不要继续执行第 8 步。必须先在 Windows 里安装并使用 `usbipd-win`。

在 Windows PowerShell 管理员窗口执行：

```powershell
winget install --exact dorssel.usbipd-win
```

如果提示：

```text
无法将“winget”项识别为 cmdlet、函数、脚本文件或可运行程序的名称
```

说明你的 Windows 没有安装 `winget`。这时有两种办法。

第一种办法：去 Microsoft Store 安装或更新 `App Installer`，安装后重新打开 PowerShell，再执行上面的 `winget` 命令。

第二种办法：不用 `winget`，直接打开 `usbipd-win` 的 GitHub 发布页，下载 `.msi` 安装包并双击安装：

```text
https://github.com/dorssel/usbipd-win/releases
```

下载文件名通常类似：

```text
usbipd-win_x.x.x.msi
```

安装完成后，重新打开 Windows PowerShell 管理员窗口，执行：

```powershell
usbipd --version
```

如果能显示版本号，说明 `usbipd-win` 安装成功。

安装完成后，重新打开 Windows PowerShell 管理员窗口，查看 USB 设备：

```powershell
usbipd list
```

找到类似下面的设备：

```text
Silicon Labs CP210x USB to UART Bridge
CP2102 USB to UART Bridge Controller
USB Serial
```

例如你看到下面这一行，就说明 A1 雷达的 USB 串口已经被 Windows 识别到了：

```text
3-3    10c4:ea60  Silicon Labs CP210x USB to UART Bridge (COM15)    Shared
```

其中 `10c4:ea60` 正好对应 A1 资料里的 CP210x 串口芯片识别码，`3-3` 就是后面要用的 `BUSID`。

记住它左侧的 `BUSID`，例如：

```text
2-3
```

然后绑定设备：

```powershell
usbipd bind --busid 2-3
```

再把设备挂载到 WSL：

```powershell
usbipd attach --wsl --busid 2-3
```

如果你的电脑有多个 WSL 发行版，可以指定 Ubuntu：

```powershell
usbipd attach --wsl --distribution Ubuntu-24.04 --busid 2-3
```

然后回到 Ubuntu 终端执行：

```bash
lsusb
ls -l /dev/ttyUSB*
dmesg | grep -i tty
```

正常情况下，这时应该能看到 A1 雷达对应的 USB 设备，并出现：

```text
/dev/ttyUSB0
```

如果 `lsusb` 能看到 CP210x，但仍然没有 `/dev/ttyUSB0`，先在 Windows PowerShell 执行：

```powershell
wsl --update
wsl --shutdown
```

然后重新打开 Ubuntu，再重新执行 `usbipd attach --wsl --busid 你的BUSID`。

如果回到 Ubuntu 后，`lsusb` 已经能看到：

```text
10c4:ea60 Silicon Labs CP210x UART Bridge
```

但是执行：

```bash
ls -l /dev/ttyUSB*
```

仍然提示：

```text
No such file or directory
```

说明 USB 已经进了 WSL，但 CP210x 串口驱动还没有加载。先在 Ubuntu 里执行：

```bash
sudo modprobe usbserial
sudo modprobe cp210x
```

然后重新检查：

```bash
ls -l /dev/ttyUSB*
dmesg | grep -i cp210
dmesg | grep -i tty
```

如果出现：

```text
/dev/ttyUSB0
```

就可以继续第 8 步。

如果你看到类似：

```text
crw------- 1 root root 188, 0 ... /dev/ttyUSB0
```

说明串口已经出现，但当前用户可能没有读写权限。后面如果启动雷达时报 `Permission denied`，执行第 9 章的串口权限处理，或者先临时执行：

```bash
sudo chmod 666 /dev/ttyUSB0
```

如果 `modprobe cp210x` 提示模块不存在，说明当前 WSL 内核缺少 CP210x 串口模块。先在 Windows PowerShell 管理员窗口执行：

```powershell
wsl --update
wsl --shutdown
```

然后重新打开 Ubuntu，并重新挂载雷达：

```powershell
usbipd attach --wsl --busid 你的BUSID
```

如果更新后仍然没有 `/dev/ttyUSB0`，建议改用原生 Ubuntu 或虚拟机 USB 直通，因为 ROS2 激光雷达长期运行时，原生 Ubuntu 对 USB 串口支持更稳定。

---

# 8. 固定雷达设备名为 `/dev/rplidar`

如果不固定设备名，雷达有时是 `/dev/ttyUSB0`，有时可能变成 `/dev/ttyUSB1`。

所以建议固定成：

```text
/dev/rplidar
```

执行：

```bash
sudo tee /etc/udev/rules.d/rplidar.rules >/dev/null <<'EOF'
KERNEL=="ttyUSB*", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE:="0666", SYMLINK+="rplidar"
EOF
```

刷新规则：

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

如果你在 WSL2 里看到：

```text
Failed to send reload request: No such file or directory
```

这是因为当前 WSL 没有正常运行 udev 控制服务。这个错误不影响你继续测试 A1 雷达。

WSL2 下可以先跳过 `/dev/rplidar` 固定名，直接使用：

```text
/dev/ttyUSB0
```

后面启动雷达时，把参数写成：

```text
serial_port:=/dev/ttyUSB0
```

如果权限不够，先执行：

```bash
sudo chmod 666 /dev/ttyUSB0
```

拔掉 A1 雷达，再重新插上。

检查：

```bash
ls -l /dev/rplidar
```

成功时会看到类似：

```text
/dev/rplidar -> ttyUSB0
```

如果没有 `/dev/rplidar`，先临时用 `/dev/ttyUSB0` 继续后面的步骤。

---

# 9. 处理串口权限

如果启动雷达时报权限错误，比如：

```text
Permission denied
```

执行：

```bash
sudo usermod -aG dialout $USER
```

然后必须：

```text
注销 Ubuntu 用户，再重新登录
```

重新登录后检查：

```bash
groups
```

你应该能看到：

```text
dialout
```

---

# 10. 第一次启动 A1 雷达

打开一个新终端，称为 **终端 1：雷达终端**。

执行：

```bash
source /opt/ros/jazzy/setup.bash
source ~/a1_lidar_ws/install/setup.bash

ros2 run sllidar_ros2 sllidar_node --ros-args \
  -p serial_port:=/dev/rplidar \
  -p serial_baudrate:=115200 \
  -p frame_id:=laser \
  -p inverted:=false \
  -p angle_compensate:=true
```

如果你没有 `/dev/rplidar`，改用：

```bash
ros2 run sllidar_ros2 sllidar_node --ros-args \
  -p serial_port:=/dev/ttyUSB0 \
  -p serial_baudrate:=115200 \
  -p frame_id:=laser \
  -p inverted:=false \
  -p angle_compensate:=true
```

成功时你应该看到类似：

```text
SLLidar health status : OK
current scan mode
```

并且雷达开始旋转。

如果你看到类似下面的输出，也表示 A1 雷达驱动已经启动成功：

```text
SLLidar health status : OK.
current scan mode: Standard, sample rate: 2 Khz, max_distance: 12.0 m, scan frequency:10.0 Hz
```

**这个终端不要关闭。**

---

# 11. 检查 `/scan` 是否出来了

再打开一个新终端，称为 **终端 2：检查终端**。

执行：

```bash
source /opt/ros/jazzy/setup.bash
source ~/a1_lidar_ws/install/setup.bash
```

查看话题列表：

```bash
ros2 topic list
```

你应该能看到：

```text
/scan
```

查看 `/scan` 类型：

```bash
ros2 topic info /scan
```

你应该看到：

```text
Type: sensor_msgs/msg/LaserScan
```

查看一帧雷达数据：

```bash
ros2 topic echo /scan --once
```

你应该能看到：

```text
header:
  frame_id: laser
angle_min:
angle_max:
ranges:
```

查看频率：

```bash
ros2 topic hz /scan
```

能持续输出频率，就说明 A1 雷达已经成功接入 ROS 2。

---

# 12. 用 RViz2 看雷达扫描

打开一个新终端，称为 **终端 3：RViz 终端**。

执行：

```bash
source /opt/ros/jazzy/setup.bash
source ~/a1_lidar_ws/install/setup.bash
rviz2
```

RViz 打开后按下面操作：

1. 左上角 `Fixed Frame` 填：`laser`
2. 左下角点 `Add`
3. 选择 `By topic`
4. 找到 `/scan`
5. 选择 `LaserScan`
6. 点 `OK`

如果你看到一圈点，说明雷达工作正常。

如果 RViz 终端出现：

```text
StandardPaths: wrong permissions on runtime directory /mnt/wslg/runtime-dir
Stereo is NOT SUPPORTED
```

这两个通常是 WSLg/RViz 的普通提示，可以先忽略。

如果 RViz 终端持续出现：

```text
Message Filter dropping message: frame 'laser' ... reason 'discarding message because the queue is full'
```

通常是 RViz 没有成功把 `/scan` 的 `laser` 坐标系转换到当前 `Fixed Frame`。先按下面方式处理：

1. 在 RViz 左侧 `Global Options` 里确认 `Fixed Frame` 是 `laser`
2. 如果原来不是 `laser`，改成 `laser` 后按回车
3. 删除已经添加的 `LaserScan` 显示项
4. 重新点 `Add`
5. 选择 `By topic`
6. 重新添加 `/scan` 的 `LaserScan`
7. 在 `LaserScan` 显示项里，把 `Reliability Policy` 改成 `Best Effort`
8. 如果还有丢包提示，把 `Queue Size` 从 `10` 改成 `100`

在只测试雷达的阶段，`Fixed Frame=laser` 是最简单的方式，因为这时还不需要 `base_link`、`odom`、`map` 这些 TF。

如果你已经把 `Fixed Frame` 改成了 `laser`，但 RViz 仍然显示：

```text
No tf data. Actual error: Frame [laser] does not exist
```

说明 RViz 里虽然填写了 `laser`，但当前 ROS 2 系统里还没有任何 TF 节点发布 `laser` 这个坐标系。可以临时发布一个静态 TF 来让 RViz 认识 `laser`。

新开一个终端执行：

```bash
source /opt/ros/jazzy/setup.bash

ros2 run tf2_ros static_transform_publisher \
  --x 0 --y 0 --z 0 \
  --roll 0 --pitch 0 --yaw 0 \
  --frame-id base_link \
  --child-frame-id laser
```

然后在 RViz 里把 `Fixed Frame` 改成：

```text
base_link
```

再看 `/scan` 的 `LaserScan` 显示项是否变成正常。这个静态 TF 只是临时测试用，后面正式安装到机器人上时，需要把 `x/y/z/roll/pitch/yaw` 改成雷达相对底盘的真实安装位置。

## 12.1 没有底盘可以建图吗

结论分两种情况。

第一种：如果 A1 雷达固定不动，只放在桌子上扫描。

这种情况下不能建出完整房间地图，只能看到雷达当前位置周围的一圈障碍物。因为建图需要雷达在环境里移动，系统才知道不同位置看到的墙面如何拼接。

第二种：如果你手持 A1 雷达，或者把雷达放在小车、推车、支架上慢慢移动。

这种情况下可以尝试建图，但还缺一个关键数据：

```text
/odom
```

普通机器人底盘会通过轮子编码器提供 `/odom`。没有底盘时，可以尝试用激光扫描匹配算法根据 `/scan` 估计一个“激光里程计”，再把它提供给 `slam_toolbox`。

这种方案的链路是：

```text
A1 雷达 -> /scan -> 激光扫描匹配里程计 -> /odom -> slam_toolbox -> /map
```

常见可选方案包括：

```text
rf2o_laser_odometry
laser_scan_matcher
```

但这种“无底盘建图”有明显限制：

- **不能导航**：没有底盘就没有 `/cmd_vel` 执行导航速度命令
- **容易漂移**：只靠激光匹配，没有轮子里程计辅助
- **移动要很慢**：手持时不能抖、不能倾斜、不能快速旋转
- **环境要有特征**：空旷房间、长走廊、玻璃环境效果会差
- **雷达必须保持水平**：A1 是 2D 雷达，倾斜后数据会变形

所以推荐顺序是：

```text
1. 先确认 /scan 和 RViz 显示正常
2. 如果只是测试雷达，到这里就够了
3. 如果想无底盘建图，再额外配置激光里程计
4. 如果想导航，必须准备可控制底盘
```

## 12.2 无底盘手持 A1 雷达尝试建图

这一节适合你当前的情况：**底盘后面再准备，现在先手持 A1 雷达体验建图。**

手持建图的思路是：

```text
A1 雷达发布 /scan
  -> rf2o_laser_odometry 根据连续激光帧估计 /odom
  -> slam_toolbox 使用 /scan + /odom 生成 /map
  -> map_saver_cli 保存地图
```

注意：这只是临时体验方案，不适合最终导航。

### 12.2.1 安装或编译 `rf2o_laser_odometry`

先尝试用源码编译，比较直接。

打开 Ubuntu 终端：

```bash
cd ~/a1_lidar_ws/src
git clone https://github.com/Adlink-ROS/rf2o_laser_odometry.git
```

如果提示目录已经存在，说明你之前下载过，可以跳过。

回到工作区编译：

```bash
cd ~/a1_lidar_ws
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --packages-select rf2o_laser_odometry
source install/setup.bash
```

检查节点是否存在：

```bash
ros2 pkg executables rf2o_laser_odometry
```

你应该能看到：

```text
rf2o_laser_odometry rf2o_laser_odometry_node
```

如果这里编译失败，把完整报错发出来，需要根据 Jazzy 的实际编译错误调整。

### 12.2.2 启动手持建图需要的终端

手持建图至少开 5 个终端。

#### 终端 1：A1 雷达驱动

如果雷达驱动已经在运行，不要关。

如果没运行，执行：

```bash
source /opt/ros/jazzy/setup.bash
source ~/a1_lidar_ws/install/setup.bash
sudo chmod 666 /dev/ttyUSB0

ros2 run sllidar_ros2 sllidar_node --ros-args \
  -p serial_port:=/dev/ttyUSB0 \
  -p serial_baudrate:=115200 \
  -p frame_id:=laser \
  -p inverted:=false \
  -p angle_compensate:=true
```

#### 终端 2：发布 `base_link -> laser`

手持时可以先认为 `base_link` 和 `laser` 在同一个位置。

```bash
source /opt/ros/jazzy/setup.bash

ros2 run tf2_ros static_transform_publisher \
  --x 0 --y 0 --z 0 \
  --roll 0 --pitch 0 --yaw 0 \
  --frame-id base_link \
  --child-frame-id laser
```

这个终端不要关闭。

#### 终端 3：启动激光里程计 `rf2o`

```bash
source /opt/ros/jazzy/setup.bash
source ~/a1_lidar_ws/install/setup.bash

ros2 run rf2o_laser_odometry rf2o_laser_odometry_node --ros-args \
  -p laser_scan_topic:=/scan \
  -p odom_topic:=/odom \
  -p publish_tf:=true \
  -p base_frame_id:=base_link \
  -p odom_frame_id:=odom \
  -p freq:=10.0
```

这个节点会根据 `/scan` 估计雷达移动，并发布：

```text
/odom
odom -> base_link
```

检查是否成功：

```bash
ros2 topic echo /odom --once
ros2 run tf2_ros tf2_echo odom base_link
```

如果能看到 `/odom` 数据和 TF 输出，说明手持建图需要的“假底盘里程计”已经有了。

#### 终端 4：启动 `slam_toolbox`

先创建手持建图参数文件：

```bash
mkdir -p ~/a1_lidar_ws/config
cat > ~/a1_lidar_ws/config/a1_handheld_slam_toolbox.yaml <<'EOF'
slam_toolbox:
  ros__parameters:
    use_sim_time: false
    odom_frame: odom
    map_frame: map
    base_frame: base_link
    scan_topic: /scan
    mode: mapping
    resolution: 0.05
    max_laser_range: 12.0
    minimum_time_interval: 0.2
    transform_timeout: 0.2
    tf_buffer_duration: 30.0
    throttle_scans: 1
    solver_plugin: solver_plugins::CeresSolver
    ceres_linear_solver: SPARSE_NORMAL_CHOLESKY
    ceres_preconditioner: SCHUR_JACOBI
    ceres_trust_strategy: LEVENBERG_MARQUARDT
    ceres_dogleg_type: TRADITIONAL_DOGLEG
    ceres_loss_function: None
EOF
```

启动建图：

```bash
source /opt/ros/jazzy/setup.bash
source ~/a1_lidar_ws/install/setup.bash

ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=$HOME/a1_lidar_ws/config/a1_handheld_slam_toolbox.yaml \
  use_sim_time:=false
```

注意不要写成：

```bash
slam_params_file:=~/a1_lidar_ws/config/a1_handheld_slam_toolbox.yaml
```

因为 ROS 2 launch 参数里 `~` 可能不会被展开，容易出现：

```text
Parameter file path is not a file: ~/a1_lidar_ws/config/a1_handheld_slam_toolbox.yaml
```

如果看到这个提示，改用：

```bash
slam_params_file:=$HOME/a1_lidar_ws/config/a1_handheld_slam_toolbox.yaml
```

启动前也可以先确认参数文件真实存在：

```bash
ls -l $HOME/a1_lidar_ws/config/a1_handheld_slam_toolbox.yaml
```

如果 `slam_toolbox` 持续提示：

```text
Failed to compute odom pose
```

说明它没有查到 `odom -> base_link`。先确认 `rf2o` 正在运行，并执行：

```bash
ros2 run tf2_ros tf2_echo odom base_link
```

只有这个命令能持续输出变换后，再启动 `slam_toolbox`。

#### 终端 5：打开 RViz 看地图

```bash
source /opt/ros/jazzy/setup.bash
source ~/a1_lidar_ws/install/setup.bash
rviz2
```

RViz 中设置：

```text
Fixed Frame: map
Add -> By topic -> /map -> Map
Add -> By topic -> /scan -> LaserScan
Add -> TF
```

如果正常，你会看到地图开始生成。

### 12.2.3 手持移动方式

手持建图时动作非常重要。

建议这样做：

- **保持水平**：雷达不能上下倾斜
- **保持高度稳定**：尽量不要一会儿高一会儿低
- **移动很慢**：每秒 5 到 10 厘米即可
- **转弯很慢**：不要快速原地转圈
- **不要遮挡雷达**：手、身体、线缆不要挡住扫描面
- **沿墙走一圈**：让雷达持续看到墙、桌子、柜子等特征
- **尽量回到起点**：方便 SLAM 闭环

不建议：

- 快速晃动雷达
- 把雷达拿在手里上下抖
- 在空旷大房间中间测试
- 对着玻璃、镜子、大面积纯白墙测试

### 12.2.4 保存手持建图地图

地图看起来差不多后，新开一个终端：

```bash
source /opt/ros/jazzy/setup.bash
mkdir -p ~/maps
ros2 run nav2_map_server map_saver_cli -f ~/maps/a1_handheld_map
```

检查：

```bash
ls -lh ~/maps/a1_handheld_map.*
```

成功后会有：

```text
~/maps/a1_handheld_map.yaml
~/maps/a1_handheld_map.pgm
```

### 12.2.5 手持建图常见问题

如果没有 `/odom`：

```bash
ros2 topic list | grep odom
ros2 topic echo /odom --once
```

如果没有 `odom -> base_link`：

```bash
ros2 run tf2_ros tf2_echo odom base_link
```

如果 `rf2o` 不工作，检查：

```bash
ros2 topic echo /scan --once
ros2 run tf2_ros tf2_echo base_link laser
```

如果地图乱飞，通常是因为：

- 雷达移动太快
- 雷达倾斜
- 环境特征太少
- 手抖太明显
- `/scan` 频率不稳定
- `rf2o` 估计的 `/odom` 漂移

这种情况下先不要追求完美地图。手持建图的目标是验证完整链路：

```text
/scan -> /odom -> /map -> 保存地图
```

到这里，**阶段 1 完成**。

---

# 13. 建图前必须确认底盘是否准备好

从这里开始，已经不只是雷达了，还需要机器人底盘。

建图需要机器人在环境中移动，所以你必须先启动你的底盘驱动。

我不知道你的底盘具体型号，所以这里写成：

```text
启动你的底盘 bringup
```

你要把它替换成你实际底盘的启动命令。

底盘启动后，必须检查 3 件事。

---

## 13.1 检查 `/odom`

执行：

```bash
ros2 topic list | grep odom
```

你应该看到：

```text
/odom
```

再执行：

```bash
ros2 topic echo /odom --once
```

能看到数据，说明里程计话题存在。

---

## 13.2 检查 `odom -> base_link`

执行：

```bash
ros2 run tf2_ros tf2_echo odom base_link
```

如果持续输出平移和旋转数据，说明 TF 正常。

如果报错：

```text
Invalid frame ID "odom"
Invalid frame ID "base_link"
```

说明你的底盘 TF 还没正常发布。

---

## 13.3 检查 `/cmd_vel`

执行：

```bash
ros2 topic info /cmd_vel
```

如果能看到类型：

```text
geometry_msgs/msg/Twist
```

说明速度控制话题存在。

如果你确定周围安全，可以做一个非常小的运动测试。

让机器人慢慢往前动一下：

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.03, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

马上停止：

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

如果底盘不动，先不要继续 Nav2。

---

# 14. 发布雷达和底盘之间的 TF

ROS 需要知道雷达安装在机器人哪里。

假设：

- 机器人底盘坐标系叫 `base_link`
- 雷达坐标系叫 `laser`
- 雷达安装在车体中心前方 10 cm
- 雷达高度 12 cm

打开一个新终端，称为 **终端 4：雷达 TF 终端**。

执行：

```bash
source /opt/ros/jazzy/setup.bash

ros2 run tf2_ros static_transform_publisher \
  --x 0.10 --y 0.00 --z 0.12 \
  --roll 0.0 --pitch 0.0 --yaw 0.0 \
  --frame-id base_link \
  --child-frame-id laser
```

这个终端也不要关闭。

检查：

```bash
ros2 run tf2_ros tf2_echo base_link laser
```

如果能输出数据，说明 `base_link -> laser` 成功。

如果你的机器人已经通过 URDF 发布了 `base_link -> laser`，这一章可以跳过。

---

# 15. 创建 slam_toolbox 建图参数文件

执行：

```bash
mkdir -p ~/a1_lidar_ws/config
```

创建参数文件：

```bash
cat > ~/a1_lidar_ws/config/a1_slam_toolbox.yaml <<'EOF'
slam_toolbox:
  ros__parameters:
    use_sim_time: false
    odom_frame: odom
    map_frame: map
    base_frame: base_link
    scan_topic: /scan
    mode: mapping
    resolution: 0.05
    max_laser_range: 12.0
    minimum_time_interval: 0.2
    transform_timeout: 0.2
    tf_buffer_duration: 30.0
    throttle_scans: 1
    solver_plugin: solver_plugins::CeresSolver
    ceres_linear_solver: SPARSE_NORMAL_CHOLESKY
    ceres_preconditioner: SCHUR_JACOBI
    ceres_trust_strategy: LEVENBERG_MARQUARDT
    ceres_dogleg_type: TRADITIONAL_DOGLEG
    ceres_loss_function: None
EOF
```

确认文件存在：

```bash
cat ~/a1_lidar_ws/config/a1_slam_toolbox.yaml
```

---

# 16. 启动建图

建图时你应该已经有这些终端在运行：

```text
终端 1：A1 雷达驱动，提供 /scan
终端 4：base_link -> laser 静态 TF
你的底盘终端：提供 /odom、/cmd_vel、odom -> base_link
```

再打开一个新终端，称为 **终端 5：建图终端**。

执行：

```bash
source /opt/ros/jazzy/setup.bash
source ~/a1_lidar_ws/install/setup.bash

ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=~/a1_lidar_ws/config/a1_slam_toolbox.yaml \
  use_sim_time:=false
```

成功后，slam_toolbox 会开始等待雷达和 TF 数据。

不要关闭这个终端。

---

# 17. 在 RViz2 中查看建图

如果 RViz 已经打开，可以继续用。

如果没打开，新开终端：

```bash
source /opt/ros/jazzy/setup.bash
rviz2
```

RViz 中设置：

1. `Fixed Frame` 改成：`map`
2. 点 `Add`
3. 添加 `Map`，话题选择 `/map`
4. 添加 `LaserScan`，话题选择 `/scan`
5. 添加 `TF`

如果正常，你应该看到：

- 雷达扫描点
- 地图逐渐生成
- TF 树里有 `map`、`odom`、`base_link`、`laser`

然后慢慢遥控机器人移动。

建图建议：

- 速度慢一点
- 不要原地快速旋转
- 尽量沿墙走
- 尽量回到起点形成闭环
- 不要在纯玻璃、纯白墙、空旷环境里测试

---

# 18. 保存地图

当地图看起来完整后，新开一个终端，执行：

```bash
source /opt/ros/jazzy/setup.bash
mkdir -p ~/maps
ros2 run nav2_map_server map_saver_cli -f ~/maps/a1_map
```

成功后检查：

```bash
ls -lh ~/maps/a1_map.*
```

你应该看到两个文件：

```text
a1_map.yaml
a1_map.pgm
```

这两个文件就是导航要用的地图。

到这里，**阶段 3 完成**。

---

# 19. 导航前关闭建图节点

导航时不再运行建图节点。

你需要关闭：

```text
slam_toolbox 建图终端
```

一般按：

```text
Ctrl + C
```

但这些还要继续运行：

```text
A1 雷达驱动
底盘驱动
base_link -> laser TF
```

---

# 20. 准备 Nav2 参数文件

先用 Nav2 默认参数作为基础：

```bash
mkdir -p ~/a1_lidar_ws/config
cp /opt/ros/jazzy/share/nav2_bringup/params/nav2_params.yaml \
  ~/a1_lidar_ws/config/a1_nav2_params.yaml
```

先不要急着大改参数。

默认参数通常已经使用这些名字：

```text
map
odom
base_link
scan
cmd_vel
```

这和本文前面使用的名字基本一致。

如果后面 Nav2 收不到雷达，再回来修改这个文件里的 `scan_topic` 或 costmap 的 `topic`。

---

# 21. 启动 Nav2 导航

此时你应该已经有这些在运行：

```text
A1 雷达驱动：发布 /scan
底盘驱动：发布 /odom，接收 /cmd_vel
雷达 TF：base_link -> laser
```

打开一个新终端，称为 **终端 6：Nav2 终端**。

执行：

```bash
source /opt/ros/jazzy/setup.bash
source ~/a1_lidar_ws/install/setup.bash

ros2 launch nav2_bringup bringup_launch.py \
  use_sim_time:=false \
  map:=~/maps/a1_map.yaml \
  params_file:=~/a1_lidar_ws/config/a1_nav2_params.yaml
```

启动后不要关闭。

---

# 22. 用 RViz2 发送导航目标

新开终端，或者用已经打开的 RViz。

推荐用 Nav2 自带 RViz 配置：

```bash
source /opt/ros/jazzy/setup.bash
rviz2 -d /opt/ros/jazzy/share/nav2_bringup/rviz/nav2_default_view.rviz
```

RViz 打开后：

1. 确认 `Fixed Frame` 是 `map`
2. 确认地图显示出来
3. 确认能看到机器人位置
4. 点击顶部工具栏 `2D Pose Estimate`
5. 在地图上点一下机器人当前真实位置，并拖出朝向
6. 等一会儿，让 AMCL 定位稳定
7. 点击 `Nav2 Goal`
8. 在地图上点目标位置，并拖出目标朝向

正常情况下：

- RViz 会出现规划路径
- Nav2 会发布 `/cmd_vel`
- 机器人开始移动

检查 Nav2 是否在发速度：

```bash
ros2 topic echo /cmd_vel
```

如果 `/cmd_vel` 有数据但机器人不动，问题在底盘驱动或底盘订阅话题。

---

# 23. 每次重新开机后的最简启动顺序

以后不用每次重新编译。

每次使用时按这个顺序开终端。

## 23.0 WSL2 断电、拔插雷达、重启电脑后的重连流程

如果你使用的是 WSL2，每次断电、拔插 A1 雷达、重启电脑、关闭 WSL 后，通常需要重新把 USB 设备挂载进 WSL。

第一步，在 Windows PowerShell 管理员窗口查看雷达：

```powershell
usbipd list
```

找到 A1 雷达这一行，例如：

```text
3-3    10c4:ea60  Silicon Labs CP210x USB to UART Bridge (COM15)
```

如果状态不是 `Attached`，执行：

```powershell
usbipd attach --wsl --busid 3-3
```

这里的 `3-3` 要换成你自己 `usbipd list` 里看到的 `BUSID`。

第二步，回到 Ubuntu 终端检查设备：

```bash
lsusb
ls -l /dev/ttyUSB*
```

如果能看到 `10c4:ea60`，但没有 `/dev/ttyUSB0`，执行：

```bash
sudo modprobe usbserial
sudo modprobe cp210x
ls -l /dev/ttyUSB*
```

第三步，给串口权限：

```bash
sudo chmod 666 /dev/ttyUSB0
```

第四步，启动 A1 雷达驱动：

```bash
source /opt/ros/jazzy/setup.bash
source ~/a1_lidar_ws/install/setup.bash

ros2 run sllidar_ros2 sllidar_node --ros-args \
  -p serial_port:=/dev/ttyUSB0 \
  -p serial_baudrate:=115200 \
  -p frame_id:=laser \
  -p inverted:=false \
  -p angle_compensate:=true
```

第五步，新开一个 Ubuntu 终端，启动 RViz：

```bash
source /opt/ros/jazzy/setup.bash
source ~/a1_lidar_ws/install/setup.bash
rviz2
```

RViz 中设置：

```text
Fixed Frame: laser
Add -> By topic -> /scan -> LaserScan
```

如果 RViz 里看不到点，先检查：

```bash
ros2 topic list
ros2 topic echo /scan --once
ros2 topic hz /scan
```

如果 `/scan` 正常，说明雷达已经连上，问题只在 RViz 显示设置。

## 终端 1：启动底盘

运行你的底盘启动命令。

要求它提供：

```text
/odom
/cmd_vel
odom -> base_link
```

## 终端 2：启动 A1 雷达

```bash
source /opt/ros/jazzy/setup.bash
source ~/a1_lidar_ws/install/setup.bash

ros2 run sllidar_ros2 sllidar_node --ros-args \
  -p serial_port:=/dev/rplidar \
  -p serial_baudrate:=115200 \
  -p frame_id:=laser \
  -p inverted:=false \
  -p angle_compensate:=true
```

## 终端 3：启动雷达 TF

```bash
source /opt/ros/jazzy/setup.bash

ros2 run tf2_ros static_transform_publisher \
  --x 0.10 --y 0.00 --z 0.12 \
  --roll 0.0 --pitch 0.0 --yaw 0.0 \
  --frame-id base_link \
  --child-frame-id laser
```

## 如果要建图，终端 4 启动 slam_toolbox

```bash
source /opt/ros/jazzy/setup.bash
source ~/a1_lidar_ws/install/setup.bash

ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=~/a1_lidar_ws/config/a1_slam_toolbox.yaml \
  use_sim_time:=false
```

## 如果要导航，终端 4 启动 Nav2

```bash
source /opt/ros/jazzy/setup.bash
source ~/a1_lidar_ws/install/setup.bash

ros2 launch nav2_bringup bringup_launch.py \
  use_sim_time:=false \
  map:=~/maps/a1_map.yaml \
  params_file:=~/a1_lidar_ws/config/a1_nav2_params.yaml
```

## 终端 5：打开 RViz

```bash
source /opt/ros/jazzy/setup.bash
rviz2
```

---

# 24. 你每一步成功的判断标准

## 雷达成功

```bash
ros2 topic echo /scan --once
```

能看到 `ranges` 数据。

## 雷达到车体 TF 成功

```bash
ros2 run tf2_ros tf2_echo base_link laser
```

能持续输出变换。

## 底盘里程计成功

```bash
ros2 topic echo /odom --once
```

能看到数据。

## 底盘 TF 成功

```bash
ros2 run tf2_ros tf2_echo odom base_link
```

能持续输出变换。

## 建图成功

```bash
ros2 topic echo /map --once
```

能看到地图数据，RViz 里地图会逐渐变大。

## 地图保存成功

```bash
ls -lh ~/maps/a1_map.*
```

能看到：

```text
a1_map.yaml
a1_map.pgm
```

## Nav2 成功

```bash
ros2 topic echo /cmd_vel
```

发送目标点后 `/cmd_vel` 有速度数据，机器人开始动。

---

# 25. 常见错误直接看这里

## 25.1 找不到 `sllidar_node`

检查：

```bash
source ~/a1_lidar_ws/install/setup.bash
ros2 pkg executables sllidar_ros2
```

如果没有输出，重新编译：

```bash
cd ~/a1_lidar_ws
colcon build --symlink-install
source install/setup.bash
```

## 25.2 没有 `/dev/rplidar`

先用这个检查：

```bash
ls -l /dev/ttyUSB*
```

如果有 `/dev/ttyUSB0`，启动雷达时临时改成：

```text
serial_port:=/dev/ttyUSB0
```

## 25.3 雷达启动失败

重点检查：

```bash
ls -l /dev/rplidar
ls -l /dev/ttyUSB*
groups
```

A1 必须用：

```text
serial_baudrate:=115200
```

不要用 A3、S1、S2 的波特率。

## 25.4 RViz 看不到雷达

先把 RViz 的 Fixed Frame 设置成：

```text
laser
```

然后添加 `/scan`。

如果这样能看到，说明雷达没问题，只是 TF 还没配置好。

## 25.5 slam_toolbox 报 TF 错误

检查这两个：

```bash
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link laser
```

两个都必须正常。

## 25.6 Nav2 不规划路径

检查：

```bash
ros2 topic echo /scan --once
ros2 topic echo /odom --once
ros2 run tf2_ros tf2_echo map odom
ros2 run tf2_ros tf2_echo odom base_link
```

还要确认 RViz 里已经点了：

```text
2D Pose Estimate
```

如果没给初始位姿，Nav2 通常不知道机器人在哪里。

## 25.7 Nav2 有路径但机器人不动

检查：

```bash
ros2 topic echo /cmd_vel
```

如果 `/cmd_vel` 有数据但机器人不动，说明 Nav2 没问题，问题在底盘控制。

可能是：

- 底盘不订阅 `/cmd_vel`
- 底盘使用了别的话题名
- 底盘急停没解除
- 电机驱动没启动
- 速度太小

---

# 26. 你现在应该按什么顺序做

如果你是第一次做，严格按下面顺序来：

```text
1. 创建 ~/a1_lidar_ws
2. 获取 sllidar_ros2 驱动
3. colcon build 编译
4. 插上 A1 雷达
5. 固定 /dev/rplidar
6. 启动 sllidar_node
7. 检查 /scan
8. RViz 看到雷达点
9. 启动底盘，确认 /odom、/cmd_vel
10. 发布 base_link -> laser
11. 启动 slam_toolbox
12. RViz 看地图
13. 保存地图
14. 关闭 slam_toolbox
15. 启动 Nav2
16. RViz 设置初始位姿
17. 发送 Nav2 Goal
```

建议你不要一次跳到导航。

先完成第 1 到第 8 步，确认 A1 雷达完全正常。

---

# 27. 如果你卡住了，应该把什么发给我

如果你操作中失败，不要只说“报错了”。

请把下面命令的输出发给我：

```bash
ros2 pkg executables sllidar_ros2
ls -l /dev/rplidar
ls -l /dev/ttyUSB*
ros2 topic list
ros2 topic info /scan
ros2 run tf2_ros tf2_echo base_link laser
ros2 topic echo /odom --once
ros2 run tf2_ros tf2_echo odom base_link
```

如果是编译失败，把下面命令的完整输出发给我：

```bash
cd ~/a1_lidar_ws
colcon build --symlink-install
```

---

# 28. 最核心的一句话

你真正要跑通的是这 5 个东西：

```text
/scan
/odom
/cmd_vel
odom -> base_link
base_link -> laser
```

这 5 个都正常后：

```text
slam_toolbox 才能建图
Nav2 才能导航
```

---

# 29. 在 VS Code 中开发这个 ROS 2 工作区

如果你使用的是 Windows + WSL2，推荐开发方式是：

```text
Windows 安装 VS Code
VS Code 通过 WSL 扩展打开 Ubuntu 里的 ~/a1_lidar_ws
所有 ROS2 编译和运行命令都在 VS Code 的 WSL 终端中执行
```

不要直接用 Windows 路径去编辑 ROS2 工作区，例如不要把工作区放在：

```text
/mnt/c/Users/...
```

推荐放在：

```text
~/a1_lidar_ws
```

也就是：

```text
/home/cgz/a1_lidar_ws
```

## 29.1 安装 VS Code 必要扩展

在 Windows 的 VS Code 里安装这些扩展：

```text
WSL
C/C++
CMake Tools
Python
YAML
XML
ROS
```

最关键的是 `WSL` 扩展。没有它，VS Code 不能方便地进入 Ubuntu 环境。

## 29.2 从 Ubuntu 终端打开 VS Code

打开 Ubuntu/WSL 终端：

```bash
cd ~/a1_lidar_ws
code .
```

第一次执行 `code .` 时，VS Code 会自动安装 WSL Server。

打开成功后，VS Code 左下角应该显示类似：

```text
WSL: Ubuntu
```

这说明你现在编辑的是 WSL 里的 ROS2 工作区。

## 29.3 VS Code 里的终端

在 VS Code 里打开终端：

```text
Terminal -> New Terminal
```

确认终端提示符类似：

```text
cgz@LAPTOP-K1Q2IO34:~/a1_lidar_ws$
```

然后执行：

```bash
source /opt/ros/jazzy/setup.bash
source ~/a1_lidar_ws/install/setup.bash
```

以后编译：

```bash
cd ~/a1_lidar_ws
colcon build --symlink-install
source install/setup.bash
```

## 29.4 VS Code 中推荐打开的目录

推荐打开整个工作区：

```text
~/a1_lidar_ws
```

不要只打开：

```text
~/a1_lidar_ws/src/sllidar_ros2
```

因为 ROS2 编译需要从工作区根目录执行 `colcon build`。

## 29.5 常用文件位置

当前工作区里常用文件大概是：

```text
~/a1_lidar_ws/src/sllidar_ros2
~/a1_lidar_ws/src/rf2o_laser_odometry
~/a1_lidar_ws/config/a1_handheld_slam_toolbox.yaml
~/maps/a1_handheld_map.yaml
~/maps/a1_handheld_map.pgm
```

如果以后你自己写 launch 文件，建议放在：

```text
~/a1_lidar_ws/src/你的包名/launch/
```

如果以后你自己写参数文件，建议放在：

```text
~/a1_lidar_ws/config/
```

## 29.6 VS Code 中启动雷达和建图

VS Code 里可以开多个终端，每个终端分别跑一个节点。

例如：

```text
终端 1：sllidar_node
终端 2：static_transform_publisher
终端 3：rf2o_laser_odometry
终端 4：slam_toolbox
终端 5：rviz2
```

注意：WSL2 下每次断电或重启后，还是要先在 Windows PowerShell 里执行：

```powershell
usbipd list
usbipd attach --wsl --busid 你的BUSID
```

然后回到 VS Code 的 WSL 终端执行：

```bash
lsusb
ls -l /dev/ttyUSB*
sudo chmod 666 /dev/ttyUSB0
```

## 29.7 建议创建一个 `.vscode` 配置

你可以在 VS Code 中创建：

```text
~/a1_lidar_ws/.vscode/settings.json
```

写入：

```json
{
  "terminal.integrated.defaultProfile.linux": "bash",
  "cmake.configureOnOpen": false,
  "files.associations": {
    "*.launch.py": "python",
    "*.yaml": "yaml",
    "*.urdf": "xml",
    "*.xacro": "xml"
  }
}
```

这个配置可以让 VS Code 更适合 ROS2 工作区开发。

## 29.8 最推荐的开发习惯

建议你以后这样工作：

```text
1. Windows PowerShell 负责 usbipd 挂载雷达
2. VS Code 通过 WSL 打开 ~/a1_lidar_ws
3. VS Code 终端里编译和运行 ROS2 命令
4. 地图和配置文件保存在 Ubuntu 的 home 目录
5. 不要在 /mnt/c 下编译 ROS2 工作区
```

这样最稳定，也最接近真实 Ubuntu ROS2 开发环境。

## 29.9 一键启动手持建图的 bringup 包

现在已经在 WSL 的 ROS2 工作区中创建了一个新包：

```text
~/a1_lidar_ws/src/a1_lidar_bringup
```

这个包用于一键启动手持建图流程，包括：

```text
sllidar_node
base_link -> laser 静态 TF
rf2o_laser_odometry
slam_toolbox
可选 rviz2
```

包内主要文件是：

```text
~/a1_lidar_ws/src/a1_lidar_bringup/package.xml
~/a1_lidar_ws/src/a1_lidar_bringup/setup.py
~/a1_lidar_ws/src/a1_lidar_bringup/launch/a1_handheld_mapping.launch.py
~/a1_lidar_ws/src/a1_lidar_bringup/config/a1_handheld_slam_toolbox.yaml
```

编译：

```bash
cd ~/a1_lidar_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select a1_lidar_bringup
source install/setup.bash
```

查看启动参数：

```bash
ros2 launch a1_lidar_bringup a1_handheld_mapping.launch.py --show-args
```

每次使用前，WSL2 仍然要先确认雷达串口：

```bash
ls -l /dev/ttyUSB*
sudo chmod 666 /dev/ttyUSB0
```

一键启动手持建图：

```bash
source /opt/ros/jazzy/setup.bash
source ~/a1_lidar_ws/install/setup.bash

ros2 launch a1_lidar_bringup a1_handheld_mapping.launch.py
```

如果想同时打开 RViz：

```bash
ros2 launch a1_lidar_bringup a1_handheld_mapping.launch.py rviz:=true
```

默认参数是：

```text
serial_port: /dev/ttyUSB0
serial_baudrate: 115200
scan_frame: laser
base_frame: base_link
odom_frame: odom
scan_topic: /scan
odom_topic: /odom
use_sim_time: false
```

如果你的串口变成 `/dev/ttyUSB1`，可以这样启动：

```bash
ros2 launch a1_lidar_bringup a1_handheld_mapping.launch.py serial_port:=/dev/ttyUSB1
```

启动后检查：

```bash
ros2 topic echo /scan --once
ros2 topic echo /odom --once
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link laser
```

如果都正常，就可以在 RViz 中查看：

```text
Fixed Frame: map
Map: /map
LaserScan: /scan
TF
```

地图完成后保存：

```bash
mkdir -p ~/maps
ros2 run nav2_map_server map_saver_cli -f ~/maps/a1_handheld_map
```
