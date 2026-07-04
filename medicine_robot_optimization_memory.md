# 药品配送机器人系统优化记忆点

更新时间：2026-06-27

## 后续优化总目标

把当前系统优化成完整闭环：

外部批次导入 → 药房装药核验 → 机器人配送 → 病人端查看 / 语音问药 / 签收或反馈 → 护士端复核处理 → 配送报告归档。

核心目标：

1. 病人端老人能看懂、会操作。
2. 护士端能快速发现并处理异常。
3. 药品识别要服务当前配送批次，而不是只显示 OCR 原文。
4. 每次配送、签收、反馈、复核都要可追溯。

---

## 推荐实施优先级

### 第一优先级：8085 异常集中处理区

下次优先做这个。

目标：在 8085 工作台新增“异常处理中心”，集中显示：

- 病人反馈问题
- 待用药复核
- 病人不在床旁
- 超时未签收
- 药品识别不匹配
- 配送异常

每条异常显示：

- 床号
- 病人姓名
- 异常类型
- 异常原因
- 发生时间
- 当前状态
- 处理按钮

操作按钮：

- 查看病人
- 定位病人卡片
- 复核通过
- 退回药房
- 联系病人
- 标记已处理

验收标准：

- 护士不用滚动找异常。
- 所有异常集中展示。
- 点击异常可以定位到具体病人卡片。
- 处理结果写入报告和审计记录。

---

### 第二优先级：8081 老人模式

目标：让病人端更适合老人、小孩、孕妇使用。

功能：

- 普通 / 大字 / 超大字模式
- 高对比度清晰模式
- 药名、剂量、频次、注意事项放大
- “本人确认签收”“药品有疑问”“咨询护士”“问药语音”按钮更大
- 老人患者 age >= 60 默认大字模式

验收标准：

- 手机端不用缩放也能看清药名。
- 签收和反馈按钮容易区分。
- 误操作风险降低。

---

### 第三优先级：JSON 本地导入 + 预览

目标：为真实 HIS / 药房系统接入做准备。

功能：

- 8085 增加“从本地 JSON 文件导入”入口
- 导入前校验字段
- 导入前预览病房、病人、药品数量
- 用户确认后才采用
- 导入后 8081 能按床位查到对应病人

验收标准：

- JSON 错误不覆盖当前批次。
- 导入前可预览。
- 支持三病房三病人模板。

---

## 后续中期优化

### 药品识别闭环

1. 条形码用于药品追溯码 / 产品码 / 批号。
2. OCR 用于辅助识别药名、规格、厂家、有效期。
3. OCR 原文不能直接作为有用信息，必须二次筛选。
4. 识别结果必须和当前配送批次匹配。
5. 匹配后需要人工确认，再写入装药记录。

### 摄像头和 OCR 画质

1. Web 预览流和 OCR 高清识别帧分离。
2. OCR 点击时抓高清单帧。
3. 条形码框和 OCR 框独立。
4. 增加药盒摆放、反光、距离提示。

### 报告和追溯

每个批次报告应包含：

- 批次号
- 来源
- 病房路线
- 病人列表
- 药品列表
- 装药记录
- 配送记录
- 签收记录
- 反馈记录
- 复核记录
- 异常记录
- 完成时间

---

## 后续智能化方向

### 问药语音助手

语音上下文必须来自：

- 当前床位
- 当前病人
- 当前配送批次
- 当前药品清单
- 年龄 / 性别 / 诊断 / 过敏史

禁止把摄像头 OCR 内容作为当前病人问药上下文。

回答规则：

1. 不擅自改医嘱。
2. 不建议加量、减量、停药。
3. 不确定时提示问护士。
4. 高风险症状直接转人工。

高风险包括：胸痛、呼吸困难、严重过敏、昏迷、孕妇用药不确定、儿童剂量不确定、服错药、吃多了、药物过敏。

---

## 当前默认下一步

下次继续优化时，默认从：

8085 异常集中处理区

开始做。

理由：当前已经有病人反馈、复核、签收闭环，但异常还分散在不同区域。先集中异常处理，可以让系统更像真实医院工作台，也方便后续接入 JSON 导入和药品识别闭环。

---

## 2026-06-28 已完成：8085 异常处理中心第一版

本次已在 8085 配送执行页完成异常集中处理区第一版。

### 已实现

1. 在病房 / 病人 / 药品清单上方新增“异常处理中心”。
2. 在批次概览中新增异常摘要：
   - 反馈 / 异常
   - 待复核
   - 未签收
   - 已签收
3. 异常中心从当前批次聚合：
   - 病人反馈问题
   - 待用药复核
   - 病人不在
   - 超时未签收
   - 药品异常
   - 药品回收
   - 识别不匹配
4. 每条异常显示：
   - 床号
   - 病人姓名
   - 病房
   - 药品名（如有）
   - 异常类型
   - 原因
   - 时间（如有）
5. 每条异常复用现有处理动作：
   - 定位病人
   - 复核通过
   - 退回药房
   - 稍后重试
   - 药师复核
   - 已处理
   - 联系病人
6. 已部署到 RK3588，并验证 8085 页面加载包含：
   - exception_center
   - collectBatchExceptions
   - renderExceptionCenter
   - exception_stat_critical

### 后续建议

下一步可以继续做：

1. 让异常中心支持筛选：全部 / 反馈 / 待复核 / 未签收 / 药品异常。
2. 增加“只看高优先级”开关。
3. 将病人未读咨询也纳入异常中心。
4. 处理完成后在异常中心显示最近处理记录。
5. 再做 8081 老人模式。

## 2026-06-28?8085 ?????????
- ????8085 ??????????????????????????????????????????
- ????????????????????????????????????????????
- ????????????????????????????????????????????
- ??????????????????HTML ???????JS ???? Unicode escape????????????
- ?????board_sync/medicine_web_dashboard/medicine_web_dashboard/dashboard_assets.py
- ?????RK3588 /mnt/sdcard/medicine_robot_ws/src ? build ? medicine_web_dashboard/dashboard_assets.py
- ???8085 ???? exception_filter_all?pending_message_risk?renderExceptionCenter?collectMessageExceptions?exception_stat_critical??? question4 count=0?
- ??????????? 8085 ???????????????????????????????/??????????

