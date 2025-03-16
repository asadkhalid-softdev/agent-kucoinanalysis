import pandas as pd
import pandas_ta as ta
import numpy as np

class OnBalanceVolume:
    def __init__(self):
        self.name = "OBV"
    
    def calculate(self, df):
        """Calculate On-Balance Volume
        
        Args:
            df (pd.DataFrame): DataFrame with OHLCV price data
            
        Returns:
            pd.Series: OBV values
        """
        return ta.obv(df['close'], df['volume'])
    
    def get_signal(self, df):
        """Generate trading signal based on OBV
        
        Args:
            df (pd.DataFrame): DataFrame with OHLCV price data
            
        Returns:
            dict: Signal information
        """
        obv = self.calculate(df)
        
        # Calculate a 20-period SMA of OBV for trend detection
        obv_sma = ta.sma(obv, length=20)
        
        current_obv = obv.iloc[-1]
        current_obv_sma = obv_sma.iloc[-1]
        
        # Calculate OBV momentum (rate of change)
        obv_change = (current_obv - obv.iloc[-6]) / abs(obv.iloc[-6]) if obv.iloc[-6] != 0 else 0
        
        # Check if price and OBV are diverging
        price_change = (df['close'].iloc[-1] - df['close'].iloc[-6]) / df['close'].iloc[-6]
        
        divergence = False
        divergence_type = None
        
        if price_change > 0.01 and obv_change < -0.01:  # 1% threshold
            divergence = True
            divergence_type = "bearish"  # Price up, OBV down
        elif price_change < -0.01 and obv_change > 0.01:
            divergence = True
            divergence_type = "bullish"  # Price down, OBV up
        
        # Determine signal
        if divergence:
            signal = divergence_type
            strength = min(1.0, abs(obv_change - price_change) * 5)
        elif current_obv > current_obv_sma and obv_change > 0:
            signal = "bullish"
            strength = min(1.0, obv_change * 5)
        elif current_obv < current_obv_sma and obv_change < 0:
            signal = "bearish"
            strength = min(1.0, abs(obv_change) * 5)
        else:
            signal = "neutral"
            strength = 0.0
            
        return {
            "indicator": self.name,
            "value": current_obv,
            "obv_change": obv_change,
            "divergence": {
                "detected": divergence,
                "type": divergence_type
            },
            "signal": signal,
            "strength": strength
        }
