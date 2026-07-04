import os
from ament_index_python.packages import PackageNotFoundError, get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def load_private_env(path=os.path.expanduser("~/.config/medicine_robot/aikit.env")):
    values = {}
    try:
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip("'\"")
    except FileNotFoundError:
        pass
    return values

def credential_env_actions():
    values = load_private_env()
    actions = []
    for key in ("XF_AI_APPID", "XF_AI_API_KEY", "XF_AI_API_SECRET"):
        value = os.environ.get(key) or values.get(key)
        if value:
            actions.append(SetEnvironmentVariable(key, value))
    return actions


def generate_launch_description():
    stations_file = get_package_share_directory("medicine_task_manager") + "/config/stations.yaml"
    default_aikit_sdk_dir = os.environ.get("AIKIT_SDK_DIR", "/home/cgz/medicine_robot_ws/aikit_sdk")
    try:
        aikit_fsa_file = get_package_share_directory("wheeltec_aikit_esr") + "/config/medicine_cn_fsa.txt"
    except PackageNotFoundError:
        aikit_fsa_file = ""
    try:
        chassis_params_file_default = (
            get_package_share_directory("medicine_chassis_bridge")
            + "/config/chassis_bridge_ardupilot_serial_readonly.yaml"
        )
    except PackageNotFoundError:
        chassis_params_file_default = ""
    simulate_navigation_duration = LaunchConfiguration("simulate_navigation_duration")
    enable_voice_console = LaunchConfiguration("enable_voice_console")
    enable_tts = LaunchConfiguration("enable_tts")
    tts_backend = LaunchConfiguration("tts_backend")
    tts_rate = LaunchConfiguration("tts_rate")
    tts_volume = LaunchConfiguration("tts_volume")
    deduplicate_window_sec = LaunchConfiguration("deduplicate_window_sec")
    enable_web_dashboard = LaunchConfiguration("enable_web_dashboard")
    enable_m2_voice_bridge = LaunchConfiguration("enable_m2_voice_bridge")
    m2_serial_port = LaunchConfiguration("m2_serial_port")
    m2_baudrate = LaunchConfiguration("m2_baudrate")
    m2_command_topic = LaunchConfiguration("m2_command_topic")
    m2_raw_topic = LaunchConfiguration("m2_raw_topic")
    m2_publish_raw = LaunchConfiguration("m2_publish_raw")
    m2_deduplicate_window_sec = LaunchConfiguration("m2_deduplicate_window_sec")
    enable_voice_command_dispatcher = LaunchConfiguration("enable_voice_command_dispatcher")
    voice_words_topic = LaunchConfiguration("voice_words_topic")
    enable_aikit_esr = LaunchConfiguration("enable_aikit_esr")
    aikit_sdk_dir = LaunchConfiguration("aikit_sdk_dir")
    pulse_server = LaunchConfiguration("pulse_server")
    aikit_audio_backend = LaunchConfiguration("aikit_audio_backend")
    aikit_record_device = LaunchConfiguration("aikit_record_device")
    navigation_backend = LaunchConfiguration("navigation_backend")
    nav2_action_name = LaunchConfiguration("nav2_action_name")
    nav2_goal_timeout_sec = LaunchConfiguration("nav2_goal_timeout_sec")
    nav2_frame_id = LaunchConfiguration("nav2_frame_id")
    enable_chassis_bridge = LaunchConfiguration("enable_chassis_bridge")
    chassis_params_file = LaunchConfiguration("chassis_params_file")
    chassis_ardupilot_port = LaunchConfiguration("chassis_ardupilot_port")
    chassis_ardupilot_baudrate = LaunchConfiguration("chassis_ardupilot_baudrate")
    chassis_emergency_stop = LaunchConfiguration("chassis_emergency_stop")
    web_host = LaunchConfiguration("web_host")
    web_port = LaunchConfiguration("web_port")
    enable_vision_detector = LaunchConfiguration("enable_vision_detector")
    vision_drug_id = LaunchConfiguration("vision_drug_id")
    vision_drug_name = LaunchConfiguration("vision_drug_name")
    vision_drug_type = LaunchConfiguration("vision_drug_type")
    vision_confidence = LaunchConfiguration("vision_confidence")
    vision_loaded = LaunchConfiguration("vision_loaded")
    vision_source = LaunchConfiguration("vision_source")
    vision_input_mode = LaunchConfiguration("vision_input_mode")
    vision_camera_device = LaunchConfiguration("vision_camera_device")
    vision_camera_width = LaunchConfiguration("vision_camera_width")
    vision_camera_height = LaunchConfiguration("vision_camera_height")
    vision_camera_fps = LaunchConfiguration("vision_camera_fps")
    vision_camera_fourcc = LaunchConfiguration("vision_camera_fourcc")
    vision_camera_read_period_sec = LaunchConfiguration("vision_camera_read_period_sec")
    vision_enable_preview_server = LaunchConfiguration("vision_enable_preview_server")
    vision_preview_host = LaunchConfiguration("vision_preview_host")
    vision_preview_port = LaunchConfiguration("vision_preview_port")
    vision_preview_quality = LaunchConfiguration("vision_preview_quality")
    vision_preview_draw_overlay = LaunchConfiguration("vision_preview_draw_overlay")
    vision_preview_stream_period_sec = LaunchConfiguration("vision_preview_stream_period_sec")
    vision_enable_qr_recognition = LaunchConfiguration("vision_enable_qr_recognition")
    vision_enable_datamatrix_recognition = LaunchConfiguration("vision_enable_datamatrix_recognition")
    vision_enable_zxingcpp_recognition = LaunchConfiguration("vision_enable_zxingcpp_recognition")
    vision_enable_pylibdmtx_recognition = LaunchConfiguration("vision_enable_pylibdmtx_recognition")
    vision_qr_recognition_period_sec = LaunchConfiguration("vision_qr_recognition_period_sec")
    vision_qr_fast_mode = LaunchConfiguration("vision_qr_fast_mode")
    vision_qr_scale_factor = LaunchConfiguration("vision_qr_scale_factor")
    vision_qr_extra_scale_factors = LaunchConfiguration("vision_qr_extra_scale_factors")
    vision_external_decoder_period_sec = LaunchConfiguration("vision_external_decoder_period_sec")
    vision_external_decoder_timeout_sec = LaunchConfiguration("vision_external_decoder_timeout_sec")
    vision_enable_isolated_zxingcpp_recognition = LaunchConfiguration("vision_enable_isolated_zxingcpp_recognition")
    vision_enable_opencv_curved_qr_recognition = LaunchConfiguration("vision_enable_opencv_curved_qr_recognition")
    vision_recognized_code_hold_sec = LaunchConfiguration("vision_recognized_code_hold_sec")
    vision_enable_ocr_recognition = LaunchConfiguration("vision_enable_ocr_recognition")
    vision_ocr_recognition_period_sec = LaunchConfiguration("vision_ocr_recognition_period_sec")
    vision_ocr_language = LaunchConfiguration("vision_ocr_language")
    vision_ocr_psm = LaunchConfiguration("vision_ocr_psm")
    vision_ocr_scale_factor = LaunchConfiguration("vision_ocr_scale_factor")
    vision_ocr_min_confidence = LaunchConfiguration("vision_ocr_min_confidence")
    vision_ocr_max_chars = LaunchConfiguration("vision_ocr_max_chars")

    return LaunchDescription(credential_env_actions() + [
        DeclareLaunchArgument("simulate_navigation_duration", default_value="8.0"),
        DeclareLaunchArgument("enable_voice_console", default_value="true"),
        DeclareLaunchArgument("enable_tts", default_value="true"),
        DeclareLaunchArgument("tts_backend", default_value="auto"),
        DeclareLaunchArgument("tts_rate", default_value="0"),
        DeclareLaunchArgument("tts_volume", default_value="100"),
        DeclareLaunchArgument("deduplicate_window_sec", default_value="1.0"),
        DeclareLaunchArgument("enable_web_dashboard", default_value="true"),
        DeclareLaunchArgument("enable_m2_voice_bridge", default_value="false"),
        DeclareLaunchArgument(
            "m2_serial_port",
            default_value="/dev/serial/by-id/usb-WCH.CN_USB_Single_Serial_0004-if00",
        ),
        DeclareLaunchArgument("m2_baudrate", default_value="115200"),
        DeclareLaunchArgument("m2_command_topic", default_value="/medicine/voice_command"),
        DeclareLaunchArgument("m2_raw_topic", default_value="/medicine/m2_voice_raw"),
        DeclareLaunchArgument("m2_publish_raw", default_value="true"),
        DeclareLaunchArgument("m2_deduplicate_window_sec", default_value="1.0"),
        DeclareLaunchArgument("enable_voice_command_dispatcher", default_value="true"),
        DeclareLaunchArgument("voice_words_topic", default_value="/voice_words"),
        DeclareLaunchArgument("enable_aikit_esr", default_value="false"),
        DeclareLaunchArgument("aikit_sdk_dir", default_value=default_aikit_sdk_dir),
        DeclareLaunchArgument("pulse_server", default_value=os.environ.get("PULSE_SERVER", "")),
        DeclareLaunchArgument("aikit_audio_backend", default_value="pulse"),
        DeclareLaunchArgument("aikit_record_device", default_value="default"),
        DeclareLaunchArgument("navigation_backend", default_value="simulated"),
        DeclareLaunchArgument("nav2_action_name", default_value="navigate_to_pose"),
        DeclareLaunchArgument("nav2_goal_timeout_sec", default_value="120.0"),
        DeclareLaunchArgument("nav2_frame_id", default_value="map"),
        DeclareLaunchArgument("enable_chassis_bridge", default_value="false"),
        DeclareLaunchArgument("chassis_params_file", default_value=chassis_params_file_default),
        DeclareLaunchArgument("chassis_ardupilot_port", default_value="/dev/ttyS9"),
        DeclareLaunchArgument("chassis_ardupilot_baudrate", default_value="115200"),
        DeclareLaunchArgument("chassis_emergency_stop", default_value="true"),
        DeclareLaunchArgument("web_host", default_value="0.0.0.0"),
        DeclareLaunchArgument("web_port", default_value="8080"),
        DeclareLaunchArgument("enable_vision_detector", default_value="true"),
        DeclareLaunchArgument("vision_drug_id", default_value="drug_001"),
        DeclareLaunchArgument("vision_drug_name", default_value="\u964d\u538b\u836f"),
        DeclareLaunchArgument("vision_drug_type", default_value="tablet"),
        DeclareLaunchArgument("vision_confidence", default_value="0.98"),
        DeclareLaunchArgument("vision_loaded", default_value="true"),
        DeclareLaunchArgument("vision_source", default_value="mock"),
        DeclareLaunchArgument("vision_input_mode", default_value="mock"),
        DeclareLaunchArgument("vision_camera_device", default_value="/dev/video0"),
        DeclareLaunchArgument("vision_camera_width", default_value="640"),
        DeclareLaunchArgument("vision_camera_height", default_value="480"),
        DeclareLaunchArgument("vision_camera_fps", default_value="30"),
        DeclareLaunchArgument("vision_camera_fourcc", default_value="MJPG"),
        DeclareLaunchArgument("vision_camera_read_period_sec", default_value="0.05"),
        DeclareLaunchArgument("vision_enable_preview_server", default_value="true"),
        DeclareLaunchArgument("vision_preview_host", default_value="0.0.0.0"),
        DeclareLaunchArgument("vision_preview_port", default_value="8090"),
        DeclareLaunchArgument("vision_preview_quality", default_value="80"),
        DeclareLaunchArgument("vision_preview_draw_overlay", default_value="true"),
        DeclareLaunchArgument("vision_preview_stream_period_sec", default_value="0.05"),
        DeclareLaunchArgument("vision_enable_qr_recognition", default_value="true"),
        DeclareLaunchArgument("vision_enable_datamatrix_recognition", default_value="true"),
        DeclareLaunchArgument("vision_enable_zxingcpp_recognition", default_value="true"),
        DeclareLaunchArgument("vision_enable_pylibdmtx_recognition", default_value="false"),
        DeclareLaunchArgument("vision_qr_recognition_period_sec", default_value="0.1"),
        DeclareLaunchArgument("vision_qr_fast_mode", default_value="true"),
        DeclareLaunchArgument("vision_qr_scale_factor", default_value="1.5"),
        DeclareLaunchArgument("vision_qr_extra_scale_factors", default_value="1.5,2.0"),
        DeclareLaunchArgument("vision_external_decoder_period_sec", default_value="0.35"),
        DeclareLaunchArgument("vision_external_decoder_timeout_sec", default_value="1.5"),
        DeclareLaunchArgument("vision_enable_isolated_zxingcpp_recognition", default_value="true"),
        DeclareLaunchArgument("vision_enable_opencv_curved_qr_recognition", default_value="false"),
        DeclareLaunchArgument("vision_recognized_code_hold_sec", default_value="0.0"),
        DeclareLaunchArgument("vision_enable_ocr_recognition", default_value="false"),
        DeclareLaunchArgument("vision_ocr_recognition_period_sec", default_value="2.0"),
        DeclareLaunchArgument("vision_ocr_language", default_value="eng"),
        DeclareLaunchArgument("vision_ocr_psm", default_value="6"),
        DeclareLaunchArgument("vision_ocr_scale_factor", default_value="2.0"),
        DeclareLaunchArgument("vision_ocr_min_confidence", default_value="35.0"),
        DeclareLaunchArgument("vision_ocr_max_chars", default_value="500"),
        SetEnvironmentVariable("LANG", "C.UTF-8"),
        SetEnvironmentVariable("LC_ALL", "C.UTF-8"),
        SetEnvironmentVariable("PULSE_SERVER", pulse_server),
        SetEnvironmentVariable(
            "LD_LIBRARY_PATH",
            [PathJoinSubstitution([aikit_sdk_dir, "libs"]), ":", os.environ.get("LD_LIBRARY_PATH", "")],
        ),
        Node(
            package="medicine_task_manager",
            executable="task_manager_node",
            name="medicine_task_manager",
            output="screen",
            parameters=[{
                "stations_file": stations_file,
                "simulate_navigation_duration": ParameterValue(
                    simulate_navigation_duration,
                    value_type=float,
                ),
                "home_station": "pharmacy",
                "navigation_backend": navigation_backend,
                "nav2_action_name": nav2_action_name,
                "nav2_goal_timeout_sec": ParameterValue(
                    nav2_goal_timeout_sec,
                    value_type=float,
                ),
                "nav2_frame_id": nav2_frame_id,
            }],
        ),
        Node(
            package="medicine_voice_interaction",
            executable="voice_console_node",
            name="medicine_voice_console",
            output="screen",
            condition=IfCondition(enable_voice_console),
            parameters=[{
                "voice_topic": "/medicine/voice_text",
                "prefix": "[\u8bed\u97f3\u64ad\u62a5]",
                "enable_tts": ParameterValue(enable_tts, value_type=bool),
                "tts_backend": tts_backend,
                "tts_rate": ParameterValue(tts_rate, value_type=int),
                "tts_volume": ParameterValue(tts_volume, value_type=int),
                "deduplicate_window_sec": ParameterValue(
                    deduplicate_window_sec,
                    value_type=float,
                ),
            }],
        ),
        Node(
            package="medicine_voice_interaction",
            executable="voice_command_dispatcher_node",
            name="medicine_voice_command_dispatcher",
            output="screen",
            condition=IfCondition(enable_voice_command_dispatcher),
            parameters=[{
                "voice_words_topic": voice_words_topic,
                "command_topic": m2_command_topic,
                "voice_topic": "/medicine/voice_text",
                "source_station": "pharmacy",
                "default_medicine": "\u5e38\u89c4\u836f\u54c1",
                "deduplicate_window_sec": ParameterValue(
                    m2_deduplicate_window_sec,
                    value_type=float,
                ),
            }],
        ),
        Node(
            package="wheeltec_aikit_esr",
            executable="aikit_esr_node",
            name="wheeltec_aikit_esr",
            output="screen",
            condition=IfCondition(enable_aikit_esr),
            parameters=[{
                "sdk_dir": aikit_sdk_dir,
                "work_dir": aikit_sdk_dir,
                "resource_dir": PathJoinSubstitution([aikit_sdk_dir, "resource"]),
                "fsa_cn_path": aikit_fsa_file,
                "fsa_en_path": "",
                "audio_backend": aikit_audio_backend,
                "record_device": aikit_record_device,
                "voice_words_topic": voice_words_topic,
            }],
        ),
        Node(
            package="medicine_voice_interaction",
            executable="m2_voice_bridge_node",
            name="medicine_m2_voice_bridge",
            output="screen",
            condition=IfCondition(enable_m2_voice_bridge),
            parameters=[{
                "serial_port": m2_serial_port,
                "baudrate": ParameterValue(m2_baudrate, value_type=int),
                "command_topic": m2_command_topic,
                "raw_topic": m2_raw_topic,
                "publish_raw": ParameterValue(m2_publish_raw, value_type=bool),
                "deduplicate_window_sec": ParameterValue(
                    m2_deduplicate_window_sec,
                    value_type=float,
                ),
            }],
        ),
        Node(
            package="medicine_vision_detector",
            executable="drug_info_detector_node",
            name="medicine_vision_detector",
            output="screen",
            condition=IfCondition(enable_vision_detector),
            respawn=True,
            respawn_delay=2.0,
            parameters=[{
                "drug_id": vision_drug_id,
                "drug_name": vision_drug_name,
                "drug_type": vision_drug_type,
                "confidence": ParameterValue(vision_confidence, value_type=float),
                "loaded": ParameterValue(vision_loaded, value_type=bool),
                "source": vision_source,
                "input_mode": vision_input_mode,
                "camera_device": vision_camera_device,
                "camera_width": ParameterValue(vision_camera_width, value_type=int),
                "camera_height": ParameterValue(vision_camera_height, value_type=int),
                "camera_fps": ParameterValue(vision_camera_fps, value_type=int),
                "camera_fourcc": vision_camera_fourcc,
                "camera_read_period_sec": ParameterValue(vision_camera_read_period_sec, value_type=float),
                "enable_preview_server": ParameterValue(vision_enable_preview_server, value_type=bool),
                "preview_host": vision_preview_host,
                "preview_port": ParameterValue(vision_preview_port, value_type=int),
                "preview_quality": ParameterValue(vision_preview_quality, value_type=int),
                "preview_draw_overlay": ParameterValue(vision_preview_draw_overlay, value_type=bool),
                "preview_stream_period_sec": ParameterValue(vision_preview_stream_period_sec, value_type=float),
                "enable_qr_recognition": ParameterValue(vision_enable_qr_recognition, value_type=bool),
                "enable_datamatrix_recognition": ParameterValue(vision_enable_datamatrix_recognition, value_type=bool),
                "enable_zxingcpp_recognition": ParameterValue(vision_enable_zxingcpp_recognition, value_type=bool),
                "enable_pylibdmtx_recognition": ParameterValue(vision_enable_pylibdmtx_recognition, value_type=bool),
                "qr_recognition_period_sec": ParameterValue(vision_qr_recognition_period_sec, value_type=float),
                "qr_fast_mode": ParameterValue(vision_qr_fast_mode, value_type=bool),
                "qr_scale_factor": ParameterValue(vision_qr_scale_factor, value_type=float),
                "qr_extra_scale_factors": ParameterValue(vision_qr_extra_scale_factors, value_type=str),
                "external_decoder_period_sec": ParameterValue(vision_external_decoder_period_sec, value_type=float),
                "external_decoder_timeout_sec": ParameterValue(vision_external_decoder_timeout_sec, value_type=float),
                "enable_isolated_zxingcpp_recognition": ParameterValue(vision_enable_isolated_zxingcpp_recognition, value_type=bool),
                "enable_opencv_curved_qr_recognition": ParameterValue(vision_enable_opencv_curved_qr_recognition, value_type=bool),
                "recognized_code_hold_sec": ParameterValue(vision_recognized_code_hold_sec, value_type=float),
                "enable_ocr_recognition": ParameterValue(vision_enable_ocr_recognition, value_type=bool),
                "ocr_recognition_period_sec": ParameterValue(vision_ocr_recognition_period_sec, value_type=float),
                "ocr_language": vision_ocr_language,
                "ocr_psm": ParameterValue(vision_ocr_psm, value_type=int),
                "ocr_scale_factor": ParameterValue(vision_ocr_scale_factor, value_type=float),
                "ocr_min_confidence": ParameterValue(vision_ocr_min_confidence, value_type=float),
                "ocr_max_chars": ParameterValue(vision_ocr_max_chars, value_type=int),
                "drug_info_topic": "/medicine/drug_info",
                "status_topic": "/medicine/drug_recognition_status",
            }],
        ),
        Node(
            package="medicine_chassis_bridge",
            executable="chassis_bridge_node",
            name="chassis_bridge",
            output="screen",
            condition=IfCondition(enable_chassis_bridge),
            parameters=[
                chassis_params_file,
                {
                    "mode": "ardupilot",
                    "ardupilot_port": chassis_ardupilot_port,
                    "ardupilot_baudrate": ParameterValue(chassis_ardupilot_baudrate, value_type=int),
                    "ardupilot_enabled": True,
                    "ardupilot_readonly": True,
                    "ardupilot_control_enabled": False,
                    "emergency_stop": ParameterValue(chassis_emergency_stop, value_type=bool),
                    "publish_odom": False,
                    "publish_tf": False,
                    "serial_enabled": False,
                },
            ],
        ),
        Node(
            package="medicine_web_dashboard",
            executable="web_dashboard_node",
            name="medicine_web_dashboard",
            output="screen",
            condition=IfCondition(enable_web_dashboard),
            parameters=[{
                "host": web_host,
                "port": ParameterValue(web_port, value_type=int),
                "stations_file": stations_file,
                "service_timeout_sec": 5.0,
            }],
        ),
    ])
