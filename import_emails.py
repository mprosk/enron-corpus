import argparse
import os
import sqlite3
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Any, Dict, List, Tuple

import polars as pl

DATE_FORMAT_STRING = "%a, %d %b %Y %H:%M:%S %z"


def create_database_schema(db_path: str) -> None:
    """Create the database schema with proper indexes."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table with schema
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS emails (
            path TEXT PRIMARY KEY,
            date DATETIME NOT NULL,
            sender TEXT NOT NULL,
            recipient TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT
        )
    """
    )

    # Create indexes for faster queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON emails(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sender ON emails(sender)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recipient ON emails(recipient)")

    conn.commit()
    conn.close()


def write_dataframe_to_database(df: pl.DataFrame, db_path: str) -> None:
    """Create database schema and write DataFrame to SQLite database."""
    print(f"Writing to SQLite database: {db_path}")
    create_database_schema(db_path)
    connection_uri = f"sqlite:///{db_path}"
    df.write_database(
        table_name="emails", connection=connection_uri, if_table_exists="replace"
    )


def scan_maildir(maildir_path: Path) -> List[str]:
    """Recursively scan maildir directory and return list of all file paths."""
    file_list: List[str] = []

    for root, dirs, files in os.walk(maildir_path):
        for file in files:
            if file == ".DS_Store":
                continue
            file_path = os.path.join(root, file)
            file_list.append(file_path)

    return file_list


def parse_email_file(
    file_path: str, load_body: bool = True
) -> Tuple[str, datetime, str, str, str | None]:
    """
    Parse an email file and extract metadata.
    Returns: (subject, date, sender, recipient, body)
    """
    with open(file_path, mode="rb") as file:
        msg = BytesParser(policy=policy.default).parse(file)

    subject = msg.get("Subject", "[ERR]")
    if not subject:
        subject = "(no subject)"

    sender = msg.get("From", "[ERR]")
    recipient = msg.get("To", "[ERR]")

    date_str = msg.get("Date")
    if date_str:
        date = datetime.strptime(date_str, DATE_FORMAT_STRING)
    else:
        raise ValueError(f"No date found in {file_path}")

    body = None
    if load_body:
        payload = msg.get_payload(decode=True)
        if payload:
            body = payload.decode("utf-8")

    return subject, date, sender, recipient, body


def parse_email_file_wrapper(
    file_path: str,
) -> Tuple[str, str, datetime, str, str, str | None] | None:
    """
    Wrapper function for parallel processing that includes file_path in return value.
    Returns: (file_path, subject, date, sender, recipient, body) or None on error
    """
    try:
        subject, date, sender, recipient, body = parse_email_file(
            file_path, load_body=True
        )
        return (file_path, subject, date, sender, recipient, body)
    except Exception as e:  # noqa: BLE001
        print(f"Failed to parse {file_path}: {e}")
        return None


def parse_emails(
    file_list: List[str], progress_every: int = 1000, num_workers: int | None = None
) -> Dict[str, List[Any]]:
    """Process emails continuously and return a dictionary of lists."""
    paths: List[str] = []
    dates: List[datetime] = []
    subjects: List[str] = []
    senders: List[str] = []
    recipients: List[str] = []
    bodies: List[str | None] = []

    total: int = len(file_list)
    processed: int = 0

    executor = ProcessPoolExecutor(max_workers=num_workers)
    interrupted = False
    try:
        # Submit all tasks upfront for continuous processing
        future_to_file = {
            executor.submit(parse_email_file_wrapper, file_path): file_path
            for file_path in file_list
        }

        # Process results as they come in continuously
        for future in as_completed(future_to_file):
            result = future.result()
            if result is not None:
                file_path, subject, date, sender, recipient, body = result
                paths.append(file_path)
                dates.append(date)
                subjects.append(subject)
                senders.append(sender)
                recipients.append(recipient)
                bodies.append(body)

            processed += 1
            if (processed % progress_every) == 0 or processed == total:
                pct = round(processed / total * 100)
                print(f"\r{processed} of {total} ({pct}%)", end="", flush=True)
    except KeyboardInterrupt:
        print("\nInterrupted by user. Cancelling remaining tasks...")
        interrupted = True
        try:
            executor.shutdown(wait=False, cancel_futures=True)
        except TypeError:
            # Python < 3.9 doesn't support cancel_futures
            executor.shutdown(wait=False)
        raise
    finally:
        if not interrupted:
            executor.shutdown(wait=True)
            print()  # Newline after final progress update

    print("\nBuilding DataFrame...")

    # Build DataFrame only at the end after all processing is complete
    return {
        "path": paths,
        "date": dates,
        "subject": subjects,
        "sender": senders,
        "recipient": recipients,
        "body": bodies,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Enron email corpus to Parquet format"
    )
    parser.add_argument(
        "--maildir",
        type=str,
        default="maildir",
        help="Path to maildir directory (default: maildir)",
    )
    parser.add_argument(
        "--parquet",
        type=str,
        default="enron.pq",
        help="Output parquet file path (default: enron.pq)",
    )
    parser.add_argument(
        "--sql",
        type=str,
        default="enron.db",
        help="Output SQLite database file path (default: enron.db)",
    )
    parser.add_argument(
        "--load-pq",
        type=str,
        default=None,
        help="Path to existing parquet file to load into SQLite database",
    )
    default_workers = min(4, os.cpu_count() or 1)
    parser.add_argument(
        "--workers",
        type=int,
        default=default_workers,
        help=f"Number of worker processes (default: {default_workers})",
    )

    args = parser.parse_args()

    try:
        if args.load_pq:
            # Load existing parquet file and convert to SQLite
            print(f"Loading existing parquet file: {args.load_pq}")
            df = pl.read_parquet(args.load_pq)
            print(f"Loaded {len(df)} emails from parquet file")

            write_dataframe_to_database(df, args.sql)

            print("Done!")
            return

        # Normal flow: parse emails from maildir
        maildir_path = Path(args.maildir)

        print(f"Scanning {maildir_path.as_posix()}...")
        file_list: List[str] = scan_maildir(maildir_path)
        print(f"Found {len(file_list)} files")

        print(f"Parsing emails with {args.workers} workers...")
        emails: Dict[str, List[Any]] = parse_emails(file_list, num_workers=args.workers)

        print("Converting to DataFrame...")
        df: pl.DataFrame = pl.DataFrame(emails)

        print(f"Writing to Parquet file: {args.parquet}")
        df.write_parquet(args.parquet)

        write_dataframe_to_database(df, args.sql)

        print("Done!")
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
