import hashlib
import ctypes
import json
import os
import queue
import re
import shutil
import subprocess
import tempfile
import threading
import time
import termios
import wave

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import String


CI1302_PROTOCOLS = {
    "欢迎语": "AA550100FB",
    "欢迎使用小幻": "AA550100FB",
    "休息语": "AA550200FB",
    "我去休息啦": "AA550200FB",
    "小幻小幻": "AA550300FB",
    "我在": "AA550300FB",
    "增大音量": "AA550400FB",
    "减小音量": "AA550500FB",
    "最大音量": "AA550600FB",
    "中等音量": "AA550700FB",
    "最小音量": "AA550800FB",
    "开启播报": "AA550900FB",
    "开播报": "AA550900FB",
    "关闭播报": "AA550A00FB",
    "关播报": "AA550A00FB",
    "前进": "AA550001FB",
    "正在前进": "AA550001FB",
    "后退": "AA550002FB",
    "正在后退": "AA550002FB",
    "左转": "AA550003FB",
    "正在左转": "AA550003FB",
    "右转": "AA550004FB",
    "正在右转": "AA550004FB",
    "停止": "AA550009FB",
    "停下": "AA550009FB",
    "收到": "AA550009FB",
    "立正": "AA55000AFB",
    "趴下": "AA55000BFB",
    "坐下": "AA55000CFB",
    "加速": "AA55000DFB",
    "减速": "AA55000EFB",
    "叫一声": "AA550011FB",
    "开灯": "AA550012FB",
    "灯已开": "AA550012FB",
    "关灯": "AA550013FB",
    "灯已关": "AA550013FB",
    "打开门": "AA550014FB",
    "门已开": "AA550014FB",
    "关闭门": "AA550015FB",
    "门已关": "AA550015FB",
    "打开水泵": "AA550016FB",
    "关闭水泵": "AA550017FB",
    "你好": "AA55001AFB",
    "介绍自己": "AA55001BFB",
    "露一手": "AA55001CFB",
    "走两步": "AA55001DFB",
    "摇头": "AA55001EFB",
    "战斗模式": "AA550021FB",
    "蹲下来": "AA550022FB",
    "开风扇": "AA550024FB",
    "关风扇": "AA550025FB",
    "亮红灯": "AA550027FB",
    "亮绿灯": "AA550028FB",
    "亮蓝灯": "AA550029FB",
    "跳舞": "AA55006CFB",
}


