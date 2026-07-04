@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="/?" goto usage
if "%~1"=="-h" goto usage
if "%~1"=="--help" goto usage
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0sync_patient_web_to_rk3588.ps1" %*
if errorlevel 1 (
  echo.
  echo Patient web sync failed. Check whether the RK3588 is online and reachable.
  pause
  exit /b 1
)
echo.
echo Patient web sync completed.
pause
exit /b 0

:usage
echo Usage:
echo   sync_patient_web_to_rk3588.bat
echo   sync_patient_web_to_rk3588.bat -HostName 192.168.31.125 -HealthBed A-01
echo   sync_patient_web_to_rk3588.bat -SkipBuild
echo   sync_patient_web_to_rk3588.bat -SkipBackend
echo.
echo This builds patient_web, uploads dist/ to the RK3588, installs the
echo patient backend files and restart helper, rebuilds medicine_web_dashboard,
echo restarts the two-port dashboard, and verifies /patient/,
echo /patient/api/robot_status, and /api/health.
exit /b 0
