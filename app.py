import os
import cs50
from types import GetSetDescriptorType

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

# Built-in to Python; will allow program to read Json files
import json

# Allows program to open specific url with API key and search terms
from urllib.request import urlopen

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
# db = SQL("sqlite:///finance.db")



@app.route("/")
def index():

    return render_template("index.html")


@app.route("/add-book", methods=["GET", "POST"])
def add_book():
    while true:
        api = "https://www.googleapis.com/books/v1/volumes?q=isbn:"
        isbn = request.form.get("isbn")

        response = urlopen(api + isbn)

        bookdata = json.loads(response.read())

        print(bookdata)
        volume_info = bookdata["items"][0]["volumeInfo"]
        title = volume_info["title"]
        print(title)

        if request.method == "GET":
            return render_template("add_book.html")

        else:
           #print(f"Title: {title}")
            return render_template("searched.html", title=title)

        
        # get isbn from form request
        # https://www.googleapis.com/books/v1/volumes?q=:keyes&key=yourAPIKey



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user for an account."""

    # POST
    if request.method == "POST":

        # Validate form submission
        if not request.form.get("username"):
            return apology("missing username")
        elif not request.form.get("password"):
            return apology("missing password")
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match")

        # Add user to database
        try:
            id = db.execute("INSERT INTO users (username, hash) VALUES(?, ?)",
                            request.form.get("username"),
                            generate_password_hash(request.form.get("password")))
        except ValueError:
            return apology("username taken")

        # Log user in
        session["user_id"] = id

        # Let user know they're registered
        flash("Registered!")
        return redirect("/")

    # GET
    else:
        return render_template("register.html")