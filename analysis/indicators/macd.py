import pandas as pd
import pandas_ta as ta
import numpy as np

class MACD:
    def __init__(self, fast=12, slow=26, signal=9):
        self.fast = fast
        self.slow = slow
        self.signal_length = signal
        self.name = f"MACD"


    def calculate(self, df):
        """Calculate MACD
        
        Args:
            df (pd.DataFrame): DataFrame with 'close' price column
            
        Returns:
            pd.DataFrame: MACD values including MACD line, signal line, and histogram
        """
        macd = ta.macd(df['close'], fast=self.fast, slow=self.slow, signal=self.signal_length)
        return macd

    def get_signal(self, df):
        """Generate trading signal based on MACD for trend following
        
        Args:
            df (pd.DataFrame): DataFrame with 'close' price column
            
        Returns:
            dict: Signal information
        """
        macd_df = self.calculate(df)
        macd_df = macd_df.sort_index(ascending=False)
        # print(df)
        # print(macd_df)
        
        # Get the column names from pandas-ta output
        macd_col = f"MACD_{self.fast}_{self.slow}_{self.signal_length}"
        signal_col = f"MACDs_{self.fast}_{self.slow}_{self.signal_length}"
        hist_col = f"MACDh_{self.fast}_{self.slow}_{self.signal_length}"
        
        # Get current and previous values
        current_macd = macd_df[macd_col].iloc[-1]
        current_signal = macd_df[signal_col].iloc[-1]
        current_hist = macd_df[hist_col].iloc[-1]
        
        # Get previous values for trend determination
        prev_macd = macd_df[macd_col].iloc[-2] if len(macd_df) > 1 else current_macd
        prev_signal = macd_df[signal_col].iloc[-2] if len(macd_df) > 1 else current_signal
        prev_hist = macd_df[hist_col].iloc[-2] if len(macd_df) > 1 else 0
        
        # Get more history for trend strength
        hist_values = macd_df[hist_col].dropna().iloc[-20:] if len(macd_df) >= 20 else macd_df[hist_col].dropna()
        max_hist = max(abs(hist_values.max()), abs(hist_values.min())) if not hist_values.empty else 1
        normalized_hist = current_hist / max_hist if max_hist > 0 else 0
        
        # Determine MACD trend direction
        macd_trend = "up" if current_macd > prev_macd else "down"
        
        # Determine histogram trend direction
        hist_trend = "up" if current_hist > prev_hist else "down"
        
        # Determine if MACD is above or below signal line
        macd_position = "above" if current_macd > current_signal else "below"
        
        # Determine signal based on trend following principles
        signal = "neutral"
        strength = 0.0
        
        # Bullish signals in trend following
        if macd_position == "above":  # MACD above signal line = bullish
            if current_macd > 0:  # Both MACD and signal positive = strong uptrend
                signal = "bullish"
                # Strength increases with histogram size and positive direction
                strength = min(1.0, 0.5 + abs(normalized_hist) * 0.5) if hist_trend == "up" else min(0.8, 0.4 + abs(normalized_hist) * 0.4)
            else:  # MACD negative but above signal = potential trend change
                signal = "slightly_bullish"
                strength = min(0.5, abs(normalized_hist) * 0.5) if hist_trend == "up" else 0.2
        
        # Bearish signals in trend following
        elif macd_position == "below":  # MACD below signal line = bearish
            if current_macd < 0:  # Both MACD and signal negative = strong downtrend
                signal = "bearish"
                # Strength increases with histogram size and negative direction
                strength = min(1.0, 0.5 + abs(normalized_hist) * 0.5) if hist_trend == "down" else min(0.8, 0.4 + abs(normalized_hist) * 0.4)
            else:  # MACD positive but below signal = potential trend change
                signal = "slightly_bearish"
                strength = min(0.5, abs(normalized_hist) * 0.5) if hist_trend == "down" else 0.2
        
        # Crossover detection (strongest signals in trend following)
        if len(macd_df) > 1:
            if prev_macd < prev_signal and current_macd > current_signal:  # Bullish crossover
                signal = "bullish"
                strength = 1.0
            elif prev_macd > prev_signal and current_macd < current_signal:  # Bearish crossover
                signal = "bearish"
                strength = 1.0
            
        return {
            "indicator": self.name,
            "value": {
                "macd": current_macd,
                "signal": current_signal,
                "histogram": current_hist,
                "macd_trend": macd_trend,
                "hist_trend": hist_trend,
                "macd_position": macd_position
            },
            "signal": signal,
            "strength": strength
        }
