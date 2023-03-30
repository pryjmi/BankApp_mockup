import pytest
import json
import datetime
from app.views import get_date_to_use, get_exchange_rate, save_exchange_rate

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
