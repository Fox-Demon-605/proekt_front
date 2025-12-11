import json
import asyncio
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from app import crud, schemas, ai_service
from app.database import get_db
from app.dependencies import get_current_user
from sqlalchemy.orm import Session


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.user_sessions: Dict[int, int] = {}  # user_id -> session_id
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await webs websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
    
    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except:
                self.disconnect(user_id)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


async def handle_websocket(websocket: WebSocket, token: str):
    """Обработка WebSocket соединений"""
    
    db: Session = next(get_db())
    
    try:
        # Аутентификация пользователя
        from app.auth import verify_token
        token_data = verify_token(token)
        user = crud.get_user_by_email(db, email=token_data.email)
        
        if not user:
            await websocket.close(code=1008)
            return
        
        # Подключаем пользователя
        await manager.connect(websocket, user.id)
        
        # Получаем или создаем текущую сессию
        session = crud.get_current_session(db, user.id)
        if not session:
            session = crud.create_session(db, schemas.SessionCreate(), user.id)
        
        manager.user_sessions[user.id] = session.id
        
        # Отправляем информацию о сессии
        await manager.send_personal_message(
            schemas.WSSessionCreated(session=session).dict(),
            user.id
        )
        
        # Обработка сообщений
        while True:
            try:
                data = await websocket.receive_text()
                await handle_websocket_message(data, user, db)
                
            except WebSocketDisconnect:
:
                break
            except Exception as e:
                error_msg = schemas.WSError(message=f"Ошибка: {str(e)}").dict()
                await manager.send_personal_message(error_msg, user.id)
    
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        manager.disconnect(user.id)
        db.close()


async def handle_websocket_message(data: str, user, db: Session):
    """Обработка входящих WebSocket сообщений"""
    
    try:
        message_data = json.loads(data)
        msg_type = message_data.get("type")
        
        if msg_type == "user_message":
            user_message = message_data.get("message", "")
            session_id = message_data.get("session_id")
            
            if not session_id:
                session_id = manager.user_sessions.get(user.id)
            
            # Сохраняем сообщение пользователя
            user_msg = schemas.MessageCreate(
                content=user_message,
                sender="user",
                session_id=session_id
            )
            
            crud.create_message(db, user_msg, user.id)
            
            # Отправляем индикатор печати
            typing_msg = schemas.WSBotTyping().dict()
            await manager.send_personal_message(typing_msg, user.id)
            
            # Получаем историю сообщений
            messages = crud.get_session_messages(db, session_id, user.id)
            
            # Форматируем для AI
            ai_messages = [
                {"sender": msg.sender, "content": msg.content}
                for msg in messages[-20:]  # Последние 20 сообщений для контекста
            ]
            
            # Генерируем ответ AI
            try:
                ai_response = await ai_service.generate_response(ai_messages)
                
                # Сохраняем ответ AI
                bot_msg = schemas.MessageCreate(
                    content=ai_response.content,
                    sender="bot",
                    session_id=session_id
                )
                
                db_message = crud.create_message(db, bot_msg, user.id)
                db_message.tokens_used = ai_response.tokens_used
                db.commit()
                
                # Отправляем ответ
                response_msg = schemas.WSBotResponse(
                    message=db_message
                ).dict()
                
                await manager.send_personal_message(response_msg, user.id)
                
            except Exception as ai_error:
                error_msg = f"Ошибка AI: {str(ai_error)}"
                error_response = schemas.WSError(message=error_msg).dict()
                await manager.send_personal_message(error_response, user.id)
        
        elif msg_type == "create_session":
            # Создание новой сессии
            new_session = crud.create_session(db, schemas.SessionCreate(), user.id)
            manager.user_sessions[user.id] = new_session.id
            
            session_msg = schemas.WSSessionCreated(session=new_session).dict()
            await manager.send_personal_message(session_msg, user.id)
    
    except json.JSONDecodeError:
        error_msg = schemas.WSError(message="Неверный формат JSON").dict()
        await manager.send_personal_message(error_msg, user.id)
    except Exception as e:
        error_msg = schemas.WSError(message=f"Ошибка обработки: {str(e)}").dict()
        await manager.send_personal_message(error_msg, user.id)
