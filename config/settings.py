import os
import json
import logging
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from config.user_config import UserConfig

# Initialize user config
user_config = UserConfig()

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
    default_timeframes: list = user_config.get_config().get("analysis", {}).get("timeframes", [])

    # Telegram Settings
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    telegram_notifications_enabled: bool = os.getenv("TELEGRAM_NOTIFICATIONS_ENABLED", "true").lower() == "true"
    telegram_notify_on_sentiment: list = ["strong buy", "moderate buy"]  # Sentiments to notify on

    main_timeframe: str = os.getenv("MAIN_TIMEFRAME", "1hour")  # Primary timeframe for analysis

    class Config:
        env_file = ".env"
