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

        # Calculate percent deviation from SMA
        deviation = (current_price / current_sma - 1)
        abs_deviation = abs(deviation)

        # For mean reversion: 
        # - When price is above SMA, expect it to fall back (bearish)
        # - When price is below SMA, expect it to rise back (bullish)
        if current_price > current_sma:
            # Price above SMA - expect reversion down
            signal = "bearish"
            # Stronger signal when price is further above SMA
            strength = min(1.0, abs_deviation * 10)
        elif current_price < current_sma:
            # Price below SMA - expect reversion up
            signal = "bullish"
            # Stronger signal when price is further below SMA
            strength = min(1.0, abs_deviation * 10)
        else:
            signal = "neutral"
            strength = 0.0

        # Add a filter for extreme deviations
        if abs_deviation > 0.15:  # 15% deviation might be too extreme for reliable mean reversion
            strength = strength * 0.5  # Reduce confidence in very extreme cases

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
