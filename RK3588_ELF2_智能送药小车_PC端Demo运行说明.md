# RK3588 ELF 2 智能送药小车 PC 端 Demo 运行说明

本文记录当前电脑端 `medicine_robot_ws` 的运行方式、功能闭环、网页访问方法和常见问题。

当前 Demo 运行在：

```text
Ubuntu 24.04 / WSL2
ROS 2 Jazzy
工作区：~/medicine_robot_ws
```

---

## 1. 当前已完成的功能

当前 PC 端 Demo 已经跑通以下闭环：

```text
网页创建送药任务
-> ROS2 服务 /medicine/create_delivery_task
-> medicine_task_manager 任务管理节点
-> 模拟导航配送流程
-> /medicine/delivery_state 状态发布
-> /medicine/voice_text 语音文本发布
-> medicine_voice_interaction 终端打印或 TTS 播报
-> 网页实时显示任务状态和进度
-> medicine_vision_detector 发布药物识别信息
-> /medicine/drug_info 药物信息话题
-> 网页实时显示药品名称、类型、置信度和装药状态
```

状态变化流程：

```text
IDLE
-> WAITING_LOAD_CONFIRMATION
-> NAVIGATING
-> WAITING_DISPENSE_CONFIRMATION
-> COMPLETED
-> IDLE
```

---

## 2. 当前 ROS2 包结构

工作区路径：

```bash
~/medicine_robot_ws
```

当前主要包：

```text
medicine_robot_ws/src
├── medicine_interfaces
├── medicine_task_manager
├── medicine_vision_detector
├── medicine_voice_interaction
├── medicine_web_dashboard
└── medicine_robot_bringup
```

### 2.1 `medicine_interfaces`

负责自定义消息和服务。

已有接口：

```text
msg/DeliveryTask.msg
msg/DeliveryState.msg
msg/DrugInfo.msg
srv/CreateDeliveryTask.srv
srv/CancelDeliveryTask.srv
```

关键服务：

```text
/medicine/create_delivery_task
/medicine/cancel_delivery_task
/medicine/verify_delivery_task
```

关键状态话题：

```text
/medicine/delivery_state
```

药物识别话题：

```text
/medicine/drug_info
/medicine/drug_recognition_status
```

语音文本话题：

```text
/medicine/voice_text
```

### 2.2 `medicine_task_manager`

负责送药任务管理。

功能：

```text
读取 stations.yaml 站点配置
接收送药任务
模拟导航过程
发布任务状态
发布语音播报文本
支持取消任务
```

站点配置文件：

```bash
~/medicine_robot_ws/src/medicine_task_manager/config/stations.yaml
```

当前站点包括：

```text
pharmacy       药房
ward_a         A病房
ward_b         B病房
nurse_station  护士站
```

### 2.3 `medicine_voice_interaction`

负责语音播报。

当前节点：

```text
voice_console_node
```

功能：

```text
订阅 /medicine/voice_text
终端打印 [语音播报] 文本
可尝试调用 TTS 播放声音
```

当前 TTS 策略：

```text
tts_backend:=auto
优先调用 WSL 中的 powershell.exe
通过 Windows System.Speech 播放中文
失败后尝试 Linux TTS
再失败则只保留终端打印
```

### 2.4 `medicine_web_dashboard`

负责浏览器任务面板。

当前节点：

```text
web_dashboard_node
```

默认地址：

```text
http://localhost:8080
```

如果 Windows 的 `localhost:8080` 被占用，可以使用 WSL IP：

```text
http://<WSL_IP>:8080
```

Web API：

```text
GET  /api/health
GET  /api/stations
GET  /api/state
GET  /api/drug_info
POST /api/tasks
POST /api/cancel
```

### 2.5 `medicine_vision_detector`

负责 PC 端药物信息获取原型。

当前节点：

```text
drug_info_detector_node
```

