#!/usr/bin/env bash
set -euo pipefail

ARCHIVE="/mnt/sdcard/ollama-linux-arm64.tgz"
SERVICE_SRC="/mnt/sdcard/ollama.service"

test -f "${ARCHIVE}"

mkdir -p /usr/local
tar -xzf "${ARCHIVE}" -C /usr/local

if [ ! -x /usr/local/bin/ollama ] && [ -x /usr/local/ollama ]; then
  ln -sf /usr/local/ollama /usr/local/bin/ollama
fi

if ! id ollama >/dev/null 2>&1; then
  useradd -r -s /bin/false -U -m -d /usr/share/ollama ollama
fi

if getent group render >/dev/null 2>&1; then
  usermod -a -G render ollama || true
fi
if getent group video >/dev/null 2>&1; then
  usermod -a -G video ollama || true
fi

if [ -f "${SERVICE_SRC}" ]; then
  cp "${SERVICE_SRC}" /etc/systemd/system/ollama.service
else
  cat >/etc/systemd/system/ollama.service <<'EOF'
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=3
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

[Install]
WantedBy=multi-user.target
EOF
fi

sed -i 's#/usr/bin/ollama#/usr/local/bin/ollama#g' /etc/systemd/system/ollama.service
sed -i 's#WantedBy=default.target#WantedBy=multi-user.target#g' /etc/systemd/system/ollama.service

systemctl daemon-reload
systemctl enable ollama
systemctl restart ollama

sleep 3
/usr/local/bin/ollama --version
systemctl --no-pager --full status ollama | head -80
curl -s --max-time 5 http://127.0.0.1:11434/api/tags || true
