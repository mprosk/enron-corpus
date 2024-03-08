from email import policy
from email.parser import BytesParser
from datetime import datetime
from pathlib import Path
import pickle


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

    def __init__(self, file_path: Path):
        self.filepath = file_path
        self.body = ""
        with open(self.filepath, mode='rb') as file:
            self.msg = BytesParser(policy=policy.default).parse(file)
        self.subject = self.msg.get('Subject', '[ERR]')
        if not self.subject:
            self.subject = "(no subject)"
        self.sender = self.msg.get('From', '[ERR]')
        self.recip = self.msg.get('To', '[ERR]')
        self.date = datetime.strptime(self.msg.get('Date'), "%a, %d %b %Y %H:%M:%S %z")
        self.body = self.msg.get_payload(decode=True).decode('utf-8')

    def get_clean_body(self) -> list:
        """Parses the body text of a decoded email and attempts to isolate just the interesting text"""
        output = []
        in_body = True
        for line in self.body.splitlines():
            line = line.strip()
            while line.startswith(">"):
                line = line[1:].strip()
            if line.startswith("----"):
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


################################################################################
# EMAIL PARSING UTILITIES
################################################################################

def get_email_date(file_path: str) -> datetime:
    with open(file_path, mode='rb') as file:
        msg = BytesParser(policy=policy.default).parse(file)
    return datetime.strptime(msg.get('Date'), "%a, %d %b %Y %H:%M:%S %z")


################################################################################
# FILES BY DATE UTILITIES
################################################################################

def generate_files_by_date(file_list: list) -> dict:
    """
    Iterates through all files in the given file_list
    and returns a list of EnronEmail objects
    """
    files_by_date = dict()
    total = len(file_list)
    for i, file_path in enumerate(file_list):
        try:
            date = get_email_date(file_path).date()
            files_by_date.setdefault(date, []).append(file_path)
        except Exception as e:
            print(f"Error parsing {file_path}")
            raise e

        if i % 1000 == 0:
            print(f"{i} of {total} ({round(i / total * 100)}%)")
    return files_by_date


def write_files_by_date_to_pickle(file_list: list):
    """Generates the list of files in the given Path and writes the resulting list as a Pickle"""
    files_by_date = generate_files_by_date(file_list)
    store_pickle(files_by_date, "files_by_date.pickle")


def read_files_by_date_from_pickle(pickle_path: Path = Path("files_by_date.pickle")) -> dict:
    return load_pickle(pickle_path)


################################################################################
# FILE LIST UTILITIES
################################################################################

def generate_file_list(maildir: Path) -> list:
    """
    Recursively iterates through all files in the given Path
    and returns a list of all paths that are a file
    """
    if not maildir.is_dir():
        return []

    print(f"Generating file list for {maildir.as_posix()}")

    file_list = []
    for file_path in maildir.iterdir():
        if file_path.is_file():
            file_list.append(file_path.as_posix())
        elif file_path.is_dir():
            file_list.extend(generate_file_list(file_path))
        else:
            print(file_path, "is neither a file nor a directory...")

    print(f"{len(file_list)} files found")
    return file_list


def write_file_list_to_pickle(maildir: Path):
    """Generates the list of files in the given Path and writes the resulting list as a Pickle"""
    file_list = generate_file_list(maildir)
    store_pickle(file_list, "file_list.pickle")


def read_file_list_from_pickle(pickle_path: Path = Path("file_list.pickle")) -> list:
    return load_pickle(pickle_path)


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

if __name__ == '__main__':
    # write_files_by_date_to_pickle(read_file_list_from_pickle())

    # files_by_date = read_files_by_date_from_pickle()
    # dates = sorted(list(files_by_date.keys()))
    # for date in dates:
    #     print(f"{date}: {len(files_by_date[date])}")
    pass