## 2026-06-28?8085 ??????????
- ????????????????????????????????????????????
- ???????????? data-audit-* ??????????? patient_id?medication_id?bed_no ???
- ???????????????????????????????????????????
- ?????????????????????????????????????????????????
- ?????board_sync/medicine_web_dashboard/medicine_web_dashboard/dashboard_assets.py
- ?????8085 ???? focusExceptionAudit?auditFilterForExceptionType?data-audit-patient?patient_rejected?medication_return?????????? question4 count=0?
- ????????????????????????????????????????????/??????????????????????????

## 2026-06-28?????????????
- ????8085 ?????????????? record_patient_message_audit ?????????????? patient_message_reply?
- ????8085 ???????/??????????????????????? patient_message_read?
- ????/api/patient_messages/reply ? /api/patient_messages/read_all ???????????????? batch?????????????????
- ????8085 ???????????????????????????? patient_message_reply / patient_message_read?
- ?????board_sync/medicine_web_dashboard/medicine_web_dashboard/web_dashboard_node.py?dashboard_http.py?dashboard_assets.py
- ?????8085 ???? patient_message_reply?patient_message_read?messageAuditEvents?resp && resp.batch??????? record_patient_message_audit ? read_all nurse_name ????? question4 count=0?
- ??????????? shell for ???? $f?PowerShell ??????????????????????????
- ????????? 8081 ??????????/??????????????????????

## 2026-06-28?8081 ?????????
- ????8081 ?????????????????????????????????????????????????????????????
- ????8081 ??????????????????????????? / ????? / ???????????????????????
- ?????????????????????????? / ????????????????????
- ?????patient_web/src/components/ContactNurseButton.tsx?patient_web/src/components/MessageDialog.tsx
- ?????npm run build ???dist ? Home chunk ?? read_by_nurse/read_by_patient ???? className ???
- ???????? /mnt/sdcard/medicine_robot_data/patient_web/dist ? chunk ??????? dist???????
- ?????????????????????????????/????????????????????

## 2026-06-28?8081 ??????????
- ????8081 ???????? unreadFromNurse > 0 ???????????????????????????????????
- ???????????????????????????????????????
- ?????? JSX ????? Unicode escape ???????????????????????????????????
- ?????patient_web/src/components/ContactNurseButton.tsx
- ?????npm run build ???dist Home chunk ??????????????????????ring-ok/10 animate-soft-pulse?bg-ok/12?read_by_patient?
- ??????????? /mnt/sdcard/medicine_robot_data/patient_web/dist??? dist ????????????
- ???????????????????????????????????????????????????

## 2026-06-28 | 8081 patient elderly reminder strategy
- Added patient-side settings fields: elderlyModeEnabled, nurseAlertSoundEnabled, nurseBrowserNotificationEnabled, quietHoursEnabled.
- Updated SettingsContext with setters and localStorage persistence, preserving old notificationEnabled compatibility.
- Updated SettingsDialog with elderly mode, delivery reminder, nurse reply sound, browser/mobile notification, and 21:00-07:00 quiet-hours controls.
- Updated ContactNurseButton to read settings, enlarge urgent nurse-reply banner in elderly mode, and keep visual banner active even when quiet hours suppress sound/system notifications.
- Updated useNurseMessageAlerts to support sound/browser/title/quiet-hours options while keeping first-poll baseline protection to avoid duplicate alerts.
- Build/deploy completed for 8081: dist uploaded to /mnt/sdcard/medicine_robot_data/patient_web/dist and web service restarted. Verified ports 8081/8085 listening.
- Gotcha: PowerShell here-strings corrupted newly written Chinese text into question marks in TSX. Rewrote new UI Chinese as JS unicode escapes / ASCII-safe source and rebuilt. Remote assets now contain expected Chinese labels.

## 2026-06-28 | 8081 mobile viewport overflow fix
- Fixed patient-web mobile layout not fitting narrow phone screens.
- Root CSS now constrains html/body/#root to width/max-width 100% and overflow-x hidden; app-shell now uses width:100% and max-width:min(560px,100%).
- Button base no longer globally uses whitespace-nowrap; large/xlarge buttons use min-height and wrapping-friendly padding.
- HeroCard grids now collapse for narrow screens, verification text is split into wrapped lines instead of one long inline sentence.
- ReportIssueCard, DeliveryCard, RobotStatusCard and OrderProgress now use min-w-0 / wrapping labels / wrapping buttons to avoid page-wide horizontal overflow.
- Built and deployed to RK3588 patient web dist; verified 8081 and 8085 listening and remote CSS/JS contain overflow/mobile-fit/wrapping changes.

## 2026-06-28 | 8081 mobile dialog adaptation
- What: Made 8081 patient-side dialogs phone-safe after main page mobile overflow was fixed.
- Why: Phone screenshots showed horizontal overflow and clipped content; modals/floating layers needed the same narrow-screen guarantees.
- Where: patient_web/src/components/ui/dialog.tsx; DrugDetailDialog.tsx; HistoryList.tsx; NotificationsDialog.tsx; MessageDialog.tsx; SettingsDialog.tsx.
- Learned: Large-font patient UI needs `svh` max-height, `w-[calc(100vw-1.5rem)]`, `min-w-0`, wrap-friendly buttons, and break-all for IDs; fixed nowrap/min-width in dialogs causes mobile overflow even after the main shell is fixed.
- Deploy: Built with `npm run build`, deployed patient_web/dist to RK3588 `/mnt/sdcard/medicine_robot_data/patient_web/dist`, restarted delivery web service, verified ports 8081 and 8085 listening.

## 2026-06-28 | 8081 mobile hardening pass
- What: Hardened remaining patient-web mobile layouts against narrow-screen overflow.
- Why: Phone screenshots showed the patient route could still clip content on small screens after the main overflow fix; remaining risk was fixed-width controls and multi-column sections.
- Where: patient_web/src/components/ContactNurseButton.tsx; SettingsDialog.tsx; AppHeader.tsx; HeroCard.tsx; pages/BedSetup.tsx.
- Learned: The sticky bottom action bar should collapse to one column below ~390px; settings font-scale controls need 2 columns on phones; bed setup needs smaller header spacing and wrap-safe identity fields. Avoid Chinese text matching in PowerShell/Python patches when terminal encoding may interfere; match structural class strings instead.
- Deploy: Built patient_web and deployed to RK3588; verified 8081 and 8085 listening with new assets index-FcGc5YKu.js and Home-DyFbIsUF.js.

