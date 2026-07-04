import os
import subprocess
import sys

import dashscope
from dashscope.audio.asr import Recognition, RecognitionCallback


class Callback(RecognitionCallback):
    def on_complete(self):
        print("[asr-test] complete")

    def on_error(self, result):
        print("[asr-test] error", result)

    def on_event(self, result):
        print("[asr-test] event", result)


def main():
    env_file = "/mnt/sdcard/medicine_robot_secrets/ai_api.env"
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key, value)

    dashscope.api_key = os.environ.get("AI_CHAT_API_KEY")
    if not dashscope.api_key:
        raise SystemExit("AI_CHAT_API_KEY is not set")

    wav_path = "/tmp/dashscope_asr_test.wav"
    subprocess.run(
        [
            "arecord",
            "-D",
            "plughw:CARD=XFMDPV0018,DEV=0",
            "-f",
            "S16_LE",
            "-r",
            "16000",
            "-c",
            "1",
            "-d",
            "3",
            wav_path,
        ],
        check=True,
    )

    model = sys.argv[1] if len(sys.argv) > 1 else "paraformer-realtime-v2"
    rec = Recognition(model=model, format="wav", sample_rate=16000, callback=Callback())
    result = rec.call(wav_path)
    print("[asr-test] model", model)
    print("[asr-test] keys", list(result.keys()) if hasattr(result, "keys") else type(result))
    for key, value in result.items():
        print(f"[asr-test] {key}: {value}")
    try:
        print("[asr-test] sentence", result.get_sentence())
    except Exception as exc:
        print("[asr-test] sentence_error", repr(exc))


if __name__ == "__main__":
    main()
