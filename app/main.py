from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import uvicorn

from app import crud, schemas, auth
from app.database import engine, Base, get_db
from app.config import settings
from app.websocket import handle_websocket
from app.dependencies import get_current_user, get_current_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создание таблиц при запуске
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    yield
    print("🚪 Shutting down...")


app = FastAPI(
    title="AI Chatbot API",
    description="Backend для AI чат-бота с WebSocket",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


# Health check
@app.get("/")
async def root():
    return {"message": "AI Chatbot API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Auth endpoints
@app.post("/api/auth/register", response_model=schemas.UserResponse)
async def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    return crud.create_user(db, user)


@app.post("/api/auth/login", response_model=schemas.Token)
async def login(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=user_data.email)
    if not user or not auth.verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token = auth.create_access_token(data={"sub": user.email})
    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
        user=user
    )


@app.get("/api/auth/me", response_model=schemas.UserResponse)
async def get_current_user_info(user=Depends(get_current_user)):
    return user


# Session endpoints
@app.get("/api/sessions", response_model=list[schemas.SessionResponse])
async def get_sessions(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.get_user_sessions(db, user.id)


@app.get("/api/sessions/current", response_model=schemas.SessionResponse)
async def get_current_session_info(session=Depends(get_current_session)):
    return session


@app.post("/api/sessions/new", response_model=schemas.SessionResponse)
async def create_new_session(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.create_session(db, schemas.SessionCreate(), user.id)


@app.get("/api/sessions/{session_id}", response_model=schemas.SessionResponse)
async def get_session(
    session_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = crud.get_session_by_id(db, session_id, user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session


@app.delete("/api/sessions/{session_id}")
async def delete_session(
    session_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = crud.deactivate_session(db, session_id, user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return {"message": "Session deleted"}


# Message endpoints
@app.get("/api/sessions/{session_id}/messages", response_model=list[schemas.MessageResponse])
async def get_messages(
    session_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.get_session_messages(db, session_id, user.id)


@app.post("/api/sessions/{session_id}/messages", response_model=schemas.MessageResponse)
async def create_message(
    session_id: int,
    message: schemas.MessageCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    message.session_id = session_id
    return crud.create_message(db, message, user.id)


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    if not token:
        await websocket.close(code=1008)
        return
    
    await handle_websocket(websocket, token)


# AI endpoints (опционально, для тестирования)
@app.post("/api/ai/generate")
async def generate_ai_response(
    request: schemas.AIRequest,
    user=Depends(get_current_user)
):
    from app.ai_service import ai_service
    
    try:
        response = await ai_service.generate_response(request.messages)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
