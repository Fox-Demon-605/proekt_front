from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app import auth, crud

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    token_data = auth.verify_token(token)
    
    user = crud.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


def get_current_session(
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = crud.get_current_session(db, user.id)
    if not session:
        # Создаем новую сессию, если нет активной
        session = crud.create_session(db, {}, user.id)
    
    return session
