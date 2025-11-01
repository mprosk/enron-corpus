#!/usr/bin/env python3
"""
Flask Web Application for Enron Email Corpus Viewer
"""

import html
import urllib.parse
from datetime import datetime
from typing import List, Tuple, Optional
import os

import polars as pl
from flask import Flask, render_template_string, request, redirect, url_for, send_from_directory

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


@app.route("/favicon.png")
def favicon():
    """Serve the favicon.png file"""
    return send_from_directory(".", "favicon.png")


@app.route("/")
@app.route("/index.html")
def index():
    """Serve the main search page"""
    total_count = get_total_count()
    html_content = """<!DOCTYPE html>
<html>
<head>
    <link rel="icon" type="image/png" href="/favicon.png">
    <title>Enron Email Corpus Search</title>
    <style>
        body {
            font-family: Arial, Helvetica, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: white;
        }
        .container {
            width: 100%;
        }
        h1 {
            color: #000080;
            border-bottom: 3px solid #000080;
            padding-bottom: 10px;
        }
        .search-box {
            margin: 20px 0;
            padding: 15px;
            background-color: #e0e0e0;
            border: 2px solid #999;
        }
        input[type="text"] {
            width: 70%;
            padding: 8px;
            font-size: 14px;
            border: 2px solid #666;
        }
        input[type="date"] {
            padding: 8px;
            font-size: 14px;
            border: 2px solid #666;
            margin: 5px;
        }
        input[type="submit"] {
            padding: 8px 20px;
            font-size: 14px;
            background-color: #ccc;
            border: 2px outset #999;
            cursor: pointer;
        }
        input[type="submit"]:active {
            border-style: inset;
        }
        .date-range {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #999;
        }
        .random-box {
            margin: 20px 0;
            padding: 15px;
            background-color: #e0e0e0;
            border: 2px solid #999;
            text-align: center;
        }
        .random-box a {
            display: inline-block;
            padding: 10px 20px;
            margin: 5px;
            font-size: 14px;
            background-color: #ccc;
            border: 2px outset #999;
            cursor: pointer;
            text-decoration: none;
            color: black;
        }
        .random-box a:hover {
            background-color: #bbb;
        }
        .random-box a:active {
            border-style: inset;
        }
        .info {
            margin: 20px 0;
            padding: 10px;
            background-color: #ffffcc;
            border: 1px solid #cccc99;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Enron Email Corpus Search</h1>
        
        <div class="info">
            <b>Database Statistics:</b> """ + f"{total_count:,} emails available for search" + """
        </div>
        
        <div class="search-box">
            <form action="/search" method="GET">
                <label for="q"><b>Quick Search:</b></label><br><br>
                <input type="text" id="q" name="q" placeholder="Search all fields">
                <input type="submit" value="Search">
                
                <div class="date-range">
                    <label><b>Advanced Search:</b></label><br><br>
                    <table style="width: 100%; border: none;">
                        <tr>
                            <td style="border: none; padding: 5px; width: 80px;"><label for="sender">From:</label></td>
                            <td style="border: none; padding: 5px;"><input type="text" id="sender" name="sender" placeholder="Sender email or name" style="width: 95%;"></td>
                        </tr>
                        <tr>
                            <td style="border: none; padding: 5px;"><label for="recipient">To:</label></td>
                            <td style="border: none; padding: 5px;"><input type="text" id="recipient" name="recipient" placeholder="Recipient email or name" style="width: 95%;"></td>
                        </tr>
                        <tr>
                            <td style="border: none; padding: 5px;"><label for="participant">Participant:</label></td>
                            <td style="border: none; padding: 5px;"><input type="text" id="participant" name="participant" placeholder="Sender OR recipient (either)" style="width: 95%;"></td>
                        </tr>
                        <tr>
                            <td style="border: none; padding: 5px;"><label for="subject">Subject:</label></td>
                            <td style="border: none; padding: 5px;"><input type="text" id="subject" name="subject" placeholder="Subject text" style="width: 95%;"></td>
                        </tr>
                        <tr>
                            <td style="border: none; padding: 5px;"><label for="body">Body:</label></td>
                            <td style="border: none; padding: 5px;"><input type="text" id="body" name="body" placeholder="Body text" style="width: 95%;"></td>
                        </tr>
                        <tr>
                            <td style="border: none; padding: 5px;"><label for="path">Path:</label></td>
                            <td style="border: none; padding: 5px;"><input type="text" id="path" name="path" placeholder="Email file path (e.g., lay-k/sent)" style="width: 95%;"></td>
                        </tr>
                        <tr>
                            <td style="border: none; padding: 5px;"><label for="start_date">Date From:</label></td>
                            <td style="border: none; padding: 5px;"><input type="date" id="start_date" name="start_date""></td>
                        </tr>
                        <tr>
                            <td style="border: none; padding: 5px;"><label for="end_date">Date To:</label></td>
                            <td style="border: none; padding: 5px;"><input type="date" id="end_date" name="end_date"></td>
                        </tr>
                    </table>
                    <div style="margin-top: 10px; margin-left: 100px;">
                        <input type="submit" value="Advanced Search">
                    </div>
                </div>
            </form>
        </div>
        
        <div class="random-box">
            <b>Random Email:</b><br><br>
            <a href="/random">Show Random Email</a>
            <a href="/random_today">Show Random Email from Today's Date</a>
        </div>
        
        <div class="info">
            <b>Instructions:</b>
            <ul>
                <li><b>Quick Search:</b> Enter text to search across all fields (subject, sender, recipient, and body)</li>
                <li><b>Advanced Search:</b> Use the fields below to search specific parts of emails</li>
                <li><b>Participant:</b> Find emails where someone was involved (either as sender OR recipient)</li>
                <li><b>Path:</b> Filter by email file path (e.g., "lay-k/sent" or "inbox")</li>
                <li>You can combine multiple advanced search fields together</li>
                <li>Date range search works alone or with other criteria (emails are mainly from 1999-2003)</li>
                <li>All searches are case-insensitive</li>
                <li>Results limited to 1000 emails per search</li>
                <li>Click on any email to view its full contents</li>
                <li>Use the random email buttons to explore the corpus</li>
            </ul>
        </div>
    </div>
</body>
</html>"""

    return html_content


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

    # Build search criteria display text
    criteria_parts = []
    if search_query:
        criteria_parts.append(f'Quick search: "{html.escape(search_query)}"')
    if sender:
        criteria_parts.append(f'From: "{html.escape(sender)}"')
    if recipient:
        criteria_parts.append(f'To: "{html.escape(recipient)}"')
    if participant:
        criteria_parts.append(f'Participant: "{html.escape(participant)}"')
    if subject:
        criteria_parts.append(f'Subject: "{html.escape(subject)}"')
    if body:
        criteria_parts.append(f'Body: "{html.escape(body)}"')
    if path_search:
        criteria_parts.append(f'Path: "{html.escape(path_search)}"')
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

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <link rel="icon" type="image/png" href="/favicon.png">
    <title>Search Results</title>
    <style>
        body {{
            font-family: Arial, Helvetica, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: white;
        }}
        .container {{
            width: 100%;
        }}
        h1 {{
            color: #000080;
            border-bottom: 3px solid #000080;
            padding-bottom: 10px;
        }}
        .back-link {{
            margin: 10px 0;
        }}
        .result-count {{
            margin: 15px 0;
            padding: 10px;
            background-color: #ffffcc;
            border: 1px solid #cccc99;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: white;
        }}
        th {{
            background-color: #cccccc;
            border: 2px solid #666;
            padding: 8px;
            text-align: left;
            font-weight: bold;
        }}
        td {{
            border: 1px solid #999;
            padding: 8px;
            position: relative;
        }}
        tbody tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tbody tr:hover {{
            background-color: #e0e0ff;
        }}
        tbody tr .email-preview {{
            display: none;
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            top: 100%;
            z-index: 1000;
            background-color: #ffffee;
            border: 2px solid #666;
            padding: 10px;
            min-width: 600px;
            max-width: 800px;
            white-space: pre-wrap;
            font-family: monospace;
            font-size: 11px;
            box-shadow: 3px 3px 5px rgba(0,0,0,0.3);
            margin-top: 2px;
        }}
        tbody tr:hover .email-preview {{
            display: block;
        }}
        a {{
            color: #0000ff;
            text-decoration: underline;
        }}
        a:visited {{
            color: #800080;
        }}
        a:hover {{
            color: #ff0000;
        }}
        .truncate {{
            max-width: 400px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Search Results</h1>
        
        <div class="back-link">
            <a href="/">&lt;&lt; Back to Search</a>
        </div>
        
        <div class="result-count">
            Search criteria: {search_criteria_text} | {count_text}
        </div>
        
"""

    if results:
        html_content += """
        <table>
            <thead>
            <tr>
                <th width="100">Date</th>
                <th width="250">Subject</th>
                <th>Preview</th>
            </tr>
            </thead>
            <tbody>
"""

        for row in results:
            path, date, subject, sender, recipient, body_content = row

            # Format date to only show date part (not time)
            if date:
                date_str = html.escape(str(date).split()[0] if " " in str(date) else str(date))
            else:
                date_str = "N/A"

            subject_str = html.escape(subject if subject else "(no subject)")

            # Create body preview (first 300 chars for table)
            body_preview = body_content[:300] if body_content else ""
            body_preview = html.escape(body_preview.replace("\n", " ").replace("\r", ""))
            if body_content and len(body_content) > 300:
                body_preview += "..."

            # Create longer preview for hover popup (first 1000 chars)
            body_hover = body_content[:1000].strip() if body_content else "(no content)"
            body_hover_escaped = html.escape(body_hover)
            if body_content and len(body_content) > 1000:
                body_hover_escaped += "\n..."

            # URL encode the path and add flag to indicate we came from search
            encoded_path = urllib.parse.quote(path)
            email_url = f"/email?path={encoded_path}&from_search=1"

            html_content += f"""
            <tr>
                <td>{date_str}</td>
                <td><a href="{email_url}">{subject_str}</a></td>
                <td>
                    {body_preview}
                    <div class="email-preview">{body_hover_escaped}</div>
                </td>
            </tr>
"""

        html_content += """
            </tbody>
        </table>
        
        <div class="back-link">
            <a href="/">&lt;&lt; Back to Search</a>
        </div>
"""
    else:
        html_content += """
        <p><i>No results found. Try a different search term.</i></p>
        
        <div class="back-link">
            <a href="/">&lt;&lt; Back to Search</a>
        </div>
"""

    html_content += """
    </div>
</body>
</html>"""

    return html_content


@app.route("/email")
def email():
    """Display full email content"""
    email_path = request.args.get("path", "").strip()
    from_search = request.args.get("from_search", "0") == "1"

    if not email_path:
        return "Email path required", 400

    # Get email from dataframe
    email_data = get_email(email_path)

    if email_data is None:
        return "Email not found", 404

    path, email_date, email_subject, email_sender, email_recipient, email_body = email_data

    # Escape HTML for headers
    date_str = html.escape(str(email_date) if email_date else "N/A")
    sender_str = html.escape(email_sender if email_sender else "N/A")
    recipient_str = html.escape(email_recipient if email_recipient else "N/A")
    subject_str = html.escape(email_subject if email_subject else "(no subject)")
    path_str = html.escape(path)

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
        return "\n".join(formatted_lines)

    # Render body based on content type
    if is_html:
        # Escape HTML for iframe srcdoc attribute
        escaped_body = html.escape(body_content, quote=True)
        body_html = f'<div class="email-body-html"><iframe srcdoc="{escaped_body}"></iframe></div>'
        formatted_body_html = ""
    else:
        # Plain text - create both original and formatted versions
        body_str_original = html.escape(body_content)
        body_str_formatted = html.escape(format_body(body_content))
        body_html = f'<div id="body-original" class="email-body" style="display: none;">{body_str_original}</div>'
        formatted_body_html = f'<div id="body-formatted" class="email-body">{body_str_formatted}</div>'

    back_link_html = (
        '<a href="#" onclick="history.back(); return false;">&lt;&lt; Back to Results</a>'
        if from_search
        else '<a href="/">&lt;&lt; Back to Search</a>'
    )

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <link rel="icon" type="image/png" href="/favicon.png">
    <title>{subject_str}</title>
    <style>
        body {{
            font-family: Arial, Helvetica, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: white;
        }}
        .container {{
            width: 100%;
        }}
        h1 {{
            color: #000080;
            border-bottom: 3px solid #000080;
            padding-bottom: 10px;
        }}
        .back-link {{
            margin: 10px 0;
        }}
        .email-header {{
            background-color: #e0e0e0;
            border: 2px solid #999;
            padding: 15px;
            margin: 20px 0;
        }}
        .email-header table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .email-header td {{
            padding: 5px;
            vertical-align: top;
        }}
        .email-header .label {{
            font-weight: bold;
            width: 100px;
        }}
        .email-body {{
            background-color: white;
            border: 2px solid #999;
            padding: 15px;
            margin: 20px 0;
            white-space: pre-wrap;
            font-family: monospace;
            font-size: 12px;
        }}
        .email-body-html {{
            background-color: white;
            border: 2px solid #999;
            margin: 20px 0;
            min-height: 800px;
        }}
        .email-body-html iframe {{
            width: 100%;
            min-height: 800px;
            border: none;
        }}
        a {{
            color: #0000ff;
            text-decoration: underline;
        }}
        a:visited {{
            color: #800080;
        }}
        a:hover {{
            color: #ff0000;
        }}
        .copy-link {{
            margin-left: 10px;
            font-size: 12px;
            cursor: pointer;
        }}
    </style>
    <script>
        function switchView(viewMode) {{
            const original = document.getElementById('body-original');
            const formatted = document.getElementById('body-formatted');
            
            if (viewMode === 'original') {{
                original.style.display = 'block';
                formatted.style.display = 'none';
            }} else {{
                original.style.display = 'none';
                formatted.style.display = 'block';
            }}
        }}
        
        function copyMdLink() {{
            const subject = {repr(email_subject if email_subject else "(no subject)")};
            const path = {repr(path)};
            const mdLink = `[${{subject}}](${{path}})`;
            
            navigator.clipboard.writeText(mdLink).catch(err => {{
                alert('Failed to copy: ' + err);
            }});
        }}
    </script>
</head>
<body>
    <div class="container">
        <h1>Email Details</h1>
        
        <div class="back-link">
            {back_link_html}
        </div>
        
        <div class="email-header">
            <table>
                <tr>
                    <td class="label">Date:</td>
                    <td>{date_str}</td>
                </tr>
                <tr>
                    <td class="label">From:</td>
                    <td>{sender_str}</td>
                </tr>
                <tr>
                    <td class="label">To:</td>
                    <td>{recipient_str}</td>
                </tr>
                <tr>
                    <td class="label">Subject:</td>
                    <td>{subject_str}</td>
                </tr>
                <tr>
                    <td class="label">Path:</td>
                    <td><small>{path_str}</small> <a href="#" onclick="copyMdLink(); return false;" class="copy-link">copy md link</a></td>
                </tr>
                {"" if is_html else '''<tr>
                    <td class="label">View:</td>
                    <td>
                        <label><input type="radio" name="view" value="original" onclick="switchView('original')"> Original</label>
                        <label style="margin-left: 15px;"><input type="radio" name="view" value="formatted" onclick="switchView('formatted')" checked> Formatted</label>
                    </td>
                </tr>'''}
            </table>
        </div>
        
        {body_html}
        {formatted_body_html}
        
        <div class="back-link">
            {back_link_html}
        </div>
    </div>
</body>
</html>"""

    return html_content


@app.route("/random")
def random_email():
    """Serve a random email"""
    email_data = get_random_email()

    if email_data is None:
        return "No emails found", 404

    path = email_data[0]
    encoded_path = urllib.parse.quote(path)
    return redirect(url_for("email", path=encoded_path))


@app.route("/random_today")
def random_today_email():
    """Serve a random email from today's date (any year)"""
    email_data = get_random_today_email()

    if email_data is None:
        from datetime import date
        today = date.today()
        return f"No emails found for {today.strftime('%B %d')}", 404

    path = email_data[0]
    encoded_path = urllib.parse.quote(path)
    return redirect(url_for("email", path=encoded_path))


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
        from datetime import date as dt_date, datetime as dt_datetime
        start_dt = dt_date(year=int(start_date[:4]), month=int(start_date[5:7]), day=int(start_date[8:10]))
        # Convert date to datetime for comparison
        start_datetime = dt_datetime.combine(start_dt, dt_datetime.min.time())
        filters.append(pl.col("date") >= start_datetime)

    if end_date:
        # Add one day to make it inclusive
        from datetime import date as dt_date, datetime as dt_datetime, timedelta
        end_dt = dt_date(year=int(end_date[:4]), month=int(end_date[5:7]), day=int(end_date[8:10])) + timedelta(days=1)
        # Convert date to datetime for comparison
        end_datetime = dt_datetime.combine(end_dt, dt_datetime.min.time())
        filters.append(pl.col("date") < end_datetime)

    # Apply all filters
    if filters:
        combined_filter = filters[0]
        for f in filters[1:]:
            combined_filter = combined_filter & f
        filtered_df = df.filter(combined_filter)
    else:
        filtered_df = df

    # Get total count
    total_count = len(filtered_df)

    # Sort by date descending and limit to 1000
    results_df = filtered_df.sort("date", descending=True).head(1000)

    # Convert to list of tuples matching the original format
    # Column order: path, date, subject, sender, recipient, body
    results = []
    for row in results_df.iter_rows(named=False):
        results.append((row[0], row[1], row[2], row[3], row[4], row[5]))  # path, date, subject, sender, recipient, body

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
    from datetime import date

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

