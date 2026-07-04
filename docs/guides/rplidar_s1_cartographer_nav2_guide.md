
# RPLIDAR S1 + Cartographer + Nav2 纯雷达建图与自主导航操作文档

> 适用硬件：RK3588 上位机、AET-H43basic 下位机、RPLIDAR S1 2D 激光雷达。  
> 适用目标：不加编码器、不加外置 IMU，仅依靠 2D 激光雷达完成建图、定位和自主导航。  
> 推荐系统：Ubuntu 22.04 + ROS2 Humble。若你的 ROS2 版本不是 Humble，包名和部分 launch 参数可能需要对应调整。

---

## 0. 总体思路

你的系统应该按下面这个逻辑理解：

```text
RPLIDAR S1
  ↓
/scan
  ↓
Cartographer 2D
  ↓
map -> odom -> base_link
  ↓
Nav2
  ↓
/cmd_vel
  ↓
RK3588 串口/USB/CAN 驱动节点
  ↓
AET-H43basic
  ↓
电机运动
```

在这个方案中：

- AET-H43basic 只负责执行运动指令；
- 不要求 AET-H43basic 返回 `/odom`；
- 不要求 AET-H43basic 返回 `/imu`；
- Cartographer 负责根据 RPLIDAR S1 的 `/scan` 建图和估计机器人位姿；
- Nav2 负责路径规划、局部避障和输出 `/cmd_vel`。

最终 TF 关系应为：

```text
map -> odom -> base_link -> laser
```

其中：

| TF | 来源 |
|---|---|
| `base_link -> laser` | 你自己通过 `static_transform_publisher` 或 URDF 发布 |
| `map -> odom` | Cartographer 发布 |
| `odom -> base_link` | Cartographer 在 `provide_odom_frame = true` 时发布 |

---

## 1. 阶段划分

建议分为 4 个阶段做，不要一上来就直接跑 Nav2。

| 阶段 | 目标 | 验收标准 |
|---|---|---|
| 阶段 1 | 硬件与基础通信 | `/scan` 稳定；底盘能响应 `/cmd_vel` |
| 阶段 2 | TF 坐标系 | `base_link -> laser` 正确，RViz2 中雷达方向正确 |
| 阶段 3 | Cartographer 建图/定位 | 地图正常生成；`map -> odom -> base_link` 正常 |
| 阶段 4 | Nav2 自主导航 | RViz2 设置目标点后，机器人能规划并移动 |

---

# 阶段 1：硬件与基础通信

## 1.1 安装基础 ROS2 包

```bash
sudo apt update
sudo apt install -y \
  ros-humble-cartographer \
  ros-humble-cartographer-ros \
  ros-humble-nav2-bringup \
  ros-humble-tf2-tools \
  ros-humble-robot-state-publisher \
  ros-humble-xacro \
  python3-colcon-common-extensions
```

确认 ROS2 环境：

```bash
source /opt/ros/humble/setup.bash
ros2 --version
```

建议加入 `~/.bashrc`：

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

---

## 1.2 安装 RPLIDAR S1 ROS2 驱动

推荐使用 Slamtec 官方 `sllidar_ros2`：

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone https://github.com/Slamtec/sllidar_ros2.git
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

临时给串口权限：

```bash
sudo chmod 666 /dev/ttyUSB0
```

如果你的雷达不是 `/dev/ttyUSB0`，先查设备：

```bash
ls /dev/ttyUSB*
ls /dev/ttyACM*
dmesg | grep tty
```

启动 RPLIDAR S1：

```bash
source ~/ros2_ws/install/setup.bash
ros2 launch sllidar_ros2 view_sllidar_s1_launch.py
```

检查 `/scan`：

```bash
ros2 topic list
ros2 topic hz /scan
ros2 topic echo /scan --once
```

验收标准：

```text
/scan 存在
/scan 频率稳定，通常约 8~15 Hz
LaserScan 的 header.frame_id 能看到，例如 laser、laser_frame、rplidar_link 等
RViz2 中能看到雷达扫描点
```

记录你的雷达 frame：

```bash
ros2 topic echo /scan --once | grep frame_id
```

