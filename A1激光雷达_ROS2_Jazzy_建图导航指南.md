# A1 激光雷达在 Ubuntu 24.04 + ROS 2 Jazzy 下建图与导航指南

本文面向你当前的状态：**Ubuntu 24.04 + ROS 2 Jazzy 已经搭好**，不再展开虚拟机、系统镜像、ROS 安装等环境搭建内容。

目标是把 A1 激光雷达接入 ROS 2，得到 `/scan`，再用 `slam_toolbox` 建图、保存地图，最后用 Nav2 做自主导航。

## 1. 从 A1 资料中提取到的有用信息

本地 `A1` 资料中，与 ROS 2 建图导航直接相关的内容主要是：

- **ROS 2 雷达驱动源码包**：`附录/4.功能源码包/rplidar_ros2_ws.zip`
- **驱动包名称**：`sllidar_ros2`
- **支持型号**：RPLIDAR A1、A2、A3、S1、S2 等
- **A1/A2 启动文件**：`sllidar_launch.py` 或 `view_sllidar_launch.py`
- **A1/A2 串口波特率**：`115200`
- **默认串口**：`/dev/ttyUSB0`
- **推荐固定设备名**：`/dev/rplidar`
- **雷达坐标系 frame_id**：资料里的 launch 默认是 `laser`
- **发布话题**：`/scan`
- **消息类型**：`sensor_msgs/msg/LaserScan`
- **驱动服务**：`/start_motor`、`/stop_motor`
- **udev 规则识别码**：`idVendor=10c4`，`idProduct=ea60`

资料里的 ROS 2 包偏旧，部分 launch 文件使用了旧字段 `node_executable`、`node_name`。在 ROS 2 Jazzy 中如果 launch 报错，优先用本文里的 `ros2 run ... --ros-args -p ...` 方式启动，或把旧字段改成 Jazzy 支持的 `executable`、`name`。

## 2. 你需要先确认的关键事实

A1 激光雷达本身只提供二维激光扫描数据，它不能单独完成完整导航。

完整建图和导航至少需要这些 ROS 数据链路：

- **激光雷达**：发布 `/scan`
- **雷达 TF**：存在 `base_link -> laser`
- **里程计**：存在 `/odom` 话题
- **里程计 TF**：存在 `odom -> base_link`
- **底盘控制**：机器人能接收 `/cmd_vel`
- **建图输出**：SLAM 发布 `map -> odom`
- **导航输入**：Nav2 使用地图、TF、`/scan`、`/odom`

如果你现在只有一个 A1 雷达，没有移动底盘、没有 `/odom`、没有 `/cmd_vel`，那么可以做到：

- 查看雷达扫描
- 录制 `/scan`
- 做静态障碍物感知测试

但不能直接完成可靠的自主导航。

## 3. 推荐工作区结构

建议在 Ubuntu 上单独建一个雷达工作区：

```bash
mkdir -p ~/a1_lidar_ws/src
cd ~/a1_lidar_ws
```

如果你要使用 A1 资料里的本地源码包，把 `rplidar_ros2_ws.zip` 复制到 Ubuntu，例如放到 `~/Downloads/rplidar_ros2_ws.zip`。

然后解压出 `sllidar_ros2`：

```bash
cd ~/a1_lidar_ws
mkdir -p /tmp/a1_rplidar_src
unzip ~/Downloads/rplidar_ros2_ws.zip -d /tmp/a1_rplidar_src
cp -r /tmp/a1_rplidar_src/rplidar_ros2_ws/src/sllidar_ros2 ~/a1_lidar_ws/src/
```

如果你更希望使用官方较新的驱动，也可以直接克隆：

```bash
cd ~/a1_lidar_ws/src
git clone https://github.com/Slamtec/sllidar_ros2.git
```

## 4. 编译 `sllidar_ros2`

```bash
source /opt/ros/jazzy/setup.bash
cd ~/a1_lidar_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

如果你不想每次手动 source，可以加入 `.bashrc`：

```bash
echo "source ~/a1_lidar_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

## 5. 固定 A1 雷达设备名为 `/dev/rplidar`

