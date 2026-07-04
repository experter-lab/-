[CmdletBinding()]
param(
    [string]$BoardHost = "192.168.31.126",
    [string]$BoardUser = "elf",
    [string]$BoardPassword = "elf",
    [string]$PuttyDir = "D:\Program Files\PuTTY",
    [string]$OutputRoot = "D:\A1\backups",
    [switch]$SkipPrivate
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$plink = Join-Path $PuttyDir "plink.exe"
$pscp = Join-Path $PuttyDir "pscp.exe"

if (-not (Test-Path -LiteralPath $plink)) { throw "plink not found: $plink" }
if (-not (Test-Path -LiteralPath $pscp)) { throw "pscp not found: $pscp" }

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupDir = Join-Path $OutputRoot "rk3588-state-$stamp"
$boardDir = Join-Path $backupDir "board"
$localDir = Join-Path $backupDir "local"
New-Item -ItemType Directory -Force -Path $boardDir, $localDir | Out-Null

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$Exe,
        [Parameter(Mandatory = $true)][string[]]$Args,
        [Parameter(Mandatory = $true)][string]$Label
    )
    Write-Host "==> $Label"
    & $Exe @Args
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

$remoteWorkDir = "/tmp/rk3588_backup_$stamp"
$remoteScript = "/tmp/rk3588_make_backup_$stamp.sh"
$remoteScriptLocal = Join-Path $backupDir "rk3588_make_backup_$stamp.sh"

$skipPrivateValue = if ($SkipPrivate) { "1" } else { "0" }
$scriptTemplate = @'
#!/usr/bin/env bash
set -u

STAMP="__STAMP__"
OUT="/tmp/rk3588_backup_${STAMP}"
SKIP_PRIVATE="__SKIP_PRIVATE__"

mkdir -p "$OUT/lists"

add_paths() {
  local list="$1"
  shift
  local p
  for p in "$@"; do
    if [ -e "$p" ]; then
      printf '%s\n' "${p#/}" >> "$list"
    fi
  done
}

make_tar() {
  local name="$1"
  local list="$2"
  if [ -s "$list" ]; then
    tar --warning=no-file-changed --ignore-failed-read -czf "$OUT/${name}.tar.gz" -C / -T "$list" >/dev/null 2>"$OUT/${name}.tar.stderr" || true
  else
    printf 'No existing paths for %s\n' "$name" > "$OUT/${name}.empty.txt"
  fi
}

code_list="$OUT/lists/code-runtime.txt"
data_list="$OUT/lists/data.txt"
systemd_list="$OUT/lists/systemd.txt"
logs_list="$OUT/lists/logs.txt"
private_list="$OUT/lists/private.txt"

add_paths "$code_list" \
  /mnt/sdcard/medicine_robot_ws/src \
  /mnt/sdcard/medicine_robot_ws/build \
  /mnt/sdcard/medicine_robot_ws/install \
  /mnt/sdcard/rk3588_start_m2_voice.sh \
  /mnt/sdcard/rk3588_delivery_webctl.sh \
  /mnt/sdcard/rk3588_start_vision_drug.sh \
  /mnt/sdcard/rk3588_start_lidar.sh \
  /mnt/sdcard/rk3588_start_nav2_carto.sh \
  /mnt/sdcard/rk3588_start_carto_mapping.sh \
  /mnt/sdcard/rk3588_start_carto_localization.sh \
  /mnt/sdcard/rk3588_start_localization_only.sh \
  /mnt/sdcard/rk3588_clean_nav_runtime.sh \
  /mnt/sdcard/rk3588_save_carto_map.sh

