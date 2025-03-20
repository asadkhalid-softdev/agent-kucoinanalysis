import logging
from config.settings import Settings
from utils.telegram_notifier import TelegramNotifier

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Get and display Telegram chat ID"""
    settings = Settings()
    
    if not settings.telegram_bot_token:
        logger.error("No Telegram bot token found in settings", exc_info=True)
        return
    
    notifier = TelegramNotifier(settings.telegram_bot_token)
    
    logger.info("Checking for Telegram updates...")
    logger.info("Please send a message to your bot if you haven't already")
    
    chat_id = notifier.get_chat_id()
    
    if chat_id:
        logger.info(f"Found chat ID: {chat_id}")
        logger.info(f"Add this to your .env file as TELEGRAM_CHAT_ID={chat_id}")
        
        # Send a test message
        notifier.send_message(f"Hello! Your chat ID is {chat_id}. "
                             "You will receive notifications here when strong buy/sell signals are detected.", 
                             chat_id)
    else:
        logger.error("No chat ID found. Please send a message to your bot and try again.", exc_info=True)

if __name__ == "__main__":
    main()
