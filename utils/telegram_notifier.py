import requests
import logging
from typing import Dict, Any, List, Optional
import os, json
from datetime import datetime, timedelta

class TelegramNotifier:
    """
    Sends notifications to Telegram
    """
    
    def __init__(self, bot_token: str, chat_id: Optional[str] = None, notification_cooldown: int = 4):
        """
        Initialize the Telegram notifier
        
        Args:
            bot_token (str): Telegram bot token
            chat_id (str, optional): Default chat ID to send messages to
            notification_cooldown (int): Hours to wait before sending another notification for the same symbol
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.logger = logging.getLogger(__name__)
        self.notification_cooldown = notification_cooldown
        
        # Store for recent notifications: {symbol: {"timestamp": datetime, "sentiment": str}}
        self.recent_notifications = {}
        
        # Create storage directory if it doesn't exist
        self.storage_dir = "data/telegram"
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Load previous notifications from file
        self._load_notifications()

    def _load_notifications(self):
        """Load recent notifications from file"""
        try:
            notification_file = os.path.join(self.storage_dir, "recent_notifications.json")
            if os.path.exists(notification_file):
                with open(notification_file, 'r') as f:
                    stored_notifications = json.load(f)
                
                # Convert stored timestamps back to datetime objects
                for symbol, data in stored_notifications.items():
                    if "timestamp" in data:
                        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
                
                self.recent_notifications = stored_notifications
                self.logger.info(f"Loaded {len(self.recent_notifications)} recent notifications from storage")
        except Exception as e:
            self.logger.error(f"Error loading recent notifications: {str(e)}")
            self.recent_notifications = {}
    
    def _save_notifications(self):
        """Save recent notifications to file"""
        try:
            # Convert datetime objects to ISO format strings for JSON serialization
            serializable_notifications = {}
            for symbol, data in self.recent_notifications.items():
                serializable_notifications[symbol] = data.copy()
                if "timestamp" in data and isinstance(data["timestamp"], datetime):
                    serializable_notifications[symbol]["timestamp"] = data["timestamp"].isoformat()
            
            notification_file = os.path.join(self.storage_dir, "recent_notifications.json")
            with open(notification_file, 'w') as f:
                json.dump(serializable_notifications, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving recent notifications: {str(e)}")
    
    def _clean_old_notifications(self):
        """Remove notifications older than the cooldown period"""
        now = datetime.now()
        cooldown_threshold = now - timedelta(hours=self.notification_cooldown)
        
        # Find symbols with old notifications
        symbols_to_remove = []
        for symbol, data in self.recent_notifications.items():
            if data.get("timestamp") < cooldown_threshold:
                symbols_to_remove.append(symbol)
        
        # Remove old notifications
        for symbol in symbols_to_remove:
            del self.recent_notifications[symbol]
        
        if symbols_to_remove:
            self.logger.info(f"Cleaned {len(symbols_to_remove)} old notifications")
            self._save_notifications()

    def should_notify(self, symbol: str, sentiment: Dict[str, Any]) -> bool:
        """
        Check if we should send a notification for this symbol
        
        Args:
            symbol (str): Symbol being analyzed
            sentiment (Dict[str, Any]): Sentiment data
            
        Returns:
            bool: True if notification should be sent
        """
        now = datetime.now()
        
        # Clean old notifications first
        self._clean_old_notifications()
        
        # Check if we have a recent notification for this symbol
        if symbol in self.recent_notifications:
            last_notification = self.recent_notifications[symbol]
            last_timestamp = last_notification.get("timestamp")
            last_sentiment = last_notification.get("sentiment", {})
            
            # If last notification is within cooldown period
            if last_timestamp and now - last_timestamp < timedelta(hours=self.notification_cooldown):
                # Check if sentiment has changed significantly
                if (last_sentiment.get("overall") == sentiment.get("overall") and 
                    last_sentiment.get("strength") == sentiment.get("strength")):
                    # Same sentiment, don't notify again
                    self.logger.info(f"Skipping notification for {symbol}: last notification was {(now - last_timestamp).total_seconds() / 3600:.1f} hours ago with same sentiment")
                    return False
        
        # Store this notification
        self.recent_notifications[symbol] = {
            "timestamp": now,
            "sentiment": {
                "overall": sentiment.get("overall"),
                "strength": sentiment.get("strength")
            }
        }
        self._save_notifications()
        
        return True

    def send_message(self, message: str, chat_id: Optional[str] = None) -> bool:
        """
        Send a message to Telegram
        
        Args:
            message (str): Message to send
            chat_id (str, optional): Chat ID to send message to (overrides default)
            
        Returns:
            bool: True if message was sent successfully
        """
        if not chat_id and not self.chat_id:
            self.logger.error("No chat ID provided")
            return False
        
        target_chat_id = chat_id or self.chat_id
        
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": target_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            self.logger.info(f"Telegram message sent to {target_chat_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {str(e)}")
            return False
    
    def send_analysis_alert(self, symbol: str, analysis: Dict[str, Any], chat_id: Optional[str] = None) -> bool:
        """
        Send an analysis alert to Telegram
        
        Args:
            symbol (str): Symbol being analyzed
            analysis (Dict[str, Any]): Analysis data
            chat_id (str, optional): Chat ID to send message to
            
        Returns:
            bool: True if message was sent successfully
        """
        try:
            sentiment = analysis.get("sentiment", {})
            
            # Check if we should send a notification
            if not self.should_notify(symbol, sentiment):
                return False
            
            overall = sentiment.get("overall", "neutral")
            strength = sentiment.get("strength", "none")
            confidence = sentiment.get("confidence", 0.0)
            price = analysis.get("price", 0.0)
            
            message = f"<b>🚨 {symbol} Alert: {strength.upper()} {overall.upper()}</b>\n\n"
            message += f"💰 Current Price: ${str(price)}\n"
            message += f"🎯 Sentiment: {strength} {overall}\n"
            message += f"🔍 Confidence: {confidence:.2f}\n\n"
            
            # Add summary if available
            if "analysis_summary" in analysis:
                message += f"<i>{analysis['analysis_summary']}</i>\n\n"
            
            # Add indicators if available
            if "indicators" in analysis and analysis["indicators"]:
                message += "<b>Key Indicators:</b>\n"
                for name, indicator in analysis["indicators"].items():
                    if name.startswith("RSI"):
                        message += f"• RSI: {indicator['value']:.2f}\n"
                    elif name.startswith("MACD"):
                        if isinstance(indicator['value'], dict):
                            histogram = indicator['value'].get('histogram', 0)
                            message += f"• MACD Histogram: {histogram:.2f}\n"
                    elif name.startswith("BBANDS"):
                        if isinstance(indicator['value'], dict):
                            percent_b = indicator['value'].get('percent_b', 0.5)
                            message += f"• BB %B: {percent_b:.2f}\n"
            
            message += f"\n<i>Generated at {analysis.get('timestamp', 'N/A')}</i>"
            
            return self.send_message(message, chat_id)
            
        except Exception as e:
            self.logger.error(f"Error creating analysis alert: {str(e)}")
            return False
    
    def get_updates(self) -> List[Dict[str, Any]]:
        """
        Get updates from Telegram
        
        Returns:
            List[Dict[str, Any]]: List of updates
        """
        try:
            url = f"{self.base_url}/getUpdates"
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            if data.get("ok"):
                return data.get("result", [])
            else:
                self.logger.error(f"Error getting updates: {data.get('description')}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting updates: {str(e)}")
            return []
    
    def get_chat_id(self) -> Optional[str]:
        """
        Get the chat ID from the most recent message
        
        Returns:
            Optional[str]: Chat ID or None if not found
        """
        updates = self.get_updates()
        
        if not updates:
            self.logger.warning("No updates found")
            return None
        
        # Get the most recent message
        latest_update = updates[-1]
        message = latest_update.get("message")
        
        if message and "chat" in message:
            chat_id = message["chat"].get("id")
            self.logger.info(f"Found chat ID: {chat_id}")
            return str(chat_id)
        
        self.logger.warning("No chat ID found in updates")
        return None