## Session Summary | 2026-06-28 | 8081 mobile UI optimization pause

## Goal
Continue optimizing the 8081 patient-side mobile UI so it fits phone screens without horizontal overflow, while keeping 8085 service unaffected.

## Instructions
- User prefers direct practical progress updates in Chinese.
- UI must remain elderly-friendly: large readable text, simple interactions, clear buttons.
- If needed, future optimization plan can be adjusted rather than followed rigidly.

## Discoveries
- Engram mem_* tools are not available in this Codex environment, so project memory is being mirrored to D:\A1\medicine_robot_optimization_memory.md.
- 8081 mobile overflow was not only from the main shell; dialogs, sticky bottom actions, settings controls, and bed setup page also needed independent small-screen handling.
- PowerShell/Python patches should avoid matching Chinese text directly because terminal encoding can prevent matches; structural class matching is safer.

## Accomplished
- Fixed 8081 mobile dialog/floating-layer adaptation: drug details, nurse message dialog, notifications, settings, and history detail.
- Fixed remaining mobile layout risks: sticky bottom action buttons collapse below 390px, settings font-scale buttons use 2 columns on phones, header icons are tighter, bed setup page spacing/wrapping improved.
- Built patient_web successfully with npm run build.
- Deployed latest 8081 patient_web dist to RK3588.
- Restarted RK3588 web service and verified 8081 and 8085 are listening.

## Next Steps
- User should test 8081 on phone after refresh.
- If screenshots still show clipping, continue with targeted component fixes.
- Next likely optimization: visual polish of 8081/8085 consistency, patient-side workflow clarity, or 8085 workbench mobile/responsive cleanup.

## Relevant Files
- patient_web/src/components/ui/dialog.tsx — phone-safe dialog base width and title/description wrapping.
- patient_web/src/components/DrugDetailDialog.tsx — mobile-safe medicine detail dialog.
- patient_web/src/components/MessageDialog.tsx — mobile-safe nurse consultation dialog.
- patient_web/src/components/NotificationsDialog.tsx — mobile-safe notification center.
- patient_web/src/components/SettingsDialog.tsx — responsive settings controls.
- patient_web/src/components/ContactNurseButton.tsx — sticky bottom actions collapse on narrow phones.
- patient_web/src/components/AppHeader.tsx — tighter mobile header.
- patient_web/src/components/HeroCard.tsx — patient info card mobile wrapping.
- patient_web/src/pages/BedSetup.tsx — mobile bed setup page spacing/wrapping.
- D:\A1\medicine_robot_optimization_memory.md — local project memory fallback.

## 2026-06-28 | 8085 responsive hardening pass
- What: Added tablet/mobile responsive fallback CSS for the 8085 dashboard workbench without changing business JS.
- Why: After 8081 mobile hardening, the next risk was 8085 workbench layout overflow on narrower screens due to header/runtime strip, tab nav, batch 3-column layout, exception center, route visualization, report grids, and IM message panel.
- Where: board_sync/medicine_web_dashboard/medicine_web_dashboard/dashboard_assets.py and root dashboard_assets.py; deployed to RK3588 source plus actual loaded build path /mnt/sdcard/medicine_robot_ws/build/medicine_web_dashboard/medicine_web_dashboard/dashboard_assets.py.
- Learned: RK3588 runtime imports dashboard_assets.py from the build path, not directly from src, so deploying only to src is insufficient. For 8085 CSS-only fixes, patch both local board_sync and root copies, then copy to remote src and build loaded path.
- Deploy: py_compile passed locally and remotely; service restarted; verified 8081/8085 listening and curl http://127.0.0.1:8085/ contains the 2026-06 mobile/tablet hardening marker.

## 2026-06-28 | 8085 readability and action-density hardening
- What: Added CSS-only readability/action-density refinements to 8085 workbench after responsive hardening.
- Why: Nurse/pharmacy workbench needed lower mis-tap risk and clearer information hierarchy for exception cards, patient/medication cards, audit rows, and patient-message IM controls.
- Where: board_sync/medicine_web_dashboard/medicine_web_dashboard/dashboard_assets.py and root dashboard_assets.py; deployed to RK3588 src plus actual loaded build path.
- Learned: Safe 8085 UI polishing can be done as CSS-only layers with markers; keep business JS untouched. For operator-facing screens, buttons need minimum touch height, long ids/reasons must wrap anywhere, and warning/review/rejected states need clear but restrained semantic backgrounds.
- Deploy: py_compile passed locally and remotely; service restarted; verified 8081/8085 listening and curl http://127.0.0.1:8085/ contains the 2026-06 readability/action hardening marker.

## 2026-06-28 | 8085 external JSON import preview validation

**What**: Added an import-before-adopt preview and validation flow for 8085 external delivery batch JSON.
**Why**: External HIS/pharmacy batch data should be reviewed before becoming a pending batch; local file selection must not directly mutate pending delivery state.
**Where**: `D:\A1\board_sync\medicine_web_dashboard\medicine_web_dashboard\dashboard_assets.py`, `D:\A1\dashboard_assets.py`, deployed to RK3588 build/src dashboard assets.
**Learned**: The previous local JSON file import path already existed, but it immediately posted to `/api/delivery_batch/import`; the safer workflow is load file -> preview/field validation -> manual “接收为待采用” -> adopt pending batch.
**Deploy**: Uploaded to `/tmp/dashboard_assets.py`, copied into RK3588 src/build dashboard asset paths, restarted `/mnt/sdcard/rk3588_delivery_webctl.sh restart`, verified 8081/8085 listening and 8085 HTML contains `batch_import_preview` plus `previewBatchImportPayload`.

## 2026-06-28 | 8085 batch workflow next-step guide

