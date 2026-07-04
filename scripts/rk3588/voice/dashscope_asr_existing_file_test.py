import os
import sys

import dashscope
from dashscope.audio.asr import Recognition, RecognitionCallback


class Callback(RecognitionCallback):
    pass


def load_env():
    path = "/mnt/sdcard/medicine_robot_secrets/ai_api.env"
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k, v)


load_env()
dashscope.api_key = os.environ.get("AI_CHAT_API_KEY")
model = sys.argv[1] if len(sys.argv) > 1 else "paraformer-realtime-v2"
path = sys.argv[2] if len(sys.argv) > 2 else "/tmp/m2_level_test.wav"

rec = Recognition(model=model, callback=Callback(), format="wav", sample_rate=16000)
result = rec.call(path)
print("model", model)
print("status", result.get("status_code"), "code", result.get("code"), "message", result.get("message"))
print("sentence", result.get_sentence())
print("keys", list(result.keys()))
