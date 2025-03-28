import requests
import logging
from typing import Dict, Any, List, Optional
import os, json
from datetime import datetime, timedelta, timezone
import numpy as np
from config.settings import Settings

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.datetime64):
            return obj.astype(str)
        elif isinstance(obj, np.timedelta64):
            return obj.astype(str)
        return super(NumpyEncoder, self).default(obj)

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
            self.logger.error(f"Error loading recent notifications: {str(e)}", exc_info=True)
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
                json.dump(serializable_notifications, f, indent=2, cls=NumpyEncoder)
        except Exception as e:
            self.logger.error(f"Error saving recent notifications: {str(e)}", exc_info=True)
    
    def _clean_old_notifications(self):
        """Remove notifications older than the cooldown period"""
        now = datetime.now(timezone.utc)
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
        now = datetime.now(timezone.utc)
        
        # Clean old notifications first
        self._clean_old_notifications()
        
        # Extract sentiment data with defaults
        current_sentiment = {
            "strategy": sentiment.get("strategy", {}),
            "overall": "neutral",  # Will be calculated based on strategy scores
            "strength": "none",    # Will be calculated based on confidence
            "confidence": 0.0,     # Will be calculated based on strategy confidences
            "score": 0.0          # Will be calculated based on strategy scores
        }
        
        # Calculate overall sentiment based on strategy scores
        strategy_scores = []
        strategy_confidences = []
        for strategy_name, data in current_sentiment["strategy"].items():
            score = data.get("score", 0.0)
            confidence = data.get("confidence", 0.0)
            strategy_scores.append(score)
            strategy_confidences.append(confidence)
        
        if strategy_scores:
            # Calculate overall score as weighted average of strategy scores
            current_sentiment["score"] = sum(score * conf for score, conf in zip(strategy_scores, strategy_confidences)) / sum(strategy_confidences)
            
            # Determine overall sentiment
            if current_sentiment["score"] >= 0.5:
                current_sentiment["overall"] = "buy"
            elif current_sentiment["score"] <= -0.5:
                current_sentiment["overall"] = "sell"
            else:
                current_sentiment["overall"] = "neutral"
            
            # Calculate overall confidence
            current_sentiment["confidence"] = sum(strategy_confidences) / len(strategy_confidences)
            
            # Determine strength based on confidence
            if current_sentiment["confidence"] >= 0.7:
                current_sentiment["strength"] = "strong"
            elif current_sentiment["confidence"] >= 0.5:
                current_sentiment["strength"] = "moderate"
            else:
                current_sentiment["strength"] = "weak"
        
        # Check if we have a recent notification for this symbol
        if symbol in self.recent_notifications:
            last_notification = self.recent_notifications[symbol]
            last_timestamp = last_notification.get("timestamp")
            last_sentiment = last_notification.get("sentiment", {})
            
            # If last notification is within cooldown period
            if (last_timestamp and now - last_timestamp < timedelta(hours=self.notification_cooldown)):
                # Only notify if confidence has increased significantly
                if current_sentiment["confidence"] <= last_sentiment.get("confidence", 0.0):
                    self.logger.info(f"Skipping notification for {symbol}: last notification was {(now - last_timestamp).total_seconds() / 3600:.1f} hours ago with same or higher confidence")
                    return False
                # Also check if sentiment has changed significantly
                if (current_sentiment["overall"] == last_sentiment.get("overall") and 
                    current_sentiment["strength"] == last_sentiment.get("strength")):
                    self.logger.info(f"Skipping notification for {symbol}: sentiment hasn't changed significantly")
                    return False
        
        # Store this notification with complete sentiment data
        self.recent_notifications[symbol] = {
            "timestamp": now,
            "sentiment": current_sentiment
        }
        self._save_notifications()
        
        self.logger.info(f"Storing new notification for {symbol} with sentiment: {current_sentiment}")
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
            self.logger.error("No chat ID provided", exc_info=True)
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
            self.logger.error(f"Error sending Telegram message: {str(e)}", exc_info=True)
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
            strategy = sentiment.get("strategy", {})
            settings = Settings()
            
            # Check if we should send a notification
            if not self.should_notify(symbol, sentiment):
                return False
            
            # Get basic analysis data
            volume = analysis.get("volume", 0.0)
            price = analysis.get("price", 0.0)
            
            # Build the message
            message = f"<b>🚨 {symbol} Alert</b>\n\n"
            message += f"💰 Current Price: ${price:,.2f}\n"
            message += f"📊 Volume: {volume:,.0f}\n\n"
            
            # Add strategy details
            message += "<b>Strategy Analysis:</b>\n"
            for strategy_name, data in strategy.items():
                score = data.get("score", 0.0)
                confidence = data.get("confidence", 0.0)
                
                # Get thresholds for this strategy
                score_threshold = getattr(settings, f"{strategy_name.lower()}_score_threshold", 0.5)
                confidence_threshold = getattr(settings, f"{strategy_name.lower()}_confidence_threshold", 0.6)
                
                # Determine signal based on thresholds
                if score >= score_threshold and confidence >= confidence_threshold:
                    signal = "🟢"  # Strong buy signal
                else:
                    signal = "🔴"  # Strong sell signal
                
                message += f"• {strategy_name.title().replace('_', ' ')}: {signal} Score: {score:.2f} (Confidence: {confidence:.2f})\n"
            
            # Add indicators if available
            if "indicators" in analysis and analysis["indicators"]:
                message += "\n<b>Key Indicators:</b>\n"
                for name, indicator in analysis["indicators"].items():
                    if name.startswith("RSI"):
                        rsi_value = indicator.get("value", {}).get("rsi", 0.0)
                        message += f"• RSI: {rsi_value:.2f}\n"
                    elif name.startswith("FIBONACCI"):
                        if isinstance(indicator.get("value"), dict):
                            closest_level = indicator["value"].get("current_level", "Unknown")
                            fib_message = f"• Fibonacci: Near {closest_level} level"
                            message += fib_message + "\n"
                    # elif name.startswith("MACD"):
                    #     macd_data = indicator.get("value", {})
                    #     message += f"• MACD: {macd_data.get('macd', 0.0):.2f} (Signal: {macd_data.get('signal', 0.0):.2f})\n"
                    # elif name.startswith("BBANDS"):
                    #     bbands_data = indicator.get("value", {})
                    #     message += f"• BB: Upper: {bbands_data.get('upper', 0.0):.2f} Lower: {bbands_data.get('lower', 0.0):.2f}\n"

            # Add timestamp
            message += f"\n<i>Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC</i>"
            
            return self.send_message(message, chat_id)
            
        except Exception as e:
            self.logger.error(f"Error creating analysis alert: {str(e)}", exc_info=True)
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
                self.logger.error(f"Error getting updates: {data.get('description')}", exc_info=True)
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting updates: {str(e)}", exc_info=True)
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