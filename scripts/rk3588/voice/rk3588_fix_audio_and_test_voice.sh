#!/usr/bin/env bash
set -eo pipefail

WS="${MEDICINE_ROBOT_WS:-/mnt/sdcard/medicine_robot_ws}"

source /opt/ros/humble/setup.bash
source "${WS}/install/setup.bash"

amixer -c 1 sset 'Speaker' 100% unmute >/dev/null 2>&1 || true
amixer -c 1 sset 'Headphone' 90% unmute >/dev/null 2>&1 || true
amixer -c 1 sset 'PCM' 100% >/dev/null 2>&1 || true
amixer -c 1 sset 'AUXOUT' unmute >/dev/null 2>&1 || true
amixer -c 1 sset 'Left Output Mixer LDAC' on >/dev/null 2>&1 || true
amixer -c 1 sset 'Right Output Mixer RDAC' on >/dev/null 2>&1 || true

pactl set-default-sink alsa_output.platform-nau8822-sound.stereo-fallback >/dev/null 2>&1 || true
pactl set-sink-mute alsa_output.platform-nau8822-sound.stereo-fallback false >/dev/null 2>&1 || true
pactl set-sink-volume alsa_output.platform-nau8822-sound.stereo-fallback 100% >/dev/null 2>&1 || true
pactl set-sink-mute nx_voice_out false >/dev/null 2>&1 || true
pactl set-sink-volume nx_voice_out 100% >/dev/null 2>&1 || true

if [ -x /mnt/sdcard/rk3588_start_m2_voice.sh ]; then
  /mnt/sdcard/rk3588_start_m2_voice.sh >/tmp/rk3588_start_m2_voice_last.log 2>&1
fi

python3 - <<'PY'
import rclpy
import time
from std_msgs.msg import String

rclpy.init()
node = rclpy.create_node("voice_audio_fix_test_pub")
pub = node.create_publisher(String, "/medicine/voice_text", 10)
msg = String()
msg.data = "音频已打开，这是语音播报测试"
deadline = time.time() + 1.0
while pub.get_subscription_count() == 0 and time.time() < deadline:
    rclpy.spin_once(node, timeout_sec=0.1)
pub.publish(msg)
rclpy.spin_once(node, timeout_sec=0.3)
node.destroy_node()
rclpy.shutdown()
PY

sleep 4
tail -80 /tmp/medicine_voice_console.log || true
