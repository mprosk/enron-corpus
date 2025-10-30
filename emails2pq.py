import pickle
from datetime import datetime
from typing import List

import polars as pl

from enronmail.utils import EnronEmail


def build_dataframe(file_list: List[str], progress_every: int = 1000) -> pl.DataFrame:
    paths: List[str] = []
    dates: List[datetime] = []
    subjects: List[str] = []
    senders: List[str] = []
    recipients: List[str] = []
    bodies: List[str | None] = []

    total: int = len(file_list)
    for i, file_path in enumerate(file_list, start=1):
        try:
            msg = EnronEmail(file_path, True)
            paths.append(file_path)
            dates.append(msg.date)
            subjects.append(msg.subject)
            senders.append(msg.sender)
            recipients.append(msg.recip)
            bodies.append(msg.body)
        except Exception as e:  # noqa: BLE001
            print(f"Failed to parse {file_path}: {e}")
            continue

        if (i % progress_every) == 0 or i == total:
            pct = round(i / total * 100)
            print(f"{i} of {total} ({pct}%)")

    return pl.DataFrame(
        {
            "path": paths,
            "date": dates,
            "subject": subjects,
            "from": senders,
            "to": recipients,
            "body": bodies,
        }
    )


def main() -> None:
    with open("pickle/file_list.pickle", "rb") as f:
        file_list: List[str] = pickle.load(f)

    df: pl.DataFrame = build_dataframe(file_list)
    print("Writing to parquet file...")
    df.write_parquet("enron.pq")


if __name__ == "__main__":
    main()