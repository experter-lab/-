import copy
import sys
import threading
import types
import unittest


if "medicine_interfaces.srv" not in sys.modules:
    medicine_interfaces = types.ModuleType("medicine_interfaces")
    srv = types.ModuleType("medicine_interfaces.srv")

    class _CreateDeliveryTask:
        class Request:
            pass

    srv.CreateDeliveryTask = _CreateDeliveryTask
    medicine_interfaces.srv = srv
    sys.modules["medicine_interfaces"] = medicine_interfaces
    sys.modules["medicine_interfaces.srv"] = srv

try:
    from medicine_web_dashboard.dashboard_delivery_batch import DeliveryBatchMixin
except ImportError:
    from dashboard_delivery_batch import DeliveryBatchMixin


def sample_payload(medications=None):
    return {
        "batch_id": "TEST-BATCH-001",
        "source_station": "pharmacy",
        "patients": [
            {
                "patient_id": "patient_a",
                "patient_name": "Patient A",
                "ward_id": "ward_a",
                "ward_name": "Ward A",
                "bed_no": "A-01",
                "target_station": "ward_a",
                "medications": medications
                or [
                    {
                        "id": "med_a",
                        "medicine_name": "Medicine A",
                        "product_code": "P001",
                        "trace_id": "T001",
                        "quantity": "1",
                    }
                ],
            }
        ],
    }


class FakeDashboard(DeliveryBatchMixin):
    def __init__(self, payload=None):
        self.stations = [
            {"id": "pharmacy", "name": "Pharmacy"},
            {"id": "ward_a", "name": "Ward A"},
        ]
        self.delivery_batch_lock = threading.RLock()
        self.delivery_batch_state_file = ""
        self.scan_max_age_sec = 8.0
        self.drug_info = {}
        self.saved_states = []
        self.saved_batches = []
        self.saved_scans = []
        self.saved_exceptions = []
        self.task_counter = 0
        self.state = {
            "task_id": "",
            "state": "",
            "progress": 0.0,
        }
        self.delivery_batch = self.create_delivery_batch_from_payload(
            payload or sample_payload()
        )

    def now_text(self):
        return "2026-06-03 21:40:00"

    def save_delivery_batch_state_locked(self, batch):
        self.saved_states.append(copy.deepcopy(batch))

    def save_batch_to_db_locked(self, batch):
        self.saved_batches.append(copy.deepcopy(batch))

    def save_scan_to_db_locked(
        self,
        batch,
        scan_type,
        product_code,
        trace_id,
        scan_result,
        stop=None,
        patient=None,
        medication=None,
        notes="",
    ):
        self.saved_scans.append(
            {
                "scan_type": scan_type,
                "product_code": product_code,
                "trace_id": trace_id,
                "scan_result": scan_result,
                "notes": notes,
            }
        )

    def save_exception_to_db_locked(
        self,
        batch,
        exception_type,
        description,
        stop=None,
        patient=None,
        medication=None,
        resolution="",
    ):
        self.saved_exceptions.append(
            {
                "exception_type": exception_type,
                "description": description,
                "resolution": resolution,
            }
        )

    def create_task_from_payload_locked(self, payload):
        self.task_counter += 1
        return {
            "accepted": True,
            "task_id": f"task-{self.task_counter}",
            "message": "accepted",
        }

    def get_state(self):
        return copy.deepcopy(self.state)

    def get_drug_info(self):
        return copy.deepcopy(self.drug_info)

    def verify_delivery_task(self, payload):
        return {
            "verified": True,
            "message": "verified",
            "confirmed_at": self.now_text(),
            "task_state": "WAITING_DISPENSE_CONFIRMATION",
        }


