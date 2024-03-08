from email import policy
from email.parser import BytesParser
from datetime import datetime
from pathlib import Path
import pickle

DATE_FORMAT_STRING = "%a, %d %b %Y %H:%M:%S %z"
PREFIXES_IGNORE = [
    "To:",
"From:",
    "Date:",
    "Sent:",
    "Re:",
    "cc:",
    "bcc:",
    "Tel:",
    "Fax:",
]
"""List of line prefixes that indicate a LINE we want to ignore"""


################################################################################
# EMAIL METADATA CLASS
################################################################################

class EnronEmail:
    """Class for containing metadata"""

    def __init__(self, file_path: Path, load_body: bool = False):
        self.file_path = file_path
        with open(self.file_path, mode='rb') as file:
            self.msg = BytesParser(policy=policy.default).parse(file)
        self.subject = self.msg.get('Subject', '[ERR]')
        if not self.subject:
            self.subject = "(no subject)"
        self.sender = self.msg.get('From', '[ERR]')
        self.recip = self.msg.get('To', '[ERR]')
        self.date = datetime.strptime(self.msg.get('Date'), DATE_FORMAT_STRING)
        self.body = None
        if load_body:
            self.body = self.msg.get_payload(decode=True).decode('utf-8')

    def get_body(self):
        with open(self.file_path, mode='rb') as file:
            self.msg = BytesParser(policy=policy.default).parse(file)
        self.body = self.msg.get_payload(decode=True).decode('utf-8')

    def get_number_of_recipients(self):
        return self.recip.count('@')

    def get_clean_body(self) -> list:
        """Parses the body text of a decoded email and attempts to isolate just the interesting text"""
        if self.body is None:
            self.get_body()
        output = []
        in_body = True
        for line in self.body.splitlines():
            line = line.strip()
            while line.startswith(">"):
                line = line[1:].strip()
            if line.startswith("----") and ("forward" in line.lower()):
                in_body = False
                continue
            if line.startswith("Subject:") or line.startswith("Subj:"):
                in_body = True
                continue
            if any(line.startswith(prefix) for prefix in PREFIXES_IGNORE):
                continue
            if in_body:
                # Only append an empty line if the previous line had content
                # Effectively removes multiple blank lines into just one
                if (not line) and output:
                    if output[-1]:
                        output.append(line)
                    continue
                output.append(line)
        return output

    def print_email(self):
        print(f" {self.file_path} ".center(80, "="))
        print("FROM:   ", self.sender)
        print("TO:     ", self.recip)
        print("DATE:   ", self.date)
        print("SUBJECT:", self.subject)
        print()
        for line in self.get_clean_body():
            print(line)
        print()


################################################################################
# EMAIL PARSING UTILITIES
################################################################################

def get_email_date(file_path: str) -> datetime:
    with open(file_path, mode='rb') as file:
        msg = BytesParser(policy=policy.default).parse(file)
    return datetime.strptime(msg.get('Date'), DATE_FORMAT_STRING)


################################################################################
# PICKLE I/O UTILITIES
################################################################################

def load_pickle(pickle_path):
    with open(pickle_path, mode='rb') as file:
        return pickle.load(file)


def store_pickle(item, pickle_path):
    with open(pickle_path, mode='wb') as file:
        pickle.dump(item, file)


################################################################################
# DATE RANGE UTILITIES
################################################################################

def parse_date_range(daterange: str):
    """
    Parses a date range string into datetime.date ranges
    :param daterange: date range string
    :return: tuple of ( [ datetime.date | None ], [ datetime.date | None ] )
    """
    def parse_date_string(date: str):
        if not date:
            return None
        for f in ["%Y-%m-%d", "%Y-%m", "%Y"]:
            try:
                return datetime.strptime(date, f).date()
            except ValueError:
                continue
        return None
    tokens = daterange.split(":")
    start = parse_date_string(tokens[0])
    end = parse_date_string(tokens[1])
    return start, end


def get_files_in_date_range(files_by_date: dict, start, end) -> list:
    """
    Creates a list of email file paths that fall within a given date range
    If `start` or `end` is None, it indicates no limit in that direction
    E.g. if `start` is a datetime.date and `end` is None, the returned list will
    include all emails with dates that are on or after the `start` date
    :param files_by_date: dictionary mapping of dates to list of email paths
    :param start: datetime.date or None indicating the lower bounds of the range
    :param end: datetime.date or None indicating the upper bounds of the range
    :return: list of email file paths that fall within the date range
    """
    file_list = []
    for date, files in files_by_date.items():
        include = True
        if start:
            include &= date >= start
        if end is not None:
            include &= date <= end
        if include:
            file_list.extend(files)
    return file_list