**What**: Added an operator-facing “下一步操作” guide to the 8085 delivery execution page.
**Why**: After external JSON import/adoption, operators needed a clear prompt for the next safe action instead of choosing among many buttons; this reduces misoperation in the delivery workflow.
**Where**: `D:\A1\board_sync\medicine_web_dashboard\medicine_web_dashboard\dashboard_assets.py`, `D:\A1\dashboard_assets.py`, deployed to RK3588 src/build dashboard assets.
**Learned**: Keep the existing safety gate responsible for blocking/allowing phase advance; add a separate guide for “what to do next”. The guide should be derived from `latestDeliveryBatch`, exception counts, review state, patient messages, current route status, and safety blockers. Static Chinese inserted via PowerShell can become question marks, so static fallback text should use HTML entities or JS unicode escapes.
**Deploy**: Uploaded dashboard_assets.py to RK3588, copied into src/build loaded paths, board-side py_compile passed, restarted `/mnt/sdcard/rk3588_delivery_webctl.sh restart`, verified 8081/8085 listening and 8085 HTML contains `batch_workflow_guide` plus `renderWorkflowGuide`.

## 2026-06-28 | 8085 report archive readiness gate

**What**: Added a “归档前检查” gate to the 8085 delivery report page.
**Why**: The report page already summarized delivery data, but operators needed an explicit final-archive readiness check to avoid treating unfinished delivery batches as completed records.
**Where**: `D:\A1\board_sync\medicine_web_dashboard\medicine_web_dashboard\dashboard_assets.py`, `D:\A1\dashboard_assets.py`, deployed to RK3588 src/build dashboard assets.
**Learned**: Report archival should be separate from raw export buttons. The gate checks un-loaded medications, loaded-but-not-delivered medications, unresolved medication exceptions, pending patient medication reviews, and unsigned patients; it gives actions to filter unclosed details or return to delivery execution. Use HTML entities/JS unicode escapes for new static Chinese to avoid mojibake.
**Deploy**: Uploaded dashboard_assets.py to RK3588, copied into src/build loaded paths, board-side py_compile passed, restarted `/mnt/sdcard/rk3588_delivery_webctl.sh restart`, verified 8081/8085 listening and 8085 HTML contains `report_archive_gate`, `renderReportArchiveGate`, and `buildReportArchiveGate`.


## 2026-06-28 | 8085 batch closure timeline

**What**: Added a compact ????????? to the 8085 delivery execution page under the next-step guide.
**Why**: Operators need a quick whole-process view of external import, adoption, pharmacist loading, departure, bedside handover, patient signing, exception handling, and report archiving, instead of inferring progress from scattered panels.
**Where**: `D:\A1oard_sync\medicine_web_dashboard\medicine_web_dashboard\dashboard_assets.py`, `D:\A1\dashboard_assets.py`, deployed to RK3588 src/build dashboard asset paths.
**Learned**: Keep the timeline as a state navigator, not another heavy card grid. It should derive from `latestDeliveryBatch`, `latestPendingBatch`, report rows, receipt stats, exception center, and archive gate readiness. Static Chinese should remain HTML entities or JS unicode escapes to avoid `????` corruption.
**Deploy**: Uploaded to `/tmp/dashboard_assets.py`, copied into RK3588 runtime src/build paths, board-side py_compile passed, restarted `/mnt/sdcard/rk3588_delivery_webctl.sh restart`, verified 8081/8085 listening and 8085 HTML contains `batch_closure_timeline` plus `renderBatchClosureTimeline`.


## Session Summary | 2026-06-29

## Goal
Continue optimizing the medicine delivery robot Web system, especially the 8085 nurse/workbench delivery workflow and its closed-loop visibility.

## Instructions
- User prefers pragmatic, direct progress without unnecessary explanation.
- UI changes should remain restrained and task-focused, following the installed impeccable/product UI rules.
- If future optimization requires changing the plan, micro-adjustments are acceptable; the saved optimization plan is a guide, not a rigid constraint.

## Discoveries
- The active 8085 dashboard asset must be deployed to the RK3588 build/runtime paths, not only the src path.
- Static Chinese inserted through shell scripts can become `????`; use HTML entities in static HTML and JS Unicode escapes in dynamic strings.
- The 8085 workflow now benefits from a state navigator rather than more separate panels.

## Accomplished
- Added and deployed a compact 8085 ????????? under the next-step guide.
- Timeline covers import, adoption, pharmacist loading, departure, bedside handover, patient signing, exception handling, and report archiving.
- Timeline nodes can jump to the corresponding handling areas such as load scan, dispense scan, exception center, and report archive gate.
- Local and RK3588 board-side Python compile checks passed.
- Restarted RK3588 Web service and verified 8081/8085 are listening and 8085 HTML includes `batch_closure_timeline` / `renderBatchClosureTimeline`.

## Next Steps
- Visually inspect the new 8085 timeline on the real browser and adjust density/wording if it feels crowded.
- Continue optimizing both 8081 patient terminal and 8085 workbench around the full loop: external batch import -> loading -> delivery -> patient sign/feedback -> nurse review -> report archive.
- Consider adding clearer completion/blocked explanations directly on each timeline node if operators still need more guidance.

## Relevant Files
- D:\A1oard_sync\medicine_web_dashboard\medicine_web_dashboard\dashboard_assets.py ? main 8085/8081 frontend asset modified and deployed.
- D:\A1\dashboard_assets.py ? synchronized root copy of dashboard asset.
- D:\A1\medicine_robot_optimization_memory.md ? local fallback project memory and session summaries.


## 2026-06-29 | 8085 batch scan match preview

**What**: Added a 8085 ???????? preview before pharmacist load scan / bedside dispense confirmation.
**Why**: The previous flow could directly write load/dispense audit after clicking the scan button; operators needed to see which current-batch medication and patient the latest barcode/trace result would match before confirming.
**Where**: `D:\A1oard_sync\medicine_web_dashboard\medicine_web_dashboard\dashboard_assets.py`, `D:\A1\dashboard_assets.py`, deployed to RK3588 src/build dashboard asset paths.
**Learned**: Backend matching is already strict and only writes records when product_code/trace_id matches the current batch; OCR drug name remains auxiliary. The frontend preview should mirror this strict rule and explicitly tell users OCR-only recognition cannot write load/dispense records.
**Deploy**: Local and RK3588 py_compile passed, restarted `/mnt/sdcard/rk3588_delivery_webctl.sh restart`, verified 8081/8085 listening and 8085 HTML contains `batch_scan_preview`, `buildBatchScanPreview`, and `buildBatchScanConfirmText`.

