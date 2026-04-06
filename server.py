import json
import html
import gzip
import psycopg
from flask import Flask, Response, request
from time import perf_counter

from lego_set_binary_format import encode_lego_set_binary

app = Flask(__name__)

DB_CONFIG = {
    "host": "localhost",
    "port": 9876,
    "dbname": "lego-db",
    "user": "lego",
    "password": "bricks",
}


def _fetch_set_with_inventory(set_id):
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select id, name, year, category, preview_image_url
                from lego_set
                where id = %s
                """,
                (set_id,),
            )
            set_row = cur.fetchone()
            if set_row is None:
                return None

            cur.execute(
                """
                select
                    i.brick_type_id,
                    i.color_id,
                    i.count,
                    b.name,
                    b.preview_image_url
                from lego_inventory i
                join lego_brick b
                    on b.brick_type_id = i.brick_type_id
                   and b.color_id = i.color_id
                where i.set_id = %s
                order by i.brick_type_id, i.color_id
                """,
                (set_id,),
            )
            inventory_rows = cur.fetchall()

    return {
        "set": {
            "id": set_row[0],
            "name": set_row[1],
            "year": set_row[2],
            "category": set_row[3],
            "previewImageUrl": set_row[4],
        },
        "inventory": [
            {
                "brickTypeId": row[0],
                "colorId": row[1],
                "count": row[2],
                "name": row[3],
                "previewImageUrl": row[4],
            }
            for row in inventory_rows
        ],
    }


@app.route("/")
def index():
    with open("templates/index.html") as f:
        template = f.read()
    return Response(template)


@app.route("/sets")
def sets():
    with open("templates/sets.html") as f:
        template = f.read()
    requested_encoding = request.args.get("encoding", "").lower()
    encoding = requested_encoding if requested_encoding in ("utf-8", "utf-16") else "utf-8"
    meta_charset_tag = '<meta charset="UTF-8">' if encoding == "utf-8" else ""

    start_time = perf_counter()
    conn = psycopg.connect(**DB_CONFIG)
    try:
        rows_list = []
        with conn.cursor() as cur:
            cur.execute("select id, name from lego_set order by id")
            for row in cur.fetchall():
                html_safe_id = html.escape(row[0])
                html_safe_name = html.escape(row[1])
                # O(1) operation
                rows_list.append(f'<tr><td><a href="/set?id={html_safe_id}">{html_safe_id}</a></td><td>{html_safe_name}</td></tr>')
        print(f"Time to render all sets: {perf_counter() - start_time}")
    finally:
        conn.close()

    page_html = template.replace("{ROWS}", "\n".join(rows_list)).replace("{META_CHARSET}", meta_charset_tag)
    page_bytes = page_html.encode(encoding)
    compressed_page_bytes = gzip.compress(page_bytes)
    response = Response(compressed_page_bytes, content_type=f"text/html; charset={encoding}")
    response.headers["Content-Encoding"] = "gzip"
    return response


@app.route("/set")
def legoSet():  # We don't want to call the function `set`, since that would hide the `set` data type.
    with open("templates/set.html") as f:
        template = f.read()
    return Response(template)


@app.route("/api/set")
def apiSet():
    set_id = request.args.get("id")
    if not set_id:
        return Response(json.dumps({"error": "Missing set id"}, indent=4), status=400, content_type="application/json")

    result = _fetch_set_with_inventory(set_id)
    if result is None:
        return Response(json.dumps({"error": "Unknown set id"}, indent=4), status=404, content_type="application/json")

    json_result = json.dumps(result, indent=4)
    return Response(json_result, content_type="application/json")


@app.route("/api/set.bin")
def apiSetBinary():
    set_id = request.args.get("id")
    if not set_id:
        return Response("Missing set id", status=400, content_type="text/plain")

    result = _fetch_set_with_inventory(set_id)
    if result is None:
        return Response("Unknown set id", status=404, content_type="text/plain")

    binary_result = encode_lego_set_binary(result)
    return Response(binary_result, content_type="application/octet-stream")


if __name__ == "__main__":
    app.run(port=5000, debug=True)

# Note: If you define new routes, they have to go above the call to `app.run`.
