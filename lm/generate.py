#!/usr/bin/env python3
"""
Generate Enron emails from a trained model.

Give it a subject line and the model writes the rest: sender, recipients, body.
You can also pin the sender, recipients, or the opening of the body and let the
model continue from there.

Examples:
  python lm/generate.py "Re: holiday party"
  python lm/generate.py "FW: haunted spreadsheet" -n 3 --temp 0.9
  python lm/generate.py "lunch?" --from john.arnold@enron.com --to jennifer.fraser@enron.com
  python lm/generate.py "URGENT" --body "Please shred" --model small --seed 42
  python lm/generate.py            # no subject: the model invents one too
"""

import argparse
import random
import sys
import time
from pathlib import Path

import mlx.core as mx
from mlx_lm import load
from mlx_lm.generate import stream_generate
from mlx_lm.sample_utils import make_logits_processors, make_sampler

RUNS = Path(__file__).resolve().parent / "runs"
CONTEXT = 1024  # the models were trained on 1024-token windows

# How the special tokens are shown in the default (pretty) output.
PRETTY = {
    "<|email|>": "",
    "<|subject|>": "Subject: ",
    "<|from|>": "From: ",
    "<|to|>": "To: ",
    "<|body|>": "",
    "<|end|>": "",
}


def resolve_model(name: str) -> Path:
    path = Path(name)
    if not path.exists():
        path = RUNS / name
    if not (path / "model.safetensors").exists():
        available = sorted(p.name for p in RUNS.iterdir() if (p / "model.safetensors").exists())
        sys.exit(f"No model at '{name}'. Available runs: {', '.join(available)}")
    return path


def build_prompt(subject, sender, to, body) -> str:
    """Prefill the headers in order; the model continues from the first one left blank."""
    fields = [("subject", subject), ("from", sender), ("to", to), ("body", body)]
    given = [v is not None for _, v in fields]
    # A field can only be prefilled if every field before it is too.
    first_missing = given.index(False) if False in given else len(fields)
    if any(given[first_missing:]):
        missing = fields[first_missing][0]
        later = [n for (n, v) in fields[first_missing:] if v is not None]
        sys.exit(f"--{later[0]} needs --{missing} too (the email is written in order: subject, from, to, body)")

    prompt = "<|email|><|subject|>"
    if subject is None:
        return prompt
    prompt += f"{subject}\n<|from|>"
    if sender is None:
        return prompt
    prompt += f"{sender}\n<|to|>"
    if to is None:
        return prompt
    prompt += f"{to}\n<|body|>\n"
    if body is None:
        return prompt
    return prompt + body


def render(text: str, raw: bool) -> str:
    if raw:
        return text
    for tok, label in PRETTY.items():
        text = text.replace(tok, label)
    return text


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("subject", nargs="?", help="subject line (omit to let the model invent one)")
    ap.add_argument("--from", dest="sender", metavar="ADDR", help="fix the sender address")
    ap.add_argument("--to", metavar="ADDRS", help="fix the recipients (comma-separated); needs --from")
    ap.add_argument("--body", metavar="TEXT", help="start the body with this text; needs --from and --to")

    g = ap.add_argument_group("model")
    g.add_argument("-m", "--model", default="medium", help="run name in lm/runs/ or a path (default: medium)")

    g = ap.add_argument_group("sampling")
    g.add_argument("-t", "--temp", type=float, default=0.8, help="temperature; higher = weirder, 0 = greedy (default: 0.8)")
    g.add_argument("--top-p", type=float, default=0.0, help="nucleus sampling cutoff, e.g. 0.95 (default: off)")
    g.add_argument("--top-k", type=int, default=0, help="sample only from the k likeliest tokens (default: off)")
    g.add_argument("--min-p", type=float, default=0.0, help="drop tokens below min_p x the top token's prob (default: off)")
    g.add_argument("--rep-penalty", type=float, default=None,
                   help="penalize recently used tokens, e.g. 1.1; curbs loops like 'pulp and paper, metals...' (default: off)")
    g.add_argument("--rep-context", type=int, default=64, help="how many recent tokens the penalty looks at (default: 64)")
    g.add_argument("--max-tokens", type=int, default=600, help="stop after this many new tokens (default: 600)")
    g.add_argument("-s", "--seed", type=int, default=None, help="random seed for reproducible output (default: random)")

    g = ap.add_argument_group("output")
    g.add_argument("-n", "--count", type=int, default=1, help="number of emails to generate (default: 1)")
    g.add_argument("--raw", action="store_true", help="show the raw special tokens (<|from|> etc.) instead of headers")
    g.add_argument("--no-stream", action="store_true", help="print each email when finished instead of token by token")
    g.add_argument("-q", "--quiet", action="store_true", help="hide the per-email stats line")
    args = ap.parse_args()

    model, tok = load(str(resolve_model(args.model)))
    prompt = build_prompt(args.subject, args.sender, args.to, args.body)
    prompt_ids = tok.encode(prompt, add_special_tokens=False)

    max_tokens = args.max_tokens
    if len(prompt_ids) + max_tokens > CONTEXT:
        max_tokens = max(CONTEXT - len(prompt_ids), 1)
        print(f"(capping --max-tokens at {max_tokens}: the model only saw {CONTEXT}-token windows in training)",
              file=sys.stderr)

    sampler = make_sampler(temp=args.temp, top_p=args.top_p, min_p=args.min_p, top_k=args.top_k)
    processors = make_logits_processors(repetition_penalty=args.rep_penalty, repetition_context_size=args.rep_context)
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    for i in range(args.count):
        seed = base_seed + i
        mx.random.seed(seed)
        if args.count > 1:
            print(f"{'=' * 30} email {i + 1}/{args.count} {'=' * 30}")

        ids, shown, n_new, finished = list(prompt_ids), "", 0, False
        start = time.perf_counter()
        for resp in stream_generate(model, tok, prompt_ids, max_tokens=max_tokens,
                                    sampler=sampler, logits_processors=processors):
            n_new += 1
            if resp.token in tok.eos_token_ids:
                finished = True
                break
            ids.append(resp.token)
            if not args.no_stream:
                # Decode the whole email each step and print only what's new; avoids split characters.
                text = render(tok.decode(ids, skip_special_tokens=False), args.raw)
                print(text[len(shown):], end="", flush=True)
                shown = text
        elapsed = time.perf_counter() - start

        text = render(tok.decode(ids, skip_special_tokens=False), args.raw)
        if args.no_stream:
            print(text, end="")
        if args.raw and finished:
            print("<|end|>", end="")
        print(flush=True)
        if not args.quiet:
            note = "" if finished else ", hit --max-tokens"
            print(f"[seed {seed}, {n_new} tokens in {elapsed:.2f}s, {n_new / elapsed:.0f} tok/s{note}]", file=sys.stderr)
        if i < args.count - 1:
            print()


if __name__ == "__main__":
    main()