假设看到：

```text
frame_id: laser
```

后面就使用 `laser`。如果实际是 `laser_frame`，后面所有 `laser` 都要替换为 `laser_frame`。

---

## 1.3 测试底盘 `/cmd_vel`

这一阶段只要求底盘能被 ROS2 控制，不要求返回 odom。

你需要有一个节点完成：

```text
/cmd_vel -> AET-H43basic 控制协议 -> 电机
```

假设你的 AET 驱动节点已经订阅 `/cmd_vel`，可以测试：

前进：

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.10}, angular: {z: 0.0}}"
```

原地左转：

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.0}, angular: {z: 0.30}}"
```

停止：

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.0}, angular: {z: 0.0}}"
```

验收标准：

```text
前进正常
后退正常
左转正常
右转正常
停止可靠
急停可靠
```

建议初期速度限制：

```text
线速度：0.10 ~ 0.25 m/s
角速度：0.20 ~ 0.50 rad/s
```

---

# 阶段 2：TF 坐标系

## 2.1 坐标系命名建议

建议使用以下 frame 名称：

| 名称 | 含义 |
|---|---|
| `map` | 全局地图坐标系 |
| `odom` | 连续局部里程计坐标系 |
| `base_link` | 机器人底盘中心 |
| `laser` | RPLIDAR S1 雷达坐标系 |

注意：Cartographer 的 frame 名不要写成 `/base_link`、`/laser`，不要带 `/` 前缀。

---

## 2.2 发布 `base_link -> laser`

先用静态 TF 测试。假设雷达安装在机器人中心前方 0.15 m，高度 0.20 m，左右不偏：

```bash
ros2 run tf2_ros static_transform_publisher \
0.15 0 0.20 0 0 0 \
base_link laser
```

参数含义：

```text
x = 0.15      雷达在机器人中心前方 0.15 m
y = 0.00      雷达没有左右偏移
z = 0.20      雷达离地 0.20 m
yaw = 0       雷达正方向与机器人正前方一致
pitch = 0
roll = 0
parent = base_link
child = laser
```

如果你的 `/scan.header.frame_id` 是 `laser_frame`，命令应改为：

```bash
ros2 run tf2_ros static_transform_publisher \
0.15 0 0.20 0 0 0 \
base_link laser_frame
```

检查 TF：

```bash
ros2 run tf2_ros tf2_echo base_link laser
```

生成 TF 图：

```bash
ros2 run tf2_tools view_frames
```

验收标准：

```text
tf2_echo 能查到 base_link 到 laser 的变换
RViz2 Fixed Frame 设为 base_link 时，/scan 能正常显示
前方障碍物显示在机器人前方
左侧障碍物显示在机器人左侧
```

如果方向反了，先检查：

1. 雷达安装方向是否反了；
2. `base_link -> laser` 的 yaw 是否需要改为 3.14159；
3. RPLIDAR 驱动参数是否反转了扫描方向。

---

# 阶段 3：Cartographer 纯雷达建图与定位

## 3.1 创建 bringup 包

```bash
cd ~/ros2_ws/src
ros2 pkg create carto_nav_bringup --build-type ament_python
mkdir -p carto_nav_bringup/config carto_nav_bringup/launch
```

目录建议：

```text
carto_nav_bringup/
  config/
    rplidar_s1_2d.lua
    rplidar_s1_localization.lua
    nav2_params.yaml
  launch/
    cartographer_mapping.launch.py
    cartographer_localization.launch.py
    nav2_navigation.launch.py
```

---

## 3.2 Cartographer 建图配置：`config/rplidar_s1_2d.lua`

```lua
include "map_builder.lua"
include "trajectory_builder.lua"

