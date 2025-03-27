import pandas as pd
import pandas_ta as ta
import numpy as np
import logging

class MACD:
    def __init__(self, fast=12, slow=26, signal=9):
        self.fast = fast
        self.slow = slow
        self.signal_length = signal
        self.name = f"MACD"
        self.logger = logging.getLogger(__name__)

    def calculate(self, df):
        """Calculate MACD
        
        Args:
            df (pd.DataFrame): DataFrame with 'close' price column
            
        Returns:
            pd.DataFrame: MACD values including MACD line, signal line, and histogram
        """
        try:
            macd = ta.macd(df['close'], fast=self.fast, slow=self.slow, signal=self.signal_length)
            return macd
        except Exception as e:
            self.logger.error(f"Error calculating MACD: {str(e)}", exc_info=True)
            return pd.DataFrame()

    def get_signal(self, df):
        """Generate trading signal based on MACD for trend following
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC price data
            
        Returns:
            dict: Signal information
        """
        try:
            macd_df = self.calculate(df)
            macd_df = macd_df.sort_index(ascending=False)
            
            if macd_df.empty:
                self.logger.warning("Empty MACD calculation result")
                return {
                    "indicator": self.name,
                    "value": {
                        "macd": 0.0,
                        "signal": 0.0,
                        "histogram": 0.0,
                        "macd_trend": "neutral",
                        "hist_trend": "neutral",
                        "macd_position": "neutral",
                        "normalized_hist": 0.0
                    }
                }
            
            # Get column names from pandas-ta output
            macd_col = f"MACD_{self.fast}_{self.slow}_{self.signal_length}"
            signal_col = f"MACDs_{self.fast}_{self.slow}_{self.signal_length}"
            hist_col = f"MACDh_{self.fast}_{self.slow}_{self.signal_length}"
            
            current_macd = macd_df[macd_col].iloc[-1]
            current_signal = macd_df[signal_col].iloc[-1]
            current_hist = macd_df[hist_col].iloc[-1]
            
            # Get previous values for trend detection
            prev_macd = macd_df[macd_col].iloc[-2] if len(macd_df) > 1 else current_macd
            prev_signal = macd_df[signal_col].iloc[-2] if len(macd_df) > 1 else current_signal
            prev_hist = macd_df[hist_col].iloc[-2] if len(macd_df) > 1 else current_hist
            
            # Get histogram values for normalization
            hist_values = macd_df[hist_col].tail(20)  # Look at last 20 periods
            
            # Normalize histogram for strength calculation
            max_hist = max(abs(hist_values.max()), abs(hist_values.min())) if not hist_values.empty else 1
            normalized_hist = current_hist / max_hist if max_hist > 0 else 0
            
            # Determine MACD trend direction
            macd_trend = "up" if current_macd > prev_macd else "down"
            
            # Determine histogram trend direction
            hist_trend = "up" if current_hist > prev_hist else "down"
            
            # Determine if MACD is above or below signal line
            macd_position = "above" if current_macd > current_signal else "below"
            
            return {
                "indicator": self.name,
                "value": {
                    "macd": current_macd,
                    "signal": current_signal,
                    "histogram": current_hist,
                    "macd_trend": macd_trend,
                    "hist_trend": hist_trend,
                    "macd_position": macd_position,
                    "normalized_hist": normalized_hist
                }
            }
        except Exception as e:
            self.logger.error(f"Error generating MACD signal: {str(e)}", exc_info=True)
            return {
                "indicator": self.name,
                "value": {
                    "macd": 0.0,
                    "signal": 0.0,
                    "histogram": 0.0,
                    "macd_trend": "neutral",
                    "hist_trend": "neutral",
                    "macd_position": "neutral",
                    "normalized_hist": 0.0
                }
            }
