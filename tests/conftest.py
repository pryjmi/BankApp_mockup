import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from run import app

@pytest.fixture
def auth(client):
    class AuthActions:
        def login(self, email="test@example.com", password="testpassword"):
            return client.post(
                "/login",
                data={"email": email, "password": password},
                follow_redirects=True,
            )

        def logout(self):
            return client.get("/logout", follow_redirects=True)

    return AuthActions()

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
