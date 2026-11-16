#!/usr/bin/env python3
"""
Turn the deduplicated Enron parquet into formatted training documents.

Each email becomes one document:

    <|email|><|subject|>Re: holiday party
    <|from|>jeff.skilling@enron.com
    <|to|>kenneth.lay@enron.com, greg.whalley@enron.com
    <|body|>
    ...body text...
    <|end|>

Cleaning is deliberately light (this is an art project, junk is flavor):
  - HTML emails: tags stripped, text kept
  - base64 blobs: removed; emails that are mostly base64 are dropped
  - nested "> >" quote lines: removed (single-level ">" quotes are kept)
  - hard-wrapped lines (~70-80 col wrapping, re-wrapped "> " quotes) rejoined so line
    breaks are where the author put them
  - URLs: cut down to scheme + host (paths and query strings dropped), and
    orphaned query-string lines from wrapped URLs removed
  - every run of 2+ spaces collapsed to one (tabs untouched)
  - quoted-printable leftovers (=20, =3D, soft line breaks, =92): decoded
  - bullet characters (U+2022, QP =95) -> "- "
  - ASCII only: mangled punctuation from the original corpus (\x01,s -> 's) repaired,
    Unicode transliterated (e.g. curly quotes, accents, (c)), remaining non-ASCII and
    control characters dropped
  - Outlook "-----Original Message-----" chains, disclaimers, separators: kept
  - whitespace: CRLF -> LF, trailing spaces stripped, 3+ blank lines -> 2

Output: lm/data/emails.pq with columns (path, split, text), plus
lm/data/samples.txt with a few random documents for eyeballing.
"""

import argparse
import hashlib
import random
import re
import unicodedata
import warnings
from pathlib import Path

import polars as pl
from bs4 import BeautifulSoup, Comment, MarkupResemblesLocatorWarning

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

SPECIAL_TOKENS = ["<|email|>", "<|subject|>", "<|from|>", "<|to|>", "<|body|>", "<|end|>"]

MAX_RECIPIENTS = 5
VAL_FRACTION = 0.01

BASE64_LINE = re.compile(r"[A-Za-z0-9+/]{40,}={0,2}")
NESTED_QUOTE_LINE = re.compile(r"^[ \t]*>[ \t]*>")
HTML_DOC = re.compile(r"(?i)<html|<!doctype html")
HTML_TAG = re.compile(
    r"(?i)</?(html|head|body|table|tr|td|th|font|div|p|br|span|b|i|u|a|img|center|li|ul|ol|h[1-6])\b[^>]*>"
)
HTML_BLOCK_TAGS = ["br", "p", "div", "tr", "li", "table", "h1", "h2", "h3", "h4", "h5", "h6", "center", "title"]
REPLY_PREFIX = re.compile(r"^\s*((re|fw|fwd)\s*:\s*)+", re.IGNORECASE)
# scheme+host (group 1) followed by path/query (dropped)
URL = re.compile(r"(?i)((?:https?|ftp)://[^\s/<>\"?#]+|\bwww\.[^\s/<>\"?#]+)[^\s<>\"]*")
MULTI_SPACE = re.compile(r" {2,}")
# orphaned continuation lines of wrapped URLs: one space-free run with ?/& and =
# URL-param "words" left inline (wrapped URL pieces rejoined onto prose, redirect paths).
# 15+ chars keeps real text like "S&P=953.4" safe.
URL_FRAGMENT_WORD = re.compile(r"(?<!\S)(?=\S*[?&])(?=\S*=)\S{15,}")
MAILTO_QUERY = re.compile(r"(?i)(mailto:[^\s?&<>]+)[?&][^\s<>]*")
URL_FRAGMENT_LINE = re.compile(r"(?m)^[> \t]*[^\s]*[?&][^\s]*=[^\s]*[ \t]*(?:\n|$)")

# Quoted-printable leftovers. The importer decoded most bodies, but ~130 emails are still
# QP-encoded, and stray codes appear elsewhere. "=XX" is also common in legit text
# (URL params, "$1=47.11"), so full decoding only happens for emails that clearly are QP.
QP_SOFT_BREAK = re.compile(r"(?<=[A-Za-z0-9.,;:!?)'\"])=\n")  # wrapped line (not =-=-= art or MIME _=)
QP_CODES = re.compile(r"(?:=[0-9A-F]{2})+")
QP_TRAILING_SPACE = re.compile(r"=20(?=\n|$)")
QP_STRONG = re.compile(r"=20\n|=3D|=09")
CP1252_PUNCT = {"91": "'", "92": "'", "93": '"', "94": '"', "96": "-", "97": "-"}
QP_PUNCT_IN_WORD = re.compile(r"(?<=[A-Za-z])=(9[1-46-7])(?=[A-Za-z\s])")


