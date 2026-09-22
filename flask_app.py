#!/usr/bin/env python3
"""
Modern Flask Web Application for Enron Email Corpus Viewer
Features: Responsive design with Tailwind CSS, mobile-first approach
"""

import html
import urllib.parse
from datetime import datetime, timedelta, date, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple
import os

import polars as pl
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from markupsafe import Markup

app = Flask(__name__)

# Configuration — prefer labeled/deduped corpora when present
DEFAULT_PARQUET_CANDIDATES = (
    "enron_dedupe_jev.pq",
    "enron_dedupe.pq",
    "enron.pq",
)


def resolve_parquet_file() -> str:
    """Pick parquet path: ENRON_PARQUET_FILE, else first existing default candidate."""
    env_path = os.environ.get("ENRON_PARQUET_FILE", "").strip()
    if env_path:
        return env_path
    for candidate in DEFAULT_PARQUET_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    return DEFAULT_PARQUET_CANDIDATES[0]


PARQUET_FILE = resolve_parquet_file()
_df_cache: Optional[pl.DataFrame] = None
_tag_counts_cache: Optional[List[Tuple[str, int]]] = None

# Canonical content tags from the Jev labeling scheme, plus the "other" fallback.
VALID_JEV_TAGS: Tuple[str, ...] = (
    "business",
    "personal",
    "marketing",
    "automated",
    "spam",
    "racist",
    "homophobic",
    "xenophobic",
    "sexist",
    "funny",
    "hostile",
    "explicit",
    "email_forward",
    "incriminating",
    "dark",
    "morale",
    "gossip_personal",
    "gossip_work",
    "office_politics",
    "politics",
    "recipe",
    "september_11",
    "enron_collapse",
    "arthur_andersen",
    "historical",
    "weird",
    "other",
)


def get_dataframe() -> pl.DataFrame:
    """Get or load the parquet dataframe (cached)"""
    global _df_cache
    if _df_cache is None:
        _df_cache = pl.read_parquet(PARQUET_FILE)
    return _df_cache


def get_total_count() -> int:
    """Get total number of emails"""
    df = get_dataframe()
    return len(df)


def has_tag_support() -> bool:
    """Whether the loaded parquet includes Jev content tags."""
    return "jev_labels" in get_dataframe().columns


def get_valid_tags() -> List[str]:
    """Return the list of tags users may select."""
    if not has_tag_support():
        return []
    return list(VALID_JEV_TAGS)


def parse_requested_tags(raw_tags: Sequence[str]) -> List[str]:
    """Keep only valid tags from request input, preserving order and uniqueness."""
    valid = set(get_valid_tags())
    seen = set()
    tags: List[str] = []
    for tag in raw_tags:
        tag = (tag or "").strip()
        if tag in valid and tag not in seen:
            seen.add(tag)
            tags.append(tag)
    return tags


def get_tag_counts() -> List[Tuple[str, int]]:
    """Return (tag, email_count) pairs for the tag browser, sorted by count desc."""
    global _tag_counts_cache
    if _tag_counts_cache is not None:
        return _tag_counts_cache

    if not has_tag_support():
        _tag_counts_cache = []
        return _tag_counts_cache

    df = get_dataframe()
    counts_df = (
        df.select(pl.col("jev_labels").explode().alias("tag"))
        .drop_nulls()
        .group_by("tag")
        .len()
        .sort("len", descending=True)
    )

    valid = set(VALID_JEV_TAGS)
    counts: List[Tuple[str, int]] = []
    for row in counts_df.iter_rows(named=True):
        tag = row["tag"]
        if tag in valid:
            counts.append((tag, int(row["len"])))

    # Include valid tags with zero count so the browser shows the full set
    present = {tag for tag, _ in counts}
    for tag in VALID_JEV_TAGS:
        if tag not in present:
            counts.append((tag, 0))

    _tag_counts_cache = counts
    return _tag_counts_cache


def extract_row_tags(row: Dict[str, Any]) -> List[str]:
    """Extract applied tags from a named row dict."""
    if "jev_labels" not in row:
        return []
    tags = row.get("jev_labels") or []
    return [t for t in tags if t]


