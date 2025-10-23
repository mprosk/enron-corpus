import email.errors
import re
from pathlib import Path
from . import utils


################################################################################
# FILE LIST GENERATION
################################################################################


def generate_file_list(maildir: Path, pickle_path: str = "pickle/file_list.pickle"):
    """
    Recursively iterates through all files in the given Path
    and returns a list of all paths that are a file
    """

    def walk_file_tree(maildir: Path) -> list:
        if not maildir.is_dir():
            return []
        file_list = []
        print(f"Walking {maildir.as_posix()}")
        for file_path in maildir.iterdir():
            if file_path.is_file():
                file_list.append(file_path.as_posix())
            elif file_path.is_dir():
                file_list.extend(walk_file_tree(file_path))
            else:
                print(file_path, "is neither a file nor a directory...")
        print(f"{len(file_list)} files found")
        return file_list

    print(f"Generating file list for {maildir.as_posix()}")
    file_list = walk_file_tree(maildir)
    print(f"{len(file_list)} total files found")
    utils.store_pickle(file_list, pickle_path)
    return file_list


################################################################################
# FILES BY DATE
################################################################################


def organize_files_by_date(
    file_list: list, pickle_path: str = "pickle/files_by_date.pickle"
) -> dict:
    """
    Iterates through all files in the given file_list
    and creates a dictionary mapping a datetime.date
    to the list of emails that fall within that datestamp
    """
    files_by_date = dict()
    total = len(file_list)
    errors = []
    for i, file_path in enumerate(file_list):
        try:
            date = utils.get_email_date(file_path).date()
            files_by_date.setdefault(date, []).append(file_path)
        except TypeError:
            print(f"Error parsing {file_path}")
            errors.append(file_path)
        except email.errors.HeaderParseError:
            print(f"Error parsing {file_path}")
            errors.append(file_path)

        if i % 1000 == 0:
            print(f"{i} of {total} ({round(i / total * 100)}%)")

    utils.store_pickle(files_by_date, pickle_path)
    if errors:
        print("The following file(s) could not be fully parsed:")
        print("\n".join(errors))
    return files_by_date


def organize_files_by_subject(file_list: list) -> dict:
    files_by_subject = dict()
    for file_path in file_list:
        msg = utils.EnronEmail(file_path)
        files_by_subject.setdefault(msg.subject, []).append(file_path)
    return files_by_subject


def filter_single_recip(file_list: list) -> dict:
    single_recip_by_date = dict()
    total = len(file_list)
    errors = []
    for i, file_path in enumerate(file_list):
        try:
            msg = utils.EnronEmail(file_path)
            date = msg.date.date()
            if msg.get_number_of_recipients() == 1:
                single_recip_by_date.setdefault(date, []).append(file_path)
        except TypeError:
            print(f"Error parsing {file_path}")
            errors.append(file_path)
        except email.errors.HeaderParseError:
            print(f"Error parsing {file_path}")
            errors.append(file_path)

        if i % 1000 == 0:
            print(f"{i} of {total} ({round(i / total * 100)}%)")

    utils.store_pickle(single_recip_by_date, "pickle/single_recip_by_date.pickle")
    if errors:
        print("The following file(s) could not be fully parsed:")
        print("\n".join(errors))
    return single_recip_by_date


################################################################################
# SEARCH UTILITIES
################################################################################


def find_participant(file_list: list, participant: str) -> list:
    """Searches through a list of files and returns a list that include
    the given participant email address as sender or receiver"""
    matches = []
    errors = []
    total = len(file_list)
    for i, file_path in enumerate(file_list):
        try:
            msg = utils.EnronEmail(file_path)
            if (participant in msg.sender) or (participant in msg.recip):
                matches.append(file_path)
        except TypeError:
            errors.append(file_path)
            continue
        except email.errors.HeaderParseError:
            errors.append(file_path)
            continue

        if i % 1000 == 0:
            print(f"{i} of {total} ({round(i / total * 100)}%)")
    if errors:
        print("The following file(s) could not be fully parsed:")
        print("\n".join(errors))
    return matches


def find_sender(file_list: list, sender: str) -> list:
    """
    Searches through the file list for any messages that
    contain the sender string in the message's sender field
    """
    matches = []
    for file_path in file_list:
        msg = utils.EnronEmail(file_path)
        if sender in msg.sender:
            matches.append(file_path)
    return matches


def find_ssns(file_list: list) -> list:
    ssns = []
    errors = []
    total = len(file_list)
    ssn_pattern = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    for i, file_path in enumerate(file_list):
        try:
            msg = utils.EnronEmail(file_path, True)
        except TypeError:
            errors.append(file_path)
            continue
        except email.errors.HeaderParseError:
            errors.append(file_path)
            continue
        if i % 1000 == 0:
            print(f"{i} of {total} ({round(i / total * 100)}%)")
        ssns.extend(re.findall(ssn_pattern, msg.body))
    if errors:
        print("The following file(s) could not be fully parsed:")
        print("\n".join(errors))
    if ssns:
        print("Found SSNs:")
        print("\n".join(ssns))
    return ssns


################################################################################

if __name__ == "__main__":
    file_list = utils.load_pickle("pickle/html_files.pickle")
    for file_path in file_list:
        utils.write_body_to_html_file(file_path, "html")
