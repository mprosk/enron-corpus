from pathlib import Path
import utils


################################################################################
# FILE LIST
################################################################################

def generate_file_list(maildir: Path):
    """
    Recursively iterates through all files in the given Path
    and returns a list of all paths that are a file
    """
    def walk_file_tree(maildir: Path) -> list:
        if not maildir.is_dir():
            return []
        file_list = []
        for file_path in maildir.iterdir():
            if file_path.is_file():
                file_list.append(file_path.as_posix())
            elif file_path.is_dir():
                file_list.extend(walk_file_tree(file_path))
            else:
                print(file_path, "is neither a file nor a directory...")
        return file_list

    print(f"Generating file list for {maildir.as_posix()}")
    file_list = walk_file_tree(maildir)
    print(f"{len(file_list)} files found")
    utils.store_pickle(file_list, "file_list.pickle")
    return file_list


################################################################################
# FILES BY DATE
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
            date = utils.get_email_date(file_path).date()
            files_by_date.setdefault(date, []).append(file_path)
        except Exception as e:
            print(f"Error parsing {file_path}")
            raise e

        if i % 1000 == 0:
            print(f"{i} of {total} ({round(i / total * 100)}%)")

    utils.store_pickle(files_by_date, "files_by_date.pickle")
    return files_by_date


################################################################################

if __name__ == '__main__':
    file_list = utils.load_pickle("file_list.pickle")
