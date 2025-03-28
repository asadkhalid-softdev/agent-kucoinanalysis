import pandas as pd
import numpy as np
import logging
from typing import Dict, Any

class CandlestickPattern:
    """Analyzes candlestick patterns and generates trading signals"""

    def __init__(self):
        self.name = "CANDLESTICK"
        self.logger = logging.getLogger(__name__)
        # Define thresholds (can be tuned)
        self.body_doji_threshold = 0.10  # Max body size relative to total range for Doji
        self.shadow_hammer_threshold = 2.0   # Min shadow size relative to body for Hammer/SS etc.
        self.shadow_limit_threshold = 1.0    # Max opposing shadow size relative to body for Hammer/SS etc.
        self.marubozu_shadow_threshold = 0.05 # Max shadow size relative to total range for Marubozu
        self.spinning_top_body_threshold = 0.3 # Max body size relative to total range for Spinning Top
        self.piercing_midpoint_threshold = 0.5 # Min close penetration into previous body for Piercing/Dark Cloud
        self.simple_candle_strength = 0.1 # Strength assigned to simple bullish/bearish candles

    # --- Basic Calculations ---
    def _calculate_body_size(self, row: pd.Series) -> float:
        """Calculate the size of the candlestick body"""
        return abs(row['close'] - row['open'])

    def _calculate_upper_shadow(self, row: pd.Series) -> float:
        """Calculate the size of the upper shadow"""
        return row['high'] - max(row['open'], row['close'])

    def _calculate_lower_shadow(self, row: pd.Series) -> float:
        """Calculate the size of the lower shadow"""
        return min(row['open'], row['close']) - row['low']

    def _calculate_total_range(self, row: pd.Series) -> float:
        """Calculate the total range (high - low)"""
        return row['high'] - row['low']

    def _is_bullish(self, row: pd.Series) -> bool:
        """Check if the candlestick is bullish"""
        return row['close'] > row['open']

    def _is_bearish(self, row: pd.Series) -> bool:
        """Check if the candlestick is bearish"""
        return row['close'] < row['open']

    # --- Single Candlestick Pattern Checks ---
    def _is_doji(self, row: pd.Series) -> bool:
        """Check if the candlestick is a doji"""
        body_size = self._calculate_body_size(row)
        total_range = self._calculate_total_range(row)
        if total_range == 0:
            return True # Consider it a doji if open=high=low=close
        # Check against threshold, ensuring body_size is not NaN
        return not pd.isna(body_size) and body_size <= (total_range * self.body_doji_threshold)

    def _is_hammer_shape(self, row: pd.Series) -> bool:
        """Check if the candlestick has a Hammer/Hanging Man shape"""
        body_size = self._calculate_body_size(row)
        lower_shadow = self._calculate_lower_shadow(row)
        upper_shadow = self._calculate_upper_shadow(row)
        # Must have a body, long lower shadow, short upper shadow
        # Ensure values are not NaN before comparison
        return (not pd.isna(body_size) and body_size > 0 and
                not pd.isna(lower_shadow) and lower_shadow >= (body_size * self.shadow_hammer_threshold) and
                not pd.isna(upper_shadow) and upper_shadow <= (body_size * self.shadow_limit_threshold))

    def _is_inverted_hammer_shape(self, row: pd.Series) -> bool:
        """Check if the candlestick has an Inverted Hammer/Shooting Star shape"""
        body_size = self._calculate_body_size(row)
        lower_shadow = self._calculate_lower_shadow(row)
        upper_shadow = self._calculate_upper_shadow(row)
        # Must have a body, long upper shadow, short lower shadow
        return (not pd.isna(body_size) and body_size > 0 and
                not pd.isna(upper_shadow) and upper_shadow >= (body_size * self.shadow_hammer_threshold) and
                not pd.isna(lower_shadow) and lower_shadow <= (body_size * self.shadow_limit_threshold))

    def _is_bullish_marubozu(self, row: pd.Series) -> bool:
        """Check for Bullish Marubozu"""
        body_size = self._calculate_body_size(row)
        total_range = self._calculate_total_range(row)
        if pd.isna(total_range) or total_range == 0: return False # Not Marubozu if no range
        upper_shadow = self._calculate_upper_shadow(row)
        lower_shadow = self._calculate_lower_shadow(row)
        if pd.isna(upper_shadow) or pd.isna(lower_shadow) or pd.isna(body_size): return False
        max_shadow = total_range * self.marubozu_shadow_threshold
        # Bullish candle with almost no shadows
        return (self._is_bullish(row) and
                body_size > 0 and # Ensure it's not flat
                upper_shadow <= max_shadow and
                lower_shadow <= max_shadow)

    def _is_bearish_marubozu(self, row: pd.Series) -> bool:
        """Check for Bearish Marubozu"""
        body_size = self._calculate_body_size(row)
        total_range = self._calculate_total_range(row)
        if pd.isna(total_range) or total_range == 0: return False
        upper_shadow = self._calculate_upper_shadow(row)
        lower_shadow = self._calculate_lower_shadow(row)
        if pd.isna(upper_shadow) or pd.isna(lower_shadow) or pd.isna(body_size): return False
        max_shadow = total_range * self.marubozu_shadow_threshold
        # Bearish candle with almost no shadows
        return (self._is_bearish(row) and
                body_size > 0 and
                upper_shadow <= max_shadow and
                lower_shadow <= max_shadow)

    def _is_spinning_top(self, row: pd.Series) -> bool:
        """Check for Spinning Top"""
        body_size = self._calculate_body_size(row)
        total_range = self._calculate_total_range(row)
        upper_shadow = self._calculate_upper_shadow(row)
        lower_shadow = self._calculate_lower_shadow(row)
        if pd.isna(total_range) or total_range == 0 or pd.isna(body_size) or body_size == 0: return False
        if pd.isna(upper_shadow) or pd.isna(lower_shadow): return False
        # Small body relative to total range, shadows larger than body
        is_small_body = body_size <= (total_range * self.spinning_top_body_threshold)
        # Allow shadows to be equal to body size as well for flexibility
        shadows_significant = upper_shadow >= body_size and lower_shadow >= body_size
        return is_small_body and shadows_significant

    # --- Two Candlestick Pattern Checks ---
    def _is_bullish_engulfing(self, current: pd.Series, previous: pd.Series) -> bool:
        """Check if the current bullish candle engulfs the previous bearish one"""
        # Ensure values are valid numbers
        if current.isnull().any() or previous.isnull().any(): return False
        return (self._is_bullish(current) and self._is_bearish(previous) and
                current['open'] < previous['close'] and current['close'] > previous['open'])

    def _is_bearish_engulfing(self, current: pd.Series, previous: pd.Series) -> bool:
        """Check if the current bearish candle engulfs the previous bullish one"""
        if current.isnull().any() or previous.isnull().any(): return False
        return (self._is_bearish(current) and self._is_bullish(previous) and
                current['open'] > previous['close'] and current['close'] < previous['open'])

    def _is_piercing_line(self, current: pd.Series, previous: pd.Series) -> bool:
        """Check for Piercing Line pattern"""
        if current.isnull().any() or previous.isnull().any(): return False
        prev_body_size = self._calculate_body_size(previous)
        if pd.isna(prev_body_size) or prev_body_size == 0: return False
        midpoint_previous_body = previous['open'] - (prev_body_size * self.piercing_midpoint_threshold)
        # Previous is bearish, current is bullish
        # Current opens below previous low (or close)
        # Current closes above midpoint of previous body, but below previous open
        return (self._is_bearish(previous) and self._is_bullish(current) and
                current['open'] < previous['close'] and # Simplified: opens below previous close
                current['close'] > midpoint_previous_body and
                current['close'] < previous['open'])

    def _is_dark_cloud_cover(self, current: pd.Series, previous: pd.Series) -> bool:
        """Check for Dark Cloud Cover pattern"""
        if current.isnull().any() or previous.isnull().any(): return False
        prev_body_size = self._calculate_body_size(previous)
        if pd.isna(prev_body_size) or prev_body_size == 0: return False
        midpoint_previous_body = previous['open'] + (prev_body_size * self.piercing_midpoint_threshold)
        # Previous is bullish, current is bearish
        # Current opens above previous high (or close)
        # Current closes below midpoint of previous body, but above previous open
        return (self._is_bullish(previous) and self._is_bearish(current) and
                current['open'] > previous['close'] and # Simplified: opens above previous close
                current['close'] < midpoint_previous_body and
                current['close'] > previous['open'])

    def _is_bullish_harami(self, current: pd.Series, previous: pd.Series) -> bool:
        """Check for Bullish Harami pattern"""
        if current.isnull().any() or previous.isnull().any(): return False
        # Previous is (typically large) bearish
        # Current is small (bullish or bearish), completely contained within previous body
        return (self._is_bearish(previous) and
                max(current['open'], current['close']) < previous['open'] and
                min(current['open'], current['close']) > previous['close'])

    def _is_bearish_harami(self, current: pd.Series, previous: pd.Series) -> bool:
        """Check for Bearish Harami pattern"""
        if current.isnull().any() or previous.isnull().any(): return False
        # Previous is (typically large) bullish
        # Current is small (bullish or bearish), completely contained within previous body
        return (self._is_bullish(previous) and
                max(current['open'], current['close']) < previous['open'] and
                min(current['open'], current['close']) > previous['close'])

    # --- Pattern Calculation and Signal Generation ---
    def _calculate_pattern_score(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate the detailed pattern name and strength"""
        if len(df) < 2:
            return {"pattern": "insufficient_data", "strength": 0.0}

        current = df.iloc[-1]
        previous = df.iloc[-2]

        # Handle potential NaN values in critical columns
        required_cols = ['open', 'high', 'low', 'close']
        if current[required_cols].isnull().any() or previous[required_cols].isnull().any():
            self.logger.warning("NaN values detected in OHLC data for pattern calculation.")
            return {"pattern": "data_error", "strength": 0.0}

        # --- Check Two-Candle Patterns First ---
        if self._is_bullish_engulfing(current, previous):
            return {"pattern": "bullish_engulfing", "strength": 0.8}
        if self._is_bearish_engulfing(current, previous):
            return {"pattern": "bearish_engulfing", "strength": 0.8}
        if self._is_piercing_line(current, previous):
            return {"pattern": "piercing_line", "strength": 0.7}
        if self._is_dark_cloud_cover(current, previous):
            return {"pattern": "dark_cloud_cover", "strength": 0.7}
        if self._is_bullish_harami(current, previous):
             # Check if it's also a doji (Harami Cross) - potentially stronger
            if self._is_doji(current):
                 return {"pattern": "bullish_harami_cross", "strength": 0.6}
            return {"pattern": "bullish_harami", "strength": 0.5}
        if self._is_bearish_harami(current, previous):
            if self._is_doji(current):
                 return {"pattern": "bearish_harami_cross", "strength": 0.6}
            return {"pattern": "bearish_harami", "strength": 0.5}

        # --- Check Specific Single-Candle Patterns ---
        # Check Hammer/Hanging Man shapes
        if self._is_hammer_shape(current):
             return {"pattern": "hammer_or_hanging_man", "strength": 0.6} # Name reflects ambiguity

        # Check Inverted Hammer/Shooting Star shapes
        if self._is_inverted_hammer_shape(current):
             return {"pattern": "inverted_hammer_or_shooting_star", "strength": 0.6} # Name reflects ambiguity

        # Check Marubozu (Strong Momentum)
        if self._is_bullish_marubozu(current):
            return {"pattern": "bullish_marubozu", "strength": 0.7}
        if self._is_bearish_marubozu(current):
            return {"pattern": "bearish_marubozu", "strength": 0.7}

        # --- Check Indecision Patterns ---
        # Check Doji first as it's more specific than spinning top or simple candles
        if self._is_doji(current):
            return {"pattern": "doji", "strength": 0.3}
        # Check Spinning Top after Doji
        if self._is_spinning_top(current):
            return {"pattern": "spinning_top", "strength": 0.2}

        # --- Check Simple Bullish/Bearish Candle (If no specific pattern matched) ---
        current_body_size = self._calculate_body_size(current)
        # Ensure it has a body (i.e., not open == close, which should be caught by Doji)
        if not pd.isna(current_body_size) and current_body_size > 0:
            if self._is_bullish(current):
                return {"pattern": "simple_bullish", "strength": self.simple_candle_strength}
            elif self._is_bearish(current): # Use elif to be explicit
                return {"pattern": "simple_bearish", "strength": self.simple_candle_strength}

        # --- Default to neutral ---
        # Reached if open == close and not Doji (unlikely), or other unclassified cases.
        return {"pattern": "neutral", "strength": 0.0}

    def get_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate candlestick pattern signal with simplified pattern value"""
        try:
            # Calculate detailed pattern score
            pattern_data = self._calculate_pattern_score(df)
            detailed_pattern = pattern_data["pattern"]
            strength = pattern_data["strength"]

            # Determine signal and simplified pattern based on detailed pattern
            # Bullish Patterns
            if detailed_pattern in [
                "bullish_engulfing", "piercing_line",
                "bullish_harami", "bullish_harami_cross",
                "bullish_marubozu",
                "simple_bullish" # Added simple bullish
            ] or detailed_pattern == "hammer_or_hanging_man": # Treat shape initially as potential Hammer
                signal = "buy"
                simplified_pattern = "bullish"
            # Bearish Patterns
            elif detailed_pattern in [
                "bearish_engulfing", "dark_cloud_cover",
                "bearish_harami", "bearish_harami_cross",
                "bearish_marubozu",
                "simple_bearish" # Added simple bearish
            ] or detailed_pattern == "inverted_hammer_or_shooting_star": # Treat shape initially as potential Shooting Star
                 signal = "sell"
                 simplified_pattern = "bearish"
            # Neutral / Indecision / Error Patterns
            else: # Covers "neutral", "doji", "spinning_top", "insufficient_data", "data_error"
                signal = "neutral"
                simplified_pattern = "neutral"

            return {
                "indicator": self.name,
                "value": {
                    "pattern": simplified_pattern, # Use the simplified pattern name
                    "strength": strength,
                    "signal": signal,
                    "detailed_pattern": detailed_pattern # Keep detailed pattern for reference
                }
            }

        except Exception as e:
            self.logger.error(f"Error generating candlestick pattern signal: {str(e)}", exc_info=True)
            return {
                "indicator": self.name,
                "value": {
                    "pattern": "neutral", # Default to neutral on error
                    "strength": 0.0,
                    "signal": "neutral",
                    "detailed_pattern": "error"
                }
            }