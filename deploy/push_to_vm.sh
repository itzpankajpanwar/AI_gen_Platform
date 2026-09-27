#!/usr/bin/env bash
# Push this repo to the GCP VM and provision it. Run on your Mac AFTER `gcloud auth login`.
set -euo pipefail

PROJECT="${PROJECT:-project-04f46d0e-669f-4bc4-843}"
ZONE="${ZONE:-asia-south1-a}"
INSTANCE="${INSTANCE:-instance-20260927-051209}"
REMOTE_DIR="AI_gen_Platform"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

HOST="${INSTANCE}.${ZONE}.${PROJECT}"

echo "==> Config: project=$PROJECT zone=$ZONE instance=$INSTANCE"
gcloud config set project "$PROJECT" >/dev/null

echo "==> Writing SSH host alias ($HOST) into ~/.ssh/config"
gcloud compute config-ssh >/dev/null

echo "==> Rsyncing repo to VM (cached assets included; build junk excluded)"
rsync -avz --delete-after \
  --exclude '.git' \
  --exclude '**/node_modules' \
  --exclude '.venv' \
  --exclude 'backend/.venv' \
  --exclude 'frontend/.next' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '/data/' \
  --exclude '.DS_Store' \
  --exclude '.env' \
  --exclude 'samples/film_premium/*.mp4' \
  -e "ssh" \
  "${LOCAL_DIR}/" "${HOST}:~/${REMOTE_DIR}/"

echo "==> Running VM provisioning (this installs everything + starts services)"
ssh "$HOST" "cd ~/${REMOTE_DIR} && chmod +x deploy/setup_vm.sh && APP_DIR=~/${REMOTE_DIR} bash deploy/setup_vm.sh"

cat <<EOF

==> PUSH COMPLETE.

Next (one time), create the .env with your fresh keys ON THE VM:
  ssh ${HOST}
  cd ~/${REMOTE_DIR}
  cp deploy/env.example .env && nano .env      # paste OPENAI_API_KEY + SARVAM_API_KEY
  chmod 600 .env
  sudo systemctl restart quiet-story-api quiet-story-web

Open the UI from your Mac via an SSH tunnel:
  ssh -N -L 3200:localhost:3200 -L 8200:localhost:8200 ${HOST}
  # then browse http://localhost:3200

Render a chapter on the VM:
  ssh ${HOST}
  cd ~/${REMOTE_DIR} && source .venv/bin/activate && python scripts/build_premium.py 5
EOF
