param(
    [string]$HostName = "192.168.31.125",
    [string]$UserName = "elf",
    [string]$Password = "elf",
    [string]$PuttyDir = "D:\Program Files\PuTTY"
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Plink = Join-Path $PuttyDir "plink.exe"
$Pscp = Join-Path $PuttyDir "pscp.exe"

$LocalFiles = @{
    "dashboard_navigation.py" = Join-Path $Root "dashboard_navigation.py"
    "dashboard_http.py" = Join-Path $Root "dashboard_http.py"
    "web_dashboard_node.py" = Join-Path $Root "web_dashboard_node_rk3588.py"
}

foreach ($tool in @($Plink, $Pscp)) {
    if (-not (Test-Path $tool)) {
        throw "PuTTY tool not found: $tool"
    }
}

foreach ($item in $LocalFiles.GetEnumerator()) {
    if (-not (Test-Path $item.Value)) {
        throw "Local file not found: $($item.Value)"
    }
}

$RemoteUpload = "/tmp/medicine_web_dashboard_navigation_upload"
$RemoteInstall = "/tmp/install_navigation_web_dashboard.sh"
$Target = "${UserName}@${HostName}"

Write-Host "[1/5] Preparing remote upload directory on $Target ..."
& $Plink -batch -ssh $Target -pw $Password "mkdir -p $RemoteUpload"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to prepare remote upload directory. Is the RK3588 online?"
}

Write-Host "[2/5] Uploading navigation web files ..."
foreach ($item in $LocalFiles.GetEnumerator()) {
    $remotePath = "${Target}:${RemoteUpload}/$($item.Key)"
    & $Pscp -batch -pw $Password $item.Value $remotePath
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upload $($item.Value)"
    }
}

$InstallScript = @'
#!/usr/bin/env bash
set -eo pipefail

WS=/mnt/sdcard/medicine_robot_ws
PKG_SRC="${WS}/src/medicine_web_dashboard/medicine_web_dashboard"
UPLOAD=/tmp/medicine_web_dashboard_navigation_upload
BACKUP_ROOT=/mnt/sdcard/medicine_robot_data/backups
BACKUP="${BACKUP_ROOT}/web_navigation_$(date +%Y%m%d_%H%M%S)"

if [ ! -d "${PKG_SRC}" ]; then
  echo "ERROR: package source not found: ${PKG_SRC}" >&2
  exit 2
fi

mkdir -p "${BACKUP}"
for file in dashboard_navigation.py dashboard_http.py web_dashboard_node.py; do
  if [ -f "${PKG_SRC}/${file}" ]; then
    cp -f "${PKG_SRC}/${file}" "${BACKUP}/${file}"
  fi
done

install -m 0644 "${UPLOAD}/dashboard_navigation.py" "${PKG_SRC}/dashboard_navigation.py"
install -m 0644 "${UPLOAD}/dashboard_http.py" "${PKG_SRC}/dashboard_http.py"
install -m 0644 "${UPLOAD}/web_dashboard_node.py" "${PKG_SRC}/web_dashboard_node.py"

python3 -m py_compile \
  "${PKG_SRC}/dashboard_navigation.py" \
  "${PKG_SRC}/dashboard_http.py" \
  "${PKG_SRC}/web_dashboard_node.py"

cd "${WS}"
source /opt/ros/humble/setup.bash
colcon build --packages-select medicine_web_dashboard

source "${WS}/install/setup.bash"

if [ -x /mnt/sdcard/rk3588_delivery_webctl.sh ]; then
  /mnt/sdcard/rk3588_delivery_webctl.sh restart
else
  pkill -f "medicine_web_dashboard.*web_dashboard_node" || true
  nohup ros2 run medicine_web_dashboard web_dashboard_node \
    > /tmp/medicine_web_dashboard.log 2>&1 < /dev/null &
  sleep 3
fi

if curl -fsS http://127.0.0.1:8085/api/health >/dev/null; then
  PORT=8085
elif curl -fsS http://127.0.0.1:8080/api/health >/dev/null; then
  PORT=8080
else
  echo "ERROR: dashboard health check failed on 8085 and 8080" >&2
  exit 3
fi

curl -fsS "http://127.0.0.1:${PORT}/navigation" >/dev/null
curl -fsS "http://127.0.0.1:${PORT}/api/navigation/snapshot" >/dev/null

echo "OK: navigation dashboard deployed"
echo "PORT=${PORT}"
echo "BACKUP=${BACKUP}"
'@

$TempInstall = Join-Path $env:TEMP "install_navigation_web_dashboard.sh"
[System.IO.File]::WriteAllText(
    $TempInstall,
    $InstallScript,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Host "[3/5] Uploading remote install script ..."
& $Pscp -batch -pw $Password $TempInstall "${Target}:${RemoteInstall}"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to upload remote install script"
}

Write-Host "[4/5] Installing, building, and restarting web dashboard ..."
& $Plink -batch -ssh $Target -pw $Password "chmod +x $RemoteInstall && bash $RemoteInstall"
if ($LASTEXITCODE -ne 0) {
    throw "Remote install failed"
}

Write-Host "[5/5] Done."
Write-Host "Open: http://${HostName}:8085/navigation"
Write-Host "If 8085 is not used on your board, check the PORT line printed above."
