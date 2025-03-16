import pandas as pd
import numpy as np

class FibonacciRetracement:
    def __init__(self, period=100):
        self.period = period
        self.name = f"FIBONACCI_{period}"
        self.levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
    
    def calculate(self, df):
        """Calculate Fibonacci Retracement levels
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC price data
            
        Returns:
            dict: Fibonacci retracement levels
        """
        # Use the specified period to find swing high and low
        period_data = df.iloc[-self.period:]
        
        high = period_data['high'].max()
        low = period_data['low'].min()
        
        # Calculate retracement levels
        diff = high - low
        levels = {}
        
        for level in self.levels:
            if diff > 0:
                levels[level] = high - diff * level
            else:
                levels[level] = high
        
        return {
            "high": high,
            "low": low,
            "levels": levels
        }
    
    def get_signal(self, df):
        """Generate trading signal based on Fibonacci Retracement
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC price data
            
        Returns:
            dict: Signal information
        """
        fib_levels = self.calculate(df)
        current_price = df['close'].iloc[-1]
        
        # Find the closest levels
        levels = fib_levels["levels"]
        sorted_levels = sorted(levels.items(), key=lambda x: x[1])
        
        # Find the level just below and just above the current price
        below_level = None
        above_level = None
        
        for level, price in sorted_levels:
            if price <= current_price:
                below_level = (level, price)
            else:
                above_level = (level, price)
                break
        
        # Calculate how close price is to a support/resistance level
        closest_level = None
        distance_pct = None
        
        if below_level and above_level:
            below_distance = (current_price - below_level[1]) / current_price
            above_distance = (above_level[1] - current_price) / current_price
            
            if below_distance < above_distance:
                closest_level = below_level
                distance_pct = below_distance
            else:
                closest_level = above_level
                distance_pct = above_distance
        elif below_level:
            closest_level = below_level
            distance_pct = (current_price - below_level[1]) / current_price
        elif above_level:
            closest_level = above_level
            distance_pct = (above_level[1] - current_price) / current_price
        
        # Determine signal
        signal = "neutral"
        strength = 0.0
        
        if closest_level and distance_pct < 0.01:  # Within 1% of a level
            level_value = closest_level[0]
            
            # Price near support
            if closest_level == below_level:
                if level_value <= 0.382:  # Strong support levels
                    signal = "bullish"
                    strength = 0.5 + (0.5 * (1 - level_value))  # Higher strength for lower levels
                else:
                    signal = "slightly_bullish"
                    strength = 0.3
            
            # Price near resistance
            elif closest_level == above_level:
                if level_value >= 0.618:  # Strong resistance levels
                    signal = "bearish"
                    strength = 0.5 + (0.5 * level_value)  # Higher strength for higher levels
                else:
                    signal = "slightly_bearish"
                    strength = 0.3
        
        return {
            "indicator": self.name,
            "value": {
                "levels": fib_levels["levels"],
                "closest_level": closest_level[0] if closest_level else None,
                "distance_pct": distance_pct
            },
            "signal": signal,
            "strength": strength
        }
