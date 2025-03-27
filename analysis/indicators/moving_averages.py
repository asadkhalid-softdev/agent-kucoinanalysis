import pandas as pd
import pandas_ta as ta
import numpy as np
import logging

class SimpleMovingAverage:
    def __init__(self, window=50):
        self.window = window
        self.name = f"SMA_{window}"
        self.logger = logging.getLogger(__name__)
    
    def calculate(self, df):
        """Calculate Simple Moving Average
        
        Args:
            df (pd.DataFrame): DataFrame with 'close' price column
            
        Returns:
            pd.Series: SMA values
        """
        try:
            sma = df['close'].rolling(window=self.window).mean()
            return sma
        except Exception as e:
            self.logger.error(f"Error calculating SMA: {str(e)}", exc_info=True)
            return pd.Series()
    
    def get_signal(self, df):
        """Generate trading signal based on SMA for trend following
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC price data
            
        Returns:
            dict: Signal information
        """
        try:
            sma = self.calculate(df)
            
            if sma.empty:
                self.logger.warning("Empty SMA calculation result")
                return {
                    "indicator": self.name,
                    "value": 0.0,
                    "sma_trend": "neutral",
                    "signal": "neutral",
                    "strength": 0.0
                }
            
            # Get current and previous values
            current_sma = sma.iloc[-1]
            current_price = df['close'].iloc[-1]
            
            # Calculate SMA trend
            sma_trend = "up" if current_sma > sma.iloc[-2] else "down"
            
            # Initialize signal and strength
            signal = "neutral"
            strength = 0.0
            
            # Crossover detection (if we have enough data)
            if len(df) > 2 and len(sma) > 1:
                prev_price = df['close'].iloc[-2]
                prev_sma = sma.iloc[-2]
                
                # Bullish crossover (price crosses above SMA)
                if prev_price < prev_sma and current_price > current_sma:
                    signal = "bullish"
                    strength = 1.0
                
                # Bearish crossover (price crosses below SMA)
                elif prev_price > prev_sma and current_price < current_sma:
                    signal = "bearish"
                    strength = 1.0
            
            return {
                "indicator": self.name,
                "value": current_sma,
                "sma_trend": sma_trend,
                "signal": signal,
                "strength": strength
            }
        except Exception as e:
            self.logger.error(f"Error generating SMA signal: {str(e)}", exc_info=True)
            return {
                "indicator": self.name,
                "value": 0.0,
                "sma_trend": "neutral",
                "signal": "neutral",
                "strength": 0.0
            }


class ExponentialMovingAverage:
    def __init__(self, window=20):
        self.window = window
        self.name = f"EMA_{window}"
    
    def calculate(self, df):
        """Calculate Exponential Moving Average
        
        Args:
            df (pd.DataFrame): DataFrame with 'close' price column
            
        Returns:
            pd.Series: EMA values
        """
        return ta.ema(df['close'], length=self.window)
    
    def get_signal(self, df):
        """Generate trading signal based on EMA for trend following
        
        Args:
            df (pd.DataFrame): DataFrame with 'close' price column
            
        Returns:
            dict: Signal information
        """
        ema = self.calculate(df)
        current_price = df['close'].iloc[-1]
        current_ema = ema.iloc[-1]
        
        # Get previous values to determine trend direction
        if len(ema) > 5:
            ema_trend = "up" if ema.iloc[-1] > ema.iloc[-5] else "down"
        else:
            ema_trend = "neutral"
        
        # Calculate percent deviation from EMA
        deviation = (current_price / current_ema - 1)
        abs_deviation = abs(deviation)
        
        # For trend following with EMA:
        # - When price is above EMA, trend is up (bullish)
        # - When price is below EMA, trend is down (bearish)
        if current_price > current_ema:
            signal = "bullish"
            # Stronger signal when EMA is also trending up
            strength = min(1.0, abs_deviation * 5) * (1.2 if ema_trend == "up" else 0.8)
        elif current_price < current_ema:
            signal = "bearish"
            # Stronger signal when EMA is also trending down
            strength = min(1.0, abs_deviation * 5) * (1.2 if ema_trend == "down" else 0.8)
        else:
            signal = "neutral"
            strength = 0.0
        
        # Crossover detection (if we have enough data)
        if len(df) > 2 and len(ema) > 1:
            prev_price = df['close'].iloc[-2]
            prev_ema = ema.iloc[-2]
            
            # Bullish crossover (price crosses above EMA)
            if prev_price < prev_ema and current_price > current_ema:
                signal = "bullish"
                strength = 1.0
            
            # Bearish crossover (price crosses below EMA)
            elif prev_price > prev_ema and current_price < current_ema:
                signal = "bearish"
                strength = 1.0
        
        return {
            "indicator": self.name,
            "value": current_ema,
            "ema_trend": ema_trend,
            "signal": signal,
            "strength": strength
        }
