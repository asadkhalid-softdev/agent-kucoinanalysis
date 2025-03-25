import numpy as np
from collections import defaultdict

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
        pass
    
    def _get_base_indicator_type(self, indicator_name):
        """Extract the base indicator type from the full indicator name."""
        # Extract the base indicator type (e.g., "RSI_14" -> "RSI")
        return indicator_name.split('_')[0]
    
    def _normalize_signal(self, signal):
        """Convert string signal to numerical value."""
        return self.SIGNAL_WEIGHTS.get(signal, 0.0)
    
    def analyze(self, indicator_signals, df):
        """
        Analyze multiple indicator signals to determine overall sentiment.
        
        Args:
            indicator_signals (list): List of dictionaries containing indicator signals
            
        Returns:
            dict: Overall sentiment analysis
        """
        if not indicator_signals:
            return {
                "overall": "neutral",
                "strength": "none",
                "confidence": 0.0,
                "score": 0.0,
                "volume": 0.0
            }
        
        # Group signals by indicator type to avoid overweighting multiple instances
        indicator_groups = defaultdict(list)
        for signal in indicator_signals:
            base_type = self._get_base_indicator_type(signal["indicator"])
            indicator_groups[base_type].append(signal)
        
        # Calculate weighted sentiment score for each indicator type
        type_scores = []
        total_weight = 0
        
        for indicator_type, signals in indicator_groups.items():
            # Average the signals of the same type
            type_signal_values = [
                self._normalize_signal(s["signal"]) * s["strength"] 
                for s in signals
            ]
            avg_signal = sum(type_signal_values) / len(type_signal_values)
            
            # Get the weight for this indicator type
            weight = self.INDICATOR_WEIGHTS.get(indicator_type, 0.5)
            type_scores.append((avg_signal, weight))
            total_weight += weight
        
            # Calculate weighted average sentiment score
            weighted_score = sum(score * weight for score, weight in type_scores) / total_weight if total_weight > 0 else 0.0

        # Revised sentiment thresholds for 15m trading
        if weighted_score >= 0.65:        # Extreme bullish confirmation
            overall = "buy"
            strength = "strong"
        elif weighted_score >= 0.45:      # Clear bullish momentum
            overall = "buy" 
            strength = "moderate"
        elif weighted_score >= 0.25:      # Potential reversal signal
            overall = "buy"
            strength = "weak"
        elif weighted_score <= -0.6:      # Extreme bearish (contrarian opportunity)
            overall = "buy"
            strength = "reversal"
        else:
            overall = "neutral" if weighted_score > -0.6 else "hold"
            strength = "none"
        
        # Calculate confidence based on agreement among indicators
        signal_values = [self._normalize_signal(s["signal"]) for s in indicator_signals]
        signal_std = np.std(signal_values)
        confidence = max(0.0, min(1.0, 1.0 - signal_std))
        
        return {
            "overall": overall,
            "strength": strength,
            "confidence": round(confidence, 2),
            "score": round(weighted_score, 2),
            "volume": df['volume'].iloc[-1],
            "price": df['close'].iloc[-1]
        }
