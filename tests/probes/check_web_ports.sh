#!/usr/bin/env bash
set +e
echo '--- ports ---'
ss -ltnp 2>/dev/null | grep -E ':8081|:8085' || true
echo '--- webctl log ---'
tail -80 /tmp/rk3588_delivery_webctl.log 2>/dev/null || true
echo '--- recent logs ---'
ls -lt /tmp/*dashboard* /tmp/*web* 2>/dev/null | head -20 || true
