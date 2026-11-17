#!/bin/bash
# Fine-tune SmolLM2-135M for one epoch, then Qwen2.5-0.5B for whatever fits before ~3:45 PM.
set -e
cd "$(dirname "$0")/../.."
source venv/bin/activate

echo "[$(date)] starting smol135"
python lm/train.py --name smol135 --init-from HuggingFaceTB/SmolLM2-135M --data-dir lm/data/smol --format plain \
    --lr 3e-4 --tokens 130e6 --batch-size 4 --grad-accum 4 --sample-every 500 --ckpt-every 500 \
    > lm/runs/smol135.stdout.log 2>&1
echo "[$(date)] smol135 done"

# size the Qwen run to end by 15:45 today at a conservative 1,300 tok/s (measured ~1,440)
TOKENS=$(python -c "
import datetime as d
now = d.datetime.now()
secs = (now.replace(hour=15, minute=45, second=0) - now).total_seconds()
print(int(max(secs, 0) * 1300))")
if [ "$TOKENS" -lt 5000000 ]; then
    echo "[$(date)] only $TOKENS tokens of time left; skipping qwen05"
    exit 0
fi
echo "[$(date)] starting qwen05 with $TOKENS tokens"
python lm/train.py --name qwen05 --init-from Qwen/Qwen2.5-0.5B --data-dir lm/data/qwen --format plain \
    --lr 1e-4 --warmup-steps 100 --tokens "$TOKENS" --batch-size 2 --grad-accum 8 --sample-every 500 --ckpt-every 500 \
    > lm/runs/qwen05.stdout.log 2>&1
echo "[$(date)] qwen05 done"
