import pandas as pd
import numpy as np

class FibonacciRetracement:
    def __init__(self, period=100):
        self.period = period
        self.name = f"FIBONACCI"
        self.levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618, 2.0, 2.618, 4.236]
    
    def calculate(self, df):
        """Calculate Fibonacci Retracement levels
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC price data
            
        Returns:
            dict: Fibonacci retracement levels and trend direction
        """
        # Use the specified period to find swing high and low
        period_data = df.iloc[-self.period:]
        
        high = period_data['high'].max()
        high_idx = period_data['high'].idxmax()
        
        low = period_data['low'].min()
        low_idx = period_data['low'].idxmin()
        
        # Determine if we're in an uptrend or downtrend based on sequence of high and low
        trend = "uptrend" if high_idx > low_idx else "downtrend"
        
        # Calculate retracement levels
        diff = high - low
        levels = {}
        
        for level in self.levels:
            if diff > 0:
                levels[level] = high - diff * level
            else:
                levels[level] = high
        
        # Get recent price movement
        if len(df) >= 20:
            recent_trend = "up" if df['close'].iloc[-1] > df['close'].iloc[-20] else "down"
        else:
            recent_trend = "neutral"
        
        return {
            "high": high,
            "low": low,
            "levels": levels,
            "trend": trend,
            "recent_trend": recent_trend
        }
    
    def get_signal(self, df):
        """Generate trading signal based on Fibonacci Retracement for trend following
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC price data
            
        Returns:
            dict: Signal information
        """
        fib_levels = self.calculate(df)
        current_price = df['close'].iloc[-1]
        previous_price = df['close'].iloc[-2] if len(df) > 1 else current_price
        
        # Determine short-term price movement
        price_direction = "up" if current_price > previous_price else "down"
        
        # Find the closest levels
        levels = fib_levels["levels"]
        sorted_levels = sorted(levels.items(), key=lambda x: x[1])
        
        # Find the level just below and just above the current price
        below_level = None
        above_level = None
        
        for level, price in sorted_levels:
            if price <= current_price:
                below_level = (level, price)
            elif price > current_price:
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
        next_level_above = above_level
        potential_profit_pct = (next_level_above[1] - current_price) / current_price * 100 if next_level_above else None
        
        # Find next level below for potential stop loss
        next_level_below = below_level
        potential_loss_pct = (current_price - next_level_below[1]) / current_price * 100 if next_level_below else None
        
        # Calculate risk/reward ratio
        risk_reward_ratio = None
        if potential_profit_pct is not None and potential_loss_pct is not None and potential_loss_pct > 0:
            risk_reward_ratio = potential_profit_pct / potential_loss_pct
        
        # Determine signal for trend following
        signal = "neutral"
        strength = 0.0
        
        # Trend following logic
        trend = fib_levels["trend"]
        recent_trend = fib_levels["recent_trend"]
        
        if trend == "uptrend" and recent_trend == "up":
            # In an uptrend, look for bounces off support levels as buying opportunities
            if closest_level == below_level and distance_pct < 0.02:  # Within 2% of a support level
                level_value = closest_level[0]
                if level_value <= 0.5:  # Key retracement levels in uptrend
                    signal = "bullish"
                    # Higher strength for stronger support levels and when price is moving up
                    strength = 0.5 + (0.5 * (1 - level_value)) * (1 if price_direction == "up" else 0.5)
                else:
                    signal = "slightly_bullish"
                    strength = 0.3 * (1 if price_direction == "up" else 0.5)
        
        elif trend == "downtrend" and recent_trend == "down":
            # In a downtrend, look for rejections at resistance levels as selling opportunities
            if closest_level == above_level and distance_pct < 0.02:  # Within 2% of a resistance level
                level_value = closest_level[0]
                if level_value >= 0.5:  # Key retracement levels in downtrend
                    signal = "bearish"
                    # Higher strength for stronger resistance levels and when price is moving down
                    strength = 0.5 + (0.5 * level_value) * (1 if price_direction == "down" else 0.5)
                else:
                    signal = "slightly_bearish"
                    strength = 0.3 * (1 if price_direction == "down" else 0.5)
        
        # Breakout scenarios - following the trend on breakouts
        elif trend == "uptrend" and current_price > fib_levels["high"]:
            # Breakout above the high in an uptrend
            signal = "bullish"
            strength = 0.8
        
        elif trend == "downtrend" and current_price < fib_levels["low"]:
            # Breakout below the low in a downtrend
            signal = "bearish"
            strength = 0.8
        
        # Trend reversal confirmation
        elif trend == "downtrend" and recent_trend == "up" and current_price > sorted_levels[len(sorted_levels)//2][1]:
            # Price moved above the middle of the range in a previous downtrend
            signal = "bullish"
            strength = 0.4
        
        elif trend == "uptrend" and recent_trend == "down" and current_price < sorted_levels[len(sorted_levels)//2][1]:
            # Price moved below the middle of the range in a previous uptrend
            signal = "bearish"
            strength = 0.4
        
        return {
            "indicator": self.name,
            "value": {
                "levels": fib_levels["levels"],
                "trend": fib_levels["trend"],
                "recent_trend": fib_levels["recent_trend"],
                "closest_level": closest_level[0] if closest_level else None,
                "closest_price": closest_level[1] if closest_level else None,
                "distance_pct": distance_pct,
                "next_level_above": next_level_above[0] if next_level_above else None,
                "next_level_above_price": next_level_above[1] if next_level_above else None,
                "potential_profit_pct": potential_profit_pct,
                "next_level_below": next_level_below[0] if next_level_below else None,
                "next_level_below_price": next_level_below[1] if next_level_below else None,
                "potential_loss_pct": potential_loss_pct,
                "risk_reward_ratio": risk_reward_ratio
            },
            "signal": signal,
            "strength": strength
        }
