import pandas as pd
import pandas_ta as ta
import numpy as np

class BollingerBands:
    def __init__(self, window=20, window_dev=2):
        self.window = window
        self.window_dev = window_dev
        self.name = f"BBANDS"
    
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
        """Generate Bollinger Bands values
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC price data
            
        Returns:
            dict: Signal information
        """
        bb_df = self.calculate(df)
        
        # Get column names from pandas-ta output
        upper_col = f"BBU_{self.window}_{self.window_dev}"
        middle_col = f"BBM_{self.window}_{self.window_dev}"
        lower_col = f"BBL_{self.window}_{self.window_dev}"
        
        # Get current values
        current_upper = bb_df[upper_col].iloc[-1]
        current_middle = bb_df[middle_col].iloc[-1]
        current_lower = bb_df[lower_col].iloc[-1]
        current_price = df['close'].iloc[-1]
        
        # Calculate bandwidth
        bandwidth = (current_upper - current_lower) / current_middle
        
        # Calculate percent B
        percent_b = (current_price - current_lower) / (current_upper - current_lower)
        
        # Determine trend direction
        trend_direction = "up" if current_middle > bb_df[middle_col].iloc[-2] else "down"
        
        return {
            "indicator": self.name,
            "value": {
                "upper": current_upper,
                "middle": current_middle,
                "lower": current_lower,
                "bandwidth": bandwidth,
                "percent_b": percent_b,
                "trend_direction": trend_direction
            }
        }
