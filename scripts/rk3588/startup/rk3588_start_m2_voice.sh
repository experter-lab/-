#!/usr/bin/env bash
set -eo pipefail

WS="${MEDICINE_ROBOT_WS:-/mnt/sdcard/medicine_robot_ws}"
SERIAL_PORT="${M2_SERIAL_PORT:-/dev/serial/by-id/usb-WCH.CN_USB_Single_Serial_0004-if00}"
BAUDRATE="${M2_BAUDRATE:-115200}"
VOICE_TOPIC="${VOICE_TOPIC:-/medicine/voice_text}"
COMMAND_TOPIC="${M2_COMMAND_TOPIC:-/medicine/voice_command}"
RAW_TOPIC="${M2_RAW_TOPIC:-/medicine/m2_voice_raw}"
ENABLE_M2_BRIDGE="${ENABLE_M2_BRIDGE:-true}"
ENABLE_AI_VOICE_CHAT="${ENABLE_AI_VOICE_CHAT:-true}"
ENABLE_VISION_DRUG_VOICE="${ENABLE_VISION_DRUG_VOICE:-true}"
ENABLE_IFLYTEK_ASR="${ENABLE_IFLYTEK_ASR:-true}"
ASR_BACKEND="${ASR_BACKEND:-dashscope}"
TTS_BACKEND="${TTS_BACKEND:-iflytek_msc}"
PULSE_SINK="${PULSE_SINK-}"
APLAY_DEVICE="${APLAY_DEVICE:-plughw:CARD=Device,DEV=0}"
CI1302_SERIAL_PORT="${CI1302_SERIAL_PORT:-/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0}"
CI1302_BAUDRATE="${CI1302_BAUDRATE:-115200}"
CI1302_OPEN_DELAY_SEC="${CI1302_OPEN_DELAY_SEC:-3.0}"
IFLYTEK_MSC_LIB_PATH="${IFLYTEK_MSC_LIB_PATH:-/mnt/sdcard/iflytek_tts_sdk/tts_make_ros2/libs/arm64/libmsc.so}"
IFLYTEK_TTS_SDK_DIR="${IFLYTEK_TTS_SDK_DIR:-/mnt/sdcard/iflytek_tts_df41b4a2}"
IFLYTEK_APPID="${IFLYTEK_APPID:-df41b4a2}"
IFLYTEK_VOICE_NAME="${IFLYTEK_VOICE_NAME:-xiaoyan}"
IFLYTEK_SAMPLE_RATE="${IFLYTEK_SAMPLE_RATE:-16000}"
IFLYTEK_SPEED="${IFLYTEK_SPEED:-50}"
IFLYTEK_VOLUME="${IFLYTEK_VOLUME:-70}"
IFLYTEK_PITCH="${IFLYTEK_PITCH:-50}"
IFLYTEK_RDN="${IFLYTEK_RDN:-2}"
AI_CHAT_BASE_URL="${AI_CHAT_BASE_URL:-https://dashscope.aliyuncs.com/compatible-mode/v1}"
AI_CHAT_API_KEY="${AI_CHAT_API_KEY:-}"
AI_CHAT_MODEL="${AI_CHAT_MODEL:-qwen-plus}"
AI_CHAT_INPUT_TOPIC="${AI_CHAT_INPUT_TOPIC:-/voice_words}"
AI_CHAT_TRIGGER_PREFIXES="${AI_CHAT_TRIGGER_PREFIXES-}"
AI_CHAT_TIMEOUT_SEC="${AI_CHAT_TIMEOUT_SEC:-180.0}"
AI_CHAT_MAX_REPLY_CHARS="${AI_CHAT_MAX_REPLY_CHARS:-80}"
AI_CHAT_MAX_TOKENS="${AI_CHAT_MAX_TOKENS:-64}"
AI_CHAT_TEMPERATURE="${AI_CHAT_TEMPERATURE:-0.2}"
AI_CHAT_PATIENT_CONTEXT_TTL_SEC="${AI_CHAT_PATIENT_CONTEXT_TTL_SEC:-420.0}"
AI_CHAT_SYSTEM_PROMPT="${AI_CHAT_SYSTEM_PROMPT:-}"
ENABLE_KNOWLEDGE_BASE="${ENABLE_KNOWLEDGE_BASE:-true}"
KNOWLEDGE_DIR="${KNOWLEDGE_DIR:-/mnt/sdcard/medicine_robot_data/knowledge}"
KNOWLEDGE_MAX_CHUNKS="${KNOWLEDGE_MAX_CHUNKS:-5}"
KNOWLEDGE_MAX_CHARS="${KNOWLEDGE_MAX_CHARS:-1800}"
VISION_DRUG_INFO_TOPIC="${VISION_DRUG_INFO_TOPIC:-/medicine/drug_info}"
VISION_RECOGNITION_STATUS_TOPIC="${VISION_RECOGNITION_STATUS_TOPIC:-/medicine/drug_recognition_status}"
VISION_DRUG_MIN_CONFIDENCE="${VISION_DRUG_MIN_CONFIDENCE:-0.50}"
VISION_DRUG_ANNOUNCE_COOLDOWN_SEC="${VISION_DRUG_ANNOUNCE_COOLDOWN_SEC:-0.0}"
VISION_DRUG_CONTEXT_COOLDOWN_SEC="${VISION_DRUG_CONTEXT_COOLDOWN_SEC:-30.0}"
IFLYTEK_ASR_SDK_DIR="${IFLYTEK_ASR_SDK_DIR:-/mnt/sdcard/iflytek_tts_df41b4a2/bin}"
IFLYTEK_ASR_LIB_DIR="${IFLYTEK_ASR_LIB_DIR:-/mnt/sdcard/iflytek_tts_df41b4a2/libs/arm64}"
ASR_RECOGNITION_MODE="${ASR_RECOGNITION_MODE:-iat}"
ASR_CAPTURE_DEVICE="${ASR_CAPTURE_DEVICE:-auto}"
ASR_LISTEN_SECONDS="${ASR_LISTEN_SECONDS:-5}"
ASR_PAUSE_MS="${ASR_PAUSE_MS:-300}"
ASR_TUNE_CAPTURE_MIXER="${ASR_TUNE_CAPTURE_MIXER:-true}"
ASR_CAPTURE_CARD_NAME="${ASR_CAPTURE_CARD_NAME:-rockchipnau8822}"
ASR_PGA_GAIN="${ASR_PGA_GAIN:-42}"
ASR_ALC_TARGET="${ASR_ALC_TARGET:-14}"
DASHSCOPE_ASR_MODEL="${DASHSCOPE_ASR_MODEL:-paraformer-realtime-v2}"
DASHSCOPE_ASR_MODE="${DASHSCOPE_ASR_MODE:-chunk}"
DASHSCOPE_ASR_CHUNK_SECONDS="${DASHSCOPE_ASR_CHUNK_SECONDS:-2}"
DASHSCOPE_DEFAULT_LISTEN_SECONDS="${DASHSCOPE_DEFAULT_LISTEN_SECONDS:-300}"
DASHSCOPE_LISTEN_ON_START="${DASHSCOPE_LISTEN_ON_START:-true}"
DASHSCOPE_TTS_MUTE_BASE_SEC="${DASHSCOPE_TTS_MUTE_BASE_SEC:-4.0}"
DASHSCOPE_TTS_MUTE_PER_CHAR_SEC="${DASHSCOPE_TTS_MUTE_PER_CHAR_SEC:-0.20}"
DASHSCOPE_TTS_MUTE_MAX_SEC="${DASHSCOPE_TTS_MUTE_MAX_SEC:-28.0}"
DASHSCOPE_TTS_ECHO_FILTER_SEC="${DASHSCOPE_TTS_ECHO_FILTER_SEC:-90.0}"
DASHSCOPE_TTS_ECHO_WINDOW_SIMILARITY="${DASHSCOPE_TTS_ECHO_WINDOW_SIMILARITY:-0.70}"
DASHSCOPE_USE_TTS_STATE_MUTE="${DASHSCOPE_USE_TTS_STATE_MUTE:-true}"
DASHSCOPE_TTS_PRE_MUTE_SEC="${DASHSCOPE_TTS_PRE_MUTE_SEC:-0.8}"
DASHSCOPE_TTS_TAIL_MUTE_SEC="${DASHSCOPE_TTS_TAIL_MUTE_SEC:-0.8}"