options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,

  map_frame = "map",
  tracking_frame = "base_link",
  published_frame = "base_link",
  odom_frame = "odom",

  provide_odom_frame = true,
  publish_frame_projected_to_2d = true,
  publish_to_tf = true,

  use_odometry = false,
  use_nav_sat = false,
  use_landmarks = false,

  num_laser_scans = 1,
  num_multi_echo_laser_scans = 0,
  num_subdivisions_per_laser_scan = 1,
  num_point_clouds = 0,

  lookup_transform_timeout_sec = 0.2,
  submap_publish_period_sec = 0.3,
  pose_publish_period_sec = 5e-3,
  trajectory_publish_period_sec = 30e-3,

  rangefinder_sampling_ratio = 1.0,
  odometry_sampling_ratio = 1.0,
  fixed_frame_pose_sampling_ratio = 1.0,
  imu_sampling_ratio = 1.0,
  landmarks_sampling_ratio = 1.0,
}

MAP_BUILDER.use_trajectory_builder_2d = true

TRAJECTORY_BUILDER_2D.use_imu_data = false

-- RPLIDAR S1 推荐先不要用满 40m，室内建图建议 12~20m。
TRAJECTORY_BUILDER_2D.min_range = 0.20
TRAJECTORY_BUILDER_2D.max_range = 18.0
TRAJECTORY_BUILDER_2D.missing_data_ray_length = 5.0

TRAJECTORY_BUILDER_2D.num_accumulated_range_data = 1

-- 没有编码器和 IMU 时，建议打开在线相关性扫描匹配。
TRAJECTORY_BUILDER_2D.use_online_correlative_scan_matching = true

TRAJECTORY_BUILDER_2D.ceres_scan_matcher.translation_weight = 10.0
TRAJECTORY_BUILDER_2D.ceres_scan_matcher.rotation_weight = 40.0

POSE_GRAPH.optimize_every_n_nodes = 90
POSE_GRAPH.constraint_builder.min_score = 0.55
POSE_GRAPH.constraint_builder.global_localization_min_score = 0.60

return options
```

关键点：

```lua
use_odometry = false
TRAJECTORY_BUILDER_2D.use_imu_data = false
provide_odom_frame = true
num_laser_scans = 1
```

含义：

```text
不使用外部 /odom
不使用 /imu
只订阅一个 /scan
由 Cartographer 发布 map -> odom -> base_link
```

---

## 3.3 Cartographer 建图 launch：`launch/cartographer_mapping.launch.py`

```python
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    config_dir = os.path.join(
        get_package_share_directory('carto_nav_bringup'),
        'config'
    )

    return LaunchDescription([
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_laser_tf',
            arguments=['0.15', '0', '0.20', '0', '0', '0', 'base_link', 'laser'],
            output='screen'
        ),

        Node(
            package='cartographer_ros',
            executable='cartographer_node',
            name='cartographer_node',
            output='screen',
            arguments=[
                '-configuration_directory', config_dir,
                '-configuration_basename', 'rplidar_s1_2d.lua'
            ],
            remappings=[
                ('scan', '/scan'),
            ]
        ),

        Node(
            package='cartographer_ros',
            executable='cartographer_occupancy_grid_node',
            name='cartographer_occupancy_grid_node',
            output='screen',
            arguments=[
                '-resolution', '0.05',
                '-publish_period_sec', '1.0'
            ]
        ),
    ])
```

如果你的雷达 frame 不是 `laser`，要同步修改：

```python
arguments=['0.15', '0', '0.20', '0', '0', '0', 'base_link', '你的雷达frame']
```

---

## 3.4 修改 `setup.py` 安装 launch 和 config 文件

打开：

```bash
nano ~/ros2_ws/src/carto_nav_bringup/setup.py
```

确认加入：

```python
import os
from glob import glob

