import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from api import server


class FakeSession:
    def __init__(self):
        self.calls = []

    async def ask(self, question, image=None):
        self.calls.append((question, image))
        return {"answer": f"answer to {question}", "trace": [], "seconds": 0.1, "error": False}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(server, "new_session", FakeSession)
    server.sessions.clear()
    return TestClient(server.app)


def png_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (20, 20), "white").save(buf, "PNG")
    return buf.getvalue()


def test_chat_text_only_creates_session(client):
    r = client.post("/api/chat", data={"message": "Bill for 250 units in Rajasthan?"})
    assert r.status_code == 200
    body = r.json()
    assert body["answer"] == "answer to Bill for 250 units in Rajasthan?"
    assert body["session_id"] in server.sessions


def test_chat_follow_up_uses_same_session(client):
    sid = client.post("/api/chat", data={"message": "Check"}).json()["session_id"]
    r = client.post("/api/chat", data={"message": "Letter", "session_id": sid})
    assert r.json()["session_id"] == sid
    assert [q for q, _ in server.sessions[sid].calls] == ["Check", "Letter"]


def test_chat_saves_uploaded_photo(client):
    r = client.post("/api/chat", data={"message": "Is it correct?"},
                    files={"image": ("bill.png", png_bytes(), "image/png")})
    sid = r.json()["session_id"]
    _, path = server.sessions[sid].calls[0]
    assert path.parent == server.UPLOAD_DIR / sid and path.suffix == ".png" and path.is_file()


def test_chat_rejects_non_image(client):
    r = client.post("/api/chat", data={"message": "x"}, files={"image": ("a.txt", b"hello", "text/plain")})
    assert r.status_code == 415


def test_chat_rejects_fake_image(client):
    r = client.post("/api/chat", data={"message": "x"}, files={"image": ("a.png", b"not a png", "image/png")})
    assert r.status_code == 400


def test_chat_rejects_empty_message_and_unknown_session(client):
    assert client.post("/api/chat", data={"message": "  "}).status_code == 400
    assert client.post("/api/chat", data={"message": "hi", "session_id": "nope"}).status_code == 404


def test_delete_session_removes_uploads(client):
    r = client.post("/api/chat", data={"message": "x"}, files={"image": ("b.png", png_bytes(), "image/png")})
    sid = r.json()["session_id"]
    assert (server.UPLOAD_DIR / sid).exists()
    assert client.delete(f"/api/sessions/{sid}").json() == {"deleted": sid}
    assert not (server.UPLOAD_DIR / sid).exists()
    assert client.delete(f"/api/sessions/{sid}").status_code == 404


def test_health_reports_missing_ollama(client, monkeypatch):
    def down():
        raise ConnectionError("refused")

    monkeypatch.setattr(server, "ollama_models", down)
    body = client.get("/api/health").json()
    assert body["ok"] is False and "refused" in body["error"]


def test_health_ok_when_model_present(client, monkeypatch):
    monkeypatch.setattr(server, "ollama_models", lambda: [server.MODEL])
    assert client.get("/api/health").json()["ok"] is True
