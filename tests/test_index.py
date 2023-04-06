import pytest
import json
import datetime

def test_index_get(client, monkeypatch):
    # Log in before testing the index page
    monkeypatch.setattr("app.views.send_email_pin", lambda email, pin: None)
    response = client.post("/login", data={"email": "testing.pryjmi@gmail.com", "password": "testpassword"})
    assert response.status_code == 302
    with client.session_transaction() as session:
        pin = session["pin"]
    response = client.post("/2fa", data={"pin": pin})
    assert response.status_code == 302

    response = client.get("/index")
    assert response.status_code == 200
    assert b'Bank Home' in response.data

def test_index_post(client, monkeypatch, tmp_path):
    # Log in before testing the index page
    monkeypatch.setattr("app.views.send_email_pin", lambda email, pin: None)
    response = client.post("/login", data={"email": "testing.pryjmi@gmail.com", "password": "testpassword"})
    assert response.status_code == 302
    with client.session_transaction() as session:
        pin = session["pin"]
    response = client.post("/2fa", data={"pin": pin})
    assert response.status_code == 302

    # Set up temporary files
    balance_file = tmp_path / "balance_test.json"
    transactions_file = tmp_path / "transactions_test.json"
    balance_file.write_text(json.dumps({}))
    transactions_file.write_text(json.dumps([]))

    monkeypatch.setattr("app.views.get_balance", lambda user_email: json.loads(balance_file.read_text()))
    monkeypatch.setattr("app.views.update_balance", lambda amount, currency: (balance_file.write_text(json.dumps({currency: amount})), currency, amount))
    monkeypatch.setattr("app.views.get_transactions", lambda user_email: json.loads(transactions_file.read_text()))
    monkeypatch.setattr("app.views.update_transactions", lambda amount, currency: transactions_file.write_text(json.dumps([{datetime.datetime.now().strftime("%d.%m.%Y"): {currency: f"+{amount:.2f}"}}])))

    response = client.post("/index", data={"amount": "100", "currency": "USD"})
