#!/usr/bin/env bash
set -eo pipefail

pkill -f '[c]hassis_bridge_node' || true

echo "=== ttyS9 baud probe ==="
echo "Send HEX continuously while this script is running:"
echo "FE 09 00 01 01 00 00 00 00 00 0A 03 00 03 03 00 00"
echo

for baud in 9600 57600 115200 921600; do
  echo "=== BAUD ${baud} ==="
  stty -F /dev/ttyS9 "${baud}" cs8 -cstopb -parenb -ixon -ixoff -crtscts raw -echo
  rm -f "/tmp/ttys9_${baud}.bin"
  timeout 5s dd if=/dev/ttyS9 of="/tmp/ttys9_${baud}.bin" bs=1 count=128 status=none || true
  bytes=$(wc -c < "/tmp/ttys9_${baud}.bin")
  echo "bytes=${bytes}"
  if [ "${bytes}" -gt 0 ]; then
    xxd -g 1 "/tmp/ttys9_${baud}.bin"
    python3 - "${baud}" "/tmp/ttys9_${baud}.bin" <<'PY'
import collections
import sys
baud = sys.argv[1]
path = sys.argv[2]
data = open(path, 'rb').read()
counts = collections.Counter(data)
print('summary baud=%s unique=%s top=%s' % (baud, len(counts), counts.most_common(8)))
PY
  fi
  echo
done
