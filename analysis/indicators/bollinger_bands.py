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
        """Generate trading signal based on Bollinger Bands
        
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

        current_price = df['close'].iloc[-1]
        upper_band = bbands[upper_col].iloc[-1]
        middle_band = bbands[middle_col].iloc[-1]
        lower_band = bbands[lower_col].iloc[-1]

        # Calculate bandwidth and %B
        bandwidth = (upper_band - lower_band) / middle_band
        percent_b = (current_price - lower_band) / (upper_band - lower_band) if upper_band != lower_band else 0.5
        
        # Determine signal
        if current_price > upper_band:
            signal = "bearish"
            strength = min(1.0, (current_price / upper_band - 1) * 5)
        elif current_price < lower_band:
            signal = "bullish"
            strength = min(1.0, (lower_band / current_price - 1) * 5)  # Corrected formula
        else:
            # Inside the bands
            if percent_b > 0.8:
                signal = "slightly_bearish"
                strength = (percent_b - 0.8) * 5
            elif percent_b < 0.2:
                signal = "slightly_bullish"
                strength = (0.2 - percent_b) * 5
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
                "percent_b": percent_b
            },
            "signal": signal,
            "strength": strength
        }
