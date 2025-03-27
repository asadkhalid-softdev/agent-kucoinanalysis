import pandas as pd
import numpy as np
import logging
from typing import Dict, Any

class CandlestickPattern:
    """Analyzes candlestick patterns and generates trading signals"""
    
    def __init__(self):
        self.name = "CANDLESTICK"
        self.logger = logging.getLogger(__name__)
        
    def _calculate_body_size(self, row: pd.Series) -> float:
        """Calculate the size of the candlestick body"""
        return abs(row['close'] - row['open'])
    
    def _calculate_upper_shadow(self, row: pd.Series) -> float:
        """Calculate the size of the upper shadow"""
        return row['high'] - max(row['open'], row['close'])
    
    def _calculate_lower_shadow(self, row: pd.Series) -> float:
        """Calculate the size of the lower shadow"""
        return min(row['open'], row['close']) - row['low']
    
    def _is_bullish(self, row: pd.Series) -> bool:
        """Check if the candlestick is bullish"""
        return row['close'] > row['open']
    
    def _is_bearish(self, row: pd.Series) -> bool:
        """Check if the candlestick is bearish"""
        return row['close'] < row['open']
    
    def _is_doji(self, row: pd.Series) -> bool:
        """Check if the candlestick is a doji"""
        body_size = self._calculate_body_size(row)
        total_size = row['high'] - row['low']
        return body_size <= (total_size * 0.1)  # Body is less than 10% of total size
    
    def _is_hammer(self, row: pd.Series) -> bool:
        """Check if the candlestick is a hammer"""
        body_size = self._calculate_body_size(row)
        lower_shadow = self._calculate_lower_shadow(row)
        upper_shadow = self._calculate_upper_shadow(row)
        return lower_shadow > (body_size * 2) and upper_shadow < body_size
    
    def _is_shooting_star(self, row: pd.Series) -> bool:
        """Check if the candlestick is a shooting star"""
        body_size = self._calculate_body_size(row)
        lower_shadow = self._calculate_lower_shadow(row)
        upper_shadow = self._calculate_upper_shadow(row)
        return upper_shadow > (body_size * 2) and lower_shadow < body_size
    
    def _is_engulfing(self, current: pd.Series, previous: pd.Series) -> Dict[str, Any]:
        """Check if the candlestick is engulfing the previous one"""
        if self._is_bullish(current) and self._is_bearish(previous):
            if current['open'] < previous['close'] and current['close'] > previous['open']:
                return {"pattern": "bullish_engulfing", "strength": 0.8}
        elif self._is_bearish(current) and self._is_bullish(previous):
            if current['open'] > previous['close'] and current['close'] < previous['open']:
                return {"pattern": "bearish_engulfing", "strength": 0.8}
        return {"pattern": "none", "strength": 0.0}
    
    def _calculate_pattern_score(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate the overall pattern score"""
        if len(df) < 2:
            return {"pattern": "insufficient_data", "strength": 0.0}
            
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Check for doji
        if self._is_doji(current):
            return {"pattern": "doji", "strength": 0.3}
            
        # Check for hammer
        if self._is_hammer(current):
            return {"pattern": "hammer", "strength": 0.6}
            
        # Check for shooting star
        if self._is_shooting_star(current):
            return {"pattern": "shooting_star", "strength": 0.6}
            
        # Check for engulfing patterns
        engulfing = self._is_engulfing(current, previous)
        if engulfing["pattern"] != "none":
            return engulfing
            
        # Default to neutral if no pattern is detected
        return {"pattern": "neutral", "strength": 0.0}
    
    def get_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate candlestick pattern signal"""
        try:
            # Calculate pattern score
            pattern_data = self._calculate_pattern_score(df)
            
            # Determine signal based on pattern
            if pattern_data["pattern"] in ["bullish_engulfing", "hammer"]:
                signal = "buy"
            elif pattern_data["pattern"] in ["bearish_engulfing", "shooting_star"]:
                signal = "sell"
            elif pattern_data["pattern"] == "doji":
                signal = "neutral"
            else:
                signal = "neutral"
            
            return {
                "indicator": self.name,
                "value": {
                    "pattern": pattern_data["pattern"],
                    "strength": pattern_data["strength"],
                    "signal": signal
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating candlestick pattern signal: {str(e)}", exc_info=True)
            return {
                "indicator": self.name,
                "value": {
                    "pattern": "error",
                    "strength": 0.0,
                    "signal": "neutral"
                }
            } 