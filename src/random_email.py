import argparse
from pathlib import Path
from datetime import datetime
import utils
import random


def print_email(file_path: str):
    print(f" {file_path} ".center(80, "="))
    email = utils.EnronEmail(Path(file_path))
    print("FROM:   ", email.sender)
    print("TO:     ", email.recip)
    print("DATE:   ", email.date)
    print("SUBJECT:", email.subject)
    print()
    for line in email.get_clean_body():
        print(line)
    print()


def parse_date_range(daterange: str):
    if ":" not in daterange:
        print("Invalid date range format. Missing ':'")
        exit(1)
    start = None
    end = None
    tokens = daterange.split(":")
    if tokens[0]:
        start = datetime.strptime(tokens[0], "%Y-%m-%d")
    if tokens[1]:
        end = datetime.strptime(tokens[1], "%Y-%m-%d")
    return start, end


def generate_file_list(files_by_date: dict, start, end) -> list:
    file_list = []
    for date, files in files_by_date.items():
        include = True
        if start is not None:
            include = date >= start.date()
        if end is not None:
            include = date <= end.date()
        if include:
            file_list.extend(files)
    return file_list


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Randomly selects any number of emails from the Enron corpus and prints it to the screen")
    parser.add_argument(
        'number', type=int, default=1, nargs='?', help="Number of random emails to select")
    # parser.add_argument('-m', '--maildir', help="Path to the directory containing the corpus")
    # parser.add_argument('-m', '--maildir', help="Path to the directory containing the corpus")
    parser.add_argument('-d', '--daterange', default=":", help="range of dates to select from")
    args = parser.parse_args()

    files_by_date = utils.read_files_by_date_from_pickle()
    start, end = parse_date_range(args.daterange)
    file_list = generate_file_list(files_by_date, start, end)
    print(len(file_list))

    for file_path in random.sample(file_list, args.number):
        print_email(file_path)
