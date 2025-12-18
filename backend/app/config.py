"""Application configuration"""

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application
    app_name: str = "CGRAPH"
    app_version: str = "3.0.0"
    debug: bool = False
    
    # Database
    database_url: str = "postgresql://cgraph:secure_password@localhost:5432/cgraph"
    database_echo: bool = False
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Security
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    
    # External APIs
    stripe_api_key: str = ""
    matrix_homeserver: str = "https://matrix.org"
    
    # CORS
    allowed_origins: list = ["https://www.cgraph.org"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
