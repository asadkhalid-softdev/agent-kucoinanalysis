import requests
import logging
from typing import Dict, Any, List, Optional

class TelegramNotifier:
    """
    Sends notifications to Telegram
    """
    
    def __init__(self, bot_token: str, chat_id: Optional[str] = None):
        """
        Initialize the Telegram notifier
        
        Args:
            bot_token (str): Telegram bot token
            chat_id (str, optional): Default chat ID to send messages to
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.logger = logging.getLogger(__name__)
    
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
            overall = sentiment.get("overall", "neutral")
            strength = sentiment.get("strength", "none")
            confidence = sentiment.get("confidence", 0.0)
            price = analysis.get("price", 0.0)
            
            message = f"<b>🚨 {symbol} Alert: {strength.upper()} {overall.upper()}</b>\n\n"
            message += f"💰 Current Price: ${price:.2f}\n"
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
