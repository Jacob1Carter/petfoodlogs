from flask import Flask, render_template, redirect, request
import sqlite3, os

app = Flask(__name__)


def get_db_connection():
    conn = sqlite3.connect("data/database.db")
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()
    return conn, cur


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
    cur.execute(f"CREATE TABLE IF NOT EXISTS pet_{id} (id INTEGER PRIMARY KEY AUTOINCREMENT, food TEXT UNIQUE NOT NULL, given_percent INTEGER NOT NULL, eaten_percent INTEGER DEFAULT 0, datetime TEXT DEFAULT CURRENT_TIMESTAMP)")

    conn.close()

    return redirect("/")


@app.route("/login")
def login():
    return render_template("main/login.html")


@app.route("/logs/<id>")
def logs(id):
    conn, cur = get_db_connection()
    cur.execute(f"SELECT id, food, given_percent, eaten_percent FROM pet_{id} ORDER BY datetime")
    logs = cur.fetchall()

    return render_template("main/logs.html", logs=logs)


@app.route("/new-log")
def new_log():
    return render_template("main/new-log.html")


@app.route("/new-log-input/<id>", methods=["POST"])
def new_log_input(id):
    food = request.form.get("food")
    given_percent = int(request.form.get("given_percent"))

    conn, cur = get_db_connection()
    cur.execute(f"INSERT INTO pet_{id} (food, given_percent) VALUES ('{food}', {given_percent})")
    conn.commit()
    conn.close()

    return redirect(f"/logs/{id}")


if __name__ == "__main__":
    app.run()