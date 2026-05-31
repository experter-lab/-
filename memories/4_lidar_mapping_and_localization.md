# 记忆库备份：激光雷达驱动、激光里程计、SLAM 建图与 AMCL 定位 (Lidar, Mapping and Localization)

## 1. 激光雷达 (RPLIDAR A1)
- **物理接口**：固定挂载于 `/dev/rplidar`（软链接指向串口板 `/dev/ttyUSB0`）。
- **驱动功能包**：`sllidar_ros2`。
- **采集频率**：扫描频率稳定在 `7-8Hz`，发布话题 `/scan`（标准 `sensor_msgs/LaserScan`），坐标系 `laser`。
- **物理标定 (TF)**：
  - 静态坐标变换由 `base_link` 指向 `laser`（`x=0.10, y=0.0, z=0.12`，单位：米）。
  - 启动文件：`medicine_robot_bringup/launch/rk3588_lidar_bringup.launch.py`。
  - *注意*：由于 Humble/Jazzy 与 sllidar 官方旧 SDK 的 C++ 兼容性差异，已在板端和工作空间内对其进行过源码修补（主要包括 `net_socket.cpp` 指针与整数比较问题以及 ROS2 参数默认显式声明）。

## 2. 激光里程计 (rf2o_laser_odometry)
在小车缺少高精度轮速编码器的现阶段，为了给导航和定位提供连贯的相对位姿估计，采用二维激光里程计：
- **源码路径**：`/mnt/sdcard/medicine_robot_ws/src/rf2o_laser_odometry`。
- **适配修补**：
  - 移除了 CMake 中不必要的原生 Boost 库物理依赖，规避了 ARM64 下的库编译报错。
  - 将 `init_pose_from_topic` 默认设置为空字符串，避免初始化阶段卡死。
  - 初始化阶段强制设定初始四元数首位 `orientation.w = 1.0`。
- **启动与输出**：
  - 读取激光扫描 `/scan` 话题，发布 `/odom` 话题，并发布从坐标系 `odom` 到 `base_link` 的 TF 动态变换。
  - 采样与发布频率稳定在 `7.0Hz`。

## 3. SLAM 建图 (slam_toolbox)
- **建图工具**：`ros-humble-slam-toolbox`（替代高内存损耗的 Cartographer，在 RK3588 上低耗、表现极其稳定）。
- **建图配置**：已优化定制手持式建图配置文件，物理路径为 `/mnt/sdcard/medicine_robot_data/config/a1_handheld_slam_toolbox.yaml`。
- **地图保存脚本**：`/mnt/sdcard/rk3588_save_handheld_map.sh`。
  - *技术注意*：此脚本内部采用 `set -eo pipefail`，并显式排除了 `set -u` 以防止与 ROS 2 Ament 环境变量加载系统产生语法冲突。
- **当前保存的地图**：
  - 最新物理 2D 栅格地图已被持久化保存至 `/mnt/sdcard/medicine_robot_data/maps/a1_handheld_map_latest.yaml` 与 `.pgm`。
  - 地图物理分辨率：`0.05m/pixel`。
  - 地图起点坐标（Origin）：`[-1.18, -0.572, 0.0]`。

## 4. AMCL 蒙特卡洛定位与一键启动
- **定位算法**：`ros-humble-navigation2` 内置的 `nav2_amcl` (自适应蒙特卡洛定位算法)。
- **定位配置文件**：`/mnt/sdcard/medicine_robot_data/config/rk3588_amcl_localization.yaml`。
- **一键启动与状态自检系统**：
  - **整车一键定位协议栈脚本**：`/mnt/sdcard/rk3588_start_localization_stack.sh`（一键自适应顺序拉起雷达驱动、雷达静态 TF、rf2o 激光里程计、Map Server 地图加载服务，并激活 AMCL 粒子滤波闭环定位）。
  - **稳定性健康监测脚本**：`/mnt/sdcard/rk3588_check_localization_status.sh`。此脚本能自动化探测各传感器子节点生命状态、动态检查 `/scan` `/odom` `/map` `/amcl_pose` 的发布频次，并精确计算 `map -> odom -> base_link -> laser` 整个 TF 树的拓扑连通完备性。
