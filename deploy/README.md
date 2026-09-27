# Deploy to the GCP VM

Target VM: `c2d-standard-8` (8 vCPU / 32 GB), zone `asia-south1-a`,
project `project-04f46d0e-669f-4bc4-843`, instance `instance-20260927-051209`.

## One-time (you do this — needs your Google login)
```bash
gcloud auth login
gcloud config set project project-04f46d0e-669f-4bc4-843
```

## Push + provision (one command, from your Mac)
```bash
bash deploy/push_to_vm.sh
```
This rsyncs the repo **including your cached narration/images** (so nothing
regenerates), installs ffmpeg + Node + headless-Chrome libs + Mukta fonts,
builds the frontend, creates a swap file, and installs two systemd services.

## Add your keys (on the VM)
```bash
ssh <instance>.<zone>.<project>
cd ~/AI_gen_Platform
cp deploy/env.example .env && nano .env   # OPENAI_API_KEY + SARVAM_API_KEY
chmod 600 .env
sudo systemctl restart quiet-story-api quiet-story-web
```

## Use it
- **UI** (from your Mac, via SSH tunnel — nothing is exposed to the internet):
  ```bash
  ssh -N -L 3200:localhost:3200 -L 8200:localhost:8200 <instance>.<zone>.<project>
  # browse http://localhost:3200
  ```
- **Render a chapter on the VM:**
  ```bash
  cd ~/AI_gen_Platform && source .venv/bin/activate && python scripts/build_premium.py 5
  ```
- **Logs:** `journalctl -u quiet-story-api -f`

## Notes
- Services bind to `127.0.0.1` on purpose — reach them through the SSH tunnel,
  not by opening firewall ports.
- `.env` is **not** rsynced (secrets stay off the wire); create it on the VM.
- Re-push after local changes: just run `deploy/push_to_vm.sh` again (incremental).