## 2026-06-29 | 8085 backend scan preview API
**What**: Added a read-only backend scan preview API `/api/delivery_batch/scan_preview` and made the 8085 delivery workflow preview/confirm dialog prefer backend matching results.
**Why**: The previous preview was only frontend-estimated, which could diverge from the strict backend load/dispense write logic.
**Where**: `board_sync/medicine_web_dashboard/medicine_web_dashboard/dashboard_delivery_batch.py`, `dashboard_http.py`, `dashboard_assets.py`; deployed to RK3588 src/build runtime paths.
**Learned**: Keep OCR drug name auxiliary only; load/dispense writes still require strict `product_code` or `trace_id`. Use Unicode escapes for newly inserted Chinese strings to avoid `????` mojibake through Windows/SSH copy paths.
**Verify**: `python -m py_compile` passed locally and on RK3588; `POST /api/delivery_batch/scan_preview` with `X-Requested-With: medicine-dashboard` returned `NO_CODE` with normal Chinese message.

## 2026-06-29 | Large-scale 8081/8085 usability hardening
**What**: Performed a broad optimization pass across the 8081 patient web and 8085 operator dashboard: patient API safe request handling, mobile anti-overflow rules, data refresh status strip, speech cleanup on dialog close, 8085 toast feedback, busy-state guards for critical batch buttons, and patient voice announce mojibake repair.
**Why**: User asked for 1-2 hours of large-scale unattended optimization while preserving existing medication delivery workflows.
**Where**: `patient_web/src/lib/api.ts`, `patient_web/src/pages/Home.tsx`, `patient_web/src/components/DrugDetailDialog.tsx`, `patient_web/src/index.css`, `board_sync/medicine_web_dashboard/medicine_web_dashboard/dashboard_assets.py`, `patient_http.py`; deployed 8081 dist to `/mnt/sdcard/medicine_robot_data/patient_web/dist` and Python runtime files to RK3588 src/build paths.
**Learned**: When deploying Vite dist from Windows to Linux, do not use PowerShell `Compress-Archive` because it stored `assets\file.js` names; use Python zipfile with POSIX `as_posix()` paths so `/patient/assets/*.js` resolves correctly.
**Verify**: `npm run build` passed for 8081; `python -m py_compile` passed; extracted 8085 inline JS passed `node --check`; RK3588 ports 8081/8085 listen; `/patient/` returns updated HTML, `/patient/assets/index-qnBe_MGe.js` returns JS, `/patient/api/voice/announce` returns `??????`, and `/api/delivery_batch/scan_preview` still returns normal Chinese JSON.



---

## 2026-06-29 | 8085 ????? 8081 ?????

**What**: ? 8085???????????????????? 8085 ????8081 ????????/ROS2?????????????????? 8081 ????????????????

**Why**: ??????????????????????/?????????????

**Where**:
- `D:\A1oard_sync\medicine_web_dashboard\medicine_web_dashboard\dashboard_assets.py`
- `D:\A1\dashboard_assets.py`
- `D:\A1\patient_web\src\pages\Home.tsx`
- RK3588: `/mnt/sdcard/medicine_robot_ws/src/medicine_web_dashboard/medicine_web_dashboard/dashboard_assets.py`
- RK3588: `/mnt/sdcard/medicine_robot_data/patient_web/dist`

**Learned**: ?? PowerShell/SSH ?????????????? shell ?????????????????? Python UTF-8 ???? Unicode escape ??????????


---

## 2026-06-29 | Added backend health check for 8085 system monitor

**What**: Added `/api/health_check` to the 8085 dashboard backend and updated the System Monitor self-check panel to render backend-verified status instead of only frontend-derived state.

**Why**: The operator needs a trustworthy single place to verify 8085, 8081, voice chain, vision/OCR, chassis/ROS2, delivery batch, and hardware load before continuing delivery operations.

**Where**:
- `D:\A1oard_sync\medicine_web_dashboard\medicine_web_dashboard\dashboard_http.py`
- `D:\A1oard_sync\medicine_web_dashboard\medicine_web_dashboard\web_dashboard_node.py`
- `D:\A1oard_sync\medicine_web_dashboard\medicine_web_dashboard\dashboard_assets.py`
- RK3588 deployed copies under `/mnt/sdcard/medicine_robot_ws/src/...`, `/mnt/sdcard/medicine_robot_ws/build/...`, and install build-lib path when present.

**Learned**: PowerShell can expand `$f` inside remote bash snippets and corrupt deployment commands; use single-quoted here-strings for remote shell loops. Chinese literals in Python code should be written with Unicode escapes when passing through this shell stack, then verified through `encode('unicode_escape')` from the running board.


---

## 2026-06-29 | Added guided actions to 8085 health check

**What**: Extended `/api/health_check` to return safe operator actions and added a `health_check_actions` button area in the 8085 System Monitor self-check panel.

**Why**: The health panel should not only report failures; it should guide the operator to the relevant screen or control without adding risky one-click service restarts.

**Where**:
- `D:\A1oard_sync\medicine_web_dashboard\medicine_web_dashboard\web_dashboard_node.py`
- `D:\A1oard_sync\medicine_web_dashboard\medicine_web_dashboard\dashboard_assets.py`
- RK3588 deployed copies under `/mnt/sdcard/medicine_robot_ws/src/...`, `/mnt/sdcard/medicine_robot_ws/build/...`, and install build-lib path when present.

**Learned**: Health-check actions should stay low-risk: refresh health, open patient web, switch dashboard tab, or focus an existing control. Avoid direct restart/repair buttons until permission, audit trail, and rollback behavior are designed.


---

## 2026-06-29 | Added traceable health-check summary and details

**What**: Added last-check metadata and an expandable health-check detail list to the 8085 System Monitor self-check panel.

