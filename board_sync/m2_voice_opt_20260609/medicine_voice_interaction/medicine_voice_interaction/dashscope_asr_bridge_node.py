import os
import json
import queue
import re
from difflib import SequenceMatcher
import subprocess
import threading
import time

import dashscope
import rclpy
from dashscope.audio.asr import Recognition, RecognitionCallback, RecognitionResult
from rclpy.node import Node
from std_msgs.msg import String


class DashScopeAsrBridgeNode(Node):
    def __init__(self):
        super().__init__("dashscope_asr_bridge")
        self.declare_parameter("capture_device", "plughw:CARD=XFMDPV0018,DEV=0")
        self.declare_parameter("model", "paraformer-realtime-v2")
        self.declare_parameter("format", "pcm")
        self.declare_parameter("sample_rate", 16000)
        self.declare_parameter("channels", 1)
        self.declare_parameter("frame_ms", 100)
        self.declare_parameter("mode", "chunk")
        self.declare_parameter("chunk_seconds", 2)
        self.declare_parameter("voice_words_topic", "/voice_words")
        self.declare_parameter("asr_text_topic", "/medicine/asr_text")
        self.declare_parameter("control_topic", "/medicine/asr_control")
        self.declare_parameter("tts_topic", "/medicine/voice_text")
        self.declare_parameter("tts_state_topic", "/medicine/tts_state")
        self.declare_parameter("listen_on_start", False)
        self.declare_parameter("default_listen_seconds", 60)
        self.declare_parameter("min_text_chars", 2)
        self.declare_parameter("suppress_during_tts", True)
        self.declare_parameter("tts_mute_base_sec", 4.0)
        self.declare_parameter("tts_mute_per_char_sec", 0.20)
        self.declare_parameter("tts_mute_max_sec", 28.0)
        self.declare_parameter("tts_echo_filter_sec", 90.0)
        self.declare_parameter("tts_echo_similarity", 0.68)
        self.declare_parameter("tts_echo_window_similarity", 0.70)
        self.declare_parameter("use_tts_state_mute", True)
        self.declare_parameter("tts_pre_mute_sec", 0.8)
        self.declare_parameter("tts_tail_mute_sec", 0.8)
        self.declare_parameter("env_file", "/mnt/sdcard/medicine_robot_secrets/ai_api.env")

        self.capture_device = self.get_parameter("capture_device").value
        self.model = self.get_parameter("model").value
        self.audio_format = self.get_parameter("format").value
        self.sample_rate = int(self.get_parameter("sample_rate").value)
        self.channels = int(self.get_parameter("channels").value)
        self.frame_ms = int(self.get_parameter("frame_ms").value)
        self.mode = self.get_parameter("mode").value
        self.chunk_seconds = int(self.get_parameter("chunk_seconds").value)
        self.listen_on_start = bool(self.get_parameter("listen_on_start").value)
        self.default_listen_seconds = int(self.get_parameter("default_listen_seconds").value)
        self.min_text_chars = int(self.get_parameter("min_text_chars").value)
        self.suppress_during_tts = bool(self.get_parameter("suppress_during_tts").value)
        self.tts_mute_base_sec = float(self.get_parameter("tts_mute_base_sec").value)
        self.tts_mute_per_char_sec = float(self.get_parameter("tts_mute_per_char_sec").value)
        self.tts_mute_max_sec = float(self.get_parameter("tts_mute_max_sec").value)
        self.tts_echo_filter_sec = float(self.get_parameter("tts_echo_filter_sec").value)
        self.tts_echo_similarity = float(self.get_parameter("tts_echo_similarity").value)
        self.tts_echo_window_similarity = float(self.get_parameter("tts_echo_window_similarity").value)
        self.use_tts_state_mute = bool(self.get_parameter("use_tts_state_mute").value)
        self.tts_pre_mute_sec = float(self.get_parameter("tts_pre_mute_sec").value)
        self.tts_tail_mute_sec = float(self.get_parameter("tts_tail_mute_sec").value)
        self.env_file = self.get_parameter("env_file").value

        self.load_env_file()
        dashscope.api_key = os.environ.get("AI_CHAT_API_KEY") or os.environ.get("DASHSCOPE_API_KEY")
        if not dashscope.api_key:
            raise RuntimeError("AI_CHAT_API_KEY or DASHSCOPE_API_KEY is not set")

        self.voice_pub = self.create_publisher(String, self.get_parameter("voice_words_topic").value, 10)
        self.asr_pub = self.create_publisher(String, self.get_parameter("asr_text_topic").value, 10)
        self.create_subscription(String, self.get_parameter("control_topic").value, self.on_control, 10)
        self.create_subscription(String, self.get_parameter("tts_topic").value, self.on_tts_voice, 10)
        self.create_subscription(String, self.get_parameter("tts_state_topic").value, self.on_tts_state, 10)
        self.text_queue = queue.Queue()
        self.listen_until = time.monotonic() + self.default_listen_seconds if self.listen_on_start else 0.0
        self.listen_lock = threading.Lock()
        self.muted_until = 0.0
        self.tts_active = False
        self.mute_generation = 0
        self.mute_lock = threading.Lock()
        self.recent_tts_text = ""
        self.recent_tts_until = 0.0
        self.running = True
        self.worker = threading.Thread(target=self.run_asr, daemon=True)
        self.worker.start()

        self.timer = self.create_timer(0.1, self.publish_pending_text)
        self.get_logger().info(
            f"DashScope ASR started. device={self.capture_device}, model={self.model}, mode={self.mode}, "
            f"sample_rate={self.sample_rate}"
        )

    def on_control(self, msg):
        try:
            payload = json.loads(msg.data)
        except Exception:
            payload = {"action": msg.data}
        action = str(payload.get("action") or "listen").strip().lower()
        if action in {"stop", "off", "idle"}:
            with self.listen_lock:
                self.listen_until = 0.0
            self.get_logger().info("DashScope ASR listening stopped by control message.")
            return
        duration = int(payload.get("duration_sec") or self.default_listen_seconds)
        duration = max(1, min(duration, 300))
        with self.listen_lock:
            self.listen_until = max(self.listen_until, time.monotonic() + duration)
        self.get_logger().info(f"DashScope ASR listening enabled for {duration}s.")

    def on_tts_voice(self, msg):
        if not self.suppress_during_tts:
            return
        text = str(msg.data or "").strip()
        if not text:
            return
        if self.use_tts_state_mute:
            duration = max(0.2, self.tts_pre_mute_sec)
        else:
            duration = self.tts_mute_base_sec + len(text) * self.tts_mute_per_char_sec
            duration = max(0.5, min(duration, self.tts_mute_max_sec))
        with self.mute_lock:
            now = time.monotonic()
            self.muted_until = max(self.muted_until, now + duration)
            self.recent_tts_text = text
            self.recent_tts_until = now + max(duration, self.tts_echo_filter_sec)
            self.mute_generation += 1
        if self.use_tts_state_mute:
            self.get_logger().info(f"DashScope ASR pre-muted before TTS state for {duration:.1f}s.")
        else:
            self.get_logger().info(f"DashScope ASR muted during TTS for {duration:.1f}s.")

    def on_tts_state(self, msg):
        if not self.suppress_during_tts or not self.use_tts_state_mute:
            return
        raw = str(msg.data or "").strip()
        if not raw:
            return
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"state": raw}
        state = str(payload.get("state") or "").strip().lower()
        text = str(payload.get("text") or "").strip()
        with self.mute_lock:
            now = time.monotonic()
            if text:
                self.recent_tts_text = text
                self.recent_tts_until = now + self.tts_echo_filter_sec
            if state in {"start", "playing", "begin"}:
                self.tts_active = True
                self.muted_until = max(self.muted_until, now + min(self.tts_mute_max_sec, 20.0))
                self.mute_generation += 1
                self.get_logger().info("DashScope ASR muted: TTS playback started.")
            elif state in {"end", "done", "stop", "finish", "finished"}:
                self.tts_active = False
                self.muted_until = max(self.muted_until, now + max(0.0, self.tts_tail_mute_sec))
                self.mute_generation += 1
                self.get_logger().info(f"DashScope ASR TTS playback ended; tail mute {self.tts_tail_mute_sec:.1f}s.")

    def is_listening(self):
        with self.listen_lock:
            listening = time.monotonic() < self.listen_until
        return listening and not self.is_muted()

    def is_muted(self):
        with self.mute_lock:
            return self.tts_active or time.monotonic() < self.muted_until

    def current_mute_generation(self):
        with self.mute_lock:
            return self.mute_generation

    def load_env_file(self):
        if not self.env_file or not os.path.exists(self.env_file):
            return
        with open(self.env_file, "r", encoding="utf-8") as env:
            for line in env:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key, value)

    def normalize_echo_text(self, text):
        normalized = str(text or "").lower()
        normalized = re.sub(r"[\s\W_]+", "", normalized, flags=re.UNICODE)
        return normalized

    def max_window_similarity(self, candidate, reference):
        """Compare short ASR fragments against windows of the last TTS text.

        TTS leakage is often recognized with one or two wrong characters, e.g.
        "药盒上有字" -> "药盒上有刺", so exact substring matching is not enough.
        """
        candidate = str(candidate or "")
        reference = str(reference or "")
        n = len(candidate)
        if n < 3 or not reference:
            return 0.0
        if n >= len(reference):
            return SequenceMatcher(None, candidate, reference).ratio()
        best = 0.0
        # Try several window sizes so fragments with a few extra/missing chars are still caught.
        for size in {n, min(len(reference), n + 3), min(len(reference), n + 6), min(len(reference), n + 10)}:
            if size <= 0 or size > len(reference):
                continue
            step = max(1, n // 3)
            for start in range(0, len(reference) - size + 1, step):
                ratio = SequenceMatcher(None, candidate, reference[start:start + size]).ratio()
                if ratio > best:
                    best = ratio
                    if best >= self.tts_echo_window_similarity:
                        return best
            # Always include the tail window; many echoes happen at the end of playback.
            tail = reference[-size:]
            ratio = SequenceMatcher(None, candidate, tail).ratio()
            if ratio > best:
                best = ratio
                if best >= self.tts_echo_window_similarity:
                    return best
        return best

    def is_probable_tts_echo(self, text):
        candidate = self.normalize_echo_text(text)
        if len(candidate) < max(3, self.min_text_chars):
            return False
        with self.mute_lock:
            recent = self.recent_tts_text
            active = time.monotonic() < self.recent_tts_until
        if not active or not recent:
            return False
        reference = self.normalize_echo_text(recent)
        if not reference:
            return False
        if candidate in reference or reference in candidate:
            return True
        # Short fragments are common after TTS playback; compare against local windows of the TTS text.
        if self.max_window_similarity(candidate, reference) >= self.tts_echo_window_similarity:
            return True
        ratio = SequenceMatcher(None, candidate, reference).ratio()
        return ratio >= self.tts_echo_similarity

    def publish_pending_text(self):
        while True:
            try:
                text = self.text_queue.get_nowait()
            except queue.Empty:
                return
            msg = String()
            msg.data = text
            self.voice_pub.publish(msg)
            self.asr_pub.publish(msg)
            self.get_logger().info(f"ASR recognized: {text}")

    def run_asr(self):
        if self.mode == "chunk":
            self.run_chunk_asr()
        else:
            self.run_stream_asr()

    def run_chunk_asr(self):
        callback = self.Callback(self)
        recognition = Recognition(
            model=self.model,
            callback=callback,
            format="wav",
            sample_rate=self.sample_rate,
        )
        wav_path = "/tmp/dashscope_asr_chunk.wav"
        cmd = [
            "arecord",
            "-D",
            self.capture_device,
            "-f",
            "S16_LE",
            "-r",
            str(self.sample_rate),
            "-c",
            str(self.channels),
            "-d",
            str(self.chunk_seconds),
            wav_path,
        ]
        while self.running and rclpy.ok():
            if not self.is_listening():
                time.sleep(0.2)
                continue
            mute_generation = self.current_mute_generation()
            try:
                subprocess.run(
                    cmd,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=self.chunk_seconds + 3,
                )
                if self.is_muted() or self.current_mute_generation() != mute_generation:
                    self.get_logger().info("DashScope ASR chunk ignored during TTS mute.")
                    continue
                result = recognition.call(wav_path)
                self.handle_sentence_result(result.get_sentence())
            except Exception as exc:
                self.get_logger().warn(f"DashScope ASR chunk error: {exc}")
                time.sleep(1)

    def run_stream_asr(self):
        callback = self.Callback(self)
        recognition = Recognition(
            model=self.model,
            callback=callback,
            format=self.audio_format,
            sample_rate=self.sample_rate,
        )

        frame_bytes = int(self.sample_rate * self.channels * 2 * self.frame_ms / 1000)
        cmd = [
            "arecord",
            "-D",
            self.capture_device,
            "-f",
            "S16_LE",
            "-r",
            str(self.sample_rate),
            "-c",
            str(self.channels),
            "-t",
            "raw",
            "-q",
        ]

        while self.running and rclpy.ok():
            if not self.is_listening():
                time.sleep(0.2)
                continue
            proc = None
            try:
                recognition.start()
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.get_logger().info("DashScope ASR streaming started.")
                while self.running and rclpy.ok():
                    if not self.is_listening():
                        break
                    data = proc.stdout.read(frame_bytes)
                    if not data:
                        break
                    recognition.send_audio_frame(data)
                recognition.stop()
            except Exception as exc:
                self.get_logger().warn(f"DashScope ASR loop error: {exc}")
                try:
                    recognition.stop()
                except Exception:
                    pass
                time.sleep(2)
            finally:
                if proc and proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        proc.kill()

    def destroy_node(self):
        self.running = False
        super().destroy_node()

    class Callback(RecognitionCallback):
        def __init__(self, node):
            self.node = node

        def on_event(self, result: RecognitionResult):
            self.node.handle_sentence_result(result.get_sentence(), final_only=True)

        def on_error(self, result):
            code = result.get("code", "") if hasattr(result, "get") else ""
            message = result.get("message", "") if hasattr(result, "get") else ""
            request_id = result.get("request_id", "") if hasattr(result, "get") else ""
            self.node.get_logger().warn(
                f"DashScope ASR error: code={code}, message={message}, request_id={request_id}"
            )

        def on_complete(self):
            self.node.get_logger().info("DashScope ASR complete.")

        def on_close(self):
            self.node.get_logger().info("DashScope ASR closed.")

    def handle_sentence_result(self, sentence_result, final_only=False):
        if self.is_muted():
            self.get_logger().info("DashScope ASR result ignored during TTS mute.")
            return
        if not sentence_result:
            return
        sentences = sentence_result if isinstance(sentence_result, list) else [sentence_result]
        for sentence in sentences:
            if not isinstance(sentence, dict):
                continue
            text = sentence.get("text", "").strip()
            if len(text) < self.min_text_chars:
                continue
            if final_only and not RecognitionResult.is_sentence_end(sentence):
                continue
            if self.is_probable_tts_echo(text):
                self.get_logger().info(f"ASR ignored probable TTS echo: {text}")
                continue
            self.text_queue.put(text)


def main(args=None):
    rclpy.init(args=args)
    node = DashScopeAsrBridgeNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
