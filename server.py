import json
import html
import psycopg
import gzip
from flask import Flask, Response, request
from time import perf_counter

app = Flask(__name__)

DB_CONFIG = {
    "host": "localhost",
    "port": 9876,
    "dbname": "lego-db",
    "user": "lego",
    "password": "bricks",
}

# Datbase wrapper class to abstract psycopg usage
class Database:
    def __init__(self):
        self.conn = psycopg.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()

    def execute_and_fetch_all(self, query):
        self.cur.execute(query)
        return self.cur.fetchall()

    def close(self):
        self.cur.close()
        self.conn.close()

# Function separated from endpoint (for testability)
def get_sets_html(db):
    row_parts = []

    rows = db.execute_and_fetch_all(
        "select id, name from lego_set order by id"
    )

    for row in rows:
        html_safe_id = html.escape(row[0])
        html_safe_name = html.escape(row[1])
        row_parts.append(
            f'<tr><td><a href="/set?id={html_safe_id}">{html_safe_id}</a></td><td>{html_safe_name}</td></tr>'
        )

    return "".join(row_parts)

@app.route("/")
def index():
    # Fix file leak with open
    with open("templates/index.html") as f:
        template = f.read()
    return Response(template)


@app.route("/sets")
def sets():
   # encoding
    encoding = request.args.get("encoding", "utf-8")
    if encoding not in ["utf-8", "utf-16"]:
        encoding = "utf-8"

    # template
    with open("templates/sets.html") as f:
        template = f.read()

    # dependency injection
    db = Database()
    try:
        rows_html = get_sets_html(db)
    finally:
        db.close()

    page_html = template.replace("{ROWS}", rows_html)

    # encoding fix
    if encoding != "utf-8":
        page_html = page_html.replace('<meta charset="UTF-8">', '')

    # Encode and compress response
    encoded_html = page_html.encode(encoding)
    compressed = gzip.compress(encoded_html)

    return Response(
        compressed,
        content_type=f"text/html; charset={encoding}",
        headers={"Content-Encoding": "gzip"}
    )


@app.route("/set")
def legoSet():  # We don't want to call the function `set`, since that would hide the `set` data type.
    # Fix file leak
    with open("templates/set.html") as f:
        template = f.read()
    return Response(template)


@app.route("/api/set")
def apiSet():
    set_id = request.args.get("id")
    result = get_api_set_json(set_id)
    return Response(result, content_type="application/json")

# Separate function for JSON generation (testable)
def get_api_set_json(set_id):
    result = {"set_id": set_id}
    return json.dumps(result, indent=4)


if __name__ == "__main__":
    app.run(port=5000, debug=True)

# Note: If you define new routes, they have to go above the call to `app.run`.
