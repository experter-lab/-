#!/usr/bin/env bash
set -e
for i in $(seq 1 30); do
  printf '%s ' "$(date '+%H:%M:%S')"
  curl -s http://127.0.0.1:8080/api/drug_info | python3 -c 'import sys,json; d=json.load(sys.stdin); print({k:d.get(k,"") for k in ["raw_code_text","code_text","code_type","code_method","label_product_code","label_product_model","label_quantity","drug_id","drug_name","source"]})'
  sleep 1
done
