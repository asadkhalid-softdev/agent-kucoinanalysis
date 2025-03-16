import pandas as pd
import pandas_ta as ta
import numpy as np

class RSI:
    def __init__(self, window=14):
        self.window = window
        self.name = f"RSI_{window}"
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
        """Generate trading signal based on RSI
        
        Args:
            df (pd.DataFrame): DataFrame with 'close' price column
            
        Returns:
            dict: Signal information
        """
        rsi = self.calculate(df)
        current_rsi = rsi.iloc[-1]
        
        if current_rsi > self.overbought:
            signal = "bearish"
            strength = min(1.0, (current_rsi - self.overbought) / (100 - self.overbought))
        elif current_rsi < self.oversold:
            signal = "bullish"
            strength = min(1.0, (self.oversold - current_rsi) / self.oversold)
        else:
            # Neutral zone
            mid_point = (self.overbought + self.oversold) / 2
            if current_rsi > mid_point:
                signal = "slightly_bearish"
                strength = (current_rsi - mid_point) / (self.overbought - mid_point) * 0.5
            elif current_rsi < mid_point:
                signal = "slightly_bullish"
                strength = (mid_point - current_rsi) / (mid_point - self.oversold) * 0.5
            else:
                signal = "neutral"
                strength = 0.0
                
        return {
            "indicator": self.name,
            "value": current_rsi,
            "signal": signal,
            "strength": strength
        }
