import logging
from config.settings import Settings
from utils.telegram_notifier import TelegramNotifier

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Test Telegram notification"""
    settings = Settings()
    
    if not settings.telegram_bot_token:
        logger.error("No Telegram bot token found in settings", exc_info=True)
        return
        
    if not settings.telegram_chat_id:
        logger.error("No Telegram chat ID found in settings", exc_info=True)
        logger.info("Run utils/get_telegram_chat_id.py to get your chat ID")
        return
    
    notifier = TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id)
    
    # Create a sample analysis
    sample_analysis = {
        "symbol": "BTC-USDT",
        "timestamp": "2023-07-15T14:30:00Z",
        "price": 29876.45,
        "indicators": {
            "RSI_14": {
                "indicator": "RSI_14",
                "value": 72.34,
                "signal": "bearish",
                "strength": 0.65
            },
            "MACD_12_26_9": {
                "indicator": "MACD_12_26_9",
                "value": {
                    "macd": 12.5,
                    "signal": 9.8,
                    "histogram": 2.7
                },
                "signal": "bullish",
                "strength": 0.54
            }
        },
        "sentiment": {
            "overall": "buy",
            "strength": "strong",
            "confidence": 0.82,
            "score": 0.67
        },
        "analysis_summary": "BTC-USDT shows strong bullish momentum with RSI entering overbought territory. Price is trading above key moving averages with positive MACD histogram."
    }
    
    # Send test notification
    success = notifier.send_analysis_alert("BTC-USDT", sample_analysis)
    
    if success:
        logger.info("Test notification sent successfully")
    else:
        logger.error("Failed to send test notification", exc_info=True)

if __name__ == "__main__":
    main()
