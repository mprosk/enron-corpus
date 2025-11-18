#!/usr/bin/env python3
"""
Modern Flask Web Application for Enron Email Corpus Viewer
Features: Responsive design with Tailwind CSS, mobile-first approach
"""

import html
import urllib.parse
from datetime import datetime, timedelta, date, timezone
from typing import List, Tuple, Optional
import os

import polars as pl
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from markupsafe import Markup

app = Flask(__name__)

# Configuration
PARQUET_FILE = os.environ.get("ENRON_PARQUET_FILE", "enron.pq")
_df_cache: Optional[pl.DataFrame] = None


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
    return render_template("index.html", total_count=total_count)


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

    # Check if at least one search criterion is provided
    if not any([search_query, sender, recipient, participant, subject, body, path_search, start_date, end_date]):
        return redirect(url_for("index"))

    # Perform search
    results, total_count = search_emails(
        search_query, sender, recipient, participant, subject, body, path_search, start_date, end_date
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
        count_text=count_text
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

    path, email_date, email_subject, email_sender, email_recipient, email_body = email_data

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
        random_type=random_type
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
) -> Tuple[List[Tuple], int]:
    """Search emails in the parquet file with field-specific or general search"""
    df = get_dataframe()

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
    
    # Convert to list of tuples matching the original format
    # Column order: path, date, subject, sender, recipient, body
    # Format dates as strings for template rendering
    results = []
    
    for row in results_df.iter_rows(named=False):
        date_val = row[1]
        if date_val:
            # Format datetime to show only date part
            if isinstance(date_val, datetime):
                # Subtract 5 hours for timezone adjustment before formatting date
                adjusted_date = date_val - timedelta(hours=5)
                date_str = adjusted_date.strftime("%Y-%m-%d")
            else:
                date_str = str(date_val).split()[0] if " " in str(date_val) else str(date_val)
        else:
            date_str = None
        
        results.append((row[0], date_str, row[2], row[3], row[4], row[5]))  # path, date, subject, sender, recipient, body

    return results, total_count


def get_email(path: str) -> Optional[Tuple]:
    """Get a single email by path"""
    df = get_dataframe()
    result = df.filter(pl.col("path") == path)

    if len(result) == 0:
        return None

    row = result.row(0, named=False)
    return (row[0], row[1], row[2], row[3], row[4], row[5])  # path, date, subject, sender, recipient, body


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

