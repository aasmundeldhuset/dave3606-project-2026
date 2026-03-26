import json
import html
from collections import OrderedDict
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

SET_CACHE = OrderedDict()
MAX_CACHE_SIZE = 100

def get_set_json(set_id):
    conn = psycopg.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:

            # hent set info
            cur.execute(
                "SELECT id, name, year, category FROM lego_set WHERE id = %s",
                (set_id,)
            )
            set_row = cur.fetchone()

            if not set_row:
                return json.dumps({"error": "Set not found"}, indent=4)

            # hent inventory
            cur.execute(
                "SELECT brick_type_id, color_id, count FROM lego_inventory WHERE set_id = %s",
                (set_id,)
            )
            inventory_rows = cur.fetchall()

            result = {
                "set": {
                    "id": set_row[0],
                    "name": set_row[1],
                    "year": set_row[2],
                    "category": set_row[3],
                },
                "inventory": []
            }

            for row in inventory_rows:
                result["inventory"].append({
                    "brick_type_id": row[0],
                    "color_id": row[1],
                    "count": row[2],
                })

            return json.dumps(result, indent=4)

    finally:
        conn.close()

def get_cached_set_json(set_id):
    if set_id in SET_CACHE:
        SET_CACHE.move_to_end(set_id)
        return SET_CACHE[set_id]

    json_output = get_set_json(set_id)

    SET_CACHE[set_id] = json_output
    SET_CACHE.move_to_end(set_id)

    if len(SET_CACHE) > MAX_CACHE_SIZE:
        SET_CACHE.popitem(last=False)

    return json_output

@app.route("/")
def index():
    template = open("templates/index.html").read()
    return Response(template)


@app.route("/sets")
def sets():
    with open("templates/sets.html", encoding="utf-8") as f:
        template = f.read()
        
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
                    f'<tr><td><a href="/set?id={html_safe_id}">{html_safe_id}</a></td>'
                    f'<td>{html_safe_name}</td></tr>\n'
                )

        rows = "".join(row_parts)
        print(f"Time to render all sets: {perf_counter() - start_time}")
    finally:
        conn.close()

    page_html = template.replace("{ROWS}", rows)
    response = Response(page_html, content_type="text/html")
    response.headers["Cache-Control"] = "public, max-age=60"
    return response


@app.route("/set")
def legoSet():  # We don't want to call the function `set`, since that would hide the `set` data type.
    template = open("templates/set.html").read()
    return Response(template)


@app.route("/api/set")
def apiSet():
    set_id = request.args.get("id")
    json_result = get_cached_set_json(set_id)
    return Response(json_result, content_type="application/json")


if __name__ == "__main__":
    app.run(port=5000, debug=True)

# Note: If you define new routes, they have to go above the call to `app.run`.

# Husk å pull før du pusher!