**Why**: Operators need traceability: not just a badge, but when the check ran, how many items are ok/warn/bad, and which specific subsystem produced each status and action.

**Where**:
- `D:\A1oard_sync\medicine_web_dashboard\medicine_web_dashboard\dashboard_assets.py`
- `D:\A1\dashboard_assets.py`
- RK3588 deployed dashboard assets copies under `/mnt/sdcard/medicine_robot_ws/src/...`, `/mnt/sdcard/medicine_robot_ws/build/...`, and install build-lib path when present.

**Learned**: For operator dashboards, health panels should include three layers: summary badge, actionable buttons, and expandable details. This keeps the default UI simple while preserving diagnostic depth.


---

## 2026-06-29 | Surfaced health check alerts in 8085 top navigation

**What**: Added a `health-tab-badge` and `health-tab-hint` to the 8085 System Monitor tab, synchronized with `/api/health_check` summary counts.

**Why**: Operators may stay on delivery or vision pages; health warnings should be visible from the top navigation without requiring the operator to open System Monitor first.

**Where**:
- `D:\A1oard_sync\medicine_web_dashboard\medicine_web_dashboard\dashboard_assets.py`
- `D:\A1\dashboard_assets.py`
- RK3588 deployed dashboard assets copies under `/mnt/sdcard/medicine_robot_ws/src/...`, `/mnt/sdcard/medicine_robot_ws/build/...`, and install build-lib path when present.

**Learned**: Cross-page operational warnings belong in navigation as low-noise badges: hidden when all ok, amber for warn, red for bad.


---

## 2026-06-29 | Added deduplicated health-change toasts

**What**: Added state-change notifications for the 8085 health check: first load is silent, warn/bad transitions show one toast, recovery to ok shows one toast, and repeated identical states are ignored.

**Why**: Operators may miss top-nav badge changes during workflow; state-change toasts surface new risk without creating alert fatigue.

**Where**:
- `D:\A1oard_sync\medicine_web_dashboard\medicine_web_dashboard\dashboard_assets.py`
- `D:\A1\dashboard_assets.py`
- RK3588 deployed dashboard assets copies under `/mnt/sdcard/medicine_robot_ws/src/...`, `/mnt/sdcard/medicine_robot_ws/build/...`, and install build-lib path when present.

**Learned**: Health notifications should compare signatures (`status:bad:warn`) and suppress first-load + duplicate states. This keeps alerts useful instead of noisy.


---

## 2026-06-29 | Added recent health-change events

**What**: Extended `/api/health_check` with an in-memory `events` list for recent health status signature changes and added a recent-events panel in the 8085 System Monitor self-check UI.

**Why**: Operators need evidence of transient health changes, not only the current ok/warn/bad state.

**Where**:
- `D:\A1oard_sync\medicine_web_dashboard\medicine_web_dashboard\web_dashboard_node.py`
- `D:\A1oard_sync\medicine_web_dashboard\medicine_web_dashboard\dashboard_assets.py`
- RK3588 deployed copies under `/mnt/sdcard/medicine_robot_ws/src/...`, `/mnt/sdcard/medicine_robot_ws/build/...`, and install build-lib path when present.

**Learned**: Defensive initialization is necessary for new runtime fields in long-lived ROS web nodes. `ensure_health_event_state()` prevents `/api/health_check` from disconnecting if a deployed instance lacks newly-added attributes during reload/startup edge cases.


---

## 2026-06-29 | Persisted health-change events to disk

**What**: Added `health_event_file` parameter and JSON persistence for recent 8085 health-check state-change events at `/mnt/sdcard/medicine_robot_data/health_events.json`.

**Why**: In-memory events disappear after restart or power loss; persistent events provide lightweight traceability for transient health changes.

**Where**:
- `D:\A1oard_sync\medicine_web_dashboard\medicine_web_dashboard\web_dashboard_node.py`
- `D:\A1\web_dashboard_node.py`
- RK3588 deployed copies under `/mnt/sdcard/medicine_robot_ws/src/...`, `/mnt/sdcard/medicine_robot_ws/build/...`, and install build-lib path when present.

**Learned**: Health event persistence should be lazy: create/write the JSON only when an actual status signature change occurs. This keeps normal all-ok startup clean while preserving real transitions.


---

## 2026-06-29 | Hardened health_check route with fail-safe JSON

**What**: Wrapped `/api/health_check` route in `dashboard_http.py` with a try/except fallback that returns structured `status=bad` JSON instead of disconnecting the HTTP request.

**Why**: A previous internal AttributeError caused RemoteDisconnected; the frontend needs a JSON error payload so it can show an actionable health failure.

**Where**:
- `D:\A1oard_sync\medicine_web_dashboard\medicine_web_dashboard\dashboard_http.py`
- `D:\A1\dashboard_http.py`
- RK3588 deployed copies under `/mnt/sdcard/medicine_robot_ws/src/...`, `/mnt/sdcard/medicine_robot_ws/build/...`, and install build-lib path when present.

**Learned**: Health endpoints must be fail-safe. Even if internal diagnostics crash, the endpoint should return a health failure JSON and never close the connection without response.


## 2026-06-29 - Hardened 8085 health-check frontend fallback
**What**: Changed 8085 dashboard health-check refresh to parse structured `/api/health_check` JSON even when HTTP status is non-2xx.
**Why**: Backend fail-safe can intentionally return 503 with useful structured checks; the old frontend treated it as a generic fetch failure and hid the actionable details.
**Where**: `board_sync/medicine_web_dashboard/medicine_web_dashboard/dashboard_assets.py`, mirrored to `dashboard_assets.py`.
**Learned**: For operational dashboards, non-2xx JSON should still render if it contains valid diagnostic payload; HTTP status alone should not erase the failure context.


## 2026-06-29 - Added 8085 health-check report copy and export
**What**: Added one-click health-check summary copy and JSON export actions to the 8085 system monitor self-check panel.
**Why**: Field debugging needs portable diagnostics for 8085, 8081, chassis, voice, vision, batch, and system-load state without manually collecting screenshots.
**Where**: `board_sync/medicine_web_dashboard/medicine_web_dashboard/dashboard_assets.py`, mirrored to `dashboard_assets.py`.
**Learned**: Operational dashboards should offer both human-readable summaries and raw JSON so on-site users and developers can use the same diagnostic source.


