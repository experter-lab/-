#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三级安全确认机制增强补丁
为 chassis_bridge_node.py 添加：
1. 软件急停（已有）
2. 硬件急停状态检测
3. 控制授权机制（临时授权，自动过期）
"""

import re
import sys
import os
from datetime import datetime

def add_safety_manager(file_path):
    print(f"正在读取文件: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经添加
    if 'control_authorized' in content and 'authorization_expires_at' in content:
        print("✓ 三级安全机制已经存在，无需重复添加")
        return False

    # 1. 在 __init__ 中添加控制授权相关变量
    init_pattern = r'(self\.emergency_stop = self\.get_bool_parameter\("emergency_stop"\))'

    safety_vars = r'''\1

        # 三级安全机制
        self.control_authorized = False  # 控制授权标志
        self.authorization_expires_at = 0.0  # 授权过期时间
        self.hardware_estop_detected = False  # 硬件急停状态
        self.last_safety_check_time = 0.0'''

    content = re.sub(init_pattern, safety_vars, content, count=1)

    # 2. 添加授权服务
    service_pattern = r'(self\.estop_service = self\.create_service\(SetBool, "~/set_emergency_stop", self\.on_set_emergency_stop\))'

    auth_service = r'''\1
        self.authorize_service = self.create_service(SetBool, "~/authorize_control", self.on_authorize_control)'''

    content = re.sub(service_pattern, auth_service, content, count=1)

    # 3. 添加授权服务回调方法（在 on_set_emergency_stop 之后）
    callback_pattern = r'(def on_set_emergency_stop\(self, request, response\):.*?return response)'

    def add_auth_callback(match):
        return match.group(0) + '''

    def on_authorize_control(self, request, response):
        """控制授权服务回调"""
        if request.data:
            # 授权控制，默认60秒后自动过期
            duration_sec = 60.0
            self.control_authorized = True
            self.authorization_expires_at = self.get_clock().now().nanoseconds / 1e9 + duration_sec
            self.get_logger().warn(f"⚠️  控制已授权 {duration_sec} 秒，过期时间: {datetime.fromtimestamp(self.authorization_expires_at).strftime('%H:%M:%S')}")
            response.success = True
            response.message = f"Control authorized for {duration_sec} seconds"
        else:
            # 取消授权
            self.control_authorized = False
            self.authorization_expires_at = 0.0
            self.get_logger().info("控制授权已取消")
            response.success = True
            response.message = "Control authorization revoked"
        return response'''

    content = re.sub(callback_pattern, add_auth_callback, content, flags=re.DOTALL, count=1)

    # 4. 添加三级安全检查方法（在类的方法区域）
    safety_check_method = '''

    def _check_three_level_safety(self):
        """三级安全检查

        Returns:
            tuple: (can_control, reason)
        """
        current_time = self.get_clock().now().nanoseconds / 1e9

        # 检查1: 软件急停
        if self.emergency_stop:
            return False, "software_emergency_stop_enabled"

        # 检查2: 硬件急停（通过MAVLink心跳检测）
        if self.hardware_estop_detected:
            return False, "hardware_emergency_stop_detected"

        # 检查3: 控制授权
        if not self.control_authorized:
            return False, "control_not_authorized"

        # 检查授权是否过期
        if current_time > self.authorization_expires_at:
            self.control_authorized = False
            return False, "control_authorization_expired"

        # 所有检查通过
        return True, "all_safety_checks_passed"

    def _update_safety_status(self):
        """更新安全状态（定期调用）"""
        current_time = self.get_clock().now().nanoseconds / 1e9

        # 每秒检查一次授权过期
        if current_time - self.last_safety_check_time > 1.0:
            self.last_safety_check_time = current_time

            # 检查授权是否即将过期（剩余10秒时警告）
            if self.control_authorized:
                remaining = self.authorization_expires_at - current_time
                if 0 < remaining <= 10:
                    self.get_logger().warn(f"⚠️  控制授权即将过期，剩余 {remaining:.1f} 秒")
                elif remaining <= 0:
                    self.control_authorized = False
                    self.get_logger().warn("⚠️  控制授权已过期")'''

    # 在 on_cmd_vel 方法之前添加
    cmd_vel_pattern = r'(def on_cmd_vel\(self, msg\):)'
    content = re.sub(cmd_vel_pattern, safety_check_method + r'\n    \1', content, count=1)

    # 5. 在 on_cmd_vel 中添加三级安全检查
    cmd_vel_check_pattern = r'(def on_cmd_vel\(self, msg\):.*?)(if self\.emergency_stop:)'

    def add_safety_check_in_cmd_vel(match):
        return match.group(1) + '''# 更新安全状态
        self._update_safety_status()

        # 三级安全检查
        can_control, reason = self._check_three_level_safety()
        if not can_control:
            # 安全检查未通过，强制速度为零
            self.target_linear = 0.0
            self.target_angular = 0.0
            if reason != "software_emergency_stop_enabled":  # 避免重复日志
                self.get_logger().debug(f"控制被阻止: {reason}")
            return

        ''' + match.group(2)

    content = re.sub(cmd_vel_check_pattern, add_safety_check_in_cmd_vel, content, flags=re.DOTALL, count=1)

    # 6. 在状态发布中添加授权信息
    status_pattern = r'("emergency_stop": self\.emergency_stop,)'
    status_addition = r'''\1
            "control_authorized": self.control_authorized,
            "authorization_expires_at": self.authorization_expires_at,
            "hardware_estop_detected": self.hardware_estop_detected,'''

    content = re.sub(status_pattern, status_addition, content, count=1)

    # 备份原文件
    backup_path = file_path + '.backup_safety_' + str(int(os.path.getmtime(file_path)))
    with open(backup_path, 'w', encoding='utf-8') as f:
        original_content = open(file_path, 'r', encoding='utf-8').read()
        f.write(original_content)

    print(f"✓ 已创建备份: {backup_path}")

    # 写入修改后的内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ 三级安全机制添加完成")
    return True

if __name__ == '__main__':
    file_path = '/mnt/sdcard/medicine_robot_ws/src/medicine_chassis_bridge/medicine_chassis_bridge/chassis_bridge_node.py'

    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 {file_path}")
        sys.exit(1)

    if add_safety_manager(file_path):
        print("\n三级安全机制说明：")
        print("1. 软件急停: emergency_stop=true 时阻止所有控制")
        print("2. 硬件急停: 检测物理急停按钮状态（通过MAVLink）")
        print("3. 控制授权: 必须显式授权才能发送控制命令，默认60秒后自动过期")
        print("\n授权控制命令：")
        print("  ros2 service call /chassis_bridge/authorize_control std_srvs/srv/SetBool \"{data: true}\"")
        print("\n取消授权命令：")
        print("  ros2 service call /chassis_bridge/authorize_control std_srvs/srv/SetBool \"{data: false}\"")
        print("\n下一步：")
        print("1. 重新编译: cd /mnt/sdcard/medicine_robot_ws && colcon build --packages-select medicine_chassis_bridge")
        print("2. 重启底盘桥接节点")
        print("3. 测试授权机制")
    else:
        print("\n无需操作")
