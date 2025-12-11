from pydantic import BaseModel, EmailStr, constr
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=6)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MessageCreate(BaseModel):
    session_id: int
    text: constr(min_length=1, max_length=2000)

class MessageOut(BaseModel):
    id: int
    sender: str
    text: str
    created_at: datetime

    class Config:
        orm_mode = True

class SessionCreate(BaseModel):
    title: Optional[str] = None

class SessionOut(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime
    messages: List[MessageOut] = []

    class Config:
        orm_mode = True

class ChatHistory(BaseModel):
    messages: List[MessageOut]
