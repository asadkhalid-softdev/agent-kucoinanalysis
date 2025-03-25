import pandas as pd
import numpy as np

class FibonacciRetracement:
    def __init__(self, period=50):
        self.period = period
        self.name = "FIBONACCI"
        self.levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618, 2.0, 2.618, 4.236]
    
    def calculate(self, df):
        period_data = df.iloc[-self.period:]
        
        high = period_data['high'].max()
        high_idx = period_data['high'].idxmax()
        
        low = period_data['low'].min()
        low_idx = period_data['low'].idxmin()
        
        trend = "uptrend" if high_idx > low_idx else "downtrend"
        
        diff = high - low
        levels = {level: high - diff * level if diff > 0 else high for level in self.levels}
        
        recent_trend = "up" if len(df) >= 20 and df['close'].iloc[-1] > df['close'].iloc[-20] else "down"
        
        return {
            "high": high,
            "low": low,
            "levels": levels,
            "trend": trend,
            "recent_trend": recent_trend
        }
    
    def get_signal(self, df):
        fib_levels = self.calculate(df)
        # print(df)
        # print(fib_levels)

        current_price = df['close'].iloc[-1]
        previous_price = df['close'].iloc[-2] if len(df) > 1 else current_price
        
        price_direction = "up" if current_price > previous_price else "down"
        
        levels = fib_levels["levels"]
        sorted_levels = sorted(levels.items(), key=lambda x: x[1])
        
        below_level = next(((level, price) for level, price in sorted_levels if price <= current_price), None)
        above_level = next(((level, price) for level, price in sorted_levels if price > current_price), None)
        
        closest_level, distance_pct = self._find_closest_level(current_price, below_level, above_level)
        
        next_level_above = above_level
        potential_profit_pct = (next_level_above[1] - current_price) / current_price * 100 if next_level_above else None
        
        next_level_below = below_level
        potential_loss_pct = (current_price - next_level_below[1]) / current_price * 100 if next_level_below else None
        
        risk_reward_ratio = potential_profit_pct / potential_loss_pct if potential_profit_pct and potential_loss_pct and potential_loss_pct > 0 else None
        
        signal, strength = self._determine_signal(fib_levels, closest_level, distance_pct, price_direction, current_price)
        
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
    
    def _find_closest_level(self, current_price, below_level, above_level):
        if below_level and above_level:
            below_distance = (current_price - below_level[1]) / current_price
            above_distance = (above_level[1] - current_price) / current_price
            return (below_level, below_distance) if below_distance < above_distance else (above_level, above_distance)
        elif below_level:
            return below_level, (current_price - below_level[1]) / current_price
        elif above_level:
            return above_level, (above_level[1] - current_price) / current_price
        return None, None
    
    def _determine_signal(self, fib_levels, closest_level, distance_pct, price_direction, current_price):
        trend = fib_levels["trend"]
        recent_trend = fib_levels["recent_trend"]
        
        if trend == "uptrend" and recent_trend == "up":
            if closest_level and closest_level[0] <= 0.5 and distance_pct < 0.02:
                return "bullish", 0.5 + (0.5 * (1 - closest_level[0])) * (1 if price_direction == "up" else 0.5)
            elif closest_level and closest_level[0] > 0.5 and distance_pct < 0.02:
                return "slightly_bullish", 0.3 * (1 if price_direction == "up" else 0.5)
        
        elif trend == "downtrend" and recent_trend == "down":
            if closest_level and closest_level[0] >= 0.5 and distance_pct < 0.02:
                return "bearish", 0.5 + (0.5 * closest_level[0]) * (1 if price_direction == "down" else 0.5)
            elif closest_level and closest_level[0] < 0.5 and distance_pct < 0.02:
                return "slightly_bearish", 0.3 * (1 if price_direction == "down" else 0.5)
        
        elif trend == "uptrend" and current_price > fib_levels["high"]:
            return "bullish", 0.8
        
        elif trend == "downtrend" and current_price < fib_levels["low"]:
            return "bearish", 0.8
        
        elif trend == "downtrend" and recent_trend == "up" and current_price > sorted(fib_levels["levels"].values())[len(fib_levels["levels"])//2]:
            return "bullish", 0.4
        
        elif trend == "uptrend" and recent_trend == "down" and current_price < sorted(fib_levels["levels"].values())[len(fib_levels["levels"])//2]:
            return "bearish", 0.4
        
        return "neutral", 0.0