class VoiceConsoleNode(Node):
    def __init__(self):
        super().__init__("medicine_voice_console")
        self.declare_parameter("voice_topic", "/medicine/voice_text")
        self.declare_parameter("tts_state_topic", "/medicine/tts_state")
        self.declare_parameter("prefix", "[语音播报]")
        self.declare_parameter("enable_tts", True)
        self.declare_parameter("tts_backend", "auto")
        self.declare_parameter("tts_rate", 0)
        self.declare_parameter("tts_volume", 100)
        self.declare_parameter("deduplicate_window_sec", 1.0)
        self.declare_parameter("queue_size", 20)
        self.declare_parameter("pico_language", "zh-CN")
        self.declare_parameter("espeak_voice", "zh")
        self.declare_parameter("aplay_device", "")
        self.declare_parameter("pulse_sink", "")
        self.declare_parameter("ci1302_serial_port", "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0")
        self.declare_parameter("ci1302_baudrate", 460800)
        self.declare_parameter("ci1302_open_delay_sec", 3.0)
        self.declare_parameter("ci1302_default_frame", "")
        self.declare_parameter("iflytek_msc_lib_path", "/mnt/sdcard/iflytek_tts_sdk/tts_make_ros2/libs/arm64/libmsc.so")
        self.declare_parameter("iflytek_tts_sdk_dir", "/mnt/sdcard/iflytek_tts_df41b4a2")
        self.declare_parameter("iflytek_appid", "df41b4a2")
        self.declare_parameter("iflytek_voice_name", "xiaoyan")
        self.declare_parameter("iflytek_sample_rate", 16000)
        self.declare_parameter("iflytek_speed", 50)
        self.declare_parameter("iflytek_volume", 70)
        self.declare_parameter("iflytek_pitch", 50)
        self.declare_parameter("iflytek_rdn", 2)

        self.voice_topic = self.get_parameter("voice_topic").value
        self.tts_state_topic = self.get_parameter("tts_state_topic").value
        self.prefix = self.get_parameter("prefix").value
        self.enable_tts = bool(self.get_parameter("enable_tts").value)
        self.tts_backend = str(self.get_parameter("tts_backend").value).strip().lower() or "auto"
        self.tts_rate = int(self.get_parameter("tts_rate").value)
        self.tts_volume = int(self.get_parameter("tts_volume").value)
        self.deduplicate_window_sec = float(self.get_parameter("deduplicate_window_sec").value)
        self.pico_language = str(self.get_parameter("pico_language").value)
        self.espeak_voice = str(self.get_parameter("espeak_voice").value)
        self.aplay_device = str(self.get_parameter("aplay_device").value).strip()
        self.pulse_sink = str(self.get_parameter("pulse_sink").value).strip()
        self.ci1302_serial_port = str(self.get_parameter("ci1302_serial_port").value).strip()
        self.ci1302_baudrate = int(self.get_parameter("ci1302_baudrate").value)
        self.ci1302_open_delay_sec = float(self.get_parameter("ci1302_open_delay_sec").value)
        self.ci1302_default_frame = str(self.get_parameter("ci1302_default_frame").value).strip()
        self.iflytek_msc_lib_path = str(self.get_parameter("iflytek_msc_lib_path").value).strip()
        self.iflytek_tts_sdk_dir = str(self.get_parameter("iflytek_tts_sdk_dir").value).strip()
        self.iflytek_appid = str(self.get_parameter("iflytek_appid").value).strip()
        self.iflytek_voice_name = str(self.get_parameter("iflytek_voice_name").value).strip() or "xiaoyan"
        self.iflytek_sample_rate = int(self.get_parameter("iflytek_sample_rate").value)
        self.iflytek_speed = int(self.get_parameter("iflytek_speed").value)
        self.iflytek_volume = int(self.get_parameter("iflytek_volume").value)
        self.iflytek_pitch = int(self.get_parameter("iflytek_pitch").value)
        self.iflytek_rdn = int(self.get_parameter("iflytek_rdn").value)
        self.ci1302_fd = None
        self.ci1302_ready = False

        max_queue = max(1, int(self.get_parameter("queue_size").value))
        self.messages = queue.Queue(maxsize=max_queue)
        self.last_key = ""
        self.last_time = 0.0
        self.running = True
        self.worker = threading.Thread(target=self.speech_worker, daemon=True)
        self.worker.start()

        if self.tts_backend == "ci1302_serial":
            self.open_ci1302_serial()

        self.tts_state_pub = self.create_publisher(String, self.tts_state_topic, 10)
        self.create_subscription(String, self.voice_topic, self.on_voice_text, 10)
        self.get_logger().info(
            f"Voice node started. topic={self.voice_topic}, tts={self.enable_tts}, backend={self.tts_backend}"
        )

    def chinese_number_for_tts(self, value, liang_for_two=False):
        try:
            n = int(value)
        except Exception:
            return str(value)
        if liang_for_two and n == 2:
            return "两"
        digits = "零一二三四五六七八九"
        if n < 0:
            return "负" + self.chinese_number_for_tts(-n, liang_for_two=liang_for_two)
        if n < 10:
            return digits[n]
        if n < 20:
            return "十" + (digits[n % 10] if n % 10 else "")
        if n < 100:
            return digits[n // 10] + "十" + (digits[n % 10] if n % 10 else "")
        if n < 1000:
            h, r = divmod(n, 100)
            if r == 0:
                return digits[h] + "百"
            if r < 10:
                return digits[h] + "百零" + digits[r]
            return digits[h] + "百" + self.chinese_number_for_tts(r, liang_for_two=liang_for_two)
        # Larger identifiers are often codes; read digit by digit to avoid odd TTS output.
        return " ".join(digits[int(ch)] if ch.isdigit() else ch for ch in str(n))

    def normalize_medical_tts_reading(self, text):
        text = str(text or "")

        def repl_decimal(match):
            left = self.chinese_number_for_tts(match.group(1))
            right = " ".join(self.chinese_number_for_tts(ch) for ch in match.group(2))
            return f"{left}点{right}"

        def repl_num_unit(match):
            raw_num = match.group(1)
            unit = match.group(2).lower()
            if "." in raw_num:
                num = re.sub(r"(\d+)\.(\d+)", repl_decimal, raw_num)
            else:
                num = self.chinese_number_for_tts(raw_num)
            unit_map = {
                "mg": "毫克",
                "g": "克",
                "ml": "毫升",
                "l": "升",
                "ug": "微克",
                "μg": "微克",
                "mcg": "微克",
                "iu": "国际单位",
                "mmhg": "毫米汞柱",
                "mmol/l": "毫摩尔每升",
            }
            return f"{num}{unit_map.get(unit, unit)}"

        # Units must run before generic number handling.
        text = re.sub(r"(?<![A-Za-z0-9])(\d+(?:\.\d+)?)\s*(mmol/l|mmHg|mcg|μg|ug|mg|ml|IU|iu|g|L|l)(?![A-Za-z])", repl_num_unit, text, flags=re.IGNORECASE)

        # Common medicine counts and frequencies.
        text = re.sub(r"(\d+)\s*片", lambda m: f"{self.chinese_number_for_tts(m.group(1))}片", text)
        text = re.sub(r"(\d+)\s*粒", lambda m: f"{self.chinese_number_for_tts(m.group(1))}粒", text)
        text = re.sub(r"(\d+)\s*袋", lambda m: f"{self.chinese_number_for_tts(m.group(1))}袋", text)
        text = re.sub(r"(\d+)\s*盒", lambda m: f"{self.chinese_number_for_tts(m.group(1))}盒", text)
        text = re.sub(r"(\d+)\s*次", lambda m: f"{self.chinese_number_for_tts(m.group(1), liang_for_two=True)}次", text)
        text = re.sub(r"每日\s*(\d+)", lambda m: f"每日{self.chinese_number_for_tts(m.group(1), liang_for_two=True)}", text)
        text = re.sub(r"每天\s*(\d+)", lambda m: f"每天{self.chinese_number_for_tts(m.group(1), liang_for_two=True)}", text)
        text = re.sub(r"一天\s*(\d+)", lambda m: f"一天{self.chinese_number_for_tts(m.group(1), liang_for_two=True)}", text)

        # Remaining small standalone numbers are usually quantities in spoken medical instructions.
        text = re.sub(r"(?<![A-Za-z0-9])([1-9]\d?)(?![A-Za-z0-9])", lambda m: self.chinese_number_for_tts(m.group(1)), text)
        return text

    def sanitize_tts_text(self, text):
        text = str(text or "").strip()
        text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
        text = re.sub(r"`([^`]*)`", r"\1", text)
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"__([^_]+)__", r"\1", text)
        text = re.sub(r"[*_#>`~]+", " ", text)
        text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", text)
        text = text.replace("\u2014\u2014", "\uff0c").replace("\u2013", "\uff0c").replace("--", "\uff0c")
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        text = self.normalize_medical_tts_reading(text)
        text = re.sub(r"(?<=[每一日天])\s+(?=[一二两三四五六七八九十百])", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def on_voice_text(self, msg):
        text = self.sanitize_tts_text(msg.data)
        if not text:
            return
        now = time.monotonic()
        key = hashlib.sha1(text.encode("utf-8")).hexdigest()
        if key == self.last_key and now - self.last_time < self.deduplicate_window_sec:
            return
        self.last_key = key
        self.last_time = now
        self.get_logger().info(f"{self.prefix} {text}")
        if not self.enable_tts:
            return
        try:
            self.messages.put_nowait(text)
        except queue.Full:
            try:
                self.messages.get_nowait()
            except queue.Empty:
                pass
            self.messages.put_nowait(text)
            self.get_logger().warn("Voice queue was full; dropped the oldest pending message")

    def speech_worker(self):
        while self.running:
            try:
                text = self.messages.get(timeout=0.2)
            except queue.Empty:
                continue
            ok = False
            self.publish_tts_state("start", text=text)
            try:
                ok = self.speak(text)
                if not ok:
                    self.get_logger().warn("No usable TTS backend found; voice text was printed only")
            except Exception as exc:
                self.get_logger().warn(f"TTS playback failed: {exc}")
            finally:
                self.publish_tts_state("end", text=text, ok=ok)
                self.messages.task_done()

    def publish_tts_state(self, state, text="", ok=None):
        try:
            payload = {
                "state": str(state),
                "text": str(text or ""),
                "stamp": time.time(),
            }
            if ok is not None:
                payload["ok"] = bool(ok)
            msg = String()
            msg.data = json.dumps(payload, ensure_ascii=False)
            self.tts_state_pub.publish(msg)
        except Exception as exc:
            self.get_logger().warn(f"Failed to publish TTS state: {exc}")

    def speak(self, text):
        backends = [self.tts_backend]
        if self.tts_backend == "auto":
            backends = ["iflytek_msc", "espeak_wav", "pico", "espeak", "spd-say"]
        for backend in backends:
            if backend == "iflytek_msc" and self.speak_with_iflytek_msc(text):
                return True
            if backend == "ci1302_serial" and self.speak_with_ci1302_serial(text):
                return True
            if backend == "espeak_wav" and self.speak_with_espeak_wav(text):
                return True
            if backend == "pico" and self.speak_with_pico(text):
                return True
            if backend == "espeak" and self.speak_with_espeak(text):
                return True
            if backend == "spd-say" and self.speak_with_spd_say(text):
                return True
            if backend == "none":
                return True
        return False

    def speak_with_ci1302_serial(self, text):
        frame = self.resolve_ci1302_frame(text)
        if not frame:
            self.get_logger().warn(
                f"No CI1302 protocol mapping for '{text}'. Send a known phrase or a hex frame like AA55001AFB."
            )
            return True
        try:
            if not self.ci1302_ready:
                self.open_ci1302_serial()
            if self.ci1302_fd is None:
                return False
            os.write(self.ci1302_fd, frame)
            termios.tcdrain(self.ci1302_fd)
            self.get_logger().info(f"CI1302 frame sent: {frame.hex(' ').upper()} via {self.ci1302_serial_port}")
            return True
        except OSError as exc:
            self.get_logger().warn(f"CI1302 serial write failed: {exc}")
            return False

    def resolve_ci1302_frame(self, text):
        normalized = "".join(ch for ch in text.strip() if not ch.isspace())
        candidate = normalized.upper().replace("0X", "").replace(",", "").replace(":", "").replace("-", "")
        if len(candidate) >= 10 and len(candidate) % 2 == 0:
            try:
                data = bytes.fromhex(candidate)
                if data.startswith(b"\xAA\x55") and data.endswith(b"\xFB"):
                    return data
            except ValueError:
                pass
        hex_frame = CI1302_PROTOCOLS.get(text.strip()) or CI1302_PROTOCOLS.get(normalized)
        if not hex_frame and self.ci1302_default_frame:
            hex_frame = self.ci1302_default_frame
        if not hex_frame:
            return None
        return bytes.fromhex(hex_frame)

    def open_ci1302_serial(self):
        if self.ci1302_fd is not None:
            return
        baud_map = {
            9600: termios.B9600,
            19200: termios.B19200,
            38400: termios.B38400,
            57600: termios.B57600,
            115200: termios.B115200,
            230400: termios.B230400,
            460800: termios.B460800,
            921600: termios.B921600,
        }
        baud = baud_map.get(int(self.ci1302_baudrate))
        if baud is None:
            raise OSError(f"Unsupported CI1302 baudrate: {self.ci1302_baudrate}")
        fd = os.open(self.ci1302_serial_port, os.O_RDWR | os.O_NOCTTY)
        attrs = termios.tcgetattr(fd)
        attrs[0] = 0
        attrs[1] = 0
        attrs[2] = baud | termios.CS8 | termios.CLOCAL | termios.CREAD
        attrs[3] = 0
        attrs[4] = baud
        attrs[5] = baud
        attrs[6][termios.VMIN] = 0
        attrs[6][termios.VTIME] = 0
        termios.tcsetattr(fd, termios.TCSANOW, attrs)
        termios.tcflush(fd, termios.TCIOFLUSH)
        self.ci1302_fd = fd
        self.ci1302_ready = False
        self.get_logger().info(
            f"CI1302 serial opened: port={self.ci1302_serial_port}, baud={self.ci1302_baudrate}; waiting {self.ci1302_open_delay_sec}s"
        )
        time.sleep(max(0.0, self.ci1302_open_delay_sec))
        self.ci1302_ready = True

    def write_serial_frame(self, port, baudrate, frame):
        baud_map = {
            9600: termios.B9600,
            19200: termios.B19200,
            38400: termios.B38400,
            57600: termios.B57600,
            115200: termios.B115200,
            230400: termios.B230400,
            460800: termios.B460800,
            921600: termios.B921600,
        }
        baud = baud_map.get(int(baudrate))
        if baud is None:
            raise OSError(f"Unsupported CI1302 baudrate: {baudrate}")
        fd = os.open(port, os.O_RDWR | os.O_NOCTTY)
        try:
            attrs = termios.tcgetattr(fd)
            attrs[0] = 0
            attrs[1] = 0
            attrs[2] = baud | termios.CS8 | termios.CLOCAL | termios.CREAD
            attrs[3] = 0
            attrs[4] = baud
            attrs[5] = baud
            attrs[6][termios.VMIN] = 0
            attrs[6][termios.VTIME] = 0
            termios.tcsetattr(fd, termios.TCSANOW, attrs)
            termios.tcflush(fd, termios.TCIOFLUSH)
            os.write(fd, frame)
            termios.tcdrain(fd)
        finally:
            os.close(fd)

    def speak_with_iflytek_msc(self, text):
        lib_path = self.iflytek_msc_lib_path
        sdk_dir = self.iflytek_tts_sdk_dir
        voice = self.iflytek_voice_name
        voice_res = os.path.join(sdk_dir, "bin", "msc", "res", "tts", f"{voice}.jet")
        common_res = os.path.join(sdk_dir, "bin", "msc", "res", "tts", "common.jet")
        work_dir = os.path.join(sdk_dir, "bin")
        if not (os.path.exists(lib_path) and os.path.exists(voice_res) and os.path.exists(common_res)):
            self.get_logger().warn(
                f"iflytek_msc backend resources missing: lib={lib_path}, voice={voice_res}, common={common_res}"
            )
            return False

        fd, wav_path = tempfile.mkstemp(prefix="medicine_iflytek_", suffix=".wav")
        os.close(fd)
        try:
            pcm = self.synthesize_iflytek_msc(text, lib_path, work_dir, voice_res, common_res)
            if not pcm:
                return False
            with wave.open(wav_path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.iflytek_sample_rate)
                wav_file.writeframes(pcm)
            return self.play_wav(wav_path)
        except Exception as exc:
            self.get_logger().warn(f"iflytek_msc backend failed: {exc}")
            return False
        finally:
            try:
                os.remove(wav_path)
            except OSError:
                pass

    def synthesize_iflytek_msc(self, text, lib_path, work_dir, voice_res, common_res):
        lib = ctypes.CDLL(lib_path)
        c_char_p = ctypes.c_char_p
        c_int = ctypes.c_int
        c_uint = ctypes.c_uint
        c_void_p = ctypes.c_void_p
        lib.MSPLogin.argtypes = [c_char_p, c_char_p, c_char_p]
        lib.MSPLogin.restype = c_int
        lib.MSPLogout.argtypes = []
        lib.MSPLogout.restype = c_int
        lib.QTTSSessionBegin.argtypes = [c_char_p, ctypes.POINTER(c_int)]
        lib.QTTSSessionBegin.restype = c_char_p
        lib.QTTSTextPut.argtypes = [c_char_p, c_char_p, c_uint, c_char_p]
        lib.QTTSTextPut.restype = c_int
        lib.QTTSAudioGet.argtypes = [c_char_p, ctypes.POINTER(c_uint), ctypes.POINTER(c_int), ctypes.POINTER(c_int)]
        lib.QTTSAudioGet.restype = c_void_p
        lib.QTTSSessionEnd.argtypes = [c_char_p, c_char_p]
        lib.QTTSSessionEnd.restype = c_int

        login_params = f"appid = {self.iflytek_appid}, work_dir = {work_dir}".encode("utf-8")
        ret = lib.MSPLogin(None, None, login_params)
        if ret != 0:
            raise RuntimeError(f"MSPLogin failed: {ret}")

        session_id = None
        try:
            params = (
                f"engine_type = local,voice_name={self.iflytek_voice_name}, text_encoding = UTF8, "
                f"tts_res_path = fo|{voice_res};fo|{common_res}, "
                f"sample_rate = {self.iflytek_sample_rate}, "
                f"speed = {max(0, min(100, self.iflytek_speed))}, "
                f"volume = {max(0, min(100, self.iflytek_volume))}, "
                f"pitch = {max(0, min(100, self.iflytek_pitch))}, "
                f"rdn = {max(0, min(3, self.iflytek_rdn))}"
            ).encode("utf-8")
            err = c_int(0)
            session_id = lib.QTTSSessionBegin(params, ctypes.byref(err))
            if err.value != 0 or not session_id:
                raise RuntimeError(f"QTTSSessionBegin failed: {err.value}")

            text_bytes = text.encode("utf-8")
            ret = lib.QTTSTextPut(session_id, text_bytes, len(text_bytes), None)
            if ret != 0:
                raise RuntimeError(f"QTTSTextPut failed: {ret}")

            pcm = bytearray()
            status = c_int(1)
            while True:
                audio_len = c_uint(0)
                ret_audio = c_int(0)
                ptr = lib.QTTSAudioGet(
                    session_id,
                    ctypes.byref(audio_len),
                    ctypes.byref(status),
                    ctypes.byref(ret_audio),
                )
                if ret_audio.value != 0:
                    raise RuntimeError(f"QTTSAudioGet failed: {ret_audio.value}")
                if ptr and audio_len.value:
                    pcm.extend(ctypes.string_at(ptr, audio_len.value))
                if status.value == 2:
                    break
            return bytes(pcm)
        finally:
            if session_id:
                lib.QTTSSessionEnd(session_id, b"Normal")
            lib.MSPLogout()

    def speak_with_espeak_wav(self, text):
        exe = shutil.which("espeak-ng") or shutil.which("espeak")
        if not exe:
            return False
        fd, wav_path = tempfile.mkstemp(prefix="medicine_voice_", suffix=".wav")
        os.close(fd)
        try:
            synth_cmd = [exe, "-v", self.espeak_voice]
            if self.tts_rate > 0:
                synth_cmd.extend(["-s", str(self.tts_rate)])
            synth_cmd.extend(["-w", wav_path, text])
            subprocess.run(
                synth_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                timeout=20,
            )
            if self.play_wav(wav_path):
                return True
            return False
        except (subprocess.SubprocessError, OSError) as exc:
            self.get_logger().warn(f"espeak_wav backend failed: {exc}")
            return False
        finally:
            try:
                os.remove(wav_path)
            except OSError:
                pass

    def play_wav(self, wav_path):
        if self.aplay_device:
            # When a dedicated USB sound card is configured, do not fall back to
            # paplay/default aplay after a timeout. The first aplay may have
            # already played most/all of the WAV, and fallback would sound like
            # the robot repeated itself.
            return self.play_wav_with_aplay(wav_path)

        paplay = shutil.which("paplay")
        if paplay:
            sinks = [sink.strip() for sink in self.pulse_sink.split(",") if sink.strip()]
            if not sinks:
                sinks = [""]
            played = False
            for sink in sinks:
                cmd = [paplay]
                if sink:
                    cmd.extend(["--device", sink])
                cmd.append(wav_path)
                try:
                    subprocess.run(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True,
                        timeout=self.wav_play_timeout(wav_path),
                    )
                    played = True
                except (subprocess.SubprocessError, OSError) as exc:
                    target = sink or "default"
                    self.get_logger().warn(f"paplay failed on {target}: {exc}")
            if played:
                return True
        return self.play_wav_with_aplay(wav_path)

    def wav_play_timeout(self, wav_path):
        try:
            with wave.open(wav_path, "rb") as wav:
                frames = wav.getnframes()
                rate = wav.getframerate() or 16000
                duration = frames / float(rate)
            return max(20.0, min(120.0, duration + 12.0))
        except Exception:
            return 60.0

    def play_wav_with_aplay(self, wav_path):
        aplay = shutil.which("aplay")
        if not aplay:
            return False
        cmd = [aplay, "-q"]
        if self.aplay_device:
            cmd.extend(["-D", self.aplay_device])
        cmd.append(wav_path)
        try:
            subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                timeout=self.wav_play_timeout(wav_path),
            )
            return True
        except (subprocess.SubprocessError, OSError) as exc:
            self.get_logger().warn(f"aplay failed: {exc}")
            return False

    def speak_with_pico(self, text):
        pico = shutil.which("pico2wave")
        if not pico:
            return False
        fd, wav_path = tempfile.mkstemp(prefix="medicine_voice_", suffix=".wav")
        os.close(fd)
        try:
            subprocess.run(
                [pico, "-l", self.pico_language, "-w", wav_path, text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                timeout=20,
            )
            return self.play_wav(wav_path)
        except (subprocess.SubprocessError, OSError) as exc:
            self.get_logger().warn(f"pico/aplay backend failed: {exc}")
            return False
        finally:
            try:
                os.remove(wav_path)
            except OSError:
                pass

    def speak_with_espeak(self, text):
        exe = shutil.which("espeak-ng") or shutil.which("espeak")
        if not exe:
            return False
        cmd = [exe, "-v", self.espeak_voice, "-a", str(max(0, min(200, self.tts_volume)))]
        if self.tts_rate > 0:
            cmd.extend(["-s", str(self.tts_rate)])
        cmd.append(text)
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, check=True, timeout=30)
            return True
        except (subprocess.SubprocessError, OSError) as exc:
            self.get_logger().warn(f"espeak backend failed: {exc}")
            return False

    def speak_with_spd_say(self, text):
        exe = shutil.which("spd-say")
        if not exe:
            return False
        cmd = [exe]
        if self.tts_rate:
            cmd.extend(["-r", str(self.tts_rate)])
        cmd.append(text)
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, check=True, timeout=30)
            return True
        except (subprocess.SubprocessError, OSError) as exc:
            self.get_logger().warn(f"spd-say backend failed: {exc}")
            return False

    def destroy_node(self):
        self.running = False
        if self.worker.is_alive():
            self.worker.join(timeout=1.0)
        if self.ci1302_fd is not None:
            try:
                os.close(self.ci1302_fd)
            except OSError:
                pass
            self.ci1302_fd = None
        super().destroy_node()


def main():
    rclpy.init()
    node = VoiceConsoleNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        try:
            if rclpy.ok():
                rclpy.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    main()
