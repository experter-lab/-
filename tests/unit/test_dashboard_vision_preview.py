import re

try:
    from medicine_web_dashboard.dashboard_assets import INDEX_HTML
except ImportError:
    from dashboard_assets import INDEX_HTML


def _inline_script():
    match = re.search(r"<script>([\s\S]*?)</script>", INDEX_HTML)
    assert match, "dashboard inline script not found"
    return match.group(1)


def test_camera_preview_stream_is_lazy_loaded():
    script = _inline_script()

    assert "reconnectCameraPreview();" not in script
    assert "function syncCameraPreview()" in script
    assert "function startCameraPreview()" in script
    assert "function stopCameraPreview()" in script
    assert "document.addEventListener('visibilitychange', syncCameraPreview);" in script


def test_camera_preview_starts_only_on_vision_tab():
    script = _inline_script()

    assert 'data-tab="batch"' in INDEX_HTML
    assert 'class="tab-button active" type="button" data-tab="batch"' in INDEX_HTML
    assert 'data-tab="vision"' in INDEX_HTML
    assert 'document.querySelector(\'[data-page="vision"].active\')' in script
    assert "cameraPreview.src =" in script
    assert "cameraPreview.removeAttribute('src');" in script


def test_scan_confirmation_requires_fresh_scan_payload():
    script = _inline_script()

    assert "const SCAN_MAX_AGE_SEC = 8;" in script
    assert "function getScanAgeSec()" in script
    assert "currentScannedKey({ requireFresh: true })" in script
    assert "{ requireScan: true }" in script
    assert "当前扫码结果已超过" in script
