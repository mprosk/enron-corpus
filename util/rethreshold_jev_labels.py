#!/usr/bin/env python3
"""Reapply jev_labels from probability columns at a new confidence threshold."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import polars as pl

DEFAULT_INPUT = Path(os.environ.get("ENRON_PARQUET_FILE", "enron_dedupe_jev.pq"))
PROB_PREFIX = "jev_probability_"


def discover_probability_columns(df: pl.DataFrame) -> list[tuple[str, str]]:
    """Return (column_name, label) pairs for jev_probability_* columns."""
    pairs = [
        (col, col[len(PROB_PREFIX) :])
        for col in df.columns
        if col.startswith(PROB_PREFIX)
    ]
    if not pairs:
        raise ValueError(
            f"No {PROB_PREFIX}* columns found. Is this a Jev-labeled parquet?"
        )
    return pairs


def reapply_labels(df: pl.DataFrame, threshold: float) -> pl.DataFrame:
    """Rebuild jev_labels and jev_label_threshold from stored probabilities."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0 and 1")

    pairs = discover_probability_columns(df)
    label_exprs = [
        pl.when(pl.col(col) >= threshold)
        .then(pl.lit(label))
        .otherwise(None)
        for col, label in pairs
    ]

    rebuilt = df.with_columns(
        pl.concat_list(label_exprs).list.drop_nulls().alias("_rethreshold_labels")
    ).with_columns(
        pl.when(pl.col("_rethreshold_labels").list.len() == 0)
        .then(pl.lit(["other"]))
        .otherwise(pl.col("_rethreshold_labels"))
        .alias("jev_labels"),
        pl.lit(threshold).cast(pl.Float64).alias("jev_label_threshold"),
    ).drop("_rethreshold_labels")

    return rebuilt


def tag_counts(df: pl.DataFrame) -> pl.DataFrame:
    """Count emails per applied tag."""
    return (
        df.select(pl.col("jev_labels").explode().alias("tag"))
        .drop_nulls()
        .group_by("tag")
        .len()
        .sort("len", descending=True)
    )


def write_output(df: pl.DataFrame, output_path: Path) -> None:
    """Write parquet atomically."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    df.write_parquet(temporary_path)
    temporary_path.replace(output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild the jev_labels column in a Jev-labeled parquet using a new "
            "confidence threshold. Labels with probability >= threshold are kept; "
            "if none qualify, ['other'] is applied. Also updates jev_label_threshold."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Input Jev parquet (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output parquet path (default: overwrite --input in place)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        required=True,
        help="Minimum probability for applying a label (0.0–1.0)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show before/after tag counts without writing a file",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not 0.0 <= args.threshold <= 1.0:
        raise SystemExit("--threshold must be between 0 and 1")

    input_path = args.input
    output_path = args.output or input_path

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    print(f"Reading {input_path}...")
    df = pl.read_parquet(input_path)

    if "jev_labels" not in df.columns:
        raise SystemExit("Input is missing jev_labels column")

    pairs = discover_probability_columns(df)
    old_threshold = None
    if "jev_label_threshold" in df.columns:
        old_threshold = float(df["jev_label_threshold"][0])

    print(f"Emails: {df.height:,}")
    print(f"Probability columns: {len(pairs)}")
    if old_threshold is not None:
        print(f"Current threshold: {old_threshold}")
    print(f"New threshold: {args.threshold}")

    before = tag_counts(df)
    print("\nTag counts before:")
    print(before)

    rebuilt = reapply_labels(df, args.threshold)
    after = tag_counts(rebuilt)
    print("\nTag counts after:")
    print(after)

    if args.dry_run:
        print("\nDry run — no file written.")
        return

    print(f"\nWriting {output_path}...")
    write_output(rebuilt, output_path)
    print("Done.")


if __name__ == "__main__":
    main()
