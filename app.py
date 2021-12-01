import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

import datetime as dt
from helpers import apology, login_required, lookup, usd
from datetime import datetime

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_stocks = db.execute("SELECT symbol, SUM(shares) as shares, transaction_type FROM stocks WHERE user = ? GROUP BY symbol HAVING (SUM(shares)) > 0;", session["user_id"])
    cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])

    stock_money = 0
    for stock in user_stocks:
        current = lookup(stock["symbol"])
        stock["name"] = current["name"]
        stock["price"] = current["price"]
        stock["symbol"] = current["symbol"]
        stock["purchases"] = stock["shares"]*stock["price"]
        stock_money = stock_money + stock["purchases"]

    budget = cash[0]["cash"] + stock_money

    return render_template("index.html", stocks=user_stocks, cash=cash[0], budget=budget)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")
    else:
        symbol = request.form.get("symbol")
        shares = float(request.form.get("shares"))
        current = lookup(symbol)

        """Check form errors"""
        if not symbol:
            return apology("Please provide a stock symbol")
        elif not lookup(symbol):
            return apology("Please provide a valid stock symbol")
        elif current is None:
            return apology("Please provide a stock symbol")
        elif not shares:
            return apology("Please provide number of shares")
        
        elif shares != int(shares):
            return apology("Shares must be a positive integer")
        try:
            shares = int(shares)
            if shares < 1:
                return apology("Shares must be a positive integer")
        except ValueError:
            return apology("Shares must be a positive integer")

        """Check that cash is sufficient"""
        purchase = current["price"]*shares
        budget = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]
        if budget - purchase < 0:
            return apology("Insufficient capital")
        else:
            """Record time of purchase"""
            when = dt.datetime.now()
            """Add purchase to stocks and update user cash"""
            db.execute("INSERT INTO stocks (user, shares, price, symbol, transaction_type, transacted) VALUES(?,?,?,?,?,?)",
                       session["user_id"], shares, current["price"], symbol.upper(), "buy", when)
            db.execute("UPDATE users SET cash = cash - ? WHERE id = ?", purchase, session["user_id"])
            return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    history = db.execute("SELECT * FROM stocks WHERE user = ?", session["user_id"])
    return render_template("history.html", history=history)



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")
    else:
        symbol = request.form.get("symbol")
        quote = lookup(symbol)

        if not quote:
            return apology("This stock symbol does not exist")
        else:
            return render_template("quoted.html", name=quote["name"], symbol=quote["symbol"], price=usd(quote["price"]))


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        """Check for any errors"""
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        existing = db.execute(
            "SELECT * FROM users WHERE username = ?", username)

        if len(existing) > 0:
            return apology("This username already exists")
        elif password != confirmation:
            return apology("Passwords do not match")
        elif not username:
             return apology("Please fill out all fields")
        elif not password:
            return apology("Please fill out all fields")
        elif not confirmation:
            return apology("Please fill out all fields")
        for character in password:
            digit = character.isdigit()
            if digit:
                hash = generate_password_hash(
                password, method='pbkdf2:sha256', salt_length=8)
                db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash)
                return redirect("/")
        return apology("Password must contain a number")

    """Returns register page"""
    if request.method == "GET":
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    stocks_symbol = db.execute("SELECT DISTINCT symbol FROM stocks WHERE user = ?", session["user_id"])
    print(stocks_symbol)
    if request.method == "GET":
        return render_template("sell.html", stocks=stocks_symbol)
    else:
        """Check for Errors"""
        sell_shares = request.form.get("shares")
        symbol = request.form.get("symbol")

        if not symbol:
            return apology("Please Select a Symbol")
        try:
            sell_shares = int(sell_shares)
            if sell_shares < 1:
                return apology("Shares must be a positive integer")
        except ValueError:
            return apology("Shares must be a positive integer")

        stocks_shares = db.execute("SELECT SUM(shares) as shares FROM stocks WHERE user = ? AND symbol = ?;", session["user_id"], symbol,)[0]

        if sell_shares > stocks_shares["shares"]:
            return apology("Exceeds amount of shares owned")

        """"Give user back the money they just made"""""
        current = lookup(symbol)
        sale = current["price"]*sell_shares

        """Record time of transaction"""
        when = dt.datetime.now()

        """Update tables"""
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", sale, session["user_id"])
        db.execute("INSERT INTO stocks (user, symbol, shares, price, transaction_type, transacted) VALUES (?, ?, ?, ?, ?, ?)", session["user_id"], symbol.upper(), - sell_shares, current["price"], "sell", when,)

        return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