# The original Enron conversion mangled typographic punctuation into control-char pairs
# ("Enron\x01,s" = "Enron's"). Mapping inferred from context.
MANGLED_PAIRS = {
    "\x01,": "'", "\x01+": "'", "\x01%": "'",
    "\x01&": '"', "\x018": '"',
    "\x01)": "-", "\x01*": "-", "\x01(": "-", "\x01.": "-",
    "\x01\x07": "- ", "\x0f\x07": "- ",
    "\x01;": " ",
    "\x01v": "(TM)",
}
MANGLED_PAIR = re.compile("|".join(re.escape(k) for k in MANGLED_PAIRS))
CONTROL_CHARS = re.compile(r"[\x00-\x08\x0B-\x1F\x7F]")
UNICODE_TO_ASCII = {
    "\u2018": "'", "\u2019": "'", "\u00b4": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\u2022": "- ", "\u00b7": "-", "\u2026": "...",
    "\u00a0": " ", "\u00ae": "(R)", "\u00a9": "(c)", "\u2122": "(TM)", "\u00b0": "deg",
    "\u00a2": "c", "\u00a3": "GBP", "\u00a5": "JPY", "\u00bc": "1/4", "\u00bd": "1/2",
    "\u00be": "3/4", "\u02c6": "^", "\u00fe": "th", "\u00df": "ss", "\u00e6": "ae",
}