A1 资料中提供的规则是把 `ttyUSB*` 固定映射为 `/dev/rplidar`。推荐你在 Ubuntu 上创建 udev 规则：

```bash
sudo tee /etc/udev/rules.d/rplidar.rules >/dev/null <<'EOF'
KERNEL=="ttyUSB*", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE:="0666", SYMLINK+="rplidar"
EOF

sudo udevadm control --reload-rules
sudo udevadm trigger
```

拔插一次雷达后检查：

```bash
lsusb
ls -l /dev/rplidar
ls -l /dev/ttyUSB*
```

如果没有 `/dev/rplidar`，先看系统是否识别到了 USB 串口：

```bash
dmesg | grep -i tty
```

如果权限不够，也可以把当前用户加入 `dialout` 组，然后注销重登：

```bash
sudo usermod -aG dialout $USER
```

## 6. 启动 A1 雷达并发布 `/scan`

资料中 A1/A2 使用的关键参数是：

- `serial_port:=/dev/ttyUSB0` 或 `/dev/rplidar`
- `serial_baudrate:=115200`
- `frame_id:=laser`
- `angle_compensate:=true`

推荐优先用固定设备名 `/dev/rplidar`：

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

如果你确认本地 launch 文件在 Jazzy 下可用，也可以使用：

```bash
ros2 launch sllidar_ros2 sllidar_launch.py \
  serial_port:=/dev/rplidar \
  serial_baudrate:=115200 \
  frame_id:=laser \
  inverted:=false \
  angle_compensate:=true
```

带 RViz 的方式：

```bash
ros2 launch sllidar_ros2 view_sllidar_launch.py \
  serial_port:=/dev/rplidar \
  serial_baudrate:=115200 \
  frame_id:=laser
```

如果 Jazzy 报类似下面的错误：

```text
Node.__init__() got an unexpected keyword argument 'node_executable'
```

说明资料里的 launch 文件太旧。解决办法有两个：

- **临时办法**：直接用上面的 `ros2 run sllidar_ros2 sllidar_node --ros-args ...`
- **修复 launch**：把 launch 文件中的 `node_executable` 改成 `executable`，`node_name` 改成 `name`

## 7. 验证 `/scan` 是否正常

另开一个终端：

```bash
source /opt/ros/jazzy/setup.bash
source ~/a1_lidar_ws/install/setup.bash

ros2 topic list
ros2 topic info /scan
ros2 topic echo /scan --once
ros2 topic hz /scan
```

你应该看到：

- `/scan` 存在
- 类型是 `sensor_msgs/msg/LaserScan`
- `header.frame_id` 是 `laser`
- 频率通常在几 Hz 到十几 Hz 左右
- `ranges` 中有非 `inf` 的距离数据

用 RViz2 检查：

```bash
rviz2
```

RViz 中设置：

- **Fixed Frame**：先设为 `laser`
- **Add**：添加 `LaserScan`
- **Topic**：选择 `/scan`

如果能看到一圈扫描点，说明雷达接入成功。

## 8. 建立雷达到车体的静态 TF

建图和导航通常不能只用 `laser` 作为孤立坐标系，需要告诉 ROS：雷达安装在机器人底盘的哪个位置。

假设你的机器人车体坐标系是 `base_link`，雷达坐标系是 `laser`，雷达位于车体中心前方 `0.10m`、高度 `0.12m`，可以先临时发布静态 TF：

```bash
ros2 run tf2_ros static_transform_publisher \
  --x 0.10 --y 0.00 --z 0.12 \
  --roll 0.0 --pitch 0.0 --yaw 0.0 \
  --frame-id base_link \
  --child-frame-id laser
```

实际项目中应根据你的真实安装位置修改 `x/y/z/roll/pitch/yaw`。

检查 TF：

```bash
ros2 run tf2_ros tf2_echo base_link laser
```

如果你的机器人已经有 URDF 和 `robot_state_publisher`，推荐把雷达作为一个 link 写进 URDF，不要长期依赖手动静态 TF 命令。

## 9. 建图前检查底盘数据

