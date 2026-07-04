# patient_web

病人侧取药终端 UI。前端使用 React + Vite + Tailwind + shadcn/ui 风格组件，部署在 RK3588 的 `8081` 端口，路径为 `/patient/`。

## 现在能做什么

- 床号设置(一次性, 存 localStorage; URL 带 `?bed=A-01` 自动识别)
- 看当前派送 + 状态 + ETA(配送中显示倒计时)
- 看机器人当前位置和与本床位的关系
- 已收到 / 有问题(选原因) 两个大按钮, 回写医护端状态贴纸
- 历史用药记录列表
- 底部"呼叫机器人"按钮, 后端 publish 到 `/medicine/patient_call`
- 病人咨询护士, 医护端可在主控台回复
- 护士/系统消息会在病人端自动刷新

真实后端在 `D:/A1/board_sync/medicine_web_dashboard/medicine_web_dashboard/patient_http.py`。
消息、确认/拒收 override 和历史记录由 `patient_state_store.py` 持久化到 `/mnt/sdcard/medicine_robot_data/patient_state.db`。

## 启动

```bash
cd D:/A1/patient_web
npm install
npm run dev      # http://localhost:5173/patient/
```

开发时 `/patient/api/*` 会按 `vite.config.ts` 代理到板子 `http://192.168.31.125:8081`。

## 后端开关

`src/lib/api.ts` 里的 `USE_MOCK` 当前应保持 `false`，走真实板端接口。只有纯本地 UI 预览时才改成 `true`。

## 构建部署

```bash
npm run build
```

推荐从 `D:/A1` 根目录使用一键脚本:

```powershell
.\sync_patient_web_to_rk3588.ps1
.\sync_patient_web_to_rk3588.ps1 -HostName 192.168.31.125 -HealthBed A-01
.\sync_patient_web_to_rk3588.ps1 -SkipBuild
.\sync_patient_web_to_rk3588.ps1 -SkipBackend
```

脚本会:

- 执行 `npm run build`
- 上传 `dist/` 到 `/mnt/sdcard/medicine_robot_data/patient_web/dist/`
- 上传病人端后端文件到 `medicine_web_dashboard` 包源码
- `colcon build --packages-select medicine_web_dashboard`
- 安装 `/mnt/sdcard/restart_dashboard_with_patient.sh`
- 重启同一个 `medicine_web_dashboard` 节点里的 `8085` 主控台和 `8081` 病人端
- 校验 `/patient/`、`/patient/api/robot_status`、`/api/health`

Windows 双击入口:

```bat
D:\A1\sync_patient_web_to_rk3588.bat
```

## 后端 API 契约

如果板端配置了 `MEDICINE_PATIENT_ACCESS_SECRET` 或 ROS 参数 `patient_access_secret`, 下列表中所有带 `bed` 的病人端 API 都会校验床位 token。token 可以通过 URL 查询参数 `t=...` / `token=...` 或请求头 `X-Patient-Token` 传入。密钥为空时不启用校验, 兼容旧演示 URL。

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/patient/api/delivery?bed=A-01` | 当前派送(无则返回 `data:null`) |
| GET | `/patient/api/order?bed=A-01` | 旧路径兼容, 同上 |
| GET | `/patient/api/history?bed=A-01&days=7` | 历史记录 |
| GET | `/patient/api/robot_status?bed=A-01` | 机器人当前位置、任务状态、是否服务本床 |
| GET | `/patient/api/messages?bed=A-01` | 病人/护士会话, 读取时自动标记病人已读 |
| POST | `/patient/api/deliveries/{id}/confirm` | 病人确认收药, body: `{bed}` |
| POST | `/patient/api/deliveries/{id}/reject` | 病人反馈问题, body: `{bed, reason}` |
| POST | `/patient/api/call_robot` | 呼叫请求, body: `{bed, reason?}` |
| POST | `/patient/api/messages` | 病人留言, body: `{bed, content, delivery_id?}` |

数据 schema 见 `src/lib/types.ts`。

## 相关端口

- 病人端: `http://192.168.31.125:8081/patient/?bed=A-01`
- 医护主控台: `http://192.168.31.125:8085/`
- 实车导航页: `http://192.168.31.125:8085/navigation`

## 床位 token

开启方式是在启动 `medicine_web_dashboard` 前设置同一个密钥:

```bash
export MEDICINE_PATIENT_ACCESS_SECRET='换成一串足够长的随机密钥'
/mnt/sdcard/restart_dashboard_with_patient.sh
```

生成床位 URL:

```powershell
cd D:\A1
$env:MEDICINE_PATIENT_ACCESS_SECRET='换成同一串密钥'
python .\make_patient_web_token.py --bed A-01 --host 192.168.31.125
```

输出的第二行类似:

```text
http://192.168.31.125:8081/patient/?bed=A-01&t=v1....
```

把这个 URL 做成床旁二维码即可。token 默认有效期 30 天，可用 `--ttl-sec` 调整。

## 主题

emerald(医院青绿色), CSS 变量在 `src/index.css` 的 `:root` 里。
病人友好: 字号偏大(17px base), 按钮高 48-80px, 圆角 12px。
