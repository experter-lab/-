from pathlib import Path


VISION_NODE = (
    Path(__file__).resolve().parents[1]
    / "board_sync"
    / "medicine_vision_detector"
    / "medicine_vision_detector"
    / "drug_info_detector_node.py"
)


def test_preview_encoding_is_gated_by_recent_client():
    source = VISION_NODE.read_text(encoding="utf-8")

    assert 'declare_parameter("preview_idle_timeout_sec", 1.0)' in source
    assert "def has_recent_preview_client(self):" in source
    assert "if not self.has_recent_preview_client():" in source
    assert "def mark_preview_client_active(self, count_request=False):" in source
    assert "preview_encoding_active" in source


def test_stream_refreshes_preview_activity_without_inflating_request_count():
    source = VISION_NODE.read_text(encoding="utf-8")

    assert "detector.mark_preview_client_active(count_request=True)" in source
    assert "detector.mark_preview_client_active()\n                    frame = detector.get_latest_frame_jpeg()" in source
    assert "preview_client_request_count += 1" in source