在运行 SLAM 前，确认底盘已经提供这些内容。

检查 `/odom`：

```bash
ros2 topic echo /odom --once
```

检查 `odom -> base_link`：

```bash
ros2 run tf2_ros tf2_echo odom base_link
```

检查 `/cmd_vel` 是否能控制底盘：

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.05, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

测试后立刻发停止：

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

如果没有 `/odom` 或 `odom -> base_link`，`slam_toolbox` 和 Nav2 通常都会报 TF 错误或无法正常工作。

## 10. 使用 `slam_toolbox` 建图

如果你已经安装了 `slam_toolbox`，可以跳过安装命令。否则安装：

```bash
sudo apt update
sudo apt install ros-jazzy-slam-toolbox
```

创建参数文件：

```bash
mkdir -p ~/a1_lidar_ws/config
nano ~/a1_lidar_ws/config/a1_slam_toolbox.yaml
```

写入：

```yaml
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
```

启动顺序建议如下。

终端 1：启动底盘驱动，让 `/odom`、`odom -> base_link`、`/cmd_vel` 可用。

```bash
# 这里运行你自己的底盘 bringup
```

终端 2：启动 A1 雷达。

```bash
source /opt/ros/jazzy/setup.bash
source ~/a1_lidar_ws/install/setup.bash

ros2 run sllidar_ros2 sllidar_node --ros-args \
  -p serial_port:=/dev/rplidar \
  -p serial_baudrate:=115200 \
  -p frame_id:=laser \
  -p angle_compensate:=true
```

终端 3：发布雷达静态 TF，除非你的 URDF 已经发布了 `base_link -> laser`。

```bash
ros2 run tf2_ros static_transform_publisher \
  --x 0.10 --y 0.00 --z 0.12 \
  --roll 0.0 --pitch 0.0 --yaw 0.0 \
  --frame-id base_link \
  --child-frame-id laser
```

终端 4：启动建图。

```bash
source /opt/ros/jazzy/setup.bash
source ~/a1_lidar_ws/install/setup.bash

ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=~/a1_lidar_ws/config/a1_slam_toolbox.yaml \
  use_sim_time:=false
```

终端 5：打开 RViz。

```bash
rviz2
```

RViz 建议设置：

- **Fixed Frame**：`map`
- **Add / Map**：显示 `/map`
- **Add / LaserScan**：显示 `/scan`
- **Add / TF**：查看 `map`、`odom`、`base_link`、`laser`

然后缓慢遥控机器人移动，让雷达扫描覆盖环境。

## 11. 保存地图

建图完成后，安装或确认 `nav2_map_server` 可用：

```bash
sudo apt install ros-jazzy-nav2-map-server
```

保存地图：

```bash
mkdir -p ~/maps
ros2 run nav2_map_server map_saver_cli -f ~/maps/a1_map
```

成功后会生成：

```text
~/maps/a1_map.yaml
~/maps/a1_map.pgm
```

检查地图文件：

```bash
ls -lh ~/maps/a1_map.*
cat ~/maps/a1_map.yaml
```

## 12. 使用 Nav2 做导航

Nav2 需要这些输入正常：

- `/map`
- `/scan`
- `/odom`
- `/cmd_vel`
- `map -> odom`
- `odom -> base_link`
- `base_link -> laser`

安装 Nav2，如果已经安装可跳过：

```bash
sudo apt update
sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-bringup
```

创建 Nav2 参数文件，推荐先复制 Jazzy 默认参数再修改：

```bash
mkdir -p ~/a1_lidar_ws/config
cp /opt/ros/jazzy/share/nav2_bringup/params/nav2_params.yaml \
  ~/a1_lidar_ws/config/a1_nav2_params.yaml
nano ~/a1_lidar_ws/config/a1_nav2_params.yaml
```

重点检查或修改这些字段：