# setup(...) 中 data_files 添加：
data_files=[
    ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml']),
    (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    (os.path.join('share', package_name, 'config'), glob('config/*')),
],
```

重新编译：

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

---

## 3.5 启动建图

终端 1：启动雷达

```bash
source ~/ros2_ws/install/setup.bash
ros2 launch sllidar_ros2 view_sllidar_s1_launch.py
```

终端 2：启动 Cartographer

```bash
source ~/ros2_ws/install/setup.bash
ros2 launch carto_nav_bringup cartographer_mapping.launch.py
```

终端 3：启动 RViz2

```bash
rviz2
```

RViz2 建议显示：

```text
Fixed Frame: map
Displays:
  TF
  LaserScan: /scan
  Map: /map
```

检查 TF：

```bash
ros2 run tf2_ros tf2_echo map base_link
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link laser
```

验收标准：

```text
/map 有地图
map -> odom -> base_link 正常
机器人移动时，RViz 中机器人位置跟随移动
/scan 和地图墙体基本重合
地图没有明显重影、弯曲、撕裂
```

建图操作建议：

```text
低速手动遥控
先沿墙走，再走中间区域
尽量形成闭环
不要快速原地旋转
不要高速冲进长走廊
遇到玻璃、镜面、强反光区域要降低速度
```

推荐建图速度：

```text
线速度：0.10 ~ 0.25 m/s
角速度：0.20 ~ 0.50 rad/s
```

---

## 3.6 保存地图

建议同时保存两种格式：

1. Cartographer 原生 `.pbstream`；
2. Nav2 常用 `.yaml + .pgm`。

创建地图目录：

```bash
mkdir -p ~/maps
```

结束 trajectory：

```bash
ros2 service call /finish_trajectory cartographer_ros_msgs/srv/FinishTrajectory \
"{trajectory_id: 0}"
```

保存 pbstream：

```bash
ros2 service call /write_state cartographer_ros_msgs/srv/WriteState \
"{filename: '/home/ubuntu/maps/rplidar_s1.pbstream', include_unfinished_submaps: true}"
```

注意：把 `/home/ubuntu` 改成你 RK3588 上真实用户名路径。可以用下面命令确认：

```bash
echo $HOME
```

保存 Nav2 地图：

```bash
ros2 run nav2_map_server map_saver_cli -f ~/maps/rplidar_s1_map
```

保存成功后应看到：

```text
~/maps/rplidar_s1.pbstream
~/maps/rplidar_s1_map.yaml
~/maps/rplidar_s1_map.pgm
```

---

# 阶段 4：Nav2 自主导航

## 4.1 推荐定位方式

因为你没有编码器、没有 IMU，所以不建议优先用 AMCL。建议优先使用：

```text
Cartographer localization mode
```

也就是：

```text
RPLIDAR S1 -> Cartographer 纯定位 -> map -> odom -> base_link -> Nav2
```

不要同时让 AMCL 和 Cartographer 都发布 `map -> odom`，否则 TF 会冲突。

---

## 4.2 Cartographer 定位配置：`config/rplidar_s1_localization.lua`

可以基于建图配置复制一份：

```bash
cp ~/ros2_ws/src/carto_nav_bringup/config/rplidar_s1_2d.lua \
   ~/ros2_ws/src/carto_nav_bringup/config/rplidar_s1_localization.lua
```

然后在文件末尾 `return options` 前加入：

```lua
TRAJECTORY_BUILDER.pure_localization_trimmer = {
  max_submaps_to_keep = 3,
}

POSE_GRAPH.optimize_every_n_nodes = 20
```

定位模式仍然保持：

```lua
use_odometry = false
TRAJECTORY_BUILDER_2D.use_imu_data = false
provide_odom_frame = true
```

---

## 4.3 Cartographer 定位 launch：`launch/cartographer_localization.launch.py`

```python
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    config_dir = os.path.join(
        get_package_share_directory('carto_nav_bringup'),
        'config'
    )

    pbstream_file = '/home/ubuntu/maps/rplidar_s1.pbstream'

    return LaunchDescription([
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_laser_tf',
            arguments=['0.15', '0', '0.20', '0', '0', '0', 'base_link', 'laser'],
            output='screen'
        ),

        Node(
            package='cartographer_ros',
            executable='cartographer_node',
            name='cartographer_node',
            output='screen',
            arguments=[
                '-configuration_directory', config_dir,
                '-configuration_basename', 'rplidar_s1_localization.lua',
                '-load_state_filename', pbstream_file,
                '-load_frozen_state', 'true'
            ],
            remappings=[
                ('scan', '/scan'),
            ]
        ),

        Node(
            package='cartographer_ros',
            executable='cartographer_occupancy_grid_node',
            name='cartographer_occupancy_grid_node',
            output='screen',
            arguments=[
                '-resolution', '0.05',
                '-publish_period_sec', '1.0'
            ]
        ),
    ])
