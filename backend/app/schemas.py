from pydantic import BaseModel, EmailStr, constr
from datetime import datetime
from typing import List, Optional

# User schemas
class UserBase(BaseModel):
    username: constr(min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: constr(min_length=6)

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    username: str
    password: str

# Chat schemas
class MessageCreate(BaseModel):
    content: constr(min_length=1, max_length=1000)
    session_id: Optional[str] = None

class MessageResponse(BaseModel):
    id: int
    content: str
    sender: str
    timestamp: datetime
    
    class Config:
        from_attributes = True

class ChatSessionResponse(BaseModel):
    id: int
    session_id: str
    created_at: datetime
    messages: List[MessageResponse] = []
    
    class Config:
        from_attributes = True

class BotResponse(BaseModel):
    message: MessageResponse
    session_id: str
