import json
import html
from collections import OrderedDict
import psycopg
from flask import Flask, Response, request
from time import perf_counter
from database import Database

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

def get_all_sets_html(database):
    with open("templates/sets.html", encoding="utf-8") as f:
        template = f.read()

    row_parts = []
    query = "SELECT id, name FROM lego_set ORDER BY id"

    for row in database.execute_and_fetch_all(query):
        html_safe_id = html.escape(row[0])
        html_safe_name = html.escape(row[1])
        row_parts.append(
            f'<tr><td><a href="/set?id={html_safe_id}">{html_safe_id}</a></td>'
            f'<td>{html_safe_name}</td></tr>\n'
        )

    rows = "".join(row_parts)
    return template.replace("{ROWS}", rows)
    
def get_set_html(database, set_id):
    with open("templates/set.html", encoding="utf-8") as f:
            template = f.read()
    return template

def get_set_json(database, set_id):
    query_set = "SELECT id, name, year, category FROM lego_set WHERE id = %s"
    query_inventory = "SELECT brick_type_id, color_id, count FROM lego_inventory WHERE set_id = %s"

    set_rows = database.execute_and_fetch_all(query_set, (set_id,))
    if not set_rows:
        return json.dumps({"error": "Set not found"}, indent=4)
    
    result = {
        "set": {
            "id": set_rows[0][0],
            "name": set_rows[0][1],
            "year": set_rows[0][2],
            "category": set_rows[0][3],
        },
        "inventory": [],
    }

    for row in database.execute_and_fetch_all(query_inventory, (set_id,)):
        result["inventory"].append({
            "brick_type_id": row[0],
            "color_id": row [1],
            "count": row[2],
        })

    return json.dumps(result, indent=4)


def get_cached_set_json(database, set_id):
    if set_id in SET_CACHE:
        SET_CACHE.move_to_end(set_id)
        return SET_CACHE[set_id]

    json_output = get_set_json(database, set_id)

    SET_CACHE[set_id] = json_output
    SET_CACHE.move_to_end(set_id)

    if len(SET_CACHE) > MAX_CACHE_SIZE:
        SET_CACHE.popitem(last=False)

    return json_output

@app.route("/")
def index():
    with open("templates/index.html", encoding="utf-8") as f:
        template = f.read()
    return Response(template, content_type="text/html")


@app.route("/sets")
def sets():
    database = Database(DB_CONFIG)
    html_output = get_all_sets_html(database)
    response = Response(html_output, content_type="text/html")
    response.headers["Cache-Control"] = "public, max-age=60"
    return response

@app.route("/set")
def lego_set_page():  # We don't want to call the function `set`, since that would hide the `set` data type.
    set_id = request.args.get("id")
    database = Database(DB_CONFIG)
    html_output = get_set_html(database, set_id)
    return Response(html_output, content_type="text/html")


@app.route("/api/set")
def apiSet():
    set_id = request.args.get("id")
    database = Database(DB_CONFIG)
    json_output = get_cached_set_json(database, set_id)
    return Response(json_output, content_type="application/json")


if __name__ == "__main__":
    app.run(port=5000, debug=True)

# Note: If you define new routes, they have to go above the call to `app.run`.

# Husk å pull før du pusher!
