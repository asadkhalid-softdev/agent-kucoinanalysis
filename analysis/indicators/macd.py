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

        # Calculate histogram extremes for normalization
        hist_values = macd_df[hist_col].iloc[:20]  # Look at recent history
        max_hist = max(abs(hist_values.max()), abs(hist_values.min()))
        normalized_hist = current_hist / max_hist if max_hist > 0 else 0

        # Determine signal based on mean reversion principles
        if current_hist > 0:
            # Positive histogram (MACD > Signal) might indicate overbought
            if normalized_hist > 0.7:  # Significantly positive histogram
                signal = "bearish"  # Expect reversion down
                strength = min(1.0, normalized_hist)
            elif current_hist < prev_hist:  # Histogram starting to decline
                signal = "slightly_bearish"  # Early reversion signal
                strength = min(1.0, normalized_hist * 0.7)
            else:
                signal = "neutral"
                strength = 0.0
        elif current_hist < 0:
            # Negative histogram (MACD < Signal) might indicate oversold
            if normalized_hist < -0.7:  # Significantly negative histogram
                signal = "bullish"  # Expect reversion up
                strength = min(1.0, abs(normalized_hist))
            elif current_hist > prev_hist:  # Histogram starting to increase
                signal = "slightly_bullish"  # Early reversion signal
                strength = min(1.0, abs(normalized_hist) * 0.7)
            else:
                signal = "neutral"
                strength = 0.0
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
