import pandas as pd
import numpy as np

class FibonacciRetracement:
    def __init__(self, period=100):
        self.period = period
        self.name = f"FIBONACCI_{period}"
        self.levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618, 2.0, 2.618, 4.236]
    
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
        
        # Find next level above for potential profit target
        next_level_above = None
        potential_profit_pct = None
        
        if above_level:
            next_level_above = above_level
            potential_profit_pct = (next_level_above[1] - current_price) / current_price * 100
        
        # Find next significant level above (if current level is not the highest)
        if above_level and sorted_levels[-1] != above_level:
            # Find the index of the above_level in sorted_levels
            for i, (level, price) in enumerate(sorted_levels):
                if level == above_level[0] and price == above_level[1]:
                    # If there's a next level, use it as the target
                    if i + 1 < len(sorted_levels):
                        next_level_above = sorted_levels[i + 1]
                        potential_profit_pct = (next_level_above[1] - current_price) / current_price * 100
                    break
        
        # Find next level below for potential stop loss
        next_level_below = None
        potential_loss_pct = None
        
        if below_level:
            next_level_below = below_level
            potential_loss_pct = (current_price - next_level_below[1]) / current_price * 100
        
        # Find next significant level below (if current level is not the lowest)
        if below_level and sorted_levels[0] != below_level:
            # Find the index of the below_level in sorted_levels
            for i, (level, price) in enumerate(sorted_levels):
                if level == below_level[0] and price == below_level[1]:
                    # If there's a previous level, use it as the stop loss
                    if i > 0:
                        next_level_below = sorted_levels[i - 1]
                        potential_loss_pct = (current_price - next_level_below[1]) / current_price * 100
                    break
        
        # Calculate risk/reward ratio
        risk_reward_ratio = None
        if potential_profit_pct is not None and potential_loss_pct is not None and potential_loss_pct > 0:
            risk_reward_ratio = potential_profit_pct / potential_loss_pct
        
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
                "closest_price": closest_level[1] if closest_level else None,
                "distance_pct": distance_pct,
                "next_level_above": next_level_above[0] if next_level_above else None,
                "next_level_price": next_level_above[1] if next_level_above else None,
                "potential_profit_pct": potential_profit_pct,
                "next_level_below": next_level_below[0] if next_level_below else None,
                "next_level_below_price": next_level_below[1] if next_level_below else None,
                "potential_loss_pct": potential_loss_pct,
                "risk_reward_ratio": risk_reward_ratio
            },
            "signal": signal,
            "strength": strength
        }


