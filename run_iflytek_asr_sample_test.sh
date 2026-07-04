#!/usr/bin/env bash
set -eo pipefail

cd /mnt/sdcard/iflytek_tts_df41b4a2/bin
export LD_LIBRARY_PATH="/mnt/sdcard/iflytek_tts_df41b4a2/libs/arm64:${LD_LIBRARY_PATH:-}"

# sample prompts twice: audio source and built-in pcm file id.
printf "0\n1\n0\n1\n" | timeout 35 ./asr_offline_record_sample_arm64