当前支持模拟识别数据和 USB 摄像头识别数据，发布：

```text
/medicine/drug_info
/medicine/drug_recognition_status
```

当前默认模拟药物信息：

```text
drug_id: drug_001
drug_name: 降压药
drug_type: tablet
confidence: 0.98
loaded: true
source: mock
```

摄像头模式当前已支持：

```text
MJPEG 摄像头预览：http://localhost:8090/stream.mjpg
OpenCV QRCodeDetector 二维码识别
zxingcpp QR/DataMatrix/工业码识别
pylibdmtx 可选安装但默认关闭
标签原始码结构化解析，例如 on/pc/pm/qty/pdi
Web Dashboard 显示原始码、码类型、识别方法、订单号、产品编码、产品型号、数量和追溯编号
```

### 2.6 `medicine_robot_bringup`

负责一键启动。

当前 launch：

```bash
ros2 launch medicine_robot_bringup pc_delivery_demo.launch.py
```

默认启动：

```text
medicine_task_manager
medicine_vision_detector
medicine_voice_interaction
medicine_web_dashboard
```

---

## 3. 编译工作区

如果修改了代码，需要重新编译：

```bash
source /opt/ros/jazzy/setup.bash
cd ~/medicine_robot_ws
colcon build --symlink-install
source install/setup.bash
```

如果只是重新运行，通常只需要 source：

```bash
source /opt/ros/jazzy/setup.bash
source ~/medicine_robot_ws/install/setup.bash
```

---

## 4. 启动完整 PC Demo

推荐先清理旧节点，避免重复播报或多个服务同时存在：

```bash
pkill -f task_manager_node
pkill -f voice_console_node
pkill -f web_dashboard_node
pkill -f pc_delivery_demo.launch.py
```

然后启动：

```bash
source /opt/ros/jazzy/setup.bash
source ~/medicine_robot_ws/install/setup.bash

ros2 launch medicine_robot_bringup pc_delivery_demo.launch.py
```

正常输出应包含：

```text
Medicine task manager started. Stations: nurse_station, pharmacy, ward_a, ward_b
Voice node started. topic=/medicine/voice_text, tts=True, backend=auto
Web dashboard started: http://localhost:8080
Medicine vision detector started. Publishing /medicine/drug_info
```

---

## 5. 常用启动参数

### 5.1 关闭 TTS，只保留终端打印

如果不想让电脑语音播报：

```bash
ros2 launch medicine_robot_bringup pc_delivery_demo.launch.py enable_tts:=false
```

### 5.2 加快模拟导航速度

例如 3 秒完成模拟导航：

```bash
ros2 launch medicine_robot_bringup pc_delivery_demo.launch.py simulate_navigation_duration:=3.0
```

### 5.3 修改网页端口

如果 `8080` 被占用：

```bash
ros2 launch medicine_robot_bringup pc_delivery_demo.launch.py web_port:=18080
```

网页访问：

```text
http://localhost:18080
```

或者：

```text
http://<WSL_IP>:18080
```

### 5.4 同时加快导航并关闭语音

```bash
ros2 launch medicine_robot_bringup pc_delivery_demo.launch.py simulate_navigation_duration:=3.0 enable_tts:=false
```

### 5.5 修改模拟药物识别信息

```bash
ros2 launch medicine_robot_bringup pc_delivery_demo.launch.py vision_drug_name:=感冒药 vision_drug_type:=capsule vision_confidence:=0.95 vision_loaded:=true
```

### 5.6 关闭药物识别节点

```bash
ros2 launch medicine_robot_bringup pc_delivery_demo.launch.py enable_vision_detector:=false
```

### 5.7 启动真实摄像头识别和网页预览

当前 WSL 实测推荐使用 `/dev/video0`、MJPG、`zxingcpp`，并默认关闭 `pylibdmtx`：

