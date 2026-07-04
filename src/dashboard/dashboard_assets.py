# Static dashboard data and frontend document for medicine_web_dashboard.

PATIENT_MEDICATION_ORDERS = [
    {
        "patient_id": "patient_001",
        "patient_name": "张三",
        "ward_id": "ward_a",
        "ward_name": "A病房",
        "bed_no": "A-01",
        "target_station": "ward_a",
        "medications": [
            {
                "id": "p001_med_001",
                "medicine_name": "头孢呋辛酯片",
                "product_code": "RX-A01-20260621-001",
                "product_model": "0.25g*12片",
                "quantity": "1",
                "trace_id": "",
                "order_no": "RX-A01-20260621-001",
                "dose": "1盒",
                "usage": "按医嘱",
            },
            {
                "id": "p001_med_002",
                "medicine_name": "苯磺酸氨氯地平片",
                "product_code": "C177248",
                "product_model": "FXL0530-100-M",
                "quantity": "5",
                "trace_id": "202011444",
                "order_no": "SO2603098044",
                "dose": "1片",
                "usage": "每日一次",
            },
        ],
    },
    {
        "patient_id": "patient_002",
        "patient_name": "李四",
        "ward_id": "ward_b",
        "ward_name": "B病房",
        "bed_no": "B-03",
        "target_station": "ward_b",
        "medications": [
            {
                "id": "p002_med_001",
                "medicine_name": "消炎药",
                "product_code": "C200100",
                "product_model": "AMX0250-24-C",
                "quantity": "2",
                "trace_id": "TRACE-P002-001",
                "order_no": "RX-B03-20260621-001",
                "dose": "1粒",
                "usage": "每日两次",
            },
        ],
    },
    {
        "patient_id": "patient_003",
        "patient_name": "王五",
        "ward_id": "ward_a",
        "ward_name": "A病房",
        "bed_no": "A-02",
        "target_station": "ward_a",
        "medications": [
            {
                "id": "p003_med_001",
                "medicine_name": "右美沙芬口服溶液",
                "product_code": "C300210",
                "product_model": "CKT0100-12-A",
                "quantity": "1",
                "trace_id": "TRACE-P003-001",
                "order_no": "RX-A02-20260621-001",
                "dose": "10ml",
                "usage": "每日三次",
            },
            {
                "id": "p003_med_002",
                "medicine_name": "维生素",
                "product_code": "C300211",
                "product_model": "VITC0500-30-B",
                "quantity": "1",
                "trace_id": "TRACE-P003-002",
                "order_no": "RX-A02-20260621-002",
                "dose": "1片",
                "usage": "每日一次",
            },
        ],
    },
    {
        "patient_id": "patient_004",
        "patient_name": "赵六",
        "ward_id": "ward_b",
        "ward_name": "B病房",
        "bed_no": "B-05",
        "target_station": "ward_b",
        "medications": [
            {
                "id": "p004_med_001",
                "medicine_name": "奥美拉唑肠溶胶囊",
                "product_code": "C400310",
                "product_model": "GST0200-20-A",
                "quantity": "2",
                "trace_id": "TRACE-P004-001",
                "order_no": "RX-B05-20260621-001",
                "dose": "1片",
                "usage": "餐前服用",
            },
            {
                "id": "p004_med_002",
                "medicine_name": "降糖药",
                "product_code": "C400311",
                "product_model": "GLU0500-28-C",
                "quantity": "1",
                "trace_id": "TRACE-P004-002",
                "order_no": "RX-B05-20260621-002",
                "dose": "1片",
                "usage": "每日两次",
            },
        ],
    },
    {
        "patient_id": "patient_005",
        "patient_name": "孙七",
        "ward_id": "ward_c",
        "ward_name": "C病房",
        "bed_no": "C-01",
        "target_station": "ward_c",
        "medications": [
            {
                "id": "p005_med_001",
                "medicine_name": "盐酸氨溴索口服液",
                "product_code": "C2765186",
                "product_model": "10ml*10支",
                "quantity": "1",
                "trace_id": "175550822",
                "order_no": "RX-C01-20260621-001",
                "dose": "1盒",
                "usage": "按医嘱",
            },
            {
                "id": "p005_med_002",
                "medicine_name": "抗过敏药",
                "product_code": "C500410",
                "product_model": "ALG0100-10-A",
                "quantity": "1",
                "trace_id": "TRACE-P005-002",
                "order_no": "RX-C01-20260621-002",
                "dose": "1片",
                "usage": "睡前服用",
            },
        ],
    },
    {
        "patient_id": "patient_006",
        "patient_name": "周八",
        "ward_id": "ward_c",
        "ward_name": "C病房",
        "bed_no": "C-03",
        "target_station": "ward_c",
        "medications": [
            {
                "id": "p006_med_001",
                "medicine_name": "退烧药",
                "product_code": "C600510",
                "product_model": "FVR0500-12-D",
                "quantity": "1",
                "trace_id": "TRACE-P006-001",
                "order_no": "RX-C03-20260621-001",
                "dose": "1片",
                "usage": "必要时服用",
            },
        ],
    },
]


INDEX_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>智能送药工作台</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #eef2f6;
      --card: #ffffff;
      --text: #102033;
      --text-2: #34495e;
      --muted: #65758b;
      --faint: #91a1b4;
      --primary: #0f6e73;
      --primary-dark: #0b5358;
      --primary-soft: #e7f3f2;
      --primary-ring: rgba(15, 110, 115, 0.18);
      --ok: #18794e;
      --ok-soft: #e9f7ef;
      --warn: #a86108;
      --warn-soft: #fff4df;
      --danger: #b42318;
      --danger-soft: #fff0ee;
      --border: #d8e1ea;
      --border-soft: #e8eef4;
      --surface: #f6f8fb;
      --surface-2: #edf3f7;
      --ink: #0b1220;
      --accent: #2f6fbb;
      --shadow-sm: 0 1px 2px rgba(16, 32, 51, 0.06);
      --shadow: 0 1px 2px rgba(16, 32, 51, 0.06), 0 8px 20px rgba(16, 32, 51, 0.045);
      --shadow-lg: 0 18px 42px rgba(16, 32, 51, 0.12);
      --radius-sm: 6px;
      --radius: 10px;
      --radius-lg: 12px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      background: linear-gradient(180deg, #f7f9fb 0, var(--bg) 280px);
      color: var(--text);
      min-height: 100vh;
      overflow-x: hidden;
      -webkit-font-smoothing: antialiased;
      font-feature-settings: "tnum" 1;
    }
    header {
      max-width: min(1680px, 96vw);
      margin: 0 auto;
      padding: 24px 28px 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      border-bottom: 1px solid rgba(216, 225, 234, 0.78);
    }
    .header-title {
      min-width: 320px;
    }
    h1 {
      margin: 0;
      font-size: 26px;
      letter-spacing: 0;
      font-weight: 700;
      color: var(--text);
      line-height: 1.15;
    }
    .subtitle {
      margin-top: 7px;
      color: var(--muted);
      font-size: 13.5px;
      line-height: 1.55;
      max-width: 620px;
    }
    .runtime-strip {
      display: grid;
      grid-template-columns: repeat(6, minmax(112px, auto));
      gap: 10px;
      align-items: stretch;
      max-width: 930px;
    }
    .runtime-cell {
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: rgba(255, 255, 255, 0.78);
      padding: 8px 10px;
      min-height: 56px;
      box-shadow: var(--shadow-sm);
    }
    .runtime-cell span {
      display: block;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.2;
    }
    .runtime-cell strong {
      display: block;
      margin-top: 5px;
      color: var(--text);
      font-size: 13.5px;
      font-weight: 700;
      white-space: nowrap;
    }
    .runtime-cell.ok { border-color: #b7e4cf; background: var(--ok-soft); }
    .runtime-cell.warn { border-color: #f5d28a; background: var(--warn-soft); }
    .runtime-cell.bad { border-color: #fecaca; background: var(--danger-soft); }
    .runtime-cell.cold { background: var(--surface); }
    .dashboard-tabs {
      max-width: min(1680px, 96vw);
      margin: 0 auto;
      padding: 12px 28px;
      display: flex;
      gap: 10px;
      overflow-x: auto;
      position: sticky;
      top: 0;
      z-index: 10;
      background: rgba(238, 242, 246, 0.88);
      backdrop-filter: saturate(170%) blur(14px);
      border-bottom: 1px solid rgba(216, 225, 234, 0.8);
    }
    .tab-button {
      flex: 0 0 auto;
      background: transparent;
      color: var(--muted);
      border: 1px solid transparent;
      border-radius: 12px;
      padding: 9px 13px;
      font-size: 14px;
      font-weight: 600;
      box-shadow: none;
      transition: background .15s ease, color .15s ease, border-color .15s ease, box-shadow .15s ease;
    }
    .tab-button span {
      display: block;
      line-height: 1.15;
      white-space: nowrap;
    }
    .tab-button small {
      display: block;
      margin-top: 3px;
      color: var(--muted);
      font-size: 11px;
      font-weight: 500;
      line-height: 1.1;
      white-space: nowrap;
    }
    .tab-button.active small {
      color: var(--primary);
    }
    .tab-button:hover {
      background: #fff;
      color: var(--text);
    }
    .tab-button.active {
      background: var(--card);
      color: var(--primary-dark);
      border-color: rgba(15, 110, 115, 0.28);
      box-shadow: 0 0 0 3px rgba(15, 110, 115, 0.08);
    }
    .tab-button[data-kind="debug"] {
      color: #718096;
    }
    .tab-button[data-kind="debug"].active {
      color: #334155;
      border-color: rgba(100, 116, 139, 0.28);
      box-shadow: 0 0 0 3px rgba(100, 116, 139, 0.08);
    }
    main {
      max-width: min(1680px, 96vw);
      margin: 0 auto;
      padding: 18px 28px 48px;
      display: grid;
      grid-template-columns: 1.05fr 0.95fr;
      gap: 16px;
      min-width: 0;
    }
    [data-page] {
      display: none;
    }
    [data-page].active {
      display: block;
    }
    [data-page="vision"].active, [data-page="report"].active, [data-page="messages"].active, [data-page="monitor"].active {
      grid-column: 1 / -1;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow);
      padding: 20px 22px;
      position: relative;
      overflow: hidden;
      min-width: 0;
    }
    /* impeccable: 顶部 3px accent 条+圆角=AI tell, 改 1px hairline */
    .card::before {
      content: "";
      position: absolute;
      left: 0;
      top: 0;
      right: 0;
      height: 1px;
      background: var(--primary);
      opacity: 0.55;
    }
    .card h2 {
      margin: 0 0 16px;
      font-size: 16px;
      font-weight: 700;
      letter-spacing: 0;
      color: var(--text);
    }
    label {
      display: block;
      margin: 14px 0 6px;
      color: var(--text-2);
      font-weight: 500;
      font-size: 13.5px;
    }
    input, select, textarea {
      width: 100%;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 9px 11px;
      font-size: 14px;
      background: #fbfcfd;
      outline: none;
      color: var(--text);
      transition: border-color .12s ease, box-shadow .12s ease;
    }
    textarea {
      min-height: 240px;
      resize: vertical;
      font-family: ui-monospace, SFMono-Regular, "JetBrains Mono", Consolas, monospace;
      line-height: 1.55;
      font-size: 12.5px;
    }
    input:focus, select:focus, textarea:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 3px var(--primary-ring);
    }
    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    /* impeccable: 卡里套卡=AI tell, 内层从"实卡"降级为"分组" - 去 border, 留 bg+radius */
    .recognized-panel {
      margin-top: 14px;
      padding: 13px 14px;
      border-radius: var(--radius);
      background: var(--surface);
    }
    .recognized-panel-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
      font-weight: 600;
      font-size: 13.5px;
      color: var(--text);
    }
    .recognized-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }
    /* impeccable: 卡里套卡套卡 - 内层 item 仅留 hairline 边, 去掉独立 bg, 用父 surface */
    .recognized-item {
      min-width: 0;
      border-radius: var(--radius-sm);
      background: var(--card);
      border: 1px solid transparent;
      padding: 10px 11px;
    }
    .recognized-item span {
      display: block;
      color: var(--muted);
      font-size: 12.5px;
      margin-bottom: 4px;
      letter-spacing: 0.02em;
    }
    .recognized-item strong {
      display: block;
      overflow-wrap: anywhere;
      font-size: 13.5px;
      font-weight: 600;
      color: var(--text);
      font-family: ui-monospace, SFMono-Regular, "JetBrains Mono", Consolas, monospace;
    }
    .closed-loop-steps {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-top: 10px;
    }
    .closed-loop-step {
      position: relative;
      min-width: 0;
      padding: 9px 10px 9px 24px;
      border-radius: var(--radius-sm);
      background: var(--card);
      border: 1px dashed var(--border);
      color: var(--muted);
      font-size: 12px;
      font-weight: 600;
    }
    .closed-loop-step::before {
      content: '';
      position: absolute;
      left: 10px;
      top: 14px;
      width: 7px;
      height: 7px;
      border-radius: 999px;
      background: #cbd5e1;
    }
    .closed-loop-step.done {
      color: #0f766e;
      border-style: solid;
      border-color: rgba(15, 118, 110, 0.25);
      background: rgba(20, 184, 166, 0.08);
    }
    .closed-loop-step.done::before { background: var(--primary); }
    .closed-loop-step.warn {
      color: #92400e;
      border-color: rgba(245, 158, 11, 0.35);
      background: rgba(245, 158, 11, 0.09);
    }
    .closed-loop-step.warn::before { background: #f59e0b; }
    button {
      border: 1px solid var(--border);
      background: var(--card);
      color: var(--text);
      border-radius: var(--radius-sm);
      padding: 8px 13px;
      font-size: 13.5px;
      font-weight: 600;
      cursor: pointer;
      transition: background .12s ease, border-color .12s ease, color .12s ease;
    }
    button:hover {
      background: #fdfefe;
      border-color: var(--primary);
      color: var(--primary-dark);
    }
    button:focus-visible {
      outline: 2px solid var(--primary);
      outline-offset: 2px;
    }
    .primary {
      width: 100%;
      margin-top: 18px;
      background: var(--primary);
      color: #fff;
      border-color: var(--primary);
      font-weight: 700;
      padding: 11px 16px;
      font-size: 14px;
      box-shadow: 0 0 0 3px rgba(15, 110, 115, 0.08);
    }
    .primary:hover {
      background: var(--primary-dark);
      border-color: var(--primary-dark);
      color: #fff;
    }
    .secondary {
      background: #fdfefe;
      color: var(--text-2);
      border: 1px solid var(--border);
    }
    .secondary:hover {
      background: var(--primary-soft);
      color: var(--primary-dark);
      border-color: var(--primary);
    }
    .small-button {
      padding: 6px 9px;
      font-size: 12px;
      border-radius: var(--radius-sm);
    }
    .danger {
      background: var(--danger-soft);
      color: var(--danger);
      border: 1px solid #fecaca;
    }
    .danger:hover {
      background: var(--danger);
      color: #fff;
      border-color: var(--danger);
    }
    .status-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border-soft);
    }
    .badge {
      display: inline-flex;
      align-items: center;
      min-width: 0;
      justify-content: center;
      border-radius: 999px;
      padding: 4px 10px;
      font-weight: 600;
      font-size: 12px;
      letter-spacing: 0;
      color: var(--muted);
      background: var(--surface);
      border: 1px solid var(--border);
    }
    .badge::before {
      content: "";
      width: 6px;
      height: 6px;
      border-radius: 999px;
      background: currentColor;
      margin-right: 6px;
      flex: 0 0 6px;
    }
    .badge.IDLE { color: var(--muted); }
    .badge.WAITING_LOAD_CONFIRMATION,
    .badge.WAITING_DISPENSE_CONFIRMATION,
    .badge.ARRIVED {
      color: var(--warn);
      background: var(--warn-soft);
      border-color: #fde68a;
    }
    .badge.NAVIGATING {
      color: var(--primary-dark);
      background: var(--primary-soft);
      border-color: #bfdbfe;
    }
    .badge.COMPLETED {
      color: var(--ok);
      background: var(--ok-soft);
      border-color: #bbf7d0;
    }
    .badge.CANCELED {
      color: var(--danger);
      background: var(--danger-soft);
      border-color: #fecaca;
    }
    .progress-wrap {
      height: 7px;
      background: var(--border-soft);
      border-radius: 999px;
      overflow: hidden;
      margin: 12px 0 18px;
    }
    .progress {
      height: 100%;
      width: 0%;
      background: var(--accent);
      transition: width .3s ease;
    }
    .kv {
      display: grid;
      grid-template-columns: 116px 1fr;
      gap: 10px;
      padding: 10px 0;
      border-bottom: 1px solid var(--border-soft);
      font-size: 14px;
    }
    .kv:last-child { border-bottom: 0; }
    .kv span:first-child { color: var(--muted); font-size: 13px; }
    .kv strong {
      min-width: 0;
      overflow-wrap: anywhere;
      font-weight: 500;
      color: var(--text);
    }
    .load-list {
      display: grid;
      gap: 12px;
      margin-top: 2px;
    }
    .load-summary {
      margin: -2px 0 14px;
      color: var(--muted);
      font-size: 13.5px;
      line-height: 1.5;
    }

    .health-gate {
      display: grid;
      gap: 6px;
      margin: 10px 0 12px;
      padding: 12px 14px;
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      background: var(--surface);
    }
    .health-gate-head {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 12px;
    }
    .health-gate-head span {
      color: var(--muted);
      font-size: 12.5px;
    }
    .health-gate-head strong {
      color: var(--text);
      font-size: 18px;
      line-height: 1.25;
    }
    .health-gate p {
      margin: 0;
      color: var(--muted);
      font-size: 13.5px;
      line-height: 1.55;
    }
    .health-gate.ok { border-color: #b7e4cf; background: var(--ok-soft); }
    .health-gate.warn { border-color: #f5d28a; background: var(--warn-soft); }
    .health-gate.bad { border-color: #fecaca; background: var(--danger-soft); }
    .health-gate.bad .health-gate-head strong { color: var(--danger); }
    .health-gate.warn .health-gate-head strong { color: #92400e; }

    .health-check-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 10px;
      margin: 10px 0 12px;
    }
    .health-check-item {
      border-color: var(--border);
      background: var(--card);
    }
    .health-check-item.ok {
      border-color: #b7e4cf;
      background: var(--ok-soft);
    }
    .health-check-item.warn {
      border-color: #f5d28a;
      background: var(--warn-soft);
    }
    .health-check-item.bad {
      border-color: #fecaca;
      background: var(--danger-soft);
    }
    .health-check-item.cold {
      background: var(--surface);
    }
    .health-check-hint {
      margin-top: 4px;
    }

    .health-check-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }
    .health-check-actions:empty {
      display: none;
    }
    .health-check-actions button {
      min-height: 34px;
      padding: 7px 11px;
      font-size: 12.5px;
    }

    .health-check-events {
      display: grid;
      gap: 6px;
      margin-top: 10px;
    }
    .health-event-row {
      display: grid;
      grid-template-columns: 86px minmax(0, 1fr) auto;
      gap: 9px;
      align-items: center;
      padding: 8px 10px;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      background: rgba(255, 255, 255, 0.70);
      font-size: 12.5px;
      line-height: 1.4;
    }
    .health-event-row strong { color: var(--text); }
    .health-event-row span { color: var(--muted); overflow-wrap: anywhere; }
    .health-event-row.ok { border-color: #b7e4cf; background: var(--ok-soft); }
    .health-event-row.warn { border-color: #f5d28a; background: var(--warn-soft); }
    .health-event-row.bad { border-color: #fecaca; background: var(--danger-soft); }
    @media (max-width: 760px) {
      .health-event-row {
        grid-template-columns: 1fr;
        gap: 3px;
      }
    }

    .health-check-meta {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      max-width: 100%;
      margin: -4px 0 10px;
      color: var(--muted);
      font-size: 12.5px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }
    .health-check-detail {
      margin-top: 10px;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      background: rgba(255, 255, 255, 0.62);
      overflow: hidden;
    }
    .health-check-detail summary {
      cursor: pointer;
      padding: 9px 11px;
      color: var(--text);
      font-size: 13px;
      font-weight: 700;
      list-style-position: inside;
    }
    .health-check-detail-list {
      display: grid;
      gap: 1px;
      background: var(--border);
      border-top: 1px solid var(--border);
    }
    .health-detail-row {
      display: grid;
      grid-template-columns: minmax(120px, 0.9fr) minmax(180px, 2fr) minmax(120px, 1.2fr);
      gap: 10px;
      align-items: start;
      padding: 9px 11px;
      background: rgba(255, 255, 255, 0.88);
      font-size: 12.5px;
      line-height: 1.45;
    }
    .health-detail-row strong {
      color: var(--text);
      font-weight: 700;
    }
    .health-detail-row span {
      color: var(--muted);
      overflow-wrap: anywhere;
    }
    .health-detail-state {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-weight: 700;
    }
    .health-detail-state::before {
      content: '';
      width: 7px;
      height: 7px;
      border-radius: 999px;
      background: #94a3b8;
    }
    .health-detail-row.ok .health-detail-state { color: #047857; }
    .health-detail-row.ok .health-detail-state::before { background: #10b981; }
    .health-detail-row.warn .health-detail-state { color: #92400e; }
    .health-detail-row.warn .health-detail-state::before { background: #f59e0b; }
    .health-detail-row.bad .health-detail-state { color: #b91c1c; }
    .health-detail-row.bad .health-detail-state::before { background: #ef4444; }
    @media (max-width: 760px) {
      .health-detail-row {
        grid-template-columns: 1fr;
        gap: 4px;
      }
    }
    .load-meter {
      display: grid;
      gap: 6px;
    }
    .load-meter-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      color: var(--muted);
      font-size: 13.5px;
    }
    .load-meter-head strong {
      color: var(--text);
      font-variant-numeric: tabular-nums;
    }
    .load-track {
      height: 8px;
      border-radius: 999px;
      background: #e8eef5;
      overflow: hidden;
    }
    .load-fill {
      width: 0%;
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--primary), #16a34a);
      transition: width .2s ease;
    }
    .load-meter.gpu .load-fill {
      background: linear-gradient(90deg, #f59e0b, #16a34a);
    }
    .load-meter.npu .load-fill {
      background: linear-gradient(90deg, #0ea5e9, var(--primary));
    }
    .drug-card {
      margin-top: 22px;
    }
    .drug-loaded { color: var(--ok); }
    .drug-empty { color: var(--danger); }
    .vision-layout {
      display: grid;
      grid-template-columns: minmax(360px, 1.2fr) minmax(320px, 0.8fr);
      gap: 16px;
      align-items: start;
    }
    .vision-panel {
      border: 1px solid var(--border-soft);
      border-radius: var(--radius);
      background: var(--surface);
      padding: 14px;
    }
    .vision-panel h3 {
      margin: 0 0 10px;
      font-size: 14px;
      color: var(--text);
    }
    .recognition-state-card {
      margin: 0 0 14px;
      padding: 12px 13px;
      border: 1px solid #dbe7f1;
      border-radius: 14px;
      background: #f8fafc;
      color: var(--ink);
    }
    .recognition-state-card.low { border-color: #bbf7d0; background: var(--ok-soft); }
    .recognition-state-card.medium { border-color: #fde68a; background: var(--warn-soft); }
    .recognition-state-card.high { border-color: #fecaca; background: var(--danger-soft); }
    .recognition-state-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      font-size: 14px;
      font-weight: 850;
      line-height: 1.35;
    }
    .recognition-state-title span:last-child {
      flex: 0 0 auto;
      font-size: 12px;
      font-weight: 750;
      color: var(--muted);
    }
    .recognition-state-body {
      margin-top: 5px;
      color: #475569;
      font-size: 12.5px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }
    .camera-preview-wrap {
      margin-bottom: 16px;
      overflow: hidden;
      border-radius: var(--radius);
      border: 1px solid var(--border);
      background: #0b1220;
      aspect-ratio: 4 / 3;
      display: block;
      position: relative;
    }
    .camera-preview-wrap img,
    .camera-preview-wrap video {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      min-width: 100%;
      min-height: 100%;
      object-fit: cover;
      object-position: center center;
      display: block;
    }
    .vision-roi-overlay {
      position: absolute;
      pointer-events: none;
      display: none;
    }
    .vision-roi-overlay.active {
      display: block;
    }
    .vision-roi-overlay::before {
      position: absolute;
      left: -2px;
      top: -24px;
      min-width: 42px;
      height: 20px;
      padding: 0 8px;
      border-radius: 4px 4px 0 0;
      background: #3dff78;
      color: #052012;
      font-size: 12px;
      font-weight: 800;
      line-height: 20px;
      text-align: center;
    }
    .ocr-roi-overlay {
      border: 2px solid #3dff78;
      box-shadow: 0 0 0 9999px rgba(7, 16, 30, .14), 0 0 18px rgba(61, 255, 120, .36);
    }
    .ocr-roi-overlay::before {
      content: "OCR";
      background: #3dff78;
      color: #052012;
    }
    .barcode-roi-overlay {
      border: 2px solid #ffd84d;
      box-shadow: 0 0 0 9999px rgba(7, 16, 30, .10), 0 0 18px rgba(255, 216, 77, .36);
    }
    .barcode-roi-overlay::before {
      content: "BARCODE";
      min-width: 78px;
      background: #ffd84d;
      color: #241a00;
    }
    .camera-empty {
      position: absolute;
      inset: 0;
      display: grid;
      place-content: center;
      gap: 10px;
      padding: 24px;
      text-align: center;
      color: #dbe4ee;
      background:
        linear-gradient(90deg, rgba(255,255,255,.04) 1px, transparent 1px) 0 0 / 28px 28px,
        #0b1220;
      pointer-events: none;
    }
    .camera-empty[hidden] {
      display: none;
    }
    .camera-empty strong { font-size: 18px; }
    .camera-empty span { color: #9fb0c4; font-size: 13px; line-height: 1.5; }
    .camera-preview-hint {
      margin-bottom: 12px;
      color: var(--muted);
      font-size: 13.5px;
    }
    .camera-preview-toolbar {
      display: flex;
      gap: 10px;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;
      flex-wrap: wrap;
    }
    .camera-preview-mode {
      display: inline-flex;
      gap: 4px;
      padding: 3px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--surface-soft);
    }
    .camera-preview-mode button {
      border: 0;
      border-radius: 6px;
      padding: 7px 12px;
      background: transparent;
      color: var(--muted);
      font-weight: 800;
      cursor: pointer;
    }
    .camera-preview-mode button.active {
      background: var(--accent);
      color: white;
    }
    .vision-controls {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin: 0 0 12px;
    }
    .vision-controls button.active {
      color: #fff;
      border-color: var(--primary);
      background: var(--primary);
    }
    .diagnostic-list {
      margin: 10px 0 0;
      padding-left: 18px;
      color: var(--muted);
      font-size: 13.5px;
      line-height: 1.65;
    }
    .actions {
      display: flex;
      gap: 10px;
      margin-top: 16px;
      flex-wrap: wrap;
    }
    .chassis-control-actions {
      align-items: center;
      margin-top: 14px;
    }
    .chassis-control-actions button {
      min-width: 104px;
    }
    .log {
      margin-top: 16px;
      border-radius: var(--radius);
      background: var(--ink);
      color: #dbe4ee;
      min-height: 120px;
      padding: 14px 16px;
      font-family: ui-monospace, SFMono-Regular, "JetBrains Mono", Consolas, monospace;
      font-size: 12.5px;
      line-height: 1.55;
      white-space: pre-wrap;
      overflow: auto;
    }
    .notice {
      margin-top: 12px;
      color: var(--muted);
      font-size: 12.5px;
      line-height: 1.6;
      padding: 10px 12px;
      background: var(--surface);
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-soft);
      border-color: rgba(15, 110, 115, 0.18);
    }
    .safety-gate {
      margin: 0 0 14px;
      padding: 13px 14px;
      border-radius: var(--radius);
      border: 1px solid #bbf7d0;
      background: var(--ok-soft);
      color: #14532d;
      font-size: 13.5px;
      line-height: 1.55;
      box-shadow: inset 0 0 0 1px rgba(22, 163, 74, 0.08);
    }
    .safety-gate.blocked {
      border-color: #fecaca;
      background: var(--danger-soft);
      color: #7f1d1d;
      box-shadow: inset 0 0 0 1px rgba(217, 45, 32, 0.10);
    }
    .safety-gate.warn {
      border-color: #fde68a;
      background: var(--warn-soft);
      color: #78350f;
      box-shadow: inset 0 0 0 1px rgba(245, 158, 11, 0.10);
    }
    .safety-gate strong {
      display: block;
      margin-bottom: 5px;
      font-size: 14px;
    }
    .safety-gate-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 8px;
    }
    .safety-gate-head strong {
      margin: 0;
    }
    .safety-gate-counts {
      display: flex;
      flex: 0 0 auto;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 6px;
    }
    .safety-gate-pill {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      padding: 3px 8px;
      border-radius: 999px;
      border: 1px solid rgba(15, 23, 42, 0.10);
      background: rgba(255, 255, 255, 0.70);
      color: currentColor;
      font-size: 11.5px;
      font-weight: 800;
      white-space: nowrap;
    }
    .safety-gate-priority {
      margin: 0 0 8px;
      padding: 8px 10px;
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.58);
      font-size: 12.5px;
      font-weight: 750;
      overflow-wrap: anywhere;
    }
    .safety-backend-gate {
      margin: 0 0 8px;
      padding: 8px 10px;
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.50);
      font-size: 12px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }
    .safety-backend-gate strong {
      display: inline;
      margin: 0;
      font-size: 12px;
    }
    .safety-gate ol {
      margin: 0;
      padding-left: 20px;
    }
    .safety-gate-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }
    .safety-gate-actions button {
      min-height: 32px;
      padding: 6px 10px;
      border-radius: 10px;
      border: 1px solid rgba(15, 110, 115, 0.22);
      background: rgba(255, 255, 255, 0.78);
      color: var(--text);
      font-size: 12px;
      font-weight: 750;
    }
    .safety-gate-actions button:hover {
      border-color: rgba(15, 110, 115, 0.42);
      background: #fff;
    }
    .safety-gate-actions button:focus-visible {
      outline: 3px solid rgba(20, 184, 166, 0.22);
      outline-offset: 2px;
      border-color: rgba(15, 110, 115, 0.52);
    }
    @media (max-width: 640px) {
      .safety-gate-head {
        flex-direction: column;
        gap: 7px;
      }
      .safety-gate-counts {
        justify-content: flex-start;
      }
      .safety-gate-actions button {
        flex: 1 1 130px;
      }
    }
    .safety-rule-panel {
      margin: -4px 0 14px;
      border: 1px solid var(--border-soft);
      border-radius: var(--radius-sm);
      background: rgba(255, 255, 255, 0.72);
      color: var(--muted);
      font-size: 12.5px;
      line-height: 1.5;
    }
    .safety-rule-panel summary {
      cursor: pointer;
      padding: 9px 11px;
      color: var(--text);
      font-weight: 750;
      user-select: none;
    }
    .safety-rule-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 8px;
      padding: 0 11px 11px;
    }
    .safety-rule-grid div {
      min-width: 0;
      border: 1px solid #e5edf5;
      border-radius: 11px;
      background: #f8fafc;
      padding: 9px 10px;
    }
    .safety-rule-grid strong {
      display: block;
      margin-bottom: 3px;
      color: var(--text);
      font-size: 12.5px;
    }
    .safety-rule-grid span {
      display: block;
      overflow-wrap: anywhere;
    }
    .action-section {
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px dashed var(--border);
    }
    .action-section:first-of-type {
      border-top: 0;
      padding-top: 0;
    }
    .action-section-title {
      margin-bottom: 8px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }
    .demo-flow-guide {
      margin-top: 12px;
      padding: 12px;
      border: 1px solid var(--border-soft);
      border-radius: var(--radius-sm);
      background: linear-gradient(180deg, rgba(240, 253, 250, 0.76), rgba(255, 255, 255, 0.82));
    }
    .demo-flow-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
      color: var(--text);
      font-size: 13px;
      font-weight: 800;
    }
    .demo-flow-status {
      color: #0f766e;
      font-size: 12px;
      font-weight: 800;
      white-space: nowrap;
    }
    .demo-flow-target {
      margin: 0 0 10px;
      padding: 9px 10px;
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.72);
      border: 1px solid rgba(15, 118, 110, 0.12);
      color: #475569;
      font-size: 12.5px;
      line-height: 1.45;
    }
    .demo-flow-target strong {
      color: var(--text);
      font-weight: 800;
    }
    .demo-flow-steps {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
    }
    .demo-flow-step {
      min-width: 0;
      padding: 10px;
      border: 1px solid rgba(15, 118, 110, 0.14);
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.74);
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }
    .demo-flow-step strong {
      display: block;
      margin-bottom: 4px;
      color: var(--text);
      font-size: 12.5px;
    }
    .demo-flow-step.active {
      border-color: rgba(217, 119, 6, 0.38);
      background: #fffbeb;
    }
    .demo-flow-step.done {
      border-color: rgba(16, 185, 129, 0.35);
      background: #ecfdf5;
    }
    .demo-flow-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 10px;
    }
    .demo-flow-actions button {
      margin-top: 0;
    }
    .demo-flow-actions .reset-action {
      margin-left: auto;
    }
    @media (max-width: 760px) {
      .demo-flow-steps { grid-template-columns: 1fr; }
      .demo-flow-actions .reset-action { margin-left: 0; }
    }

    /* 2026-06 operator next-step guide for 8085 batch workflow. */
    .workflow-guide {
      margin: -2px 0 14px;
      padding: 12px 14px;
      border: 1px solid #dbe7f1;
      border-radius: var(--radius);
      background: #f8fafc;
      color: #334155;
      font-size: 13px;
      line-height: 1.55;
    }
    .workflow-guide.warn {
      border-color: #fde68a;
      background: #fffbeb;
      color: #78350f;
    }
    .workflow-guide.danger {
      border-color: #fecaca;
      background: #fff5f5;
      color: #7f1d1d;
    }
    .workflow-guide.ok {
      border-color: #bbf7d0;
      background: #f0fdf4;
      color: #14532d;
    }
    .workflow-guide-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 6px;
    }
    .workflow-guide strong {
      color: inherit;
      font-size: 14px;
      font-weight: 800;
    }
    .workflow-guide .badge {
      flex: 0 0 auto;
      background: rgba(255, 255, 255, 0.72);
    }
    .workflow-guide-body {
      overflow-wrap: anywhere;
    }
    .workflow-guide-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
      margin-top: 9px;
    }
    .workflow-guide-actions button {
      min-height: 32px;
      padding: 6px 10px;
      font-size: 12.5px;
    }
    button.recommended-action {
      border-color: var(--primary);
      background: var(--primary-soft);
      color: var(--primary-dark);
      box-shadow: 0 0 0 3px rgba(15, 110, 115, 0.10);
    }
    button.primary-flow.recommended-action {
      color: #fff;
      background: var(--primary);
    }
    @media (max-width: 760px) {
      .workflow-guide-head {
        align-items: flex-start;
        flex-direction: column;
      }
      .workflow-guide-actions button {
        flex: 1 1 150px;
      }
    }
    /* 2026-06 batch closure timeline: compact workflow evidence, not another card grid. */
    .batch-closure-timeline {
      margin: 0 0 14px;
      padding: 13px 14px 14px;
      border: 1px solid #dbe7f1;
      border-radius: 16px;
      background: #ffffff;
      color: #334155;
    }
    .batch-closure-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 12px;
    }
    .batch-closure-head strong {
      display: block;
      color: var(--ink);
      font-size: 14px;
      font-weight: 850;
      line-height: 1.35;
    }
    .batch-closure-head span:not(.badge) {
      display: block;
      margin-top: 3px;
      color: var(--muted);
      font-size: 12.5px;
      line-height: 1.45;
    }
    .batch-closure-steps {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(138px, 1fr));
      gap: 8px;
    }
    .batch-closure-step {
      position: relative;
      min-height: 74px;
      margin: 0;
      padding: 11px 11px 10px 34px;
      border: 1px solid #e2e8f0;
      border-radius: 14px;
      background: #f8fafc;
      color: #334155;
      box-shadow: none;
      text-align: left;
      transition: border-color .16s ease, background-color .16s ease, transform .16s ease;
    }
    .batch-closure-step:hover {
      transform: translateY(-1px);
      border-color: #bfd7dd;
      background: #f4fbfb;
    }
    .batch-closure-step:focus-visible {
      outline: 3px solid rgba(15, 110, 115, 0.16);
      outline-offset: 2px;
    }
    .batch-closure-dot {
      position: absolute;
      left: 12px;
      top: 14px;
      width: 10px;
      height: 10px;
      border-radius: 999px;
      background: #94a3b8;
      box-shadow: 0 0 0 4px rgba(148, 163, 184, 0.12);
    }
    .batch-closure-step.done .batch-closure-dot {
      background: var(--ok);
      box-shadow: 0 0 0 4px rgba(5, 150, 105, 0.13);
    }
    .batch-closure-step.active .batch-closure-dot {
      background: var(--primary);
      box-shadow: 0 0 0 4px rgba(15, 110, 115, 0.16);
    }
    .batch-closure-step.blocked .batch-closure-dot {
      background: var(--danger);
      box-shadow: 0 0 0 4px rgba(220, 38, 38, 0.13);
    }
    .batch-closure-step.waiting {
      color: #64748b;
      background: #f8fafc;
    }
    .batch-closure-step.done {
      border-color: #bbf7d0;
      background: #f0fdf4;
    }
    .batch-closure-step.active {
      border-color: #99d8dd;
      background: #ecfeff;
    }
    .batch-closure-step.blocked {
      border-color: #fecaca;
      background: #fff5f5;
    }
    .batch-closure-title {
      display: block;
      color: inherit;
      font-size: 13px;
      font-weight: 850;
      line-height: 1.35;
    }
    .batch-closure-meta {
      display: block;
      margin-top: 5px;
      color: #64748b;
      font-size: 12px;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }
    @media (max-width: 760px) {
      .batch-closure-head {
        flex-direction: column;
      }
      .batch-closure-steps {
        grid-template-columns: 1fr 1fr;
      }
      .batch-closure-step {
        min-height: 68px;
      }
    }
    @media (max-width: 460px) {
      .batch-closure-steps {
        grid-template-columns: 1fr;
      }
    }
    button.primary-flow {
      color: #fff;
      border-color: var(--primary);
      background: var(--primary);
      box-shadow: 0 12px 24px rgba(37, 99, 235, 0.16);
    }
    button.primary-flow:hover { background: var(--primary-dark); }
    button:disabled,
    button[disabled] {
      cursor: not-allowed;
      opacity: .55;
      box-shadow: none;
    }
    /* impeccable: audit-list 父已是 .card, 这层不应再做"卡", 仅 hairline 分组 */
    .audit-list {
      margin-top: 12px;
      border-top: 1px solid var(--border-soft);
      border-bottom: 1px solid var(--border-soft);
      overflow: hidden;
    }
    .audit-item {
      padding: 11px 13px;
      border-bottom: 1px solid var(--border-soft);
      font-size: 13.5px;
      line-height: 1.5;
    }
    .audit-item:last-child { border-bottom: 0; }
    .audit-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 4px;
      font-weight: 600;
      color: var(--text);
    }
    .audit-pass { color: var(--ok); }
    .audit-fail { color: var(--danger); }
    .audit-detail {
      color: var(--muted);
      overflow-wrap: anywhere;
    }
    .audit-filter-row {
      display: grid;
      grid-template-columns: 1fr;
      gap: 6px;
      margin: 4px 0 10px;
    }
    .patient-panel {
      margin-top: 16px;
      padding: 14px 16px;
      border: 1px solid #c7e9d6;
      border-radius: var(--radius);
      background: var(--ok-soft);
    }
    .medication-list {
      display: grid;
      gap: 10px;
      margin-top: 10px;
    }
    .medication-item {
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 11px 13px;
      background: var(--card);
      font-size: 13.5px;
    }
    .medication-item.matched {
      border-color: #86efac;
      background: var(--ok-soft);
    }
    .medication-item.loaded {
      border-color: #bfdbfe;
      background: var(--primary-soft);
    }
    .medication-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 6px;
      font-weight: 600;
      color: var(--text);
    }
    .batch-card { grid-column: 1 / -1; }
    .batch-layout {
      display: grid;
      grid-template-columns: minmax(320px, 0.9fr) minmax(520px, 1.35fr) minmax(300px, 0.88fr);
      gap: 14px;
      min-width: 0;
    }
    /* impeccable: 大卡内的分栏 panel 降级 - 去 border, 用 surface 区分 */
    .batch-panel {
      border-radius: var(--radius);
      background: rgba(248, 250, 252, 0.78);
      padding: 15px 16px;
      min-width: 0;
      min-height: 0;
      box-shadow: inset 0 0 0 1px rgba(220, 230, 240, 0.72);
    }
    .batch-panel h2 {
      font-size: 15px !important;
      font-weight: 700;
      color: var(--text);
      margin-bottom: 12px !important;
      text-wrap: balance;
    }
    .batch-panel.worklist-panel {
      background: #fff;
    }
    .batch-panel.audit-panel {
      background: rgba(245, 248, 251, 0.74);
    }
    .safety-audit-summary {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin: 10px 0 12px;
      padding: 10px 11px;
      border: 1px solid #fecaca;
      border-radius: 13px;
      background: #fff7f7;
    }
    .safety-audit-summary[hidden] { display: none; }
    .safety-audit-summary div { display: grid; gap: 2px; min-width: 0; }
    .safety-audit-summary strong { color: var(--danger); font-size: 13.5px; }
    .safety-audit-summary span { color: var(--muted); font-size: 12.5px; line-height: 1.4; overflow-wrap: anywhere; }
    .safety-self-test-result {
      margin-top: 10px;
      border: 1px solid var(--border);
      border-radius: 13px;
      background: #fff;
      padding: 10px 11px;
      color: var(--muted);
      font-size: 12.5px;
      line-height: 1.5;
    }
    .safety-self-test-result.ok { border-color: #b7e4cf; background: var(--ok-soft); }
    .safety-self-test-result.fail { border-color: #fecaca; background: var(--danger-soft); }
    .safety-self-test-result strong { color: var(--text); display: block; margin-bottom: 4px; }
    .safety-self-test-result ol { margin: 6px 0 0 18px; padding: 0; }
    .audit-item.safety-blocked {
      border-color: #fecaca;
      background: #fff7f7;
    }
    .exception-center {
      margin-bottom: 14px;
      border: 1px solid rgba(226, 232, 240, 0.95);
      border-radius: 14px;
      background: #fff;
      overflow: hidden;
    }
    .exception-center-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 12px 14px;
      border-bottom: 1px solid #eef2f7;
    }
    .exception-center-title { display: grid; gap: 2px; min-width: 0; }
    .exception-center-title strong { color: var(--text); font-size: 14.5px; font-weight: 800; }
    .exception-center-title span { color: var(--muted); font-size: 12.5px; }
    .exception-summary {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      margin: 12px 0;
    }
    .exception-stat {
      border: 1px solid #e5edf5;
      border-radius: 12px;
      background: #fff;
      padding: 10px 11px;
    }
    .exception-stat span { display: block; color: var(--muted); font-size: 12px; font-weight: 650; }
    .exception-stat strong { display: block; margin-top: 3px; color: var(--text); font-size: 18px; line-height: 1; }
    .exception-stat.danger strong { color: var(--danger); }
    .exception-stat.warn strong { color: var(--warn); }
    .exception-stat.ok strong { color: var(--ok); }
    .exception-list {
      display: grid;
      gap: 8px;
      padding: 12px 14px 14px;
      max-height: 360px;
      overflow: auto;
    }
    .exception-empty {
      border: 1px dashed #dbe7f1;
      border-radius: 12px;
      padding: 14px;
      color: var(--muted);
      background: #f8fafc;
      font-size: 13px;
      line-height: 1.55;
    }
    .exception-item {
      border: 1px solid #e5edf5;
      border-radius: 13px;
      background: #f8fafc;
      padding: 11px 12px;
    }
    .exception-item.danger { border-color: #fecaca; background: #fff7f7; }
    .exception-item.warn { border-color: #fed7aa; background: #fff8ed; }
    .exception-item.info { border-color: #bfdbfe; background: #eff6ff; }
    .exception-item-head {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 10px;
      margin-bottom: 6px;
    }
    .exception-item-title { min-width: 0; color: var(--text); font-size: 13.5px; font-weight: 800; }
    .exception-item-title small { display: block; margin-top: 2px; color: var(--muted); font-size: 12px; font-weight: 650; }
    .exception-type-pill {
      flex: 0 0 auto;
      border-radius: 999px;
      padding: 3px 9px;
      font-size: 11.5px;
      font-weight: 750;
      border: 1px solid #e2e8f0;
      background: #fff;
      color: var(--muted);
      white-space: nowrap;
    }
    .exception-type-pill.danger { color: var(--danger); border-color: #fecaca; background: #fee2e2; }
    .exception-type-pill.warn { color: #b45309; border-color: #fed7aa; background: #ffedd5; }
    .exception-type-pill.info { color: #1d4ed8; border-color: #bfdbfe; background: #dbeafe; }
    .exception-reason { color: #475569; font-size: 12.5px; line-height: 1.5; margin: 6px 0 8px; }
    .exception-actions { display: flex; flex-wrap: wrap; gap: 6px; }
    .exception-actions .small-button { padding: 6px 9px; min-height: 30px; font-size: 12px; }
    .exception-resolution-strip {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 9px 14px;
      border-bottom: 1px solid #dbeafe;
      background: linear-gradient(90deg, rgba(236, 253, 245, 0.92), rgba(239, 246, 255, 0.84));
      color: #0f766e;
      font-size: 12.5px;
      font-weight: 750;
    }
    .audit-item.audit-focus {
      outline: 3px solid rgba(14, 159, 154, 0.32);
      outline-offset: 2px;
      background: rgba(236, 253, 245, 0.92);
      transition: outline-color 180ms ease, background 180ms ease;
    }
    @media (prefers-reduced-motion: reduce) {
      .audit-item.audit-focus { transition: none; }
    }
    .exception-filter-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      padding: 10px 14px;
      border-bottom: 1px solid #eef2f7;
      background: #f8fafc;
    }
    .exception-filter-button {
      border: 1px solid #dbe7f1;
      border-radius: 999px;
      background: #fff;
      color: #475569;
      padding: 5px 10px;
      font-size: 12px;
      font-weight: 750;
      cursor: pointer;
    }
    .exception-filter-button.active {
      border-color: rgba(15, 159, 154, 0.55);
      background: rgba(15, 159, 154, 0.10);
      color: var(--primary);
    }
    #batch_stops {
      max-height: calc(100vh - 360px);
      min-height: 420px;
      overflow: auto;
      padding-right: 3px;
    }
    .route-steps {
      --route-active: #0f9f9a;
      --route-active-2: #12b8ad;
      --route-done: #16a34a;
      --route-muted: #d9e4ef;
      --route-text: #102a43;
      position: relative;
      margin-top: 12px;
      padding: 18px 20px 14px;
      border: 1px solid #edf2f7;
      border-radius: 16px;
      background: #fff;
      box-shadow: 0 14px 34px rgba(15, 23, 42, 0.08);
      overflow: hidden;
    }
    .route-flow {
      position: relative;
      width: 100%;
      aspect-ratio: 16 / 9;
      min-height: 246px;
      max-height: 310px;
    }
    .route-path-svg {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      z-index: 0;
      overflow: visible;
    }
    .route-path-segment {
      fill: none;
      stroke-linecap: round;
      stroke-linejoin: round;
      stroke-width: 8;
    }
    .route-path-segment.pending {
      stroke: var(--route-muted);
      stroke-dasharray: 12 14;
    }
    .route-path-segment.done {
      stroke: url(#routeProgressGradient);
    }
    .route-step {
      position: absolute;
      z-index: 1;
      width: 126px;
      transform: translate(-50%, -50%);
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      color: #64748b;
    }
    .route-node {
      position: relative;
      width: 40px;
      height: 40px;
      border-radius: 999px;
      border: 2px solid #dbe7f1;
      background: #f8fafc;
      color: #8aa0b6;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 0 6px #fff;
    }
    .route-node svg {
      width: 18px;
      height: 18px;
      stroke: currentColor;
    }
    .route-step.active .route-node {
      width: 54px;
      height: 54px;
      border-color: rgba(15, 159, 154, 0.24);
      background: linear-gradient(135deg, var(--route-active), var(--route-active-2));
      color: #fff;
      box-shadow: 0 0 0 8px rgba(15, 159, 154, 0.12), 0 12px 24px rgba(15, 159, 154, 0.22);
    }
    .route-step.done .route-node {
      border-color: rgba(22, 163, 74, 0.26);
      background: #16a34a;
      color: #fff;
    }
    .route-step-no {
      position: absolute;
      right: -4px;
      top: -5px;
      min-width: 20px;
      height: 20px;
      padding: 0 5px;
      border-radius: 999px;
      border: 2px solid #fff;
      background: #e8f2fb;
      color: #60758b;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 11px;
      font-weight: 800;
      line-height: 1;
      font-variant-numeric: tabular-nums;
      box-shadow: 0 2px 6px rgba(15, 23, 42, 0.08);
    }
    .route-step.active .route-step-no {
      background: #063b3a;
      color: #fff;
    }
    .route-copy {
      margin-top: 7px;
      min-width: 0;
    }
    .route-label {
      color: var(--route-text);
      font-size: 13.5px;
      font-weight: 750;
      line-height: 1.2;
      white-space: nowrap;
    }
    .route-eta {
      margin-top: 5px;
      color: #8aa0b6;
      font-size: 12px;
      font-weight: 600;
      white-space: nowrap;
    }
    .route-step.active .route-label {
      color: #064e4b;
      font-size: 14px;
    }
    .route-step.active .route-eta {
      color: var(--route-active);
    }
    .route-step.done .route-label {
      color: #166534;
    }
    .route-summary {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-top: 2px;
      padding-top: 12px;
      border-top: 1px solid #eef3f8;
    }
    .route-summary-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      min-width: 0;
      padding: 10px 12px;
      border-radius: 12px;
      background: #f8fbfd;
      color: #64748b;
      font-size: 12px;
      font-weight: 600;
    }
    .route-summary-item strong {
      color: #0f766e;
      font-size: 13.5px;
      font-weight: 800;
      white-space: nowrap;
    }
    @media (max-width: 680px) {
      .route-steps {
        padding: 14px 12px 12px;
      }
      .route-flow {
        min-height: 230px;
      }
      .route-step {
        width: 104px;
      }
      .route-summary {
        grid-template-columns: 1fr;
      }
    }
    .batch-stop {
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: var(--card);
      padding: 11px 12px;
      margin-bottom: 8px;
    }
    .batch-stop.active {
      border-color: var(--primary);
      box-shadow: inset 3px 0 0 var(--primary), var(--shadow-sm);
    }
    .batch-stop-head, .batch-patient-head, .batch-med-head {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: center;
      font-weight: 600;
      font-size: 13.5px;
      margin-bottom: 6px;
      color: var(--text);
    }
    .batch-patient {
      border-top: 1px dashed var(--border);
      padding-top: 9px;
      margin-top: 9px;
    }
    .batch-patient-profile {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 7px;
      margin: 8px 0;
      color: var(--muted);
      font-size: 12.5px;
    }
    .batch-patient-profile strong {
      color: var(--text);
      font-weight: 700;
    }
    .patient-edit-panel {
      margin-top: 10px;
      padding: 12px;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      background: rgba(255, 255, 255, 0.72);
    }
    .patient-edit-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 10px;
    }
    .patient-edit-grid label {
      display: grid;
      gap: 5px;
      font-size: 12px;
      color: var(--muted);
      font-weight: 600;
    }
    .patient-edit-grid input, .patient-edit-grid textarea {
      min-height: 0;
      font-size: 13px;
      padding: 8px 10px;
    }
    .patient-edit-grid textarea {
      min-height: 72px;
      resize: vertical;
    }
    .patient-edit-full {
      grid-column: 1 / -1;
    }
    .patient-edit-message {
      margin-top: 8px;
      font-size: 12.5px;
      color: var(--muted);
    }
    /* 闭环 B: 病人确认/拒绝状态 */
    .batch-patient.confirmed,
    .batch-patient.rejected,
    .batch-patient.timeout,
    .batch-patient.review {
      border: 1px solid transparent;
      border-radius: var(--radius-sm);
      padding: 9px 11px;
    }
    .batch-patient.confirmed {
      border-color: rgba(22, 163, 74, 0.28);
      background: rgba(240, 253, 244, 0.78);
    }
    .batch-patient.demo-focus {
      outline: 3px solid rgba(14, 165, 233, 0.38);
      outline-offset: 3px;
      background: #eff6ff;
      transition: outline-color 180ms ease, background 180ms ease;
    }
    .batch-patient.feedback-focus {
      outline: 3px solid rgba(217, 45, 32, 0.42);
      outline-offset: 3px;
      background: rgba(254, 226, 226, 0.88);
      transition: outline-color 180ms ease, background 180ms ease;
    }
    @media (prefers-reduced-motion: reduce) {
      .batch-patient.demo-focus, .batch-patient.feedback-focus { transition: none; }
    }
    .batch-patient.rejected {
      border-color: rgba(217, 45, 32, 0.24);
      background: rgba(254, 242, 242, 0.74);
    }
    .batch-patient.timeout {
      border-color: rgba(245, 158, 11, 0.32);
      background: rgba(255, 251, 235, 0.82);
      animation: timeoutBlink 1.6s ease-in-out infinite;
    }
    @keyframes timeoutBlink {
      0%, 100% { box-shadow: 0 0 0 0 rgba(245,158,11,0.0); }
      50%      { box-shadow: 0 0 0 3px rgba(245,158,11,0.20); }
    }
    .patient-status-pill {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      margin-left: 8px;
      padding: 2px 9px;
      border-radius: 999px;
      font-size: 11.5px;
      font-weight: 600;
      white-space: nowrap;
    }
    .patient-status-pill.confirmed {
      background: var(--ok-soft);
      color: var(--ok);
      border: 1px solid #bbf7d0;
    }
    .patient-status-pill.rejected {
      background: var(--danger-soft);
      color: var(--danger);
      border: 1px solid #fecaca;
    }
    .patient-status-pill.timeout {
      background: #fef3c7;
      color: #b45309;
      border: 1px solid #fcd34d;
    }
    .patient-status-pill.review {
      background: #ffedd5;
      color: #c2410c;
      border: 1px solid #fdba74;
    }
    .patient-status-reason {
      margin-top: 4px;
      font-size: 12px;
      color: var(--danger);
      font-style: italic;
    }
    .batch-med {
      border-radius: var(--radius-sm);
      border: 1px solid var(--border);
      padding: 9px 10px;
      margin-top: 6px;
      background: var(--surface);
      font-size: 12.5px;
    }
    .batch-med.loaded {
      border-color: #bfdbfe;
      background: var(--primary-soft);
    }
    .batch-med.dispensed {
      border-color: #86efac;
      background: var(--ok-soft);
    }
    .batch-med-details {
      margin-top: 6px;
    }
    .batch-med-details summary {
      cursor: pointer;
      color: var(--primary-dark);
      font-weight: 600;
      font-size: 12px;
    }
    .batch-status {
      display: inline-flex;
      border-radius: 999px;
      padding: 3px 8px;
      background: var(--surface);
      color: var(--muted);
      border: 1px solid var(--border);
      font-size: 11.5px;
      font-weight: 600;
      white-space: nowrap;
    }
    .batch-status.ok      { background: var(--ok-soft);      color: var(--ok);      border-color: #bbf7d0; }
    .batch-status.warn    { background: var(--warn-soft);    color: var(--warn);    border-color: #fde68a; }
    .batch-status.info    { background: var(--primary-soft); color: var(--primary-dark); border-color: #bfdbfe; }
    .batch-status.danger  { background: var(--danger-soft);  color: var(--danger);  border-color: #fecaca; }
    .batch-audit {
      max-height: calc(100vh - 360px);
      min-height: 420px;
      overflow: auto;
    }
    .batch-import {
      margin-top: 16px;
      border-top: 1px dashed var(--border);
      padding-top: 14px;
    }
    .batch-import summary {
      cursor: pointer;
      color: var(--primary-dark);
      font-weight: 600;
      font-size: 13.5px;
      margin-bottom: 10px;
    }

    /* 2026-06 report archive readiness gate for delivery closure. */
    .report-archive-gate {
      margin: 12px 0 14px;
      padding: 13px 14px;
      border: 1px solid #dbe7f1;
      border-radius: var(--radius);
      background: #f8fafc;
      color: #334155;
      font-size: 13px;
      line-height: 1.55;
    }
    .report-archive-gate.ok {
      border-color: #bbf7d0;
      background: #f0fdf4;
      color: #14532d;
    }
    .report-archive-gate.warn {
      border-color: #fde68a;
      background: #fffbeb;
      color: #78350f;
    }
    .report-archive-gate.danger {
      border-color: #fecaca;
      background: #fff5f5;
      color: #7f1d1d;
    }
    .report-archive-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 7px;
    }
    .report-archive-head strong {
      font-size: 14px;
      font-weight: 800;
      color: inherit;
    }
    .report-archive-head .badge {
      flex: 0 0 auto;
      background: rgba(255, 255, 255, 0.72);
    }
    .report-archive-list {
      display: grid;
      gap: 5px;
      margin: 8px 0 0;
      padding-left: 0;
      list-style: none;
    }
    .report-archive-list li {
      overflow-wrap: anywhere;
    }
    .report-archive-list li::before {
      content: '\2022 ';
      font-weight: 900;
    }
    .report-archive-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
      margin-top: 10px;
    }
    .report-archive-actions button {
      min-height: 32px;
      padding: 6px 10px;
      font-size: 12.5px;
    }
    @media (max-width: 760px) {
      .report-archive-head {
        align-items: flex-start;
        flex-direction: column;
      }
      .report-archive-actions button {
        flex: 1 1 150px;
      }
    }
    .report-summary-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(135px, 1fr));
      gap: 10px;
      margin: 14px 0 18px;
    }
    .report-summary-card {
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 13px 14px;
      background: #fbfcfd;
      min-width: 0;
    }
    .report-summary-card span {
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }
    .report-summary-card strong {
      display: block;
      font-size: 22px;
      font-weight: 700;
      color: var(--text);
      letter-spacing: 0;
    }
    .report-controls {
      display: grid;
      grid-template-columns: 1fr 1fr 1.3fr auto;
      gap: 12px;
      align-items: end;
      margin-bottom: 14px;
    }
    .report-section-title {
      margin: 18px 0 8px;
      color: var(--text);
      font-size: 15px;
      font-weight: 700;
    }
    .report-focus {
      outline: 3px solid rgba(14, 165, 233, 0.32);
      outline-offset: 4px;
      border-radius: 12px;
      transition: outline-color 180ms ease;
    }
    @media (prefers-reduced-motion: reduce) {
      .report-focus { transition: none; }
    }
    .signature-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
      margin-top: 18px;
      font-size: 13.5px;
    }
    .signature-grid div {
      border-top: 1px solid var(--border);
      padding-top: 10px;
      color: var(--muted);
    }
    .report-table-wrap {
      border: 1px solid var(--border);
      border-radius: var(--radius);
      overflow: auto;
      background: var(--card);
      max-height: calc(100vh - 390px);
    }
    .report-table {
      width: 100%;
      border-collapse: collapse;
      min-width: 980px;
      font-size: 13.5px;
    }
    .report-table th, .report-table td {
      border-bottom: 1px solid var(--border-soft);
      padding: 9px 11px;
      text-align: left;
      vertical-align: top;
    }
    .report-table th {
      background: #eef3f7;
      color: var(--muted);
      font-size: 12px;
      font-weight: 600;
      position: sticky;
      top: 0;
      z-index: 1;
    }
    .report-table tr:hover td { background: var(--surface); }
    .report-table tr:last-child td { border-bottom: 0; }
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 999px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--faint); }
    @media (max-width: 980px) {
      main { grid-template-columns: 1fr; }
      .grid-2 { grid-template-columns: 1fr; }
      .batch-layout { grid-template-columns: 1fr; }
      .report-summary-grid { grid-template-columns: 1fr 1fr; }
      .report-controls { grid-template-columns: 1fr; }
    }
    @media (max-width: 560px) {
      header {
        padding: 24px 18px 12px;
        display: block;
      }
      h1 { font-size: 24px; }
      main {
        display: block;
        padding: 12px 18px 36px;
        overflow-x: hidden;
      }
      .dashboard-tabs { padding: 6px 18px 12px; }
      .card { padding: 18px 16px; }
      [data-page].active { margin-bottom: 12px; }
      .status-head {
        display: block;
      }
      .status-head .badge { margin-top: 10px; }
      .actions button {
        flex: 1 1 calc(50% - 8px);
        min-width: 0;
      }
      .actions .primary {
        flex-basis: 100%;
      }
      .kv {
        grid-template-columns: 104px minmax(0, 1fr);
      }
    }
    .tab-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 18px;
      height: 18px;
      padding: 0 5px;
      margin-left: 6px;
      border-radius: 999px;
      background: #d92d20;
      color: #fff;
      font-size: 11px;
      font-weight: 700;
      line-height: 1;
      vertical-align: middle;
    }
    .tab-badge.review-tab-badge {
      background: #dc2626;
      color: #fff;
      box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.12);
    }
    .tab-button.has-review-alert {
      border-color: rgba(220, 38, 38, 0.32);
      background: #fff7f7;
      color: #991b1b;
    }
    .tab-button.has-review-alert small {
      color: #b45309;
      font-weight: 700;
    }

    .tab-badge.health-tab-badge {
      background: #f59e0b;
      color: #fff;
      box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.14);
    }
    .tab-badge.health-tab-badge.bad {
      background: #dc2626;
      box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.14);
    }
    .tab-button.has-health-alert {
      border-color: rgba(245, 158, 11, 0.36);
      background: #fffbeb;
      color: #92400e;
    }
    .tab-button.has-health-alert.bad {
      border-color: rgba(220, 38, 38, 0.32);
      background: #fff7f7;
      color: #991b1b;
    }
    .tab-button.has-health-alert small {
      color: #92400e;
      font-weight: 700;
    }
    .tab-button.has-health-alert.bad small {
      color: #b91c1c;
    }
    .messages-head-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .messages-head-actions .muted {
      color: #6b7280;
      font-size: 13.5px;
    }
    .nurse-name-input {
      padding: 6px 10px;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      font-size: 13.5px;
      width: 180px;
    }
    .nurse-name-input:focus {
      outline: none;
      border-color: #10b981;
    }
    .messages-empty {
      padding: 28px 12px;
      text-align: center;
      color: #94a3b8;
      border: 1px dashed #e5e7eb;
      border-radius: 10px;
    }
    /* === 微信式 IM 布局: 2/8 比例, 撑满主区高度 === */
    .im-layout {
      display: grid;
      grid-template-columns: 2fr 8fr;
      height: min(78vh, 900px);
      min-height: 560px;
      margin-top: 12px;
      border: 1px solid #e5e7eb;
      border-radius: 14px;
      background: #fff;
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
    }
    .im-sidebar {
      display: flex;
      flex-direction: column;
      border-right: 1px solid #eef2f7;
      background: #f8fafc;
      min-width: 0;
    }
    .im-sidebar-head {
      padding: 10px 12px;
      border-bottom: 1px solid #eef2f7;
      background: #fff;
      font-size: 13.5px;
      color: #475569;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }
    .im-sidebar-head strong { color: #0f172a; }
    .im-sidebar-list {
      flex: 1;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
    }
    .im-sidebar-empty {
      padding: 28px 14px;
      text-align: center;
      color: #94a3b8;
      font-size: 13.5px;
    }
    .im-thread-item {
      display: grid;
      grid-template-columns: 36px minmax(0, 1fr) auto;
      gap: 10px;
      padding: 10px 12px;
      border-bottom: 1px solid #eef2f7;
      cursor: pointer;
      background: #fff;
      transition: background 0.12s ease;
    }
    .im-thread-item:hover { background: #f1f5f9; }
    .im-thread-item.active {
      background: #ecfdf5;
      box-shadow: inset 0 0 0 1px rgba(16, 185, 129, 0.24);
    }
    .im-thread-avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: #cffafe;
      color: #0e7490;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 13.5px;
      letter-spacing: 0.5px;
      grid-row: span 2;
    }
    .im-thread-item.has-unread .im-thread-avatar {
      background: #fee2e2;
      color: #b91c1c;
    }
    .im-thread-item.has-risk {
      background: #fff7ed;
    }
    .im-thread-item.has-risk.active {
      background: #fffbeb;
      box-shadow: inset 0 0 0 1px rgba(245, 158, 11, 0.32);
    }
    .im-thread-risk {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      width: max-content;
      max-width: 100%;
      margin-top: 2px;
      padding: 1px 7px;
      border-radius: 999px;
      background: #fef3c7;
      color: #92400e;
      font-size: 11px;
      font-weight: 700;
    }
    .im-thread-main {
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .im-thread-bed {
      font-weight: 700;
      font-size: 14px;
      color: #0f172a;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .im-thread-snippet {
      font-size: 12px;
      color: #64748b;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .im-thread-side {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      justify-self: end;
    }
    .im-thread-time {
      font-size: 11px;
      color: #94a3b8;
      white-space: nowrap;
    }
    .im-thread-unread {
      background: #d92d20;
      color: #fff;
      font-size: 11px;
      font-weight: 700;
      padding: 1px 7px;
      border-radius: 999px;
      min-width: 18px;
      text-align: center;
    }
    /* 右侧聊天面板 */
    .im-main {
      display: flex;
      flex-direction: column;
      min-width: 0;
      /* fix: grid item 默认 min-height:auto, 内容多时会撑爆 .im-layout 的 900px 上限,
         把下面的 quick + input 区推到屏幕外。min-height:0 让它能被高度约束 */
      min-height: 0;
      background: #fff;
    }
    .im-main-empty {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #94a3b8;
      font-size: 14px;
      padding: 24px;
      text-align: center;
    }
    .im-main-head {
      padding: 12px 18px;
      border-bottom: 1px solid #eef2f7;
      background: #fafbff;
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }
    .im-main-head .bed {
      font-size: 17px;
      font-weight: 700;
      color: #0f172a;
    }
    .im-main-head .delivery-id {
      font-family: ui-monospace, "JetBrains Mono", Consolas, monospace;
      font-size: 12px;
      color: #0d9488;
      background: #f0fdfa;
      padding: 2px 8px;
      border-radius: 6px;
    }
    .im-main-head .unread-pill {
      background: #d92d20;
      color: #fff;
      font-size: 11px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 999px;
    }
    .im-main-head .meta {
      margin-left: auto;
      font-size: 12px;
      color: #64748b;
    }
    .im-main-body {
      flex: 1;
      /* fix: flex item 默认 min-height:auto, 内容多时不会触发自身滚动反而撑爆父亲 */
      min-height: 0;
      overflow-y: auto;
      padding: 16px 18px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      background: linear-gradient(180deg, #fafbff 0%, #ffffff 100%);
    }
    .msg-row {
      display: flex;
      max-width: 100%;
    }
    .msg-row.patient { justify-content: flex-start; }
    .msg-row.nurse { justify-content: flex-end; }
    .msg-bubble {
      max-width: 78%;
      padding: 9px 13px;
      border-radius: 14px;
      font-size: 14px;
      line-height: 1.55;
      white-space: pre-wrap;
      word-break: break-word;
      position: relative;
    }
    .msg-row.patient .msg-bubble {
      background: #f1f5f9;
      color: #0f172a;
      border-top-left-radius: 4px;
    }
    .msg-row.nurse .msg-bubble {
      background: #d1fae5;
      color: #064e3b;
      border-top-right-radius: 4px;
    }
    .msg-row.patient .msg-bubble.unread {
      background: #fef2f2;
      box-shadow: 0 0 0 2px rgba(217, 45, 32, 0.15);
    }
    .msg-row.patient .msg-bubble.risk,
    .msg-row.system .msg-bubble.risk {
      background: #fff7ed;
      color: #7c2d12;
      border: 1px solid #fed7aa;
      box-shadow: 0 0 0 2px rgba(251, 146, 60, 0.14);
    }
    .msg-risk-label {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      margin: 0 0 6px;
      padding: 2px 8px;
      border-radius: 999px;
      background: #ffedd5;
      color: #9a3412;
      font-size: 12px;
      font-weight: 800;
    }
    /* 系统事件 (病人确认/拒绝/反馈), 居中黄色横条 */
    .msg-row.system { justify-content: center; }
    .msg-row.system .msg-bubble {
      background: #fffbeb;
      color: #92400e;
      border: 1px dashed #f59e0b;
      border-radius: 10px;
      max-width: 92%;
      text-align: center;
      font-size: 13.5px;
      font-weight: 500;
    }
    .msg-row.system .msg-bubble.alert {
      background: #fef2f2;
      color: #991b1b;
      border-color: #dc2626;
      font-weight: 600;
    }
    .msg-row.system .msg-meta {
      text-align: center;
      color: #92400e;
    }
    .msg-meta {
      font-size: 11px;
      color: #94a3b8;
      margin-top: 3px;
    }
    .msg-row.nurse .msg-meta { text-align: right; }
    .im-main-quick {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      padding: 8px 18px;
      border-top: 1px solid #eef2f7;
      background: #fff;
    }
    .im-main-quick button {
      padding: 4px 10px;
      font-size: 12px;
      border: 1px solid #e5e7eb;
      background: #fff;
      color: #475569;
      border-radius: 999px;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .im-main-quick button:hover {
      border-color: #10b981;
      color: #047857;
      background: #f0fdf4;
    }
    .im-main-quick button.risk-reply {
      border-color: #fdba74;
      background: #fff7ed;
      color: #9a3412;
      font-weight: 700;
    }
    .im-main-quick button.risk-reply:hover {
      border-color: #f97316;
      background: #ffedd5;
      color: #7c2d12;
    }
    .im-main-input {
      padding: 10px 18px 14px;
      border-top: 1px solid #eef2f7;
      background: #fff;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .im-main-input textarea {
      width: 100%;
      box-sizing: border-box;
      min-height: 78px;
      max-height: 180px;
      padding: 10px 12px;
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      font-size: 14px;
      font-family: inherit;
      line-height: 1.5;
      resize: vertical;
      background: #fff;
      color: #0f172a;
    }
    .im-main-input textarea:focus {
      outline: none;
      border-color: #10b981;
      box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.12);
    }
    .im-main-input-bar {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .im-main-input-bar .hint {
      font-size: 12px;
      color: #94a3b8;
      flex: 1 1 200px;
      min-width: 0;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .im-main-input-bar button {
      padding: 10px 28px;
      font-size: 14px;
      white-space: nowrap;
      flex: 0 0 auto;
    }
    @media (max-width: 860px) {
      .im-layout {
        grid-template-columns: 1fr;
        grid-template-rows: 220px 1fr;
        height: min(85vh, 760px);
      }
      .im-sidebar { border-right: none; border-bottom: 1px solid #eef2f7; }
    }
    @media (min-width: 1400px) {
      .im-layout { height: min(82vh, 1000px); }
    }
    @media (max-width: 1100px) {
      header {
        align-items: stretch;
        flex-direction: column;
      }
      .runtime-strip {
        grid-template-columns: repeat(3, minmax(0, 1fr));
        max-width: none;
      }
      .vision-layout {
        grid-template-columns: 1fr;
      }
    }

    /* 2026-06 mobile/tablet hardening for 8085 workbench. Business logic unchanged. */
    html, body {
      width: 100%;
      max-width: 100%;
    }
    header, .dashboard-tabs, main {
      width: 100%;
      max-width: min(1680px, 100%);
    }
    .header-title,
    .runtime-strip,
    .card,
    .batch-layout,
    .batch-panel,
    .exception-center,
    .vision-layout,
    .im-layout,
    .im-main,
    .im-sidebar {
      min-width: 0;
    }
    .batch-stop-head,
    .batch-patient-head,
    .batch-med-head,
    .medication-title,
    .exception-item-head,
    .status-head {
      min-width: 0;
    }
    .batch-stop-head > *,
    .batch-patient-head > *,
    .batch-med-head > *,
    .medication-title > *,
    .exception-item-title,
    .exception-reason,
    .exception-center-title,
    .audit-detail,
    .im-main-head .delivery-id {
      min-width: 0;
      overflow-wrap: anywhere;
    }
    @media (max-width: 1280px) {
      .batch-layout {
        grid-template-columns: minmax(280px, 0.95fr) minmax(420px, 1.25fr);
      }
      .batch-panel.audit-panel {
        grid-column: 1 / -1;
      }
    }
    @media (max-width: 1180px) {
      .batch-layout {
        grid-template-columns: 1fr;
      }
      #batch_stops,
      .batch-audit {
        max-height: none;
        min-height: 0;
      }
      .batch-audit {
        overflow: visible;
      }
    }
    @media (max-width: 760px) {
      header {
        padding: 18px 14px 10px;
        gap: 12px;
      }
      h1 {
        font-size: 22px;
      }
      .subtitle {
        font-size: 12.5px;
        max-width: none;
      }
      .runtime-strip {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
      }
      .runtime-cell {
        min-height: 50px;
        padding: 7px 8px;
      }
      .runtime-cell strong {
        white-space: normal;
        overflow-wrap: anywhere;
        font-size: 12.5px;
        line-height: 1.25;
      }
      .dashboard-tabs {
        padding: 8px 12px 10px;
        gap: 8px;
        scroll-padding-inline: 12px;
      }
      .tab-button {
        padding: 8px 10px;
      }
      .tab-button span,
      .tab-button small {
        white-space: normal;
      }
      main {
        display: block;
        padding: 12px 12px 36px;
      }
      .card {
        padding: 16px 14px;
      }
      .grid-2,
      .recognized-grid,
      .closed-loop-steps,
      .exception-summary,
      .report-summary-grid,
      .signature-grid {
        grid-template-columns: 1fr;
      }
      .status-head,
      .exception-center-head,
      .exception-resolution-strip,
      .batch-stop-head,
      .batch-patient-head,
      .batch-med-head,
      .medication-title,
      .route-summary-item {
        align-items: flex-start;
        flex-wrap: wrap;
      }
      .status-head {
        display: flex;
      }
      .exception-center-head,
      .exception-resolution-strip {
        flex-direction: column;
      }
      .exception-center-head > *,
      .exception-resolution-strip > * {
        width: 100%;
      }
      .exception-filter-row {
        padding: 9px 10px;
      }
      .exception-list {
        max-height: none;
        overflow: visible;
        padding: 10px;
      }
      .exception-item-head {
        flex-direction: column;
      }
      .exception-type-pill {
        align-self: flex-start;
        white-space: normal;
      }
      .exception-actions .small-button,
      .actions button {
        flex: 1 1 100%;
        min-width: 0;
        white-space: normal;
      }
      .patient-status-pill,
      .batch-status,
      .badge {
        white-space: normal;
      }
      .patient-status-pill {
        margin-left: 0;
      }
      .route-label,
      .route-eta,
      .route-summary-item strong {
        white-space: normal;
        overflow-wrap: anywhere;
      }
      .route-flow {
        min-height: 210px;
      }
      .route-step {
        width: 96px;
      }
      .report-table-wrap {
        max-height: none;
      }
      .nurse-name-input {
        width: 100%;
        max-width: 220px;
      }
      .messages-head-actions {
        align-items: stretch;
      }
      .im-layout {
        height: auto;
        min-height: 0;
        grid-template-rows: auto minmax(480px, auto);
      }
      .im-sidebar-list {
        max-height: 260px;
      }
      .im-main-head .meta {
        margin-left: 0;
        width: 100%;
      }
      .msg-bubble {
        max-width: 90%;
      }
      .im-main-input-bar .hint {
        flex-basis: 100%;
        white-space: normal;
      }
      .im-main-input-bar button {
        width: 100%;
        flex: 1 1 100%;
      }
    }
    @media (max-width: 420px) {
      header {
        padding-inline: 10px;
      }
      .runtime-strip {
        grid-template-columns: 1fr;
      }
      .dashboard-tabs {
        padding-inline: 10px;
      }
      .tab-button small {
        display: none;
      }
      main {
        padding-inline: 10px;
      }
      .card {
        padding: 14px 12px;
      }
      .route-flow {
        min-height: 190px;
      }
      .route-step {
        width: 82px;
      }
      .route-node {
        width: 34px;
        height: 34px;
      }
      .route-step.active .route-node {
        width: 44px;
        height: 44px;
      }
      .im-main-body,
      .im-main-head,
      .im-main-quick,
      .im-main-input {
        padding-left: 12px;
        padding-right: 12px;
      }
    }



    /* 2026-06 import preview hardening for external delivery batch JSON. */
    .batch-import-preview {
      margin: 10px 0 12px;
      border: 1px solid #dbe7f1;
      border-radius: 12px;
      background: #f8fafc;
      padding: 12px;
    }
    .batch-import-preview.is-ok {
      border-color: #bbf7d0;
      background: #f0fdf4;
    }
    .batch-import-preview.has-warn {
      border-color: #fdba74;
      background: #fff7ed;
    }
    .batch-import-preview.has-error {
      border-color: #fecaca;
      background: #fff5f5;
    }
    .batch-import-preview-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
    }
    .batch-import-preview-head strong {
      color: var(--text);
      font-size: 13.5px;
      font-weight: 800;
    }
    .batch-import-preview-head span {
      color: var(--muted);
      font-size: 12.5px;
      line-height: 1.45;
    }
    .batch-import-preview-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
      margin-bottom: 10px;
    }
    .batch-import-preview-stat {
      border: 1px solid rgba(226, 232, 240, 0.95);
      border-radius: 10px;
      background: #fff;
      padding: 9px 10px;
      min-width: 0;
    }
    .batch-import-preview-stat span {
      display: block;
      color: var(--muted);
      font-size: 11.5px;
      font-weight: 700;
    }
    .batch-import-preview-stat strong {
      display: block;
      margin-top: 4px;
      color: var(--text);
      font-size: 16px;
      line-height: 1.2;
      overflow-wrap: anywhere;
    }
    .batch-import-preview-list {
      display: grid;
      gap: 6px;
      margin-top: 8px;
      padding-left: 0;
      list-style: none;
      color: #475569;
      font-size: 12.5px;
      line-height: 1.5;
    }
    .batch-import-preview-list li {
      overflow-wrap: anywhere;
    }
    .batch-import-preview-list li::before {
      content: '\2022 ';
      color: var(--primary);
      font-weight: 900;
    }
    .batch-import-preview-list li.issue-error::before { color: var(--danger); }
    .batch-import-preview-list li.issue-warn::before { color: var(--warn); }
    @media (max-width: 760px) {
      .batch-import-preview-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .batch-import-preview-head {
        flex-direction: column;
      }
    }
    @media (max-width: 420px) {
      .batch-import-preview-grid {
        grid-template-columns: 1fr;
      }
    }


    /* 2026-06-29 operator feedback: non-blocking toasts for long-running actions. */
    .dashboard-toast-host {
      position: fixed;
      right: 18px;
      bottom: 18px;
      z-index: 80;
      display: grid;
      gap: 8px;
      width: min(380px, calc(100vw - 24px));
      pointer-events: none;
    }
    .dashboard-toast {
      pointer-events: auto;
      border: 1px solid #dbe7f1;
      border-radius: 14px;
      background: rgba(255,255,255,0.94);
      color: var(--ink);
      box-shadow: 0 12px 28px rgba(15, 23, 42, 0.14);
      padding: 10px 12px;
      display: grid;
      gap: 2px;
      backdrop-filter: blur(10px);
    }
    .dashboard-toast strong { font-size: 13px; line-height: 1.35; }
    .dashboard-toast span { color: var(--muted); font-size: 12.5px; line-height: 1.45; overflow-wrap: anywhere; }
    .dashboard-toast.ok { border-color: #bbf7d0; background: rgba(240,253,244,0.96); }
    .dashboard-toast.warn { border-color: #fde68a; background: rgba(255,251,235,0.96); }
    .dashboard-toast.danger { border-color: #fecaca; background: rgba(255,245,245,0.96); }
    .is-busy-action { opacity: .72; cursor: wait !important; }
    @media (max-width: 760px) { .dashboard-toast-host { left: 12px; right: 12px; bottom: 12px; width: auto; } }

    /* 2026-06 readability/action hardening for 8085 workbench. CSS-only. */
    button {
      min-height: 36px;
      line-height: 1.25;
      white-space: normal;
      overflow-wrap: anywhere;
      touch-action: manipulation;
    }
    button:active {
      transform: translateY(1px);
    }
    button:disabled,
    button[disabled] {
      transform: none;
    }
    .small-button {
      min-height: 32px;
      line-height: 1.25;
    }
    .primary {
      min-height: 42px;
      line-height: 1.28;
    }
    .tab-button {
      min-height: 48px;
    }
    .status-head h2,
    .batch-panel h2,
    .exception-center-title strong {
      overflow-wrap: anywhere;
    }
    .badge,
    .batch-status,
    .patient-status-pill,
    .exception-type-pill,
    .tab-badge {
      line-height: 1.2;
      text-align: center;
    }
    .exception-item {
      padding: 12px 13px;
      border-color: #dbe7f1;
      background: #fbfdff;
    }
    .exception-item.danger {
      border-color: #fca5a5;
      background: #fff5f5;
    }
    .exception-item.warn {
      border-color: #fdba74;
      background: #fff7ed;
    }
    .exception-item.info {
      border-color: #93c5fd;
      background: #eff6ff;
    }
    .exception-item-title {
      line-height: 1.35;
    }
    .exception-item-title small,
    .exception-reason {
      overflow-wrap: anywhere;
    }
    .exception-actions {
      gap: 7px;
    }
    .exception-actions .small-button {
      min-height: 34px;
      padding: 7px 10px;
    }
    .exception-filter-button {
      min-height: 32px;
    }
    .batch-stop,
    .batch-patient,
    .batch-med,
    .medication-item,
    .audit-item {
      min-width: 0;
      overflow-wrap: anywhere;
    }
    .batch-stop-head,
    .batch-patient-head,
    .batch-med-head,
    .medication-title,
    .audit-head {
      align-items: flex-start;
    }
    .batch-patient.review {
      border-color: #fdba74;
      background: #fff7ed;
    }
    .batch-patient.rejected {
      border-color: #fca5a5;
      background: #fff5f5;
    }
    .batch-patient.timeout {
      border-color: #facc15;
      background: #fffbeb;
    }
    .patient-status-reason {
      color: #991b1b;
      font-style: normal;
      font-weight: 650;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }
    .batch-patient-profile {
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    }
    .batch-med-details summary {
      min-height: 28px;
      display: inline-flex;
      align-items: center;
    }
    /* 2026-06 batch scan preview: show exact current-batch target before writing load/dispense audit. */
    .batch-scan-preview {
      margin: 8px 0 10px;
      min-height: 258px;
      padding: 11px 12px;
      border: 1px solid #dbe7f1;
      border-radius: 14px;
      background: #f8fafc;
      color: #334155;
      overflow-anchor: none;
      transition: background-color 160ms ease, border-color 160ms ease;
    }
    .batch-scan-preview.match { border-color: #bbf7d0; background: #f0fdf4; }
    .batch-scan-preview.warn { border-color: #fde68a; background: #fffbeb; }
    .batch-scan-preview.mismatch { border-color: #fecaca; background: #fff5f5; }
    .batch-scan-preview-head { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: flex-start; gap: 10px; min-height: 48px; margin-bottom: 8px; }
    .batch-scan-preview-title { display: block; color: var(--ink); font-size: 13.5px; font-weight: 850; line-height: 1.35; }
    .batch-scan-preview-hint { display: -webkit-box; min-height: 36px; margin-top: 2px; color: var(--muted); font-size: 12.5px; line-height: 1.45; overflow: hidden; overflow-wrap: anywhere; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
    .batch-scan-preview .badge { min-width: 74px; white-space: normal; text-align: center; line-height: 1.15; }
    .batch-scan-preview-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
    .batch-scan-preview-item { min-width: 0; min-height: 72px; padding: 8px 9px; border: 1px solid rgba(148, 163, 184, 0.24); border-radius: 12px; background: rgba(255, 255, 255, 0.72); }
    .batch-scan-preview-item span { display: block; color: #64748b; font-size: 12px; line-height: 1.3; }
    .batch-scan-preview-item strong { display: -webkit-box; margin-top: 3px; color: var(--ink); font-size: 13px; line-height: 1.35; overflow: hidden; overflow-wrap: anywhere; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
    .batch-scan-preview-action { grid-column: 1 / -1; min-height: 78px; }
    .batch-scan-preview-action strong { -webkit-line-clamp: 3; }
    .auto-load-status {
      min-height: 70px;
      display: flex;
      align-items: center;
      overflow-anchor: none;
      transition: background-color 160ms ease, border-color 160ms ease, color 160ms ease;
    }
    #batch-auto-load-toggle { min-width: 168px; }
    @media (max-width: 760px) {
      .batch-scan-preview { min-height: 420px; }
      .batch-scan-preview-head { grid-template-columns: 1fr; }
      .batch-scan-preview-grid { grid-template-columns: 1fr; }
      .auto-load-status { min-height: 88px; }
    }
    @media (prefers-reduced-motion: reduce) {
      .batch-scan-preview, .auto-load-status { transition: none; }
    }
    .audit-item {
      background: #fff;
    }
    .audit-item:hover {
      background: #f8fafc;
    }
    .audit-head {
      flex-wrap: wrap;
    }
    .audit-detail {
      line-height: 1.55;
    }
    .im-thread-item {
      min-height: 58px;
    }
    .im-thread-bed,
    .im-thread-snippet,
    .im-thread-time {
      min-width: 0;
    }
    .im-thread-risk {
      line-height: 1.25;
      overflow-wrap: anywhere;
    }
    .msg-bubble {
      line-height: 1.62;
      overflow-wrap: anywhere;
    }
    .msg-row.patient .msg-bubble.unread {
      border: 1px solid #fecaca;
    }
    .msg-row.patient .msg-bubble.risk,
    .msg-row.system .msg-bubble.risk {
      border-color: #fb923c;
    }
    .im-main-quick button {
      min-height: 32px;
      padding: 6px 11px;
      line-height: 1.25;
    }
    .im-main-input textarea {
      line-height: 1.55;
    }
    .im-main-input-bar button {
      min-height: 38px;
    }
    @media (max-width: 760px) {
      button {
        min-height: 40px;
      }
      .small-button,
      .exception-actions .small-button,
      .exception-filter-button,
      .im-main-quick button {
        min-height: 38px;
      }
      .batch-stop,
      .exception-item,
      .medication-item {
        padding: 12px;
      }
      .msg-bubble {
        max-width: 92%;
        font-size: 13.5px;
      }
    }

  </style>
</head>
<body>
  <header>
    <div class="header-title">
      <h1>智能送药工作台</h1>
      <div class="subtitle">药房装药、机器人配送、床旁签收和异常复核的统一工作台</div>
    </div>
    <div class="runtime-strip" aria-label="机器人运行状态">
      <div class="runtime-cell cold" id="rt_robot"><span>机器人</span><strong>R1 待连接</strong></div>
      <div class="runtime-cell cold" id="rt_battery"><span>电量</span><strong>待上报</strong></div>
      <div class="runtime-cell cold" id="rt_cabinet"><span>药舱</span><strong>锁定状态待确认</strong></div>
      <div class="runtime-cell cold" id="rt_estop"><span>急停</span><strong>待上报</strong></div>
      <div class="runtime-cell cold" id="rt_ros"><span>ROS2</span><strong>等待状态</strong></div>
      <div class="runtime-cell cold" id="rt_vision"><span>识别设备</span><strong>待检测</strong></div>
    </div>
  </header>
  <nav class="dashboard-tabs" aria-label="控制台分区">
    <button class="tab-button active" type="button" data-tab="batch"><span>配送执行<span id="review-tab-badge" class="tab-badge review-tab-badge" hidden>0</span></span><small id="review-tab-hint">批次 / 装药 / 推进</small></button>
    <button class="tab-button" type="button" data-tab="report"><span>审计报告</span><small>交付 / 异常 / 归档</small></button>
    <button class="tab-button" type="button" data-tab="task" data-kind="debug"><span>任务调试</span><small>单床 / 单药测试</small></button>
    <button class="tab-button" type="button" data-tab="vision"><span>药品识别</span><small>摄像头 / 条码 / OCR</small></button>
    <button class="tab-button" type="button" data-tab="monitor"><span>系统监控</span><small>底盘 / 负载 / 安全</small></button>
    <button class="tab-button" type="button" data-tab="messages"><span>病人咨询<span id="messages-tab-badge" class="tab-badge" hidden>0</span></span><small>消息 / 回复 / 提醒</small></button>
  </nav>
  <main>
    <section class="card batch-card active" data-page="batch">
      <div class="status-head">
        <h2>配送执行</h2>
        <div id="batch-status-badge" class="badge IDLE">WAITING</div>
      </div>
      <div id="batch_blocker_bar" class="safety-gate" role="status" aria-live="polite">
        <strong>当前可推进</strong>
        <div>等待批次和机器人状态刷新。</div>
      </div>
      <details id="safety_rule_panel" class="safety-rule-panel">
        <summary>&#x5B89;&#x5168;&#x95E8;&#x89C4;&#x5219;&#x8BF4;&#x660E;</summary>
        <div class="safety-rule-grid">
          <div><strong>&#x7CFB;&#x7EDF;&#x81EA;&#x68C0;</strong><span>&#x81EA;&#x68C0;&#x5F02;&#x5E38;&#x4F1A;&#x963B;&#x65AD;&#xFF1B;&#x5B89;&#x5168;&#x95E8;&#x81EA;&#x6D4B;&#x5931;&#x8D25;&#x4F1A;&#x963B;&#x65AD;&#xFF0C;&#x672A;&#x81EA;&#x6D4B;&#x4F1A;&#x63D0;&#x793A;&#x786E;&#x8BA4;&#x3002;</span></div>
          <div><strong>&#x836F;&#x54C1;&#x88C5;&#x8F7D;</strong><span>&#x672A;&#x5B8C;&#x6210;&#x88C5;&#x836F;&#x6838;&#x9A8C;&#x65F6;&#x4E0D;&#x80FD;&#x51FA;&#x53D1;&#xFF1B;&#x626B;&#x7801;&#x4E0D;&#x5339;&#x914D;&#x4E0D;&#x80FD;&#x5199;&#x5165;&#x88C5;&#x836F;&#x6216;&#x4EA4;&#x4ED8;&#x8BB0;&#x5F55;&#x3002;</span></div>
          <div><strong>&#x75C5;&#x4EBA;&#x590D;&#x6838;</strong><span>&#x75C5;&#x4EBA;&#x53CD;&#x9988;&#x3001;&#x5F85;&#x7528;&#x836F;&#x590D;&#x6838;&#x3001;&#x7591;&#x4F3C;&#x7528;&#x836F;&#x98CE;&#x9669;&#x54A8;&#x8BE2;&#x672A;&#x5904;&#x7406;&#x65F6;&#x4E0D;&#x80FD;&#x7EE7;&#x7EED;&#x63A8;&#x8FDB;&#x3002;</span></div>
          <div><strong>&#x5E95;&#x76D8;&#x5B89;&#x5168;</strong><span>&#x6025;&#x505C;&#x3001;&#x7535;&#x91CF;&#x4F4E;&#x3001;&#x5E95;&#x76D8;&#x672A;&#x8FDE;&#x63A5;&#x6216;&#x836F;&#x8231;&#x672A;&#x9501;&#x5B9A;&#x65F6;&#x7981;&#x6B62;&#x8FDB;&#x5165;&#x914D;&#x9001;&#x3002;</span></div>
          <div><strong>&#x6D41;&#x7A0B;&#x9636;&#x6BB5;</strong><span>&#x975E;&#x88C5;&#x836F;&#x9636;&#x6BB5;&#x4E0D;&#x80FD;&#x91CD;&#x590D;&#x88C5;&#x836F;&#xFF1B;&#x672A;&#x5230;&#x5E8A;&#x65C1;&#x4EA4;&#x4ED8;&#x9636;&#x6BB5;&#x4E0D;&#x80FD;&#x5199;&#x5165;&#x4EA4;&#x4ED8;&#x3002;</span></div>
          <div><strong>&#x5BA1;&#x8BA1;&#x7559;&#x75D5;</strong><span>&#x540E;&#x7AEF;&#x963B;&#x65AD;&#x4F1A;&#x8BB0;&#x5F55;&#x4E3A;&#x5B89;&#x5168;&#x95E8;&#x963B;&#x65AD;&#xFF0C;&#x53EF;&#x5728;&#x5BA1;&#x8BA1;&#x8BB0;&#x5F55;&#x4E2D;&#x7B5B;&#x9009;&#x67E5;&#x770B;&#x3002;</span></div>
        </div>
      </details>
      <div id="batch_workflow_guide" class="workflow-guide" aria-live="polite">
        <div class="workflow-guide-head">
          <strong id="batch_workflow_title">&#x4E0B;&#x4E00;&#x6B65;&#x64CD;&#x4F5C;</strong>
          <span id="batch_workflow_badge" class="badge IDLE">&#x5F85;&#x5237;&#x65B0;</span>
        </div>
        <div id="batch_workflow_body" class="workflow-guide-body">&#x7B49;&#x5F85;&#x6279;&#x6B21;&#x72B6;&#x6001;&#x5237;&#x65B0;&#x540E;&#xFF0C;&#x7CFB;&#x7EDF;&#x4F1A;&#x63D0;&#x793A;&#x5F53;&#x524D;&#x5E94;&#x6267;&#x884C;&#x7684;&#x64CD;&#x4F5C;&#x3002;</div>
        <div id="batch_workflow_actions" class="workflow-guide-actions"></div>
      </div>
      <div id="batch_closure_timeline" class="batch-closure-timeline" aria-live="polite">
        <div class="batch-closure-head">
          <div>
            <strong id="batch_closure_title">&#x6279;&#x6B21;&#x95ED;&#x73AF;&#x65F6;&#x95F4;&#x7EBF;</strong>
            <span id="batch_closure_hint">&#x7B49;&#x5F85;&#x6279;&#x6B21;&#x72B6;&#x6001;&#x5237;&#x65B0;&#x540E;&#x663E;&#x793A;&#x5BFC;&#x5165;&#x3001;&#x88C5;&#x836F;&#x3001;&#x914D;&#x9001;&#x3001;&#x7B7E;&#x6536;&#x3001;&#x5F02;&#x5E38;&#x548C;&#x5F52;&#x6863;&#x8FDB;&#x5EA6;&#x3002;</span>
          </div>
          <span id="batch_closure_badge" class="badge IDLE">&#x5F85;&#x5237;&#x65B0;</span>
        </div>
        <div id="batch_closure_steps" class="batch-closure-steps"></div>
      </div>
      <div class="batch-layout">
        <div class="batch-panel overview-panel">
          <h2 style="font-size: 18px; margin-bottom: 12px;">批次概览</h2>
          <div class="kv"><span>批次号</span><strong id="batch_id">-</strong></div>
          <div class="kv"><span>当前状态</span><strong id="batch_route_status">-</strong></div>
          <div class="kv"><span>当前位置</span><strong id="batch_current_station">-</strong></div>
          <div class="kv"><span>病房进度</span><strong id="batch_stop_progress">-</strong></div>
          <div class="kv"><span>病人进度</span><strong id="batch_patient_progress">-</strong></div>
          <div class="kv"><span>&#x7B7E;&#x6536;&#x72B6;&#x6001;</span><strong id="batch_receipt_progress">-</strong></div>
          <div class="kv"><span>药品进度</span><strong id="batch_medication_progress">-</strong></div>
          <div class="kv"><span>机器人编号</span><strong id="batch_robot_id">R1</strong></div>
          <div class="kv"><span>药舱状态</span><strong id="batch_cabinet_state">待上报</strong></div>
          <div class="kv"><span>最近扫码</span><strong id="batch_last_scan">暂无记录</strong></div>
          <div class="kv"><span>最近异常</span><strong id="batch_last_issue">暂无异常</strong></div>
          <div class="exception-summary" id="exception_summary">
            <div class="exception-stat danger"><span>&#x53CD;&#x9988;/&#x5F02;&#x5E38;</span><strong id="exception_stat_critical">0</strong></div>
            <div class="exception-stat warn"><span>&#x5F85;&#x590D;&#x6838;</span><strong id="exception_stat_review">0</strong></div>
            <div class="exception-stat warn"><span>&#x672A;&#x7B7E;&#x6536;</span><strong id="exception_stat_pending">0</strong></div>
            <div class="exception-stat ok"><span>&#x5DF2;&#x7B7E;&#x6536;</span><strong id="exception_stat_signed">0</strong></div>
          </div>
          <div class="route-steps" id="batch_route_steps"></div>
          <div class="action-section">
            <div class="action-section-title">主流程操作</div>
            <div id="batch_scan_preview" class="batch-scan-preview" aria-live="polite">
              <div class="batch-scan-preview-head">
                <div>
                  <span id="batch_scan_preview_title" class="batch-scan-preview-title">&#x5F53;&#x524D;&#x8BC6;&#x522B;&#x5339;&#x914D;</span>
                  <span id="batch_scan_preview_hint" class="batch-scan-preview-hint">&#x5C06;&#x836F;&#x76D2;&#x6761;&#x5F62;&#x7801;&#x6216;&#x8FFD;&#x6EAF;&#x7801;&#x653E;&#x5165;&#x8BC6;&#x522B;&#x6846;&#xFF0C;&#x7CFB;&#x7EDF;&#x4F1A;&#x5148;&#x9884;&#x89C8;&#x5339;&#x914D;&#x7684;&#x6279;&#x6B21;&#x836F;&#x54C1;&#x3002;</span>
                </div>
                <span id="batch_scan_preview_badge" class="badge IDLE">&#x5F85;&#x8BC6;&#x522B;</span>
              </div>
              <div class="batch-scan-preview-grid">
                <div class="batch-scan-preview-item"><span>&#x8BC6;&#x522B;&#x7ED3;&#x679C;</span><strong id="batch_scan_preview_code">-</strong></div>
                <div class="batch-scan-preview-item"><span>&#x5339;&#x914D;&#x836F;&#x54C1;</span><strong id="batch_scan_preview_med">-</strong></div>
                <div class="batch-scan-preview-item"><span>&#x5BF9;&#x5E94;&#x75C5;&#x4EBA;</span><strong id="batch_scan_preview_patient">-</strong></div>
                <div class="batch-scan-preview-item"><span>&#x53EF;&#x4FE1;&#x7B49;&#x7EA7;</span><strong id="batch_scan_preview_confidence">-</strong></div>
                <div class="batch-scan-preview-item batch-scan-preview-action"><span>&#x5904;&#x7406;&#x5EFA;&#x8BAE;</span><strong id="batch_scan_preview_action">-</strong></div>
              </div>
            </div>
            <div id="batch_auto_load_status" class="notice auto-load-status">&#x81EA;&#x52A8;&#x8BC6;&#x522B;&#x836F;&#x54C1;&#x672A;&#x5F00;&#x542F;&#x3002;&#x5F00;&#x542F;&#x540E;&#xFF0C;&#x540C;&#x65F6;&#x542F;&#x52A8; OCR &#x548C;&#x6761;&#x7801;/&#x8FFD;&#x6EAF;&#x7801;&#x8BC6;&#x522B;&#xFF1B;&#x5173;&#x95ED;&#x540E;&#xFF0C;&#x4E24;&#x8005;&#x90FD;&#x505C;&#x6B62;&#x3002</div>
            <div class="actions">
              <button id="batch-load-scan" class="secondary" type="button">药师装药核验</button>
              <button id="batch-auto-load-toggle" class="secondary" type="button">&#x5F00;&#x542F;&#x81EA;&#x52A8;&#x8BC6;&#x522B;&#x88C5;&#x836F;</button>
              <button id="batch-advance" class="primary-flow" type="button">进入下一配送阶段</button>
              <button id="batch-dispense-scan" class="secondary" type="button">床旁交付核验</button>
            </div>
          </div>
          <div class="action-section">
            <div class="action-section-title">报告导出</div>
            <div class="actions">
              <button id="export-batch-json" class="secondary" type="button">导出审计 JSON</button>
              <button id="export-batch-csv" class="secondary" type="button">导出配送明细 CSV</button>
            </div>
          </div>
          <div class="action-section">
            <div class="action-section-title">调试 / 管理</div>
            <div class="actions">
              <button id="voice-listen-60" class="secondary" type="button">语音对话 5 分钟</button>
              <button id="demo-review-scenario" class="secondary" type="button">&#x4E00;&#x952E;&#x590D;&#x6838;&#x6F14;&#x793A;</button>
              <button id="locate-feedback-patient" class="secondary" type="button">&#x5B9A;&#x4F4D;&#x53CD;&#x9988;&#x95EE;&#x9898;</button>
              <button id="safety-self-test" class="secondary" type="button">&#x5B89;&#x5168;&#x95E8;&#x81EA;&#x6D4B;</button>
              <button id="reset-batch" class="secondary" type="button">新建配送批次</button>
            </div>
            <div id="safety_self_test_latest" class="safety-self-test-result" hidden>
              <strong>&#x5B89;&#x5168;&#x95E8;&#x81EA;&#x6D4B;</strong><span>-</span>
            </div>
          </div>
          <div class="demo-flow-guide" id="demo_review_guide">
            <div class="demo-flow-head">
              <span>&#x590D;&#x6838;&#x95ED;&#x73AF;&#x6F14;&#x793A;</span>
              <span class="demo-flow-status" id="demo_review_status">&#x5F85;&#x751F;&#x6210;</span>
            </div>
            <div class="demo-flow-target" id="demo_review_target">&#x5F53;&#x524D;&#x5F85;&#x590D;&#x6838;&#xFF1A;&#x6682;&#x65E0;&#xFF0C;&#x8BF7;&#x5148;&#x70B9;&#x51FB;&#x201C;&#x4E00;&#x952E;&#x590D;&#x6838;&#x6F14;&#x793A;&#x201D;&#x3002;</div>
            <div class="demo-flow-steps">
              <div class="demo-flow-step" id="demo_step_generate"><strong>1. &#x751F;&#x6210;&#x5F85;&#x590D;&#x6838;</strong><span>&#x70B9;&#x51FB;&#x201C;&#x4E00;&#x952E;&#x590D;&#x6838;&#x6F14;&#x793A;&#x201D;&#xFF0C;&#x7CFB;&#x7EDF;&#x81EA;&#x52A8;&#x9009;&#x62E9;&#x75C5;&#x4EBA;&#x3002;</span></div>
              <div class="demo-flow-step" id="demo_step_handle"><strong>2. &#x62A4;&#x58EB;&#x5904;&#x7406;</strong><span>&#x5728;&#x75C5;&#x4EBA;&#x5361;&#x7247;&#x4E2D;&#x9009;&#x62E9;&#x201C;&#x590D;&#x6838;&#x901A;&#x8FC7;&#x201D;&#x6216;&#x201C;&#x9000;&#x56DE;&#x836F;&#x623F;&#x201D;&#x3002;</span></div>
              <div class="demo-flow-step" id="demo_step_report"><strong>3. &#x67E5;&#x770B;&#x7559;&#x75D5;</strong><span>&#x5207;&#x5230;&#x201C;&#x5BA1;&#x8BA1;&#x62A5;&#x544A;&#x201D;&#xFF0C;&#x67E5;&#x770B;&#x53CD;&#x9988;&#x3001;&#x5904;&#x7406;&#x548C;&#x7ED3;&#x679C;&#x3002;</span></div>
            </div>
            <div class="demo-flow-actions">
              <button id="demo-locate-review-patient" class="secondary small-button" type="button">&#x5B9A;&#x4F4D;&#x5F85;&#x590D;&#x6838;&#x75C5;&#x4EBA;</button>
              <button id="demo-continue-review" class="secondary small-button" type="button">&#x901A;&#x8FC7;&#x5F53;&#x524D;&#x590D;&#x6838;</button>
              <button id="demo-return-review" class="secondary small-button danger-action" type="button">&#x9000;&#x56DE;&#x5F53;&#x524D;&#x590D;&#x6838;</button>
              <button id="demo-open-review-report" class="secondary small-button" type="button">&#x67E5;&#x770B;&#x590D;&#x6838;&#x62A5;&#x544A;</button>
              <button id="demo-reset-review" class="secondary small-button reset-action" type="button">&#x91CD;&#x7F6E;&#x590D;&#x6838;&#x6F14;&#x793A;</button>
            </div>
          </div>
          <div class="notice" id="batch_action_result">&#x5148;&#x5B8C;&#x6210;&#x5168;&#x90E8;&#x88C5;&#x836F;&#x626B;&#x7801;&#xFF0C;&#x518D;&#x63A8;&#x8FDB;&#x5230; A/B/C &#x75C5;&#x623F;&#x4EA4;&#x4ED8;&#x3002;</div>
          <div class="recognized-panel" id="pending_batch_panel">
            <div class="recognized-panel-head">
              <strong>&#x5916;&#x90E8;&#x6279;&#x6B21;&#x5F85;&#x91C7;&#x7528;</strong>
              <span class="badge IDLE" id="pending_batch_badge">&#x65E0;&#x5F85;&#x91C7;&#x7528;</span>
            </div>
            <div class="recognized-grid">
              <div class="recognized-item"><span>&#x6765;&#x6E90;</span><strong id="pending_batch_source">-</strong></div>
              <div class="recognized-item"><span>&#x6279;&#x6B21;&#x53F7;</span><strong id="pending_batch_id">-</strong></div>
              <div class="recognized-item"><span>&#x63A5;&#x6536;&#x65F6;&#x95F4;</span><strong id="pending_batch_received_at">-</strong></div>
              <div class="recognized-item"><span>&#x60A3;&#x8005; / &#x836F;&#x54C1;</span><strong id="pending_batch_counts">-</strong></div>
            </div>
            <div class="actions" style="margin-top: 10px;">
              <button id="adopt-pending-batch" class="primary" type="button" disabled>&#x91C7;&#x7528;&#x6B64;&#x6279;&#x6B21;</button>
              <button id="discard-pending-batch" class="secondary" type="button" disabled>&#x5FFD;&#x7565;&#x5F85;&#x91C7;&#x7528;</button>
            </div>
            <div class="notice" id="pending_batch_result">&#x5916;&#x90E8;&#x7CFB;&#x7EDF;&#x53EF; POST /api/external/delivery_batch &#x4E0B;&#x53D1;&#x6279;&#x6B21;&#xFF1B;&#x7CFB;&#x7EDF;&#x5148;&#x6682;&#x5B58;&#xFF0C;&#x786E;&#x8BA4;&#x91C7;&#x7528;&#x540E;&#x624D;&#x8986;&#x76D6;&#x5F53;&#x524D;&#x914D;&#x9001;&#x6279;&#x6B21;&#x3002;</div>
          </div>
          <details class="batch-import">
            <summary>&#x5916;&#x90E8;&#x6279;&#x6B21; JSON &#x63A5;&#x6536; / &#x7F16;&#x8F91;</summary>
            <label for="batch_import_text">&#x5916;&#x90E8;&#x6279;&#x6B21; JSON</label>
            <textarea id="batch_import_text" spellcheck="false"></textarea>
            <input id="batch-import-file" type="file" accept=".json,application/json" hidden />
            <div id="batch_import_preview" class="batch-import-preview" aria-live="polite">
              <div class="batch-import-preview-head">
                <div>
                  <strong>&#x5BFC;&#x5165;&#x524D;&#x9884;&#x89C8;</strong>
                  <span id="batch_import_preview_hint">&#x8BF7;&#x5148;&#x586B;&#x5165;&#x6A21;&#x677F;&#x3001;&#x8F7D;&#x5165;&#x5F53;&#x524D;&#x6279;&#x6B21;&#x6216;&#x4ECE;&#x672C;&#x5730;&#x6587;&#x4EF6;&#x9009;&#x62E9; JSON&#x3002;</span>
                </div>
                <span class="badge IDLE" id="batch_import_preview_badge">&#x672A;&#x9884;&#x89C8;</span>
              </div>
              <div class="batch-import-preview-grid">
                <div class="batch-import-preview-stat"><span>&#x6279;&#x6B21;&#x53F7;</span><strong id="batch_import_preview_batch">-</strong></div>
                <div class="batch-import-preview-stat"><span>&#x75C5;&#x623F; / &#x60A3;&#x8005;</span><strong id="batch_import_preview_patients">-</strong></div>
                <div class="batch-import-preview-stat"><span>&#x836F;&#x54C1;&#x6570;</span><strong id="batch_import_preview_meds">-</strong></div>
                <div class="batch-import-preview-stat"><span>&#x8DEF;&#x7EBF;</span><strong id="batch_import_preview_route">-</strong></div>
              </div>
              <ul id="batch_import_preview_issues" class="batch-import-preview-list"></ul>
            </div>
            <div class="actions">
              <button id="load-batch-template" class="secondary" type="button">&#x586B;&#x5165;&#x6A21;&#x677F;</button>
              <button id="load-current-batch-json" class="secondary" type="button">&#x8F7D;&#x5165;&#x5F53;&#x524D;&#x6279;&#x6B21;</button>
              <button id="load-local-batch-json" class="secondary" type="button">&#x4ECE;&#x672C;&#x5730;&#x6587;&#x4EF6;&#x5BFC;&#x5165;</button>
              <button id="import-batch-json" class="primary" type="button" disabled>&#x5BFC;&#x5165;&#x5E76;&#x91C7;&#x7528;</button>
            </div>
            <div class="notice" id="batch_import_result">&#x652F;&#x6301;&#x5916;&#x90E8;&#x7CFB;&#x7EDF;&#x6216;&#x624B;&#x52A8;&#x5BFC;&#x5165;&#x75C5;&#x4EBA;/&#x836F;&#x54C1;&#x6E05;&#x5355; JSON&#xFF1B;&#x63A5;&#x6536;&#x524D;&#x5148;&#x770B;&#x9884;&#x89C8;&#x548C;&#x5B57;&#x6BB5;&#x68C0;&#x67E5;&#xFF0C;&#x63A5;&#x6536;&#x540E;&#x4E0D;&#x4F1A;&#x7ACB;&#x5373;&#x8986;&#x76D6;&#x5F53;&#x524D;&#x6279;&#x6B21;&#x3002;</div>
          </details>
        </div>
        <div class="batch-panel worklist-panel">
          <div class="exception-center" id="exception_center">
            <div class="exception-center-head">
              <div class="exception-center-title">
                <strong>&#x5F02;&#x5E38;&#x5904;&#x7406;&#x4E2D;&#x5FC3;</strong>
                <span id="exception_center_hint">&#x96C6;&#x4E2D;&#x663E;&#x793A;&#x53CD;&#x9988;&#x3001;&#x590D;&#x6838;&#x3001;&#x672A;&#x7B7E;&#x6536;&#x548C;&#x836F;&#x54C1;&#x5F02;&#x5E38;&#x3002;</span>
              </div>
              <span class="badge IDLE" id="exception_center_badge">0 &#x9879;</span>
            </div>
            <div class="exception-resolution-strip" id="exception_resolution_strip" hidden>
              <span id="exception_resolution_text">-</span>
            </div>
            <div class="exception-filter-row" id="exception_filter_row">
              <button class="exception-filter-button active" id="exception_filter_all" type="button" data-exception-filter="all">&#x5168;&#x90E8;</button>
              <button class="exception-filter-button" type="button" data-exception-filter="danger">&#x9AD8;&#x4F18;&#x5148;&#x7EA7;</button>
              <button class="exception-filter-button" type="button" data-exception-filter="medication_review">&#x5F85;&#x590D;&#x6838;</button>
              <button class="exception-filter-button" type="button" data-exception-filter="pending_message">&#x75C5;&#x4EBA;&#x54A8;&#x8BE2;</button>
              <button class="exception-filter-button" type="button" data-exception-filter="timeout">&#x672A;&#x7B7E;&#x6536;</button>
              <button class="exception-filter-button" type="button" data-exception-filter="medication_exception">&#x836F;&#x54C1;&#x5F02;&#x5E38;</button>
            </div>
            <div id="exception_center_list" class="exception-list">
              <div class="exception-empty">&#x5F53;&#x524D;&#x6CA1;&#x6709;&#x9700;&#x8981;&#x96C6;&#x4E2D;&#x5904;&#x7406;&#x7684;&#x5F02;&#x5E38;&#x3002;</div>
            </div>
          </div>
          <h2 style="font-size: 18px; margin-bottom: 12px;">病房 / 病人 / 药品清单</h2>
          <div id="batch_stops"></div>
        </div>
        <div class="batch-panel audit-panel">
          <h2 style="font-size: 18px; margin-bottom: 12px;">批次审计记录</h2>
          <div class="audit-filter-row">
            <label for="batch_audit_filter">审计筛选</label>
            <select id="batch_audit_filter">
              <option value="all">全部</option>
              <option value="fail">失败</option>
              <option value="medication_review">用药复核</option>
              <option value="patient_message">&#x75C5;&#x4EBA;&#x54A8;&#x8BE2;</option>
              <option value="patient_rejected">病人反馈</option>
              <option value="manual_review">药师复核</option>
              <option value="patient_absent">病人不在</option>
              <option value="medication_return">药品回收</option>
              <option value="advance">阶段推进</option>
              <option value="load_scan">装药校验</option>
              <option value="dispense_scan">床旁交付</option>
              <option value="system">系统事件</option>
            </select>
          </div>
          <div id="batch_safety_audit_summary" class="safety-audit-summary" hidden>
            <div><strong id="safety_audit_title">&#x5B89;&#x5168;&#x95E8;&#x963B;&#x65AD;</strong><span id="safety_audit_meta">-</span></div>
            <button id="safety_audit_filter_button" class="secondary small-button" type="button">&#x53EA;&#x770B;&#x963B;&#x65AD;</button>
          </div>
          <div id="batch_audit_records" class="audit-list batch-audit">
            <div class="audit-item"><div class="audit-detail">暂无批次审计记录</div></div>
          </div>
        </div>
      </div>
    </section>
    <section class="card" data-page="report">
      <div class="status-head">
        <h2>审计报告</h2>
        <div class="actions">
          <button id="refresh-report" class="secondary small-button" type="button">刷新报告</button>
          <button id="print-report" class="secondary small-button" type="button">打印报告</button>
          <button id="report-export-json" class="secondary small-button" type="button">导出审计 JSON</button>
          <button id="report-export-csv" class="secondary small-button" type="button">导出明细 CSV</button>
        </div>
      </div>
      <div class="kv"><span>批次号</span><strong id="report_batch_id">-</strong></div>
      <div class="kv"><span>生成时间</span><strong id="report_generated_at">-</strong></div>
      <div class="report-summary-grid">
        <div class="report-summary-card"><span>涉及病房</span><strong id="report_stop_count">0</strong></div>
        <div class="report-summary-card"><span>涉及病人</span><strong id="report_patient_count">0</strong></div>
        <div class="report-summary-card"><span>应配送药品</span><strong id="report_medication_count">0</strong></div>
        <div class="report-summary-card"><span>已完成交付</span><strong id="report_dispensed_count">0</strong></div>
        <div class="report-summary-card"><span>异常/回收</span><strong id="report_issue_count">0</strong></div>
        <div class="report-summary-card"><span>药师复核</span><strong id="report_review_count">0</strong></div>
        <div class="report-summary-card"><span>用药复核</span><strong id="report_med_review_count">0</strong></div>
      </div>
      <div class="notice" id="report_summary_text">等待当前配送批次生成审计摘要。</div>
      <div id="report_archive_gate" class="report-archive-gate" aria-live="polite">
        <div class="report-archive-head">
          <strong id="report_archive_title">&#x5F52;&#x6863;&#x524D;&#x68C0;&#x67E5;</strong>
          <span id="report_archive_badge" class="badge IDLE">&#x5F85;&#x5237;&#x65B0;</span>
        </div>
        <div id="report_archive_body">&#x7B49;&#x5F85;&#x62A5;&#x544A;&#x6570;&#x636E;&#x5237;&#x65B0;&#x540E;&#x68C0;&#x67E5;&#x662F;&#x5426;&#x53EF;&#x5F52;&#x6863;&#x3002;</div>
        <ul id="report_archive_issues" class="report-archive-list"></ul>
        <div id="report_archive_actions" class="report-archive-actions"></div>
      </div>
      <div class="report-controls">
        <div>
          <label for="report_ward_filter">病房筛选</label>
          <select id="report_ward_filter"></select>
        </div>
        <div>
          <label for="report_status_filter">状态筛选</label>
          <select id="report_status_filter">
            <option value="all">全部状态</option>
            <option value="pending">待处理</option>
            <option value="loaded">已装药未交付</option>
            <option value="dispensed">已交付</option>
            <option value="returned">已回收</option>
            <option value="exception">异常</option>
            <option value="reviewed">药师已复核</option>
          </select>
        </div>
        <div>
          <label for="report_search">关键词</label>
          <input id="report_search" placeholder="搜索病人、床号、药品、编码、追溯编号" />
        </div>
        <button id="clear-report-filters" class="secondary" type="button">清除筛选</button>
      </div>
      <div class="notice" id="report_filter_result">报告数据会随当前批次自动刷新。</div>
      <div class="report-section-title">用药复核记录</div>
      <div id="medication_review_report" class="report-table-wrap report-review-section" style="max-height: 220px;">
        <table class="report-table">
          <thead>
            <tr>
              <th>病房/床号</th>
              <th>病人</th>
              <th>触发原因</th>
              <th>处理结果</th>
              <th>处理时间</th>
              <th>影响</th>
            </tr>
          </thead>
          <tbody id="report_med_review_rows">
            <tr><td colspan="6">暂无用药复核记录</td></tr>
          </tbody>
        </table>
      </div>
      <div class="report-section-title">异常汇总</div>
      <div class="report-table-wrap" style="max-height: 220px;">
        <table class="report-table">
          <thead>
            <tr>
              <th>病房/床号</th>
              <th>病人</th>
              <th>药品</th>
              <th>异常类型</th>
              <th>处理方式</th>
              <th>复核人/时间</th>
            </tr>
          </thead>
          <tbody id="report_exception_rows">
            <tr><td colspan="6">暂无异常或回收记录</td></tr>
          </tbody>
        </table>
      </div>
      <div class="report-section-title">药品明细</div>
      <div class="report-table-wrap">
        <table class="report-table">
          <thead>
            <tr>
              <th>病房/床号</th>
              <th>病人</th>
              <th>药品</th>
              <th>编码/追溯</th>
              <th>状态</th>
              <th>异常/回收/复核</th>
            </tr>
          </thead>
          <tbody id="report_rows">
            <tr><td colspan="6">暂无报告数据</td></tr>
          </tbody>
        </table>
      </div>
    </section>
    <section class="card" data-page="task">
      <h2>创建送药任务</h2>
      <form id="task-form">
        <div class="grid-2">
          <div>
            <label for="target_station">目标站点</label>
            <select id="target_station" required></select>
          </div>
          <div>
            <label for="source_station">起点站点</label>
            <select id="source_station" required></select>
          </div>
        </div>
        <label for="medicine_name">药品名称</label>
        <input id="medicine_name" value="降压药" placeholder="例如：降压药" />
        <div class="patient-panel">
          <label for="patient_order">指定患者用药清单</label>
          <select id="patient_order"></select>
          <div class="recognized-grid" style="margin-top: 10px;">
            <div class="recognized-item"><span>患者</span><strong id="patient_name_view">-</strong></div>
            <div class="recognized-item"><span>床号</span><strong id="patient_bed_view">-</strong></div>
            <div class="recognized-item"><span>病区</span><strong id="patient_ward_view">-</strong></div>
            <div class="recognized-item"><span>目标站点</span><strong id="patient_target_view">-</strong></div>
          </div>
          <div class="actions">
            <button id="scan-patient-medication" class="secondary" type="button">扫码核对患者药品</button>
            <button id="create-patient-task" class="secondary" type="button">按患者清单创建任务</button>
          </div>
          <div class="notice" id="patient_match_result">请选择患者后，扫码核对此药是否属于该患者。</div>
          <div id="patient_medications" class="medication-list"></div>
        </div>
        <div class="recognized-panel">
          <div class="recognized-panel-head">
            <strong>识别结果联动</strong>
            <button id="use-recognized" class="secondary small-button" type="button">使用识别结果</button>
          </div>
          <div class="recognized-grid">
            <div class="recognized-item"><span>产品编码</span><strong id="task_product_code">-</strong></div>
            <div class="recognized-item"><span>产品型号</span><strong id="task_product_model">-</strong></div>
            <div class="recognized-item"><span>数量</span><strong id="task_quantity">-</strong></div>
            <div class="recognized-item"><span>追溯编号</span><strong id="task_trace_id">-</strong></div>
            <div class="recognized-item"><span>订单号</span><strong id="task_order_no">-</strong></div>
          </div>
          <div class="recognized-item" style="margin-top: 10px;"><span>将提交药品名称</span><strong id="task_medicine_preview">降压药</strong></div>
          <div class="closed-loop-steps" aria-label="药品识别闭环状态">
            <div class="closed-loop-step" id="loop_step_recognize">识别药名/追溯码</div>
            <div class="closed-loop-step" id="loop_step_match">匹配患者清单</div>
            <div class="closed-loop-step" id="loop_step_task">创建配送任务</div>
            <div class="closed-loop-step" id="loop_step_report">配送报告归档</div>
          </div>
          <div class="notice" id="autofill_hint">识别到结构化药名后会自动填充任务；条形码只作为追溯码进入核验和报告。</div>
        </div>
        <label for="patient_id">患者 ID</label>
        <input id="patient_id" value="patient_001" placeholder="例如：patient_001" />
        <button class="primary" type="submit">创建送药任务</button>
      </form>
      <div class="notice">提交后会调用 ROS2 服务 <b>/medicine/create_delivery_task</b>。任务管理节点会发布状态和语音播报文本。</div>
      <div id="result" class="log">等待操作...</div>
    </section>
    <section class="card" data-page="task">
      <div class="status-head">
        <h2>当前任务状态</h2>
        <div id="state-badge" class="badge IDLE">IDLE</div>
      </div>
      <div class="progress-wrap"><div id="progress" class="progress"></div></div>
      <div class="kv"><span>任务 ID</span><strong id="task_id">-</strong></div>
      <div class="kv"><span>状态说明</span><strong id="message">等待送药任务</strong></div>
      <div class="kv"><span>当前位置</span><strong id="current_station">-</strong></div>
      <div class="kv"><span>目标站点</span><strong id="target_station_view">-</strong></div>
      <div class="kv"><span>患者</span><strong id="state_patient">-</strong></div>
      <div class="kv"><span>床号</span><strong id="state_bed_no">-</strong></div>
      <div class="kv"><span>任务药品</span><strong id="task_medicine_name">-</strong></div>
      <div class="kv"><span>用药清单</span><strong id="state_medication_progress">-</strong></div>
      <div class="kv"><span>产品编码</span><strong id="state_product_code">-</strong></div>
      <div class="kv"><span>产品型号</span><strong id="state_product_model">-</strong></div>
      <div class="kv"><span>数量</span><strong id="state_quantity">-</strong></div>
      <div class="kv"><span>追溯编号</span><strong id="state_trace_id">-</strong></div>
      <div class="kv"><span>订单号</span><strong id="state_order_no">-</strong></div>
      <div class="kv"><span>装药确认</span><strong id="load_confirmed">-</strong></div>
      <div class="kv"><span>装药时间</span><strong id="load_confirmed_at">-</strong></div>
      <div class="kv"><span>取药确认</span><strong id="dispense_confirmed">-</strong></div>
      <div class="kv"><span>取药时间</span><strong id="dispense_confirmed_at">-</strong></div>
      <div class="kv"><span>最近校验</span><strong id="last_verification">-</strong></div>
      <div class="kv"><span>进度</span><strong id="progress_text">0%</strong></div>
      <h2 style="margin-top: 20px;">扫码确认记录</h2>
      <div id="verification_records" class="audit-list">
        <div class="audit-item"><div class="audit-detail">暂无扫码确认记录</div></div>
      </div>
      <div class="actions">
        <button id="refresh" class="secondary" type="button">刷新状态</button>
        <button id="verify-scan" class="secondary" type="button">扫码一致性校验</button>
        <button id="confirm-load" class="secondary" type="button">装药扫码确认</button>
        <button id="confirm-dispense" class="secondary" type="button">取药扫码确认</button>
        <button id="cancel" class="danger" type="button">取消当前任务</button>
      </div>
      <div class="notice" id="verify_result">等待扫码校验或装药/取药确认。</div>
    </section>
    <section class="card" data-page="monitor">
      <div class="status-head">
        <h2>底盘安全状态</h2>
        <div id="chassis_status_badge" class="badge IDLE">未启用</div>
      </div>
      <div class="recognized-grid">
        <div class="recognized-item"><span>桥接状态</span><strong id="chassis_bridge_state">未收到状态</strong></div>
        <div class="recognized-item"><span>串口</span><strong id="chassis_serial_port">-</strong></div>
        <div class="recognized-item"><span>MAVLink 心跳</span><strong id="chassis_mavlink_heartbeat">-</strong></div>
        <div class="recognized-item"><span>飞控身份</span><strong id="chassis_mavlink_identity">-</strong></div>
        <div class="recognized-item"><span>急停</span><strong id="chassis_emergency_stop">-</strong></div>
        <div class="recognized-item"><span>控制输出</span><strong id="chassis_control_output">-</strong></div>
        <div class="recognized-item"><span>目标速度</span><strong id="chassis_velocity_target">-</strong></div>
        <div class="recognized-item"><span>当前速度</span><strong id="chassis_current_speed">-</strong></div>
        <div class="recognized-item"><span>Watchdog</span><strong id="chassis_watchdog">-</strong></div>
        <div class="recognized-item"><span>更新时间</span><strong id="chassis_update_time">-</strong></div>
      </div>
      <div class="actions chassis-control-actions">
        <button id="chassis-estop-on" class="danger" type="button">开启急停</button>
        <button id="chassis-estop-off" class="secondary" type="button">解除急停</button>
        <button id="chassis-refresh" class="secondary" type="button">刷新底盘状态</button>
      </div>
      <div class="notice" id="chassis_action_result">急停操作会直接调用底盘桥接服务；解除急停前请确认现场安全。</div>
      <div class="notice" id="chassis_status_hint">未启用底盘桥接时这里会保持未收到状态；接飞控前应始终保持只读、禁控和急停。</div>
    </section>
    <section class="card" data-page="monitor">
      <div class="status-head">
        <h2>系统自检</h2>
        <div id="health_check_badge" class="badge IDLE">检测中</div>
      </div>
      <div class="load-summary">把工作台、病人端入口、底盘、语音、识别和当前批次集中到一个检查区，便于现场快速判断哪里没起来。</div>
      <div id="health_gate" class="health-gate cold" role="status" aria-live="polite">
        <div class="health-gate-head"><span id="health_gate_label">&#x81EA;&#x68C0;&#x7ED3;&#x8BBA;</span><strong id="health_gate_title">&#x6B63;&#x5728;&#x5224;&#x65AD;</strong></div>
        <p id="health_gate_message">&#x6B63;&#x5728;&#x8BFB;&#x53D6;&#x5DE5;&#x4F5C;&#x53F0;&#x3001;&#x75C5;&#x4EBA;&#x7AEF;&#x3001;&#x5E95;&#x76D8;&#x3001;&#x8BED;&#x97F3;&#x3001;&#x8BC6;&#x522B;&#x548C;&#x6279;&#x6B21;&#x72B6;&#x6001;&#x3002;</p>
      </div>
      <div class="health-check-grid">
        <div id="health_8085" class="recognized-item health-check-item cold"><span>8085 工作台</span><strong>-</strong></div>
        <div id="health_8081" class="recognized-item health-check-item cold"><span>8081 病人端</span><strong>-</strong></div>
        <div id="health_chassis" class="recognized-item health-check-item cold"><span>底盘 / ROS2</span><strong>-</strong></div>
        <div id="health_voice" class="recognized-item health-check-item cold"><span>语音窗口</span><strong>-</strong></div>
        <div id="health_vision" class="recognized-item health-check-item cold"><span>药品识别</span><strong>-</strong></div>
        <div id="health_batch" class="recognized-item health-check-item cold"><span>配送批次</span><strong>-</strong></div>
        <div id="health_safety" class="recognized-item health-check-item cold"><span>&#x5B89;&#x5168;&#x95E8;&#x81EA;&#x6D4B;</span><strong>-</strong></div>
      </div>
      <div class="notice health-check-hint" id="health_check_hint">正在汇总运行状态。</div>
    </section>
    <section class="card" data-page="monitor">
      <div class="status-head">
        <h2>硬件实时负载</h2>
        <div class="badge RUNNING">1 秒刷新</div>
      </div>
      <div class="load-summary">显示 RK3588 当前 CPU、GPU、NPU 的占用率；GPU/NPU 同时显示当前工作频率。</div>
      <div class="load-list">
        <div class="load-meter cpu">
          <div class="load-meter-head"><span>CPU 总占用</span><strong id="load_cpu_text">-</strong></div>
          <div class="load-track"><div id="load_cpu_bar" class="load-fill"></div></div>
        </div>
        <div class="load-meter gpu">
          <div class="load-meter-head"><span>GPU 图形负载</span><strong id="load_gpu_text">-</strong></div>
          <div class="load-track"><div id="load_gpu_bar" class="load-fill"></div></div>
        </div>
        <div class="load-meter npu">
          <div class="load-meter-head"><span>NPU 推理负载</span><strong id="load_npu_text">-</strong></div>
          <div class="load-track"><div id="load_npu_bar" class="load-fill"></div></div>
        </div>
      </div>
      <div class="notice">NPU 负载来自 RK3588 devfreq。OCR 识别触发时 NPU 会出现短时间高占用，这是正常现象。</div>
    </section>
    <section class="card drug-card" data-page="vision">
      <div class="status-head">
        <h2>药品识别</h2>
        <div id="vision-status-badge" class="badge IDLE">待检测</div>
      </div>
      <div class="vision-layout">
        <div class="vision-panel">
          <h3>摄像头预览</h3>
          <div class="camera-preview-toolbar">
            <div class="camera-preview-hint">默认高清 MJPEG 直连，用于药品小字核对；流畅模式使用 WebRTC。</div>
            <div class="camera-preview-mode" aria-label="摄像头预览模式">
              <button id="camera-mode-hd" class="active" type="button">高清</button>
              <button id="camera-mode-smooth" type="button">流畅</button>
            </div>
          </div>
          <div class="camera-preview-wrap">
            <video id="camera-preview-video" autoplay playsinline muted></video>
            <img id="camera-preview" hidden alt="摄像头识别画面" />
            <div id="barcode-roi-overlay" class="vision-roi-overlay barcode-roi-overlay" aria-hidden="true"></div>
            <div id="ocr-roi-overlay" class="vision-roi-overlay ocr-roi-overlay" aria-hidden="true"></div>
            <div id="camera-empty" class="camera-empty">
              <strong>摄像头未连接</strong>
              <span>未收到 MJPEG 画面时仍可使用扫码器或手动录入药品编码。</span>
            </div>
          </div>
          <div class="notice" id="vision_hint">请检查摄像头连接、medicine_vision_detector 节点和 MJPEG 地址。</div>
        </div>
        <div class="vision-panel">
          <h3>识别状态</h3>
          <div class="vision-controls">
            <button id="vision-qr-toggle" class="secondary small-button" type="button">打开条形码识别</button>
            <button id="vision-ocr-once" class="secondary small-button" type="button">OCR 识别文字</button>
          </div>
          <div class="kv"><span>节点状态</span><strong id="vision_node_state">待检测</strong></div>
          <div class="kv"><span>条形码识别</span><strong id="qr_runtime_state">未开启</strong></div>
          <div class="kv"><span>OCR 模式</span><strong id="ocr_runtime_state">待触发</strong></div>
          <div class="kv"><span>最近帧时间</span><strong id="vision_frame_time">-</strong></div>
          <div class="kv"><span>目标帧率</span><strong id="vision_fps">-</strong></div>
          <div class="kv"><span>实际采集帧率</span><strong id="vision_actual_fps">-</strong></div>
          <div class="kv"><span>Web显示帧率</span><strong id="vision_display_fps">-</strong></div>
          <div class="kv"><span>结果状态</span><strong id="vision_match_status">未识别</strong></div>
          <ol class="diagnostic-list">
            <li>确认摄像头 USB/CSI 已连接。</li>
            <li>确认 medicine_vision_detector 节点已启动。</li>
            <li>确认 MJPEG 地址 8090/stream.mjpg 可访问。</li>
          </ol>
        </div>
        <div class="vision-panel">
          <h3>最近识别结果</h3>
                              <div id="recognition_state_card" class="recognition-state-card" aria-live="polite">
            <div class="recognition-state-title"><span id="recognition_state_title">&#x7B49;&#x5F85;&#x8BC6;&#x522B;</span><span id="recognition_stability_badge">&#x672A;&#x7A33;&#x5B9A;</span></div>
            <div id="recognition_state_body" class="recognition-state-body">&#x8BF7;&#x5C06;&#x836F;&#x76D2;&#x6587;&#x5B57;&#x6216;&#x6761;&#x5F62;&#x7801;&#x653E;&#x5165;&#x8BC6;&#x522B;&#x6846;&#xFF0C;&#x7CFB;&#x7EDF;&#x4F1A;&#x5224;&#x65AD;&#x662F;&#x5426;&#x5C5E;&#x4E8E;&#x5F53;&#x524D;&#x914D;&#x9001;&#x6279;&#x6B21;&#x3002;</div>
          </div>
<div class="kv"><span>药品 ID</span><strong id="drug_id">-</strong></div>
          <div class="kv"><span>药品名称</span><strong id="drug_name">-</strong></div>
          <div class="kv"><span>药品类型</span><strong id="drug_type">-</strong></div>
          <div class="kv"><span>置信度</span><strong id="drug_confidence">-</strong></div>
          <div class="kv"><span>装药状态</span><strong id="drug_loaded">-</strong></div>
          <div class="kv"><span>识别来源</span><strong id="drug_source">-</strong></div>
          <div class="kv"><span>识别通道</span><strong id="recognition_channel">-</strong></div>
          <div class="kv"><span>复核状态</span><strong id="recognition_review_state">-</strong></div>
          <div class="kv"><span>原始码</span><strong id="code_text">-</strong></div>
          <div class="kv"><span>药品追溯码</span><strong id="trace_code">-</strong></div>
          <div class="kv"><span>追溯来源</span><strong id="trace_source">-</strong></div>
          <div class="kv"><span>码类型</span><strong id="code_type">-</strong></div>
          <div class="kv"><span>识别方法</span><strong id="code_method">-</strong></div>
        </div>
        <div class="vision-panel">
          <h3>标签字段解析</h3>
          <div class="kv"><span>OCR 文本</span><strong id="ocr_text">-</strong></div>
          <div class="kv"><span>OCR 匹配文本</span><strong id="ocr_match_text">-</strong></div>
          <div class="kv"><span>OCR 抽取药名</span><strong id="ocr_drug_name">-</strong></div>
          <div class="kv"><span>&#x004F;&#x0043;&#x0052; &#x836F;&#x540D;&#x5019;&#x9009;</span><strong id="ocr_drug_candidates">-</strong></div>
          <div class="kv"><span>&#x6279;&#x6B21;&#x9884;&#x5339;&#x914D;</span><strong id="ocr_batch_match">-</strong></div>
          <div class="kv"><span>OCR 规格</span><strong id="ocr_spec">-</strong></div>
          <div class="kv"><span>OCR 厂家</span><strong id="ocr_manufacturer">-</strong></div>
          <div class="kv"><span>OCR 批准文号</span><strong id="ocr_approval_no">-</strong></div>
          <div class="kv"><span>OCR 置信度</span><strong id="ocr_confidence">-</strong></div>
          <div class="kv"><span>OCR 后端</span><strong id="ocr_backend">-</strong></div>
          <div class="kv"><span>OCR 耗时</span><strong id="ocr_worker_busy_ms">-</strong></div>
          <div class="kv"><span>OCR 识别框</span><strong id="ocr_roi_rect">-</strong></div>
          <div class="kv"><span>OCR 状态</span><strong id="ocr_status">-</strong></div>
          <div class="kv"><span>OCR &#x7A33;&#x5B9A;&#x7F13;&#x5B58;</span><strong id="ocr_hold_status">-</strong></div>
          <div class="kv"><span>&#x8BA2;&#x5355;&#x53F7;</span><strong id="label_order_no">-</strong></div>
          <div class="kv"><span>&#x4EA7;&#x54C1;&#x7F16;&#x7801;</span><strong id="label_product_code">-</strong></div>
          <div class="kv"><span>&#x4EA7;&#x54C1;&#x578B;&#x53F7;</span><strong id="label_product_model">-</strong></div>
          <div class="kv"><span>&#x6570;&#x91CF;</span><strong id="label_quantity">-</strong></div>
          <div class="kv"><span>&#x8FFD;&#x6EAF;&#x7F16;&#x53F7;</span><strong id="label_trace_id">-</strong></div>
          <div class="kv"><span>&#x66F4;&#x65B0;&#x65F6;&#x95F4;</span><strong id="drug_stamp">-</strong></div>
        </div>
      </div>
      <div class="notice">当前数据来自 ROS2 话题 <b>/medicine/drug_info</b> 和 <b>/medicine/drug_recognition_status</b>，支持扫码器、条形码/工业码识别、OCR 标签字段解析和药师复核。</div>
    </section>
    <section class="card" data-page="messages">
      <div class="status-head">
        <h2>病人咨询</h2>
        <div class="messages-head-actions">
          <span id="messages_count_hint" class="muted">共 0 个会话 / 未处理 0</span>
          <input id="nurse_name_input" class="nurse-name-input" type="text" placeholder="您的称呼 (会显示给病人)" maxlength="20" />
          <button id="messages_refresh" class="secondary" type="button">刷新</button>
          <button id="messages_mark_all" class="secondary" type="button">全部已读</button>
        </div>
      </div>
      <div class="notice">病人通过 /patient/api/messages 发起咨询会在这里出现。左侧是床位会话列表, 点击选中即可在右侧查看完整对话并回复, 病人端会同步看到。</div>
      <div class="im-layout">
        <aside class="im-sidebar" aria-label="床位会话列表">
          <div class="im-sidebar-head">
            <strong>会话</strong>
            <span id="messages_sidebar_hint" class="muted">0</span>
          </div>
          <div id="messages_sidebar_list" class="im-sidebar-list">
            <div class="im-sidebar-empty">暂无病人咨询</div>
          </div>
        </aside>
        <section class="im-main" id="messages_main_panel">
          <div class="im-main-empty" id="messages_main_empty">
            从左侧选一个床位开始对话
          </div>
        </section>
      </div>
    </section>
  </main>
  <div id="dashboard_toast_host" class="dashboard-toast-host" aria-live="polite" aria-atomic="true"></div>
  <script>
    const result = document.getElementById('result');
    const cameraPreview = document.getElementById('camera-preview');
    const cameraPreviewVideo = document.getElementById('camera-preview-video');
    const ocrRoiOverlay = document.getElementById('ocr-roi-overlay');
    const barcodeRoiOverlay = document.getElementById('barcode-roi-overlay');
    const cameraModeHdButton = document.getElementById('camera-mode-hd');
    const cameraModeSmoothButton = document.getElementById('camera-mode-smooth');
    const medicineNameInput = document.getElementById('medicine_name');
    let latestTaskId = '';
    let latestDrugInfo = {};
    let visionQrEnabled = false;
    let ocrRoiVisibleUntil = 0;
    let lastAutoFilledMedicineName = '';
    let patientOrders = [];
    // 闭环 B: 各床位 confirm/reject 状态 dict, key=bed_no, value={status,eta,reason}
    let latestPatientStatusOverrides = {};
    let selectedPatientOrder = null;
    let latestPatientMedicationMatch = null;
    let latestDeliveryBatch = {};
    let latestBatchScanPreviewModel = null;
    let autoLoadEnabled = localStorage.getItem('medicine_auto_load_enabled') === '1';
    let autoLoadBusy = false;
    let autoLoadChecking = false;
    let autoLoadLastCheckAt = 0;
    let autoLoadCandidate = { signature: '', count: 0, lastSeenAt: 0 };
    let autoLoadLastCommit = { signature: '', at: 0 };
    const AUTO_LOAD_STABLE_REQUIRED = 1;
    const AUTO_LOAD_COOLDOWN_MS = 3000;
    let recognitionStability = { signature: '', count: 0, lastSeenAt: 0 };
    let editingBatchPatientKey = '';
    let editingBatchMedicationKey = '';
    let latestPendingBatch = null;
    let latestBatchImportPreview = { ok: false, payload: null };
    let batchImportPreviewTimer = null;
    let latestReportRows = [];
    let latestReportFilteredRows = [];
    let latestReportGeneratedAt = '';
    let latestChassisStatus = {};
    let latestSystemLoad = {};
    let latestHealthCheck = null;
    let latestBackendSafetyGate = null;
    let lastHealthToastSignature = null;
    let lastHealthToastAt = 0;
    let latestAuditFilter = 'all';
    let cameraPreviewStreaming = false;
    let cameraPreviewReconnectTimer = null;
    let cameraPreviewRefreshTimer = null;
    let cameraPreviewPeer = null;
    let cameraPreviewPreferredMode = localStorage.getItem('cameraPreviewPreferredMode') || 'hd';
    let cameraPreviewMode = 'idle';
    let cameraDisplayFrameCount = 0;
    let cameraDisplayLastSample = performance.now();
    let cameraDisplayFps = 0;
    const SCAN_MAX_AGE_SEC = 8;

    function isCameraPreviewVisible() {
      return document.visibilityState !== 'hidden' && Boolean(document.querySelector('[data-page="vision"].active'));
    }

    function setCameraPreviewState(online, text, mode = '') {
      const empty = document.getElementById('camera-empty');
      const badge = document.getElementById('vision-status-badge');
      if (empty) empty.hidden = Boolean(online);
      if (badge) {
        badge.textContent = text;
        badge.className = online ? 'badge COMPLETED' : 'badge CANCELED';
      }
      if (mode) {
        cameraPreviewMode = mode;
      }
    }

    function updateCameraPreviewModeButtons() {
      if (cameraModeHdButton) {
        cameraModeHdButton.classList.toggle('active', cameraPreviewPreferredMode === 'hd');
      }
      if (cameraModeSmoothButton) {
        cameraModeSmoothButton.classList.toggle('active', cameraPreviewPreferredMode === 'smooth');
      }
    }

    function setCameraPreviewPreferredMode(mode) {
      cameraPreviewPreferredMode = mode === 'hd' ? 'hd' : 'smooth';
      localStorage.setItem('cameraPreviewPreferredMode', cameraPreviewPreferredMode);
      updateCameraPreviewModeButtons();
      if (isCameraPreviewVisible()) {
        stopCameraPreview();
        startCameraPreview();
      }
    }

    function getActiveCameraMediaElement() {
      if (cameraPreviewVideo && !cameraPreviewVideo.hidden && cameraPreviewVideo.videoWidth > 0 && cameraPreviewVideo.videoHeight > 0) {
        return {
          element: cameraPreviewVideo,
          mediaWidth: cameraPreviewVideo.videoWidth,
          mediaHeight: cameraPreviewVideo.videoHeight,
        };
      }
      if (cameraPreview && !cameraPreview.hidden && cameraPreview.naturalWidth > 0 && cameraPreview.naturalHeight > 0) {
        return {
          element: cameraPreview,
          mediaWidth: cameraPreview.naturalWidth,
          mediaHeight: cameraPreview.naturalHeight,
        };
      }
      const frameSize = Array.isArray(latestDrugInfo?.ocr_roi_frame_size) && latestDrugInfo.ocr_roi_frame_size.length >= 2
        ? latestDrugInfo.ocr_roi_frame_size
        : (Array.isArray(latestDrugInfo?.barcode_roi_frame_size) ? latestDrugInfo.barcode_roi_frame_size : []);
      const fallbackWidth = Number(frameSize[0] || 0);
      const fallbackHeight = Number(frameSize[1] || 0);
      if (fallbackWidth > 0 && fallbackHeight > 0) {
        return {
          element: cameraPreviewVideo && !cameraPreviewVideo.hidden ? cameraPreviewVideo : cameraPreview,
          mediaWidth: fallbackWidth,
          mediaHeight: fallbackHeight,
        };
      }
      return null;
    }

    function updateRoiOverlay(overlay, enabled, roi, frameSize) {
      if (!overlay) {
        return;
      }
      const rect = Array.isArray(roi) ? roi.map(value => Number(value)) : [];
      const sourceFrameSize = Array.isArray(frameSize) ? frameSize.map(value => Number(value)) : [];
      const media = getActiveCameraMediaElement();
      if (!enabled || rect.length < 4 || sourceFrameSize.length < 2 || !media) {
        overlay.classList.remove('active');
        return;
      }
      const [x, y, width, height] = rect;
      const [frameWidth, frameHeight] = sourceFrameSize;
      if (![x, y, width, height, frameWidth, frameHeight].every(Number.isFinite) || frameWidth <= 0 || frameHeight <= 0 || width <= 0 || height <= 0) {
        overlay.classList.remove('active');
        return;
      }
      const wrapRect = media.element.parentElement.getBoundingClientRect();
      const elementRect = media.element.getBoundingClientRect();
      const mediaAspect = media.mediaWidth / media.mediaHeight;
      const boxAspect = elementRect.width / elementRect.height;
      let renderedWidth = elementRect.width;
      let renderedHeight = elementRect.height;
      let offsetX = elementRect.left - wrapRect.left;
      let offsetY = elementRect.top - wrapRect.top;
      const objectFit = window.getComputedStyle(media.element).objectFit || 'contain';
      if (objectFit === 'cover') {
        if (boxAspect > mediaAspect) {
          renderedHeight = elementRect.width / mediaAspect;
          offsetY += (elementRect.height - renderedHeight) / 2;
        } else {
          renderedWidth = elementRect.height * mediaAspect;
          offsetX += (elementRect.width - renderedWidth) / 2;
        }
      } else if (boxAspect > mediaAspect) {
        renderedWidth = elementRect.height * mediaAspect;
        offsetX += (elementRect.width - renderedWidth) / 2;
      } else {
        renderedHeight = elementRect.width / mediaAspect;
        offsetY += (elementRect.height - renderedHeight) / 2;
      }
      const scaleX = renderedWidth / frameWidth;
      const scaleY = renderedHeight / frameHeight;
      overlay.style.left = `${offsetX + x * scaleX}px`;
      overlay.style.top = `${offsetY + y * scaleY}px`;
      overlay.style.width = `${width * scaleX}px`;
      overlay.style.height = `${height * scaleY}px`;
      overlay.classList.add('active');
    }

    function isOcrRoiVisible(data = latestDrugInfo) {
      if (!data?.ocr_roi_enabled) {
        return false;
      }
      if (data.ocr_runtime_enabled || data.ocr_single_shot_pending) {
        return true;
      }
      if (Date.now() < ocrRoiVisibleUntil) {
        return true;
      }
      const age = Number(data.ocr_age_sec || 999);
      return Number.isFinite(age) && age < 8;
    }

    function updateVisionRoiOverlays(data = latestDrugInfo) {
      updateRoiOverlay(
        barcodeRoiOverlay,
        Boolean(data?.qr_enabled && data?.barcode_roi_enabled),
        data?.barcode_roi_rect,
        data?.barcode_roi_frame_size
      );
      updateRoiOverlay(
        ocrRoiOverlay,
        isOcrRoiVisible(data),
        data?.ocr_roi_rect,
        data?.ocr_roi_frame_size
      );
    }

    function updateOcrRoiOverlay(data = latestDrugInfo) {
      updateVisionRoiOverlays(data);
    }

    async function startCameraPreview() {
      if (!isCameraPreviewVisible() || cameraPreviewStreaming) {
        return;
      }
      cameraPreviewStreaming = true;
      cameraDisplayFrameCount = 0;
      cameraDisplayLastSample = performance.now();
      cameraDisplayFps = 0;
      if (cameraPreviewPreferredMode === 'hd') {
        startCameraPreviewMjpeg('hd');
        return;
      }
      try {
        await startCameraPreviewWebRTC();
      } catch (error) {
        console.warn('WebRTC preview failed, fallback to MJPEG stream:', error);
        startCameraPreviewMjpeg('mjpeg');
      }
    }

    function stopCameraPreview() {
      if (cameraPreviewReconnectTimer) {
        clearTimeout(cameraPreviewReconnectTimer);
        cameraPreviewReconnectTimer = null;
      }
      if (cameraPreviewRefreshTimer) {
        clearTimeout(cameraPreviewRefreshTimer);
        cameraPreviewRefreshTimer = null;
      }
      cameraPreviewStreaming = false;
      if (cameraPreviewPeer) {
        cameraPreviewPeer.close();
        cameraPreviewPeer = null;
      }
      if (cameraPreviewVideo) {
        cameraPreviewVideo.pause();
        cameraPreviewVideo.removeAttribute('src');
        cameraPreviewVideo.srcObject = null;
        cameraPreviewVideo.hidden = true;
      }
      cameraPreview.removeAttribute('src');
      cameraPreview.hidden = true;
      if (ocrRoiOverlay) {
        ocrRoiOverlay.classList.remove('active');
      }
      if (barcodeRoiOverlay) {
        barcodeRoiOverlay.classList.remove('active');
      }
      document.getElementById('vision_display_fps').textContent = '-';
      cameraPreviewMode = 'idle';
    }

    async function startCameraPreviewWebRTC() {
      if (!window.RTCPeerConnection) {
        throw new Error('browser does not support RTCPeerConnection');
      }
      const statusResponse = await fetch('/api/vision/webrtc/status', { cache: 'no-store' });
      const status = await statusResponse.json();
      if (!status.available) {
        throw new Error(status.last_error || 'WebRTC service unavailable');
      }
      const pc = new RTCPeerConnection({ iceServers: [] });
      cameraPreviewPeer = pc;
      pc.addTransceiver('video', { direction: 'recvonly' });
      pc.ontrack = event => {
        cameraPreviewVideo.srcObject = event.streams[0];
        cameraPreviewVideo.hidden = false;
        cameraPreview.hidden = true;
        forceFillCameraPreviewElement(cameraPreviewVideo);
        setCameraPreviewState(true, 'WebRTC画面在线', 'webrtc');
        cameraPreviewVideo.play().catch(() => {});
        updateOcrRoiOverlay();
        watchCameraVideoFrames();
      };
      pc.onconnectionstatechange = () => {
        if (!cameraPreviewStreaming) return;
        if (['failed', 'closed', 'disconnected'].includes(pc.connectionState)) {
          setCameraPreviewState(false, '摄像头离线', 'webrtc');
          scheduleCameraPreviewReconnect();
        }
      };
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      const answerResponse = await fetch('/api/vision/webrtc/offer', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'medicine-dashboard',
        },
        body: JSON.stringify(pc.localDescription),
      });
      if (!answerResponse.ok) {
        const text = await answerResponse.text();
        throw new Error(text || `offer failed: ${answerResponse.status}`);
      }
      const answer = await answerResponse.json();
      await pc.setRemoteDescription(answer);
    }

    function forceFillCameraPreviewElement(element) {
      if (!element) return;
      element.style.position = 'absolute';
      element.style.inset = '0';
      element.style.width = '100%';
      element.style.height = '100%';
      element.style.minWidth = '100%';
      element.style.minHeight = '100%';
      element.style.objectFit = 'cover';
      element.style.objectPosition = 'center center';
      element.style.display = 'block';
    }

    function startCameraPreviewMjpeg(mode = 'hd') {
      cameraPreviewVideo.hidden = true;
      cameraPreviewVideo.srcObject = null;
      cameraPreview.hidden = false;
      forceFillCameraPreviewElement(cameraPreview);
      if (mode === 'hd') {
        const directUrl = `${window.location.protocol}//${window.location.hostname}:8090/stream.mjpg?ts=${Date.now()}`;
        cameraPreview.src = directUrl;
        setCameraPreviewState(true, '高清直连在线', 'hd');
        document.getElementById('vision_display_fps').textContent = 'MJPEG 直连';
      } else {
        cameraPreview.src = `/api/vision/stream.mjpg?ts=${Date.now()}`;
        setCameraPreviewState(true, 'MJPEG画面在线', 'mjpeg');
        document.getElementById('vision_display_fps').textContent = 'MJPEG';
      }
      updateOcrRoiOverlay();
    }

    function scheduleCameraPreviewReconnect() {
      if (!isCameraPreviewVisible()) {
        return;
      }
      if (cameraPreviewReconnectTimer) {
        clearTimeout(cameraPreviewReconnectTimer);
      }
      cameraPreviewReconnectTimer = setTimeout(() => {
        cameraPreviewReconnectTimer = null;
        stopCameraPreview();
        startCameraPreview();
      }, 2000);
    }

    function watchCameraVideoFrames() {
      if (!cameraPreviewVideo || cameraPreviewVideo.hidden || !cameraPreviewStreaming) {
        return;
      }
      const onFrame = () => {
        if (!cameraPreviewStreaming || cameraPreviewVideo.hidden) {
          return;
        }
        cameraDisplayFrameCount += 1;
        const now = performance.now();
        const elapsed = now - cameraDisplayLastSample;
        if (elapsed >= 1000) {
          cameraDisplayFps = cameraDisplayFrameCount * 1000 / elapsed;
          cameraDisplayFrameCount = 0;
          cameraDisplayLastSample = now;
          document.getElementById('vision_display_fps').textContent = `${cameraDisplayFps.toFixed(1)} FPS (${cameraPreviewMode})`;
        }
        if (cameraPreviewVideo.requestVideoFrameCallback) {
          cameraPreviewVideo.requestVideoFrameCallback(onFrame);
        } else {
          requestAnimationFrame(onFrame);
        }
      };
      if (cameraPreviewVideo.requestVideoFrameCallback) {
        cameraPreviewVideo.requestVideoFrameCallback(onFrame);
      } else {
        requestAnimationFrame(onFrame);
      }
    }

    function syncCameraPreview() {
      if (isCameraPreviewVisible()) {
        startCameraPreview();
      } else {
        stopCameraPreview();
      }
    }

    cameraPreview.addEventListener('error', () => {
      setCameraPreviewState(false, '摄像头离线', cameraPreviewMode || 'mjpeg');
      scheduleCameraPreviewReconnect();
    });
    cameraPreview.addEventListener('load', () => {
      setCameraPreviewState(true, cameraPreviewMode === 'hd' ? '高清直连在线' : 'MJPEG画面在线', cameraPreviewMode === 'hd' ? 'hd' : 'mjpeg');
      updateOcrRoiOverlay();
    });
    cameraPreviewVideo.addEventListener('loadedmetadata', () => updateOcrRoiOverlay());
    window.addEventListener('resize', () => updateOcrRoiOverlay());
    cameraModeHdButton?.addEventListener('click', () => setCameraPreviewPreferredMode('hd'));
    cameraModeSmoothButton?.addEventListener('click', () => setCameraPreviewPreferredMode('smooth'));
    updateCameraPreviewModeButtons();
    document.addEventListener('visibilitychange', syncCameraPreview);

    function log(text) {
      const now = new Date().toLocaleTimeString();
      result.textContent = `[${now}] ${text}\n` + result.textContent;
    }

    function setRuntimeCell(id, label, value, tone = 'cold') {
      const el = document.getElementById(id);
      if (!el) return;
      el.className = `runtime-cell ${tone}`;
      el.innerHTML = `<span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong>`;
    }

    function updateRuntimeStatus() {
      const state = latestDeliveryBatch?.route_status || latestDeliveryBatch?.status || latestTaskId ? '运行中' : '待命';
      setRuntimeCell('rt_robot', '机器人', `R1 ${state}`, latestTaskId || latestDeliveryBatch?.batch_id ? 'ok' : 'cold');
      const battery = latestChassisStatus?.battery ?? latestChassisStatus?.battery_percent;
      setRuntimeCell('rt_battery', '电量', Number.isFinite(Number(battery)) ? `${Math.round(Number(battery))}%` : '待上报', Number.isFinite(Number(battery)) ? 'ok' : 'cold');
      const cabinetLocked = latestChassisStatus?.cabinet_locked ?? latestChassisStatus?.medicine_cabinet_locked;
      setRuntimeCell('rt_cabinet', '药舱', cabinetLocked === undefined ? '锁定状态待确认' : (cabinetLocked ? '已锁定' : '未锁定'), cabinetLocked === false ? 'warn' : (cabinetLocked === true ? 'ok' : 'cold'));
      const emergencyStop = latestChassisStatus?.emergency_stop;
      setRuntimeCell('rt_estop', '急停', emergencyStop === undefined ? '待上报' : (emergencyStop ? '急停已开启' : '急停正常'), emergencyStop ? 'warn' : (emergencyStop === false ? 'ok' : 'cold'));
      const received = Boolean(latestChassisStatus?.received);
      const age = latestChassisStatus?.web_received_at ? Math.max(0, Date.now() / 1000 - Number(latestChassisStatus.web_received_at)) : null;
      setRuntimeCell('rt_ros', 'ROS2', received ? `已连接 ${age == null ? '' : `${age.toFixed(1)}s`}` : '等待状态', received ? 'ok' : 'cold');
      const hasRecognition = Boolean(latestDrugInfo?.drug_name || latestDrugInfo?.code_text || latestDrugInfo?.raw_code_text || latestDrugInfo?.label_product_code);
      setRuntimeCell('rt_vision', '识别设备', hasRecognition ? '最近有识别结果' : '待检测', hasRecognition ? 'ok' : 'cold');
      if (latestDeliveryBatch && latestDeliveryBatch.batch_id) {
        updateBatchSafetyGate(latestDeliveryBatch);
      }
      refreshHealthCheck();
    }


    function setHealthCheckField(id, label, value, tone = 'cold') {
      const el = document.getElementById(id);
      if (!el) return;
      el.className = `recognized-item health-check-item ${tone}`;
      el.innerHTML = `<span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong>`;
    }

    function healthTone(status) {
      if (status === 'ok') return 'ok';
      if (status === 'bad') return 'bad';
      if (status === 'warn') return 'warn';
      return 'cold';
    }

    function getHealthCheckByKey(key) {
      const checks = latestHealthCheck && latestHealthCheck.checks;
      return checks && checks[key] ? checks[key] : null;
    }

    function uniqueHealthActions(actions) {
      const seen = new Set();
      const result = [];
      (actions || []).forEach(action => {
        if (!action || !action.label || !action.action) return;
        const key = `${action.action}:${action.tab || ''}:${action.target || ''}:${action.label}`;
        if (seen.has(key)) return;
        seen.add(key);
        result.push(action);
      });
      return result.slice(0, 8);
    }

    function showDashboardToast(title, body = '', tone = 'ok') {
      const host = document.getElementById('dashboard_toast_host');
      if (!host) return;
      const toast = document.createElement('div');
      const safeTone = tone === 'danger' ? 'danger' : (tone === 'warn' ? 'warn' : 'ok');
      toast.className = `dashboard-toast ${safeTone}`;
      toast.innerHTML = `<strong>${escapeHtml(title || '\u63d0\u793a')}</strong>${body ? `<span>${escapeHtml(body)}</span>` : ''}`;
      host.appendChild(toast);
      window.setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(4px)';
        window.setTimeout(() => toast.remove(), 220);
      }, 4200);
    }

    function buildHealthCheckReportText(data) {
      const source = data || latestHealthCheck || {};
      const summary = source.summary || {};
      const checks = source.checks || {};
      const decision = deriveHealthGate(source);
      const lines = [
        '\u836f\u54c1\u914d\u9001\u673a\u5668\u4eba\u7cfb\u7edf\u81ea\u68c0\u6458\u8981',
        `\u65f6\u95f4\uff1a${formatHealthCheckTime(source.updated_at)}`,
        `\u7ed3\u8bba\uff1a${decision.title}\uff0c${decision.message}`,
        `\u72b6\u6001\uff1a${healthStatusLabel(source.status)}\uff08\u6b63\u5e38 ${Number(summary.ok || 0)} / \u9700\u786e\u8ba4 ${Number(summary.warn || 0)} / \u5f02\u5e38 ${Number(summary.bad || 0)}\uff09`,
        '',
        '\u68c0\u67e5\u9879\uff1a',
      ];
      Object.values(checks).forEach(item => {
        if (!item) return;
        lines.push(`- ${item.label || '\u9879\u76ee'}\uff1a${healthStatusLabel(item.status)}\uff0c${item.message || '-'}`);
        if (item.detail) lines.push(`  \u8be6\u60c5\uff1a${item.detail}`);
      });
      const actions = uniqueHealthActions(Object.values(checks).flatMap(item => item?.actions || []).concat(source.actions || []));
      if (actions.length) {
        lines.push('', '\u5efa\u8bae\u5904\u7406\uff1a');
        actions.forEach(action => lines.push(`- ${action.label || action.action}`));
      }
      return lines.join('\n');
    }

    async function copyTextToClipboard(text) {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        return true;
      }
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.setAttribute('readonly', 'readonly');
      textarea.style.position = 'fixed';
      textarea.style.left = '-9999px';
      document.body.appendChild(textarea);
      textarea.select();
      const ok = document.execCommand('copy');
      textarea.remove();
      if (!ok) throw new Error('copy failed');
      return true;
    }

    async function copyHealthCheckReport() {
      await copyTextToClipboard(buildHealthCheckReportText(latestHealthCheck));
      showDashboardToast('\u5df2\u590d\u5236\u81ea\u68c0\u6458\u8981', '\u53ef\u76f4\u63a5\u7c98\u8d34\u7ed9\u7ef4\u62a4\u4eba\u5458\u6216\u7528\u4e8e\u73b0\u573a\u8bb0\u5f55\u3002', 'ok');
    }

    function exportHealthCheckJson() {
      const payload = JSON.stringify(latestHealthCheck || {}, null, 2);
      const blob = new Blob([payload], { type: 'application/json;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      const stamp = new Date().toISOString().replace(/[:.]/g, '-');
      a.href = url;
      a.download = `medicine-health-check-${stamp}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      showDashboardToast('\u5df2\u5bfc\u51fa\u81ea\u68c0 JSON', '\u6587\u4ef6\u5305\u542b\u5f53\u524d\u5404\u6a21\u5757\u72b6\u6001\u548c\u5efa\u8bae\u52a8\u4f5c\u3002', 'ok');
    }

    function runHealthCheckAction(action) {
      if (!action || !action.action) return;
      if (action.action === 'copy_health_report') {
        copyHealthCheckReport().catch(error => showDashboardToast('\u590d\u5236\u81ea\u68c0\u6458\u8981\u5931\u8d25', error.message || '\u6d4f\u89c8\u5668\u4e0d\u5141\u8bb8\u590d\u5236', 'warn'));
        return;
      }
      if (action.action === 'export_health_json') {
        exportHealthCheckJson();
        return;
      }
      if (action.action === 'refresh_health') {
        refreshHealthCheckApi();
        showDashboardToast('\u6b63\u5728\u5237\u65b0\u81ea\u68c0', '\u5df2\u91cd\u65b0\u8bf7\u6c42\u540e\u7aef\u5065\u5eb7\u68c0\u67e5\u3002', 'ok');
        return;
      }
      if (action.action === 'open_patient') {
        const host = location.hostname || '192.168.31.125';
        window.open(`${location.protocol}//${host}:8081/patient/`, '_blank');
        return;
      }
      if (action.action === 'switch_tab') {
        switchDashboardTab(action.tab || 'monitor');
        return;
      }
      if (action.action === 'focus') {
        if (action.tab) switchDashboardTab(action.tab);
        window.setTimeout(() => {
          const target = document.getElementById(action.target || '');
          if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'center' });
            if (typeof target.focus === 'function') target.focus({ preventScroll: true });
            target.classList.add('recommended-action');
            window.setTimeout(() => target.classList.remove('recommended-action'), 2200);
          }
        }, 80);
        return;
      }
      showDashboardToast('\u6682\u4e0d\u652f\u6301\u7684\u5904\u7406\u52a8\u4f5c', action.label || action.action, 'warn');
    }

    function renderHealthCheckActions(data) {
      const container = document.getElementById('health_check_actions');
      if (!container) return;
      const checks = data?.checks || {};
      const problemActions = Object.values(checks)
        .filter(item => item && item.status !== 'ok')
        .flatMap(item => item.actions || []);
      const fallbackActions = data?.actions || [];
      const reportActions = [
        { label: '\u590d\u5236\u81ea\u68c0\u6458\u8981', action: 'copy_health_report' },
        { label: '\u5bfc\u51fa\u81ea\u68c0 JSON', action: 'export_health_json' },
      ];
      const actions = uniqueHealthActions(reportActions.concat(problemActions.length ? problemActions : fallbackActions));
      container.innerHTML = actions.map((action, index) => `<button type="button" class="secondary" data-health-action="${index}">${escapeHtml(action.label || '\u5904\u7406')}</button>`).join('');
      actions.forEach((action, index) => {
        const button = container.querySelector(`[data-health-action="${index}"]`);
        if (button) button.addEventListener('click', () => runHealthCheckAction(action));
      });
    }

    function formatHealthCheckTime(epochSeconds) {
      const ts = Number(epochSeconds || 0);
      if (!Number.isFinite(ts) || ts <= 0) return '-';
      try {
        return new Date(ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      } catch (_) {
        return '-';
      }
    }

    function healthStatusLabel(status) {
      if (status === 'ok') return '\u6b63\u5e38';
      if (status === 'warn') return '\u9700\u786e\u8ba4';
      if (status === 'bad') return '\u5f02\u5e38';
      return '\u672a\u77e5';
    }

    function deriveHealthGate(data) {
      const summary = data?.summary || {};
      const bad = Number(summary.bad || 0);
      const warn = Number(summary.warn || 0);
      if (!data || !data.checks) {
        return { tone: 'cold', title: '正在判断', message: '正在读取工作台、病人端、底盘、语音、识别和批次状态。' };
      }
      if (bad > 0) {
        return { tone: 'bad', title: '禁止配送', message: `存在 ${bad} 项异常，先处理红色项目；处理前不要推进配送任务。` };
      }
      if (warn > 0) {
        return { tone: 'warn', title: '需人工确认', message: `存在 ${warn} 项需确认，请核对提示项后再继续装药、复核或配送。` };
      }
      return { tone: 'ok', title: '可继续配送', message: '核心模块在线，仍需按流程完成装药、复核和床旁确认。' };
    }

    function renderHealthGate(data) {
      const gate = document.getElementById('health_gate');
      const title = document.getElementById('health_gate_title');
      const message = document.getElementById('health_gate_message');
      if (!gate || !title || !message) return;
      const decision = deriveHealthGate(data);
      gate.className = `health-gate ${decision.tone || 'cold'}`;
      title.textContent = decision.title || '-';
      message.textContent = decision.message || '-';
    }

    function renderHealthCheckMeta(data) {
      const meta = document.getElementById('health_check_meta');
      if (!meta) return;
      const summary = data?.summary || {};
      meta.textContent = `\u6700\u540e\u68c0\u67e5 ${formatHealthCheckTime(data?.updated_at)} \u00b7 \u6b63\u5e38 ${Number(summary.ok || 0)} \u00b7 \u9700\u786e\u8ba4 ${Number(summary.warn || 0)} \u00b7 \u5f02\u5e38 ${Number(summary.bad || 0)}`;
    }

    function updateHealthTabBadge(data) {
      const badgeEl = document.getElementById('health-tab-badge');
      const hintEl = document.getElementById('health-tab-hint');
      const tabEl = document.querySelector('.tab-button[data-tab="monitor"]');
      if (!badgeEl || !tabEl) return;
      const summary = data?.summary || {};
      const bad = Number(summary.bad || 0);
      const warn = Number(summary.warn || 0);
      const count = bad + warn;
      badgeEl.textContent = count > 99 ? '99+' : String(count);
      badgeEl.hidden = count <= 0;
      badgeEl.style.display = count > 0 ? '' : 'none';
      badgeEl.classList.toggle('bad', bad > 0);
      tabEl.classList.toggle('has-health-alert', count > 0);
      tabEl.classList.toggle('bad', bad > 0);
      if (hintEl) {
        if (bad > 0) {
          hintEl.textContent = `\u5f02\u5e38 ${bad} \u00b7 \u9700\u5904\u7406`;
        } else if (warn > 0) {
          hintEl.textContent = `\u9700\u786e\u8ba4 ${warn} \u00b7 \u70b9\u51fb\u67e5\u770b`;
        } else {
          hintEl.textContent = '\u5e95\u76d8 / \u8d1f\u8f7d / \u5b89\u5168';
        }
      }
    }

    function healthSeverityRank(status) {
      if (status === 'bad') return 3;
      if (status === 'warn') return 2;
      if (status === 'ok') return 1;
      return 0;
    }

    function buildHealthToastSignature(data) {
      const summary = data?.summary || {};
      const status = data?.status || 'unknown';
      return `${status}:${Number(summary.bad || 0)}:${Number(summary.warn || 0)}`;
    }

    function maybeNotifyHealthChange(data) {
      if (!data || !data.summary) return;
      const signature = buildHealthToastSignature(data);
      if (!lastHealthToastSignature) {
        lastHealthToastSignature = signature;
        return;
      }
      if (signature === lastHealthToastSignature) return;
      const now = Date.now();
      if (now - lastHealthToastAt < 2500) {
        lastHealthToastSignature = signature;
        return;
      }
      const summary = data.summary || {};
      const bad = Number(summary.bad || 0);
      const warn = Number(summary.warn || 0);
      const previousStatus = String(lastHealthToastSignature).split(':')[0] || 'unknown';
      const currentStatus = data.status || (bad > 0 ? 'bad' : (warn > 0 ? 'warn' : 'ok'));
      lastHealthToastSignature = signature;
      lastHealthToastAt = now;
      if (currentStatus === 'ok') {
        showDashboardToast('\u7cfb\u7edf\u81ea\u68c0\u5df2\u6062\u590d', '\u6240\u6709\u5065\u5eb7\u68c0\u67e5\u9879\u5df2\u56de\u5230\u6b63\u5e38\u72b6\u6001\u3002', 'ok');
        return;
      }
      const worse = healthSeverityRank(currentStatus) > healthSeverityRank(previousStatus);
      const title = currentStatus === 'bad' ? '\u7cfb\u7edf\u81ea\u68c0\u51fa\u73b0\u5f02\u5e38' : '\u7cfb\u7edf\u81ea\u68c0\u9700\u786e\u8ba4';
      const body = `\u5f02\u5e38 ${bad} \u9879\uff0c\u9700\u786e\u8ba4 ${warn} \u9879\u3002\u8bf7\u6253\u5f00\u7cfb\u7edf\u76d1\u63a7\u67e5\u770b\u660e\u7ec6\u3002`;
      showDashboardToast(title, body, currentStatus === 'bad' ? 'danger' : (worse ? 'warn' : 'ok'));
    }

    function renderHealthCheckDetails(data) {
      const list = document.getElementById('health_check_detail_list');
      if (!list) return;
      const checks = data?.checks || {};
      const order = ['dashboard', 'patient_web', 'voice', 'vision', 'chassis', 'delivery_batch', 'system_load'];
      const rows = order
        .filter(key => checks[key])
        .map(key => {
          const item = checks[key] || {};
          const actions = (item.actions || []).map(action => action.label).filter(Boolean).slice(0, 2).join('\uff0c') || '-';
          const tone = healthTone(item.status);
          return `<div class="health-detail-row ${tone}"><strong>${escapeHtml(item.label || key)}</strong><span>${escapeHtml(item.message || '-')}</span><span class="health-detail-state">${escapeHtml(healthStatusLabel(item.status))} ? ${escapeHtml(actions)}</span></div>`;
        });
      list.innerHTML = rows.length ? rows.join('') : `<div class="health-detail-row"><strong>\u6682\u65e0\u660e\u7ec6</strong><span>-</span><span>-</span></div>`;
    }

    function renderHealthCheckEvents(data) {
      const container = document.getElementById('health_check_events');
      if (!container) return;
      const events = Array.isArray(data?.events) ? data.events.slice(0, 4) : [];
      if (!events.length) {
        container.innerHTML = `<div class="health-event-row ok"><strong>\u6682\u65e0\u53d8\u5316</strong><span>\u5f53\u524d\u8fd0\u884c\u72b6\u6001\u7a33\u5b9a\u3002</span><span>-</span></div>`;
        return;
      }
      container.innerHTML = events.map(event => {
        const tone = healthTone(event.status);
        const summary = event.summary || {};
        const timeText = formatHealthCheckTime(event.time);
        const countText = `\u5f02\u5e38 ${Number(summary.bad || 0)} \u00b7 \u9700\u786e\u8ba4 ${Number(summary.warn || 0)}`;
        return `<div class="health-event-row ${tone}"><strong>${escapeHtml(timeText)}</strong><span>${escapeHtml(event.message || '-')}</span><span>${escapeHtml(healthStatusLabel(event.status))} ? ${escapeHtml(countText)}</span></div>`;
      }).join('');
    }

    function renderHealthCheckFromApi(data) {
      latestHealthCheck = data || null;
      const badge = document.getElementById('health_check_badge');
      const hint = document.getElementById('health_check_hint');
      if (!badge || !hint || !latestHealthCheck) return false;
      const checks = latestHealthCheck.checks || {};
      const map = [
        ['health_8085', 'dashboard', '8085 \u5de5\u4f5c\u53f0'],
        ['health_8081', 'patient_web', '8081 \u75c5\u4eba\u7aef'],
        ['health_chassis', 'chassis', '\u5e95\u76d8 / ROS2'],
        ['health_voice', 'voice', '\u8bed\u97f3\u94fe\u8def'],
        ['health_vision', 'vision', '\u836f\u54c1\u8bc6\u522b'],
        ['health_batch', 'delivery_batch', '\u914d\u9001\u6279\u6b21'],
        ['health_safety', 'safety_self_test', '\u5b89\u5168\u95e8\u81ea\u6d4b'],
      ];
      map.forEach(([elementId, key, fallbackLabel]) => {
        const item = checks[key] || {};
        setHealthCheckField(
          elementId,
          item.label || fallbackLabel,
          item.message || '-',
          healthTone(item.status)
        );
      });
      const summary = latestHealthCheck.summary || {};
      const bad = Number(summary.bad || 0);
      const warn = Number(summary.warn || 0);
      if (bad > 0) {
        badge.textContent = `\u5f02\u5e38 ${bad}`;
        badge.className = 'badge CANCELED';
      } else if (warn > 0) {
        badge.textContent = `\u9700\u786e\u8ba4 ${warn}`;
        badge.className = 'badge WAITING_LOAD_CONFIRMATION';
      } else {
        badge.textContent = '\u6838\u5fc3\u5728\u7ebf';
        badge.className = 'badge RUNNING';
      }
      const problemTexts = Object.values(checks)
        .filter(item => item && item.status !== 'ok')
        .map(item => `${item.label || '\u9879\u76ee'}\uff1a${item.message || '-'}`);
      hint.textContent = problemTexts.length
        ? `\u5efa\u8bae\u5148\u5904\u7406\uff1a${problemTexts.join('\uff1b')}\u3002`
        : '\u540e\u7aef\u5065\u5eb7\u68c0\u67e5\u901a\u8fc7\uff1b\u6267\u884c\u914d\u9001\u524d\u4ecd\u9700\u6309\u6d41\u7a0b\u5b8c\u6210\u88c5\u836f\u3001\u590d\u6838\u548c\u5e8a\u65c1\u786e\u8ba4\u3002';
      renderHealthGate(latestHealthCheck);
      renderHealthCheckMeta(latestHealthCheck);
      renderHealthCheckDetails(latestHealthCheck);
      renderHealthCheckEvents(latestHealthCheck);
      renderHealthCheckActions(latestHealthCheck);
      updateHealthTabBadge(latestHealthCheck);
      maybeNotifyHealthChange(latestHealthCheck);
      return true;
    }

    function refreshHealthCheck() {
      if (latestHealthCheck && renderHealthCheckFromApi(latestHealthCheck)) return;
      const badge = document.getElementById('health_check_badge');
      const hint = document.getElementById('health_check_hint');
      if (!badge || !hint) return;
      const host = location.hostname || '192.168.31.125';
      const patientUrl = `${host}:8081/patient/`;
      const nowSec = Date.now() / 1000;
      const chassisReceived = Boolean(latestChassisStatus?.received);
      const chassisAge = latestChassisStatus?.web_received_at ? Math.max(0, nowSec - Number(latestChassisStatus.web_received_at)) : null;
      const chassisFresh = chassisReceived && (chassisAge == null || chassisAge < 5);
      const hasBatch = Boolean(latestDeliveryBatch && latestDeliveryBatch.batch_id);
      const batchStage = latestDeliveryBatch?.route_status || latestDeliveryBatch?.status || '-';
      const hasRecognition = Boolean(latestDrugInfo?.drug_name || latestDrugInfo?.ocr_drug_name || latestDrugInfo?.trace_code || latestDrugInfo?.label_product_code || latestDrugInfo?.raw_code_text || latestDrugInfo?.code_text);
      const voiceRemaining = Math.max(0, Math.ceil(((typeof voiceListenEndsAt === 'number' ? voiceListenEndsAt : 0) - Date.now()) / 1000));
      const voiceActive = voiceRemaining > 0;
      const warnings = [];

      setHealthCheckField('health_8085', '8085 \u5de5\u4f5c\u53f0', '\u5f53\u524d\u5728\u7ebf', 'ok');
      setHealthCheckField('health_8081', '8081 \u75c5\u4eba\u7aef', patientUrl, 'ok');
      setHealthCheckField('health_chassis', '\u5e95\u76d8 / ROS2', chassisFresh ? `\u5df2\u8fde\u63a5 ${chassisAge == null ? '' : `${chassisAge.toFixed(1)}s`}` : (chassisReceived ? '\u72b6\u6001\u5ef6\u8fdf' : '\u7b49\u5f85\u72b6\u6001'), chassisFresh ? 'ok' : (chassisReceived ? 'warn' : 'cold'));
      setHealthCheckField('health_voice', '\u8bed\u97f3\u7a97\u53e3', voiceActive ? `\u76d1\u542c\u4e2d ${voiceRemaining}s` : '\u672a\u5f00\u542f', voiceActive ? 'ok' : 'cold');
      setHealthCheckField('health_vision', '\u836f\u54c1\u8bc6\u522b', hasRecognition ? '\u6700\u8fd1\u6709\u7ed3\u679c' : '\u7b49\u5f85\u8bc6\u522b', hasRecognition ? 'ok' : 'cold');
      setHealthCheckField('health_batch', '\u914d\u9001\u6279\u6b21', hasBatch ? `${latestDeliveryBatch.batch_id} \u00b7 ${batchStage}` : '\u6682\u65e0\u6279\u6b21', hasBatch ? 'ok' : 'warn');

      if (!chassisFresh) warnings.push('\u5e95\u76d8\u72b6\u6001\u672a\u5b9e\u65f6\u4e0a\u62a5');
      if (!hasBatch) warnings.push('\u5f53\u524d\u6ca1\u6709\u53ef\u6267\u884c\u914d\u9001\u6279\u6b21');
      if (!hasRecognition) warnings.push('\u836f\u54c1\u8bc6\u522b\u6682\u65e0\u6700\u8fd1\u7ed3\u679c');
      badge.textContent = warnings.length ? `\u9700\u786e\u8ba4 ${warnings.length}` : '\u6838\u5fc3\u5728\u7ebf';
      badge.className = warnings.length ? 'badge WAITING_LOAD_CONFIRMATION' : 'badge RUNNING';
      hint.textContent = warnings.length ? `\u5efa\u8bae\u5148\u5904\u7406\uff1a${warnings.join('\uff1b')}\u3002` : '\u5de5\u4f5c\u53f0\u3001\u75c5\u4eba\u7aef\u5165\u53e3\u3001\u5e95\u76d8\u72b6\u6001\u3001\u8bed\u97f3\u7a97\u53e3\u3001\u8bc6\u522b\u548c\u6279\u6b21\u72b6\u6001\u5df2\u6c47\u603b\uff1b\u6267\u884c\u914d\u9001\u524d\u4ecd\u9700\u6309\u6d41\u7a0b\u5b8c\u6210\u88c5\u836f\u3001\u590d\u6838\u548c\u5e8a\u65c1\u786e\u8ba4\u3002';
    }

    async function refreshHealthCheckApi() {
      try {
        const response = await fetch('/api/health_check', { cache: 'no-store' });
        const text = await response.text();
        let data = null;
        try {
          data = text ? JSON.parse(text) : null;
        } catch (_) {
          data = null;
        }
        if (data && data.checks && data.summary) {
          renderHealthCheckFromApi(data);
          if (!response.ok) {
            const hint = document.getElementById('health_check_hint');
            if (hint) hint.textContent = `\u540e\u7aef\u81ea\u68c0\u8fd4\u56de\u5f02\u5e38\u72b6\u6001 ${response.status}\uff0c\u5df2\u663e\u793a\u7ed3\u6784\u5316\u9519\u8bef\u3002`;
          }
          return;
        }
        throw new Error(`HTTP ${response.status}`);
      } catch (error) {
        latestHealthCheck = null;
        refreshHealthCheck();
        const hint = document.getElementById('health_check_hint');
        if (hint) hint.textContent = `\u540e\u7aef\u5065\u5eb7\u68c0\u67e5\u63a5\u53e3\u6682\u4e0d\u53ef\u7528\uff0c\u5df2\u964d\u7ea7\u4e3a\u524d\u7aef\u72b6\u6001\u6c47\u603b\uff1a${error.message}`;
      }
    }

    function batchExceptionSummary(batch) {
      const rows = collectBatchExceptions(batch || latestDeliveryBatch || {});
      return {
        rows,
        danger: rows.filter(item => item.severity === 'danger').length,
        review: rows.filter(item => item.type === 'medication_review').length,
        riskMessages: rows.filter(item => item.type === 'pending_message_risk').length,
        pendingMessages: rows.filter(item => item.type === 'pending_message').length,
      };
    }

    function buildBatchBlockers(batch, action = 'advance') {
      const data = batch || {};
      const summary = data.summary || {};
      const status = data.route_status || 'WAITING_LOAD_CONFIRMATION';
      const blockers = [];
      const warnings = [];
      const emergencyStop = latestChassisStatus?.emergency_stop;
      const battery = latestChassisStatus?.battery ?? latestChassisStatus?.battery_percent;
      const batteryNumber = Number(battery);
      const chassisReceived = Boolean(latestChassisStatus?.received);
      const cabinetLocked = latestChassisStatus?.cabinet_locked ?? latestChassisStatus?.medicine_cabinet_locked;
      const healthDecision = deriveHealthGate(latestHealthCheck);
      const exceptions = batchExceptionSummary(data);

      if (!data.batch_id) {
        blockers.push('当前没有配送批次，请先导入或新建批次。');
      }
      if (healthDecision.tone === 'bad') {
        blockers.push(`系统自检结论：${healthDecision.title}，请先处理自检异常。`);
      } else if (healthDecision.tone === 'warn') {
        warnings.push(`系统自检结论：${healthDecision.title}，建议先确认。`);
      }
      const safetyCheck = latestHealthCheck?.checks?.safety_self_test || null;
      if (safetyCheck?.status === 'bad') {
        blockers.push(`\u5b89\u5168\u95e8\u81ea\u6d4b\u5f02\u5e38\uff1a${safetyCheck.message || '\u8bf7\u91cd\u65b0\u8fd0\u884c\u5b89\u5168\u95e8\u81ea\u6d4b\u3002'}`);
      } else if (safetyCheck?.status === 'warn') {
        warnings.push(`\u5b89\u5168\u95e8\u81ea\u6d4b\u5f85\u786e\u8ba4\uff1a${safetyCheck.message || '\u5efa\u8bae\u5148\u8fd0\u884c\u5b89\u5168\u95e8\u81ea\u6d4b\u3002'}`);
      }
      if (exceptions.danger > 0) {
        blockers.push(`异常中心有 ${exceptions.danger} 项高优先级问题，处理前不要推进配送。`);
      }
      if (exceptions.review > 0) {
        blockers.push(`有 ${exceptions.review} 位病人待用药复核，需先复核通过或退回药房。`);
      }
      if (exceptions.riskMessages > 0) {
        blockers.push(`有 ${exceptions.riskMessages} 条疑似用药风险咨询，需先回复并处理。`);
      } else if (exceptions.pendingMessages > 0) {
        warnings.push(`有 ${exceptions.pendingMessages} 条病人咨询未处理，建议先回复。`);
      }
      if (emergencyStop === true) {
        blockers.push('急停已开启，禁止下发移动任务。');
      }
      if (Number.isFinite(batteryNumber) && batteryNumber < 20) {
        blockers.push(`电量 ${Math.round(batteryNumber)}%，低于 20%，禁止新配送任务。`);
      } else if (Number.isFinite(batteryNumber) && batteryNumber < 50) {
        warnings.push(`电量 ${Math.round(batteryNumber)}%，建议只执行短任务并尽快充电。`);
      } else if (!Number.isFinite(batteryNumber)) {
        warnings.push('电量未上报，自动配送前建议确认底盘电源状态。');
      }
      if (action === 'load' && status !== 'WAITING_LOAD_CONFIRMATION') {
        warnings.push('当前已不是装药核验阶段，请确认是否需要重复写入装药记录。');
      }
      if (action === 'dispense' && !['WARD_HANDOVER', 'NAVIGATING_TO_WARD'].includes(status)) {
        blockers.push('当前还未到床旁交付阶段，不建议执行床旁交付核验。');
      }
      if (status === 'WAITING_LOAD_CONFIRMATION' && summary.all_loaded !== true && action === 'advance') {
        const total = summary.medication_total_count || 0;
        const loaded = summary.medication_loaded_count || 0;
        blockers.push(`${Math.max(total - loaded, 0)} 项药品未完成药师装药核验。`);
      }
      if (status === 'READY_TO_DEPART' && !chassisReceived) {
        blockers.push('ROS2/底盘状态未连接，暂不建议进入配送。');
      }
      if (cabinetLocked === false && ['READY_TO_DEPART', 'NAVIGATING_TO_WARD'].includes(status)) {
        blockers.push('药舱未锁定，禁止进入或继续配送。');
      } else if (cabinetLocked === undefined) {
        warnings.push('药舱锁定状态未上报，请人工确认药舱门已关闭。');
      }
      return { blockers, warnings };
    }

    function uniqueSafetyGateActions(actions) {
      const seen = new Set();
      const result = [];
      (actions || []).forEach(action => {
        if (!action || !action.action || !action.label) return;
        const key = `${action.action}:${action.tab || ''}:${action.target || ''}:${action.filter || ''}:${action.label}`;
        if (seen.has(key)) return;
        seen.add(key);
        result.push(action);
      });
      return result.slice(0, 5);
    }

    function safetyTextHas(text, words) {
      return (words || []).some(word => text.includes(word));
    }

    function buildSafetyGateActions(blockers = [], warnings = []) {
      const text = [...(blockers || []), ...(warnings || [])].join(' ');
      const actions = [];
      const add = (label, action, extra = {}) => actions.push({ label, action, ...extra });
      if (safetyTextHas(text, ['\u7cfb\u7edf\u81ea\u68c0', '\u81ea\u68c0\u7ed3\u8bba'])) add('\u67e5\u770b\u7cfb\u7edf\u81ea\u68c0', 'switch_tab', { tab: 'monitor' });
      if (safetyTextHas(text, ['\u5b89\u5168\u95e8\u81ea\u6d4b'])) add('\u8fd0\u884c\u5b89\u5168\u95e8\u81ea\u6d4b', 'run_safety_test');
      if (safetyTextHas(text, ['\u5f85\u7528\u836f\u590d\u6838', '\u75c5\u4eba\u5f85\u7528\u836f\u590d\u6838', '\u75c5\u4eba\u53cd\u9988', '\u7591\u4f3c\u7528\u836f\u98ce\u9669', '\u75c5\u4eba\u54a8\u8be2', '\u9ad8\u4f18\u5148\u7ea7\u95ee\u9898', '\u5f02\u5e38\u4e2d\u5fc3'])) add('\u5b9a\u4f4d\u5f85\u5904\u7406\u95ee\u9898', 'locate_feedback');
      if (safetyTextHas(text, ['\u5e95\u76d8', 'ROS2', '\u6025\u505c', '\u7535\u91cf', '\u836f\u8231'])) add('\u67e5\u770b\u5e95\u76d8\u72b6\u6001', 'switch_tab', { tab: 'monitor' });
      if (safetyTextHas(text, ['\u672a\u5b8c\u6210\u836f\u5e08\u88c5\u836f', '\u672a\u5b8c\u6210\u88c5\u836f', '\u836f\u54c1\u672a\u5b8c\u6210', '\u88c5\u836f\u6838\u9a8c'])) add('\u67e5\u770b\u836f\u54c1\u6e05\u5355', 'focus', { target: 'batch_stops' });
      if (safetyTextHas(text, ['\u6ca1\u6709\u914d\u9001\u6279\u6b21', '\u5bfc\u5165', '\u65b0\u5efa\u6279\u6b21'])) add('\u67e5\u770b\u6279\u6b21\u5bfc\u5165', 'focus', { target: 'batch_import_text' });
      if (safetyTextHas(text, ['\u4ea4\u4ed8\u9636\u6bb5', '\u5e8a\u65c1\u4ea4\u4ed8'])) add('\u67e5\u770b\u6d41\u7a0b\u8fdb\u5ea6', 'focus', { target: 'batch_workflow_guide' });
      add('\u5237\u65b0\u6279\u6b21\u72b6\u6001', 'refresh_batch');
      return uniqueSafetyGateActions(actions);
    }

    function renderSafetyGateActions(actions) {
      const items = uniqueSafetyGateActions(actions);
      if (!items.length) return '';
      return `<div class="safety-gate-actions">${items.map((action, index) => `<button type="button" data-safety-action="${index}">${escapeHtml(action.label)}</button>`).join('')}</div>`;
    }

    function renderSafetyGateHeader(title, blockers = [], warnings = []) {
      const parts = [];
      if (blockers.length) parts.push(`<span class="safety-gate-pill">${blockers.length} \u9879\u963b\u65ad</span>`);
      if (warnings.length) parts.push(`<span class="safety-gate-pill">${warnings.length} \u9879\u63d0\u9192</span>`);
      if (!parts.length) parts.push('<span class="safety-gate-pill">\u5df2\u901a\u8fc7</span>');
      return `<div class="safety-gate-head"><strong>${escapeHtml(title)}</strong><div class="safety-gate-counts">${parts.join('')}</div></div>`;
    }

    function renderSafetyGatePriority(blockers = [], warnings = []) {
      const top = (blockers && blockers[0]) || (warnings && warnings[0]) || '';
      if (!top) return '<div class="safety-gate-priority">\u4e3b\u8981\u7ed3\u8bba\uff1a\u5f53\u524d\u6ca1\u6709\u9700\u8981\u5904\u7406\u7684\u5b89\u5168\u95e8\u9879\u3002</div>';
      const prefix = blockers.length ? '\u4f18\u5148\u5904\u7406' : '\u5efa\u8bae\u5148\u786e\u8ba4';
      return `<div class="safety-gate-priority">${prefix}\uff1a${escapeHtml(top)}</div>`;
    }

    function renderBackendSafetyGateSummary() {
      const gate = latestBackendSafetyGate || null;
      if (!gate || !gate.summary) return '';
      const summary = gate.summary || {};
      const blockers = Number(summary.blockers || 0);
      const warnings = Number(summary.warnings || 0);
      const primary = summary.primary_action || 'advance';
      const labelMap = { load: '\u88c5\u836f', advance: '\u63a8\u8fdb', dispense: '\u4ea4\u4ed8' };
      const tone = blockers ? '\u540e\u7aef\u9884\u68c0\u963b\u65ad' : (warnings ? '\u540e\u7aef\u9884\u68c0\u63d0\u9192' : '\u540e\u7aef\u9884\u68c0\u901a\u8fc7');
      return `<div class="safety-backend-gate"><strong>${tone}</strong>\uff1a${blockers} \u9879\u963b\u65ad / ${warnings} \u9879\u63d0\u9192\uff0c\u4e3b\u8981\u52a8\u4f5c\uff1a${escapeHtml(labelMap[primary] || primary)}\u3002</div>`;
    }

    function bindSafetyGateActions(actions) {
      const items = uniqueSafetyGateActions(actions);
      document.querySelectorAll('[data-safety-action]').forEach(button => {
        const index = Number(button.getAttribute('data-safety-action'));
        const action = items[index];
        button.addEventListener('click', () => runSafetyGateAction(action));
      });
    }

    function runSafetyGateAction(action) {
      if (!action) return;
      if (action.action === 'switch_tab') {
        switchDashboardTab(action.tab || 'batch');
        return;
      }
      if (action.action === 'locate_feedback') {
        locateFeedbackPatient();
        return;
      }
      if (action.action === 'run_safety_test') {
        const button = document.getElementById('safety-self-test');
        if (button) {
          button.scrollIntoView({ behavior: 'smooth', block: 'center' });
          button.focus({ preventScroll: true });
        }
        runSafetySelfTest().catch(error => showDashboardToast('\u5b89\u5168\u95e8\u81ea\u6d4b\u5931\u8d25', error.message, 'danger'));
        return;
      }
      if (action.action === 'refresh_batch') {
        refreshDeliveryBatch();
        showDashboardToast('\u6b63\u5728\u5237\u65b0\u6279\u6b21', '\u5df2\u91cd\u65b0\u8bf7\u6c42\u914d\u9001\u6279\u6b21\u72b6\u6001\u3002', 'ok');
        return;
      }
      if (action.action === 'focus') {
        switchDashboardTab('batch');
        window.setTimeout(() => {
          const target = document.getElementById(action.target || '');
          if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'center' });
            if (typeof target.focus === 'function') target.focus({ preventScroll: true });
            target.classList.add('recommended-action');
            window.setTimeout(() => target.classList.remove('recommended-action'), 2200);
          }
        }, 80);
      }
    }

    function updateBatchSafetyGate(batch) {
      const bar = document.getElementById('batch_blocker_bar');
      const advanceButton = document.getElementById('batch-advance');
      const loadButton = document.getElementById('batch-load-scan');
      const dispenseButton = document.getElementById('batch-dispense-scan');
      if (!bar) return;
      const { blockers, warnings } = buildBatchBlockers(batch, 'advance');
      const loadGate = buildBatchBlockers(batch, 'load');
      const dispenseGate = buildBatchBlockers(batch, 'dispense');
      const actions = buildSafetyGateActions(blockers, warnings);
      if (advanceButton) {
        advanceButton.disabled = blockers.length > 0;
        advanceButton.title = blockers.length ? blockers.join(' ') : '\u6761\u4ef6\u6ee1\u8db3\uff0c\u53ef\u8fdb\u5165\u4e0b\u4e00\u914d\u9001\u9636\u6bb5';
      }
      if (loadButton) {
        loadButton.disabled = loadGate.blockers.length > 0;
        loadButton.title = loadGate.blockers.length ? loadGate.blockers.join(' ') : '\u53ef\u6267\u884c\u836f\u5e08\u88c5\u836f\u6838\u9a8c';
      }
      if (dispenseButton) {
        dispenseButton.disabled = dispenseGate.blockers.length > 0;
        dispenseButton.title = dispenseGate.blockers.length ? dispenseGate.blockers.join(' ') : '\u53ef\u6267\u884c\u5e8a\u65c1\u4ea4\u4ed8\u6838\u9a8c';
      }
      if (blockers.length) {
        bar.className = 'safety-gate blocked';
        bar.innerHTML = `${renderSafetyGateHeader('\u5f53\u524d\u4e0d\u53ef\u8fdb\u5165\u4e0b\u4e00\u914d\u9001\u9636\u6bb5', blockers, warnings)}${renderSafetyGatePriority(blockers, warnings)}${renderBackendSafetyGateSummary()}<ol>${blockers.map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ol>${warnings.length ? `<ol>${warnings.map(item => `<li>\u63d0\u9192\uff1a${escapeHtml(item)}</li>`).join('')}</ol>` : ''}${renderSafetyGateActions(actions)}`;
      } else if (warnings.length) {
        bar.className = 'safety-gate warn';
        bar.innerHTML = `${renderSafetyGateHeader('\u5f53\u524d\u53ef\u4eba\u5de5\u63a8\u8fdb\uff0c\u4f46\u5efa\u8bae\u5148\u786e\u8ba4', blockers, warnings)}${renderSafetyGatePriority(blockers, warnings)}${renderBackendSafetyGateSummary()}<ol>${warnings.map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ol>${renderSafetyGateActions(actions)}`;
      } else {
        bar.className = 'safety-gate';
        bar.innerHTML = `${renderSafetyGateHeader('\u5f53\u524d\u53ef\u8fdb\u5165\u4e0b\u4e00\u914d\u9001\u9636\u6bb5', blockers, warnings)}${renderSafetyGatePriority(blockers, warnings)}${renderBackendSafetyGateSummary()}<div>\u88c5\u836f\u3001\u5e95\u76d8\u3001\u836f\u8231\u3001\u6025\u505c\u3001\u75c5\u4eba\u590d\u6838\u548c\u81ea\u68c0\u672a\u53d1\u73b0\u963b\u585e\u9879\u3002</div>`;
      }
      bindSafetyGateActions(actions);
    }

    function activeBatchStop(batch) {
      const stops = Array.isArray(batch && batch.stops) ? batch.stops : [];
      const index = Number(batch && batch.active_stop_index);
      if (Number.isFinite(index) && index >= 0 && stops[index]) return stops[index];
      return stops.find(stop => !['COMPLETED', 'SKIPPED'].includes(String(stop.stop_status || ''))) || stops[0] || null;
    }

    function summarizeWorkflowGuide(batch) {
      const data = batch || {};
      const status = data.route_status || 'WAITING_LOAD_CONFIRMATION';
      const summary = data.summary || {};
      const exceptions = collectBatchExceptions(data);
      const critical = exceptions.filter(item => item.severity === 'danger').length;
      const review = exceptions.filter(item => item.type === 'medication_review').length;
      const pendingMessages = exceptions.filter(item => ['pending_message', 'pending_message_risk'].includes(item.type)).length;
      const activeStop = activeBatchStop(data);
      const activeWard = activeStop ? (activeStop.display_name || activeStop.ward_name || activeStop.target_station || '') : '';
      const totalMeds = Number(summary.medication_total_count || 0);
      const loadedMeds = Number(summary.medication_loaded_count || 0);
      const dispensedMeds = Number(summary.medication_dispensed_count || 0);
      const remainingLoad = Math.max(totalMeds - loadedMeds, 0);
      const remainingDispense = Math.max(totalMeds - dispensedMeds, 0);
      const { blockers, warnings } = buildBatchBlockers(data);
      if (!data.batch_id) {
        return {
          tone: 'warn',
          badgeClass: 'IDLE',
          badge: '\u5f85\u6279\u6b21',
          title: '\u8bf7\u5148\u5bfc\u5165\u6216\u521b\u5efa\u914d\u9001\u6279\u6b21',
          body: '\u5f53\u524d\u6ca1\u6709\u53ef\u6267\u884c\u7684\u6279\u6b21\u3002\u53ef\u4ece\u5916\u90e8 JSON \u63a5\u6536\u5f85\u91c7\u7528\u6279\u6b21\uff0c\u6216\u4f7f\u7528\u65b0\u5efa\u914d\u9001\u6279\u6b21\u8fdb\u884c\u6f14\u793a\u3002',
          actions: [{ label: '\u67e5\u770b\u5916\u90e8\u6279\u6b21\u5bfc\u5165', target: 'batch_import_text' }],
        };
      }
      if (critical > 0) {
        return {
          tone: 'danger',
          badgeClass: 'CANCELED',
          badge: `${critical} \u9879\u9ad8\u4f18\u5148\u7ea7`,
          title: '\u5148\u5904\u7406\u9ad8\u4f18\u5148\u7ea7\u5f02\u5e38',
          body: `\u5f53\u524d\u6709 ${critical} \u9879\u9ad8\u4f18\u5148\u7ea7\u5f02\u5e38\u3002\u5efa\u8bae\u5148\u5728\u5f02\u5e38\u5904\u7406\u4e2d\u5fc3\u5b9a\u4f4d\u5e76\u5904\u7406\uff0c\u518d\u7ee7\u7eed\u914d\u9001\u6d41\u7a0b\u3002`,
          actions: [{ label: '\u67e5\u770b\u9ad8\u4f18\u5148\u7ea7\u5f02\u5e38', target: 'exception_center', filter: 'danger' }],
        };
      }
      if (review > 0) {
        return {
          tone: 'warn',
          badgeClass: 'WAITING_LOAD_CONFIRMATION',
          badge: `${review} \u9879\u5f85\u590d\u6838`,
          title: '\u5148\u5b8c\u6210\u7528\u836f\u590d\u6838',
          body: `\u5f53\u524d\u6709 ${review} \u9879\u75c5\u4eba\u7528\u836f\u590d\u6838\u3002\u590d\u6838\u524d\u4e0d\u5efa\u8bae\u7ee7\u7eed\u4ea4\u4ed8\u6216\u5f52\u6863\u3002`,
          actions: [{ label: '\u67e5\u770b\u5f85\u590d\u6838', target: 'exception_center', filter: 'medication_review' }],
        };
      }
      if (pendingMessages > 0) {
        return {
          tone: 'warn',
          badgeClass: 'WAITING_LOAD_CONFIRMATION',
          badge: `${pendingMessages} \u6761\u54a8\u8be2`,
          title: '\u5148\u56de\u590d\u75c5\u4eba\u54a8\u8be2',
          body: `\u75c5\u4eba\u7aef\u8fd8\u6709 ${pendingMessages} \u6761\u672a\u5904\u7406\u54a8\u8be2\u3002\u5efa\u8bae\u5148\u56de\u590d\uff0c\u907f\u514d\u75c5\u4eba\u5bf9\u7528\u836f\u4ea7\u751f\u7591\u95ee\u540e\u7ee7\u7eed\u7b7e\u6536\u3002`,
          actions: [{ label: '\u6253\u5f00\u75c5\u4eba\u54a8\u8be2', target: 'messages-tab' }],
        };
      }
      if (status === 'WAITING_LOAD_CONFIRMATION') {
        return {
          tone: remainingLoad > 0 ? 'warn' : 'ok',
          badgeClass: remainingLoad > 0 ? 'WAITING_LOAD_CONFIRMATION' : 'COMPLETED',
          badge: remainingLoad > 0 ? `\u5f85\u88c5\u836f ${remainingLoad}` : '\u88c5\u836f\u5df2\u5b8c\u6210',
          title: remainingLoad > 0 ? '\u4e0b\u4e00\u6b65\uff1a\u836f\u5e08\u88c5\u836f\u6838\u9a8c' : '\u88c5\u836f\u5df2\u5b8c\u6210\uff0c\u53ef\u63a8\u8fdb\u9636\u6bb5',
          body: remainingLoad > 0
            ? `\u5df2\u91c7\u7528\u6279\u6b21\u540e\uff0c\u8bf7\u5148\u6267\u884c\u836f\u5e08\u88c5\u836f\u6838\u9a8c\u3002\u5f53\u524d\u8fd8\u6709 ${remainingLoad} \u9879\u836f\u54c1\u672a\u6838\u9a8c\uff0c\u6838\u9a8c\u5b8c\u624d\u80fd\u8fdb\u5165\u914d\u9001\u3002`
            : '\u88c5\u836f\u6838\u9a8c\u5df2\u5b8c\u6210\u3002\u8bf7\u518d\u6838\u5bf9\u5e95\u76d8\u3001\u836f\u8231\u548c\u6025\u505c\u72b6\u6001\uff0c\u7136\u540e\u70b9\u51fb\u8fdb\u5165\u4e0b\u4e00\u914d\u9001\u9636\u6bb5\u3002',
          actions: remainingLoad > 0
            ? [{ label: '\u6267\u884c\u88c5\u836f\u6838\u9a8c', target: 'batch-load-scan', primary: true }]
            : [{ label: '\u8fdb\u5165\u4e0b\u4e00\u914d\u9001\u9636\u6bb5', target: 'batch-advance', primary: true }],
        };
      }
      if (status === 'READY_TO_DEPART') {
        return {
          tone: blockers.length ? 'danger' : (warnings.length ? 'warn' : 'ok'),
          badgeClass: blockers.length ? 'CANCELED' : (warnings.length ? 'WAITING_LOAD_CONFIRMATION' : 'COMPLETED'),
          badge: blockers.length ? '\u6709\u963b\u585e' : '\u5f85\u51fa\u53d1',
          title: blockers.length ? '\u5148\u89e3\u9664\u963b\u585e\u9879' : '\u4e0b\u4e00\u6b65\uff1a\u51fa\u53d1\u524d\u786e\u8ba4',
          body: blockers.length ? blockers.join(' ') : `\u88c5\u836f\u5df2\u5b8c\u6210\u3002${warnings.length ? '\u8bf7\u5148\u786e\u8ba4\uff1a' + warnings.join(' ') : '\u72b6\u6001\u672a\u53d1\u73b0\u963b\u585e\u3002'}\u786e\u8ba4\u540e\u53ef\u70b9\u51fb\u8fdb\u5165\u4e0b\u4e00\u914d\u9001\u9636\u6bb5\u3002`,
          actions: [{ label: '\u8fdb\u5165\u4e0b\u4e00\u914d\u9001\u9636\u6bb5', target: 'batch-advance', primary: true }],
        };
      }
      if (status === 'NAVIGATING_TO_WARD') {
        return {
          tone: 'ok',
          badgeClass: 'NAVIGATING',
          badge: '\u914d\u9001\u4e2d',
          title: activeWard ? `\u6b63\u5728\u524d\u5f80 ${activeWard}` : '\u6b63\u5728\u524d\u5f80\u76ee\u6807\u75c5\u623f',
          body: '\u673a\u5668\u4eba\u6b63\u5728\u79fb\u52a8\u3002\u8bf7\u5173\u6ce8\u5e95\u76d8\u72b6\u6001\u548c\u6025\u505c\uff0c\u5230\u8fbe\u5e8a\u65c1\u540e\u518d\u6267\u884c\u5e8a\u65c1\u4ea4\u4ed8\u6838\u9a8c\u3002',
          actions: [{ label: '\u67e5\u770b\u7cfb\u7edf\u76d1\u63a7', target: 'monitor-tab' }],
        };
      }
      if (status === 'WARD_HANDOVER') {
        return {
          tone: 'warn',
          badgeClass: 'WAITING_DISPENSE_CONFIRMATION',
          badge: `\u5f85\u4ea4\u4ed8 ${remainingDispense}`,
          title: activeWard ? `\u4e0b\u4e00\u6b65\uff1a${activeWard} \u5e8a\u65c1\u4ea4\u4ed8\u6838\u9a8c` : '\u4e0b\u4e00\u6b65\uff1a\u5e8a\u65c1\u4ea4\u4ed8\u6838\u9a8c',
          body: '\u5230\u8fbe\u75c5\u623f\u540e\uff0c\u8bf7\u9010\u4e00\u6838\u5bf9\u75c5\u4eba\u3001\u5e8a\u53f7\u548c\u836f\u54c1\uff0c\u518d\u6267\u884c\u5e8a\u65c1\u4ea4\u4ed8\u6838\u9a8c\u3002',
          actions: [{ label: '\u6267\u884c\u5e8a\u65c1\u4ea4\u4ed8\u6838\u9a8c', target: 'batch-dispense-scan', primary: true }],
        };
      }
      if (status === 'WARD_COMPLETED') {
        return {
          tone: 'ok',
          badgeClass: 'COMPLETED',
          badge: '\u75c5\u623f\u5b8c\u6210',
          title: '\u5f53\u524d\u75c5\u623f\u5df2\u5b8c\u6210',
          body: '\u5f53\u524d\u75c5\u623f\u5df2\u5b8c\u6210\u4ea4\u4ed8\u3002\u8bf7\u6839\u636e\u8def\u7ebf\u72b6\u6001\u63a8\u8fdb\u5230\u4e0b\u4e00\u75c5\u623f\u6216\u8fd4\u56de\u836f\u623f\u3002',
          actions: [{ label: '\u8fdb\u5165\u4e0b\u4e00\u914d\u9001\u9636\u6bb5', target: 'batch-advance', primary: true }],
        };
      }
      if (status === 'RETURNING_TO_PHARMACY') {
        return {
          tone: 'ok',
          badgeClass: 'NAVIGATING',
          badge: '\u8fd4\u56de\u4e2d',
          title: '\u673a\u5668\u4eba\u6b63\u5728\u8fd4\u56de\u836f\u623f',
          body: '\u8bf7\u5173\u6ce8\u5e95\u76d8\u72b6\u6001\u3002\u8fd4\u56de\u540e\u53ef\u5bfc\u51fa\u914d\u9001\u62a5\u544a\u548c\u5ba1\u8ba1\u7559\u75d5\u3002',
          actions: [{ label: '\u67e5\u770b\u914d\u9001\u62a5\u544a', target: 'report-tab' }],
        };
      }
      if (['BATCH_COMPLETED', 'COMPLETED'].includes(status)) {
        return {
          tone: 'ok',
          badgeClass: 'COMPLETED',
          badge: '\u5df2\u5b8c\u6210',
          title: '\u672c\u6b21\u6279\u6b21\u5df2\u5b8c\u6210',
          body: '\u5efa\u8bae\u5bfc\u51fa\u914d\u9001\u62a5\u544a\u548c\u5ba1\u8ba1 JSON\uff0c\u4fbf\u4e8e\u7559\u5b58\u548c\u8ffd\u6eaf\u3002',
          actions: [{ label: '\u5bfc\u51fa\u914d\u9001\u62a5\u544a', target: 'report-tab' }],
        };
      }
      return {
        tone: warnings.length ? 'warn' : 'ok',
        badgeClass: warnings.length ? 'WAITING_LOAD_CONFIRMATION' : 'COMPLETED',
        badge: batchStatusText(status),
        title: '\u6839\u636e\u5f53\u524d\u72b6\u6001\u63a8\u8fdb',
        body: warnings.length ? warnings.join(' ') : '\u672a\u53d1\u73b0\u660e\u786e\u963b\u585e\u9879\uff0c\u8bf7\u6309\u4e3b\u6d41\u7a0b\u6309\u94ae\u7ee7\u7eed\u3002',
        actions: [{ label: '\u8fdb\u5165\u4e0b\u4e00\u914d\u9001\u9636\u6bb5', target: 'batch-advance', primary: true }],
      };
    }

    function clearRecommendedBatchActions() {
      ['batch-load-scan', 'batch-advance', 'batch-dispense-scan'].forEach(id => {
        const button = document.getElementById(id);
        if (button) button.classList.remove('recommended-action');
      });
    }

    function runWorkflowGuideAction(target, filter = '') {
      if (filter) {
        exceptionCenterFilter = filter;
        renderExceptionCenter(latestDeliveryBatch);
      }
      if (target === 'messages-tab') {
        switchDashboardTab('messages');
        renderPatientMessages();
        return;
      }
      if (target === 'monitor-tab') {
        switchDashboardTab('monitor');
        return;
      }
      if (target === 'report-tab') {
        switchDashboardTab('report');
        renderDeliveryReport();
        return;
      }
      const element = document.getElementById(target);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        if (typeof element.focus === 'function') element.focus({ preventScroll: true });
      }
    }

    function renderWorkflowGuide(batch) {
      const guide = document.getElementById('batch_workflow_guide');
      if (!guide) return;
      const title = document.getElementById('batch_workflow_title');
      const badge = document.getElementById('batch_workflow_badge');
      const body = document.getElementById('batch_workflow_body');
      const actions = document.getElementById('batch_workflow_actions');
      const model = summarizeWorkflowGuide(batch || latestDeliveryBatch || {});
      guide.className = `workflow-guide ${model.tone || ''}`.trim();
      if (title) title.textContent = model.title || '\u4e0b\u4e00\u6b65\u64cd\u4f5c';
      if (badge) {
        badge.textContent = model.badge || '-';
        badge.className = `badge ${model.badgeClass || 'IDLE'}`;
      }
      if (body) body.textContent = model.body || '-';
      clearRecommendedBatchActions();
      if (actions) {
        actions.innerHTML = (model.actions || []).map((action, index) => `<button type="button" class="secondary ${action.primary ? 'recommended-action' : ''}" data-workflow-action="${index}">${escapeHtml(action.label || '\u67e5\u770b')}</button>`).join('');
        (model.actions || []).forEach((action, index) => {
          const button = actions.querySelector(`[data-workflow-action="${index}"]`);
          if (button) button.addEventListener('click', () => runWorkflowGuideAction(action.target, action.filter || ''));
          if (action.primary && action.target) {
            const targetButton = document.getElementById(action.target);
            if (targetButton) targetButton.classList.add('recommended-action');
          }
        });
      }
    }

    function safeBatchRows(batch) {
      try {
        return buildReportRowsFromBatch(batch || {});
      } catch (_) {
        return [];
      }
    }

    function batchClosureMedicationStats(batch) {
      const data = batch || {};
      const summary = data.summary || {};
      const rows = safeBatchRows(data);
      const total = rows.length || Number(summary.medication_total_count || 0);
      const loaded = rows.length ? rows.filter(row => row.loaded || row.dispensed || row.returned).length : Number(summary.medication_loaded_count || 0);
      const dispensed = rows.length ? rows.filter(row => row.dispensed).length : Number(summary.medication_dispensed_count || 0);
      const returned = rows.filter(row => row.returned).length;
      const reviewed = rows.filter(row => row.manual_reviewed).length;
      const exception = rows.filter(row => row.exception).length;
      return { rows, total, loaded, dispensed, returned, reviewed, exception };
    }

    function isRouteAtLeast(status, target) {
      const order = ['WAITING_LOAD_CONFIRMATION', 'READY_TO_DEPART', 'NAVIGATING_TO_WARD', 'WARD_HANDOVER', 'WARD_COMPLETED', 'RETURNING_TO_PHARMACY', 'BATCH_COMPLETED', 'COMPLETED'];
      const currentIndex = order.indexOf(status || 'WAITING_LOAD_CONFIRMATION');
      const targetIndex = order.indexOf(target);
      return currentIndex >= 0 && targetIndex >= 0 && currentIndex >= targetIndex;
    }

    function batchClosureArchiveModel(batch, medStats) {
      try {
        const reviewRows = buildMedicationReviewReportRows(batch || {});
        return buildReportArchiveGate(batch || {}, medStats.rows || [], reviewRows || []);
      } catch (_) {
        return { ok: false, tone: 'warn', badge: '\u5f85\u68c0\u67e5', issues: ['archive_check_unavailable'] };
      }
    }

    function makeBatchClosureStep(key, label, meta, state, target, filter = '') {
      return { key, label, meta, state, target, filter };
    }

    function buildBatchClosureTimeline(batch) {
      const data = batch || {};
      const status = data.route_status || 'WAITING_LOAD_CONFIRMATION';
      const hasBatch = Boolean(data.batch_id);
      const summary = data.summary || {};
      const med = batchClosureMedicationStats(data);
      const receipts = batchReceiptStats(data);
      const exceptions = collectBatchExceptions(data);
      const archive = batchClosureArchiveModel(data, med);
      const total = med.total || Number(summary.medication_total_count || 0);
      const loadedDone = total > 0 && med.loaded >= total;
      const deliveredOrClosed = total > 0 && (med.dispensed + med.returned + med.reviewed) >= total;
      const departed = isRouteAtLeast(status, 'NAVIGATING_TO_WARD');
      const finalStatus = ['BATCH_COMPLETED', 'COMPLETED'].includes(status);
      const allSigned = receipts.total > 0 && receipts.pending === 0 && receipts.review === 0;
      const activeWard = stationDisplayName(data.current_station || '');
      const steps = [];
      steps.push(makeBatchClosureStep(
        'import',
        '\u6279\u6b21\u5bfc\u5165',
        hasBatch ? (data.batch_id || '-') : (latestPendingBatch ? '\u6709\u5f85\u91c7\u7528\u6279\u6b21' : '\u7b49\u5f85\u5916\u90e8 JSON'),
        hasBatch ? 'done' : (latestPendingBatch ? 'active' : 'waiting'),
        latestPendingBatch && !hasBatch ? 'pending_batch_panel' : 'batch_import_text'
      ));
      steps.push(makeBatchClosureStep(
        'adopt',
        '\u6279\u6b21\u91c7\u7528',
        hasBatch ? batchStatusText(status) : '\u672a\u91c7\u7528',
        hasBatch ? 'done' : (latestPendingBatch ? 'active' : 'waiting'),
        'pending_batch_panel'
      ));
      steps.push(makeBatchClosureStep(
        'load',
        '\u836f\u5e08\u88c5\u836f',
        total ? `${med.loaded}/${total}` : '\u6682\u65e0\u836f\u54c1',
        loadedDone ? 'done' : (hasBatch ? 'active' : 'waiting'),
        'batch-load-scan'
      ));
      steps.push(makeBatchClosureStep(
        'depart',
        '\u51fa\u53d1\u914d\u9001',
        departed ? activeWard : batchStatusText(status),
        departed ? 'done' : (loadedDone || status === 'READY_TO_DEPART' ? 'active' : 'waiting'),
        'batch-advance'
      ));
      steps.push(makeBatchClosureStep(
        'handover',
        '\u5e8a\u65c1\u4ea4\u4ed8',
        total ? `${med.dispensed + med.returned + med.reviewed}/${total}` : '-',
        deliveredOrClosed ? 'done' : (['NAVIGATING_TO_WARD', 'WARD_HANDOVER', 'WARD_COMPLETED'].includes(status) ? 'active' : 'waiting'),
        'batch-dispense-scan'
      ));
      steps.push(makeBatchClosureStep(
        'sign',
        '\u75c5\u4eba\u7b7e\u6536',
        receipts.total ? `${receipts.signed}/${receipts.total}${receipts.review ? ' / \u5f85\u590d\u6838 ' + receipts.review : ''}` : '-',
        allSigned ? 'done' : (receipts.review || receipts.rejected ? 'blocked' : (receipts.pending ? 'active' : 'waiting')),
        receipts.review ? 'exception_center' : 'batch_stops',
        receipts.review ? 'medication_review' : ''
      ));
      steps.push(makeBatchClosureStep(
        'exceptions',
        '\u5f02\u5e38\u5904\u7406',
        exceptions.length ? `${exceptions.length} \u9879\u5f85\u5904\u7406` : '\u65e0\u96c6\u4e2d\u5f02\u5e38',
        exceptions.length ? (exceptions.some(item => item.severity === 'danger') ? 'blocked' : 'active') : 'done',
        'exception_center',
        exceptions.some(item => item.type === 'medication_review') ? 'medication_review' : 'all'
      ));
      steps.push(makeBatchClosureStep(
        'archive',
        '\u62a5\u544a\u5f52\u6863',
        archive.ok ? '\u53ef\u5f52\u6863' : (archive.issues && archive.issues.length ? `${archive.issues.length} \u9879\u672a\u95ed\u73af` : '\u5f85\u5b8c\u6210'),
        archive.ok || finalStatus ? 'done' : (hasBatch ? 'active' : 'waiting'),
        'report_archive_gate'
      ));
      const firstAttention = steps.find(step => step.state === 'blocked') || steps.find(step => step.state === 'active') || steps.find(step => step.state === 'waiting');
      const doneCount = steps.filter(step => step.state === 'done').length;
      return {
        steps,
        doneCount,
        totalCount: steps.length,
        blocked: steps.some(step => step.state === 'blocked'),
        complete: steps.every(step => step.state === 'done'),
        next: firstAttention,
        status,
      };
    }

    function runBatchClosureAction(target, filter = '') {
      if (!target) return;
      if (target === 'report_archive_gate') {
        switchDashboardTab('report');
        renderDeliveryReport();
        window.setTimeout(() => {
          const gate = document.getElementById('report_archive_gate');
          if (gate) gate.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 80);
        return;
      }
      if (target === 'exception_center') {
        exceptionCenterFilter = filter || 'all';
        renderExceptionCenter(latestDeliveryBatch);
      }
      const element = document.getElementById(target);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        if (typeof element.focus === 'function') element.focus({ preventScroll: true });
      }
    }

    function renderBatchClosureTimeline(batch) {
      const container = document.getElementById('batch_closure_timeline');
      const stepsEl = document.getElementById('batch_closure_steps');
      if (!container || !stepsEl) return;
      const title = document.getElementById('batch_closure_title');
      const hint = document.getElementById('batch_closure_hint');
      const badge = document.getElementById('batch_closure_badge');
      const model = buildBatchClosureTimeline(batch || latestDeliveryBatch || {});
      if (title) title.textContent = '\u6279\u6b21\u95ed\u73af\u65f6\u95f4\u7ebf';
      if (badge) {
        badge.textContent = model.complete ? '\u5df2\u95ed\u73af' : (model.blocked ? '\u6709\u963b\u585e' : `${model.doneCount}/${model.totalCount}`);
        badge.className = `badge ${model.complete ? 'COMPLETED' : (model.blocked ? 'CANCELED' : 'WAITING_LOAD_CONFIRMATION')}`;
      }
      if (hint) {
        hint.textContent = model.complete
          ? '\u5168\u6d41\u7a0b\u5df2\u95ed\u73af\uff0c\u53ef\u8fdb\u5165\u62a5\u544a\u5bfc\u51fa\u548c\u5f52\u6863\u3002'
          : (model.next ? `\u5f53\u524d\u5173\u6ce8\uff1a${model.next.label}\uff0c\u70b9\u51fb\u5bf9\u5e94\u8282\u70b9\u53ef\u8df3\u5230\u5904\u7406\u533a\u3002` : '\u6309\u5f53\u524d\u72b6\u6001\u7ee7\u7eed\u63a8\u8fdb\u6279\u6b21\u3002');
      }
      stepsEl.innerHTML = model.steps.map((step, index) => `<button type="button" class="batch-closure-step ${escapeHtml(step.state)}" data-closure-step="${index}"><span class="batch-closure-dot"></span><span class="batch-closure-title">${escapeHtml(step.label)}</span><span class="batch-closure-meta">${escapeHtml(step.meta || '-')}</span></button>`).join('');
      model.steps.forEach((step, index) => {
        const button = stepsEl.querySelector(`[data-closure-step="${index}"]`);
        if (button) button.addEventListener('click', () => runBatchClosureAction(step.target, step.filter || ''));
      });
    }

    function confirmCriticalAction(title, body) {
      return window.confirm(`${title}\n\n${body}`);
    }

    function switchDashboardTab(tabName) {
      document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.toggle('active', button.dataset.tab === tabName);
      });
      document.querySelectorAll('[data-page]').forEach(page => {
        page.classList.toggle('active', page.dataset.page === tabName);
      });
      if (tabName === 'report') {
        renderDeliveryReport();
      }
      syncCameraPreview();
    }

    async function api(path, options = {}) {
      const tokenFromUrl = new URLSearchParams(window.location.search).get('token') || '';
      if (tokenFromUrl) {
        window.localStorage.setItem('medicine_dashboard_api_token', tokenFromUrl);
      }
      const apiToken = tokenFromUrl || window.localStorage.getItem('medicine_dashboard_api_token') || '';
      const headers = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'medicine-dashboard',
        ...(options.headers || {}),
      };
      if (apiToken) {
        headers['X-API-Token'] = apiToken;
      }
      let response;
      try {
        response = await fetch(path, { ...options, headers });
      } catch (error) {
        const message = error?.message || '\u7f51\u7edc\u8fde\u63a5\u5931\u8d25';
        showDashboardToast('\u63a5\u53e3\u8fde\u63a5\u5931\u8d25', `${path}\uff1a${message}`, 'danger');
        throw new Error(message);
      }
      let data = {};
      try {
        data = await response.json();
      } catch (_) {
        data = {};
      }
      if (!response.ok) {
        const message = data.message || data.error || `HTTP ${response.status}`;
        showDashboardToast('\u64cd\u4f5c\u672a\u5b8c\u6210', message, 'danger');
        throw new Error(message);
      }
      return data;
    }

    async function loadStations() {
      const data = await api('/api/stations');
      for (const id of ['target_station', 'source_station']) {
        const select = document.getElementById(id);
        select.innerHTML = '';
        for (const station of data.stations) {
          const option = document.createElement('option');
          option.value = station.id;
          option.textContent = `${station.name} (${station.id})`;
          select.appendChild(option);
        }
      }
      document.getElementById('source_station').value = 'pharmacy';
      document.getElementById('target_station').value = data.stations.find(s => s.id !== 'pharmacy')?.id || data.stations[0]?.id || '';
    }

    function updateState(data) {
      const state = data.state || 'IDLE';
      latestTaskId = data.task_id || latestTaskId || '';
      const badge = document.getElementById('state-badge');
      badge.textContent = state;
      badge.className = `badge ${state}`;
      const progress = Math.round((data.progress || 0) * 100);
      document.getElementById('progress').style.width = `${progress}%`;
      document.getElementById('task_id').textContent = data.task_id || '-';
      document.getElementById('message').textContent = data.message || '-';
      document.getElementById('current_station').textContent = data.current_station || '-';
      document.getElementById('target_station_view').textContent = data.target_station || '-';
      document.getElementById('state_patient').textContent = data.patient_name ? `${data.patient_name} (${data.patient_id || '-'})` : (data.patient_id || '-');
      document.getElementById('state_bed_no').textContent = data.bed_no || '-';
      document.getElementById('task_medicine_name').textContent = data.medicine_name || '-';
      document.getElementById('state_medication_progress').textContent = formatMedicationProgress(data);
      document.getElementById('state_product_code').textContent = data.product_code || '-';
      document.getElementById('state_product_model').textContent = data.product_model || '-';
      document.getElementById('state_quantity').textContent = data.quantity || '-';
      document.getElementById('state_trace_id').textContent = data.trace_id || '-';
      document.getElementById('state_order_no').textContent = data.order_no || '-';
      document.getElementById('load_confirmed').textContent = data.load_confirmed ? '已确认' : '未确认';
      document.getElementById('load_confirmed_at').textContent = data.load_confirmed_at || '-';
      document.getElementById('dispense_confirmed').textContent = data.dispense_confirmed ? '已确认' : '未确认';
      document.getElementById('dispense_confirmed_at').textContent = data.dispense_confirmed_at || '-';
      const verificationStage = data.last_verification_stage || '-';
      const verificationResult = data.last_verification_message || '-';
      document.getElementById('last_verification').textContent = `${verificationStage}：${verificationResult}`;
      document.getElementById('progress_text').textContent = `${progress}%`;
      updateVerificationRecords(data.verification_records || []);
    }

    function parseMedicationsJson(value) {
      try {
        const parsed = JSON.parse(value || '[]');
        return Array.isArray(parsed) ? parsed : [];
      } catch (error) {
        return [];
      }
    }

    function formatMedicationProgress(data) {
      const total = data.medication_total_count || 0;
      if (!total) {
        return '-';
      }
      const loaded = data.medication_loaded_count || 0;
      const dispensed = data.medication_dispensed_count || 0;
      return `装药 ${loaded}/${total}，取药 ${dispensed}/${total}`;
    }

    function formatVerificationStage(stage) {
      if (stage === 'load') {
        return '装药确认';
      }
      if (stage === 'dispense') {
        return '取药确认';
      }
      return '一致性校验';
    }

    function escapeHtml(value) {
      return String(value ?? '').replace(/[&<>"']/g, char => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
      }[char]));
    }

    // ----- 病人咨询 (双向 IM, 微信式布局) -----
    let latestPatientMessages = [];
    // 当前选中的床位 (右侧聊天面板)
    let selectedBed = null;
    let markingNurseReadBed = '';
    // 每个床位独立的输入框草稿, 切换 / 刷新都不丢
    const replyDraftByBed = {};
    function formatMessageTime(seconds) {
      if (!seconds && seconds !== 0) return '';
      const ms = Number(seconds) * 1000;
      if (!Number.isFinite(ms)) return '';
      const d = new Date(ms);
      const diff = Date.now() - ms;
      if (diff < 60_000) return '刚刚';
      if (diff < 3600_000) return `${Math.floor(diff / 60_000)} 分钟前`;
      if (diff < 86400_000) return `${Math.floor(diff / 3600_000)} 小时前`;
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      const hh = String(d.getHours()).padStart(2, '0');
      const mm = String(d.getMinutes()).padStart(2, '0');
      return `${m}-${day} ${hh}:${mm}`;
    }
    function formatSidebarTime(seconds) {
      if (!seconds && seconds !== 0) return '';
      const ms = Number(seconds) * 1000;
      if (!Number.isFinite(ms)) return '';
      const d = new Date(ms);
      const diff = Date.now() - ms;
      if (diff < 60_000) return '刚刚';
      if (diff < 3600_000) return `${Math.floor(diff / 60_000)} 分前`;
      const todayStart = new Date();
      todayStart.setHours(0, 0, 0, 0);
      if (ms >= todayStart.getTime()) {
        const hh = String(d.getHours()).padStart(2, '0');
        const mm = String(d.getMinutes()).padStart(2, '0');
        return `${hh}:${mm}`;
      }
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      return `${m}-${day}`;
    }
    const NURSE_QUICK_REPLIES = [
      '请核对姓名和床位后确认取药',
      '请按医嘱用药',
      '请稍等，医护马上处理',
      '如身体不适，请立即呼叫医护',
      '本次药品将转回药房复核',
      '已通知主管医生',
    ];
    const NURSE_SAFETY_REPLIES = [
      '\u6536\u5230\uff0c\u8bf7\u6682\u505c\u670d\u7528\u5f53\u524d\u836f\u54c1\uff0c\u7b49\u62a4\u58eb\u6838\u5bf9\u540e\u518d\u4f7f\u7528\u3002',
      '\u8bf7\u628a\u836f\u54c1\u653e\u5728\u539f\u5305\u88c5\u4e0a\uff0c\u4e0d\u8981\u6253\u5f00\u6216\u670d\u7528\uff0c\u6211\u4eec\u6b63\u5728\u6838\u5bf9\u3002',
      '\u8bf7\u60a8\u518d\u6838\u5bf9\u4e00\u4e0b\u59d3\u540d\u3001\u5e8a\u4f4d\u548c\u836f\u76d2\u540d\u79f0\uff0c\u6211\u4eec\u4f1a\u5c3d\u5feb\u5904\u7406\u3002',
      '\u5df2\u8f6c\u4e3a\u7528\u836f\u590d\u6838\uff0c\u8bf7\u7a0d\u7b49\u533b\u62a4\u786e\u8ba4\u3002',
    ];
    function isMedicationSafetyMessage(m) {
      const text = String((m && m.content) || '');
      return /\u75c5\u4eba\u7aef\u53cd\u9988|\u4fe1\u606f\u6709\u8bef|\u7528\u836f|\u836f\u54c1|\u5242\u91cf|\u8fc7\u654f|\u6838\u5bf9|\u62d2\u7edd|\u53cd\u9988/.test(text);
    }
    function getThreadSafetyMessages(thread) {
      return (thread && Array.isArray(thread.messages) ? thread.messages : []).filter(isMedicationSafetyMessage);
    }
    function groupMessagesByBed(messages) {
      // messages 来自后端: 时间倒序。这里按 bed 分组, 每组内按时间正序展示。
      const byBed = {};
      for (const m of messages) {
        const bed = m.bed || '-';
        if (!byBed[bed]) byBed[bed] = [];
        byBed[bed].push(m);
      }
      for (const bed of Object.keys(byBed)) {
        byBed[bed].sort((a, b) => (a.created_at || 0) - (b.created_at || 0));
      }
      const beds = Object.keys(byBed).sort((a, b) => {
        const la = byBed[a][byBed[a].length - 1].created_at || 0;
        const lb = byBed[b][byBed[b].length - 1].created_at || 0;
        return lb - la;
      });
      return beds.map(bed => ({ bed, messages: byBed[bed] }));
    }
    function getCurrentNurseName() {
      const el = document.getElementById('nurse_name_input');
      const v = (el && el.value || '').trim();
      try { window.localStorage.setItem('medicine_nurse_name', v); } catch (_) {}
      return v;
    }
    function saveActiveDraft() {
      // 把当前聚焦中的 textarea 内容回写到 draft, 避免刷新时丢
      const ta = document.getElementById('im_reply_textarea');
      if (ta && selectedBed) replyDraftByBed[selectedBed] = ta.value;
    }
    function isNursePendingMessage(m) {
      return Boolean(m && (m.sender === 'patient' || m.sender === 'system') && !m.read_by_nurse);
    }
    function updateMessagesTabBadge(items = latestPatientMessages) {
      const badgeEl = document.getElementById('messages-tab-badge');
      if (!badgeEl) return;
      const count = (Array.isArray(items) ? items : []).filter(isNursePendingMessage).length;
      badgeEl.textContent = count > 99 ? '99+' : String(count);
      badgeEl.hidden = count <= 0;
      badgeEl.style.display = count > 0 ? '' : 'none';
    }

    function getMedicationReviewPatients(batch = latestDeliveryBatch) {
      const rows = [];
      const seen = new Set();
      ((batch && batch.stops) || []).forEach(stop => {
        (stop.patients || []).forEach(patient => {
          const medications = Array.isArray(patient.medications) ? patient.medications : [];
          const reviewItems = medications.filter(item => item.review_required);
          const hasReview = Boolean(patient.medication_review_required || reviewItems.length);
          if (!hasReview) return;
          const key = patient.patient_id || patient.bed_no || `${stop.target_station || ''}:${patient.patient_name || ''}`;
          if (seen.has(key)) return;
          seen.add(key);
          rows.push({
            key,
            patient_id: patient.patient_id || '',
            bed_no: patient.bed_no || '-',
            patient_name: patient.patient_name || '-',
            ward_name: stop.display_name || patient.ward_name || stop.target_station || '-',
            medication_count: reviewItems.length || medications.length || 0,
          });
        });
      });
      return rows;
    }

    function countMedicationReviewPatients(batch = latestDeliveryBatch) {
      return getMedicationReviewPatients(batch).length;
    }

    function locateDemoReviewPatient(options = {}) {
      switchDashboardTab('batch');
      const list = document.getElementById('batch_stops');
      const target = document.querySelector('.batch-patient.review') || list;
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        if (target.classList && target.classList.contains('batch-patient')) {
          document.querySelectorAll('.batch-patient.demo-focus').forEach(item => item.classList.remove('demo-focus'));
          target.classList.add('demo-focus');
          window.setTimeout(() => target.classList.remove('demo-focus'), 2800);
        }
      }
      const result = document.getElementById('batch_action_result');
      if (result) {
        const pendingPatients = getMedicationReviewPatients(latestDeliveryBatch);
        const pending = pendingPatients.length;
        const first = pendingPatients[0] || {};
        const targetText = pending > 0 ? `${first.bed_no || '-'} ${first.patient_name || '-'}\uff0c${first.medication_count || 0} \u9879\u836f\u54c1` : '';
        result.textContent = pending > 0
          ? (options.afterGenerate
            ? `\u5df2\u751f\u6210\u5f85\u590d\u6838\uff1a${targetText}\uff0c\u5df2\u81ea\u52a8\u5b9a\u4f4d\u3002\u8bf7\u9009\u62e9\u590d\u6838\u901a\u8fc7\u6216\u9000\u56de\u836f\u623f\u3002`
            : `\u5df2\u5b9a\u4f4d\u5f85\u590d\u6838\uff1a${targetText}\uff0c\u8bf7\u5728\u5361\u7247\u4e2d\u9009\u62e9\u590d\u6838\u901a\u8fc7\u6216\u9000\u56de\u836f\u623f\u3002`)
          : '\u5f53\u524d\u6ca1\u6709\u5f85\u590d\u6838\u75c5\u4eba\uff0c\u8bf7\u5148\u70b9\u51fb\u4e00\u952e\u590d\u6838\u6f14\u793a\u3002';
        result.style.color = pending > 0 ? 'var(--ok)' : 'var(--muted)';
      }
    }

    function getFeedbackPatients(batch = latestDeliveryBatch) {
      const items = [];
      (batch?.stops || []).forEach(stop => {
        (stop.patients || []).forEach(patient => {
          const bedNo = patient.bed_no || '';
          const ovr = bedNo ? latestPatientStatusOverrides[bedNo] : null;
          const medications = patient.medications || [];
          const hasRejected = Boolean(
            patient.patient_status === 'PATIENT_REJECTED'
            || ovr?.status === 'rejected'
            || medications.some(item => item.exception === 'patient_rejected')
          );
          const hasReview = Boolean(
            patient.medication_review_required
            || patient.patient_status === 'WAITING_MEDICATION_REVIEW'
            || ovr?.status === 'review'
            || medications.some(item => item.review_required)
          );
          if (hasRejected || hasReview) {
            items.push({ patient, stop, type: hasRejected ? 'rejected' : 'review' });
          }
        });
      });
      return items;
    }

    function locateFeedbackPatient() {
      switchDashboardTab('batch');
      const feedback = getFeedbackPatients(latestDeliveryBatch);
      const first = feedback[0] || null;
      const targetPatientId = first?.patient?.patient_id ? String(first.patient.patient_id).replace(/[^a-zA-Z0-9_-]/g, '_') : '';
      const target = (targetPatientId ? document.querySelector(`[data-patient-dom-id="${targetPatientId}"]`) : null)
        || document.querySelector('.batch-patient.rejected')
        || document.querySelector('.batch-patient.review');
      const result = document.getElementById('batch_action_result');
      if (!feedback.length || !target) {
        if (result) {
          result.textContent = '当前没有病人反馈问题或待复核病人。';
          result.style.color = 'var(--muted)';
        }
        return;
      }
      target.scrollIntoView({ behavior: 'smooth', block: 'center' });
      document.querySelectorAll('.batch-patient.feedback-focus').forEach(item => item.classList.remove('feedback-focus'));
      target.classList.add('feedback-focus');
      window.setTimeout(() => target.classList.remove('feedback-focus'), 3200);
      if (result) {
        const kind = first.type === 'rejected' ? '反馈问题' : '待用药复核';
        result.textContent = `已定位${kind}：${first.patient.bed_no || '-'} ${first.patient.patient_name || '-'}，共 ${feedback.length} 人需处理。`;
        result.style.color = first.type === 'rejected' ? 'var(--danger)' : 'var(--warn)';
      }
    }

    function getCurrentDemoReviewPatient() {
      const patients = getMedicationReviewPatients(latestDeliveryBatch);
      return patients[0] || null;
    }

    function setDemoReviewActionMessage(message, ok = false) {
      const result = document.getElementById('batch_action_result');
      if (!result) return;
      result.textContent = message;
      result.style.color = ok ? 'var(--ok)' : 'var(--muted)';
    }

    async function continueCurrentDemoReview() {
      const patient = getCurrentDemoReviewPatient();
      if (!patient || !patient.patient_id) {
        setDemoReviewActionMessage('\u5f53\u524d\u6ca1\u6709\u5f85\u590d\u6838\u75c5\u4eba\uff0c\u8bf7\u5148\u70b9\u51fb\u4e00\u952e\u590d\u6838\u6f14\u793a\u3002');
        return;
      }
      await continuePatientMedicationReview(patient.patient_id);
    }

    async function returnCurrentDemoReview() {
      const patient = getCurrentDemoReviewPatient();
      if (!patient || !patient.patient_id) {
        setDemoReviewActionMessage('\u5f53\u524d\u6ca1\u6709\u5f85\u590d\u6838\u75c5\u4eba\uff0c\u8bf7\u5148\u70b9\u51fb\u4e00\u952e\u590d\u6838\u6f14\u793a\u3002');
        return;
      }
      await returnPatientMedicationReview(patient.patient_id);
    }

    function openDemoReviewReport() {
      switchDashboardTab('report');
      const filter = document.getElementById('report_status_filter');
      if (filter) filter.value = 'all';
      renderDeliveryReport();
      const target = document.getElementById('medication_review_report') || document.querySelector('[data-page="report"]');
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        target.classList.add('report-focus');
        window.setTimeout(() => target.classList.remove('report-focus'), 2600);
      }
    }

    async function resetDemoReviewScenario() {
      try {
        if (!confirmCriticalAction(
          '\u786e\u8ba4\u91cd\u7f6e\u590d\u6838\u6f14\u793a\uff1f',
          '\u8fd9\u4f1a\u65b0\u5efa\u4e00\u4e2a\u5e72\u51c0\u7684\u6f14\u793a\u6279\u6b21\uff0c\u7528\u4e8e\u91cd\u590d\u6d4b\u8bd5\u201c\u751f\u6210\u2014\u590d\u6838\u2014\u62a5\u544a\u201d\u95ed\u73af\u3002'
        )) return;
        const data = await api('/api/delivery_batch/demo_review_reset', {
          method: 'POST',
          body: JSON.stringify({ operator_id: 'web_operator' }),
        });
        updateDeliveryBatch(data.batch || data);
        updateDemoReviewGuide(latestDeliveryBatch);
        renderDeliveryReport();
        const auditFilter = document.getElementById('batch_audit_filter');
        if (auditFilter) {
          auditFilter.value = 'medication_review';
          latestAuditFilter = 'medication_review';
          renderBatchAudit((latestDeliveryBatch && latestDeliveryBatch.audit_records) || []);
        }
        const result = document.getElementById('batch_action_result');
        if (result) {
          result.textContent = data.message || '\u5df2\u91cd\u7f6e\u590d\u6838\u6f14\u793a\u3002';
          result.style.color = data.ok === false ? 'var(--danger)' : 'var(--ok)';
        }
        log(data.message || '\u5df2\u91cd\u7f6e\u590d\u6838\u6f14\u793a');
      } catch (error) {
        const result = document.getElementById('batch_action_result');
        if (result) {
          result.textContent = `\u91cd\u7f6e\u590d\u6838\u6f14\u793a\u5931\u8d25\uff1a${error.message}`;
          result.style.color = 'var(--danger)';
        }
        log(`\u91cd\u7f6e\u590d\u6838\u6f14\u793a\u5931\u8d25\uff1a${error.message}`);
      }
    }

    function updateDemoReviewGuide(batch = latestDeliveryBatch) {
      const statusEl = document.getElementById('demo_review_status');
      const stepGenerate = document.getElementById('demo_step_generate');
      const stepHandle = document.getElementById('demo_step_handle');
      const stepReport = document.getElementById('demo_step_report');
      if (!statusEl || !stepGenerate || !stepHandle || !stepReport) return;
      const targetEl = document.getElementById('demo_review_target');
      const pendingPatients = getMedicationReviewPatients(batch);
      const pendingCount = pendingPatients.length;
      const audit = Array.isArray(batch?.audit_records) ? batch.audit_records : [];
      const hasHandled = audit.some(record => ['patient_medication_review_continue', 'patient_medication_review_return'].includes(record.event));
      [stepGenerate, stepHandle, stepReport].forEach(step => step.classList.remove('active', 'done'));
      if (pendingCount > 0) {
        const first = pendingPatients[0];
        const more = pendingCount > 1 ? `\uff0c\u8fd8\u6709 ${pendingCount - 1} \u4eba` : '';
        statusEl.textContent = `\u5f85\u62a4\u58eb\u5904\u7406 ${pendingCount} \u4eba`;
        if (targetEl) targetEl.innerHTML = `<strong>\u5f53\u524d\u5f85\u590d\u6838\uff1a</strong>${escapeHtml(first.bed_no || '-')} ${escapeHtml(first.patient_name || '-')}\uff0c${first.medication_count || 0} \u9879\u836f\u54c1${more}`;
        stepGenerate.classList.add('done');
        stepHandle.classList.add('active');
        stepReport.classList.toggle('done', hasHandled);
        return;
      }
      if (hasHandled) {
        statusEl.textContent = '\u5df2\u6709\u590d\u6838\u7559\u75d5';
        if (targetEl) targetEl.innerHTML = '<strong>\u590d\u6838\u7ed3\u679c\uff1a</strong>\u5df2\u6709\u5904\u7406\u8bb0\u5f55\uff0c\u53ef\u70b9\u51fb\u201c\u67e5\u770b\u590d\u6838\u62a5\u544a\u201d\u786e\u8ba4\u7559\u75d5\u3002';
        stepGenerate.classList.add('done');
        stepHandle.classList.add('done');
        stepReport.classList.add('active');
        return;
      }
      statusEl.textContent = '\u5f85\u751f\u6210';
      if (targetEl) targetEl.innerHTML = '<strong>\u5f53\u524d\u5f85\u590d\u6838\uff1a</strong>\u6682\u65e0\uff0c\u8bf7\u5148\u70b9\u51fb\u201c\u4e00\u952e\u590d\u6838\u6f14\u793a\u201d\u3002';
      stepGenerate.classList.add('active');
    }

    function updateMedicationReviewTabBadge(batch = latestDeliveryBatch) {
      const badgeEl = document.getElementById('review-tab-badge');
      const hintEl = document.getElementById('review-tab-hint');
      const tabEl = document.querySelector('.tab-button[data-tab="batch"]');
      if (!badgeEl) return;
      const count = countMedicationReviewPatients(batch);
      badgeEl.textContent = count > 99 ? '99+' : String(count);
      badgeEl.hidden = count <= 0;
      badgeEl.style.display = count > 0 ? '' : 'none';
      if (tabEl) tabEl.classList.toggle('has-review-alert', count > 0);
      if (hintEl) {
        hintEl.textContent = count > 0
          ? `${count} 人待用药复核`
          : '批次 / 装药 / 推进';
      }
    }
    function buildReplyComposerHtml(threadBed, bedLabel, quickRepliesHtml) {
      const draft = escapeHtml(replyDraftByBed[threadBed] || '');
      return `
        <div class="im-main-quick">${quickRepliesHtml}</div>
        <div class="im-main-input">
          <textarea id="im_reply_textarea" placeholder="回复床位 ${bedLabel} 的病人, 支持回车换行, Ctrl/Cmd+Enter 直接发送">${draft}</textarea>
          <div class="im-main-input-bar">
            <span class="hint">Ctrl/Cmd + Enter 直接发送 · 病人端 3 秒内自动收到</span>
            <button type="button" class="primary" id="im_send_reply_btn">发送回复</button>
          </div>
        </div>
      `;
    }
    function renderPatientMessages() {
      saveActiveDraft();
      const sidebarEl = document.getElementById('messages_sidebar_list');
      const sidebarHintEl = document.getElementById('messages_sidebar_hint');
      const hintEl = document.getElementById('messages_count_hint');
      const badgeEl = document.getElementById('messages-tab-badge');
      const items = Array.isArray(latestPatientMessages) ? latestPatientMessages : [];
      const unreadPatientMsgs = items.filter(isNursePendingMessage);
      const unreadCount = unreadPatientMsgs.length;
      const threads = groupMessagesByBed(items);
      const threadsWithUnread = threads.filter(t =>
        t.messages.some(isNursePendingMessage)
      ).length;
      if (hintEl) {
        hintEl.textContent = `共 ${threads.length} 个会话 / 未处理 ${threadsWithUnread} / 未读病人消息 ${unreadCount}`;
      }
      if (sidebarHintEl) {
        sidebarHintEl.textContent = threads.length ? String(threads.length) : '0';
      }
      updateMessagesTabBadge(items);
      // 左侧床位列表
      if (sidebarEl) {
        if (threads.length === 0) {
          sidebarEl.innerHTML = '<div class="im-sidebar-empty">暂无病人咨询</div>';
        } else {
          sidebarEl.innerHTML = threads.map(thread => {
            const bed = escapeHtml(thread.bed);
            const last = thread.messages[thread.messages.length - 1] || {};
            const lastText = (last.content || '').replace(/\s+/g, ' ');
            let snippetPrefix = '';
            if (last.sender === 'nurse') snippetPrefix = '[我] ';
            else if (last.sender === 'system') snippetPrefix = '[系统] ';
            const snippetRaw = snippetPrefix + lastText;
            const snippet = escapeHtml(snippetRaw.length > 40 ? snippetRaw.slice(0, 40) + '…' : snippetRaw);
            const tStr = formatSidebarTime(last.created_at);
            const unreadInThread = thread.messages.filter(isNursePendingMessage).length;
            const hasSafetyRisk = getThreadSafetyMessages(thread).length > 0;
            const isActive = thread.bed === selectedBed ? 'active' : '';
            const hasUnread = unreadInThread > 0 ? 'has-unread' : '';
            const riskClass = hasSafetyRisk ? 'has-risk' : '';
            const unreadHtml = unreadInThread > 0
              ? `<span class="im-thread-unread">${unreadInThread}</span>`
              : '';
            const riskHtml = hasSafetyRisk ? '<div class="im-thread-risk">\u26a0 \u7528\u836f\u6838\u5bf9</div>' : '';
            const avatarText = String(thread.bed).slice(0, 3);
            return `<div class="im-thread-item ${isActive} ${hasUnread} ${riskClass}" data-thread-bed="${bed}">
              <div class="im-thread-avatar">${escapeHtml(avatarText)}</div>
              <div class="im-thread-main">
                <div class="im-thread-bed">\u5e8a\u4f4d ${bed}</div>
                <div class="im-thread-snippet">${snippet}</div>
                ${riskHtml}
              </div>
              <div class="im-thread-side">
                <div class="im-thread-time">${escapeHtml(tStr)}</div>
                ${unreadHtml}
              </div>
            </div>`;
          }).join('');
        }
      }
      // 若选中的床位已经不存在 (例如被清空), 取消选中
      if (selectedBed && !threads.some(t => t.bed === selectedBed)) {
        selectedBed = null;
      }
      renderMainPanel(threads);
    }
    function renderMainPanel(threads) {
      const mainEl = document.getElementById('messages_main_panel');
      if (!mainEl) return;
      if (!selectedBed) {
        mainEl.innerHTML = '<div class="im-main-empty" id="messages_main_empty">从左侧选一个床位开始对话</div>';
        return;
      }
      const thread = threads.find(t => t.bed === selectedBed);
      if (!thread) {
        mainEl.innerHTML = '<div class="im-main-empty">该会话已无消息</div>';
        return;
      }
      const bed = escapeHtml(thread.bed);
      let lastDeliveryId = '';
      for (let i = thread.messages.length - 1; i >= 0; i--) {
        if (thread.messages[i].delivery_id) { lastDeliveryId = thread.messages[i].delivery_id; break; }
      }
      const dlvHtml = lastDeliveryId
        ? `<span class="delivery-id">${escapeHtml(lastDeliveryId)}</span>`
        : '';
      const unreadInThread = thread.messages.filter(isNursePendingMessage).length;
      const safetyMessages = getThreadSafetyMessages(thread);
      const hasSafetyRisk = safetyMessages.length > 0;
      const unreadPill = unreadInThread > 0
        ? `<span class="unread-pill">\u672a\u5904\u7406 ${unreadInThread}</span>`
        : '';
      const safetyPill = hasSafetyRisk ? '<span class="unread-pill" style="background:#f97316">\u7528\u836f\u6838\u5bf9</span>' : '';
      const nurseCount = thread.messages.filter(m => m.sender === 'nurse').length;
      const patientCount = thread.messages.filter(m => m.sender === 'patient').length;
      const bubblesHtml = thread.messages.map(m => {
        let cls;
        if (m.sender === 'nurse') cls = 'nurse';
        else if (m.sender === 'system') cls = 'system';
        else cls = 'patient';
        const isSystemAlert = m.sender === 'system' && /\u53cd\u9988|\u62d2\u7edd|\u26a0/.test(m.content || '');
        const isRiskMessage = isMedicationSafetyMessage(m);
        const bubbleExtra = isRiskMessage
          ? 'risk'
          : (m.sender === 'patient' && !m.read_by_nurse ? 'unread' : (isSystemAlert ? 'alert' : ''));
        const riskLabel = isRiskMessage ? '<div class="msg-risk-label">\u26a0 \u7528\u836f\u6838\u5bf9</div>' : '';
        const dt = formatMessageTime(m.created_at);
        let senderLabel;
        if (m.sender === 'nurse') senderLabel = m.nurse_name ? `${escapeHtml(m.nurse_name)} (\u533b\u62a4)` : '\u533b\u62a4';
        else if (m.sender === 'system') senderLabel = '\u7cfb\u7edf';
        else senderLabel = '\u75c5\u4eba';
        return `<div class="msg-row ${cls}">
          <div>
            <div class="msg-bubble ${bubbleExtra}">${riskLabel}${escapeHtml(m.content || '')}</div>
            <div class="msg-meta">${senderLabel} \u00b7 ${dt}</div>
          </div>
        </div>`;
      }).join('');
      const quickReplyItems = hasSafetyRisk
        ? NURSE_SAFETY_REPLIES.map(q => ({ text: q, risk: true })).concat(NURSE_QUICK_REPLIES.map(q => ({ text: q, risk: false })))
        : NURSE_QUICK_REPLIES.map(q => ({ text: q, risk: false }));
      const quickRepliesHtml = quickReplyItems.map(item =>
        `<button type="button" class="${item.risk ? 'risk-reply' : ''}" data-quick="${escapeHtml(item.text)}">${escapeHtml(item.text)}</button>`
      ).join('');
      const previousBed = mainEl.getAttribute('data-active-bed') || '';
      const sameBed = previousBed === thread.bed;
      const headerHtml = `
        <div class="im-main-head">
          <span class="bed">床位 ${bed}</span>
          ${dlvHtml}
          ${unreadPill}
          ${safetyPill}
          <span class="meta">\u75c5\u4eba ${patientCount} \u6761 / \u6211\u65b9 ${nurseCount} \u6761</span>
        </div>`;
      if (sameBed && document.getElementById('im_reply_textarea')) {
        const header = mainEl.querySelector('.im-main-head');
        const body = document.getElementById('im_main_body');
        const quick = mainEl.querySelector('.im-main-quick');
        if (header) header.outerHTML = headerHtml;
        if (body) body.innerHTML = bubblesHtml;
        if (quick) quick.innerHTML = quickRepliesHtml;
      } else {
        mainEl.innerHTML = `${headerHtml}
          <div class="im-main-body" id="im_main_body">${bubblesHtml}</div>
          ${buildReplyComposerHtml(thread.bed, bed, quickRepliesHtml)}`;
        mainEl.setAttribute('data-active-bed', thread.bed);
      }
      const body = document.getElementById('im_main_body');
      if (body) body.scrollTop = body.scrollHeight;
    }
    async function refreshPatientMessages() {
      try {
        const data = await api('/api/patient_messages');
        latestPatientMessages = Array.isArray(data?.messages) ? data.messages : [];
        renderPatientMessages();
        renderExceptionCenter(latestDeliveryBatch);
      } catch (error) {
        console.warn('refreshPatientMessages 失败:', error?.message || error);
      }
    }
    async function sendNurseReply(bed) {
      if (!bed) return;
      const ta = document.getElementById('im_reply_textarea');
      if (!ta) return;
      const content = (ta.value || '').trim();
      if (!content) {
        log('请输入回复内容');
        return;
      }
      const nurse_name = getCurrentNurseName();
      const thread = latestPatientMessages.filter(m => m.bed === bed);
      let delivery_id = '';
      for (let i = thread.length - 1; i >= 0; i--) {
        if (thread[i].delivery_id) { delivery_id = thread[i].delivery_id; break; }
      }
      try {
        const resp = await api('/api/patient_messages/reply', {
          method: 'POST',
          body: JSON.stringify({ bed, content, delivery_id, nurse_name }),
        });
        if (resp && resp.message) {
          latestPatientMessages.push(resp.message);
        }
        if (resp && resp.batch) updateDeliveryBatch(resp.batch);
        replyDraftByBed[bed] = '';
        // 立刻清空 DOM 上的 textarea, 避免 renderPatientMessages -> saveActiveDraft
        // 把旧内容又写回 draft
        const taNow = document.getElementById('im_reply_textarea');
        if (taNow) taNow.value = '';
        for (const m of latestPatientMessages) {
          if (m.bed === bed && (m.sender === 'patient' || m.sender === 'system')) m.read_by_nurse = true;
        }
        renderPatientMessages();
      } catch (error) {
        log(`回复失败: ${error.message}`);
      }
    }
    async function markSelectedPatientThreadRead(bed) {
      if (!bed || markingNurseReadBed === bed) return;
      const hasUnread = latestPatientMessages.some(m =>
        m.bed === bed && isNursePendingMessage(m)
      );
      if (!hasUnread) return;
      markingNurseReadBed = bed;
      latestPatientMessages.forEach(m => {
        if (m.bed === bed && (m.sender === 'patient' || m.sender === 'system')) m.read_by_nurse = true;
      });
      updateMessagesTabBadge();
      renderPatientMessages();
      try {
        const data = await api('/api/patient_messages/read_all', {
          method: 'POST',
          body: JSON.stringify({ bed, nurse_name: getCurrentNurseName() }),
        });
        if (data?.batch) updateDeliveryBatch(data.batch);
        await refreshPatientMessages();
      } catch (error) {
        log(`标记会话已读失败: ${error.message}`);
      } finally {
        markingNurseReadBed = '';
      }
    }
    async function markAllPatientMessagesRead() {
      try {
        const data = await api('/api/patient_messages/read_all', {
          method: 'POST',
          body: JSON.stringify({ nurse_name: getCurrentNurseName() }),
        });
        if (data?.batch) updateDeliveryBatch(data.batch);
        latestPatientMessages.forEach(m => {
          if (m.sender === 'patient' || m.sender === 'system') m.read_by_nurse = true;
        });
        renderPatientMessages();
      } catch (error) {
        log(`全部已读失败: ${error.message}`);
      }
    }
    document.addEventListener('click', (event) => {
      // 左侧选床位
      const item = event.target.closest('.im-thread-item[data-thread-bed]');
      if (item) {
        const bed = item.getAttribute('data-thread-bed');
        if (bed) {
          saveActiveDraft();
          selectedBed = bed;
          renderPatientMessages();
          markSelectedPatientThreadRead(bed);
        }
        return;
      }
      // 发送回复
      if (event.target.closest('#im_send_reply_btn')) {
        sendNurseReply(selectedBed);
        return;
      }
      // 快捷回复 chip
      const quickBtn = event.target.closest('.im-main-quick button[data-quick]');
      if (quickBtn) {
        const txt = quickBtn.getAttribute('data-quick');
        const ta = document.getElementById('im_reply_textarea');
        if (ta && selectedBed) {
          ta.value = ta.value ? `${ta.value}\n${txt}` : txt;
          ta.focus();
          replyDraftByBed[selectedBed] = ta.value;
        }
      }
    });
    document.addEventListener('keydown', (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        if (event.target && event.target.id === 'im_reply_textarea') {
          event.preventDefault();
          sendNurseReply(selectedBed);
        }
      }
    });
    document.addEventListener('input', (event) => {
      if (event.target && event.target.id === 'im_reply_textarea' && selectedBed) {
        replyDraftByBed[selectedBed] = event.target.value;
      }
    });
    const messagesRefreshBtn = document.getElementById('messages_refresh');
    if (messagesRefreshBtn) messagesRefreshBtn.addEventListener('click', refreshPatientMessages);
    const messagesMarkAllBtn = document.getElementById('messages_mark_all');
    if (messagesMarkAllBtn) messagesMarkAllBtn.addEventListener('click', markAllPatientMessagesRead);
    // 加载护士姓名持久化
    const nurseNameInput = document.getElementById('nurse_name_input');
    if (nurseNameInput) {
      try {
        nurseNameInput.value = window.localStorage.getItem('medicine_nurse_name') || '';
      } catch (_) {}
      nurseNameInput.addEventListener('change', getCurrentNurseName);
      nurseNameInput.addEventListener('blur', getCurrentNurseName);
    }

    function stationDisplayName(stationId) {
      const names = {
        pharmacy: '药房',
        ward_a: 'A病房',
        ward_b: 'B病房',
        ward_c: 'C病房',
        nurse_station: '护士站',
      };
      return names[stationId] || stationId || '-';
    }

    function batchStatusClass(status) {
      if (['COMPLETED', 'BATCH_COMPLETED'].includes(status)) {
        return 'ok';
      }
      if (['NAVIGATING_TO_WARD', 'WARD_HANDOVER', 'RETURNING_TO_PHARMACY'].includes(status)) {
        return 'info';
      }
      return 'warn';
    }

    function batchStatusText(status) {
      const labels = {
        WAITING_LOAD_CONFIRMATION: '待药师装药核验',
        READY_TO_DEPART: '装药完成待出发',
        NAVIGATING_TO_WARD: '前往病房',
        WARD_HANDOVER: '床旁交付核验',
        WARD_COMPLETED: '病房完成',
        RETURNING_TO_PHARMACY: '返回药房',
        BATCH_COMPLETED: '批次完成',
      };
      return labels[status] || status || '-';
    }

    function batchReceiptStats(batch) {
      const stats = { total: 0, signed: 0, pending: 0, rejected: 0, review: 0 };
      (batch?.stops || []).forEach(stop => {
        (stop.patients || []).forEach(patient => {
          stats.total += 1;
          const medications = patient.medications || [];
          const bedNo = patient.bed_no || '';
          const override = bedNo ? latestPatientStatusOverrides[bedNo] : null;
          const hasSigned = Boolean(
            patient.patient_signed_at
            || override?.status === 'confirmed'
            || medications.some(item => item.patient_signed)
          );
          const hasRejected = Boolean(
            patient.patient_status === 'PATIENT_REJECTED'
            || override?.status === 'rejected'
            || medications.some(item => item.exception === 'patient_rejected')
          );
          const hasReview = Boolean(
            patient.medication_review_required
            || patient.patient_status === 'WAITING_MEDICATION_REVIEW'
            || override?.status === 'review'
            || medications.some(item => item.review_required)
          );
          if (hasRejected) {
            stats.rejected += 1;
          } else if (hasReview) {
            stats.review += 1;
          } else if (hasSigned) {
            stats.signed += 1;
          } else {
            stats.pending += 1;
          }
        });
      });
      return stats;
    }

    function receiptStatsText(stats) {
      if (!stats || !stats.total) return '-';
      const parts = [
        `已签收 ${stats.signed}/${stats.total}`,
        `待签收 ${stats.pending}`,
      ];
      if (stats.rejected) parts.push(`反馈问题 ${stats.rejected}`);
      if (stats.review) parts.push(`待复核 ${stats.review}`);
      return parts.join('，');
    }

    let exceptionCenterFilter = 'all';
    let latestExceptionResolutionSummary = null;


    function countBatchExceptions(batch = latestDeliveryBatch) {
      return collectBatchExceptions(batch).length;
    }

    function latestAuditSummary(batch = latestDeliveryBatch) {
      const records = Array.isArray(batch?.audit_records) ? batch.audit_records : [];
      if (!records.length) return null;
      const record = records[records.length - 1];
      const extra = record.extra || {};
      return {
        event: record.event || '',
        time: record.timestamp || record.time || '',
        operator: extra.operator_id || extra.operator || record.operator_id || '',
        message: batchAuditMessageText(record),
      };
    }

    function buildResolutionSummary(actionLabel, beforeCount, afterCount, batch) {
      const latest = latestAuditSummary(batch);
      const delta = Math.max(0, Number(beforeCount || 0) - Number(afterCount || 0));
      return {
        actionLabel,
        beforeCount: Number(beforeCount || 0),
        afterCount: Number(afterCount || 0),
        delta,
        time: latest?.time || new Date().toLocaleString('zh-CN', { hour12: false }),
        operator: latest?.operator || 'web_operator',
        auditMessage: latest?.message || '',
      };
    }

    function resolutionSummaryText(summary) {
      if (!summary) return '';
      const deltaText = summary.delta > 0
        ? `\u51cf\u5c11 ${summary.delta} \u9879`
        : '\u5df2\u5904\u7406\uff0c\u7b49\u5f85\u72b6\u6001\u5237\u65b0';
      const operator = summary.operator ? ` / \u5904\u7406\u4eba\uff1a${summary.operator}` : '';
      const time = summary.time ? ` / ${summary.time}` : '';
      return `${summary.actionLabel}\uff1a${summary.beforeCount} \u2192 ${summary.afterCount}\uff0c${deltaText}${operator}${time}`;
    }

    function classifyExceptionSeverity(type) {
      if (['patient_rejected', 'patient_absent', 'medication_exception', 'scan_mismatch', 'pending_message_risk'].includes(type)) return 'danger';
      if (['medication_review', 'timeout', 'medication_return', 'pending_message'].includes(type)) return 'warn';
      return 'info';
    }

    function exceptionTypeLabel(type) {
      const labels = {
        patient_rejected: '\u75c5\u4eba\u53cd\u9988',
        medication_review: '\u5f85\u590d\u6838',
        patient_absent: '\u75c5\u4eba\u4e0d\u5728',
        timeout: '\u672a\u7b7e\u6536',
        medication_exception: '\u836f\u54c1\u5f02\u5e38',
        medication_return: '\u836f\u54c1\u56de\u6536',
        scan_mismatch: '\u8bc6\u522b\u4e0d\u5339\u914d',
        pending_message: '\u75c5\u4eba\u54a8\u8be2',
        pending_message_risk: '\u7528\u836f\u98ce\u9669\u54a8\u8be2',
      };
      return labels[type] || '\u5f02\u5e38';
    }


    function auditFilterForExceptionType(type) {
      const mapping = {
        patient_rejected: 'patient_rejected',
        medication_review: 'medication_review',
        patient_absent: 'patient_absent',
        timeout: 'all',
        medication_exception: 'medication_exception',
        medication_return: 'medication_return',
        scan_mismatch: 'fail',
        pending_message: 'patient_message',
        pending_message_risk: 'patient_message',
      };
      return mapping[type] || 'all';
    }

    function auditEventsForExceptionType(type) {
      const mapping = {
        patient_rejected: ['patient_rejected', 'patient_medication_review_required'],
        medication_review: ['patient_medication_review_required', 'patient_medication_review_continue', 'patient_medication_review_return'],
        patient_absent: ['patient_absent'],
        timeout: ['patient_absent', 'patient_rejected'],
        medication_exception: ['medication_exception', 'dispense_scan', 'load_scan'],
        medication_return: ['medication_return'],
        scan_mismatch: ['dispense_scan', 'load_scan', 'medication_exception'],
        pending_message: ['patient_message_reply', 'patient_message_read'],
        pending_message_risk: ['patient_message_reply', 'patient_message_read', 'patient_medication_review_required'],
      };
      return mapping[type] || [];
    }

    function findAuditRecordForException(type, patientId, medicationId, bedNo) {
      const records = Array.isArray(latestDeliveryBatch?.audit_records) ? latestDeliveryBatch.audit_records : [];
      const events = auditEventsForExceptionType(type);
      const targetPatient = String(patientId || '').trim();
      const targetMedication = String(medicationId || '').trim();
      const targetBed = String(bedNo || '').trim();
      const matches = records.filter(record => {
        const extra = record.extra || {};
        if (events.length && !events.includes(record.event)) return false;
        if (targetMedication && String(extra.medication_id || '') === targetMedication) return true;
        if (targetPatient && String(extra.patient_id || '') === targetPatient) return true;
        if (targetBed && String(extra.bed_no || extra.bed || '') === targetBed) return true;
        const text = batchAuditMessageText(record);
        return Boolean(targetBed && text.includes(targetBed));
      });
      return matches.length ? matches[matches.length - 1] : null;
    }

    function getPatientOverride(patient) {
      const bedNo = patient?.bed_no || '';
      return bedNo ? latestPatientStatusOverrides[bedNo] : null;
    }

    function buildExceptionActions(item) {
      const patientId = escapeHtml(item.patient_id || '');
      const medicationId = escapeHtml(item.medication_id || '');
      const bed = escapeHtml(item.bed_no || '');
      const actions = [];
      if (item.patient_id) actions.push(`<button class="secondary small-button" type="button" onclick="locateExceptionTarget('${patientId}')">\u5b9a\u4f4d\u75c5\u4eba</button>`);
      if (item.type === 'patient_rejected' || item.type === 'medication_review') {
        if (item.patient_id) {
          actions.push(`<button class="secondary small-button" type="button" onclick="continuePatientMedicationReview('${patientId}')">\u590d\u6838\u901a\u8fc7</button>`);
          actions.push(`<button class="secondary small-button danger-action" type="button" onclick="returnPatientMedicationReview('${patientId}')">\u9000\u56de\u836f\u623f</button>`);
        }
      } else if (item.type === 'patient_absent' || item.type === 'timeout') {
        if (item.patient_id) {
          actions.push(`<button class="secondary small-button" type="button" onclick="retryBatchPatientException('${patientId}')">\u7a0d\u540e\u91cd\u8bd5</button>`);
          actions.push(`<button class="secondary small-button" type="button" onclick="clearBatchPatientException('${patientId}')">\u5df2\u5904\u7406</button>`);
        }
      } else if (item.type === 'medication_exception' || item.type === 'medication_return' || item.type === 'scan_mismatch') {
        if (item.medication_id) {
          actions.push(`<button class="secondary small-button" type="button" onclick="retryBatchMedicationException('${medicationId}')">\u7a0d\u540e\u91cd\u8bd5</button>`);
          actions.push(`<button class="secondary small-button" type="button" onclick="reviewBatchMedicationException('${medicationId}')">\u836f\u5e08\u590d\u6838</button>`);
          actions.push(`<button class="secondary small-button" type="button" onclick="clearBatchMedicationException('${medicationId}')">\u5df2\u5904\u7406</button>`);
        } else if (item.patient_id) {
          actions.push(`<button class="secondary small-button" type="button" onclick="reviewBatchPatientException('${patientId}')">\u836f\u5e08\u590d\u6838</button>`);
        }
      }
      actions.push(`<button class="secondary small-button" type="button" onclick="focusExceptionAudit('${escapeHtml(item.type || '')}', '${patientId}', '${medicationId}', '${bed}')">\u67e5\u770b\u7559\u75d5</button>`);
      if (bed) actions.push(`<button class="secondary small-button" type="button" onclick="openPatientConversation('${bed}')">\u8054\u7cfb\u75c5\u4eba</button>`);
      return actions.join('');
    }

    function findBatchPatientByBedNo(batch, bedNo) {
      const target = String(bedNo || '').trim();
      if (!target) return null;
      for (const stop of (batch?.stops || [])) {
        for (const patient of (stop.patients || [])) {
          if (String(patient.bed_no || '').trim() === target) return { stop, patient };
        }
      }
      return null;
    }

    function collectMessageExceptions(batch = latestDeliveryBatch) {
      const rows = [];
      const threads = groupMessagesByBed(latestPatientMessages || []);
      threads.forEach(thread => {
        const unread = thread.messages.filter(isNursePendingMessage);
        if (!unread.length) return;
        const safety = getThreadSafetyMessages(thread).filter(isNursePendingMessage);
        const latest = unread[unread.length - 1] || {};
        const found = findBatchPatientByBedNo(batch, thread.bed);
        const patient = found?.patient || {};
        const stop = found?.stop || {};
        const isRisk = safety.length > 0;
        rows.push({
          key: `message:${thread.bed}`,
          type: isRisk ? 'pending_message_risk' : 'pending_message',
          patient_id: patient.patient_id || '',
          bed_no: thread.bed || '-',
          patient_name: patient.patient_name || '-',
          ward_name: stop.display_name || patient.ward_name || stop.target_station || '-',
          reason: `${isRisk ? '\u7591\u4f3c\u7528\u836f\u98ce\u9669\uff1a' : '\u672a\u8bfb\u75c5\u4eba\u54a8\u8be2\uff1a'}${String(latest.content || '').slice(0, 80)}`,
          time: latest.created_at ? formatMessageTime(latest.created_at) : '',
          severity: classifyExceptionSeverity(isRisk ? 'pending_message_risk' : 'pending_message'),
          unread_count: unread.length,
        });
      });
      return rows;
    }

    function collectBatchExceptions(batch = latestDeliveryBatch) {
      const rows = [];
      const seen = new Set();
      const add = (item) => {
        const key = item.key || `${item.type}:${item.patient_id || item.bed_no || ''}:${item.medication_id || ''}`;
        if (seen.has(key)) return;
        seen.add(key);
        rows.push({ ...item, key, severity: item.severity || classifyExceptionSeverity(item.type) });
      };
      (batch?.stops || []).forEach(stop => {
        (stop.patients || []).forEach(patient => {
          const medications = Array.isArray(patient.medications) ? patient.medications : [];
          const ovr = getPatientOverride(patient);
          const base = { patient_id: patient.patient_id || '', bed_no: patient.bed_no || '-', patient_name: patient.patient_name || '-', ward_name: stop.display_name || patient.ward_name || stop.target_station || '-' };
          const rejectedMedication = medications.find(m => m.exception === 'patient_rejected');
          if (patient.patient_status === 'PATIENT_REJECTED' || ovr?.status === 'rejected' || rejectedMedication) {
            add({ ...base, type: 'patient_rejected', reason: (ovr && ovr.reason) || patient.patient_rejected_reason || rejectedMedication?.exception_reason || '\u75c5\u4eba\u53cd\u9988\u836f\u54c1\u6216\u4e2a\u4eba\u4fe1\u606f\u53ef\u80fd\u6709\u8bef', time: patient.patient_rejected_at || rejectedMedication?.exception_at || ovr?.timestamp || '' });
          }
          if (patient.patient_status === 'PATIENT_ABSENT' || ovr?.status === 'timeout') {
            add({ ...base, type: patient.patient_status === 'PATIENT_ABSENT' ? 'patient_absent' : 'timeout', reason: patient.patient_status === 'PATIENT_ABSENT' ? '\u75c5\u4eba\u6682\u65f6\u4e0d\u5728\u5e8a\u65c1\uff0c\u9700\u7a0d\u540e\u91cd\u8bd5\u6216\u8054\u7cfb\u62a4\u58eb' : '\u673a\u5668\u4eba\u5230\u4f4d\u8f83\u4e45\uff0c\u75c5\u4eba\u5c1a\u672a\u786e\u8ba4\u7b7e\u6536', time: ovr?.timestamp || '' });
          }
          const reviewItems = medications.filter(m => m.review_required);
          if (patient.medication_review_required || patient.patient_status === 'WAITING_MEDICATION_REVIEW' || ovr?.status === 'review' || reviewItems.length) {
            add({ ...base, type: 'medication_review', reason: (ovr && ovr.reason) || patient.medication_review_reason || '\u75c5\u4eba\u53cd\u9988\u7528\u836f\u6216\u4e2a\u4eba\u4fe1\u606f\u53ef\u80fd\u6709\u8bef\uff0c\u5f85\u62a4\u58eb/\u836f\u5e08\u590d\u6838', time: patient.medication_review_requested_at || ovr?.timestamp || '', count: reviewItems.length || medications.length || 0 });
          }
          medications.forEach(med => {
            if (med.exception && med.exception !== 'patient_rejected') {
              add({ ...base, type: String(med.exception || '').includes('mismatch') ? 'scan_mismatch' : 'medication_exception', medication_id: med.id || '', medicine_name: med.medicine_name || '-', reason: med.exception_reason || med.exception || '\u836f\u54c1\u5f02\u5e38\uff0c\u5f85\u4eba\u5de5\u5904\u7406', time: med.exception_at || '' });
            }
            if (med.returned && !med.dispensed) {
              add({ ...base, type: 'medication_return', medication_id: med.id || '', medicine_name: med.medicine_name || '-', reason: med.return_reason || '\u672a\u4ea4\u4ed8\uff0c\u5df2\u56de\u836f\u623f\u56de\u6536', time: med.returned_at || '' });
            }
          });
        });
      });
      collectMessageExceptions(batch).forEach(add);
      rows.sort((a, b) => {
        const rank = { danger: 0, warn: 1, info: 2 };
        return (rank[a.severity] ?? 9) - (rank[b.severity] ?? 9);
      });
      return rows;
    }

    function exceptionMatchesFilter(item, filter) {
      if (!filter || filter === 'all') return true;
      if (filter === 'danger') return item.severity === 'danger';
      if (filter === 'medication_exception') return ['medication_exception', 'medication_return', 'scan_mismatch'].includes(item.type);
      if (filter === 'pending_message') return ['pending_message', 'pending_message_risk'].includes(item.type);
      return item.type === filter;
    }

    function renderExceptionCenter(batch = latestDeliveryBatch) {
      const allRows = collectBatchExceptions(batch);
      const rows = allRows.filter(item => exceptionMatchesFilter(item, exceptionCenterFilter));
      const stats = batchReceiptStats(batch);
      const critical = allRows.filter(r => r.severity === 'danger').length;
      const review = allRows.filter(r => r.type === 'medication_review').length;
      const messages = allRows.filter(r => ['pending_message', 'pending_message_risk'].includes(r.type)).length;
      const setText = (id, value) => { const el = document.getElementById(id); if (el) el.textContent = String(value); };
      setText('exception_stat_critical', critical);
      setText('exception_stat_review', review);
      setText('exception_stat_pending', stats.pending || 0);
      setText('exception_stat_signed', stats.signed || 0);
      document.querySelectorAll('[data-exception-filter]').forEach(btn => btn.classList.toggle('active', btn.dataset.exceptionFilter === exceptionCenterFilter));
      const badge = document.getElementById('exception_center_badge');
      if (badge) {
        badge.textContent = `${allRows.length} \u9879`;
        badge.className = `badge ${critical ? 'FAIL' : (allRows.length ? 'WARN' : 'OK')}`;
      }
      const hint = document.getElementById('exception_center_hint');
      if (hint) {
        hint.textContent = allRows.length ? `\u9700\u5904\u7406 ${allRows.length} \u9879\uff1a\u9ad8\u4f18\u5148\u7ea7 ${critical}\uff0c\u5f85\u590d\u6838 ${review}\uff0c\u75c5\u4eba\u54a8\u8be2 ${messages}\uff0c\u5f85\u7b7e\u6536 ${stats.pending || 0}\u3002` : '\u5f53\u524d\u6ca1\u6709\u96c6\u4e2d\u5904\u7406\u9879\uff0c\u7ee7\u7eed\u5173\u6ce8\u7b7e\u6536\u548c\u914d\u9001\u8fdb\u5ea6\u3002';
      }
      const resolutionStrip = document.getElementById('exception_resolution_strip');
      const resolutionText = document.getElementById('exception_resolution_text');
      if (resolutionStrip && resolutionText) {
        const text = resolutionSummaryText(latestExceptionResolutionSummary);
        resolutionStrip.hidden = !text;
        resolutionText.textContent = text || '-';
      }
      const list = document.getElementById('exception_center_list');
      if (!list) return;
      if (!rows.length) {
        list.innerHTML = '<div class="exception-empty">\u5f53\u524d\u7b5b\u9009\u6761\u4ef6\u4e0b\u6ca1\u6709\u9700\u5904\u7406\u9879\u3002</div>';
        return;
      }
      list.innerHTML = rows.map(item => {
        const pillClass = item.severity;
        const med = item.medicine_name ? ` / ${escapeHtml(item.medicine_name)}` : '';
        const count = item.count ? ` / ${item.count} \u9879\u836f\u54c1` : (item.unread_count ? ` / ${item.unread_count} \u6761\u672a\u8bfb` : '');
        const time = item.time ? ` / ${escapeHtml(item.time)}` : '';
        return `<div class="exception-item ${pillClass}">\n          <div class="exception-item-head">\n            <div class="exception-item-title">${escapeHtml(item.bed_no || '-')} ${escapeHtml(item.patient_name || '-')}${med}<small>${escapeHtml(item.ward_name || '-')}${count}${time}</small></div>\n            <span class="exception-type-pill ${pillClass}">${escapeHtml(exceptionTypeLabel(item.type))}</span>\n          </div>\n          <div class="exception-reason">${escapeHtml(item.reason || '-')}</div>\n          <div class="exception-actions">${buildExceptionActions(item)}</div>\n        </div>`;
      }).join('');
    }


    function focusExceptionAudit(type, patientId = '', medicationId = '', bedNo = '') {
      switchDashboardTab('batch');
      const auditFilter = document.getElementById('batch_audit_filter');
      const nextFilter = auditFilterForExceptionType(type);
      if (auditFilter) {
        auditFilter.value = nextFilter;
        latestAuditFilter = nextFilter;
      }
      renderBatchAudit((latestDeliveryBatch && latestDeliveryBatch.audit_records) || []);
      const record = findAuditRecordForException(type, patientId, medicationId, bedNo);
      let target = null;
      if (record && record.__dom_id) {
        target = document.getElementById(record.__dom_id);
      }
      if (!target) {
        const selectorParts = [];
        if (patientId) selectorParts.push(`[data-audit-patient="${String(patientId).replace(/[^a-zA-Z0-9_-]/g, '_')}"]`);
        if (medicationId) selectorParts.push(`[data-audit-medication="${String(medicationId).replace(/[^a-zA-Z0-9_-]/g, '_')}"]`);
        for (const selector of selectorParts) {
          target = document.querySelector(selector);
          if (target) break;
        }
      }
      const result = document.getElementById('batch_action_result');
      if (!target) {
        if (result) {
          result.textContent = '\u67e5\u770b\u7559\u75d5\uff1a\u6682\u65e0\u76f4\u63a5\u5339\u914d\u7684\u5ba1\u8ba1\u8bb0\u5f55\uff0c\u5df2\u5207\u6362\u5230\u76f8\u5173\u7b5b\u9009\u3002';
          result.style.color = 'var(--muted)';
        }
        return;
      }
      target.scrollIntoView({ behavior: 'smooth', block: 'center' });
      document.querySelectorAll('.audit-item.audit-focus').forEach(item => item.classList.remove('audit-focus'));
      target.classList.add('audit-focus');
      window.setTimeout(() => target.classList.remove('audit-focus'), 3600);
      if (result) {
        result.textContent = '\u5df2\u5b9a\u4f4d\u5230\u76f8\u5173\u5ba1\u8ba1\u7559\u75d5\uff0c\u53ef\u6838\u5bf9\u5904\u7406\u4eba\u548c\u5904\u7406\u7ed3\u679c\u3002';
        result.style.color = 'var(--ok)';
      }
    }

    function locateExceptionTarget(patientId) {
      switchDashboardTab('batch');
      const safe = String(patientId || '').replace(/[^a-zA-Z0-9_-]/g, '_');
      const target = safe ? document.querySelector(`[data-patient-dom-id="${safe}"]`) : null;
      if (!target) {
        const result = document.getElementById('batch_action_result');
        if (result) {
          result.textContent = '\u6ca1\u6709\u627e\u5230\u5bf9\u5e94\u75c5\u4eba\u5361\u7247\uff0c\u53ef\u80fd\u5f53\u524d\u6279\u6b21\u5df2\u5237\u65b0\u3002';
          result.style.color = 'var(--muted)';
        }
        return;
      }
      target.scrollIntoView({ behavior: 'smooth', block: 'center' });
      document.querySelectorAll('.batch-patient.feedback-focus').forEach(item => item.classList.remove('feedback-focus'));
      target.classList.add('feedback-focus');
      window.setTimeout(() => target.classList.remove('feedback-focus'), 3200);
    }

    function openPatientConversation(bed) {
      const cleanBed = String(bed || '').trim();
      if (!cleanBed) return;
      selectedBed = cleanBed;
      switchDashboardTab('messages');
      renderPatientMessages();
      markSelectedPatientThreadRead(cleanBed);
    }

    function updateDeliveryBatch(batch) {
      const data = batch || {};
      latestDeliveryBatch = data;
      const summary = data.summary || {};
      const status = data.route_status || 'WAITING_LOAD_CONFIRMATION';
      const badge = document.getElementById('batch-status-badge');
      badge.textContent = batchStatusText(status);
      badge.className = `badge ${status}`;
      document.getElementById('batch_id').textContent = data.batch_id || '-';
      document.getElementById('batch_route_status').textContent = batchStatusText(status);
      document.getElementById('batch_current_station').textContent = stationDisplayName(data.current_station);
      document.getElementById('batch_stop_progress').textContent = `${summary.stop_completed_count || 0}/${summary.stop_total_count || 0}`;
      document.getElementById('batch_patient_progress').textContent = `${summary.patient_completed_count || 0}/${summary.patient_total_count || 0}`;
      const receiptEl = document.getElementById('batch_receipt_progress');
      if (receiptEl) receiptEl.textContent = receiptStatsText(batchReceiptStats(data));
      renderExceptionCenter(data);
      document.getElementById('batch_medication_progress').textContent = `装药 ${summary.medication_loaded_count || 0}/${summary.medication_total_count || 0}，交付 ${summary.medication_dispensed_count || 0}/${summary.medication_total_count || 0}`;
      document.getElementById('batch_robot_id').textContent = data.robot_id || 'R1';
      const cabinetLocked = latestChassisStatus?.cabinet_locked ?? latestChassisStatus?.medicine_cabinet_locked;
      document.getElementById('batch_cabinet_state').textContent = cabinetLocked === undefined ? '待上报' : (cabinetLocked ? '已锁定' : '未锁定');
      const audit = Array.isArray(data.audit_records) ? data.audit_records : [];
      const lastScan = [...audit].reverse().find(item => /扫码|核验|scan|verify/i.test(`${item.event || ''} ${item.message || ''}`));
      const medicationReviewEvents = ['patient_medication_review_required', 'patient_medication_review_return'];
      const lastIssue = [...audit].reverse().find(item => {
        const event = item.event || '';
        return item.result === 'fail'
          || medicationReviewEvents.includes(event)
          || /\u5f02\u5e38|\u56de\u6536|\u65e0\u4eba|\u4e0d\u5339\u914d|\u590d\u6838|\u9000\u56de|exception|absent|mismatch|review|return/i.test(`${event} ${item.message || ''}`);
      });
      document.getElementById('batch_last_scan').textContent = lastScan ? `${lastScan.message || lastScan.event || '\u6838\u9a8c\u8bb0\u5f55'} / ${lastScan.timestamp || '-'}` : '\u6682\u65e0\u8bb0\u5f55';
      document.getElementById('batch_last_issue').textContent = lastIssue ? `${batchAuditMessageText(lastIssue) || lastIssue.event || '\u5f02\u5e38\u8bb0\u5f55'} / ${lastIssue.timestamp || '-'}` : '\u6682\u65e0\u5f02\u5e38';
      updateMedicationReviewTabBadge(data);
      updateDemoReviewGuide(data);
      renderBatchRoute(data);
      renderBatchStops(data);
      updateBatchSafetyGate(data);
      renderWorkflowGuide(data);
      renderBatchClosureTimeline(data);
      updateBatchScanPreview();
      renderBatchAudit(data.audit_records || []);
      renderDeliveryReport();
      updateRuntimeStatus();
    }

    function renderBatchRoute(batch) {
      const route = batch.route || [];
      const activeStopIndex = Number(batch.active_stop_index ?? -1);
      const activeStation = activeStopIndex >= 0 && batch.stops?.[activeStopIndex] ? batch.stops[activeStopIndex].target_station : batch.current_station;
      const activeRouteIndex = Math.max(0, route.findIndex(station => station === activeStation));
      const returning = batch.route_status === 'RETURNING_TO_PHARMACY';
      document.getElementById('batch_route_steps').innerHTML = route.map(station => {
        const index = route.indexOf(station);
        const active = station === activeStation || (returning && station === 'pharmacy');
        const done = !active && index >= 0 && activeRouteIndex >= 0 && index < activeRouteIndex;
        const cls = active ? 'active' : (done ? 'done' : 'pending');
        const marker = done ? '✓' : String(index + 1);
        return `<span class="route-step ${cls}">
          <span class="route-dot">${escapeHtml(marker)}</span>
          <span class="route-label">${escapeHtml(stationDisplayName(station))}</span>
        </span>`;
      }).join('');
    }

    function renderBatchRoute(batch) {
      const route = batch.route || [];
      const activeStopIndex = Number(batch.active_stop_index ?? -1);
      const activeStation = activeStopIndex >= 0 && batch.stops?.[activeStopIndex] ? batch.stops[activeStopIndex].target_station : batch.current_station;
      const returnIndex = route.length > 1 && route[route.length - 1] === 'pharmacy' ? route.length - 1 : -1;
      const returning = batch.route_status === 'RETURNING_TO_PHARMACY';
      let activeRouteIndex = route.findIndex((station, index) => station === activeStation && index !== returnIndex);
      if (returning && returnIndex >= 0) activeRouteIndex = returnIndex;
      if (activeRouteIndex < 0) activeRouteIndex = 0;
      const el = document.getElementById('batch_route_steps');
      if (!el) return;
      el.innerHTML = route.map((station, index) => {
        const isReturn = index === returnIndex;
        const active = index === activeRouteIndex;
        const done = !active && index < activeRouteIndex;
        const stateCls = active ? 'active' : (done ? 'done' : 'pending');
        const marker = done ? '✓' : String(index + 1);
        const label = isReturn ? '返回药房' : stationDisplayName(station);
        const eta = active
          ? '当前步骤'
          : (done ? '已完成' : `预计 ${Math.max(1, (index - activeRouteIndex) * 3)} 分钟`);
        return `<span class="route-step ${stateCls}">
          <span class="route-dot">${escapeHtml(marker)}</span>
          <span class="route-label">${escapeHtml(label)}</span>
          <span class="route-eta">${escapeHtml(eta)}</span>
        </span>`;
      }).join('');
    }

    function renderBatchRoute(batch) {
      const route = Array.isArray(batch.route) ? batch.route : [];
      const activeStopIndex = Number(batch.active_stop_index ?? -1);
      const activeStation = activeStopIndex >= 0 && batch.stops?.[activeStopIndex]
        ? batch.stops[activeStopIndex].target_station
        : batch.current_station;
      const returnIndex = route.length > 1 && route[route.length - 1] === 'pharmacy' ? route.length - 1 : -1;
      const returning = batch.route_status === 'RETURNING_TO_PHARMACY';
      let activeRouteIndex = route.findIndex((station, index) => station === activeStation && index !== returnIndex);
      if (returning && returnIndex >= 0) activeRouteIndex = returnIndex;
      if (activeRouteIndex < 0) activeRouteIndex = 0;

      const el = document.getElementById('batch_route_steps');
      if (!el) return;
      el.innerHTML = route.map((station, index) => {
        const isReturn = index === returnIndex;
        const active = index === activeRouteIndex;
        const done = !active && index < activeRouteIndex;
        const stateCls = active ? 'active' : (done ? 'done' : 'pending');
        const markerHtml = done ? '&#10003;' : `<span class="route-index">${escapeHtml(String(index + 1))}</span>`;
        const label = isReturn ? '\u8fd4\u56de\u836f\u623f' : stationDisplayName(station);
        const eta = active
          ? '\u5f53\u524d\u6b65\u9aa4'
          : (done ? '\u5df2\u5b8c\u6210' : `\u9884\u8ba1 ${Math.max(1, (index - activeRouteIndex) * 3)} \u5206\u949f`);
        return `<span class="route-step ${stateCls}">
          <span class="route-dot">${markerHtml}</span>
          <span class="route-label">${escapeHtml(label)}</span>
          <span class="route-eta">${escapeHtml(eta)}</span>
        </span>`;
      }).join('');
    }

    function renderBatchRoute(batch) {
      const route = Array.isArray(batch.route) ? batch.route.slice(0, 5) : [];
      const normalizedRoute = route.length ? route : ['pharmacy', 'ward_a', 'ward_b', 'ward_c', 'pharmacy'];
      const activeStopIndex = Number(batch.active_stop_index ?? -1);
      const activeStation = activeStopIndex >= 0 && batch.stops?.[activeStopIndex]
        ? batch.stops[activeStopIndex].target_station
        : batch.current_station;
      const returnIndex = normalizedRoute.length > 1 && normalizedRoute[normalizedRoute.length - 1] === 'pharmacy'
        ? normalizedRoute.length - 1
        : -1;
      const returning = batch.route_status === 'RETURNING_TO_PHARMACY';
      let activeRouteIndex = normalizedRoute.findIndex((station, index) => station === activeStation && index !== returnIndex);
      if (returning && returnIndex >= 0) activeRouteIndex = returnIndex;
      if (activeRouteIndex < 0) activeRouteIndex = 0;

      const positions = [
        { left: 14, top: 24 },
        { left: 50, top: 24 },
        { left: 84, top: 24 },
        { left: 62, top: 72 },
        { left: 28, top: 72 },
      ];
      const pathSegments = [
        { d: 'M 14 24 L 50 24', from: 0 },
        { d: 'M 50 24 L 84 24', from: 1 },
        { d: 'M 84 24 C 94 24 94 72 62 72', from: 2 },
        { d: 'M 62 72 L 28 72', from: 3 },
      ];
      const iconMedical = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14"/><path d="M5 12h14"/></svg>';
      const iconWard = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 11h16"/><path d="M6 11V7a2 2 0 0 1 2-2h3v6"/><path d="M13 11V8h3a3 3 0 0 1 3 3v6"/><path d="M5 17h14"/><path d="M7 17v2"/><path d="M17 17v2"/></svg>';
      const pathsHtml = pathSegments.map(segment => {
        const done = segment.from < activeRouteIndex;
        return `<path class="route-path-segment ${done ? 'done' : 'pending'}" d="${segment.d}" pathLength="100"></path>`;
      }).join('');

      const el = document.getElementById('batch_route_steps');
      if (!el) return;
      const nodesHtml = normalizedRoute.map((station, index) => {
        const active = index === activeRouteIndex;
        const done = !active && index < activeRouteIndex;
        const stateCls = active ? 'active' : (done ? 'done' : 'pending');
        const isReturn = index === returnIndex;
        const label = isReturn ? '\u8fd4\u56de\u836f\u623f' : stationDisplayName(station);
        const eta = active
          ? '\u5f53\u524d\u6b65\u9aa4'
          : `\u9884\u8ba1 ${Math.max(1, index * 3)} \u5206\u949f`;
        const pos = positions[index] || positions[positions.length - 1];
        const icon = station === 'pharmacy' || isReturn ? iconMedical : iconWard;
        return `<div class="route-step ${stateCls}" style="left:${pos.left}%; top:${pos.top}%">
          <div class="route-node">
            ${icon}
            <span class="route-step-no">${escapeHtml(String(index + 1))}</span>
          </div>
          <div class="route-copy">
            <div class="route-label">${escapeHtml(label)}</div>
            <div class="route-eta">${escapeHtml(eta)}</div>
          </div>
        </div>`;
      }).join('');
      const totalMinutes = Math.max(0, (normalizedRoute.length - 1) * 3);
      el.innerHTML = `<div class="route-flow">
        <svg class="route-path-svg" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          <defs>
            <linearGradient id="routeProgressGradient" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stop-color="#0f9f9a"></stop>
              <stop offset="100%" stop-color="#12b8ad"></stop>
            </linearGradient>
          </defs>
          ${pathsHtml}
        </svg>
        ${nodesHtml}
      </div>
      <div class="route-summary">
        <div class="route-summary-item"><span>\u9884\u8ba1\u5168\u7a0b\u5b8c\u6210\u65f6\u95f4</span><strong>${escapeHtml(String(totalMinutes))} \u5206\u949f</strong></div>
        <div class="route-summary-item"><span>\u603b\u914d\u9001\u8def\u7ebf</span><strong>${escapeHtml(String(normalizedRoute.length))} \u4e2a\u7ad9\u70b9</strong></div>
      </div>`;
    }

    function renderBatchStops(batch) {
      const stops = batch.stops || [];
      const activeIndex = Number(batch.active_stop_index ?? -1);
      const container = document.getElementById('batch_stops');
      if (!stops.length) {
        container.innerHTML = '<div class="audit-detail">暂无病房配送清单</div>';
        return;
      }
      container.innerHTML = stops.map((stop, index) => {
        const active = index === activeIndex;
        const patients = stop.patients || [];
        const patientHtml = patients.map(patient => renderBatchPatient(patient)).join('');
        return `<div class="batch-stop ${active ? 'active' : ''}">
          <div class="batch-stop-head">
            <span>${escapeHtml(stop.display_name || stop.target_station)} / ${patients.length} 位病人</span>
            <span class="batch-status ${batchStatusClass(stop.stop_status)}">${escapeHtml(batchStatusText(stop.stop_status))}</span>
          </div>
          <div class="audit-detail">药品：装药 ${stop.medication_loaded_count || 0}/${stop.medication_total_count || 0}，交付 ${stop.medication_dispensed_count || 0}/${stop.medication_total_count || 0}，回收 ${stop.medication_returned_count || 0}，异常 ${stop.medication_exception_count || 0}</div>
          ${patientHtml}
        </div>`;
      }).join('');
    }

    function batchPatientKey(patient) {
      return String(patient.patient_id || patient.bed_no || '');
    }

    function renderPatientProfileSummary(patient) {
      const fields = [
        ['\u5e74\u9f84', patient.age ? `${patient.age}\u5c81` : '-'],
        ['\u6027\u522b', patient.gender || '-'],
        ['\u8eab\u9ad8', patient.height_cm ? `${patient.height_cm}cm` : '-'],
        ['\u4f53\u91cd', patient.weight_kg ? `${patient.weight_kg}kg` : '-'],
        ['\u8bca\u65ad', patient.diagnosis || '-'],
        ['\u8fc7\u654f\u53f2', patient.allergies || '-'],
      ];
      return `<div class="batch-patient-profile">${fields.map(([label, value]) => (
        `<span>${escapeHtml(label)}\uff1a<strong>${escapeHtml(value)}</strong></span>`
      )).join('')}</div>`;
    }

    function renderBatchPatientEditPanel(patient) {
      const key = batchPatientKey(patient);
      if (!key || editingBatchPatientKey !== key) return '';
      const safeKey = key.replace(/[^a-zA-Z0-9_-]/g, '_');
      const id = (name) => `patient_edit_${safeKey}_${name}`;
      const input = (name, label, value, attrs = '') => `
        <label>${escapeHtml(label)}
          <input id="${escapeHtml(id(name))}" data-patient-edit-field="${escapeHtml(name)}" value="${escapeHtml(value || '')}" ${attrs} />
        </label>`;
      const textarea = (name, label, value) => `
        <label class="patient-edit-full">${escapeHtml(label)}
          <textarea id="${escapeHtml(id(name))}" data-patient-edit-field="${escapeHtml(name)}">${escapeHtml(value || '')}</textarea>
        </label>`;
      return `<div class="patient-edit-panel" data-patient-edit-key="${escapeHtml(key)}">
        <div class="patient-edit-grid">
          ${input('patient_name', '\u59d3\u540d', patient.patient_name || '')}
          ${input('age', '\u5e74\u9f84', patient.age || '', 'inputmode="numeric"')}
          ${input('gender', '\u6027\u522b', patient.gender || '')}
          ${input('height_cm', '\u8eab\u9ad8 cm', patient.height_cm || '', 'inputmode="decimal"')}
          ${input('weight_kg', '\u4f53\u91cd kg', patient.weight_kg || '', 'inputmode="decimal"')}
          ${input('doctor_name', '\u533b\u751f', patient.doctor_name || '')}
          ${textarea('diagnosis', '\u75be\u75c5\u8bca\u65ad / \u5f53\u524d\u75c5\u60c5', patient.diagnosis || '')}
          ${textarea('allergies', '\u8fc7\u654f\u53f2', patient.allergies || '')}
          ${textarea('contraindications', '\u7981\u5fcc / \u91cd\u70b9\u63d0\u9192', patient.contraindications || '')}
          ${textarea('nursing_note', '\u62a4\u7406\u5907\u6ce8', patient.nursing_note || '')}
        </div>
        <div class="actions" style="margin-top: 10px;">
          <button class="primary small-button" type="button" onclick="saveBatchPatientInfo('${escapeHtml(key)}')">\u4fdd\u5b58\u75c5\u4eba\u4fe1\u606f</button>
          <button class="secondary small-button" type="button" onclick="cancelBatchPatientEdit()">\u53d6\u6d88</button>
        </div>
        <div class="patient-edit-message" id="patient_edit_message_${escapeHtml(safeKey)}">\u4fdd\u5b58\u540e 8081 \u75c5\u4eba\u7aef\u5c06\u5728 5 \u79d2\u5185\u81ea\u52a8\u5237\u65b0\uff0cAI \u8bed\u97f3\u4e5f\u4f1a\u4f7f\u7528\u6700\u65b0\u4fe1\u606f\u3002</div>
      </div>`;
    }

    function renderBatchPatient(patient) {
      const medications = patient.medications || [];
      const done = medications.filter(item => item.dispensed || item.returned || item.exception).length;
      const medicationHtml = medications.map(item => renderBatchMedication(item)).join('');
      const hasRetryableException = medications.some(item => item.exception && !item.dispensed && !item.returned);
      const hasReviewableIssue = medications.some(item => item.exception || item.returned);
      const hasMedicationReview = Boolean(patient.medication_review_required || medications.some(item => item.review_required));
      const rejectedMedication = medications.find(item => item.exception === 'patient_rejected');
      const hasPatientRejected = Boolean(patient.patient_status === 'PATIENT_REJECTED' || rejectedMedication);
      const reviewResolveButtons = hasMedicationReview ? `
          <button class="secondary small-button" type="button" onclick="continuePatientMedicationReview('${escapeHtml(patient.patient_id || '')}')">复核通过继续配送</button>
          <button class="secondary small-button danger-action" type="button" onclick="returnPatientMedicationReview('${escapeHtml(patient.patient_id || '')}')">退回药房</button>` : '';
      const retryButtons = hasRetryableException ? `
          <button class="secondary small-button" type="button" onclick="retryBatchPatientException('${escapeHtml(patient.patient_id || '')}')">稍后重试</button>
          <button class="secondary small-button" type="button" onclick="clearBatchPatientException('${escapeHtml(patient.patient_id || '')}')">复核通过</button>` : '';
      const reviewButton = hasReviewableIssue ? `<button class="secondary small-button" type="button" onclick="reviewBatchPatientException('${escapeHtml(patient.patient_id || '')}')">药师复核</button>` : '';
      // 闭环 B: 根据 patient_status_overrides 给卡片打贴纸
      const bedNo = patient.bed_no || '';
      const ovr = bedNo && latestPatientStatusOverrides[bedNo];
      let patientStatusClass = '';
      let patientStatusPill = '';
      let patientStatusReason = '';
      if (ovr && ovr.status === 'confirmed') {
        patientStatusClass = 'confirmed';
        patientStatusPill = '<span class="patient-status-pill confirmed">✓ 病人已取药</span>';
      } else if ((ovr && ovr.status === 'rejected') || hasPatientRejected) {
        patientStatusClass = 'rejected';
        patientStatusPill = '<span class="patient-status-pill rejected">&#9888; &#x75C5;&#x4EBA;&#x53CD;&#x9988;&#x95EE;&#x9898;</span>';
        const rejectReason = (ovr && ovr.reason) || patient.patient_rejected_reason || rejectedMedication?.exception_reason || '';
        patientStatusReason = `<div class="patient-status-reason">&#x53CD;&#x9988;: ${escapeHtml(rejectReason || '未填写原因')}</div>`;
      } else if ((ovr && ovr.status === 'review') || hasMedicationReview) {
        patientStatusClass = 'review';
        patientStatusPill = '<span class="patient-status-pill review">⚠ 待用药复核</span>';
        const reviewReason = (ovr && ovr.reason) || patient.medication_review_reason || '病人反馈信息可能有误';
        patientStatusReason = `<div class="patient-status-reason">复核原因: ${escapeHtml(reviewReason)}</div>`;
      } else if (ovr && ovr.status === 'timeout') {
        // 闭环 #6: 机器人到位 N 分钟病人未确认 → 橙色"等待确认"贴纸
        patientStatusClass = 'timeout';
        patientStatusPill = '<span class="patient-status-pill timeout">⏰ 病人长时间未确认</span>';
        patientStatusReason = '<div class="patient-status-reason">建议: 联系病人/护士到床位旁协助</div>';
      }
      const patientDomId = String(patient.patient_id || '').replace(/[^a-zA-Z0-9_-]/g, '_');
      return `<div class="batch-patient ${patientStatusClass}" data-patient-dom-id="${escapeHtml(patientDomId)}" data-bed-no="${escapeHtml(patient.bed_no || '')}">
        <div class="batch-patient-head">
          <span>${escapeHtml(patient.bed_no || '-')} ${escapeHtml(patient.patient_name || '-')}${patientStatusPill}</span>
          <span class="batch-status ${done >= medications.length && medications.length ? 'ok' : 'warn'}">${done}/${medications.length}</span>
        </div>
        ${patientStatusReason}
        ${renderPatientProfileSummary(patient)}
        <div class="actions" style="margin-top: 8px;">
          <button class="secondary small-button" type="button" onclick="toggleBatchPatientEdit('${escapeHtml(batchPatientKey(patient))}')">编辑病人信息</button>
          <button class="secondary small-button" type="button" onclick="markBatchPatientAbsent('${escapeHtml(patient.patient_id || '')}')">病人不在</button>
          ${retryButtons}
          ${reviewButton}
          ${reviewResolveButtons}
        </div>
        ${renderBatchPatientEditPanel(patient)}
        ${medicationHtml}
      </div>`;
    }

    function batchMedicationKey(item) {
      return String(item.id || item.trace_id || item.product_code || item.medicine_name || '');
    }

    function renderBatchMedicationEditPanel(item) {
      const key = batchMedicationKey(item);
      if (!key || editingBatchMedicationKey !== key) return '';
      const safeKey = key.replace(/[^a-zA-Z0-9_-]/g, '_');
      const id = (name) => `med_edit_${safeKey}_${name}`;
      const input = (name, label, value, attrs = '') => `
        <label>${escapeHtml(label)}
          <input id="${escapeHtml(id(name))}" data-med-edit-field="${escapeHtml(name)}" value="${escapeHtml(value || '')}" ${attrs} />
        </label>`;
      const textarea = (name, label, value) => `
        <label class="patient-edit-full">${escapeHtml(label)}
          <textarea id="${escapeHtml(id(name))}" data-med-edit-field="${escapeHtml(name)}">${escapeHtml(value || '')}</textarea>
        </label>`;
      return `<div class="patient-edit-panel" data-med-edit-key="${escapeHtml(key)}">
        <div class="patient-edit-grid">
          ${input('medicine_name', '\u836f\u54c1\u540d\u79f0', item.medicine_name || '')}
          ${input('quantity', '\u6570\u91cf', item.quantity || '')}
          ${input('dose', '\u5355\u6b21\u5242\u91cf', item.dose || '')}
          ${input('frequency', '\u9891\u6b21', item.frequency || '')}
          ${input('route_label', '\u7ed9\u836f\u9014\u5f84', item.route_label || '')}
          ${input('timing', '\u670d\u7528\u65f6\u673a', item.timing || '')}
          ${input('duration', '\u7597\u7a0b', item.duration || '')}
          ${input('product_model', '\u89c4\u683c', item.product_model || '')}
          ${textarea('usage', '\u533b\u5631 / \u7528\u6cd5\u8bf4\u660e', item.usage || '')}
          ${textarea('precautions', '\u6ce8\u610f\u4e8b\u9879', item.precautions || '')}
          ${textarea('doctor_note', '\u533b\u751f\u5907\u6ce8', item.doctor_note || '')}
        </div>
        <div class="actions" style="margin-top: 10px;">
          <button class="primary small-button" type="button" onclick="saveBatchMedicationInfo('${escapeHtml(key)}')">\u4fdd\u5b58\u836f\u54c1\u8bf4\u660e</button>
          <button class="secondary small-button" type="button" onclick="cancelBatchMedicationEdit()">\u53d6\u6d88</button>
        </div>
        <div class="patient-edit-message" id="med_edit_message_${escapeHtml(safeKey)}">\u4fdd\u5b58\u540e 8081 \u836f\u54c1\u8be6\u60c5\u3001\u64ad\u62a5\u548c AI \u8bed\u97f3\u90fd\u4f1a\u4f7f\u7528\u6700\u65b0\u8bf4\u660e\u3002</div>
      </div>`;
    }

    function renderBatchMedication(item) {
      const hasException = Boolean(item.exception);
      const returned = Boolean(item.returned);
      const reviewed = Boolean(item.manual_reviewed);
      const className = item.dispensed ? 'batch-med dispensed' : (returned || hasException ? 'batch-med loaded' : (item.loaded ? 'batch-med loaded' : 'batch-med'));
      const stateText = item.dispensed ? '已交付' : (returned ? (reviewed ? '已回收/药师已复核' : '已回收') : (hasException ? (reviewed ? '药师已复核' : '待药师复核') : (item.loaded ? '已装药' : '待装药')));
      const stateClass = item.dispensed ? 'ok' : (hasException ? 'warn' : (item.loaded ? 'info' : 'warn'));
      const exceptionText = item.exception ? `<div class="audit-detail">异常：${escapeHtml(item.exception_reason || item.exception || '-')}</div>` : '';
      const returnText = item.returned ? `<div class="audit-detail">回收：${escapeHtml(item.return_reason || '未交付，回药房回收')}</div>` : '';
      const resolvedText = item.exception_resolved_at ? `<div class="audit-detail">异常处理：${escapeHtml(item.exception_resolved_reason || '-')}（${escapeHtml(item.exception_resolved_at)}）</div>` : '';
      const reviewText = reviewed ? `<div class="audit-detail">药师复核：${escapeHtml(item.manual_review_result || '-')}（${escapeHtml(item.manual_reviewed_at || '-')}）</div>` : '';
      const signedText = item.patient_signed ? `<div class="audit-detail">病人本人签收：${escapeHtml(item.patient_signed_at || item.dispensed_at || '-')}${item.patient_signed_delivery_id ? ' / 派送 ' + escapeHtml(item.patient_signed_delivery_id) : ''}</div>` : '';
      const retryButtons = hasException && !item.dispensed && !returned ? `
          <button class="secondary small-button" type="button" onclick="retryBatchMedicationException('${escapeHtml(item.id || '')}')">稍后重试</button>
          <button class="secondary small-button" type="button" onclick="clearBatchMedicationException('${escapeHtml(item.id || '')}')">复核通过</button>` : '';
      const reviewButton = hasException || returned ? `<button class="secondary small-button" type="button" onclick="reviewBatchMedicationException('${escapeHtml(item.id || '')}')">药师复核</button>` : '';
      return `<div class="${className}">
        <div class="batch-med-head">
          <span>${escapeHtml(item.medicine_name || '-')}</span>
          <span class="batch-status ${stateClass}">${stateText}</span>
        </div>
        <div class="audit-detail">数量：${escapeHtml(item.quantity || '-')}；${hasException ? '存在异常' : '无异常'}；${reviewed ? '药师已复核' : '未复核'}</div>
        <details class="batch-med-details">
          <summary>展开详情</summary>
          ${item.task_manager_task_id ? `<div class="audit-detail">任务管理 ID：${escapeHtml(item.task_manager_task_id)}</div>` : ''}
          <div class="audit-detail">产品编码：${escapeHtml(item.product_code || '-')}；追溯编号：${escapeHtml(item.trace_id || '-')}</div>
          <div class="audit-detail">规格：${escapeHtml(item.product_model || '-')}；医嘱：${escapeHtml(item.dose || '-')}/${escapeHtml(item.usage || '-')}</div>
        </details>
        ${exceptionText}
        ${returnText}
        ${resolvedText}
        ${signedText}
        ${reviewText}
        <div class="actions" style="margin-top: 8px;">
          <button class="secondary small-button" type="button" onclick="toggleBatchMedicationEdit('${escapeHtml(batchMedicationKey(item))}')">\u7f16\u8f91\u836f\u54c1\u8bf4\u660e</button>
          <button class="secondary small-button" type="button" onclick="markBatchMedicationException('${escapeHtml(item.id || '')}')">\u836f\u54c1\u5f02\u5e38</button>
          <button class="secondary small-button" type="button" onclick="markBatchMedicationReturn('${escapeHtml(item.id || '')}')">\u672a\u4ea4\u4ed8\u56de\u6536</button>
          ${retryButtons}
          ${reviewButton}
        </div>
        ${renderBatchMedicationEditPanel(item)}
      </div>`;
    }

    function batchAuditMessageText(record) {
      const event = record?.event || '';
      const raw = String(record?.message || '');
      const extra = record?.extra || record || {};
      const bed = extra.bed_no || extra.bed || '';
      const name = extra.patient_name || '';
      const reason = extra.reason || '';
      const affected = extra.affected_medication_count;
      const looksBroken = !raw || /\?{3,}/.test(raw);
      if (!looksBroken) return raw;
      if (event === 'patient_medication_review_required') {
        return `\u75c5\u4eba\u53cd\u9988\u5f85\u7528\u836f\u590d\u6838\uff1a${bed || '-'} ${name || ''}${reason ? '\uff0c' + reason : ''}`;
      }
      if (event === 'patient_medication_review_continue') {
        return `\u7528\u836f\u590d\u6838\u901a\u8fc7\uff0c\u53ef\u7ee7\u7eed\u914d\u9001\uff1a${bed || '-'} ${name || ''}`;
      }
      if (event === 'patient_medication_review_return') {
        return `\u7528\u836f\u590d\u6838\u9000\u56de\u836f\u623f\uff1a${bed || '-'} ${name || ''}${affected !== undefined ? '\uff0c\u5f71\u54cd ' + affected + ' \u9879\u836f\u54c1' : ''}`;
      }
      if (event === 'patient_message_reply') {
        return `\u62a4\u58eb\u5df2\u56de\u590d\u54a8\u8be2\uff1a${bed || '-'} ${name || ''}${extra.content_preview ? '\uff0c' + extra.content_preview : ''}`;
      }
      if (event === 'patient_message_read') {
        return `\u62a4\u58eb\u5df2\u8bfb\u54a8\u8be2\uff1a${bed || '-'} ${name || ''}`;
      }
      return raw || '-';
    }

    function isSafetyBlockedAudit(record) {
      return ['advance_blocked', 'load_scan_blocked', 'dispense_scan_blocked'].includes(record?.event || '');
    }

    function safetyBlockedAuditLabel(event) {
      const labels = {
        advance_blocked: '阶段推进被阻断',
        load_scan_blocked: '装药核验被阻断',
        dispense_scan_blocked: '交付核验被阻断',
      };
      return labels[event] || '安全门阻断';
    }

    function renderSafetyAuditSummary(records) {
      const box = document.getElementById('batch_safety_audit_summary');
      if (!box) return;
      const title = document.getElementById('safety_audit_title');
      const meta = document.getElementById('safety_audit_meta');
      const button = document.getElementById('safety_audit_filter_button');
      const blocked = (records || []).filter(isSafetyBlockedAudit);
      box.hidden = !blocked.length;
      if (!blocked.length) return;
      const latest = blocked[blocked.length - 1] || {};
      if (title) title.textContent = `安全门阻断 ${blocked.length} 次`;
      if (meta) meta.textContent = `${safetyBlockedAuditLabel(latest.event)} / ${latest.time || '-'} / ${batchAuditMessageText(latest)}`;
      if (button && !button.dataset.bound) {
        button.dataset.bound = '1';
        button.addEventListener('click', () => {
          latestAuditFilter = 'safety_blocked';
          const select = document.getElementById('batch_audit_filter');
          if (select) select.value = 'safety_blocked';
          renderBatchAudit((latestDeliveryBatch && latestDeliveryBatch.audit_records) || []);
        });
      }
    }

    function renderBatchAudit(records) {
      const container = document.getElementById('batch_audit_records');
      const reviewEvents = ['patient_medication_review_required', 'patient_medication_review_continue', 'patient_medication_review_return'];
      const messageAuditEvents = ['patient_message_reply', 'patient_message_read'];
      const safetyBlockedEvents = ['advance_blocked', 'load_scan_blocked', 'dispense_scan_blocked'];
      renderSafetyAuditSummary(records || []);
      const primaryAuditEvents = ['load_scan', 'dispense_scan', 'advance', ...safetyBlockedEvents, 'patient_absent', 'patient_signed', 'patient_rejected', 'manual_review', 'medication_return', 'medication_exception', ...reviewEvents, ...messageAuditEvents];
      const filteredRecords = (records || []).filter(record => {
        if (latestAuditFilter === 'all') return true;
        if (latestAuditFilter === 'fail') return record.result === 'fail';
        if (latestAuditFilter === 'safety_blocked') return safetyBlockedEvents.includes(record.event);
        if (latestAuditFilter === 'medication_review') return reviewEvents.includes(record.event);
        if (latestAuditFilter === 'patient_message') return messageAuditEvents.includes(record.event);
        if (latestAuditFilter === 'system') return !primaryAuditEvents.includes(record.event);
        if (latestAuditFilter === 'advance') {
          return ['advance', 'navigate_to_ward', 'arrived_at_ward', 'ward_completed', 'returning_to_pharmacy', 'batch_completed'].includes(record.event);
        }
        return record.event === latestAuditFilter;
      });
      const latest = [...filteredRecords].slice(-18).reverse();
      if (!latest.length) {
        container.innerHTML = '<div class="audit-item"><div class="audit-detail">暂无符合筛选条件的批次审计记录</div></div>';
        return;
      }


      const eventLabels = {
        batch_created: '批次创建',
        load_scan: '药师装药核验',
        dispense_scan: '床旁交付核验',
        advance: '配送阶段推进',
        patient_absent: '床旁无人应答',
        patient_signed: '患者本人签收',
        patient_rejected: '患者反馈问题',
        patient_medication_review_required: '\u5f85\u7528\u836f\u590d\u6838',
        patient_medication_review_continue: '\u7528\u836f\u590d\u6838\u901a\u8fc7',
        patient_medication_review_return: '\u7528\u836f\u590d\u6838\u9000\u56de',
        patient_message_reply: '\u62a4\u58eb\u56de\u590d\u54a8\u8be2',
        patient_message_read: '\u54a8\u8be2\u5df2\u8bfb',
        manual_review: '药师复核',
        medication_return: '药品未交付回收',
        medication_exception: '药品异常登记',
        navigate_to_ward: '配送阶段推进',
        arrived_at_ward: '到达病房',
        ward_completed: '病房完成',
        returning_to_pharmacy: '返回药房',
        batch_completed: '批次完成',
      };
      container.innerHTML = latest.map((record, index) => {
        const ok = record.result !== 'fail';
        const eventText = eventLabels[record.event] || record.event || '-';
        const extra = record.extra || {};
        const affected = extra.medication_id || extra.patient_id || extra.stop_id || extra.task_manager_task_id || '';
        const auditId = `audit_${index}_${String(record.event || 'event').replace(/[^a-zA-Z0-9_-]/g, '_')}_${String(affected || '').replace(/[^a-zA-Z0-9_-]/g, '_')}`;
        record.__dom_id = auditId;
        const safetyBlocked = isSafetyBlockedAudit(record);
        return `<div class="audit-item ${safetyBlocked ? 'safety-blocked' : ''}" id="${escapeHtml(auditId)}" data-audit-event="${escapeHtml(record.event || '')}" data-audit-result="${escapeHtml(record.result || '')}" data-audit-patient="${escapeHtml(extra.patient_id || '')}" data-audit-medication="${escapeHtml(extra.medication_id || '')}" data-audit-bed="${escapeHtml(extra.bed_no || extra.bed || '')}">
          <div class="audit-head">
            <span>${escapeHtml(record.time || '-')} ${escapeHtml(eventText)}</span>
            <span class="${ok ? 'audit-pass' : 'audit-fail'}">${ok ? '通过' : '失败'}</span>
          </div>
          <div class="audit-detail">${escapeHtml(batchAuditMessageText(record))}</div>
          ${affected ? `<div class="audit-detail">对象：${escapeHtml(affected)}</div>` : ''}
        </div>`;
      }).join('');
    }

    function buildReportRowsFromBatch(batch) {
      const rows = [];
      (batch.stops || []).forEach(stop => {
        (stop.patients || []).forEach(patient => {
          (patient.medications || []).forEach(medication => {
            rows.push({
              batch_id: batch.batch_id || '',
              route_status: batch.route_status || '',
              ward_id: patient.ward_id || stop.target_station || '',
              ward_name: patient.ward_name || stop.display_name || stop.target_station || '',
              bed_no: patient.bed_no || '',
              patient_id: patient.patient_id || '',
              patient_name: patient.patient_name || '',
              medicine_name: medication.medicine_name || '',
              product_code: medication.product_code || '',
              trace_id: medication.trace_id || '',
              quantity: medication.quantity || '',
              loaded: Boolean(medication.loaded),
              loaded_at: medication.loaded_at || '',
              dispensed: Boolean(medication.dispensed),
              dispensed_at: medication.dispensed_at || '',
              patient_signed: Boolean(medication.patient_signed),
              patient_signed_at: medication.patient_signed_at || '',
              patient_signed_delivery_id: medication.patient_signed_delivery_id || '',
              returned: Boolean(medication.returned),
              returned_at: medication.returned_at || '',
              return_reason: medication.return_reason || '',
              exception: medication.exception || '',
              exception_at: medication.exception_at || '',
              exception_reason: medication.exception_reason || '',
              exception_resolved_at: medication.exception_resolved_at || '',
              exception_resolved_reason: medication.exception_resolved_reason || '',
              exception_resolution_action: medication.exception_resolution_action || '',
              manual_reviewed: Boolean(medication.manual_reviewed),
              manual_reviewed_at: medication.manual_reviewed_at || '',
              manual_review_result: medication.manual_review_result || '',
            });
          });
        });
      });
      return rows;
    }

    function reportStatus(row) {
      if (row.dispensed) {
        return { key: 'dispensed', text: '已交付', className: 'ok' };
      }
      if (row.returned) {
        return { key: 'returned', text: row.manual_reviewed ? '已回收/药师已复核' : '已回收', className: 'warn' };
      }
      if (row.exception) {
        return { key: 'exception', text: row.manual_reviewed ? '药师已复核' : '待药师复核', className: 'warn' };
      }
      if (row.loaded) {
        return { key: 'loaded', text: '已装药未交付', className: 'info' };
      }
      return { key: 'pending', text: '待装药', className: 'warn' };
    }

    function buildReportArchiveGate(batch, rows, medicationReviewRows) {
      const data = batch || {};
      const stats = batchReceiptStats(data);
      const total = rows.length;
      const exceptionUnreviewed = rows.filter(row => row.exception && !row.manual_reviewed && !row.exception_resolved_at && !row.returned);
      const loadedNotDelivered = rows.filter(row => row.loaded && !row.dispensed && !row.returned);
      const notLoaded = rows.filter(row => !row.loaded && !row.dispensed && !row.returned);
      const pendingMedReview = (medicationReviewRows || []).filter(row => String(row.result || '').includes('\u5f85\u5904\u7406'));
      const issues = [];
      if (!data.batch_id) issues.push('\u5f53\u524d\u6ca1\u6709\u53ef\u5f52\u6863\u7684\u914d\u9001\u6279\u6b21\u3002');
      if (notLoaded.length) issues.push(`${notLoaded.length} \u9879\u836f\u54c1\u5c1a\u672a\u88c5\u836f\u6838\u9a8c\u3002`);
      if (loadedNotDelivered.length) issues.push(`${loadedNotDelivered.length} \u9879\u836f\u54c1\u5df2\u88c5\u836f\u4f46\u672a\u4ea4\u4ed8/\u56de\u6536\u3002`);
      if (exceptionUnreviewed.length) issues.push(`${exceptionUnreviewed.length} \u9879\u836f\u54c1\u5f02\u5e38\u5c1a\u672a\u5904\u7406\u6216\u590d\u6838\u3002`);
      if (pendingMedReview.length) issues.push(`${pendingMedReview.length} \u6761\u75c5\u4eba\u7528\u836f\u590d\u6838\u4ecd\u5f85\u5904\u7406\u3002`);
      if (stats.pending) issues.push(`${stats.pending} \u540d\u75c5\u4eba\u5c1a\u672a\u7b7e\u6536\u6216\u786e\u8ba4\u3002`);
      const complete = Boolean(data.batch_id) && total > 0 && !issues.length;
      const danger = exceptionUnreviewed.length || pendingMedReview.length || stats.rejected;
      return {
        ok: complete,
        tone: complete ? 'ok' : (danger ? 'danger' : 'warn'),
        badgeClass: complete ? 'COMPLETED' : (danger ? 'CANCELED' : 'WAITING_LOAD_CONFIRMATION'),
        badge: complete ? '\u53ef\u5f52\u6863' : '\u6682\u4e0d\u5efa\u8bae\u5f52\u6863',
        title: complete ? '\u5f52\u6863\u68c0\u67e5\u901a\u8fc7' : '\u5f52\u6863\u524d\u8fd8\u9700\u5904\u7406',
        body: complete
          ? `\u672c\u6279\u6b21 ${total} \u9879\u836f\u54c1\u5747\u5df2\u4ea4\u4ed8\u3001\u56de\u6536\u6216\u590d\u6838\u7559\u75d5\uff0c\u53ef\u5bfc\u51fa\u5ba1\u8ba1 JSON/CSV \u5e76\u5f52\u6863\u3002`
          : '\u8bf7\u5148\u5904\u7406\u4e0b\u5217\u672a\u95ed\u73af\u9879\uff0c\u518d\u5c06\u62a5\u544a\u4f5c\u4e3a\u6700\u7ec8\u5f52\u6863\u6750\u6599\u3002',
        issues,
        actions: complete
          ? [
              { label: '\u5bfc\u51fa\u5ba1\u8ba1 JSON', target: 'report-export-json' },
              { label: '\u5bfc\u51fa\u660e\u7ec6 CSV', target: 'report-export-csv' },
            ]
          : [
              { label: '\u67e5\u770b\u672a\u95ed\u73af\u660e\u7ec6', target: 'report_status_filter', status: notLoaded.length ? 'pending' : (loadedNotDelivered.length ? 'loaded' : 'exception') },
              { label: '\u56de\u5230\u914d\u9001\u6267\u884c', target: 'batch-tab' },
            ],
      };
    }

    function runReportArchiveAction(target, status = '') {
      if (target === 'batch-tab') {
        switchDashboardTab('batch');
        return;
      }
      const element = document.getElementById(target);
      if (!element) return;
      if (target === 'report_status_filter' && status) {
        element.value = status;
        renderDeliveryReport();
      }
      if (target === 'report-export-json' || target === 'report-export-csv') {
        element.click();
        return;
      }
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      if (typeof element.focus === 'function') element.focus({ preventScroll: true });
    }

    function renderReportArchiveGate(batch, rows, medicationReviewRows) {
      const gate = document.getElementById('report_archive_gate');
      if (!gate) return;
      const model = buildReportArchiveGate(batch, rows, medicationReviewRows);
      const title = document.getElementById('report_archive_title');
      const badge = document.getElementById('report_archive_badge');
      const body = document.getElementById('report_archive_body');
      const issues = document.getElementById('report_archive_issues');
      const actions = document.getElementById('report_archive_actions');
      gate.className = `report-archive-gate ${model.tone}`;
      if (title) title.textContent = model.title;
      if (badge) {
        badge.textContent = model.badge;
        badge.className = `badge ${model.badgeClass}`;
      }
      if (body) body.textContent = model.body;
      if (issues) {
        issues.innerHTML = (model.issues || []).slice(0, 8).map(item => `<li>${escapeHtml(item)}</li>`).join('');
      }
      if (actions) {
        actions.innerHTML = (model.actions || []).map((action, index) => `<button type="button" class="secondary" data-report-archive-action="${index}">${escapeHtml(action.label)}</button>`).join('');
        (model.actions || []).forEach((action, index) => {
          const button = actions.querySelector(`[data-report-archive-action="${index}"]`);
          if (button) button.addEventListener('click', () => runReportArchiveAction(action.target, action.status || ''));
        });
      }
    }

    function updateReportWardFilter(rows) {
      const select = document.getElementById('report_ward_filter');
      const current = select.value || 'all';
      const wards = [];
      rows.forEach(row => {
        const wardId = row.ward_id || row.ward_name || '-';
        if (!wards.some(item => item.id === wardId)) {
          wards.push({ id: wardId, name: row.ward_name || stationDisplayName(wardId) });
        }
      });
      select.innerHTML = '<option value="all">全部病房</option>' + wards.map(ward => (
        `<option value="${escapeHtml(ward.id)}">${escapeHtml(ward.name)} (${escapeHtml(ward.id)})</option>`
      )).join('');
      select.value = wards.some(ward => ward.id === current) ? current : 'all';
    }

    function applyReportFilters(rows) {
      const wardFilter = document.getElementById('report_ward_filter').value || 'all';
      const statusFilter = document.getElementById('report_status_filter').value || 'all';
      const keyword = document.getElementById('report_search').value.trim().toLowerCase();
      return rows.filter(row => {
        if (wardFilter !== 'all' && (row.ward_id || row.ward_name || '-') !== wardFilter) {
          return false;
        }
        const status = reportStatus(row).key;
        if (statusFilter !== 'all') {
          if (statusFilter === 'reviewed' && !row.manual_reviewed) {
            return false;
          }
          if (statusFilter !== 'reviewed' && status !== statusFilter) {
            return false;
          }
        }
        if (keyword) {
          const text = [
            row.ward_id,
            row.ward_name,
            row.bed_no,
            row.patient_id,
            row.patient_name,
            row.medicine_name,
            row.product_code,
            row.trace_id,
            row.exception_reason,
            row.return_reason,
            row.manual_review_result,
          ].join(' ').toLowerCase();
          if (!text.includes(keyword)) {
            return false;
          }
        }
        return true;
      });
    }

    function buildMedicationReviewReportRows(batch = latestDeliveryBatch) {
      const records = Array.isArray(batch?.audit_records) ? batch.audit_records : [];
      const reviewEvents = ['patient_medication_review_required', 'patient_medication_review_continue', 'patient_medication_review_return'];
      const rowsByKey = new Map();
      const rowKey = (record) => {
        const extra = record.extra || {};
        return String(extra.patient_id || extra.bed_no || extra.bed || record.patient_id || record.bed_no || record.time || Math.random());
      };
      records.filter(record => reviewEvents.includes(record.event)).forEach(record => {
        const extra = record.extra || {};
        const key = rowKey(record);
        const current = rowsByKey.get(key) || {
          key,
          bed_no: extra.bed_no || extra.bed || '-',
          patient_name: extra.patient_name || '-',
          patient_id: extra.patient_id || '',
          reason: extra.reason || '',
          requested_at: '',
          result: '\u5f85\u5904\u7406',
          handled_at: '',
          affected_count: extra.affected_medication_count,
          message: '',
        };
        current.bed_no = extra.bed_no || extra.bed || current.bed_no || '-';
        current.patient_name = extra.patient_name || current.patient_name || '-';
        current.patient_id = extra.patient_id || current.patient_id || '';
        current.reason = extra.reason || current.reason || '';
        current.affected_count = extra.affected_medication_count ?? current.affected_count;
        if (record.event === 'patient_medication_review_required') {
          current.requested_at = record.timestamp || record.time || current.requested_at || '';
          current.message = batchAuditMessageText(record);
        } else if (record.event === 'patient_medication_review_continue') {
          current.result = '\u590d\u6838\u901a\u8fc7\uff0c\u7ee7\u7eed\u914d\u9001';
          current.handled_at = record.timestamp || record.time || current.handled_at || '';
          current.message = batchAuditMessageText(record);
        } else if (record.event === 'patient_medication_review_return') {
          current.result = '\u9000\u56de\u836f\u623f';
          current.handled_at = record.timestamp || record.time || current.handled_at || '';
          current.message = batchAuditMessageText(record);
        }
        rowsByKey.set(key, current);
      });
      ((batch && batch.stops) || []).forEach(stop => {
        (stop.patients || []).forEach(patient => {
          const hasPendingReview = Boolean(patient.medication_review_required || (patient.medications || []).some(item => item.review_required));
          if (!hasPendingReview) return;
          const key = String(patient.patient_id || patient.bed_no || `${stop.target_station || ''}:${patient.patient_name || ''}`);
          if (rowsByKey.has(key)) return;
          rowsByKey.set(key, {
            key,
            bed_no: patient.bed_no || '-',
            patient_name: patient.patient_name || '-',
            patient_id: patient.patient_id || '',
            reason: patient.medication_review_reason || '\u75c5\u4eba\u53cd\u9988\u7528\u836f\u6216\u4e2a\u4eba\u4fe1\u606f\u53ef\u80fd\u6709\u8bef',
            requested_at: '',
            result: '\u5f85\u5904\u7406',
            handled_at: '',
            affected_count: (patient.medications || []).length,
            message: '',
          });
        });
      });
      return Array.from(rowsByKey.values()).sort((a, b) => String(b.handled_at || b.requested_at).localeCompare(String(a.handled_at || a.requested_at)));
    }

    function renderMedicationReviewReportRows(rows) {
      const tbody = document.getElementById('report_med_review_rows');
      if (!tbody) return;
      if (!rows.length) {
        tbody.innerHTML = '<tr><td colspan="6">\u6682\u65e0\u7528\u836f\u590d\u6838\u8bb0\u5f55</td></tr>';
        return;
      }
      tbody.innerHTML = rows.map(row => {
        const resultClass = row.result === '\u5f85\u5904\u7406' ? 'warn' : (row.result.includes('\u9000\u56de') ? 'warn' : 'ok');
        const reason = row.reason || row.message || '-';
        const affected = row.affected_count !== undefined && row.affected_count !== null ? `${row.affected_count} \u9879\u836f\u54c1` : '-';
        return `<tr>
          <td>${escapeHtml(row.bed_no || '-')}<br><span class="audit-detail">${escapeHtml(row.requested_at || '-')}</span></td>
          <td>${escapeHtml(row.patient_name || '-')}<br><span class="audit-detail">${escapeHtml(row.patient_id || '-')}</span></td>
          <td>${escapeHtml(reason)}</td>
          <td><span class="batch-status ${resultClass}">${escapeHtml(row.result || '-')}</span></td>
          <td>${escapeHtml(row.handled_at || '-')}</td>
          <td>${escapeHtml(affected)}</td>
        </tr>`;
      }).join('');
    }

    function renderDeliveryReport() {
      const batch = latestDeliveryBatch || {};
      const rows = buildReportRowsFromBatch(batch);
      latestReportRows = rows;
      latestReportGeneratedAt = new Date().toLocaleString();
      updateReportWardFilter(rows);
      const filtered = applyReportFilters(rows);
      latestReportFilteredRows = filtered;
      const medicationReviewRows = buildMedicationReviewReportRows(batch);
      const patientIds = new Set(rows.map(row => row.patient_id).filter(Boolean));
      const issueCount = rows.filter(row => row.exception || row.returned).length;
      document.getElementById('report_batch_id').textContent = batch.batch_id || '-';
      document.getElementById('report_generated_at').textContent = latestReportGeneratedAt;
      document.getElementById('report_stop_count').textContent = String((batch.stops || []).length);
      document.getElementById('report_patient_count').textContent = String(patientIds.size);
      document.getElementById('report_medication_count').textContent = String(rows.length);
      document.getElementById('report_dispensed_count').textContent = String(rows.filter(row => row.dispensed).length);
      document.getElementById('report_issue_count').textContent = String(issueCount);
      document.getElementById('report_review_count').textContent = String(rows.filter(row => row.manual_reviewed).length);
      document.getElementById('report_med_review_count').textContent = String(medicationReviewRows.length);
      const reviewedCount = rows.filter(row => row.manual_reviewed).length;
      const deliveredCount = rows.filter(row => row.dispensed).length;
      const closedCount = rows.filter(row => row.dispensed || row.returned || row.manual_reviewed).length;
      const conclusion = rows.length && closedCount >= rows.length
        ? '本批次所有药品均已完成交付、回收或药师复核，可进入归档。'
        : '当前批次仍有药品未完成交付、回收或药师复核，不建议归档。';
      document.getElementById('report_summary_text').textContent =
        `本批次共覆盖 ${(batch.stops || []).length} 个病房、${patientIds.size} 名病人、${rows.length} 项药品。已完成交付 ${deliveredCount} 项，异常/回收 ${issueCount} 项，药师复核 ${reviewedCount} 项，用药复核 ${medicationReviewRows.length} 人次。${conclusion}`;
      renderReportArchiveGate(batch, rows, medicationReviewRows);
      document.getElementById('report_filter_result').textContent = `当前显示 ${filtered.length}/${rows.length} 条药品明细。`;
      renderMedicationReviewReportRows(medicationReviewRows);
      renderReportExceptionRows(rows);
      renderReportRows(filtered);
    }

    function renderReportExceptionRows(rows) {
      const tbody = document.getElementById('report_exception_rows');
      const issueRows = rows.filter(row => row.exception || row.returned || row.manual_reviewed);
      if (!issueRows.length) {
        tbody.innerHTML = '<tr><td colspan="6">暂无异常、回收或药师复核记录</td></tr>';
        return;
      }
      tbody.innerHTML = issueRows.map(row => {
        const issueType = row.exception
          ? (row.exception_reason || row.exception || '药品异常')
          : (row.returned ? (row.return_reason || '未交付回收') : '药师复核');
        const handling = [
          row.returned ? '已回收' : '',
          row.exception_resolved_at ? `异常已处理：${row.exception_resolved_reason || '-'}` : '',
          row.manual_reviewed ? `药师已复核：${row.manual_review_result || '-'}` : '',
        ].filter(Boolean).join('；') || '待处理';
        const reviewText = row.manual_reviewed
          ? `${escapeHtml(row.manual_reviewed_by || '药师')}<br><span class="audit-detail">${escapeHtml(row.manual_reviewed_at || '-')}</span>`
          : '<span class="batch-status warn">待复核</span>';
        return `<tr>
          <td>${escapeHtml(row.ward_name || row.ward_id || '-')}<br><span class="audit-detail">${escapeHtml(row.bed_no || '-')}</span></td>
          <td>${escapeHtml(row.patient_name || '-')}<br><span class="audit-detail">${escapeHtml(row.patient_id || '-')}</span></td>
          <td>${escapeHtml(row.medicine_name || '-')}<br><span class="audit-detail">数量：${escapeHtml(row.quantity || '-')}</span></td>
          <td>${escapeHtml(issueType)}</td>
          <td>${escapeHtml(handling)}</td>
          <td>${reviewText}</td>
        </tr>`;
      }).join('');
    }

    function renderReportRows(rows) {
      const tbody = document.getElementById('report_rows');
      if (!rows.length) {
        tbody.innerHTML = '<tr><td colspan="6">暂无符合条件的报告数据</td></tr>';
        return;
      }
      tbody.innerHTML = rows.map(row => {
        const status = reportStatus(row);
        const issueLines = [
          row.exception ? `异常：${escapeHtml(row.exception_reason || row.exception)}` : '',
          row.exception_resolved_at ? `处理：${escapeHtml(row.exception_resolved_reason || '-')} / ${escapeHtml(row.exception_resolved_at)}` : '',
          row.returned ? `回收：${escapeHtml(row.return_reason || '-')} / ${escapeHtml(row.returned_at || '-')}` : '',
          row.manual_reviewed ? `复核：${escapeHtml(row.manual_review_result || '-')} / ${escapeHtml(row.manual_reviewed_at || '-')}` : '',
        ].filter(Boolean).join('<br>');
        return `<tr>
          <td>${escapeHtml(row.ward_name || row.ward_id || '-')}<br><span class="audit-detail">${escapeHtml(row.bed_no || '-')}</span></td>
          <td>${escapeHtml(row.patient_name || '-')}<br><span class="audit-detail">${escapeHtml(row.patient_id || '-')}</span></td>
          <td>${escapeHtml(row.medicine_name || '-')}<br><span class="audit-detail">数量：${escapeHtml(row.quantity || '-')}</span></td>
          <td>${escapeHtml(row.product_code || '-')}<br><span class="audit-detail">${escapeHtml(row.trace_id || '-')}</span></td>
          <td><span class="batch-status ${status.className}">${escapeHtml(status.text)}</span><br><span class="audit-detail">${escapeHtml(row.patient_signed_at || row.dispensed_at || row.loaded_at || '-')}</span></td>
          <td>${issueLines || '-'}</td>
        </tr>`;
      }).join('');
    }

    function buildPrintableReportHtml() {
      const rows = latestReportFilteredRows;
      const summary = {
        batchId: latestDeliveryBatch.batch_id || '-',
        generatedAt: latestReportGeneratedAt || new Date().toLocaleString(),
        total: latestReportRows.length,
        filtered: rows.length,
        dispensed: latestReportRows.filter(row => row.dispensed).length,
        issues: latestReportRows.filter(row => row.exception || row.returned).length,
        reviewed: latestReportRows.filter(row => row.manual_reviewed).length,
      };
      const issueRows = latestReportRows.filter(row => row.exception || row.returned || row.manual_reviewed);
      const issueHtml = issueRows.map(row => {
        const issueType = row.exception
          ? (row.exception_reason || row.exception || '药品异常')
          : (row.returned ? (row.return_reason || '未交付回收') : '药师复核');
        const handling = [
          row.returned ? '已回收' : '',
          row.exception_resolved_reason,
          row.manual_reviewed ? `药师已复核：${row.manual_review_result || '-'}` : '',
        ].filter(Boolean).join('；') || '待处理';
        return `<tr>
          <td>${escapeHtml(row.ward_name || row.ward_id || '-')} / ${escapeHtml(row.bed_no || '-')}</td>
          <td>${escapeHtml(row.patient_name || '-')}</td>
          <td>${escapeHtml(row.medicine_name || '-')}</td>
          <td>${escapeHtml(issueType)}</td>
          <td>${escapeHtml(handling)}</td>
          <td>${escapeHtml(row.manual_reviewed_at || '-')}</td>
        </tr>`;
      }).join('');
      const rowHtml = rows.map(row => {
        const status = reportStatus(row);
        const issue = [
          row.patient_signed ? `病人本人签收：${row.patient_signed_at || row.dispensed_at || '-'}` : '',
          row.exception_reason,
          row.return_reason,
          row.exception_resolved_reason,
          row.manual_review_result,
        ].filter(Boolean).join('；') || '-';
        return `<tr>
          <td>${escapeHtml(row.ward_name || row.ward_id || '-')} / ${escapeHtml(row.bed_no || '-')}</td>
          <td>${escapeHtml(row.patient_name || '-')}</td>
          <td>${escapeHtml(row.medicine_name || '-')} x ${escapeHtml(row.quantity || '-')}</td>
          <td>${escapeHtml(row.product_code || '-')} / ${escapeHtml(row.trace_id || '-')}</td>
          <td>${escapeHtml(status.text)}</td>
          <td>${escapeHtml(issue)}</td>
        </tr>`;
      }).join('');
      return `<!doctype html>
<html><head><meta charset="utf-8"><title>配送报告 ${escapeHtml(summary.batchId)}</title>
<style>
body { font-family: Arial, "Microsoft YaHei", sans-serif; color: #0f172a; margin: 24px; }
h1 { font-size: 22px; margin: 0 0 10px; }
.summary { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin: 14px 0; }
.summary div { border: 1px solid #cbd5e1; border-radius: 10px; padding: 8px; }
.summary span { display: block; color: #64748b; font-size: 12px; }
.summary strong { display: block; font-size: 18px; margin-top: 4px; }
.section-title { font-weight: 700; margin: 18px 0 8px; }
table { width: 100%; border-collapse: collapse; font-size: 12px; }
th, td { border: 1px solid #cbd5e1; padding: 7px; text-align: left; vertical-align: top; }
th { background: #f1f5f9; }
.signatures { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-top: 28px; font-size: 13px; }
.signatures div { border-top: 1px solid #334155; padding-top: 8px; }
@media print { body { margin: 12mm; } }
</style></head><body>
<h1>智能送药配送报告</h1>
<div>批次号：${escapeHtml(summary.batchId)}　生成时间：${escapeHtml(summary.generatedAt)}</div>
<div class="summary">
  <div><span>全部明细</span><strong>${summary.total}</strong></div>
  <div><span>当前筛选</span><strong>${summary.filtered}</strong></div>
  <div><span>已交付</span><strong>${summary.dispensed}</strong></div>
  <div><span>异常/回收</span><strong>${summary.issues}</strong></div>
  <div><span>药师复核</span><strong>${summary.reviewed}</strong></div>
</div>
<div class="section-title">异常汇总</div>
<table><thead><tr><th>病房/床号</th><th>病人</th><th>药品</th><th>异常类型</th><th>处理方式</th><th>复核时间</th></tr></thead><tbody>${issueHtml || '<tr><td colspan="6">暂无异常、回收或药师复核记录</td></tr>'}</tbody></table>
<div class="section-title">药品明细</div>
<table><thead><tr><th>病房/床号</th><th>病人</th><th>药品</th><th>编码/追溯</th><th>状态</th><th>异常/回收/复核</th></tr></thead><tbody>${rowHtml || '<tr><td colspan="6">暂无报告数据</td></tr>'}</tbody></table>
<div class="signatures"><div>药师签名：</div><div>护士签名：</div><div>主管签名：</div><div>归档时间：</div></div>
</body></html>`;
    }

    function printDeliveryReport() {
      renderDeliveryReport();
      const printWindow = window.open('', '_blank');
      if (!printWindow) {
        document.getElementById('report_filter_result').textContent = '浏览器阻止了打印窗口，请允许弹窗后重试。';
        return;
      }
      printWindow.document.open();
      printWindow.document.write(buildPrintableReportHtml());
      printWindow.document.close();
      printWindow.focus();
      printWindow.print();
    }

    function buildBatchImportTemplate() {
      const today = new Date().toISOString().slice(0, 10).replaceAll('-', '');
      return {
        batch_id: `TEST-3WARD-${today}-001`,
        source_station: 'pharmacy',
        source: 'his_test',
        issued_at: new Date().toLocaleString(),
        operator_id: 'operator_test_001',
        message: '测试批次：3 个病人 / 3 个病房 / 不同药品，用于验证 8081 病人端药品显示、播报和 AI 语音上下文。',
        patients: [
          {
            patient_id: 'P-A01-001',
            patient_name: '张叔叔',
            age: 68,
            gender: '\u7537',
            height_cm: 170,
            weight_kg: 72,
            ward_id: 'ward_a',
            ward_name: 'A病房',
            bed_no: 'A-01',
            target_station: 'ward_a',
            prescription_no: 'RX-A01-TEST-001',
            diagnosis: '\u9ad8\u8840\u538b\uff0c\u672c\u6b21\u5408\u5e76\u547c\u5438\u9053\u611f\u67d3\u7528\u836f',
            allergies: '\u65e0\u660e\u786e\u836f\u7269\u8fc7\u654f\u53f2',
            contraindications: '\u670d\u7528\u5934\u5b62\u671f\u95f4\u7981\u9152\uff1b\u82e5\u51fa\u73b0\u76ae\u75b9\u3001\u547c\u5438\u56f0\u96be\u7acb\u5373\u547c\u53eb\u62a4\u58eb',
            nursing_note: '\u8001\u5e74\u9ad8\u8840\u538b\u60a3\u8005\uff0c\u5efa\u8bae\u8d77\u8eab\u6162\u4e00\u70b9\uff0c\u7559\u610f\u5934\u6655\u548c\u8840\u538b\u53d8\u5316\u3002',
            medications: [
              {
                medicine_name: '头孢呋辛酯片',
                product_code: 'MED-CEFUROXIME-100MG',
                product_model: '100 mg × 12片/盒',
                quantity: '1盒',
                trace_id: 'TRACE-A01-CEFU-0001',
                order_no: 'ORD-A01-001',
                dose: '100 mg',
                usage: '口服，每日 2 次，饭后服用。服药期间禁酒，如出现皮疹、呼吸困难等不适请立即联系护士或医生。',
              },
              {
                medicine_name: '苯磺酸氨氯地平片',
                product_code: 'MED-AMLODIPINE-5MG',
                product_model: '5 mg × 7片/板',
                quantity: '1板',
                trace_id: 'TRACE-A01-AMLO-0002',
                order_no: 'ORD-A01-002',
                dose: '5 mg',
                usage: '口服，每日 1 次，建议早晨固定时间服用。若出现明显头晕、下肢水肿，请联系护士或医生。',
              },
            ],
          },
          {
            patient_id: 'P-B01-001',
            patient_name: '李奶奶',
            age: 76,
            gender: '\u5973',
            height_cm: 158,
            weight_kg: 61,
            ward_id: 'ward_b',
            ward_name: 'B病房',
            bed_no: 'B-01',
            target_station: 'ward_b',
            prescription_no: 'RX-B01-TEST-001',
            diagnosis: '\u0032\u578b\u7cd6\u5c3f\u75c5\uff0c\u9ad8\u8102\u8840\u75c7',
            allergies: '\u78fa\u80fa\u7c7b\u836f\u7269\u8fc7\u654f\u53f2',
            contraindications: '\u4e8c\u7532\u53cc\u80cd\u5efa\u8bae\u968f\u9910\u6216\u9910\u540e\u670d\uff1b\u82e5\u660e\u663e\u4e4f\u529b\u3001\u6076\u5fc3\u6216\u4f4e\u8840\u7cd6\u8868\u73b0\u8981\u8054\u7cfb\u533b\u62a4',
            nursing_note: '\u8001\u5e74\u7cd6\u5c3f\u75c5\u60a3\u8005\uff0c\u63d0\u9192\u89c4\u5f8b\u8fdb\u9910\uff0c\u4e0d\u8981\u81ea\u884c\u52a0\u51cf\u836f\u91cf\u3002',
            medications: [
              {
                medicine_name: '阿托伐他汀钙片',
                product_code: 'MED-ATORVASTATIN-20MG',
                product_model: '20 mg × 7片/盒',
                quantity: '1盒',
                trace_id: 'TRACE-B01-ATOR-0001',
                order_no: 'ORD-B01-001',
                dose: '20 mg',
                usage: '口服，每晚 1 次。用药期间如出现明显肌肉酸痛、尿色加深，请及时联系医生或药师。',
              },
              {
                medicine_name: '二甲双胍缓释片',
                product_code: 'MED-METFORMIN-XR-500MG',
                product_model: '500 mg × 10片/板',
                quantity: '2板',
                trace_id: 'TRACE-B01-METF-0002',
                order_no: 'ORD-B01-002',
                dose: '500 mg',
                usage: '口服，每日 2 次，随餐或餐后服用。若胃肠道反应明显，请告知护士或医生。',
              },
            ],
          },
          {
            patient_id: 'P-C01-001',
            patient_name: '王阿姨',
            age: 52,
            gender: '\u5973',
            height_cm: 162,
            weight_kg: 58,
            ward_id: 'ward_c',
            ward_name: 'C病房',
            bed_no: 'C-01',
            target_station: 'ward_c',
            prescription_no: 'RX-C01-TEST-001',
            diagnosis: '\u80c3\u98df\u7ba1\u53cd\u6d41\uff0c\u8179\u6cfb\u5f85\u89c2\u5bdf',
            allergies: '\u9752\u9709\u7d20\u8fc7\u654f\u53f2',
            contraindications: '\u8499\u8131\u77f3\u6563\u4e0e\u5176\u4ed6\u836f\u7269\u5efa\u8bae\u95f4\u9694\u670d\u7528\uff1b\u8179\u6cfb\u52a0\u91cd\u6216\u4fbf\u8840\u8981\u7acb\u5373\u8054\u7cfb\u533b\u62a4',
            nursing_note: '\u6ce8\u610f\u8865\u6c34\uff0c\u89c2\u5bdf\u8179\u75db\u3001\u53d1\u70ed\u548c\u5927\u4fbf\u6027\u72b6\u53d8\u5316\u3002',
            medications: [
              {
                medicine_name: '奥美拉唑肠溶胶囊',
                product_code: 'MED-OMEPRAZOLE-20MG',
                product_model: '20 mg × 14粒/盒',
                quantity: '1盒',
                trace_id: 'TRACE-C01-OME-0001',
                order_no: 'ORD-C01-001',
                dose: '20 mg',
                usage: '口服，每日 1 次，通常早餐前服用。不要自行长期加量，如症状加重请联系医生。',
              },
              {
                medicine_name: '蒙脱石散',
                product_code: 'MED-SMECTITE-3G',
                product_model: '3 g × 10袋/盒',
                quantity: '1盒',
                trace_id: 'TRACE-C01-SMEC-0002',
                order_no: 'ORD-C01-002',
                dose: '3 g',
                usage: '口服，按医嘱冲服。与其他药物同服时建议间隔一段时间，避免影响其他药物吸收。',
              },
            ],
          },
        ],
      };
    }

    function compactImportText(value) {
      return String(value ?? '').trim();
    }

    function importArray(value) {
      return Array.isArray(value) ? value : [];
    }

    function firstImportText(...values) {
      for (const value of values) {
        const text = compactImportText(value);
        if (text) return text;
      }
      return '';
    }

    function collectImportMedications(patient) {
      if (!patient || typeof patient !== 'object') return [];
      if (Array.isArray(patient.medications)) return patient.medications;
      if (Array.isArray(patient.medicines)) return patient.medicines;
      if (Array.isArray(patient.drugs)) return patient.drugs;
      return [];
    }

    function collectImportPatients(payload) {
      const rows = [];
      importArray(payload && payload.patients).forEach(patient => rows.push({ patient, stop: null }));
      importArray(payload && payload.stops).forEach(stop => {
        const patients = importArray(stop && stop.patients);
        if (!patients.length && stop && typeof stop === 'object') {
          const maybePatient = stop.patient || stop.patient_info || null;
          if (maybePatient && typeof maybePatient === 'object') rows.push({ patient: maybePatient, stop });
        }
        patients.forEach(patient => rows.push({ patient, stop }));
      });
      return rows;
    }

    function previewBatchImportPayload(payload) {
      const errors = [];
      const warnings = [];
      if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
        errors.push('\u6839\u8282\u70b9\u5fc5\u987b\u662f JSON \u5bf9\u8c61\u3002');
        return {
          ok: false,
          payload,
          errors,
          warnings,
          stats: { batchId: '-', wardCount: 0, patientCount: 0, medicationCount: 0, routeText: '-' },
        };
      }
      const hasPatientsField = Array.isArray(payload.patients);
      const hasStopsField = Array.isArray(payload.stops);
      if (!hasPatientsField && !hasStopsField) {
        errors.push('\u672a\u627e\u5230 patients \u6216 stops \u5b57\u6bb5\uff0c\u65e0\u6cd5\u751f\u6210\u914d\u9001\u6e05\u5355\u3002');
      }
      const rows = collectImportPatients(payload);
      if (!rows.length) {
        errors.push('\u672a\u627e\u5230\u60a3\u8005\u6570\u636e\uff0c\u8bf7\u81f3\u5c11\u63d0\u4f9b 1 \u4e2a\u60a3\u8005\u3002');
      }
      if (!firstImportText(payload.batch_id, payload.delivery_id, payload.id)) {
        warnings.push('\u7f3a\u5c11 batch_id\uff0c\u7cfb\u7edf\u53ef\u80fd\u4f1a\u4f7f\u7528\u81ea\u52a8\u6279\u6b21\u53f7\u3002');
      }
      if (!firstImportText(payload.source, payload.source_station, payload.origin)) {
        warnings.push('\u7f3a\u5c11\u6765\u6e90\u5b57\u6bb5\uff0c\u540e\u7eed\u5ba1\u8ba1\u65f6\u96be\u4ee5\u8ffd\u6eaf\u6765\u6e90\u7cfb\u7edf\u3002');
      }
      if (!Array.isArray(payload.route) && !rows.some(({ patient, stop }) => firstImportText(patient && patient.target_station, patient && patient.ward_name, stop && stop.stop_id, stop && stop.ward_name))) {
        warnings.push('\u672a\u63d0\u4f9b\u8def\u7ebf\u6216\u76ee\u6807\u75c5\u623f\uff0c\u91c7\u7528\u524d\u5efa\u8bae\u6838\u5bf9\u914d\u9001\u8def\u7ebf\u3002');
      }

      const beds = new Set();
      const duplicateBeds = new Set();
      const wards = new Set();
      let medicationCount = 0;
      let patientsWithoutMeds = 0;
      let medsWithoutIds = 0;

      rows.forEach(({ patient, stop }, index) => {
        const patientName = firstImportText(patient && patient.patient_name, patient && patient.name, patient && patient.full_name);
        const bedNo = firstImportText(patient && patient.bed_no, patient && patient.bed, patient && patient.bed_id, stop && stop.bed_no);
        const wardName = firstImportText(patient && patient.ward_name, patient && patient.ward_id, stop && stop.ward_name, stop && stop.stop_id, patient && patient.target_station);
        const label = [wardName, bedNo, patientName].filter(Boolean).join(' / ') || `#${index + 1}`;
        if (!patientName) errors.push(`\u60a3\u8005 ${label} \u7f3a\u5c11\u59d3\u540d\u5b57\u6bb5\u3002`);
        if (!bedNo) errors.push(`\u60a3\u8005 ${label} \u7f3a\u5c11\u5e8a\u4f4d\u5b57\u6bb5\u3002`);
        if (bedNo) {
          const bedKey = `${wardName || '-'}::${bedNo}`;
          if (beds.has(bedKey)) duplicateBeds.add(`${wardName || '-'} ${bedNo}`);
          beds.add(bedKey);
        }
        if (wardName) wards.add(wardName);
        const meds = collectImportMedications(patient);
        if (!meds.length) {
          patientsWithoutMeds += 1;
          errors.push(`\u60a3\u8005 ${label} \u6ca1\u6709\u836f\u54c1\u5217\u8868\u3002`);
        }
        medicationCount += meds.length;
        meds.forEach((med, medIndex) => {
          const medName = firstImportText(med && med.medicine_name, med && med.name, med && med.drug_name, med && med.medication_name);
          if (!medName) errors.push(`\u60a3\u8005 ${label} \u7b2c ${medIndex + 1} \u4e2a\u836f\u54c1\u7f3a\u5c11\u836f\u540d\u3002`);
          if (!firstImportText(med && med.product_code, med && med.trace_id, med && med.order_no, med && med.barcode)) medsWithoutIds += 1;
        });
      });
      if (duplicateBeds.size) {
        warnings.push(`\u68c0\u6d4b\u5230\u91cd\u590d\u5e8a\u4f4d\uff1a${Array.from(duplicateBeds).slice(0, 5).join('\u3001')}\u3002`);
      }
      if (patientsWithoutMeds && patientsWithoutMeds < rows.length) {
        warnings.push(`${patientsWithoutMeds} \u4e2a\u60a3\u8005\u6682\u65e0\u836f\u54c1\uff0c\u8bf7\u786e\u8ba4\u662f\u5426\u4e3a\u7a7a\u8ba2\u5355\u3002`);
      }
      if (medsWithoutIds) {
        warnings.push(`${medsWithoutIds} \u4e2a\u836f\u54c1\u7f3a\u5c11\u4ea7\u54c1\u7801/\u8ffd\u6eaf\u7801/\u8ba2\u5355\u53f7\uff0c\u53ef\u80fd\u5f71\u54cd\u626b\u7801\u5339\u914d\u3002`);
      }
      const routeValues = Array.isArray(payload.route)
        ? payload.route.map(value => compactImportText(value)).filter(Boolean)
        : [];
      const routeText = routeValues.length
        ? routeValues.slice(0, 6).join(' \u2192 ')
        : (Array.from(wards).slice(0, 6).join(' \u2192 ') || '-');
      return {
        ok: errors.length === 0,
        payload,
        errors,
        warnings,
        stats: {
          batchId: firstImportText(payload.batch_id, payload.delivery_id, payload.id) || '-',
          wardCount: wards.size,
          patientCount: rows.length,
          medicationCount,
          routeText: routeValues.length > 6 || wards.size > 6 ? `${routeText} ...` : routeText,
        },
      };
    }

    function renderBatchImportPreview(result) {
      const preview = document.getElementById('batch_import_preview');
      const badge = document.getElementById('batch_import_preview_badge');
      const hint = document.getElementById('batch_import_preview_hint');
      const issueList = document.getElementById('batch_import_preview_issues');
      const importButton = document.getElementById('import-batch-json');
      if (!preview || !badge || !hint || !issueList) return;
      const safeResult = result || { ok: false, payload: null };
      safeResult.errors = Array.isArray(safeResult.errors) ? safeResult.errors : [];
      safeResult.warnings = Array.isArray(safeResult.warnings) ? safeResult.warnings : [];
      safeResult.stats = safeResult.stats || { batchId: '-', wardCount: 0, patientCount: 0, medicationCount: 0, routeText: '-' };
      latestBatchImportPreview = safeResult;
      preview.classList.toggle('is-ok', Boolean(safeResult.ok && !safeResult.warnings.length));
      preview.classList.toggle('has-warn', Boolean(safeResult.ok && safeResult.warnings.length));
      preview.classList.toggle('has-error', Boolean(safeResult.errors && safeResult.errors.length));
      const canReceive = Boolean(safeResult.ok);
      if (importButton) importButton.disabled = !canReceive;
      if (!safeResult.payload) {
        badge.textContent = '\u672a\u9884\u89c8';
        badge.className = 'badge IDLE';
        hint.textContent = '\u8bf7\u5148\u586b\u5165\u6a21\u677f\u3001\u8f7d\u5165\u5f53\u524d\u6279\u6b21\u6216\u4ece\u672c\u5730\u6587\u4ef6\u9009\u62e9 JSON\u3002';
      } else if (safeResult.ok && safeResult.warnings.length) {
        badge.textContent = '\u53ef\u63a5\u6536\uff0c\u9700\u6838\u5bf9';
        badge.className = 'badge WAITING_LOAD_CONFIRMATION';
        hint.textContent = '\u683c\u5f0f\u53ef\u7528\uff0c\u4f46\u6709\u9700\u6838\u5bf9\u7684\u5b57\u6bb5\u3002';
      } else if (safeResult.ok) {
        badge.textContent = '\u53ef\u63a5\u6536';
        badge.className = 'badge COMPLETED';
        hint.textContent = '\u683c\u5f0f\u548c\u5173\u952e\u5b57\u6bb5\u68c0\u67e5\u901a\u8fc7\uff0c\u53ef\u63a5\u6536\u4e3a\u5f85\u91c7\u7528\u3002';
      } else {
        badge.textContent = '\u4e0d\u53ef\u63a5\u6536';
        badge.className = 'badge CANCELED';
        hint.textContent = '\u8bf7\u5148\u4fee\u6b63\u9519\u8bef\u5b57\u6bb5\uff0c\u518d\u63a5\u6536\u4e3a\u5f85\u91c7\u7528\u3002';
      }
      document.getElementById('batch_import_preview_batch').textContent = safeResult.stats.batchId || '-';
      document.getElementById('batch_import_preview_patients').textContent = `${safeResult.stats.wardCount || 0} / ${safeResult.stats.patientCount || 0}`;
      document.getElementById('batch_import_preview_meds').textContent = `${safeResult.stats.medicationCount || 0}`;
      document.getElementById('batch_import_preview_route').textContent = safeResult.stats.routeText || '-';
      issueList.innerHTML = '';
      const issues = [];
      (safeResult.errors || []).forEach(text => issues.push({ kind: 'error', text: `\u9519\u8bef\uff1a${text}` }));
      (safeResult.warnings || []).forEach(text => issues.push({ kind: 'warn', text: `\u63d0\u9192\uff1a${text}` }));
      if (!issues.length && safeResult.payload) {
        issues.push({ kind: 'ok', text: '\u5173\u952e\u5b57\u6bb5\u68c0\u67e5\u901a\u8fc7\u3002' });
      }
      issues.slice(0, 8).forEach(issue => {
        const li = document.createElement('li');
        li.className = issue.kind === 'error' ? 'issue-error' : (issue.kind === 'warn' ? 'issue-warn' : 'issue-ok');
        li.textContent = issue.text;
        issueList.appendChild(li);
      });
      if (issues.length > 8) {
        const li = document.createElement('li');
        li.className = 'issue-warn';
        li.textContent = `\u8fd8\u6709 ${issues.length - 8} \u6761\u95ee\u9898\u672a\u663e\u793a\uff0c\u8bf7\u4f18\u5148\u4fee\u6b63\u4e0a\u65b9\u9879\u3002`;
        issueList.appendChild(li);
      }
    }

    function clearBatchImportPreview() {
      latestBatchImportPreview = { ok: false, payload: null };
      renderBatchImportPreview(latestBatchImportPreview);
    }

    function previewBatchImportText(sourceLabel = '') {
      const text = document.getElementById('batch_import_text').value.trim();
      if (!text) {
        clearBatchImportPreview();
        return latestBatchImportPreview;
      }
      try {
        const payload = JSON.parse(text);
        const result = previewBatchImportPayload(payload);
        renderBatchImportPreview(result);
        if (sourceLabel) {
          setBatchImportMessage(result.ok
            ? `${sourceLabel}\u5df2\u8f7d\u5165\uff0c\u8bf7\u6838\u5bf9\u9884\u89c8\u540e\u518d\u63a5\u6536\u4e3a\u5f85\u91c7\u7528\u3002`
            : `${sourceLabel}\u5df2\u8f7d\u5165\uff0c\u4f46\u5b57\u6bb5\u6821\u9a8c\u672a\u901a\u8fc7\u3002`, result.ok);
        }
        return result;
      } catch (error) {
        const result = {
          ok: false,
          payload: {},
          errors: [`JSON \u89e3\u6790\u5931\u8d25\uff1a${error.message}`],
          warnings: [],
          stats: { batchId: '-', wardCount: 0, patientCount: 0, medicationCount: 0, routeText: '-' },
        };
        renderBatchImportPreview(result);
        if (sourceLabel) setBatchImportMessage(`${sourceLabel} JSON \u89e3\u6790\u5931\u8d25\uff1a${error.message}`, false);
        return result;
      }
    }

    function setBatchImportMessage(message, ok = true) {
      const element = document.getElementById('batch_import_result');
      element.textContent = message;
      element.style.color = ok ? 'var(--ok)' : 'var(--danger)';
    }

    function updatePendingBatchPanel(pending) {
      latestPendingBatch = pending || null;
      const summary = (pending && pending.summary) || {};
      const hasPending = Boolean(pending && pending.batch);
      document.getElementById('pending_batch_badge').textContent = hasPending ? '\u5f85\u91c7\u7528' : '\u65e0\u5f85\u91c7\u7528';
      document.getElementById('pending_batch_badge').className = hasPending ? 'badge WAITING_LOAD_CONFIRMATION' : 'badge IDLE';
      document.getElementById('pending_batch_source').textContent = hasPending ? (pending.source || '-') : '-';
      document.getElementById('pending_batch_id').textContent = hasPending ? (summary.batch_id || pending.raw_batch_id || '-') : '-';
      document.getElementById('pending_batch_received_at').textContent = hasPending ? (pending.received_at || '-') : '-';
      document.getElementById('pending_batch_counts').textContent = hasPending
        ? `${summary.patient_count || 0} \u4eba / ${summary.medication_count || 0} \u9879`
        : '-';
      document.getElementById('adopt-pending-batch').disabled = !hasPending;
      document.getElementById('discard-pending-batch').disabled = !hasPending;
    }

    async function refreshPendingBatch() {
      try {
        const data = await api('/api/delivery_batch/pending');
        updatePendingBatchPanel(data.pending || null);
      } catch (error) {
        log(`\u5f85\u91c7\u7528\u6279\u6b21\u5237\u65b0\u5931\u8d25\uff1a${error.message}`);
      }
    }

    async function refreshDeliveryBatch() {
      try {
        const [batch, pending, ovr, safetyLatest, backendGate] = await Promise.all([
          api('/api/delivery_batch'),
          api('/api/delivery_batch/pending').catch(() => ({ pending: null })),
          api('/api/patient_status_overrides').catch(() => ({ overrides: {} })),
          api('/api/delivery_batch/safety_self_test/latest').catch(() => ({ available: false })),
          api('/api/delivery_batch/safety_gate').catch(() => null),
        ]);
        latestPatientStatusOverrides = (ovr && ovr.overrides) || {};
        latestBackendSafetyGate = backendGate || null;
        updatePendingBatchPanel((pending && pending.pending) || null);
        renderSafetySelfTestResult(safetyLatest, 'safety_self_test_latest');
        if (!editingBatchPatientKey && !editingBatchMedicationKey) {
          updateDeliveryBatch(batch);
        }
      } catch (error) {
        log(`\u6279\u6b21\u72b6\u6001\u5237\u65b0\u5931\u8d25\uff1a${error.message}`);
      }
    }

    function findBatchPatientByKey(key) {
      const stops = latestDeliveryBatch?.stops || [];
      for (const stop of stops) {
        for (const patient of (stop.patients || [])) {
          if (batchPatientKey(patient) === key) return patient;
        }
      }
      return null;
    }


    function findBatchPatientById(patientId) {
      const id = String(patientId || '');
      const stops = latestDeliveryBatch?.stops || [];
      for (const stop of stops) {
        for (const patient of (stop.patients || [])) {
          if (String(patient.patient_id || '') === id) return { patient, stop };
        }
      }
      return { patient: null, stop: null };
    }

    function buildMedicationReviewConfirmText(patientId, action) {
      const found = findBatchPatientById(patientId);
      const patient = found.patient;
      if (!patient) {
        return action === 'return'
          ? '未找到该病人详细信息，确认退回药房？'
          : '未找到该病人详细信息，确认复核通过并继续配送？';
      }
      const bed = patient.bed_no || '-';
      const name = patient.patient_name || '-';
      const ward = (found.stop && (found.stop.display_name || found.stop.target_station)) || '-';
      const reason = patient.medication_review_reason || '病人反馈用药或个人信息可能有误';
      const meds = (patient.medications || []).map(item => {
        const qty = item.quantity || '-';
        const dose = item.dose || '-';
        const usage = item.usage || '-';
        return `- ${item.medicine_name || '-'}（${qty}；${dose} / ${usage}）`;
      }).join('\n') || '-';
      const actionText = action === 'return'
        ? '处理：退回药房，未交付药品将进入回收/异常审计。'
        : '处理：复核通过，该床位可继续配送和床旁交付。';
      return [
        `病人：${bed} ${name}`,
        `病房：${ward}`,
        `复核原因：${reason}`,
        '药品：',
        meds,
        '',
        actionText,
      ].join('\n');
    }

    function toggleBatchPatientEdit(key) {
      editingBatchPatientKey = editingBatchPatientKey === key ? '' : key;
      renderBatchStops(latestDeliveryBatch || {});
    }

    function cancelBatchPatientEdit() {
      editingBatchPatientKey = '';
      renderBatchStops(latestDeliveryBatch || {});
    }

    async function saveBatchPatientInfo(key) {
      const patient = findBatchPatientByKey(key);
      if (!patient) {
        log('\u672a\u627e\u5230\u8981\u4fdd\u5b58\u7684\u75c5\u4eba\u4fe1\u606f');
        return;
      }
      const panel = Array.from(document.querySelectorAll('[data-patient-edit-key]')).find(el => el.getAttribute('data-patient-edit-key') === key);
      if (!panel) return;
      const payload = {
        patient_id: patient.patient_id || '',
        bed_no: patient.bed_no || '',
      };
      panel.querySelectorAll('[data-patient-edit-field]').forEach(el => {
        const field = el.getAttribute('data-patient-edit-field');
        payload[field] = (el.value || '').trim();
      });
      const safeKey = key.replace(/[^a-zA-Z0-9_-]/g, '_');
      const messageEl = document.getElementById(`patient_edit_message_${safeKey}`);
      if (messageEl) {
        messageEl.textContent = '\u6b63\u5728\u4fdd\u5b58...';
        messageEl.style.color = 'var(--muted)';
      }
      try {
        const data = await api('/api/delivery_batch/update_patient', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
        latestDeliveryBatch = data.batch || latestDeliveryBatch;
        editingBatchPatientKey = '';
        updateDeliveryBatch(latestDeliveryBatch);
        const resultElement = document.getElementById('batch_action_result');
        if (resultElement) {
          resultElement.textContent = data.message || '\u75c5\u4eba\u4fe1\u606f\u5df2\u4fdd\u5b58';
          resultElement.style.color = 'var(--ok)';
        }
        log(data.message || '\u75c5\u4eba\u4fe1\u606f\u5df2\u4fdd\u5b58');
      } catch (error) {
        if (messageEl) {
          messageEl.textContent = `\u4fdd\u5b58\u5931\u8d25\uff1a${error.message}`;
          messageEl.style.color = 'var(--danger)';
        }
        log(`\u75c5\u4eba\u4fe1\u606f\u4fdd\u5b58\u5931\u8d25: ${error.message}`);
      }
    }

    function findBatchMedicationByKey(key) {
      const stops = latestDeliveryBatch?.stops || [];
      for (const stop of stops) {
        for (const patient of (stop.patients || [])) {
          for (const item of (patient.medications || [])) {
            if (batchMedicationKey(item) === key) return item;
          }
        }
      }
      return null;
    }

    function toggleBatchMedicationEdit(key) {
      editingBatchMedicationKey = editingBatchMedicationKey === key ? '' : key;
      renderBatchStops(latestDeliveryBatch || {});
    }

    function cancelBatchMedicationEdit() {
      editingBatchMedicationKey = '';
      renderBatchStops(latestDeliveryBatch || {});
    }

    async function saveBatchMedicationInfo(key) {
      const item = findBatchMedicationByKey(key);
      if (!item) {
        log('\u672a\u627e\u5230\u8981\u4fdd\u5b58\u7684\u836f\u54c1');
        return;
      }
      const panel = Array.from(document.querySelectorAll('[data-med-edit-key]')).find(el => el.getAttribute('data-med-edit-key') === key);
      if (!panel) return;
      const payload = {
        medication_id: item.id || '',
        product_code: item.product_code || '',
        trace_id: item.trace_id || '',
      };
      panel.querySelectorAll('[data-med-edit-field]').forEach(el => {
        const field = el.getAttribute('data-med-edit-field');
        payload[field] = (el.value || '').trim();
      });
      const safeKey = key.replace(/[^a-zA-Z0-9_-]/g, '_');
      const messageEl = document.getElementById(`med_edit_message_${safeKey}`);
      if (messageEl) {
        messageEl.textContent = '\u6b63\u5728\u4fdd\u5b58...';
        messageEl.style.color = 'var(--muted)';
      }
      try {
        const data = await api('/api/delivery_batch/update_medication', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
        latestDeliveryBatch = data.batch || latestDeliveryBatch;
        editingBatchMedicationKey = '';
        updateDeliveryBatch(latestDeliveryBatch);
        const resultElement = document.getElementById('batch_action_result');
        if (resultElement) {
          resultElement.textContent = data.message || '\u836f\u54c1\u8bf4\u660e\u5df2\u4fdd\u5b58';
          resultElement.style.color = 'var(--ok)';
        }
        log(data.message || '\u836f\u54c1\u8bf4\u660e\u5df2\u4fdd\u5b58');
      } catch (error) {
        if (messageEl) {
          messageEl.textContent = `\u4fdd\u5b58\u5931\u8d25\uff1a${error.message}`;
          messageEl.style.color = 'var(--danger)';
        }
        log(`\u836f\u54c1\u8bf4\u660e\u4fdd\u5b58\u5931\u8d25: ${error.message}`);
      }
    }

    async function postBatchAction(path, successPrefix, options = {}) {
      const payload = {};
      if (options.scanPayload && typeof options.scanPayload === 'object') {
        Object.assign(payload, options.scanPayload);
      } else if (options.requireScan) {
        await refreshDrugInfo();
        Object.assign(payload, currentScannedKey({ requireFresh: true, requireCode: true }));
        payload.medicine_name = getRecognizedMedicineName(latestDrugInfo || {}) || '';
      }
      const data = await api(path, { method: 'POST', body: JSON.stringify(payload) });
      updateDeliveryBatch(data.batch || data);
      const message = data.message || '\u6279\u6b21\u72b6\u6001\u5df2\u66f4\u65b0';
      const resultElement = document.getElementById('batch_action_result');
      resultElement.textContent = `${successPrefix}\uff1a${message}`;
      resultElement.style.color = data.ok === false ? 'var(--danger)' : 'var(--ok)';
      log(`${successPrefix}\uff1a${message}`);
    }

    async function postBatchException(payload, successPrefix) {
      const beforeCount = countBatchExceptions(latestDeliveryBatch);
      const data = await api('/api/delivery_batch/exception', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      const nextBatch = data.batch || data;
      const afterCount = countBatchExceptions(nextBatch);
      latestExceptionResolutionSummary = buildResolutionSummary(successPrefix, beforeCount, afterCount, nextBatch);
      updateDeliveryBatch(nextBatch);
      renderBatchAudit((latestDeliveryBatch && latestDeliveryBatch.audit_records) || []);
      const message = data.message || '\u5f02\u5e38\u72b6\u6001\u5df2\u66f4\u65b0';
      const resultElement = document.getElementById('batch_action_result');
      const summary = resolutionSummaryText(latestExceptionResolutionSummary);
      resultElement.textContent = `${successPrefix}\uff1a${message}${summary ? '\uff1b' + summary : ''}`;
      resultElement.style.color = data.ok === false ? 'var(--danger)' : 'var(--ok)';
      log(`${successPrefix}\uff1a${message}`);
    }

    async function postPatientMedicationReview(payload, successPrefix) {
      const beforeCount = countBatchExceptions(latestDeliveryBatch);
      const data = await api('/api/delivery_batch/resolve_review', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      const nextBatch = data.batch || data;
      const afterCount = countBatchExceptions(nextBatch);
      latestExceptionResolutionSummary = buildResolutionSummary(successPrefix, beforeCount, afterCount, nextBatch);
      updateDeliveryBatch(nextBatch);
      await refreshPatientStatusOverrides();
      updateDemoReviewGuide(latestDeliveryBatch);
      const auditFilter = document.getElementById('batch_audit_filter');
      if (auditFilter) {
        auditFilter.value = 'medication_review';
        latestAuditFilter = 'medication_review';
        renderBatchAudit((latestDeliveryBatch && latestDeliveryBatch.audit_records) || []);
      }
      const message = data.message || '\u590d\u6838\u72b6\u6001\u5df2\u66f4\u65b0';
      const resultElement = document.getElementById('batch_action_result');
      const summary = resolutionSummaryText(latestExceptionResolutionSummary);
      resultElement.textContent = `${successPrefix}\uff1a${message}\u3002${summary ? summary + '\u3002' : ''}\u5df2\u5199\u5165\u5ba1\u8ba1\u7559\u75d5\uff0c\u53ef\u70b9\u51fb\u201c\u67e5\u770b\u7559\u75d5\u201d\u786e\u8ba4\u3002`;
      resultElement.style.color = data.ok === false ? 'var(--danger)' : 'var(--ok)';
    }



    async function continuePatientMedicationReview(patientId) {
      try {
        if (!confirmCriticalAction('确认复核通过并继续配送？', buildMedicationReviewConfirmText(patientId, 'continue'))) return;
        await postPatientMedicationReview({
          action: 'continue',
          patient_id: patientId,
          reason: '护士核对通过，继续配送',
        }, '用药复核通过');
      } catch (error) {
        log(`用药复核通过失败：${error.message}`);
      }
    }

    async function returnPatientMedicationReview(patientId) {
      try {
        if (!confirmCriticalAction('确认退回药房？', buildMedicationReviewConfirmText(patientId, 'return'))) return;
        await postPatientMedicationReview({
          action: 'return',
          patient_id: patientId,
          reason: '病人反馈信息有误，退回药房复核',
        }, '已退回药房');
      } catch (error) {
        log(`退回药房失败：${error.message}`);
      }
    }

    async function markBatchPatientAbsent(patientId) {
      try {
        if (!confirmCriticalAction('确认标记病人不在？', '该床位本轮药品会暂停交付，并写入审计记录，后续需要医护或药师处理。')) return;
        await postBatchException({
          action: 'patient_absent',
          patient_id: patientId,
          reason: '病人不在，暂不交付',
        }, '病人不在');
      } catch (error) {
        log(`标记病人不在失败：${error.message}`);
      }
    }

    async function markBatchMedicationException(medicationId) {
      try {
        if (!confirmCriticalAction('确认登记药品异常？', '该药品会从正常交付流程中移出，并进入人工处理/药师复核闭环。')) return;
        await postBatchException({
          action: 'drug_exception',
          medication_id: medicationId,
          reason: '药品异常，转人工处理',
        }, '药品异常');
      } catch (error) {
        log(`标记药品异常失败：${error.message}`);
      }
    }

    async function markBatchMedicationReturn(medicationId) {
      try {
        if (!confirmCriticalAction('确认未交付回收？', '该药品会标记为回收状态，并写入审计记录，不建议随意撤销。')) return;
        await postBatchException({
          action: 'return',
          medication_id: medicationId,
          reason: '未交付，回药房回收',
        }, '未交付回收');
      } catch (error) {
        log(`标记未交付回收失败：${error.message}`);
      }
    }

    async function retryBatchPatientException(patientId) {
      try {
        if (!confirmCriticalAction('确认稍后重试该病人？', '该病人的异常状态会被清理，并重新进入床旁交付流程。')) return;
        await postBatchException({
          action: 'retry',
          patient_id: patientId,
          reason: '稍后重试，重新进入交付流程',
        }, '稍后重试');
      } catch (error) {
        log(`病人稍后重试失败：${error.message}`);
      }
    }

    async function clearBatchPatientException(patientId) {
      try {
        if (!confirmCriticalAction('确认解除该病人异常？', '该操作会写入审计记录，表示异常已被人工复核通过。')) return;
        await postBatchException({
          action: 'clear_exception',
          patient_id: patientId,
          reason: '异常解除，重新进入交付流程',
        }, '复核通过');
      } catch (error) {
        log(`解除病人异常失败：${error.message}`);
      }
    }

    async function reviewBatchPatientException(patientId) {
      try {
        if (!confirmCriticalAction('确认药师复核该病人记录？', '该病人相关异常/回收药品会标记为药师已复核，并进入审计报告。')) return;
        await postBatchException({
          action: 'manual_review',
          patient_id: patientId,
          reason: '药师复核通过，已记录审计',
        }, '药师复核');
      } catch (error) {
        log(`病人药师复核失败：${error.message}`);
      }
    }

    async function retryBatchMedicationException(medicationId) {
      try {
        if (!confirmCriticalAction('确认稍后重试该药品？', '该药品的异常状态会被清理，并重新进入交付流程。')) return;
        await postBatchException({
          action: 'retry',
          medication_id: medicationId,
          reason: '稍后重试，重新进入交付流程',
        }, '稍后重试');
      } catch (error) {
        log(`药品稍后重试失败：${error.message}`);
      }
    }

    async function clearBatchMedicationException(medicationId) {
      try {
        if (!confirmCriticalAction('确认解除该药品异常？', '该操作会写入审计记录，表示该药品异常已人工复核通过。')) return;
        await postBatchException({
          action: 'clear_exception',
          medication_id: medicationId,
          reason: '异常解除，重新进入交付流程',
        }, '复核通过');
      } catch (error) {
        log(`解除药品异常失败：${error.message}`);
      }
    }

    async function reviewBatchMedicationException(medicationId) {
      try {
        if (!confirmCriticalAction('确认药师复核该药品？', '该药品会标记为药师已复核，作为审计报告归档依据。')) return;
        await postBatchException({
          action: 'manual_review',
          medication_id: medicationId,
          reason: '药师复核通过，已记录审计',
        }, '药师复核');
      } catch (error) {
        log(`药品药师复核失败：${error.message}`);
      }
    }

    function updateVerificationRecords(records) {
      const container = document.getElementById('verification_records');
      const parsed = records.map(item => {
        if (typeof item === 'string') {
          try {
            return JSON.parse(item);
          } catch (error) {
            return null;
          }
        }
        return item;
      }).filter(Boolean).slice(-8).reverse();
      if (!parsed.length) {
        container.innerHTML = '<div class="audit-item"><div class="audit-detail">暂无扫码确认记录</div></div>';
        return;
      }
      container.innerHTML = parsed.map(record => {
        const passed = Boolean(record.passed);
        const productMatch = record.product_code_matched ? '产品编码一致' : '产品编码不一致';
        const traceMatch = record.trace_id_matched ? '追溯编号一致' : '追溯编号不一致';
        const statusClass = passed ? 'audit-pass' : 'audit-fail';
        const statusText = passed ? '通过' : '失败';
        const expected = `${record.expected_product_code || '-'} / ${record.expected_trace_id || '-'}`;
        const scanned = `${record.scanned_product_code || '-'} / ${record.scanned_trace_id || '-'}`;
        const matchedName = record.matched_medicine_name ? `；匹配药品：${record.matched_medicine_name}` : '';
        return `<div class="audit-item">
          <div class="audit-head">
            <span>${escapeHtml(record.time || '-')} ${escapeHtml(formatVerificationStage(record.stage))}</span>
            <span class="${statusClass}">${statusText}</span>
          </div>
          <div class="audit-detail">${escapeHtml(record.message || '-')}${escapeHtml(matchedName)}；${productMatch}；${traceMatch}</div>
          <div class="audit-detail">期望：${escapeHtml(expected)}</div>
          <div class="audit-detail">扫码：${escapeHtml(scanned)}</div>
        </div>`;
      }).join('');
    }

    function updateVerifyResult(data) {
      const result = document.getElementById('verify_result');
      const productStatus = data.product_code_matched ? '产品编码一致' : '产品编码不一致';
      const traceStatus = data.trace_id_matched ? '追溯编号一致' : '追溯编号不一致';
      const stage = data.stage || 'scan';
      const taskState = data.task_state ? `；任务状态 ${data.task_state}` : '';
      const confirmedAt = data.confirmed_at ? `；确认时间 ${data.confirmed_at}` : '';
      const matchedName = data.matched_medicine_name ? `；匹配药品 ${data.matched_medicine_name}` : '';
      const progress = data.medication_total_count ? `；清单进度 ${data.medication_verified_count}/${data.medication_total_count}` : '';
      result.textContent = `${data.verified ? '校验通过' : '校验失败'}：${data.message}；阶段 ${stage}；${productStatus}；${traceStatus}${matchedName}${progress}${taskState}${confirmedAt}`;
      result.style.color = data.verified ? 'var(--ok)' : 'var(--danger)';
    }

    async function verifyByStage(stage, successLabel, failLabel) {
      await refreshDrugInfo();
      const scan = currentScannedKey({ requireFresh: true, requireCode: true });
      const payload = {
        task_id: latestTaskId,
        product_code: scan.product_code,
        trace_id: scan.trace_id,
        stage,
      };
      const data = await api('/api/verify_task', { method: 'POST', body: JSON.stringify(payload) });
      updateVerifyResult(data);
      log(`${data.verified ? successLabel : failLabel}：${data.message}`);
      await refreshState();
    }

    function isFreshOcrResult(data = latestDrugInfo) {
      const age = Number(data?.ocr_age_sec);
      if (!Number.isFinite(age)) return Boolean(data?.ocr_runtime_enabled || data?.ocr_single_shot_pending);
      return age >= 0 && age <= 15;
    }

    function hasExplicitMedicineRecognition(data = latestDrugInfo) {
      const sourceText = String(data?.recognition_source || data?.source || '').toLowerCase();
      const channel = String(data?.recognition_channel || '').toLowerCase();
      return Boolean(
        channel
        || sourceText.includes('ocr')
        || sourceText.includes('barcode')
        || sourceText.includes('qr')
        || sourceText.includes('datamatrix')
        || data?.label_product_code
        || data?.raw_code_text
        || data?.code_text
        || data?.trace_code
        || data?.label_trace_id
      );
    }

    function getRecognizedMedicineName(data) {
      const ocrName = String(data.ocr_drug_name || '').trim();
      if (ocrName && isFreshOcrResult(data)) {
        return ocrName;
      }
      if (data.drug_type && data.drug_type !== 'unknown' && data.drug_name && hasExplicitMedicineRecognition(data)) {
        return String(data.drug_name || '').trim();
      }
      return '';
    }

    function getTaskMedicineName() {
      const data = latestDrugInfo || {};
      const baseName = medicineNameInput.value.trim() || getRecognizedMedicineName(data) || '常规药品';
      return baseName;
    }

    function getTaskRecognitionFields() {
      const data = latestDrugInfo || {};
      const stableProduct = String(data.stable_product_code || '').trim();
      const stableTrace = String(data.stable_trace_code || '').trim();
      const productCode = String(
        data.label_product_code
        || stableProduct
        || data.raw_code_text
        || data.code_text
        || ''
      ).trim();
      const traceId = String(
        data.trace_code
        || data.label_trace_id
        || stableTrace
        || ''
      ).trim();
      return {
        product_code: productCode,
        product_model: data.ocr_spec || data.label_product_model || '',
        quantity: data.label_quantity || '',
        trace_id: traceId,
        order_no: data.label_order_no || '',
        recognition_channel: data.recognition_channel || '',
        needs_review: Boolean(data.needs_review),
      };
    }

    function getScanAgeSec() {
      const data = latestDrugInfo || {};
      const age = Number(data.scan_age_sec);
      if (Number.isFinite(age) && age >= 0) {
        return age;
      }
      return null;
    }

    function getSelectedPatientOrder() {
      const patientId = document.getElementById('patient_order').value;
      return patientOrders.find(order => order.patient_id === patientId) || patientOrders[0] || null;
    }

    function normalizeMedicationForTask(item) {
      return {
        id: item.id || '',
        medicine_name: item.medicine_name || '',
        product_code: item.product_code || '',
        product_model: item.product_model || '',
        quantity: item.quantity || '',
        trace_id: item.trace_id || '',
        order_no: item.order_no || '',
        dose: item.dose || '',
        usage: item.usage || '',
      };
    }

    function normalizeRecognitionText(value) {
      return String(value || '')
        .toLowerCase()
        .replace(/[\s\-_/\\.\u00b7:\uFF1A,\uFF0C;\uFF1B()\uFF08\uFF09\u3010\u3011\[\]{}]/g, '')
        .replace(/(\u80A0\u6EB6\u80F6\u56CA|\u5206\u6563\u7247|\u7F13\u91CA\u7247|\u53E3\u670D\u6DB2|\u6CE8\u5C04\u6DB2|\u80F6\u56CA|\u9897\u7C92|\u6EB6\u6DB2|\u7247)$/g, '');
    }

    function recognitionTextMatches(expected, actual) {
      const left = normalizeRecognitionText(expected);
      const right = normalizeRecognitionText(actual);
      if (!left || !right || Math.min(left.length, right.length) < 2) {
        return false;
      }
      return left === right || left.includes(right) || right.includes(left);
    }

    function currentScannedKey(options = {}) {
      const fields = getTaskRecognitionFields();
      const age = getScanAgeSec();
      const codeStale = age !== null && age > SCAN_MAX_AGE_SEC;
      const allowStale = options.allowStale === true;
      const scan = {
        medicine_name: getRecognizedMedicineName(latestDrugInfo || {}),
        product_code: codeStale && !allowStale ? '' : (fields.product_code || ''),
        trace_id: codeStale && !allowStale ? '' : (fields.trace_id || ''),
        recognition_channel: fields.recognition_channel || '',
        needs_review: Boolean(fields.needs_review),
        age_sec: age,
        code_stale: codeStale,
      };
      const hasRecognition = Boolean(scan.medicine_name || scan.product_code || scan.trace_id);
      if (options.requireFresh && !hasRecognition) {
        throw new Error('\u8bf7\u5148\u5c06\u836f\u54c1\u653e\u5165\u8bc6\u522b\u6846\uff0c\u7b49\u5f85\u8bc6\u522b\u7ed3\u679c\u3002');
      }
      if (options.requireCode && !(scan.product_code || scan.trace_id)) {
        if (codeStale) {
          throw new Error(`\u6761\u7801/\u8ffd\u6eaf\u7801\u5df2\u8d85\u8fc7 ${Math.round(age || 0)} \u79d2\uff0c\u8bf7\u91cd\u65b0\u5bf9\u51c6\u836f\u54c1\u626b\u7801\u3002`);
        }
        throw new Error('\u5df2\u8bc6\u522b OCR \u836f\u540d\uff0c\u4f46\u672a\u8bfb\u5230\u6761\u7801/\u8ffd\u6eaf\u7801\uff0c\u8bf7\u5bf9\u51c6\u6761\u7801\u533a\u57df\u3002');
      }
      if (options.requireFresh && codeStale && !scan.medicine_name) {
        throw new Error(`\u8bc6\u522b\u7ed3\u679c\u5df2\u8d85\u8fc7 ${Math.round(age || 0)} \u79d2\uff0c\u8bf7\u91cd\u65b0\u5bf9\u51c6\u836f\u54c1\u3002`);
      }
      return scan;
    }

    function medicationMatchesScan(item, scan) {
      const expectedProductCode = String(item.product_code || '').trim();
      const expectedTraceId = String(item.trace_id || '').trim();
      const expectedName = String(item.medicine_name || '').trim();
      const scannedProduct = String(scan.product_code || '').trim();
      const scannedTrace = String(scan.trace_id || '').trim();
      const scannedName = String(scan.medicine_name || '').trim();
      const productMismatch = expectedProductCode && scannedProduct && scannedProduct !== expectedProductCode;
      const traceMismatch = expectedTraceId && scannedTrace && scannedTrace !== expectedTraceId;
      if (productMismatch || traceMismatch) {
        return false;
      }
      const productOk = Boolean(expectedProductCode && scannedProduct && scannedProduct === expectedProductCode);
      const traceOk = Boolean(expectedTraceId && scannedTrace && scannedTrace === expectedTraceId);
      const nameOk = recognitionTextMatches(expectedName, scannedName);
      return productOk || traceOk || nameOk;
    }

    function batchMedicationMatchesScan(item, scan, allowName = false) {
      const expectedProductCode = String(item.product_code || '').trim();
      const expectedTraceId = String(item.trace_id || '').trim();
      const scannedProduct = String(scan.product_code || '').trim();
      const scannedTrace = String(scan.trace_id || '').trim();
      const productMismatch = expectedProductCode && scannedProduct && scannedProduct !== expectedProductCode;
      const traceMismatch = expectedTraceId && scannedTrace && scannedTrace !== expectedTraceId;
      if (productMismatch || traceMismatch) return false;
      const productOk = Boolean(expectedProductCode && scannedProduct && scannedProduct === expectedProductCode);
      const traceOk = Boolean(expectedTraceId && scannedTrace && scannedTrace === expectedTraceId);
      const nameOk = allowName && recognitionTextMatches(item.medicine_name || '', scan.medicine_name || '');
      return productOk || traceOk || nameOk;
    }

    function findBatchMedicationByScan(scan, mode = 'load') {
      const batch = latestDeliveryBatch || {};
      const matches = [];
      const activeIndex = Number(batch.active_stop_index ?? -1);
      const activeStop = activeIndex >= 0 && Array.isArray(batch.stops) ? batch.stops[activeIndex] : null;
      const activeStation = activeStop ? String(activeStop.target_station || '') : '';
      (batch.stops || []).forEach(stop => {
        (stop.patients || []).forEach(patient => {
          (patient.medications || []).forEach(med => {
            if (!batchMedicationMatchesScan(med, scan, !(scan.product_code || scan.trace_id))) return;
            if (med.returned || med.exception) return;
            if (mode === 'load' && med.loaded) return;
            if (mode === 'dispense') {
              if (med.dispensed) return;
              if (activeStation && String(stop.target_station || '') !== activeStation) return;
            }
            matches.push({ stop, patient, medication: med });
          });
        });
      });
      return matches;
    }

    function updateRecognitionStability(signature) {
      const now = Date.now();
      const clean = String(signature || '').trim();
      if (!clean) {
        recognitionStability = { signature: '', count: 0, lastSeenAt: now };
        return { stable: false, count: 0 };
      }
      if (recognitionStability.signature === clean && now - recognitionStability.lastSeenAt < 15000) {
        recognitionStability.count += 1;
      } else {
        recognitionStability = { signature: clean, count: 1, lastSeenAt: now };
      }
      recognitionStability.lastSeenAt = now;
      return { stable: recognitionStability.count >= 2, count: recognitionStability.count };
    }

    function confidenceClassFromBackend(backend = {}) {
      const level = String(backend.recognition_confidence || '').toLowerCase();
      if (level === 'high') return 'low';
      if (level === 'medium') return 'medium';
      if (level === 'low' || level === 'none') return 'high';
      if (level === 'pending') return 'medium';
      return '';
    }

    function confidenceTitleFromBackend(backend = {}) {
      const label = backend.recognition_confidence_label || '';
      if (label) return label;
      const level = String(backend.recognition_confidence || '').toLowerCase();
      if (level === 'high') return '\u9ad8\u53ef\u4fe1\u00b7\u53ef\u5199\u5165';
      if (level === 'medium') return '\u4e2d\u53ef\u4fe1\u00b7\u9700\u590d\u6838';
      if (level === 'low') return '\u4f4e\u53ef\u4fe1\u00b7\u4ec5\u8f85\u52a9';
      if (level === 'none') return '\u672a\u5339\u914d\u00b7\u4e0d\u53ef\u91c7\u7528';
      if (level === 'pending') return '\u5f85\u8bc6\u522b\u00b7\u8bc1\u636e\u4e0d\u8db3';
      return '\u5f85\u5224\u5b9a';
    }

    function updateRecognitionStateCard(model = latestBatchScanPreviewModel) {
      const card = document.getElementById('recognition_state_card');
      if (!card) return;
      const title = document.getElementById('recognition_state_title');
      const body = document.getElementById('recognition_state_body');
      const badge = document.getElementById('recognition_stability_badge');
      const safe = model || {};
      const backend = safe.backend || {};
      const signature = [backend.status || safe.badge || '', backend.medicine_match_source || '', safe.code || '', safe.medication || '', safe.patient || ''].join('|');
      const localStableInfo = updateRecognitionStability(signature);
      const backendStableKnown = latestDrugInfo && Number(latestDrugInfo.recognition_stable_required || 0) > 0;
      const stableInfo = backendStableKnown
        ? {
          stable: Boolean(latestDrugInfo.recognition_stable),
          count: Number(latestDrugInfo.recognition_stable_count || 0),
          required: Number(latestDrugInfo.recognition_stable_required || 0),
          backend: true,
        }
        : localStableInfo;
      const source = String(backend.medicine_match_source || '').trim();
      const risk = String(backend.match_risk || '').toUpperCase();
      const confidenceLevel = String(backend.recognition_confidence || '').toLowerCase();
      let stateClass = confidenceClassFromBackend(backend);
      let stateTitle = confidenceTitleFromBackend(backend);
      let stateBody = [backend.recognition_confidence_reason, backend.recommended_action].filter(Boolean).join(' \u00b7 ');
      if (!stateBody) {
        stateTitle = '\u7b49\u5f85\u8bc6\u522b';
        stateBody = '\u8bf7\u5c06\u836f\u76d2\u6587\u5b57\u6216\u6761\u5f62\u7801\u653e\u5165\u8bc6\u522b\u6846\uff0c\u7cfb\u7edf\u4f1a\u5224\u65ad\u662f\u5426\u5c5e\u4e8e\u5f53\u524d\u914d\u9001\u6279\u6b21\u3002';
      }
      if (!confidenceLevel) {
        if (source === 'code' && backend.write_allowed === true) {
          stateClass = 'low';
          stateTitle = '\u6761\u7801\u5df2\u786e\u8ba4\uff1a\u6279\u6b21\u5185\u836f\u54c1';
          stateBody = backend.safety_note || '\u4ea7\u54c1\u7801/\u8ffd\u6eaf\u7801\u5df2\u5339\u914d\u5f53\u524d\u914d\u9001\u6279\u6b21\uff0c\u53ef\u6309\u6d41\u7a0b\u88c5\u836f\u6216\u4ea4\u4ed8\u3002';
        } else if (source === 'ocr_name' && safe.medication) {
          stateClass = risk === 'HIGH' ? 'high' : 'medium';
          stateTitle = risk === 'HIGH' ? '\u9ad8\u98ce\u9669\uff1a\u4ec5 OCR \u8f85\u52a9\u5339\u914d' : '\u9700\u590d\u6838\uff1aOCR \u8f85\u52a9\u5339\u914d';
          stateBody = backend.safety_note || 'OCR \u836f\u540d\u53ea\u4f5c\u4e3a\u5019\u9009\u63d0\u793a\uff0c\u5199\u5165\u8bb0\u5f55\u524d\u9700\u8981\u626b\u7801\u6216\u4eba\u5de5\u590d\u6838\u3002';
        } else if (backend.status === 'NO_MATCH' || backend.status === 'NAME_NO_MATCH') {
          stateClass = 'high';
          stateTitle = '\u6279\u6b21\u5916\u6216\u672a\u5339\u914d';
          stateBody = backend.message || '\u5f53\u524d\u8bc6\u522b\u7ed3\u679c\u672a\u5339\u914d\u914d\u9001\u6279\u6b21\uff0c\u8bf7\u6838\u5bf9\u836f\u54c1\u6216\u91cd\u65b0\u8bc6\u522b\u3002';
        } else if (safe.code && safe.code !== '-') {
          stateClass = 'medium';
          stateTitle = '\u5df2\u8bc6\u522b\uff0c\u7b49\u5f85\u6279\u6b21\u786e\u8ba4';
          stateBody = safe.action || '\u5df2\u6536\u5230\u8bc6\u522b\u7ed3\u679c\uff0c\u8bf7\u7b49\u5f85\u6279\u6b21\u5339\u914d\u3002';
        }
      }
      card.className = `recognition-state-card ${stateClass}`.trim();
      if (title) title.textContent = stateTitle;
      if (body) body.textContent = stateBody;
      if (badge) {
        const requiredText = stableInfo.required ? `/${stableInfo.required}` : '';
        const sourceText = stableInfo.backend ? '\u540e\u7aef' : '\u524d\u7aef';
        badge.textContent = stableInfo.stable
          ? `\u7a33\u5b9a\u8bc6\u522b\uff1a${stableInfo.count}${requiredText}\uff08${sourceText}\uff09`
          : `\u786e\u8ba4\u4e2d\uff1a${stableInfo.count || 0}${requiredText}\uff08${sourceText}\uff09`;
      }
    }

    function getRecognitionReviewStateText(data = latestDrugInfo, model = latestBatchScanPreviewModel) {
      const backend = (model && model.backend) ? model.backend : {};
      const confidenceLabel = String(backend.recognition_confidence_label || '').trim();
      const recommendedAction = String(backend.recommended_action || '').trim();
      const safetyNote = String(backend.safety_note || '').trim();
      const canCommit = backend.can_commit === true;
      const writeAllowed = backend.write_allowed === true;
      const hasRecognition = Boolean(
        data && (data.drug_name || data.ocr_drug_name || data.trace_code || data.label_product_code || data.raw_code_text || data.code_text)
      );
      if (canCommit && writeAllowed) {
        return confidenceLabel || '\u6761\u7801/\u8ffd\u6eaf\u7801\u5df2\u786e\u8ba4\uff0c\u5141\u8bb8\u5199\u5165';
      }
      if (backend.needs_manual_review === true || backend.write_allowed === false) {
        return confidenceLabel || recommendedAction || safetyNote || '\u9700\u8981\u4eba\u5de5\u786e\u8ba4';
      }
      return data && data.needs_review ? '\u9700\u8981\u4eba\u5de5\u786e\u8ba4' : (hasRecognition ? '\u53ef\u7528' : '-');
    }

    function updateRecognitionReviewStateText(data = latestDrugInfo, model = latestBatchScanPreviewModel) {
      const reviewEl = document.getElementById('recognition_review_state');
      if (reviewEl) reviewEl.textContent = getRecognitionReviewStateText(data, model);
    }

    function setBatchScanPreview(model) {
      const panel = document.getElementById('batch_scan_preview');
      if (!panel) return;
      const safe = model || {};
      latestBatchScanPreviewModel = safe;
      updateRecognitionReviewStateText(latestDrugInfo, safe);
      panel.className = `batch-scan-preview ${safe.tone || ''}`.trim();
      const setText = (id, value) => { const el = document.getElementById(id); if (el) el.textContent = value || '-'; };
      setText('batch_scan_preview_title', safe.title || '\u5f53\u524d\u8bc6\u522b\u5339\u914d');
      setText('batch_scan_preview_hint', safe.hint || '\u5c06\u836f\u76d2\u6761\u5f62\u7801\u6216\u8ffd\u6eaf\u7801\u653e\u5165\u8bc6\u522b\u6846\uff0c\u7cfb\u7edf\u4f1a\u5148\u9884\u89c8\u5339\u914d\u7684\u6279\u6b21\u836f\u54c1\u3002');
      setText('batch_scan_preview_code', safe.code || '-');
      setText('batch_scan_preview_med', safe.medication || '-');
      setText('batch_scan_preview_patient', safe.patient || '-');
      setText('batch_scan_preview_confidence', safe.confidence || (safe.backend && safe.backend.recognition_confidence_label) || '-');
      setText('batch_scan_preview_action', safe.action || '-');
      const ocrBatchMatch = document.getElementById('ocr_batch_match');
      if (ocrBatchMatch) {
        if (safe.backend && safe.backend.medicine_match_source === 'ocr_name' && safe.medication) {
          const score = Number(safe.backend.medicine_match_score || 0);
          const risk = String(safe.backend.match_risk || '').toUpperCase();
          const riskText = risk === 'HIGH' ? '高风险辅助匹配' : (risk === 'MEDIUM' ? '需复核辅助匹配' : '辅助匹配');
          const reason = safe.backend.match_reason ? `\uFF1B${safe.backend.match_reason}` : '';
          ocrBatchMatch.textContent = `${riskText}\uFF1A${safe.medication} / ${safe.patient || '-'}${score ? `\uFF08${score.toFixed(2)}\uFF09` : ''}${reason}`;
          ocrBatchMatch.className = risk === 'HIGH' ? 'audit-fail' : 'audit-detail';
        } else if (safe.backend && safe.backend.medicine_match_source === 'code' && safe.medication) {
          ocrBatchMatch.textContent = `条码已匹配当前批次：${safe.medication} / ${safe.patient || '-'}`;
          ocrBatchMatch.className = 'audit-pass';
        } else if (safe.backend && (safe.backend.status === 'NAME_NO_MATCH' || safe.backend.status === 'NO_MATCH')) {
          ocrBatchMatch.textContent = safe.backend.message || '未匹配当前批次';
          ocrBatchMatch.className = 'audit-fail';
        } else if (safe.backend && safe.backend.status === 'NO_CODE_OR_NAME') {
          ocrBatchMatch.textContent = '-';
          ocrBatchMatch.className = '';
        }
      }
      const badge = document.getElementById('batch_scan_preview_badge');
      if (badge) {
        badge.textContent = safe.badge || '\u5f85\u8bc6\u522b';
        badge.className = `badge ${safe.badgeClass || 'IDLE'}`;
      }
      updateRecognitionStateCard(safe);
    }

    function buildBatchScanPreview(mode = 'load') {
      let scan = null;
      try { scan = currentScannedKey({ requireFresh: false, requireCode: false }); } catch (_) { scan = { medicine_name: '', product_code: '', trace_id: '' }; }
      const codeText = [scan.product_code, scan.trace_id].filter(Boolean).join(' / ') || scan.medicine_name || '-';
      const hasRecognition = Boolean(scan.product_code || scan.trace_id || scan.medicine_name);
      if (!latestDeliveryBatch || !latestDeliveryBatch.batch_id) return { tone: 'warn', badge: '\u65e0\u6279\u6b21', badgeClass: 'WAITING_LOAD_CONFIRMATION', code: codeText, action: '\u8bf7\u5148\u5bfc\u5165\u6216\u65b0\u5efa\u914d\u9001\u6279\u6b21\u3002' };
      if (!hasRecognition) return { tone: '', badge: '\u5f85\u8bc6\u522b', badgeClass: 'IDLE', code: '-', action: '\u8bf7\u5148\u626b\u63cf\u6761\u5f62\u7801/\u8ffd\u6eaf\u7801\uff0cOCR \u836f\u540d\u53ea\u505a\u8f85\u52a9\u53c2\u8003\u3002' };
      if (!(scan.product_code || scan.trace_id)) return { tone: 'warn', badge: '\u9700\u626b\u7801', badgeClass: 'WAITING_LOAD_CONFIRMATION', code: codeText, medication: scan.medicine_name || '-', action: '\u5df2\u6709 OCR \u836f\u540d\uff0c\u4f46\u88c5\u836f/\u4ea4\u4ed8\u5199\u5165\u9700\u8981\u4ea7\u54c1\u7801\u6216\u8ffd\u6eaf\u7801\u3002' };
      const matches = findBatchMedicationByScan(scan, mode);
      if (!matches.length) return { tone: 'mismatch', badge: '\u672a\u5339\u914d', badgeClass: 'CANCELED', code: codeText, medication: scan.medicine_name || '-', action: mode === 'dispense' ? '\u672a\u5339\u914d\u5f53\u524d\u75c5\u623f\u836f\u54c1\uff0c\u8bf7\u590d\u6838\u75c5\u623f/\u6761\u7801\u3002' : '\u672a\u5339\u914d\u5f53\u524d\u6279\u6b21\u5f85\u88c5\u836f\u54c1\uff0c\u8bf7\u590d\u6838\u6761\u7801\u6216\u6279\u6b21\u6e05\u5355\u3002' };
      const first = matches[0];
      const patientText = `${first.stop.display_name || first.patient.ward_name || first.stop.target_station || '-'} / ${first.patient.bed_no || '-'} / ${first.patient.patient_name || '-'}`;
      const medText = `${first.medication.medicine_name || '-'}${first.medication.product_model ? ' / ' + first.medication.product_model : ''}`;
      return { tone: matches.length > 1 ? 'warn' : 'match', badge: matches.length > 1 ? '\u591a\u4e2a\u5019\u9009' : '\u5339\u914d\u5230\u836f\u54c1', badgeClass: matches.length > 1 ? 'WAITING_LOAD_CONFIRMATION' : 'COMPLETED', code: codeText, medication: medText, patient: patientText, action: matches.length > 1 ? `\u627e\u5230 ${matches.length} \u4e2a\u5019\u9009\uff0c\u8bf7\u6838\u5bf9\u540e\u518d\u786e\u8ba4\u3002` : (mode === 'dispense' ? '\u70b9\u51fb\u5e8a\u65c1\u4ea4\u4ed8\u6838\u9a8c\u540e\u5199\u5165\u4ea4\u4ed8\u8bb0\u5f55\u3002' : '\u70b9\u51fb\u836f\u5e08\u88c5\u836f\u6838\u9a8c\u540e\u5199\u5165\u88c5\u836f\u8bb0\u5f55\u3002'), match: first, matchCount: matches.length };
    }

    function updateBatchScanPreview(mode = '') {
      const effectiveMode = mode || getBatchRouteMode();
      setBatchScanPreview(buildBatchScanPreview(effectiveMode));
    }

    function modelFromBackendScanPreview(data, mode = 'load') {
      const safe = data || {};
      const codeText = [safe.product_code, safe.trace_id].filter(Boolean).join(' / ') || safe.medicine_name || '-';
      const first = Array.isArray(safe.candidates) && safe.candidates.length ? safe.candidates[0] : null;
      if (safe.status === 'NO_BATCH') {
        return { tone: 'warn', badge: '\u65e0\u6279\u6b21', badgeClass: 'WAITING_LOAD_CONFIRMATION', code: codeText, confidence: confidenceTitleFromBackend(safe), action: safe.recommended_action || safe.message || '\u5f53\u524d\u6ca1\u6709\u914d\u9001\u6279\u6b21\u3002', backend: safe };
      }
      if (safe.status === 'NO_CODE') {
        return { tone: 'warn', badge: '\u9700\u626b\u7801', badgeClass: 'WAITING_LOAD_CONFIRMATION', code: codeText, medication: safe.medicine_name || '-', confidence: confidenceTitleFromBackend(safe), action: safe.recommended_action || '\u9700\u8981\u4ea7\u54c1\u7801\u6216\u8ffd\u6eaf\u7801\u624d\u80fd\u5199\u5165\u88c5\u836f/\u4ea4\u4ed8\u8bb0\u5f55\u3002', backend: safe };
      }
      if (safe.status === 'NO_CODE_OR_NAME') {
        return { tone: 'warn', badge: '\u5f85 OCR', badgeClass: 'WAITING_LOAD_CONFIRMATION', code: codeText, medication: '-', confidence: confidenceTitleFromBackend(safe), action: safe.recommended_action || safe.message || '\u8bf7\u5148 OCR \u8bc6\u522b\u836f\u540d\u6216\u6253\u5f00\u6761\u5f62\u7801\u8bc6\u522b\u3002', backend: safe };
      }
      if (!first) {
        return { tone: 'mismatch', badge: '\u672a\u5339\u914d', badgeClass: 'CANCELED', code: codeText, medication: safe.medicine_name || '-', confidence: confidenceTitleFromBackend(safe), action: safe.recommended_action || safe.message || (mode === 'dispense' ? '\u672a\u5339\u914d\u5f53\u524d\u75c5\u623f\u836f\u54c1\u3002' : '\u672a\u5339\u914d\u5f53\u524d\u6279\u6b21\u836f\u54c1\u3002'), backend: safe };
      }
      const medText = `${first.medicine_name || '-'}${first.product_model ? ' / ' + first.product_model : ''}`;
      const patientText = `${first.ward_name || first.target_station || '-'} / ${first.bed_no || '-'} / ${first.patient_name || '-'}`;
      const multi = Array.isArray(safe.candidates) && safe.candidates.length > 1;
      const nameMatched = String(safe.medicine_match_source || '') === 'ocr_name';
      const scoreText = Number(safe.medicine_match_score || first.match_score || 0);
      const matchReason = safe.match_reason || first.match_reason || '';
      const baseAction = safe.recommended_action || safe.safety_note || safe.message || (multi ? `\u540e\u7aef\u8fd4\u56de ${safe.candidates.length} \u4e2a\u5019\u9009\uff0c\u8bf7\u6838\u5bf9\u540e\u786e\u8ba4\u3002` : (nameMatched ? `OCR \u836f\u540d\u8f85\u52a9\u5339\u914d\uff0c\u76f8\u4f3c\u5ea6 ${scoreText ? scoreText.toFixed(2) : '-'}\uff0c\u5199\u5165\u524d\u5efa\u8bae\u518d\u626b\u6761\u7801/\u4eba\u5de5\u786e\u8ba4\u3002` : (mode === 'dispense' ? '\u540e\u7aef\u786e\u8ba4\u53ef\u5199\u5165\u4ea4\u4ed8\u8bb0\u5f55\u3002' : '\u540e\u7aef\u786e\u8ba4\u53ef\u5199\u5165\u88c5\u836f\u8bb0\u5f55\u3002')));
      const actionText = matchReason ? `${baseAction} \u5339\u914d\u4f9d\u636e\uFF1A${matchReason}\u3002` : baseAction;
      return {
        tone: multi ? 'warn' : (nameMatched ? 'warn' : 'match'),
        badge: multi ? '\u591a\u4e2a\u5019\u9009' : (nameMatched ? 'OCR \u836f\u540d\u5339\u914d' : '\u540e\u7aef\u5df2\u5339\u914d'),
        badgeClass: multi || nameMatched ? 'WAITING_LOAD_CONFIRMATION' : 'COMPLETED',
        code: codeText,
        medication: medText,
        patient: patientText,
        confidence: confidenceTitleFromBackend(safe),
        action: actionText,
        backend: safe,
      };
    }

    function renderSafetySelfTestResult(data, targetId = 'batch_action_result') {
      const result = document.getElementById(targetId);
      if (!result) return;
      const payload = data?.result || data || {};
      const available = data?.available !== false && Boolean(payload && (payload.total || payload.scenarios));
      if (!available) {
        result.hidden = targetId === 'safety_self_test_latest';
        return;
      }
      result.hidden = false;
      const scenarios = Array.isArray(payload?.scenarios) ? payload.scenarios : [];
      const rows = scenarios.map(item => `<li>${escapeHtml(item.name || '-')} \u00b7 ${item.ok ? '\u901a\u8fc7' : '\u5931\u8d25'}${item.blockers && item.blockers.length ? ` / ${escapeHtml(item.blockers.join(' \u00b7 '))}` : ''}</li>`).join('');
      const testedAt = payload.tested_at ? ` / ${escapeHtml(payload.tested_at)}` : '';
      result.className = `safety-self-test-result ${payload?.ok ? 'ok' : 'fail'}`;
      result.innerHTML = `<strong>${escapeHtml(payload?.message || '\u5b89\u5168\u95e8\u81ea\u6d4b\u5b8c\u6210')}</strong><span>\u6279\u6b21 \u00b7 ${escapeHtml(payload?.batch_id || '-')} / ${Number(payload?.passed || 0)}/${Number(payload?.total || 0)}${testedAt}</span>${rows && targetId !== 'safety_self_test_latest' ? `<ol>${rows}</ol>` : ''}`;
    }

    async function refreshSafetySelfTestLatest() {
      try {
        const data = await api('/api/delivery_batch/safety_self_test/latest');
        renderSafetySelfTestResult(data, 'safety_self_test_latest');
      } catch (error) {
        const target = document.getElementById('safety_self_test_latest');
        if (target) target.hidden = true;
      }
    }

    async function runSafetySelfTest() {
      const data = await api('/api/delivery_batch/safety_self_test', { method: 'POST', body: '{}' });
      renderSafetySelfTestResult(data);
      renderSafetySelfTestResult(data, 'safety_self_test_latest');
      showDashboardToast(data.ok ? '\u5b89\u5168\u95e8\u81ea\u6d4b\u901a\u8fc7' : '\u5b89\u5168\u95e8\u81ea\u6d4b\u672a\u5168\u901a\u8fc7', data.message || '', data.ok ? 'ok' : 'warn');
      return data;
    }

    function getBatchRouteMode() {
      const status = String(latestDeliveryBatch?.route_status || '');
      return status === 'WARD_HANDOVER' ? 'dispense' : 'load';
    }

    function setBatchActionResultText(text, tone = 'muted') {
      const resultElement = document.getElementById('batch_action_result');
      if (!resultElement) return;
      resultElement.textContent = text || '-';
      const colorMap = { ok: 'var(--ok)', warn: 'var(--warning)', danger: 'var(--danger)', muted: 'var(--muted)' };
      resultElement.style.color = colorMap[tone] || colorMap.muted;
    }

    async function withBusyButton(button, busyText, fn) {
      if (!button) return fn();
      const oldText = button.textContent;
      button.disabled = true;
      button.textContent = busyText || oldText;
      try {
        return await fn();
      } finally {
        button.disabled = false;
        button.textContent = oldText;
      }
    }

    function setBatchActionResult(text, tone = 'muted') {
      setBatchActionResultText(text, tone);
    }

    function updateAutoLoadUi(message = '') {
      const button = document.getElementById('batch-auto-load-toggle');
      const status = document.getElementById('batch_auto_load_status');
      if (button) {
        button.textContent = autoLoadEnabled ? '\u5173\u95ed\u81ea\u52a8\u8bc6\u522b\u88c5\u836f' : '\u5f00\u542f\u81ea\u52a8\u8bc6\u522b\u88c5\u836f';
        button.classList.toggle('active', autoLoadEnabled);
      }
      if (status) {
        const defaultText = autoLoadEnabled
          ? `\u81ea\u52a8\u8bc6\u522b\u836f\u54c1\u5df2\u5f00\u542f\uff1aOCR \u548c\u6761\u7801/\u8ffd\u6eaf\u7801\u540c\u65f6\u8bc6\u522b\u3002OCR \u7531 8085 \u5b89\u5168\u540e\u53f0\u5904\u7406\uff0c\u4e0d\u4f1a\u4e2d\u65ad\u6444\u50cf\u5934\u753b\u9762\uff1b\u6761\u7801\u8fde\u7eed ${AUTO_LOAD_STABLE_REQUIRED} \u6b21\u7a33\u5b9a\u540e\u81ea\u52a8\u5f55\u5165\u3002`
          : '\u81ea\u52a8\u8bc6\u522b\u836f\u54c1\u672a\u5f00\u542f\u3002\u5f00\u542f\u540e\uff0cOCR \u548c\u6761\u7801/\u8ffd\u6eaf\u7801\u540c\u65f6\u542f\u52a8\uff1b\u5173\u95ed\u540e\u4e24\u8005\u90fd\u505c\u6b62\u3002';
        status.textContent = message || defaultText;
      }
    }

    function autoLoadSignatureFromBackend(backend = {}) {
      const first = Array.isArray(backend.candidates) && backend.candidates.length ? backend.candidates[0] : {};
      return [backend.mode || 'load', first.medication_id || '', backend.product_code || '', backend.trace_id || '', first.product_code || '', first.trace_id || ''].join('|');
    }

    function updateAutoLoadCandidate(signature) {
      const now = Date.now();
      const clean = String(signature || '').trim();
      if (!clean) {
        autoLoadCandidate = { signature: '', count: 0, lastSeenAt: now };
        return 0;
      }
      if (autoLoadCandidate.signature === clean && now - autoLoadCandidate.lastSeenAt < 10000) {
        autoLoadCandidate.count += 1;
      } else {
        autoLoadCandidate = { signature: clean, count: 1, lastSeenAt: now };
      }
      autoLoadCandidate.lastSeenAt = now;
      return autoLoadCandidate.count;
    }

    function shouldAutoCommitLoad(model) {
      if (!autoLoadEnabled || autoLoadBusy) return { ok: false, reason: '\u81ea\u52a8\u8bc6\u522b\u88c5\u836f\u672a\u5c31\u7eea' };
      if (getBatchRouteMode() !== 'load') return { ok: false, reason: '\u5f53\u524d\u4e0d\u5728\u836f\u623f\u88c5\u836f\u9636\u6bb5' };
      const gate = buildBatchBlockers(latestDeliveryBatch || {}, 'load');
      if (gate.blockers.length) return { ok: false, reason: gate.blockers.join(' ') };
      const backend = model?.backend || {};
      const source = String(backend.medicine_match_source || '').trim();
      if (source !== 'code') {
        updateAutoLoadCandidate('');
        return { ok: false, reason: '\u672a\u547d\u4e2d\u6761\u7801/\u8ffd\u6eaf\u7801\u786e\u8ba4\u7684\u6279\u6b21\u836f\u54c1' };
      }
      if (backend.can_commit !== true || backend.write_allowed !== true) return { ok: false, reason: backend.recommended_action || '\u8bc6\u522b\u7ed3\u679c\u4e0d\u80fd\u81ea\u52a8\u5199\u5165' };
      const signature = autoLoadSignatureFromBackend(backend);
      const count = updateAutoLoadCandidate(signature);
      if (autoLoadLastCommit.signature === signature && Date.now() - autoLoadLastCommit.at < AUTO_LOAD_COOLDOWN_MS) {
        return { ok: false, reason: '\u5f53\u524d\u836f\u54c1\u5df2\u5f55\u5165\uff0c\u8bf7\u79fb\u5f00\u540e\u653e\u5165\u4e0b\u4e00\u4ef6\u65b0\u836f', signature, count };
      }
      if (count < AUTO_LOAD_STABLE_REQUIRED) {
        return { ok: false, reason: `\u7b49\u5f85\u7a33\u5b9a ${count}/${AUTO_LOAD_STABLE_REQUIRED}`, signature, count };
      }
      return { ok: true, signature, count };
    }

    async function autoCommitLoadFromRecognition(model) {
      const decision = shouldAutoCommitLoad(model);
      if (!autoLoadEnabled) return;
      if (!decision.ok) {
        if (decision.reason) updateAutoLoadUi(`\u81ea\u52a8\u8bc6\u522b\u88c5\u836f\uff1a${decision.reason}`);
        return;
      }
      autoLoadBusy = true;
      updateAutoLoadUi('\u81ea\u52a8\u8bc6\u522b\u88c5\u836f\uff1a\u7a33\u5b9a\u547d\u4e2d\uff0c\u6b63\u5728\u5199\u5165\u88c5\u836f\u8bb0\u5f55...');
      try {
        const backend = model?.backend || {};
        const firstCandidate = Array.isArray(backend.candidates) && backend.candidates.length ? backend.candidates[0] : {};
        const scanPayload = {
          product_code: backend.product_code || '',
          trace_id: backend.trace_id || '',
          medicine_name: firstCandidate.matched_ocr_name || firstCandidate.medicine_name || backend.medicine_name || '',
        };
        await postBatchAction('/api/delivery_batch/load_scan', '\u81ea\u52a8\u8bc6\u522b\u88c5\u836f', { scanPayload });
        autoLoadLastCommit = { signature: decision.signature, at: Date.now() };
        autoLoadCandidate = { signature: '', count: 0, lastSeenAt: Date.now() };
        updateAutoLoadUi('\u81ea\u52a8\u8bc6\u522b\u88c5\u836f\uff1a\u5df2\u81ea\u52a8\u5f55\u5165\uff0c\u79fb\u5f00\u5f53\u524d\u836f\u54c1\u540e\u53ef\u7ee7\u7eed\u8bc6\u522b\u4e0b\u4e00\u4ef6\u3002');
        showDashboardToast('\u81ea\u52a8\u8bc6\u522b\u88c5\u836f\u5b8c\u6210', '\u8bc6\u522b\u7ed3\u679c\u5df2\u901a\u8fc7\u540e\u7aef\u5199\u5165\u89c4\u5219\uff0c\u5df2\u5199\u5165\u88c5\u836f\u8bb0\u5f55\u3002', 'ok');
      } catch (error) {
        updateAutoLoadUi(`\u81ea\u52a8\u8bc6\u522b\u88c5\u836f\u5931\u8d25\uff1a${error.message}`);
        setBatchActionResultText(`\u81ea\u52a8\u8bc6\u522b\u88c5\u836f\u5931\u8d25\uff1a${error.message}`, 'danger');
        showDashboardToast('\u81ea\u52a8\u8bc6\u522b\u88c5\u836f\u5931\u8d25', error.message, 'danger');
      } finally {
        autoLoadBusy = false;
      }
    }

    async function runAutoLoadRecognitionCycle() {
      if (!autoLoadEnabled || autoLoadBusy || autoLoadChecking) return;
      const now = Date.now();
      if (now - autoLoadLastCheckAt < 900) return;
      autoLoadLastCheckAt = now;
      if (getBatchRouteMode() !== 'load') {
        updateAutoLoadUi('\u81ea\u52a8\u8bc6\u522b\u88c5\u836f\uff1a\u5f53\u524d\u4e0d\u5728\u836f\u623f\u88c5\u836f\u9636\u6bb5\u3002');
        return;
      }
      autoLoadChecking = true;
      try {
        const model = await refreshBackendBatchScanPreview('load');
        await autoCommitLoadFromRecognition(model);
      } catch (error) {
        updateAutoLoadUi(`\u81ea\u52a8\u8bc6\u522b\u88c5\u836f\uff1a${error.message}`);
      } finally {
        autoLoadChecking = false;
      }
    }

    async function setAutoLoadEnabled(enabled) {
      autoLoadEnabled = Boolean(enabled);
      localStorage.setItem('medicine_auto_load_enabled', autoLoadEnabled ? '1' : '0');
      autoLoadCandidate = { signature: '', count: 0, lastSeenAt: 0 };
      updateAutoLoadUi();
      if (autoLoadEnabled && !visionQrEnabled) {
        try {
          await api('/api/vision/qr', { method: 'POST', body: JSON.stringify({ enabled: true }) });
          visionQrEnabled = true;
          const qrToggle = document.getElementById('vision-qr-toggle');
          if (qrToggle) {
            qrToggle.textContent = '\u5173\u95ed\u6761\u5f62\u7801\u8bc6\u522b';
            qrToggle.classList.add('active');
          }
          const qrState = document.getElementById('qr_runtime_state');
          if (qrState) qrState.textContent = '\u5df2\u5f00\u542f';
        } catch (error) {
          updateAutoLoadUi(`\u81ea\u52a8\u8bc6\u522b\u88c5\u836f\u5df2\u5f00\u542f\uff0c\u4f46\u6761\u5f62\u7801\u8bc6\u522b\u5f00\u542f\u5931\u8d25\uff1a${error.message}`);
        }
      }
      if (autoLoadEnabled) {
        try {
          await api('/api/vision/ocr', { method: 'POST', body: JSON.stringify({ mode: 'continuous' }) });
          ocrRoiVisibleUntil = Date.now() + 10 * 60 * 1000;
          updateVisionRoiOverlays();
          const ocrState = document.getElementById('ocr_runtime_state');
          if (ocrState) ocrState.textContent = '\u8fde\u7eed OCR \u8bc6\u522b\u4e2d\uff08\u5b89\u5168\u540e\u53f0\uff09';
        } catch (error) {
          updateAutoLoadUi(`\u81ea\u52a8\u8bc6\u522b\u88c5\u836f\u5df2\u5f00\u542f\uff0c\u4f46 OCR \u6301\u7eed\u8bc6\u522b\u5f00\u542f\u5931\u8d25\uff1a${error.message}`);
        }
        runAutoLoadRecognitionCycle();
      } else {
        try {
          await api('/api/vision/ocr', { method: 'POST', body: JSON.stringify({ mode: 'stop' }) });
          ocrRoiVisibleUntil = 0;
        } catch (_) {}
        try {
          await api('/api/vision/qr', { method: 'POST', body: JSON.stringify({ enabled: false }) });
          visionQrEnabled = false;
          const qrToggle = document.getElementById('vision-qr-toggle');
          if (qrToggle) {
            qrToggle.textContent = '\u6253\u5f00\u6761\u5f62\u7801\u8bc6\u522b';
            qrToggle.classList.remove('active');
          }
          const qrState = document.getElementById('qr_runtime_state');
          if (qrState) qrState.textContent = '\u672a\u5f00\u542f';
        } catch (_) {}
        updateVisionRoiOverlays();
        const ocrState = document.getElementById('ocr_runtime_state');
        if (ocrState) ocrState.textContent = '\u672a\u5f00\u542f\uff08\u6253\u5f00\u81ea\u52a8\u8bc6\u522b\u836f\u54c1\u540e\u542f\u52a8\uff09';
      }
    }

    async function refreshBackendBatchScanPreview(mode = '') {
      const status = String(latestDeliveryBatch?.route_status || '');
      const effectiveMode = mode || (status === 'WARD_HANDOVER' ? 'dispense' : 'load');
      let scan = null;
      try {
        scan = currentScannedKey({ requireFresh: false, requireCode: false });
      } catch (_) {
        scan = { medicine_name: '', product_code: '', trace_id: '' };
      }
      if (!(scan.product_code || scan.trace_id || scan.medicine_name)) {
        updateBatchScanPreview(effectiveMode);
        return buildBatchScanPreview(effectiveMode);
      }
      try {
        const data = await api('/api/delivery_batch/scan_preview', {
          method: 'POST',
          body: JSON.stringify({
            mode: effectiveMode,
            product_code: scan.product_code || '',
            trace_id: scan.trace_id || '',
            medicine_name: scan.medicine_name || '',
          }),
        });
        const model = modelFromBackendScanPreview(data, effectiveMode);
        setBatchScanPreview(model);
        return model;
      } catch (error) {
        const fallback = buildBatchScanPreview(effectiveMode);
        fallback.hint = `\u540e\u7aef\u9884\u5339\u914d\u6682\u4e0d\u53ef\u7528\uff0c\u5df2\u663e\u793a\u672c\u5730\u9884\u89c8\uff1a${error.message}`;
        setBatchScanPreview(fallback);
        return fallback;
      }
    }

    function buildBatchScanConfirmText(mode = 'load') {
      const preview = latestBatchScanPreviewModel || buildBatchScanPreview(mode);
      const backend = preview.backend || {};
      const safetyNote = backend.safety_note || preview.action || '-';
      const writeAllowed = backend.write_allowed === true;
      return [
        mode === 'dispense' ? '\u5373\u5c06\u6267\u884c\u5e8a\u65c1\u4ea4\u4ed8\u6838\u9a8c\u3002' : '\u5373\u5c06\u6267\u884c\u836f\u5e08\u88c5\u836f\u6838\u9a8c\u3002',
        `\u8bc6\u522b\u7ed3\u679c\uff1a${preview.code || '-'}`,
        `\u5339\u914d\u836f\u54c1\uff1a${preview.medication || '-'}`,
        `\u5bf9\u5e94\u75c5\u4eba\uff1a${preview.patient || '-'}`,
        `\u5199\u5165\u8bb0\u5f55\uff1a${writeAllowed ? '\u5141\u8bb8' : '\u6682\u4e0d\u5141\u8bb8/\u9700\u590d\u6838'}`,
        `\u5b89\u5168\u8bf4\u660e\uff1a${safetyNote}`,
        '',
        '\u6761\u7801/\u8ffd\u6eaf\u7801\u552f\u4e00\u547d\u4e2d\uff0c\u6216 OCR \u836f\u540d\u552f\u4e00\u547d\u4e2d\u4e14\u226550%\u65f6\uff0c\u540e\u7aef\u4f1a\u76f4\u63a5\u5199\u5165\u88c5\u836f\u8bb0\u5f55\uff0c\u4e0d\u518d\u4eba\u5de5\u6838\u5b9e\u3002',
      ].join('\n');
    }

    function renderPatientOrder(matchId = '') {
      const order = selectedPatientOrder;
      const container = document.getElementById('patient_medications');
      if (!order) {
        container.innerHTML = '<div class="medication-item">暂无患者用药清单</div>';
        return;
      }
      document.getElementById('patient_name_view').textContent = `${order.patient_name || '-'} (${order.patient_id || '-'})`;
      document.getElementById('patient_bed_view').textContent = order.bed_no || '-';
      document.getElementById('patient_ward_view').textContent = order.ward_name || order.ward_id || '-';
      document.getElementById('patient_target_view').textContent = order.target_station || '-';
      document.getElementById('patient_id').value = order.patient_id || '';
      if (order.target_station && document.getElementById('target_station').querySelector(`option[value="${order.target_station}"]`)) {
        document.getElementById('target_station').value = order.target_station;
      }
      if (!matchId) {
        latestPatientMedicationMatch = null;
      }
      const medications = order.medications || [];
      container.innerHTML = medications.map(item => {
        const matched = item.id && item.id === matchId;
        const className = matched ? 'medication-item matched' : 'medication-item';
        return `<div class="${className}">
          <div class="medication-title">
            <span>${escapeHtml(item.medicine_name || '-')}</span>
            <span>${matched ? '当前扫码匹配' : '待扫码'}</span>
          </div>
          <div class="audit-detail">产品编码：${escapeHtml(item.product_code || '-')}；追溯编号：${escapeHtml(item.trace_id || '-')}</div>
          <div class="audit-detail">规格：${escapeHtml(item.product_model || '-')}；数量：${escapeHtml(item.quantity || '-')}；医嘱：${escapeHtml(item.dose || '-')}/${escapeHtml(item.usage || '-')}</div>
        </div>`;
      }).join('');
    }

    async function loadPatientOrders() {
      const data = await api('/api/patient_orders');
      patientOrders = data.orders || [];
      const select = document.getElementById('patient_order');
      select.innerHTML = '';
      for (const order of patientOrders) {
        const option = document.createElement('option');
        option.value = order.patient_id;
        option.textContent = `${order.patient_name} / ${order.bed_no} / ${order.ward_name}`;
        select.appendChild(option);
      }
      selectedPatientOrder = getSelectedPatientOrder();
      renderPatientOrder();
    }

    async function scanPatientMedication() {
      await refreshDrugInfo();
      selectedPatientOrder = getSelectedPatientOrder();
      const scan = currentScannedKey({ requireFresh: true });
      if (!selectedPatientOrder) {
        document.getElementById('patient_match_result').textContent = '暂无患者用药清单。';
        return null;
      }
      const match = (selectedPatientOrder.medications || []).find(item => medicationMatchesScan(item, scan));
      if (!match) {
        latestPatientMedicationMatch = null;
        renderPatientOrder();
        const scanLabel = scan.medicine_name || scan.product_code || scan.trace_id || '-';
        document.getElementById('patient_match_result').textContent = `当前识别 ${scanLabel} 不属于 ${selectedPatientOrder.patient_name} 的用药清单。`;
        document.getElementById('patient_match_result').style.color = 'var(--danger)';
        updateRecognitionClosedLoopStatus();
        log('患者用药核对失败：当前识别结果不属于该患者');
        return null;
      }
      latestPatientMedicationMatch = match;
      renderPatientOrder(match.id || '');
      const matchMethod = scan.product_code || scan.trace_id ? '编码/追溯码' : 'OCR 药名';
      document.getElementById('patient_match_result').textContent = `核对通过：${match.medicine_name} 属于 ${selectedPatientOrder.patient_name} 的用药清单（${matchMethod}）。`;
      document.getElementById('patient_match_result').style.color = 'var(--ok)';
      updateRecognitionClosedLoopStatus();
      log(`患者用药核对通过：${match.medicine_name}`);
      return match;
    }

    function buildPatientTaskPayload() {
      const order = selectedPatientOrder || getSelectedPatientOrder();
      const medications = (order?.medications || []).map(normalizeMedicationForTask);
      const matchedPrimary = latestPatientMedicationMatch && medications.find(item => item.id === latestPatientMedicationMatch.id);
      const primary = matchedPrimary || medications[0] || {};
      return {
        target_station: order?.target_station || document.getElementById('target_station').value,
        source_station: document.getElementById('source_station').value,
        medicine_name: medications.map(item => item.medicine_name).filter(Boolean).join('、') || getTaskMedicineName(),
        patient_id: order?.patient_id || document.getElementById('patient_id').value,
        patient_name: order?.patient_name || '',
        ward_id: order?.ward_id || '',
        bed_no: order?.bed_no || '',
        product_code: primary.product_code || '',
        product_model: primary.product_model || '',
        quantity: primary.quantity || '',
        trace_id: primary.trace_id || '',
        order_no: primary.order_no || '',
        medications_json: JSON.stringify(medications),
      };
    }

    function updateRecognitionClosedLoopStatus() {
      const data = latestDrugInfo || {};
      const recognizedName = getRecognizedMedicineName(data);
      const traceId = data.trace_code || data.label_trace_id || '';
      const hasRecognized = Boolean(recognizedName || data.label_product_code || traceId);
      const hasMatch = Boolean(latestPatientMedicationMatch);
      const hasTask = Boolean(latestTaskId);
      const hasReport = Boolean(latestReportRows.length || latestDeliveryBatch?.audit_records?.length);
      const steps = [
        ['loop_step_recognize', hasRecognized, false],
        ['loop_step_match', hasMatch, hasRecognized && !hasMatch],
        ['loop_step_task', hasTask, hasMatch && !hasTask],
        ['loop_step_report', hasReport, hasTask && !hasReport],
      ];
      for (const [id, done, warn] of steps) {
        const element = document.getElementById(id);
        if (!element) continue;
        element.classList.toggle('done', Boolean(done));
        element.classList.toggle('warn', Boolean(warn));
      }
    }

    function updateTaskRecognitionPanel(data) {
      const fields = getTaskRecognitionFields();
      document.getElementById('task_product_code').textContent = fields.product_code || '-';
      document.getElementById('task_product_model').textContent = fields.product_model || '-';
      document.getElementById('task_quantity').textContent = fields.quantity || '-';
      document.getElementById('task_trace_id').textContent = fields.trace_id || '-';
      document.getElementById('task_order_no').textContent = fields.order_no || '-';
      document.getElementById('task_medicine_preview').textContent = getTaskMedicineName();
      updateRecognitionClosedLoopStatus();
    }

    function applyRecognizedToTask(force = false) {
      const data = latestDrugInfo || {};
      const candidate = getRecognizedMedicineName(data);
      if (!candidate) {
        document.getElementById('autofill_hint').textContent = '等待结构化识别结果。';
        updateTaskRecognitionPanel(data);
        return false;
      }
      const current = medicineNameInput.value.trim();
      const canReplace = force || !current || current === '降压药' || current === lastAutoFilledMedicineName;
      if (!canReplace) {
        document.getElementById('autofill_hint').textContent = '检测到识别结果，当前药品名称已手动编辑，可点击“使用识别结果”。';
        updateTaskRecognitionPanel(data);
        return false;
      }
      medicineNameInput.value = candidate;
      lastAutoFilledMedicineName = candidate;
      document.getElementById('autofill_hint').textContent = '已根据最新识别结果填充药品名称。';
      updateTaskRecognitionPanel(data);
      return true;
    }

    function updateDrugInfo(data) {
      latestDrugInfo = data || {};
      visionQrEnabled = Boolean(data.qr_enabled);
      const confidence = Math.round((data.confidence || 0) * 100);
      const loaded = Boolean(data.loaded);
      const loadedElement = document.getElementById('drug_loaded');
      const hasRecognition = Boolean(data.drug_name || data.ocr_drug_name || data.trace_code || data.label_product_code);
      const channel = String(data.recognition_channel || '').trim();
      const sourceText = String(data.recognition_source || data.source || '').trim();
      let channelLabel = '-';
      if (channel === 'barcode' || sourceText.includes('barcode') || sourceText.includes('qr') || sourceText.includes('datamatrix')) {
        channelLabel = '条形码识别';
      } else if (channel === 'ocr' || sourceText.includes('ocr')) {
        channelLabel = 'OCR 文字识别';
      } else if (hasRecognition) {
        channelLabel = '默认/手动结果';
      }
      document.getElementById('drug_id').textContent = data.drug_id || '-';
      document.getElementById('drug_name').textContent = data.drug_name || '-';
      document.getElementById('drug_type').textContent = data.drug_type || '-';
      document.getElementById('drug_confidence').textContent = data.drug_name ? `${confidence}%` : '-';
      loadedElement.textContent = data.drug_name ? (loaded ? '已装药' : '未装药') : '-';
      loadedElement.className = loaded ? 'drug-loaded' : 'drug-empty';
      document.getElementById('drug_source').textContent = data.source || '-';
      document.getElementById('recognition_channel').textContent = channelLabel;
      updateRecognitionReviewStateText(data);
      document.getElementById('code_text').textContent = data.raw_code_text || data.code_text || '-';
      document.getElementById('trace_code').textContent = data.trace_code || data.label_trace_id || '-';
      document.getElementById('trace_source').textContent = data.trace_source ? `条形码 / ${data.trace_source}` : '-';
      document.getElementById('code_type').textContent = data.code_type || '-';
      document.getElementById('code_method').textContent = data.code_method || '-';
      const qrToggle = document.getElementById('vision-qr-toggle');
      if (qrToggle) {
        qrToggle.textContent = visionQrEnabled ? '关闭条形码识别' : '打开条形码识别';
        qrToggle.classList.toggle('active', visionQrEnabled);
      }
      document.getElementById('qr_runtime_state').textContent = visionQrEnabled ? '已开启' : '未开启';
      document.getElementById('ocr_runtime_state').textContent = data.ocr_runtime_enabled
        ? '连续识别中'
        : (data.ocr_single_shot_pending ? '等待识别' : '点击按钮后识别一次');
      const ocrError = String(data.ocr_error || '').trim();
      const ocrText = String(data.ocr_text || '').trim();
      const ocrBusyMs = Number(data.ocr_worker_busy_ms || 0);
      const ocrRoi = Array.isArray(data.ocr_roi_rect) && data.ocr_roi_rect.length >= 4
        ? data.ocr_roi_rect.map(value => Math.round(Number(value) || 0)).join(', ')
        : '-';
      const ocrHeld = Boolean(data.ocr_held);
      const ocrLastGoodAge = Number(data.ocr_last_good_age_sec || -1);
      const ocrHoldSec = Number(data.ocr_hold_last_good_sec || 0);
      const ocrDrugNameText = String(data.ocr_drug_name || '').trim();
      const ocrHasUsefulText = /[\u4e00-\u9fff]/.test(ocrText) || /(?:C?\d{4,}|TRACE[-A-Z0-9]+)/i.test(ocrText);
      const ocrIsTinyNoise = Boolean(ocrText) && !ocrHasUsefulText && ocrText.replace(/[\s_\-|.,??:?;?]+/g, '').length <= 3;
      const ocrDisplayText = (ocrIsTinyNoise || !ocrText) && ocrDrugNameText
        ? '\u672A\u8BFB\u5230\u6709\u6548\u836F\u540D\u6587\u5B57\uFF0C\u5DF2\u901A\u8FC7\u6761\u7801/\u8FFD\u6EAF\u7801\u53CD\u67E5'
        : (ocrText
          ? (ocrHeld ? `${ocrText}\uFF08\u4FDD\u7559\u4E0A\u6B21\u6709\u6548\u8BC6\u522B\uFF09` : ocrText)
          : (ocrError.includes('no text') ? '\u672A\u68C0\u6D4B\u5230\u6587\u5B57\uFF0C\u8BF7\u628A\u836F\u76D2\u6587\u5B57\u653E\u5165\u7EFF\u8272\u8BC6\u522B\u6846' : '-'));
      const fallbackCodeText = String(data.label_product_code || data.product_code || data.trace_code || data.label_trace_id || data.raw_code_text || '').trim();
      const fallbackMatchText = ocrDrugNameText && fallbackCodeText ? `${fallbackCodeText} \u2192 ${ocrDrugNameText}` : '';
      const rawMatchText = String(data.ocr_match_text || '').trim();
      const rawMatchIsNoise = rawMatchText && ocrDrugNameText && !/[\u4e00-\u9fff]/.test(rawMatchText);
      document.getElementById('ocr_text').textContent = ocrDisplayText;
      document.getElementById('ocr_match_text').textContent = rawMatchIsNoise ? (fallbackMatchText || rawMatchText) : (rawMatchText || fallbackMatchText || '-');
      document.getElementById('ocr_drug_name').textContent = data.ocr_drug_name || '-';
      const ocrCandidateList = Array.isArray(data.ocr_drug_name_candidates)
        ? data.ocr_drug_name_candidates
            .map(item => String(item || '').trim())
            .filter(item => item && /[\u4e00-\u9fff]/.test(item))
            .filter(item => !/^(code|code128|barcode|trace|[A-Za-z0-9\s/|_-]{1,16})$/i.test(item))
            .slice(0, 5)
        : [];
      const ocrCandidateScore = Number(data.ocr_drug_name_score || 0);
      document.getElementById('ocr_drug_candidates').textContent = ocrCandidateList.length
        ? `${ocrCandidateList.join(' / ')}${ocrCandidateScore ? `\uFF08${ocrCandidateScore}\uFF09` : ''}`
        : '-';
      document.getElementById('ocr_spec').textContent = data.ocr_spec || '-';
      document.getElementById('ocr_manufacturer').textContent = data.ocr_manufacturer || '-';
      document.getElementById('ocr_approval_no').textContent = data.ocr_approval_no || '-';
      document.getElementById('ocr_confidence').textContent = ocrText ? `${Math.round((data.ocr_confidence || 0) * 100)}%` : '-';
      document.getElementById('ocr_backend').textContent = data.ocr_backend || (data.ocr_available ? 'available' : '-');
      document.getElementById('ocr_worker_busy_ms').textContent = Number.isFinite(ocrBusyMs) && ocrBusyMs > 0 ? `${ocrBusyMs.toFixed(1)} ms` : '-';
      document.getElementById('ocr_roi_rect').textContent = data.ocr_roi_enabled ? ocrRoi : '未启用';
      document.getElementById('ocr_status').textContent = data.ocr_enabled ? (ocrError || `已启用 ${data.ocr_language || ''}`) : '未启用';
      const holdText = ocrHoldSec > 0
        ? (ocrHeld
          ? `\u5DF2\u4FDD\u7559\u4E0A\u6B21\u6709\u6548\u7ED3\u679C\uFF0C\u8DDD\u4E0A\u6B21 ${ocrLastGoodAge >= 0 ? ocrLastGoodAge.toFixed(1) : '-'} \u79D2 / \u4FDD\u7559 ${ocrHoldSec.toFixed(0)} \u79D2`
          : `\u542F\u7528\uFF0C\u4FDD\u7559 ${ocrHoldSec.toFixed(0)} \u79D2`)
        : '\u672A\u542F\u7528';
      document.getElementById('ocr_hold_status').textContent = holdText;
      updateOcrRoiOverlay(data);
      document.getElementById('label_order_no').textContent = data.label_order_no || '-';
      document.getElementById('label_product_code').textContent = data.label_product_code || '-';
      document.getElementById('label_product_model').textContent = data.label_product_model || '-';
      document.getElementById('label_quantity').textContent = data.label_quantity || '-';
      document.getElementById('label_trace_id').textContent = data.label_trace_id || data.trace_code || '-';
      document.getElementById('drug_stamp').textContent = data.stamp ? new Date(data.stamp * 1000).toLocaleString() : '-';
      document.getElementById('vision_node_state').textContent = hasRecognition ? '识别节点有数据' : '等待识别数据';
      document.getElementById('vision_frame_time').textContent = data.recognition_received_at ? new Date(data.recognition_received_at * 1000).toLocaleString() : '-';
      document.getElementById('vision_fps').textContent = data.camera_fps ? `${Number(data.camera_fps).toFixed(0)} FPS` : '-';
      document.getElementById('vision_actual_fps').textContent = data.camera_actual_fps ? `${Number(data.camera_actual_fps).toFixed(1)} FPS` : '-';
      const expectedCode = String(document.getElementById('task_product_code')?.textContent || '').trim();
      const actualCode = String(data.label_product_code || '').trim();
      let matchText = '未识别';
      let matchClass = 'audit-detail';
      if (hasRecognition && confidence > 0 && confidence < 70) {
        matchText = '低置信度，请扫码确认';
        matchClass = 'audit-detail';
      } else if (hasRecognition && expectedCode && expectedCode !== '-' && actualCode && actualCode !== expectedCode) {
        matchText = '与当前任务药品不一致，请复核';
        matchClass = 'audit-fail';
      } else if (hasRecognition) {
        matchText = expectedCode && expectedCode !== '-' ? '与当前任务药品一致' : '已识别，等待任务匹配';
        matchClass = 'audit-pass';
      }
      const matchElement = document.getElementById('vision_match_status');
      matchElement.textContent = matchText;
      matchElement.className = matchClass;
      const visionBadge = document.getElementById('vision-status-badge');
      if (visionBadge) {
        visionBadge.textContent = hasRecognition ? '识别在线' : '待识别';
        visionBadge.className = hasRecognition ? 'badge COMPLETED' : 'badge WAITING_LOAD_CONFIRMATION';
      }
      document.getElementById('vision_hint').textContent = hasRecognition
        ? '已收到识别结果。低置信度或不匹配时，请使用扫码器或药师复核确认。'
        : '未收到结构化识别结果。请检查摄像头、识别节点和 MJPEG 地址，或使用扫码器/手动录入。';
      updateTaskRecognitionPanel(data);
      applyRecognizedToTask(false);
      if (autoLoadEnabled) {
        runAutoLoadRecognitionCycle();
      } else {
        updateBatchScanPreview();
      }
      updateRuntimeStatus();
    }

    function formatChassisNumber(value, digits = 2) {
      const number = Number(value);
      if (!Number.isFinite(number)) {
        return '0.00';
      }
      return number.toFixed(digits);
    }

    function setChassisField(id, text, className = '') {
      const element = document.getElementById(id);
      element.textContent = text;
      element.className = className;
    }

    function setChassisActionResult(text, tone = 'muted') {
      const element = document.getElementById('chassis_action_result');
      if (!element) return;
      element.textContent = text || '-';
      const colorMap = { ok: 'var(--ok)', warn: 'var(--warning)', danger: 'var(--danger)', muted: 'var(--muted)' };
      element.style.color = colorMap[tone] || colorMap.muted;
    }

    async function setChassisEmergencyStop(enabled, button) {
      if (!enabled) {
        const ok = window.confirm('解除急停会恢复底盘运动输出能力。请确认现场安全、机器人不会碰到人或物。是否继续？');
        if (!ok) return;
      }
      const busyText = enabled ? '开启急停中...' : '解除急停中...';
      await withBusyButton(button, busyText, async () => {
        const data = await api('/api/chassis/emergency_stop', {
          method: 'POST',
          body: JSON.stringify({ enabled }),
        });
        if (data.chassis_status) {
          updateChassisStatus(data.chassis_status);
        }
        setChassisActionResult(data.message || (enabled ? '急停已开启' : '急停已解除'), data.ok ? 'ok' : 'danger');
        await refreshChassisStatus();
      });
    }

    function updateChassisStatus(data) {
      latestChassisStatus = data || {};
      const badge = document.getElementById('chassis_status_badge');
      const hint = document.getElementById('chassis_status_hint');
      if (!data || !data.received) {
        badge.textContent = '未启用';
        badge.className = 'badge IDLE';
        setChassisField('chassis_bridge_state', data?.message || '未收到状态', 'audit-detail');
        setChassisField('chassis_serial_port', '-');
        setChassisField('chassis_mavlink_heartbeat', '-');
        setChassisField('chassis_mavlink_identity', '-');
        setChassisField('chassis_emergency_stop', '-');
        setChassisField('chassis_control_output', '-');
        setChassisField('chassis_velocity_target', '-');
        setChassisField('chassis_current_speed', '-');
        setChassisField('chassis_watchdog', '-');
        setChassisField('chassis_update_time', '-');
        hint.textContent = '未收到 /medicine/chassis_status。默认不启用底盘桥接时这是正常状态。';
        ['chassis-estop-on', 'chassis-estop-off'].forEach(id => { const button = document.getElementById(id); if (button) button.disabled = true; });
        updateRuntimeStatus();
        return;
      }
      const ardupilot = data.ardupilot || {};
      const readonly = Boolean(ardupilot.readonly);
      const controlEnabled = Boolean(ardupilot.control_enabled);
      const emergencyStop = Boolean(data.emergency_stop);
      const heartbeatOk = Boolean(ardupilot.heartbeat_ok);
      const safeReadOnly = readonly && !controlEnabled && emergencyStop;
      if (!readonly || controlEnabled) {
        badge.textContent = '危险配置';
        badge.className = 'badge CANCELED';
      } else if (safeReadOnly && heartbeatOk) {
        badge.textContent = '只读正常';
        badge.className = 'badge COMPLETED';
      } else if (safeReadOnly) {
        badge.textContent = '只读待心跳';
        badge.className = 'badge WAITING_LOAD_CONFIRMATION';
      } else {
        badge.textContent = '需确认';
        badge.className = 'badge WAITING_LOAD_CONFIRMATION';
      }
      setChassisField('chassis_bridge_state', `${data.mode || '-'} / ${data.publish_odom ? '发布里程计' : '不发布里程计'}`);
      setChassisField('chassis_serial_port', `${ardupilot.port || data.serial_port || '-'} @ ${ardupilot.baudrate || '-'}`);
      const heartbeatAge = ardupilot.heartbeat_age_sec == null ? '-' : `${formatChassisNumber(ardupilot.heartbeat_age_sec, 2)}s`;
      setChassisField(
        'chassis_mavlink_heartbeat',
        heartbeatOk ? `正常 count=${ardupilot.heartbeat_count || 0} age=${heartbeatAge}` : `未收到/超时 count=${ardupilot.heartbeat_count || 0}`,
        heartbeatOk ? 'audit-pass' : 'audit-detail',
      );
      setChassisField(
        'chassis_mavlink_identity',
        `sys=${ardupilot.system_id ?? '-'} comp=${ardupilot.component_id ?? '-'} type=${ardupilot.type ?? '-'} autopilot=${ardupilot.autopilot ?? '-'} status=${ardupilot.system_status ?? '-'}`,
      );
      setChassisField('chassis_emergency_stop', emergencyStop ? '已开启' : '已解除', emergencyStop ? 'audit-pass' : 'audit-fail');
      const estopOnButton = document.getElementById('chassis-estop-on');
      const estopOffButton = document.getElementById('chassis-estop-off');
      if (estopOnButton) estopOnButton.disabled = emergencyStop;
      if (estopOffButton) estopOffButton.disabled = !emergencyStop;
      setChassisField(
        'chassis_control_output',
        `readonly=${readonly} control_enabled=${controlEnabled}`,
        readonly && !controlEnabled ? 'audit-pass' : 'audit-fail',
      );
      setChassisField(
        'chassis_velocity_target',
        `linear=${formatChassisNumber(data.target_linear)} angular=${formatChassisNumber(data.target_angular)}`,
      );
      setChassisField(
        'chassis_current_speed',
        `linear=${formatChassisNumber(data.current_linear)} angular=${formatChassisNumber(data.current_angular)}`,
      );
      setChassisField(
        'chassis_watchdog',
        data.cmd_timed_out ? '已超时/归零' : '正常',
        data.cmd_timed_out ? 'audit-detail' : 'audit-pass',
      );
      const stamp = Number(data.stamp_sec || data.web_received_at || 0);
      setChassisField('chassis_update_time', stamp > 0 ? new Date(stamp * 1000).toLocaleString() : '-');
      hint.textContent = safeReadOnly
        ? '当前底盘桥接保持只读、禁控和急停。未接真实飞控时 heartbeat 未收到属于正常状态。'
        : '请确认底盘安全状态：接飞控前必须保持只读、禁控和急停。';
      updateRuntimeStatus();
    }

    async function refreshState() {
      try {
        updateState(await api('/api/state'));
      } catch (error) {
        log(`状态刷新失败：${error.message}`);
      }
    }

    async function refreshDrugInfo() {
      try {
        updateDrugInfo(await api('/api/drug_info'));
      } catch (error) {
        log(`药物识别信息刷新失败：${error.message}`);
      }
    }

    function setLoadMeter(name, percent, suffix = '') {
      const value = Math.max(0, Math.min(100, Number(percent) || 0));
      const textEl = document.getElementById(`load_${name}_text`);
      const barEl = document.getElementById(`load_${name}_bar`);
      if (textEl) textEl.textContent = `${value.toFixed(0)}%${suffix}`;
      if (barEl) barEl.style.width = `${value}%`;
    }

    function updateSystemLoad(data) {
      latestSystemLoad = data || {};
      setLoadMeter('cpu', data.cpu_percent);
      const gpuFreq = Number(data.gpu_freq_mhz || 0);
      const npuFreq = Number(data.npu_freq_mhz || 0);
      setLoadMeter('gpu', data.gpu_percent, gpuFreq > 0 ? ` @ ${gpuFreq.toFixed(0)} MHz` : '');
      setLoadMeter('npu', data.npu_percent, npuFreq > 0 ? ` @ ${npuFreq.toFixed(0)} MHz` : '');
    }

    async function refreshSystemLoad() {
      try {
        updateSystemLoad(await api('/api/system_load'));
      } catch (error) {
        log(`系统负载刷新失败：${error.message}`);
      }
    }

    async function refreshChassisStatus() {
      try {
        updateChassisStatus(await api('/api/chassis_status'));
      } catch (error) {
        updateChassisStatus({ received: false, message: `底盘状态刷新失败：${error.message}` });
      }
    }

    document.getElementById('chassis-estop-on')?.addEventListener('click', async (event) => {
      try {
        await setChassisEmergencyStop(true, event.currentTarget);
      } catch (error) {
        setChassisActionResult(`开启急停失败：${error.message}`, 'danger');
      }
    });
    document.getElementById('chassis-estop-off')?.addEventListener('click', async (event) => {
      try {
        await setChassisEmergencyStop(false, event.currentTarget);
      } catch (error) {
        setChassisActionResult(`解除急停失败：${error.message}`, 'danger');
      }
    });
    document.getElementById('chassis-refresh')?.addEventListener('click', async (event) => withBusyButton(event.currentTarget, '刷新中...', refreshChassisStatus));
    document.getElementById('task-form').addEventListener('submit', async event => {
      event.preventDefault();
      const payload = {
        target_station: document.getElementById('target_station').value,
        source_station: document.getElementById('source_station').value,
        medicine_name: getTaskMedicineName(),
        patient_id: document.getElementById('patient_id').value,
        patient_name: '',
        ward_id: '',
        bed_no: '',
        ...getTaskRecognitionFields(),
      };
      try {
        const data = await api('/api/tasks', { method: 'POST', body: JSON.stringify(payload) });
        latestTaskId = data.task_id || '';
        log(`${data.accepted ? '任务创建成功' : '任务未接受'}：${data.message} ${data.task_id || ''}`);
        await refreshState();
      } catch (error) {
        log(`任务创建失败：${error.message}`);
      }
    });

    document.querySelectorAll('.tab-button').forEach(button => {
      button.addEventListener('click', () => switchDashboardTab(button.dataset.tab));
    });
    syncCameraPreview();
    medicineNameInput.addEventListener('input', () => updateTaskRecognitionPanel(latestDrugInfo));
    document.getElementById('patient_order').addEventListener('change', () => {
      selectedPatientOrder = getSelectedPatientOrder();
      renderPatientOrder();
    });
    document.getElementById('scan-patient-medication').addEventListener('click', async () => {
      try {
        await scanPatientMedication();
      } catch (error) {
        log(`患者用药核对失败：${error.message}`);
      }
    });
    document.getElementById('create-patient-task').addEventListener('click', async () => {
      try {
        selectedPatientOrder = getSelectedPatientOrder();
        const payload = buildPatientTaskPayload();
        const data = await api('/api/tasks', { method: 'POST', body: JSON.stringify(payload) });
        latestTaskId = data.task_id || '';
        log(`${data.accepted ? '患者清单任务创建成功' : '患者清单任务未接受'}：${data.message} ${data.task_id || ''}`);
        await refreshState();
      } catch (error) {
        log(`患者清单任务创建失败：${error.message}`);
      }
    });
    document.getElementById('use-recognized').addEventListener('click', () => {
      if (applyRecognizedToTask(true)) {
        log('已使用识别结果填充任务表单');
      } else {
        log('暂无可用的结构化识别结果');
      }
    });
    document.getElementById('vision-qr-toggle').addEventListener('click', async () => {
      const button = document.getElementById('vision-qr-toggle');
      button.disabled = true;
      try {
        const enabled = !visionQrEnabled;
        const data = await api('/api/vision/qr', {
          method: 'POST',
          body: JSON.stringify({ enabled }),
        });
        visionQrEnabled = enabled;
        button.textContent = enabled ? '关闭条形码识别' : '打开条形码识别';
        button.classList.toggle('active', enabled);
        document.getElementById('qr_runtime_state').textContent = enabled ? '已开启' : '未开启';
        document.getElementById('vision_hint').textContent = enabled ? '条形码识别已开启，请将药品条形码放入画面。' : '条形码识别已关闭。';
        log(`条形码识别${enabled ? '已开启' : '已关闭'}，订阅数 ${data.subscribers ?? 0}`);
      } catch (error) {
        log(`条形码识别控制失败：${error.message}`);
      } finally {
        button.disabled = false;
      }
    });
    document.getElementById('vision-ocr-once').addEventListener('click', async () => {
      const button = document.getElementById('vision-ocr-once');
      button.disabled = true;
      button.textContent = 'OCR 识别中';
      try {
        ocrRoiVisibleUntil = Date.now() + 8000;
        updateVisionRoiOverlays();
        const data = await api('/api/vision/ocr', {
          method: 'POST',
          body: JSON.stringify({ mode: 'single' }),
        });
        document.getElementById('ocr_runtime_state').textContent = '等待识别';
        document.getElementById('vision_hint').textContent = 'OCR 已触发，请保持文字区域清晰稳定。';
        log(`OCR 单次识别已触发，订阅数 ${data.subscribers ?? 0}`);
        updateVisionRoiOverlays();
        setTimeout(refreshState, 1800);
      } catch (error) {
        log(`OCR 识别触发失败：${error.message}`);
      } finally {
        setTimeout(() => {
          button.disabled = false;
          button.textContent = 'OCR 识别文字';
        }, 1200);
      }
    });
    document.getElementById('reset-batch').addEventListener('click', async () => {
      try {
        if (!confirmCriticalAction('确认新建/重建配送批次？', '当前批次会被新的演示批次替换；如需归档，请先导出审计 JSON 或明细 CSV。')) return;
        const data = await api('/api/delivery_batch/reset', { method: 'POST', body: JSON.stringify({}) });
        updateDeliveryBatch(data);
        document.getElementById('batch_action_result').textContent = '已创建新的配送批次，请先完成药师装药核验。';
        document.getElementById('batch_action_result').style.color = 'var(--ok)';
        log('已创建新的配送批次');
      } catch (error) {
        log(`新建配送批次失败：${error.message}`);
      }
    });
    let voiceListenCountdownTimer = null;
    let voiceListenEndsAt = 0;

    function startVoiceListenCountdown(durationSec) {
      const button = document.getElementById('voice-listen-60');
      const result = document.getElementById('batch_action_result');
      const duration = Math.max(1, Number(durationSec) || 300);
      voiceListenEndsAt = Date.now() + duration * 1000;
      button.disabled = true;

      if (voiceListenCountdownTimer) {
        clearInterval(voiceListenCountdownTimer);
      }

      function renderCountdown() {
        const remaining = Math.max(0, Math.ceil((voiceListenEndsAt - Date.now()) / 1000));
        if (remaining <= 0) {
          clearInterval(voiceListenCountdownTimer);
          voiceListenCountdownTimer = null;
          button.disabled = false;
          button.textContent = '语音对话 5 分钟';
          result.textContent = '语音对话监听已结束。';
          result.style.color = 'var(--muted)';
          return;
        }
        const minutes = Math.floor(remaining / 60);
        const seconds = String(remaining % 60).padStart(2, '0');
        button.textContent = `监听中 ${minutes}:${seconds}`;
        result.textContent = `语音对话监听中，剩余 ${minutes}:${seconds}。`;
        result.style.color = 'var(--ok)';
      }

      renderCountdown();
      voiceListenCountdownTimer = setInterval(renderCountdown, 1000);
    }

    document.getElementById('voice-listen-60').addEventListener('click', async () => {
      try {
        const data = await api('/api/voice/listen', {
          method: 'POST',
          body: JSON.stringify({ duration_sec: 300 }),
        });
        const result = document.getElementById('batch_action_result');
        if (data.ok) {
          startVoiceListenCountdown(data.duration_sec || 300);
          log(`语音对话监听已开启 ${data.duration_sec || 300} 秒`);
        } else {
          result.textContent = '语音对话监听开启失败。';
          result.style.color = 'var(--danger)';
        }
      } catch (error) {
        const button = document.getElementById('voice-listen-60');
        button.disabled = false;
        button.textContent = '语音对话 5 分钟';
        log(`语音对话监听开启失败：${error.message}`);
      }
    });
    document.getElementById('demo-review-scenario').addEventListener('click', async () => {
      try {
        if (!confirmCriticalAction('\u5f00\u59cb\u4e00\u952e\u590d\u6838\u6f14\u793a\uff1f', '\u4f18\u5148\u4f7f\u7528\u5f53\u524d\u6279\u6b21\u4e2d\u7684\u672a\u4ea4\u4ed8\u75c5\u4eba\uff1b\u82e5\u5f53\u524d\u6279\u6b21\u65e0\u53ef\u6f14\u793a\u836f\u54c1\uff0c\u7cfb\u7edf\u4f1a\u81ea\u52a8\u65b0\u5efa\u6f14\u793a\u6279\u6b21\u3002')) return;
        const data = await api('/api/delivery_batch/demo_review', {
          method: 'POST',
          body: JSON.stringify({ auto_create_demo_batch: true }),
        });
        updateDeliveryBatch(data.batch || data);
        const result = document.getElementById('batch_action_result');
        result.textContent = data.message || '\u5df2\u751f\u6210\u7528\u836f\u590d\u6838\u6f14\u793a\u573a\u666f\u3002';
        result.style.color = data.ok === false ? 'var(--danger)' : 'var(--ok)';
        const auditFilter = document.getElementById('batch_audit_filter');
        updateDemoReviewGuide(latestDeliveryBatch);
        if (auditFilter) {
          auditFilter.value = 'medication_review';
          latestAuditFilter = 'medication_review';
          renderBatchAudit((latestDeliveryBatch && latestDeliveryBatch.audit_records) || []);
        }
        window.setTimeout(() => locateDemoReviewPatient({ afterGenerate: true }), 120);
        log(data.message || '\u5df2\u751f\u6210\u7528\u836f\u590d\u6838\u6f14\u793a\u573a\u666f');
      } catch (error) {
        const result = document.getElementById('batch_action_result');
        result.textContent = `\u751f\u6210\u590d\u6838\u6f14\u793a\u573a\u666f\u5931\u8d25\uff1a${error.message}`;
        result.style.color = 'var(--danger)';
        log(`\u751f\u6210\u590d\u6838\u6f14\u793a\u573a\u666f\u5931\u8d25\uff1a${error.message}`);
      }
    });
    document.getElementById('demo-locate-review-patient').addEventListener('click', locateDemoReviewPatient);
    document.getElementById('locate-feedback-patient').addEventListener('click', locateFeedbackPatient);
    document.getElementById('safety-self-test').addEventListener('click', async (event) => withBusyButton(event.currentTarget, '\u81ea\u6d4b\u4e2d...', async () => {
      try {
        await runSafetySelfTest();
      } catch (error) {
        setBatchActionResult(`\u5b89\u5168\u95e8\u81ea\u6d4b\u5931\u8d25\uff1a${error.message}`, 'danger');
        showDashboardToast('\u5b89\u5168\u95e8\u81ea\u6d4b\u5931\u8d25', error.message, 'danger');
      }
    }));
    document.getElementById('demo-continue-review').addEventListener('click', continueCurrentDemoReview);
    document.getElementById('demo-return-review').addEventListener('click', returnCurrentDemoReview);
    document.getElementById('demo-open-review-report').addEventListener('click', openDemoReviewReport);
    document.getElementById('demo-reset-review').addEventListener('click', resetDemoReviewScenario);
    document.getElementById('batch-auto-load-toggle')?.addEventListener('click', async () => {
      await setAutoLoadEnabled(!autoLoadEnabled);
    });
    updateAutoLoadUi();
    if (autoLoadEnabled) {
      setAutoLoadEnabled(true);
    }
    document.getElementById('batch-load-scan').addEventListener('click', async (event) => withBusyButton(event.currentTarget, '\u88c5\u836f\u6838\u9a8c\u4e2d...', async () => {
      try {
        const gate = buildBatchBlockers(latestDeliveryBatch || {}, 'load');
        if (gate.blockers.length) {
          setBatchActionResult(`暂不可装药核验：${gate.blockers.join(' ')}`, 'danger');
          showDashboardToast('暂不可装药核验', gate.blockers.join(' '), 'danger');
          updateBatchSafetyGate(latestDeliveryBatch || {});
          return;
        }
        await refreshDrugInfo();
        await refreshBackendBatchScanPreview('load');
        if (!confirmCriticalAction('\u786e\u8ba4\u6267\u884c\u836f\u5e08\u88c5\u836f\u6838\u9a8c\uff1f', buildBatchScanConfirmText('load'))) return;
        await postBatchAction('/api/delivery_batch/load_scan', '\u836f\u5e08\u88c5\u836f\u6838\u9a8c', { requireScan: true });
      } catch (error) {
        showDashboardToast('\u836f\u5e08\u88c5\u836f\u6838\u9a8c\u5931\u8d25', error.message, 'danger');
        setBatchActionResult(`\u836f\u5e08\u88c5\u836f\u6838\u9a8c\u5931\u8d25\uff1a${error.message}`, 'danger');
        log(`\u836f\u5e08\u88c5\u836f\u6838\u9a8c\u5931\u8d25\uff1a${error.message}`);
      }
    }));
    document.getElementById('batch-advance').addEventListener('click', async (event) => withBusyButton(event.currentTarget, '\u63a8\u8fdb\u4e2d...', async () => {
      try {
        const { blockers } = buildBatchBlockers(latestDeliveryBatch || {});
        if (blockers.length) {
          setBatchActionResult(`\u6682\u4e0d\u53ef\u63a8\u8fdb\uff1a${blockers.join(' ')}`, 'danger');
          showDashboardToast('\u6682\u4e0d\u53ef\u63a8\u8fdb', blockers.join(' '), 'danger');
          updateBatchSafetyGate(latestDeliveryBatch || {});
          return;
        }
        if (!confirmCriticalAction('\u786e\u8ba4\u8fdb\u5165\u4e0b\u4e00\u914d\u9001\u9636\u6bb5\uff1f', '\u7cfb\u7edf\u4f1a\u63a8\u8fdb\u5f53\u524d\u6279\u6b21\u72b6\u6001\uff1b\u82e5\u8fdb\u5165\u914d\u9001\uff0c\u4f1a\u5c1d\u8bd5\u521b\u5efa ROS2 \u914d\u9001\u4efb\u52a1\u5e76\u5199\u5165\u5ba1\u8ba1\u8bb0\u5f55\u3002')) return;
        await postBatchAction('/api/delivery_batch/advance', '\u914d\u9001\u9636\u6bb5\u63a8\u8fdb');
      } catch (error) {
        showDashboardToast('\u914d\u9001\u9636\u6bb5\u63a8\u8fdb\u5931\u8d25', error.message, 'danger');
        setBatchActionResult(`\u914d\u9001\u9636\u6bb5\u63a8\u8fdb\u5931\u8d25\uff1a${error.message}`, 'danger');
        log(`\u914d\u9001\u9636\u6bb5\u63a8\u8fdb\u5931\u8d25\uff1a${error.message}`);
      }
    }));
    document.getElementById('batch-dispense-scan').addEventListener('click', async (event) => withBusyButton(event.currentTarget, '\u4ea4\u4ed8\u6838\u9a8c\u4e2d...', async () => {
      try {
        const gate = buildBatchBlockers(latestDeliveryBatch || {}, 'dispense');
        if (gate.blockers.length) {
          setBatchActionResult(`暂不可交付核验：${gate.blockers.join(' ')}`, 'danger');
          showDashboardToast('暂不可交付核验', gate.blockers.join(' '), 'danger');
          updateBatchSafetyGate(latestDeliveryBatch || {});
          return;
        }
        await refreshDrugInfo();
        await refreshBackendBatchScanPreview('dispense');
        if (!confirmCriticalAction('\u786e\u8ba4\u6267\u884c\u5e8a\u65c1\u4ea4\u4ed8\u6838\u9a8c\uff1f', buildBatchScanConfirmText('dispense'))) return;
        await postBatchAction('/api/delivery_batch/dispense_scan', '\u5e8a\u65c1\u4ea4\u4ed8\u6838\u9a8c', { requireScan: true });
      } catch (error) {
        showDashboardToast('\u5e8a\u65c1\u4ea4\u4ed8\u6838\u9a8c\u5931\u8d25', error.message, 'danger');
        setBatchActionResult(`\u5e8a\u65c1\u4ea4\u4ed8\u6838\u9a8c\u5931\u8d25\uff1a${error.message}`, 'danger');
        log(`\u5e8a\u65c1\u4ea4\u4ed8\u6838\u9a8c\u5931\u8d25\uff1a${error.message}`);
      }
    }));
    document.getElementById('batch_audit_filter').addEventListener('change', event => {
      latestAuditFilter = event.target.value || 'all';
      renderBatchAudit((latestDeliveryBatch && latestDeliveryBatch.audit_records) || []);
    });
    document.querySelectorAll('[data-exception-filter]').forEach(button => {
      button.addEventListener('click', event => {
        exceptionCenterFilter = event.target.dataset.exceptionFilter || 'all';
        renderExceptionCenter(latestDeliveryBatch);
      });
    });
    document.getElementById('export-batch-json').addEventListener('click', () => {
      window.open('/api/delivery_batch/report.json', '_blank');
    });
    document.getElementById('export-batch-csv').addEventListener('click', () => {
      window.open('/api/delivery_batch/report.csv', '_blank');
    });
    document.getElementById('report-export-json').addEventListener('click', () => {
      window.open('/api/delivery_batch/report.json', '_blank');
    });
    document.getElementById('report-export-csv').addEventListener('click', () => {
      window.open('/api/delivery_batch/report.csv', '_blank');
    });
    document.getElementById('refresh-report').addEventListener('click', () => {
      renderDeliveryReport();
      log('配送报告已刷新');
    });
    document.getElementById('print-report').addEventListener('click', printDeliveryReport);
    document.getElementById('report_ward_filter').addEventListener('change', renderDeliveryReport);
    document.getElementById('report_status_filter').addEventListener('change', renderDeliveryReport);
    document.getElementById('report_search').addEventListener('input', renderDeliveryReport);
    document.getElementById('clear-report-filters').addEventListener('click', () => {
      document.getElementById('report_ward_filter').value = 'all';
      document.getElementById('report_status_filter').value = 'all';
      document.getElementById('report_search').value = '';
      renderDeliveryReport();
    });
    document.getElementById('load-batch-template').addEventListener('click', () => {
      document.getElementById('batch_import_text').value = JSON.stringify(buildBatchImportTemplate(), null, 2);
      previewBatchImportText('\u6a21\u677f');
    });
    document.getElementById('load-current-batch-json').addEventListener('click', () => {
      document.getElementById('batch_import_text').value = JSON.stringify(latestDeliveryBatch || {}, null, 2);
      previewBatchImportText('\u5f53\u524d\u6279\u6b21');
    });
    document.getElementById('batch_import_text').addEventListener('input', () => {
      if (batchImportPreviewTimer) clearTimeout(batchImportPreviewTimer);
      batchImportPreviewTimer = window.setTimeout(() => {
        previewBatchImportText();
      }, 260);
    });

    async function receiveBatchImportPayload(payload, fallbackMessage) {
      const data = await api('/api/delivery_batch/apply_import', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      const message = data.message || fallbackMessage || '\u5916\u90e8\u6279\u6b21\u5df2\u5bfc\u5165\u5e76\u91c7\u7528\u3002';
      updateDeliveryBatch(data.batch || data);
      updatePendingBatchPanel(data.pending || null);
      setBatchImportMessage(message);
      const importButton = document.getElementById('import-batch-json');
      if (importButton) importButton.disabled = true;
      document.getElementById('pending_batch_result').textContent = message;
      document.getElementById('pending_batch_result').style.color = 'var(--ok)';
      document.getElementById('batch_action_result').textContent = `${message} \u53ef\u76f4\u63a5\u8fdb\u884c\u81ea\u52a8\u8bc6\u522b\u88c5\u836f\u3002`;
      document.getElementById('batch_action_result').style.color = 'var(--ok)';
      log(message);
      return data;
    }

    document.getElementById('load-local-batch-json').addEventListener('click', () => {
      document.getElementById('batch-import-file').click();
    });
    document.getElementById('batch-import-file').addEventListener('change', async (event) => {
      const file = event.target.files && event.target.files[0];
      if (!file) {
        setBatchImportMessage('\u8bf7\u9009\u62e9 JSON \u6587\u4ef6\u3002', false);
        return;
      }
      try {
        const text = await file.text();
        document.getElementById('batch_import_text').value = text;
        const result = previewBatchImportText(`\u672c\u5730\u6587\u4ef6 ${file.name}`);
        if (result.ok) {
          setBatchImportMessage(`\u672c\u5730\u6587\u4ef6\u5df2\u8f7d\u5165\uff1a${file.name}\u3002\u8bf7\u6838\u5bf9\u9884\u89c8\uff0c\u786e\u8ba4\u540e\u70b9\u51fb\u201c\u63a5\u6536\u4e3a\u5f85\u91c7\u7528\u201d\u3002`);
        }
      } catch (error) {
        setBatchImportMessage(`\u672c\u5730\u6587\u4ef6\u8bfb\u53d6\u5931\u8d25\uff1a${error.message}`, false);
        log(`\u672c\u5730\u6279\u6b21\u6587\u4ef6\u8bfb\u53d6\u5931\u8d25\uff1a${error.message}`);
      } finally {
        event.target.value = '';
      }
    });
    document.getElementById('import-batch-json').addEventListener('click', async () => {
      try {
        const text = document.getElementById('batch_import_text').value.trim();
        if (!text) {
          setBatchImportMessage('\u8bf7\u5148\u586b\u5199\u6216\u8f7d\u5165\u5916\u90e8\u6279\u6b21 JSON\u3002', false);
          clearBatchImportPreview();
          return;
        }
        const result = previewBatchImportText();
        if (!result.ok) {
          setBatchImportMessage('\u9884\u89c8\u6821\u9a8c\u672a\u901a\u8fc7\uff0c\u8bf7\u5148\u4fee\u6b63\u9519\u8bef\u540e\u518d\u63a5\u6536\u3002', false);
          return;
        }
        await receiveBatchImportPayload(result.payload);
      } catch (error) {
        setBatchImportMessage(`\u63a5\u6536\u5931\u8d25\uff1a${error.message}`, false);
        log(`\u63a5\u6536\u5916\u90e8\u6279\u6b21\u5931\u8d25\uff1a${error.message}`);
      }
    });
    document.getElementById('adopt-pending-batch').addEventListener('click', async () => {
      try {
        if (!latestPendingBatch) {
          document.getElementById('pending_batch_result').textContent = '\u5f53\u524d\u6ca1\u6709\u5f85\u91c7\u7528\u6279\u6b21\u3002';
          document.getElementById('pending_batch_result').style.color = 'var(--danger)';
          return;
        }
        if (!confirmCriticalAction('\u786e\u8ba4\u91c7\u7528\u5916\u90e8\u6279\u6b21\uff1f', '\u91c7\u7528\u540e\u4f1a\u8986\u76d6\u5f53\u524d\u914d\u9001\u6279\u6b21\uff1b\u5df2\u6709\u88c5\u836f/\u914d\u9001\u8fdb\u5ea6\u8bf7\u5148\u786e\u8ba4\u662f\u5426\u9700\u8981\u5bfc\u51fa\u62a5\u544a\u3002')) return;
        const data = await api('/api/delivery_batch/adopt_pending', {
          method: 'POST',
          body: JSON.stringify({ operator_id: 'web_operator' }),
        });
        updateDeliveryBatch(data.batch || data);
        updatePendingBatchPanel(null);
        document.getElementById('pending_batch_result').textContent = data.message || '\u5916\u90e8\u6279\u6b21\u5df2\u91c7\u7528\u3002';
        document.getElementById('pending_batch_result').style.color = 'var(--ok)';
        const adoptedMessage = data.message || '\u5916\u90e8\u6279\u6b21\u5df2\u91c7\u7528\u3002';
        document.getElementById('batch_action_result').textContent = `${adoptedMessage} \u4e0b\u4e00\u6b65\uff1a\u5148\u6267\u884c\u836f\u5e08\u88c5\u836f\u6838\u9a8c\uff0c\u6838\u9a8c\u5b8c\u6210\u540e\u518d\u8fdb\u5165\u914d\u9001\u9636\u6bb5\u3002`;
        document.getElementById('batch_action_result').style.color = 'var(--ok)';
        log(data.message || '\u5916\u90e8\u6279\u6b21\u5df2\u91c7\u7528');
      } catch (error) {
        document.getElementById('pending_batch_result').textContent = `\u91c7\u7528\u5931\u8d25\uff1a${error.message}`;
        document.getElementById('pending_batch_result').style.color = 'var(--danger)';
        log(`\u91c7\u7528\u5916\u90e8\u6279\u6b21\u5931\u8d25\uff1a${error.message}`);
      }
    });
    document.getElementById('discard-pending-batch').addEventListener('click', async () => {
      try {
        if (!latestPendingBatch) return;
        if (!confirmCriticalAction('\u786e\u8ba4\u5ffd\u7565\u5f85\u91c7\u7528\u6279\u6b21\uff1f', '\u5ffd\u7565\u540e\u4e0d\u4f1a\u5f71\u54cd\u5f53\u524d\u914d\u9001\u6279\u6b21\u3002')) return;
        const data = await api('/api/delivery_batch/discard_pending', {
          method: 'POST',
          body: JSON.stringify({}),
        });
        updatePendingBatchPanel(null);
        document.getElementById('pending_batch_result').textContent = data.message || '\u5df2\u5ffd\u7565\u5f85\u91c7\u7528\u6279\u6b21\u3002';
        document.getElementById('pending_batch_result').style.color = 'var(--ok)';
        log(data.message || '\u5df2\u5ffd\u7565\u5f85\u91c7\u7528\u6279\u6b21');
      } catch (error) {
        document.getElementById('pending_batch_result').textContent = `\u5ffd\u7565\u5931\u8d25\uff1a${error.message}`;
        document.getElementById('pending_batch_result').style.color = 'var(--danger)';
        log(`\u5ffd\u7565\u5f85\u91c7\u7528\u6279\u6b21\u5931\u8d25\uff1a${error.message}`);
      }
    });
    document.getElementById('refresh').addEventListener('click', refreshState);
    document.getElementById('verify-scan').addEventListener('click', async () => {
      try {
        await verifyByStage('scan', '扫码校验通过', '扫码校验失败');
      } catch (error) {
        log(`扫码校验失败：${error.message}`);
      }
    });
    document.getElementById('confirm-load').addEventListener('click', async () => {
      try {
        await verifyByStage('load', '装药确认通过', '装药确认失败');
      } catch (error) {
        log(`装药确认失败：${error.message}`);
      }
    });
    document.getElementById('confirm-dispense').addEventListener('click', async () => {
      try {
        await verifyByStage('dispense', '取药确认通过', '取药确认失败');
      } catch (error) {
        log(`取药确认失败：${error.message}`);
      }
    });
    document.getElementById('cancel').addEventListener('click', async () => {
      try {
        const data = await api('/api/cancel', { method: 'POST', body: JSON.stringify({ task_id: latestTaskId }) });
        log(`${data.success ? '取消成功' : '取消失败'}：${data.message}`);
        await refreshState();
      } catch (error) {
        log(`取消失败：${error.message}`);
      }
    });

    loadStations().then(async () => {
      await loadPatientOrders();
      await refreshDeliveryBatch();
      await refreshState();
      await refreshDrugInfo();
      await refreshSystemLoad();
      await refreshChassisStatus();
      await refreshPatientMessages();
    }).catch(error => log(`初始化失败：${error.message}`));
    setInterval(refreshDeliveryBatch, 1500);
    setInterval(refreshPendingBatch, 3000);
    setInterval(refreshState, 1000);
    setInterval(refreshDrugInfo, 1000);
    setInterval(runAutoLoadRecognitionCycle, 1200);
    setInterval(refreshSystemLoad, 1000);
    setInterval(refreshChassisStatus, 1000);
    setInterval(refreshPatientMessages, 3000);
    setInterval(refreshHealthCheckApi, 3000);
    setInterval(refreshHealthCheck, 1000);
  </script>
</body>
</html>
"""











