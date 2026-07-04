#!/usr/bin/env bash
# 启动 RViz2 查看 Cartographer 建图/定位实时效果
# 用法: bash rk3588_open_carto_rviz.sh
# 注意: 在 RK3588 桌面（NoMachine/物理屏幕）上执行，需要 X/Wayland 显示
# 不用 set -u: ROS setup.bash 会引用未绑定变量
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

# 没有 DISPLAY 时给个明确报错
if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
  echo "[carto-rviz] ERROR: 没检测到图形显示环境"
  echo "[carto-rviz] 通过 NoMachine 连入 RK3588 桌面后再运行；或先 export DISPLAY=:0"
  exit 1
fi

# Mali-G610 GPU 的 OpenGL 驱动会让 RViz Map shader 链接失败，强制软件渲染绕过
# 想试硬件渲染：注释下一行（性能更高，但可能黑屏/花屏）
export LIBGL_ALWAYS_SOFTWARE=1

echo "[carto-rviz] launching RViz2 with Cartographer view config..."
echo "[carto-rviz] LIBGL_ALWAYS_SOFTWARE=$LIBGL_ALWAYS_SOFTWARE (软件渲染绕过 Mali GPU bug)"
exec ros2 launch medicine_robot_bringup rk3588_carto_view.launch.py
