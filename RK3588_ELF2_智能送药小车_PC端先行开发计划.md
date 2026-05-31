# RK3588 ELF 2 智能送药小车 PC 端先行开发计划

## 1. 项目目标

本项目计划基于 **RK3588 ELF 2 开发板** 实现智能送药小车，面向医院病区、养老院、社区卫生服务中心等场景，提供自动化、低接触的药品配送服务。

系统核心技术路线：

```text
ROS 2 Jazzy
slam_toolbox
Navigation 2
激光雷达
IMU
视觉感知
YOLOv8
语音交互
任务管理
远程状态上传
```

当前阶段先在电脑端完成软件原型，后续再迁移到 RK3588 和真实底盘。

---

## 2. 电脑端可以先完成什么

### 2.1 现在就能做

```text
1. ROS 2 项目工作区结构
2. A1 雷达建图流程
3. slam_toolbox 地图生成与保存
4. Nav2 仿真导航
5. 送药任务管理节点
6. 配送点配置文件
7. YOLOv8 摄像头检测原型
8. 语音播报原型
9. Web 或命令行任务下发原型
10. 一键启动 launch 文件
```

### 2.2 等硬件后再做

```text
1. RK3588 上部署 ROS 2
2. 底盘电机控制
3. 真实 /odom 闭环
4. IMU 标定与融合
5. 雷达和摄像头安装 TF 标定
6. YOLOv8 RK3588 NPU 加速
7. 药箱舱门控制
8. 电池电量与急停检测
9. 真实场景长时间测试
```

---

## 3. 推荐 ROS 2 工作区

建议新建独立工作区：

```bash
mkdir -p ~/medicine_robot_ws/src
cd ~/medicine_robot_ws
```

推荐包结构：

```text
medicine_robot_ws/src
├── medicine_robot_bringup
├── medicine_robot_description
├── medicine_robot_navigation
├── medicine_interfaces
├── medicine_task_manager
├── medicine_yolov8_detector
├── medicine_voice_interaction
└── medicine_web_dashboard
```

---

## 4. 各模块职责

### 4.1 `medicine_robot_bringup`

负责一键启动系统。

后续可以提供：

```text
pc_sim.launch.py
handheld_mapping.launch.py
real_robot.launch.py
nav2.launch.py
```

### 4.2 `medicine_robot_description`

负责机器人模型。

包括：

```text
base_link
laser
camera_link
imu_link
medicine_box_link
```

电脑端可以先写 URDF/Xacro，后续硬件确定后再改尺寸。

### 4.3 `medicine_robot_navigation`

负责导航配置。

包括：

```text
slam_toolbox 参数
Nav2 参数
地图文件
站点坐标文件
```

### 4.4 `medicine_interfaces`

负责自定义接口。

建议后续定义：

```text
DeliveryTask.msg
DeliveryState.msg
MedicineBoxState.msg
CreateDeliveryTask.srv
CancelDeliveryTask.srv
```

### 4.5 `medicine_task_manager`

负责送药任务逻辑。

典型流程：

```text
接收任务
读取目标站点
调用 Nav2 导航
到站后语音提醒
等待身份确认
完成配送
返回起点
异常告警
```

### 4.6 `medicine_yolov8_detector`

负责视觉检测。

电脑端先用 USB 摄像头或视频文件测试：

```text
药品包装检测
行人检测
动态障碍物检测
检测结果发布到 ROS2 topic
```

### 4.7 `medicine_voice_interaction`

负责语音播报和简单交互。

电脑端先实现文本转语音：

```text
任务开始
正在前往某病房
已到达
请取药
身份确认成功
异常告警
```

### 4.8 `medicine_web_dashboard`

负责远程任务管理原型。

电脑端可以先做：

```text
创建送药任务
查看任务状态
查看机器人当前位置
查看异常告警
```

---

## 5. 第一阶段建议目标

第一阶段不要追求全部功能，先完成一个最小闭环：

```text
电脑端 ROS2 工作区
地图文件
Nav2 或模拟导航接口
送药任务管理节点
站点配置文件
语音播报
命令行下发送药任务
```

最小演示效果：

```text
输入：送药到 A 病房
系统：播报“开始送药到 A 病房”
系统：调用导航目标 A
系统：模拟或等待导航完成
系统：播报“已到达 A 病房，请取药”
系统：任务状态变为 completed
```

---

## 6. 第一阶段实施顺序

建议按这个顺序做：

```text
1. 创建 medicine_robot_ws
2. 创建 medicine_interfaces
3. 创建 medicine_task_manager
4. 创建站点配置文件 stations.yaml
5. 实现命令行创建送药任务
6. 先用模拟导航完成任务闭环
7. 接入 Nav2 NavigateToPose
8. 接入语音播报
9. 接入 YOLOv8 摄像头检测
10. 整理一键启动 launch
```

---

## 7. 与当前 A1 雷达成果的关系

你已经完成了：

```text
A1 雷达接入
/scan 数据验证
rf2o 激光里程计
slam_toolbox 手持建图
地图保存
一键手持建图 bringup 包
```

这些成果后续可以迁移到送药小车项目中。

短期建议：

```text
A1 项目继续作为雷达验证工程
medicine_robot_ws 作为送药小车主工程
```

等底盘准备好后，再把 A1 雷达、Nav2、任务管理统一到真实机器人 bringup 中。

---

## 8. 下一步最推荐做什么

下一步建议先做：

```text
medicine_task_manager 送药任务管理节点
```

原因是：

```text
不依赖底盘
不依赖 RK3588
不依赖真实导航
可以在电脑上完整验证业务逻辑
后续可以无缝接入 Nav2
```

第一版任务管理节点只需要做到：

```text
读取 stations.yaml
接收目标站点名称
发布任务状态
模拟导航完成
打印或语音播报任务过程
```
