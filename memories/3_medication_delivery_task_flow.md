# 记忆库备份：送药业务逻辑、配送批次与任务调度 (Medication Delivery and Task Flow)

## 1. 业务逻辑层架构与数据结构
本小车完全支持并实现了面向医院病房真实配送场景的四级层级式数据管理：
- **配送批次 (DeliveryBatch)**：一个批次代表小车的一次出门配送旅程（如：从药房出发 -> 配送完所有病房 -> 返回药房）。
- **配送站点 (DeliveryStop)**：一个批次包含多个病房停靠点（如：`ward_a`、`ward_b`、`ward_c` 以及最终回到的 `pharmacy` 药房起点）。
- **患者订单 (PatientOrder)**：每个病房停靠点对应一个或多个患者，拥有独立的患者 ID、患者姓名和病床号（`bed_no`）。
- **药品明细 (MedicationItem)**：每个患者下属拥有若干药品明细，包含药品名称、条码追溯码（`trace_id`）和配送确认状态。

## 2. 配送控制台与 REST API
- **主配置文件**：`/mnt/sdcard/medicine_robot_ws/src/medicine_web_dashboard` 内的 REST 服务。
- **业务接口清单**：
  - `GET /api/delivery_batch`：获取当前活动批次的所有站点、患者订单、装药确认状态及异常记录。
  - `POST /api/delivery_batch/import`：解析导入包含完整配送计划的真实 JSON 数据。
  - `POST /api/delivery_batch/load_scan`：装药环节扫码校验（验证药品 trace_id 是否属于该病房该患者，核对成功后标记 `load_confirmed = true`）。
  - `POST /api/delivery_batch/dispense_scan`：病房派发环节扫码校验（验证发放药品的 trace_id，匹配则更新分发状态）。
  - `POST /api/delivery_batch/exception`：标记配送异常，支持：
    - `patient_absent`（患者不在）
    - `drug_exception`（药品破损/异常）
    - `return` / `retry` / `clear_exception` / `manual_review` 等生命周期操作。
  - `POST /api/delivery_batch/advance`：手动/自动推进配送流程状态机。
  - `GET /api/delivery_batch/report`：配送报告数据统计及过滤（支持导出 JSON/CSV 报表，具有过滤、按病房搜索及纯文本打印排版视图）。

## 3. 业务管理器 (Task Manager) 联动
- 业务流和任务管理器节点 `medicine_task_manager` 进行深层次联动：
  - 小车出发前，药师必须对该病房的所有药品进行逐一扫码确认装车（即所有 Medications 均为 `load_confirmed = true`）。
  - 所有药品装车成功后，Web Dashboard 会将所有未配送的药品明细序列化为 JSON Payload，自动发起创建 ROS2 配送任务。
  - `medicine_task_manager` 解析该 Medications JSON，保留 `patient_id` / `patient_name` / `ward_id` / `bed_no`，自动创建配送任务并推进到 `NAVIGATING`（导航中）状态。
  - 只有当前 `medicine_task_manager` 执行的任务 ID 与活动站点的任务 ID 匹配，且任务状态达到 `WAITING_DISPENSE_CONFIRMATION`（在病房等待扫码分发）时，前端配送页面才允许解除“扫码发放”按钮的锁定。

## 4. 双导航后端 (Dual Navigation Backend)
`medicine_task_manager` 支持以下两种导航后端，可在启动时通过 launch 参数进行无缝切换：
- **`simulated` (仿真模式)**：
  - 默认安全模式，无需真实底盘和雷达数据。
  - 通过内置的 `simulate_navigation_duration` 时间参数模拟行驶过程，模拟超时后任务自动流转。
- **`nav2` (真实导航模式)**：
  - 真正与 ROS 2 Nav2 导航协议栈进行 Action 联动。
  - 节点根据 `stations.yaml` 检索目标站点（如 `ward_a`）的物理 `X/Y/Yaw` 坐标。
  - 通过内置的 ROS 2 Action 客户端（接口类型 `nav2_msgs/action/NavigateToPose`）向 Nav2 发送导航目标。
  - 实时订阅反馈，输出 `distance_remaining`（剩余物理距离）在 Dashboard 页面上进行像素级进度条展示。
  - 仅在 Nav2 动作服务器返回 `GoalStatus.STATUS_SUCCEEDED`（成功抵达目标）时，状态机才转换为 `WAITING_DISPENSE_CONFIRMATION`；如若发生路径规划失败、超时（默认 `120.0s`）或中途被取消，则自动进入 `NAVIGATION_FAILED` 异常安全挂起态。
