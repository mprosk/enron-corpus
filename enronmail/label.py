import email.errors
import os
import random
import utils

FILE_LIST = "pickle/file_list.pickle"
LABELLED_DATA = "pickle/labelled_data.pickle"


def load_labels() -> list:
    with open("labels.txt") as file:
        return file.read().splitlines()


def prompt_for_label(labels: list) -> str | None:
    for i, label in enumerate(labels):
        print(f"{i + 1}. {label}")
    print("0. EXIT")

    v = 0
    while v not in range(1, len(labels) + 1):
        response = input("?> ")
        try:
            v = int(response)
        except ValueError:
            print("Invalid entry")
            continue
        if v == 0:
            return None
    return labels[v - 1]


def get_labels(file_list: list, labels: list, labelled_data: dict):
    while True:
        file_path = random.choice(file_list)
        if file_path in labelled_data:
            continue
        try:
            msg = utils.EnronEmail(file_path, True)
        except TypeError:
            continue
        except email.errors.HeaderParseError:
            continue
        os.system("clear")
        print(f"{len(labelled_data)} labelled files")
        msg.print_email()
        label = prompt_for_label(labels)
        if label is None:
            break
        labelled_data[file_path] = label
        utils.store_pickle(labelled_data, LABELLED_DATA)


def convert_to_labels_to_files():
    files_to_labels = utils.load_pickle("pickle/labelled_data_files_to_label.pickle")
    labels_to_files = dict()
    for file, label in files_to_labels.items():
        labels_to_files.setdefault(label, []).append(file)
    utils.store_pickle(labels_to_files, "pickle/labelled_data_labels_to_files.pickle")


def apply_label_to_all_files(file_list: list, label: str):
    labelled_data = utils.load_pickle(LABELLED_DATA)
    for file in file_list:
        labelled_data[file] = label
    utils.store_pickle(labelled_data, LABELLED_DATA)


def main():
    file_list = utils.load_pickle(FILE_LIST)
    # file_list = ["maildir/lenhart-m/sent_items/819."]
    labelled_data = utils.load_pickle(LABELLED_DATA)
    labels = load_labels()
    print(f"{len(labelled_data)} labelled files")
    try:
        get_labels(file_list, labels, labelled_data)
    except KeyboardInterrupt:
        pass
    finally:
        utils.store_pickle(labelled_data, LABELLED_DATA)
        print("Data saved. Exiting...")


if __name__ == '__main__':
    convert_to_labels_to_files()