```yaml
amcl:
  ros__parameters:
    use_sim_time: false
    base_frame_id: "base_link"
    odom_frame_id: "odom"
    global_frame_id: "map"
    scan_topic: /scan

bt_navigator:
  ros__parameters:
    use_sim_time: false
    global_frame: map
    robot_base_frame: base_link
    odom_topic: /odom

controller_server:
  ros__parameters:
    use_sim_time: false

local_costmap:
  local_costmap:
    ros__parameters:
      use_sim_time: false
      global_frame: odom
      robot_base_frame: base_link
      update_frequency: 5.0
      publish_frequency: 2.0
      robot_radius: 0.18
      plugins: ["voxel_layer", "inflation_layer"]
      voxel_layer:
        plugin: "nav2_costmap_2d::VoxelLayer"
        enabled: true
        observation_sources: scan
        scan:
          topic: /scan
          max_obstacle_height: 2.0
          clearing: true
          marking: true
          data_type: "LaserScan"
          raytrace_max_range: 3.0
          raytrace_min_range: 0.0
          obstacle_max_range: 2.5
          obstacle_min_range: 0.0

global_costmap:
  global_costmap:
    ros__parameters:
      use_sim_time: false
      global_frame: map
      robot_base_frame: base_link
      update_frequency: 1.0
      publish_frequency: 1.0
      robot_radius: 0.18
      plugins: ["static_layer", "obstacle_layer", "inflation_layer"]
      obstacle_layer:
        plugin: "nav2_costmap_2d::ObstacleLayer"
        enabled: true
        observation_sources: scan
        scan:
          topic: /scan
          max_obstacle_height: 2.0
          clearing: true
          marking: true
          data_type: "LaserScan"
          raytrace_max_range: 3.0
          raytrace_min_range: 0.0
          obstacle_max_range: 2.5
          obstacle_min_range: 0.0
```

其中 `robot_radius` 要改成你机器人真实半径。如果机器人不是圆形，后续可以改成 `footprint` 多边形。

启动顺序如下。

终端 1：启动底盘。

```bash
# 运行你的底盘 bringup，确保 /odom、/cmd_vel、odom->base_link 正常
```

终端 2：启动 A1 雷达。

```bash
source /opt/ros/jazzy/setup.bash
source ~/a1_lidar_ws/install/setup.bash

ros2 run sllidar_ros2 sllidar_node --ros-args \
  -p serial_port:=/dev/rplidar \
  -p serial_baudrate:=115200 \
  -p frame_id:=laser \
  -p angle_compensate:=true
```

终端 3：发布 `base_link -> laser`，除非 URDF 已经发布。

```bash
ros2 run tf2_ros static_transform_publisher \
  --x 0.10 --y 0.00 --z 0.12 \
  --roll 0.0 --pitch 0.0 --yaw 0.0 \
  --frame-id base_link \
  --child-frame-id laser
```

终端 4：启动 Nav2。

```bash
source /opt/ros/jazzy/setup.bash
source ~/a1_lidar_ws/install/setup.bash

ros2 launch nav2_bringup bringup_launch.py \
  use_sim_time:=false \
  map:=~/maps/a1_map.yaml \
  params_file:=~/a1_lidar_ws/config/a1_nav2_params.yaml
```

终端 5：打开 RViz。

```bash
rviz2
```

RViz 操作顺序：

1. Fixed Frame 设置为 `map`
2. 添加 `Map`，话题选 `/map`
3. 添加 `LaserScan`，话题选 `/scan`
4. 添加 `TF`
5. 添加 Nav2 相关显示，或直接使用 Nav2 默认 RViz 配置
6. 点击 **2D Pose Estimate**，给机器人一个初始位姿
7. 点击 **Nav2 Goal**，给目标点

如果一切正常，Nav2 会规划路径，并通过 `/cmd_vel` 控制底盘移动。

## 13. 最小启动流程总结

每次使用时，最少需要这些终端。

### 建图流程

```text
终端 1：底盘 bringup，提供 /odom、/cmd_vel、odom->base_link
终端 2：A1 雷达驱动，提供 /scan
终端 3：base_link->laser 静态 TF 或 URDF
终端 4：slam_toolbox online_async_launch.py
终端 5：rviz2 查看地图并遥控建图
```

### 导航流程

