#!/usr/bin/env python3
"""
Encode the formatted emails into flat token arrays for training.

Writes, per split:
  lm/data/{split}.bin         uint16 token ids, all emails concatenated
  lm/data/{split}_starts.npy  int64 offset of each email's first token
                              (so training can begin windows at an email start)
and prints token statistics.
"""

import argparse
from pathlib import Path

import numpy as np
import polars as pl
from tokenizers import Tokenizer


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default="lm/data/emails.pq")
    ap.add_argument("--tokenizer", default="lm/data/tokenizer/tokenizer.json")
    ap.add_argument("--out-dir", default="lm/data")
    args = ap.parse_args()

    tok = Tokenizer.from_file(args.tokenizer)
    assert tok.get_vocab_size() <= 65536, "uint16 storage needs vocab <= 65536"
    df = pl.read_parquet(args.input)
    out = Path(args.out_dir)

    for split in ["train", "val"]:
        texts = df.filter(pl.col("split") == split)["text"].to_list()
        lengths, chunks = [], []
        for i in range(0, len(texts), 5000):
            for enc in tok.encode_batch(texts[i : i + 5000], add_special_tokens=False):
                ids = enc.ids
                lengths.append(len(ids))
                chunks.append(np.asarray(ids, dtype=np.uint16))
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
