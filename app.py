import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

# from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
# app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///bookswap.db")

# Create new table, and index
db.execute("CREATE TABLE IF NOT EXISTS registrations (id INTEGER, user_id NUMERIC NOT NULL, password TEXT NOT NULL, \
            timestamp TEXT, PRIMARY KEY(id), \
            FOREIGN KEY(user_id)")
db.execute("CREATE INDEX IF NOT EXISTS orders_by_user_id_index ON orders (user_id)")


@app.route("/")
# @login_required
def index():

    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register User"""
    if request.method == "GET":
        return render_template("register.html")
    
    # Check username and password
    email = request.form.get("email")
    password = request.form.get("password")
    confirmation = request.form.get("confirmation")

    # Add users to bookswap.db
    db.execute('INSERT INTO users (email, hash) \
        VALUES(?,?)', email, generate_password_hash(password))
    
    rows = db.execute("SELECT * FROM users WHERE email = ?", email)
    session["user_id"] = rows[0]["id"]
    return redirect("/")

    # Joining two tables 
    db.execute("CREATE TABLE IF NOT EXSITS books (id INTEGER, title TEXT NOT NULL, author TEXT NOT NULL, seller TEXT NOT NULL"))
    join = "INNER JOIN books ON registrations.users_id = books.seller"