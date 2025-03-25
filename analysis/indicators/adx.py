import pandas as pd
import pandas_ta as ta
import numpy as np

class AverageDirectionalIndex:
    def __init__(self, length=14, adx_threshold=25):
        self.length = length
        self.adx_threshold = adx_threshold
        self.name = f"ADX"
    
    def calculate(self, df):
        """Calculate Average Directional Index
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC price data
            
        Returns:
            pd.DataFrame: ADX values including ADX, +DI, and -DI
        """
        return ta.adx(df['high'], df['low'], df['close'], length=self.length)
    
    def get_signal(self, df):
        """Generate trading signal based on ADX for trend following
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC price data
            
        Returns:
            dict: Signal information
        """
        adx_df = self.calculate(df)
        # print(df)
        # print(adx_df)
        
        # Get column names from pandas-ta output
        adx_col = f"ADX_{self.length}"
        pdi_col = f"DMP_{self.length}"
        ndi_col = f"DMN_{self.length}"
        
        current_adx = adx_df[adx_col].iloc[-1]
        current_pdi = adx_df[pdi_col].iloc[-1]
        current_ndi = adx_df[ndi_col].iloc[-1]

        # Determine trend strength
        if current_adx < 20:
            trend_strength = "weak"
        elif current_adx < 40:
            trend_strength = "moderate"
        else:
            trend_strength = "strong"

        # Determine signal for trend following
        if current_adx > self.adx_threshold:
            if current_pdi > current_ndi:
                # Strong uptrend - follow the trend up
                signal = "bullish"
                # Strength increases with both ADX and the difference between +DI and -DI
                strength = min(1.0, (current_adx / 100) * (current_pdi - current_ndi) / 20)
            elif current_ndi > current_pdi:
                # Strong downtrend - follow the trend down
                signal = "bearish"
                strength = min(1.0, (current_adx / 100) * (current_ndi - current_pdi) / 20)
            else:
                signal = "neutral"
                strength = 0.0
        else:
            # ADX below threshold indicates weak trend - not ideal for trend following
            signal = "neutral"
            strength = 0.0
            
        return {
            "indicator": self.name,
            "value": {
                "adx": current_adx,
                "plus_di": current_pdi,
                "minus_di": current_ndi,
                "trend_strength": trend_strength
            },
            "signal": signal,
            "strength": strength
        }
