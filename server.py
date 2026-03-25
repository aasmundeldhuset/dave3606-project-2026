import json
import html
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
 
 
class Database:
    def __init__(self):
        self.conn = psycopg.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
 
    def execute_and_fetch_all(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchall()
 
    def close(self):
        self.cursor.close()
        self.conn.close()
 
 
@app.route("/")
def index():
    template = open("templates/index.html").read()
    return Response(template)
 
 
def get_sets_html(db):
    template = open("templates/sets.html").read()
    rows = ""
 
    start_time = perf_counter()
    for row in db.execute_and_fetch_all("select id, name from lego_set order by id"):
        html_safe_id = html.escape(row[0])
        html_safe_name = html.escape(row[1])
        existing_rows = rows
        rows = existing_rows + f'<tr><td><a href="/set?id={html_safe_id}">{html_safe_id}</a></td><td>{html_safe_name}</td></tr>\n'
    db.close()
    print(f"Time to render all sets: {perf_counter() - start_time}")
 
    return template.replace("{ROWS}", rows)
 
 
@app.route("/sets")
def sets():
    db = Database()
    return Response(get_sets_html(db), content_type="text/html")
 
 
@app.route("/set")
def legoSet():  # We don't want to call the function `set`, since that would hide the `set` data type.
    template = open("templates/set.html").read()
    return Response(template)
 
 
def get_api_set_json(set_id, db):
    result = {"set_id": set_id}
    db.close()
    return json.dumps(result, indent=4)
 
 
@app.route("/api/set")
def apiSet():
    set_id = request.args.get("id")
    db = Database()
    return Response(get_api_set_json(set_id, db), content_type="application/json")
 
 
if __name__ == "__main__":
    app.run(port=5000, debug=True)