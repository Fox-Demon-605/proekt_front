from sqlalchemy.orm import Session
from sqlalchemy import desc
from app import models, schemas, auth
from typing import List, Optional


# User CRUD
def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Создаем первую сессию для пользователя
    create_session(db, schemas.SessionCreate(), db_user.id)
    
    return db_user


# Session CRUD
def get_user_sessions(db: Session, user_id: int) -> List[models.Session]:
    return db.query(models.Session).filter(
        models.Session.user_id == user_id,
        models.Session.is_active == True
    ).order_by(desc(models.Session.updated_at)).all()


def get_session_by_id(db: Session, session_id: int, user_id: int) -> Optional[models.Session]:
    return db.query(models.Session).filter(
        models.Session.id == session_id,
        models.Session.user_id == user_id,
        models.Session.is_active == True
    ).first()


def get_current_session(db: Session, user_id: int) -> Optional[models.Session]:
    return db.query(models.Session).filter(
        models.Session.user_id == user_id,
        models.Session.is_active == True
    ).order_by(desc(models.Session.updated_at)).first()


def create_session(db: Session, session: schemas.SessionCreate, user_id: int) -> models.Session:
    db_session = models.Session(**session.dict(), user_id=user_id)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def update_session_title(db: Session, session_id: int, title: str) -> models.Session:
    session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if session:
        session.title = title
        db.commit()
        db.refresh(session)
    return session


def deactivate_session(db: Session, session_id: int, user_id: int) -> bool:
    session = get_session_by_id(db, session_id, user_id)
    if session:
        session.is_active = False
        db.commit()
        return True
    return False


# Message CRUD
def get_session_messages(db: Session, session_id: int, user_id: int) -> List[models.Message]:
    session = get_session_by_id(db, session_id, user_id)
    if not session:
        return []
    
    return db.query(models.Message).filter(
        models.Message.session_id == session_id
    ).order_by(models.Message.created_at).all()


def create_message(db: Session, message: schemas.MessageCreate, user_id: int) -> models.Message:
    # Проверяем, что сессия принадлежит пользователю
    session = get_session_by_id(db, message.session_id, user_id)
    if not session:
        raise ValueError("Session not found or access denied")
    
    db_message = models.Message(**message.dict())
    db.add(db_message)
    
    # Обновляем время сессии
    session.updated_at = db.func.now()
    
    db.commit()
    db.refresh(db_message)
    return db_message


def get_last_messages(db: Session, session_id: int, limit: int = 10) -> List[models.Message]:
    return db.query(models.Message).filter(
        models.Message.session_id == session_id
    ).order_by(desc(models.Message.created_at)).limit(limit).all()
