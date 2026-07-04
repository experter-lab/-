"""Navigation map page and helpers for the RK3588 web dashboard."""

from __future__ import annotations

from pathlib import Path


NAVIGATION_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>RK3588 导航状态</title>
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
        radial-gradient(circle at 18% 12%, rgba(15, 139, 141, 0.22), transparent 30%),
        var(--bg);
      font-family: var(--sans);
      letter-spacing: 0;
    }
    button, select { font: inherit; }
    button, select {
      border: 1px solid var(--line);
      border-radius: 6px;
      min-height: 38px;
      padding: 0 12px;
      background: #fffaf0;
      color: var(--ink);
    }
    button {
      cursor: pointer;
      background: var(--ink);
      color: #fffaf0;
      border-color: var(--ink);
    }
    button.secondary {
      background: transparent;
      color: var(--ink);
      border-color: var(--line);
    }
    .shell {
      width: min(1480px, calc(100vw - 28px));
      margin: 14px auto;
      display: grid;
      grid-template-columns: 320px minmax(0, 1fr);
      gap: 14px;
    }
    .rail, .panel, .card {
      background: var(--panel);
      border: 1px solid var(--line);
      box-shadow: 0 26px 70px rgba(0, 0, 0, 0.24);
    }
    .rail {
      min-height: calc(100vh - 28px);
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
      margin: 0;
      font-size: 25px;
      line-height: 1.08;
    }
    .brand p {
      color: var(--muted);
      margin: 8px 0 0;
      font-size: 13px;
      line-height: 1.45;
    }
    .meters {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .meter {
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.34);
      min-height: 78px;
      padding: 10px;
    }
    .meter span {
      display: block;
      color: var(--muted);
      font-size: 12px;
    }
    .meter strong {
      display: block;
      margin-top: 7px;
      font: 700 18px/1 var(--mono);
      overflow-wrap: anywhere;
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
    .panel {
      min-height: calc(100vh - 28px);
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
    .grid {
      display: grid;
      grid-template-columns: minmax(0, 1.45fr) minmax(330px, 0.75fr);
      gap: 14px;
    }
    .card {
      box-shadow: none;
      border-radius: 8px;
      padding: 14px;
    }
    .card h3 {
      margin: 0 0 12px;
      font-size: 15px;
      display: flex;
      align-items: center;
      justify-content: space-between;
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
      right: 14px;
      bottom: 14px;
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
      pointer-events: none;
    }
    .hud-cell {
      background: rgba(244,241,232,0.9);
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
    .stack { display: grid; gap: 14px; }
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
    .diag-list {
      display: grid;
      gap: 8px;
    }
    .diag {
      display: grid;
      grid-template-columns: 82px minmax(0, 1fr) auto;
      gap: 10px;
      align-items: center;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.32);
      padding: 10px;
    }
    .diag strong { font-size: 13px; }
    .diag span {
      color: var(--muted);
      font: 12px/1.35 var(--mono);
    }
    .notice {
      border-left: 4px solid var(--accent);
      background: rgba(15, 139, 141, 0.08);
      padding: 10px 12px;
      color: #384340;
      font-size: 13px;
      line-height: 1.5;
    }
    @media (max-width: 980px) {
      .shell, .grid { grid-template-columns: 1fr; }
      .rail { min-height: 0; }
      .map-hud { grid-template-columns: 1fr 1fr; }
    }
    @media (max-width: 620px) {
      .shell { width: calc(100vw - 16px); margin: 8px auto; }
      .map-frame { min-height: 440px; }
      canvas { height: 440px; }
      .map-hud { grid-template-columns: 1fr; }
      .diag { grid-template-columns: 1fr auto; }
      .diag span { grid-column: 1 / -1; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside class="rail">
      <div class="brand">
        <h1>RK3588 导航状态</h1>
        <p>这个页面读取真实 ROS 状态和保存地图。没有小车时会显示未收到数据，不使用假运行状态。</p>
      </div>
      <div class="meters">
        <div class="meter"><span>页面模式</span><strong>REAL</strong></div>
        <div class="meter"><span>状态时间</span><strong id="statusAge">-</strong></div>
        <div class="meter"><span>线速度</span><strong id="linearSpeed">-</strong></div>
        <div class="meter"><span>角速度</span><strong id="angularSpeed">-</strong></div>
      </div>
      <div>
        <label for="mapSelect">地图文件</label>
        <select id="mapSelect"></select>
      </div>
      <button id="reload" type="button">刷新状态</button>
      <button id="fitMap" class="secondary" type="button">重绘地图</button>
      <button id="exportSnapshot" class="secondary" type="button">导出诊断快照</button>
      <div class="notice">安全边界：此页只读状态，不发送 /cmd_vel，不调用 Nav2 Goal，不操作授权和急停。</div>
    </aside>

    <main class="panel">
      <div class="topbar">
        <h2>地图、定位与导航诊断</h2>
        <span id="overallBadge" class="badge warn">等待数据</span>
      </div>
      <div class="grid">
        <section class="card">
          <h3>实车地图视图 <span id="mapBadge" class="badge cold">未加载</span></h3>
          <div class="map-frame">
            <canvas id="mapCanvas" width="920" height="620"></canvas>
            <div class="map-hud">
              <div class="hud-cell"><span>地图</span><strong id="mapName">-</strong></div>
              <div class="hud-cell"><span>分辨率</span><strong id="mapResolution">-</strong></div>
              <div class="hud-cell"><span>小车位姿</span><strong id="poseText">未收到 TF</strong></div>
              <div class="hud-cell"><span>任务目标</span><strong id="goalText">-</strong></div>
            </div>
          </div>
        </section>
        <section class="stack">
          <div class="card">
            <h3>实时状态 <span id="navBadge" class="badge warn">未确认</span></h3>
            <div class="kv"><span>定位来源</span><strong id="localization">-</strong></div>
            <div class="kv"><span>TF 链路</span><strong id="tfChain">-</strong></div>
            <div class="kv"><span>Nav2 action</span><strong id="navAction">-</strong></div>
            <div class="kv"><span>雷达</span><strong id="scanState">-</strong></div>
            <div class="kv"><span>底盘</span><strong id="chassisState">-</strong></div>
            <div class="kv"><span>PWM</span><strong id="pwmState">-</strong></div>
          </div>
          <div class="card">
            <h3>启动前检查</h3>
            <div id="diagList" class="diag-list"></div>
          </div>
        </section>
      </div>
    </main>
  </div>

  <script>
    const state = { map: null, mapPixels: null, robotPose: null, target: null };
    const $ = id => document.getElementById(id);

    function setBadge(el, text, cls) {
      el.textContent = text;
      el.className = `badge ${cls}`;
    }

    async function api(path) {
      const response = await fetch(path, { cache: 'no-store', keepalive: true });
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      return response.json();
    }

    async function loadMaps() {
      const data = await api('/api/navigation/maps');
      const select = $('mapSelect');
      select.innerHTML = (data.maps || []).map(item => (
        `<option value="${item.yaml}">${item.name}</option>`
      )).join('');
      if (!data.maps || data.maps.length === 0) {
        setBadge($('mapBadge'), '无地图', 'bad');
        return;
      }
      select.value = data.default_map || data.maps[0].yaml;
      select.addEventListener('change', () => loadMap(select.value));
      await loadMap(select.value);
    }

    async function loadMap(name) {
      setBadge($('mapBadge'), '加载中', 'cold');
      const meta = await api(`/api/navigation/map?name=${encodeURIComponent(name)}`);
      const bytes = await fetch(meta.image_url, { cache: 'force-cache', keepalive: true }).then(r => r.arrayBuffer());
      state.map = meta;
      state.mapPixels = parsePgm(new Uint8Array(bytes));
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
      if (magic !== 'P5' || !width || !height || !maxVal) throw new Error('仅支持 P5 PGM 地图');
      return { width, height, maxVal, pixels };
    }

    function worldToPixel(x, y) {
      const origin = state.map.origin || [0, 0, 0];
      return {
        x: (x - origin[0]) / state.map.resolution,
        y: state.mapPixels.height - (y - origin[1]) / state.map.resolution,
      };
    }

    function draw() {
      const canvas = $('mapCanvas');
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#101615';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      if (!state.map || !state.mapPixels) return;
      const map = state.mapPixels;
      const image = ctx.createImageData(map.width, map.height);
      for (let i = 0; i < map.pixels.length; i++) {
        const value = map.pixels[i];
        const off = i * 4;
        let r = 207, g = 207, b = 207;
        if (value < 80) { r = 18; g = 22; b = 21; }
        else if (value > 235) { r = 250; g = 247; b = 239; }
        image.data[off] = r;
        image.data[off + 1] = g;
        image.data[off + 2] = b;
        image.data[off + 3] = 255;
      }
      const scratch = document.createElement('canvas');
      scratch.width = map.width;
      scratch.height = map.height;
      scratch.getContext('2d').putImageData(image, 0, 0);
      const scale = Math.min(canvas.width / map.width, canvas.height / map.height) * 0.9;
      const ox = (canvas.width - map.width * scale) / 2;
      const oy = (canvas.height - map.height * scale) / 2;
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(scratch, ox, oy, map.width * scale, map.height * scale);
      ctx.save();
      ctx.translate(ox, oy);
      ctx.scale(scale, scale);
      drawGrid(ctx, map.width, map.height);
      if (state.target) drawTarget(ctx, state.target);
      if (state.robotPose) drawRobot(ctx, state.robotPose);
      ctx.restore();
    }

    function drawGrid(ctx, width, height) {
      ctx.strokeStyle = 'rgba(15, 139, 141, 0.16)';
      ctx.lineWidth = 1;
      for (let x = 0; x <= width; x += 20) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
      }
      for (let y = 0; y <= height; y += 20) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
      }
    }

    function drawTarget(ctx, target) {
      const p = worldToPixel(target.x, target.y);
      ctx.strokeStyle = '#0f8b8d';
      ctx.lineWidth = 3;
      ctx.beginPath(); ctx.arc(p.x, p.y, 8, 0, Math.PI * 2); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(p.x - 12, p.y); ctx.lineTo(p.x + 12, p.y); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(p.x, p.y - 12); ctx.lineTo(p.x, p.y + 12); ctx.stroke();
    }

    function drawRobot(ctx, pose) {
      const p = worldToPixel(pose.x, pose.y);
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(-pose.yaw);
      ctx.fillStyle = '#c44536';
      ctx.strokeStyle = '#111817';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(13, 0);
      ctx.lineTo(-9, -8);
      ctx.lineTo(-6, 0);
      ctx.lineTo(-9, 8);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      ctx.restore();
    }

    function boolText(value) {
      return value ? 'true' : 'false';
    }

    async function refreshStatus() {
      if (state.statusInFlight) return;
      state.statusInFlight = true;
      try {
      const data = await api('/api/navigation/status');
      const pose = data.robot_pose && data.robot_pose.ok ? data.robot_pose : null;
      state.robotPose = pose ? { x: pose.x, y: pose.y, yaw: pose.yaw } : null;
      const delivery = data.delivery_state || {};
      state.target = Number.isFinite(Number(delivery.target_x)) ? {
        x: Number(delivery.target_x),
        y: Number(delivery.target_y || 0),
      } : null;
      $('statusAge').textContent = data.generated_at ? new Date(data.generated_at * 1000).toLocaleTimeString() : '-';
      $('linearSpeed').textContent = data.chassis?.current_linear ?? '-';
      $('angularSpeed').textContent = data.chassis?.current_angular ?? '-';
      $('poseText').textContent = pose ? `x=${pose.x.toFixed(2)} y=${pose.y.toFixed(2)} yaw=${pose.yaw.toFixed(2)}` : '未收到 TF';
      $('goalText').textContent = delivery.target_station || '-';
      setBadge($('overallBadge'), data.overall_ok ? '链路可用' : '等待实车数据', data.overall_ok ? 'ok' : 'warn');
      setBadge($('navBadge'), data.nav2?.ok ? 'Nav2 可用' : 'Nav2 未确认', data.nav2?.ok ? 'ok' : 'warn');
      $('localization').textContent = data.localization?.summary || '-';
      $('tfChain').textContent = data.tf?.summary || '-';
      $('navAction').textContent = data.nav2?.summary || '-';
      $('scanState').textContent = data.scan?.summary || '-';
      const chassis = data.chassis || {};
      $('chassisState').textContent = `received=${boolText(Boolean(chassis.received))} auth=${boolText(Boolean(chassis.control_authorized))} estop=${boolText(Boolean(chassis.emergency_stop))}`;
      const rc = chassis.ardupilot?.rc_override || {};
      $('pwmState').textContent = `${rc.pwm_min ?? '-'}/${rc.pwm_mid ?? '-'}/${rc.pwm_max ?? '-'} steering=${rc.steering_pwm_min ?? '-'}/${rc.steering_pwm_mid ?? '-'}/${rc.steering_pwm_max ?? '-'}`;
      const checks = [data.scan, data.tf, data.localization, data.nav2, data.costmap, data.chassis_check];
      $('diagList').innerHTML = checks.map(item => `
        <div class="diag">
          <strong>${item?.name || '-'}</strong>
          <span>${item?.summary || '-'}</span>
          <b class="badge ${item?.ok ? 'ok' : 'warn'}">${item?.ok ? 'PASS' : 'CHECK'}</b>
        </div>
      `).join('');
      draw();
      } finally {
        state.statusInFlight = false;
      }
    }

    async function exportSnapshot() {
      const mapName = $('mapSelect').value || '';
      const snapshot = await api(`/api/navigation/snapshot?map=${encodeURIComponent(mapName)}`);
      const stamp = new Date().toISOString().replace(/[:.]/g, '-');
      const blob = new Blob([JSON.stringify(snapshot, null, 2)], { type: 'application/json;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `rk3588-navigation-snapshot-${stamp}.json`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    }

    $('reload').addEventListener('click', refreshStatus);
    $('fitMap').addEventListener('click', draw);
    $('exportSnapshot').addEventListener('click', () => exportSnapshot().catch(console.error));
    window.addEventListener('resize', draw);
    loadMaps().catch(error => {
      setBadge($('mapBadge'), '地图失败', 'bad');
      console.error(error);
    });
    refreshStatus().catch(console.error);
    setInterval(() => refreshStatus().catch(console.error), 2000);
  </script>
</body>
</html>
"""


def parse_map_yaml(path: Path) -> dict:
    data = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            data[key] = [
                float(item.strip()) for item in value[1:-1].split(",") if item.strip()
            ]
            continue
        try:
            data[key] = float(value) if "." in value else int(value)
        except ValueError:
            data[key] = value.strip("'\"")
    return data


def list_navigation_maps(map_directory: str) -> list[dict]:
    root = Path(map_directory).expanduser()
    if not root.exists():
        return []
    return [
        {"name": path.stem, "yaml": path.name}
        for path in sorted(root.glob("*.yaml"))
        if path.is_file()
    ]


def resolve_navigation_map(map_directory: str, name: str | None) -> Path:
    root = Path(map_directory).expanduser().resolve()
    maps = list_navigation_maps(str(root))
    if not maps:
        raise FileNotFoundError(f"no map yaml files in {root}")
    selected = name or maps[-1]["yaml"]
    candidate = (root / selected).resolve()
    if not str(candidate).startswith(str(root)) or not candidate.exists():
        candidate = (root / maps[-1]["yaml"]).resolve()
    return candidate


def build_navigation_map_payload(map_directory: str, name: str | None) -> dict:
    yaml_path = resolve_navigation_map(map_directory, name)
    meta = parse_map_yaml(yaml_path)
    image_name = str(meta.get("image", "")).strip()
    image_path = (yaml_path.parent / image_name).resolve()
    root = Path(map_directory).expanduser().resolve()
    if not str(image_path).startswith(str(root)) or not image_path.exists():
        raise FileNotFoundError(f"map image not found: {image_name}")
    return {
        "name": yaml_path.stem,
        "yaml": yaml_path.name,
        "image": image_path.name,
        "image_url": f"/navigation/maps/{image_path.name}",
        "resolution": float(meta.get("resolution", 0.05)),
        "origin": meta.get("origin", [0.0, 0.0, 0.0]),
        "mode": meta.get("mode", "trinary"),
        "occupied_thresh": float(meta.get("occupied_thresh", 0.65)),
        "free_thresh": float(meta.get("free_thresh", 0.25)),
    }


def resolve_navigation_map_asset(map_directory: str, file_name: str) -> Path:
    root = Path(map_directory).expanduser().resolve()
    candidate = (root / file_name).resolve()
    if not str(candidate).startswith(str(root)) or not candidate.exists():
        raise FileNotFoundError(file_name)
    return candidate
