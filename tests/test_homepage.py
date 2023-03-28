import pytest
import json
import datetime
import smtplib
from flask import url_for
from app.views import  get_date_to_use, get_exchange_rate, save_exchange_rate, send_email_pin

def test_login(client, monkeypatch):
    monkeypatch.setattr("app.views.send_email_pin", lambda email, pin: None)
    response = client.post("/login", data={"email": "testing.pryjmi@gmail.com", "password": "testpassword"})
    assert response.status_code == 302
    assert "/2fa" in response.location

def test_invalid_login(client):
    response = client.post("/login", data={"email": "test@example.com", "password": "wrong_password"})
    assert response.status_code == 401

def test_twofactor(client, monkeypatch):
    monkeypatch.setattr("app.views.send_email_pin", lambda email, pin: None)
    response = client.post("/login", data={"email": "testing.pryjmi@gmail.com", "password": "testpassword"})
    assert response.status_code == 302
    with client.session_transaction() as session:
        pin = session["pin"]
    response = client.post("/2fa", data={"pin": pin})
    assert response.status_code == 302
    assert "/index" in response.location

def test_twofactor_invalid_pin(client, monkeypatch):
    monkeypatch.setattr("app.views.send_email_pin", lambda email, pin: None)
    response = client.post("/login", data={"email": "testing.pryjmi@gmail.com", "password": "testpassword"})
    assert response.status_code == 302
    with client.session_transaction() as session:
        session["pin"] = "0000"
    response = client.post("/2fa", data={"pin": "1234"})
    assert response.status_code == 401

def test_logout(client):
    with client.session_transaction() as session:
        session["_user_id"] = "testing.pryjmi@gmail.com"
    response = client.get("/logout")
    assert response.status_code == 302
    assert "/login" in response.location

def test_send_email_pin(monkeypatch):
    email_sent = False

    def mock_sendmail(*args, **kwargs):
        nonlocal email_sent
        email_sent = True

    monkeypatch.setattr("smtplib.SMTP.sendmail", mock_sendmail)
    send_email_pin("testing.pryjmi@gmail.com", "1234")
    assert email_sent

def test_login_route_get(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b'Login' in response.data

def test_get_date_to_use():
    # weekend
    weekend = datetime.datetime(2023, 3, 25) # saturday
    expected_date_weekend = "24.03.2023" # nearest friday
    assert get_date_to_use(weekend) == expected_date_weekend
    # weekday
    weekday = datetime.datetime(2023, 3, 22) # tuesday
    expected_date_weekday = "22.03.2023" # same day
    assert get_date_to_use(weekday) == expected_date_weekday

def test_get_exchange_rate(tmp_path):
    test_file = tmp_path / "exchange_rates_test.json"
    get_exchange_rate(test_file)
    
    assert test_file.exists()
    
    with open(test_file, "r") as file:
        exchange_rates = json.load(file)
    
    date_to_use = get_date_to_use()
    assert date_to_use in exchange_rates

def test_save_exchange_rate(tmp_path):
    test_file = tmp_path / "exchange_rates_test.json"
    test_date = "25.03.2023"
    test_data = {}
    
    save_exchange_rate(test_date, test_data, test_file)
    assert test_file.exists()
    
    with open(test_file, "r") as file:
        data = json.load(file)
    assert data
    
    assert test_date in data
    assert data[test_date]