for p in /mnt/sdcard/rk3588_*.sh /mnt/sdcard/*medicine*.sh /mnt/sdcard/*voice*.sh; do
  [ -e "$p" ] && printf '%s\n' "${p#/}" >> "$code_list"
done

add_paths "$data_list" \
  /mnt/sdcard/medicine_robot_data \
  /home/elf/.local/share/medicine_robot

for p in /etc/systemd/system/rk3588*.service /etc/systemd/system/medicine*.service /etc/systemd/system/*voice*.service /etc/systemd/system/*dashboard*.service /lib/systemd/system/rk3588*.service /lib/systemd/system/medicine*.service; do
  [ -e "$p" ] && printf '%s\n' "${p#/}" >> "$systemd_list"
done

for p in /tmp/rk3588_* /tmp/*voice* /tmp/*dashboard* /tmp/*asr* /tmp/*vision* /tmp/*medicine*; do
  [ -e "$p" ] || continue
  case "$p" in
    /tmp/rk3588_backup_*|/tmp/rk3588_restore_*|/tmp/rk3588_make_backup_*.sh) continue ;;
  esac
  printf '%s\n' "${p#/}" >> "$logs_list"
done

if [ "$SKIP_PRIVATE" != "1" ]; then
  add_paths "$private_list" \
    /mnt/sdcard/medicine_robot_data/.env \
    /mnt/sdcard/medicine_robot_data/env \
    /mnt/sdcard/medicine_robot_data/keys \
    /mnt/sdcard/iflytek_tts_df41b4a2 \
    /mnt/sdcard/iflytek_tts_sdk \
    /home/elf/.config/medicine_robot \
    /home/elf/.dashscope \
    /home/elf/.bashrc \
    /home/elf/.profile
fi

sort -u -o "$code_list" "$code_list" 2>/dev/null || true
sort -u -o "$data_list" "$data_list" 2>/dev/null || true
sort -u -o "$systemd_list" "$systemd_list" 2>/dev/null || true
sort -u -o "$logs_list" "$logs_list" 2>/dev/null || true
sort -u -o "$private_list" "$private_list" 2>/dev/null || true

make_tar "rk3588-code-runtime" "$code_list"
make_tar "rk3588-data" "$data_list"
make_tar "rk3588-systemd" "$systemd_list"
make_tar "rk3588-logs" "$logs_list"
if [ "$SKIP_PRIVATE" != "1" ]; then
  make_tar "rk3588-private" "$private_list"
fi

{
  echo "# RK3588 backup manifest"
  echo
  echo "[time]"
  date -Is
  echo
  echo "[host]"
  hostname
  uname -a
  echo
  echo "[network]"
  ip addr
  echo
  echo "[disk]"
  df -h
  echo
  echo "[audio]"
  arecord -l 2>&1 || true
  aplay -l 2>&1 || true
  echo
  echo "[camera]"
  ls -l /dev/video* 2>&1 || true
  v4l2-ctl --list-devices 2>&1 || true
  echo
  echo "[python]"
  python3 --version 2>&1 || true
  echo
  echo "[process]"
  ps -eo pid,ppid,stat,cmd --sort=cmd | grep -E 'medicine|rk3588|voice|asr|tts|vision|dashboard|ros2|chassis|nav2|carto' | grep -v grep || true
  echo
  echo "[systemd]"
  systemctl list-units --type=service --all 2>/dev/null | grep -E 'medicine|rk3588|voice|dashboard|vision|chassis' || true
  echo
  echo "[web-health]"
  curl -sS --max-time 3 http://127.0.0.1:8085/api/health 2>&1 || true
  echo
  curl -sS --max-time 3 http://127.0.0.1:8085/api/chassis_status 2>&1 || true
  echo
  curl -sS --max-time 3 http://127.0.0.1:8085/api/drug_info 2>&1 | head -c 4000 || true
  echo
  echo "[ros2-nodes]"
  if [ -f /opt/ros/humble/setup.bash ]; then
    set +u
    . /opt/ros/humble/setup.bash
    ros2 node list 2>&1 || true
    ros2 topic list 2>&1 || true
    set -u
  fi
} > "$OUT/manifest.txt" 2>&1

(
  cd "$OUT" || exit 0
  sha256sum *.tar.gz 2>/dev/null > SHA256SUMS.txt || true
  find . -maxdepth 2 -type f -printf '%p\t%s bytes\n' | sort > FILES.txt
)

echo "$OUT"
'@

$remoteScriptContent = $scriptTemplate.Replace("__STAMP__", $stamp).Replace("__SKIP_PRIVATE__", $skipPrivateValue)
[System.IO.File]::WriteAllText($remoteScriptLocal, $remoteScriptContent, [System.Text.UTF8Encoding]::new($false))

Invoke-Checked -Exe $pscp -Args @("-batch", "-scp", "-pw", $BoardPassword, $remoteScriptLocal, "${BoardUser}@${BoardHost}:$remoteScript") -Label "upload remote backup script"
Invoke-Checked -Exe $plink -Args @("-batch", "-ssh", "${BoardUser}@${BoardHost}", "-pw", $BoardPassword, "chmod +x $remoteScript && bash $remoteScript") -Label "create board backup archives"
Invoke-Checked -Exe $pscp -Args @("-batch", "-r", "-pw", $BoardPassword, "${BoardUser}@${BoardHost}:$remoteWorkDir", $boardDir) -Label "download board backup archives"

$localPaths = New-Object System.Collections.Generic.List[string]
foreach ($relative in @("board_sync", "docs", "tools", ".codex")) {
    $path = Join-Path $repoRoot $relative
    if (Test-Path -LiteralPath $path) { $localPaths.Add($path) }
}
Get-ChildItem -LiteralPath $repoRoot -File | Where-Object {
    $_.Name -like "rk3588_*" -or
    $_.Name -in @("AGENTS.md", "dashboard_assets.py", "dashboard_delivery_batch.py", "web_dashboard_node.py", "dashboard_http.py")
} | ForEach-Object { $localPaths.Add($_.FullName) }

$localZip = Join-Path $localDir "local-a1-project-$stamp.zip"
if ($localPaths.Count -gt 0) {
    Compress-Archive -Path $localPaths.ToArray() -DestinationPath $localZip -Force
}

$readme = @"
# RK3588 state backup

Created: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Board: $BoardUser@$BoardHost

Contents:
- board/rk3588_backup_$stamp/: archives downloaded from the RK3588 board.
- local/local-a1-project-$stamp.zip: selected local repository snapshot.

Sensitive:
- rk3588-data.tar.gz can contain patient/batch/runtime data.
- rk3588-private.tar.gz can contain API keys or local credentials when SkipPrivate is not used.

Restore quick start:
1. Confirm the board is reachable.
2. Run:
   powershell -ExecutionPolicy Bypass -File tools/restore-rk3588-state.ps1 -BackupDir "$backupDir"
3. Add -RestoreData only when you intentionally want to overwrite board runtime data.
4. Add -RestorePrivate only on the same trusted board/user environment.
"@
[System.IO.File]::WriteAllText((Join-Path $backupDir "RESTORE-README.md"), $readme, [System.Text.UTF8Encoding]::new($false))

Write-Host
Write-Host "Backup complete:"
Write-Host $backupDir
