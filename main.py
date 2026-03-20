from flask import Flask, render_template, redirect, request, session
from datetime import datetime
from functools import wraps
import sqlite3, os

app = Flask(__name__)


def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not session.get("id"):
            return redirect("/login")
        return func(*args, **kwargs)

    return decorated_view


def session_check():
    if not session.get("name"):
        return redirect("/login")
    else:
        login_check = True
    return login_check


def get_db_connection():
    conn = sqlite3.connect("data/database.db")
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()
    return conn, cur


def get_foods():
    conn, cur = get_db_connection()
    cur.execute("SELECT DISTINCT food FROM pet_1")
    data = cur.fetchall()
    foods = [food["food"] for food in data]
    conn.close()

    return foods


@app.before_request
def construct_db():
    # check that db exists
    if not os.path.exists("data/database.db"):
        with open("data/database.db", "w"):
            pass
    conn, cur = get_db_connection()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS pets (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL, password TEXT NOT NULL, datetime TEXT DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.commit()
    conn.close()


@app.route("/")
def landing():
    return render_template("main/landing.html")


@app.route("/register")
def register():
    return render_template("main/register.html")


@app.route("/register-input", methods=["POST"])
def register_input():
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")

    conn, cur = get_db_connection()

    cur.execute(f"INSERT INTO pets (email, name, password) VALUES ('{email}', '{name}', '{password}')")
    conn.commit()

    cur.execute(f"SELECT id FROM pets WHERE email = '{email}'")
    row = cur.fetchone()
    id = row["id"]
    cur.execute(f"CREATE TABLE IF NOT EXISTS pet_{id} (id INTEGER PRIMARY KEY AUTOINCREMENT, food TEXT NOT NULL, given_percent INTEGER NOT NULL, eaten_percent INTEGER DEFAULT 0, datetime TEXT DEFAULT CURRENT_TIMESTAMP)")

    conn.close()

    session["id"] = id

    return redirect("/logs")


@app.route("/login")
def login():
    return render_template("main/login.html")


@app.route("/login-input", methods=["POST"])
def login_input():
    email = request.form.get("email")
    password = request.form.get("password")

    conn, cur = get_db_connection()
    cur.execute(f"SELECT id, password FROM pets WHERE email = '{email}'")
    data = cur.fetchone()
    id = data["id"]
    password_md5 = data["password"]
    
    if password_md5:
        if password == password_md5:
            session["id"] = id
            #CATCH ERRORS
    
    return redirect("/logs")


@login_required
@app.route("/logs")
def logs():
    id = session["id"]
    conn, cur = get_db_connection()
    cur.execute(f"SELECT id, food, given_percent, eaten_percent, datetime FROM pet_{id} ORDER BY datetime DESC")
    logs = [dict(row) for row in cur.fetchall()]
    conn.close()
    now = datetime.now()

    for log in logs:
        log_time = datetime.fromisoformat(log["datetime"])
        diff = now - log_time

        minutes = int(diff.total_seconds() // 60)

        if minutes < 60:
            log["datetime_str"] = f"{minutes} min ago"
        elif minutes < 1440:
            hours = minutes // 60
            log["datetime_str"] = f"{hours} hr ago"
        else:
            days = minutes // 1440
            log["datetime_str"] = f"{days} day ago"

    return render_template("main/logs.html", logs=logs)

@login_required
@app.route("/new-log")
def new_log():
    id = session["id"]
    foods = get_foods(id)
    return render_template("main/new-log.html", foods=foods)


@app.route("/new-log-input", methods=["POST"])
def new_log_input():
    id = session["id"]
    food = request.form.get("food")
    new_food = request.form.get("new_food")
    given_percent = int(request.form.get("given_percent"))

    if new_food != None:
        foods = get_foods()
        if new_food not in foods:
            food = new_food
            #CATCH ERRORS

    conn, cur = get_db_connection()
    cur.execute(f"INSERT INTO pet_{id} (food, given_percent) VALUES ('{food}', {given_percent})")
    conn.commit()
    conn.close()

    return redirect(f"/logs")


if __name__ == "__main__":
    app.run()