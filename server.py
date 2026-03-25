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


@app.route("/")
def index():
    # Fix file leak with open
    with open("templates/index.html") as f:
        template = f.read()
    return Response(template)


@app.route("/sets")
def sets():

    # Read encoding from query parameter (default utf-8)
    # Encode HTML before sending response
    encoding = request.args.get("encoding", "utf-8")

    if encoding not in ["utf-8", "utf-16"]:
        encoding = "utf-8"

    # Use 'with open' to ensure file is closed properly (avoid file handle leaks)
    with open("templates/sets.html") as f:
        template = f.read()
    
    rows = ""

    start_time = perf_counter()
    conn = psycopg.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute("select id, name from lego_set order by id")
            for row in cur.fetchall():
                html_safe_id = html.escape(row[0])
                html_safe_name = html.escape(row[1])
                existing_rows = rows
                rows = existing_rows + f'<tr><td><a href="/set?id={html_safe_id}">{html_safe_id}</a></td><td>{html_safe_name}</td></tr>\n'
        print(f"Time to render all sets: {perf_counter() - start_time}")
    finally:
        conn.close()

    page_html = template.replace("{ROWS}", rows)
    
    # Remove UTF-8 meta tag when using utf-16 to avoid conflicts
    if encoding != "utf-8":
        page_html = page_html.replace('<meta charset="UTF-8">', '')

    # encode
    encoded_html = page_html.encode(encoding)

    # Compress response using gzip to reduce response size
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
    result = {"set_id": set_id}
    json_result = json.dumps(result, indent=4)
    return Response(json_result, content_type="application/json")


if __name__ == "__main__":
    app.run(port=5000, debug=True)

# Note: If you define new routes, they have to go above the call to `app.run`.
