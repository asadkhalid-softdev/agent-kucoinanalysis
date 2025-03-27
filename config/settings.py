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

    # Strategy-specific Settings
    momentum_score_threshold: float = float(os.getenv("MOMENTUM_SCORE_THRESHOLD", "0.5"))
    momentum_confidence_threshold: float = float(os.getenv("MOMENTUM_CONFIDENCE_THRESHOLD", "0.6"))
    mean_reversion_score_threshold: float = float(os.getenv("MEAN_REVERSION_SCORE_THRESHOLD", "0.5"))
    mean_reversion_confidence_threshold: float = float(os.getenv("MEAN_REVERSION_CONFIDENCE_THRESHOLD", "0.6"))
    breakout_score_threshold: float = float(os.getenv("BREAKOUT_SCORE_THRESHOLD", "0.5"))
    breakout_confidence_threshold: float = float(os.getenv("BREAKOUT_CONFIDENCE_THRESHOLD", "0.6"))

    # Strategy Filters
    enable_momentum_strategy: bool = os.getenv("ENABLE_MOMENTUM_STRATEGY", "true").lower() == "true"
    enable_mean_reversion_strategy: bool = os.getenv("ENABLE_MEAN_REVERSION_STRATEGY", "true").lower() == "true"
    enable_breakout_strategy: bool = os.getenv("ENABLE_BREAKOUT_STRATEGY", "true").lower() == "true"

    # Telegram Settings
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    telegram_notifications_enabled: bool = os.getenv("TELEGRAM_NOTIFICATIONS_ENABLED", "false").lower() == "true"
    telegram_notify_on_volume: float = float(os.getenv("TELEGRAM_NOTIFY_ON_VOLUME", "0"))
    telegram_notify_on_rsi_buy: float = float(os.getenv("TELEGRAM_NOTIFY_ON_RSI_BUY", "70"))

    class Config:
        env_file = ".env"
