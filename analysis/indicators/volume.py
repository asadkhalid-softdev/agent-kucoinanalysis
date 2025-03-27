import pandas as pd
import pandas_ta as ta
import numpy as np

class OnBalanceVolume:
    def __init__(self, obv_sma_period=20):
        self.name = "OBV"
        self.obv_sma_period = obv_sma_period
    
    def calculate(self, df):
        """Calculate On-Balance Volume
        
        Args:
            df (pd.DataFrame): DataFrame with OHLCV price data
            
        Returns:
            pd.Series: OBV values
        """
        df['obv'] = ta.obv(df['close'], df['volume'])
        return df['obv']
    
    def get_signal(self, df):
        """Generate trading signal based on OBV for trend following
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC price data
            
        Returns:
            dict: Signal information
        """
        obv = self.calculate(df)
        
        # Get current and previous OBV values
        current_obv = obv.iloc[-1]
        prev_obv = obv.iloc[-2] if len(obv) > 1 else current_obv
        
        # Calculate OBV SMA
        obv_sma = obv.rolling(window=self.obv_sma_period).mean()
        current_obv_sma = obv_sma.iloc[-1]
        
        # Determine trends
        short_term_trend = "up" if current_obv > prev_obv else "down"
        
        # Get medium-term trend (5 periods)
        medium_term_trend = "up" if len(obv) >= 5 and current_obv > obv.iloc[-5] else "down"
        
        # Calculate OBV change percentage
        obv_change = (current_obv - prev_obv) / prev_obv if prev_obv != 0 else 0
        
        # Detect patterns
        confirmation = current_obv > current_obv_sma
        divergence = False
        pattern_type = None
        
        # Check for divergence
        if len(df) >= 5:
            price_trend = "up" if df['close'].iloc[-1] > df['close'].iloc[-5] else "down"
            obv_trend = "up" if current_obv > obv.iloc[-5] else "down"
            
            if price_trend != obv_trend:
                divergence = True
                pattern_type = "bullish" if obv_trend == "up" else "bearish"
        
        return {
            "indicator": self.name,
            "value": {
                "obv": current_obv,
                "obv_sma": current_obv_sma,
                "short_term_trend": short_term_trend,
                "medium_term_trend": medium_term_trend,
                "obv_change": obv_change,
                "pattern": {
                    "confirmation": confirmation,
                    "divergence": divergence,
                    "type": pattern_type
                }
            }
        }
