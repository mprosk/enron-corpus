#!/usr/bin/env python3
"""
Simple Web 1.0-style Enron Email Corpus Viewer
Uses only Python standard library - no external packages required
"""

import sqlite3
import html
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import List, Tuple, Optional

DATABASE = "enron.db"


class EmailViewerHandler(BaseHTTPRequestHandler):
    """HTTP request handler for email search and viewing"""

    def do_GET(self) -> None:
        """Handle GET requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query_params = urllib.parse.parse_qs(parsed_path.query)

        if path == "/" or path == "/index.html":
            self.serve_index()
        elif path == "/search":
            search_query = query_params.get("q", [""])[0]
            sender = query_params.get("sender", [""])[0]
            recipient = query_params.get("recipient", [""])[0]
            participant = query_params.get("participant", [""])[0]
            subject = query_params.get("subject", [""])[0]
            body = query_params.get("body", [""])[0]
            path_search = query_params.get("path", [""])[0]
            start_date = query_params.get("start_date", [""])[0]
            end_date = query_params.get("end_date", [""])[0]
            self.serve_search_results(
                search_query,
                sender,
                recipient,
                participant,
                subject,
                body,
                path_search,
                start_date,
                end_date,
            )
        elif path == "/email":
            email_path = query_params.get("path", [""])[0]
            from_search = query_params.get("from_search", [""])[0] == "1"
            self.serve_email(email_path, from_search)
        elif path == "/random":
            self.serve_random_email()
        elif path == "/random_today":
            self.serve_random_today_email()
        else:
            self.send_error(404, "Page not found")

    def serve_index(self) -> None:
        """Serve the main search page"""
        html_content = """<!DOCTYPE html>
<html>
<head>
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
            <b>Database Statistics:</b> 517,401 emails available for search
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
                            <td style="border: none; padding: 5px;"><input type="date" id="start_date" name="start_date" style="width: 95%;"></td>
                        </tr>
                        <tr>
                            <td style="border: none; padding: 5px;"><label for="end_date">Date To:</label></td>
                            <td style="border: none; padding: 5px;"><input type="date" id="end_date" name="end_date" style="width: 95%;"></td>
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

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def serve_search_results(
        self,
        search_query: str = "",
        sender: str = "",
        recipient: str = "",
        participant: str = "",
        subject: str = "",
        body: str = "",
        path_search: str = "",
        start_date: str = "",
        end_date: str = "",
    ) -> None:
        """Search emails and display results in a table"""
        # Check if at least one search criterion is provided
        if not any(
            [
                search_query.strip(),
                sender.strip(),
                recipient.strip(),
                participant.strip(),
                subject.strip(),
                body.strip(),
                path_search.strip(),
                start_date,
                end_date,
            ]
        ):
            self.redirect_to_index()
            return

        # Search the database
        results, total_count = self.search_emails(
            search_query,
            sender,
            recipient,
            participant,
            subject,
            body,
            path_search,
            start_date,
            end_date,
        )

        # Build search criteria display text
        criteria_parts = []
        if search_query.strip():
            criteria_parts.append(f'Quick search: "{html.escape(search_query)}"')
        if sender.strip():
            criteria_parts.append(f'From: "{html.escape(sender)}"')
        if recipient.strip():
            criteria_parts.append(f'To: "{html.escape(recipient)}"')
        if participant.strip():
            criteria_parts.append(f'Participant: "{html.escape(participant)}"')
        if subject.strip():
            criteria_parts.append(f'Subject: "{html.escape(subject)}"')
        if body.strip():
            criteria_parts.append(f'Body: "{html.escape(body)}"')
        if path_search.strip():
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
            count_text = f"Found {total_count} result(s) (showing first 1000)"
        else:
            count_text = f"Found {total_count} result(s)"

        html_content = f"""<!DOCTYPE html>
<html>
<head>
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
                path, date, sender, recipient, subject, body = row

                # Escape HTML and create preview
                # Format date to only show date part (not time)
                if date:
                    date_only = str(date).split()[0] if " " in str(date) else str(date)
                    date_str = html.escape(date_only)
                else:
                    date_str = "N/A"

                subject_str = html.escape(subject if subject else "(no subject)")

                # Create body preview (first 200 chars for table)
                body_preview = body[:300] if body else ""
                body_preview = html.escape(
                    body_preview.replace("\n", " ").replace("\r", "")
                )
                if body and len(body) > 300:
                    body_preview += "..."

                # Create longer preview for hover popup (first 500 chars)
                body_hover = body[:1000].strip() if body else "(no content)"
                body_hover_escaped = html.escape(body_hover)
                if body and len(body) > 1000:
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

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def serve_email(self, email_path: str, from_search: bool = False) -> None:
        """Display full email content"""
        if not email_path:
            self.send_error(400, "Email path required")
            return

        # Get email from database
        email_data = self.get_email(email_path)

        if not email_data:
            self.send_error(404, "Email not found")
            return

        (
            db_path,
            email_date,
            email_sender,
            email_recipient,
            email_subject,
            email_body,
        ) = email_data

        # Escape HTML for headers
        date_str = html.escape(str(email_date) if email_date else "N/A")
        sender_str = html.escape(email_sender if email_sender else "N/A")
        recipient_str = html.escape(email_recipient if email_recipient else "N/A")
        subject_str = html.escape(email_subject if email_subject else "(no subject)")
        path_str = html.escape(db_path)

        # Detect if email body is HTML
        is_html = False
        body_content = email_body if email_body else "(no content)"
        if body_content:
            body_lower = body_content.lower()
            is_html = (
                "<html" in body_lower
                or "<body" in body_lower
                or "<table" in body_lower
                and "<tr" in body_lower
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
            # HTML emails don't get formatted view
            formatted_body_html = ""
        else:
            # Plain text - create both original and formatted versions
            body_str_original = html.escape(body_content)
            body_str_formatted = html.escape(format_body(body_content))
            body_html = f'<div id="body-original" class="email-body" style="display: none;">{body_str_original}</div>'
            formatted_body_html = f'<div id="body-formatted" class="email-body">{body_str_formatted}</div>'

        html_content = f"""<!DOCTYPE html>
