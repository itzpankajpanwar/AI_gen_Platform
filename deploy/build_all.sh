#!/usr/bin/env bash
# Build all 15 chapters on the VM, one after another. Continues past a failed
# chapter so one problem never blocks the rest. Run detached; logs to ~/build_all.log.
cd "$HOME/AI_gen_Platform"
source .venv/bin/activate
echo "########## FULL BUILD START $(date) ##########"
for N in $(seq 1 15); do
  echo "===== CHAPTER $N  START $(date '+%H:%M:%S') ====="
  if python scripts/build_premium.py "$N"; then
    echo ">>> CH$N DONE $(date '+%H:%M:%S')"
  else
    echo ">>> CH$N FAILED $(date '+%H:%M:%S')"
  fi
done
echo "########## FULL BUILD COMPLETE $(date) ##########"
ls -la samples/film_premium/*.mp4
