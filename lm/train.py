#!/usr/bin/env python3
"""
Train a small Llama-style model from scratch on the packed Enron token stream (MLX).

Training windows are random 1024-token slices of lm/data/train.bin, so emails are
packed back to back and long emails are seen in full across windows.

A run directory (lm/runs/<name>/) holds:
  config.json, model.safetensors, tokenizer*.json   -> loadable with mlx_lm.load()
  optimizer.safetensors, train_state.json            -> for --resume
  log.csv                                            -> step, loss, val loss, lr, tok/s
  samples.txt                                        -> generations from fixed prompts over time

Example:
  python lm/train.py --preset tiny --name smoke --tokens 20e6

Fine-tuning a pretrained model instead (plain-header data from encode_data.py --format plain):
  python lm/train.py --name smol --init-from HuggingFaceTB/SmolLM2-135M --data-dir lm/data/smol \
      --format plain --lr 3e-4
"""

import argparse
import csv
import json
import math
import shutil
import time
from pathlib import Path

import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
import numpy as np
from mlx.utils import tree_flatten, tree_map, tree_unflatten
from mlx_lm.models import llama
from tokenizers import Tokenizer

RUNS = Path("lm/runs")

PRESETS = {
    # name: (hidden, layers, heads, ffn)
    "tiny": (256, 4, 4, 704),
    "small": (512, 8, 8, 1408),
    "medium": (768, 12, 12, 2048),
}

SUBJECTS = ["Re: holiday party", "California", "URGENT: document retention", "the ghosts on the trading floor"]
SAMPLE_PROMPTS = {
    "special": [f"<|email|><|subject|>{s}\n" for s in SUBJECTS] + ["<|email|>"],
    "plain": [f"Subject: {s}\nFrom:" for s in SUBJECTS] + ["Subject:"],
}
END_TOKEN = {"special": "<|end|>", "plain": "<|endoftext|>"}


def model_config(preset: str, vocab_size: int, context: int) -> dict:
    hidden, layers, heads, ffn = PRESETS[preset]
    return {
        "model_type": "llama",
        "hidden_size": hidden,
        "num_hidden_layers": layers,
        "num_attention_heads": heads,
        "num_key_value_heads": heads,
        "intermediate_size": ffn,
        "rms_norm_eps": 1e-5,
        "vocab_size": vocab_size,
        "max_position_embeddings": context,
        "rope_theta": 10000.0,
        "tie_word_embeddings": True,
    }


def pretrained_model(config: dict) -> nn.Module:
    """Empty model of whatever architecture a pretrained config names (llama, qwen2, ...)."""
    from mlx_lm.utils import _get_classes

    model_cls, args_cls = _get_classes(config)
    return model_cls(args_cls.from_dict(config))


def build_model(config: dict) -> llama.Model:
    model = llama.Model(llama.ModelArgs.from_dict(config))
    # small-init for a from-scratch run: N(0, 0.02), output projections scaled by depth
    std = 0.02
    out_std = std / math.sqrt(2 * config["num_hidden_layers"])
    params = {}
    for k, v in tree_flatten(model.parameters()):
        if k.endswith("norm.weight"):
            params[k] = v
        elif k.endswith(("o_proj.weight", "down_proj.weight")):
            params[k] = mx.random.normal(v.shape) * out_std
        else:
            params[k] = mx.random.normal(v.shape) * std
    model.update(tree_unflatten(list(params.items())))
    return model


def count_params(model: nn.Module) -> tuple[int, int]:
    flat = tree_flatten(model.parameters())
    total = sum(v.size for _, v in flat)
    emb = sum(v.size for k, v in flat if "embed_tokens" in k)
    return total, emb


def resolve_pretrained(name: str) -> Path:
    """A local model dir, or a Hugging Face repo id (downloaded on first use)."""
    if Path(name).exists():
        return Path(name)
    from huggingface_hub import snapshot_download

    return Path(snapshot_download(name, allow_patterns=["*.json", "*.safetensors", "*.txt"]))


class Batches:
    def __init__(self, data_dir: Path, split: str, context: int, batch_size: int, seed: int):
        meta = data_dir / "meta.json"
        dtype = json.loads(meta.read_text())["dtype"] if meta.exists() else "uint16"
        self.data = np.memmap(data_dir / f"{split}.bin", dtype=dtype, mode="r")
        self.context, self.batch_size = context, batch_size
        self.rng = np.random.default_rng(seed)

    def sample(self, rng=None) -> tuple[mx.array, mx.array]:
        rng = rng or self.rng
        starts = rng.integers(0, len(self.data) - self.context - 1, size=self.batch_size)
        chunk = np.stack([self.data[s : s + self.context + 1] for s in starts]).astype(np.int32)
        return mx.array(chunk[:, :-1]), mx.array(chunk[:, 1:])


def loss_fn(model, x, y):
    logits = model(x).astype(mx.float32)
    return nn.losses.cross_entropy(logits, y, reduction="mean")