```

注意修改：

```python
pbstream_file = '/home/ubuntu/maps/rplidar_s1.pbstream'
```

为你的真实路径。

重新编译：

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

启动定位：

```bash
ros2 launch carto_nav_bringup cartographer_localization.launch.py
```

验收标准：

```text
/map 正常显示
机器人在地图中的位置基本正确
移动机器人后，位姿能跟随变化
map -> odom -> base_link 正常
没有 AMCL 同时发布 map -> odom
```

---

## 4.4 Nav2 启动建议

使用 Cartographer 负责定位时，Nav2 不需要 AMCL 发布 `map -> odom`。建议只启动 Nav2 navigation 部分。

示例命令：

```bash
ros2 launch nav2_bringup navigation_launch.py \
use_sim_time:=False \
params_file:=~/ros2_ws/src/carto_nav_bringup/config/nav2_params.yaml
```

Nav2 输入：

```text
/map
/scan
/tf
```

Nav2 输出：

```text
/cmd_vel
```

确认 Nav2 是否输出速度：

```bash
ros2 topic echo /cmd_vel
```

如果 `/cmd_vel` 有输出但车不动，问题在 AET 驱动节点。  
如果 `/cmd_vel` 没有输出，通常是 TF、costmap、定位或 Nav2 参数问题。

---

## 4.5 `nav2_params.yaml` 关键参数建议

不要一开始追求速度，先保守调参。

建议速度限制：

```yaml
controller_server:
  ros__parameters:
    controller_frequency: 10.0

    FollowPath:
      desired_linear_vel: 0.18
      max_linear_accel: 0.30
      max_angular_accel: 0.70
      rotate_to_heading_angular_vel: 0.40
```

局部代价地图建议：

```yaml
local_costmap:
  local_costmap:
    ros__parameters:
      global_frame: odom
      robot_base_frame: base_link
      rolling_window: true
      width: 3
      height: 3
      resolution: 0.05
```

全局代价地图建议：

```yaml
global_costmap:
  global_costmap:
    ros__parameters:
      global_frame: map
      robot_base_frame: base_link
      resolution: 0.05
      track_unknown_space: true
```

雷达 obstacle layer 要使用 `/scan`：

```yaml
obstacle_layer:
  plugin: "nav2_costmap_2d::ObstacleLayer"
  enabled: True
  observation_sources: scan
  scan:
    topic: /scan
    max_obstacle_height: 2.0
    clearing: True
    marking: True
    data_type: "LaserScan"
    raytrace_max_range: 8.0
    raytrace_min_range: 0.0
    obstacle_max_range: 6.0
    obstacle_min_range: 0.0
```

机器人外形建议先用圆形半径：

```yaml
robot_radius: 0.18
inflation_layer:
  plugin: "nav2_costmap_2d::InflationLayer"
  cost_scaling_factor: 3.0
  inflation_radius: 0.35