source /opt/ros/humble/setup.bash
source "${WS}/install/setup.bash"

AI_CHAT_ENV_FILE="${AI_CHAT_ENV_FILE:-/mnt/sdcard/medicine_robot_secrets/ai_api.env}"
if [ -f "${AI_CHAT_ENV_FILE}" ]; then
  set -a
  # shellcheck disable=SC1090
  source "${AI_CHAT_ENV_FILE}"
  set +a
fi

if [ "${ENABLE_AI_VOICE_CHAT}" != "false" ] && [ -z "${AI_CHAT_API_KEY:-}" ]; then
  echo "[m2-voice] ERROR: AI_CHAT_API_KEY is not set." >&2
  echo "[m2-voice] Put it in ${AI_CHAT_ENV_FILE} or export it before running this script." >&2
  exit 2
fi

asr_capture_device_works() {
  local device="$1"
  rm -f /tmp/dashscope_asr_probe.wav
  arecord -D "${device}" -f S16_LE -r 16000 -c 1 -d 1 /tmp/dashscope_asr_probe.wav >/dev/null 2>&1
}

resolve_asr_capture_device() {
  if [ "${ASR_CAPTURE_DEVICE}" != "auto" ]; then
    echo "${ASR_CAPTURE_DEVICE}"
    return
  fi
  for candidate in \
    "plughw:CARD=XFMDPV0018,DEV=0" \
    "plughw:CARD=rockchipnau8822,DEV=0" \
    "default"; do
    if asr_capture_device_works "${candidate}"; then
      echo "${candidate}"
      return
    fi
  done
  echo "plughw:CARD=rockchipnau8822,DEV=0"
}
RESOLVED_ASR_CAPTURE_DEVICE="$(resolve_asr_capture_device)"

