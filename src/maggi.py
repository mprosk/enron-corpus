from datetime import datetime, timedelta

import utils
import analysis


PREFIXES = ["-----", "From:", "Sent:", "To:", "Cc:", "Subject:", "Sent from my BlackBerry"]


class Message:

    def __init__(self, date: datetime, sender: str, body: str):
        self.date = date
        self.sender = sender
        self.body = body

    def __eq__(self, other):
        return ((self.date.date() == other.date.date()) and
                (self.sender == other.sender) and
                (self.body == other.body))

    def __hash__(self):
        return hash((self.date.date(), self.sender, self.body))

    def __lt__(self, other):
        return self.date < other.date

    def print(self):
        date = self.date.strftime("%a %b %d %Y %I:%M:%S %p")
        for line in self.body.splitlines():
            print(f"{date}    {self.sender.rjust(16, ' ')}:    {line}")


def parse_date(date: str):
    """
    Mon 11/26/2001 9:08 PM
    Wednesday, January 16, 2002 10:38 AM
    Wed Nov 21 08:00:39 2001
    :param date:
    :return:
    """
    for f in ["%A, %B %d, %Y %I:%M %p", "%a %m/%d/%Y %I:%M %p", "%a %b %d %H:%M:%S %Y"]:
        try:
            return datetime.strptime(date, f)
        except ValueError:
            continue
    return None


def parse_files_as_messages(file_list: list):
    email_lookup = {
        "mike.maggi@enron.com": "Maggi, Mike",
        "michelle.nelson@enron.com": "Nelson, Michelle",
    }
    messages = set()
    for file_path in file_list:
        email = utils.EnronEmail(file_path, True)
        date = email.date.replace(tzinfo=None) + timedelta(hours=2)
        sender = email_lookup[email.sender]
        body = []
        for line in email.body.splitlines():
            line = line.strip()
            if "-----Original Message-----" in line:
                messages.add(Message(date, sender, "\n".join(body)))
                body = []
                continue
            if line.startswith("From:"):
                sender = line.split(":")[1].strip()
                continue
            if line.startswith("Sent:"):
                date = parse_date(line[5:].strip())
                if date is None:
                    print(file_path)
                continue
            if any(line.startswith(prefix) for prefix in PREFIXES):
                continue
            if line:
                body.append(line)
        messages.add(Message(date, sender, "\n".join(body)))
    return messages


def text_only(file_list: list):
    output = set()
    for file_path in file_list:
        msg = utils.EnronEmail(file_path, True)
        for line in msg.body.splitlines():
            line = line.strip()
            if any(line.startswith(prefix) for prefix in PREFIXES):
                continue
            if line:
                output.add(line.lower())
    return output


def all_message_contents(file_list: list):
    for file_path in file_list:
        msg = utils.EnronEmail(file_path, True)
        print(msg.body)


if __name__ == '__main__':
    file_list = utils.load_pickle("pickle/file_list_maggi_michelle.pickle")
    messages = parse_files_as_messages(file_list)
    print(len(messages))
    messages = sorted(list(messages))
    for m in messages:
        m.print()
