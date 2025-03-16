import pandas as pd
import numpy as np
from collections import defaultdict

class MultiTimeframeAnalyzer:
    """
    Analyzes multiple timeframes to provide a more comprehensive view.
    """
    
    # Timeframe weights (higher weight for longer timeframes)
    TIMEFRAME_WEIGHTS = {
        "5min": 0.4,
        "15min": 0.6,
        "1hour": 1.0,
        "4hour": 1.5,
        "1day": 2.0
    }
    
    def __init__(self, analysis_engine):
        """
        Initialize the multi-timeframe analyzer.
        
        Args:
            analysis_engine (AnalysisEngine): The analysis engine to use
        """
        self.analysis_engine = analysis_engine
    
    def analyze(self, symbol, timeframe_data):
        """
        Analyze multiple timeframes for a symbol.
        
        Args:
            symbol (str): Trading pair symbol
            timeframe_data (dict): Dictionary mapping timeframes to klines data
            
        Returns:
            dict: Combined analysis results
        """
        # Analyze each timeframe
        timeframe_results = {}
        all_sentiments = []
        
        for timeframe, klines in timeframe_data.items():
            # Skip if no data or insufficient data
            if not klines or len(klines) < 50:
                continue
                
            # Analyze this timeframe
            result = self.analysis_engine.analyze_symbol(symbol, klines)
            timeframe_results[timeframe] = result
            
            # Store sentiment with timeframe weight
            weight = self.TIMEFRAME_WEIGHTS.get(timeframe, 1.0)
            all_sentiments.append({
                "timeframe": timeframe,
                "sentiment": result["sentiment"],
                "weight": weight
            })
        
        # Combine sentiments from all timeframes
        combined_sentiment = self._combine_sentiments(all_sentiments)
        
        # Get the primary timeframe result (usually 1hour)
        primary_timeframe = "1hour"
        primary_result = timeframe_results.get(primary_timeframe, next(iter(timeframe_results.values())) if timeframe_results else None)
        
        if not primary_result:
            return {
                "symbol": symbol,
                "timestamp": pd.Timestamp.now().isoformat(),
                "error": "No valid analysis available",
                "sentiment": {
                    "overall": "neutral",
                    "strength": "none",
                    "confidence": 0.0
                }
            }
        
        # Create combined result
        combined_result = primary_result.copy()
        combined_result["multi_timeframe"] = {
            "timeframes_analyzed": list(timeframe_results.keys()),
            "timeframe_sentiments": {tf: res["sentiment"] for tf, res in timeframe_results.items()}
        }
        combined_result["sentiment"] = combined_sentiment
        
        # Update analysis summary
        combined_result["analysis_summary"] = self._generate_multi_tf_summary(symbol, timeframe_results, combined_sentiment)
        
        return combined_result
    
    def _combine_sentiments(self, sentiment_data):
        """
        Combine sentiments from multiple timeframes.
        
        Args:
            sentiment_data (list): List of dictionaries with timeframe sentiments and weights
            
        Returns:
            dict: Combined sentiment
        """
        if not sentiment_data:
            return {
                "overall": "neutral",
                "strength": "none",
                "confidence": 0.0,
                "score": 0.0
            }
        
        # Map sentiment to numerical values
        sentiment_values = {
            "buy": 1.0,
            "neutral": 0.0,
            "sell": -1.0
        }
        
        # Map strength to multipliers
        strength_multipliers = {
            "strong": 1.0,
            "moderate": 0.66,
            "weak": 0.33,
            "none": 0.0
        }
        
        # Calculate weighted score
        total_weight = sum(item["weight"] for item in sentiment_data)
        weighted_score = 0.0
        
        for item in sentiment_data:
            sentiment = item["sentiment"]["overall"]
            strength = item["sentiment"]["strength"]
            base_value = sentiment_values.get(sentiment, 0.0)
            multiplier = strength_multipliers.get(strength, 0.0)
            score = base_value * multiplier
            weighted_score += score * item["weight"] / total_weight
        
        # Determine overall sentiment and strength based on weighted score
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
        
        # Calculate confidence based on agreement among timeframes
        confidence_scores = []
        for item in sentiment_data:
            if item["sentiment"]["overall"] == overall:
                confidence_scores.append(item["sentiment"]["confidence"])
            else:
                confidence_scores.append(0.0)
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return {
            "overall": overall,
            "strength": strength,
            "confidence": round(avg_confidence, 2),
            "score": round(weighted_score, 2)
        }
    
    def _generate_multi_tf_summary(self, symbol, timeframe_results, combined_sentiment):
        """
        Generate a summary that includes multi-timeframe analysis.
        
        Args:
            symbol (str): Trading pair symbol
            timeframe_results (dict): Results for each timeframe
            combined_sentiment (dict): Combined sentiment analysis
            
        Returns:
            str: Analysis summary
        """
        # Get primary timeframe (1hour or first available)
        primary_tf = "1hour" if "1hour" in timeframe_results else next(iter(timeframe_results.keys()))
        primary_result = timeframe_results[primary_tf]
        
        # Start with basic information
        summary_parts = []
        
        # Add price information from primary timeframe
        if "price" in primary_result:
            summary_parts.append(f"{symbol} is trading at {primary_result['price']:.2f}")
        
        # Add combined sentiment
        sentiment_str = f"{combined_sentiment['strength']} {combined_sentiment['overall']}" if combined_sentiment['strength'] != 'none' else 'neutral'
        summary_parts.append(f"Multi-timeframe analysis shows {sentiment_str} sentiment (confidence: {combined_sentiment['confidence']:.2f})")
        
        # Add timeframe breakdown
        tf_sentiments = []
        for tf, result in timeframe_results.items():
            sentiment = result["sentiment"]
            tf_sentiment = f"{tf}: {sentiment['strength']} {sentiment['overall']}" if sentiment['strength'] != 'none' else f"{tf}: neutral"
            tf_sentiments.append(tf_sentiment)
        
        if tf_sentiments:
            summary_parts.append("Timeframe breakdown: " + ", ".join(tf_sentiments))
        
        # Add key indicator insights from primary timeframe
        if "indicators" in primary_result:
            indicators = primary_result["indicators"]
            
            # RSI
            rsi_keys = [k for k in indicators if k.startswith("RSI")]
            if rsi_keys:
                rsi = indicators[rsi_keys[0]]
                rsi_value = rsi['value']
                if rsi_value > 70:
                    summary_parts.append(f"RSI is overbought at {rsi_value:.2f}")
                elif rsi_value < 30:
                    summary_parts.append(f"RSI is oversold at {rsi_value:.2f}")
            
            # MACD
            macd_keys = [k for k in indicators if k.startswith("MACD")]
            if macd_keys:
                macd = indicators[macd_keys[0]]
                if macd['signal'] in ['bullish', 'strongly_bullish']:
                    summary_parts.append("MACD shows bullish momentum")
                elif macd['signal'] in ['bearish', 'strongly_bearish']:
                    summary_parts.append("MACD shows bearish momentum")
        
        # Combine all parts
        return " ".join(summary_parts)