if [ "${ASR_TUNE_CAPTURE_MIXER}" != "false" ]; then
  amixer -c "${ASR_CAPTURE_CARD_NAME}" sset 'PGA' "${ASR_PGA_GAIN}" >/dev/null 2>&1 || true
  amixer -c "${ASR_CAPTURE_CARD_NAME}" sset 'ALC Enable' Both >/dev/null 2>&1 || true
  amixer -c "${ASR_CAPTURE_CARD_NAME}" sset 'ALC Target' "${ASR_ALC_TARGET}" >/dev/null 2>&1 || true
  amixer -c "${ASR_CAPTURE_CARD_NAME}" sset 'ALC Max Gain' 7 >/dev/null 2>&1 || true
  amixer -c "${ASR_CAPTURE_CARD_NAME}" sset 'ALC Min Gain' 1 >/dev/null 2>&1 || true
  amixer -c "${ASR_CAPTURE_CARD_NAME}" sset 'ALC Noise Gate' off >/dev/null 2>&1 || true
fi

kill_matching() {
  local pattern="$1"
  if pgrep -af "$pattern" >/tmp/rk3588_m2_voice_pids.txt 2>/dev/null; then
    awk '{print $1}' /tmp/rk3588_m2_voice_pids.txt | sort -u | while read -r pid; do
      if [ -n "$pid" ] && [ "$pid" != "$$" ]; then
        kill "$pid" 2>/dev/null || true
      fi
    done
    sleep 2
    if pgrep -af "$pattern" >/tmp/rk3588_m2_voice_pids.txt 2>/dev/null; then
      awk '{print $1}' /tmp/rk3588_m2_voice_pids.txt | sort -u | while read -r pid; do
        if [ -n "$pid" ] && [ "$pid" != "$$" ]; then
          kill -9 "$pid" 2>/dev/null || true
        fi
      done
      sleep 1
    fi
  fi
}