def extract_tag_scores(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract all per-tag confidence scores, sorted by score descending."""
    scores: List[Dict[str, Any]] = []
    for key, value in row.items():
        if not key.startswith("jev_probability_"):
            continue
        tag = key[len("jev_probability_") :]
        if value is None:
            continue
        try:
            score = float(value)
        except (TypeError, ValueError):
            continue
        scores.append({"tag": tag, "score": score})
    scores.sort(key=lambda item: item["score"], reverse=True)
    return scores


def format_result_date(date_val: Any) -> Optional[str]:
    """Format a date value for search result list display."""
    if not date_val:
        return None
    if isinstance(date_val, datetime):
        adjusted_date = date_val - timedelta(hours=5)
        return adjusted_date.strftime("%Y-%m-%d")
    date_str = str(date_val)
    return date_str.split()[0] if " " in date_str else date_str


@app.template_filter('intcomma')
def intcomma_filter(value: int) -> str:
    """Format number with commas"""
    return f"{value:,}"


@app.template_filter('urlencode')
def urlencode_filter(value: str) -> str:
    """URL encode a string"""
    return urllib.parse.quote(value)


@app.template_filter('tojson')
def tojson_filter(value: str) -> str:
    """Convert value to JSON string (marked as safe for JavaScript)"""
    import json
    return Markup(json.dumps(value))


@app.route("/favicon.png")
def favicon():
    """Serve the favicon.png file"""
    return send_from_directory(".", "favicon.png")


@app.route("/")
@app.route("/index.html")
def index():
    """Serve the main search page"""
    total_count = get_total_count()
    tag_counts = get_tag_counts() if has_tag_support() else []
    return render_template(
        "index.html",
        total_count=total_count,
        has_tags=has_tag_support(),
        valid_tags=get_valid_tags(),
        tag_counts=tag_counts,
    )


@app.route("/search")
def search():
    """Search emails and display results"""
    # Get search parameters
    search_query = request.args.get("q", "").strip()
    sender = request.args.get("sender", "").strip()
    recipient = request.args.get("recipient", "").strip()
    participant = request.args.get("participant", "").strip()
    subject = request.args.get("subject", "").strip()
    body = request.args.get("body", "").strip()
    path_search = request.args.get("path", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    tags = parse_requested_tags(request.args.getlist("tag"))
    tag_mode = request.args.get("tag_mode", "or").strip().lower()
    if tag_mode not in ("and", "or"):
        tag_mode = "or"

    # Check if at least one search criterion is provided
    if not any([
        search_query, sender, recipient, participant, subject, body,
        path_search, start_date, end_date, tags,
    ]):
        return redirect(url_for("index"))

    # Perform search
    results, total_count = search_emails(
        search_query, sender, recipient, participant, subject, body,
        path_search, start_date, end_date, tags, tag_mode,
    )

    # Build search criteria display text (Jinja2 will auto-escape, so we don't escape here)
    criteria_parts = []
    if search_query:
        criteria_parts.append(f'Quick search: "{search_query}"')
    if sender:
        criteria_parts.append(f'From: "{sender}"')
    if recipient:
        criteria_parts.append(f'To: "{recipient}"')
    if participant:
        criteria_parts.append(f'Participant: "{participant}"')
    if subject:
        criteria_parts.append(f'Subject: "{subject}"')
    if body:
        criteria_parts.append(f'Body: "{body}"')
    if path_search:
        criteria_parts.append(f'Path: "{path_search}"')
    if start_date and end_date:
        criteria_parts.append(f"Date: {start_date} to {end_date}")
    elif start_date:
        criteria_parts.append(f"Date: from {start_date}")
    elif end_date:
        criteria_parts.append(f"Date: until {end_date}")
    if tags:
        joiner = f" {tag_mode.upper()} "
        criteria_parts.append(f'Tags: {joiner.join(tags)}')

    search_criteria_text = " | ".join(criteria_parts)

    # Build result count text
    if total_count > 1000:
        count_text = f"Found {total_count:,} result(s) (showing first 1000)"
    else:
        count_text = f"Found {total_count:,} result(s)"

    return render_template(
        "search_results.html",
        results=results,
        search_criteria_text=search_criteria_text,
        count_text=count_text,
        has_tags=has_tag_support(),
    )


@app.route("/email")
def email():
    """Display full email content"""
    email_path = request.args.get("path", "").strip()
    from_search = request.args.get("from_search", "0") == "1"
    random_type = request.args.get("random_type", "").strip()  # "random" or "random_today" or ""

    if not email_path:
        return "Email path required", 400

    # Add trailing period if missing (all email paths end with a period)
    if not email_path.endswith('.'):
        email_path = email_path + '.'

    # Get email from dataframe
    email_data = get_email(email_path)

    if email_data is None:
        return "Email not found", 404

    path = email_data["path"]
    email_date = email_data["date"]
    email_subject = email_data["subject"]
    email_sender = email_data["sender"]
    email_recipient = email_data["recipient"]
    email_body = email_data["body"]
    tags = email_data["tags"]
    tag_scores = email_data["tag_scores"]

    # Format values for template (Jinja2 will auto-escape, so we don't escape here)
    if email_date:
        if isinstance(email_date, datetime):
            # Subtract 5 hours for timezone adjustment
            adjusted_date = email_date - timedelta(hours=5)
            date_str = adjusted_date.strftime("%Y-%m-%d %I:%M %p")
        else:
            # Try to parse and reformat if it's a string
            try:
                dt = datetime.fromisoformat(str(email_date).replace('Z', '+00:00'))
                # Subtract 5 hours for timezone adjustment
                adjusted_date = dt - timedelta(hours=5)
                date_str = adjusted_date.strftime("%Y-%m-%d %I:%M %p")
            except (ValueError, AttributeError):
                date_str = str(email_date)
    else:
        date_str = "N/A"
    sender_str = email_sender if email_sender else "N/A"
    recipient_str = email_recipient if email_recipient else "N/A"
    subject_str = email_subject if email_subject else "(no subject)"
    path_str = path

    # Detect if email body is HTML
    is_html = False
    body_content = email_body if email_body else "(no content)"
    if body_content:
        body_lower = body_content.lower()
        is_html = (
            "<html" in body_lower
            or "<body" in body_lower
            or ("<table" in body_lower and "<tr" in body_lower)
        )

    # Create formatted version of the body (strip lines and remove leading ">")
    def format_body(text: str) -> str:
        """Format email body by stripping lines and removing leading '>' characters"""
        lines = text.split("\n")
        formatted_lines = []
        for line in lines:
            line = line.strip()
            # Remove leading ">" characters
            while line.startswith(">"):
                line = line[1:].strip()
            formatted_lines.append(line)
        result = "\n".join(formatted_lines)
        # Remove leading and trailing whitespace from entire body
        return result.strip()

    # Render body based on content type
    if is_html:
        # For HTML emails, escape for iframe srcdoc attribute (needs manual escaping for attribute)
        body_content_html = html.escape(body_content, quote=True)
        # Provide completely raw HTML source code for text view (no formatting applied)
        # Jinja2 will escape it for safe display as text
        body_content_raw = email_body if email_body else "(no content)"
        body_content_original = ""
        body_content_formatted = ""
    else:
        # Plain text - Jinja2 will auto-escape these, so we don't escape here
        body_content_original = body_content
        body_content_formatted = format_body(body_content)
        body_content_html = ""
        body_content_raw = ""

    return render_template(
        "email_detail.html",
        path=path_str,
        date=date_str,
        sender=sender_str,
        recipient=recipient_str,
        subject=subject_str,
        is_html=is_html,
        body_content=body_content_html,
        body_content_raw=body_content_raw,
        body_content_original=body_content_original,
        body_content_formatted=body_content_formatted,
        from_search=from_search,
        random_type=random_type,
        tags=tags,
        tag_scores=tag_scores,
        has_tag_scores=bool(tag_scores),
    )


@app.route("/random")
def random_email():
    """Serve a random email"""
    email_data = get_random_email()

    if email_data is None:
        return "No emails found", 404

    path = email_data[0]
    encoded_path = urllib.parse.quote(path)
    return redirect(url_for("email", path=encoded_path, random_type="random"))


@app.route("/random_today")
def random_today_email():
    """Serve a random email from today's date (any year)"""
    email_data = get_random_today_email()

    if email_data is None:
        today = date.today()
        return f"No emails found for {today.strftime('%B %d')}", 404

    path = email_data[0]
    encoded_path = urllib.parse.quote(path)
    return redirect(url_for("email", path=encoded_path, random_type="random_today"))


def search_emails(
    query: str = "",
    sender: str = "",
    recipient: str = "",
    participant: str = "",
    subject: str = "",
    body: str = "",
    path_search: str = "",
    start_date: str = "",
    end_date: str = "",
    tags: Optional[List[str]] = None,
    tag_mode: str = "or",
) -> Tuple[List[Dict[str, Any]], int]:
    """Search emails in the parquet file with field-specific or general search"""
    df = get_dataframe()
    tags = tags or []

    # Build filters
    filters = []

    # Quick search across all fields
    if query:
        query_lower = query.lower()
        filters.append(
            (pl.col("subject").str.to_lowercase().str.contains(query_lower, literal=False))
            | (pl.col("sender").str.to_lowercase().str.contains(query_lower, literal=False))
            | (pl.col("recipient").str.to_lowercase().str.contains(query_lower, literal=False))
            | (pl.col("body").str.to_lowercase().str.contains(query_lower, literal=False))
        )

    # Field-specific searches
    if sender:
        filters.append(pl.col("sender").str.to_lowercase().str.contains(sender.lower(), literal=False))

    if recipient:
        filters.append(pl.col("recipient").str.to_lowercase().str.contains(recipient.lower(), literal=False))

    if participant:
        participant_lower = participant.lower()
        filters.append(
            (pl.col("sender").str.to_lowercase().str.contains(participant_lower, literal=False))
            | (pl.col("recipient").str.to_lowercase().str.contains(participant_lower, literal=False))
        )

    if subject:
        filters.append(pl.col("subject").str.to_lowercase().str.contains(subject.lower(), literal=False))

    if body:
        filters.append(pl.col("body").str.to_lowercase().str.contains(body.lower(), literal=False))

    if path_search:
        filters.append(pl.col("path").str.to_lowercase().str.contains(path_search.lower(), literal=False))

    # Date filtering
    if start_date:
        start_dt = date(year=int(start_date[:4]), month=int(start_date[5:7]), day=int(start_date[8:10]))
        # Convert date to timezone-aware datetime (UTC) for comparison
        start_datetime = datetime.combine(start_dt, datetime.min.time(), tzinfo=timezone.utc)
        filters.append(pl.col("date") >= start_datetime)

    if end_date:
        # Add one day to make it inclusive
        end_dt = date(year=int(end_date[:4]), month=int(end_date[5:7]), day=int(end_date[8:10])) + timedelta(days=1)
        # Convert date to timezone-aware datetime (UTC) for comparison
        end_datetime = datetime.combine(end_dt, datetime.min.time(), tzinfo=timezone.utc)
        filters.append(pl.col("date") < end_datetime)

    # Tag filtering (jev_labels only)
    if tags and has_tag_support():
        if tag_mode == "and":
            for tag in tags:
                filters.append(pl.col("jev_labels").list.contains(tag))
        else:
            tag_filter = pl.col("jev_labels").list.contains(tags[0])
            for tag in tags[1:]:
                tag_filter = tag_filter | pl.col("jev_labels").list.contains(tag)
            filters.append(tag_filter)

    # Apply all filters
    if filters:
        combined_filter = filters[0]
        for f in filters[1:]:
            combined_filter = combined_filter & f
        filtered_df = df.filter(combined_filter)
    else:
        filtered_df = df

    # Sort by date descending first, then deduplicate to keep the most recent email for each (subject, body) pair
    sorted_df = filtered_df.sort("date", descending=True)
    deduplicated_df = sorted_df.unique(subset=["subject", "body"], keep="first")
    
    # Get deduplicated count
    total_count = len(deduplicated_df)
    
    # Sort again by date descending to ensure newest emails are first, then limit to 1000 results
    results_df = deduplicated_df.sort("date", descending=True).head(1000)
    
    # Convert to list of dicts for template rendering
    results: List[Dict[str, Any]] = []
    
    for row in results_df.iter_rows(named=True):
        results.append({
            "path": row["path"],
            "date": format_result_date(row["date"]),
            "subject": row["subject"],
            "sender": row["sender"],
            "recipient": row["recipient"],
            "body": row["body"],
            "tags": extract_row_tags(row),
        })

    return results, total_count


def get_email(path: str) -> Optional[Dict[str, Any]]:
    """Get a single email by path"""
    df = get_dataframe()
    result = df.filter(pl.col("path") == path)

    if len(result) == 0:
        return None

    row = result.row(0, named=True)
    return {
        "path": row["path"],
        "date": row["date"],
        "subject": row["subject"],
        "sender": row["sender"],
        "recipient": row["recipient"],
        "body": row["body"],
        "tags": extract_row_tags(row),
        "tag_scores": extract_tag_scores(row),
    }


def get_random_email() -> Optional[Tuple]:
    """Get a random email from the dataframe"""
    df = get_dataframe()
    result = df.sample(n=1)

    if len(result) == 0:
        return None

    row = result.row(0, named=False)
    return (row[0], row[1], row[2], row[3], row[4], row[5])  # path, date, subject, sender, recipient, body


def get_random_today_email() -> Optional[Tuple]:
    """Get a random email from today's date (any year)"""
    today = date.today()
    month = today.month
    day = today.day

    df = get_dataframe()
    result = df.filter(
        (pl.col("date").dt.month() == month) & (pl.col("date").dt.day() == day)
    ).sample(n=1)

    if len(result) == 0:
        return None

    row = result.row(0, named=False)
    return (row[0], row[1], row[2], row[3], row[4], row[5])  # path, date, subject, sender, recipient, body


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
