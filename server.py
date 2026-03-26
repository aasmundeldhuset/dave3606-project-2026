import json
import html
import re
import psycopg
from collections import OrderedDict
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

SET_CACHE = OrderedDict()
CACHE_LIMIT = 100


class Database:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def execute_and_fetch_all(self, query):
        self.connection = psycopg.connect(**DB_CONFIG)
        self.cursor = self.connection.cursor()
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def close(self):
        if self.cursor is not None:
            self.cursor.close()
            self.cursor = None
        if self.connection is not None:
            self.connection.close()
            self.connection = None


def render_index_page():
    with open("templates/index.html") as f:
        return f.read()


def render_sets_page(database):
    with open("templates/sets.html") as f:
        template = f.read()

    rows = database.execute_and_fetch_all("SELECT id, name FROM lego_set ORDER BY id")

    row_list = []
    for row in rows:
        html_safe_id = html.escape(row[0])
        html_safe_name = html.escape(row[1])
        row_list.append(
            f'<tr><td><a href="/set?id={html_safe_id}">{html_safe_id}</a></td><td>{html_safe_name}</td></tr>\n'
        )

    return template.replace("{ROWS}", "".join(row_list))


def render_set_page():
    with open("templates/set.html") as f:
        return f.read()


def is_valid_set_id(set_id):
    return set_id is not None and re.fullmatch(r"[A-Za-z0-9\-]+", set_id) is not None


def build_set_result(set_row, inventory_rows):
    result = {
        "set": {
            "id": set_row[0],
            "name": set_row[1],
            "year": set_row[2],
            "category": set_row[3],
            "preview_image_url": set_row[4]
        },
        "inventory": []
    }

    for row in inventory_rows:
        result["inventory"].append({
            "brick_type_id": row[0],
            "color_id": row[1],
            "count": row[2],
            "name": row[3] if row[3] is not None else "",
            "preview_image_url": row[4] if row[4] is not None else ""
        })

    return result


def get_set_result(database, set_id):
    if not set_id:
        return {"error": "Missing set id"}

    if not is_valid_set_id(set_id):
        return {"error": "Invalid set id"}

    if set_id in SET_CACHE:
        cached_result = SET_CACHE.pop(set_id)
        SET_CACHE[set_id] = cached_result
        print(f"Cache hit for {set_id}")
        return cached_result

    print(f"Cache miss for {set_id}")

    set_rows = database.execute_and_fetch_all(
        f"""
        SELECT id, name, year, category, preview_image_url
        FROM lego_set
        WHERE id = '{set_id}'
        """
    )

    if len(set_rows) == 0:
        return {"error": "Set not found"}

    set_row = set_rows[0]

    inventory_rows = database.execute_and_fetch_all(
        f"""
        SELECT
            i.brick_type_id,
            i.color_id,
            SUM(i.count) AS total_count,
            MAX(b.name) AS name,
            MAX(b.preview_image_url) AS preview_image_url
        FROM lego_inventory i
        JOIN lego_brick b
          ON i.brick_type_id = b.brick_type_id
         AND i.color_id = b.color_id
        WHERE i.set_id = '{set_id}'
        GROUP BY i.brick_type_id, i.color_id
        ORDER BY i.brick_type_id, i.color_id
        """
    )

    result = build_set_result(set_row, inventory_rows)

    if len(SET_CACHE) >= CACHE_LIMIT:
        SET_CACHE.popitem(last=False)

    SET_CACHE[set_id] = result
    return result


def render_api_set_json(database, set_id):
    result = get_set_result(database, set_id)
    return json.dumps(result, indent=4)


@app.route("/")
def index():
    page_html = render_index_page()
    return Response(page_html, content_type="text/html")


@app.route("/sets")
def sets():
    start_time = perf_counter()
    db = Database()
    try:
        page_html = render_sets_page(db)
        print(f"Time to render all sets: {perf_counter() - start_time}")

        response = Response(page_html, content_type="text/html")
        response.headers["Cache-Control"] = "public, max-age=60"
        return response
    finally:
        db.close()


@app.route("/set")
def legoSet():
    page_html = render_set_page()
    return Response(page_html, content_type="text/html")


@app.route("/api/set")
def apiSet():
    set_id = request.args.get("id")

    start_time = perf_counter()
    db = Database()
    try:
        json_result = render_api_set_json(db, set_id)
        print(f"Time to serve /api/set for {set_id}: {perf_counter() - start_time}")
        return Response(json_result, content_type="application/json")
    finally:
        db.close()


if __name__ == "__main__":
    app.run(port=5001, debug=True)