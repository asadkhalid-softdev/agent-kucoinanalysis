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
    analysis_interval: int = user_config.get_config().get("analysis", {}).get("interval", "1") # in minutes
    default_timeframes: list = user_config.get_config().get("analysis", {}).get("timeframes", ["1hour"])
    main_timeframe: str = user_config.get_config().get("analysis", {}).get("main_timeframe", "1hour")

    # Telegram Settings
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    telegram_notifications_enabled: bool = user_config.get_config().get("telegram", {}).get("telegram_notifications_enabled", False)
    telegram_notify_on_sentiment: list = user_config.get_config().get("telegram", {}).get("telegram_notify_on_sentiment", ["strong buy"])
    telegram_notify_on_confidence: float = user_config.get_config().get("telegram", {}).get("telegram_notify_on_confidence", 0)
    telegram_notify_on_volume: float = user_config.get_config().get("telegram", {}).get("telegram_notify_on_volume", 100000)
    telegram_notify_on_plr: float = user_config.get_config().get("telegram", {}).get("telegram_notify_on_plr", 0.0)
    telegram_notify_on_rsi_buy: float = user_config.get_config().get("telegram", {}).get("telegram_notify_on_rsi_buy", 100)

    class Config:
        env_file = ".env"
