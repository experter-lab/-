import copy
import json
import os
import re
import time

from medicine_interfaces.srv import CreateDeliveryTask

try:
    from .dashboard_assets import PATIENT_MEDICATION_ORDERS
except ImportError:
    from dashboard_assets import PATIENT_MEDICATION_ORDERS


OCR_AUTO_LOAD_SCORE_THRESHOLD = 0.50
OCR_AUTO_LOAD_SCORE_PERCENT = int(OCR_AUTO_LOAD_SCORE_THRESHOLD * 100)


class DeliveryBatchMixin:
    def create_demo_delivery_batch(self):
        route = ["ward_a", "ward_b", "ward_c"]
        station_names = {station["id"]: station["name"] for station in self.stations}
        stops = []
        for index, station_id in enumerate(route):
            patients = []
            for order in PATIENT_MEDICATION_ORDERS:
                if order.get("target_station") != station_id:
                    continue
                patient = copy.deepcopy(order)
                patient["patient_status"] = "WAITING_LOAD_CONFIRMATION"
                for medication in patient.get("medications", []):
                    medication["loaded"] = False
                    medication["loaded_at"] = ""
                    medication["dispensed"] = False
                    medication["dispensed_at"] = ""
                    medication["returned"] = False
                    medication["returned_at"] = ""
                    medication["return_reason"] = ""
                    medication["exception"] = ""
                    medication["exception_at"] = ""
                    medication["exception_reason"] = ""
                    medication["exception_resolved_at"] = ""
                    medication["exception_resolved_reason"] = ""
                    medication["exception_resolution_action"] = ""
                    medication["manual_reviewed"] = False
                    medication["manual_reviewed_at"] = ""
                    medication["manual_review_result"] = ""
                patients.append(patient)
            stops.append(
                {
                    "stop_id": f"stop_{station_id}",
                    "target_station": station_id,
                    "display_name": station_names.get(station_id, station_id),
                    "sequence_index": index + 1,
                    "stop_status": "WAITING_LOAD_CONFIRMATION",
                    "arrived_time": "",
                    "completed_time": "",
                    "patients": patients,
                }
            )
        now = self.now_text()
        batch = {
            "batch_id": f"BATCH-{time.strftime('%Y%m%d-%H%M%S', time.localtime())}",
            "source_station": "pharmacy",
            "route": ["pharmacy"] + route + ["pharmacy"],
            "route_status": "WAITING_LOAD_CONFIRMATION",
            "current_station": "pharmacy",
            "active_stop_index": -1,
            "active_stop_id": "",
            "created_time": now,
            "started_time": "",
            "finished_time": "",
            "operator_id": "pharmacist_001",
            "audit_records": [
                {
                    "time": now,
                    "event": "batch_created",
                    "message": "药师创建配送批次",
                    "result": "ok",
                }
            ],
            "stops": stops,
        }
        self.update_batch_summary(batch)
        return batch

    def reset_medication_runtime_fields(self, medication):
        medication["loaded"] = False
        medication["loaded_at"] = ""
        medication["dispensed"] = False
        medication["dispensed_at"] = ""
        medication["returned"] = False
        medication["returned_at"] = ""
        medication["return_reason"] = ""
        medication["exception"] = ""
        medication["exception_at"] = ""
        medication["exception_reason"] = ""
        medication["exception_resolved_at"] = ""
        medication["exception_resolved_reason"] = ""
        medication["exception_resolution_action"] = ""
        medication["manual_reviewed"] = False
        medication["manual_reviewed_at"] = ""
        medication["manual_review_result"] = ""
        medication["task_manager_task_id"] = ""

    def delivery_batch_has_progress(self, batch):
        if not isinstance(batch, dict):
            return False
        summary = batch.get("summary") if isinstance(batch.get("summary"), dict) else {}
        for key in (
            "medication_loaded_count",
            "medication_dispensed_count",
            "medication_returned_count",
            "medication_exception_count",
        ):
            try:
                if int(summary.get(key) or 0) > 0:
                    return True
            except (TypeError, ValueError):
                pass
        for stop in batch.get("stops", []):
            for patient in stop.get("patients", []):
                for medication in patient.get("medications", []):
                    if (
                        medication.get("loaded")
                        or medication.get("dispensed")
                        or medication.get("returned")
                        or medication.get("exception")
                    ):
                        return True
        return False

    def create_catalog_delivery_batch_for_scan(self, product_code, trace_id):
        product_code = str(product_code or "").strip()
        trace_id = str(trace_id or "").strip()
        if not product_code and not trace_id:
            return None
        station_names = {station["id"]: station["name"] for station in self.stations}
        for order in PATIENT_MEDICATION_ORDERS:
            for source_medication in order.get("medications", []):
                if not self.batch_medication_matches(source_medication, product_code, trace_id):
                    continue
                patient = copy.deepcopy(order)
                medication = copy.deepcopy(source_medication)
                self.reset_medication_runtime_fields(medication)
                patient["medications"] = [medication]
                patient["patient_status"] = "WAITING_LOAD_CONFIRMATION"
                station_id = patient.get("target_station") or patient.get("ward_id") or "ward_a"
                now = self.now_text()
                batch = {
                    "batch_id": f"AUTO-SCAN-{time.strftime('%Y%m%d-%H%M%S', time.localtime())}",
                    "source_station": "pharmacy",
                    "route": ["pharmacy", station_id, "pharmacy"],
                    "route_status": "WAITING_LOAD_CONFIRMATION",
                    "current_station": "pharmacy",
                    "active_stop_index": -1,
                    "active_stop_id": "",
                    "created_time": now,
                    "started_time": "",
                    "finished_time": "",
                    "operator_id": "auto_scan_catalog",
                    "audit_records": [
                        {
                            "time": now,
                            "event": "batch_created_from_scan",
                            "message": f"\u6839\u636e\u626b\u7801\u7ed3\u679c\u81ea\u52a8\u521b\u5efa\u88c5\u836f\u6d4b\u8bd5\u6279\u6b21\uff1a{product_code or '-'} / {trace_id or '-'}",
                            "result": "ok",
                        }
                    ],
                    "stops": [
                        {
                            "stop_id": f"stop_{station_id}",
                            "target_station": station_id,
                            "display_name": station_names.get(station_id, station_id),
                            "sequence_index": 1,
                            "stop_status": "WAITING_LOAD_CONFIRMATION",
                            "arrived_time": "",
                            "completed_time": "",
                            "patients": [patient],
                        }
                    ],
                }
                self.update_batch_summary(batch)
                return batch
        return None

    def append_catalog_medication_to_auto_batch_locked(self, batch, product_code, trace_id):
        if not isinstance(batch, dict):
            return False
        if not self.text_value(batch.get("batch_id")).startswith("AUTO-SCAN-"):
            return False
        product_code = str(product_code or "").strip()
        trace_id = str(trace_id or "").strip()
        if not product_code and not trace_id:
            return False
        existing = self.find_batch_medication_candidates(
            batch,
            product_code,
            trace_id,
            "load",
            include_unavailable=True,
        )
        if existing:
            return False
        station_names = {station["id"]: station["name"] for station in self.stations}
        for order in PATIENT_MEDICATION_ORDERS:
            for source_medication in order.get("medications", []):
                if not self.batch_medication_matches(source_medication, product_code, trace_id):
                    continue
                patient = copy.deepcopy(order)
                medication = copy.deepcopy(source_medication)
                self.reset_medication_runtime_fields(medication)
                patient["medications"] = [medication]
                patient["patient_status"] = "WAITING_LOAD_CONFIRMATION"
                station_id = patient.get("target_station") or patient.get("ward_id") or "ward_a"
                stops = batch.setdefault("stops", [])
                target_stop = None
                for stop in stops:
                    if self.text_value(stop.get("target_station")) == self.text_value(station_id):
                        target_stop = stop
                        break
                if target_stop is None:
                    target_stop = {
                        "stop_id": f"stop_{station_id}",
                        "target_station": station_id,
                        "display_name": station_names.get(station_id, station_id),
                        "sequence_index": len(stops) + 1,
                        "stop_status": "WAITING_LOAD_CONFIRMATION",
                        "arrived_time": "",
                        "completed_time": "",
                        "patients": [],
                    }
                    stops.append(target_stop)
                    route = batch.setdefault("route", ["pharmacy"])
                    if station_id not in route:
                        if route and route[-1] == "pharmacy":
                            route.insert(max(len(route) - 1, 1), station_id)
                        else:
                            route.append(station_id)
                existing_patient = None
                for current_patient in target_stop.setdefault("patients", []):
                    if self.text_value(current_patient.get("patient_id")) == self.text_value(patient.get("patient_id")):
                        existing_patient = current_patient
                        break
                if existing_patient is None:
                    target_stop["patients"].append(patient)
                else:
                    existing_patient.setdefault("medications", []).append(medication)
                    existing_patient["patient_status"] = "WAITING_LOAD_CONFIRMATION"
                batch["route_status"] = "WAITING_LOAD_CONFIRMATION"
                self.append_batch_audit(
                    batch,
                    "batch_auto_scan_medication_added",
                    f"\u81ea\u52a8\u626b\u63cf\u6d4b\u8bd5\u6279\u6b21\u8ffd\u52a0\u836f\u54c1\uff1a{patient.get('bed_no') or '-'} {patient.get('patient_name') or '-'} / {medication.get('medicine_name') or '-'}",
                    "ok",
                    {
                        "patient_id": patient.get("patient_id", ""),
                        "medication_id": medication.get("id", ""),
                        "scanned_product_code": product_code,
                        "scanned_trace_id": trace_id,
                    },
                )
                self.update_batch_summary(batch)
                self.save_delivery_batch_state_locked(batch)
                return True
        return False

    def maybe_adopt_catalog_batch_for_scan_locked(self, product_code, trace_id):
        current = getattr(self, "delivery_batch", None)
        if self.delivery_batch_has_progress(current):
            if self.append_catalog_medication_to_auto_batch_locked(current, product_code, trace_id):
                return current, True
            return current, False
        catalog_batch = self.create_catalog_delivery_batch_for_scan(product_code, trace_id)
        if not catalog_batch:
            return current, False
        self.delivery_batch = catalog_batch
        self.pending_delivery_batch = None
        self.save_delivery_batch_state_locked(self.delivery_batch)
        self.save_pending_delivery_batch_state_locked(None)
        return self.delivery_batch, True

    def load_delivery_batch_state(self):
        try:
            with open(self.delivery_batch_state_file, "r", encoding="utf-8") as file:
                batch = json.load(file)
            if not isinstance(batch, dict) or "stops" not in batch:
                raise ValueError("invalid delivery batch state")
            self.update_batch_summary(batch)
            return batch
        except (FileNotFoundError, json.JSONDecodeError, ValueError, OSError):
            batch = self.create_demo_delivery_batch()
            self.save_delivery_batch_state_locked(batch)
            return batch

    def save_delivery_batch_state_locked(self, batch):
        directory = os.path.dirname(self.delivery_batch_state_file)
        if directory:
            os.makedirs(directory, exist_ok=True)
        temp_file = f"{self.delivery_batch_state_file}.tmp"
        with open(temp_file, "w", encoding="utf-8") as file:
            json.dump(batch, file, ensure_ascii=False, indent=2)
        os.replace(temp_file, self.delivery_batch_state_file)

    def load_pending_delivery_batch_state(self):
        path = getattr(self, "pending_delivery_batch_file", "")
        if not path:
            return None
        try:
            with open(path, "r", encoding="utf-8") as file:
                envelope = json.load(file)
            if not isinstance(envelope, dict) or "batch" not in envelope:
                raise ValueError("invalid pending delivery batch")
            batch = envelope.get("batch")
            if not isinstance(batch, dict) or "stops" not in batch:
                raise ValueError("invalid pending batch payload")
            self.update_batch_summary(batch)
            envelope["batch"] = batch
            return envelope
        except (FileNotFoundError, json.JSONDecodeError, ValueError, OSError):
            return None

    def save_pending_delivery_batch_state_locked(self, envelope):
        path = getattr(self, "pending_delivery_batch_file", "")
        if not path:
            return
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        if not envelope:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass
            return
        temp_file = f"{path}.tmp"
        with open(temp_file, "w", encoding="utf-8") as file:
            json.dump(envelope, file, ensure_ascii=False, indent=2)
        os.replace(temp_file, path)

    def summarize_imported_batch(self, batch):
        summary = batch.get("summary") or {}
        return {
            "batch_id": batch.get("batch_id", ""),
            "source_station": batch.get("source_station", ""),
            "route_status": batch.get("route_status", ""),
            "stop_count": len(batch.get("stops", [])),
            "patient_count": int(summary.get("patient_total_count", 0) or 0),
            "medication_count": int(summary.get("medication_total_count", 0) or 0),
            "route": batch.get("route", []),
        }

    def get_pending_delivery_batch(self):
        with self.delivery_batch_lock:
            pending = copy.deepcopy(getattr(self, "pending_delivery_batch", None))
            if pending and isinstance(pending.get("batch"), dict):
                self.update_batch_summary(pending["batch"])
                pending["summary"] = self.summarize_imported_batch(pending["batch"])
            return {"pending": pending}

    def receive_external_delivery_batch(self, payload):
        with self.delivery_batch_lock:
            try:
                batch = self.create_delivery_batch_from_payload(payload)
                now = self.now_text()
                source = self.text_value(
                    payload.get("source") or payload.get("source_system"), "external"
                )
                envelope = {
                    "status": "PENDING_ADOPTION",
                    "source": source,
                    "received_at": now,
                    "issued_at": self.text_value(payload.get("issued_at")),
                    "message": self.text_value(payload.get("message")),
                    "raw_batch_id": self.text_value(payload.get("batch_id")),
                    "summary": self.summarize_imported_batch(batch),
                    "batch": batch,
                }
                self.pending_delivery_batch = envelope
                self.save_pending_delivery_batch_state_locked(envelope)
                return {
                    "ok": True,
                    "message": f"已接收外部批次，等待采用：{batch.get('batch_id')}",
                    "pending": copy.deepcopy(envelope),
                }
            except ValueError as error:
                return {"ok": False, "message": str(error)}

    def adopt_pending_delivery_batch(self, payload=None):
        payload = payload or {}
        with self.delivery_batch_lock:
            pending = getattr(self, "pending_delivery_batch", None)
            if not pending or not isinstance(pending.get("batch"), dict):
                return {"ok": False, "message": "没有待采用的外部批次"}
            batch = copy.deepcopy(pending["batch"])
            self.update_batch_summary(batch)
            self.append_batch_audit(
                batch,
                "external_batch_adopted",
                f"已采用外部批次：来源 {pending.get('source') or '-'}?接收时间 {pending.get('received_at') or '-'}",
                "ok",
                {
                    "external_source": pending.get("source", ""),
                    "external_received_at": pending.get("received_at", ""),
                    "external_issued_at": pending.get("issued_at", ""),
                    "adopt_operator": self.text_value(payload.get("operator_id")),
                },
            )
            self.delivery_batch = batch
            self.pending_delivery_batch = None
            self.save_delivery_batch_state_locked(self.delivery_batch)
            self.save_pending_delivery_batch_state_locked(None)
            return {
                "ok": True,
                "message": f"已采用外部批次：{batch.get('batch_id')}",
                "batch": copy.deepcopy(self.delivery_batch),
                "pending": None,
            }

    def discard_pending_delivery_batch(self):
        with self.delivery_batch_lock:
            pending = getattr(self, "pending_delivery_batch", None)
            if not pending:
                return {"ok": True, "message": "当前没有待采用批次", "pending": None}
            batch_id = (pending.get("summary") or {}).get("batch_id") or pending.get("raw_batch_id") or "-"
            self.pending_delivery_batch = None
            self.save_pending_delivery_batch_state_locked(None)
            return {"ok": True, "message": f"已忽略待采用批次：{batch_id}", "pending": None}

    def update_delivery_batch_patient_info(self, payload):
        """Update editable patient profile/clinical context in current batch."""
        payload = payload or {}
        patient_id = self.text_value(payload.get("patient_id"))
        bed_no = self.text_value(payload.get("bed_no") or payload.get("bed"))
        editable_fields = (
            "patient_name",
            "age",
            "gender",
            "height_cm",
            "weight_kg",
            "diagnosis",
            "allergies",
            "contraindications",
            "nursing_note",
            "doctor_name",
            "doctor_title",
            "prescription_no",
            "prescription_note",
        )
        if not patient_id and not bed_no:
            return {"ok": False, "message": "\u7f3a\u5c11 patient_id \u6216 bed_no"}
        with self.delivery_batch_lock:
            batch = getattr(self, "delivery_batch", None)
            if not isinstance(batch, dict):
                return {"ok": False, "message": "\u5f53\u524d\u6ca1\u6709\u53ef\u7f16\u8f91\u7684\u914d\u9001\u6279\u6b21"}
            target = None
            for stop in batch.get("stops", []) or []:
                for patient in stop.get("patients", []) or []:
                    if not isinstance(patient, dict):
                        continue
                    if patient_id and self.text_value(patient.get("patient_id")) == patient_id:
                        target = patient
                        break
                    if bed_no and self.text_value(patient.get("bed_no")) == bed_no:
                        target = patient
                        break
                if target is not None:
                    break
            if target is None:
                return {"ok": False, "message": "\u672a\u627e\u5230\u5bf9\u5e94\u75c5\u4eba"}
            changed = {}
            for field in editable_fields:
                if field not in payload:
                    continue
                value = payload.get(field)
                if value is None:
                    value = ""
                if isinstance(value, str):
                    value = value.strip()
                if target.get(field) != value:
                    target[field] = value
                    changed[field] = value
            if not changed:
                return {
                    "ok": True,
                    "message": "\u75c5\u4eba\u4fe1\u606f\u65e0\u53d8\u5316",
                    "patient": copy.deepcopy(target),
                    "batch": copy.deepcopy(batch),
                }
            self.append_batch_audit(
                batch,
                "patient_info_updated",
                f"\u5df2\u66f4\u65b0\u75c5\u4eba\u4fe1\u606f\uff1a{target.get('bed_no') or '-'} {target.get('patient_name') or '-'}",
                "ok",
                {"patient_id": target.get("patient_id", ""), "bed_no": target.get("bed_no", ""), "fields": list(changed.keys())},
            )
            self.update_batch_summary(batch)
            self.save_delivery_batch_state_locked(batch)
            return {
                "ok": True,
                "message": "\u75c5\u4eba\u4fe1\u606f\u5df2\u4fdd\u5b58\uff0c8081 \u75c5\u4eba\u7aef\u4f1a\u81ea\u52a8\u5237\u65b0",
                "patient": copy.deepcopy(target),
                "batch": copy.deepcopy(batch),
                "changed": changed,
            }

    def update_delivery_batch_medication_info(self, payload):
        """Update editable medication instruction fields in current batch."""
        payload = payload or {}
        medication_id = self.text_value(payload.get("medication_id") or payload.get("id"))
        product_code = self.text_value(payload.get("product_code"))
        trace_id = self.text_value(payload.get("trace_id"))
        editable_fields = (
            "medicine_name",
            "product_code",
            "product_model",
            "quantity",
            "dose",
            "usage",
            "frequency",
            "route_label",
            "timing",
            "duration",
            "precautions",
            "doctor_note",
        )
        if not medication_id and not product_code and not trace_id:
            return {"ok": False, "message": "\u7f3a\u5c11 medication_id/product_code/trace_id"}
        with self.delivery_batch_lock:
            batch = getattr(self, "delivery_batch", None)
            if not isinstance(batch, dict):
                return {"ok": False, "message": "\u5f53\u524d\u6ca1\u6709\u53ef\u7f16\u8f91\u7684\u914d\u9001\u6279\u6b21"}
            target = None
            owner_patient = None
            for stop in batch.get("stops", []) or []:
                for patient in stop.get("patients", []) or []:
                    if not isinstance(patient, dict):
                        continue
                    for med in patient.get("medications", []) or []:
                        if not isinstance(med, dict):
                            continue
                        if medication_id and self.text_value(med.get("id")) == medication_id:
                            target = med
                        elif product_code and self.text_value(med.get("product_code")) == product_code:
                            target = med
                        elif trace_id and self.text_value(med.get("trace_id")) == trace_id:
                            target = med
                        if target is not None:
                            owner_patient = patient
                            break
                    if target is not None:
                        break
                if target is not None:
                    break
            if target is None:
                return {"ok": False, "message": "\u672a\u627e\u5230\u5bf9\u5e94\u836f\u54c1"}
            changed = {}
            for field in editable_fields:
                if field not in payload:
                    continue
                value = payload.get(field)
                if value is None:
                    value = ""
                if isinstance(value, str):
                    value = value.strip()
                if target.get(field) != value:
                    target[field] = value
                    changed[field] = value
            if not changed:
                return {
                    "ok": True,
                    "message": "\u836f\u54c1\u8bf4\u660e\u65e0\u53d8\u5316",
                    "medication": copy.deepcopy(target),
                    "batch": copy.deepcopy(batch),
                }
            self.append_batch_audit(
                batch,
                "medication_info_updated",
                f"\u5df2\u66f4\u65b0\u836f\u54c1\u8bf4\u660e\uff1a{owner_patient.get('bed_no') if owner_patient else '-'} {target.get('medicine_name') or '-'}",
                "ok",
                {
                    "medication_id": target.get("id", ""),
                    "product_code": target.get("product_code", ""),
                    "trace_id": target.get("trace_id", ""),
                    "fields": list(changed.keys()),
                },
            )
            self.update_batch_summary(batch)
            self.save_delivery_batch_state_locked(batch)
            return {
                "ok": True,
                "message": "\u836f\u54c1\u8bf4\u660e\u5df2\u4fdd\u5b58\uff0c8081 \u548c AI \u8bed\u97f3\u4f1a\u4f7f\u7528\u6700\u65b0\u4fe1\u606f",
                "medication": copy.deepcopy(target),
                "batch": copy.deepcopy(batch),
                "changed": changed,
            }

    def now_text(self):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    def update_batch_summary(self, batch):
        total_patients = 0
        completed_patients = 0
        total_medications = 0
        loaded_medications = 0
        dispensed_medications = 0
        returned_medications = 0
        exception_medications = 0
        done_medications = 0
        completed_stops = 0
        for stop in batch.get("stops", []):
            stop_total = 0
            stop_loaded = 0
            stop_dispensed = 0
            stop_returned = 0
            stop_exception = 0
            stop_done = 0
            stop_patient_done = 0
            patients = stop.get("patients", [])
            total_patients += len(patients)
            for patient in patients:
                patient_medications = patient.get("medications", [])
                patient_total = len(patient_medications)
                patient_loaded = sum(
                    1 for item in patient_medications if item.get("loaded")
                )
                patient_dispensed = sum(
                    1 for item in patient_medications if item.get("dispensed")
                )
                patient_returned = sum(
                    1 for item in patient_medications if item.get("returned")
                )
                patient_exception = sum(
                    1 for item in patient_medications if item.get("exception")
                )
                patient_done = sum(
                    1
                    for item in patient_medications
                    if item.get("dispensed")
                    or item.get("returned")
                    or item.get("exception")
                )
                stop_total += patient_total
                stop_loaded += patient_loaded
                stop_dispensed += patient_dispensed
                stop_returned += patient_returned
                stop_exception += patient_exception
                stop_done += patient_done
                total_medications += patient_total
                loaded_medications += patient_loaded
                dispensed_medications += patient_dispensed
                returned_medications += patient_returned
                exception_medications += patient_exception
                done_medications += patient_done
                if patient.get("medication_review_required"):
                    patient["patient_status"] = "WAITING_MEDICATION_REVIEW"
                elif patient_total and patient_done >= patient_total:
                    patient["patient_status"] = "COMPLETED"
                    completed_patients += 1
                    stop_patient_done += 1
                elif patient_loaded:
                    patient["patient_status"] = "LOADED"
                else:
                    patient["patient_status"] = "WAITING_LOAD_CONFIRMATION"
            stop["medication_total_count"] = stop_total
            stop["medication_loaded_count"] = stop_loaded
            stop["medication_dispensed_count"] = stop_dispensed
            stop["medication_returned_count"] = stop_returned
            stop["medication_exception_count"] = stop_exception
            stop["medication_done_count"] = stop_done
            if stop_total and stop["medication_done_count"] >= stop_total:
                if stop.get("stop_status") not in {
                    "WAITING_LOAD_CONFIRMATION",
                    "NAVIGATING_TO_WARD",
                }:
                    stop["stop_status"] = "COMPLETED"
                completed_stops += 1
            elif stop_loaded >= stop_total and stop_total:
                if stop.get("stop_status") == "WAITING_LOAD_CONFIRMATION":
                    stop["stop_status"] = "READY_TO_DEPART"
            if patients and stop_patient_done >= len(patients):
                completed_stops += 0
        all_loaded = total_medications > 0 and loaded_medications >= total_medications
        all_dispensed = (
            total_medications > 0 and dispensed_medications >= total_medications
        )
        batch["summary"] = {
            "stop_total_count": len(batch.get("stops", [])),
            "stop_completed_count": sum(
                1
                for stop in batch.get("stops", [])
                if stop.get("stop_status") == "COMPLETED"
            ),
            "patient_total_count": total_patients,
            "patient_completed_count": completed_patients,
            "medication_total_count": total_medications,
            "medication_loaded_count": loaded_medications,
            "medication_dispensed_count": dispensed_medications,
            "medication_returned_count": returned_medications,
            "medication_exception_count": exception_medications,
            "medication_done_count": done_medications,
            "all_loaded": all_loaded,
            "all_dispensed": all_dispensed,
        }
        if all_loaded and batch.get("route_status") == "WAITING_LOAD_CONFIRMATION":
            batch["route_status"] = "READY_TO_DEPART"

    def append_batch_audit(self, batch, event, message, result="ok", extra=None):
        record = {
            "time": self.now_text(),
            "event": event,
            "message": message,
            "result": result,
        }
        if isinstance(extra, dict):
            record.update(extra)
        batch.setdefault("audit_records", []).append(record)
        del batch["audit_records"][:-80]

    def get_delivery_batch(self):
        with self.delivery_batch_lock:
            self.update_batch_summary(self.delivery_batch)
            return copy.deepcopy(self.delivery_batch)

    def reset_delivery_batch(self):
        with self.delivery_batch_lock:
            self.delivery_batch = self.create_demo_delivery_batch()
            return copy.deepcopy(self.delivery_batch)

    def text_value(self, value, default=""):
        text = str(value if value is not None else "").strip()
        return text or default

    def medicine_alias_groups(self):
        return [
            ["\u82ef\u78fa\u9178\u6c28\u6c2f\u5730\u5e73\u7247", "\u6c28\u6c2f\u5730\u5e73\u7247", "\u6c28\u6c2f\u5730\u5e73", "\u7edc\u6d3b\u559c"],
            ["\u5934\u5b62\u544b\u8f9b\u916f\u7247", "\u5934\u5b62\u544b\u8f9b", "\u5934\u5b62\u544b\u8f9b\u916f"],
            ["\u5965\u7f8e\u62c9\u5511\u80a0\u6eb6\u80f6\u56ca", "\u5965\u7f8e\u62c9\u5511\u80f6\u56ca", "\u5965\u7f8e\u62c9\u5511"],
            ["\u76d0\u9178\u6c28\u6eb4\u7d22\u53e3\u670d\u6db2", "\u6c28\u6eb4\u7d22\u53e3\u670d\u6db2", "\u6c28\u6eb4\u7d22"],
            ["\u53f3\u7f8e\u6c99\u82ac\u53e3\u670d\u6eb6\u6db2", "\u53f3\u7f8e\u6c99\u82ac\u53e3\u670d\u6db2", "\u53f3\u7f8e\u6c99\u82ac"],
            ["\u4e91\u5357\u767d\u836f\u521b\u53ef\u8d34", "\u767d\u836f\u521b\u53ef\u8d34", "\u521b\u53ef\u8d34"],
            ["\u5bf9\u4e59\u9170\u6c28\u57fa\u915a", "\u5bf9\u4e59\u9170\u6c28\u57fa\u915a\u7247", "\u9000\u70e7\u836f"],
            ["\u4e8c\u7532\u53cc\u80cd", "\u4e8c\u7532\u53cc\u80cd\u7247", "\u964d\u7cd6\u836f"],
            ["\u6c2f\u96f7\u4ed6\u5b9a", "\u6c2f\u96f7\u4ed6\u5b9a\u7247", "\u6297\u8fc7\u654f\u836f"],
        ]

    def medicine_alias_canonical(self, value):
        normalized = self.normalize_medicine_match_text(value)
        if not normalized:
            return ""
        for group in self.medicine_alias_groups():
            normalized_group = [self.normalize_medicine_match_text(item) for item in group]
            if normalized in normalized_group:
                return normalized_group[0]
        return normalized

    def clean_identifier(self, value, default):
        text = self.text_value(value, default)
        cleaned = "".join(
            char if char.isalnum() or char in {"_", "-"} else "_" for char in text
        )
        return cleaned or default

    def normalize_batch_medication(self, medication, patient_id, index):
        if not isinstance(medication, dict):
            raise ValueError("药品条目必须是对象")
        medication_id = self.clean_identifier(
            medication.get("id") or medication.get("medication_id"),
            f"{patient_id}_med_{index + 1:03d}",
        )
        return {
            "id": medication_id,
            "medicine_name": self.text_value(
                medication.get("medicine_name") or medication.get("name"), "未命名药品"
            ),
            "product_code": self.text_value(medication.get("product_code")),
            "product_model": self.text_value(medication.get("product_model")),
            "quantity": self.text_value(medication.get("quantity"), "1"),
            "trace_id": self.text_value(medication.get("trace_id")),
            "order_no": self.text_value(medication.get("order_no")),
            "dose": self.text_value(medication.get("dose")),
            "usage": self.text_value(medication.get("usage")),
            "loaded": False,
            "loaded_at": "",
            "dispensed": False,
            "dispensed_at": "",
            "returned": False,
            "returned_at": "",
            "return_reason": "",
            "exception": "",
            "exception_at": "",
            "exception_reason": "",
            "exception_resolved_at": "",
            "exception_resolved_reason": "",
            "exception_resolution_action": "",
            "manual_reviewed": False,
            "manual_reviewed_at": "",
            "manual_review_result": "",
            "task_manager_task_id": self.text_value(
                medication.get("task_manager_task_id")
            ),
        }

    def normalize_batch_patient(self, patient, index, default_station=""):
        if not isinstance(patient, dict):
            raise ValueError("病人条目必须是对象")
        patient_id = self.clean_identifier(
            patient.get("patient_id") or patient.get("id"),
            f"patient_{index + 1:03d}",
        )
        target_station = self.text_value(
            patient.get("target_station") or patient.get("ward_id") or default_station,
            default_station or "ward_a",
        )
        medications = patient.get("medications") or patient.get("items") or []
        if not isinstance(medications, list) or not medications:
            raise ValueError(f"病人 {patient_id} 至少需要 1 项药品")
        normalized = {
            "patient_id": patient_id,
            "patient_name": self.text_value(
                patient.get("patient_name") or patient.get("name"), "未命名患者"
            ),
            "ward_id": self.text_value(patient.get("ward_id"), target_station),
            "ward_name": self.text_value(patient.get("ward_name"), target_station),
            "bed_no": self.text_value(patient.get("bed_no")),
            "target_station": target_station,
            "medications": [
                self.normalize_batch_medication(item, patient_id, medication_index)
                for medication_index, item in enumerate(medications)
            ],
            "patient_status": "WAITING_LOAD_CONFIRMATION",
        }
        return normalized

    def create_delivery_batch_from_payload(self, payload):
        if not isinstance(payload, dict):
            raise ValueError("批次 JSON 必须是对象")
        now = self.now_text()
        source_station = self.text_value(payload.get("source_station"), "pharmacy")
        station_names = {station["id"]: station["name"] for station in self.stations}
        stops = []
        route_stations = []
        source_stops = payload.get("stops")
        if isinstance(source_stops, list) and source_stops:
            patient_index = 0
            for stop_index, source_stop in enumerate(source_stops):
                if not isinstance(source_stop, dict):
                    raise ValueError("病房站点条目必须是对象")
                station_id = self.text_value(
                    source_stop.get("target_station")
                    or source_stop.get("station_id")
                    or source_stop.get("ward_id"),
                    f"ward_{stop_index + 1}",
                )
                source_patients = source_stop.get("patients") or []
                if not isinstance(source_patients, list):
                    raise ValueError(f"站点 {station_id} 的 patients 必须是数组")
                patients = []
                for patient in source_patients:
                    patients.append(
                        self.normalize_batch_patient(patient, patient_index, station_id)
                    )
                    patient_index += 1
                route_stations.append(station_id)
                stops.append(
                    {
                        "stop_id": self.clean_identifier(
                            source_stop.get("stop_id"), f"stop_{station_id}"
                        ),
                        "target_station": station_id,
                        "display_name": self.text_value(
                            source_stop.get("display_name")
                            or source_stop.get("ward_name"),
                            station_names.get(station_id, station_id),
                        ),
                        "sequence_index": stop_index + 1,
                        "stop_status": "WAITING_LOAD_CONFIRMATION",
                        "arrived_time": "",
                        "completed_time": "",
                        "patients": patients,
                    }
                )
        else:
            source_patients = payload.get("patients") or payload.get("orders") or []
            if not isinstance(source_patients, list) or not source_patients:
                raise ValueError("批次 JSON 需要包含 patients 数组或 stops 数组")
            grouped = []
            station_index = {}
            for patient_index, patient in enumerate(source_patients):
                normalized_patient = self.normalize_batch_patient(
                    patient, patient_index
                )
                station_id = normalized_patient.get("target_station", "ward_a")
                if station_id not in station_index:
                    station_index[station_id] = len(grouped)
                    grouped.append({"station_id": station_id, "patients": []})
                grouped[station_index[station_id]]["patients"].append(
                    normalized_patient
                )
            route_payload = payload.get("route") or []
            if isinstance(route_payload, list):
                for station_id in route_payload:
                    station_id = self.text_value(station_id)
                    if (
                        station_id
                        and station_id != source_station
                        and station_id not in route_stations
                    ):
                        route_stations.append(station_id)
            for group in grouped:
                if group["station_id"] not in route_stations:
                    route_stations.append(group["station_id"])
            for stop_index, station_id in enumerate(route_stations):
                group = next(
                    (item for item in grouped if item["station_id"] == station_id),
                    {"patients": []},
                )
                stops.append(
                    {
                        "stop_id": f"stop_{station_id}",
                        "target_station": station_id,
                        "display_name": station_names.get(station_id, station_id),
                        "sequence_index": stop_index + 1,
                        "stop_status": "WAITING_LOAD_CONFIRMATION",
                        "arrived_time": "",
                        "completed_time": "",
                        "patients": group["patients"],
                    }
                )
        medication_count = sum(
            len(patient.get("medications", []))
            for stop in stops
            for patient in stop.get("patients", [])
        )
        if medication_count <= 0:
            raise ValueError("批次至少需要 1 项药品")
        batch = {
            "batch_id": self.text_value(
                payload.get("batch_id"),
                f"REAL-{time.strftime('%Y%m%d-%H%M%S', time.localtime())}",
            ),
            "source_station": source_station,
            "route": [source_station] + route_stations + [source_station],
            "route_status": "WAITING_LOAD_CONFIRMATION",
            "current_station": source_station,
            "active_stop_index": -1,
            "active_stop_id": "",
            "created_time": now,
            "started_time": "",
            "finished_time": "",
            "operator_id": self.text_value(payload.get("operator_id"), "web_operator"),
            "audit_records": [
                {
                    "time": now,
                    "event": "batch_imported",
                    "message": f"真实配送批次已导入：{len(stops)} 个病房，{medication_count} 项药品",
                    "result": "ok",
                }
            ],
            "stops": stops,
        }
        self.update_batch_summary(batch)
        return batch

    def import_delivery_batch(self, payload):
        response = self.receive_external_delivery_batch(payload)
        if not response.get("ok"):
            return response
        return {
            "ok": True,
            "message": response.get("message", "已接收外部批次，等待采用"),
            "pending": response.get("pending"),
        }

    def apply_imported_delivery_batch(self, payload):
        response = self.receive_external_delivery_batch(payload)
        if not response.get("ok"):
            return response
        return self.adopt_pending_delivery_batch({})

    def build_stop_task_payload(self, batch, stop):
        medications = []
        patient_names = []
        bed_numbers = []
        patient_ids = []
        for patient in stop.get("patients", []):
            patient_id = self.text_value(patient.get("patient_id"))
            patient_name = self.text_value(patient.get("patient_name"))
            bed_no = self.text_value(patient.get("bed_no"))
            if patient_name:
                patient_names.append(patient_name)
            if bed_no:
                bed_numbers.append(bed_no)
            if patient_id:
                patient_ids.append(patient_id)
            for medication in patient.get("medications", []):
                if (
                    medication.get("dispensed")
                    or medication.get("returned")
                    or medication.get("exception")
                ):
                    continue
                medication_payload = {
                    "id": self.text_value(medication.get("id")),
                    "medicine_name": self.text_value(
                        medication.get("medicine_name"), "未命名药品"
                    ),
                    "product_code": self.text_value(medication.get("product_code")),
                    "product_model": self.text_value(medication.get("product_model")),
                    "quantity": self.text_value(medication.get("quantity"), "1"),
                    "trace_id": self.text_value(medication.get("trace_id")),
                    "order_no": self.text_value(medication.get("order_no")),
                    "dose": self.text_value(medication.get("dose")),
                    "usage": self.text_value(medication.get("usage")),
                    "patient_id": patient_id,
                    "patient_name": patient_name,
                    "ward_id": self.text_value(
                        patient.get("ward_id"), stop.get("target_station", "")
                    ),
                    "bed_no": bed_no,
                    "load_confirmed": bool(medication.get("loaded")),
                    "load_confirmed_at": self.text_value(medication.get("loaded_at")),
                    "dispense_confirmed": bool(medication.get("dispensed")),
                    "dispense_confirmed_at": self.text_value(
                        medication.get("dispensed_at")
                    ),
                }
                medications.append(medication_payload)
        if not medications:
            return None
        primary = medications[0]
        return {
            "medicine_name": f"{stop.get('display_name') or stop.get('target_station')}批次药品（{len(medications)}项）",
            "source_station": self.text_value(batch.get("source_station"), "pharmacy"),
            "target_station": self.text_value(stop.get("target_station")),
            "patient_id": ",".join(patient_ids[:8]),
            "patient_name": "、".join(patient_names[:8]),
            "ward_id": self.text_value(stop.get("target_station")),
            "bed_no": "、".join(bed_numbers[:8]),
            "product_code": primary.get("product_code", ""),
            "product_model": primary.get("product_model", ""),
            "quantity": str(len(medications)),
            "trace_id": primary.get("trace_id", ""),
            "order_no": f"{batch.get('batch_id', '')}/{stop.get('stop_id', '')}",
            "medications_json": json.dumps(medications, ensure_ascii=False),
        }

    def create_task_from_payload_locked(self, payload):
        if not self.create_task_client.wait_for_service(
            timeout_sec=self.service_timeout_sec
        ):
            return {"accepted": False, "task_id": "", "message": "创建任务服务不可用"}
        request = CreateDeliveryTask.Request()
        request.medicine_name = str(payload.get("medicine_name") or "常规药品")
        request.source_station = str(payload.get("source_station") or "pharmacy")
        request.target_station = str(payload.get("target_station") or "")
        request.patient_id = str(payload.get("patient_id") or "")
        request.patient_name = str(payload.get("patient_name") or "")
        request.ward_id = str(payload.get("ward_id") or "")
        request.bed_no = str(payload.get("bed_no") or "")
        request.product_code = str(payload.get("product_code") or "")
        request.product_model = str(payload.get("product_model") or "")
        request.quantity = str(payload.get("quantity") or "")
        request.trace_id = str(payload.get("trace_id") or "")
        request.order_no = str(payload.get("order_no") or "")
        request.medications_json = str(payload.get("medications_json") or "")
        future = self.create_task_client.call_async(request)
        response = self.wait_future(future)
        if response is None:
            return {"accepted": False, "task_id": "", "message": "创建任务服务超时"}
        return {
            "accepted": bool(response.accepted),
            "task_id": response.task_id,
            "message": response.message,
        }

    def create_task_manager_stop_task_locked(self, batch, stop):
        payload = self.build_stop_task_payload(batch, stop)
        if payload is None:
            return {
                "accepted": True,
                "task_id": "",
                "message": "当前病房没有需要创建任务的药品",
            }
        response = self.create_task_from_payload_locked(payload)
        if not response.get("accepted"):
            return response
        task_id = response.get("task_id", "")
        now = self.now_text()
        stop["task_manager_task_id"] = task_id
        stop["task_manager_task_created_at"] = now
        stop["task_manager_task_message"] = response.get("message", "")
        for patient in stop.get("patients", []):
            for medication in patient.get("medications", []):
                if (
                    medication.get("dispensed")
                    or medication.get("returned")
                    or medication.get("exception")
                ):
                    continue
                medication["task_manager_task_id"] = task_id
        return response

    def persist_current_delivery_batch(self):
        with self.delivery_batch_lock:
            self.update_batch_summary(self.delivery_batch)
            self.save_delivery_batch_state_locked(self.delivery_batch)
            self.save_batch_to_db_locked(self.delivery_batch)

    def collect_delivery_batch_backend_blockers(self, batch, action="advance", include_motion=True):
        blockers = []
        warnings = []
        if not isinstance(batch, dict) or not batch.get("batch_id"):
            blockers.append("\u5f53\u524d\u6ca1\u6709\u914d\u9001\u6279\u6b21\uff0c\u62d2\u7edd\u6267\u884c\u64cd\u4f5c")
            return blockers, warnings
        self.update_batch_summary(batch)
        status = batch.get("route_status") or "WAITING_LOAD_CONFIRMATION"
        summary = batch.get("summary") or {}
        danger_count = 0
        review_count = 0
        returned_count = 0
        for stop in batch.get("stops", []):
            for patient in stop.get("patients", []):
                patient_review = bool(
                    patient.get("medication_review_required")
                    or patient.get("patient_status") == "WAITING_MEDICATION_REVIEW"
                )
                if patient.get("patient_status") in {"PATIENT_REJECTED", "PATIENT_ABSENT"}:
                    danger_count += 1
                if patient_review:
                    review_count += 1
                for medication in patient.get("medications", []):
                    if medication.get("review_required"):
                        review_count += 1
                    exception = str(medication.get("exception") or "").strip()
                    if exception and not medication.get("exception_resolved_at"):
                        if exception != "patient_rejected":
                            danger_count += 1
                    if medication.get("returned") and not medication.get("dispensed"):
                        returned_count += 1
        safety_latest = self.get_delivery_safety_self_test_result()
        safety_result = safety_latest.get("result") if isinstance(safety_latest, dict) else None
        if safety_result:
            if safety_result.get("ok") is False:
                blockers.append(
                    f"\u5b89\u5168\u95e8\u81ea\u6d4b\u5931\u8d25\uff1a{int(safety_result.get('passed') or 0)}/{int(safety_result.get('total') or 0)} \u9879\u901a\u8fc7\uff0c\u62d2\u7edd\u7ee7\u7eed\u64cd\u4f5c"
                )
        else:
            warnings.append("\u5c1a\u672a\u6267\u884c\u5b89\u5168\u95e8\u81ea\u6d4b\uff0c\u5efa\u8bae\u5148\u81ea\u6d4b\u540e\u518d\u914d\u9001")
        if danger_count:
            blockers.append(f"\u5f53\u524d\u6279\u6b21\u5b58\u5728 {danger_count} \u9879\u672a\u5904\u7406\u9ad8\u4f18\u5148\u7ea7\u5f02\u5e38\uff0c\u62d2\u7edd\u7ee7\u7eed\u64cd\u4f5c")
        if review_count:
            blockers.append(f"\u5f53\u524d\u6279\u6b21\u5b58\u5728 {review_count} \u9879\u7528\u836f\u5f85\u590d\u6838\uff0c\u62d2\u7edd\u7ee7\u7eed\u64cd\u4f5c")
        if returned_count and action in {"advance", "dispense"}:
            warnings.append(f"\u5f53\u524d\u6279\u6b21\u5b58\u5728 {returned_count} \u9879\u5df2\u56de\u6536\u836f\u54c1\uff0c\u8bf7\u786e\u8ba4\u5ba1\u8ba1\u8bb0\u5f55\u5b8c\u6574")
        if action == "advance":
            if status == "WAITING_LOAD_CONFIRMATION" and not summary.get("all_loaded"):
                total = int(summary.get("medication_total_count") or 0)
                loaded = int(summary.get("medication_loaded_count") or 0)
                blockers.append(f"\u8fd8\u6709 {max(total - loaded, 0)} \u9879\u836f\u54c1\u672a\u5b8c\u6210\u88c5\u836f\u786e\u8ba4\uff0c\u62d2\u7edd\u51fa\u53d1")
            if include_motion and status == "READY_TO_DEPART":
                motion_blocker = self.delivery_motion_blocker()
                if motion_blocker:
                    blockers.append(motion_blocker)
        elif action == "load":
            if status not in {"WAITING_LOAD_CONFIRMATION", "READY_TO_DEPART"}:
                blockers.append(f"\u5f53\u524d\u6279\u6b21\u72b6\u6001\u4e3a {status}\uff0c\u4e0d\u662f\u88c5\u836f\u6838\u9a8c\u9636\u6bb5\uff0c\u62d2\u7edd\u5199\u5165\u88c5\u836f\u8bb0\u5f55")
        elif action == "dispense":
            if status not in {"WARD_HANDOVER", "NAVIGATING_TO_WARD"}:
                blockers.append(f"\u5f53\u524d\u6279\u6b21\u72b6\u6001\u4e3a {status}\uff0c\u5c1a\u672a\u5230\u5e8a\u65c1\u4ea4\u4ed8\u9636\u6bb5\uff0c\u62d2\u7edd\u5199\u5165\u4ea4\u4ed8\u8bb0\u5f55")
        return blockers, warnings

    def get_delivery_batch_safety_gate(self):
        with self.delivery_batch_lock:
            batch = self.delivery_batch
            if isinstance(batch, dict):
                self.update_batch_summary(batch)
            actions = {}
            for action in ("load", "advance", "dispense"):
                blockers, warnings = self.collect_delivery_batch_backend_blockers(
                    batch, action, include_motion=(action == "advance")
                )
                actions[action] = {
                    "action": action,
                    "blocked": bool(blockers),
                    "warning": bool(warnings),
                    "blockers": list(blockers),
                    "warnings": list(warnings),
                    "blocker_count": len(blockers),
                    "warning_count": len(warnings),
                }
            total_blockers = sum(item.get("blocker_count", 0) for item in actions.values())
            total_warnings = sum(item.get("warning_count", 0) for item in actions.values())
            primary_action = "advance"
            for candidate in ("load", "advance", "dispense"):
                if actions.get(candidate, {}).get("blocked"):
                    primary_action = candidate
                    break
            return {
                "ok": total_blockers == 0,
                "batch_id": batch.get("batch_id", "") if isinstance(batch, dict) else "",
                "route_status": batch.get("route_status", "") if isinstance(batch, dict) else "",
                "summary": {
                    "blockers": total_blockers,
                    "warnings": total_warnings,
                    "primary_action": primary_action,
                    "checked_at": self.now_text(),
                },
                "actions": actions,
            }

    def persist_delivery_safety_self_test_result(self, result):
        path = getattr(self, "delivery_safety_self_test_file", "") or ""
        if not path:
            return
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp_path = path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as handle:
                json.dump(result, handle, ensure_ascii=False, indent=2)
            os.replace(tmp_path, path)
        except Exception as exc:
            try:
                self.get_logger().warning(f"\u4fdd\u5b58\u5b89\u5168\u95e8\u81ea\u6d4b\u7ed3\u679c\u5931\u8d25: {exc}")
            except Exception:
                pass

    def get_delivery_safety_self_test_result(self):
        path = getattr(self, "delivery_safety_self_test_file", "") or ""
        if not path or not os.path.isfile(path):
            return {"ok": True, "available": False, "result": None}
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            return {"ok": True, "available": True, "result": data}
        except Exception as exc:
            return {"ok": False, "available": False, "message": str(exc), "result": None}

    def run_delivery_batch_safety_self_test(self):
        with self.delivery_batch_lock:
            source = copy.deepcopy(self.delivery_batch)
        scenarios = []

        def run_case(name, action, mutator, expect_blocked=True):
            batch = copy.deepcopy(source)
            if mutator:
                mutator(batch)
            blockers, warnings = self.collect_delivery_batch_backend_blockers(
                batch, action, include_motion=False
            )
            blocked = bool(blockers)
            scenarios.append(
                {
                    "name": name,
                    "action": action,
                    "expected_blocked": expect_blocked,
                    "blocked": blocked,
                    "ok": blocked == expect_blocked,
                    "blockers": blockers,
                    "warnings": warnings,
                }
            )

        def set_unloaded(batch):
            batch["route_status"] = "WAITING_LOAD_CONFIRMATION"
            found_loaded = False
            for stop in batch.get("stops", []):
                for patient in stop.get("patients", []):
                    for medication in patient.get("medications", []):
                        medication["loaded"] = False
                        found_loaded = True
            if not found_loaded:
                batch.setdefault("summary", {})["all_loaded"] = False

        def set_review_required(batch):
            for stop in batch.get("stops", []):
                for patient in stop.get("patients", []):
                    patient["medication_review_required"] = True
                    patient["patient_status"] = "WAITING_MEDICATION_REVIEW"
                    return

        def set_stage_wrong_for_dispense(batch):
            batch["route_status"] = "READY_TO_DEPART"

        def set_stage_wrong_for_load(batch):
            batch["route_status"] = "WARD_HANDOVER"

        run_case("\u672a\u88c5\u836f\u963b\u65ad\u63a8\u8fdb", "advance", set_unloaded, True)
        run_case("\u5f85\u590d\u6838\u963b\u65ad\u63a8\u8fdb", "advance", set_review_required, True)
        run_case("\u9636\u6bb5\u9519\u8bef\u963b\u65ad\u4ea4\u4ed8", "dispense", set_stage_wrong_for_dispense, True)
        run_case("\u9636\u6bb5\u9519\u8bef\u963b\u65ad\u88c5\u836f", "load", set_stage_wrong_for_load, True)
        passed = sum(1 for item in scenarios if item.get("ok"))
        result = {
            "ok": passed == len(scenarios),
            "passed": passed,
            "total": len(scenarios),
            "scenarios": scenarios,
            "batch_id": source.get("batch_id", ""),
            "tested_at": self.now_text(),
            "message": f"\u5b89\u5168\u95e8\u81ea\u6d4b\u901a\u8fc7 {passed}/{len(scenarios)} \u9879",
        }
        self.persist_delivery_safety_self_test_result(result)
        return result


    def reject_delivery_batch_action_locked(self, batch, event, message, extra=None):
        try:
            self.append_batch_audit(batch, event, message, "fail", extra or {})
            self.update_batch_summary(batch)
        except Exception:
            pass
        return {"ok": False, "message": message, "batch": copy.deepcopy(batch)}

    def delivery_motion_blocker(self):
        if not hasattr(self, "get_chassis_status"):
            return ""
        try:
            chassis = self.get_chassis_status()
        except Exception:
            return ""
        if not isinstance(chassis, dict) or not chassis:
            return ""
        if not chassis.get("received"):
            return "ROS2/底盘状态未连接，禁止进入配送阶段"
        if chassis.get("emergency_stop") is True:
            return "急停已开启，禁止下发移动任务"
        battery = chassis.get("battery", chassis.get("battery_percent"))
        try:
            if battery is not None and float(battery) < 20.0:
                return "电量低于 20%，禁止新配送任务"
        except (TypeError, ValueError):
            pass
        cabinet_locked = chassis.get(
            "cabinet_locked", chassis.get("medicine_cabinet_locked")
        )
        if cabinet_locked is False:
            return "药舱未锁定，禁止进入配送阶段"
        return ""

    def current_scan_key(self, payload=None):
        payload = payload or {}
        product_code = str(payload.get("product_code") or "").strip()
        trace_id = str(payload.get("trace_id") or "").strip()
        if product_code or trace_id:
            return product_code, trace_id
        drug_info = self.get_drug_info()
        product_code = str(
            drug_info.get("label_product_code")
            or drug_info.get("stable_product_code")
            or drug_info.get("raw_code_text")
            or drug_info.get("code_text")
            or ""
        ).strip()
        trace_id = str(
            drug_info.get("label_trace_id")
            or drug_info.get("trace_code")
            or drug_info.get("stable_trace_code")
            or ""
        ).strip()
        if (product_code or trace_id) and self.is_scan_info_stale(drug_info):
            return "", ""
        return product_code, trace_id

    def is_scan_info_stale(self, drug_info):
        max_age = float(getattr(self, "scan_max_age_sec", 8.0) or 0.0)
        if max_age <= 0.0:
            return False
        age = drug_info.get("scan_age_sec")
        try:
            age_value = float(age)
        except (TypeError, ValueError):
            received_at = (
                drug_info.get("recognition_received_at")
                or drug_info.get("web_received_at")
            )
            try:
                age_value = time.time() - float(received_at)
            except (TypeError, ValueError):
                return False
        return age_value > max_age

    def batch_medication_matches(self, medication, product_code, trace_id):
        expected_product_code = str(medication.get("product_code") or "").strip()
        expected_trace_id = str(medication.get("trace_id") or "").strip()
        scanned_product_code = str(product_code or "").strip()
        scanned_trace_id = str(trace_id or "").strip()
        compared = []
        if scanned_product_code and expected_product_code:
            compared.append(scanned_product_code == expected_product_code)
        if scanned_trace_id and expected_trace_id:
            compared.append(scanned_trace_id == expected_trace_id)
        return bool(compared) and all(compared)

    def normalize_medicine_match_text(self, value):
        text = self.text_value(value)
        if not text:
            return ""
        text = re.sub(r"\s+", "", text)
        text = re.sub(r"[\u3000\uff0c,\u3002.\uff1a:;\uff1b\-_/\\|()\uff08\uff09\[\]{}]+", "", text)
        text = re.sub(r"\d+(?:mg|g|ml|mL|ML|\u03bcg|ug|IU|%)", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\d+(?:\u7247|\u7c92|\u888b|\u8d34|\u652f|\u74f6|\u76d2|\u677f|\u679a|\u5305|\u4e38)(?:\u88c5)?", "", text)
        text = re.sub(r"(?:\u53e3\u670d|\u5916\u7528|\u6bcf\u65e5|\u6bcf\u6b21|\u4e00\u65e5|\u4e00\u6b21|\u4e8c\u6b21|\u4e09\u6b21)", "", text)
        return text.strip().lower()

    def explain_medicine_name_similarity(self, observed, expected):
        observed_norm = self.normalize_medicine_match_text(observed)
        expected_norm = self.normalize_medicine_match_text(expected)
        observed_alias = self.medicine_alias_canonical(observed)
        expected_alias = self.medicine_alias_canonical(expected)
        if not observed_norm or not expected_norm:
            return 0.0, "empty_name", "\u836f\u540d\u4e3a\u7a7a\uff0c\u65e0\u6cd5\u6bd4\u5bf9"
        if observed_alias and expected_alias and observed_alias == expected_alias:
            if observed_norm == expected_norm:
                return 1.0, "exact", "\u836f\u540d\u5b8c\u5168\u4e00\u81f4"
            return 0.97, "alias", "\u547d\u4e2d\u836f\u54c1\u522b\u540d/\u901a\u7528\u540d\u6620\u5c04"
        if observed_norm == expected_norm:
            return 1.0, "exact", "\u836f\u540d\u5b8c\u5168\u4e00\u81f4"
        if expected_norm in observed_norm:
            score = min(0.98, 0.72 + len(expected_norm) / max(len(observed_norm), 1) * 0.24)
            return score, "expected_in_observed", "OCR \u6587\u672c\u5305\u542b\u6279\u6b21\u836f\u540d"
        if observed_norm in expected_norm and len(observed_norm) >= 2:
            score = min(0.94, 0.62 + len(observed_norm) / max(len(expected_norm), 1) * 0.25)
            return score, "observed_in_expected", "OCR \u836f\u540d\u662f\u6279\u6b21\u836f\u540d\u7684\u90e8\u5206\u5b57\u6bb5"
        observed_chars = set(observed_norm)
        expected_chars = set(expected_norm)
        overlap = len(observed_chars & expected_chars)
        union = len(observed_chars | expected_chars) or 1
        containment = overlap / max(min(len(observed_chars), len(expected_chars)), 1)
        jaccard = overlap / union
        score = max(jaccard, containment * 0.82)
        return score, "char_overlap", f"\u5b57\u7b26\u91cd\u5408\u5ea6 {score:.2f}"

    def medicine_name_similarity(self, observed, expected):
        score, _reason_code, _reason_text = self.explain_medicine_name_similarity(observed, expected)
        return score

    def batch_medication_available_for_mode(self, medication, mode):
        if medication.get("returned") or medication.get("exception"):
            return False
        if mode == "load" and medication.get("loaded"):
            return False
        if mode == "dispense" and medication.get("dispensed"):
            return False
        return True

    def build_name_match_explanation(self, observed_name, expected_name, score):
        _score, reason_code, reason_text = self.explain_medicine_name_similarity(observed_name, expected_name)
        return {
            "match_type": reason_code,
            "match_reason": reason_text,
            "observed_name": self.text_value(observed_name),
            "expected_name": self.text_value(expected_name),
            "score": round(float(score), 3),
        }

    def apply_scan_confidence_policy(self, response):
        source = self.text_value(response.get("medicine_match_source"))
        status = self.text_value(response.get("status"))
        risk = self.text_value(response.get("match_risk"), "UNKNOWN").upper()
        write_allowed = bool(response.get("write_allowed"))
        score = 0.0
        try:
            score = float(response.get("medicine_match_score") or 0.0)
        except (TypeError, ValueError):
            score = 0.0
        match_type = self.text_value(response.get("match_type"))
        mode = self.text_value(response.get("mode"), "load").lower()
        candidates = response.get("candidates") if isinstance(response.get("candidates"), list) else []
        candidate_count = len(candidates)

        confidence_level = "unknown"
        confidence_label = "\u672a\u5f00\u59cb\u5224\u5b9a"
        confidence_reason = "\u7b49\u5f85\u6761\u7801\u3001\u8ffd\u6eaf\u7801\u6216 OCR \u836f\u540d\u8bc6\u522b\u7ed3\u679c"
        recommended_action = "\u8bf7\u5148\u8bc6\u522b\u836f\u54c1\u5305\u88c5"
        can_commit = False
        needs_manual_review = True

        if source == "code" and write_allowed and candidate_count == 1:
            confidence_level = "high"
            confidence_label = "\u9ad8\u53ef\u4fe1\u00b7\u53ef\u5199\u5165"
            confidence_reason = "\u6761\u7801/\u8ffd\u6eaf\u7801\u552f\u4e00\u547d\u4e2d\u5f53\u524d\u6279\u6b21\u836f\u54c1"
            recommended_action = "\u53ef\u6309\u6d41\u7a0b\u5199\u5165\u88c5\u836f/\u4ea4\u4ed8\u8bb0\u5f55"
            can_commit = True
            needs_manual_review = False
        elif source == "code" and candidate_count > 1:
            confidence_level = "medium"
            confidence_label = "\u4e2d\u53ef\u4fe1\u00b7\u591a\u5019\u9009"
            confidence_reason = "\u6761\u7801/\u8ffd\u6eaf\u7801\u547d\u4e2d\u591a\u4e2a\u6279\u6b21\u5019\u9009"
            recommended_action = "\u8bf7\u4eba\u5de5\u6838\u5bf9\u5e8a\u53f7\u3001\u75c5\u4eba\u548c\u836f\u540d\u540e\u518d\u5904\u7406"
        elif source == "ocr_name" and write_allowed and candidate_count == 1 and score >= OCR_AUTO_LOAD_SCORE_THRESHOLD and mode == "load":
            confidence_level = "medium"
            confidence_label = f"OCR\u2265{OCR_AUTO_LOAD_SCORE_PERCENT}%\u00b7\u76f4\u63a5\u88c5\u836f"
            confidence_reason = f"OCR \u836f\u540d\u552f\u4e00\u547d\u4e2d\u5f53\u524d\u6279\u6b21\uff0c\u5339\u914d\u5206\u6570\u5927\u4e8e\u7b49\u4e8e {OCR_AUTO_LOAD_SCORE_PERCENT}%"
            recommended_action = "\u5df2\u6309\u514d\u4eba\u5de5\u590d\u6838\u7b56\u7565\u5141\u8bb8\u81ea\u52a8\u5199\u5165\u88c5\u836f\u8bb0\u5f55"
            can_commit = True
            needs_manual_review = False
        elif source == "ocr_name" and status == "CODE_NO_MATCH_NAME_MATCH":
            confidence_level = "low"
            confidence_label = "\u4f4e\u53ef\u4fe1\u00b7\u4ec5\u8f85\u52a9"
            confidence_reason = "\u6761\u7801/\u8ffd\u6eaf\u7801\u672a\u547d\u4e2d\u6279\u6b21\uff0c\u4ec5 OCR \u836f\u540d\u547d\u4e2d\u5019\u9009"
            recommended_action = "\u7981\u6b62\u76f4\u63a5\u5199\u5165\uff1b\u8bf7\u91cd\u626b\u6761\u7801\u6216\u7531\u836f\u5e08\u590d\u6838"
        elif source == "ocr_name" and candidate_count == 1 and score >= 0.95 and match_type in {"exact", "alias"}:
            confidence_level = "medium"
            confidence_label = "\u4e2d\u53ef\u4fe1\u00b7\u9700\u590d\u6838"
            confidence_reason = "OCR \u836f\u540d\u4e0e\u6279\u6b21\u836f\u540d\u9ad8\u76f8\u4f3c\uff0c\u4f46\u672a\u7531\u6761\u7801/\u8ffd\u6eaf\u7801\u786e\u8ba4"
            recommended_action = "\u53ef\u4f5c\u4e3a\u88c5\u836f\u53c2\u8003\uff1b\u5199\u5165\u524d\u5fc5\u987b\u626b\u7801\u6216\u4eba\u5de5\u590d\u6838"
        elif source == "ocr_name" and candidate_count > 0:
            confidence_level = "low"
            confidence_label = "\u4f4e\u53ef\u4fe1\u00b7\u4ec5\u5019\u9009"
            confidence_reason = "OCR \u836f\u540d\u5b58\u5728\u5019\u9009\uff0c\u4f46\u76f8\u4f3c\u5ea6\u6216\u552f\u4e00\u6027\u4e0d\u8db3"
            recommended_action = "\u8bf7\u8c03\u6574\u836f\u76d2\u4f4d\u7f6e\u3001\u91cd\u65b0 OCR \u6216\u626b\u6761\u7801"
        elif status in {"ALREADY_LOADED", "ALREADY_PROCESSED"}:
            confidence_level = "done"
            confidence_label = "\u5df2\u88c5\u836f\u00b7\u4e0d\u91cd\u590d\u5199\u5165"
            confidence_reason = "\u6761\u7801/\u8ffd\u6eaf\u7801\u547d\u4e2d\u5f53\u524d\u6279\u6b21\uff0c\u4f46\u8be5\u836f\u54c1\u5df2\u6709\u88c5\u836f\u8bb0\u5f55"
            recommended_action = "\u5df2\u88c5\u836f\uff0c\u8bf7\u79fb\u5f00\u5f53\u524d\u836f\u54c1\u540e\u7ee7\u7eed\u4e0b\u4e00\u4ef6"
            can_commit = False
            needs_manual_review = False
        elif status in {"NO_MATCH", "NAME_NO_MATCH"}:
            confidence_level = "none"
            confidence_label = "\u672a\u5339\u914d\u00b7\u4e0d\u53ef\u91c7\u7528"
            confidence_reason = "\u8bc6\u522b\u7ed3\u679c\u672a\u547d\u4e2d\u5f53\u524d\u914d\u9001\u6279\u6b21"
            recommended_action = "\u8bf7\u786e\u8ba4\u836f\u54c1\u662f\u5426\u5c5e\u4e8e\u5f53\u524d\u6279\u6b21\uff0c\u6216\u6539\u7528\u624b\u5de5\u590d\u6838"
        elif status in {"NO_CODE", "NO_CODE_OR_NAME"}:
            confidence_level = "pending"
            confidence_label = "\u5f85\u8bc6\u522b\u00b7\u8bc1\u636e\u4e0d\u8db3"
            confidence_reason = "\u5c1a\u672a\u83b7\u53d6\u8db3\u591f\u7684\u6761\u7801\u3001\u8ffd\u6eaf\u7801\u6216 OCR \u836f\u540d"
            recommended_action = "\u8bf7\u5c06\u6761\u7801\u6216\u836f\u540d\u653e\u5165\u8bc6\u522b\u6846"

        if risk == "HIGH" and confidence_level in {"medium", "high"} and source != "code" and not write_allowed:
            confidence_level = "low"
            confidence_label = "\u4f4e\u53ef\u4fe1\u00b7\u4ec5\u8f85\u52a9"

        response["recognition_confidence"] = confidence_level
        response["recognition_confidence_label"] = confidence_label
        response["recognition_confidence_reason"] = confidence_reason
        response["recommended_action"] = recommended_action
        response["can_commit"] = bool(can_commit and write_allowed)
        response["needs_manual_review"] = bool(needs_manual_review)
        return response

    def find_batch_medication_name_candidates(self, batch, medicine_name, mode, extra_names=None):
        names = []
        for value in [medicine_name] + list(extra_names or []):
            value = self.text_value(value)
            if value and value not in names:
                names.append(value)
        if not names:
            return []
        matches = []
        active_station = ""
        if mode == "dispense":
            try:
                active_index = int(batch.get("active_stop_index", -1))
            except (TypeError, ValueError):
                active_index = -1
            if 0 <= active_index < len(batch.get("stops", [])):
                active_station = self.text_value(batch["stops"][active_index].get("target_station"))
        for stop in batch.get("stops", []):
            if mode == "dispense" and active_station:
                if self.text_value(stop.get("target_station")) != active_station:
                    continue
            for patient in stop.get("patients", []):
                for medication in patient.get("medications", []):
                    if not self.batch_medication_available_for_mode(medication, mode):
                        continue
                    expected_name = self.text_value(medication.get("medicine_name"))
                    best_score = 0.0
                    best_observed = ""
                    for observed_name in names:
                        score = self.medicine_name_similarity(observed_name, expected_name)
                        if score > best_score:
                            best_score = score
                            best_observed = observed_name
                    if best_score >= 0.58:
                        matches.append((best_score, best_observed, stop, patient, medication))
        matches.sort(key=lambda item: item[0], reverse=True)
        return matches

    def find_ocr_commit_match(self, batch, medicine_name, mode, extra_names=None):
        matches = self.find_batch_medication_name_candidates(
            batch,
            medicine_name,
            mode,
            extra_names=extra_names,
        )
        if len(matches) != 1:
            return None, None, None, 0.0, ""
        score, observed_name, stop, patient, medication = matches[0]
        if float(score) < OCR_AUTO_LOAD_SCORE_THRESHOLD:
            return None, None, None, float(score), observed_name
        return stop, patient, medication, float(score), observed_name

    def find_batch_medication(self, batch, product_code, trace_id, mode):
        for stop in batch.get("stops", []):
            for patient in stop.get("patients", []):
                for medication in patient.get("medications", []):
                    if not self.batch_medication_matches(
                        medication, product_code, trace_id
                    ):
                        continue
                    if medication.get("returned") or medication.get("exception"):
                        continue
                    if mode == "load" and medication.get("loaded"):
                        continue
                    if mode == "dispense" and medication.get("dispensed"):
                        continue
                    return stop, patient, medication
        return None, None, None

    def serialize_scan_match(self, stop, patient, medication):
        return {
            "stop_id": self.text_value(stop.get("stop_id")),
            "target_station": self.text_value(stop.get("target_station")),
            "ward_name": self.text_value(
                stop.get("display_name")
                or patient.get("ward_name")
                or stop.get("target_station")
            ),
            "patient_id": self.text_value(patient.get("patient_id")),
            "patient_name": self.text_value(patient.get("patient_name")),
            "bed_no": self.text_value(patient.get("bed_no")),
            "medication_id": self.text_value(medication.get("id")),
            "medicine_name": self.text_value(medication.get("medicine_name")),
            "product_code": self.text_value(medication.get("product_code")),
            "trace_id": self.text_value(medication.get("trace_id")),
            "product_model": self.text_value(medication.get("product_model")),
            "loaded": bool(medication.get("loaded")),
            "dispensed": bool(medication.get("dispensed")),
            "returned": bool(medication.get("returned")),
            "exception": self.text_value(medication.get("exception")),
        }

    def find_batch_medication_candidates(self, batch, product_code, trace_id, mode, include_unavailable=False):
        matches = []
        active_station = ""
        if mode == "dispense":
            try:
                active_index = int(batch.get("active_stop_index", -1))
            except (TypeError, ValueError):
                active_index = -1
            if 0 <= active_index < len(batch.get("stops", [])):
                active_station = self.text_value(
                    batch["stops"][active_index].get("target_station")
                )
        for stop in batch.get("stops", []):
            if mode == "dispense" and active_station:
                if self.text_value(stop.get("target_station")) != active_station:
                    continue
            for patient in stop.get("patients", []):
                for medication in patient.get("medications", []):
                    if not self.batch_medication_matches(
                        medication, product_code, trace_id
                    ):
                        continue
                    if not include_unavailable:
                        if medication.get("returned") or medication.get("exception"):
                            continue
                        if mode == "load" and medication.get("loaded"):
                            continue
                        if mode == "dispense" and medication.get("dispensed"):
                            continue
                    matches.append((stop, patient, medication))
        return matches

    def preview_delivery_batch_scan(self, payload):
        payload = payload or {}
        mode = self.text_value(payload.get("mode"), "load").lower()
        if mode not in {"load", "dispense"}:
            mode = "load"
        product_code, trace_id = self.current_scan_key(payload)
        drug_info = self.get_drug_info()
        extracted_fields = drug_info.get("ocr_extracted_fields")
        if not isinstance(extracted_fields, dict):
            extracted_fields = {}
        ocr_candidates = extracted_fields.get("drug_name_candidates")
        if not isinstance(ocr_candidates, list):
            ocr_candidates = []
        ocr_age_raw = drug_info.get("ocr_age_sec")
        try:
            ocr_age_sec = float(ocr_age_raw)
        except (TypeError, ValueError):
            ocr_age_sec = None
        # OCR can be cached by the vision node. For automatic matching, stale OCR must not
        # keep representing a previous medicine after the operator swaps packages.
        ocr_fresh = ocr_age_sec is None or ocr_age_sec <= 15.0
        explicit_medicine_name = self.text_value(payload.get("medicine_name"))
        recognition_source = self.text_value(drug_info.get("recognition_source") or drug_info.get("source")).lower()
        recognition_channel = self.text_value(drug_info.get("recognition_channel")).lower()
        has_explicit_recognition = bool(
            recognition_channel
            or "ocr" in recognition_source
            or "barcode" in recognition_source
            or "qr" in recognition_source
            or "datamatrix" in recognition_source
            or product_code
            or trace_id
        )
        default_drug_name = drug_info.get("drug_name") if has_explicit_recognition else ""
        medicine_name = self.text_value(
            explicit_medicine_name
            or (drug_info.get("ocr_drug_name") if ocr_fresh else "")
            or (extracted_fields.get("drug_name") if ocr_fresh else "")
            or default_drug_name
        )
        if ocr_fresh:
            ocr_text = self.text_value(drug_info.get("ocr_text"))
            if ocr_text:
                for token in re.split(r"[\s,\uFF0C\u3002\uFF1B;\uFF1F?:\uFF1A/|]+", ocr_text):
                    token = self.text_value(token)
                    normalized = self.normalize_medicine_match_text(token)
                    if len(normalized) >= 2 and token not in ocr_candidates:
                        ocr_candidates.append(token)
                if not medicine_name:
                    medicine_name = ocr_text
        if not ocr_fresh and not explicit_medicine_name:
            ocr_candidates = []
        response = {
            "ok": False,
            "mode": mode,
            "product_code": product_code,
            "trace_id": trace_id,
            "medicine_name": medicine_name,
            "medicine_match_source": "",
            "medicine_match_score": 0.0,
            "match_risk": "UNKNOWN",
            "write_allowed": False,
            "safety_note": "",
            "match_type": "",
            "match_reason": "",
            "observed_name": "",
            "expected_name": "",
            "recognition_confidence": "unknown",
            "recognition_confidence_label": "",
            "recognition_confidence_reason": "",
            "recommended_action": "",
            "can_commit": False,
            "needs_manual_review": True,
            "medicine_name_candidates": [self.text_value(item) for item in ocr_candidates if self.text_value(item)][:5],
            "candidates": [],
            "status": "NO_MATCH",
            "message": "",
        }
        with self.delivery_batch_lock:
            batch = getattr(self, "delivery_batch", None)
            auto_batch_adopted = False
            if not isinstance(batch, dict) or not batch.get("batch_id"):
                batch, auto_batch_adopted = self.maybe_adopt_catalog_batch_for_scan_locked(product_code, trace_id)
                if not isinstance(batch, dict) or not batch.get("batch_id"):
                    response["status"] = "NO_BATCH"
                    response["message"] = "\u5f53\u524d\u6ca1\u6709\u53ef\u5339\u914d\u7684\u914d\u9001\u6279\u6b21"
                    return self.apply_scan_confidence_policy(response)
            if product_code or trace_id:
                matches = self.find_batch_medication_candidates(
                    batch, product_code, trace_id, mode
                )
                if not matches:
                    batch, auto_batch_adopted = self.maybe_adopt_catalog_batch_for_scan_locked(product_code, trace_id)
                    if isinstance(batch, dict):
                        matches = self.find_batch_medication_candidates(
                            batch, product_code, trace_id, mode
                        )
                response["auto_batch_adopted"] = bool(auto_batch_adopted)
                if not matches:
                    completed_matches = self.find_batch_medication_candidates(
                        batch, product_code, trace_id, mode, include_unavailable=True
                    )
                    if completed_matches:
                        response["candidates"] = [
                            self.serialize_scan_match(stop, patient, medication)
                            for stop, patient, medication in completed_matches[:8]
                        ]
                        response["ok"] = True
                        response["status"] = "ALREADY_LOADED" if mode == "load" else "ALREADY_PROCESSED"
                        response["medicine_match_source"] = "code"
                        response["match_risk"] = "LOW"
                        response["write_allowed"] = False
                        first = response["candidates"][0]
                        response["message"] = (
                            f"\u5f53\u524d\u836f\u54c1\u5df2\u88c5\u836f\uff1a{first.get('bed_no') or '-'} "
                            f"{first.get('patient_name') or '-'} / {first.get('medicine_name') or '-'}"
                        )
                        response["safety_note"] = "\u8be5\u836f\u54c1\u5df2\u6709\u88c5\u836f\u8bb0\u5f55\uff0c\u4e0d\u91cd\u590d\u5199\u5165"
                        return self.apply_scan_confidence_policy(response)
                response["candidates"] = [
                    self.serialize_scan_match(stop, patient, medication)
                    for stop, patient, medication in matches[:8]
                ]
                if matches:
                    response["ok"] = True
                    response["status"] = "MATCHED" if len(matches) == 1 else "MULTI_MATCH"
                    response["medicine_match_source"] = "code"
                    response["match_risk"] = "LOW" if len(matches) == 1 else "MEDIUM"
                    response["write_allowed"] = len(matches) == 1
                    response["safety_note"] = "\u6761\u7801/\u8ffd\u6eaf\u7801\u5df2\u5339\u914d\u5f53\u524d\u6279\u6b21" if len(matches) == 1 else "\u6761\u7801\u5339\u914d\u5230\u591a\u4e2a\u5019\u9009\uff0c\u9700\u4eba\u5de5\u786e\u8ba4"
                    first = response["candidates"][0]
                    action_text = "交付" if mode == "dispense" else "装药"
                    response["message"] = (
                        f"已匹配{action_text}药品：{first.get('bed_no') or '-'} "
                        f"{first.get('patient_name') or '-'} / {first.get('medicine_name') or '-'}"
                    )
                else:
                    name_matches = self.find_batch_medication_name_candidates(
                        batch,
                        medicine_name,
                        mode,
                        extra_names=response["medicine_name_candidates"],
                    ) if medicine_name else []
                    if name_matches:
                        response["status"] = "CODE_NO_MATCH_NAME_MATCH"
                        response["medicine_match_source"] = "ocr_name"
                        response["medicine_match_score"] = round(float(name_matches[0][0]), 3)
                        ocr_write_allowed = mode == "load" and len(name_matches) == 1 and float(name_matches[0][0]) >= OCR_AUTO_LOAD_SCORE_THRESHOLD
                        response["ok"] = bool(ocr_write_allowed)
                        response["match_risk"] = "MEDIUM" if len(name_matches) == 1 and float(name_matches[0][0]) >= OCR_AUTO_LOAD_SCORE_THRESHOLD else "HIGH"
                        response["write_allowed"] = bool(ocr_write_allowed)
                        response["safety_note"] = f"OCR \u836f\u540d\u552f\u4e00\u547d\u4e2d\u4e14\u2265{OCR_AUTO_LOAD_SCORE_PERCENT}%\uff0c\u5df2\u6309\u514d\u4eba\u5de5\u590d\u6838\u7b56\u7565\u5141\u8bb8\u76f4\u63a5\u88c5\u836f" if ocr_write_allowed else "\u6761\u7801/\u8ffd\u6eaf\u7801\u672a\u5339\u914d\u6279\u6b21\uff0cOCR \u836f\u540d\u4ec5\u4f5c\u5019\u9009\u63d0\u793a"
                        response["candidates"] = []
                        for score, observed_name, stop, patient, medication in name_matches[:8]:
                            item = self.serialize_scan_match(stop, patient, medication)
                            item["match_score"] = round(float(score), 3)
                            item["matched_ocr_name"] = observed_name
                            item.update(self.build_name_match_explanation(observed_name, medication.get("medicine_name"), score))
                            response["candidates"].append(item)
                        first = response["candidates"][0]
                        response["match_type"] = first.get("match_type", "")
                        response["match_reason"] = first.get("match_reason", "")
                        response["observed_name"] = first.get("observed_name", "")
                        response["expected_name"] = first.get("expected_name", "")
                        response["message"] = (
                            f"条码/追溯码未匹配批次，但 OCR 药名匹配到候选："
                            f"{first.get('bed_no') or '-'} {first.get('patient_name') or '-'} / "
                            f"{first.get('medicine_name') or '-'}，"
                            f"{'允许装药' if ocr_write_allowed else '需人工确认'}"
                        )
                    else:
                        response["status"] = "NO_MATCH"
                        scope_text = "病房" if mode == "dispense" else "批次"
                        response["message"] = (
                            f"未匹配当前{scope_text}药品："
                            f"{product_code or '-'} / {trace_id or '-'}"
                        )
                return self.apply_scan_confidence_policy(response)
            if not medicine_name:
                response["status"] = "NO_CODE_OR_NAME"
                response["message"] = "未获取条码/追溯码，也未从 OCR 提取到药名"
                return self.apply_scan_confidence_policy(response)
            name_matches = self.find_batch_medication_name_candidates(
                batch,
                medicine_name,
                mode,
                extra_names=response["medicine_name_candidates"],
            )
            response["candidates"] = []
            for score, observed_name, stop, patient, medication in name_matches[:8]:
                item = self.serialize_scan_match(stop, patient, medication)
                item["match_score"] = round(float(score), 3)
                item["matched_ocr_name"] = observed_name
                item.update(self.build_name_match_explanation(observed_name, medication.get("medicine_name"), score))
                response["candidates"].append(item)
            if name_matches:
                best_score, observed_name, stop, patient, medication = name_matches[0]
                ocr_write_allowed = mode == "load" and len(name_matches) == 1 and float(best_score) >= OCR_AUTO_LOAD_SCORE_THRESHOLD
                response["ok"] = bool(ocr_write_allowed)
                response["status"] = "NAME_MATCHED" if len(name_matches) == 1 else "NAME_MULTI_MATCH"
                response["medicine_match_source"] = "ocr_name"
                response["medicine_match_score"] = round(float(best_score), 3)
                response["match_risk"] = "MEDIUM" if len(name_matches) == 1 and float(best_score) >= OCR_AUTO_LOAD_SCORE_THRESHOLD else "HIGH"
                response["write_allowed"] = bool(ocr_write_allowed)
                response["safety_note"] = f"OCR \u836f\u540d\u552f\u4e00\u547d\u4e2d\u4e14\u2265{OCR_AUTO_LOAD_SCORE_PERCENT}%\uff0c\u5df2\u6309\u514d\u4eba\u5de5\u590d\u6838\u7b56\u7565\u5141\u8bb8\u76f4\u63a5\u88c5\u836f" if ocr_write_allowed else "OCR \u836f\u540d\u4ec5\u7528\u4e8e\u9884\u89c8\uff0c\u672a\u8fbe\u5230\u76f4\u63a5\u88c5\u836f\u6761\u4ef6"
                first = response["candidates"][0]
                response["match_type"] = first.get("match_type", "")
                response["match_reason"] = first.get("match_reason", "")
                response["observed_name"] = first.get("observed_name", "")
                response["expected_name"] = first.get("expected_name", "")
                if len(name_matches) == 1:
                    response["message"] = (
                        f"OCR 药名已匹配当前批次："
                        f"{first.get('bed_no') or '-'} {first.get('patient_name') or '-'} / "
                        f"{first.get('medicine_name') or '-'}，相似度 {response['medicine_match_score']:.2f}"
                    )
                else:
                    response["message"] = (
                        f"OCR 药名匹配到 {len(name_matches)} 个候选，需要人工确认"
                    )
            else:
                response["status"] = "NAME_NO_MATCH"
                response["match_risk"] = "HIGH"
                response["write_allowed"] = False
                response["safety_note"] = "OCR \u836f\u540d\u5339\u914d\u4ec5\u7528\u4e8e\u9884\u89c8\uff0c\u5199\u5165\u88c5\u836f/\u4ea4\u4ed8\u524d\u5efa\u8bae\u6761\u7801\u6216\u4eba\u5de5\u590d\u6838"
                response["message"] = (
                    f"OCR 药名未匹配当前批次：{medicine_name or '-'}"
                )
            return self.apply_scan_confidence_policy(response)

    def scan_load_delivery_batch(self, payload):
        payload = payload or {}
        product_code, trace_id = self.current_scan_key(payload)
        medicine_name = self.text_value(payload.get("medicine_name"))
        drug_info = self.get_drug_info()
        extracted_fields = drug_info.get("ocr_extracted_fields")
        ocr_extra_names = []
        if isinstance(extracted_fields, dict):
            candidates = extracted_fields.get("drug_name_candidates")
            if isinstance(candidates, list):
                ocr_extra_names.extend([self.text_value(item) for item in candidates if self.text_value(item)])
            extracted_name = self.text_value(extracted_fields.get("drug_name"))
            if extracted_name:
                ocr_extra_names.insert(0, extracted_name)
        ocr_drug_name = self.text_value(drug_info.get("ocr_drug_name"))
        if ocr_drug_name:
            ocr_extra_names.insert(0, ocr_drug_name)
        with self.delivery_batch_lock:
            batch = self.delivery_batch
            if not self.find_batch_medication_candidates(batch, product_code, trace_id, "load"):
                batch, _auto_batch_adopted = self.maybe_adopt_catalog_batch_for_scan_locked(product_code, trace_id)
            blockers, _warnings = self.collect_delivery_batch_backend_blockers(batch, "load")
            if blockers:
                message = '；'.join(blockers)
                return self.reject_delivery_batch_action_locked(
                    batch,
                    "load_scan_blocked",
                    message,
                    {
                        "scanned_product_code": product_code,
                        "scanned_trace_id": trace_id,
                    },
                )
            stop, patient, medication = self.find_batch_medication(
                batch, product_code, trace_id, "load"
            )
            if medication is None:
                ocr_stop, ocr_patient, ocr_medication, ocr_score, ocr_observed = self.find_ocr_commit_match(
                    batch,
                    medicine_name,
                    "load",
                    extra_names=ocr_extra_names,
                )
                if ocr_medication is not None:
                    stop, patient, medication = ocr_stop, ocr_patient, ocr_medication
                    self.append_batch_audit(
                        batch,
                        "load_scan",
                        f"OCR\u76f4\u63a5\u88c5\u836f\u547d\u4e2d\uff1a{patient.get('bed_no') or '-'} {patient.get('patient_name') or '-'} / {medication.get('medicine_name') or '-'}\uff0c\u5206\u6570 {float(ocr_score):.2f}",
                        "ok",
                        {
                            "patient_id": patient.get("patient_id", ""),
                            "medication_id": medication.get("id", ""),
                            "scanned_product_code": product_code,
                            "scanned_trace_id": trace_id,
                            "ocr_medicine_name": medicine_name,
                            "ocr_observed_name": ocr_observed,
                            "ocr_match_score": round(float(ocr_score), 3),
                            "commit_policy": "ocr_name_ge_0.50_auto_load",
                        },
                    )
                else:
                    message = (
                        f"\u88c5\u836f\u626b\u7801\u672a\u5339\u914d\u5f53\u524d\u6279\u6b21\uff1a{product_code or '-'} / {trace_id or '-'}"
                    )
                    self.append_batch_audit(
                    batch,
                    "load_scan",
                    message,
                        "fail",
                        {
                            "scanned_product_code": product_code,
                            "scanned_trace_id": trace_id,
                            "ocr_medicine_name": medicine_name,
                            "ocr_observed_name": ocr_observed,
                            "ocr_match_score": round(float(ocr_score), 3),
                            "commit_policy": "ocr_name_ge_0.50_required",
                        },
                    )
                    self.update_batch_summary(batch)
                    self.save_scan_to_db_locked(
                        batch,
                        "load",
                        product_code,
                        trace_id,
                        "mismatch",
                        notes=message,
                    )
                    return {"ok": False, "message": message, "batch": copy.deepcopy(batch)}
            if medication is None:
                message = (
                    f"装药扫码未匹配当前批次：{product_code or '-'} / {trace_id or '-'}"
                )
                self.append_batch_audit(
                    batch,
                    "load_scan",
                    message,
                    "fail",
                    {
                        "scanned_product_code": product_code,
                        "scanned_trace_id": trace_id,
                    },
                )
                self.update_batch_summary(batch)
                self.save_scan_to_db_locked(
                    batch,
                    "load",
                    product_code,
                    trace_id,
                    "mismatch",
                    notes=message,
                )
                return {"ok": False, "message": message, "batch": copy.deepcopy(batch)}
            now = self.now_text()
            medication["loaded"] = True
            medication["loaded_at"] = now
            patient["patient_status"] = "LOADED"
            message = f"装药确认：{patient.get('bed_no')} {patient.get('patient_name')} / {medication.get('medicine_name')}"
            self.append_batch_audit(
                batch,
                "load_scan",
                message,
                "ok",
                {
                    "patient_id": patient.get("patient_id", ""),
                    "medication_id": medication.get("id", ""),
                    "scanned_product_code": product_code,
                    "scanned_trace_id": trace_id,
                },
            )
            self.update_batch_summary(batch)
            self.save_scan_to_db_locked(
                batch,
                "load",
                product_code,
                trace_id,
                "success",
                stop=stop,
                patient=patient,
                medication=medication,
                notes=message,
            )
            return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}

    def scan_dispense_delivery_batch(self, payload):
        product_code, trace_id = self.current_scan_key(payload)
        with self.delivery_batch_lock:
            batch = self.delivery_batch
            blockers, _warnings = self.collect_delivery_batch_backend_blockers(batch, "dispense")
            if blockers:
                message = '；'.join(blockers)
                return self.reject_delivery_batch_action_locked(
                    batch,
                    "dispense_scan_blocked",
                    message,
                    {
                        "scanned_product_code": product_code,
                        "scanned_trace_id": trace_id,
                    },
                )
            active_index = int(batch.get("active_stop_index", -1))
            active_station = ""
            if 0 <= active_index < len(batch.get("stops", [])):
                active_station = batch["stops"][active_index].get("target_station", "")
            stop, patient, medication = self.find_batch_medication(
                batch, product_code, trace_id, "dispense"
            )
            if medication is None or (
                active_station and stop.get("target_station") != active_station
            ):
                message = (
                    f"交付扫码未匹配当前病房：{product_code or '-'} / {trace_id or '-'}"
                )
                self.append_batch_audit(
                    batch,
                    "dispense_scan",
                    message,
                    "fail",
                    {
                        "scanned_product_code": product_code,
                        "scanned_trace_id": trace_id,
                    },
                )
                self.update_batch_summary(batch)
                self.save_scan_to_db_locked(
                    batch,
                    "dispense",
                    product_code,
                    trace_id,
                    "mismatch",
                    stop=stop,
                    patient=patient,
                    medication=medication,
                    notes=message,
                )
                return {"ok": False, "message": message, "batch": copy.deepcopy(batch)}
            if patient.get("medication_review_required") or medication.get("review_required"):
                message = f"\u7528\u836f\u590d\u6838\u672a\u5b8c\u6210\uff0c\u6682\u4e0d\u80fd\u4ea4\u4ed8\uff1a{patient.get('bed_no')} {patient.get('patient_name')} / {medication.get('medicine_name')}"
                self.append_batch_audit(
                    batch,
                    "dispense_scan",
                    message,
                    "fail",
                    {
                        "patient_id": patient.get("patient_id", ""),
                        "medication_id": medication.get("id", ""),
                    },
                )
                self.update_batch_summary(batch)
                return {"ok": False, "message": message, "batch": copy.deepcopy(batch)}
            if not medication.get("loaded"):
                message = (
                    f"药品尚未装药确认，不能交付：{medication.get('medicine_name')}"
                )
                self.append_batch_audit(
                    batch,
                    "dispense_scan",
                    message,
                    "fail",
                    {
                        "patient_id": patient.get("patient_id", ""),
                        "medication_id": medication.get("id", ""),
                    },
                )
                self.update_batch_summary(batch)
                self.save_scan_to_db_locked(
                    batch,
                    "dispense",
                    product_code,
                    trace_id,
                    "error",
                    stop=stop,
                    patient=patient,
                    medication=medication,
                    notes=message,
                )
                return {"ok": False, "message": message, "batch": copy.deepcopy(batch)}
            task_id = stop.get("task_manager_task_id") or medication.get(
                "task_manager_task_id", ""
            )
            task_confirmed_at = ""
            if task_id:
                task_state = self.get_state()
                if task_state.get("task_id") != task_id:
                    message = f"任务管理状态不匹配，不能交付：期望 {task_id}，当前 {task_state.get('task_id') or '-'}"
                    self.append_batch_audit(
                        batch,
                        "dispense_scan",
                        message,
                        "fail",
                        {
                            "patient_id": patient.get("patient_id", ""),
                            "medication_id": medication.get("id", ""),
                            "task_manager_task_id": task_id,
                        },
                    )
                    self.update_batch_summary(batch)
                    self.save_scan_to_db_locked(
                        batch,
                        "dispense",
                        product_code,
                        trace_id,
                        "error",
                        stop=stop,
                        patient=patient,
                        medication=medication,
                        notes=message,
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                if task_state.get("state") != "WAITING_DISPENSE_CONFIRMATION":
                    message = f"任务管理尚未到达病房取药确认阶段：{task_state.get('state') or '-'}"
                    self.append_batch_audit(
                        batch,
                        "dispense_scan",
                        message,
                        "fail",
                        {
                            "patient_id": patient.get("patient_id", ""),
                            "medication_id": medication.get("id", ""),
                            "task_manager_task_id": task_id,
                        },
                    )
                    self.update_batch_summary(batch)
                    self.save_scan_to_db_locked(
                        batch,
                        "dispense",
                        product_code,
                        trace_id,
                        "error",
                        stop=stop,
                        patient=patient,
                        medication=medication,
                        notes=message,
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                verify_response = self.verify_delivery_task(
                    {
                        "task_id": task_id,
                        "product_code": product_code,
                        "trace_id": trace_id,
                        "stage": "dispense",
                    }
                )
                if not verify_response.get("verified"):
                    message = (
                        f"任务管理交付确认失败：{verify_response.get('message', '')}"
                    )
                    self.append_batch_audit(
                        batch,
                        "dispense_scan",
                        message,
                        "fail",
                        {
                            "patient_id": patient.get("patient_id", ""),
                            "medication_id": medication.get("id", ""),
                            "task_manager_task_id": task_id,
                            "scanned_product_code": product_code,
                            "scanned_trace_id": trace_id,
                        },
                    )
                    self.update_batch_summary(batch)
                    self.save_scan_to_db_locked(
                        batch,
                        "dispense",
                        product_code,
                        trace_id,
                        "error",
                        stop=stop,
                        patient=patient,
                        medication=medication,
                        notes=message,
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                task_confirmed_at = verify_response.get("confirmed_at", "")
                medication["task_manager_confirmed_at"] = task_confirmed_at
                medication["task_manager_task_state"] = verify_response.get(
                    "task_state", ""
                )
            now = task_confirmed_at or self.now_text()
            medication["dispensed"] = True
            medication["dispensed_at"] = now
            message = f"交付确认：{stop.get('display_name')} {patient.get('bed_no')} {patient.get('patient_name')} / {medication.get('medicine_name')}"
            self.append_batch_audit(
                batch,
                "dispense_scan",
                message,
                "ok",
                {
                    "patient_id": patient.get("patient_id", ""),
                    "medication_id": medication.get("id", ""),
                    "scanned_product_code": product_code,
                    "scanned_trace_id": trace_id,
                },
            )
            self.update_batch_summary(batch)
            self.save_scan_to_db_locked(
                batch,
                "dispense",
                product_code,
                trace_id,
                "success",
                stop=stop,
                patient=patient,
                medication=medication,
                notes=message,
            )
            if stop.get("medication_total_count") and stop.get(
                "medication_done_count"
            ) >= stop.get("medication_total_count"):
                stop["stop_status"] = "COMPLETED"
                stop["completed_time"] = now
                batch["route_status"] = "WARD_COMPLETED"
                self.append_batch_audit(
                    batch,
                    "ward_completed",
                    f"{stop.get('display_name')} 已全部交付",
                    "ok",
                )
            return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}

    def find_batch_patient_by_bed(self, batch, bed_no):
        bed = str(bed_no or "").strip()
        if not bed:
            return None, None
        for stop in batch.get("stops", []):
            for patient in stop.get("patients", []):
                if str(patient.get("bed_no") or "").strip() == bed:
                    return stop, patient
        return None, None

    def record_patient_receipt_in_batch(self, delivery_id, bed, status, reason=""):
        bed_no = str(bed or "").strip()
        status = str(status or "").strip()
        reason = str(reason or "").strip()
        with self.delivery_batch_lock:
            batch = self.delivery_batch
            stop, patient = self.find_batch_patient_by_bed(batch, bed_no)
            if patient is None:
                return {
                    "ok": False,
                    "message": f"当前配送批次未找到床位：{bed_no or '-'}",
                    "batch": copy.deepcopy(batch),
                }
            now = self.now_text()
            medications = patient.get("medications", [])
            affected = 0
            if status == "confirmed":
                for item in medications:
                    if item.get("dispensed") or item.get("returned") or item.get("exception"):
                        continue
                    item["dispensed"] = True
                    item["dispensed_at"] = now
                    item["patient_signed"] = True
                    item["patient_signed_at"] = now
                    item["patient_signed_delivery_id"] = str(delivery_id or "")
                    affected += 1
                patient["patient_status"] = "PATIENT_SIGNED"
                patient["patient_signed_at"] = now
                message = (
                    f"患者本人签收：{patient.get('bed_no')} {patient.get('patient_name')}，"
                    f"确认 {affected} 项药品"
                )
                self.append_batch_audit(
                    batch,
                    "patient_signed",
                    message,
                    "ok",
                    {
                        "patient_id": patient.get("patient_id", ""),
                        "bed_no": patient.get("bed_no", ""),
                        "delivery_id": str(delivery_id or ""),
                        "affected_medication_count": affected,
                    },
                )
            elif status == "rejected":
                for item in medications:
                    if item.get("dispensed") or item.get("returned") or item.get("exception"):
                        continue
                    item["exception"] = "patient_rejected"
                    item["exception_at"] = now
                    item["exception_reason"] = reason or "患者反馈药品有疑问"
                    item["exception_resolved_at"] = ""
                    item["exception_resolved_reason"] = ""
                    item["exception_resolution_action"] = ""
                    item["manual_reviewed"] = False
                    item["manual_reviewed_at"] = ""
                    item["manual_review_result"] = ""
                    affected += 1
                patient["patient_status"] = "PATIENT_REJECTED"
                patient["patient_rejected_at"] = now
                patient["patient_rejected_reason"] = reason
                message = (
                    f"患者反馈问题：{patient.get('bed_no')} {patient.get('patient_name')}，"
                    f"{reason or '未填写原因'}"
                )
                self.append_batch_audit(
                    batch,
                    "patient_rejected",
                    message,
                    "warn",
                    {
                        "patient_id": patient.get("patient_id", ""),
                        "bed_no": patient.get("bed_no", ""),
                        "delivery_id": str(delivery_id or ""),
                        "affected_medication_count": affected,
                        "reason": reason,
                    },
                )
                self.save_exception_to_db_locked(
                    batch,
                    "patient_rejected",
                    reason or message,
                    stop=stop,
                    patient=patient,
                )
            else:
                return {
                    "ok": False,
                    "message": f"不支持的患者签收状态：{status or '-'}",
                    "batch": copy.deepcopy(batch),
                }
            self.update_batch_summary(batch)
            self.mark_active_stop_completed_if_ready(batch, stop)
            self.save_delivery_batch_state_locked(batch)
            self.save_batch_to_db_locked(batch)
            return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}
    def reset_medication_review_demo_scenario(self, payload=None):
        payload = payload or {}
        with self.delivery_batch_lock:
            batch = self.create_demo_delivery_batch()
            operator_id = self.text_value(payload.get("operator_id"), "web_operator")
            batch["operator_id"] = operator_id
            message = (
                "\u5df2\u91cd\u7f6e\u590d\u6838\u6f14\u793a\u6279\u6b21\uff1a"
                f"{batch.get('batch_id') or '-'}\uff0c\u53ef\u91cd\u65b0\u6f14\u793a\u75c5\u4eba\u7528\u836f\u590d\u6838\u3002"
            )
            self.append_batch_audit(
                batch,
                "demo_review_reset",
                message,
                "ok",
                {"source": "demo_review", "operator_id": operator_id},
            )
            self.update_batch_summary(batch)
            self.delivery_batch = batch
            self.save_delivery_batch_state_locked(batch)
            self.save_batch_to_db_locked(batch)
            return {
                "ok": True,
                "message": message,
                "batch": copy.deepcopy(batch),
            }

    def create_medication_review_demo_scenario(self, payload=None):
        payload = payload or {}
        requested_bed = str(payload.get("bed") or payload.get("bed_no") or "").strip()
        requested_patient_id = str(payload.get("patient_id") or "").strip()
        reason = str(payload.get("reason") or "").strip() or "\u6f14\u793a\uff1a\u75c5\u4eba\u53cd\u9988\u836f\u54c1\u8bf4\u660e\u6216\u4e2a\u4eba\u4fe1\u606f\u53ef\u80fd\u6709\u8bef\uff0c\u5f85\u62a4\u58eb\u590d\u6838"
        with self.delivery_batch_lock:
            batch = self.delivery_batch
            stop = patient = None
            if requested_patient_id:
                stop, patient, _ = self.find_batch_item_by_id(batch, requested_patient_id, "")
            if patient is None and requested_bed:
                stop, patient = self.find_batch_patient_by_bed(batch, requested_bed)
            if patient is None:
                for candidate_stop in batch.get("stops", []):
                    for candidate_patient in candidate_stop.get("patients", []):
                        available = [
                            item
                            for item in candidate_patient.get("medications", [])
                            if not (item.get("dispensed") or item.get("returned") or item.get("exception"))
                        ]
                        if available:
                            stop = candidate_stop
                            patient = candidate_patient
                            break
                    if patient is not None:
                        break
            created_demo_batch = False
            if patient is None and bool(payload.get("auto_create_demo_batch")):
                batch = self.create_demo_delivery_batch()
                self.delivery_batch = batch
                created_demo_batch = True
                for candidate_stop in batch.get("stops", []):
                    for candidate_patient in candidate_stop.get("patients", []):
                        available = [
                            item
                            for item in candidate_patient.get("medications", [])
                            if not (item.get("dispensed") or item.get("returned") or item.get("exception"))
                        ]
                        if available:
                            stop = candidate_stop
                            patient = candidate_patient
                            break
                    if patient is not None:
                        break
            if patient is None:
                return {
                    "ok": False,
                    "message": "\u5f53\u524d\u6279\u6b21\u6ca1\u6709\u53ef\u7528\u4e8e\u6f14\u793a\u7684\u75c5\u4eba\uff1a\u8bf7\u5148\u5bfc\u5165\u6216\u65b0\u5efa\u914d\u9001\u6279\u6b21",
                    "batch": copy.deepcopy(batch),
                }
            now = self.now_text()
            affected = 0
            patient["patient_status"] = "WAITING_MEDICATION_REVIEW"
            patient["medication_review_required"] = True
            patient["medication_review_reason"] = reason
            patient["medication_review_source"] = "demo_review"
            patient["medication_review_delivery_id"] = str(payload.get("delivery_id") or "")
            patient["medication_review_at"] = now
            patient["medication_review_resolved_at"] = ""
            patient["medication_review_resolution"] = ""
            patient["medication_review_resolution_reason"] = ""
            for item in patient.get("medications", []):
                if item.get("dispensed") or item.get("returned") or item.get("exception"):
                    continue
                item["review_required"] = True
                item["review_reason"] = reason
                item["review_required_at"] = now
                item["review_resolved_at"] = ""
                item["review_resolution"] = ""
                affected += 1
            if affected <= 0:
                return {
                    "ok": False,
                    "message": f"\u75c5\u4eba\u6ca1\u6709\u53ef\u8fdb\u5165\u7528\u836f\u590d\u6838\u7684\u672a\u4ea4\u4ed8\u836f\u54c1\uff1a{patient.get('bed_no') or '-'} {patient.get('patient_name') or '-'}",
                    "batch": copy.deepcopy(batch),
                }
            try:
                self.clear_status_override(patient.get("bed_no", ""))
            except Exception:
                pass
            prefix = "\u5df2\u65b0\u5efa\u6f14\u793a\u6279\u6b21\u5e76\u751f\u6210\u7528\u836f\u590d\u6838\u573a\u666f\uff1a" if created_demo_batch else "\u5df2\u751f\u6210\u7528\u836f\u590d\u6838\u6f14\u793a\u573a\u666f\uff1a"
            message = (
                f"{prefix}"
                f"{patient.get('bed_no') or '-'} {patient.get('patient_name') or '-'}\uff0c\u5f85\u590d\u6838 {affected} \u9879\u836f\u54c1"
            )
            self.append_batch_audit(
                batch,
                "patient_medication_review_required",
                message,
                "warn",
                {
                    "patient_id": patient.get("patient_id", ""),
                    "bed_no": patient.get("bed_no", ""),
                    "patient_name": patient.get("patient_name", ""),
                    "affected_medication_count": affected,
                    "reason": reason,
                    "source": "demo_review",
                },
            )
            self.update_batch_summary(batch)
            self.save_delivery_batch_state_locked(batch)
            self.save_batch_to_db_locked(batch)
            return {
                "ok": True,
                "message": message,
                "created_demo_batch": created_demo_batch,
                "patient": {
                    "patient_id": patient.get("patient_id", ""),
                    "bed_no": patient.get("bed_no", ""),
                    "patient_name": patient.get("patient_name", ""),
                    "affected_medication_count": affected,
                },
                "batch": copy.deepcopy(batch),
            }

    def mark_patient_medication_review_required(self, bed, delivery_id="", reason="", source=""):
        bed_no = str(bed or "").strip()
        reason = str(reason or "").strip() or "\u75c5\u4eba\u53cd\u9988\u7528\u836f\u6216\u4e2a\u4eba\u4fe1\u606f\u53ef\u80fd\u6709\u8bef"
        with self.delivery_batch_lock:
            batch = self.delivery_batch
            stop, patient = self.find_batch_patient_by_bed(batch, bed_no)
            if patient is None:
                return {
                    "ok": False,
                    "message": f"\u5f53\u524d\u914d\u9001\u6279\u6b21\u672a\u627e\u5230\u5e8a\u4f4d\uff1a{bed_no or '-'}",
                    "batch": copy.deepcopy(batch),
                }
            now = self.now_text()
            patient["patient_status"] = "WAITING_MEDICATION_REVIEW"
            patient["medication_review_required"] = True
            patient["medication_review_reason"] = reason
            patient["medication_review_source"] = str(source or "patient_feedback")
            patient["medication_review_delivery_id"] = str(delivery_id or "")
            patient["medication_review_at"] = now
            for item in patient.get("medications", []):
                if item.get("dispensed") or item.get("returned") or item.get("exception"):
                    continue
                item["review_required"] = True
                item["review_reason"] = reason
                item["review_required_at"] = now
            message = (
                f"\u75c5\u4eba\u53cd\u9988\u5f85\u7528\u836f\u590d\u6838\uff1a"
                f"{patient.get('bed_no')} {patient.get('patient_name')}\uff0c{reason}"
            )
            self.append_batch_audit(
                batch,
                "patient_medication_review_required",
                message,
                "warn",
                {
                    "patient_id": patient.get("patient_id", ""),
                    "bed_no": patient.get("bed_no", ""),
                    "patient_name": patient.get("patient_name", ""),
                    "delivery_id": str(delivery_id or ""),
                    "reason": reason,
                },
            )
            self.update_batch_summary(batch)
            self.save_delivery_batch_state_locked(batch)
            self.save_batch_to_db_locked(batch)
            return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}

    def resolve_patient_medication_review(self, payload):
        payload = payload or {}
        patient_id = str(payload.get("patient_id") or "").strip()
        bed_no = str(payload.get("bed_no") or payload.get("bed") or "").strip()
        action = str(payload.get("action") or "continue").strip()
        reason = str(payload.get("reason") or "").strip()
        if action not in {"continue", "return"}:
            return {"ok": False, "message": "\u4e0d\u652f\u6301\u7684\u590d\u6838\u5904\u7406\u52a8\u4f5c"}
        with self.delivery_batch_lock:
            batch = self.delivery_batch
            stop = patient = None
            if patient_id:
                stop, patient, _ = self.find_batch_item_by_id(batch, patient_id, "")
            if patient is None and bed_no:
                stop, patient = self.find_batch_patient_by_bed(batch, bed_no)
            if patient is None:
                return {
                    "ok": False,
                    "message": f"\u672a\u627e\u5230\u75c5\u4eba\uff1a{patient_id or bed_no or '-'}",
                    "batch": copy.deepcopy(batch),
                }
            now = self.now_text()
            old_reason = patient.get("medication_review_reason") or reason
            patient["medication_review_required"] = False
            patient["medication_review_resolved_at"] = now
            patient["medication_review_resolution"] = action
            patient["medication_review_resolution_reason"] = reason or (
                "\u62a4\u58eb\u590d\u6838\u901a\u8fc7" if action == "continue" else "\u590d\u6838\u540e\u9000\u56de\u836f\u623f"
            )
            affected = 0
            if action == "continue":
                for item in patient.get("medications", []):
                    if item.get("review_required"):
                        item["review_required"] = False
                        item["review_resolved_at"] = now
                        item["review_resolution"] = "continue"
                        affected += 1
                if any(
                    item.get("loaded")
                    and not (item.get("dispensed") or item.get("returned") or item.get("exception"))
                    for item in patient.get("medications", [])
                ):
                    patient["patient_status"] = "LOADED"
                elif patient.get("patient_status") == "WAITING_MEDICATION_REVIEW":
                    patient["patient_status"] = "WAITING_LOAD_CONFIRMATION"
                message = (
                    f"\u7528\u836f\u590d\u6838\u901a\u8fc7\uff0c\u53ef\u7ee7\u7eed\u914d\u9001\uff1a"
                    f"{patient.get('bed_no')} {patient.get('patient_name')}"
                )
                event = "patient_medication_review_continue"
                result = "ok"
                try:
                    self.clear_status_override(patient.get("bed_no", ""))
                except Exception:
                    pass
            else:
                for item in patient.get("medications", []):
                    if item.get("dispensed") or item.get("returned"):
                        continue
                    item["returned"] = True
                    item["returned_at"] = now
                    item["return_reason"] = reason or old_reason or "\u75c5\u4eba\u53cd\u9988\u5f85\u590d\u6838\uff0c\u9000\u56de\u836f\u623f"
                    item["review_required"] = False
                    item["review_resolved_at"] = now
                    item["review_resolution"] = "return"
                    affected += 1
                patient["patient_status"] = "MEDICATION_RETURNED_FOR_REVIEW"
                message = (
                    f"\u7528\u836f\u590d\u6838\u9000\u56de\u836f\u623f\uff1a"
                    f"{patient.get('bed_no')} {patient.get('patient_name')}\uff0c"
                    f"\u5f71\u54cd {affected} \u9879\u836f\u54c1"
                )
                event = "patient_medication_review_return"
                result = "warn"
            self.append_batch_audit(
                batch,
                event,
                message,
                result,
                {
                    "patient_id": patient.get("patient_id", ""),
                    "bed_no": patient.get("bed_no", ""),
                    "patient_name": patient.get("patient_name", ""),
                    "affected_medication_count": affected,
                    "reason": reason or old_reason or "",
                },
            )
            self.update_batch_summary(batch)
            self.mark_active_stop_completed_if_ready(batch, stop)
            self.save_delivery_batch_state_locked(batch)
            self.save_batch_to_db_locked(batch)
            return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}

    def mark_delivery_batch_exception(self, payload):
        action = str(payload.get("action") or "").strip()
        patient_id = str(payload.get("patient_id") or "").strip()
        medication_id = str(payload.get("medication_id") or "").strip()
        reason = str(payload.get("reason") or "").strip()
        with self.delivery_batch_lock:
            batch = self.delivery_batch
            stop, patient, medication = self.find_batch_item_by_id(
                batch, patient_id, medication_id
            )
            if patient is None:
                message = f"未找到病人：{patient_id or '-'}"
                self.append_batch_audit(
                    batch, "exception", message, "fail", {"patient_id": patient_id}
                )
                return {"ok": False, "message": message, "batch": copy.deepcopy(batch)}
            now = self.now_text()
            if action == "patient_absent":
                affected = 0
                for item in patient.get("medications", []):
                    if (
                        item.get("dispensed")
                        or item.get("returned")
                        or item.get("exception")
                    ):
                        continue
                    item["exception"] = "patient_absent"
                    item["exception_at"] = now
                    item["exception_reason"] = reason or "病人不在，暂不交付"
                    item["exception_resolved_at"] = ""
                    item["exception_resolved_reason"] = ""
                    item["exception_resolution_action"] = ""
                    item["manual_reviewed"] = False
                    item["manual_reviewed_at"] = ""
                    item["manual_review_result"] = ""
                    affected += 1
                patient["patient_status"] = "PATIENT_ABSENT"
                message = f"已标记病人不在：{patient.get('bed_no')} {patient.get('patient_name')}，影响 {affected} 项药品"
                self.append_batch_audit(
                    batch,
                    "patient_absent",
                    message,
                    "warn",
                    {
                        "patient_id": patient.get("patient_id", ""),
                        "affected_medication_count": affected,
                    },
                )
                self.save_exception_to_db_locked(
                    batch,
                    "patient_absent",
                    reason or message,
                    stop=stop,
                    patient=patient,
                )
                self.update_batch_summary(batch)
                self.mark_active_stop_completed_if_ready(batch, stop)
                return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}
            if action in {"retry", "clear_exception"} and not medication_id:
                if batch.get("route_status") in {
                    "RETURNING_TO_PHARMACY",
                    "BATCH_COMPLETED",
                }:
                    message = "批次已离开病房或已完成，不能重新打开异常"
                    self.append_batch_audit(
                        batch,
                        action,
                        message,
                        "fail",
                        {"patient_id": patient.get("patient_id", "")},
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                if stop.get(
                    "stop_status"
                ) == "COMPLETED" and not self.reopen_active_stop_for_retry(batch, stop):
                    message = (
                        f"{stop.get('display_name')} 不是当前病房，不能重新打开异常"
                    )
                    self.append_batch_audit(
                        batch,
                        action,
                        message,
                        "fail",
                        {"patient_id": patient.get("patient_id", "")},
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                affected = 0
                for item in patient.get("medications", []):
                    if (
                        item.get("exception")
                        and not item.get("dispensed")
                        and not item.get("returned")
                    ):
                        self.clear_medication_exception_for_retry(
                            item,
                            now,
                            reason
                            or (
                                "稍后重试，重新进入交付流程"
                                if action == "retry"
                                else "异常解除，重新进入交付流程"
                            ),
                            action,
                        )
                        affected += 1
                if affected <= 0:
                    message = f"没有可重新处理的异常药品：{patient.get('bed_no')} {patient.get('patient_name')}"
                    self.append_batch_audit(
                        batch,
                        action,
                        message,
                        "fail",
                        {"patient_id": patient.get("patient_id", "")},
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                patient["patient_status"] = "LOADED"
                self.reopen_active_stop_for_retry(batch, stop)
                message = f"已重新打开病人异常：{patient.get('bed_no')} {patient.get('patient_name')}，{affected} 项药品可继续交付"
                self.append_batch_audit(
                    batch,
                    action,
                    message,
                    "ok",
                    {
                        "patient_id": patient.get("patient_id", ""),
                        "affected_medication_count": affected,
                    },
                )
                self.update_batch_summary(batch)
                return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}
            if action == "manual_review" and not medication_id:
                affected = 0
                for item in patient.get("medications", []):
                    if item.get("exception") or item.get("returned"):
                        self.mark_medication_manual_reviewed(
                            item, now, reason or "药师复核通过，已记录审计"
                        )
                        affected += 1
                if affected <= 0:
                    message = f"没有需要药师复核的异常药品：{patient.get('bed_no')} {patient.get('patient_name')}"
                    self.append_batch_audit(
                        batch,
                        "manual_review",
                        message,
                        "fail",
                        {"patient_id": patient.get("patient_id", "")},
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                message = f"药师复核确认：{patient.get('bed_no')} {patient.get('patient_name')}，已复核 {affected} 项药品"
                self.append_batch_audit(
                    batch,
                    "manual_review",
                    message,
                    "ok",
                    {
                        "patient_id": patient.get("patient_id", ""),
                        "affected_medication_count": affected,
                    },
                )
                self.save_exception_to_db_locked(
                    batch,
                    "manual_review",
                    reason or message,
                    stop=stop,
                    patient=patient,
                )
                self.update_batch_summary(batch)
                self.mark_active_stop_completed_if_ready(batch, stop)
                return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}
            if medication is None:
                message = f"未找到药品：{medication_id or '-'}"
                self.append_batch_audit(
                    batch,
                    "exception",
                    message,
                    "fail",
                    {
                        "patient_id": patient_id,
                        "medication_id": medication_id,
                    },
                )
                return {"ok": False, "message": message, "batch": copy.deepcopy(batch)}
            if action == "drug_exception":
                if medication.get("dispensed"):
                    message = (
                        f"药品已交付，不能标记异常：{medication.get('medicine_name')}"
                    )
                    self.append_batch_audit(
                        batch,
                        "drug_exception",
                        message,
                        "fail",
                        {
                            "patient_id": patient.get("patient_id", ""),
                            "medication_id": medication.get("id", ""),
                        },
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                medication["exception"] = "drug_exception"
                medication["exception_at"] = now
                medication["exception_reason"] = reason or "药品异常，转人工处理"
                medication["exception_resolved_at"] = ""
                medication["exception_resolved_reason"] = ""
                medication["exception_resolution_action"] = ""
                medication["manual_reviewed"] = False
                medication["manual_reviewed_at"] = ""
                medication["manual_review_result"] = ""
                message = f"已标记药品异常：{patient.get('bed_no')} {patient.get('patient_name')} / {medication.get('medicine_name')}"
                self.append_batch_audit(
                    batch,
                    "drug_exception",
                    message,
                    "warn",
                    {
                        "patient_id": patient.get("patient_id", ""),
                        "medication_id": medication.get("id", ""),
                    },
                )
                self.save_exception_to_db_locked(
                    batch,
                    "drug_exception",
                    reason or message,
                    stop=stop,
                    patient=patient,
                    medication=medication,
                )
                self.update_batch_summary(batch)
                self.mark_active_stop_completed_if_ready(batch, stop)
                return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}
            if action == "return":
                if medication.get("dispensed"):
                    message = f"药品已交付，不能回收：{medication.get('medicine_name')}"
                    self.append_batch_audit(
                        batch,
                        "return_medication",
                        message,
                        "fail",
                        {
                            "patient_id": patient.get("patient_id", ""),
                            "medication_id": medication.get("id", ""),
                        },
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                medication["returned"] = True
                medication["returned_at"] = now
                medication["return_reason"] = reason or "未交付，回药房回收"
                medication["manual_reviewed"] = False
                medication["manual_reviewed_at"] = ""
                medication["manual_review_result"] = ""
                message = f"已标记未交付回收：{patient.get('bed_no')} {patient.get('patient_name')} / {medication.get('medicine_name')}"
                self.append_batch_audit(
                    batch,
                    "return_medication",
                    message,
                    "ok",
                    {
                        "patient_id": patient.get("patient_id", ""),
                        "medication_id": medication.get("id", ""),
                    },
                )
                self.save_exception_to_db_locked(
                    batch,
                    "return_medication",
                    reason or message,
                    stop=stop,
                    patient=patient,
                    medication=medication,
                )
                self.update_batch_summary(batch)
                self.mark_active_stop_completed_if_ready(batch, stop)
                return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}
            if action in {"retry", "clear_exception"}:
                if not medication.get("exception"):
                    message = f"药品没有待复核异常：{medication.get('medicine_name')}"
                    self.append_batch_audit(
                        batch,
                        action,
                        message,
                        "fail",
                        {
                            "patient_id": patient.get("patient_id", ""),
                            "medication_id": medication.get("id", ""),
                        },
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                if medication.get("dispensed") or medication.get("returned"):
                    message = f"药品已交付或已回收，不能重新打开：{medication.get('medicine_name')}"
                    self.append_batch_audit(
                        batch,
                        action,
                        message,
                        "fail",
                        {
                            "patient_id": patient.get("patient_id", ""),
                            "medication_id": medication.get("id", ""),
                        },
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                if batch.get("route_status") in {
                    "RETURNING_TO_PHARMACY",
                    "BATCH_COMPLETED",
                }:
                    message = "批次已离开病房或已完成，不能重新打开异常"
                    self.append_batch_audit(
                        batch,
                        action,
                        message,
                        "fail",
                        {
                            "patient_id": patient.get("patient_id", ""),
                            "medication_id": medication.get("id", ""),
                        },
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                if stop.get(
                    "stop_status"
                ) == "COMPLETED" and not self.reopen_active_stop_for_retry(batch, stop):
                    message = (
                        f"{stop.get('display_name')} 不是当前病房，不能重新打开异常"
                    )
                    self.append_batch_audit(
                        batch,
                        action,
                        message,
                        "fail",
                        {
                            "patient_id": patient.get("patient_id", ""),
                            "medication_id": medication.get("id", ""),
                        },
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                self.clear_medication_exception_for_retry(
                    medication,
                    now,
                    reason
                    or (
                        "稍后重试，重新进入交付流程"
                        if action == "retry"
                        else "异常解除，重新进入交付流程"
                    ),
                    action,
                )
                patient["patient_status"] = "LOADED"
                self.reopen_active_stop_for_retry(batch, stop)
                message = f"已重新打开药品异常：{patient.get('bed_no')} {patient.get('patient_name')} / {medication.get('medicine_name')}"
                self.append_batch_audit(
                    batch,
                    action,
                    message,
                    "ok",
                    {
                        "patient_id": patient.get("patient_id", ""),
                        "medication_id": medication.get("id", ""),
                    },
                )
                self.update_batch_summary(batch)
                return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}
            if action == "manual_review":
                if not medication.get("exception") and not medication.get("returned"):
                    message = (
                        f"药品没有需要药师复核的异常：{medication.get('medicine_name')}"
                    )
                    self.append_batch_audit(
                        batch,
                        "manual_review",
                        message,
                        "fail",
                        {
                            "patient_id": patient.get("patient_id", ""),
                            "medication_id": medication.get("id", ""),
                        },
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                self.mark_medication_manual_reviewed(
                    medication, now, reason or "药师复核通过，已记录审计"
                )
                message = f"药师复核确认：{patient.get('bed_no')} {patient.get('patient_name')} / {medication.get('medicine_name')}"
                self.append_batch_audit(
                    batch,
                    "manual_review",
                    message,
                    "ok",
                    {
                        "patient_id": patient.get("patient_id", ""),
                        "medication_id": medication.get("id", ""),
                    },
                )
                self.save_exception_to_db_locked(
                    batch,
                    "manual_review",
                    reason or message,
                    stop=stop,
                    patient=patient,
                    medication=medication,
                )
                self.update_batch_summary(batch)
                self.mark_active_stop_completed_if_ready(batch, stop)
                return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}
            message = f"未知异常动作：{action or '-'}"
            self.append_batch_audit(
                batch,
                "exception",
                message,
                "fail",
                {
                    "patient_id": patient_id,
                    "medication_id": medication_id,
                },
            )
            return {"ok": False, "message": message, "batch": copy.deepcopy(batch)}

    def find_batch_item_by_id(self, batch, patient_id, medication_id=""):
        for stop in batch.get("stops", []):
            for patient in stop.get("patients", []):
                if not medication_id:
                    if patient_id and patient.get("patient_id") == patient_id:
                        return stop, patient, None
                    continue
                for medication in patient.get("medications", []):
                    if medication.get("id") == medication_id and (
                        not patient_id or patient.get("patient_id") == patient_id
                    ):
                        return stop, patient, medication
        return None, None, None

    def reopen_active_stop_for_retry(self, batch, stop):
        active_index = int(batch.get("active_stop_index", -1))
        if (
            0 <= active_index < len(batch.get("stops", []))
            and batch["stops"][active_index] is stop
        ):
            stop["stop_status"] = "WARD_HANDOVER"
            stop["completed_time"] = ""
            batch["route_status"] = "WARD_HANDOVER"
            batch["current_station"] = stop.get(
                "target_station", batch.get("current_station", "")
            )
            return True
        return False

    def clear_medication_exception_for_retry(self, medication, now, reason, action):
        medication["exception"] = ""
        medication["exception_at"] = ""
        medication["exception_reason"] = ""
        medication["exception_resolved_at"] = now
        medication["exception_resolved_reason"] = reason
        medication["exception_resolution_action"] = action
        medication["manual_reviewed"] = False
        medication["manual_reviewed_at"] = ""
        medication["manual_review_result"] = ""

    def mark_medication_manual_reviewed(self, medication, now, reason):
        medication["manual_reviewed"] = True
        medication["manual_reviewed_at"] = now
        medication["manual_review_result"] = reason

    def mark_active_stop_completed_if_ready(self, batch, stop):
        active_index = int(batch.get("active_stop_index", -1))
        active_stop = None
        if 0 <= active_index < len(batch.get("stops", [])):
            active_stop = batch["stops"][active_index]
        if active_stop is not stop:
            return
        if stop.get("stop_status") == "COMPLETED":
            batch["route_status"] = "WARD_COMPLETED"
            if not stop.get("completed_time"):
                stop["completed_time"] = self.now_text()
            self.append_batch_audit(
                batch, "ward_completed", f"{stop.get('display_name')} 已处理完成", "ok"
            )

    def advance_delivery_batch(self):
        with self.delivery_batch_lock:
            batch = self.delivery_batch
            self.update_batch_summary(batch)
            status = batch.get("route_status")
            blockers, _warnings = self.collect_delivery_batch_backend_blockers(batch, "advance")
            if blockers:
                message = '；'.join(blockers)
                return self.reject_delivery_batch_action_locked(
                    batch,
                    "advance_blocked",
                    message,
                    {"route_status": status},
                )
            if status == "WAITING_LOAD_CONFIRMATION":
                message = "还有药品未完成装药确认，暂不能出发"
                self.append_batch_audit(batch, "advance", message, "fail")
                return {"ok": False, "message": message, "batch": copy.deepcopy(batch)}
            if status == "READY_TO_DEPART":
                blocker = self.delivery_motion_blocker()
                if blocker:
                    self.append_batch_audit(batch, "advance", blocker, "fail")
                    return {
                        "ok": False,
                        "message": blocker,
                        "batch": copy.deepcopy(batch),
                    }
                return self.move_to_next_batch_stop_locked(batch)
            if status == "NAVIGATING_TO_WARD":
                active_index = int(batch.get("active_stop_index", -1))
                if 0 <= active_index < len(batch.get("stops", [])):
                    stop = batch["stops"][active_index]
                    task_id = stop.get("task_manager_task_id", "")
                    if task_id:
                        task_state = self.get_state()
                        if task_state.get("task_id") != task_id:
                            message = f"等待任务管理同步当前病房任务：期望 {task_id}，当前 {task_state.get('task_id') or '-'}"
                            self.append_batch_audit(
                                batch,
                                "arrive_wait_task_manager",
                                message,
                                "fail",
                                {
                                    "stop_id": stop.get("stop_id", ""),
                                    "task_manager_task_id": task_id,
                                },
                            )
                            return {
                                "ok": False,
                                "message": message,
                                "batch": copy.deepcopy(batch),
                            }
                        if task_state.get("state") != "WAITING_DISPENSE_CONFIRMATION":
                            message = f"尚未到达{stop.get('display_name')}，任务管理状态：{task_state.get('state') or '-'}，进度 {int(float(task_state.get('progress', 0.0)) * 100)}%"
                            self.append_batch_audit(
                                batch,
                                "arrive_wait_task_manager",
                                message,
                                "fail",
                                {
                                    "stop_id": stop.get("stop_id", ""),
                                    "task_manager_task_id": task_id,
                                },
                            )
                            return {
                                "ok": False,
                                "message": message,
                                "batch": copy.deepcopy(batch),
                            }
                    now = self.now_text()
                    stop["stop_status"] = "WARD_HANDOVER"
                    stop["arrived_time"] = now
                    batch["route_status"] = "WARD_HANDOVER"
                    batch["current_station"] = stop.get("target_station", "")
                    message = f"已到达{stop.get('display_name')}，进入病房交付确认"
                    self.append_batch_audit(batch, "arrived_at_ward", message, "ok")
                    return {
                        "ok": True,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
            if status in {"WARD_COMPLETED", "WARD_HANDOVER"}:
                active_index = int(batch.get("active_stop_index", -1))
                if 0 <= active_index < len(batch.get("stops", [])):
                    stop = batch["stops"][active_index]
                    if stop.get("stop_status") != "COMPLETED":
                        message = f"{stop.get('display_name')} 仍有药品未交付或未处理"
                        self.append_batch_audit(batch, "advance", message, "fail")
                        return {
                            "ok": False,
                            "message": message,
                            "batch": copy.deepcopy(batch),
                        }
                return self.move_to_next_batch_stop_locked(batch)
            if status == "RETURNING_TO_PHARMACY":
                now = self.now_text()
                batch["route_status"] = "BATCH_COMPLETED"
                batch["current_station"] = "pharmacy"
                batch["finished_time"] = now
                message = "已返回药房，本次配送批次完成"
                self.append_batch_audit(batch, "batch_completed", message, "ok")
                return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}
            message = f"当前批次状态无需推进：{status}"
            return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}

    def move_to_next_batch_stop_locked(self, batch):
        for index, stop in enumerate(batch.get("stops", [])):
            if stop.get("stop_status") != "COMPLETED":
                now = self.now_text()
                task_response = self.create_task_manager_stop_task_locked(batch, stop)
                if not task_response.get("accepted"):
                    message = f"创建病房级任务失败：{task_response.get('message', '')}"
                    self.append_batch_audit(
                        batch,
                        "task_manager_create_failed",
                        message,
                        "fail",
                        {
                            "stop_id": stop.get("stop_id", ""),
                            "target_station": stop.get("target_station", ""),
                        },
                    )
                    return {
                        "ok": False,
                        "message": message,
                        "batch": copy.deepcopy(batch),
                    }
                batch["active_stop_index"] = index
                batch["active_stop_id"] = stop.get("stop_id", "")
                batch["route_status"] = "NAVIGATING_TO_WARD"
                batch["current_station"] = (
                    "pharmacy"
                    if index == 0
                    else batch.get("current_station", "pharmacy")
                )
                if not batch.get("started_time"):
                    batch["started_time"] = now
                stop["stop_status"] = "NAVIGATING_TO_WARD"
                task_id_text = (
                    f"，任务管理 ID：{task_response.get('task_id')}"
                    if task_response.get("task_id")
                    else ""
                )
                message = f"开始前往{stop.get('display_name')}{task_id_text}"
                self.append_batch_audit(
                    batch,
                    "navigate_to_ward",
                    message,
                    "ok",
                    {
                        "stop_id": stop.get("stop_id", ""),
                        "target_station": stop.get("target_station", ""),
                        "task_manager_task_id": task_response.get("task_id", ""),
                    },
                )
                return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}
        batch["active_stop_index"] = -1
        batch["active_stop_id"] = ""
        batch["route_status"] = "RETURNING_TO_PHARMACY"
        batch["current_station"] = batch.get("current_station", "")
        message = "所有病房已处理，开始返回药房"
        self.append_batch_audit(batch, "returning_to_pharmacy", message, "ok")
        return {"ok": True, "message": message, "batch": copy.deepcopy(batch)}