<html>
<head>
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
            const path = {repr(db_path)};
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
            {"<a href='#' onclick='history.back(); return false;'>&lt;&lt; Back to Results</a>" if from_search else "<a href='/'>&lt;&lt; Back to Search</a>"}
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
            {"<a href='#' onclick='history.back(); return false;'>&lt;&lt; Back to Results</a>" if from_search else "<a href='/'>&lt;&lt; Back to Search</a>"}
        </div>
    </div>
</body>
</html>"""

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def redirect_to_index(self) -> None:
        """Redirect to index page"""
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def search_emails(
        self,
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
        """Search emails in the database with field-specific or general search"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Build the WHERE clause
        where_clauses = []
        params = []

        # If quick search query is provided, search across all fields
        if query.strip():
            search_pattern = f"%{query}%"
            where_clauses.append(
                "(subject LIKE ? COLLATE NOCASE OR sender LIKE ? COLLATE NOCASE OR recipient LIKE ? COLLATE NOCASE OR body LIKE ? COLLATE NOCASE)"
            )
            params.extend(
                [search_pattern, search_pattern, search_pattern, search_pattern]
            )

        # Add field-specific searches
        if sender.strip():
            where_clauses.append("sender LIKE ? COLLATE NOCASE")
            params.append(f"%{sender}%")

        if recipient.strip():
            where_clauses.append("recipient LIKE ? COLLATE NOCASE")
            params.append(f"%{recipient}%")

        if participant.strip():
            where_clauses.append(
                "(sender LIKE ? COLLATE NOCASE OR recipient LIKE ? COLLATE NOCASE)"
            )
            participant_pattern = f"%{participant}%"
            params.extend([participant_pattern, participant_pattern])

        if subject.strip():
            where_clauses.append("subject LIKE ? COLLATE NOCASE")
            params.append(f"%{subject}%")

        if body.strip():
            where_clauses.append("body LIKE ? COLLATE NOCASE")
            params.append(f"%{body}%")

        if path_search.strip():
            where_clauses.append("path LIKE ? COLLATE NOCASE")
            params.append(f"%{path_search}%")

        # Add date filtering
        if start_date:
            where_clauses.append("date >= ?")
            params.append(start_date)

        if end_date:
            # Add one day to end_date to make it inclusive
            where_clauses.append("date < date(?, '+1 day')")
            params.append(end_date)

        # Build final WHERE clause (default to 1=1 if no conditions)
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Get total count first
        count_sql = f"""
            SELECT COUNT(*)
            FROM emails
            WHERE {where_clause}
        """
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()[0]

        # Get results with limit
        query_sql = f"""
            SELECT path, date, sender, recipient, subject, body
            FROM emails
            WHERE {where_clause}
            ORDER BY date DESC
            LIMIT 1000
        """

        cursor.execute(query_sql, params)

        results = cursor.fetchall()
        conn.close()

        return results, total_count

    def get_email(self, path: str) -> Optional[Tuple]:
        """Get a single email by path"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT path, date, sender, recipient, subject, body
            FROM emails
            WHERE path = ?
        """,
            (path,),
        )

        result = cursor.fetchone()
        conn.close()

        return result

    def get_random_email(self) -> Optional[Tuple]:
        """Get a random email from the database"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT path, date, sender, recipient, subject, body
            FROM emails
            WHERE path IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 1
        """
        )

        result = cursor.fetchone()
        conn.close()

        return result

    def get_random_today_email(self) -> Optional[Tuple]:
        """Get a random email from today's date (any year)"""
        import datetime

        today = datetime.date.today()
        month = today.month
        day = today.day

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT path, date, sender, recipient, subject, body
            FROM emails
            WHERE strftime('%m', date) = ? 
              AND strftime('%d', date) = ?
              AND path IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 1
        """,
            (f"{month:02d}", f"{day:02d}"),
        )

        result = cursor.fetchone()
        conn.close()

        return result

    def serve_random_email(self) -> None:
        """Serve a random email"""
        email_data = self.get_random_email()

        if not email_data:
            self.send_error(404, "No emails found")
            return

        path = email_data[0]
        # Redirect to the email viewer
        encoded_path = urllib.parse.quote(path)
        self.send_response(302)
        self.send_header("Location", f"/email?path={encoded_path}")
        self.end_headers()

    def serve_random_today_email(self) -> None:
        """Serve a random email from today's date (any year)"""
        email_data = self.get_random_today_email()

        if not email_data:
            import datetime

            today = datetime.date.today()
            self.send_error(404, f"No emails found for {today.strftime('%B %d')}")
            return

        path = email_data[0]
        # Redirect to the email viewer
        encoded_path = urllib.parse.quote(path)
        self.send_response(302)
        self.send_header("Location", f"/email?path={encoded_path}")
        self.end_headers()

    def log_message(self, format: str, *args) -> None:
        """Log HTTP requests"""
        print(
            f"{self.address_string()} - [{self.log_date_time_string()}] {format % args}"
        )


def run_server(host: str = "localhost", port: int = 8000) -> None:
    """Start the HTTP server"""
    server_address = (host, port)
    httpd = HTTPServer(server_address, EmailViewerHandler)

    print(f"Starting Enron Email Corpus Viewer...")
    print(f"Server running at http://{host}:{port}/")
    print(f"Press Ctrl+C to stop the server")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()


if __name__ == "__main__":
    run_server()
