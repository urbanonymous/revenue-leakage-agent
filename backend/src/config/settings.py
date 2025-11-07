"""Application configuration using Pydantic BaseSettings"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal, List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_max_retries: int = 2
    
    # API Configuration
    api_title: str = "Revenue Leakage Detection Agent API"
    api_description: str = "AI-powered revenue leakage detection and correction system"
    api_version: str = "1.0.0"
    
    # CORS Configuration
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    
    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "DEBUG"
    
    # Investigation Configuration
    invoice_date_tolerance_days: int = 5
    min_amount_threshold: float = 0.01
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance (singleton pattern)"""
    return Settings()

