import pandas as pd
import pandas_ta as ta
import numpy as np

class BollingerBands:
    def __init__(self, window=20, window_dev=2):
        self.window = window
        self.window_dev = window_dev
        self.name = f"BBANDS_{window}_{window_dev}"
    
    def calculate(self, df):
        """Calculate Bollinger Bands
        
        Args:
            df (pd.DataFrame): DataFrame with 'close' price column
            
        Returns:
            pd.DataFrame: Bollinger Bands values including upper, middle, and lower bands
        """
        
        bbands = ta.bbands(df['close'], length=self.window, std=self.window_dev)
        
        return bbands
    
    def get_signal(self, df):
        """Generate trading signal based on Bollinger Bands for trend following
        
        Args:
            df (pd.DataFrame): DataFrame with 'close' price column
            
        Returns:
            dict: Signal information
        """
        bbands = self.calculate(df)
        
        # Get column names from pandas-ta output
        upper_col = f"BBU_{self.window}_{float(self.window_dev)}"
        middle_col = f"BBM_{self.window}_{float(self.window_dev)}"
        lower_col = f"BBL_{self.window}_{float(self.window_dev)}"

        # Get current and previous values
        current_price = df['close'].iloc[-1]
        previous_price = df['close'].iloc[-2] if len(df) > 1 else current_price
        
        upper_band = bbands[upper_col].iloc[-1]
        middle_band = bbands[middle_col].iloc[-1]
        lower_band = bbands[lower_col].iloc[-1]

        # Calculate bandwidth and %B
        bandwidth = (upper_band - lower_band) / middle_band
        percent_b = (current_price - lower_band) / (upper_band - lower_band) if upper_band != lower_band else 0.5
        
        # Get price direction
        price_direction = "up" if current_price > previous_price else "down"
        
        # Calculate slope of middle band (trend direction)
        if len(bbands) > 5:
            middle_slope = bbands[middle_col].iloc[-1] - bbands[middle_col].iloc[-5]
            trend_direction = "up" if middle_slope > 0 else "down"
        else:
            trend_direction = "neutral"
        
        # Determine signal for trend following
        if trend_direction == "up":
            if current_price > middle_band and bandwidth > 0.05:  # Expanding bands in uptrend
                signal = "bullish"
                strength = min(1.0, percent_b * bandwidth * 5)
            elif current_price < middle_band:
                signal = "neutral"
                strength = 0.0
            else:
                signal = "slightly_bullish"
                strength = min(0.5, percent_b * 0.5)
        elif trend_direction == "down":
            if current_price < middle_band and bandwidth > 0.05:  # Expanding bands in downtrend
                signal = "bearish"
                strength = min(1.0, (1 - percent_b) * bandwidth * 5)
            elif current_price > middle_band:
                signal = "neutral"
                strength = 0.0
            else:
                signal = "slightly_bearish"
                strength = min(0.5, (1 - percent_b) * 0.5)
        else:
            # No clear trend
            if bandwidth < 0.03:  # Very narrow bands suggest potential breakout
                if price_direction == "up":
                    signal = "slightly_bullish"
                    strength = 0.3
                else:
                    signal = "slightly_bearish"
                    strength = 0.3
            else:
                signal = "neutral"
                strength = 0.0
                
        return {
            "indicator": self.name,
            "value": {
                "upper": upper_band,
                "middle": middle_band,
                "lower": lower_band,
                "bandwidth": bandwidth,
                "percent_b": percent_b,
                "trend_direction": trend_direction
            },
            "signal": signal,
            "strength": strength
        }
