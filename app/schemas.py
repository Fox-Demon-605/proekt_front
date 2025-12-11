from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional


# User Schemas
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class TokenData(BaseModel):
    email: Optional[str] = None


# Session Schemas
class SessionBase(BaseModel):
    title: Optional[str] = None


class SessionCreate(SessionBase):
    pass


class SessionResponse(SessionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    
    class Config:
        from_attributes = True


# Message Schemas
class MessageBase(BaseModel):
    content: str
    sender: str


class MessageCreate(MessageBase):
    session_id: int


class MessageResponse(MessageBase):
    id: int
    session_id: int
    created_at: datetime
    tokens_used: Optional[int] = None
    
    class Config:
        from_attributes = True


# WebSocket Schemas
class WSMessage(BaseModel):
    type: str
    message: Optional[str] = None
    session_id: Optional[int] = None


class WSSessionCreated(BaseModel):
    type: str = "session_created"
    session: SessionResponse


class WSBotTyping(BaseModel):
    type: str = "bot_typing"


class WSBotResponse(BaseModel):
    type: str = "bot_response"
    message: MessageResponse


class WSError(BaseModel):
    type type: str = "error"
    message: str


# AI Response
class AIRequest(BaseModel):
    messages: List[dict]
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class AIResponse(BaseModel):
    content: str
    tokens_used: int
