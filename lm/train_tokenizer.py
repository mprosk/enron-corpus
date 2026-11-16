#!/usr/bin/env python3
"""
Train an Enron-only byte-level BPE tokenizer on the training split.

Byte-level means any byte sequence can be encoded (no unknown tokens), and the
GPT-2 pre-tokenizer regex keeps runs of punctuation together, so frequent
separator lines like "*****..." can be merged into a few tokens.

Writes lm/data/tokenizer/{tokenizer.json, tokenizer_config.json, special_tokens_map.json}
in a layout that Hugging Face / mlx-lm can load directly.
"""

import argparse
import json
from pathlib import Path

import polars as pl
from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers

from prepare_data import SPECIAL_TOKENS


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default="lm/data/emails.pq")
    ap.add_argument("--out-dir", default="lm/data/tokenizer")
    ap.add_argument("--vocab-size", type=int, default=16384)
    ap.add_argument("--min-frequency", type=int, default=2)
    args = ap.parse_args()

    texts = pl.read_parquet(args.input).filter(pl.col("split") == "train")["text"].to_list()
    print(f"Training on {len(texts):,} emails, vocab size {args.vocab_size:,}")

    tok = Tokenizer(models.BPE())
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False, use_regex=True)
    tok.decoder = decoders.ByteLevel()
    trainer = trainers.BpeTrainer(
        vocab_size=args.vocab_size,
        min_frequency=args.min_frequency,
        special_tokens=SPECIAL_TOKENS,  # ids 0..5, matched before pre-tokenization
        initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
        show_progress=True,
    )

    def batches(size: int = 1000):
        for i in range(0, len(texts), size):
            yield texts[i : i + size]

    tok.train_from_iterator(batches(), trainer=trainer, length=len(texts))

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tok.save(str(out / "tokenizer.json"))
    (out / "tokenizer_config.json").write_text(
        json.dumps(
            {
                "tokenizer_class": "PreTrainedTokenizerFast",
                "bos_token": "<|email|>",
                "eos_token": "<|end|>",
                "additional_special_tokens": SPECIAL_TOKENS[1:-1],
                "model_max_length": 1024,
                "clean_up_tokenization_spaces": False,
            },
            indent=2,
        )
    )
    (out / "special_tokens_map.json").write_text(
        json.dumps({"bos_token": "<|email|>", "eos_token": "<|end|>"}, indent=2)
    )
    print(f"Saved tokenizer to {out} ({tok.get_vocab_size():,} tokens)")


if __name__ == "__main__":
    main()