## 2026-06-29 - Added 8085 health-check delivery gate decision
**What**: Added a prominent health gate decision panel to classify self-check results as continue delivery, manual confirmation required, or delivery blocked.
**Why**: Nurses need a clear operational conclusion, not only module-by-module technical statuses.
**Where**: `board_sync/medicine_web_dashboard/medicine_web_dashboard/dashboard_assets.py`, mirrored to `dashboard_assets.py`.
**Learned**: For clinical workflow UI, diagnostics should collapse into direct action guidance while preserving detailed checks underneath.


## 2026-06-29 - Expanded 8085 delivery safety gate
**What**: Extended the batch safety gate to block or warn load, advance, and bedside dispense actions based on health-check status, high-priority exceptions, medication review, risk messages, chassis, battery, cabinet lock, and route stage.
**Why**: The delivery workflow needs clear prevention of unsafe stage advancement, not only visual warnings.
**Where**: `board_sync/medicine_web_dashboard/medicine_web_dashboard/dashboard_assets.py`, mirrored to `dashboard_assets.py`.
**Learned**: Frontend safety gates should share one blocker source across buttons so UI state, titles, toasts, and action handlers stay consistent. Backend validation should still be added later for hard guarantees.


## 2026-06-29 - Added backend delivery batch safety gate
**What**: Added backend guards for delivery batch load scan, advance, and dispense scan actions using batch state, unresolved exceptions, medication review flags, route stage, and chassis motion blockers.
**Why**: Frontend disabled buttons reduce mistakes but backend APIs must reject unsafe direct calls for a real safety boundary.
**Where**: `board_sync/medicine_web_dashboard/medicine_web_dashboard/dashboard_delivery_batch.py`, mirrored to `dashboard_delivery_batch.py`.
**Learned**: Do not test safety gate by calling advance on a live batch; verify by code presence and non-mutating API checks unless a disposable test batch is explicitly created.


## 2026-06-29 - Added 8085 safety-blocked audit summary
**What**: Added a safety gate blocked summary panel and audit filter for backend-blocked delivery actions in the 8085 batch audit panel.
**Why**: After backend safety gates were added, operators need a visible place to see why load, advance, or dispense actions were rejected.
**Where**: `board_sync/medicine_web_dashboard/medicine_web_dashboard/dashboard_assets.py`, mirrored to `dashboard_assets.py`.
**Learned**: Safety events should not be buried among generic failed audits; they need a separate filter and prominent summary.


## 2026-06-29 - Added non-destructive delivery safety self-test
**What**: Added `/api/delivery_batch/safety_self_test` and an 8085 ??????? button that validates safety gate scenarios on a deep copy of the current batch.
**Why**: Operators and developers need to verify backend/frontend safety gates without mutating the real delivery batch.
**Where**: `dashboard_delivery_batch.py`, `dashboard_http.py`, and `dashboard_assets.py` under `board_sync/medicine_web_dashboard/medicine_web_dashboard/`, mirrored to root files.
**Learned**: Safety tests for live workflow systems must be non-destructive by default; use copied state and synthetic mutations, not real action endpoints.


## 2026-06-29 - Persisted delivery safety self-test result
**What**: Persisted the latest safety self-test result to disk, added a latest-result GET API, and rendered the latest result in the 8085 debug/manage section after refresh or restart.
**Why**: Safety self-test results should remain visible after page refresh or service restart without polluting real delivery audit records.
**Where**: `dashboard_delivery_batch.py`, `dashboard_http.py`, `web_dashboard_node.py`, and `dashboard_assets.py` under `board_sync/medicine_web_dashboard/medicine_web_dashboard/`, mirrored to root files.
**Learned**: For live clinical workflow tools, diagnostics should be durable but separated from operational audit trails unless they directly affect a real delivery action.


## 2026-06-29 - Surfaced latest safety self-test result in 8085
**What**: Exposed the latest non-destructive safety self-test result in the 8085 debug/manage area and fixed self-test result separators.
**Why**: Operators should see when the safety gate was last verified without polluting real delivery batch audit records.
**Where**: `dashboard_assets.py`, with existing support from `dashboard_delivery_batch.py`, `dashboard_http.py`, and `web_dashboard_node.py`.
**Learned**: Self-test visibility should be separate from delivery audit: operational confidence without altering clinical delivery history.


## 2026-06-29 - Added safety self-test to health check panel
**What**: Added the latest delivery safety self-test as a first-class 8085 health-check item and displayed it in the system self-check grid.
**Why**: Operators should see safety-gate verification status from the main system monitor, not only the debug/manage area.
**Where**: `web_dashboard_node.py` and `dashboard_assets.py` under `board_sync/medicine_web_dashboard/medicine_web_dashboard/`, mirrored to root files.
**Learned**: Safety verification should participate in overall health status so stale or missing self-tests are visible during pre-delivery checks.


## 2026-06-30 - Linked safety self-test status into delivery gates
**What**: Updated frontend and backend delivery safety gates to treat failed safety self-tests as blockers and missing safety self-tests as warnings.
**Why**: Once safety self-test became part of system health, delivery actions also needed to respect that status.
**Where**: `dashboard_assets.py` and `dashboard_delivery_batch.py` under `board_sync/medicine_web_dashboard/medicine_web_dashboard/`, mirrored to root files.
**Learned**: A health-check item only becomes operationally meaningful when action gates consume it, not just display it.


## 2026-06-30 - Added delivery safety gate rule explanation panel
**What**: Added a collapsible safety gate rules panel under the 8085 batch safety gate, grouped by self-check, medication, patient review, chassis, stage, and audit categories.
**Why**: Operators need to understand why delivery buttons are blocked without reading code or hunting through audit logs.
**Where**: `board_sync/medicine_web_dashboard/medicine_web_dashboard/dashboard_assets.py`, mirrored to `dashboard_assets.py`.
**Learned**: Safety UX needs not only blockers but also nearby rule explanations that are compact and task-oriented.

