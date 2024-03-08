import utils

if __name__ == '__main__':
    file_list = utils.load_pickle("file_list_maggi_michelle.pickle")
    subjects = set()
    for file_path in file_list:
        msg = utils.EnronEmail(file_path)
        subjects.add(msg.subject)

    for s in sorted(list(subjects)):
        print(s)
