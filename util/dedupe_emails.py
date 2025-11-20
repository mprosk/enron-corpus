#!/usr/bin/env python3
"""
Deduplicate the email corpus.
Creates a deduplicated version while preserving metadata about duplicates.
"""

import os
from pathlib import Path
from typing import Optional

import polars as pl

# Configuration
PARQUET_FILE = os.environ.get("ENRON_PARQUET_FILE", "enron.pq")
OUTPUT_DIR = Path("analysis")
DEDUPLICATED_FILE = OUTPUT_DIR / "enron_dedupe.pq"

# Deduplication strategy
KEEP_STRATEGY = "first"  # Options: "first", "last", "most_recent"
SORT_BY_DATE = True  # Sort by date before deduplicating


def deduplicate_emails(
    df: pl.DataFrame,
    keep_strategy: str = "first",
    sort_by_date: bool = True,
) -> pl.DataFrame:
    """
    Deduplicate emails by subject + body.
    
    Args:
        df: Input dataframe
        keep_strategy: "first", "last", or "most_recent" (keeps earliest/latest date)
        sort_by_date: Whether to sort by date before deduplicating
    
    Returns:
        Deduplicated dataframe with additional metadata columns
    """
    print("Deduplicating emails...")
    
    original_count = len(df)
    
    # Sort by date if requested
    if sort_by_date:
        if keep_strategy == "most_recent":
            df_sorted = df.sort("date", descending=True)
            keep_strategy = "first"  # After sorting desc, "first" = most recent
        elif keep_strategy == "first":
            df_sorted = df.sort("date", descending=False)  # Earliest first
        else:  # "last"
            df_sorted = df.sort("date", descending=True)  # Latest first
    else:
        df_sorted = df
    
    # Count duplicates before deduplicating
    duplicate_counts = (
        df.group_by(["subject", "body"])
        .agg(pl.len().alias("duplicate_count"))
    )
    
    # Deduplicate
    df_dedup = df_sorted.unique(subset=["subject", "body"], keep=keep_strategy)
    
    # Add duplicate count metadata
    df_dedup = df_dedup.join(
        duplicate_counts,
        on=["subject", "body"],
        how="left",
    )
    
    # Add metadata about senders/recipients for duplicates
    sender_recipient_info = (
        df.group_by(["subject", "body"])
        .agg([
            pl.col("sender").n_unique().alias("unique_senders"),
            pl.col("recipient").n_unique().alias("unique_recipients"),
            pl.col("sender").alias("all_senders"),  # Automatically creates list in group_by
            pl.col("recipient").alias("all_recipients"),  # Automatically creates list in group_by
        ])
    )
    
    df_dedup = df_dedup.join(
        sender_recipient_info,
        on=["subject", "body"],
        how="left",
    )
    
    deduplicated_count = len(df_dedup)
    removed_count = original_count - deduplicated_count
    
    print(f"  Original emails: {original_count:,}")
    print(f"  Deduplicated emails: {deduplicated_count:,}")
    print(f"  Removed duplicates: {removed_count:,}")
    print(f"  Reduction: {removed_count/original_count:.1%}")
    
    return df_dedup


def main() -> None:
    """Main execution function."""
    print("=" * 80)
    print("Deduplicate Email Corpus")
    print("=" * 80)
    
    # Check if deduplicated file already exists
    if DEDUPLICATED_FILE.exists():
        response = input(
            f"\nDeduplicated file already exists: {DEDUPLICATED_FILE}\n"
            "Overwrite? (y/N): "
        )
        if response.lower() != "y":
            print("Aborted.")
            return
    
    # Load emails
    print(f"\nLoading emails from {PARQUET_FILE}...")
    df = pl.read_parquet(PARQUET_FILE)
    print(f"Loaded {len(df):,} emails")
    
    # Deduplicate
    df_dedup = deduplicate_emails(
        df,
        keep_strategy=KEEP_STRATEGY,
        sort_by_date=SORT_BY_DATE,
    )
    
    # Save deduplicated corpus
    print(f"\nSaving deduplicated corpus to {DEDUPLICATED_FILE}...")
    df_dedup.write_parquet(DEDUPLICATED_FILE)
    
    print("\n" + "=" * 80)
    print("Deduplication Complete!")
    print("=" * 80)
    print(f"\nOutput file: {DEDUPLICATED_FILE}")
    print(f"\nNew columns added:")
    print(f"  - duplicate_count: How many times this email appeared")
    print(f"  - unique_senders: Number of different senders")
    print(f"  - unique_recipients: Number of different recipients")
    print(f"  - all_senders: List of all senders (for duplicates)")
    print(f"  - all_recipients: List of all recipients (for duplicates)")
    print(f"\nTo use deduplicated corpus:")
    print(f"  export ENRON_PARQUET_FILE={DEDUPLICATED_FILE}")


if __name__ == "__main__":
    main()

