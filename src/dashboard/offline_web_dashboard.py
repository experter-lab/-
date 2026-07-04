#!/usr/bin/env python3
"""Local offline dashboard for developing the robot web UI without RK3588."""

from __future__ import annotations

import argparse
import json
import math
import mimetypes
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parent
MAPS_DIR = ROOT / "maps"
DEFAULT_MAP = MAPS_DIR / "a1_handheld_map_latest.yaml"


INDEX_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>RK3588 离线导航控制台</title>
  <style>
    :root {
      --bg: #0d1112;
      --panel: #f4f1e8;
      --panel-2: #e9e4d7;
      --ink: #111817;
      --muted: #66706b;
      --line: #c9c1ad;
      --line-dark: #2b3532;
      --accent: #0f8b8d;
      --accent-2: #e9b44c;
      --danger: #c44536;
      --ok: #1f7a4d;
      --shadow: 0 26px 70px rgba(0, 0, 0, 0.24);
      --mono: "Cascadia Mono", "IBM Plex Mono", "Consolas", monospace;
      --sans: "Bahnschrift", "Microsoft YaHei UI", "Segoe UI", sans-serif;
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      background:
        linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px) 0 0 / 24px 24px,
        radial-gradient(circle at 16% 12%, rgba(15, 139, 141, 0.22), transparent 28%),
        var(--bg);
      font-family: var(--sans);
      letter-spacing: 0;
    }

    button, input, select { font: inherit; }
    button {
      border: 1px solid var(--line-dark);
      background: var(--ink);
      color: #fffaf0;
      min-height: 38px;
      padding: 0 14px;
      border-radius: 6px;
      cursor: pointer;
    }
    button.secondary {
      background: transparent;
      color: var(--ink);
      border-color: var(--line);
    }
    button:focus-visible, select:focus-visible {
      outline: 3px solid rgba(15, 139, 141, 0.35);
      outline-offset: 2px;
    }

    .shell {
      width: min(1440px, calc(100vw - 28px));
      margin: 18px auto;
      display: grid;
      grid-template-columns: 330px minmax(0, 1fr);
      gap: 14px;
    }

    .rail, .main-panel, .card {
      background: var(--panel);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
    }
    .rail {
      min-height: calc(100vh - 36px);
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    .brand {
      border-bottom: 2px solid var(--ink);
      padding-bottom: 14px;
    }
    .brand h1 {
      font-size: 25px;
      line-height: 1.08;
      margin: 0;
      font-weight: 800;
    }
    .brand p {
      color: var(--muted);
      margin: 8px 0 0;
      font-size: 13px;
    }
    .status-strip {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .meter {
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.34);
      padding: 10px;
      min-height: 78px;
    }
    .meter span {
      display: block;
      color: var(--muted);
      font-size: 12px;
    }
    .meter strong {
      display: block;
      margin-top: 7px;
      font: 700 19px/1 var(--mono);
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      min-height: 28px;
      padding: 4px 10px;
      border: 1px solid currentColor;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }
    .badge::before {
      content: "";
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: currentColor;
    }
    .ok { color: var(--ok); }
    .warn { color: #9a6400; }
    .bad { color: var(--danger); }
    .cold { color: var(--accent); }

    .control-group {
      display: grid;
      gap: 8px;
    }
    .control-group label {
      color: var(--muted);
      font-size: 12px;
    }
    select {
      width: 100%;
      border: 1px solid var(--line);
      background: #fffaf0;
      min-height: 38px;
      padding: 0 10px;
      border-radius: 6px;
      color: var(--ink);
    }

    .main-panel {
      min-height: calc(100vh - 36px);
      padding: 14px;
    }
    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      margin-bottom: 14px;
    }
    .topbar h2 {
      margin: 0;
      font-size: 18px;
    }
    .tabs {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .tabs button {
      background: transparent;
      color: var(--ink);
      border-color: var(--line);
    }
    .tabs button.active {
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
    }

    .grid {
      display: grid;
      grid-template-columns: minmax(0, 1.45fr) minmax(330px, 0.75fr);
      gap: 14px;
    }
    .card {
      box-shadow: none;
      padding: 14px;
      border-radius: 8px;
    }
    .card h3 {
      margin: 0 0 12px;
      font-size: 15px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
    }

    .map-frame {
      position: relative;
      min-height: 620px;
      background: #101615;
      border: 1px solid var(--line-dark);
      overflow: hidden;
    }
    canvas {
      display: block;
      width: 100%;
      height: 620px;
    }
    .map-hud {
      position: absolute;
      left: 14px;
      bottom: 14px;
      right: 14px;
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
      pointer-events: none;
    }
    .hud-cell {
      background: rgba(244,241,232,0.88);
      border: 1px solid rgba(17,24,23,0.28);
      padding: 8px;
      min-width: 0;
    }
    .hud-cell span {
      color: var(--muted);
      font-size: 11px;
      display: block;
    }
    .hud-cell strong {
      font: 700 14px/1.25 var(--mono);
      display: block;
      margin-top: 4px;
      overflow-wrap: anywhere;
    }

    .diag-list {
      display: grid;
      gap: 8px;
    }
    .diag {
      display: grid;
      grid-template-columns: 74px minmax(0, 1fr) auto;
      gap: 10px;
      align-items: center;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.32);
      padding: 10px;
    }
    .diag strong {
      font-size: 13px;
    }
    .diag span {
      color: var(--muted);
      font: 12px/1.35 var(--mono);
    }

    .kv {
      display: grid;
      grid-template-columns: 108px minmax(0, 1fr);
      gap: 10px;
      border-top: 1px solid var(--line);
      padding: 10px 0;
    }
    .kv:first-of-type { border-top: 0; }
    .kv span {
      color: var(--muted);
      font-size: 12px;
    }
    .kv strong {
      font: 700 13px/1.35 var(--mono);
      overflow-wrap: anywhere;
    }
    .notice {
      border-left: 4px solid var(--accent);
      background: rgba(15, 139, 141, 0.08);
      padding: 10px 12px;
      color: #384340;
      font-size: 13px;
      line-height: 1.5;
    }
    .timeline {
      display: grid;
      gap: 8px;
      max-height: 210px;
      overflow: auto;
      padding-right: 2px;
    }
    .event {
      border: 1px solid var(--line);
      padding: 9px;
      background: var(--panel-2);
      font-size: 12px;
    }
    .event b {
      display: block;
      font-family: var(--mono);
      margin-bottom: 3px;
    }

    .page { display: none; }
    .page.active { display: block; }
    .stack { display: grid; gap: 14px; }

    @media (max-width: 980px) {
      .shell, .grid {
        grid-template-columns: 1fr;
      }
      .rail {
        min-height: 0;
      }
      .map-hud {
        grid-template-columns: 1fr 1fr;
      }
    }
    @media (max-width: 620px) {
      .shell { width: calc(100vw - 16px); margin: 8px auto; }
      .map-frame { min-height: 440px; }
      canvas { height: 440px; }
      .map-hud { grid-template-columns: 1fr; }
      .topbar { align-items: flex-start; flex-direction: column; }
      .diag { grid-template-columns: 1fr auto; }
      .diag span { grid-column: 1 / -1; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside class="rail">
      <div class="brand">
        <h1>RK3588 离线导航控制台</h1>
        <p>不连接小车时，用模拟状态继续开发 Web、地图显示和诊断流程。</p>
      </div>
      <div class="status-strip">
        <div class="meter"><span>运行模式</span><strong id="modeLabel">SIM</strong></div>
        <div class="meter"><span>模拟时间</span><strong id="simClock">0.0s</strong></div>
        <div class="meter"><span>线速度</span><strong id="linearSpeed">0.00</strong></div>
        <div class="meter"><span>角速度</span><strong id="angularSpeed">0.00</strong></div>
      </div>
      <div class="control-group">
        <label for="scenario">模拟场景</label>
        <select id="scenario">
          <option value="normal">定位正常，Nav2 待命</option>
          <option value="mapping">建图中，地图逐步更新</option>
          <option value="tf_delay">TF 延迟，RViz 可能丢帧</option>
          <option value="blocked">局部代价地图过密</option>
          <option value="chassis_safe">底盘未授权，安全待机</option>
        </select>
      </div>
      <div class="control-group">
        <label for="mapSelect">地图文件</label>
        <select id="mapSelect"></select>
      </div>
      <button id="resetPose" type="button">重置模拟位姿</button>
      <button id="freeze" class="secondary" type="button">暂停模拟</button>
      <div class="notice">
        这里不会发布 /cmd_vel，也不会连接飞控。它只服务本地浏览器，适合离线设计和流程排练。
      </div>
    </aside>

    <main class="main-panel">
      <div class="topbar">
        <h2>地图、定位与导航诊断</h2>
        <nav class="tabs" aria-label="离线控制台页面">
          <button class="active" type="button" data-page="map">地图</button>
          <button type="button" data-page="diagnostics">诊断</button>
          <button type="button" data-page="chassis">底盘</button>
        </nav>
      </div>

      <section id="page-map" class="page active">
        <div class="grid">
          <div class="card">
            <h3>离线地图视图 <span id="mapBadge" class="badge cold">加载中</span></h3>
            <div class="map-frame">
              <canvas id="mapCanvas" width="920" height="620"></canvas>
              <div class="map-hud">
                <div class="hud-cell"><span>地图</span><strong id="mapName">-</strong></div>
                <div class="hud-cell"><span>分辨率</span><strong id="mapResolution">-</strong></div>
                <div class="hud-cell"><span>小车位姿</span><strong id="poseText">-</strong></div>
                <div class="hud-cell"><span>目标点</span><strong id="goalText">-</strong></div>
              </div>
            </div>
          </div>
          <div class="stack">
            <div class="card">
              <h3>实时摘要 <span id="navBadge" class="badge ok">READY</span></h3>
              <div class="kv"><span>定位来源</span><strong id="localization">Cartographer localization</strong></div>
              <div class="kv"><span>TF 链路</span><strong id="tfChain">map -> odom -> base_link -> laser</strong></div>
              <div class="kv"><span>Nav2 action</span><strong id="navAction">/navigate_to_pose 可用</strong></div>
              <div class="kv"><span>雷达</span><strong id="scanState">/scan 10Hz, frame=laser</strong></div>
            </div>
            <div class="card">
              <h3>模拟事件</h3>
              <div id="events" class="timeline"></div>
            </div>
          </div>
        </div>
      </section>

      <section id="page-diagnostics" class="page">
        <div class="grid">
          <div class="card">
            <h3>启动前检查</h3>
            <div id="diagList" class="diag-list"></div>
          </div>
          <div class="card">
            <h3>下一次实车验证顺序</h3>
            <div class="notice">
              先手动 A/D 验证转向，再短距离 Nav2 Goal，最后看 Web 中 TF、/scan、底盘授权是否同时为绿色。
            </div>
            <div class="kv"><span>第一步</span><strong>确认 /scan 自身遮挡已被 0.35m 过滤</strong></div>
            <div class="kv"><span>第二步</span><strong>确认 Cartographer 定位未跑出地图</strong></div>
            <div class="kv"><span>第三步</span><strong>底盘授权后只点 30-50cm 目标点</strong></div>
            <div class="kv"><span>失败时</span><strong>保留日志，不继续叠加调参</strong></div>
          </div>
        </div>
      </section>

      <section id="page-chassis" class="page">
        <div class="grid">
          <div class="card">
            <h3>底盘安全状态 <span id="chassisBadge" class="badge warn">SIM</span></h3>
            <div class="kv"><span>桥接状态</span><strong id="bridgeState">-</strong></div>
            <div class="kv"><span>控制授权</span><strong id="controlAuth">-</strong></div>
            <div class="kv"><span>急停</span><strong id="estop">-</strong></div>
            <div class="kv"><span>PWM 油门</span><strong id="throttlePwm">-</strong></div>
            <div class="kv"><span>PWM 转向</span><strong id="steeringPwm">-</strong></div>
            <div class="kv"><span>速度限制</span><strong id="speedLimit">-</strong></div>
          </div>
          <div class="card">
            <h3>离线开发边界</h3>
            <div class="notice">
              现在可以安全开发 UI、地图绘制、诊断规则、日志展示和按钮流程。涉及真实速度、PWM、急停默认值的修改，等重新连上车再验证。
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>

  <script>
    const state = {
      map: null,
      mapPixels: null,
      pose: { x: 0, y: 0, yaw: 0 },
      goal: { x: 1.2, y: 0.55 },
      t0: performance.now(),
      frozen: false,
      scenario: 'normal',
    };

    const $ = id => document.getElementById(id);

    function setBadge(el, text, cls) {
      el.textContent = text;
      el.className = `badge ${cls}`;
    }

    async function api(path) {
      const res = await fetch(path, { cache: 'no-store' });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      return res.json();
    }

    async function loadMaps() {
      const data = await api('/api/maps');
      const select = $('mapSelect');
      select.innerHTML = data.maps.map(item => (
        `<option value="${item.yaml}">${item.name}</option>`
      )).join('');
      select.value = data.default_map || (data.maps[0] && data.maps[0].yaml) || '';
      select.addEventListener('change', () => loadMap(select.value));
      if (select.value) await loadMap(select.value);
    }

    async function loadMap(yamlName) {
      setBadge($('mapBadge'), '加载中', 'cold');
      const meta = await api(`/api/map?name=${encodeURIComponent(yamlName)}`);
      const bytes = await fetch(meta.image_url, { cache: 'no-store' }).then(r => r.arrayBuffer());
      state.map = meta;
      state.mapPixels = parsePgm(new Uint8Array(bytes));
      state.pose = { x: 0, y: 0, yaw: -0.15 };
      $('mapName').textContent = meta.name;
      $('mapResolution').textContent = `${meta.resolution} m/px, ${state.mapPixels.width}x${state.mapPixels.height}`;
      setBadge($('mapBadge'), '已加载', 'ok');
      draw();
    }

    function readToken(bytes, indexRef) {
      while (indexRef.i < bytes.length) {
        const c = bytes[indexRef.i];
        if (c === 35) {
          while (indexRef.i < bytes.length && bytes[indexRef.i] !== 10) indexRef.i++;
        } else if (c <= 32) {
          indexRef.i++;
        } else {
          break;
        }
      }
      const start = indexRef.i;
      while (indexRef.i < bytes.length && bytes[indexRef.i] > 32) indexRef.i++;
      return new TextDecoder().decode(bytes.slice(start, indexRef.i));
    }

    function parsePgm(bytes) {
      const ref = { i: 0 };
      const magic = readToken(bytes, ref);
      const width = Number(readToken(bytes, ref));
      const height = Number(readToken(bytes, ref));
      const maxVal = Number(readToken(bytes, ref));
      while (bytes[ref.i] <= 32) ref.i++;
      const pixels = bytes.slice(ref.i, ref.i + width * height);
      if (magic !== 'P5' || !width || !height || !maxVal) {
        throw new Error('仅支持 P5 PGM 地图');
      }
      return { width, height, maxVal, pixels };
    }

    function worldToPixel(x, y) {
      const origin = state.map.origin || [0, 0, 0];
      const px = (x - origin[0]) / state.map.resolution;
      const py = state.mapPixels.height - (y - origin[1]) / state.map.resolution;
      return { x: px, y: py };
    }

    function draw() {
      if (!state.map || !state.mapPixels) return;
      const canvas = $('mapCanvas');
      const ctx = canvas.getContext('2d');
      const map = state.mapPixels;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#101615';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const img = ctx.createImageData(map.width, map.height);
      for (let i = 0; i < map.pixels.length; i++) {
        const value = map.pixels[i];
        const off = i * 4;
        let r = 207, g = 207, b = 207;
        if (value < 80) { r = 18; g = 22; b = 21; }
        else if (value > 235) { r = 250; g = 247; b = 239; }
        img.data[off] = r;
        img.data[off + 1] = g;
        img.data[off + 2] = b;
        img.data[off + 3] = 255;
      }

      const scale = Math.min(canvas.width / map.width, canvas.height / map.height) * 0.9;
      const ox = (canvas.width - map.width * scale) / 2;
      const oy = (canvas.height - map.height * scale) / 2;
      const scratch = document.createElement('canvas');
      scratch.width = map.width;
      scratch.height = map.height;
      scratch.getContext('2d').putImageData(img, 0, 0);
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(scratch, ox, oy, map.width * scale, map.height * scale);

      ctx.save();
      ctx.translate(ox, oy);
      ctx.scale(scale, scale);
      drawGrid(ctx, map.width, map.height);
      drawPath(ctx);
      drawGoal(ctx);
      drawRobot(ctx);
      ctx.restore();

      $('poseText').textContent = `x=${state.pose.x.toFixed(2)} y=${state.pose.y.toFixed(2)} yaw=${state.pose.yaw.toFixed(2)}`;
      $('goalText').textContent = `x=${state.goal.x.toFixed(2)} y=${state.goal.y.toFixed(2)}`;
    }

    function drawGrid(ctx, width, height) {
      ctx.strokeStyle = 'rgba(15, 139, 141, 0.18)';
      ctx.lineWidth = 1;
      for (let x = 0; x <= width; x += 20) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
      }
      for (let y = 0; y <= height; y += 20) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
      }
    }

    function drawPath(ctx) {
      const a = worldToPixel(state.pose.x, state.pose.y);
      const b = worldToPixel(state.goal.x, state.goal.y);
      ctx.strokeStyle = '#e9b44c';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
      ctx.setLineDash([]);
    }

    function drawGoal(ctx) {
      const g = worldToPixel(state.goal.x, state.goal.y);
      ctx.strokeStyle = '#0f8b8d';
      ctx.lineWidth = 3;
      ctx.beginPath(); ctx.arc(g.x, g.y, 7, 0, Math.PI * 2); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(g.x - 10, g.y); ctx.lineTo(g.x + 10, g.y); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(g.x, g.y - 10); ctx.lineTo(g.x, g.y + 10); ctx.stroke();
    }

    function drawRobot(ctx) {
      const p = worldToPixel(state.pose.x, state.pose.y);
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(-state.pose.yaw);
      ctx.fillStyle = '#c44536';
      ctx.strokeStyle = '#111817';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(12, 0);
      ctx.lineTo(-8, -7);
      ctx.lineTo(-5, 0);
      ctx.lineTo(-8, 7);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      ctx.restore();
    }

    async function refreshStatus() {
      const data = await api(`/api/sim/status?scenario=${encodeURIComponent(state.scenario)}`);
      $('simClock').textContent = `${data.sim_time.toFixed(1)}s`;
      $('linearSpeed').textContent = data.chassis.current_linear.toFixed(2);
      $('angularSpeed').textContent = data.chassis.current_angular.toFixed(2);
      updateScenarioText(data);
      updateDiagnostics(data);
      updateChassis(data);
      updateEvents(data.events);
      if (!state.frozen) {
        state.pose = data.pose;
        state.goal = data.goal;
        draw();
      }
    }

    function updateScenarioText(data) {
      const nav = data.nav2;
      setBadge($('navBadge'), nav.state, nav.ok ? 'ok' : 'warn');
      $('localization').textContent = data.localization.summary;
      $('tfChain').textContent = data.tf.summary;
      $('navAction').textContent = nav.summary;
      $('scanState').textContent = data.scan.summary;
    }

    function updateDiagnostics(data) {
      const checks = [
        data.scan,
        data.tf,
        data.localization,
        data.nav2,
        data.costmap,
        data.chassis_check,
      ];
      $('diagList').innerHTML = checks.map(item => `
        <div class="diag">
          <strong>${item.name}</strong>
          <span>${item.summary}</span>
          <b class="badge ${item.ok ? 'ok' : 'warn'}">${item.ok ? 'PASS' : 'CHECK'}</b>
        </div>
      `).join('');
    }

    function updateChassis(data) {
      const c = data.chassis;
      setBadge($('chassisBadge'), c.control_authorized ? '已授权' : '安全待机', c.control_authorized ? 'warn' : 'ok');
      $('bridgeState').textContent = c.bridge_state;
      $('controlAuth').textContent = String(c.control_authorized);
      $('estop').textContent = c.emergency_stop ? '开启' : '解除';
      $('throttlePwm').textContent = `${c.rc.pwm_min}/${c.rc.pwm_mid}/${c.rc.pwm_max}`;
      $('steeringPwm').textContent = `${c.rc.steering_pwm_min}/${c.rc.steering_pwm_mid}/${c.rc.steering_pwm_max}`;
      $('speedLimit').textContent = `linear=${c.max_linear_speed} angular=${c.max_angular_speed}`;
    }

    function updateEvents(events) {
      $('events').innerHTML = events.map(item => `
        <div class="event"><b>${item.time}</b>${item.text}</div>
      `).join('');
    }

    function bindUi() {
      document.querySelectorAll('.tabs button').forEach(button => {
        button.addEventListener('click', () => {
          document.querySelectorAll('.tabs button').forEach(b => b.classList.remove('active'));
          document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
          button.classList.add('active');
          $(`page-${button.dataset.page}`).classList.add('active');
          draw();
        });
      });
      $('scenario').addEventListener('change', event => {
        state.scenario = event.target.value;
        refreshStatus();
      });
      $('resetPose').addEventListener('click', () => {
        state.pose = { x: 0, y: 0, yaw: -0.15 };
        state.t0 = performance.now();
        draw();
      });
      $('freeze').addEventListener('click', () => {
        state.frozen = !state.frozen;
        $('freeze').textContent = state.frozen ? '继续模拟' : '暂停模拟';
      });
      window.addEventListener('resize', draw);
    }

    bindUi();
    loadMaps().catch(error => {
      console.error(error);
      setBadge($('mapBadge'), '地图失败', 'bad');
    });
    refreshStatus();
    setInterval(refreshStatus, 1000);
    requestAnimationFrame(function loop() {
      if (!state.frozen) draw();
      requestAnimationFrame(loop);
    });
  </script>
</body>
</html>
"""


def parse_simple_yaml(path: Path) -> dict:
    data = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            data[key.strip()] = [
                float(item.strip()) for item in value[1:-1].split(",") if item.strip()
            ]
        else:
            try:
                data[key.strip()] = float(value) if "." in value else int(value)
            except ValueError:
                data[key.strip()] = value.strip("'\"")
    return data


def list_maps() -> list[dict]:
    maps = []
    for path in sorted(MAPS_DIR.glob("*.yaml")):
        maps.append({"name": path.stem, "yaml": path.name})
    return maps


def build_map_payload(name: str | None) -> dict:
    yaml_path = MAPS_DIR / (name or DEFAULT_MAP.name)
    yaml_path = yaml_path.resolve()
    if not str(yaml_path).startswith(str(MAPS_DIR.resolve())) or not yaml_path.exists():
        yaml_path = DEFAULT_MAP
    meta = parse_simple_yaml(yaml_path)
    image_name = str(meta.get("image", "")).strip()
    image_path = (yaml_path.parent / image_name).resolve()
    if not str(image_path).startswith(str(MAPS_DIR.resolve())) or not image_path.exists():
        raise FileNotFoundError(f"map image not found: {image_name}")
    return {
        "name": yaml_path.stem,
        "yaml": yaml_path.name,
        "image": image_path.name,
        "image_url": f"/maps/{image_path.name}",
        "resolution": float(meta.get("resolution", 0.05)),
        "origin": meta.get("origin", [0.0, 0.0, 0.0]),
        "mode": meta.get("mode", "trinary"),
        "occupied_thresh": float(meta.get("occupied_thresh", 0.65)),
        "free_thresh": float(meta.get("free_thresh", 0.25)),
    }


def simulated_status(scenario: str) -> dict:
    now = time.time()
    t = now % 120.0
    x = 0.25 + 0.7 * math.sin(t / 18.0)
    y = 0.12 + 0.42 * math.sin(t / 23.0)
    yaw = math.sin(t / 11.0) * 0.8
    goal = {"x": 1.15, "y": 0.55}
    base = {
        "sim_time": t,
        "pose": {"x": x, "y": y, "yaw": yaw},
        "goal": goal,
        "scan": {"name": "/scan", "ok": True, "summary": "10Hz stable, frame=laser, min_range=0.35m"},
        "tf": {"name": "TF", "ok": True, "summary": "map -> odom -> base_link -> laser"},
        "localization": {
            "name": "Cartographer",
            "ok": True,
            "summary": "localization mode, pose confidence nominal",
        },
        "nav2": {"name": "Nav2", "ok": True, "state": "READY", "summary": "/navigate_to_pose available"},
        "costmap": {"name": "Costmap", "ok": True, "summary": "local inflation=0.25m, obstacle_min_range=0.35m"},
        "chassis_check": {"name": "Chassis", "ok": True, "summary": "bridge online, offline control disabled"},
        "chassis": {
            "bridge_state": "offline simulation",
            "control_authorized": False,
            "emergency_stop": False,
            "current_linear": 0.03 + 0.01 * math.sin(t / 5.0),
            "current_angular": 0.08 * math.sin(t / 7.0),
            "max_linear_speed": 0.05,
            "max_angular_speed": 0.15,
            "rc": {
                "pwm_min": 1435,
                "pwm_mid": 1500,
                "pwm_max": 1565,
                "steering_pwm_min": 1370,
                "steering_pwm_mid": 1500,
                "steering_pwm_max": 1630,
            },
        },
        "events": [
            {"time": "T+00", "text": "加载离线地图和模拟 TF 链。"},
            {"time": "T+04", "text": "模拟 /scan 点云进入局部代价地图。"},
            {"time": "T+08", "text": "Nav2 等待短距离目标点。"},
        ],
    }
    if scenario == "mapping":
        base["nav2"] = {"name": "Nav2", "ok": False, "state": "SLAM", "summary": "建图模式下先不发送 Nav2 goal"}
        base["localization"]["summary"] = "Cartographer mapping, submap list updating"
        base["events"].insert(0, {"time": "SLAM", "text": "模拟 Cartographer 子图持续增长。"})
    elif scenario == "tf_delay":
        base["tf"] = {"name": "TF", "ok": False, "summary": "laser message queue may drop when TF is delayed"}
        base["events"].insert(0, {"time": "WARN", "text": "模拟 RViz Message Filter queue full。"})
    elif scenario == "blocked":
        base["costmap"] = {"name": "Costmap", "ok": False, "summary": "local obstacle layer dense near robot body"}
        base["nav2"] = {"name": "Nav2", "ok": False, "state": "BLOCKED", "summary": "planner ready, controller not committing motion"}
        base["events"].insert(0, {"time": "BLOCK", "text": "模拟车身附近代价过高，路径被挤压。"})
    elif scenario == "chassis_safe":
        base["chassis_check"] = {"name": "Chassis", "ok": False, "summary": "control_authorized=false, test is intentionally safe"}
        base["chassis"]["control_authorized"] = False
        base["chassis"]["current_linear"] = 0.0
        base["chassis"]["current_angular"] = 0.0
        base["events"].insert(0, {"time": "SAFE", "text": "底盘未授权，Web 只显示状态。"})
    return base


class OfflineDashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format_text: str, *args) -> None:
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            if path == "/":
                self.write_bytes(INDEX_HTML.encode("utf-8"), "text/html; charset=utf-8")
                return
            if path == "/api/health":
                self.write_json({"ok": True, "mode": "offline"})
                return
            if path == "/api/maps":
                maps = list_maps()
                self.write_json({"maps": maps, "default_map": DEFAULT_MAP.name})
                return
            if path == "/api/map":
                query = dict(
                    item.split("=", 1) for item in parsed.query.split("&") if "=" in item
                )
                self.write_json(build_map_payload(unquote(query.get("name", "")) or None))
                return
            if path == "/api/sim/status":
                query = dict(
                    item.split("=", 1) for item in parsed.query.split("&") if "=" in item
                )
                self.write_json(simulated_status(unquote(query.get("scenario", "normal"))))
                return
            if path.startswith("/maps/"):
                self.serve_map(path.removeprefix("/maps/"))
                return
            self.write_json({"message": "not found"}, status=404)
        except Exception as exc:
            self.write_json({"message": str(exc)}, status=500)

    def serve_map(self, name: str) -> None:
        target = (MAPS_DIR / unquote(name)).resolve()
        if not str(target).startswith(str(MAPS_DIR.resolve())) or not target.exists():
            self.write_json({"message": "map file not found"}, status=404)
            return
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.write_bytes(target.read_bytes(), content_type)

    def write_json(self, payload: dict, status: int = 200) -> None:
        self.write_bytes(
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
            status,
        )

    def write_bytes(self, data: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the offline robot dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8086)
    args = parser.parse_args()
    if not MAPS_DIR.exists():
        raise SystemExit(f"maps directory not found: {MAPS_DIR}")
    server = ThreadingHTTPServer((args.host, args.port), OfflineDashboardHandler)
    print(f"Offline dashboard: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
