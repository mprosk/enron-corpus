#!/usr/bin/env python3
"""
Encode the formatted emails into flat token arrays for training.

Writes, per split:
  lm/data/{split}.bin         token ids (uint16, or uint32 for vocabs > 65536), all emails concatenated
  lm/data/meta.json           {"dtype": ..., "format": ...}
  lm/data/{split}_starts.npy  int64 offset of each email's first token
                              (so training can begin windows at an email start)
and prints token statistics.

--format plain re-renders each email with ordinary text headers
("Subject: ...\nFrom: ...\nTo: ...\n\n<body>") and ends it with the tokenizer's
end-of-text token, for fine-tuning a pretrained model with its own tokenizer:
  python lm/encode_data.py --format plain --tokenizer <hf_model_dir>/tokenizer.json \
      --eos "<|endoftext|>" --out-dir lm/data/smol
"""

import argparse
import json
import re
from pathlib import Path

import numpy as np
import polars as pl
from tokenizers import Tokenizer


PLAIN = [
    (re.compile(r"^<\|email\|><\|subject\|>"), "Subject: "),
    (re.compile(r"\n<\|from\|>"), "\nFrom: "),
    (re.compile(r"\n<\|to\|>"), "\nTo: "),
    (re.compile(r"\n<\|body\|>\n"), "\n\n"),
    (re.compile(r"\n<\|end\|>$"), "\n"),
]


def to_plain(text: str) -> str:
    for pat, rep in PLAIN:
        text, n = pat.subn(rep, text, count=1)
        assert n == 1, f"unexpected email layout: {text[:200]!r}"
    return text


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default="lm/data/emails.pq")
    ap.add_argument("--tokenizer", default="lm/data/tokenizer/tokenizer.json")
    ap.add_argument("--out-dir", default="lm/data")
    ap.add_argument("--format", choices=["special", "plain"], default="special")
    ap.add_argument("--eos", help="end-of-email token appended in plain format")
    args = ap.parse_args()

    tok = Tokenizer.from_file(args.tokenizer)
    # uint16 halves the file size; fall back to uint32 for big vocabs (e.g. Qwen's 152k)
    dtype = np.uint16 if tok.get_vocab_size() <= 65536 else np.uint32
    eos = []
    if args.format == "plain":
        assert args.eos, "--format plain needs --eos"
        eos = [tok.token_to_id(args.eos)]
        assert eos[0] is not None, f"{args.eos} not in tokenizer"
    df = pl.read_parquet(args.input)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "meta.json").write_text(json.dumps({"dtype": np.dtype(dtype).name, "format": args.format}))

    for split in ["train", "val"]:
        texts = df.filter(pl.col("split") == split)["text"].to_list()
        if args.format == "plain":
            texts = [to_plain(t) for t in texts]
        lengths, chunks = [], []
        for i in range(0, len(texts), 5000):
            for enc in tok.encode_batch(texts[i : i + 5000], add_special_tokens=False):
                ids = enc.ids + eos
                lengths.append(len(ids))
                chunks.append(np.asarray(ids, dtype=dtype))
        lengths = np.asarray(lengths)
        ids = np.concatenate(chunks)
        starts = np.concatenate([[0], np.cumsum(lengths)[:-1]]).astype(np.int64)
        ids.tofile(out / f"{split}.bin")
        np.save(out / f"{split}_starts.npy", starts)

        chars = sum(len(t) for t in texts)
        print(f"\n{split}: {len(texts):,} emails -> {ids.size:,} tokens ({chars / ids.size:.2f} chars/token)")
        p = np.percentile(lengths, [50, 90, 99])
        print(f"  tokens per email: median {p[0]:.0f}, p90 {p[1]:.0f}, p99 {p[2]:.0f}, max {lengths.max():,}")
        for limit in (512, 1024, 2048):
            over = lengths > limit
            print(
                f"  emails > {limit} tokens: {over.mean():.1%} "
                f"(holding {(lengths[over] - limit).sum() / ids.size:.1%} of tokens beyond the limit)"
            )


if __name__ == "__main__":
    main()
