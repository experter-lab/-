import json
import math
from datetime import datetime
from typing import Dict, Optional

import rclpy
from geometry_msgs.msg import TransformStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Imu
from std_msgs.msg import String
from std_srvs.srv import SetBool, Trigger
from tf2_ros import TransformBroadcaster

try:
    import serial
except ImportError:
    serial = None

try:
    from pymavlink import mavutil
except ImportError:
    mavutil = None


class ChassisBridge(Node):
    def __init__(self):
        super().__init__("chassis_bridge")
        self.declare_parameter("mode", "mock")
        self.declare_parameter("cmd_vel_topic", "/cmd_vel")
        self.declare_parameter("odom_topic", "/odom")
        self.declare_parameter("status_topic", "/medicine/chassis_status")
        self.declare_parameter("imu_topic", "/imu")
        self.declare_parameter("base_frame_id", "base_link")
        self.declare_parameter("odom_frame_id", "odom")
        self.declare_parameter("imu_frame_id", "base_link")
        self.declare_parameter("publish_odom", True)
        self.declare_parameter("publish_tf", True)
        self.declare_parameter("publish_imu", True)
        self.declare_parameter("control_rate_hz", 30.0)
        self.declare_parameter("odom_publish_rate_hz", 30.0)
        self.declare_parameter("cmd_timeout_sec", 0.5)
        self.declare_parameter("max_linear_speed", 0.35)
        self.declare_parameter("max_angular_speed", 0.8)
        self.declare_parameter("max_linear_accel", 0.5)
        self.declare_parameter("max_angular_accel", 1.2)
        self.declare_parameter("wheel_base", 0.34)
        self.declare_parameter("track_width", 0.30)
        self.declare_parameter("wheel_radius", 0.065)
        self.declare_parameter("emergency_stop", False)
        self.declare_parameter("control_authorization_duration_sec", 60.0)
        self.declare_parameter("serial_port", "/dev/ttyUSB1")
        self.declare_parameter("serial_baudrate", 115200)
        self.declare_parameter("serial_enabled", False)
        self.declare_parameter("serial_protocol", "placeholder_v1")
        self.declare_parameter("serial_write_period_sec", 0.05)
        self.declare_parameter("serial_read_timeout_sec", 0.02)
        self.declare_parameter("ardupilot_port", "/dev/ttyACM0")
        self.declare_parameter("ardupilot_baudrate", 115200)
        self.declare_parameter("ardupilot_enabled", False)
        self.declare_parameter("ardupilot_readonly", True)
        self.declare_parameter("ardupilot_control_enabled", False)
        self.declare_parameter("ardupilot_status_timeout_sec", 2.0)
        self.declare_parameter("ardupilot_source_system", 255)
        self.declare_parameter("ardupilot_source_component", 0)
        self.declare_parameter("ardupilot_target_system", 1)
        self.declare_parameter("ardupilot_target_component", 1)
        # RC override mapping (ArduRover Skid Steering 默认: ch1=steering, ch3=throttle)
        self.declare_parameter("ardupilot_rc_steering_channel", 1)
        self.declare_parameter("ardupilot_rc_throttle_channel", 3)
        self.declare_parameter("ardupilot_rc_pwm_min", 1100)
        self.declare_parameter("ardupilot_rc_pwm_mid", 1500)
        self.declare_parameter("ardupilot_rc_pwm_max", 1900)
        self.declare_parameter("ardupilot_rc_steering_pwm_min", 0)
        self.declare_parameter("ardupilot_rc_steering_pwm_mid", 0)
        self.declare_parameter("ardupilot_rc_steering_pwm_max", 0)
        self.declare_parameter("ardupilot_rc_send_period_sec", 0.1)
        self.declare_parameter("ardupilot_rc_release_on_idle", True)
        # 调试反向：cmd_vel 方向若和物理方向不一致，改这两个
        self.declare_parameter("ardupilot_invert_throttle", False)
        self.declare_parameter("ardupilot_invert_steering", False)

        self.mode = self.get_string_parameter("mode")
        self.cmd_vel_topic = self.get_string_parameter("cmd_vel_topic")
        self.odom_topic = self.get_string_parameter("odom_topic")
        self.status_topic = self.get_string_parameter("status_topic")
        self.imu_topic = self.get_string_parameter("imu_topic")
        self.base_frame_id = self.get_string_parameter("base_frame_id")
        self.odom_frame_id = self.get_string_parameter("odom_frame_id")
        self.imu_frame_id = self.get_string_parameter("imu_frame_id")
        self.publish_odom_enabled = self.get_bool_parameter("publish_odom")
        self.publish_tf = self.get_bool_parameter("publish_tf")
        self.publish_imu_enabled = self.get_bool_parameter("publish_imu")
        self.control_rate_hz = max(self.get_float_parameter("control_rate_hz"), 1.0)
        self.odom_publish_rate_hz = max(
            self.get_float_parameter("odom_publish_rate_hz"), 1.0
        )
        self.cmd_timeout_sec = max(self.get_float_parameter("cmd_timeout_sec"), 0.0)
        self.max_linear_speed = abs(self.get_float_parameter("max_linear_speed"))
        self.max_angular_speed = abs(self.get_float_parameter("max_angular_speed"))
        self.max_linear_accel = abs(self.get_float_parameter("max_linear_accel"))
        self.max_angular_accel = abs(self.get_float_parameter("max_angular_accel"))
        self.wheel_base = self.get_float_parameter("wheel_base")
        self.track_width = self.get_float_parameter("track_width")
        self.wheel_radius = self.get_float_parameter("wheel_radius")
        self.emergency_stop = self.get_bool_parameter("emergency_stop")
        self.authorization_duration_sec = max(
            self.get_float_parameter("control_authorization_duration_sec"), 1.0
        )

        # 三级安全机制
        self.control_authorized = False  # 控制授权标志
        self.authorization_expires_at = 0.0  # 授权过期时间
        self.hardware_estop_detected = False  # 硬件急停状态
        self.last_safety_check_time = 0.0
        self.serial_port = self.get_string_parameter("serial_port")
        self.serial_baudrate = self.get_int_parameter("serial_baudrate")
        self.serial_enabled = self.get_bool_parameter("serial_enabled")
        self.serial_protocol = self.get_string_parameter("serial_protocol")
        self.serial_write_period_sec = max(
            self.get_float_parameter("serial_write_period_sec"), 0.01
        )
        self.serial_read_timeout_sec = max(
            self.get_float_parameter("serial_read_timeout_sec"), 0.001
        )
        self.ardupilot_port = self.get_string_parameter("ardupilot_port")
        self.ardupilot_baudrate = self.get_int_parameter("ardupilot_baudrate")
        self.ardupilot_enabled = self.get_bool_parameter("ardupilot_enabled")
        self.ardupilot_readonly = self.get_bool_parameter("ardupilot_readonly")
        self.ardupilot_control_enabled = self.get_bool_parameter(
            "ardupilot_control_enabled"
        )
        self.ardupilot_status_timeout_sec = max(
            self.get_float_parameter("ardupilot_status_timeout_sec"), 0.1
        )
        self.ardupilot_source_system = self.get_int_parameter("ardupilot_source_system")
        self.ardupilot_source_component = self.get_int_parameter("ardupilot_source_component")
        self.ardupilot_target_system = self.get_int_parameter("ardupilot_target_system")
        self.ardupilot_target_component = self.get_int_parameter("ardupilot_target_component")
        self.rc_steering_channel = max(1, min(8, self.get_int_parameter("ardupilot_rc_steering_channel")))
        self.rc_throttle_channel = max(1, min(8, self.get_int_parameter("ardupilot_rc_throttle_channel")))
        self.rc_pwm_min = self.get_int_parameter("ardupilot_rc_pwm_min")
        self.rc_pwm_mid = self.get_int_parameter("ardupilot_rc_pwm_mid")
        self.rc_pwm_max = self.get_int_parameter("ardupilot_rc_pwm_max")
        steering_pwm_min = self.get_int_parameter("ardupilot_rc_steering_pwm_min")
        steering_pwm_mid = self.get_int_parameter("ardupilot_rc_steering_pwm_mid")
        steering_pwm_max = self.get_int_parameter("ardupilot_rc_steering_pwm_max")
        self.rc_steering_pwm_min = steering_pwm_min if steering_pwm_min > 0 else self.rc_pwm_min
        self.rc_steering_pwm_mid = steering_pwm_mid if steering_pwm_mid > 0 else self.rc_pwm_mid
        self.rc_steering_pwm_max = steering_pwm_max if steering_pwm_max > 0 else self.rc_pwm_max
        self.rc_send_period_sec = max(self.get_float_parameter("ardupilot_rc_send_period_sec"), 0.02)
        self.rc_release_on_idle = self.get_bool_parameter("ardupilot_rc_release_on_idle")
        self.invert_throttle = self.get_bool_parameter("ardupilot_invert_throttle")
        self.invert_steering = self.get_bool_parameter("ardupilot_invert_steering")

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.target_linear = 0.0
        self.target_angular = 0.0
        self.current_linear = 0.0
        self.current_angular = 0.0
        self.last_cmd_time = self.get_clock().now()
        self.last_update_time = self.get_clock().now()
        self.last_odom_publish_time = self.get_clock().now()
        self.last_serial_write_time = self.get_clock().now()
        self.cmd_count = 0
        self.timeout_count = 0
        self.serial_error: Optional[str] = None
        self.serial_handle = None
        self.ardupilot_error: Optional[str] = None
        self.ardupilot_conn = None
        self.ardupilot_last_heartbeat_time = None
        self.ardupilot_last_send_time = self.get_clock().now()
        self.ardupilot_heartbeat_count = 0
        self.ardupilot_message_count = 0
        self.ardupilot_imu_count = 0
        self.ardupilot_last_imu_time = None
        self.ardupilot_system_id: Optional[int] = None
        self.ardupilot_component_id: Optional[int] = None
        self.ardupilot_custom_mode: Optional[int] = None
        self.ardupilot_type: Optional[int] = None
        self.ardupilot_autopilot: Optional[int] = None
        self.ardupilot_base_mode: Optional[int] = None
        self.ardupilot_system_status: Optional[int] = None
        self.ardupilot_mavlink_version: Optional[int] = None
        # ATTITUDE
        self.ardupilot_attitude_roll: Optional[float] = None
        self.ardupilot_attitude_pitch: Optional[float] = None
        self.ardupilot_attitude_yaw: Optional[float] = None
        self.ardupilot_attitude_yawspeed: Optional[float] = None
        # VFR_HUD (airspeed/groundspeed/heading/throttle/alt/climb)
        self.ardupilot_vfr_groundspeed: Optional[float] = None
        self.ardupilot_vfr_heading_deg: Optional[int] = None
        self.ardupilot_vfr_throttle: Optional[int] = None
        # SYS_STATUS (battery/error)
        self.ardupilot_battery_voltage_v: Optional[float] = None
        self.ardupilot_battery_current_a: Optional[float] = None
        self.ardupilot_battery_remaining_pct: Optional[int] = None
        self.ardupilot_errors_count: Optional[int] = None
        self.ardupilot_sensors_health: Optional[int] = None
        # LOCAL_POSITION_NED
        self.ardupilot_local_x: Optional[float] = None
        self.ardupilot_local_y: Optional[float] = None
        self.ardupilot_local_vx: Optional[float] = None
        self.ardupilot_local_vy: Optional[float] = None
        # RC_CHANNELS / SERVO_OUTPUT_RAW diagnostics
        self.ardupilot_rc_channels: Dict[str, Optional[int]] = {}
        self.ardupilot_servo_outputs: Dict[str, Optional[int]] = {}
        # RC override 调试
        self.last_rc_throttle_pwm: Optional[int] = None
        self.last_rc_steering_pwm: Optional[int] = None

        # ArduRover 模式映射 (custom_mode → 名称，按 ArduPilot Rover 官方 mode.h)
        self.ROVER_MODES: Dict[int, str] = {
            0: "MANUAL",   1: "ACRO",      3: "STEERING",
            4: "HOLD",     5: "LOITER",    6: "FOLLOW",
            7: "SIMPLE",   8: "DOCK",      9: "CIRCLE",
            10: "AUTO",    11: "RTL",      12: "SMART_RTL",
            15: "GUIDED",  16: "INITIALIZING",
        }

        self.odom_pub = (
            self.create_publisher(Odometry, self.odom_topic, 10)
            if self.publish_odom_enabled
            else None
        )
        self.status_pub = self.create_publisher(String, self.status_topic, 10)
        self.imu_pub = (
            self.create_publisher(Imu, self.imu_topic, 20)
            if self.publish_imu_enabled
            else None
        )
        self.tf_broadcaster = (
            TransformBroadcaster(self)
            if self.publish_tf and self.publish_odom_enabled
            else None
        )
        self.cmd_sub = self.create_subscription(
            Twist, self.cmd_vel_topic, self.on_cmd_vel, 10
        )
        self.estop_service = self.create_service(
            SetBool, "~/set_emergency_stop", self.on_set_emergency_stop
        )
        self.authorize_service = self.create_service(
            SetBool, "~/authorize_control", self.on_authorize_control
        )
        self.reset_odom_service = self.create_service(
            Trigger, "~/reset_odom", self.on_reset_odom
        )
        self.set_mode_service = self.create_service(
            SetBool, "~/set_mode", self.on_set_mode
        )
        self.arm_service = self.create_service(
            SetBool, "~/arm", self.on_arm
        )
        # 字符串切模式：std_msgs/String 命令 topic（因为 std_srvs 没有 String 服务）
        self.set_mode_str_sub = self.create_subscription(
            String, "~/set_mode_str_cmd", self.on_set_mode_str_msg, 1
        )

        if self.mode == "serial" and self.serial_enabled:
            self.open_serial()
        elif self.mode == "serial":
            self.get_logger().warn(
                "serial mode selected, but serial_enabled is false; commands will not be sent to hardware"
            )
        elif self.mode == "ardupilot" and self.ardupilot_enabled:
            self.open_ardupilot()
        elif self.mode == "ardupilot":
            self.get_logger().warn(
                "ardupilot mode selected, but ardupilot_enabled is false; USB/MAVLink will be read-only disabled"
            )
        elif self.mode != "mock":
            self.get_logger().warn(
                f"unknown mode '{self.mode}', falling back to mock behavior"
            )

        self.timer = self.create_timer(1.0 / self.control_rate_hz, self.on_timer)
        self.get_logger().info(
            f"chassis bridge started mode={self.mode} cmd_vel={self.cmd_vel_topic} odom={self.odom_topic} "
            f"base_frame={self.base_frame_id} odom_frame={self.odom_frame_id}"
        )

    def get_string_parameter(self, name):
        return str(self.get_parameter(name).value)

    def get_bool_parameter(self, name):
        return bool(self.get_parameter(name).value)

    def get_float_parameter(self, name):
        return float(self.get_parameter(name).value)

    def get_int_parameter(self, name):
        return int(self.get_parameter(name).value)

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
                    self.get_logger().warn(
                        f"⚠️  控制授权即将过期，剩余 {remaining:.1f} 秒"
                    )
                elif remaining <= 0:
                    self.control_authorized = False
                    self.get_logger().warn("⚠️  控制授权已过期")

    def on_cmd_vel(self, msg):
        self.target_linear = self.clamp(
            msg.linear.x, -self.max_linear_speed, self.max_linear_speed
        )
        self.target_angular = self.clamp(
            msg.angular.z, -self.max_angular_speed, self.max_angular_speed
        )
        self.last_cmd_time = self.get_clock().now()
        self.cmd_count += 1

    def on_set_emergency_stop(self, request, response):
        try:
            self.emergency_stop = bool(request.data)
            self._update_safety_status()
            if self.emergency_stop:
                self.target_linear = 0.0
                self.target_angular = 0.0
                self.current_linear = 0.0
                self.current_angular = 0.0
                self.send_serial_command(0.0, 0.0)
                self.send_ardupilot_neutral_override("software emergency stop")
                self.send_set_mode_by_id(4)
                self.send_arm_command(False)
            response.success = True
            response.message = f"emergency_stop={self.emergency_stop}"
        except Exception as exc:
            response.success = False
            response.message = f"on_set_emergency_stop exception: {exc}"
            self.get_logger().error(response.message)
        return response

    def on_authorize_control(self, request, response):
        """控制授权服务回调"""
        try:
            if request.data:
                duration_sec = self.authorization_duration_sec
                self.control_authorized = True
                self.authorization_expires_at = (
                    self.get_clock().now().nanoseconds / 1e9 + duration_sec
                )
                self.get_logger().warn(
                    f"控制已授权 {duration_sec} 秒，过期时间: "
                    f"{datetime.fromtimestamp(self.authorization_expires_at).strftime('%H:%M:%S')}"
                )
                response.success = True
                response.message = f"Control authorized for {duration_sec} seconds"
            else:
                self.control_authorized = False
                self.authorization_expires_at = 0.0
                self.get_logger().info("控制授权已取消")
                response.success = True
                response.message = "Control authorization revoked"
        except Exception as exc:
            response.success = False
            response.message = f"on_authorize_control exception: {exc}"
            self.get_logger().error(response.message)
        return response

    def on_reset_odom(self, request, response):
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.current_linear = 0.0
        self.current_angular = 0.0
        response.success = True
        response.message = "odom reset to zero"
        return response

    def on_set_mode(self, request, response):
        """True → MANUAL(0), False → HOLD(4)."""
        try:
            success, msg = self.send_set_mode_command(bool(request.data))
        except Exception as exc:
            success, msg = False, f"on_set_mode exception: {exc}"
            self.get_logger().error(msg)
        response.success = bool(success)
        response.message = str(msg) if msg is not None else ""
        return response

    def on_arm(self, request, response):
        """True → arm, False → disarm."""
        try:
            success, msg = self.send_arm_command(bool(request.data))
        except Exception as exc:
            success, msg = False, f"on_arm exception: {exc}"
            self.get_logger().error(msg)
        response.success = bool(success)
        response.message = str(msg) if msg is not None else ""
        return response

    # ── MAVLink 命令下发 ────────────────────────────────────────────

    def send_set_mode_command(self, to_manual: bool):
        """旧 SetBool 服务回调用：True→MANUAL, False→HOLD"""
        return self.send_set_mode_by_id(0 if to_manual else 4)

    def send_set_mode_by_name(self, mode_name: str):
        """通用按名字切模式。mode_name 大小写不敏感。"""
        mode_name_upper = mode_name.strip().upper()
        # 反向查 ROVER_MODES
        target_id = None
        for mid, mname in self.ROVER_MODES.items():
            if mname == mode_name_upper:
                target_id = mid
                break
        if target_id is None:
            valid = ", ".join(sorted(self.ROVER_MODES.values()))
            return False, f"unknown mode '{mode_name}'. valid: {valid}"
        return self.send_set_mode_by_id(target_id)

    def check_ardupilot_write_allowed(self, command_name: str, require_authorized: bool = True):
        if self.mode != "ardupilot" or self.ardupilot_conn is None:
            return False, "ardupilot connection not available"
        if self.ardupilot_readonly:
            return False, f"{command_name} blocked: ardupilot_readonly=true"
        if not self.ardupilot_control_enabled:
            return False, f"{command_name} blocked: ardupilot_control_enabled=false"
        if self.ardupilot_last_heartbeat_time is None:
            return False, f"{command_name} blocked: heartbeat_missing"
        heartbeat_age = (
            self.get_clock().now() - self.ardupilot_last_heartbeat_time
        ).nanoseconds / 1e9
        if heartbeat_age > self.ardupilot_status_timeout_sec:
            return False, f"{command_name} blocked: heartbeat_timeout"
        if require_authorized:
            can_control, reason = self._check_three_level_safety()
            if not can_control:
                return False, f"{command_name} blocked: {reason}"
        return True, "ok"

    def send_set_mode_by_id(self, target_mode: int):
        """统一 MAVLink SET_MODE 下发。"""
        mode_name = self.ROVER_MODES.get(target_mode, f"MODE_{target_mode}")
        allowed, reason = self.check_ardupilot_write_allowed(
            f"set_mode {mode_name}",
            require_authorized=target_mode != 4,
        )
        if not allowed:
            self.get_logger().warn(reason)
            return False, reason
        # ArduPilot Rover：base_mode 必须带 CUSTOM_MODE_ENABLED；ARMED 位保留当前
        base_mode = mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED
        if self.ardupilot_base_mode is not None and (self.ardupilot_base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED):
            base_mode |= mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
        try:
            self.ardupilot_conn.mav.set_mode_send(
                self.ardupilot_target_system,
                base_mode,
                target_mode,
            )
            self.get_logger().info(
                f"SET_MODE → {mode_name}({target_mode}) base_mode=0x{base_mode:02x} sent"
            )
            return True, f"mode command sent: {mode_name}"
        except Exception as exc:
            self.get_logger().error(f"failed to send set_mode: {exc}")
            return False, str(exc)

    def on_set_mode_str_msg(self, msg: String):
        """收到字符串命令切模式。"""
        mode_name = msg.data.strip()
        if not mode_name:
            return
        ok, info = self.send_set_mode_by_name(mode_name)
        if ok:
            self.get_logger().info(f"set_mode_str: {info}")
        else:
            self.get_logger().error(f"set_mode_str failed: {info}")

    def send_arm_command(self, arm: bool):
        action = "ARM" if arm else "DISARM"
        allowed, reason = self.check_ardupilot_write_allowed(
            action,
            require_authorized=arm,
        )
        if not allowed:
            self.get_logger().warn(reason)
            return False, reason
        try:
            self.ardupilot_conn.mav.command_long_send(
                self.ardupilot_target_system,
                self.ardupilot_target_component,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                0,  # confirmation
                1 if arm else 0,  # arm / disarm
                0, 0, 0, 0, 0, 0,
            )
            self.get_logger().info(f"MAV_CMD_COMPONENT_ARM_DISARM → {action} sent")
            return True, f"arm command sent: {action}"
        except Exception as exc:
            self.get_logger().error(f"failed to send arm command: {exc}")
            return False, str(exc)

    def on_timer(self):
        now = self.get_clock().now()
        dt = max((now - self.last_update_time).nanoseconds / 1e9, 0.0)
        self.last_update_time = now

        cmd_age = (now - self.last_cmd_time).nanoseconds / 1e9
        timed_out = self.cmd_timeout_sec > 0.0 and cmd_age > self.cmd_timeout_sec
        if timed_out:
            if abs(self.target_linear) > 1e-6 or abs(self.target_angular) > 1e-6:
                self.timeout_count += 1
            self.target_linear = 0.0
            self.target_angular = 0.0

        if self.emergency_stop:
            self.target_linear = 0.0
            self.target_angular = 0.0
            self.current_linear = 0.0
            self.current_angular = 0.0
        else:
            self.current_linear = self.apply_accel_limit(
                self.current_linear, self.target_linear, self.max_linear_accel, dt
            )
            self.current_angular = self.apply_accel_limit(
                self.current_angular, self.target_angular, self.max_angular_accel, dt
            )

        if self.mode == "mock" or (
            self.mode != "ardupilot" and not self.serial_enabled
        ):
            self.integrate_mock_odom(dt)
        elif self.mode == "serial":
            self.poll_serial()
        elif self.mode == "ardupilot":
            self.poll_ardupilot()

        if (
            now - self.last_serial_write_time
        ).nanoseconds / 1e9 >= self.serial_write_period_sec:
            self.send_serial_command(self.current_linear, self.current_angular)
            self.send_ardupilot_command(self.current_linear, self.current_angular)
            self.last_serial_write_time = now

        if (
            self.publish_odom_enabled
            and (now - self.last_odom_publish_time).nanoseconds / 1e9
            >= 1.0 / self.odom_publish_rate_hz
        ):
            self.publish_odom(now)
            self.last_odom_publish_time = now

        self.publish_status(now, cmd_age, timed_out)

    def integrate_mock_odom(self, dt):
        if dt <= 0.0:
            return
        delta_yaw = self.current_angular * dt
        if abs(delta_yaw) < 1e-9:
            self.x += self.current_linear * math.cos(self.yaw) * dt
            self.y += self.current_linear * math.sin(self.yaw) * dt
        else:
            next_yaw = self.yaw + delta_yaw
            radius = (
                self.current_linear / self.current_angular
                if abs(self.current_angular) > 1e-9
                else 0.0
            )
            self.x += radius * (math.sin(next_yaw) - math.sin(self.yaw))
            self.y -= radius * (math.cos(next_yaw) - math.cos(self.yaw))
        self.yaw = self.normalize_angle(self.yaw + delta_yaw)

    def publish_odom(self, stamp):
        quat_z = math.sin(self.yaw * 0.5)
        quat_w = math.cos(self.yaw * 0.5)
        odom = Odometry()
        odom.header.stamp = stamp.to_msg()
        odom.header.frame_id = self.odom_frame_id
        odom.child_frame_id = self.base_frame_id
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation.z = quat_z
        odom.pose.pose.orientation.w = quat_w
        odom.twist.twist.linear.x = self.current_linear
        odom.twist.twist.angular.z = self.current_angular
        odom.pose.covariance[0] = 0.02
        odom.pose.covariance[7] = 0.02
        odom.pose.covariance[35] = 0.05
        odom.twist.covariance[0] = 0.05
        odom.twist.covariance[35] = 0.1
        if self.odom_pub is not None:
            self.odom_pub.publish(odom)

        if self.tf_broadcaster is not None:
            transform = TransformStamped()
            transform.header.stamp = stamp.to_msg()
            transform.header.frame_id = self.odom_frame_id
            transform.child_frame_id = self.base_frame_id
            transform.transform.translation.x = self.x
            transform.transform.translation.y = self.y
            transform.transform.translation.z = 0.0
            transform.transform.rotation.z = quat_z
            transform.transform.rotation.w = quat_w
            self.tf_broadcaster.sendTransform(transform)

    def publish_status(self, stamp, cmd_age, timed_out):
        status = {
            "stamp_sec": stamp.nanoseconds / 1e9,
            "mode": self.mode,
            "serial_enabled": self.serial_enabled,
            "serial_port": self.serial_port,
            "serial_protocol": self.serial_protocol,
            "serial_error": self.serial_error,
            "ardupilot": self.build_ardupilot_status(stamp),
            "emergency_stop": self.emergency_stop,
            "control_authorized": self.control_authorized,
            "authorization_expires_at": self.authorization_expires_at,
            "hardware_estop_detected": self.hardware_estop_detected,
            "cmd_vel_topic": self.cmd_vel_topic,
            "odom_topic": self.odom_topic,
            "publish_odom": self.publish_odom_enabled,
            "cmd_count": self.cmd_count,
            "cmd_age_sec": cmd_age,
            "cmd_timed_out": timed_out,
            "timeout_count": self.timeout_count,
            "target_linear": self.target_linear,
            "target_angular": self.target_angular,
            "current_linear": self.current_linear,
            "current_angular": self.current_angular,
            "x": self.x,
            "y": self.y,
            "yaw": self.yaw,
            "max_linear_speed": self.max_linear_speed,
            "max_angular_speed": self.max_angular_speed,
        }
        msg = String()
        msg.data = json.dumps(status, ensure_ascii=False)
        self.status_pub.publish(msg)

    def open_serial(self):
        if serial is None:
            self.serial_error = "pyserial is not installed"
            self.get_logger().error(self.serial_error)
            return
        try:
            self.serial_handle = serial.Serial(
                self.serial_port,
                self.serial_baudrate,
                timeout=self.serial_read_timeout_sec,
                write_timeout=self.serial_read_timeout_sec,
            )
            self.serial_error = None
            self.get_logger().info(
                f"opened chassis serial port {self.serial_port} @ {self.serial_baudrate}"
            )
        except Exception as exc:
            self.serial_error = str(exc)
            self.serial_handle = None
            self.get_logger().error(f"failed to open chassis serial port: {exc}")

    def send_serial_command(self, linear, angular):
        if (
            self.mode != "serial"
            or not self.serial_enabled
            or self.serial_handle is None
        ):
            return
        if abs(linear) > 1e-6 or abs(angular) > 1e-6:
            can_control, reason = self._check_three_level_safety()
            if not can_control:
                self.target_linear = 0.0
                self.target_angular = 0.0
                self.current_linear = 0.0
                self.current_angular = 0.0
                linear = 0.0
                angular = 0.0
                self.get_logger().warn(
                    f"serial command blocked: {reason}; sending zero command",
                    throttle_duration_sec=2.0,
                )
        payload = self.encode_placeholder_command(linear, angular)
        try:
            self.serial_handle.write(payload)
        except Exception as exc:
            self.serial_error = str(exc)
            self.get_logger().error(f"failed to write chassis serial command: {exc}")

    def poll_serial(self):
        if (
            self.mode != "serial"
            or not self.serial_enabled
            or self.serial_handle is None
        ):
            return
        try:
            if self.serial_handle.in_waiting:
                self.serial_handle.read(self.serial_handle.in_waiting)
        except Exception as exc:
            self.serial_error = str(exc)
            self.get_logger().error(f"failed to read chassis serial data: {exc}")

    def open_ardupilot(self):
        if mavutil is None:
            self.ardupilot_error = "pymavlink is not installed"
            self.get_logger().error(self.ardupilot_error)
            return
        try:
            conn_str = self.ardupilot_port
            self.ardupilot_conn = mavutil.mavlink_connection(
                conn_str,
                baud=self.ardupilot_baudrate,
                source_system=self.ardupilot_source_system,
                source_component=self.ardupilot_source_component,
                autoreconnect=True,
            )
            self.ardupilot_error = None
            self.get_logger().info(
                f"opened ArduPilot MAVLink {self.ardupilot_port} @ {self.ardupilot_baudrate}; "
                f"src_sys={self.ardupilot_source_system} tgt_sys={self.ardupilot_target_system} "
                f"readonly={self.ardupilot_readonly} control_enabled={self.ardupilot_control_enabled}"
            )
            self.request_ardupilot_sensor_streams()
        except Exception as exc:
            self.ardupilot_error = str(exc)
            self.ardupilot_conn = None
            self.get_logger().error(
                f"failed to open ArduPilot MAVLink port: {exc}"
            )

    def request_ardupilot_sensor_streams(self):
        if self.ardupilot_conn is None:
            return
        try:
            self.ardupilot_conn.mav.request_data_stream_send(
                self.ardupilot_target_system,
                self.ardupilot_target_component,
                mavutil.mavlink.MAV_DATA_STREAM_RAW_SENSORS,
                30,
                1,
            )
            self.ardupilot_conn.mav.request_data_stream_send(
                self.ardupilot_target_system,
                self.ardupilot_target_component,
                mavutil.mavlink.MAV_DATA_STREAM_EXTRA1,
                30,
                1,
            )
            self.ardupilot_conn.mav.request_data_stream_send(
                self.ardupilot_target_system,
                self.ardupilot_target_component,
                mavutil.mavlink.MAV_DATA_STREAM_RC_CHANNELS,
                10,
                1,
            )
        except Exception as exc:
            self.get_logger().warn(f"failed to request ArduPilot sensor streams: {exc}")

    def poll_ardupilot(self):
        if (
            self.mode != "ardupilot"
            or not self.ardupilot_enabled
            or self.ardupilot_conn is None
        ):
            return
        # pymavlink 串口：blocking=False 超时=0=不读字节；需 blocking=True + 极短 timeout
        # 单帧最长 ~280B；921600 下 ~2.4ms 能收完
        try:
            max_burst = 30  # 防止异常流卡死
            for _ in range(max_burst):
                msg = self.ardupilot_conn.recv_match(blocking=True, timeout=0.008)
                if msg is None:
                    break
                self.handle_mavlink_message(msg)
        except Exception as exc:
            self.ardupilot_error = str(exc)
            self.get_logger().error(f"failed to read MAVLink: {exc}")

    def handle_mavlink_message(self, msg):
        mtype = msg.get_type()
        if mtype == "BAD_DATA":
            return
        self.ardupilot_message_count += 1
        if mtype == "HEARTBEAT":
            self.ardupilot_system_id = msg.get_srcSystem()
            self.ardupilot_component_id = msg.get_srcComponent()
            self.ardupilot_type = int(msg.type)
            self.ardupilot_autopilot = int(msg.autopilot)
            self.ardupilot_base_mode = int(msg.base_mode)
            self.ardupilot_custom_mode = int(msg.custom_mode)
            self.ardupilot_system_status = int(msg.system_status)
            self.ardupilot_mavlink_version = int(msg.mavlink_version)
            self.ardupilot_heartbeat_count += 1
            self.ardupilot_last_heartbeat_time = self.get_clock().now()
            self.ardupilot_error = None
            # 硬件急停信号：仅 EMERGENCY(6) 触发。CRITICAL(5) 是未解锁正常状态
            self.hardware_estop_detected = self.ardupilot_system_status in (6,)
        elif mtype == "ATTITUDE":
            self.ardupilot_attitude_roll = float(msg.roll)
            self.ardupilot_attitude_pitch = float(msg.pitch)
            self.ardupilot_attitude_yaw = float(msg.yaw)
            self.ardupilot_attitude_yawspeed = float(msg.yawspeed)
        elif mtype in ("RAW_IMU", "SCALED_IMU", "SCALED_IMU2", "SCALED_IMU3"):
            self.publish_mavlink_imu(msg)
        elif mtype == "VFR_HUD":
            self.ardupilot_vfr_groundspeed = float(msg.groundspeed)
            self.ardupilot_vfr_heading_deg = int(msg.heading)
            self.ardupilot_vfr_throttle = int(msg.throttle)
        elif mtype == "SYS_STATUS":
            # battery: voltage_battery in mV, current_battery in cA (10 mA units)
            self.ardupilot_battery_voltage_v = float(msg.voltage_battery) / 1000.0
            self.ardupilot_battery_current_a = float(msg.current_battery) / 100.0
            self.ardupilot_battery_remaining_pct = int(msg.battery_remaining)
            self.ardupilot_errors_count = (
                int(msg.errors_count1) + int(msg.errors_count2)
                + int(msg.errors_count3) + int(msg.errors_count4)
            )
            self.ardupilot_sensors_health = int(msg.onboard_control_sensors_health)
        elif mtype == "LOCAL_POSITION_NED":
            self.ardupilot_local_x = float(msg.x)
            self.ardupilot_local_y = float(msg.y)
            self.ardupilot_local_vx = float(msg.vx)
            self.ardupilot_local_vy = float(msg.vy)
        elif mtype == "RC_CHANNELS":
            self.ardupilot_rc_channels = {
                f"chan{i}_raw": int(getattr(msg, f"chan{i}_raw", 0))
                for i in range(1, 9)
            }
            self.ardupilot_rc_channels["rssi"] = int(getattr(msg, "rssi", 0))
            self.ardupilot_rc_channels["chancount"] = int(getattr(msg, "chancount", 0))
        elif mtype == "SERVO_OUTPUT_RAW":
            self.ardupilot_servo_outputs = {
                f"servo{i}_raw": int(getattr(msg, f"servo{i}_raw", 0))
                for i in range(1, 9)
            }

    def publish_mavlink_imu(self, msg):
        if self.imu_pub is None:
            return
        # MAVLink body IMU is FRD; ROS base_link is FLU.
        accel_scale = 9.80665 / 1000.0
        gyro_scale = 0.001
        imu = Imu()
        imu.header.stamp = self.get_clock().now().to_msg()
        imu.header.frame_id = self.imu_frame_id
        imu.orientation_covariance[0] = -1.0
        imu.angular_velocity.x = float(msg.xgyro) * gyro_scale
        imu.angular_velocity.y = -float(msg.ygyro) * gyro_scale
        imu.angular_velocity.z = -float(msg.zgyro) * gyro_scale
        imu.linear_acceleration.x = float(msg.xacc) * accel_scale
        imu.linear_acceleration.y = -float(msg.yacc) * accel_scale
        imu.linear_acceleration.z = -float(msg.zacc) * accel_scale
        imu.angular_velocity_covariance[0] = 0.02
        imu.angular_velocity_covariance[4] = 0.02
        imu.angular_velocity_covariance[8] = 0.02
        imu.linear_acceleration_covariance[0] = 0.2
        imu.linear_acceleration_covariance[4] = 0.2
        imu.linear_acceleration_covariance[8] = 0.2
        self.imu_pub.publish(imu)
        self.ardupilot_imu_count += 1
        self.ardupilot_last_imu_time = self.get_clock().now()

    def send_ardupilot_command(self, linear, angular):
        if (
            self.mode != "ardupilot"
            or not self.ardupilot_enabled
            or self.ardupilot_conn is None
        ):
            return
        if self.ardupilot_readonly or not self.ardupilot_control_enabled:
            return
        # 安全闸：未授权或心跳挂掉，直接不下发
        can_control, reason = self._check_three_level_safety()
        if not can_control:
            return
        if self.ardupilot_last_heartbeat_time is None:
            return
        heartbeat_age = (
            self.get_clock().now() - self.ardupilot_last_heartbeat_time
        ).nanoseconds / 1e9
        if heartbeat_age > self.ardupilot_status_timeout_sec:
            return
        now = self.get_clock().now()
        if (now - self.ardupilot_last_send_time).nanoseconds / 1e9 < self.rc_send_period_sec:
            return
        self.ardupilot_last_send_time = now

        # 把 (linear, angular) 归一化为 [-1, +1] 再映射到 PWM
        lin_norm = self.clamp(linear / self.max_linear_speed, -1.0, 1.0) if self.max_linear_speed > 0 else 0.0
        ang_norm = self.clamp(angular / self.max_angular_speed, -1.0, 1.0) if self.max_angular_speed > 0 else 0.0
        if self.invert_throttle:
            lin_norm = -lin_norm
        if self.invert_steering:
            ang_norm = -ang_norm
        throttle_pwm = self.normalized_to_pwm(lin_norm)
        steering_pwm = self.normalized_to_pwm(
            ang_norm,
            self.rc_steering_pwm_min,
            self.rc_steering_pwm_mid,
            self.rc_steering_pwm_max,
        )

        # idle 时若 rc_release_on_idle=True，则发 0 释放通道（让 ArduPilot 用 RC）
        # 否则即使 idle 也发中位 PWM，避免 ArduPilot 把 0 误判为 throttle failsafe
        idle = abs(lin_norm) < 1e-6 and abs(ang_norm) < 1e-6
        if idle and self.rc_release_on_idle:
            throttle_pwm = 0
            steering_pwm = 0
        # else：idle 时 throttle_pwm/steering_pwm 已是中位 PWM（normalized_to_pwm(0)=pwm_mid）

        # RC_CHANNELS_OVERRIDE 八通道：未指定的填 65535（不覆盖）
        channels = [65535] * 8
        channels[self.rc_throttle_channel - 1] = int(throttle_pwm)
        channels[self.rc_steering_channel - 1] = int(steering_pwm)
        try:
            self.ardupilot_conn.mav.rc_channels_override_send(
                self.ardupilot_target_system,
                self.ardupilot_target_component,
                channels[0], channels[1], channels[2], channels[3],
                channels[4], channels[5], channels[6], channels[7],
            )
            self.last_rc_throttle_pwm = channels[self.rc_throttle_channel - 1]
            self.last_rc_steering_pwm = channels[self.rc_steering_channel - 1]
        except Exception as exc:
            self.ardupilot_error = f"rc_override send failed: {exc}"
            self.get_logger().error(self.ardupilot_error)

    def send_ardupilot_neutral_override(self, reason: str = "neutral stop"):
        if (
            self.mode != "ardupilot"
            or not self.ardupilot_enabled
            or self.ardupilot_conn is None
        ):
            return False, "ardupilot connection not available"
        if self.ardupilot_readonly or not self.ardupilot_control_enabled:
            return False, "ardupilot write disabled"
        if self.ardupilot_last_heartbeat_time is None:
            return False, "heartbeat_missing"
        heartbeat_age = (
            self.get_clock().now() - self.ardupilot_last_heartbeat_time
        ).nanoseconds / 1e9
        if heartbeat_age > self.ardupilot_status_timeout_sec:
            return False, "heartbeat_timeout"

        channels = [65535] * 8
        channels[self.rc_throttle_channel - 1] = int(self.rc_pwm_mid)
        channels[self.rc_steering_channel - 1] = int(self.rc_steering_pwm_mid)
        try:
            self.ardupilot_conn.mav.rc_channels_override_send(
                self.ardupilot_target_system,
                self.ardupilot_target_component,
                channels[0], channels[1], channels[2], channels[3],
                channels[4], channels[5], channels[6], channels[7],
            )
            self.last_rc_throttle_pwm = channels[self.rc_throttle_channel - 1]
            self.last_rc_steering_pwm = channels[self.rc_steering_channel - 1]
            self.get_logger().warn(f"neutral RC override sent: {reason}")
            return True, "neutral override sent"
        except Exception as exc:
            self.ardupilot_error = f"neutral rc_override send failed: {exc}"
            self.get_logger().error(self.ardupilot_error)
            return False, str(exc)

    def normalized_to_pwm(
        self,
        norm: float,
        pwm_min: Optional[int] = None,
        pwm_mid: Optional[int] = None,
        pwm_max: Optional[int] = None,
    ) -> int:
        """把 [-1, +1] 映射到 [pwm_min, pwm_max]，0 → pwm_mid。"""
        pwm_min = self.rc_pwm_min if pwm_min is None else pwm_min
        pwm_mid = self.rc_pwm_mid if pwm_mid is None else pwm_mid
        pwm_max = self.rc_pwm_max if pwm_max is None else pwm_max
        if norm >= 0:
            return int(round(pwm_mid + norm * (pwm_max - pwm_mid)))
        return int(round(pwm_mid + norm * (pwm_mid - pwm_min)))

    def build_ardupilot_status(self, stamp) -> Dict[str, object]:
        heartbeat_age = None
        heartbeat_ok = False
        imu_age = None
        if self.ardupilot_last_heartbeat_time is not None:
            heartbeat_age = (
                stamp - self.ardupilot_last_heartbeat_time
            ).nanoseconds / 1e9
            heartbeat_ok = heartbeat_age <= self.ardupilot_status_timeout_sec
        if self.ardupilot_last_imu_time is not None:
            imu_age = (stamp - self.ardupilot_last_imu_time).nanoseconds / 1e9
        return {
            "enabled": self.ardupilot_enabled,
            "readonly": self.ardupilot_readonly,
            "control_enabled": self.ardupilot_control_enabled,
            "port": self.ardupilot_port,
            "baudrate": self.ardupilot_baudrate,
            "error": self.ardupilot_error,
            "heartbeat_ok": heartbeat_ok,
            "heartbeat_count": self.ardupilot_heartbeat_count,
            "heartbeat_age_sec": heartbeat_age,
            "message_count": self.ardupilot_message_count,
            "imu_count": self.ardupilot_imu_count,
            "imu_age_sec": imu_age,
            "system_id": self.ardupilot_system_id,
            "component_id": self.ardupilot_component_id,
            "mavlink_version": self.ardupilot_mavlink_version,
            "type": self.ardupilot_type,
            "autopilot": self.ardupilot_autopilot,
            "base_mode": self.ardupilot_base_mode,
            "custom_mode": self.ardupilot_custom_mode,
            "custom_mode_name": self.ROVER_MODES.get(
                self.ardupilot_custom_mode
                if self.ardupilot_custom_mode is not None
                else -1,
                "UNKNOWN",
            ),
            "system_status": self.ardupilot_system_status,
            "attitude": {
                "roll": self.ardupilot_attitude_roll,
                "pitch": self.ardupilot_attitude_pitch,
                "yaw": self.ardupilot_attitude_yaw,
                "yawspeed": self.ardupilot_attitude_yawspeed,
            },
            "vfr_hud": {
                "groundspeed": self.ardupilot_vfr_groundspeed,
                "heading_deg": self.ardupilot_vfr_heading_deg,
                "throttle": self.ardupilot_vfr_throttle,
            },
            "battery": {
                "voltage_v": self.ardupilot_battery_voltage_v,
                "current_a": self.ardupilot_battery_current_a,
                "remaining_pct": self.ardupilot_battery_remaining_pct,
            },
            "errors_count": self.ardupilot_errors_count,
            "sensors_health": self.ardupilot_sensors_health,
            "local_position": {
                "x": self.ardupilot_local_x,
                "y": self.ardupilot_local_y,
                "vx": self.ardupilot_local_vx,
                "vy": self.ardupilot_local_vy,
            },
            "rc_channels": self.ardupilot_rc_channels,
            "servo_outputs": self.ardupilot_servo_outputs,
            "rc_override": {
                "steering_channel": self.rc_steering_channel,
                "throttle_channel": self.rc_throttle_channel,
                "pwm_min": self.rc_pwm_min,
                "pwm_mid": self.rc_pwm_mid,
                "pwm_max": self.rc_pwm_max,
                "steering_pwm_min": self.rc_steering_pwm_min,
                "steering_pwm_mid": self.rc_steering_pwm_mid,
                "steering_pwm_max": self.rc_steering_pwm_max,
                "last_throttle_pwm": self.last_rc_throttle_pwm,
                "last_steering_pwm": self.last_rc_steering_pwm,
            },
        }

    def encode_placeholder_command(self, linear, angular):
        line = f"CMD_VEL {linear:.4f} {angular:.4f}\n"
        return line.encode("ascii")

    @staticmethod
    def apply_accel_limit(current, target, max_accel, dt):
        if max_accel <= 0.0 or dt <= 0.0:
            return target
        delta = target - current
        limit = max_accel * dt
        if delta > limit:
            return current + limit
        if delta < -limit:
            return current - limit
        return target

    @staticmethod
    def clamp(value, lower, upper):
        return min(max(value, lower), upper)

    @staticmethod
    def normalize_angle(angle):
        while angle > math.pi:
            angle -= 2.0 * math.pi
        while angle < -math.pi:
            angle += 2.0 * math.pi
        return angle


def main(args=None):
    rclpy.init(args=args)
    node = ChassisBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except rclpy.executors.ExternalShutdownException:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
