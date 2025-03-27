import pandas as pd
import numpy as np
import logging

class FibonacciRetracement:
    def __init__(self, period=50):
        self.period = period
        self.name = f"FIBONACCI"
        self.logger = logging.getLogger(__name__)
        
        # Fibonacci levels
        self.levels = {
            0.000: "0.000",
            0.236: "0.236",
            0.382: "0.382",
            0.500: "0.500",
            0.618: "0.618",
            0.786: "0.786",
            1.000: "1.000",
            1.618: "1.618",
            2.618: "2.618"
        }
    
    def calculate(self, df):
        """Calculate Fibonacci Retracement levels
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC price data
            
        Returns:
            dict: Fibonacci levels and their prices
        """
        try:
            # Get high and low for the period
            high = df['high'].rolling(window=self.period).max().iloc[-1]
            low = df['low'].rolling(window=self.period).min().iloc[-1]
            
            # Calculate price range
            price_range = high - low
            
            # Calculate Fibonacci levels
            levels = {}
            for level, name in self.levels.items():
                levels[name] = high - (price_range * level)
            
            return {
                "high": high,
                "low": low,
                "levels": levels
            }
        except Exception as e:
            self.logger.error(f"Error calculating Fibonacci Retracement: {str(e)}", exc_info=True)
            return {
                "high": 0.0,
                "low": 0.0,
                "levels": {}
            }
    
    def _find_closest_level(self, price, below_level, above_level):
        """Find the closest Fibonacci level to the current price
        
        Args:
            price (float): Current price
            below_level (tuple): (level, price) of the level below current price
            above_level (tuple): (level, price) of the level above current price
            
        Returns:
            tuple: (closest level, distance percentage)
        """
        try:
            if not below_level and not above_level:
                return None, 0.0
            
            if not below_level:
                return above_level[0], ((above_level[1] - price) / price) * 100
            
            if not above_level:
                return below_level[0], ((price - below_level[1]) / price) * 100
            
            # Calculate distance to both levels
            dist_below = ((price - below_level[1]) / price) * 100
            dist_above = ((above_level[1] - price) / price) * 100
            
            # Return the closer level
            if dist_below < dist_above:
                return below_level[0], dist_below
            else:
                return above_level[0], dist_above
        except Exception as e:
            self.logger.error(f"Error finding closest Fibonacci level: {str(e)}", exc_info=True)
            return None, 0.0
    
    def get_signal(self, df):
        """Generate Fibonacci Retracement levels
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC price data
            
        Returns:
            dict: Signal information
        """
        try:
            fib_levels = self.calculate(df)
            current_price = df['close'].iloc[-1]
            previous_price = df['close'].iloc[-2] if len(df) > 1 else current_price
            
            price_direction = "up" if current_price > previous_price else "down"
            
            levels = fib_levels["levels"]
            sorted_levels = sorted(levels.items(), key=lambda x: x[1])
            
            below_level = next(((level, price) for level, price in sorted_levels if price <= current_price), None)
            above_level = next(((level, price) for level, price in sorted_levels if price > current_price), None)
            
            closest_level, distance_pct = self._find_closest_level(current_price, below_level, above_level)
            
            return {
                "indicator": self.name,
                "value": {
                    "current_level": closest_level,
                    "distance_pct": distance_pct,
                    "price_direction": price_direction,
                    "levels": levels
                }
            }
        except Exception as e:
            self.logger.error(f"Error generating Fibonacci Retracement signal: {str(e)}", exc_info=True)
            return {
                "indicator": self.name,
                "value": {
                    "current_level": None,
                    "distance_pct": 0.0,
                    "price_direction": "neutral",
                    "potential_profit_pct": None,
                    "potential_loss_pct": None,
                    "risk_reward_ratio": None,
                    "levels": {}
                }
            }
