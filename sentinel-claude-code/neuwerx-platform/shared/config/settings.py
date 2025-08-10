"""
Shared configuration management for the neuwerx-platform.
This modular approach makes it easy to split configurations when separating services.
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
from enum import Enum

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class BaseConfig(BaseSettings):
    """Base configuration that's common to all services."""
    
    # Application
    APP_NAME: str = "Neuwerx Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    
    # Database (shared by both Sentinel and Metamorphic)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/sentinel_db"
    DATABASE_SCHEMA: str = "sentinel"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # CORS (shared web configuration)
    CORS_ENABLED: bool = True
    CORS_ALLOW_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields to be ignored

class SentinelConfig(BaseConfig):
    """
    Sentinel-specific configuration.
    In separate services, this would be in sentinel/backend/config.py
    """
    
    # Cache Configuration
    REDIS_ENABLED: bool = False
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_BACKEND: str = "memory"
    CACHE_TTL: int = 300
    
    # Authentication & JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Password Policy
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # Account Security
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    
    # Approval Workflows
    APPROVAL_TIMEOUT_HOURS: int = 48
    AUTO_APPROVE_ENABLED: bool = False
    
    # Biometrics
    BIOMETRICS_ENABLED: bool = False
    KEYSTROKE_THRESHOLD: float = 0.7
    MOUSE_MOVEMENT_THRESHOLD: float = 0.6
    
    # Feature Store
    FEATURE_STORE_TTL: int = 3600
    FEATURE_COMPUTE_BATCH_SIZE: int = 100
    
    # Agent Configuration
    AGENT_MESSAGE_TIMEOUT: int = 30
    AGENT_RETRY_COUNT: int = 3
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60

class MetamorphicConfig(BaseConfig):
    """
    Metamorphic-specific configuration.
    In separate services, this would be in metamorphic/backend/config.py
    """
    
    # Field Management
    MAX_FIELDS_PER_ENTITY: int = 100
    MAX_FIELD_NAME_LENGTH: int = 100
    FIELD_CACHE_TTL: int = 3600
    
    # Field Promotion Rules
    PROMOTION_THRESHOLD_PERCENTAGE: float = 0.7  # 70% of tenants
    PROMOTION_USAGE_THRESHOLD: int = 1000  # queries per day
    
    # Performance Settings
    BATCH_OPERATION_SIZE: int = 100
    FIELD_INDEX_ENABLED: bool = True

class UnifiedPlatformSettings(BaseConfig):
    """
    Unified platform settings that include both Sentinel and Metamorphic configs.
    This makes it easy to access all settings in one place during unified deployment.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Create sub-configurations using object.__setattr__ to bypass Pydantic validation
        object.__setattr__(self, 'sentinel', SentinelConfig(**kwargs))
        object.__setattr__(self, 'metamorphic', MetamorphicConfig(**kwargs))
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == Environment.DEVELOPMENT
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == Environment.PRODUCTION
    
    def get_database_url(self, service: str = "default") -> str:
        """
        Get database URL for a specific service.
        In separate services, each would have its own database configuration.
        """
        # For now, both services share the same database
        # Later, this could return different URLs for different services
        return self.DATABASE_URL
    
    def get_cors_config(self) -> dict:
        """Get CORS configuration for FastAPI."""
        return {
            "allow_origins": self.CORS_ALLOW_ORIGINS,
            "allow_credentials": True,
            "allow_methods": self.CORS_ALLOW_METHODS,
            "allow_headers": self.CORS_ALLOW_HEADERS,
        }

# Global settings instance
settings: Optional[UnifiedPlatformSettings] = None

def get_settings() -> UnifiedPlatformSettings:
    """
    Get the global settings instance.
    This function signature stays the same for both unified and separate architectures.
    """
    global settings
    if not settings:
        settings = UnifiedPlatformSettings()
    return settings

def initialize_settings(env_file: Optional[str] = None) -> UnifiedPlatformSettings:
    """
    Initialize settings with optional environment file.
    This allows different services to use different .env files when separated.
    """
    global settings
    if env_file:
        settings = UnifiedPlatformSettings(_env_file=env_file)
    else:
        settings = UnifiedPlatformSettings()
    return settings