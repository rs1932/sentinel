from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "Sentinel Access Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/sentinel_db"
    DATABASE_SCHEMA: str = "sentinel"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    REDIS_ENABLED: bool = False
    REDIS_URL: Optional[str] = "redis://localhost:6379"
    CACHE_BACKEND: str = "memory"
    CACHE_TTL: int = 300
    
    JWT_SECRET_KEY: str = "your-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    APPROVAL_TIMEOUT_HOURS: int = 48
    AUTO_APPROVE_ENABLED: bool = False
    
    BIOMETRICS_ENABLED: bool = False
    KEYSTROKE_THRESHOLD: float = 0.7
    MOUSE_MOVEMENT_THRESHOLD: float = 0.6
    
    FEATURE_STORE_TTL: int = 3600
    FEATURE_COMPUTE_BATCH_SIZE: int = 100
    
    AGENT_MESSAGE_TIMEOUT: int = 30
    AGENT_RETRY_COUNT: int = 3
    
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    
    CORS_ENABLED: bool = True
    CORS_ALLOW_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]
    CORS_ALLOW_METHODS: list = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()