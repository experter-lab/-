@echo off
setlocal
cd /d "%~dp0"
echo Starting RK3588 offline dashboard on http://127.0.0.1:8086 ...
start "RK3588 Offline Dashboard" /min python "%~dp0offline_web_dashboard.py" --host 127.0.0.1 --port 8086
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8086/"
