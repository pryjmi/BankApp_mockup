from flask import render_template, Flask, jsonify
from bs4 import BeautifulSoup as bs
import datetime
import schedule
import time
import requests
import os
import json
from app import app

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
        file_name = "exchange_rates.json"
        path = f"app/{file_name}"

    if os.path.exists(path):
        with open(path, "r") as file:
            exchange_rates = json.load(file)
    else:
        exchange_rates = {}

    if date_to_use not in exchange_rates:
        save_exchange_rate(date_to_use, exchange_rates, path)


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

@app.route("/")
@app.route("/index")
def index():
    user = "uživatel"
    get_exchange_rate()
    return render_template("index.html", user=user)
