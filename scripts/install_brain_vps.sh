#!/usr/bin/env bash
set -euo pipefail

echo "=== Provaliant Brain OS VPS Installer ==="

sudo apt update && sudo apt upgrade -y
sudo apt install -y \
  git curl wget unzip build-essential \
  python3 python3-pip python3-venv \
  postgresql postgresql-contrib postgresql-server-dev-all \
  nginx ufw jq

cd /tmp
if [ ! -d pgvector ]; then
  git clone https://github.com/pgvector/pgvector.git
fi
cd pgvector
make
sudo make install

sudo mkdir -p /opt/provaliant-brain-os
sudo chown -R "$USER":"$USER" /opt/provaliant-brain-os

sudo ufw allow 22/tcp
sudo ufw allow 8000/tcp
sudo ufw --force enable

echo "Installation complete. Clone repository to /opt/provaliant-brain-os and run scripts/setup_db.sh"
