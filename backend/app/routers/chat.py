from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
from typing import Optional
import logging

from ..database import get_db
from .. import models, schemas, auth, bot_logic

router = APIRouter()
logger = logging.getLogger(__name__)

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ")[1]
    payload = auth.verify_token(token)
    
    if not payload:
        return None
    
    return payload

@router.post("/session", response_model=schemas.ChatSessionResponse)
async def create_session(
    db: Session = Depends(get_db),
    user_data: Optional[dict] = Depends(get_current_user)
):
    session_id = str(uuid.uuid4())
    
    db_session = models.ChatSession(
        session_id=session_id,
        user_id=user_data.get("user_id") if user_data else None
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    # Добавляем приветственное сообщение от бота
    welcome_message = models.Message(
        session_id=db_session.id,
        content="Привет! Я бот погоды. Спросите о погоде в любом городе России!",
        sender="bot"
    )
    
    db.add(welcome_message)
    db.commit()
    
    return db_session

@router.post("/message", response_model=schemas.BotResponse)
async def send_message(
    message_data: schemas.MessageCreate,
    db: Session = Depends(get_db),
    user_data: Optional[dict] = Depends(get_current_user)
):
    # Если session_id не предоставлен, создаем новую сессию
    if not message_data.session_id:
        session_response = await create_session(db, user_data)
        session_id = session_response.session_id
        db_session = session_response
    else:
        # Ищем существующую сессию
        db_session = db.query(models.ChatSession).filter(
            models.ChatSession.session_id == message_data.session_id
        ).first()
        
        if not db_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
    
    # Сохраняем сообщение пользователя
    user_message = models.Message(
        session_id=db_session.id,
        content=message_data.content,
        sender="user"
    )
    
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # Получаем ответ от бота
    bot_response_text = bot_logic.weather_bot.get_response(message_data.content)
    
    # Сохраняем ответ бота
    bot_message = models.Message(
        session_id=db_session.id,
        content=bot_response_text,
        sender="bot"
    )
    
    db.add(bot_message)
    db.commit()
    db.refresh(bot_message)
    
    logger.info(f"User message: {message_data.content}, Bot response: {bot_response_text}")
    
    return schemas.BotResponse(
        message=bot_message,
        session_id=db_session.session_id
    )

@router.get("/history/{session_id}", response_model=schemas.ChatSessionResponse)
async def get_history(
    session_id: str,
    db: Session = Depends(get_db),
    user_data: Optional[dict] = Depends(get_current_user)
):
    db_session = db.query(models.ChatSession).filter(
        models.ChatSession.session_id == session_id
    ).first()
    
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return db_session
