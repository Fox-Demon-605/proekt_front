import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.main import app
from backend.app.database import Base, get_db

# Тестовая база данных
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Переопределяем зависимость базы данных
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    # Создаем таблицы перед каждым тестом
    Base.metadata.create_all(bind=engine)
    yield
    # Удаляем таблицы после каждого теста
    Base.metadata.drop_all(bind=engine)

def test_create_session():
    response = client.post("/chat/session")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "messages" in data
    assert len(data["messages"]) == 1  # Приветственное сообщение

def test_send_message():
    # Сначала создаем сессию
    session_response = client.post("/chat/session")
    session_id = session_response.json()["session_id"]
    
    # Отправляем сообщение
    response = client.post("/chat/message", json={
        "content": "Какая погода в Москве?",
        "session_id": session_id
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"]["sender"] == "bot"
    assert "Москв" in data["message"]["content"] or "погод" in data["message"]["content"]

def test_get_history():
    # Создаем сессию и отправляем сообщение
    session_response = client.post("/chat/session")
    session_id = session_response.json()["session_id"]
    
    client.post("/chat/message", json={
        "content": "Привет",
        "session_id": session_id
    })
    
    # Получаем историю
    response = client.get(f"/chat/history/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["messages"]) >= 2  # Приветствие + ответ на "Привет"
