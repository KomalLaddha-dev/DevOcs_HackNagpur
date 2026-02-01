"""
Application Configuration Settings
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    PROJECT_NAME: str = "SmartCare API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/smartcare"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    
    # AI Model (optional - rule-based triage works without trained model)
    AI_MODEL_PATH: str = "./ai/models/trained/triage_model.pkl"
    USE_ML_MODEL: bool = False  # Set True only if you have trained a model
    
    # Queue Settings
    QUEUE_UPDATE_INTERVAL: int = 300  # 5 minutes
    MAX_QUEUE_SIZE: int = 500
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
