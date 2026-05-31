# 记忆库备份：M2 麦克风阵列与科大讯飞 AIKit 语音识别 (M2 Microphone and AIKit ESR)

## 1. 硬件麦克风阵列与物理接口
- **硬件模块**：科大讯飞 M2 环形麦克风语音拾音阵列（由 WHEELTEC 生产）。
- **物理接口**：
  - 默认使用 USB 串口线接入：`/dev/ttyACM0`。
  - 支持直接免驱动热插拔。

## 2. 科大讯飞 AIKit 离线指令词识别 (ESR) SDK
- **SDK 版本**：科大讯飞提供给 WHEELTEC 的离线语音唤醒及命令词识别专用开发包 `Linux_awaken_esr_xtts_aisound_v2.2.15-rc5`。
- **授权密钥管理**：
  - **核心鉴权文件**：离线鉴权证书及 API 密钥。为防止版本泄露，其敏感配置不直接硬编码在代码仓库里，而是统一部署在环境文件中：`~/.config/medicine_robot/aikit.env`（设置只读安全权限 `chmod 600`）。
  - **AppID/APISecret/APIKey 纠错历史**：开发过程中，曾因图片扫描文字混淆（把相似字符和大小写字母读错）导致 AIKIT_Init 报 18714 鉴权鉴错码。目前已确认为以下解密十六进制鉴权，验证测试全部通过并获取到本地离线授权文件。

## 3. ROS2 离线语音识别节点 (wheeltec_aikit_esr)
- **开发节点**：在本地及 RK3588 工作空间内，编写编译了 `wheeltec_aikit_esr` ROS2 包。
- **运行原理**：
  - 加载本地 GBK / GB18030 字符集语料 FSA 文件 `medicine_cn_fsa.txt`（包含医院特定的病房派送指令，如“*送药到B病房*”、“*取消当前配送任务*”）。
  - 内置 GB18030 到万国码 UTF-8 的运行时动态转换函数，防止终端及 ROS 话题数据中文乱码。
  - 过滤 SDK 输出的无用内部标签与标点符号。
  - 支持多音频后端切换（PulseAudio 模式、ALSA 模式、以及 PCM 离线文件灌入模式）。
  - 识别成功后向 ROS2 发布 `/voice_words`（`std_msgs/String`）文本话题。

## 4. 语音指令分发器 (voice_command_dispatcher)
- **核心组件**：`voice_command_dispatcher_node`。
- **业务中转逻辑**：
  - 实时订阅离线识别文本话题 `/voice_words`。
  - 提取关键命令词并转译。
  - 映射解析：
    - 如识别到“*送药到B病房*”，自动在后台构建去往 `ward_b` 的目标任务载荷，向业务控制台发布 `/medicine/create_delivery_task`。
    - 如识别到“*取消配送*”，自动构建取消请求并向后台发布 `/medicine/cancel_delivery_task`。
  - 经过端到端链路仿真测试，语音指令成功连通业务状态机，实现一句话创建/取消任务。
