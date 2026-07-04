@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="/?" goto usage
if "%~1"=="-h" goto usage
if "%~1"=="--help" goto usage
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0sync_navigation_web_to_rk3588.ps1" %*
if errorlevel 1 (
  echo.
  echo Sync failed. Check whether the RK3588 is online and reachable.
  pause
  exit /b 1
)
echo.
echo Sync completed.
pause
exit /b 0

:usage
echo Usage:
echo   sync_navigation_web_to_rk3588.bat
echo   sync_navigation_web_to_rk3588.bat -HostName 192.168.31.125
echo   sync_navigation_web_to_rk3588.bat -HostName 192.168.31.125 -UserName elf -Password elf
echo.
echo This uploads the navigation web dashboard files, backs up remote files,
echo builds medicine_web_dashboard, restarts the RK3588 web dashboard, and
echo verifies /navigation plus /api/navigation/snapshot.
exit /b 0
