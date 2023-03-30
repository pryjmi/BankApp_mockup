import pytest
from app.views import update_balance, update_transactions, get_balance, get_transactions


def test_update_balance(tmp_path):
    balance_file = tmp_path / "balance_test.json"
    balance_file.write_text('{"USD": 200}')
    
    update_balance(100, "USD", balance_file)
    balance = get_balance(balance_file)
    
    assert balance["USD"] == 300

def test_update_transactions(tmp_path):
    transactions_file = tmp_path / "transactions_test.json"
    transactions_file.write_text('[]')
    
    update_transactions(100, "USD", transactions_file)
    transactions = get_transactions(transactions_file)
    last_transaction = transactions[-1]
    date = list(last_transaction.keys())[0]
    value = last_transaction[date]["USD"]
    
    assert value == "+100.00"