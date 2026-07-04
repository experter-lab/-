[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$BackupDir,
    [string]$BoardHost = "192.168.31.126",
    [string]$BoardUser = "elf",
    [string]$BoardPassword = "elf",
    [string]$PuttyDir = "D:\Program Files\PuTTY",
    [switch]$RestoreData,
    [switch]$RestorePrivate,
    [switch]$RestartServices
)

$ErrorActionPreference = "Stop"

$plink = Join-Path $PuttyDir "plink.exe"
$pscp = Join-Path $PuttyDir "pscp.exe"
if (-not (Test-Path -LiteralPath $plink)) { throw "plink not found: $plink" }
if (-not (Test-Path -LiteralPath $pscp)) { throw "pscp not found: $pscp" }

$backupPath = (Resolve-Path -LiteralPath $BackupDir).Path
$boardBackupDir = Get-ChildItem -LiteralPath (Join-Path $backupPath "board") -Directory -Filter "rk3588_backup_*" | Select-Object -First 1
if (-not $boardBackupDir) {
    throw "No board/rk3588_backup_* directory found under $backupPath"
}

$required = Join-Path $boardBackupDir.FullName "rk3588-code-runtime.tar.gz"
if (-not (Test-Path -LiteralPath $required)) {
    throw "Missing required archive: $required"
}

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

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$remoteDir = "/tmp/rk3588_restore_$stamp"
$restoreScript = "/tmp/rk3588_restore_$stamp.sh"
$restoreScriptLocal = Join-Path $backupPath "rk3588_restore_$stamp.sh"

$restoreDataValue = if ($RestoreData) { "1" } else { "0" }
$restorePrivateValue = if ($RestorePrivate) { "1" } else { "0" }
$restartValue = if ($RestartServices) { "1" } else { "0" }

$scriptTemplate = @'
#!/usr/bin/env bash
set -u

IN="__REMOTE_DIR__"
RESTORE_DATA="__RESTORE_DATA__"
RESTORE_PRIVATE="__RESTORE_PRIVATE__"
RESTART_SERVICES="__RESTART_SERVICES__"

extract_if_present() {
  local archive="$1"
  local label="$2"
  if [ -f "$IN/$archive" ]; then
    echo "extracting $label from $archive"
    tar --warning=no-file-changed --ignore-failed-read -xzf "$IN/$archive" -C / || true
  else
    echo "skip missing $archive"
  fi
}

extract_if_present rk3588-code-runtime.tar.gz code-runtime

if [ "$RESTORE_DATA" = "1" ]; then
  extract_if_present rk3588-data.tar.gz data
else
  echo "skip data restore; pass -RestoreData to restore board runtime data"
fi

if [ "$RESTORE_PRIVATE" = "1" ]; then
  extract_if_present rk3588-private.tar.gz private
else
  echo "skip private restore; pass -RestorePrivate to restore credentials/private config"
fi

chmod +x /mnt/sdcard/rk3588_*.sh 2>/dev/null || true

if [ "$RESTART_SERVICES" = "1" ]; then
  if [ -x /mnt/sdcard/rk3588_delivery_webctl.sh ]; then
    /mnt/sdcard/rk3588_delivery_webctl.sh restart || true
  fi
  if [ -x /mnt/sdcard/rk3588_start_vision_drug.sh ]; then
    nohup /mnt/sdcard/rk3588_start_vision_drug.sh >/tmp/rk3588_restore_vision_restart.log 2>&1 &
  fi
  if [ -x /mnt/sdcard/rk3588_start_m2_voice.sh ]; then
    nohup /mnt/sdcard/rk3588_start_m2_voice.sh >/tmp/rk3588_restore_voice_restart.log 2>&1 &
  fi
fi

echo "[verify]"
curl -sS --max-time 3 http://127.0.0.1:8085/api/health 2>&1 || true
echo
curl -sS --max-time 3 http://127.0.0.1:8085/api/chassis_status 2>&1 | head -c 1000 || true
echo
'@

$restoreScriptContent = $scriptTemplate.Replace("__REMOTE_DIR__", $remoteDir).Replace("__RESTORE_DATA__", $restoreDataValue).Replace("__RESTORE_PRIVATE__", $restorePrivateValue).Replace("__RESTART_SERVICES__", $restartValue)
[System.IO.File]::WriteAllText($restoreScriptLocal, $restoreScriptContent, [System.Text.UTF8Encoding]::new($false))

Invoke-Checked -Exe $plink -Args @("-batch", "-ssh", "${BoardUser}@${BoardHost}", "-pw", $BoardPassword, "mkdir -p $remoteDir") -Label "create remote restore directory"

$archives = @("rk3588-code-runtime.tar.gz")
if ($RestoreData) { $archives += "rk3588-data.tar.gz" }
if ($RestorePrivate) { $archives += "rk3588-private.tar.gz" }

foreach ($archive in $archives) {
    $localArchive = Join-Path $boardBackupDir.FullName $archive
    if (Test-Path -LiteralPath $localArchive) {
        Invoke-Checked -Exe $pscp -Args @("-batch", "-scp", "-pw", $BoardPassword, $localArchive, "${BoardUser}@${BoardHost}:$remoteDir/$archive") -Label "upload $archive"
    } else {
        Write-Warning "Archive missing, skipped: $localArchive"
    }
}

Invoke-Checked -Exe $pscp -Args @("-batch", "-scp", "-pw", $BoardPassword, $restoreScriptLocal, "${BoardUser}@${BoardHost}:$restoreScript") -Label "upload restore script"
Invoke-Checked -Exe $plink -Args @("-batch", "-ssh", "${BoardUser}@${BoardHost}", "-pw", $BoardPassword, "chmod +x $restoreScript && bash $restoreScript") -Label "restore board runtime"

Write-Host
Write-Host "Restore command completed from:"
Write-Host $backupPath