kill_matching "ros2 run medicine_voice_interaction voice_console_node|medicine_voice_interaction/lib/medicine_voice_interaction/voice_console_node"
kill_matching "ros2 run medicine_voice_interaction m2_voice_bridge_node|medicine_voice_interaction/lib/medicine_voice_interaction/m2_voice_bridge_node"
kill_matching "ai_voice_chat_bridge_node|medicine_voice_interaction.ai_voice_chat_bridge_node"
kill_matching "vision_drug_voice_bridge_node|medicine_vision_drug_voice_bridge"
kill_matching "ros2 run iflytek_asr_bridge iflytek_asr_bridge|iflytek_asr_bridge/lib/iflytek_asr_bridge/iflytek_asr_bridge"
kill_matching "dashscope_asr_bridge_node|medicine_voice_interaction.dashscope_asr_bridge_node"
kill_matching "arecord -D .*XFMDPV0018"

if [ "${ENABLE_M2_BRIDGE}" != "false" ] && [ ! -e "${SERIAL_PORT}" ]; then
  echo "[m2-voice] ERROR: serial port not found: ${SERIAL_PORT}" >&2
  echo "[m2-voice] Available candidates:" >&2
  ls -l /dev/ttyACM* /dev/ttyUSB* /dev/serial/by-id/* 2>/dev/null || true
  exit 2
fi

if [ "${TTS_BACKEND}" = "ci1302_serial" ] && [ ! -e "${CI1302_SERIAL_PORT}" ]; then
  echo "[m2-voice] ERROR: CI1302 serial port not found: ${CI1302_SERIAL_PORT}" >&2
  echo "[m2-voice] Available candidates:" >&2
  ls -l /dev/ttyACM* /dev/ttyUSB* /dev/serial/by-id/* 2>/dev/null || true
  exit 2
fi

: > /tmp/medicine_voice_console.log
: > /tmp/medicine_m2_voice_bridge.log
: > /tmp/iflytek_asr_bridge.log
: > /tmp/dashscope_asr_bridge.log

VOICE_ARGS=(
  ros2 run medicine_voice_interaction voice_console_node --ros-args
  -p voice_topic:="${VOICE_TOPIC}"
  -p enable_tts:=true
  -p tts_backend:="${TTS_BACKEND}"
  -p aplay_device:="${APLAY_DEVICE}"
  -p ci1302_serial_port:="${CI1302_SERIAL_PORT}"
  -p ci1302_baudrate:="${CI1302_BAUDRATE}"
  -p ci1302_open_delay_sec:="${CI1302_OPEN_DELAY_SEC}"
  -p iflytek_msc_lib_path:="${IFLYTEK_MSC_LIB_PATH}"
  -p iflytek_tts_sdk_dir:="${IFLYTEK_TTS_SDK_DIR}"
  -p iflytek_appid:="${IFLYTEK_APPID}"
  -p iflytek_voice_name:="${IFLYTEK_VOICE_NAME}"
  -p iflytek_sample_rate:="${IFLYTEK_SAMPLE_RATE}"
  -p iflytek_speed:="${IFLYTEK_SPEED}"
  -p iflytek_volume:="${IFLYTEK_VOLUME}"
  -p iflytek_pitch:="${IFLYTEK_PITCH}"
  -p iflytek_rdn:="${IFLYTEK_RDN}"
)
if [ -n "${PULSE_SINK}" ]; then
  VOICE_ARGS+=(-p pulse_sink:="${PULSE_SINK}")
fi

nohup "${VOICE_ARGS[@]}" > /tmp/medicine_voice_console.log 2>&1 < /dev/null &

if [ "${ENABLE_M2_BRIDGE}" != "false" ]; then
  nohup ros2 run medicine_voice_interaction m2_voice_bridge_node --ros-args \
    -p serial_port:="${SERIAL_PORT}" \
    -p baudrate:="${BAUDRATE}" \
    -p command_topic:="${COMMAND_TOPIC}" \
    -p raw_topic:="${RAW_TOPIC}" \
    -p publish_raw:=true \
    > /tmp/medicine_m2_voice_bridge.log 2>&1 < /dev/null &
else
  echo "[m2-voice] M2 bridge disabled; voice console only." > /tmp/medicine_m2_voice_bridge.log
fi

if [ "${ENABLE_IFLYTEK_ASR}" != "false" ] && [ "${ASR_BACKEND}" = "dashscope" ]; then
  nohup ros2 run medicine_voice_interaction dashscope_asr_bridge_node --ros-args \
    -p capture_device:="${RESOLVED_ASR_CAPTURE_DEVICE}" \
    -p model:="${DASHSCOPE_ASR_MODEL}" \
    -p mode:="${DASHSCOPE_ASR_MODE}" \
    -p chunk_seconds:="${DASHSCOPE_ASR_CHUNK_SECONDS}" \
    -p listen_on_start:="${DASHSCOPE_LISTEN_ON_START}" \
    -p default_listen_seconds:="${DASHSCOPE_DEFAULT_LISTEN_SECONDS}" \
    -p tts_mute_base_sec:="${DASHSCOPE_TTS_MUTE_BASE_SEC}" \
    -p tts_mute_per_char_sec:="${DASHSCOPE_TTS_MUTE_PER_CHAR_SEC}" \
    -p tts_mute_max_sec:="${DASHSCOPE_TTS_MUTE_MAX_SEC}" \
    -p tts_echo_filter_sec:="${DASHSCOPE_TTS_ECHO_FILTER_SEC}" \
    -p tts_echo_window_similarity:="${DASHSCOPE_TTS_ECHO_WINDOW_SIMILARITY}" \
    -p use_tts_state_mute:="${DASHSCOPE_USE_TTS_STATE_MUTE}" \
    -p tts_pre_mute_sec:="${DASHSCOPE_TTS_PRE_MUTE_SEC}" \
    -p tts_tail_mute_sec:="${DASHSCOPE_TTS_TAIL_MUTE_SEC}" \
    > /tmp/dashscope_asr_bridge.log 2>&1 < /dev/null &
  echo "[m2-voice] iFlytek ASR bridge disabled; DashScope ASR enabled." > /tmp/iflytek_asr_bridge.log
elif [ "${ENABLE_IFLYTEK_ASR}" != "false" ]; then
  LD_LIBRARY_PATH="${IFLYTEK_ASR_LIB_DIR}:${LD_LIBRARY_PATH:-}" \
  nohup ros2 run iflytek_asr_bridge iflytek_asr_bridge --ros-args \
    -p appid:="${IFLYTEK_APPID}" \
    -p sdk_dir:="${IFLYTEK_ASR_SDK_DIR}" \
    -p recognition_mode:="${ASR_RECOGNITION_MODE}" \
    -p capture_device:="${RESOLVED_ASR_CAPTURE_DEVICE}" \
    -p listen_seconds:="${ASR_LISTEN_SECONDS}" \
    -p pause_ms:="${ASR_PAUSE_MS}" \
    > /tmp/iflytek_asr_bridge.log 2>&1 < /dev/null &
else
  echo "[m2-voice] iFlytek ASR bridge disabled." > /tmp/iflytek_asr_bridge.log
fi

if [ "${ENABLE_AI_VOICE_CHAT}" != "false" ]; then
  : > /tmp/medicine_ai_voice_chat_bridge.log
  AI_CHAT_ARGS=(
    python3 -m medicine_voice_interaction.ai_voice_chat_bridge_node --ros-args
    -p voice_words_topic:="${AI_CHAT_INPUT_TOPIC}"
    -p voice_topic:="${VOICE_TOPIC}"
    -p base_url:="${AI_CHAT_BASE_URL}"
    -p use_model:="${AI_CHAT_MODEL}"
    -p temperature:="${AI_CHAT_TEMPERATURE}"
    -p timeout_sec:="${AI_CHAT_TIMEOUT_SEC}"
    -p max_reply_chars:="${AI_CHAT_MAX_REPLY_CHARS}"
    -p max_tokens:="${AI_CHAT_MAX_TOKENS}"
    -p patient_context_ttl_sec:="${AI_CHAT_PATIENT_CONTEXT_TTL_SEC}"
    -p enable_knowledge_base:="${ENABLE_KNOWLEDGE_BASE}"
    -p knowledge_dir:="${KNOWLEDGE_DIR}"
    -p knowledge_max_chunks:="${KNOWLEDGE_MAX_CHUNKS}"
    -p knowledge_max_chars:="${KNOWLEDGE_MAX_CHARS}"
  )
  if [ -n "${AI_CHAT_SYSTEM_PROMPT}" ]; then
    AI_CHAT_ARGS+=(-p system_prompt:="${AI_CHAT_SYSTEM_PROMPT}")
  fi
  if [ -n "${AI_CHAT_TRIGGER_PREFIXES}" ]; then
    AI_CHAT_ARGS+=(-p trigger_prefixes:="${AI_CHAT_TRIGGER_PREFIXES}")
  fi
  nohup "${AI_CHAT_ARGS[@]}" > /tmp/medicine_ai_voice_chat_bridge.log 2>&1 < /dev/null &
else
  echo "[m2-voice] AI voice chat bridge disabled." > /tmp/medicine_ai_voice_chat_bridge.log
fi

if [ "${ENABLE_VISION_DRUG_VOICE}" != "false" ]; then
  : > /tmp/medicine_vision_drug_voice_bridge.log
  nohup ros2 run medicine_voice_interaction vision_drug_voice_bridge_node --ros-args \
    -p drug_info_topic:="${VISION_DRUG_INFO_TOPIC}" \
    -p recognition_status_topic:="${VISION_RECOGNITION_STATUS_TOPIC}" \
    -p voice_topic:="${VOICE_TOPIC}" \
    -p ai_context_topic:=/medicine/vision_drug_context \
    -p min_confidence:="${VISION_DRUG_MIN_CONFIDENCE}" \
    -p announce_cooldown_sec:="${VISION_DRUG_ANNOUNCE_COOLDOWN_SEC}" \
    -p context_cooldown_sec:="${VISION_DRUG_CONTEXT_COOLDOWN_SEC}" \
    -p enable_voice_announce:=false \
    > /tmp/medicine_vision_drug_voice_bridge.log 2>&1 < /dev/null &
else
  echo "[m2-voice] Vision drug voice bridge disabled." > /tmp/medicine_vision_drug_voice_bridge.log
fi

sleep 3

echo "[m2-voice] nodes:"
ros2 node list | grep -E "voice|m2|ai" || true

echo "[m2-voice] topics:"
ros2 topic info "${VOICE_TOPIC}" || true
ros2 topic info "${COMMAND_TOPIC}" || true
ros2 topic info "${RAW_TOPIC}" || true
ros2 topic info /medicine/ai_chat_response || true
ros2 topic info /medicine/asr_text || true

echo "[m2-voice] voice log:"
tail -20 /tmp/medicine_voice_console.log || true

echo "[m2-voice] bridge log:"
tail -20 /tmp/medicine_m2_voice_bridge.log || true

echo "[m2-voice] asr log:"
tail -20 /tmp/iflytek_asr_bridge.log || true
tail -20 /tmp/dashscope_asr_bridge.log || true

echo "[m2-voice] ai chat log:"
tail -20 /tmp/medicine_ai_voice_chat_bridge.log || true

echo "[m2-voice] vision voice log:"
tail -20 /tmp/medicine_vision_drug_voice_bridge.log || true

