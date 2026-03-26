import json
import html
import gzip
import psycopg
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


@app.route("/")
def index():
    with open("templates/index.html", encoding="utf-8") as f:
        template = f.read()
    return Response(template, content_type="text/html; charset=utf-8")


@app.route("/sets")
def sets():
    encoding = request.args.get("encoding", "utf-8").lower()
    if encoding not in ("utf-8", "utf-16"):
        encoding = "utf-8"

    with open("templates/sets.html", encoding="utf-8") as f:
        template = f.read()

    if encoding != "utf-8":
        template = template.replace('<meta charset="UTF-8">', "")

    row_parts = []

    start_time = perf_counter()
    conn = psycopg.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute("select id, name from lego_set order by id")
            for row in cur.fetchall():
                html_safe_id = html.escape(row[0])
                html_safe_name = html.escape(row[1])
                row_parts.append(
                    f'<tr><td><a href="/set?id={html_safe_id}">{html_safe_id}</a></td><td>{html_safe_name}</td></tr>\n'
                )
        print(f"Time to render all sets: {perf_counter() - start_time}")
    finally:
        conn.close()

    rows = "".join(row_parts)
    page_html = template.replace("{ROWS}", rows)

    encoded_html = page_html.encode(encoding)
    compressed_html = gzip.compress(encoded_html)

    response = Response(
        compressed_html,
        content_type=f"text/html; charset={encoding}"
    )
    response.headers["Content-Encoding"] = "gzip"
    return response


@app.route("/api/set")
def apiSet():
    set_id = request.args.get("id")
    result = {"set_id": set_id}
    json_result = json.dumps(result, indent=4)
    return Response(json_result, content_type="application/json")


if __name__ == "__main__":
    app.run(port=5000, debug=True)

# Note: If you define new routes, they have to go above the call to `app.run`.
