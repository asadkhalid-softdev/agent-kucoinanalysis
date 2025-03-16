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
        "RSI": 1.0,
        "MACD": 1.0,
        "BBANDS": 0.8,
        "SMA": 0.7,
        "EMA": 0.8,
        "OBV": 0.6,
        "STOCH": 0.7,
        "ADX": 0.6,
        "FIBONACCI": 0.5
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
    
    def analyze(self, indicator_signals):
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
                "score": 0.0
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
        if total_weight > 0:
            weighted_score = sum(score * weight for score, weight in type_scores) / total_weight
        else:
            weighted_score = 0.0
        
        # Determine overall sentiment and strength
        if weighted_score > 0.5:
            overall = "buy"
            strength = "strong"
        elif weighted_score > 0.2:
            overall = "buy"
            strength = "moderate"
        elif weighted_score > 0.05:
            overall = "buy"
            strength = "weak"
        elif weighted_score < -0.5:
            overall = "sell"
            strength = "strong"
        elif weighted_score < -0.2:
            overall = "sell"
            strength = "moderate"
        elif weighted_score < -0.05:
            overall = "sell"
            strength = "weak"
        else:
            overall = "neutral"
            strength = "none"
        
        # Calculate confidence based on agreement among indicators
        signal_values = [self._normalize_signal(s["signal"]) for s in indicator_signals]
        signal_std = np.std(signal_values)
        confidence = max(0.0, min(1.0, 1.0 - signal_std))
        
        return {
            "overall": overall,
            "strength": strength,
            "confidence": round(confidence, 2),
            "score": round(weighted_score, 2)
        }