```text
终端 1：底盘 bringup，提供 /odom、/cmd_vel、odom->base_link
终端 2：A1 雷达驱动，提供 /scan
终端 3：base_link->laser 静态 TF 或 URDF
终端 4：nav2_bringup bringup_launch.py，加载保存好的地图
终端 5：rviz2 设置初始位姿并发送目标点
```

## 14. 常见问题排查

### 14.1 没有 `/scan`

检查：

```bash
ls -l /dev/rplidar
ls -l /dev/ttyUSB*
dmesg | grep -i tty
ros2 topic list
```

可能原因：

- 雷达没插好
- USB 串口没识别
- 设备名不是 `/dev/rplidar`
- 没有串口权限
- A1 波特率没有用 `115200`
- 启动的是 A3/S1/S2 的 launch，波特率不匹配

### 14.2 `/scan` 有数据，但 RViz 看不到

检查：

- RViz 的 Fixed Frame 是否设置为 `laser`
- LaserScan topic 是否选择 `/scan`
- RViz LaserScan 的 QoS 是否与传感器兼容

如果还没有完整 TF，先用 `laser` 作为 Fixed Frame 看单独扫描。

### 14.3 `slam_toolbox` 报 TF 错误

通常是缺少：

- `odom -> base_link`
- `base_link -> laser`

检查：

```bash
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link laser
```

### 14.4 地图漂移严重

可能原因：

- 轮式里程计不准
- 雷达安装位置 TF 不准
- 雷达高度或角度有偏差
- 建图时速度太快
- 环境特征太少，比如长走廊或纯玻璃环境

建议：

- 降低移动速度
- 尽量闭环回到起点
- 校准 `base_link -> laser`
- 检查 `/odom` 是否连续、方向是否正确

### 14.5 Nav2 不动

检查：

```bash
ros2 topic echo /cmd_vel
ros2 topic echo /odom --once
ros2 topic echo /scan --once
ros2 run tf2_ros tf2_echo map odom
ros2 run tf2_ros tf2_echo odom base_link
```

常见原因：

- 没有点击 `2D Pose Estimate`
- AMCL 没定位成功
- 地图路径错误
- costmap 没收到 `/scan`
- `robot_base_frame` 和实际 TF 不一致
- 底盘不接收 `/cmd_vel`
- 安全半径 `robot_radius` 设置过大导致无法规划

### 14.6 本地 A1 资料里的 launch 在 Jazzy 下报错

旧 launch 里可能有：

```python
node_executable='sllidar_node'
node_name='sllidar_node'
```

Jazzy 推荐写法：

```python
executable='sllidar_node'
name='sllidar_node'
```

或者直接绕过 launch：

```bash
ros2 run sllidar_ros2 sllidar_node --ros-args \
  -p serial_port:=/dev/rplidar \
  -p serial_baudrate:=115200 \
  -p frame_id:=laser \
  -p angle_compensate:=true
```

## 15. 推荐你按这个顺序实施

1. 先把 `sllidar_ros2` 编译通过
2. 固定 `/dev/rplidar`
3. 启动雷达，确认 `/scan` 正常
4. RViz 用 `laser` 作为 Fixed Frame 看扫描
5. 加 `base_link -> laser` 静态 TF
6. 确认底盘 `/odom`、`/cmd_vel`、`odom -> base_link` 正常
7. 启动 `slam_toolbox` 建图
8. 保存 `a1_map.yaml` 和 `a1_map.pgm`
9. 配置 Nav2 参数
10. 启动 Nav2，设置初始位姿，发送目标点

## 16. 当前最重要的结论

A1 资料里最有用的信息是：**A1 使用 `sllidar_ros2`，串口波特率是 `115200`，发布 `/scan`，frame_id 可用 `laser`。**

在 ROS 2 Jazzy 下，建图和导航建议不要照搬旧教程里的 ROS1/Gmapping/AMCL/move_base 流程，而是采用：

```text
A1 雷达 -> /scan -> slam_toolbox 建图 -> map_saver_cli 保存地图 -> Nav2 导航
```

只要 `/scan`、`/odom`、`/cmd_vel`、TF 链路正常，后续就是调 `slam_toolbox` 和 Nav2 参数。
