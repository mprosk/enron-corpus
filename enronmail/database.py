import email.errors
import sqlite3
from datetime import datetime

import enronmail.utils as utils
from enronmail.utils import EnronEmail

DATABASE = "enron.db"


class DatabaseEmail:
    def __init__(
        self,
        path: str,
        date: datetime,
        sender: str = "",
        recipient: str = "",
        subject: str = "",
        body: str = "",
    ):
        self.path = path
        self.date = date
        self.sender = sender
        self.recipient = recipient
        self.subject = subject
        self.body = body

    def print(self):
        print(f" {self.path} ".center(80, "="))
        print("FROM:   ", self.sender)
        print("TO:     ", self.recipient)
        print("DATE:   ", self.date)
        print("SUBJECT:", self.subject)
        print()
        prev_was_blank = False
        for line in self.body.splitlines():
            line = line.strip()
            while line.startswith(">"):
                line = line[1:].strip()
            if line:
                prev_was_blank = False
                print(line)
            else:
                if not prev_was_blank:
                    print()
                prev_was_blank = True
        print()


def get_email_by_path(email_path: str) -> DatabaseEmail | None:
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Query to retrieve the email body based on the email path
    cursor.execute(
        """
        SELECT * FROM emails
        WHERE path = ?
    """,
        (email_path,),
    )

    # Fetch the result
    result = cursor.fetchone()
    conn.close()

    # Check if the result is not empty
    if result:
        return DatabaseEmail(
            *result
        )  # Assuming there's only one result, return the body
    else:
        return None


def get_files_by_body_text(search_text):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Query to retrieve emails containing the search text in the body
    cursor.execute(
        """
        SELECT path FROM emails
        WHERE LOWER(body) LIKE '%' || LOWER(?) || '%'
    """,
        (search_text,),
    )

    rows = cursor.fetchall()
    conn.close()
    return [f[0] for f in rows]


def get_files_by_subject(search_text):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Query to retrieve emails containing the search text in the body
    cursor.execute(
        """
        SELECT path FROM emails
        WHERE LOWER(subject) LIKE '%' || LOWER(?) || '%'
    """,
        (search_text,),
    )

    rows = cursor.fetchall()
    conn.close()
    return [f[0] for f in rows]


def get_emails_in_date_range(start_date=None, end_date=None):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    if start_date is not None and end_date is not None and start_date > end_date:
        print("Invalid date range. start_date must be less than or equal to end_date.")
        return []

    # Build the SQL query based on the provided date range
    if start_date is None and end_date is None:
        query = """
            SELECT path, date FROM emails
        """
        cursor.execute(query)
    elif start_date is not None and end_date is not None:
        query = """
            SELECT path, date FROM emails
            WHERE date BETWEEN ? AND ?
        """
        cursor.execute(
            query,
            (
                start_date.strftime("%Y-%m-%d %H:%M:%S"),
                end_date.strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
    elif start_date is not None:
        query = """
            SELECT path, date FROM emails
            WHERE date >= ?
        """
        cursor.execute(query, (start_date.strftime("%Y-%m-%d %H:%M:%S"),))
    elif end_date is not None:
        query = """
            SELECT path, date FROM emails
            WHERE date <= ?
        """
        cursor.execute(query, (end_date.strftime("%Y-%m-%d %H:%M:%S"),))

    # Fetch all rows and create Email instances
    rows = cursor.fetchall()
    emails = [DatabaseEmail(*row) for row in rows]

    conn.close()
    return emails


def init_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS emails (
            path TEXT PRIMARY KEY,
            date DATETIME,
            sender TEXT,
            recipient TEXT,
            subject TEXT,
            body TEXT
        )
    """
    )
    conn.commit()
    conn.close()


def insert_entry(cursor, entry: EnronEmail):
    cursor.execute(
        """
        INSERT INTO emails (path, date, sender, recipient, subject, body) VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            entry.file_path,
            entry.date.strftime("%Y-%m-%d %H:%M:%S"),
            entry.sender,
            entry.recip,
            entry.subject,
            entry.get_body(),
        ),
    )


def populate_database(file_list: list):
    errors = []
    total = len(file_list)
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    for i, file_path in enumerate(file_list):
        try:
            msg = EnronEmail(file_path, True)
            insert_entry(cursor, msg)
        except TypeError:
            errors.append(file_path)
            continue
        except email.errors.HeaderParseError:
            errors.append(file_path)
            continue
        if i % 1000 == 0:
            print(f"{i} of {total} ({round(i / total * 100)}%)")

    conn.commit()
    conn.close()

    if errors:
        print("The following file(s) could not be fully parsed:")
        print("\n".join(errors))


if __name__ == "__main__":
    init_table()
    file_list = utils.load_pickle("pickle/file_list.pickle")
    populate_database(file_list)
    pass
