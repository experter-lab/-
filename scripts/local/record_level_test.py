import audioop
import subprocess
import wave


path = "/tmp/m2_level_test.wav"
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
        "6",
        path,
    ],
    check=True,
)

with wave.open(path, "rb") as wav:
    data = wav.readframes(wav.getnframes())

rms = audioop.rms(data, 2)
peak = audioop.max(data, 2)
print(f"path={path}")
print(f"bytes={len(data)} rms={rms} peak={peak}")
