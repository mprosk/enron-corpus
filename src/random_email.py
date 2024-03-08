import argparse
import random
import utils


def main(pickle: str, daterange: str, number: int):
    files_by_date = utils.load_pickle(pickle)
    start, end = utils.parse_date_range(daterange)
    file_list = utils.get_files_in_date_range(files_by_date, start, end)
    print(len(file_list))
    for file_path in random.sample(file_list, number):
        email = utils.EnronEmail(file_path)
        email.print_email()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Randomly selects any number of emails from the Enron corpus and prints it to the screen")
    parser.add_argument(
        'number', type=int, default=1, nargs='?', help="Number of random emails to select")
    # parser.add_argument('-m', '--maildir', help="Path to the directory containing the corpus")
    parser.add_argument(
        '-p', '--pickle', default="pickle/files_by_date.pickle", help="path to the pickle file to load")
    parser.add_argument('-d', '--daterange', default=":", help="range of dates to select from")
    args = parser.parse_args()
    if ":" not in args.daterange:
        print("Invalid date range format. Missing a ':'")
        exit(1)
    main(args.pickle, args.daterange, args.number)