def to_ascii(text: str, stats: dict | None = None) -> str:
    """Repair mangled punctuation, transliterate to ASCII, drop whatever is left."""
    text = MANGLED_PAIR.sub(lambda m: MANGLED_PAIRS[m.group()], text)
    text = text.translate(str.maketrans(UNICODE_TO_ASCII))
    # accented letters -> base letter (e -> e, n~ -> n)
    text = unicodedata.normalize("NFKD", text)
    before = len(text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = CONTROL_CHARS.sub("", text)
    if stats is not None:
        stats["non_ascii_or_control_chars_dropped"] += before - len(text)
    return text


def is_quoted_printable(body: str) -> bool:
    strong = len(QP_STRONG.findall(body))
    return strong >= 2 or (strong >= 1 and len(QP_SOFT_BREAK.findall(body)) >= 2)


def decode_qp_codes(m: re.Match) -> str:
    raw = bytes(int(h, 16) for h in m.group().split("=")[1:])
    for enc in ("utf-8", "cp1252"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("latin-1")
    return "".join(CP1252_PUNCT.get(f"{ord(c):02X}", c) for c in text.translate(
        {0x2018: "'", 0x2019: "'", 0x201C: '"', 0x201D: '"', 0x2013: "-", 0x2014: "-", 0xA0: " ", 0x2022: "- "}))


def repair_quoted_printable(body: str, stats: dict) -> str:
    if is_quoted_printable(body):
        body = QP_SOFT_BREAK.sub("", body)
        body = QP_CODES.sub(decode_qp_codes, body)
        stats["qp_emails_decoded"] += 1
        return body
    body, n1 = QP_TRAILING_SPACE.subn("", body)
    body, n2 = QP_PUNCT_IN_WORD.subn(lambda m: CP1252_PUNCT[m.group(1)], body)
    stats["qp_stray_codes_fixed"] += n1 + n2
    return body


# --- Unwrapping hard-wrapped lines -------------------------------------------------------
# Mail clients wrapped text at ~70-80 columns, and forwarding added "> " prefixes that
# re-wrapped it again (leaving orphans like "> some"). We rejoin a line onto the previous
# one when its first word would NOT have fit within the block's wrap width, i.e. the
# break was forced by wrapping rather than chosen by the author.
QUOTE_PREFIX = re.compile(r"^((?:[ \t]*>)*[ \t]?)")
LIST_ITEM = re.compile(r"^(?:[-*o]\s|\d{1,2}[.)]\s|[a-zA-Z][.)]\s)")
HEADER_LINE = re.compile(
    r"^(?:From|To|Cc|Bcc|Sent|Date|Subject|Re|Fw|Importance|Received|Return-Path|Message-ID"
    r"|MIME-Version|Content-[\w-]+|X-[\w-]+)\s*:",
    re.IGNORECASE,
)
SEPARATOR_LINE = re.compile(r"^\s*([-=*_~.#+])\1{4,}\s*$|^\s*-{3,}\s*Original")
SENTENCE_END = re.compile(r"[.!?:;)\"']$")
UNWRAP_MIN_WIDTH, UNWRAP_MAX_WIDTH = 60, 80


def _split_prefix(line: str) -> tuple[str, str]:
    m = QUOTE_PREFIX.match(line)
    return m.group(1), line[m.end() :]


def _digit_heavy(s: str) -> bool:
    s = re.sub(r"\s", "", s)
    return bool(s) and sum(c.isdigit() for c in s) / len(s) > 0.3


def unwrap_lines(body: str, stats: dict) -> str:
    lines = body.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        prefix, text = _split_prefix(lines[i])
        # block = consecutive non-blank lines sharing the same quote depth
        block = [text]
        j = i + 1
        while j < len(lines):
            p2, t2 = _split_prefix(lines[j])
            if p2.strip() != prefix.strip() or not t2.strip():
                break
            block.append(t2)
            j += 1
        lens = [len(prefix) + len(t) for t in block]
        width = max([n for n in lens if n <= UNWRAP_MAX_WIDTH] or [0])
        if width < UNWRAP_MIN_WIDTH:
            out.extend(prefix + t for t in block)
        else:
            cur, prev_raw = block[0], block[0]
            for k, nxt in enumerate(block[1:], start=1):
                is_last = k == len(block) - 1
                first_word = nxt.split(" ", 1)[0]
                author_break = (
                    len(prefix) + len(cur.rstrip()) + 1 + len(first_word) <= width
                    or LIST_ITEM.match(nxt)
                    or HEADER_LINE.match(nxt)
                    or SEPARATOR_LINE.match(nxt)
                    or SEPARATOR_LINE.match(cur)
                    or "\t" in prev_raw
                    or "\t" in nxt
                    or _digit_heavy(prev_raw)
                    or _digit_heavy(nxt)
                    # short final line after a finished sentence = sign-off, not a wrap
                    or (is_last and len(nxt) <= 20 and SENTENCE_END.search(cur.rstrip()))
                )
                if author_break:
                    out.append(prefix + cur)
                    cur = nxt
                else:
                    cur = cur.rstrip() + " " + nxt.lstrip()
                    stats["wrapped_lines_rejoined"] += 1
                prev_raw = nxt
            out.append(prefix + cur)
        if j < len(lines):  # the blank line that ended the block
            out.append(lines[j])
            j += 1
        i = j
    return "\n".join(out)


def is_html(body: str) -> bool:
    return bool(HTML_DOC.search(body)) or len(HTML_TAG.findall(body)) >= 5


def html_to_text(body: str) -> str:
    soup = BeautifulSoup(body, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    for c in soup.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    for tag in soup.find_all(HTML_BLOCK_TAGS):
        tag.insert_before("\n")
        tag.insert_after("\n")
    text = soup.get_text()
    # HTML source is full of indentation; collapse runs of spaces within lines
    text = "\n".join(re.sub(r"[ \t\xa0]+", " ", line).strip() for line in text.split("\n"))
    return text


def base64_fraction(lines: list[str]) -> float:
    nonempty = [l.strip() for l in lines if l.strip()]
    if not nonempty:
        return 0.0
    return sum(bool(BASE64_LINE.fullmatch(l)) for l in nonempty) / len(nonempty)


def strip_base64_blocks(lines: list[str]) -> list[str]:
    """Remove runs of 2+ consecutive base64-looking lines."""
    out, run = [], []
    for line in lines:
        if BASE64_LINE.fullmatch(line.strip()):
            run.append(line)
            continue
        if len(run) == 1:
            out.extend(run)
        run = []
        out.append(line)
    if len(run) == 1:
        out.extend(run)
    return out


def clean_body(body: str, stats: dict) -> str | None:
    body = body.replace("\r\n", "\n").replace("\r", "\n")
    body = repair_quoted_printable(body, stats)
    if is_html(body):
        body = html_to_text(body)
        stats["html_converted"] += 1
    body = to_ascii(body, stats)

    lines = body.split("\n")
    if base64_fraction(lines) > 0.5:
        stats["dropped_base64"] += 1
        return None
    before = len(lines)
    lines = strip_base64_blocks(lines)
    if len(lines) != before:
        stats["base64_blocks_stripped"] += 1

    before = len(lines)
    lines = [l for l in lines if not NESTED_QUOTE_LINE.match(l)]
    stats["nested_quote_lines_removed"] += before - len(lines)

    text = "\n".join(l.rstrip() for l in lines)
    # must run before URL shortening / space collapsing, which change line lengths
    text = unwrap_lines(text, stats)
    text, n = URL.subn(r"\1", text)
    stats["urls_shortened"] += n
    text, n = URL_FRAGMENT_LINE.subn("", text)
    stats["url_fragment_lines_removed"] += n
    text = MAILTO_QUERY.sub(r"\1", text)
    text, n = URL_FRAGMENT_WORD.subn("", text)
    stats["url_fragment_words_removed"] += n
    text, n = MULTI_SPACE.subn(" ", text)
    stats["space_runs_collapsed"] += n
    text = re.sub(r"\n{4,}", "\n\n\n", text).strip("\n")
    # never let raw text collide with our special tokens
    text = text.replace("<|", "< |")
    if not text.strip():
        stats["dropped_empty"] += 1
        return None
    return text


def one_line(s: str | None) -> str:
    return re.sub(r"\s+", " ", to_ascii(s or "")).strip().replace("<|", "< |")


def format_recipients(recipient: str | None) -> str:
    # util/import_emails.py writes "[ERR]" when an email has no To: header (mass mailings, BCC)
    if one_line(recipient) == "[ERR]":
        return ""
    addrs = [a.strip() for a in one_line(recipient).split(",") if a.strip()]
    if len(addrs) > MAX_RECIPIENTS:
        addrs = addrs[:MAX_RECIPIENTS] + ["..."]
    return ", ".join(addrs)


def thread_key(subject: str) -> str:
    return REPLY_PREFIX.sub("", subject).strip().lower()


def split_for(subject: str) -> str:
    h = int(hashlib.md5(thread_key(subject).encode()).hexdigest()[:8], 16)
    return "val" if h / 0xFFFFFFFF < VAL_FRACTION else "train"


def format_email(subject: str, sender: str, recipients: str, body: str) -> str:
    return (
        f"<|email|><|subject|>{subject}\n"
        f"<|from|>{sender}\n"
        f"<|to|>{recipients}\n"
        f"<|body|>\n{body}\n<|end|>"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default="enron_dedupe.pq")
    ap.add_argument("--out-dir", default="lm/data")
    ap.add_argument("--n-samples", type=int, default=30)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pl.read_parquet(args.input, columns=["path", "date", "subject", "sender", "recipient", "body"])
    df = df.sort("date")
    print(f"Loaded {df.height:,} emails from {args.input}")

    stats = dict.fromkeys(
        [
            "html_converted", "dropped_base64", "base64_blocks_stripped", "nested_quote_lines_removed", "wrapped_lines_rejoined",
            "qp_emails_decoded", "qp_stray_codes_fixed", "urls_shortened", "url_fragment_lines_removed", "url_fragment_words_removed", "non_ascii_or_control_chars_dropped",
            "space_runs_collapsed", "dropped_empty",
        ],
        0,
    )
    paths, splits, texts = [], [], []
    for i, (path, subject, sender, recipient, body) in enumerate(
        df.select("path", "subject", "sender", "recipient", "body").iter_rows()
    ):
        cleaned = clean_body(body or "", stats)
        if cleaned is None:
            continue
        subject = URL.sub(r"\1", one_line(subject))
        paths.append(path)
        splits.append(split_for(subject))
        texts.append(format_email(subject, one_line(sender), format_recipients(recipient), cleaned))
        if (i + 1) % 25000 == 0:
            print(f"  {i + 1:,} / {df.height:,}")

    out = pl.DataFrame({"path": paths, "split": splits, "text": texts})
    out.write_parquet(out_dir / "emails.pq")

    print("\nCleaning stats:")
    for k, v in stats.items():
        print(f"  {k}: {v:,}")
    by_split = out.group_by("split").agg(pl.len().alias("emails"), pl.col("text").str.len_chars().sum().alias("chars"))
    print("\nOutput:")
    for split, n, chars in by_split.sort("split").iter_rows():
        print(f"  {split}: {n:,} emails, {chars:,} chars (~{chars / 4 / 1e6:.0f}M tokens at ~4 chars/token)")

    rng = random.Random(0)
    sample_idx = rng.sample(range(out.height), min(args.n_samples, out.height))
    with open(out_dir / "samples.txt", "w") as f:
        for idx in sample_idx:
            f.write(f"#################### {paths[idx]}\n{texts[idx]}\n\n")
    print(f"\nWrote {out_dir / 'emails.pq'} and {out_dir / 'samples.txt'}")


if __name__ == "__main__":
    main()