```bash
ros2 launch medicine_robot_bringup pc_delivery_demo.launch.py \
  vision_input_mode:=camera \
  vision_camera_device:=/dev/video0 \
  vision_camera_width:=640 \
  vision_camera_height:=480 \
  vision_camera_fps:=60 \
  vision_camera_fourcc:=MJPG \
  vision_camera_read_period_sec:=0.016 \
  vision_enable_preview_server:=true \
  vision_preview_quality:=60 \
  vision_preview_draw_overlay:=true \
  vision_preview_stream_period_sec:=0.033 \
  vision_enable_qr_recognition:=true \
  vision_enable_datamatrix_recognition:=true \
  vision_enable_zxingcpp_recognition:=true \
  vision_enable_pylibdmtx_recognition:=false \
  vision_qr_recognition_period_sec:=0.1 \
  vision_qr_fast_mode:=true \
  vision_qr_scale_factor:=1.5 \
  vision_qr_extra_scale_factors:=1.5,2.0 \
  vision_external_decoder_period_sec:=0.35 \
  vision_external_decoder_timeout_sec:=1.5 \
  vision_enable_isolated_zxingcpp_recognition:=true \
  vision_enable_opencv_curved_qr_recognition:=false \
  vision_recognized_code_hold_sec:=0.0 \
  enable_aikit_esr:=false \
  enable_m2_voice_bridge:=false
```

网页访问：

```text
任务面板：http://localhost:8080
摄像头流：http://localhost:8090/stream.mjpg
```

---

## 6. 打开网页面板

启动 launch 后，优先尝试在 Windows 浏览器访问：

```text
http://localhost:8080
```

如果打不开，先在 WSL 中测试：

```bash
curl http://127.0.0.1:8080/api/health
```

正常返回：

```json
{"ok": true}
```

如果 WSL 内部正常，但 Windows 浏览器打不开，说明 Windows 的 `localhost:8080` 可能被其他程序占用，或者 WSL localhost 转发异常。

查看 WSL IP：

```bash
hostname -I
```

例如输出：

```text
172.17.42.120 ...
```

则浏览器访问：

```text
http://172.17.42.120:8080
```

注意：WSL 重启后 IP 可能变化，需要重新执行 `hostname -I`。

---

## 7. 网页测试流程

打开网页后：

```text
指定患者用药清单：选择 patient_001 / 张三 / A-01
目标站点：选择 护士站 / A病房 / B病房
起点站点：选择 药房
药品名称：例如 降压药
患者 ID：例如 patient_001
点击：创建送药任务
```

也可以使用新增的患者用药清单流程：

```text
1. 在“指定患者用药清单”中选择患者
2. 查看该患者应送药品列表、病区、床号和目标站点
3. 摄像头扫药品二维码
4. 点击“扫码核对患者药品”
5. 若当前药品属于该患者清单，页面会提示核对通过并高亮匹配药品
6. 点击“按患者清单创建任务”
```

当前 Demo 内置示例：

```text
patient_001 / 张三 / A-01 / A病房
- 演示二维码药品：product_code=43043
- 降压药：product_code=C177248，trace_id=202011444

patient_002 / 李四 / B-03 / B病房
- 消炎药：product_code=C200100，trace_id=TRACE-P002-001
```

如果摄像头已经识别到结构化标签，网页左侧会显示“识别结果联动”：

```text
产品编码
产品型号
数量
追溯编号
订单号
将提交药品名称
```

此时药品名称会优先自动填充为产品型号，也可以点击“使用识别结果”手动覆盖当前输入。创建任务时，产品编码、产品型号、数量、追溯编号和订单号会通过独立字段提交到 `/medicine/create_delivery_task`，并在 `/medicine/delivery_state` 和网页“当前任务状态”中显示。

