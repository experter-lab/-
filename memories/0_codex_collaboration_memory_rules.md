# Codex 协作与记忆规则

更新时间：2026-06-09

## 1. 错误修正必须沉淀

当 Codex 在协作中犯错，尤其是以下类型的小错，修正后必须记录为记忆点，避免下次重复：

- 看错文件、路径、话题名、端口、设备号、参数名或配置项。
- 误判当前系统状态、源码位置、运行入口或部署位置。
- 用错命令参数、launch 参数、ROS 2 话题、服务名或配置 profile。
- 因为忽略已有文档、已有脚本、已有用户改动而走了弯路。

记录格式建议：

```text
错误场景：
错误原因：
正确做法：
下次预防：
相关文件/命令：
```

## 2. 关键点子也必须沉淀

后续调试、优化或架构讨论中，只要出现对项目有长期价值的关键点子，也要记为记忆点，而不是只停留在一次对话里。

适合记录的关键点包括：

- 能显著降低 CPU、温度、延迟或误识别率的优化思路。
- 能提升导航、视觉、底盘、语音、Dashboard 闭环稳定性的设计。
- 影响安全边界、业务状态机、扫码校验、真实机器人行为的决策。
- 被验证有效的测试方法、诊断路径、回滚方案和部署顺序。

记录时应说明上下文、为什么重要、适用范围和潜在风险。

## 3. 本次视觉摸底形成的关键记忆

- 视觉系统原设计是单摄像头统一节点，避免多个进程抢 `/dev/video21`。
- 当前 `D:\A1` 里主要有视觉配置、文档、Dashboard 消费端和测试脚本，未看到 `medicine_vision_detector` 源码包本体；后续改视觉算法前，应先从 RK3588 板端 `/mnt/sdcard/medicine_robot_ws/src/medicine_vision_detector` 同步源码。
- Dashboard 的 `/api/drug_info` 会合并 `/medicine/drug_info` 与 `/medicine/drug_recognition_status`，批次装药/交付会用最新扫码结果核对 `product_code` 和 `trace_id`。
- `pylibdmtx` 默认关闭是稳定性取舍；`zxingcpp` 在 ARM64/RK3588 上也要保留隔离解码与降级路径，不能让扫码库崩溃拖垮主视觉节点。
- 后续视觉优化优先关注扫码 ROI、透视裁剪、候选帧选择、识别结果保持、低功耗调度，以及不破坏装药/交付业务闭环。

## 4. 2026-06-09 视觉优化启动记忆

### 错误场景：PowerShell 中混用了 Bash 写法和复杂 rg 引号

错误原因：
- 当前工作区 shell 是 PowerShell，但误用了 Bash heredoc `python - <<'PY'`。
- 搜索 HTML/JS 片段时，用复杂正则和转义引号导致 `rg` 解析失败。

正确做法：
- 在 Windows/PowerShell 下运行短 Python 代码，优先用 `python -c "..."` 或 PowerShell here-string。
- 搜索包含引号的 HTML/JS 片段时，优先用 `Select-String -SimpleMatch`，或用 `rg -F` 固定字符串并避免复杂转义。

下次预防：
- 运行命令前先确认 shell 语法，不把 Bash 命令习惯带到 PowerShell。
- 对带引号的前端片段，用更小、更简单的搜索词逐步定位。

### 关键优化点：Dashboard 摄像头预览必须按需连接

背景：
- 低功耗视觉配置依赖“无预览客户端时跳过 JPEG 编码”来降低 CPU。
- 原 Dashboard 页面加载后立即连接 `http://<host>:8090/stream.mjpg`，即使用户停留在“配送批次”页，也会让视觉节点持续为浏览器编码预览流。

正确做法：
- 摄像头 MJPEG 流只在“药品识别”标签页激活且浏览器页面可见时连接。
- 切到其它标签页或浏览器页面隐藏时移除 `<img>` 的 `src`，让 8090 预览客户端断开。
- 错误重连也必须受同一可见性条件约束，避免后台反复拉起预览流。

相关文件：
- `dashboard_assets.py`
- `web_dashboard_node_snapshot.py`
- `web_dashboard_node_rk3588_new.py`

### 错误/阻塞场景：不要假设旧 shell 脚本都是有效 UTF-8

错误原因：
- 尝试用 `apply_patch` 重写 `rk3588_switch_vision_config.sh` 时，发现该文件包含 invalid UTF-8 字节，补丁工具无法安全读取。
- 该脚本在 `git status` 中也是未跟踪文件，不能在不了解板端部署来源的情况下强行覆盖。

正确做法：
- 对旧脚本做优化前，先确认编码、跟踪状态和板端实际部署路径。
- 如果需要重写，应先备份原文件，并明确采用 UTF-8 新版本替换；不能在当前轮次用不安全写法硬改。

