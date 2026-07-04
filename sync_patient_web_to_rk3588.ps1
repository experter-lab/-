param(
    [string]$HostName = "192.168.31.125",
    [string]$UserName = "elf",
    [string]$Password = "elf",
    [string]$PuttyDir = "D:\Program Files\PuTTY",
    [string]$HealthBed = "A-01",
    [int]$PatientPort = 8081,
    [int]$DashboardPort = 8085,
    [switch]$SkipBuild,
    [switch]$SkipBackend
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$PatientRoot = Join-Path $Root "patient_web"
$DistDir = Join-Path $PatientRoot "dist"
$BackendRoot = Join-Path $Root "board_sync\medicine_web_dashboard\medicine_web_dashboard"
$RestartScript = Join-Path $Root "board_sync\medicine_web_dashboard\restart_dashboard_with_patient.sh"
$Plink = Join-Path $PuttyDir "plink.exe"
$Pscp = Join-Path $PuttyDir "pscp.exe"
$Target = "${UserName}@${HostName}"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$RemoteUpload = "/tmp/patient_web_dist_upload_${Stamp}"
$RemoteBackendUpload = "/tmp/patient_web_backend_upload_${Stamp}"
$RemoteRestartScript = "/tmp/restart_dashboard_with_patient_${Stamp}.sh"
$RemoteInstall = "/tmp/install_patient_web_${Stamp}.sh"
$BackendFiles = @(
    @{ Name = "patient_http.py"; Source = Join-Path $BackendRoot "patient_http.py" },
    @{ Name = "web_dashboard_node.py"; Source = Join-Path $BackendRoot "web_dashboard_node.py" },
    @{ Name = "patient_state_store.py"; Source = Join-Path $BackendRoot "patient_state_store.py" },
    @{ Name = "dashboard_http.py"; Source = Join-Path $BackendRoot "dashboard_http.py" },
    @{ Name = "dashboard_assets.py"; Source = Join-Path $BackendRoot "dashboard_assets.py" },
    @{ Name = "dashboard_delivery_batch.py"; Source = Join-Path $Root "dashboard_delivery_batch.py" }
)

foreach ($tool in @($Plink, $Pscp)) {
    if (-not (Test-Path $tool)) {
        throw "PuTTY tool not found: $tool"
    }
}

if (-not (Test-Path $PatientRoot)) {
    throw "patient_web directory not found: $PatientRoot"
}
if (-not (Test-Path $RestartScript)) {
    throw "Restart script not found: $RestartScript"
}
if (-not $SkipBackend) {
    if (-not (Test-Path $BackendRoot)) {
        throw "Dashboard backend directory not found: $BackendRoot"
    }
    foreach ($file in $BackendFiles) {
        if (-not (Test-Path $file.Source)) {
            throw "Dashboard backend file not found: $($file.Source)"
        }
    }
}

if (-not $SkipBuild) {
    Write-Host "[1/6] Building patient_web ..."
    Push-Location $PatientRoot
    try {
        & npm run build
        if ($LASTEXITCODE -ne 0) {
            throw "npm run build failed"
        }
    } finally {
        Pop-Location
    }
} else {
    Write-Host "[1/6] Skipping build; using existing dist/ ..."
}

if (-not (Test-Path (Join-Path $DistDir "index.html"))) {
    throw "patient_web dist is missing index.html: $DistDir"
}

Write-Host "[2/7] Preparing remote upload directories on $Target ..."
& $Plink -batch -ssh $Target -pw $Password "mkdir -p $RemoteUpload $RemoteBackendUpload"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to prepare remote upload directory. Is the RK3588 online?"
}

Write-Host "[3/7] Uploading patient_web dist ..."
foreach ($item in Get-ChildItem -LiteralPath $DistDir -Force) {
    & $Pscp -batch -r -pw $Password $item.FullName "${Target}:${RemoteUpload}/"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upload $($item.FullName)"
    }
}

if (-not $SkipBackend) {
    Write-Host "[4/7] Uploading patient backend files ..."
    foreach ($file in $BackendFiles) {
        & $Pscp -batch -pw $Password $file.Source "${Target}:${RemoteBackendUpload}/$($file.Name)"
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to upload $($file.Source)"
        }
    }
} else {
    Write-Host "[4/7] Skipping backend upload/build ..."
}

Write-Host "[5/7] Uploading patient dashboard restart helper ..."
& $Pscp -batch -pw $Password $RestartScript "${Target}:${RemoteRestartScript}"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to upload $RestartScript"
}

$InstallScriptTemplate = @'
#!/usr/bin/env bash
set -eo pipefail

UPLOAD="__REMOTE_UPLOAD__"
BACKEND_UPLOAD="__REMOTE_BACKEND_UPLOAD__"
TARGET="/mnt/sdcard/medicine_robot_data/patient_web/dist"
BACKUP_ROOT="/mnt/sdcard/medicine_robot_data/backups"
BACKUP="${BACKUP_ROOT}/patient_web_dist___STAMP__"
BACKEND_BACKUP="${BACKUP_ROOT}/patient_web_backend___STAMP__"
RESTART_SRC="__REMOTE_RESTART_SCRIPT__"
RESTART_DST="/mnt/sdcard/restart_dashboard_with_patient.sh"
PATIENT_PORT="__PATIENT_PORT__"
DASHBOARD_PORT="__DASHBOARD_PORT__"
HEALTH_BED="__HEALTH_BED__"
HOST_NAME="__HOST_NAME__"
INSTALL_BACKEND="__INSTALL_BACKEND__"