## 2026-06-30 - Added 8085 safety gate quick actions
**What**: Added contextual quick-action buttons inside the 8085 delivery safety gate for system self-check, safety self-test, feedback/review location, chassis/system status, medication list, batch import, workflow progress, and batch refresh.
**Why**: Operators need a direct recovery path from blocked or warning states instead of manually searching the dashboard.
**Where**: `board_sync/medicine_web_dashboard/medicine_web_dashboard/dashboard_assets.py`, mirrored to `dashboard_assets.py`, deployed to RK3588 8085.
**Learned**: Safety blockers should be paired with nearby action affordances so the UI explains both why delivery is blocked and what to do next.

## 2026-06-30 - Enhanced 8085 safety gate summary and mobile handling
**What**: Added a structured safety gate header with blocker/warning counters, a primary-priority line, responsive narrow-screen layout, focus-visible styling, and polite live-region semantics.
**Why**: Operators need to quickly see how many issues block delivery, which issue to handle first, and use the same safety gate comfortably on smaller screens.
**Where**: `board_sync/medicine_web_dashboard/medicine_web_dashboard/dashboard_assets.py`, mirrored to `dashboard_assets.py`, deployed to RK3588 8085.
**Learned**: The safety gate should present three layers: final decision, counts/severity, and the first action priority; this reduces scanning cost when there are multiple blockers.

## 2026-06-30 - Added backend delivery safety gate precheck
**What**: Added read-only `GET /api/delivery_batch/safety_gate` to return backend blockers/warnings for load, advance, and dispense actions, and surfaced the backend precheck summary in the 8085 safety gate.
**Why**: The operator UI should show the backend's real safety boundary before a user clicks an action, not only frontend-estimated blockers.
**Where**: `dashboard_delivery_batch.py`, `dashboard_http.py`, and `dashboard_assets.py` under `board_sync/medicine_web_dashboard/medicine_web_dashboard/`, mirrored to root files and deployed to RK3588.
**Learned**: For safety-critical workflow UI, frontend gating should be reinforced by a read-only backend precheck endpoint so visible status matches API enforcement. Use `pscp -scp` when normal SFTP-mode `pscp` stalls on the RK3588 link.

## 2026-06-30 - Added 8081 patient receipt double confirmation
**What**: Changed the 8081 patient-side receipt action so the main button opens a final confirmation dialog; the patient must review identity/bed/medication count, see the medicine list, and tick a checklist before submitting receipt.
**Why**: Elderly patients can accidentally tap large mobile buttons; signing receipt should require one deliberate second confirmation.
**Where**: `patient_web/src/components/DeliveryCard.tsx`, built `patient_web/dist`, deployed to RK3588 patient web dist at `/mnt/sdcard/medicine_robot_data/patient_web/dist`.
**Learned**: For patient-facing clinical actions, large buttons improve accessibility but increase accidental activation risk; pair them with a clear, low-friction confirmation step for irreversible status changes. Avoid inserting raw Chinese via PowerShell-generated patches because it can become `????`; use Unicode escapes or verify immediately.

## 2026-06-30 - Pushed medicine recognition and voice stability
**What**: Improved the lagging medicine recognition and voice modules: OCR now keeps the last valid RKNN OCR result for 12 seconds to avoid single-frame no-text flicker, 8085 now exposes OCR cache status, DashScope ASR is fixed at 1-second chunks with 300-second default listening, and voice echo/repeat suppression is strengthened.
**Why**: The user reported medicine recognition and voice interaction were behind the rest of the workflow; OCR misses and voice replay/context issues made testing unstable.
**Where**: `board_sync/medicine_vision_detector/medicine_vision_detector/drug_info_detector_node.py`, `board_sync/medicine_web_dashboard/medicine_web_dashboard/web_dashboard_node.py`, `board_sync/medicine_web_dashboard/medicine_web_dashboard/dashboard_assets.py`, `board_sync/m2_voice_opt_20260609/medicine_voice_interaction/medicine_voice_interaction/ai_voice_chat_bridge_node.py`, `board_sync/m2_voice_opt_20260609/medicine_voice_interaction/medicine_voice_interaction/dashscope_asr_bridge_node.py`, `rk3588_start_m2_voice.sh`, deployed to RK3588.
**Learned**: The 8085 restart path also restarts voice through `rk3588_start_m2_voice.sh`; voice tuning must be fixed in that script, not only in node defaults, otherwise ASR chunk/listen parameters regress after dashboard restarts. Avoid storing Chinese prompts in shell scripts; let Python node defaults own Chinese prompt text to prevent mojibake.

## 2026-06-30 - Fixed voice appearing to recognize only once
**What**: Diagnosed that ASR continued recognizing after the first answer, but later utterances were only partial wake-word fragments like `???`/`??`; AI intent filtering dropped them. Changed DashScope ASR chunk size from 1s to 2s for fuller sentence capture, kept mic fragment merge, and added wake-word-only acknowledgement (`????????`).
**Why**: User reported voice could only recognize once; logs showed later ASR results existed but were too short/low-intent for AI handling.
**Where**: `board_sync/m2_voice_opt_20260609/medicine_voice_interaction/medicine_voice_interaction/ai_voice_chat_bridge_node.py`, `rk3588_start_m2_voice.sh`, deployed to RK3588.
**Learned**: For the current rockchipnau8822 mic + chunk ASR path, 1s chunks reduce latency but hurt full-sentence capture; 2s chunks are a better default for patient voice dialog. Wake-word-only fragments should produce a short acknowledgement instead of silent discard so users know the listener is still active.

## 2026-06-30 - Relaxed voice follow-up intent filtering
**What**: Relaxed AI voice mic intent filtering so short follow-up questions recognized by ASR, such as `???`, `????`, `????`, `???`, or any text ending with a question mark, are queued to the AI instead of silently ignored.
**Why**: User reported only the first voice question got an answer; logs showed later ASR results existed but were discarded as low-intent.
**Where**: `board_sync/m2_voice_opt_20260609/medicine_voice_interaction/medicine_voice_interaction/ai_voice_chat_bridge_node.py`, deployed to RK3588.
**Learned**: In spoken dialog, short follow-ups depend on conversation context and should not be filtered like noise; question punctuation and words like `??/??/???` must be treated as valid intent.

