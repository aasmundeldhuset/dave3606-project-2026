import json
import html
import psycopg
from flask import Flask, Response, request
from time import perf_counter
import gzip

app = Flask(__name__)

DB_CONFIG = {
    "host": "localhost",
    "port": 9876,
    "dbname": "lego-db",
    "user": "lego",
    "password": "bricks",
}

def read_file(path):
    with open(path, encoding="utf-8") as f:
        return f.read()
    

@app.route("/")
def index():
    template = read_file("templates/index.html")
    return Response(template, content_type="text/html; charset=utf-8")


@app.route("/sets")
def sets():
    requested_encoding = request.args.get("encoding", "").lower()
    if requested_encoding in ["utf-8", "utf-16"]:
        encoding = requested_encoding
    else:
        encoding = "utf-8"
        
    template = read_file("templates/sets.html")
    rows = []

    start_time = perf_counter()
    conn = psycopg.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute("select id, name from lego_set order by id")
            for row in cur.fetchall():
                html_safe_id = html.escape(row[0])
                html_safe_name = html.escape(row[1])
                rows.append(f'<tr><td><a href="/set?id={html_safe_id}">{html_safe_id}</a></td><td>{html_safe_name}</td></tr>\n')
        print(f"Time to render all sets: {perf_counter() - start_time}")
    finally:
        conn.close()
        
    result = "".join(rows)
    
    if encoding == "utf-8":
        charset_meta = '<meta charset="UTF-8">'
    else:
        charset_meta = ""

    page_html = template.replace("{CHARSET_META}", charset_meta)
    page_html = page_html.replace("{ROWS}", result)
    
    encoded_html = page_html.encode(encoding)
    compressed_html = gzip.compress(encoded_html)
    
    return Response(compressed_html, content_type=f"text/html; charset={encoding}", headers={"Content-Encoding": "gzip"})


@app.route("/set")
def legoSet():  # We don't want to call the function `set`, since that would hide the `set` data type.
    template = read_file("templates/set.html")
    return Response(template, content_type="text/html; charset=utf-8")


@app.route("/api/set")
def apiSet():
    set_id = request.args.get("id")
    result = {"set_id": set_id}
    json_result = json.dumps(result, indent=4)
    return Response(json_result, content_type="application/json; charset=utf-8")


if __name__ == "__main__":
    app.run(port=5000, debug=True)

# Note: If you define new routes, they have to go above the call to `app.run`.