if [ ! -d "${UPLOAD}" ]; then
  echo "ERROR: upload directory not found: ${UPLOAD}" >&2
  exit 2
fi

case "${TARGET}" in
  /mnt/sdcard/medicine_robot_data/patient_web/dist) ;;
  *) echo "ERROR: refusing unexpected target: ${TARGET}" >&2; exit 2 ;;
esac

mkdir -p "${BACKUP_ROOT}" "$(dirname "${TARGET}")"

if [ "${INSTALL_BACKEND}" = "1" ]; then
  WS="/mnt/sdcard/medicine_robot_ws"
  PKG_SRC="${WS}/src/medicine_web_dashboard/medicine_web_dashboard"
  if [ ! -d "${PKG_SRC}" ]; then
    echo "ERROR: package source not found: ${PKG_SRC}" >&2
    exit 2
  fi
  mkdir -p "${BACKEND_BACKUP}"
  for file in patient_http.py web_dashboard_node.py patient_state_store.py dashboard_http.py dashboard_assets.py dashboard_delivery_batch.py; do
    if [ -f "${PKG_SRC}/${file}" ]; then
      cp -f "${PKG_SRC}/${file}" "${BACKEND_BACKUP}/${file}"
    fi
    install -m 0644 "${BACKEND_UPLOAD}/${file}" "${PKG_SRC}/${file}"
  done
  python3 -m py_compile \
    "${PKG_SRC}/patient_http.py" \
    "${PKG_SRC}/web_dashboard_node.py" \
    "${PKG_SRC}/patient_state_store.py" \
    "${PKG_SRC}/dashboard_http.py" \
    "${PKG_SRC}/dashboard_assets.py" \
    "${PKG_SRC}/dashboard_delivery_batch.py"
  cd "${WS}"
  source /opt/ros/humble/setup.bash
  colcon build --packages-select medicine_web_dashboard
fi

if [ -d "${TARGET}" ]; then
  mkdir -p "${BACKUP}"
  cp -a "${TARGET}/." "${BACKUP}/" 2>/dev/null || true
fi

rm -rf "${TARGET}.new"
mkdir -p "${TARGET}.new"
cp -a "${UPLOAD}/." "${TARGET}.new/"
test -f "${TARGET}.new/index.html"
rm -rf "${TARGET}"
mv "${TARGET}.new" "${TARGET}"

install -m 0755 "${RESTART_SRC}" "${RESTART_DST}"

if [ -x "${RESTART_DST}" ]; then
  "${RESTART_DST}"
else
  echo "ERROR: restart helper not executable: ${RESTART_DST}" >&2
  exit 3
fi

sleep 3

curl -fsS "http://127.0.0.1:${PATIENT_PORT}/patient/" >/dev/null
curl -fsS "http://127.0.0.1:${PATIENT_PORT}/patient/api/robot_status?bed=${HEALTH_BED}" >/dev/null
curl -fsS "http://127.0.0.1:${DASHBOARD_PORT}/api/health" >/dev/null

echo "OK: patient web deployed"
echo "PATIENT_URL=http://${HOST_NAME}:${PATIENT_PORT}/patient/?bed=${HEALTH_BED}"
echo "DASHBOARD_URL=http://${HOST_NAME}:${DASHBOARD_PORT}/"
echo "BACKUP=${BACKUP}"
if [ "${INSTALL_BACKEND}" = "1" ]; then
  echo "BACKEND_BACKUP=${BACKEND_BACKUP}"
fi
'@

$InstallScript = $InstallScriptTemplate `
    -replace "__REMOTE_UPLOAD__", $RemoteUpload `
    -replace "__REMOTE_BACKEND_UPLOAD__", $RemoteBackendUpload `
    -replace "__REMOTE_RESTART_SCRIPT__", $RemoteRestartScript `
    -replace "__STAMP__", $Stamp `
    -replace "__PATIENT_PORT__", ([string]$PatientPort) `
    -replace "__DASHBOARD_PORT__", ([string]$DashboardPort) `
    -replace "__HEALTH_BED__", $HealthBed `
    -replace "__HOST_NAME__", $HostName `
    -replace "__INSTALL_BACKEND__", ($(if ($SkipBackend) { "0" } else { "1" }))

$TempInstall = Join-Path $env:TEMP "install_patient_web_${Stamp}.sh"
[System.IO.File]::WriteAllText(
    $TempInstall,
    $InstallScript,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Host "[6/7] Installing dist and restarting patient web on RK3588 ..."
& $Pscp -batch -pw $Password $TempInstall "${Target}:${RemoteInstall}"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to upload remote install script"
}
& $Plink -batch -ssh $Target -pw $Password "chmod +x $RemoteInstall && bash $RemoteInstall"
if ($LASTEXITCODE -ne 0) {
    throw "Remote patient web install failed"
}

Write-Host "[7/7] Done."
Write-Host "Open patient web: http://${HostName}:${PatientPort}/patient/?bed=${HealthBed}"
Write-Host "Open dashboard:    http://${HostName}:${DashboardPort}/"