class DeliveryBatchMixinTest(unittest.TestCase):
    def first_stop(self, dashboard):
        return dashboard.delivery_batch["stops"][0]

    def first_patient(self, dashboard):
        return self.first_stop(dashboard)["patients"][0]

    def first_medication(self, dashboard):
        return self.first_patient(dashboard)["medications"][0]

    def test_import_payload_normalizes_route_and_summary(self):
        dashboard = FakeDashboard()

        batch = dashboard.delivery_batch

        self.assertEqual(batch["batch_id"], "TEST-BATCH-001")
        self.assertEqual(batch["route"], ["pharmacy", "ward_a", "pharmacy"])
        self.assertEqual(batch["route_status"], "WAITING_LOAD_CONFIRMATION")
        self.assertEqual(batch["summary"]["medication_total_count"], 1)
        self.assertFalse(batch["summary"]["all_loaded"])

    def test_load_scan_marks_medication_loaded_and_ready_to_depart(self):
        dashboard = FakeDashboard()

        response = dashboard.scan_load_delivery_batch(
            {"product_code": "P001", "trace_id": "T001"}
        )

        self.assertTrue(response["ok"])
        self.assertTrue(self.first_medication(dashboard)["loaded"])
        self.assertEqual(dashboard.delivery_batch["route_status"], "READY_TO_DEPART")
        self.assertEqual(dashboard.saved_scans[-1]["scan_type"], "load")
        self.assertEqual(dashboard.saved_scans[-1]["scan_result"], "success")

    def test_load_scan_uses_fresh_dashboard_drug_info_fallback(self):
        dashboard = FakeDashboard()
        dashboard.drug_info = {
            "label_product_code": "P001",
            "label_trace_id": "T001",
            "scan_age_sec": 1.0,
        }

        response = dashboard.scan_load_delivery_batch({})

        self.assertTrue(response["ok"])
        self.assertTrue(self.first_medication(dashboard)["loaded"])
        self.assertEqual(dashboard.saved_scans[-1]["scan_result"], "success")

    def test_load_scan_rejects_stale_dashboard_drug_info_fallback(self):
        dashboard = FakeDashboard()
        dashboard.drug_info = {
            "label_product_code": "P001",
            "label_trace_id": "T001",
            "scan_age_sec": 30.0,
        }

        response = dashboard.scan_load_delivery_batch({})

        self.assertFalse(response["ok"])
        self.assertFalse(self.first_medication(dashboard)["loaded"])
        self.assertEqual(dashboard.saved_scans[-1]["scan_result"], "mismatch")
        self.assertEqual(dashboard.saved_scans[-1]["product_code"], "")
        self.assertEqual(dashboard.saved_scans[-1]["trace_id"], "")

    def test_explicit_load_scan_payload_works_even_if_cached_drug_info_is_stale(self):
        dashboard = FakeDashboard()
        dashboard.drug_info = {
            "label_product_code": "P001",
            "label_trace_id": "T001",
            "scan_age_sec": 30.0,
        }

        response = dashboard.scan_load_delivery_batch(
            {"product_code": "P001", "trace_id": "T001"}
        )

        self.assertTrue(response["ok"])
        self.assertTrue(self.first_medication(dashboard)["loaded"])

    def test_advance_and_dispense_complete_single_stop_batch(self):
        dashboard = FakeDashboard()
        dashboard.scan_load_delivery_batch({"product_code": "P001", "trace_id": "T001"})

        depart = dashboard.advance_delivery_batch()
        task_id = self.first_stop(dashboard)["task_manager_task_id"]
        dashboard.state = {
            "task_id": task_id,
            "state": "WAITING_DISPENSE_CONFIRMATION",
            "progress": 1.0,
        }
        arrive = dashboard.advance_delivery_batch()
        dispense = dashboard.scan_dispense_delivery_batch(
            {"product_code": "P001", "trace_id": "T001"}
        )
        returning = dashboard.advance_delivery_batch()
        completed = dashboard.advance_delivery_batch()

        self.assertTrue(depart["ok"])
        self.assertEqual(depart["batch"]["route_status"], "NAVIGATING_TO_WARD")
        self.assertTrue(arrive["ok"])
        self.assertEqual(arrive["batch"]["route_status"], "WARD_HANDOVER")
        self.assertTrue(dispense["ok"])
        self.assertTrue(self.first_medication(dashboard)["dispensed"])
        self.assertEqual(self.first_stop(dashboard)["stop_status"], "COMPLETED")
        self.assertTrue(returning["ok"])
        self.assertEqual(returning["batch"]["route_status"], "RETURNING_TO_PHARMACY")
        self.assertTrue(completed["ok"])
        self.assertEqual(completed["batch"]["route_status"], "BATCH_COMPLETED")

    def test_mismatched_load_scan_does_not_mark_loaded(self):
        dashboard = FakeDashboard()

        response = dashboard.scan_load_delivery_batch(
            {"product_code": "NO_SUCH_CODE", "trace_id": "T001"}
        )

        self.assertFalse(response["ok"])
        self.assertFalse(self.first_medication(dashboard)["loaded"])
        self.assertEqual(dashboard.saved_scans[-1]["scan_result"], "mismatch")

    def test_patient_absent_marks_all_pending_medications_exception(self):
        dashboard = FakeDashboard(
            sample_payload(
                medications=[
                    {
                        "id": "med_a",
                        "medicine_name": "Medicine A",
                        "product_code": "P001",
                        "trace_id": "T001",
                    },
                    {
                        "id": "med_b",
                        "medicine_name": "Medicine B",
                        "product_code": "P002",
                        "trace_id": "T002",
                    },
                ]
            )
        )

        response = dashboard.mark_delivery_batch_exception(
            {
                "action": "patient_absent",
                "patient_id": "patient_a",
                "reason": "patient unavailable",
            }
        )

        self.assertTrue(response["ok"])
        self.assertEqual(self.first_patient(dashboard)["patient_status"], "COMPLETED")
        self.assertEqual(
            dashboard.delivery_batch["summary"]["medication_exception_count"], 2
        )
        self.assertEqual(
            {item["exception"] for item in self.first_patient(dashboard)["medications"]},
            {"patient_absent"},
        )
        self.assertEqual(
            dashboard.saved_exceptions[-1]["exception_type"], "patient_absent"
        )


if __name__ == "__main__":
    unittest.main()
