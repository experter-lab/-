@echo off
:: RK3588 核心资产一键备份工具 (Windows 批处理版)
:: 适用于将 RK3588 嵌入式板端非代码核心数据一键拉取备份到本地电脑

set "BOARD_IP=192.168.31.125"
set "BOARD_USER=elf"
set "BACKUP_DIR=D:\A1\backup"

echo ===================================================
echo        RK3588 核心资产一键备份与迁移工具
echo ===================================================
echo 目标开发板 IP: %BOARD_IP%
echo 登录用户名    : %BOARD_USER%
echo 本地备份目录  : %BACKUP_DIR%
echo ===================================================

:: 1. 检查网络连通性
echo [*] 正在检测开发板网络连通性...
ping -n 2 %BOARD_IP% >nul
if errorlevel 1 (
    echo [ERROR] 无法连接到开发板 %BOARD_IP%。
    echo [ERROR] 请确保：
    echo         1. 机器人已经上电开机
    echo         2. 电脑与开发板处于同一个 Wi-Fi 或局域网段下
    echo         3. 开发板 IP 没有发生变更
    echo.
    echo [提示] 如果开发板 IP 发生变更，请用文本编辑器修改本 `.bat` 脚本中的 BOARD_IP 参数。
    echo.
    pause
    exit /b 1
)
echo [OK] 开发板网络畅通！

:: 2. 创建本地备份目录
if not exist "%BACKUP_DIR%" (
    echo [*] 正在创建本地备份文件夹...
    mkdir "%BACKUP_DIR%"
)
if not exist "%BACKUP_DIR%\maps" mkdir "%BACKUP_DIR%\maps"
if not exist "%BACKUP_DIR%\models" mkdir "%BACKUP_DIR%\models"
if not exist "%BACKUP_DIR%\scripts" mkdir "%BACKUP_DIR%\scripts"

echo.
echo ===================================================
echo 开始备份进程 (传输期间需要您输入板端的 SSH 登录密码)
echo ===================================================
echo.

:: 3. 备份语音离线授权
echo [1/4] 正在拉取科大讯飞离线语音授权密钥 aikit.env...
scp %BOARD_USER%@%BOARD_IP%:~/.config/medicine_robot/aikit.env "%BACKUP_DIR%\aikit.env"
if errorlevel 0 (
    echo [OK] 语音授权 aikit.env 备份成功。
) else (
    echo [WARN] 未找到 aikit.env，请确认语音服务是否已授权。
)
echo.

:: 4. 备份已建好的医院地图
echo [2/4] 正在拉取板端扫好的 2D 栅格地图文件 (maps)...
scp %BOARD_USER%@%BOARD_IP%:/mnt/sdcard/medicine_robot_data/maps/* "%BACKUP_DIR%\maps\"
if errorlevel 0 (
    echo [OK] 地图文件备份成功。
) else (
    echo [WARN] 未拉取到地图文件，请确认板上是否有地图。
)
echo.

:: 5. 备份 NPU YOLO 离线模型
echo [3/4] 正在拉取板端高精度 RKNN YOLOv8 神经网络模型...
scp %BOARD_USER%@%BOARD_IP%:/mnt/sdcard/medicine_robot_data/models/yolov8n_rk3588.rknn "%BACKUP_DIR%\models\"
if errorlevel 0 (
    echo [OK] RKNN 模型备份成功。
) else (
    echo [WARN] 未拉取到模型文件，请确认模型是否存在。
)
echo.

:: 6. 备份定制的板端运维与一键启动脚本
echo [4/4] 正在拉取板载一键自检与运维启动脚本 (*.sh)...
scp %BOARD_USER%@%BOARD_IP%:/mnt/sdcard/rk3588_*.sh "%BACKUP_DIR%\scripts\"
if errorlevel 0 (
    echo [OK] 运维脚本备份成功。
) else (
    echo [WARN] 运维脚本拉取失败。
)
echo.

echo ===================================================
echo                  备份任务全部结束！
echo ===================================================
echo 所有资产已成功保存至本地：
echo %BACKUP_DIR%
echo.
pause
