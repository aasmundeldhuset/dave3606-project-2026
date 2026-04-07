import json
import html
import gzip
from collections import OrderedDict
from threading import Lock
from flask import Flask, Response, request
from time import perf_counter

from database import Database
from lego_set_binary_format import encode_lego_set_binary

app = Flask(__name__)

DB_CONFIG = {
    "host": "localhost",
    "port": 9876,
    "dbname": "lego-db",
    "user": "lego",
    "password": "bricks",
}

SET_CACHE_CAPACITY = 100
SET_CACHE = OrderedDict()
SET_CACHE_LOCK = Lock()

SETS_QUERY = "select id, name from lego_set order by id"


def _get_cached_set(set_id):
    with SET_CACHE_LOCK:
        cached = SET_CACHE.get(set_id)
        if cached is not None:
            # LRU: mark this key as most recently used.
            SET_CACHE.move_to_end(set_id)
        return cached


def _put_cached_set(set_id, payload):
    with SET_CACHE_LOCK:
        SET_CACHE[set_id] = payload
        SET_CACHE.move_to_end(set_id)
        if len(SET_CACHE) > SET_CACHE_CAPACITY:
            SET_CACHE.popitem(last=False)


def _sql_quote(value):
    return str(value).replace("'", "''")


def _set_query(set_id):
    return (
        "select id, name, year, category, preview_image_url "
        "from lego_set "
        f"where id = '{_sql_quote(set_id)}'"
    )


def _inventory_query(set_id):
    return (
        "select i.brick_type_id, i.color_id, i.count, b.name, b.preview_image_url "
        "from lego_inventory i "
        "join lego_brick b on b.brick_type_id = i.brick_type_id and b.color_id = i.color_id "
        f"where i.set_id = '{_sql_quote(set_id)}' "
        "order by i.brick_type_id, i.color_id"
    )


def _fetch_set_with_inventory(database, set_id):
    cached_result = _get_cached_set(set_id)
    if cached_result is not None:
        print(f"/api/set cache hit for {set_id}")
        return cached_result

    start_time = perf_counter()
    set_rows = database.execute_and_fetch_all(_set_query(set_id))
    if len(set_rows) == 0:
        return None
    set_row = set_rows[0]
    inventory_rows = database.execute_and_fetch_all(_inventory_query(set_id))

    payload = {
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
    _put_cached_set(set_id, payload)
    print(f"/api/set cache miss for {set_id}, DB fetch took {perf_counter() - start_time:.6f}s")
    return payload


def generate_sets_page_html(database, template, encoding):
    meta_charset_tag = '<meta charset="UTF-8">' if encoding == "utf-8" else ""
    start_time = perf_counter()
    rows = database.execute_and_fetch_all(SETS_QUERY)

    rows_list = []
    for row in rows:
        html_safe_id = html.escape(row[0])
        html_safe_name = html.escape(row[1])
        rows_list.append(f'<tr><td><a href="/set?id={html_safe_id}">{html_safe_id}</a></td><td>{html_safe_name}</td></tr>')

    print(f"Time to render all sets: {perf_counter() - start_time}")
    return template.replace("{ROWS}", "\n".join(rows_list)).replace("{META_CHARSET}", meta_charset_tag)


def generate_set_json(database, set_id):
    payload = _fetch_set_with_inventory(database, set_id)
    if payload is None:
        return None
    return json.dumps(payload, indent=4)


def generate_set_binary(database, set_id):
    payload = _fetch_set_with_inventory(database, set_id)
    if payload is None:
        return None
    return encode_lego_set_binary(payload)


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

    database = Database(DB_CONFIG)
    try:
        page_html = generate_sets_page_html(database, template, encoding)
    finally:
        database.close()

    page_bytes = page_html.encode(encoding)
    compressed_page_bytes = gzip.compress(page_bytes)
    response = Response(compressed_page_bytes, content_type=f"text/html; charset={encoding}")
    response.headers["Content-Encoding"] = "gzip"
    response.headers["Cache-Control"] = "public, max-age=60"
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

    database = Database(DB_CONFIG)
    try:
        json_result = generate_set_json(database, set_id)
    finally:
        database.close()

    if json_result is None:
        return Response(json.dumps({"error": "Unknown set id"}, indent=4), status=404, content_type="application/json")
    return Response(json_result, content_type="application/json")


@app.route("/api/set.bin")
def apiSetBinary():
    set_id = request.args.get("id")
    if not set_id:
        return Response("Missing set id", status=400, content_type="text/plain")

    database = Database(DB_CONFIG)
    try:
        binary_result = generate_set_binary(database, set_id)
    finally:
        database.close()

    if binary_result is None:
        return Response("Unknown set id", status=404, content_type="text/plain")
    return Response(binary_result, content_type="application/octet-stream")


if __name__ == "__main__":
    app.run(port=5000, debug=True)

# Note: If you define new routes, they have to go above the call to `app.run`.
