"""Core configuration settings for AgentOps API service."""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable fallbacks."""
    
    # App Information
    APP_NAME: str = "AgentOps API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security & Auth
    SECRET_KEY: str = "agentops-super-secret-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Allowed CORS Origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]
    
    # Database Settings
    # Supports postgresql+asyncpg:// or sqlite+aiosqlite:///
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite+aiosqlite:///./agentops.db"
    )
    
    # Redis Settings
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", None)
    
    # Rate Limiting Defaults
    DEFAULT_RATE_LIMIT_PER_MINUTE: int = 120
    INGEST_RATE_LIMIT_PER_MINUTE: int = 600
    
    # Agent Runtime Defaults
    MAX_AGENT_STEPS: int = 10
    AGENT_TIMEOUT_SECONDS: int = 60
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )


settings = Settings()
