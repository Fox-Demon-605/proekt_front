import pytest
from httpx import AsyncClient
from app.main import app
import asyncio

@pytest.mark.asyncio
async def test_register_login_create_session_and_chat(tmp_path, monkeypatch):
    # Тесты используют тестовую БД через env var
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1 register
        r = await ac.post("/auth/register", json={"email":"t@t.com","password":"password"})
        assert r.status_code == 200
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # create session
        r2 = await ac.post("/chat/session", json={"title":"t"}, headers=headers)
        assert r2.status_code == 200
        session_id = r2.json()["id"]

        # send message
        r3 = await ac.post("/chat/message", json={"session_id": session_id, "text":"Привет"}, headers=headers)
        assert r3.status_code == 200
        assert "reply" in r3.json()

        # history
        r4 = await ac.get(f"/chat/history/{session_id}", headers=headers)
        assert r4.status_code == 200
        data = r4.json()
        assert len(data["messages"]) >= 2
