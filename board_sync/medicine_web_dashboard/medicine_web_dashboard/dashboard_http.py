import json
from http.server import BaseHTTPRequestHandler
import mimetypes
import urllib.error
import urllib.request
from urllib.parse import parse_qs, unquote, urlparse

try:
    from .dashboard_assets import INDEX_HTML
except ImportError:
    from dashboard_assets import INDEX_HTML

try:
    from .dashboard_navigation import NAVIGATION_HTML
except ImportError:
    from dashboard_navigation import NAVIGATION_HTML


def create_dashboard_handler(dashboard):
    class DashboardRequestHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format_text, *args):
            status = int(args[1]) if len(args) > 1 and str(args[1]).isdigit() else 0
            if status >= 400:
                dashboard.get_logger().warn(format_text % args)

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/":
                self.write_html(INDEX_HTML)
                return
            if path == "/navigation":
                self.write_html(NAVIGATION_HTML)
                return
            if path == "/api/health":
                self.write_json({"ok": True})
                return
            if path == "/api/health_check":
                try:
                    self.write_json(dashboard.get_health_check())
                except Exception as exc:
                    try:
                        dashboard.get_logger().error(f"health_check failed: {exc}")
                    except Exception:
                        pass
                    self.write_json(
                        {
                            "ok": False,
                            "status": "bad",
                            "updated_at": 0,
                            "summary": {"bad": 1, "warn": 0, "ok": 0},
                            "checks": {
                                "health_check": {
                                    "label": "系统自检接口",
                                    "status": "bad",
                                    "ok": False,
                                    "message": f"自检生成失败：{exc}",
                                    "details": {},
                                    "actions": [
                                        {"label": "刷新自检", "action": "refresh_health"}
                                    ],
                                }
                            },
                            "actions": [
                                {"label": "刷新自检", "action": "refresh_health"}
                            ],
                            "events": [],
                        },
                        status=503,
                    )
                return
            if path == "/api/navigation/maps":
                self.write_json(dashboard.get_navigation_maps())
                return
            if path == "/api/navigation/map":
                query = parse_qs(urlparse(self.path).query)
                name = query.get("name", [""])[0]
                self.write_json(dashboard.get_navigation_map(name))
                return
            if path == "/api/navigation/status":
                self.write_json(dashboard.get_navigation_status())
                return
            if path == "/api/navigation/snapshot":
                query = parse_qs(urlparse(self.path).query)
                name = query.get("map", [""])[0]
                self.write_json(dashboard.get_navigation_snapshot(name))
                return
            if path.startswith("/navigation/maps/"):
                file_name = unquote(path.removeprefix("/navigation/maps/"))
                self.write_file(dashboard.get_navigation_map_file(file_name))
                return
            if path == "/api/stations":
                self.write_json({"stations": dashboard.stations})
                return
            if path == "/api/patient_orders":
                self.write_json(dashboard.get_patient_orders())
                return
            if path == "/api/delivery_batch":
                self.write_json(dashboard.get_delivery_batch())
                return
            if path == "/api/delivery_batch/pending":
                self.write_json(dashboard.get_pending_delivery_batch())
                return
            if path == "/api/delivery_batch/report.json":
                self.write_json(dashboard.build_delivery_batch_report())
                return
            if path == "/api/delivery_batch/report.csv":
                self.write_text(
                    dashboard.build_delivery_batch_report_csv(),
                    content_type="text/csv; charset=utf-8",
                    filename="delivery_batch_report.csv",
                )
                return
            if path == "/api/delivery_batch/safety_self_test/latest":
                self.write_json(dashboard.get_delivery_safety_self_test_result())
                return
            if path == "/api/delivery_batch/safety_gate":
                self.write_json(dashboard.get_delivery_batch_safety_gate())
                return
            if path == "/api/state":
                self.write_json(dashboard.get_state())
                return
            if path == "/api/system_load":
                self.write_json(dashboard.get_system_load())
                return
            if path == "/api/drug_info":
                self.write_json(dashboard.get_drug_info())
                return
            if path == "/api/vision/stream.mjpg":
                self.proxy_camera_preview("http://127.0.0.1:8090/stream.mjpg")
                return
            if path == "/api/vision/snapshot.jpg":
                self.proxy_camera_preview("http://127.0.0.1:8090/snapshot.jpg")
                return
            if path == "/api/vision/webrtc/status":
                self.write_json(dashboard.get_vision_webrtc_status())
                return
            if path == "/api/chassis_status":
                self.write_json(dashboard.get_chassis_status())
                return
            if path == "/api/patient_messages":
                self.write_json(
                    {"messages": dashboard.get_patient_messages()}
                )
                return
            if path == "/api/patient_status_overrides":
                # 闭环 B: 返回所有床位的 confirm/reject 状态 + reason
                # 让医护端配送批次 tab 给每张床位卡片打 "已取药" / "病人反馈" 贴纸
                overrides = getattr(dashboard, "patient_status_overrides", {}) or {}
                self.write_json({"overrides": overrides})
                return
            self.write_json({"message": "Not found"}, status=404)

        def do_POST(self):
            path = urlparse(self.path).path
            if not self.is_write_request_allowed():
                self.write_json({"message": "Write API request not authorized"}, status=403)
                return
            try:
                payload = self.read_json_body()
            except ValueError as exc:
                self.write_json({"message": str(exc)}, status=400)
                return
            if path == "/api/tasks":
                self.write_json(dashboard.create_task(payload))
                return
            if path == "/api/voice/announce":
                response = dashboard.announce_voice_text(payload)
                self.write_json(response, status=200 if response.get("ok") else 400)
                return
            if path == "/api/voice/listen":
                response = dashboard.start_voice_listen(payload)
                self.write_json(response, status=200 if response.get("ok") else 400)
                return
            if path == "/api/chassis/emergency_stop":
                response = dashboard.set_chassis_emergency_stop(payload)
                self.write_json(response, status=200 if response.get("ok") else 400)
                return
            if path == "/api/vision/qr":
                response = dashboard.set_vision_qr(payload)
                self.write_json(response, status=200 if response.get("ok") else 400)
                return
            if path == "/api/vision/ocr":
                response = dashboard.trigger_vision_ocr(payload)
                self.write_json(response, status=200 if response.get("ok") else 400)
                return
            if path == "/api/vision/webrtc/offer":
                try:
                    response = dashboard.create_vision_webrtc_answer(payload)
                    self.write_json(response)
                except Exception as exc:
                    self.write_json({"ok": False, "message": str(exc)}, status=503)
                return
            if path == "/api/delivery_batch/reset":
                response = dashboard.reset_delivery_batch()
                dashboard.persist_current_delivery_batch()
                self.write_json(response)
                return
            if path == "/api/delivery_batch/import":
                response = dashboard.import_delivery_batch(payload)
                self.write_json(response, status=200 if response.get("ok") else 400)
                return
            if path == "/api/external/delivery_batch":
                response = dashboard.receive_external_delivery_batch(payload)
                self.write_json(response, status=200 if response.get("ok") else 400)
                return
            if path == "/api/delivery_batch/adopt_pending":
                response = dashboard.adopt_pending_delivery_batch(payload)
                if response.get("ok"):
                    dashboard.persist_current_delivery_batch()
                self.write_json(response, status=200 if response.get("ok") else 400)
                return
            if path == "/api/delivery_batch/discard_pending":
                response = dashboard.discard_pending_delivery_batch()
                self.write_json(response, status=200 if response.get("ok") else 400)
                return
            if path == "/api/delivery_batch/apply_import":
                response = dashboard.apply_imported_delivery_batch(payload)
                if response.get("ok"):
                    dashboard.persist_current_delivery_batch()
                self.write_json(response, status=200 if response.get("ok") else 400)
                return
            if path == "/api/delivery_batch/update_patient":
                response = dashboard.update_delivery_batch_patient_info(payload)
                if response.get("ok"):
                    dashboard.persist_current_delivery_batch()
                self.write_json(response, status=200 if response.get("ok") else 400)
                return
            if path == "/api/delivery_batch/update_medication":
                response = dashboard.update_delivery_batch_medication_info(payload)
                if response.get("ok"):
                    dashboard.persist_current_delivery_batch()
                self.write_json(response, status=200 if response.get("ok") else 400)
                return
            if path == "/api/delivery_batch/scan_preview":
                response = dashboard.preview_delivery_batch_scan(payload)
                self.write_json(response)
                return
            if path == "/api/delivery_batch/safety_self_test":
                response = dashboard.run_delivery_batch_safety_self_test()
                self.write_json(response, status=200 if response.get("ok") else 400)
                return
            if path == "/api/delivery_batch/load_scan":
                response = dashboard.scan_load_delivery_batch(payload)
                dashboard.persist_current_delivery_batch()
                self.write_json(response)
                return
            if path == "/api/delivery_batch/dispense_scan":
                response = dashboard.scan_dispense_delivery_batch(payload)
                dashboard.persist_current_delivery_batch()
                self.write_json(response)
                return
            if path == "/api/delivery_batch/exception":
                response = dashboard.mark_delivery_batch_exception(payload)
                dashboard.persist_current_delivery_batch()
                self.write_json(response)
                return
            if path == "/api/delivery_batch/demo_review":
                response = dashboard.create_medication_review_demo_scenario(payload)
                dashboard.persist_current_delivery_batch()
                self.write_json(response, status=200 if response.get("ok") else 400)
                return
            if path == "/api/delivery_batch/demo_review_reset":
                response = dashboard.reset_medication_review_demo_scenario(payload)
                dashboard.persist_current_delivery_batch()
                self.write_json(response, status=200 if response.get("ok") else 400)
                return
            if path == "/api/delivery_batch/resolve_review":
                response = dashboard.resolve_patient_medication_review(payload)
                dashboard.persist_current_delivery_batch()
                self.write_json(response, status=200 if response.get("ok") else 400)
                return
            if path == "/api/delivery_batch/advance":
                response = dashboard.advance_delivery_batch()
                dashboard.persist_current_delivery_batch()
                self.write_json(response)
                return
            if path == "/api/verify_task":
                self.write_json(dashboard.verify_delivery_task(payload))
                return
            if path == "/api/cancel":
                self.write_json(dashboard.cancel_task(payload))
                return
            if path == "/api/patient_messages/reply":
                bed = str(payload.get("bed") or "").strip()
                content = str(payload.get("content") or "").strip()
                delivery_id = str(payload.get("delivery_id") or "").strip()
                nurse_name = str(payload.get("nurse_name") or "").strip()
                if not bed or not content:
                    self.write_json(
                        {"message": "缺少 bed 或 content"}, status=400
                    )
                    return
                msg = dashboard.append_nurse_reply(
                    bed=bed,
                    content=content,
                    delivery_id=delivery_id,
                    nurse_name=nurse_name,
                )
                if msg is None:
                    self.write_json({"message": "回复失败"}, status=500)
                    return
                self.write_json({"ok": True, "message": msg})
                return
            if path == "/api/patient_messages/read":
                ok = dashboard.mark_message_read_by_nurse(
                    str(payload.get("id") or "")
                )
                self.write_json({"ok": ok})
                return
            if path == "/api/patient_messages/read_all":
                bed = str(payload.get("bed") or "").strip()
                nurse_name = str(payload.get("nurse_name") or "web_operator").strip() or "web_operator"
                result = dashboard.mark_all_messages_read_by_nurse(bed=bed, nurse_name=nurse_name)
                response = {"ok": True, "read": result}
                if getattr(dashboard, "delivery_batch", None) is not None:
                    response["batch"] = dashboard.get_delivery_batch()
                self.write_json(response)
                return
            if path == "/api/patient_status_overrides/clear":
                bed = str(payload.get("bed") or "").strip()
                cleared = dashboard.clear_status_override(bed=bed)
                self.write_json({"ok": True, "cleared": cleared})
                return
            self.write_json({"message": "Not found"}, status=404)

        def read_json_body(self):
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length <= 0:
                return {}
            if length > dashboard.max_request_body_bytes:
                raise ValueError(
                    f"request body too large: {length} > {dashboard.max_request_body_bytes}"
                )
            raw = self.rfile.read(length).decode("utf-8")
            try:
                return json.loads(raw or "{}")
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON body: {exc.msg}") from exc

        def is_write_request_allowed(self):
            if self.headers.get("X-Requested-With", "") != "medicine-dashboard":
                return False
            if not dashboard.api_write_token:
                return True
            token = self.headers.get("X-API-Token", "")
            return token == dashboard.api_write_token

        def write_html(self, html):
            data = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.close_connection = True
            self.end_headers()
            self.wfile.write(data)
            self.wfile.flush()

        def write_json(self, payload, status=200):
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.close_connection = True
            self.end_headers()
            self.wfile.write(data)
            self.wfile.flush()

        def write_text(
            self,
            text,
            status=200,
            content_type="text/plain; charset=utf-8",
            filename="",
        ):
            data = text.encode("utf-8-sig")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.close_connection = True
            if filename:
                self.send_header(
                    "Content-Disposition", f'attachment; filename="{filename}"'
                )
            self.end_headers()
            self.wfile.write(data)
            self.wfile.flush()

        def write_file(self, file_path):
            data = file_path.read_bytes()
            content_type = (
                mimetypes.guess_type(str(file_path))[0]
                or "application/octet-stream"
            )
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "public, max-age=30")
            self.send_header("Connection", "close")
            self.close_connection = True
            self.end_headers()
            self.wfile.write(data)
            self.wfile.flush()

        def proxy_camera_preview(self, source_url):
            request = urllib.request.Request(
                source_url,
                headers={"User-Agent": "medicine-dashboard"},
            )
            try:
                upstream = urllib.request.urlopen(request, timeout=5)
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                self.write_json(
                    {"message": f"camera preview unavailable: {exc}"},
                    status=503,
                )
                return

            try:
                content_type = upstream.headers.get(
                    "Content-Type", "application/octet-stream"
                )
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Pragma", "no-cache")
                self.send_header("Connection", "close")
                self.close_connection = True
                self.end_headers()
                while True:
                    chunk = upstream.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, TimeoutError, OSError):
                pass
            finally:
                upstream.close()

    return DashboardRequestHandler