下次预防：
- 看到中文乱码或历史脚本时，先做 `git status`、编码检查和只读查看。
- `apply_patch` 失败时，不要为了赶进度绕过安全编辑规则强行覆盖。

### 关键优化点：扫码确认必须防止复用旧识别结果

背景：
- Dashboard 批次装药/交付扫码原本可以在 POST payload 为空时，直接 fallback 到 `/api/drug_info` 的最新识别结果。
- 如果识别结果长时间未更新，用户点击确认可能误用上一张标签的 `product_code` / `trace_id`。

正确做法：
- Dashboard 服务端在收到 `/medicine/drug_recognition_status` 时记录 `web_received_at`，并在 `/api/drug_info` 中输出 `scan_age_sec`。
- 前端装药/交付/单任务校验按钮必须调用 `currentScannedKey({ requireFresh: true })`，缺码或超过 `SCAN_MAX_AGE_SEC=8` 秒时直接提示重新扫描。
- 批次装药/交付 POST 应显式携带当前扫码 payload，不依赖后端 fallback。
- 后端 fallback 仍保留，但如果 `scan_age_sec` 超过 `scan_max_age_sec`，返回空码，避免直接 API 调用复用旧码。

相关文件：
- `web_dashboard_node_rk3588.py`
- `dashboard_delivery_batch.py`
- `dashboard_assets.py`
- `test/test_dashboard_delivery_batch.py`
- `test/test_dashboard_vision_preview.py`

## 5. 2026-06-09 PuTTY 板端同步与视觉节点优化记忆

### 关键点：Windows 侧可用 PuTTY 工具访问 RK3588

背景：
- OpenSSH 非交互登录没有免密权限，但用户提供了 PuTTY 目录 `D:\Program Files\PuTTY`。
- `plink.exe` 和 `pscp.exe` 可用于访问 `192.168.31.125` 并同步源码。

正确做法：
- 使用 `plink.exe` 做只读检查和板端命令执行。
- 使用 `pscp.exe` 同步文件。
- 不把用户提供的密码写入记忆文件；需要时按当次用户授权使用。

### 错误场景：plink 远端命令不要混用复杂 heredoc / python -c 引号

错误原因：
- 通过 PowerShell 调用 `plink` 时，再嵌套远端 bash、Python heredoc、`python3 -c` 和引号，容易被本地或远端 shell 吃掉引号。
- 曾导致远端 Python 路径字符串变成未加引号的裸路径，触发 `SyntaxError`。

正确做法：
- 能用 `find`、`grep`、`readlink`、`ls` 完成的检查，不要再套 Python。
- 必须运行复杂远端脚本时，优先放到临时脚本文件后执行，或拆成多个简单 `plink` 命令。
- 含管道和正则的远端命令要尽量拆开，避免 PowerShell 把 `|` 当成本地管道。

### 关键优化点：视觉节点内部也要跳过空闲预览编码

背景：
- 前端已改为只有“药品识别”页可见时连接 `:8090/stream.mjpg`。
- 但板端 `drug_info_detector_node.py` 原本仍会在每次 camera update 中调用 `encode_preview_frame(frame)`，只靠 `preview_encode_period_sec` 限频，不能判断有没有预览客户端。

正确做法：
- 增加 `preview_idle_timeout_sec` 参数，默认 `1.0` 秒。
- `/stream.mjpg` 和 `/snapshot.jpg` 请求调用 `mark_preview_client_active()`。
- `encode_preview_frame()` 在没有近期预览客户端时直接返回，不做 overlay 和 JPEG 编码。
- `/medicine/drug_recognition_status` 增加 `preview_client_request_count`、`preview_client_age_sec`、`preview_encoding_active`，方便确认是否真的进入空闲编码抑制。

部署记录：
- 本地同步源码目录：`D:\A1\board_sync\medicine_vision_detector`。
- 板端视觉源码：`/mnt/sdcard/medicine_robot_ws/src/medicine_vision_detector/medicine_vision_detector/drug_info_detector_node.py`。
- 板端备份：`drug_info_detector_node.py.bak_20260609_preview_idle`。
- 板端 `medicine_vision_detector` 是 symlink/develop 安装，运行入口会回到源码目录，不需要重新 build。

### 板端 Dashboard 同步记录

- 已同步 `dashboard_assets.py`、`dashboard_delivery_batch.py`、`web_dashboard_node.py` 到 `/mnt/sdcard/medicine_robot_ws/src/medicine_web_dashboard/medicine_web_dashboard/`。
- 已备份为 `*.bak_20260609_vision_opt`。
- 板端 `medicine_web_dashboard` 是 symlink/develop 安装，运行入口会回到源码目录。
- 同步内容包括：摄像头预览按需连接、扫码新鲜度保险、`scan_max_age_sec=8.0`。
