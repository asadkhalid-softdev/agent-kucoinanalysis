import pandas as pd
import pandas_ta as ta
import numpy as np

class MACD:
    def __init__(self, fast=12, slow=26, signal=9):
        self.fast = fast
        self.slow = slow
        self.signal_length = signal
        self.name = f"MACD_{fast}_{slow}_{signal}"
    
    def calculate(self, df, short_period=12, long_period=26, signal_period=9):
        """Calculate MACD
        
        Args:
            df (pd.DataFrame): DataFrame with 'close' price column
            
        Returns:
            pd.DataFrame: MACD values including MACD line, signal line, and histogram
        """
        macd = ta.macd(df['close'], fast=self.fast, slow=self.slow, signal=self.signal_length)
        # Calculate short-term and long-term EMAs
        # short_ema = df['Close'].ewm(span=short_period, adjust=False).mean()
        # long_ema = df['Close'].ewm(span=long_period, adjust=False).mean()
        
        # # Calculate macd line
        # macd = short_ema - long_ema
        return macd
    
    def get_signal(self, df):
        """Generate trading signal based on MACD
        
        Args:
            df (pd.DataFrame): DataFrame with 'close' price column
            
        Returns:
            dict: Signal information
        """
        macd_df = self.calculate(df)
        
        # Get the column names from pandas-ta output
        macd_col = f"MACD_{self.fast}_{self.slow}_{self.signal_length}"
        signal_col = f"MACDs_{self.fast}_{self.slow}_{self.signal_length}"
        hist_col = f"MACDh_{self.fast}_{self.slow}_{self.signal_length}"
        
        current_macd = macd_df[macd_col].iloc[0]
        current_signal = macd_df[signal_col].iloc[0]
        current_hist = macd_df[hist_col].iloc[0]
        prev_hist = macd_df[hist_col].iloc[1] if len(macd_df) > 1 else 0

        # Determine signal
        if current_macd > current_signal:
            if current_hist > 0 and current_hist > prev_hist:
                signal = "strongly_bullish"
                strength = min(1.0, abs(current_hist) * 5)
            else:
                signal = "bullish"
                strength = min(1.0, abs(current_macd - current_signal) * 5)
        elif current_macd < current_signal:
            if current_hist < 0 and current_hist < prev_hist:
                signal = "strongly_bearish"
                strength = min(1.0, abs(current_hist) * 5)
            else:
                signal = "bearish"
                strength = min(1.0, abs(current_macd - current_signal) * 5)
        else:
            signal = "neutral"
            strength = 0.0
            
        return {
            "indicator": self.name,
            "value": {
                "macd": current_macd,
                "signal": current_signal,
                "histogram": current_hist
            },
            "signal": signal,
            "strength": strength
        }
