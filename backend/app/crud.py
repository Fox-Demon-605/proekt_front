from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from . import models
from .auth import hash_password, verify_password
from typing import Optional

async def create_user(db: AsyncSession, email: str, password: str):
    user = models.User(email=email, hashed_password=hash_password(password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[models.User]:
    q = await db.execute(select(models.User).where(models.User.email==email))
    return q.scalars().first()

async def create_session(db: AsyncSession, user_id: int = None, title: str = None):
    s = models.Session(title=title, user_id=user_id)
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s

async def get_session(db: AsyncSession, session_id: int):
    q = await db.execute(select(models.Session).where(models.Session.id==session_id))
    return q.scalars().first()

async def save_message(db: AsyncSession, session: models.Session, sender: str, text: str):
    m = models.Message(session_id=session.id, sender=sender, text=text)
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return m

async def get_history(db: AsyncSession, session: models.Session):
    await db.refresh(session)
    return session.messages