创建任务后，任务不会立即开始导航，而是先进入 `WAITING_LOAD_CONFIRMATION`。Dashboard 可以点击“扫码一致性校验”“装药扫码确认”或“取药扫码确认”。这些按钮会把最新扫码结果中的产品编码和追溯编号提交到 `/medicine/verify_delivery_task`，由任务管理节点对比当前任务的 `product_code` 和 `trace_id`：

```text
product_code 一致
trace_id 一致
stage=scan
-> 只做一致性校验，不改变任务状态

stage=load
-> 单药任务：装药确认通过，任务进入 NAVIGATING
-> 多药清单任务：该药标记为已装药；全部药品装药确认通过后才进入 NAVIGATING

product_code 或 trace_id 任一不一致
-> 校验失败，并播报请核对药品

到达目标站点后任务进入 WAITING_DISPENSE_CONFIRMATION

stage=dispense
-> 单药任务：取药确认通过，任务进入 COMPLETED
-> 多药清单任务：该药标记为已取药；全部药品取药确认通过后才进入 COMPLETED
```

预期网页右侧状态变化：

```text
IDLE
-> WAITING_LOAD_CONFIRMATION
-> NAVIGATING
-> WAITING_DISPENSE_CONFIRMATION
-> COMPLETED
-> IDLE
```

预期终端输出：

```text
[语音播报] 任务已创建，请扫码确认装药
[语音播报] 装药确认通过，开始送药到A病房
[语音播报] 已到达A病房，请扫码确认取药
[语音播报] 取药确认通过，送药任务已完成
```

如果 TTS 正常，电脑会同时语音播放这些内容。

---

## 8. 命令行测试方法

### 8.1 查看任务状态

```bash
ros2 topic echo /medicine/delivery_state
```

### 8.2 查看语音文本

```bash
ros2 topic echo /medicine/voice_text
```

### 8.3 查看药物识别信息

```bash
ros2 topic echo /medicine/drug_info
```

预期输出类似：

```text
drug_id: drug_001
drug_name: 降压药
drug_type: tablet
confidence: 0.98
loaded: true
source: mock
```

也可以测试 Web API：

```bash
curl http://127.0.0.1:8080/api/drug_info
```

查看完整识别状态：

```bash
ros2 topic echo /medicine/drug_recognition_status
```

识别到物料标签原始码后，状态中会出现类似字段：

```json
{
  "raw_code_text": "{on:SO2603098044,pc:C177248,pm:FXL0530-100-M,qty:5,mc:,cc:1,pdi:202011444,hp:null}",
  "code_type": "qrcode",
  "code_method": "scaled_gray_1.5x:zxingcpp",
  "label_order_no": "SO2603098044",
  "label_product_code": "C177248",
  "label_product_model": "FXL0530-100-M",
  "label_quantity": "5",
  "label_trace_id": "202011444"
}
```

### 8.4 命令行创建任务

```bash
ros2 run medicine_task_manager create_delivery_task ward_a --medicine "降压药" --patient "patient_001"
```

可用目标站点：

```text
ward_a
ward_b
nurse_station
pharmacy
```

### 8.5 查看节点

```bash
ros2 node list
```

正常应包含：

```text
/medicine_task_manager
/medicine_vision_detector
/medicine_voice_console
/medicine_web_dashboard
```

---

## 9. 常见问题

### 9.1 网页打不开，但 curl 正常

现象：

```bash
curl http://127.0.0.1:8080/api/health
```

返回：

```json
{"ok": true}
```

但 Windows 浏览器打不开。

处理：

```bash
hostname -I
```

然后用 WSL IP 访问：

```text
http://<WSL_IP>:8080
```

也可以换端口：

```bash
ros2 launch medicine_robot_bringup pc_delivery_demo.launch.py web_port:=18080
```

### 9.2 语音或状态重复出现

原因通常是多个旧节点还在运行。

清理：

```bash
pkill -f task_manager_node
pkill -f voice_console_node
pkill -f web_dashboard_node
pkill -f pc_delivery_demo.launch.py
```

