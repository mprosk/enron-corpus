import email.errors
from pathlib import Path
import utils


################################################################################
# FILE LIST
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

def generate_files_by_date(file_list: list) -> dict:
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

    utils.store_pickle(files_by_date, "pickle/files_by_date.pickle")
    print("The following file(s) could not be fully parsed:")
    for fail in errors:
        print(fail)
    return files_by_date


################################################################################
# SINGLE RECIPIENT MESSAGES
################################################################################

def generate_single_recip(file_list: list) -> dict:
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
    print("The following file(s) could not be fully parsed:")
    for fail in errors:
        print(fail)
    return single_recip_by_date


################################################################################
# SEARCH UTILITIES
################################################################################

def find_participant(file_list: list, participant: str) -> list:
    """Searches through a list of files and returns a list that include
    the given participant email address as sender or receiver"""
    matches = []
    for file_path in file_list:
        msg = utils.EnronEmail(file_path, True)
        if (participant in msg.sender) or (participant in msg.recip):
            matches.append(file_path)
    return matches


################################################################################

if __name__ == '__main__':
    pass
