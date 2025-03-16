import pandas as pd
import pandas_ta as ta
import numpy as np

class StochasticOscillator:
    def __init__(self, k_period=14, d_period=3, smooth_k=3):
        self.k_period = k_period
        self.d_period = d_period
        self.smooth_k = smooth_k
        self.name = f"STOCH_{k_period}_{d_period}_{smooth_k}"
        self.overbought = 80
        self.oversold = 20
    
    def calculate(self, df):
        """Calculate Stochastic Oscillator
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC price data
            
        Returns:
            pd.DataFrame: Stochastic oscillator values including %K and %D
        """
        return ta.stoch(df['high'], df['low'], df['close'], 
                        k=self.k_period, d=self.d_period, smooth_k=self.smooth_k)
    
    def get_signal(self, df):
        """Generate trading signal based on Stochastic Oscillator
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC price data
            
        Returns:
            dict: Signal information
        """
        stoch = self.calculate(df)
        
        # Get column names from pandas-ta output
        k_col = f"STOCHk_{self.k_period}_{self.d_period}_{self.smooth_k}"
        d_col = f"STOCHd_{self.k_period}_{self.d_period}_{self.smooth_k}"
        
        current_k = stoch[k_col].iloc[0]
        current_d = stoch[d_col].iloc[0]
        prev_k = stoch[k_col].iloc[-2] if len(stoch) > 1 else current_k
        prev_d = stoch[d_col].iloc[-2] if len(stoch) > 1 else current_d
        
        # Determine signal
        if current_k > self.overbought and current_d > self.overbought:
            signal = "bearish"
            strength = min(1.0, (current_k - self.overbought) / (100 - self.overbought))
        elif current_k < self.oversold and current_d < self.oversold:
            signal = "bullish"
            strength = min(1.0, (self.oversold - current_k) / self.oversold)
        elif current_k > current_d and prev_k <= prev_d:
            # K line crosses above D line
            signal = "bullish"
            strength = min(1.0, abs(current_k - current_d) / 10)
        elif current_k < current_d and prev_k >= prev_d:
            # K line crosses below D line
            signal = "bearish"
            strength = min(1.0, abs(current_k - current_d) / 10)
        else:
            # No clear signal
            signal = "neutral"
            strength = 0.0
            
        return {
            "indicator": self.name,
            "value": {
                "k": current_k,
                "d": current_d
            },
            "signal": signal,
            "strength": strength
        }