然后重新启动 launch。

### 9.3 没有听到 TTS 声音

先确认终端是否有：

```text
[语音播报] xxx
```

如果终端有文字，说明 ROS2 语音链路正常。

可以先关闭 TTS，仅测试业务流程：

```bash
ros2 launch medicine_robot_bringup pc_delivery_demo.launch.py enable_tts:=false
```

WSL 中 TTS 受 Windows 音频、默认语音包、权限和系统设置影响。后续部署到 RK3588 时，可以替换为板端 TTS 引擎。

### 9.4 提示已有任务正在执行

说明当前 `medicine_task_manager` 正在执行一个任务。

等待它完成，或者点击网页中的“取消当前任务”。

### 9.5 WSL 中摄像头断开或没有 `/dev/video0`

Windows 中先确认 USB 摄像头 BUSID，例如当前常见为 `4-4`：

```powershell
usbipd list
```

重新挂载到 WSL：

```powershell
usbipd attach --wsl Ubuntu --busid 4-4
```

如果 WSL 中仍然没有 `/dev/video0`，加载 UVC 驱动并临时放开权限：

```powershell
wsl.exe -d Ubuntu -u root -- bash -lc "modprobe uvcvideo"
wsl.exe -d Ubuntu -u root -- bash -lc "chmod a+rw /dev/video0 /dev/video1 /dev/media0"
```

检查：

```bash
ls -l /dev/video*
```

当前实测 `/dev/video0` 是主视频流，`/dev/video1` 通常不是可用图像流。

### 9.6 识别节点运行一段时间后崩溃

如果看到 `medicine_vision_detector` 退出并出现 `exit code -11`，优先确认是否启用了 `pylibdmtx`。

当前稳定配置：

```text
vision_enable_zxingcpp_recognition:=true
vision_enable_pylibdmtx_recognition:=false
vision_recognized_code_hold_sec:=5.0
```

`pylibdmtx` 可以保留安装，但默认不要启用。`medicine_vision_detector` 已在 launch 中配置自动重启，Web Dashboard 的摄像头预览图片也会在加载失败后自动重新连接。若网页预览区域黑屏，可优先检查：

```bash
ss -ltnp | grep 8090
curl -I http://127.0.0.1:8090/snapshot.jpg
```

如果 `8090` 不在监听，说明视觉节点没有运行或刚刚发生过崩溃；等待自动重启，或重新启动 PC Demo。

---

## 10. 当前阶段意义

当前阶段已经完成智能送药小车的软件业务原型：

```text
任务创建
任务状态管理
站点配置
网页任务面板
语音文本发布
TTS 尝试播报
模拟配送闭环
摄像头实时预览
QR/DataMatrix/工业码识别
标签结构化解析
Dashboard 结构化识别字段显示
识别结果联动送药任务表单
结构化字段进入送药任务状态
扫码结果和当前任务 product_code/trace_id 一致性校验
装药扫码确认后开始导航
到站取药扫码确认后完成任务
Dashboard 显示最近扫码确认审计记录
```

这些功能不依赖真实底盘、不依赖 RK3588、不依赖激光雷达，适合先在 PC 上开发验证；其中视觉模块可使用 USB 摄像头在 WSL 中做真实识别验证。

---

## 11. 后续建议

下一阶段建议继续完善可追溯记录，再接入导航接口：

```text
记录操作人
持久化保存确认记录
支持导出确认记录
异常确认失败时触发告警或阻止继续
Nav2 NavigateToPose
```

目标是把当前的“模拟导航”替换为真实导航动作调用：

```text
读取目标站点坐标
-> 调用 Nav2 NavigateToPose action
-> 根据 action 反馈更新任务状态
-> 到达后触发语音提醒和任务完成逻辑
```

再往后可以继续接入：

```text
YOLOv8 摄像头检测
身份确认
药箱状态检测
异常告警
真实机器人 bringup
```
