import os
os.environ["RECRUITER_BOT_TOKEN"] = "x"
from fastapi.testclient import TestClient
from app.main import app, SECRET

def test_health():
    assert TestClient(app).get("/health").json() == {"ok": True}

def test_bad_secret():
    assert TestClient(app).post("/webhook/bad", json={}).status_code == 404
