#!/usr/bin/env bash
set -euo pipefail
BASE="http://127.0.0.1:8080"

printf 'Current state:\n'
curl -s "$BASE/api/state" | python3 -m json.tool
printf '\nCurrent drug_info:\n'
curl -s "$BASE/api/drug_info" | python3 -m json.tool

payload=$(cat <<'JSON'
{
  "medicine_name": "TYPE-C 16PIN 2MD(073)",
  "source_station": "pharmacy",
  "target_station": "ward_a",
  "patient_id": "patient_demo_001",
  "patient_name": "张三",
  "ward_id": "ward_a",
  "bed_no": "A-01",
  "product_code": "C2765186",
  "product_model": "TYPE-C 16PIN 2MD(073)",
  "quantity": "10",
  "trace_id": "175550822",
  "order_no": "SO25091117540",
  "medications_json": "[{\"medicine_name\":\"TYPE-C 16PIN 2MD(073)\",\"product_code\":\"C2765186\",\"product_model\":\"TYPE-C 16PIN 2MD(073)\",\"quantity\":\"10\",\"trace_id\":\"175550822\",\"order_no\":\"SO25091117540\"}]"
}
JSON
)

printf '\nCreate task:\n'
create_resp=$(curl -s -X POST "$BASE/api/tasks" -H 'Content-Type: application/json' -d "$payload")
printf '%s\n' "$create_resp" | python3 -m json.tool
task_id=$(printf '%s' "$create_resp" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("task_id", ""))')
if [ -z "$task_id" ]; then
  echo "ERROR: empty task_id" >&2
  exit 1
fi

verify_payload_load=$(cat <<JSON
{"task_id":"$task_id","product_code":"C2765186","trace_id":"175550822","stage":"load"}
JSON
)
printf '\nVerify load:\n'
curl -s -X POST "$BASE/api/verify_task" -H 'Content-Type: application/json' -d "$verify_payload_load" | python3 -m json.tool

printf '\nState after load:\n'
curl -s "$BASE/api/state" | python3 -m json.tool

printf '\nWait simulated navigation...\n'
sleep 5
printf '\nState before dispense:\n'
curl -s "$BASE/api/state" | python3 -m json.tool

verify_payload_dispense=$(cat <<JSON
{"task_id":"$task_id","product_code":"C2765186","trace_id":"175550822","stage":"dispense"}
JSON
)
printf '\nVerify dispense:\n'
curl -s -X POST "$BASE/api/verify_task" -H 'Content-Type: application/json' -d "$verify_payload_dispense" | python3 -m json.tool

printf '\nFinal state:\n'
curl -s "$BASE/api/state" | python3 -m json.tool
