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
$LocalPackage = Join-Path $Root "board_sync\m2_voice_opt_20260609"
$Target = "${UserName}@${HostName}"
$RemoteUpload = "/tmp/m2_voice_opt_20260609"

foreach ($tool in @($Plink, $Pscp)) {
    if (-not (Test-Path $tool)) {
        throw "PuTTY tool not found: $tool"
    }
}
foreach ($path in @($LocalPackage, (Join-Path $LocalPackage "apply_on_board.py"))) {
    if (-not (Test-Path $path)) {
        throw "Required local path not found: $path"
    }
}

Get-ChildItem -Path $LocalPackage -Directory -Recurse -Filter "__pycache__" |
    Remove-Item -Recurse -Force

Write-Host "[1/5] Preparing upload directory on $Target ..."
& $Plink -batch -ssh $Target -pw $Password "rm -rf $RemoteUpload && mkdir -p $RemoteUpload"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to prepare remote upload directory. Is the RK3588 online?"
}

Write-Host "[2/5] Uploading M2 voice/TTS package ..."
& $Pscp -batch -r -pw $Password "$LocalPackage\*" "${Target}:${RemoteUpload}/"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to upload M2 voice/TTS package"
}

$RemoteInstall = @'
set -eo pipefail

WS=/mnt/sdcard/medicine_robot_ws
UPLOAD=/tmp/m2_voice_opt_20260609

if [ ! -d "${WS}/src" ]; then
  echo "ERROR: workspace source directory not found: ${WS}/src" >&2
  exit 2
fi

python3 "${UPLOAD}/apply_on_board.py"

cd "${WS}"
source /opt/ros/humble/setup.bash

rm -rf "${WS}/build/medicine_robot_bringup" "${WS}/install/medicine_robot_bringup"
colcon build --packages-select medicine_voice_interaction medicine_robot_bringup --symlink-install
source "${WS}/install/setup.bash"

echo "[check] package executables:"
ros2 pkg executables medicine_voice_interaction

echo "[check] local audio tools:"
for cmd in pico2wave aplay espeak-ng espeak spd-say; do
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "  OK $cmd=$(command -v "$cmd")"
  else
    echo "  missing $cmd"
  fi
done

if pgrep -af "ros2 run medicine_voice_interaction voice_console_node|medicine_voice_interaction/lib/medicine_voice_interaction/voice_console_node" >/tmp/voice_console_pids.txt 2>/dev/null; then
  awk '{print $1}' /tmp/voice_console_pids.txt | while read -r pid; do
    if [ -n "$pid" ] && [ "$pid" != "$$" ]; then
      kill "$pid" 2>/dev/null || true
    fi
  done
  sleep 1
fi
nohup ros2 run medicine_voice_interaction voice_console_node --ros-args \
  -p voice_topic:=/medicine/voice_text \
  -p enable_tts:=true \
  -p tts_backend:=auto \
  > /tmp/medicine_voice_console.log 2>&1 < /dev/null &

sleep 2
python3 - <<'PY'
import rclpy
from std_msgs.msg import String

rclpy.init()
node = rclpy.create_node("m2_voice_tts_smoke_pub")
pub = node.create_publisher(String, "/medicine/voice_text", 10)
msg = String()
msg.data = "\u8bed\u97f3\u64ad\u62a5\u6d4b\u8bd5\uff0cRK3588 \u5df2\u63a5\u5165 M2 \u8bed\u97f3\u64ad\u62a5"
deadline = node.get_clock().now().nanoseconds + 800_000_000
while pub.get_subscription_count() == 0 and node.get_clock().now().nanoseconds < deadline:
    rclpy.spin_once(node, timeout_sec=0.1)
pub.publish(msg)
rclpy.spin_once(node, timeout_sec=0.2)
node.destroy_node()
rclpy.shutdown()
PY
sleep 2

echo "[check] voice log:"
tail -40 /tmp/medicine_voice_console.log || true

echo "OK: M2 voice/TTS bridge deployed"
'@

$TempInstall = Join-Path $env:TEMP "install_m2_voice_tts.sh"
[System.IO.File]::WriteAllText(
    $TempInstall,
    $RemoteInstall,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Host "[3/5] Uploading remote install script ..."
& $Pscp -batch -pw $Password $TempInstall "${Target}:/tmp/install_m2_voice_tts.sh"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to upload remote install script"
}

Write-Host "[4/5] Installing, building, and running voice smoke test ..."
& $Plink -batch -ssh $Target -pw $Password "chmod +x /tmp/install_m2_voice_tts.sh && bash /tmp/install_m2_voice_tts.sh"
if ($LASTEXITCODE -ne 0) {
    throw "Remote M2 voice/TTS install failed"
}

Write-Host "[5/5] Done."
Write-Host "Voice log on RK3588: /tmp/medicine_voice_console.log"
Write-Host "Manual test:"
Write-Host "  ros2 topic pub --once /medicine/voice_text std_msgs/msg/String `"{data: '测试语音播报'}`""
