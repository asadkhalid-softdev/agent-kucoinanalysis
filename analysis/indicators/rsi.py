import pandas as pd
import pandas_ta as ta
import numpy as np

class RSI:
    def __init__(self, window=14):
        self.window = window
        self.name = f"RSI_{window}"
        self.overbought = 70
        self.oversold = 30

    def calculate(self, df):
        """Calculate Relative Strength Index
        
        Args:
            df (pd.DataFrame): DataFrame with 'close' price column
            
        Returns:
            pd.Series: RSI values
        """
        return ta.rsi(df['close'], length=self.window)

    def get_signal(self, df):
        """Generate trading signal based on RSI for trend following
        
        Args:
            df (pd.DataFrame): DataFrame with 'close' price column
            
        Returns:
            dict: Signal information
        """
        rsi = self.calculate(df)
        current_rsi = rsi.iloc[-1]
        
        # Get previous RSI values to determine trend
        prev_rsi = rsi.iloc[-2] if len(rsi) > 1 else current_rsi
        rsi_trend = "up" if current_rsi > prev_rsi else "down"
        
        # Get more history for trend confirmation
        if len(rsi) >= 5:
            rsi_5_periods_ago = rsi.iloc[-5]
            longer_rsi_trend = "up" if current_rsi > rsi_5_periods_ago else "down"
        else:
            longer_rsi_trend = rsi_trend
        
        # For trend following with RSI:
        # - Strong trends often show RSI staying in overbought/oversold zones
        # - We want to follow the trend, not anticipate reversals
        
        signal = "neutral"
        strength = 0.0
        
        # Bullish trend following signals
        if current_rsi > 50:
            # RSI above 50 indicates bullish momentum
            if current_rsi > self.overbought:
                # Strong uptrend with RSI in overbought zone
                if rsi_trend == "up":
                    # RSI still rising in overbought zone = very strong trend
                    signal = "bullish"
                    strength = min(1.0, 0.7 + (current_rsi - self.overbought) / (100 - self.overbought) * 0.3)
                else:
                    # RSI starting to fall from overbought = potential trend weakening
                    signal = "slightly_bullish"
                    strength = 0.3
            elif rsi_trend == "up" and longer_rsi_trend == "up":
                # RSI trending up above 50 = bullish momentum
                signal = "bullish"
                strength = min(1.0, (current_rsi - 50) / (self.overbought - 50) * 0.8)
            elif rsi_trend == "up":
                # RSI just started trending up above 50
                signal = "slightly_bullish"
                strength = min(0.5, (current_rsi - 50) / (self.overbought - 50) * 0.5)
        
        # Bearish trend following signals
        elif current_rsi < 50:
            # RSI below 50 indicates bearish momentum
            if current_rsi < self.oversold:
                # Strong downtrend with RSI in oversold zone
                if rsi_trend == "down":
                    # RSI still falling in oversold zone = very strong downtrend
                    signal = "bearish"
                    strength = min(1.0, 0.7 + (self.oversold - current_rsi) / self.oversold * 0.3)
                else:
                    # RSI starting to rise from oversold = potential trend weakening
                    signal = "slightly_bearish"
                    strength = 0.3
            elif rsi_trend == "down" and longer_rsi_trend == "down":
                # RSI trending down below 50 = bearish momentum
                signal = "bearish"
                strength = min(1.0, (50 - current_rsi) / (50 - self.oversold) * 0.8)
            elif rsi_trend == "down":
                # RSI just started trending down below 50
                signal = "slightly_bearish"
                strength = min(0.5, (50 - current_rsi) / (50 - self.oversold) * 0.5)
        
        # Detect RSI crossing the centerline (50)
        if len(rsi) > 1:
            if prev_rsi < 50 and current_rsi > 50:
                # Bullish crossover of centerline
                signal = "bullish"
                strength = 0.7
            elif prev_rsi > 50 and current_rsi < 50:
                # Bearish crossover of centerline
                signal = "bearish"
                strength = 0.7
        
        # Detect RSI divergence with price (advanced trend following signal)
        if len(df) > 5 and len(rsi) > 5:
            price_trend = "up" if df['close'].iloc[-1] > df['close'].iloc[-5] else "down"
            
            # Bullish divergence in downtrend (potential trend reversal)
            if price_trend == "down" and longer_rsi_trend == "up" and current_rsi < 50:
                signal = "slightly_bullish"
                strength = 0.4
            
            # Bearish divergence in uptrend (potential trend reversal)
            elif price_trend == "up" and longer_rsi_trend == "down" and current_rsi > 50:
                signal = "slightly_bearish"
                strength = 0.4
                
        return {
            "indicator": self.name,
            "value": current_rsi,
            "rsi_trend": rsi_trend,
            "longer_rsi_trend": longer_rsi_trend,
            "signal": signal,
            "strength": strength
        }