```

注意：如果你的机器人宽度较大，`robot_radius` 和 `inflation_radius` 必须加大。

---

## 4.6 自主导航测试顺序

不要一开始给远距离目标。按下面顺序：

```text
1. 原地设置短目标：0.5 m
2. 前方 1 m 目标
3. 带轻微转弯的 1~2 m 目标
4. 走廊内 3~5 m 目标
5. 有障碍物绕行目标
6. 跨房间导航目标
```

每一步验收：

```text
路径能规划
/cmd_vel 有输出
机器人朝正确方向运动
定位没有明显漂移
局部 costmap 能看到障碍物
到达目标后能停止
```

---

# 常见故障排查

## 问题 1：Cartographer 启动后没有地图

检查：

```bash
ros2 topic hz /scan
ros2 topic echo /scan --once
ros2 run tf2_ros tf2_echo base_link laser
```

常见原因：

```text
/scan 没有数据
/scan.header.frame_id 与 TF 中的 laser 名称不一致
没有 base_link -> laser
Cartographer lua 中 num_laser_scans 没设为 1
remapping 没有把 scan 对到 /scan
```

---

## 问题 2：报 TF extrapolation / lookup transform failed

检查：

```bash
ros2 run tf2_tools view_frames
ros2 run tf2_ros tf2_echo base_link laser
ros2 run tf2_ros tf2_echo map base_link
```

处理：

```text
确认所有节点使用同一台机器时间
不要开启 use_sim_time，除非你在播放 rosbag
确认 static_transform_publisher 已启动
确认 frame 名称完全一致
```

---

## 问题 3：地图严重重影或弯曲

处理建议：

```text
降低机器人速度
降低原地旋转速度
确认雷达安装牢固
确认雷达前方方向与 base_link 前方一致
max_range 从 18.0 降到 12.0
检查地面打滑
避免玻璃和强反光区域
```

可以尝试：

```lua
TRAJECTORY_BUILDER_2D.max_range = 12.0
TRAJECTORY_BUILDER_2D.ceres_scan_matcher.rotation_weight = 60.0
POSE_GRAPH.optimize_every_n_nodes = 60
```

---

## 问题 4：Nav2 能规划，但机器人不动

检查：

```bash
ros2 topic echo /cmd_vel
ros2 node list
ros2 topic info /cmd_vel
```

判断：

```text
/cmd_vel 有输出：AET 驱动节点没有正确接收或转换
/cmd_vel 无输出：Nav2 没进入激活状态，或 costmap/TF/定位异常
```

---

## 问题 5：机器人运动方向反了

可能原因：

```text
电机左右接反
AET 驱动里线速度/角速度符号反了
base_link 坐标定义反了
雷达 frame 方向错了
```

ROS 标准方向：

```text
base_link x 正方向：机器人前方
base_link y 正方向：机器人左方
base_link z 正方向：机器人上方
angular.z 正方向：逆时针左转
```

---

# 每次启动推荐顺序

建图模式：

```text
1. 启动 RPLIDAR S1
2. 启动 Cartographer mapping launch
3. 启动 RViz2
4. 手动遥控建图
5. 保存 pbstream 和 yaml/pgm 地图
```

导航模式：

```text
1. 启动 RPLIDAR S1
2. 启动 Cartographer localization launch
3. 启动 Nav2 navigation_launch.py
4. 启动 RViz2
5. 设置 2D Nav Goal
```

---

# 最小验收清单

在进入 Nav2 前，必须满足：

```text
[ ] /scan 稳定
[ ] /cmd_vel 能控制底盘
[ ] base_link -> laser 正确
[ ] Cartographer 能生成 /map
[ ] map -> odom -> base_link 正常
[ ] 地图能保存为 .pbstream
[ ] 地图能保存为 .yaml + .pgm
```

进入 Nav2 后，必须满足：

```text
[ ] Nav2 lifecycle 节点 active
[ ] RViz2 中能看到 global costmap
[ ] RViz2 中能看到 local costmap
[ ] 设置短距离目标后能规划路径
[ ] /cmd_vel 有输出
[ ] 底盘能按 /cmd_vel 运动
[ ] 到达目标后能停止
```

---

# 关键原则

1. 不要同时运行 AMCL 和 Cartographer 发布 `map -> odom`。
2. 不要让多个节点同时发布 `odom -> base_link`。
3. 没有编码器和 IMU 时，速度必须保守。
4. 先建图，再定位，再导航。
5. TF 错了，后面所有东西都会错。
6. `/scan`、`/cmd_vel`、`base_link -> laser` 是最先要打通的三个基础。

---

# 推荐最终架构

```text
RPLIDAR S1
  ↓ /scan
Cartographer localization
  ↓ map -> odom -> base_link
Nav2
  ↓ /cmd_vel
cmd_vel_to_aet_driver
  ↓ AT/串口/USB/CAN 指令
AET-H43basic
  ↓
电机
```

如果后续发现定位漂移严重，优先从以下方向优化：

```text
1. 降低速度
2. 修正 base_link -> laser
3. 缩小 Cartographer max_range
4. 检查雷达安装是否晃动
5. 改善环境特征
6. 最后再考虑加编码器或 IMU
```
