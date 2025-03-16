import os
import json
import logging
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    api_username: str = os.getenv("API_USERNAME", "admin")
    api_password: str = os.getenv("API_PASSWORD", "password")
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-for-jwt")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # KuCoin API Settings
    kucoin_api_key: str = os.getenv("KUCOIN_API_KEY", "")
    kucoin_api_secret: str = os.getenv("KUCOIN_API_SECRET", "")
    kucoin_api_passphrase: str = os.getenv("KUCOIN_API_PASSPHRASE", "")
    
    # Analysis Settings
    analysis_interval: int = os.getenv("ANALYSIS_INTERVAL", 60) # minutes
    default_timeframes: list = ["4hour", "1day", "1week"]
    
    class Config:
        env_file = ".env"
