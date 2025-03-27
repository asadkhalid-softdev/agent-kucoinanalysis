import pandas as pd
import pandas_ta as ta
import numpy as np

class RSI:
    def __init__(self, window=14):
        self.window = window
        self.name = f"RSI"
        self.overbought = 70
        self.oversold = 30

    def calculate(self, df):
        """Calculate Relative Strength Index
        
        Args:
            df (pd.DataFrame): DataFrame with 'close' price column
            
        Returns:
            pd.Series: RSI values
        """
        return ta.rsi(df['close'], length=self.window)

    def get_signal(self, df):
        """Generate trading signal based on RSI for trend following
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC price data
            
        Returns:
            dict: Signal information
        """
        rsi = self.calculate(df)
        
        # Get current and previous RSI values
        current_rsi = rsi.iloc[-1]
        prev_rsi = rsi.iloc[-2] if len(rsi) > 1 else current_rsi
        
        # Determine RSI trend
        rsi_trend = "up" if current_rsi > prev_rsi else "down"
        
        # Get longer-term trend (5 periods)
        longer_rsi_trend = "up" if len(rsi) >= 5 and current_rsi > rsi.iloc[-5] else "down"
        
        return {
            "indicator": self.name,
            "value": {
                "rsi": current_rsi,
                "rsi_trend": rsi_trend,
                "longer_rsi_trend": longer_rsi_trend,
                "overbought": self.overbought,
                "oversold": self.oversold
            }
        }
