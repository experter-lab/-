import csv
import io


DELIVERY_BATCH_REPORT_FIELDS = [
    "batch_id",
    "route_status",
    "ward_id",
    "ward_name",
    "bed_no",
    "patient_id",
    "patient_name",
    "medicine_name",
    "product_code",
    "trace_id",
    "quantity",
    "loaded",
    "loaded_at",
    "dispensed",
    "dispensed_at",
    "patient_signed",
    "patient_signed_at",
    "patient_signed_delivery_id",
    "returned",
    "returned_at",
    "return_reason",
    "exception",
    "exception_at",
    "exception_reason",
    "exception_resolved_at",
    "exception_resolved_reason",
    "exception_resolution_action",
    "manual_reviewed",
    "manual_reviewed_at",
    "manual_review_result",
]


def build_delivery_batch_report(batch, generated_at):
    rows = []
    for stop in batch.get("stops", []):
        for patient in stop.get("patients", []):
            for medication in patient.get("medications", []):
                rows.append(
                    {
                        "batch_id": batch.get("batch_id", ""),
                        "route_status": batch.get("route_status", ""),
                        "ward_id": patient.get("ward_id", ""),
                        "ward_name": patient.get(
                            "ward_name", stop.get("display_name", "")
                        ),
                        "bed_no": patient.get("bed_no", ""),
                        "patient_id": patient.get("patient_id", ""),
                        "patient_name": patient.get("patient_name", ""),
                        "medicine_name": medication.get("medicine_name", ""),
                        "product_code": medication.get("product_code", ""),
                        "trace_id": medication.get("trace_id", ""),
                        "quantity": medication.get("quantity", ""),
                        "loaded": bool(medication.get("loaded")),
                        "loaded_at": medication.get("loaded_at", ""),
                        "dispensed": bool(medication.get("dispensed")),
                        "dispensed_at": medication.get("dispensed_at", ""),
                        "patient_signed": bool(medication.get("patient_signed")),
                        "patient_signed_at": medication.get("patient_signed_at", ""),
                        "patient_signed_delivery_id": medication.get("patient_signed_delivery_id", ""),
                        "returned": bool(medication.get("returned")),
                        "returned_at": medication.get("returned_at", ""),
                        "return_reason": medication.get("return_reason", ""),
                        "exception": medication.get("exception", ""),
                        "exception_at": medication.get("exception_at", ""),
                        "exception_reason": medication.get("exception_reason", ""),
                        "exception_resolved_at": medication.get(
                            "exception_resolved_at", ""
                        ),
                        "exception_resolved_reason": medication.get(
                            "exception_resolved_reason", ""
                        ),
                        "exception_resolution_action": medication.get(
                            "exception_resolution_action", ""
                        ),
                        "manual_reviewed": bool(medication.get("manual_reviewed")),
                        "manual_reviewed_at": medication.get("manual_reviewed_at", ""),
                        "manual_review_result": medication.get(
                            "manual_review_result", ""
                        ),
                    }
                )
    summary = batch.get("summary") or {}
    return {
        "generated_at": generated_at,
        "batch_id": batch.get("batch_id", ""),
        "route_status": batch.get("route_status", ""),
        "source_station": batch.get("source_station", ""),
        "current_station": batch.get("current_station", ""),
        "summary": summary,
        "batch": batch,
        "rows": rows,
    }


def build_delivery_batch_report_csv(report):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=DELIVERY_BATCH_REPORT_FIELDS)
    writer.writeheader()
    for row in report["rows"]:
        writer.writerow(row)
    return output.getvalue()
