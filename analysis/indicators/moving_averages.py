import pandas as pd
import pandas_ta as ta
import numpy as np

class SimpleMovingAverage:
    def __init__(self, window=50):
        self.window = window
        self.name = f"SMA_{window}"
    
    def calculate(self, df):
        """Calculate Simple Moving Average
        
        Args:
            df (pd.DataFrame): DataFrame with 'close' price column
            
        Returns:
            pd.Series: SMA values
        """
        sma = ta.sma(df['close'], length=self.window)
        return sma
    
    def get_signal(self, df):
        """Generate trading signal based on SMA
        
        Args:
            df (pd.DataFrame): DataFrame with 'close' price column
            
        Returns:
            dict: Signal information
        """
        sma = self.calculate(df)
        current_price = df['close'].iloc[-1]
        current_sma = sma.iloc[-1]
        
        if current_price > current_sma:
            signal = "bullish"
            strength = min(1.0, (current_price / current_sma - 1) * 10)
        elif current_price < current_sma:
            signal = "bearish"
            strength = min(1.0, (1 - current_price / current_sma) * 10)
        else:
            signal = "neutral"
            strength = 0.0
            
        return {
            "indicator": self.name,
            "value": current_sma,
            "signal": signal,
            "strength": strength
        }


class ExponentialMovingAverage:
    def __init__(self, window=20):
        self.window = window
        self.name = f"EMA_{window}"
    
    def calculate(self, df):
        """Calculate Exponential Moving Average
        
        Args:
            df (pd.DataFrame): DataFrame with 'close' price column
            
        Returns:
            pd.Series: EMA values
        """
        return ta.ema(df['close'], length=self.window)
    
    def get_signal(self, df):
        """Generate trading signal based on EMA
        
        Args:
            df (pd.DataFrame): DataFrame with 'close' price column
            
        Returns:
            dict: Signal information
        """
        ema = self.calculate(df)
        current_price = df['close'].iloc[-1]
        current_ema = ema.iloc[-1]
        
        if current_price > current_ema:
            signal = "bullish"
            strength = min(1.0, (current_price / current_ema - 1) * 10)
        elif current_price < current_ema:
            signal = "bearish"
            strength = min(1.0, (1 - current_price / current_ema) * 10)
        else:
            signal = "neutral"
            strength = 0.0
            
        return {
            "indicator": self.name,
            "value": current_ema,
            "signal": signal,
            "strength": strength
        }