def generate(model, prompt_ids: list[int], max_tokens: int, temp: float, end_id: int, seed: int) -> list[int]:
    from mlx_lm.models.cache import make_prompt_cache

    key = mx.random.key(seed)
    cache = make_prompt_cache(model)
    logits = model(mx.array(prompt_ids)[None], cache=cache)[:, -1, :]
    out = []
    for _ in range(max_tokens):
        key, sub = mx.random.split(key)
        tok = mx.random.categorical(logits / temp, key=sub).item()
        if tok == end_id:
            break
        out.append(tok)
        logits = model(mx.array([[tok]]), cache=cache)[:, -1, :]
    return out


def save_checkpoint(run: Path, model, optimizer, state: dict) -> None:
    mx.save_safetensors(str(run / "model.safetensors"), dict(tree_flatten(model.parameters())))
    mx.save_safetensors(str(run / "optimizer.safetensors"), dict(tree_flatten(optimizer.state)))
    (run / "train_state.json").write_text(json.dumps(state, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--preset", choices=PRESETS, default="tiny")
    ap.add_argument("--context", type=int, default=1024)
    ap.add_argument("--batch-size", type=int, default=16, help="sequences per micro-batch")
    ap.add_argument("--grad-accum", type=int, default=1)
    ap.add_argument("--tokens", type=float, default=20e6, help="total training tokens")
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--min-lr-frac", type=float, default=0.1)
    ap.add_argument("--warmup-steps", type=int, default=200)
    ap.add_argument("--weight-decay", type=float, default=0.1)
    ap.add_argument("--eval-every", type=int, default=250)
    ap.add_argument("--eval-batches", type=int, default=20)
    ap.add_argument("--sample-every", type=int, default=1000)
    ap.add_argument("--ckpt-every", type=int, default=1000)
    ap.add_argument("--log-every", type=int, default=25)
    ap.add_argument("--max-steps", type=int, default=None, help="stop early (for benchmarking)")
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--init-from", help="start from pretrained weights: HF repo id or local dir (ignores --preset)")
    ap.add_argument("--data-dir", default="lm/data", help="dir with {train,val}.bin")
    ap.add_argument("--format", choices=["special", "plain"], default="special",
                    help="email layout of the data: our special tokens, or plain text headers")
    args = ap.parse_args()

    run = RUNS / args.name

    if args.resume:
        saved = json.loads((run / "train_state.json").read_text())
        args = argparse.Namespace(**{**vars(args), **saved["args"], "resume": True, "max_steps": args.max_steps})
        config = json.loads((run / "config.json").read_text())
    else:
        if run.exists() and any(run.iterdir()):
            raise SystemExit(f"{run} already exists; use --resume or a new --name")
        run.mkdir(parents=True, exist_ok=True)
        if args.init_from:
            src = resolve_pretrained(args.init_from)
            config = json.loads((src / "config.json").read_text())
            tok_files = [f for f in src.iterdir() if f.suffix in (".json", ".txt") and f.name != "config.json"]
        else:
            vocab = Tokenizer.from_file("lm/data/tokenizer/tokenizer.json").get_vocab_size()
            config = model_config(args.preset, vocab, args.context)
            tok_files = list(Path("lm/data/tokenizer").iterdir())
        (run / "config.json").write_text(json.dumps(config, indent=2))
        for f in tok_files:
            shutil.copy(f, run / f.name)

    data_dir = Path(args.data_dir)
    tokenizer = Tokenizer.from_file(str(run / "tokenizer.json"))
    end_id = tokenizer.token_to_id(END_TOKEN[args.format])

    tokens_per_step = args.batch_size * args.grad_accum * args.context
    total_steps = int(args.tokens // tokens_per_step)

    mx.random.seed(args.seed)
    model = pretrained_model(config) if args.init_from else build_model(config)
    if args.init_from and not args.resume:
        weights = {}
        for f in sorted(resolve_pretrained(args.init_from).glob("*.safetensors")):
            weights.update(mx.load(str(f)))
        model.load_weights(list(model.sanitize(weights).items()))
    model.set_dtype(mx.float32)
    n_params, n_emb = count_params(model)

    warmup = min(args.warmup_steps, max(1, total_steps // 10))
    schedule = optim.join_schedules(
        [
            optim.linear_schedule(0.0, args.lr, warmup),
            optim.cosine_decay(args.lr, max(1, total_steps - warmup), args.lr * args.min_lr_frac),
        ],
        [warmup],
    )
    optimizer = optim.AdamW(learning_rate=schedule, betas=[0.9, 0.95], weight_decay=args.weight_decay)

    start_step = 0
    if args.resume:
        model.load_weights(str(run / "model.safetensors"))
        optimizer.init(model.trainable_parameters())
        optimizer.state = tree_unflatten(list(mx.load(str(run / "optimizer.safetensors")).items()))
        start_step = saved["step"]
        print(f"Resuming {run} from step {start_step}")

    train = Batches(data_dir, "train", args.context, args.batch_size, seed=args.seed + start_step)
    val = Batches(data_dir, "val", args.context, args.batch_size, seed=0)
    epochs = args.tokens / len(train.data)
    print(
        f"Model: {args.init_from or args.preset}, {n_params / 1e6:.1f}M params ({(n_params - n_emb) / 1e6:.1f}M non-embedding)\n"
        f"Training: {total_steps:,} steps x {tokens_per_step:,} tokens = {args.tokens / 1e6:.0f}M tokens "
        f"({epochs:.2f} epochs of {len(train.data) / 1e6:.0f}M)"
    )

    loss_and_grad = nn.value_and_grad(model, loss_fn)
    state = [model.state, optimizer.state]

    # weights must be declared as compile inputs, or they're captured as constants
    grad_step = mx.compile(lambda x, y: loss_and_grad(model, x, y), inputs=model.state, outputs=model.state)

    def train_step():
        loss, grads = None, None
        for _ in range(args.grad_accum):
            l, g = grad_step(*train.sample())
            loss = l if loss is None else loss + l
            grads = g if grads is None else tree_map(mx.add, grads, g)
            # evaluate now, or MLX keeps every micro-batch's activations alive until the update
            mx.eval(grads, loss)
        if args.grad_accum > 1:
            grads = tree_map(lambda g: g / args.grad_accum, grads)
            loss = loss / args.grad_accum
        grads, gnorm = optim.clip_grad_norm(grads, 1.0)
        optimizer.update(model, grads)
        mx.eval(state, loss, gnorm)
        return loss.item(), gnorm.item()

    def evaluate() -> float:
        rng = np.random.default_rng(0)
        losses = [loss_fn(model, *val.sample(rng)).item() for _ in range(args.eval_batches)]
        return float(np.mean(losses))

    def write_samples(step: int) -> None:
        with open(run / "samples.txt", "a") as f:
            f.write(f"\n{'=' * 30} step {step:,} {'=' * 30}\n")
            for i, p in enumerate(SAMPLE_PROMPTS[args.format]):
                ids = tokenizer.encode(p, add_special_tokens=False).ids
                out = generate(model, ids, max_tokens=300, temp=0.8, end_id=end_id, seed=i)
                f.write("\n" + tokenizer.decode(ids + out, skip_special_tokens=False) + "\n" + "-" * 40 + "\n")

    def checkpoint(step: int) -> None:
        save_checkpoint(run, model, optimizer, {"step": step, "args": vars(args)})

    log_path = run / "log.csv"
    new_log = not log_path.exists()
    log_file = open(log_path, "a", newline="")
    log = csv.writer(log_file)
    if new_log:
        log.writerow(["step", "tokens", "train_loss", "val_loss", "lr", "grad_norm", "tok_per_s", "elapsed_s"])

    if args.init_from and start_step == 0:
        base_val = evaluate()
        print(f"step      0  val {base_val:.3f}  (pretrained model before fine-tuning)", flush=True)
        log.writerow([0, 0, "", f"{base_val:.4f}", "", "", "", 0])
        write_samples(0)

    end_step = total_steps if args.max_steps is None else min(total_steps, start_step + args.max_steps)
    t0 = time.time()
    t_last, losses = time.time(), []
    step = start_step
    try:
        for step in range(start_step + 1, end_step + 1):
            loss, gnorm = train_step()
            losses.append(loss)
            if step % args.log_every == 0 or step == end_step:
                dt = time.time() - t_last
                tps = len(losses) * tokens_per_step / dt
                lr = float(schedule(step))
                remaining = (end_step - step) * tokens_per_step / tps
                val_loss = evaluate() if (step % args.eval_every == 0 or step == end_step) else None
                msg = (
                    f"step {step:>6,}/{end_step:,}  loss {np.mean(losses):.3f}"
                    + (f"  val {val_loss:.3f}" if val_loss is not None else "")
                    + f"  lr {lr:.2e}  gnorm {gnorm:.2f}  {tps:,.0f} tok/s  eta {remaining / 60:.0f}m"
                )
                print(msg, flush=True)
                log.writerow(
                    [step, step * tokens_per_step, f"{np.mean(losses):.4f}",
                     "" if val_loss is None else f"{val_loss:.4f}", f"{lr:.3e}", f"{gnorm:.3f}",
                     f"{tps:.0f}", f"{time.time() - t0:.0f}"]
                )
                log_file.flush()
                t_last, losses = time.time(), []
            if step % args.sample_every == 0:
                write_samples(step)
            if step % args.ckpt_every == 0:
                checkpoint(step)
    except KeyboardInterrupt:
        print("\nInterrupted; saving checkpoint")
    checkpoint(step)
    write_samples(step)
    log_file.close()
    print(f"Done at step {step:,} in {(time.time() - t0) / 60:.1f} min. Run dir: {run}")


if __name__ == "__main__":
    main()
