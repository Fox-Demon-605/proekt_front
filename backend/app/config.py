import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Для Vercel используем PostgreSQL
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://user:password@localhost/weather_chatbot"
    )
    
    # Для локальной разработки - SQLite
    if "localhost" in database_url or "127.0.0.1" in database_url:
        database_url = database_url.replace("postgresql://", "sqlite:///")
    
       secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    class Config:
        env_file = ".env"

settings = Settings()
