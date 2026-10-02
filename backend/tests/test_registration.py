import os
import subprocess
import sys


def test_public_registration_is_rejected(client):
    response = client.post("/auth/register", json={"username": "intruder", "password": "test-password", "role": "admin"})
    assert response.status_code in (401, 403)


def test_regular_user_cannot_register_an_admin(client):
    token = client.post("/auth/login", json={"username": "user", "password": "test-password"}).json()["access_token"]
    response = client.post("/auth/register", json={"username": "intruder", "password": "test-password", "role": "admin"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_admin_can_register_and_new_user_can_login(client):
    token = client.post("/auth/login", json={"username": "admin", "password": "test-password"}).json()["access_token"]
    response = client.post("/auth/register", json={"username": "new-user", "password": "new-password", "role": "superuser"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["role"] == "user"
    assert client.post("/auth/login", json={"username": "new-user", "password": "new-password"}).status_code == 200


def test_startup_requires_a_private_signing_key():
    env = dict(os.environ)
    env.pop("SECRET_KEY", None)
    result = subprocess.run([sys.executable, "-c", "import config"], env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert "SECRET_KEY" in result.stderr
