#!/usr/bin/env bash
# Provision the VM to run The Quiet Story pipeline (UI + API + worker + renders).
# Idempotent: safe to re-run. Target OS: Ubuntu 22.04/24.04 or Debian 12.
set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/AI_gen_Platform}"
RUN_USER="$(whoami)"

echo "==> 1/8  System packages (ffmpeg, python, node deps, headless-Chrome libs, fonts)"
sudo apt-get update -y
sudo apt-get install -y \
  ffmpeg python3 python3-venv python3-pip git curl fontconfig \
  libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libgbm1 libasound2 \
  libpangocairo-1.0-0 libgtk-3-0 libxdamage1 libxcomposite1 libxrandr2 \
  libxkbcommon0 libxfixes3 libxext6 libx11-xcb1 fonts-noto

echo "==> 2/8  Node.js 20 (for Remotion)"
if ! command -v node >/dev/null 2>&1; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi
node --version

echo "==> 3/8  Swap file (2G) if none present"
if ! sudo swapon --show | grep -q .; then
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

echo "==> 4/8  Python venv + backend deps"
cd "$APP_DIR"
[ -d .venv ] || python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip wheel
pip install -r backend/requirements.txt

echo "==> 5/8  Remotion install + headless Chrome"
cd "$APP_DIR/remotion"
npm install
npx remotion browser ensure || true
cd "$APP_DIR"

echo "==> 6/8  Frontend build"
npm --prefix frontend install
npm --prefix frontend run build

echo "==> 7/8  Install Mukta fonts (Devanagari) system-wide"
if ls assets/fonts/Mukta-*.ttf >/dev/null 2>&1; then
  sudo mkdir -p /usr/share/fonts/truetype/mukta
  sudo cp assets/fonts/Mukta-*.ttf /usr/share/fonts/truetype/mukta/
  sudo fc-cache -f
fi

echo "==> 8/8  systemd services (API+worker on :8200, web on :3200, bound to localhost)"
sudo tee /etc/systemd/system/quiet-story-api.service >/dev/null <<UNIT
[Unit]
Description=The Quiet Story API + generation/render worker
After=network.target

[Service]
User=${RUN_USER}
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8200
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT

sudo tee /etc/systemd/system/quiet-story-web.service >/dev/null <<UNIT
[Unit]
Description=The Quiet Story Next.js frontend
After=network.target quiet-story-api.service

[Service]
User=${RUN_USER}
WorkingDirectory=${APP_DIR}/frontend
ExecStart=/usr/bin/npm run start
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable quiet-story-api quiet-story-web

if [ -f "${APP_DIR}/.env" ]; then
  chmod 600 "${APP_DIR}/.env"
  sudo systemctl restart quiet-story-api quiet-story-web
  echo "==> services started."
else
  echo "!!  No .env yet — copy deploy/env.example to .env, add your API keys, then:"
  echo "    sudo systemctl restart quiet-story-api quiet-story-web"
fi

echo ""
echo "DONE. Render a chapter with:"
echo "    cd ${APP_DIR} && source .venv/bin/activate && python scripts/build_premium.py 5"
echo "Reach the UI from your Mac via an SSH tunnel (see deploy/README.md)."
