import pytest
from flask import url_for

def test_first_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"<title>Bank Home</title>" in response.data

def test_homepage(client):
    response = client.get("/index")
    assert response.status_code == 200
    assert b"<title>Bank Home</title>" in response.data
