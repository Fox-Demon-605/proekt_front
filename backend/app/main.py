from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from . import db, models, schemas, crud, auth
from .db import get_db
from fastapi.middleware.cors import CORSMiddleware
import typing
import asyncio
import logging

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="Library + AI Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # для демонстрации; в production ограничьте домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db_s: AsyncSession = Depends(get_db)):
    payload = auth.decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    email = payload["sub"]
    user = await crud.get_user_by_email(db_s, email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@app.post("/auth/register", response_model=schemas.Token)
async def register(user_in: schemas.UserCreate, db_s: AsyncSession = Depends(get_db)):
    existing = await crud.get_user_by_email(db_s, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    user = await crud.create_user(db_s, user_in.email, user_in.password)
    token = auth.create_access_token({"sub": user.email})
    return {"access_token": token}

@app.post("/auth/login", response_model=schemas.Token)
async def login(form: schemas.UserCreate, db_s: AsyncSession = Depends(get_db)):
    # Using schema with EmailStr and password; not OAuth2 form for simplicity here
    user = await crud.get_user_by_email(db_s, form.email)
    if not user or not auth.verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    token = auth.create_access_token({"sub": user.email})
    return {"access_token": token}

@app.post("/chat/session", response_model=schemas.SessionOut)
async def create_session_endpoint(s_in: schemas.SessionCreate, current_user: models.User = Depends(get_current_user), db_s: AsyncSession = Depends(get_db)):
    s = await crud.create_session(db_s, user_id=current_user.id, title=s_in.title)
    return s

@app.post("/chat/message")
async def post_message(msg_in: schemas.MessageCreate, current_user: models.User = Depends(get_current_user), db_s: AsyncSession = Depends(get_db)):
    session = await crud.get_session(db_s, msg_in.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    # check session ownership
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Session does not belong to user")

    # Save user message
    user_msg = await crud.save_message(db_s, session, "user", msg_in.text)

    # Very simple bot logic: keyword matching
    text_lower = msg_in.text.lower()
    if any(k in text_lower for k in ["книг", "рекоменд", "посовет"]):
        reply = "Могу порекомендовать вам классику: «Война и мир», «Преступление и наказание», а также современные бестселлеры."
    elif "привет" in text_lower or "здравств" in text_lower:
        reply = "Привет! Чем могу помочь по библиотеке?"
    else:
        reply = "Извините, я вас не совсем понял. Попробуйте сформулировать вопрос иначе."

    bot_msg = await crud.save_message(db_s, session, "bot", reply)

    return {"reply": reply, "user_message_id": user_msg.id, "bot_message_id": bot_msg.id}
    
@app.get("/chat/history/{session_id}", response_model=schemas.ChatHistory)
async def get_history(session_id: int, current_user: models.User = Depends(get_current_user), db_s: AsyncSession = Depends(get_db)):
    session = await crud.get_session(db_s, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Session does not belong to user")
    messages = await crud.get_history(db_s, session)
    # sort by created_at
    messages = sorted(messages, key=lambda m: m.created_at)
    return {"messages": messages}

# Optional WebSocket route (demonstrates JWT check on connect)
@app.websocket("/ws/chat")
async def websocket_chat(ws: WebSocket, token: str = None):
    await ws.accept()
    # token must be passed as query param: /ws/chat?token=...
    if not token:
        await ws.close(code=1008)
        return
    payload = auth.decode_token(token)
    if not payload or "sub" not in payload:
        await ws.close(code=1008)
        return
    # In a real app: link websocket with DB session, user, etc.
    try:
        while True:
            data = await ws.receive_json()
            # echo / minimal bot
            user_text = data.get("text", "")
            await ws.send_json({"sender":"bot","text":"Echo: " + user_text})
    except WebSocketDisconnect:
        logger.info("Websocket disconnected")
