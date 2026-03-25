import json
import html
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

DB = Database(config=DB_CONFIG)

def get_all_sets_html(database):
    with open("templates/sets.html") as f:
        template = f.read()
    rows = ""
    start_time = perf_counter()
    query = "SELECT id, name FROM lego_set ORDER BY id"
    for row in database.execute_and_fetch_all(query):
        html_safe_id = html.escape(row[0])
        html_safe_name = html.escape(row[1])
        rows+= f'<tr><td><a href="/set?id={html_safe_id}">{html_safe_id}</a></td><td>{html_safe_name}</td></tr>\n'
    print(f"Time to render all sets: {perf_counter() - start_time}")
    return template.replace("{ROWS}", rows)

def get_set_html(database, set_id):
    with open("templates/set.html") as f:
        template = f.read()
    return template

def get_set_json(database, set_id):
    query_set = "SELECT id, name, year, category FROM lego_set WHERE id = %s"
    query_inventory = "SELECT brick_type_id, color_id, count FROM lego_inventory WHERE set_id = %s"
    set_rows = database.execute_and_fetch_all(query_set, (set_id,))
    if not set_rows:
        return json.dumps({"error": "Set not found"}, indent=4)
    
    set_data = {
        "id": set_rows[0][0],
        "name": set_rows[0][1],
        "year": set_rows[0][2],
        "category": set_rows[0][3],
        "inventory": [],
    }
    
    for brick in database.execute_and_fetch_all(query_inventory, (set_id,)):
        set_data["inventory"].append({
            "brick_type_id": brick[0],
            "color_id": brick[1],
            "count": brick[2],
        })
    return json.dumps(set_data, indent=4)

@app.route("/")
def index():
    with open("templates/index.html") as f:
        template = f.read()
    return Response(template)


@app.route("/sets")
def sets():
    html_output = get_all_sets_html(DB)
    return Response(html_output, content_type="text/html")


@app.route("/set")
def lego_set_page():
    set_id = request.args.get("id")
    html_output = get_set_html(DB, set_id)
    return Response(html_output, content_type="text/html")


@app.route("/api/set")
def api_set():
    set_id = request.args.get("id")
    json_output = get_set_json(DB, set_id)
    return Response(json_output, content_type="application/json")


if __name__ == "__main__":
    app.run(port=5000, debug=True)

# Note: If you define new routes, they have to go above the call to `app.run`.
