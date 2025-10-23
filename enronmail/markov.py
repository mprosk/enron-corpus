import random
import sys


def init_from_text(file_path: str) -> dict:
    markov = dict()
    with open(file_path, mode="r") as fp:
        text = fp.read()

    tokens = text.split(" ")
    for i in range(0, len(tokens) - 1):
        markov.setdefault(tokens[i], []).append(tokens[i + 1])
    return markov


def generate_text(markov: dict, token: str, number: int) -> str:
    output = token
    for _ in range(number):
        token = random.choice(markov[token])
        output += f" {token}"
    return output


if __name__ == "__main__":
    markov = init_from_text("misc/maggi_text_clean.txt")
    print(generate_text(markov, sys.argv[1], int(sys.argv[2])))
