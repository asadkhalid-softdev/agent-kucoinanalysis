import pandas as pd
import pandas_ta as ta
import numpy as np
import logging

class StochasticOscillator:
    def __init__(self, k_period=14, d_period=3, smooth_k=3):
        self.k_period = k_period
        self.d_period = d_period
        self.smooth_k = smooth_k
        self.name = f"STOCH"
        self.logger = logging.getLogger(__name__)
        self.overbought = 80
        self.oversold = 20

    def calculate(self, df):
        """Calculate Stochastic Oscillator
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC price data
            
        Returns:
            pd.DataFrame: Stochastic values including %K and %D lines
        """
        try:
            stoch = ta.stoch(
                df['high'],
                df['low'],
                df['close'],
                k=self.k_period,
                d=self.d_period,
                smooth_k=self.smooth_k
            )
            return stoch
        except Exception as e:
            self.logger.error(f"Error calculating Stochastic Oscillator: {str(e)}", exc_info=True)
            return pd.DataFrame()

    def get_signal(self, df):
        """Generate trading signal based on Stochastic Oscillator for trend following
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC price data
            
        Returns:
            dict: Signal information
        """
        try:
            stoch_df = self.calculate(df)
            stoch_df = stoch_df.sort_index(ascending=False)
            
            if stoch_df.empty:
                self.logger.warning("Empty Stochastic Oscillator calculation result")
                return {
                    "indicator": self.name,
                    "value": {
                        "k": 0.0,
                        "d": 0.0,
                        "k_trend": "neutral",
                        "d_trend": "neutral",
                        "price_trend": "neutral",
                        "overbought": 70,
                        "oversold": 30
                    }
                }
            
            # Get column names from pandas-ta output
            k_col = f"STOCHk_{self.k_period}_{self.d_period}_{self.smooth_k}"
            d_col = f"STOCHd_{self.k_period}_{self.d_period}_{self.smooth_k}"
            
            current_k = stoch_df[k_col].iloc[-1]
            current_d = stoch_df[d_col].iloc[-1]
            
            # Get previous values for trend detection
            prev_k = stoch_df[k_col].iloc[-2] if len(stoch_df) > 1 else current_k
            prev_d = stoch_df[d_col].iloc[-2] if len(stoch_df) > 1 else current_d
            
            # Determine trend directions
            k_trend = "up" if current_k > prev_k else "down"
            d_trend = "up" if current_d > prev_d else "down"
            
            # Determine price trend
            price_trend = "up" if df['close'].iloc[-1] > df['close'].iloc[-2] else "down"
            
            return {
                "indicator": self.name,
                "value": {
                    "k": current_k,
                    "d": current_d,
                    "k_trend": k_trend,
                    "d_trend": d_trend,
                    "price_trend": price_trend,
                    "overbought": 70,
                    "oversold": 30
                }
            }
        except Exception as e:
            self.logger.error(f"Error generating Stochastic Oscillator signal: {str(e)}", exc_info=True)
            return {
                "indicator": self.name,
                "value": {
                    "k": 0.0,
                    "d": 0.0,
                    "k_trend": "neutral",
                    "d_trend": "neutral",
                    "price_trend": "neutral",
                    "overbought": 70,
                    "oversold": 30
                }
            }
