#!/usr/bin/env python3
"""
Analyze duplicate emails in the corpus.
Identifies emails with identical subject + body and provides statistics.
"""

import os
from pathlib import Path
from typing import Dict, List

import polars as pl

# Configuration
PARQUET_FILE = os.environ.get("ENRON_PARQUET_FILE", "enron.pq")
OUTPUT_DIR = Path("analysis")
DUPLICATE_ANALYSIS_FILE = OUTPUT_DIR / "duplicate_analysis.pq"
DUPES_MD_FILE = OUTPUT_DIR / "dupes.md"
BASE_URL = "https://mprosk.pythonanywhere.com/email?path="


def analyze_duplicates(df: pl.DataFrame) -> Dict:
    """Analyze duplicate emails in the corpus."""
    print("Analyzing duplicates...")
    
    total_emails = len(df)
    
    # Count duplicates by subject + body and get a sample path for each group
    duplicate_counts = (
        df.group_by(["subject", "body"])
        .agg([
            pl.count().alias("count"),
            pl.col("path").first().alias("sample_path"),  # Get first path from each group
        ])
        .filter(pl.col("count") > 1)
        .sort("count", descending=True)
    )
    
    num_unique_emails = df.select(["subject", "body"]).n_unique()
    num_duplicates = total_emails - num_unique_emails
    num_duplicate_groups = len(duplicate_counts)
    
    # Statistics
    stats = {
        "total_emails": total_emails,
        "unique_emails": num_unique_emails,
        "duplicate_emails": num_duplicates,
        "duplicate_groups": num_duplicate_groups,
        "duplication_rate": num_duplicates / total_emails if total_emails > 0 else 0,
    }
    
    # Top duplicate groups (for display)
    top_duplicates = duplicate_counts.head(20)
    
    return {
        "stats": stats,
        "duplicate_counts": duplicate_counts,
        "top_duplicates": top_duplicates,
    }


def print_duplicate_analysis(analysis: Dict) -> None:
    """Print duplicate analysis results."""
    stats = analysis["stats"]
    top_duplicates = analysis["top_duplicates"]
    
    print("\n" + "=" * 80)
    print("Duplicate Email Analysis")
    print("=" * 80)
    
    print(f"\nStatistics:")
    print(f"  Total emails: {stats['total_emails']:,}")
    print(f"  Unique emails (by subject + body): {stats['unique_emails']:,}")
    print(f"  Duplicate emails: {stats['duplicate_emails']:,}")
    print(f"  Duplicate groups: {stats['duplicate_groups']:,}")
    print(f"  Duplication rate: {stats['duplication_rate']:.1%}")


def save_top_duplicates_to_file(analysis: Dict, output_file: Path) -> None:
    """Save duplicated emails' subject lines to a markdown file (only groups with 10+ duplicates)."""
    all_duplicates = analysis["duplicate_counts"]
    
    # Filter to only include groups with 10 or more duplicates
    filtered_duplicates = all_duplicates.filter(pl.col("count") >= 10)
    
    print(f"\nSaving duplicate subject lines (10+ duplicates) to {output_file}...")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Duplicated Emails (10+ duplicates)\n\n")
        
        for i, row in enumerate(filtered_duplicates.iter_rows(named=True), 1):
            subject = row["subject"] or "(no subject)"
            count = row["count"]
            path = row.get("sample_path", "")
            
            # Create markdown link
            if path:
                url = f"{BASE_URL}{path}"
                subject_link = f"[{subject}]({url})"
            else:
                subject_link = subject
            
            f.write(f"{i}. [{count}] {subject_link}\n")
    
    print(f"  Saved {len(filtered_duplicates)} duplicate entries (out of {len(all_duplicates)} total) to {output_file}")


def main() -> None:
    """Main execution function."""
    print("=" * 80)
    print("Duplicate Email Analysis")
    print("=" * 80)
    
    # Load emails
    print(f"\nLoading emails from {PARQUET_FILE}...")
    df = pl.read_parquet(PARQUET_FILE)
    print(f"Loaded {len(df):,} emails")
    
    # Analyze duplicates
    analysis = analyze_duplicates(df)
    
    # Print results
    print_duplicate_analysis(analysis)
    
    # Save analysis
    print(f"\nSaving duplicate analysis to {DUPLICATE_ANALYSIS_FILE}...")
    analysis["duplicate_counts"].write_parquet(DUPLICATE_ANALYSIS_FILE)
    
    # Save top 200 duplicates to markdown file
    save_top_duplicates_to_file(analysis, DUPES_MD_FILE)
    
    print("\n" + "=" * 80)
    print("Analysis Complete!")
    print("=" * 80)
    print(f"\nRecommendation:")
    duplication_rate = analysis["stats"]["duplication_rate"]
    if duplication_rate > 0.1:  # More than 10% duplicates
        print(f"  High duplication rate ({duplication_rate:.1%}) detected.")



if __name__ == "__main__":
    main()

