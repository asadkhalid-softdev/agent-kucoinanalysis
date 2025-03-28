import numpy as np
from collections import defaultdict
import logging

class SentimentAnalyzer:
    """
    Analyzes technical indicators to determine overall market sentiment.
    """
    
    # Signal strength mapping
    SIGNAL_WEIGHTS = {
        "strongly_bullish": 1.0,
        "bullish": 0.75,
        "slightly_bullish": 0.25,
        "neutral": 0.0,
        "slightly_bearish": -0.25,
        "bearish": -0.75,
        "strongly_bearish": -1.0
    }
    
    # Indicator importance weights (can be adjusted)
    INDICATOR_WEIGHTS = {
        "VWAP": 1.4,      # Critical for intraday price validation [11][14][17]
        "EMA": 1.3,       # 20-period EMA particularly effective for trend identification [13][17]
        "MACD": 1.25,     # Maintains momentum tracking but reduced vs 1H due to more false signals [5][19]
        "BBANDS": 1.1,    # Tightened bands work well with 15m volatility [9][18]
        "RSI": 1.0,       # Use shorter lookback (9-11 periods) to reduce lag [12][16]
        "OBV": 0.9,       # Volume confirmation crucial for breakout validation [19][20]
        "ADX": 1.0,       # Essential for filtering low-strength trends in noisy markets [5][19]
        "STOCH": 0.85,    # Useful but prone to whipsaws - pair with EMA [14][16]
        "SMA": 0.7,       # Longer-period SMAs (50/100) for higher timeframe confluence [15][17]
        "FIBONACCI": 0.5  # Less reliable on 15m - use only with cluster zones [9][14]
    }
    
    def __init__(self):
        """Initialize the sentiment analyzer."""
        self.logger = logging.getLogger(__name__)
    
    def _get_base_indicator_type(self, indicator_name):
        """Extract the base indicator type from the full indicator name."""
        # Extract the base indicator type (e.g., "RSI_14" -> "RSI")
        return indicator_name.split('_')[0]
    
    def _normalize_signal(self, signal):
        """Convert string signal to numerical value."""
        return self.SIGNAL_WEIGHTS.get(signal, 0.0)
    
    def analyze(self, indicator_signals):
        """
        Analyze multiple indicator signals to determine overall sentiment for different strategies.
        
        Args:
            indicator_signals (list): List of dictionaries containing indicator signals
            df (pd.DataFrame): DataFrame with OHLCV price data
            
        Returns:
            dict: Strategy-specific sentiment analysis
        """
        if not indicator_signals:
            self.logger.warning("No indicator signals provided for sentiment analysis")
            return {
                "volume": 0.0,
                "price": 0.0,
                "strategy": {
                    "momentum": {"score": 0.0, "confidence": 0.0},
                    "mean_reversion": {"score": 0.0, "confidence": 0.0},
                    "breakout": {"score": 0.0, "confidence": 0.0}
                }
            }
        
        self.logger.info(f"Starting sentiment analysis with {len(indicator_signals)} indicators")
        
        # Group signals by indicator type
        indicator_groups = defaultdict(list)
        for signal in indicator_signals:
            base_type = self._get_base_indicator_type(signal["indicator"])
            indicator_groups[base_type].append(signal)
        
        self.logger.debug(f"Grouped indicators: {list(indicator_groups.keys())}")
        
        # Strategy-specific weights for indicators
        MOMENTUM_WEIGHTS = {
            "MACD": 1.5,      # Keep as primary (good for daytrading)
            "RSI": 1.3,       # Increase slightly (faster signals)
            "STOCH": 1.1,     # Increase slightly (good for short-term)
            "ADX": 0.9,       # Increase (trend strength is crucial for daytrading)
            "OBV": 0.8,       # Increase (volume is more important for daytrading)
            "CANDLESTICK": 0.7 # Increase (candlestick patterns are crucial for daytrading)
        }
        
        MEAN_REVERSION_WEIGHTS = {
            "BBANDS": 1.4,    # Slightly decrease (mean reversion is less reliable in daytrading)
            "RSI": 1.3,       # Increase (more important for short-term reversals)
            "STOCH": 1.2,     # Increase (better for short-term reversals)
            "FIBONACCI": 0.6, # Decrease (less reliable for daytrading)
            "ADX": 0.7,       # Increase (trend strength is important)
            "CANDLESTICK": 0.8 # Increase significantly (crucial for daytrading reversals)
        }
        
        BREAKOUT_WEIGHTS = {
            "BBANDS": 1.2,    # Decrease (volatility is less reliable for daytrading breakouts)
            "OBV": 1.5,       # Increase significantly (volume is crucial for breakouts)
            "ADX": 1.3,       # Increase (trend strength is crucial for breakouts)
            "MACD": 1.0,      # Increase (momentum confirmation is important)
            "RSI": 0.8,       # Slightly increase (momentum confirmation)
            "CANDLESTICK": 0.9 # Increase significantly (crucial for breakout confirmation)
        }
        
        # Calculate scores for each strategy
        momentum_scores = []
        momentum_scores_dict = {}
        mean_reversion_scores = []
        mean_reversion_scores_dict = {}
        breakout_scores = []
        breakout_scores_dict = {}
        
        for indicator_type, signals in indicator_groups.items():
            # Calculate momentum score
            if indicator_type in MOMENTUM_WEIGHTS:
                momentum_weight = MOMENTUM_WEIGHTS[indicator_type]
                for signal in signals:
                    value = signal["value"]
                    if indicator_type == "MACD":
                        # MACD momentum score
                        if value["macd_position"] == "above":
                            score = 0.5 + (value["normalized_hist"] * 0.5) if value["hist_trend"] == "up" else 0.3
                        else:
                            score = -0.5 - (abs(value["normalized_hist"]) * 0.5) if value["hist_trend"] == "down" else -0.3
                    elif indicator_type == "RSI":
                        # RSI momentum score
                        if value["rsi"] > 50:
                            score = 0.5 + ((value["rsi"] - 50) / 50) * 0.5
                        else:
                            score = -0.5 - ((50 - value["rsi"]) / 50) * 0.5
                    elif indicator_type == "STOCH":
                        # Stochastic momentum score
                        if value["k"] > 50:
                            score = 0.5 + ((value["k"] - 50) / 50) * 0.5
                        else:
                            score = -0.5 - ((50 - value["k"]) / 50) * 0.5
                    elif indicator_type == "CANDLESTICK":
                        # Candlestick pattern momentum score
                        if value["pattern"] == "bullish":
                            score = 0.8
                        elif value["pattern"] == "bearish":
                            score = -0.8
                        else:
                            score = 0.0

                    elif indicator_type == "ADX":
                        # ADX momentum score based on trend strength and DI crossover
                        if value["trend_strength"] == "strong":
                            score = 0.8 if value["plus_di"] > value["minus_di"] else -0.8
                        elif value["trend_strength"] == "moderate":
                            score = 0.5 if value["plus_di"] > value["minus_di"] else -0.5
                        else:
                            score = 0.0
                    elif indicator_type == "OBV":
                        # OBV momentum score based on trend and confirmation
                        if value["pattern"]["confirmation"]:
                            score = 0.6 if value["short_term_trend"] == "up" else -0.6
                        else:
                            score = 0.3 if value["short_term_trend"] == "up" else -0.3
                    momentum_scores.append(score * momentum_weight)
                    momentum_scores_dict[indicator_type] = score
            
            # Calculate mean reversion score
            if indicator_type in MEAN_REVERSION_WEIGHTS:
                mean_reversion_weight = MEAN_REVERSION_WEIGHTS[indicator_type]
                for signal in signals:
                    value = signal["value"]
                    if indicator_type == "BBANDS":
                        # Bollinger Bands mean reversion score
                        if value["percent_b"] > 0.8:
                            score = -0.8  # Overbought
                        elif value["percent_b"] < 0.2:
                            score = 0.8   # Oversold
                        else:
                            score = 0.0
                    elif indicator_type == "RSI":
                        # RSI mean reversion score
                        if value["rsi"] > value["overbought"]:
                            score = -0.8
                        elif value["rsi"] < value["oversold"]:
                            score = 0.8
                        else:
                            score = 0.0
                    elif indicator_type == "STOCH":
                        # Stochastic mean reversion score
                        if value["k"] > value["overbought"]:
                            score = -0.8
                        elif value["k"] < value["oversold"]:
                            score = 0.8
                        else:
                            score = 0.0
                    elif indicator_type == "CANDLESTICK":
                        # Candlestick pattern mean reversion score
                        if value["pattern"] == "bullish":
                            score = 0.6  # Potential reversal from downtrend
                        elif value["pattern"] == "bearish":
                            score = -0.6  # Potential reversal from uptrend
                        else:
                            score = 0.0
                    elif indicator_type == "FIBONACCI":
                        # Fibonacci mean reversion score based on current level and distance
                        current_level = value["current_level"]
                        distance_pct = value["distance_pct"]
                        price_direction = value["price_direction"]
                        
                        # Strong reversal signals at extreme levels
                        if current_level in ["0.786", "1.618"]:
                            score = -0.8 if price_direction == "up" else 0.8
                        elif current_level in ["0.236", "0.382"]:
                            score = 0.8 if price_direction == "down" else -0.8
                        # Moderate reversal signals at standard levels
                        elif current_level in ["0.500", "0.618"]:
                            if distance_pct > 0.5:  # Price is significantly away from level
                                score = -0.6 if price_direction == "up" else 0.6
                            else:
                                score = 0.0
                        elif current_level in ["0.382", "0.500"]:
                            if distance_pct > 0.5:  # Price is significantly away from level
                                score = 0.6 if price_direction == "down" else -0.6
                            else:
                                score = 0.0
                        else:
                            score = 0.0
                    elif indicator_type == "ADX":
                        # ADX mean reversion score based on trend strength and potential reversal
                        if value["trend_strength"] == "strong":
                            # Strong trend - look for potential reversal
                            if value["plus_di"] > value["minus_di"]:
                                score = -0.6  # Potential reversal from uptrend
                            else:
                                score = 0.6   # Potential reversal from downtrend
                        elif value["trend_strength"] == "moderate":
                            # Moderate trend - weaker reversal signals
                            if value["plus_di"] > value["minus_di"]:
                                score = -0.4  # Potential reversal from uptrend
                            else:
                                score = 0.4   # Potential reversal from downtrend
                        else:
                            score = 0.0  # Weak trend - no clear reversal signal
                    mean_reversion_scores.append(score * mean_reversion_weight)
                    mean_reversion_scores_dict[indicator_type] = score

            # Calculate breakout score
            if indicator_type in BREAKOUT_WEIGHTS:
                breakout_weight = BREAKOUT_WEIGHTS[indicator_type]
                for signal in signals:
                    value = signal["value"]
                    if indicator_type == "BBANDS":
                        # Bollinger Bands breakout score
                        if value["bandwidth"] > 0.1:  # High volatility
                            if value["percent_b"] > 0.8:
                                score = -0.8  # Potential breakdown
                            elif value["percent_b"] < 0.2:
                                score = 0.8   # Potential breakout
                            else:
                                score = 0.0
                        else:
                            score = 0.0
                    elif indicator_type == "OBV":
                        # OBV breakout score
                        if value["pattern"]["confirmation"]:
                            score = 0.5 if value["short_term_trend"] == "up" else -0.5
                        else:
                            score = 0.0
                    elif indicator_type == "ADX":
                        # ADX breakout score
                        if value["trend_strength"] == "strong":
                            score = 0.8 if value["plus_di"] > value["minus_di"] else -0.8
                        elif value["trend_strength"] == "moderate":
                            score = 0.5 if value["plus_di"] > value["minus_di"] else -0.5
                        else:
                            score = 0.0
                    elif indicator_type == "CANDLESTICK":
                        # Candlestick pattern breakout score
                        if value["pattern"] in ["bullish_engulfing", "hammer"]:
                            score = 0.6  # Potential breakout to the upside
                        elif value["pattern"] in ["bearish_engulfing", "shooting_star"]:
                            score = -0.6  # Potential breakout to the downside
                        else:
                            score = 0.0
                    elif indicator_type == "MACD":
                        # MACD breakout score based on histogram momentum and signal line crossover
                        if value["hist_trend"] == "up" and value["normalized_hist"] > 0.5:
                            score = 0.7  # Strong upward momentum breakout
                        elif value["hist_trend"] == "down" and value["normalized_hist"] < -0.5:
                            score = -0.7  # Strong downward momentum breakout
                        elif value["hist_trend"] == "up" and value["normalized_hist"] > 0.2:
                            score = 0.4  # Moderate upward momentum breakout
                        elif value["hist_trend"] == "down" and value["normalized_hist"] < -0.2:
                            score = -0.4  # Moderate downward momentum breakout
                        else:
                            score = 0.0
                    elif indicator_type == "RSI":
                        # RSI breakout score based on momentum and overbought/oversold levels
                        if value["rsi"] > 70 and value["rsi_trend"] == "up":
                            score = 0.6  # Strong upward momentum breakout
                        elif value["rsi"] < 30 and value["rsi_trend"] == "down":
                            score = -0.6  # Strong downward momentum breakout
                        elif value["rsi"] > 60 and value["rsi_trend"] == "up":
                            score = 0.4  # Moderate upward momentum breakout
                        elif value["rsi"] < 40 and value["rsi_trend"] == "down":
                            score = -0.4  # Moderate downward momentum breakout
                        else:
                            score = 0.0
                    breakout_scores.append(score * breakout_weight)
                    breakout_scores_dict[indicator_type] = score
            
        # Calculate weighted average scores
        weighted_score_momentum = sum(momentum_scores) / sum(MOMENTUM_WEIGHTS.values()) if momentum_scores else 0.0
        weighted_score_mean_reversion = sum(mean_reversion_scores) / sum(MEAN_REVERSION_WEIGHTS.values()) if mean_reversion_scores else 0.0
        weighted_score_breakout = sum(breakout_scores) / sum(BREAKOUT_WEIGHTS.values()) if breakout_scores else 0.0
        
        # Calculate confidence for each strategy
        confidence_momentum = max(0.0, min(1.0, 1.0 - np.std(momentum_scores))) if momentum_scores else 0.0
        confidence_mean_reversion = max(0.0, min(1.0, 1.0 - np.std(mean_reversion_scores))) if mean_reversion_scores else 0.0
        confidence_breakout = max(0.0, min(1.0, 1.0 - np.std(breakout_scores))) if breakout_scores else 0.0
        
        result = {
            "strategy": {
                "momentum": {
                    "score": round(weighted_score_momentum, 2),
                    "confidence": round(confidence_momentum, 2),
                    "scores": momentum_scores_dict
                },
                "mean_reversion": {
                    "score": round(weighted_score_mean_reversion, 1),
                    "confidence": round(confidence_mean_reversion, 1),
                    "scores": mean_reversion_scores_dict
                },
                "breakout": {
                    "score": round(weighted_score_breakout, 1),
                    "confidence": round(confidence_breakout, 1),
                    "scores": breakout_scores_dict
                }
            }
        }
        
        self.logger.info(f"Sentiment analysis completed with scores: Momentum={result['strategy']['momentum']['score']:.2f}, "
                        f"Mean Reversion={result['strategy']['mean_reversion']['score']:.2f}, "
                        f"Breakout={result['strategy']['breakout']['score']:.2f}")
        
        return result
        
