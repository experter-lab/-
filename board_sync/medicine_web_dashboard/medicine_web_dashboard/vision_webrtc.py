import asyncio
import fractions
import threading
import time
import urllib.request
from typing import Optional

try:
    import cv2
    import numpy as np
except Exception:  # pragma: no cover - optional runtime dependency
    cv2 = None
    np = None

try:
    from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
    from av import VideoFrame
except Exception:  # pragma: no cover - optional runtime dependency
    RTCPeerConnection = None
    RTCSessionDescription = None
    VideoStreamTrack = object
    VideoFrame = None


class MjpegLatestFrameSource:
    """Keep the latest frame from the local MJPEG preview server.

    The camera is already owned by medicine_vision_detector. This source reads the
    existing preview stream instead of opening /dev/video* again, so it avoids
    fighting with the vision node for the same hardware.
    """

    def __init__(self, stream_url="http://127.0.0.1:8090/stream.mjpg", snapshot_url="http://127.0.0.1:8090/snapshot.jpg"):
        self.stream_url = stream_url
        self.snapshot_url = snapshot_url
        self._lock = threading.Lock()
        self._latest_frame = None
        self._latest_ts = 0.0
        self._frame_count = 0
        self._fps_window = []
        self._actual_fps = 0.0
        self._running = False
        self._thread = None
        self._last_error = ""

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, name="vision-webrtc-frame-source", daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def get_frame(self):
        with self._lock:
            if self._latest_frame is None:
                return None
            return self._latest_frame.copy()

    def status(self):
        with self._lock:
            age = time.time() - self._latest_ts if self._latest_ts else None
            return {
                "ok": RTCPeerConnection is not None and cv2 is not None and np is not None,
                "running": self._running,
                "frame_count": self._frame_count,
                "source_fps": round(self._actual_fps, 1),
                "latest_frame_age_sec": round(age, 3) if age is not None else None,
                "last_error": self._last_error,
            }

    def _remember_frame(self, frame):
        now = time.time()
        with self._lock:
            self._latest_frame = frame
            self._latest_ts = now
            self._frame_count += 1
            self._fps_window.append(now)
            cutoff = now - 2.0
            self._fps_window = [item for item in self._fps_window if item >= cutoff]
            if len(self._fps_window) >= 2:
                elapsed = self._fps_window[-1] - self._fps_window[0]
                self._actual_fps = (len(self._fps_window) - 1) / elapsed if elapsed > 0 else 0.0
            self._last_error = ""

    def _run(self):
        if cv2 is None:
            self._last_error = "opencv-python is not available"
            return
        while self._running:
            try:
                self._read_stream_once()
            except Exception as exc:
                with self._lock:
                    self._last_error = str(exc)
                self._read_snapshot_fallback()
                time.sleep(0.2)

    def _read_stream_once(self):
        cap = cv2.VideoCapture(self.stream_url)
        if not cap.isOpened():
            raise RuntimeError(f"cannot open {self.stream_url}")
        try:
            while self._running:
                ok, frame = cap.read()
                if not ok or frame is None:
                    raise RuntimeError("MJPEG stream read failed")
                self._remember_frame(frame)
        finally:
            cap.release()

    def _read_snapshot_fallback(self):
        if cv2 is None or np is None:
            return
        try:
            with urllib.request.urlopen(self.snapshot_url, timeout=1.5) as response:
                raw = response.read()
            arr = np.frombuffer(raw, dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame is not None:
                self._remember_frame(frame)
        except Exception as exc:
            with self._lock:
                self._last_error = f"snapshot fallback failed: {exc}"


class LatestFrameVideoTrack(VideoStreamTrack):
    kind = "video"

    def __init__(self, frame_source: MjpegLatestFrameSource, width=1280, height=960, fps=30):
        super().__init__()
        self.frame_source = frame_source
        self.width = int(width)
        self.height = int(height)
        self.fps = max(1, min(int(fps), 30))
        self._pts = 0
        self._time_base = fractions.Fraction(1, 90000)
        self._last_emit = 0.0

    async def recv(self):
        # Limit browser preview to 30fps. Camera capture can remain 60fps for OCR.
        wait = max(0.0, (1.0 / self.fps) - (time.time() - self._last_emit))
        if wait:
            await asyncio.sleep(wait)
        self._last_emit = time.time()

        frame = self.frame_source.get_frame()
        if frame is None:
            frame = self._blank_frame()
        elif self.width > 0 and self.height > 0 and (frame.shape[1] != self.width or frame.shape[0] != self.height):
            frame = cv2.resize(frame, (self.width, self.height), interpolation=cv2.INTER_AREA)

        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        self._pts += int(90000 / self.fps)
        video_frame.pts = self._pts
        video_frame.time_base = self._time_base
        return video_frame

    def _blank_frame(self):
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        cv2.putText(frame, "Waiting for camera", (60, self.height // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (210, 220, 230), 2, cv2.LINE_AA)
        return frame


class VisionWebRTCService:
    def __init__(self, logger=None):
        self.logger = logger
        self.frame_source = MjpegLatestFrameSource()
        self.loop = None
        self.thread = None
        self._pcs = set()
        self._started = False
        self._lock = threading.Lock()

    @property
    def available(self):
        return RTCPeerConnection is not None and RTCSessionDescription is not None and VideoFrame is not None and cv2 is not None and np is not None

    def start(self):
        with self._lock:
            if self._started:
                return
            self._started = True
            self.loop = asyncio.new_event_loop()
            self.thread = threading.Thread(target=self._run_loop, name="vision-webrtc-loop", daemon=True)
            self.thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def stop(self):
        with self._lock:
            if not self._started:
                return
            self._started = False
        self.frame_source.stop()
        if self.loop is not None:
            future = asyncio.run_coroutine_threadsafe(self._close_all(), self.loop)
            try:
                future.result(timeout=3)
            except Exception:
                pass
            self.loop.call_soon_threadsafe(self.loop.stop)

    def status(self):
        source_status = self.frame_source.status()
        source_status.update({
            "available": self.available,
            "peer_count": len(self._pcs),
            "mode": "webrtc",
        })
        if not self.available:
            source_status["last_error"] = source_status.get("last_error") or "aiortc/av/cv2/numpy dependency missing"
        return source_status

    def create_answer(self, payload):
        if not self.available:
            raise RuntimeError("WebRTC dependency missing: install aiortc, av, opencv-python and numpy")
        if not self._started:
            self.start()
        if self.loop is None:
            raise RuntimeError("WebRTC loop not running")
        future = asyncio.run_coroutine_threadsafe(self._create_answer(payload), self.loop)
        return future.result(timeout=10)

    async def _create_answer(self, payload):
        offer_sdp = str(payload.get("sdp") or "")
        offer_type = str(payload.get("type") or "offer")
        if not offer_sdp:
            raise ValueError("missing WebRTC offer sdp")

        pc = RTCPeerConnection()
        self._pcs.add(pc)
        self.frame_source.start()

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            state = pc.connectionState
            if self.logger:
                try:
                    self.logger.info(f"Vision WebRTC connection state: {state}")
                except Exception:
                    pass
            if state in {"failed", "closed", "disconnected"}:
                await pc.close()
                self._pcs.discard(pc)
                if not self._pcs:
                    self.frame_source.stop()

        pc.addTrack(LatestFrameVideoTrack(self.frame_source, width=1280, height=960, fps=30))
        offer = RTCSessionDescription(sdp=offer_sdp, type=offer_type)
        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        response_sdp = self._add_video_bitrate_hint(pc.localDescription.sdp, bitrate_kbps=6000)
        return {"sdp": response_sdp, "type": pc.localDescription.type, "mode": "webrtc"}

    def _add_video_bitrate_hint(self, sdp, bitrate_kbps=6000):
        # Some aiortc versions on RK3588 do not expose RTCRtpSender parameters.
        # SDP bitrate hints are widely tolerated by browsers and help avoid
        # over-compressing the 1280x960 low-latency preview when bandwidth allows.
        try:
            lines = str(sdp or "").splitlines()
            out = []
            in_video = False
            video_hint_added = False
            for line in lines:
                if line.startswith("m="):
                    if in_video and not video_hint_added:
                        out.append(f"b=AS:{int(bitrate_kbps)}")
                        video_hint_added = True
                    in_video = line.startswith("m=video")
                    video_hint_added = False
                    out.append(line)
                    continue
                out.append(line)
                if in_video and line.startswith("c=") and not video_hint_added:
                    out.append(f"b=AS:{int(bitrate_kbps)}")
                    out.append(f"b=TIAS:{int(bitrate_kbps) * 1000}")
                    video_hint_added = True
            if in_video and not video_hint_added:
                out.append(f"b=AS:{int(bitrate_kbps)}")
            return "\r\n".join(out) + "\r\n"
        except Exception as exc:
            if self.logger:
                try:
                    self.logger.warn(f"Vision WebRTC SDP bitrate hint skipped: {exc}")
                except Exception:
                    pass
            return sdp

    async def _close_all(self):
        pcs = list(self._pcs)
        self._pcs.clear()
        for pc in pcs:
            try:
                await pc.close()
            except Exception:
                pass
