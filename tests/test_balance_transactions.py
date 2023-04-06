import pytest
import json
from app.views import update_balance, update_transactions, get_balance, get_transactions

def test_update_balance(tmp_path, monkeypatch):
    balance_file = tmp_path / "balance_test.json"
    balance_file.write_text('{"USD": 200, "CZK": 5000}')

    exchange_rate_file = tmp_path / "exchange_rate_test.json"
    exchange_rate_file.write_text('{"01.01.2023": {"USD": {"amount": 1, "rate": 20}, "CZK": {"amount": 1, "rate": 1}}}')

    date_to_use = "04.04.2023"

    # Temporarily change the behavior of the get_exchange_rate() and get_date_to_use() functions
    monkeypatch.setattr("app.views.get_exchange_rate", lambda: json.loads(exchange_rate_file.read_text()))
    monkeypatch.setattr("app.views.get_date_to_use", lambda: date_to_use)

    # Test positive amount
    _, _, _ = update_balance(100, "USD", balance_file)
    balance = get_balance(balance_file)

    assert balance["USD"] == 100

def test_update_balance_unsupported_currency(tmp_path, monkeypatch):
    balance_file = tmp_path / "balance_test.json"
    balance_file.write_text('{"USD": 200, "CZK": 5000}')

    exchange_rate_file = tmp_path / "exchange_rate_test.json"
    exchange_rate_file.write_text('{"01.01.2023": {"USD": {"amount": 1, "rate": 20}, "CZK": {"amount": 1, "rate": 1}}}')

    date_to_use = "01.01.2023"

    monkeypatch.setattr("app.views.get_exchange_rate", lambda: json.loads(exchange_rate_file.read_text()))
    monkeypatch.setattr("app.views.get_date_to_use", lambda: date_to_use)

    msg, _, _ = update_balance(-100, "JPY", balance_file)
    assert msg == "Currency not supported."

def test_update_balance_not_enough_funds(tmp_path, monkeypatch):
    balance_file = tmp_path / "balance_test.json"
    balance_file.write_text('{"USD": 200, "CZK": 5000}')

    exchange_rate_file = tmp_path / "exchange_rate_test.json"
    exchange_rate_file.write_text('{"01.01.2023": {"USD": {"amount": 1, "rate": 20}, "CZK": {"amount": 1, "rate": 1}}}')

    date_to_use = "01.01.2023"

    monkeypatch.setattr("app.views.get_exchange_rate", lambda: json.loads(exchange_rate_file.read_text()))
    monkeypatch.setattr("app.views.get_date_to_use", lambda: date_to_use)

    msg, _, _ = update_balance(-300, "USD", balance_file)
    assert msg == "Not enough funds."

def test_update_transactions(tmp_path):
    transactions_file = tmp_path / "transactions_test.json"
    transactions_file.write_text('[]')
    
    update_transactions(100, "USD", transactions_file)
    transactions = get_transactions(transactions_file)
    last_transaction = transactions[-1]
    date = list(last_transaction.keys())[0]
    value = last_transaction[date]["USD"]
    
    assert value == "+100.00"