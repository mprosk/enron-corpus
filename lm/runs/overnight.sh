#!/bin/bash
# Overnight chain: small, then medium. Run from the repo root.
set -e
cd "$(dirname "$0")/../.."
source venv/bin/activate
echo "[$(date)] starting small"
python lm/train.py --name small --preset small --batch-size 16 --grad-accum 1 --tokens 180e6 --lr 1e-3 > lm/runs/small.stdout.log 2>&1
echo "[$(date)] small done; starting medium"
python lm/train.py --name medium --preset medium --batch-size 8 --grad-accum 2 --tokens 240e6 --lr 6e-4 > lm/runs/medium.stdout.log 2>&1
echo "[$(date)] medium done"
