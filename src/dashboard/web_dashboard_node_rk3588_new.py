import copy
import csv
import io
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import rclpy
from ament_index_python.packages import get_package_share_directory
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
import yaml

from medicine_interfaces.msg import DeliveryState, DrugInfo
from medicine_interfaces.srv import (
    CancelDeliveryTask,
    CreateDeliveryTask,
    VerifyDeliveryTask,
)
from std_msgs.msg import String

try:
    from delivery_database import DeliveryDatabase

    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("Warning: delivery_database not available")


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
                "medicine_name": "演示二维码药品",
                "product_code": "43043",
                "product_model": "QR-43043-DEMO",
                "quantity": "1",
                "trace_id": "",
                "order_no": "DEMO-P001-001",
                "dose": "1盒",
                "usage": "按医嘱",
            },
            {
                "id": "p001_med_002",
                "medicine_name": "降压药",
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
                "order_no": "DEMO-P002-001",
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
                "medicine_name": "止咳药",
                "product_code": "C300210",
                "product_model": "CKT0100-12-A",
                "quantity": "1",
                "trace_id": "TRACE-P003-001",
                "order_no": "DEMO-P003-001",
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
                "order_no": "DEMO-P003-002",
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
                "medicine_name": "胃药",
                "product_code": "C400310",
                "product_model": "GST0200-20-A",
                "quantity": "2",
                "trace_id": "TRACE-P004-001",
                "order_no": "DEMO-P004-001",
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
                "order_no": "DEMO-P004-002",
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
                "medicine_name": "真实标签演示药品",
                "product_code": "C2765186",
                "product_model": "REAL-LABEL-DEMO",
                "quantity": "1",
                "trace_id": "175550822",
                "order_no": "DEMO-P005-001",
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
                "order_no": "DEMO-P005-002",
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
                "order_no": "DEMO-P006-001",
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
  <title>智能送药小车任务面板</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap" />
  <style>
    /* === Clinical Precision Design System ===
       基底 #0b0d0e · 临床薄荷 #5eead4 · 朱砂 #f87171 · 琥珀 #f59e0b
       字体 IBM Plex Sans + IBM Plex Mono（数据/编码）+ Noto Sans SC（中文）
       结构 发丝边 · 直角为主 · 无阴影 · 信息密度向仪器倾斜 */

    :root {
      color-scheme: dark;
      --bg:        #0b0d0e;
      --surface-0: #111416;
      --surface-1: #15181a;
      --surface-2: #1c2024;
      --surface-3: #242a30;
      --border:    #2a3036;
      --border-hi: #3a424a;
      --rule:      #20262c;
      --text:      #e8ecef;
      --text-dim:  #8b949c;
      --text-faint:#5a6068;
      --mint:      #5eead4;
      --mint-dim:  #2dd4bf;
      --mint-deep: #0f2a26;
      --amber:     #f59e0b;
      --amber-dim: #b97506;
      --amber-deep:#2a1d05;
      --red:       #f87171;
      --red-dim:   #c54545;
      --red-deep:  #2a0e0e;
      --blue:      #60a5fa;
      --blue-deep: #0e1f33;

      --font-sans: "IBM Plex Sans", "Noto Sans SC", "Source Han Sans SC", "Microsoft YaHei", system-ui, sans-serif;
      --font-mono: "IBM Plex Mono", "JetBrains Mono", "Cascadia Code", ui-monospace, SFMono-Regular, "Consolas", monospace;

      /* 兼容别名：JS 里的行内 style 还在用旧变量名 */
      --ok: var(--mint);
      --danger: var(--red);
      --warn: var(--amber);
      --primary: var(--mint);
      --primary-dark: var(--mint-dim);
      --muted: var(--text-dim);
      --card: var(--surface-1);
    }

    *, *::before, *::after { box-sizing: border-box; }

    html, body { height: 100%; }
    body {
      margin: 0;
      font-family: var(--font-sans);
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      font-feature-settings: "tnum" 1, "ss01" 1;
      -webkit-font-smoothing: antialiased;
      text-rendering: optimizeLegibility;
      font-size: 14px;
      line-height: 1.5;
    }

    /* 顶部仪器读数带：上下双发丝线 + 等宽刻度 */
    header {
      position: relative;
      max-width: 1320px;
      margin: 0 auto;
      padding: 28px 28px 18px;
      border-bottom: 1px solid var(--rule);
    }
    header::before {
      content: "";
      position: absolute; left: 0; right: 0; top: 0;
      height: 1px;
      background:
        linear-gradient(to right,
          transparent 0, transparent 24px,
          var(--mint) 24px, var(--mint) 32px,
          transparent 32px, transparent 56px,
          var(--text-faint) 56px, var(--text-faint) 60px,
          transparent 60px);
    }
    h1 {
      margin: 0;
      font-family: var(--font-mono);
      font-weight: 600;
      font-size: clamp(20px, 2.4vw, 26px);
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: var(--text);
    }
    h1::before {
      content: "▣ ";
      color: var(--mint);
      margin-right: 2px;
    }
    .subtitle {
      margin-top: 8px;
      color: var(--text-dim);
      font-size: 12px;
      font-family: var(--font-mono);
      letter-spacing: 0.04em;
    }
    .subtitle::before {
      content: "// ";
      color: var(--text-faint);
    }

    /* 标签条：高对比、等宽、紧致字距 */
    .dashboard-tabs {
      max-width: 1320px;
      margin: 0 auto;
      padding: 16px 28px 0;
      display: flex;
      gap: 0;
      overflow-x: auto;
      border-bottom: 1px solid var(--rule);
    }
    .tab-button {
      flex: 0 0 auto;
      background: transparent;
      color: var(--text-dim);
      border: 0;
      border-bottom: 2px solid transparent;
      border-radius: 0;
      padding: 12px 18px;
      font-family: var(--font-mono);
      font-size: 12px;
      font-weight: 500;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      cursor: pointer;
      box-shadow: none;
      transition: color .12s linear, border-color .12s linear;
    }
    .tab-button:hover { color: var(--text); }
    .tab-button.active {
      color: var(--mint);
      border-bottom-color: var(--mint);
      background: transparent;
    }
    .tab-button.active::before { content: "● "; font-size: 10px; }

    main {
      max-width: 1320px;
      margin: 0 auto;
      padding: 20px 28px 60px;
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 16px;
    }
    [data-page] { display: none; }
    [data-page].active { display: block; }
    [data-page="vision"].active, [data-page="report"].active { grid-column: 1 / -1; }

    /* 卡片：发丝边 + 直角，不漂浮 */
    .card {
      background: var(--surface-1);
      border: 1px solid var(--border);
      border-radius: 2px;
      box-shadow: none;
      padding: 22px 24px;
      backdrop-filter: none;
      position: relative;
    }
    .card::before {
      content: "";
      position: absolute;
      top: -1px; left: -1px;
      width: 14px; height: 14px;
      border-top: 1px solid var(--mint);
      border-left: 1px solid var(--mint);
      pointer-events: none;
    }
    .card h2 {
      margin: 0 0 18px;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--text-dim);
      padding-bottom: 12px;
      border-bottom: 1px solid var(--rule);
    }
    .card h2::before { content: "┄ "; color: var(--text-faint); }

    /* 表单：暗色背景 + 等宽输入 + 薄荷绿 focus */
    label {
      display: block;
      margin: 14px 0 6px;
      color: var(--text-dim);
      font-family: var(--font-mono);
      font-weight: 500;
      font-size: 11px;
      letter-spacing: 0.1em;
      text-transform: uppercase;
    }
    input, select, textarea {
      width: 100%;
      border: 1px solid var(--border);
      border-radius: 2px;
      padding: 10px 12px;
      font-size: 14px;
      font-family: var(--font-mono);
      background: var(--surface-0);
      color: var(--text);
      outline: none;
      transition: border-color .12s linear;
    }
    select {
      appearance: none;
      background-image: linear-gradient(45deg, transparent 50%, var(--text-dim) 50%),
                        linear-gradient(135deg, var(--text-dim) 50%, transparent 50%);
      background-position: calc(100% - 16px) 50%, calc(100% - 11px) 50%;
      background-size: 5px 5px, 5px 5px;
      background-repeat: no-repeat;
      padding-right: 30px;
    }
    textarea {
      min-height: 240px;
      resize: vertical;
      line-height: 1.55;
      font-size: 12px;
    }
    input:focus, select:focus, textarea:focus {
      border-color: var(--mint);
      box-shadow: inset 0 0 0 1px var(--mint);
    }
    ::placeholder { color: var(--text-faint); }

    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }

    /* 识别面板：蓝色信息态 */
    .recognized-panel {
      margin-top: 14px;
      padding: 14px;
      border: 1px solid var(--border);
      border-left: 2px solid var(--blue);
      border-radius: 0;
      background: var(--surface-2);
    }
    .recognized-panel-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
      font-family: var(--font-mono);
      font-size: 11px;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--text-dim);
    }
    .recognized-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1px;
      background: var(--rule);
      border: 1px solid var(--rule);
    }
    .recognized-item {
      min-width: 0;
      background: var(--surface-1);
      padding: 10px 12px;
    }
    .recognized-item span {
      display: block;
      color: var(--text-faint);
      font-family: var(--font-mono);
      font-size: 10px;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      margin-bottom: 4px;
    }
    .recognized-item strong {
      display: block;
      overflow-wrap: anywhere;
      font-family: var(--font-mono);
      font-size: 13px;
      font-weight: 500;
      color: var(--text);
    }

    /* 按钮：直角、发丝边、悬停改色不动位移 */
    button {
      border: 1px solid var(--border-hi);
      background: var(--surface-2);
      color: var(--text);
      border-radius: 2px;
      padding: 9px 14px;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      cursor: pointer;
      transition: background .12s linear, border-color .12s linear, color .12s linear;
    }
    button:hover {
      background: var(--surface-3);
      border-color: var(--mint);
      color: var(--mint);
      transform: none;
    }
    button:active { background: var(--surface-1); }
    button:focus-visible {
      outline: 1px solid var(--mint);
      outline-offset: 2px;
    }

    .primary {
      width: 100%;
      margin-top: 18px;
      background: var(--mint);
      color: var(--bg);
      border-color: var(--mint);
      font-weight: 700;
      padding: 12px 16px;
      letter-spacing: 0.14em;
    }
    .primary:hover {
      background: var(--mint-dim);
      color: var(--bg);
      border-color: var(--mint-dim);
    }
    .primary::before { content: "▶ "; }

    .secondary {
      background: var(--surface-2);
      color: var(--text);
      border-color: var(--border-hi);
    }
    .small-button {
      padding: 6px 10px;
      font-size: 10px;
      border-radius: 2px;
    }
    .danger {
      background: var(--red-deep);
      color: var(--red);
      border-color: var(--red-dim);
    }
    .danger:hover {
      background: var(--red);
      color: var(--bg);
      border-color: var(--red);
    }

    /* 顶部状态行 */
    .status-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 18px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--rule);
    }
    .status-head h2 {
      margin: 0;
      padding: 0;
      border: 0;
    }

    /* 状态徽章：方块、等宽、紧致字距 */
    .badge {
      display: inline-flex;
      align-items: center;
      min-width: 0;
      justify-content: center;
      border-radius: 2px;
      padding: 6px 12px;
      font-family: var(--font-mono);
      font-weight: 600;
      font-size: 11px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--text-dim);
      background: transparent;
      border: 1px solid var(--border-hi);
    }
    .badge::before {
      content: "■";
      margin-right: 6px;
      font-size: 8px;
      color: currentColor;
    }
    .badge.IDLE { color: var(--text-dim); border-color: var(--border-hi); }
    .badge.WAITING_LOAD_CONFIRMATION,
    .badge.WAITING_DISPENSE_CONFIRMATION,
    .badge.ARRIVED {
      color: var(--amber);
      border-color: var(--amber-dim);
      background: var(--amber-deep);
    }
    .badge.NAVIGATING {
      color: var(--blue);
      border-color: var(--blue);
      background: var(--blue-deep);
    }
    .badge.NAVIGATING::before {
      animation: pulse-dot 1.6s linear infinite;
    }
    .badge.COMPLETED {
      color: var(--mint);
      border-color: var(--mint);
      background: var(--mint-deep);
    }
    .badge.CANCELED {
      color: var(--red);
      border-color: var(--red-dim);
      background: var(--red-deep);
    }
    @keyframes pulse-dot {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.25; }
    }

    /* 进度条：扁平、发丝边、扫描线 */
    .progress-wrap {
      height: 6px;
      background: var(--surface-0);
      border: 1px solid var(--rule);
      border-radius: 0;
      overflow: hidden;
      margin: 14px 0 18px;
      position: relative;
    }
    .progress {
      height: 100%;
      width: 0%;
      background: var(--mint);
      transition: width .3s linear;
      position: relative;
    }
    .progress::after {
      content: "";
      position: absolute;
      top: 0; right: 0; bottom: 0;
      width: 24px;
      background: linear-gradient(90deg, transparent, rgba(94, 234, 212, 0.5));
    }

    /* 键值行：单行、左侧标签等宽小字 */
    .kv {
      display: grid;
      grid-template-columns: 130px 1fr;
      gap: 12px;
      padding: 8px 0;
      border-bottom: 1px solid var(--rule);
      font-size: 13px;
      align-items: baseline;
    }
    .kv:last-child { border-bottom: 0; }
    .kv span:first-child {
      color: var(--text-faint);
      font-family: var(--font-mono);
      font-size: 10px;
      letter-spacing: 0.1em;
      text-transform: uppercase;
    }
    .kv strong {
      min-width: 0;
      overflow-wrap: anywhere;
      font-family: var(--font-mono);
      font-weight: 500;
      color: var(--text);
      font-size: 13px;
    }

    .drug-card { margin-top: 16px; }
    .drug-loaded { color: var(--mint); }
    .drug-empty { color: var(--red); }

    /* 摄像头预览：保留暗背景 + 边角十字准星 */
    .camera-preview-wrap {
      margin-bottom: 16px;
      overflow: hidden;
      border-radius: 0;
      border: 1px solid var(--border);
      background: #050708;
      aspect-ratio: 4 / 3;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
    }
    .camera-preview-wrap::before,
    .camera-preview-wrap::after {
      content: "";
      position: absolute;
      width: 18px; height: 18px;
      border: 1px solid var(--mint);
    }
    .camera-preview-wrap::before {
      top: 8px; left: 8px;
      border-right: 0; border-bottom: 0;
    }
    .camera-preview-wrap::after {
      bottom: 8px; right: 8px;
      border-left: 0; border-top: 0;
    }
    .camera-preview-wrap img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      display: block;
    }
    .camera-preview-hint {
      margin-bottom: 10px;
      color: var(--text-dim);
      font-family: var(--font-mono);
      font-size: 11px;
      letter-spacing: 0.04em;
    }
    .camera-preview-hint::before { content: "// "; color: var(--text-faint); }

    .actions {
      display: flex;
      gap: 6px;
      margin-top: 16px;
      flex-wrap: wrap;
    }

    /* 终端式日志 */
    .log {
      margin-top: 16px;
      border-radius: 0;
      background: #050708;
      color: var(--mint);
      min-height: 120px;
      padding: 14px 16px;
      font-family: var(--font-mono);
      font-size: 12px;
      line-height: 1.55;
      white-space: pre-wrap;
      overflow: auto;
      border: 1px solid var(--border);
      position: relative;
    }
    .log::before {
      content: "[stdout]";
      position: absolute;
      top: 6px; right: 10px;
      font-size: 9px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--text-faint);
    }

    .notice {
      margin-top: 12px;
      color: var(--text-dim);
      font-size: 12px;
      line-height: 1.6;
      padding: 10px 12px;
      background: var(--surface-2);
      border-left: 2px solid var(--border-hi);
    }
    .notice::before { content: "› "; color: var(--text-faint); }

    /* 审计/扫码记录：终端日志风 */
    .audit-list {
      margin-top: 12px;
      border: 1px solid var(--border);
      border-radius: 0;
      overflow: hidden;
      background: var(--surface-0);
    }
    .audit-item {
      padding: 10px 12px;
      border-bottom: 1px solid var(--rule);
      font-size: 12px;
      line-height: 1.45;
      font-family: var(--font-mono);
    }
    .audit-item:last-child { border-bottom: 0; }
    .audit-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 4px;
      font-weight: 600;
      letter-spacing: 0.04em;
      color: var(--text);
    }
    .audit-pass { color: var(--mint); }
    .audit-pass::before { content: "✓ "; }
    .audit-fail { color: var(--red); }
    .audit-fail::before { content: "✗ "; }
    .audit-detail {
      color: var(--text-dim);
      overflow-wrap: anywhere;
      font-size: 11px;
    }

    /* 患者面板：薄荷绿强调 */
    .patient-panel {
      margin-top: 16px;
      padding: 14px;
      border: 1px solid var(--border);
      border-left: 2px solid var(--mint);
      border-radius: 0;
      background: var(--surface-2);
    }
    .medication-list {
      display: grid;
      gap: 6px;
      margin-top: 10px;
    }
    .medication-item {
      border: 1px solid var(--border);
      border-radius: 0;
      padding: 10px 12px;
      background: var(--surface-1);
      font-family: var(--font-mono);
      font-size: 12px;
      transition: border-color .12s linear;
    }
    .medication-item.matched {
      border-color: var(--mint);
      background: var(--mint-deep);
    }
    .medication-item.loaded {
      border-color: var(--blue);
      background: var(--blue-deep);
    }
    .medication-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 6px;
      font-weight: 600;
      letter-spacing: 0.04em;
    }

    /* 批次：三列等密度、可单独滚 */
    .batch-card { grid-column: 1 / -1; }
    .batch-layout {
      display: grid;
      grid-template-columns: 0.95fr 1.25fr 0.8fr;
      gap: 0;
      background: var(--rule);
      border: 1px solid var(--rule);
    }
    .batch-panel {
      border: 0;
      border-radius: 0;
      background: var(--surface-1);
      padding: 14px 16px;
      min-width: 0;
      min-height: 0;
    }
    .batch-panel + .batch-panel { border-left: 1px solid var(--rule); }
    .batch-panel h2 {
      font-family: var(--font-mono);
      font-size: 10px;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      color: var(--text-dim);
      margin-bottom: 12px !important;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--rule);
    }
    #batch_stops {
      max-height: calc(100vh - 360px);
      min-height: 420px;
      overflow: auto;
      padding-right: 4px;
    }

    /* 路线步骤：方形 tag */
    .route-steps {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      margin-top: 10px;
    }
    .route-step {
      border-radius: 0;
      border: 1px solid var(--border);
      background: var(--surface-2);
      color: var(--text-dim);
      padding: 4px 10px;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 500;
      letter-spacing: 0.06em;
    }
    .route-step.active {
      background: var(--mint-deep);
      border-color: var(--mint);
      color: var(--mint);
    }

    .batch-stop {
      border: 1px solid var(--border);
      border-radius: 0;
      background: var(--surface-2);
      padding: 12px;
      margin-bottom: 8px;
    }
    .batch-stop.active {
      border-color: var(--mint);
      box-shadow: inset 2px 0 0 0 var(--mint);
    }
    .batch-stop-head, .batch-patient-head, .batch-med-head {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: center;
      font-family: var(--font-mono);
      font-weight: 600;
      font-size: 12px;
      letter-spacing: 0.04em;
      margin-bottom: 6px;
      color: var(--text);
    }
    .batch-patient {
      border-top: 1px dashed var(--rule);
      padding-top: 10px;
      margin-top: 10px;
    }
    .batch-med {
      border-radius: 0;
      border: 1px solid var(--rule);
      padding: 8px 10px;
      margin-top: 6px;
      background: var(--surface-1);
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-dim);
    }
    .batch-med.loaded {
      border-color: var(--blue);
      background: var(--blue-deep);
      color: var(--text);
    }
    .batch-med.dispensed {
      border-color: var(--mint);
      background: var(--mint-deep);
      color: var(--text);
    }

    /* batch-status: 方形小条，无圆角 */
    .batch-status {
      display: inline-flex;
      border-radius: 0;
      padding: 3px 8px;
      background: transparent;
      color: var(--text-dim);
      border: 1px solid var(--border-hi);
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      white-space: nowrap;
    }
    .batch-status.ok      { color: var(--mint);  border-color: var(--mint);    background: var(--mint-deep); }
    .batch-status.warn    { color: var(--amber); border-color: var(--amber-dim); background: var(--amber-deep); }
    .batch-status.info    { color: var(--blue);  border-color: var(--blue);    background: var(--blue-deep); }
    .batch-status.danger  { color: var(--red);   border-color: var(--red-dim);   background: var(--red-deep); }

    .batch-audit {
      max-height: calc(100vh - 360px);
      min-height: 420px;
      overflow: auto;
    }
    .batch-import {
      margin-top: 16px;
      border-top: 1px dashed var(--rule);
      padding-top: 14px;
    }
    .batch-import summary {
      cursor: pointer;
      color: var(--mint);
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      margin-bottom: 10px;
      padding: 6px 0;
      list-style: none;
    }
    .batch-import summary::before { content: "▸ "; }
    .batch-import[open] summary::before { content: "▾ "; }

    /* 通用折叠区：折次要 kv */
    .details-fold {
      margin-top: 10px;
      border-top: 1px solid var(--rule);
      padding-top: 6px;
    }
    .details-fold summary {
      cursor: pointer;
      list-style: none;
      color: var(--text-dim);
      font-family: var(--font-mono);
      font-size: 10px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      padding: 6px 0;
      transition: color .12s linear;
    }
    .details-fold summary:hover { color: var(--mint); }
    .details-fold summary::-webkit-details-marker { display: none; }
    .details-fold summary::before { content: "▸ "; color: var(--text-faint); }
    .details-fold[open] summary::before { content: "▾ "; color: var(--mint); }
    .details-fold[open] summary { color: var(--mint); margin-bottom: 6px; border-bottom: 1px solid var(--rule); }

    /* 报告统计：六列读数表盘 */
    .report-summary-grid {
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 0;
      margin: 14px 0 18px;
      border: 1px solid var(--rule);
      background: var(--rule);
    }
    .report-summary-card {
      border: 0;
      border-radius: 0;
      padding: 14px 16px;
      background: var(--surface-1);
      min-width: 0;
    }
    .report-summary-card span {
      display: block;
      color: var(--text-faint);
      font-family: var(--font-mono);
      font-size: 10px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      margin-bottom: 8px;
    }
    .report-summary-card strong {
      display: block;
      font-family: var(--font-mono);
      font-size: 28px;
      font-weight: 500;
      color: var(--text);
      letter-spacing: -0.02em;
    }
    .report-controls {
      display: grid;
      grid-template-columns: 1fr 1fr 1.3fr auto;
      gap: 10px;
      align-items: end;
      margin-bottom: 14px;
    }
    .report-table-wrap {
      border: 1px solid var(--border);
      border-radius: 0;
      overflow: auto;
      background: var(--surface-0);
      max-height: calc(100vh - 390px);
    }
    .report-table {
      width: 100%;
      border-collapse: collapse;
      min-width: 980px;
      font-size: 12px;
      font-family: var(--font-mono);
    }
    .report-table th, .report-table td {
      border-bottom: 1px solid var(--rule);
      padding: 10px 12px;
      text-align: left;
      vertical-align: top;
    }
    .report-table th {
      background: var(--surface-2);
      color: var(--text-dim);
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      position: sticky;
      top: 0;
      z-index: 1;
      border-bottom: 1px solid var(--border-hi);
    }
    .report-table td { color: var(--text); }
    .report-table tr:hover td { background: var(--surface-2); }
    .report-table tr:last-child td { border-bottom: 0; }

    /* 滚动条 */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: var(--surface-0); }
    ::-webkit-scrollbar-thumb { background: var(--border-hi); }
    ::-webkit-scrollbar-thumb:hover { background: var(--text-faint); }

    /* 选中文本：薄荷绿反白 */
    ::selection { background: var(--mint); color: var(--bg); }

    /* 响应式 */
    @media (max-width: 980px) {
      main { grid-template-columns: 1fr; }
      .grid-2 { grid-template-columns: 1fr; }
      .batch-layout { grid-template-columns: 1fr; }
      .batch-panel + .batch-panel { border-left: 0; border-top: 1px solid var(--rule); }
      .report-summary-grid { grid-template-columns: 1fr 1fr; }
      .report-controls { grid-template-columns: 1fr; }
      .kv { grid-template-columns: 110px 1fr; }
    }
    @media (max-width: 560px) {
      header { padding: 22px 16px 14px; }
      main { padding: 16px 16px 40px; }
      .dashboard-tabs { padding: 12px 16px 0; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Medicine Delivery · Operator Console</h1>
    <div class="subtitle">RK3588 · ROS 2 Humble · 任务调度 · 扫码核验 · 视觉识别 · 实时审计</div>
  </header>
  <nav class="dashboard-tabs" aria-label="控制台分区">
    <button class="tab-button active" type="button" data-tab="batch">配送批次</button>
    <button class="tab-button" type="button" data-tab="report">配送报告</button>
    <button class="tab-button" type="button" data-tab="task">单任务调试</button>
    <button class="tab-button" type="button" data-tab="vision">药品识别</button>
  </nav>
  <main>
    <section class="card batch-card active" data-page="batch">
      <div class="status-head">
        <h2>配送批次控制台</h2>
        <div id="batch-status-badge" class="badge IDLE">WAITING</div>
      </div>
      <div class="batch-layout">
        <div class="batch-panel">
          <h2 style="font-size: 18px; margin-bottom: 12px;">批次概览</h2>
          <div class="kv"><span>批次号</span><strong id="batch_id">-</strong></div>
          <div class="kv"><span>当前状态</span><strong id="batch_route_status">-</strong></div>
          <div class="kv"><span>当前位置</span><strong id="batch_current_station">-</strong></div>
          <div class="kv"><span>病房进度</span><strong id="batch_stop_progress">-</strong></div>
          <div class="kv"><span>病人进度</span><strong id="batch_patient_progress">-</strong></div>
          <div class="kv"><span>药品进度</span><strong id="batch_medication_progress">-</strong></div>
          <div class="route-steps" id="batch_route_steps"></div>
          <div class="actions">
            <button id="reset-batch" class="secondary" type="button">重建演示批次</button>
            <button id="batch-load-scan" class="secondary" type="button">批次装药扫码</button>
            <button id="batch-advance" class="secondary" type="button">推进下一步</button>
            <button id="batch-dispense-scan" class="secondary" type="button">病房交付扫码</button>
            <button id="export-batch-json" class="secondary" type="button">导出 JSON 报告</button>
            <button id="export-batch-csv" class="secondary" type="button">导出 CSV 报告</button>
          </div>
          <div class="notice" id="batch_action_result">先完成全部装药扫码，再推进到 A/B/C 病房交付。</div>
          <details class="batch-import">
            <summary>真实批次 JSON 导入 / 编辑</summary>
            <label for="batch_import_text">批次 JSON</label>
            <textarea id="batch_import_text" spellcheck="false"></textarea>
            <div class="actions">
              <button id="load-batch-template" class="secondary" type="button">填入模板</button>
              <button id="load-current-batch-json" class="secondary" type="button">载入当前批次</button>
              <button id="import-batch-json" class="primary" type="button">应用为当前批次</button>
            </div>
            <div class="notice" id="batch_import_result">支持导入病人/药品清单 JSON，应用后会覆盖当前批次并持久化。</div>
          </details>
        </div>
        <div class="batch-panel">
          <h2 style="font-size: 18px; margin-bottom: 12px;">病房 / 病人 / 药品清单</h2>
          <div id="batch_stops"></div>
        </div>
        <div class="batch-panel">
          <h2 style="font-size: 18px; margin-bottom: 12px;">批次审计记录</h2>
          <div id="batch_audit_records" class="audit-list batch-audit">
            <div class="audit-item"><div class="audit-detail">暂无批次审计记录</div></div>
          </div>
        </div>
      </div>
    </section>
    <section class="card" data-page="report">
      <div class="status-head">
        <h2>配送报告</h2>
        <div class="actions">
          <button id="refresh-report" class="secondary small-button" type="button">刷新报告</button>
          <button id="print-report" class="secondary small-button" type="button">打印报告</button>
          <button id="report-export-json" class="secondary small-button" type="button">导出 JSON</button>
          <button id="report-export-csv" class="secondary small-button" type="button">导出 CSV</button>
        </div>
      </div>
      <div class="kv"><span>批次号</span><strong id="report_batch_id">-</strong></div>
      <div class="kv"><span>生成时间</span><strong id="report_generated_at">-</strong></div>
      <div class="report-summary-grid">
        <div class="report-summary-card"><span>病房</span><strong id="report_stop_count">0</strong></div>
        <div class="report-summary-card"><span>病人</span><strong id="report_patient_count">0</strong></div>
        <div class="report-summary-card"><span>药品</span><strong id="report_medication_count">0</strong></div>
        <div class="report-summary-card"><span>已交付</span><strong id="report_dispensed_count">0</strong></div>
        <div class="report-summary-card"><span>异常/回收</span><strong id="report_issue_count">0</strong></div>
        <div class="report-summary-card"><span>人工复核</span><strong id="report_review_count">0</strong></div>
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
            <option value="reviewed">已人工复核</option>
          </select>
        </div>
        <div>
          <label for="report_search">关键词</label>
          <input id="report_search" placeholder="搜索病人、床号、药品、编码、追溯编号" />
        </div>
        <button id="clear-report-filters" class="secondary" type="button">清除筛选</button>
      </div>
      <div class="notice" id="report_filter_result">报告数据会随当前批次自动刷新。</div>
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
          <div class="notice" id="autofill_hint">识别到结构化标签后会自动填充药品名称。</div>
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
      <div class="kv"><span>进度</span><strong id="progress_text">0%</strong></div>
      <details class="details-fold">
        <summary>展开次要字段（编码 / 时间戳 / 校验）</summary>
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
      </details>
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
    <section class="card" data-page="task">
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
      <div class="notice" id="chassis_status_hint">未启用底盘桥接时这里会保持未收到状态；接飞控前应始终保持只读、禁控和急停。</div>
    </section>
    <section class="card drug-card" data-page="vision">
      <h2>药物识别信息</h2>
      <div class="camera-preview-hint">摄像头实时预览：来自 medicine_vision_detector 的 MJPEG 画面流。</div>
      <div class="camera-preview-wrap">
        <img id="camera-preview" alt="摄像头识别画面" />
      </div>
      <div class="kv"><span>药品 ID</span><strong id="drug_id">-</strong></div>
      <div class="kv"><span>药品名称</span><strong id="drug_name">-</strong></div>
      <div class="kv"><span>药品类型</span><strong id="drug_type">-</strong></div>
      <div class="kv"><span>置信度</span><strong id="drug_confidence">-</strong></div>
      <div class="kv"><span>装药状态</span><strong id="drug_loaded">-</strong></div>
      <div class="kv"><span>识别来源</span><strong id="drug_source">-</strong></div>
      <div class="kv"><span>更新时间</span><strong id="drug_stamp">-</strong></div>
      <details class="details-fold">
        <summary>展开扫码/OCR 详情</summary>
        <div class="kv"><span>原始码</span><strong id="code_text">-</strong></div>
        <div class="kv"><span>码类型</span><strong id="code_type">-</strong></div>
        <div class="kv"><span>识别方法</span><strong id="code_method">-</strong></div>
        <div class="kv"><span>OCR 文本</span><strong id="ocr_text">-</strong></div>
        <div class="kv"><span>OCR 置信度</span><strong id="ocr_confidence">-</strong></div>
        <div class="kv"><span>OCR 后端</span><strong id="ocr_backend">-</strong></div>
        <div class="kv"><span>OCR 状态</span><strong id="ocr_status">-</strong></div>
      </details>
      <details class="details-fold">
        <summary>展开标签字段（订单 / 编码 / 追溯）</summary>
        <div class="kv"><span>订单号</span><strong id="label_order_no">-</strong></div>
        <div class="kv"><span>产品编码</span><strong id="label_product_code">-</strong></div>
        <div class="kv"><span>产品型号</span><strong id="label_product_model">-</strong></div>
        <div class="kv"><span>数量</span><strong id="label_quantity">-</strong></div>
        <div class="kv"><span>追溯编号</span><strong id="label_trace_id">-</strong></div>
      </details>
      <div class="notice">当前数据来自 ROS2 话题 <b>/medicine/drug_info</b> 和 <b>/medicine/drug_recognition_status</b>，支持二维码/工业码识别与标签字段解析。</div>
    </section>
  </main>
  <script>
    const result = document.getElementById('result');
    const cameraPreview = document.getElementById('camera-preview');
    const medicineNameInput = document.getElementById('medicine_name');
    let latestTaskId = '';
    let latestDrugInfo = {};
    let lastAutoFilledMedicineName = '';
    let patientOrders = [];
    let selectedPatientOrder = null;
    let latestDeliveryBatch = {};
    let latestReportRows = [];
    let latestReportFilteredRows = [];
    let latestReportGeneratedAt = '';
    let latestChassisStatus = {};
    let cameraPreviewStreaming = false;
    let cameraPreviewReconnectTimer = null;
    const SCAN_MAX_AGE_SEC = 8;

    function isCameraPreviewVisible() {
      return document.visibilityState !== 'hidden' && Boolean(document.querySelector('[data-page="vision"].active'));
    }

    function startCameraPreview() {
      if (!isCameraPreviewVisible() || cameraPreviewStreaming) {
        return;
      }
      cameraPreviewStreaming = true;
      cameraPreview.src = `${window.location.protocol}//${window.location.hostname}:8090/stream.mjpg?ts=${Date.now()}`;
    }

    function stopCameraPreview() {
      if (cameraPreviewReconnectTimer) {
        clearTimeout(cameraPreviewReconnectTimer);
        cameraPreviewReconnectTimer = null;
      }
      cameraPreviewStreaming = false;
      cameraPreview.removeAttribute('src');
    }

    function syncCameraPreview() {
      if (isCameraPreviewVisible()) {
        startCameraPreview();
      } else {
        stopCameraPreview();
      }
    }

    cameraPreview.addEventListener('error', () => {
      cameraPreviewStreaming = false;
      if (!isCameraPreviewVisible()) {
        return;
      }
      if (cameraPreviewReconnectTimer) {
        clearTimeout(cameraPreviewReconnectTimer);
      }
      cameraPreviewReconnectTimer = setTimeout(() => {
        cameraPreviewReconnectTimer = null;
        startCameraPreview();
      }, 2000);
    });
    document.addEventListener('visibilitychange', syncCameraPreview);

    function log(text) {
      const now = new Date().toLocaleTimeString();
      result.textContent = `[${now}] ${text}\n` + result.textContent;
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
      const response = await fetch(path, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.message || `HTTP ${response.status}`);
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
        WAITING_LOAD_CONFIRMATION: '等待装药',
        READY_TO_DEPART: '待出发',
        NAVIGATING_TO_WARD: '前往病房',
        WARD_HANDOVER: '病房交付',
        WARD_COMPLETED: '病房完成',
        RETURNING_TO_PHARMACY: '返回药房',
        BATCH_COMPLETED: '批次完成',
      };
      return labels[status] || status || '-';
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
      document.getElementById('batch_medication_progress').textContent = `装药 ${summary.medication_loaded_count || 0}/${summary.medication_total_count || 0}，交付 ${summary.medication_dispensed_count || 0}/${summary.medication_total_count || 0}`;
      renderBatchRoute(data);
      renderBatchStops(data);
      renderBatchAudit(data.audit_records || []);
      renderDeliveryReport();
    }

    function renderBatchRoute(batch) {
      const route = batch.route || [];
      const activeStopIndex = Number(batch.active_stop_index ?? -1);
      const activeStation = activeStopIndex >= 0 && batch.stops?.[activeStopIndex] ? batch.stops[activeStopIndex].target_station : batch.current_station;
      document.getElementById('batch_route_steps').innerHTML = route.map(station => {
        const active = station === activeStation || (batch.route_status === 'RETURNING_TO_PHARMACY' && station === 'pharmacy');
        return `<span class="route-step ${active ? 'active' : ''}">${escapeHtml(stationDisplayName(station))}</span>`;
      }).join('');
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

    function renderBatchPatient(patient) {
      const medications = patient.medications || [];
      const done = medications.filter(item => item.dispensed || item.returned || item.exception).length;
      const medicationHtml = medications.map(item => renderBatchMedication(item)).join('');
      const hasRetryableException = medications.some(item => item.exception && !item.dispensed && !item.returned);
      const hasReviewableIssue = medications.some(item => item.exception || item.returned);
      const retryButtons = hasRetryableException ? `
          <button class="secondary small-button" type="button" onclick="retryBatchPatientException('${escapeHtml(patient.patient_id || '')}')">稍后重试</button>
          <button class="secondary small-button" type="button" onclick="clearBatchPatientException('${escapeHtml(patient.patient_id || '')}')">解除异常</button>` : '';
      const reviewButton = hasReviewableIssue ? `<button class="secondary small-button" type="button" onclick="reviewBatchPatientException('${escapeHtml(patient.patient_id || '')}')">人工复核</button>` : '';
      return `<div class="batch-patient">
        <div class="batch-patient-head">
          <span>${escapeHtml(patient.bed_no || '-')} ${escapeHtml(patient.patient_name || '-')}</span>
          <span class="batch-status ${done >= medications.length && medications.length ? 'ok' : 'warn'}">${done}/${medications.length}</span>
        </div>
        <div class="actions" style="margin-top: 8px;">
          <button class="secondary small-button" type="button" onclick="markBatchPatientAbsent('${escapeHtml(patient.patient_id || '')}')">病人不在</button>
          ${retryButtons}
          ${reviewButton}
        </div>
        ${medicationHtml}
      </div>`;
    }

    function renderBatchMedication(item) {
      const hasException = Boolean(item.exception);
      const returned = Boolean(item.returned);
      const reviewed = Boolean(item.manual_reviewed);
      const className = item.dispensed ? 'batch-med dispensed' : (returned || hasException ? 'batch-med loaded' : (item.loaded ? 'batch-med loaded' : 'batch-med'));
      const stateText = item.dispensed ? '已交付' : (returned ? (reviewed ? '已回收/已复核' : '已回收') : (hasException ? (reviewed ? '异常已复核' : '异常') : (item.loaded ? '已装药' : '待装药')));
      const stateClass = item.dispensed ? 'ok' : (hasException ? 'warn' : (item.loaded ? 'info' : 'warn'));
      const exceptionText = item.exception ? `<div class="audit-detail">异常：${escapeHtml(item.exception_reason || item.exception || '-')}</div>` : '';
      const returnText = item.returned ? `<div class="audit-detail">回收：${escapeHtml(item.return_reason || '未交付，回药房回收')}</div>` : '';
      const resolvedText = item.exception_resolved_at ? `<div class="audit-detail">异常处理：${escapeHtml(item.exception_resolved_reason || '-')}（${escapeHtml(item.exception_resolved_at)}）</div>` : '';
      const reviewText = reviewed ? `<div class="audit-detail">人工复核：${escapeHtml(item.manual_review_result || '-')}（${escapeHtml(item.manual_reviewed_at || '-')}）</div>` : '';
      const retryButtons = hasException && !item.dispensed && !returned ? `
          <button class="secondary small-button" type="button" onclick="retryBatchMedicationException('${escapeHtml(item.id || '')}')">稍后重试</button>
          <button class="secondary small-button" type="button" onclick="clearBatchMedicationException('${escapeHtml(item.id || '')}')">解除异常</button>` : '';
      const reviewButton = hasException || returned ? `<button class="secondary small-button" type="button" onclick="reviewBatchMedicationException('${escapeHtml(item.id || '')}')">人工复核</button>` : '';
      return `<div class="${className}">
        <div class="batch-med-head">
          <span>${escapeHtml(item.medicine_name || '-')}</span>
          <span class="batch-status ${stateClass}">${stateText}</span>
        </div>
        ${item.task_manager_task_id ? `<div class="audit-detail">任务管理 ID：${escapeHtml(item.task_manager_task_id)}</div>` : ''}
        <div class="audit-detail">产品编码：${escapeHtml(item.product_code || '-')}；追溯编号：${escapeHtml(item.trace_id || '-')}</div>
        <div class="audit-detail">规格：${escapeHtml(item.product_model || '-')}；数量：${escapeHtml(item.quantity || '-')}</div>
        ${exceptionText}
        ${returnText}
        ${resolvedText}
        ${reviewText}
        <div class="actions" style="margin-top: 8px;">
          <button class="secondary small-button" type="button" onclick="markBatchMedicationException('${escapeHtml(item.id || '')}')">药品异常</button>
          <button class="secondary small-button" type="button" onclick="markBatchMedicationReturn('${escapeHtml(item.id || '')}')">未交付回收</button>
          ${retryButtons}
          ${reviewButton}
        </div>
      </div>`;
    }

    function renderBatchAudit(records) {
      const container = document.getElementById('batch_audit_records');
      const latest = [...records].slice(-14).reverse();
      if (!latest.length) {
        container.innerHTML = '<div class="audit-item"><div class="audit-detail">暂无批次审计记录</div></div>';
        return;
      }
      container.innerHTML = latest.map(record => {
        const ok = record.result !== 'fail';
        return `<div class="audit-item">
          <div class="audit-head">
            <span>${escapeHtml(record.time || '-')} ${escapeHtml(record.event || '-')}</span>
            <span class="${ok ? 'audit-pass' : 'audit-fail'}">${ok ? '通过' : '失败'}</span>
          </div>
          <div class="audit-detail">${escapeHtml(record.message || '-')}</div>
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
        return { key: 'returned', text: row.manual_reviewed ? '已回收/已复核' : '已回收', className: 'warn' };
      }
      if (row.exception) {
        return { key: 'exception', text: row.manual_reviewed ? '异常已复核' : '异常', className: 'warn' };
      }
      if (row.loaded) {
        return { key: 'loaded', text: '已装药未交付', className: 'info' };
      }
      return { key: 'pending', text: '待装药', className: 'warn' };
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

    function renderDeliveryReport() {
      const batch = latestDeliveryBatch || {};
      const rows = buildReportRowsFromBatch(batch);
      latestReportRows = rows;
      latestReportGeneratedAt = new Date().toLocaleString();
      updateReportWardFilter(rows);
      const filtered = applyReportFilters(rows);
      latestReportFilteredRows = filtered;
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
      document.getElementById('report_filter_result').textContent = `当前显示 ${filtered.length}/${rows.length} 条药品明细。`;
      renderReportRows(filtered);
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
          <td><span class="batch-status ${status.className}">${escapeHtml(status.text)}</span><br><span class="audit-detail">${escapeHtml(row.dispensed_at || row.loaded_at || '-')}</span></td>
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
      const rowHtml = rows.map(row => {
        const status = reportStatus(row);
        const issue = [
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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=Noto+Sans+SC:wght@400;500;700&display=swap">
<style>
  :root { --ink: #0a0c0e; --rule: #0a0c0e; --dim: #5a6068; --paper: #ffffff;
          --fs: "IBM Plex Sans","Noto Sans SC","Microsoft YaHei",sans-serif;
          --fm: "IBM Plex Mono",ui-monospace,Consolas,monospace; }
  * { box-sizing: border-box; }
  body { font-family: var(--fs); color: var(--ink); margin: 22mm 18mm; background: var(--paper); font-size: 11px; line-height: 1.5; }
  .doc-head { border-bottom: 2px solid var(--ink); padding-bottom: 10px; margin-bottom: 14px; }
  .doc-head .eyebrow { font-family: var(--fm); font-size: 9px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--dim); }
  h1 { font-family: var(--fm); font-size: 20px; font-weight: 600; letter-spacing: 0.02em; margin: 4px 0 0; }
  .meta { display: flex; gap: 32px; margin-top: 10px; font-family: var(--fm); font-size: 11px; }
  .meta span { color: var(--dim); font-size: 9px; letter-spacing: 0.12em; text-transform: uppercase; display: block; margin-bottom: 2px; }
  .summary { display: grid; grid-template-columns: repeat(5, 1fr); gap: 0; margin: 16px 0 18px; border-top: 1px solid var(--ink); border-bottom: 1px solid var(--ink); }
  .summary div { padding: 10px 12px; border-right: 1px solid var(--ink); }
  .summary div:last-child { border-right: 0; }
  .summary span { display: block; color: var(--dim); font-family: var(--fm); font-size: 9px; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 6px; }
  .summary strong { display: block; font-family: var(--fm); font-size: 20px; font-weight: 500; }
  table { width: 100%; border-collapse: collapse; font-size: 10px; font-family: var(--fm); }
  thead th { border-top: 1px solid var(--ink); border-bottom: 1px solid var(--ink); padding: 8px; text-align: left; font-size: 9px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--dim); background: var(--paper); font-weight: 600; }
  tbody td { border-bottom: 1px solid var(--dim); padding: 7px 8px; text-align: left; vertical-align: top; }
  .doc-foot { margin-top: 18px; padding-top: 8px; border-top: 1px solid var(--ink); font-family: var(--fm); font-size: 9px; color: var(--dim); letter-spacing: 0.04em; }
  @media print { body { margin: 12mm; } @page { margin: 12mm; } }
</style></head><body>
<div class="doc-head">
  <div class="eyebrow">// Medication Delivery · Audit Report</div>
  <h1>智能送药配送报告</h1>
  <div class="meta">
    <div><span>批次号 Batch</span>${escapeHtml(summary.batchId)}</div>
    <div><span>生成时间 Generated</span>${escapeHtml(summary.generatedAt)}</div>
  </div>
</div>
<div class="summary">
  <div><span>全部明细 Total</span><strong>${summary.total}</strong></div>
  <div><span>当前筛选 Filtered</span><strong>${summary.filtered}</strong></div>
  <div><span>已交付 Dispensed</span><strong>${summary.dispensed}</strong></div>
  <div><span>异常/回收 Issues</span><strong>${summary.issues}</strong></div>
  <div><span>人工复核 Reviewed</span><strong>${summary.reviewed}</strong></div>
</div>
<table><thead><tr><th>病房/床号</th><th>病人</th><th>药品</th><th>编码/追溯</th><th>状态</th><th>异常/回收/复核</th></tr></thead><tbody>${rowHtml || '<tr><td colspan="6">暂无报告数据</td></tr>'}</tbody></table>
<div class="doc-foot">— 文件结束 / END OF DOCUMENT —</div>
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
      return {
        batch_id: `REAL-${new Date().toISOString().slice(0, 10).replaceAll('-', '')}-001`,
        source_station: 'pharmacy',
        operator_id: 'operator_001',
        patients: [
          {
            patient_id: 'real_patient_001',
            patient_name: '患者姓名',
            ward_id: 'ward_a',
            ward_name: 'A病房',
            bed_no: 'A-01',
            target_station: 'ward_a',
            medications: [
              {
                medicine_name: '药品名称',
                product_code: '产品编码',
                product_model: '规格型号',
                quantity: '1',
                trace_id: '追溯编号',
                order_no: '医嘱/订单号',
                dose: '1盒',
                usage: '按医嘱',
              },
            ],
          },
        ],
      };
    }

    function setBatchImportMessage(message, ok = true) {
      const element = document.getElementById('batch_import_result');
      element.textContent = message;
      element.style.color = ok ? 'var(--ok)' : 'var(--danger)';
    }

    async function refreshDeliveryBatch() {
      try {
        updateDeliveryBatch(await api('/api/delivery_batch'));
      } catch (error) {
        log(`批次状态刷新失败：${error.message}`);
      }
    }

    async function postBatchAction(path, successPrefix, options = {}) {
      await refreshDrugInfo();
      const payload = {};
      if (options.requireScan) {
        Object.assign(payload, currentScannedKey({ requireFresh: true }));
      }
      const data = await api(path, { method: 'POST', body: JSON.stringify(payload) });
      updateDeliveryBatch(data.batch || data);
      const message = data.message || '批次状态已更新';
      const resultElement = document.getElementById('batch_action_result');
      resultElement.textContent = `${successPrefix}：${message}`;
      resultElement.style.color = data.ok === false ? 'var(--danger)' : 'var(--ok)';
      log(`${successPrefix}：${message}`);
    }

    async function postBatchException(payload, successPrefix) {
      const data = await api('/api/delivery_batch/exception', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      updateDeliveryBatch(data.batch || data);
      const message = data.message || '异常状态已更新';
      const resultElement = document.getElementById('batch_action_result');
      resultElement.textContent = `${successPrefix}：${message}`;
      resultElement.style.color = data.ok === false ? 'var(--danger)' : 'var(--ok)';
      log(`${successPrefix}：${message}`);
    }

    async function markBatchPatientAbsent(patientId) {
      try {
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
        await postBatchException({
          action: 'clear_exception',
          patient_id: patientId,
          reason: '异常解除，重新进入交付流程',
        }, '解除异常');
      } catch (error) {
        log(`解除病人异常失败：${error.message}`);
      }
    }

    async function reviewBatchPatientException(patientId) {
      try {
        await postBatchException({
          action: 'manual_review',
          patient_id: patientId,
          reason: '人工复核确认已处理',
        }, '人工复核');
      } catch (error) {
        log(`病人人工复核失败：${error.message}`);
      }
    }

    async function retryBatchMedicationException(medicationId) {
      try {
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
        await postBatchException({
          action: 'clear_exception',
          medication_id: medicationId,
          reason: '异常解除，重新进入交付流程',
        }, '解除异常');
      } catch (error) {
        log(`解除药品异常失败：${error.message}`);
      }
    }

    async function reviewBatchMedicationException(medicationId) {
      try {
        await postBatchException({
          action: 'manual_review',
          medication_id: medicationId,
          reason: '人工复核确认已处理',
        }, '人工复核');
      } catch (error) {
        log(`药品人工复核失败：${error.message}`);
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
      const scan = currentScannedKey({ requireFresh: true });
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

    function getRecognizedMedicineName(data) {
      if (data.label_product_model) {
        return data.label_product_model;
      }
      if (data.drug_type && data.drug_type !== 'unknown' && data.drug_name) {
        return data.drug_name;
      }
      if (data.label_product_code) {
        return data.label_product_code;
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
      return {
        product_code: data.label_product_code || data.raw_code_text || data.code_text || '',
        product_model: data.label_product_model || '',
        quantity: data.label_quantity || '',
        trace_id: data.label_trace_id || '',
        order_no: data.label_order_no || '',
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

    function currentScannedKey(options = {}) {
      const fields = getTaskRecognitionFields();
      const scan = {
        product_code: fields.product_code || '',
        trace_id: fields.trace_id || '',
      };
      const age = getScanAgeSec();
      const hasCode = Boolean(scan.product_code || scan.trace_id);
      if (options.requireFresh && !hasCode) {
        throw new Error('当前没有可用扫码结果，请将药品标签放到摄像头前重新扫描。');
      }
      if (options.requireFresh && age !== null && age > SCAN_MAX_AGE_SEC) {
        throw new Error(`当前扫码结果已超过 ${Math.round(age)} 秒，请重新扫描标签后再确认。`);
      }
      return scan;
    }

    function medicationMatchesScan(item, scan) {
      const expectedProductCode = item.product_code || '';
      const expectedTraceId = item.trace_id || '';
      const productOk = !expectedProductCode || scan.product_code === expectedProductCode;
      const traceOk = !expectedTraceId || scan.trace_id === expectedTraceId;
      return Boolean(expectedProductCode || expectedTraceId) && productOk && traceOk;
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
        renderPatientOrder();
        document.getElementById('patient_match_result').textContent = `当前扫码 ${scan.product_code || '-'} / ${scan.trace_id || '-'} 不属于 ${selectedPatientOrder.patient_name} 的用药清单。`;
        document.getElementById('patient_match_result').style.color = 'var(--danger)';
        log('患者用药核对失败：当前扫码不属于该患者');
        return null;
      }
      renderPatientOrder(match.id || '');
      document.getElementById('patient_match_result').textContent = `核对通过：${match.medicine_name} 属于 ${selectedPatientOrder.patient_name} 的用药清单。`;
      document.getElementById('patient_match_result').style.color = 'var(--ok)';
      log(`患者用药核对通过：${match.medicine_name}`);
      return match;
    }

    function buildPatientTaskPayload() {
      const order = selectedPatientOrder || getSelectedPatientOrder();
      const medications = (order?.medications || []).map(normalizeMedicationForTask);
      const primary = medications[0] || {};
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

    function updateTaskRecognitionPanel(data) {
      document.getElementById('task_product_code').textContent = data.label_product_code || '-';
      document.getElementById('task_product_model').textContent = data.label_product_model || '-';
      document.getElementById('task_quantity').textContent = data.label_quantity || '-';
      document.getElementById('task_trace_id').textContent = data.label_trace_id || '-';
      document.getElementById('task_order_no').textContent = data.label_order_no || '-';
      document.getElementById('task_medicine_preview').textContent = getTaskMedicineName();
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
      const confidence = Math.round((data.confidence || 0) * 100);
      const loaded = Boolean(data.loaded);
      const loadedElement = document.getElementById('drug_loaded');
      document.getElementById('drug_id').textContent = data.drug_id || '-';
      document.getElementById('drug_name').textContent = data.drug_name || '-';
      document.getElementById('drug_type').textContent = data.drug_type || '-';
      document.getElementById('drug_confidence').textContent = data.drug_name ? `${confidence}%` : '-';
      loadedElement.textContent = data.drug_name ? (loaded ? '已装药' : '未装药') : '-';
      loadedElement.className = loaded ? 'drug-loaded' : 'drug-empty';
      document.getElementById('drug_source').textContent = data.source || '-';
      document.getElementById('code_text').textContent = data.raw_code_text || data.code_text || '-';
      document.getElementById('code_type').textContent = data.code_type || '-';
      document.getElementById('code_method').textContent = data.code_method || '-';
      document.getElementById('ocr_text').textContent = data.ocr_text || '-';
      document.getElementById('ocr_confidence').textContent = data.ocr_text ? `${Math.round((data.ocr_confidence || 0) * 100)}%` : '-';
      document.getElementById('ocr_backend').textContent = data.ocr_backend || (data.ocr_available ? 'available' : '-');
      document.getElementById('ocr_status').textContent = data.ocr_enabled ? (data.ocr_error || `已启用 ${data.ocr_language || ''}`) : '未启用';
      document.getElementById('label_order_no').textContent = data.label_order_no || '-';
      document.getElementById('label_product_code').textContent = data.label_product_code || '-';
      document.getElementById('label_product_model').textContent = data.label_product_model || '-';
      document.getElementById('label_quantity').textContent = data.label_quantity || '-';
      document.getElementById('label_trace_id').textContent = data.label_trace_id || '-';
      document.getElementById('drug_stamp').textContent = data.stamp ? new Date(data.stamp * 1000).toLocaleString() : '-';
      updateTaskRecognitionPanel(data);
      applyRecognizedToTask(false);
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

    async function refreshChassisStatus() {
      try {
        updateChassisStatus(await api('/api/chassis_status'));
      } catch (error) {
        updateChassisStatus({ received: false, message: `底盘状态刷新失败：${error.message}` });
      }
    }

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
    document.getElementById('reset-batch').addEventListener('click', async () => {
      try {
        const data = await api('/api/delivery_batch/reset', { method: 'POST', body: JSON.stringify({}) });
        updateDeliveryBatch(data);
        document.getElementById('batch_action_result').textContent = '已重建演示配送批次。';
        document.getElementById('batch_action_result').style.color = 'var(--ok)';
        log('已重建演示配送批次');
      } catch (error) {
        log(`重建批次失败：${error.message}`);
      }
    });
    document.getElementById('batch-load-scan').addEventListener('click', async () => {
      try {
        await postBatchAction('/api/delivery_batch/load_scan', '批次装药扫码', { requireScan: true });
      } catch (error) {
        log(`批次装药扫码失败：${error.message}`);
      }
    });
    document.getElementById('batch-advance').addEventListener('click', async () => {
      try {
        await postBatchAction('/api/delivery_batch/advance', '批次推进');
      } catch (error) {
        log(`批次推进失败：${error.message}`);
      }
    });
    document.getElementById('batch-dispense-scan').addEventListener('click', async () => {
      try {
        await postBatchAction('/api/delivery_batch/dispense_scan', '病房交付扫码', { requireScan: true });
      } catch (error) {
        log(`病房交付扫码失败：${error.message}`);
      }
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
      setBatchImportMessage('已填入真实批次导入模板。');
    });
    document.getElementById('load-current-batch-json').addEventListener('click', () => {
      document.getElementById('batch_import_text').value = JSON.stringify(latestDeliveryBatch || {}, null, 2);
      setBatchImportMessage('已载入当前批次 JSON，可编辑后重新应用。');
    });
    document.getElementById('import-batch-json').addEventListener('click', async () => {
      try {
        const text = document.getElementById('batch_import_text').value.trim();
        if (!text) {
          setBatchImportMessage('请先填写或载入批次 JSON。', false);
          return;
        }
        const payload = JSON.parse(text);
        const data = await api('/api/delivery_batch/import', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
        updateDeliveryBatch(data.batch || data);
        setBatchImportMessage(data.message || '真实批次已应用。');
        document.getElementById('batch_action_result').textContent = data.message || '真实批次已应用。';
        document.getElementById('batch_action_result').style.color = 'var(--ok)';
        log(data.message || '真实批次已应用');
      } catch (error) {
        setBatchImportMessage(`导入失败：${error.message}`, false);
        log(`导入真实批次失败：${error.message}`);
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
      await refreshChassisStatus();
    }).catch(error => log(`初始化失败：${error.message}`));
    setInterval(refreshDeliveryBatch, 1500);
    setInterval(refreshState, 1000);
    setInterval(refreshDrugInfo, 1000);
    setInterval(refreshChassisStatus, 1000);
  </script>
</body>
</html>
"""


class MedicineWebDashboard(Node):
    def __init__(self):
        super().__init__("medicine_web_dashboard")
        default_stations_file = (
            get_package_share_directory("medicine_task_manager")
            + "/config/stations.yaml"
        )
        self.declare_parameter("host", "0.0.0.0")
        self.declare_parameter("port", 8080)
        self.declare_parameter("stations_file", default_stations_file)
        self.declare_parameter("service_timeout_sec", 5.0)
        self.declare_parameter("chassis_status_topic", "/medicine/chassis_status")
        self.declare_parameter(
            "delivery_batch_state_file",
            os.path.expanduser(
                "~/.local/share/medicine_robot/delivery_batch_state.json"
            ),
        )

        self.host = self.get_parameter("host").get_parameter_value().string_value
        self.port = self.get_parameter("port").get_parameter_value().integer_value
        self.stations_file = (
            self.get_parameter("stations_file").get_parameter_value().string_value
        )
        self.service_timeout_sec = (
            self.get_parameter("service_timeout_sec").get_parameter_value().double_value
        )
        self.chassis_status_topic = (
            self.get_parameter("chassis_status_topic")
            .get_parameter_value()
            .string_value
        )
        self.delivery_batch_state_file = (
            self.get_parameter("delivery_batch_state_file")
            .get_parameter_value()
            .string_value
        )
        self.state_lock = threading.Lock()
        self.drug_info_lock = threading.Lock()
        self.chassis_status_lock = threading.Lock()
        self.latest_state = self.empty_state()
        self.latest_drug_info = self.empty_drug_info()
        self.latest_recognition_status = {}
        self.latest_chassis_status = self.empty_chassis_status()
        self.stations = self.load_stations(self.stations_file)
        self.delivery_batch_lock = threading.Lock()
        self.delivery_batch = self.load_delivery_batch_state()
        self.create_task_client = self.create_client(
            CreateDeliveryTask, "/medicine/create_delivery_task"
        )
        self.cancel_task_client = self.create_client(
            CancelDeliveryTask, "/medicine/cancel_delivery_task"
        )
        self.verify_task_client = self.create_client(
            VerifyDeliveryTask, "/medicine/verify_delivery_task"
        )
        self.create_subscription(
            DeliveryState, "/medicine/delivery_state", self.on_delivery_state, 10
        )
        self.create_subscription(DrugInfo, "/medicine/drug_info", self.on_drug_info, 10)
        self.create_subscription(
            String,
            "/medicine/drug_recognition_status",
            self.on_drug_recognition_status,
            10,
        )
        self.create_subscription(
            String, self.chassis_status_topic, self.on_chassis_status, 10
        )
        self.server = None
        self.server_thread = None

    def empty_state(self):
        return {
            "task_id": "",
            "state": "IDLE",
            "message": "等待送药任务",
            "current_station": "pharmacy",
            "target_station": "",
            "medicine_name": "",
            "patient_id": "",
            "patient_name": "",
            "ward_id": "",
            "bed_no": "",
            "product_code": "",
            "product_model": "",
            "quantity": "",
            "trace_id": "",
            "order_no": "",
            "medications_json": "[]",
            "medication_total_count": 0,
            "medication_loaded_count": 0,
            "medication_dispensed_count": 0,
            "load_confirmed": False,
            "load_confirmed_at": "",
            "dispense_confirmed": False,
            "dispense_confirmed_at": "",
            "last_verification_stage": "",
            "last_verification_passed": False,
            "last_verification_message": "",
            "verification_records": [],
            "progress": 0.0,
            "stamp": 0.0,
        }

    def empty_drug_info(self):
        return {
            "drug_id": "",
            "drug_name": "",
            "drug_type": "",
            "confidence": 0.0,
            "loaded": False,
            "source": "",
            "stamp": 0.0,
            "raw_code_text": "",
            "code_text": "",
            "code_type": "",
            "code_method": "",
            "ocr_enabled": False,
            "ocr_available": False,
            "ocr_text": "",
            "ocr_confidence": 0.0,
            "ocr_language": "",
            "ocr_backend": "",
            "ocr_error": "",
            "label_order_no": "",
            "label_product_code": "",
            "label_product_model": "",
            "label_quantity": "",
            "label_trace_id": "",
        }

    def empty_chassis_status(self):
        return {
            "ok": False,
            "received": False,
            "message": "no chassis status received",
            "topic": self.chassis_status_topic,
            "web_received_at": 0.0,
        }

    def load_stations(self, stations_file):
        with open(stations_file, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
        stations = []
        for station_id, value in sorted((data.get("stations") or {}).items()):
            stations.append(
                {
                    "id": station_id,
                    "name": value.get("name", station_id),
                    "x": float(value.get("x", 0.0)),
                    "y": float(value.get("y", 0.0)),
                    "yaw": float(value.get("yaw", 0.0)),
                }
            )
        return stations

    def create_demo_delivery_batch(self):
        route = ["ward_a", "ward_b", "ward_c"]
        station_names = {station["id"]: station["name"] for station in self.stations}
        stops = []
        for index, station_id in enumerate(route):
            patients = []
            for order in PATIENT_MEDICATION_ORDERS:
                if order.get("target_station") != station_id:
                    continue
                patient = copy.deepcopy(order)
                patient["patient_status"] = "WAITING_LOAD_CONFIRMATION"
                for medication in patient.get("medications", []):
                    medication["loaded"] = False
                    medication["loaded_at"] = ""
                    medication["dispensed"] = False
                    medication["dispensed_at"] = ""
                    medication["returned"] = False
                    medication["returned_at"] = ""
                    medication["return_reason"] = ""
                    medication["exception"] = ""
                    medication["exception_at"] = ""
                    medication["exception_reason"] = ""
                    medication["exception_resolved_at"] = ""
                    medication["exception_resolved_reason"] = ""
                    medication["exception_resolution_action"] = ""
                    medication["manual_reviewed"] = False
                    medication["manual_reviewed_at"] = ""
                    medication["manual_review_result"] = ""
                patients.append(patient)
            stops.append(
                {
                    "stop_id": f"stop_{station_id}",
                    "target_station": station_id,
                    "display_name": station_names.get(station_id, station_id),
                    "sequence_index": index + 1,
                    "stop_status": "WAITING_LOAD_CONFIRMATION",
                    "arrived_time": "",
                    "completed_time": "",
                    "patients": patients,
                }
            )
        now = self.now_text()
        batch = {
            "batch_id": f"BATCH-{time.strftime('%Y%m%d-%H%M%S', time.localtime())}",
            "source_station": "pharmacy",
            "route": ["pharmacy"] + route + ["pharmacy"],
            "route_status": "WAITING_LOAD_CONFIRMATION",
            "current_station": "pharmacy",
            "active_stop_index": -1,
            "active_stop_id": "",
            "created_time": now,
            "started_time": "",
            "finished_time": "",
            "operator_id": "demo_operator",
            "audit_records": [
                {
                    "time": now,
                    "event": "batch_created",
                    "message": "演示配送批次已创建",
                    "result": "ok",
                }
            ],
            "stops": stops,
        }
        self.update_batch_summary(batch)
        return batch

    def load_delivery_batch_state(self):
        try:
            with open(self.delivery_batch_state_file, "r", encoding="utf-8") as file:
                batch = json.load(file)
            if not isinstance(batch, dict) or "stops" not in batch:
                raise ValueError("invalid delivery batch state")
            self.update_batch_summary(batch)
            return batch
        except (FileNotFoundError, json.JSONDecodeError, ValueError, OSError):
            batch = self.create_demo_delivery_batch()
            self.save_delivery_batch_state_locked(batch)
            return batch

    def save_delivery_batch_state_locked(self, batch):
        directory = os.path.dirname(self.delivery_batch_state_file)
        if directory:
            os.makedirs(directory, exist_ok=True)
        temp_file = f"{self.delivery_batch_state_file}.tmp"
        with open(temp_file, "w", encoding="utf-8") as file:
            json.dump(batch, file, ensure_ascii=False, indent=2)
        os.replace(temp_file, self.delivery_batch_state_file)

    def now_text(self):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    def update_batch_summary(self, batch):
        total_patients = 0
        completed_patients = 0
        total_medications = 0
        loaded_medications = 0
        dispensed_medications = 0
        returned_medications = 0
        exception_medications = 0
        done_medications = 0
        completed_stops = 0
        for stop in batch.get("stops", []):
            stop_total = 0
            stop_loaded = 0
            stop_dispensed = 0
            stop_returned = 0
            stop_exception = 0
            stop_done = 0
            stop_patient_done = 0
            patients = stop.get("patients", [])
            total_patients += len(patients)
            for patient in patients:
                patient_medications = patient.get("medications", [])
                patient_total = len(patient_medications)
                patient_loaded = sum(
                    1 for item in patient_medications if item.get("loaded")
                )
                patient_dispensed = sum(
                    1 for item in patient_medications if item.get("dispensed")
                )
                patient_returned = sum(
                    1 for item in patient_medications if item.get("returned")
                )
                patient_exception = sum(
                    1 for item in patient_medications if item.get("exception")
                )
                patient_done = sum(
                    1
                    for item in patient_medications
                    if item.get("dispensed")
                    or item.get("returned")
                    or item.get("exception")
                )
                stop_total += patient_total
                stop_loaded += patient_loaded
                stop_dispensed += patient_dispensed
                stop_returned += patient_returned
                stop_exception += patient_exception
                stop_done += patient_done
                total_medications += patient_total
                loaded_medications += patient_loaded
                dispensed_medications += patient_dispensed
                returned_medications += patient_returned
                exception_medications += patient_exception
                done_medications += patient_done
                if patient_total and patient_done >= patient_total:
                    patient["patient_status"] = "COMPLETED"
                    completed_patients += 1
                    stop_patient_done += 1
                elif patient_loaded:
                    patient["patient_status"] = "LOADED"
                else:
                    patient["patient_status"] = "WAITING_LOAD_CONFIRMATION"
            stop["medication_total_count"] = stop_total
            stop["medication_loaded_count"] = stop_loaded
            stop["medication_dispensed_count"] = stop_dispensed
            stop["medication_returned_count"] = stop_returned
            stop["medication_exception_count"] = stop_exception
            stop["medication_done_count"] = stop_done
            if stop_total and stop["medication_done_count"] >= stop_total:
                if stop.get("stop_status") not in {
                    "WAITING_LOAD_CONFIRMATION",
                    "NAVIGATING_TO_WARD",
                }:
                    stop["stop_status"] = "COMPLETED"
                completed_stops += 1
            elif stop_loaded >= stop_total and stop_total:
                if stop.get("stop_status") == "WAITING_LOAD_CONFIRMATION":
                    stop["stop_status"] = "READY_TO_DEPART"
            if patients and stop_patient_done >= len(patients):
                completed_stops += 0
        all_loaded = total_medications > 0 and loaded_medications >= total_medications
        all_dispensed = (
            total_medications > 0 and dispensed_medications >= total_medications
        )
        batch["summary"] = {
            "stop_total_count": len(batch.get("stops", [])),
            "stop_completed_count": sum(
                1
                for stop in batch.get("stops", [])
                if stop.get("stop_status") == "COMPLETED"
            ),
            "patient_total_count": total_patients,
            "patient_completed_count": completed_patients,
            "medication_total_count": total_medications,
            "medication_loaded_count": loaded_medications,
            "medication_dispensed_count": dispensed_medications,
            "medication_returned_count": returned_medications,
            "medication_exception_count": exception_medications,
            "medication_done_count": done_medications,
            "all_loaded": all_loaded,
            "all_dispensed": all_dispensed,
        }
        if all_loaded and batch.get("route_status") == "WAITING_LOAD_CONFIRMATION":
            batch["route_status"] = "READY_TO_DEPART"

    def append_batch_audit(self, batch, event, message, result="ok", extra=None):
        record = {
            "time": self.now_text(),
            "event": event,
            "message": message,
            "result": result,
        }
        if isinstance(extra, dict):
            record.update(extra)
        batch.setdefault("audit_records", []).append(record)
        del batch["audit_records"][:-80]

    def get_delivery_batch(self):
        with self.delivery_batch_lock:
            self.update_batch_summary(self.delivery_batch)
            return copy.deepcopy(self.delivery_batch)

    def reset_delivery_batch(self):
        with self.delivery_batch_lock:
            self.delivery_batch = self.create_demo_delivery_batch()
            return copy.deepcopy(self.delivery_batch)

    def text_value(self, value, default=""):
        text = str(value if value is not None else "").strip()
        return text or default

    def clean_identifier(self, value, default):
        text = self.text_value(value, default)
        cleaned = "".join(
            char if char.isalnum() or char in {"_", "-"} else "_" for char in text
        )
        return cleaned or default

    def normalize_batch_medication(self, medication, patient_id, index):
        if not isinstance(medication, dict):
            raise ValueError("药品条目必须是对象")
        medication_id = self.clean_identifier(
            medication.get("id") or medication.get("medication_id"),
            f"{patient_id}_med_{index + 1:03d}",
        )
        return {
            "id": medication_id,
            "medicine_name": self.text_value(
                medication.get("medicine_name") or medication.get("name"), "未命名药品"
            ),
            "product_code": self.text_value(medication.get("product_code")),
            "product_model": self.text_value(medication.get("product_model")),
            "quantity": self.text_value(medication.get("quantity"), "1"),
            "trace_id": self.text_value(medication.get("trace_id")),
            "order_no": self.text_value(medication.get("order_no")),
            "dose": self.text_value(medication.get("dose")),
            "usage": self.text_value(medication.get("usage")),
            "loaded": False,
            "loaded_at": "",
            "dispensed": False,
            "dispensed_at": "",
            "returned": False,
            "returned_at": "",
            "return_reason": "",
            "exception": "",
            "exception_at": "",
            "exception_reason": "",
            "exception_resolved_at": "",
            "exception_resolved_reason": "",
            "exception_resolution_action": "",
            "manual_reviewed": False,
            "manual_reviewed_at": "",
            "manual_review_result": "",
            "task_manager_task_id": self.text_value(
                medication.get("task_manager_task_id")
            ),
        }

    def normalize_batch_patient(self, patient, index, default_station=""):
        if not isinstance(patient, dict):
            raise ValueError("病人条目必须是对象")
        patient_id = self.clean_identifier(
            patient.get("patient_id") or patient.get("id"),
            f"patient_{index + 1:03d}",
        )
        target_station = self.text_value(
            patient.get("target_station") or patient.get("ward_id") or default_station,
            default_station or "ward_a",
        )
        medications = patient.get("medications") or patient.get("items") or []
        if not isinstance(medications, list) or not medications:
            raise ValueError(f"病人 {patient_id} 至少需要 1 项药品")
        normalized = {
            "patient_id": patient_id,
            "patient_name": self.text_value(
                patient.get("patient_name") or patient.get("name"), "未命名患者"
            ),
            "ward_id": self.text_value(patient.get("ward_id"), target_station),
            "ward_name": self.text_value(patient.get("ward_name"), target_station),
            "bed_no": self.text_value(patient.get("bed_no")),
            "target_station": target_station,
            "medications": [
                self.normalize_batch_medication(item, patient_id, medication_index)
                for medication_index, item in enumerate(medications)
            ],
            "patient_status": "WAITING_LOAD_CONFIRMATION",
        }
        return normalized

    def create_delivery_batch_from_payload(self, payload):
        if not isinstance(payload, dict):
            raise ValueError("批次 JSON 必须是对象")
        now = self.now_text()
        source_station = self.text_value(payload.get("source_station"), "pharmacy")
        station_names = {station["id"]: station["name"] for station in self.stations}
        stops = []
        route_stations = []
        source_stops = payload.get("stops")
        if isinstance(source_stops, list) and source_stops:
            patient_index = 0
            for stop_index, source_stop in enumerate(source_stops):
                if not isinstance(source_stop, dict):
                    raise ValueError("病房站点条目必须是对象")
                station_id = self.text_value(
                    source_stop.get("target_station")
                    or source_stop.get("station_id")
                    or source_stop.get("ward_id"),
                    f"ward_{stop_index + 1}",
                )
                source_patients = source_stop.get("patients") or []
                if not isinstance(source_patients, list):
                    raise ValueError(f"站点 {station_id} 的 patients 必须是数组")
                patients = []
                for patient in source_patients:
                    patients.append(
                        self.normalize_batch_patient(patient, patient_index, station_id)
                    )
                    patient_index += 1
                route_stations.append(station_id)
                stops.append(
                    {
                        "stop_id": self.clean_identifier(
                            source_stop.get("stop_id"), f"stop_{station_id}"
                        ),
                        "target_station": station_id,
                        "display_name": self.text_value(
                            source_stop.get("display_name")
                            or source_stop.get("ward_name"),
                            station_names.get(station_id, station_id),
                        ),
                        "sequence_index": stop_index + 1,
                        "stop_status": "WAITING_LOAD_CONFIRMATION",
                        "arrived_time": "",
                        "completed_time": "",
                        "patients": patients,
                    }
                )
        else:
            source_patients = payload.get("patients") or payload.get("orders") or []
            if not isinstance(source_patients, list) or not source_patients:
                raise ValueError("批次 JSON 需要包含 patients 数组或 stops 数组")
            grouped = []
            station_index = {}
            for patient_index, patient in enumerate(source_patients):
                normalized_patient = self.normalize_batch_patient(
                    patient, patient_index
                )
                station_id = normalized_patient.get("target_station", "ward_a")
                if station_id not in station_index:
                    station_index[station_id] = len(grouped)
                    grouped.append({"station_id": station_id, "patients": []})
                grouped[station_index[station_id]]["patients"].append(
                    normalized_patient
                )
            route_payload = payload.get("route") or []
            if isinstance(route_payload, list):
                for station_id in route_payload:
                    station_id = self.text_value(station_id)
                    if (
                        station_id
                        and station_id != source_station
                        and station_id not in route_stations
                    ):
                        route_stations.append(station_id)
            for group in grouped:
                if group["station_id"] not in route_stations:
                    route_stations.append(group["station_id"])
            for stop_index, station_id in enumerate(route_stations):
                group = next(
                    (item for item in grouped if item["station_id"] == station_id),
                    {"patients": []},
                )
                stops.append(
                    {
                        "stop_id": f"stop_{station_id}",
                        "target_station": station_id,
                        "display_name": station_names.get(station_id, station_id),
                        "sequence_index": stop_index + 1,
                        "stop_status": "WAITING_LOAD_CONFIRMATION",
                        "arrived_time": "",
                        "completed_time": "",
                        "patients": group["patients"],
                    }
                )
        medication_count = sum(
            len(patient.get("medications", []))
            for stop in stops
            for patient in stop.get("patients", [])
        )
        if medication_count <= 0:
            raise ValueError("批次至少需要 1 项药品")
        batch = {
            "batch_id": self.text_value(
                payload.get("batch_id"),
                f"REAL-{time.strftime('%Y%m%d-%H%M%S', time.localtime())}",
            ),
            "source_station": source_station,
            "route": [source_station] + route_stations + [source_station],
            "route_status": "WAITING_LOAD_CONFIRMATION",
            "current_station": source_station,
            "active_stop_index": -1,
            "active_stop_id": "",
            "created_time": now,
            "started_time": "",
            "finished_time": "",
            "operator_id": self.text_value(payload.get("operator_id"), "web_operator"),
            "audit_records": [
                {
                    "time": now,
                    "event": "batch_imported",
                    "message": f"真实配送批次已导入：{len(stops)} 个病房，{medication_count} 项药品",
                    "result": "ok",
                }
            ],
            "stops": stops,
        }
        self.update_batch_summary(batch)
        return batch

    def import_delivery_batch(self, payload):
        with self.delivery_batch_lock:
            try:
                self.delivery_batch = self.create_delivery_batch_from_payload(payload)
                return {
                    "ok": True,
                    "message": f"已应用真实批次：{self.delivery_batch.get('batch_id')}",
                    "batch": copy.deepcopy(self.delivery_batch),
                }
            except ValueError as error:
                return {"ok": False, "message": str(error)}

    def build_stop_task_payload(self, batch, stop):
        medications = []
        patient_names = []
        bed_numbers = []
        patient_ids = []
        for patient in stop.get("patients", []):
            patient_id = self.text_value(patient.get("patient_id"))
            patient_name = self.text_value(patient.get("patient_name"))
            bed_no = self.text_value(patient.get("bed_no"))
            if patient_name:
                patient_names.append(patient_name)
            if bed_no:
                bed_numbers.append(bed_no)
            if patient_id:
                patient_ids.append(patient_id)
            for medication in patient.get("medications", []):
                if (
                    medication.get("dispensed")
                    or medication.get("returned")
                    or medication.get("exception")
                ):
                    continue
                medication_payload = {
                    "id": self.text_value(medication.get("id")),
                    "medicine_name": self.text_value(
                        medication.get("medicine_name"), "未命名药品"
                    ),
                    "product_code": self.text_value(medication.get("product_code")),
                    "product_model": self.text_value(medication.get("product_model")),
                    "quantity": self.text_value(medication.get("quantity"), "1"),
                    "trace_id": self.text_value(medication.get("trace_id")),
                    "order_no": self.text_value(medication.get("order_no")),
                    "dose": self.text_value(medication.get("dose")),
                    "usage": self.text_value(medication.get("usage")),
                    "patient_id": patient_id,
                    "patient_name": patient_name,
                    "ward_id": self.text_value(
                        patient.get("ward_id"), stop.get("target_station", "")
                    ),
                    "bed_no": bed_no,
                    "load_confirmed": bool(medication.get("loaded")),
                    "load_confirmed_at": self.text_value(medication.get("loaded_at")),
                    "dispense_confirmed": bool(medication.get("dispensed")),
                    "dispense_confirmed_at": self.text_value(
                        medication.get("dispensed_at")
                    ),
                }
                medications.append(medication_payload)
        if not medications:
            return None
        primary = medications[0]
        return {
            "medicine_name": f"{stop.get('display_name') or stop.get('target_station')}批次药品（{len(medications)}项）",
            "source_station": self.text_value(batch.get("source_station"), "pharmacy"),
            "target_station": self.text_value(stop.get("target_station")),
            "patient_id": ",".join(patient_ids[:8]),
            "patient_name": "、".join(patient_names[:8]),
            "ward_id": self.text_value(stop.get("target_station")),
            "bed_no": "、".join(bed_numbers[:8]),
            "product_code": primary.get("product_code", ""),
            "product_model": primary.get("product_model", ""),
            "quantity": str(len(medications)),
            "trace_id": primary.get("trace_id", ""),
            "order_no": f"{batch.get('batch_id', '')}/{stop.get('stop_id', '')}",
            "medications_json": json.dumps(medications, ensure_ascii=False),
        }

    def create_task_from_payload_locked(self, payload):
        if not self.create_task_client.wait_for_service(
            timeout_sec=self.service_timeout_sec
        ):
            return {"accepted": False, "task_id": "", "message": "创建任务服务不可用"}
        request = CreateDeliveryTask.Request()
        request.medicine_name = str(payload.get("medicine_name") or "常规药品")
        request.source_station = str(payload.get("source_station") or "pharmacy")
        request.target_station = str(payload.get("target_station") or "")
        request.patient_id = str(payload.get("patient_id") or "")
        request.patient_name = str(payload.get("patient_name") or "")
        request.ward_id = str(payload.get("ward_id") or "")
        request.bed_no = str(payload.get("bed_no") or "")
        request.product_code = str(payload.get("product_code") or "")
        request.product_model = str(payload.get("product_model") or "")
        request.quantity = str(payload.get("quantity") or "")
        request.trace_id = str(payload.get("trace_id") or "")
        request.order_no = str(payload.get("order_no") or "")
        request.medications_json = str(payload.get("medications_json") or "")
        future = self.create_task_client.call_async(request)
        response = self.wait_future(future)
        if response is None:
            return {"accepted": False, "task_id": "", "message": "创建任务服务超时"}
        return {
            "accepted": bool(response.accepted),
            "task_id": response.task_id,
            "message": response.message,
        }

    def create_task_manager_stop_task_locked(self, batch, stop):
        payload = self.build_stop_task_payload(batch, stop)
        if payload is None:
            return {
                "accepted": True,
                "task_id": "",
                "message": "当前病房没有需要创建任务的药品",
            }
        response = self.create_task_from_payload_locked(payload)
        if not response.get("accepted"):
            return response
        task_id = response.get("task_id", "")
        now = self.now_text()
        stop["task_manager_task_id"] = task_id
        stop["task_manager_task_created_at"] = now
        stop["task_manager_task_message"] = response.get("message", "")
        for patient in stop.get("patients", []):
            for medication in patient.get("medications", []):
                if (
                    medication.get("dispensed")
                    or medication.get("returned")
                    or medication.get("exception")
                ):
                    continue
                medication["task_manager_task_id"] = task_id
        return response

    def persist_current_delivery_batch(self):
        with self.delivery_batch_lock:
            self.update_batch_summary(self.delivery_batch)
            self.save_delivery_batch_state_locked(self.delivery_batch)

    def current_scan_key(self, payload=None):
        payload = payload or {}
        product_code = str(payload.get("product_code") or "").strip()
        trace_id = str(payload.get("trace_id") or "").strip()
        if product_code or trace_id:
            return product_code, trace_id
        drug_info = self.get_drug_info()
        product_code = str(
            drug_info.get("label_product_code")
            or drug_info.get("raw_code_text")
            or drug_info.get("code_text")
            or ""
        ).strip()
        trace_id = str(drug_info.get("label_trace_id") or "").strip()
        return product_code, trace_id

    def batch_medication_matches(self, medication, product_code, trace_id):
        expected_product_code = str(medication.get("product_code") or "").strip()
        expected_trace_id = str(medication.get("trace_id") or "").strip()
        product_matched = (
            not expected_product_code or product_code == expected_product_code
        )
        trace_matched = not expected_trace_id or trace_id == expected_trace_id
        return (
            bool(expected_product_code or expected_trace_id)
            and product_matched
            and trace_matched
        )

    def find_batch_medication(self, batch, product_code, trace_id, mode):
        for stop in batch.get("stops", []):
            for patient in stop.get("patients", []):
                for medication in patient.get("medications", []):
                    if not self.batch_medication_matches(
                        medication, product_code, trace_id
                    ):
                        continue
                    if medication.get("returned") or medication.get("exception"):
                        continue
                    if mode == "load" and medication.get("loaded"):
                        continue
                    if mode == "dispense" and medication.get("dispensed"):
                        continue
                    return stop, patient, medication
        return None, None, None

    def scan_load_delivery_batch(self, payload):
        product_code, trace_id = self.current_scan_key(payload)
        with self.delivery_batch_lock:
            batch = self.delivery_batch
            stop, patient, medication = self.find_batch_medication(
                batch, product_code, trace_id, "load"
            )
            if medication is None:
                message = (
                    f"装药扫码未匹配当前批次：{product_code or '-'} / {trace_id or '-'}"
                )
                self.append_batch_audit(
                    batch,
                    "load_scan",
                    message,
                    "fail",
                    {
                        "scanned_product_code": product_code,
                        "scanned_trace_id": trace_id,
                    },
                )
                self.update_batch_summary(batch)
                return {"ok": False, "message": message, "batch": copy.deepcopy(batch)}
            now = self.now_text()
            medication["loaded"] = True
            medication["loaded_at"] = now
            patient["patient_status"] = "LOADED"
            message = f"装药确认：{patient.get('bed_no')} {patient.get('patient_name')} / {medication.get('medicine_name')}"
            self.append_batch_audit(
                batch,
                "load_scan",
                message,
                "ok",
                {
                    "patient_id": patient.get("patient_id", ""),
                    "medication_id": medication.get("id", ""),
                    "scanned_product_code": product_code,
                    "scanned_trace_id": trace_id,
                },
            )
            self.update_batch_summary(batch)
            return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}

    def scan_dispense_delivery_batch(self, payload):
        product_code, trace_id = self.current_scan_key(payload)
        with self.delivery_batch_lock:
            batch = self.delivery_batch
            active_index = int(batch.get("active_stop_index", -1))
            active_station = ""
            if 0 <= active_index < len(batch.get("stops", [])):
                active_station = batch["stops"][active_index].get("target_station", "")
            stop, patient, medication = self.find_batch_medication(
                batch, product_code, trace_id, "dispense"
            )
            if medication is None or (
                active_station and stop.get("target_station") != active_station
            ):
                message = (
                    f"交付扫码未匹配当前病房：{product_code or '-'} / {trace_id or '-'}"
                )
                self.append_batch_audit(
                    batch,
                    "dispense_scan",
                    message,
                    "fail",
                    {
                        "scanned_product_code": product_code,
                        "scanned_trace_id": trace_id,
                    },
                )
                self.update_batch_summary(batch)
                return {"ok": False, "message": message, "batch": copy.deepcopy(batch)}
            if not medication.get("loaded"):
                message = (
                    f"药品尚未装药确认，不能交付：{medication.get('medicine_name')}"
                )
                self.append_batch_audit(
                    batch,
                    "dispense_scan",
                    message,
                    "fail",
                    {
                        "patient_id": patient.get("patient_id", ""),
                        "medication_id": medication.get("id", ""),
                    },
                )
                self.update_batch_summary(batch)
                return {"ok": False, "message": message, "batch": copy.deepcopy(batch)}
            task_id = stop.get("task_manager_task_id") or medication.get(
                "task_manager_task_id", ""
            )
            task_confirmed_at = ""
            if task_id:
                task_state = self.get_state()
                if task_state.get("task_id") != task_id:
                    message = f"任务管理状态不匹配，不能交付：期望 {task_id}，当前 {task_state.get('task_id') or '-'}"
                    self.append_batch_audit(
                        batch,
                        "dispense_scan",
                        message,
                        "fail",
                        {
                            "patient_id": patient.get("patient_id", ""),
                            "medication_id": medication.get("id", ""),
                            "task_manager_task_id": task_id,
                        },
                    )
                    self.update_batch_summary(batch)
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                if task_state.get("state") != "WAITING_DISPENSE_CONFIRMATION":
                    message = f"任务管理尚未到达病房取药确认阶段：{task_state.get('state') or '-'}"
                    self.append_batch_audit(
                        batch,
                        "dispense_scan",
                        message,
                        "fail",
                        {
                            "patient_id": patient.get("patient_id", ""),
                            "medication_id": medication.get("id", ""),
                            "task_manager_task_id": task_id,
                        },
                    )
                    self.update_batch_summary(batch)
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                verify_response = self.verify_delivery_task(
                    {
                        "task_id": task_id,
                        "product_code": product_code,
                        "trace_id": trace_id,
                        "stage": "dispense",
                    }
                )
                if not verify_response.get("verified"):
                    message = (
                        f"任务管理交付确认失败：{verify_response.get('message', '')}"
                    )
                    self.append_batch_audit(
                        batch,
                        "dispense_scan",
                        message,
                        "fail",
                        {
                            "patient_id": patient.get("patient_id", ""),
                            "medication_id": medication.get("id", ""),
                            "task_manager_task_id": task_id,
                            "scanned_product_code": product_code,
                            "scanned_trace_id": trace_id,
                        },
                    )
                    self.update_batch_summary(batch)
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                task_confirmed_at = verify_response.get("confirmed_at", "")
                medication["task_manager_confirmed_at"] = task_confirmed_at
                medication["task_manager_task_state"] = verify_response.get(
                    "task_state", ""
                )
            now = task_confirmed_at or self.now_text()
            medication["dispensed"] = True
            medication["dispensed_at"] = now
            message = f"交付确认：{stop.get('display_name')} {patient.get('bed_no')} {patient.get('patient_name')} / {medication.get('medicine_name')}"
            self.append_batch_audit(
                batch,
                "dispense_scan",
                message,
                "ok",
                {
                    "patient_id": patient.get("patient_id", ""),
                    "medication_id": medication.get("id", ""),
                    "scanned_product_code": product_code,
                    "scanned_trace_id": trace_id,
                },
            )
            self.update_batch_summary(batch)
            if stop.get("medication_total_count") and stop.get(
                "medication_done_count"
            ) >= stop.get("medication_total_count"):
                stop["stop_status"] = "COMPLETED"
                stop["completed_time"] = now
                batch["route_status"] = "WARD_COMPLETED"
                self.append_batch_audit(
                    batch,
                    "ward_completed",
                    f"{stop.get('display_name')} 已全部交付",
                    "ok",
                )
            return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}

    def mark_delivery_batch_exception(self, payload):
        action = str(payload.get("action") or "").strip()
        patient_id = str(payload.get("patient_id") or "").strip()
        medication_id = str(payload.get("medication_id") or "").strip()
        reason = str(payload.get("reason") or "").strip()
        with self.delivery_batch_lock:
            batch = self.delivery_batch
            stop, patient, medication = self.find_batch_item_by_id(
                batch, patient_id, medication_id
            )
            if patient is None:
                message = f"未找到病人：{patient_id or '-'}"
                self.append_batch_audit(
                    batch, "exception", message, "fail", {"patient_id": patient_id}
                )
                return {"ok": False, "message": message, "batch": copy.deepcopy(batch)}
            now = self.now_text()
            if action == "patient_absent":
                affected = 0
                for item in patient.get("medications", []):
                    if (
                        item.get("dispensed")
                        or item.get("returned")
                        or item.get("exception")
                    ):
                        continue
                    item["exception"] = "patient_absent"
                    item["exception_at"] = now
                    item["exception_reason"] = reason or "病人不在，暂不交付"
                    item["exception_resolved_at"] = ""
                    item["exception_resolved_reason"] = ""
                    item["exception_resolution_action"] = ""
                    item["manual_reviewed"] = False
                    item["manual_reviewed_at"] = ""
                    item["manual_review_result"] = ""
                    affected += 1
                patient["patient_status"] = "PATIENT_ABSENT"
                message = f"已标记病人不在：{patient.get('bed_no')} {patient.get('patient_name')}，影响 {affected} 项药品"
                self.append_batch_audit(
                    batch,
                    "patient_absent",
                    message,
                    "warn",
                    {
                        "patient_id": patient.get("patient_id", ""),
                        "affected_medication_count": affected,
                    },
                )
                self.update_batch_summary(batch)
                self.mark_active_stop_completed_if_ready(batch, stop)
                return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}
            if action in {"retry", "clear_exception"} and not medication_id:
                if batch.get("route_status") in {
                    "RETURNING_TO_PHARMACY",
                    "BATCH_COMPLETED",
                }:
                    message = "批次已离开病房或已完成，不能重新打开异常"
                    self.append_batch_audit(
                        batch,
                        action,
                        message,
                        "fail",
                        {"patient_id": patient.get("patient_id", "")},
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                if stop.get(
                    "stop_status"
                ) == "COMPLETED" and not self.reopen_active_stop_for_retry(batch, stop):
                    message = (
                        f"{stop.get('display_name')} 不是当前病房，不能重新打开异常"
                    )
                    self.append_batch_audit(
                        batch,
                        action,
                        message,
                        "fail",
                        {"patient_id": patient.get("patient_id", "")},
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                affected = 0
                for item in patient.get("medications", []):
                    if (
                        item.get("exception")
                        and not item.get("dispensed")
                        and not item.get("returned")
                    ):
                        self.clear_medication_exception_for_retry(
                            item,
                            now,
                            reason
                            or (
                                "稍后重试，重新进入交付流程"
                                if action == "retry"
                                else "异常解除，重新进入交付流程"
                            ),
                            action,
                        )
                        affected += 1
                if affected <= 0:
                    message = f"没有可重新处理的异常药品：{patient.get('bed_no')} {patient.get('patient_name')}"
                    self.append_batch_audit(
                        batch,
                        action,
                        message,
                        "fail",
                        {"patient_id": patient.get("patient_id", "")},
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                patient["patient_status"] = "LOADED"
                self.reopen_active_stop_for_retry(batch, stop)
                message = f"已重新打开病人异常：{patient.get('bed_no')} {patient.get('patient_name')}，{affected} 项药品可继续交付"
                self.append_batch_audit(
                    batch,
                    action,
                    message,
                    "ok",
                    {
                        "patient_id": patient.get("patient_id", ""),
                        "affected_medication_count": affected,
                    },
                )
                self.update_batch_summary(batch)
                return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}
            if action == "manual_review" and not medication_id:
                affected = 0
                for item in patient.get("medications", []):
                    if item.get("exception") or item.get("returned"):
                        self.mark_medication_manual_reviewed(
                            item, now, reason or "人工复核确认已处理"
                        )
                        affected += 1
                if affected <= 0:
                    message = f"没有需要人工复核的异常药品：{patient.get('bed_no')} {patient.get('patient_name')}"
                    self.append_batch_audit(
                        batch,
                        "manual_review",
                        message,
                        "fail",
                        {"patient_id": patient.get("patient_id", "")},
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                message = f"人工复核确认：{patient.get('bed_no')} {patient.get('patient_name')}，已复核 {affected} 项药品"
                self.append_batch_audit(
                    batch,
                    "manual_review",
                    message,
                    "ok",
                    {
                        "patient_id": patient.get("patient_id", ""),
                        "affected_medication_count": affected,
                    },
                )
                self.update_batch_summary(batch)
                self.mark_active_stop_completed_if_ready(batch, stop)
                return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}
            if medication is None:
                message = f"未找到药品：{medication_id or '-'}"
                self.append_batch_audit(
                    batch,
                    "exception",
                    message,
                    "fail",
                    {
                        "patient_id": patient_id,
                        "medication_id": medication_id,
                    },
                )
                return {"ok": False, "message": message, "batch": copy.deepcopy(batch)}
            if action == "drug_exception":
                if medication.get("dispensed"):
                    message = (
                        f"药品已交付，不能标记异常：{medication.get('medicine_name')}"
                    )
                    self.append_batch_audit(
                        batch,
                        "drug_exception",
                        message,
                        "fail",
                        {
                            "patient_id": patient.get("patient_id", ""),
                            "medication_id": medication.get("id", ""),
                        },
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                medication["exception"] = "drug_exception"
                medication["exception_at"] = now
                medication["exception_reason"] = reason or "药品异常，转人工处理"
                medication["exception_resolved_at"] = ""
                medication["exception_resolved_reason"] = ""
                medication["exception_resolution_action"] = ""
                medication["manual_reviewed"] = False
                medication["manual_reviewed_at"] = ""
                medication["manual_review_result"] = ""
                message = f"已标记药品异常：{patient.get('bed_no')} {patient.get('patient_name')} / {medication.get('medicine_name')}"
                self.append_batch_audit(
                    batch,
                    "drug_exception",
                    message,
                    "warn",
                    {
                        "patient_id": patient.get("patient_id", ""),
                        "medication_id": medication.get("id", ""),
                    },
                )
                self.update_batch_summary(batch)
                self.mark_active_stop_completed_if_ready(batch, stop)
                return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}
            if action == "return":
                if medication.get("dispensed"):
                    message = f"药品已交付，不能回收：{medication.get('medicine_name')}"
                    self.append_batch_audit(
                        batch,
                        "return_medication",
                        message,
                        "fail",
                        {
                            "patient_id": patient.get("patient_id", ""),
                            "medication_id": medication.get("id", ""),
                        },
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                medication["returned"] = True
                medication["returned_at"] = now
                medication["return_reason"] = reason or "未交付，回药房回收"
                medication["manual_reviewed"] = False
                medication["manual_reviewed_at"] = ""
                medication["manual_review_result"] = ""
                message = f"已标记未交付回收：{patient.get('bed_no')} {patient.get('patient_name')} / {medication.get('medicine_name')}"
                self.append_batch_audit(
                    batch,
                    "return_medication",
                    message,
                    "ok",
                    {
                        "patient_id": patient.get("patient_id", ""),
                        "medication_id": medication.get("id", ""),
                    },
                )
                self.update_batch_summary(batch)
                self.mark_active_stop_completed_if_ready(batch, stop)
                return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}
            if action in {"retry", "clear_exception"}:
                if not medication.get("exception"):
                    message = f"药品没有待解除异常：{medication.get('medicine_name')}"
                    self.append_batch_audit(
                        batch,
                        action,
                        message,
                        "fail",
                        {
                            "patient_id": patient.get("patient_id", ""),
                            "medication_id": medication.get("id", ""),
                        },
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                if medication.get("dispensed") or medication.get("returned"):
                    message = f"药品已交付或已回收，不能重新打开：{medication.get('medicine_name')}"
                    self.append_batch_audit(
                        batch,
                        action,
                        message,
                        "fail",
                        {
                            "patient_id": patient.get("patient_id", ""),
                            "medication_id": medication.get("id", ""),
                        },
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                if batch.get("route_status") in {
                    "RETURNING_TO_PHARMACY",
                    "BATCH_COMPLETED",
                }:
                    message = "批次已离开病房或已完成，不能重新打开异常"
                    self.append_batch_audit(
                        batch,
                        action,
                        message,
                        "fail",
                        {
                            "patient_id": patient.get("patient_id", ""),
                            "medication_id": medication.get("id", ""),
                        },
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                if stop.get(
                    "stop_status"
                ) == "COMPLETED" and not self.reopen_active_stop_for_retry(batch, stop):
                    message = (
                        f"{stop.get('display_name')} 不是当前病房，不能重新打开异常"
                    )
                    self.append_batch_audit(
                        batch,
                        action,
                        message,
                        "fail",
                        {
                            "patient_id": patient.get("patient_id", ""),
                            "medication_id": medication.get("id", ""),
                        },
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                self.clear_medication_exception_for_retry(
                    medication,
                    now,
                    reason
                    or (
                        "稍后重试，重新进入交付流程"
                        if action == "retry"
                        else "异常解除，重新进入交付流程"
                    ),
                    action,
                )
                patient["patient_status"] = "LOADED"
                self.reopen_active_stop_for_retry(batch, stop)
                message = f"已重新打开药品异常：{patient.get('bed_no')} {patient.get('patient_name')} / {medication.get('medicine_name')}"
                self.append_batch_audit(
                    batch,
                    action,
                    message,
                    "ok",
                    {
                        "patient_id": patient.get("patient_id", ""),
                        "medication_id": medication.get("id", ""),
                    },
                )
                self.update_batch_summary(batch)
                return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}
            if action == "manual_review":
                if not medication.get("exception") and not medication.get("returned"):
                    message = (
                        f"药品没有需要人工复核的异常：{medication.get('medicine_name')}"
                    )
                    self.append_batch_audit(
                        batch,
                        "manual_review",
                        message,
                        "fail",
                        {
                            "patient_id": patient.get("patient_id", ""),
                            "medication_id": medication.get("id", ""),
                        },
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                self.mark_medication_manual_reviewed(
                    medication, now, reason or "人工复核确认已处理"
                )
                message = f"人工复核确认：{patient.get('bed_no')} {patient.get('patient_name')} / {medication.get('medicine_name')}"
                self.append_batch_audit(
                    batch,
                    "manual_review",
                    message,
                    "ok",
                    {
                        "patient_id": patient.get("patient_id", ""),
                        "medication_id": medication.get("id", ""),
                    },
                )
                self.update_batch_summary(batch)
                self.mark_active_stop_completed_if_ready(batch, stop)
                return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}
            message = f"未知异常动作：{action or '-'}"
            self.append_batch_audit(
                batch,
                "exception",
                message,
                "fail",
                {
                    "patient_id": patient_id,
                    "medication_id": medication_id,
                },
            )
            return {"ok": False, "message": message, "batch": copy.deepcopy(batch)}

    def find_batch_item_by_id(self, batch, patient_id, medication_id=""):
        for stop in batch.get("stops", []):
            for patient in stop.get("patients", []):
                if not medication_id:
                    if patient_id and patient.get("patient_id") == patient_id:
                        return stop, patient, None
                    continue
                for medication in patient.get("medications", []):
                    if medication.get("id") == medication_id and (
                        not patient_id or patient.get("patient_id") == patient_id
                    ):
                        return stop, patient, medication
        return None, None, None

    def reopen_active_stop_for_retry(self, batch, stop):
        active_index = int(batch.get("active_stop_index", -1))
        if (
            0 <= active_index < len(batch.get("stops", []))
            and batch["stops"][active_index] is stop
        ):
            stop["stop_status"] = "WARD_HANDOVER"
            stop["completed_time"] = ""
            batch["route_status"] = "WARD_HANDOVER"
            batch["current_station"] = stop.get(
                "target_station", batch.get("current_station", "")
            )
            return True
        return False

    def clear_medication_exception_for_retry(self, medication, now, reason, action):
        medication["exception"] = ""
        medication["exception_at"] = ""
        medication["exception_reason"] = ""
        medication["exception_resolved_at"] = now
        medication["exception_resolved_reason"] = reason
        medication["exception_resolution_action"] = action
        medication["manual_reviewed"] = False
        medication["manual_reviewed_at"] = ""
        medication["manual_review_result"] = ""

    def mark_medication_manual_reviewed(self, medication, now, reason):
        medication["manual_reviewed"] = True
        medication["manual_reviewed_at"] = now
        medication["manual_review_result"] = reason

    def mark_active_stop_completed_if_ready(self, batch, stop):
        active_index = int(batch.get("active_stop_index", -1))
        active_stop = None
        if 0 <= active_index < len(batch.get("stops", [])):
            active_stop = batch["stops"][active_index]
        if active_stop is not stop:
            return
        if stop.get("stop_status") == "COMPLETED":
            batch["route_status"] = "WARD_COMPLETED"
            if not stop.get("completed_time"):
                stop["completed_time"] = self.now_text()
            self.append_batch_audit(
                batch, "ward_completed", f"{stop.get('display_name')} 已处理完成", "ok"
            )

    def advance_delivery_batch(self):
        with self.delivery_batch_lock:
            batch = self.delivery_batch
            self.update_batch_summary(batch)
            status = batch.get("route_status")
            if status == "WAITING_LOAD_CONFIRMATION":
                message = "还有药品未完成装药确认，暂不能出发"
                self.append_batch_audit(batch, "advance", message, "fail")
                return {"ok": False, "message": message, "batch": copy.deepcopy(batch)}
            if status == "READY_TO_DEPART":
                return self.move_to_next_batch_stop_locked(batch)
            if status == "NAVIGATING_TO_WARD":
                active_index = int(batch.get("active_stop_index", -1))
                if 0 <= active_index < len(batch.get("stops", [])):
                    stop = batch["stops"][active_index]
                    task_id = stop.get("task_manager_task_id", "")
                    if task_id:
                        task_state = self.get_state()
                        if task_state.get("task_id") != task_id:
                            message = f"等待任务管理同步当前病房任务：期望 {task_id}，当前 {task_state.get('task_id') or '-'}"
                            self.append_batch_audit(
                                batch,
                                "arrive_wait_task_manager",
                                message,
                                "fail",
                                {
                                    "stop_id": stop.get("stop_id", ""),
                                    "task_manager_task_id": task_id,
                                },
                            )
                            return {
                                "ok": False,
                                "message": message,
                                "batch": copy.deepcopy(batch),
                            }
                        if task_state.get("state") != "WAITING_DISPENSE_CONFIRMATION":
                            message = f"尚未到达{stop.get('display_name')}，任务管理状态：{task_state.get('state') or '-'}，进度 {int(float(task_state.get('progress', 0.0)) * 100)}%"
                            self.append_batch_audit(
                                batch,
                                "arrive_wait_task_manager",
                                message,
                                "fail",
                                {
                                    "stop_id": stop.get("stop_id", ""),
                                    "task_manager_task_id": task_id,
                                },
                            )
                            return {
                                "ok": False,
                                "message": message,
                                "batch": copy.deepcopy(batch),
                            }
                    now = self.now_text()
                    stop["stop_status"] = "WARD_HANDOVER"
                    stop["arrived_time"] = now
                    batch["route_status"] = "WARD_HANDOVER"
                    batch["current_station"] = stop.get("target_station", "")
                    message = f"已到达{stop.get('display_name')}，进入病房交付确认"
                    self.append_batch_audit(batch, "arrived_at_ward", message, "ok")
                    return {
                        "ok": True,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
            if status in {"WARD_COMPLETED", "WARD_HANDOVER"}:
                active_index = int(batch.get("active_stop_index", -1))
                if 0 <= active_index < len(batch.get("stops", [])):
                    stop = batch["stops"][active_index]
                    if stop.get("stop_status") != "COMPLETED":
                        message = f"{stop.get('display_name')} 仍有药品未交付或未处理"
                        self.append_batch_audit(batch, "advance", message, "fail")
                        return {
                            "ok": False,
                            "message": message,
                            "batch": copy.deepcopy(batch),
                        }
                return self.move_to_next_batch_stop_locked(batch)
            if status == "RETURNING_TO_PHARMACY":
                now = self.now_text()
                batch["route_status"] = "BATCH_COMPLETED"
                batch["current_station"] = "pharmacy"
                batch["finished_time"] = now
                message = "已返回药房，本次配送批次完成"
                self.append_batch_audit(batch, "batch_completed", message, "ok")
                return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}
            message = f"当前批次状态无需推进：{status}"
            return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}

    def move_to_next_batch_stop_locked(self, batch):
        for index, stop in enumerate(batch.get("stops", [])):
            if stop.get("stop_status") != "COMPLETED":
                now = self.now_text()
                task_response = self.create_task_manager_stop_task_locked(batch, stop)
                if not task_response.get("accepted"):
                    message = f"创建病房级任务失败：{task_response.get('message', '')}"
                    self.append_batch_audit(
                        batch,
                        "task_manager_create_failed",
                        message,
                        "fail",
                        {
                            "stop_id": stop.get("stop_id", ""),
                            "target_station": stop.get("target_station", ""),
                        },
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                batch["active_stop_index"] = index
                batch["active_stop_id"] = stop.get("stop_id", "")
                batch["route_status"] = "NAVIGATING_TO_WARD"
                batch["current_station"] = (
                    "pharmacy"
                    if index == 0
                    else batch.get("current_station", "pharmacy")
                )
                if not batch.get("started_time"):
                    batch["started_time"] = now
                stop["stop_status"] = "NAVIGATING_TO_WARD"
                task_id_text = (
                    f"，任务管理 ID：{task_response.get('task_id')}"
                    if task_response.get("task_id")
                    else ""
                )
                message = f"开始前往{stop.get('display_name')}{task_id_text}"
                self.append_batch_audit(
                    batch,
                    "navigate_to_ward",
                    message,
                    "ok",
                    {
                        "stop_id": stop.get("stop_id", ""),
                        "target_station": stop.get("target_station", ""),
                        "task_manager_task_id": task_response.get("task_id", ""),
                    },
                )
                return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}
        batch["active_stop_index"] = -1
        batch["active_stop_id"] = ""
        batch["route_status"] = "RETURNING_TO_PHARMACY"
        batch["current_station"] = batch.get("current_station", "")
        message = "所有病房已处理，开始返回药房"
        self.append_batch_audit(batch, "returning_to_pharmacy", message, "ok")
        return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}

    def on_delivery_state(self, msg):
        with self.state_lock:
            self.latest_state = {
                "task_id": msg.task_id,
                "state": msg.state,
                "message": msg.message,
                "current_station": msg.current_station,
                "target_station": msg.target_station,
                "medicine_name": msg.medicine_name,
                "patient_id": msg.patient_id,
                "patient_name": msg.patient_name,
                "ward_id": msg.ward_id,
                "bed_no": msg.bed_no,
                "product_code": msg.product_code,
                "product_model": msg.product_model,
                "quantity": msg.quantity,
                "trace_id": msg.trace_id,
                "order_no": msg.order_no,
                "medications_json": msg.medications_json,
                "medication_total_count": int(msg.medication_total_count),
                "medication_loaded_count": int(msg.medication_loaded_count),
                "medication_dispensed_count": int(msg.medication_dispensed_count),
                "load_confirmed": bool(msg.load_confirmed),
                "load_confirmed_at": msg.load_confirmed_at,
                "dispense_confirmed": bool(msg.dispense_confirmed),
                "dispense_confirmed_at": msg.dispense_confirmed_at,
                "last_verification_stage": msg.last_verification_stage,
                "last_verification_passed": bool(msg.last_verification_passed),
                "last_verification_message": msg.last_verification_message,
                "verification_records": list(msg.verification_records),
                "progress": float(msg.progress),
                "stamp": float(msg.stamp.sec)
                + float(msg.stamp.nanosec) / 1_000_000_000.0,
            }

    def on_drug_info(self, msg):
        with self.drug_info_lock:
            self.latest_drug_info = {
                "drug_id": msg.drug_id,
                "drug_name": msg.drug_name,
                "drug_type": msg.drug_type,
                "confidence": float(msg.confidence),
                "loaded": bool(msg.loaded),
                "source": msg.source,
                "stamp": float(msg.stamp.sec)
                + float(msg.stamp.nanosec) / 1_000_000_000.0,
            }

    def on_drug_recognition_status(self, msg):
        try:
            status = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        with self.drug_info_lock:
            self.latest_recognition_status = status if isinstance(status, dict) else {}

    def on_chassis_status(self, msg):
        try:
            status = json.loads(msg.data)
        except json.JSONDecodeError:
            status = {
                "ok": False,
                "received": True,
                "message": "invalid chassis status json",
                "raw": msg.data,
            }
        if not isinstance(status, dict):
            status = {
                "ok": False,
                "received": True,
                "message": "chassis status payload is not an object",
            }
        status["received"] = True
        status["web_received_at"] = time.time()
        status.setdefault("ok", True)
        status.setdefault("topic", self.chassis_status_topic)
        with self.chassis_status_lock:
            self.latest_chassis_status = status

    def get_state(self):
        with self.state_lock:
            return dict(self.latest_state)

    def get_drug_info(self):
        with self.drug_info_lock:
            data = dict(self.latest_drug_info)
            status = dict(self.latest_recognition_status)
            label_fields = (
                status.get("label_fields")
                if isinstance(status.get("label_fields"), dict)
                else {}
            )
            data.update(
                {
                    "raw_code_text": status.get("raw_code_text", ""),
                    "code_text": status.get("code_text", ""),
                    "code_type": status.get("code_type", ""),
                    "code_method": status.get("code_method", ""),
                    "ocr_enabled": bool(status.get("ocr_enabled", False)),
                    "ocr_available": bool(status.get("ocr_available", False)),
                    "ocr_text": status.get("ocr_text", ""),
                    "ocr_confidence": float(status.get("ocr_confidence", 0.0) or 0.0),
                    "ocr_language": status.get("ocr_language", ""),
                    "ocr_backend": status.get("ocr_backend", ""),
                    "ocr_error": status.get("ocr_error", ""),
                    "label_fields": label_fields,
                    "label_order_no": status.get(
                        "label_order_no", label_fields.get("on", "")
                    ),
                    "label_product_code": status.get(
                        "label_product_code", label_fields.get("pc", "")
                    ),
                    "label_product_model": status.get(
                        "label_product_model", label_fields.get("pm", "")
                    ),
                    "label_quantity": status.get(
                        "label_quantity", label_fields.get("qty", "")
                    ),
                    "label_trace_id": status.get(
                        "label_trace_id", label_fields.get("pdi", "")
                    ),
                }
            )
            return data

    def get_chassis_status(self):
        with self.chassis_status_lock:
            return copy.deepcopy(self.latest_chassis_status)

    def start_web_server(self):
        handler = self.make_handler()
        self.server = ThreadingHTTPServer((self.host, self.port), handler)
        self.server_thread = threading.Thread(
            target=self.server.serve_forever, daemon=True
        )
        self.server_thread.start()
        self.get_logger().info(f"Web dashboard started: http://localhost:{self.port}")

    def stop_web_server(self):
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None

    def create_task(self, payload):
        if not self.create_task_client.wait_for_service(
            timeout_sec=self.service_timeout_sec
        ):
            return {"accepted": False, "task_id": "", "message": "创建任务服务不可用"}
        request = CreateDeliveryTask.Request()
        request.medicine_name = str(payload.get("medicine_name") or "常规药品")
        request.source_station = str(payload.get("source_station") or "pharmacy")
        request.target_station = str(payload.get("target_station") or "")
        request.patient_id = str(payload.get("patient_id") or "")
        request.patient_name = str(payload.get("patient_name") or "")
        request.ward_id = str(payload.get("ward_id") or "")
        request.bed_no = str(payload.get("bed_no") or "")
        request.product_code = str(payload.get("product_code") or "")
        request.product_model = str(payload.get("product_model") or "")
        request.quantity = str(payload.get("quantity") or "")
        request.trace_id = str(payload.get("trace_id") or "")
        request.order_no = str(payload.get("order_no") or "")
        request.medications_json = str(payload.get("medications_json") or "")
        future = self.create_task_client.call_async(request)
        response = self.wait_future(future)
        if response is None:
            return {"accepted": False, "task_id": "", "message": "创建任务服务超时"}
        return {
            "accepted": bool(response.accepted),
            "task_id": response.task_id,
            "message": response.message,
        }

    def verify_delivery_task(self, payload):
        if not self.verify_task_client.wait_for_service(
            timeout_sec=self.service_timeout_sec
        ):
            return {"verified": False, "message": "扫码校验服务不可用"}
        request = VerifyDeliveryTask.Request()
        request.task_id = str(payload.get("task_id") or "")
        request.product_code = str(payload.get("product_code") or "")
        request.trace_id = str(payload.get("trace_id") or "")
        request.stage = str(payload.get("stage") or "scan")
        future = self.verify_task_client.call_async(request)
        response = self.wait_future(future)
        if response is None:
            return {"verified": False, "message": "扫码校验服务超时"}
        return {
            "verified": bool(response.verified),
            "product_code_matched": bool(response.product_code_matched),
            "trace_id_matched": bool(response.trace_id_matched),
            "expected_product_code": response.expected_product_code,
            "expected_trace_id": response.expected_trace_id,
            "scanned_product_code": response.scanned_product_code,
            "scanned_trace_id": response.scanned_trace_id,
            "message": response.message,
            "stage": response.stage,
            "state_changed": bool(response.state_changed),
            "task_state": response.task_state,
            "confirmed_at": response.confirmed_at,
            "matched_medicine_name": response.matched_medicine_name,
            "medication_total_count": int(response.medication_total_count),
            "medication_verified_count": int(response.medication_verified_count),
            "medications_json": response.medications_json,
        }

    def get_patient_orders(self):
        return {"orders": PATIENT_MEDICATION_ORDERS}

    def build_delivery_batch_report(self):
        batch = self.get_delivery_batch()
        rows = []
        for stop in batch.get("stops", []):
            for patient in stop.get("patients", []):
                for medication in patient.get("medications", []):
                    rows.append(
                        {
                            "batch_id": batch.get("batch_id", ""),
                            "route_status": batch.get("route_status", ""),
                            "ward_id": patient.get("ward_id", ""),
                            "ward_name": patient.get(
                                "ward_name", stop.get("display_name", "")
                            ),
                            "bed_no": patient.get("bed_no", ""),
                            "patient_id": patient.get("patient_id", ""),
                            "patient_name": patient.get("patient_name", ""),
                            "medicine_name": medication.get("medicine_name", ""),
                            "product_code": medication.get("product_code", ""),
                            "trace_id": medication.get("trace_id", ""),
                            "quantity": medication.get("quantity", ""),
                            "loaded": bool(medication.get("loaded")),
                            "loaded_at": medication.get("loaded_at", ""),
                            "dispensed": bool(medication.get("dispensed")),
                            "dispensed_at": medication.get("dispensed_at", ""),
                            "returned": bool(medication.get("returned")),
                            "returned_at": medication.get("returned_at", ""),
                            "return_reason": medication.get("return_reason", ""),
                            "exception": medication.get("exception", ""),
                            "exception_at": medication.get("exception_at", ""),
                            "exception_reason": medication.get("exception_reason", ""),
                            "exception_resolved_at": medication.get(
                                "exception_resolved_at", ""
                            ),
                            "exception_resolved_reason": medication.get(
                                "exception_resolved_reason", ""
                            ),
                            "exception_resolution_action": medication.get(
                                "exception_resolution_action", ""
                            ),
                            "manual_reviewed": bool(medication.get("manual_reviewed")),
                            "manual_reviewed_at": medication.get(
                                "manual_reviewed_at", ""
                            ),
                            "manual_review_result": medication.get(
                                "manual_review_result", ""
                            ),
                        }
                    )
        return {
            "generated_at": self.now_text(),
            "batch": batch,
            "rows": rows,
        }

    def build_delivery_batch_report_csv(self):
        report = self.build_delivery_batch_report()
        output = io.StringIO()
        fieldnames = [
            "batch_id",
            "route_status",
            "ward_id",
            "ward_name",
            "bed_no",
            "patient_id",
            "patient_name",
            "medicine_name",
            "product_code",
            "trace_id",
            "quantity",
            "loaded",
            "loaded_at",
            "dispensed",
            "dispensed_at",
            "returned",
            "returned_at",
            "return_reason",
            "exception",
            "exception_at",
            "exception_reason",
            "exception_resolved_at",
            "exception_resolved_reason",
            "exception_resolution_action",
            "manual_reviewed",
            "manual_reviewed_at",
            "manual_review_result",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in report["rows"]:
            writer.writerow(row)
        return output.getvalue()

    def cancel_task(self, payload):
        if not self.cancel_task_client.wait_for_service(
            timeout_sec=self.service_timeout_sec
        ):
            return {"success": False, "message": "取消任务服务不可用"}
        request = CancelDeliveryTask.Request()
        request.task_id = str(payload.get("task_id") or "")
        future = self.cancel_task_client.call_async(request)
        response = self.wait_future(future)
        if response is None:
            return {"success": False, "message": "取消任务服务超时"}
        return {"success": bool(response.success), "message": response.message}

    def wait_future(self, future):
        deadline = time.monotonic() + self.service_timeout_sec
        while time.monotonic() < deadline:
            if future.done():
                return future.result()
            time.sleep(0.02)
        return None

    def make_handler(self):
        dashboard = self

        class DashboardRequestHandler(BaseHTTPRequestHandler):
            def log_message(self, format_text, *args):
                dashboard.get_logger().info(format_text % args)

            def do_GET(self):
                path = urlparse(self.path).path
                if path == "/":
                    self.write_html(INDEX_HTML)
                    return
                if path == "/api/health":
                    self.write_json({"ok": True})
                    return
                if path == "/api/stations":
                    self.write_json({"stations": dashboard.stations})
                    return
                if path == "/api/patient_orders":
                    self.write_json(dashboard.get_patient_orders())
                    return
                if path == "/api/delivery_batch":
                    self.write_json(dashboard.get_delivery_batch())
                    return
                if path == "/api/delivery_batch/report.json":
                    self.write_json(dashboard.build_delivery_batch_report())
                    return
                if path == "/api/delivery_batch/report.csv":
                    self.write_text(
                        dashboard.build_delivery_batch_report_csv(),
                        content_type="text/csv; charset=utf-8",
                        filename="delivery_batch_report.csv",
                    )
                    return
                if path == "/api/state":
                    self.write_json(dashboard.get_state())
                    return
                if path == "/api/drug_info":
                    self.write_json(dashboard.get_drug_info())
                    return
                if path == "/api/chassis_status":
                    self.write_json(dashboard.get_chassis_status())
                    return
                self.write_json({"message": "Not found"}, status=404)

            def do_POST(self):
                path = urlparse(self.path).path
                payload = self.read_json_body()
                if path == "/api/tasks":
                    self.write_json(dashboard.create_task(payload))
                    return
                if path == "/api/delivery_batch/reset":
                    response = dashboard.reset_delivery_batch()
                    dashboard.persist_current_delivery_batch()
                    self.write_json(response)
                    return
                if path == "/api/delivery_batch/import":
                    response = dashboard.import_delivery_batch(payload)
                    if response.get("ok"):
                        dashboard.persist_current_delivery_batch()
                    self.write_json(response, status=200 if response.get("ok") else 400)
                    return
                if path == "/api/delivery_batch/load_scan":
                    response = dashboard.scan_load_delivery_batch(payload)
                    dashboard.persist_current_delivery_batch()
                    self.write_json(response)
                    return
                if path == "/api/delivery_batch/dispense_scan":
                    response = dashboard.scan_dispense_delivery_batch(payload)
                    dashboard.persist_current_delivery_batch()
                    self.write_json(response)
                    return
                if path == "/api/delivery_batch/exception":
                    response = dashboard.mark_delivery_batch_exception(payload)
                    dashboard.persist_current_delivery_batch()
                    self.write_json(response)
                    return
                if path == "/api/delivery_batch/advance":
                    response = dashboard.advance_delivery_batch()
                    dashboard.persist_current_delivery_batch()
                    self.write_json(response)
                    return
                if path == "/api/verify_task":
                    self.write_json(dashboard.verify_delivery_task(payload))
                    return
                if path == "/api/cancel":
                    self.write_json(dashboard.cancel_task(payload))
                    return
                self.write_json({"message": "Not found"}, status=404)

            def read_json_body(self):
                length = int(self.headers.get("Content-Length", "0") or "0")
                if length <= 0:
                    return {}
                raw = self.rfile.read(length).decode("utf-8")
                return json.loads(raw or "{}")

            def write_html(self, html):
                data = html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def write_json(self, payload, status=200):
                data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def write_text(
                self,
                text,
                status=200,
                content_type="text/plain; charset=utf-8",
                filename="",
            ):
                data = text.encode("utf-8-sig")
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(data)))
                if filename:
                    self.send_header(
                        "Content-Disposition", f'attachment; filename="{filename}"'
                    )
                self.end_headers()
                self.wfile.write(data)

        return DashboardRequestHandler


def main():
    rclpy.init()
    node = MedicineWebDashboard()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    node.start_web_server()
    try:
        executor.spin()
    finally:
        node.stop_web_server()
        executor.remove_node(node)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
