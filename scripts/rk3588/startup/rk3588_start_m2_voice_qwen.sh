#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${AI_CHAT_ENV_FILE:-/mnt/sdcard/medicine_robot_secrets/ai_api.env}"

if [ -f "${ENV_FILE}" ]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

if [ -z "${AI_CHAT_API_KEY:-}" ]; then
  echo "[m2-voice-qwen] ERROR: AI_CHAT_API_KEY is not set." >&2
  echo "[m2-voice-qwen] Put it in ${ENV_FILE} or export it before running this script." >&2
  exit 2
fi

export ENABLE_AI_VOICE_CHAT="${ENABLE_AI_VOICE_CHAT:-true}"
export AI_CHAT_BASE_URL="${AI_CHAT_BASE_URL:-https://dashscope.aliyuncs.com/compatible-mode/v1}"
export AI_CHAT_MODEL="${AI_CHAT_MODEL:-qwen-plus}"
export AI_CHAT_TIMEOUT_SEC="${AI_CHAT_TIMEOUT_SEC:-60.0}"
export AI_CHAT_MAX_REPLY_CHARS="${AI_CHAT_MAX_REPLY_CHARS:-220}"
export AI_CHAT_MAX_TOKENS="${AI_CHAT_MAX_TOKENS:-160}"
export AI_CHAT_SYSTEM_PROMPT="${AI_CHAT_SYSTEM_PROMPT:-你是医院配送机器人，也是药品和疾病注意事项科普助手。用简短中文语音回答，通常不超过三句话。可以说明常见用药方法、副作用、漏服处理、疾病护理和就医提醒。不要诊断疾病，不要调整处方剂量，不要建议停药换药。遇到胸痛、呼吸困难、意识不清、大出血、孕妇儿童老人复杂用药、多药联用或过敏等风险，提醒立即联系医生或护士。不要输出思考过程。}"
export AI_CHAT_TRIGGER_PREFIXES="${AI_CHAT_TRIGGER_PREFIXES-}"

exec /mnt/sdcard/rk3588_start_m2_voice.sh
