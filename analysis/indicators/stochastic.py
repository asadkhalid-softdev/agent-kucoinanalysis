import pandas as pd
import pandas_ta as ta
import numpy as np

class StochasticOscillator:
    def __init__(self, k_period=14, d_period=3, smooth_k=3):
        self.k_period = k_period
        self.d_period = d_period
        self.smooth_k = smooth_k
        self.name = f"STOCH"
        self.overbought = 80
        self.oversold = 20

    def calculate(self, df):
        """Calculate Stochastic Oscillator
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC price data
            
        Returns:
            pd.DataFrame: Stochastic oscillator values including %K and %D
        """
        return ta.stoch(df['high'], df['low'], df['close'], 
                        k=self.k_period, d=self.d_period, smooth_k=self.smooth_k)

    def get_signal(self, df):
        """Generate trading signal based on Stochastic Oscillator for trend following
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC price data
            
        Returns:
            dict: Signal information
        """
        stoch = self.calculate(df)
        stoch = stoch.sort_index(ascending=False)

        # print(df)
        # print(stoch)

        # Get column names from pandas-ta output
        k_col = f"STOCHk_{self.k_period}_{self.d_period}_{self.smooth_k}"
        d_col = f"STOCHd_{self.k_period}_{self.d_period}_{self.smooth_k}"

        current_k = stoch[k_col].iloc[-1]
        current_d = stoch[d_col].iloc[-1]
        
        # Get previous values for trend determination
        prev_k = stoch[k_col].iloc[-2] if len(stoch) > 1 else current_k
        prev_d = stoch[d_col].iloc[-2] if len(stoch) > 1 else current_d
        
        # Get more history for trend confirmation
        if len(stoch) >= 5:
            k_5_periods_ago = stoch[k_col].iloc[-5]
            d_5_periods_ago = stoch[d_col].iloc[-5]
            k_trend = "up" if current_k > k_5_periods_ago else "down"
            d_trend = "up" if current_d > d_5_periods_ago else "down"
        else:
            k_trend = "up" if current_k > prev_k else "down"
            d_trend = "up" if current_d > prev_d else "down"
        
        # Determine overall price trend using close prices
        if len(df) >= 20:
            price_trend = "up" if df['close'].iloc[-1] > df['close'].iloc[-20] else "down"
        else:
            price_trend = "neutral"

        # Determine signal based on trend following principles
        signal = "neutral"
        strength = 0.0
        
        # For trend following with Stochastic:
        # 1. In strong uptrends, stochastic often remains in the upper range (above 50)
        # 2. In strong downtrends, stochastic often remains in the lower range (below 50)
        # 3. Crossovers of %K and %D can signal trend continuation or early reversal
        
        # Bullish trend following signals
        if price_trend == "up":
            if current_k > 50 and current_d > 50:
                # Stochastic confirming uptrend
                if current_k > self.overbought and current_d > self.overbought:
                    # Strong uptrend with stochastic in overbought zone
                    if k_trend == "up" and d_trend == "up":
                        # Still strengthening
                        signal = "bullish"
                        strength = min(1.0, 0.7 + (current_k - self.overbought) / (100 - self.overbought) * 0.3)
                    else:
                        # Might be losing momentum but still in uptrend
                        signal = "slightly_bullish"
                        strength = 0.5
                elif current_k > current_d and prev_k <= prev_d:
                    # Bullish crossover in upper range - trend continuation
                    signal = "bullish"
                    strength = 0.8
                else:
                    # General uptrend confirmation
                    signal = "bullish"
                    strength = 0.6
            elif current_k < 50 and current_k > current_d and prev_k <= prev_d:
                # Bullish crossover in lower range during uptrend - potential reversal back to trend
                signal = "slightly_bullish"
                strength = 0.4
        
        # Bearish trend following signals
        elif price_trend == "down":
            if current_k < 50 and current_d < 50:
                # Stochastic confirming downtrend
                if current_k < self.oversold and current_d < self.oversold:
                    # Strong downtrend with stochastic in oversold zone
                    if k_trend == "down" and d_trend == "down":
                        # Still strengthening
                        signal = "bearish"
                        strength = min(1.0, 0.7 + (self.oversold - current_k) / self.oversold * 0.3)
                    else:
                        # Might be losing momentum but still in downtrend
                        signal = "slightly_bearish"
                        strength = 0.5
                elif current_k < current_d and prev_k >= prev_d:
                    # Bearish crossover in lower range - trend continuation
                    signal = "bearish"
                    strength = 0.8
                else:
                    # General downtrend confirmation
                    signal = "bearish"
                    strength = 0.6
            elif current_k > 50 and current_k < current_d and prev_k >= prev_d:
                # Bearish crossover in upper range during downtrend - potential reversal back to trend
                signal = "slightly_bearish"
                strength = 0.4
        
        # When price trend is not clear, use stochastic for early trend detection
        else:
            # Bullish signals
            if current_k > 50 and current_d > 50 and current_k > current_d and prev_k <= prev_d:
                # Bullish crossover above 50
                signal = "bullish"
                strength = 0.6
            # Bearish signals
            elif current_k < 50 and current_d < 50 and current_k < current_d and prev_k >= prev_d:
                # Bearish crossover below 50
                signal = "bearish"
                strength = 0.6
            # Potential trend starts
            elif current_k > 80 and k_trend == "up":
                signal = "slightly_bullish"
                strength = 0.3
            elif current_k < 20 and k_trend == "down":
                signal = "slightly_bearish"
                strength = 0.3
            
        return {
            "indicator": self.name,
            "value": {
                "k": current_k,
                "d": current_d,
                "k_trend": k_trend,
                "d_trend": d_trend,
                "price_trend": price_trend
            },
            "signal": signal,
            "strength": strength
        }
