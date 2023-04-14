from flask import render_template, Flask, jsonify, request, redirect, url_for, session, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import requests
import os
import json
import smtplib
import random

app = Flask(__name__, template_folder="./template", static_folder="./static")
app.config["SECRET_KEY"] = "secretkey"

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

##################################################### INIT USER ###########################################################

class User(UserMixin):
    def __init__(self, id, first_name, last_name, password):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.password = password
        self.pin = None

@login_manager.user_loader
def load_user(user_id):
    with open("app/users.json", "r") as file:
        users = json.load(file)
    return next(
        (
            User(user_id, user_data["first_name"], user_data["last_name"], user_data["password"])
            for email, user_data in users.items()
            if user_id == email
        ),
        None,
    )

################################################### FETCHING RATES #########################################################

def get_date_to_use(now=None):
    if now is None:
        now = datetime.datetime.now()

    if now.weekday() >= 5:
        days_to_friday = (now.weekday() - 4) % 7
        friday = now - datetime.timedelta(days=days_to_friday)
        date_to_use = friday.date()
    else:
        date_to_use = now.date()
    
    return date_to_use.strftime("%d.%m.%Y")

def get_exchange_rate(path=None):
    date_to_use = get_date_to_use()

    if path is None:
        path = "app/exchange_rates.json"

    if os.path.exists(path):
        with open(path, "r") as file:
            exchange_rates = json.load(file)
    else:
        exchange_rates = {}

    if date_to_use not in exchange_rates:
        save_exchange_rate(date_to_use, exchange_rates, path)

    return exchange_rates


def save_exchange_rate(date_to_use, exchange_rates, path):
    url = f"https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt;jsessionid=4809CDD45D1657F6A4F2F9A435E55F13?date={date_to_use}"
    response = requests.get(url)

    data_lines = response.text.strip().split("\n")[2:]
    parsed_data = {}
    for line in data_lines:
        _, _, amount, code, rate = line.split("|")
        parsed_data[code] = {
            'amount': float(amount),
            'rate': float(rate.replace(",", "."))
        }
    exchange_rates[date_to_use] = parsed_data

    with open(path, "w") as file:
        json.dump(exchange_rates, file)

##################################################### BALANCE ##############################################################

def get_balance(user_email, balance_file_path="app/balance.json"):
    with open(balance_file_path, "r") as file:
        balances = json.load(file)
    return balances.get(user_email, {})

def update_balance(user_email, amount, currency, balance_file_path="app/balance.json"):
    with open(balance_file_path, "r") as file:
        all_balances = json.load(file)
    balance = all_balances.get(user_email, {})

    exchange_rate = get_exchange_rate()
    date_to_use = get_date_to_use()
    msg = ""

    if currency not in balance:
        balance[currency] = 0

    if amount < 0 and balance[currency] < -amount:
        if currency not in exchange_rate[date_to_use]:
            msg = "Currency not supported."
        else:
            amount_in_czk = -amount * (exchange_rate[date_to_use][currency]["rate"] / exchange_rate[date_to_use][currency]["amount"])
            if "CZK" in balance and balance["CZK"] >= amount_in_czk:
                balance["CZK"] -= amount_in_czk
                currency = "CZK"
                amount = -amount_in_czk
            else:
                msg = "Not enough funds."
    else:
        balance[currency] += amount

    all_balances[user_email] = balance
    with open(balance_file_path, "w") as file:
        json.dump(all_balances, file)

    return msg, currency, amount

############################################### TRANSACTION HISTORY #########################################################

def get_transactions(user_email, transactions_file_path="app/transactions.json"):
    with open(transactions_file_path, "r") as file:
        all_transactions = json.load(file)
    return all_transactions.get(user_email, [])

def update_transactions(user_email, amount, currency, transactions_file_path="app/transactions.json"):
    with open(transactions_file_path, "r") as file:
        all_transactions = json.load(file)

    date = datetime.datetime.now().strftime("%d.%m.%Y")
    value = f"{amount:.2f}" if str(amount).startswith("-") else f"+{amount:.2f}"
    new_transaction = {
        date: {
            currency: value
            }
        }

    if user_email in all_transactions:
        all_transactions[user_email].append(new_transaction)
    else:
        all_transactions[user_email] = [new_transaction]

    with open(transactions_file_path, "w") as file:
        json.dump(all_transactions, file)

###################################################### HOMEPAGE ############################################################

@app.route("/")
@app.route("/index", methods=["GET", "POST"])
@login_required
def index():
    get_exchange_rate()
    user_email = current_user.id
    balance = get_balance(user_email)
    transactions = get_transactions(user_email)
    err = ""
    
    if request.method == "POST":
        amount = float(request.form["amount"])
        currency = request.form["currency"]
        action = request.form["action"]

        if action == "pay":
            amount = -amount

        err, currency, amount = update_balance(current_user.id, amount, currency)
        if err == "":
            update_transactions(current_user.id, amount, currency)


    balance = get_balance(user_email)
    transactions = get_transactions(user_email)

    return render_template("index.html", user=current_user, balance=balance, transactions=transactions, err=err)

################################################### AUTHENTICATION ##########################################################

def send_email_pin(email, pin):
    sender_email = "testing.pryjmi@gmail.com"
    sender_password = "sauvdtwtdpkcynpk"
    receiver_email = email
    message = f"Subject: Your login pin\n\nYour pin is: {pin}"
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(sender_email, sender_password)
        smtp.sendmail(sender_email, receiver_email, message)
        smtp.quit()

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method != "POST":
        return render_template("login.html")
    email = request.form["email"]
    password = request.form["password"]
    with open("app/users.json", "r") as file:
        users = json.load(file)
    if email not in users or password != users[email]["password"]:
        return "Invalid email or password", 401
    user = User(email, users[email]["first_name"], users[email]["last_name"], password)
    login_user(user)
    pin = random.randint(1000, 9999)
    send_email_pin(email, pin)
    session["pin"] = str(pin)
    session["email"] = email
    session["pin_expiry"] = (datetime.datetime.now() + datetime.timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
    return redirect(url_for("twofactor"))

@app.route("/2fa", methods=["GET", "POST"])
@login_required
def twofactor():
    if request.method == "POST":
        pin = request.form["pin"]
        expiry = datetime.datetime.strptime(session["pin_expiry"], "%Y-%m-%d %H:%M:%S")

        if datetime.datetime.now() > expiry:
            logout_user()
            return redirect(url_for("login"))

        if pin == session["pin"]:
            return redirect(url_for("index"))
        else:
            return "Invalid pin", 401
    return render_template("2fa.html", user=current_user)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))
