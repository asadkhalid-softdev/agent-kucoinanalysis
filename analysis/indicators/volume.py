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
            df (pd.DataFrame): DataFrame with OHLCV price data
            
        Returns:
            dict: Signal information
        """
        obv = self.calculate(df)
        # print(df)
        # print(obv)

        # Calculate a SMA of OBV for trend identification
        obv_sma = ta.sma(obv, length=self.obv_sma_period)

        current_obv = obv.iloc[-1]
        current_obv_sma = obv_sma.iloc[-1]
        
        # Get previous values for trend determination
        prev_obv = obv.iloc[-2] if len(obv) > 1 else current_obv
        prev_obv_sma = obv_sma.iloc[-2] if len(obv_sma) > 1 else current_obv_sma
        
        # Calculate short-term and medium-term OBV trends
        if len(obv) >= 5:
            obv_5_periods_ago = obv.iloc[-5]
            short_term_trend = "up" if current_obv > obv_5_periods_ago else "down"
        else:
            short_term_trend = "up" if current_obv > prev_obv else "down"
            
        if len(obv) >= 20:
            obv_20_periods_ago = obv.iloc[-20]
            medium_term_trend = "up" if current_obv > obv_20_periods_ago else "down"
        else:
            medium_term_trend = short_term_trend
        
        # Calculate OBV momentum (rate of change)
        obv_change = (current_obv - obv.iloc[-6]) / abs(obv.iloc[-6]) if len(obv) >= 6 and obv.iloc[-6] != 0 else 0

        # Check if price and OBV are confirming or diverging
        price_change = (df['close'].iloc[-1] - df['close'].iloc[-6]) / df['close'].iloc[-6] if len(df) >= 6 else 0
        
        # Confirmation/divergence analysis
        confirmation = False
        divergence = False
        pattern_type = None
        
        if price_change > 0.01 and obv_change > 0.01:  # Both price and OBV rising
            confirmation = True
            pattern_type = "bullish"  # Confirming uptrend
        elif price_change < -0.01 and obv_change < -0.01:  # Both price and OBV falling
            confirmation = True
            pattern_type = "bearish"  # Confirming downtrend
        elif price_change > 0.01 and obv_change < -0.01:  # Price up, OBV down
            divergence = True
            pattern_type = "bearish"  # Potential trend weakness
        elif price_change < -0.01 and obv_change > 0.01:  # Price down, OBV up
            divergence = True
            pattern_type = "bullish"  # Potential trend weakness

        # Determine signal based on trend following principles
        signal = "neutral"
        strength = 0.0
        
        # OBV above its SMA and rising = bullish trend
        if current_obv > current_obv_sma:
            if short_term_trend == "up" and medium_term_trend == "up":
                # Strong uptrend confirmation
                signal = "bullish"
                # Strength increases with the deviation from SMA and recent momentum
                strength = min(1.0, 0.5 + (current_obv / current_obv_sma - 1) * 3 + obv_change * 2)
            elif short_term_trend == "up":
                # Potential start of uptrend
                signal = "slightly_bullish"
                strength = 0.4
            elif confirmation and pattern_type == "bullish":
                # Price and OBV both rising, confirming uptrend
                signal = "bullish"
                strength = 0.7
        
        # OBV below its SMA and falling = bearish trend
        elif current_obv < current_obv_sma:
            if short_term_trend == "down" and medium_term_trend == "down":
                # Strong downtrend confirmation
                signal = "bearish"
                # Strength increases with the deviation from SMA and recent momentum
                strength = min(1.0, 0.5 + (1 - current_obv / current_obv_sma) * 3 + abs(obv_change) * 2)
            elif short_term_trend == "down":
                # Potential start of downtrend
                signal = "slightly_bearish"
                strength = 0.4
            elif confirmation and pattern_type == "bearish":
                # Price and OBV both falling, confirming downtrend
                signal = "bearish"
                strength = 0.7
        
        # OBV crossing above its SMA = potential trend change to upside
        if prev_obv < prev_obv_sma and current_obv > current_obv_sma:
            signal = "bullish"
            strength = 0.8
        
        # OBV crossing below its SMA = potential trend change to downside
        elif prev_obv > prev_obv_sma and current_obv < current_obv_sma:
            signal = "bearish"
            strength = 0.8
        
        # Divergence can sometimes indicate early trend changes
        if divergence:
            if pattern_type == "bullish" and current_obv < current_obv_sma:
                # Bullish divergence during downtrend - potential reversal
                signal = "slightly_bullish"
                strength = 0.3
            elif pattern_type == "bearish" and current_obv > current_obv_sma:
                # Bearish divergence during uptrend - potential reversal
                signal = "slightly_bearish"
                strength = 0.3
            
        return {
            "indicator": self.name,
            "value": current_obv,
            "obv_sma": current_obv_sma,
            "short_term_trend": short_term_trend,
            "medium_term_trend": medium_term_trend,
            "obv_change": obv_change,
            "pattern": {
                "confirmation": confirmation,
                "divergence": divergence,
                "type": pattern_type
            },
            "signal": signal,
            "strength": strength
        }
