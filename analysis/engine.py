import pandas as pd
import logging
from datetime import datetime

from analysis.indicators import (
    SimpleMovingAverage, ExponentialMovingAverage, RSI, 
    MACD, BollingerBands, OnBalanceVolume, StochasticOscillator,
    AverageDirectionalIndex, FibonacciRetracement
)
from analysis.sentiment import SentimentAnalyzer

class AnalysisEngine:
    """
    Main analysis engine that coordinates technical indicators and sentiment analysis.
    """
    
    def __init__(self, config=None):
        """
        Initialize the analysis engine with indicators.
        
        Args:
            config (dict, optional): Configuration parameters
        """
        self.config = config or {}
        self.indicators = self._initialize_indicators()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.logger = logging.getLogger(__name__)
    
    def _initialize_indicators(self):
        """Initialize technical indicators based on configuration."""
        indicators = []
        self.biggest_window = 50
        
        # Add default indicators or use configuration if provided
        analysis_list = self.config.get('analysis', [])
        if 'SMA' in analysis_list.get('indicators', []):
            indicators.append(SimpleMovingAverage(window=20))  # Captures recent trend
            indicators.append(SimpleMovingAverage(window=50))  # Intermediate trend
        if 'EMA' in analysis_list.get('indicators', []):
            indicators.append(ExponentialMovingAverage(window=9))  # Fast signal
            indicators.append(ExponentialMovingAverage(window=21))  # Medium signal
        if 'RSI' in analysis_list.get('indicators', []):
            indicators.append(RSI(window=14))
        if 'MACD' in analysis_list.get('indicators', []):
            indicators.append(MACD(fast=12, slow=26, signal=9))  # 
        if 'BBANDS' in analysis_list.get('indicators', []):
            indicators.append(BollingerBands(window=20, window_dev=2.0))  # 
        if 'OBV' in analysis_list.get('indicators', []):
            indicators.append(OnBalanceVolume())
        if 'STOCH' in analysis_list.get('indicators', []):
            indicators.append(StochasticOscillator(k_period=14, d_period=3, smooth_k=3))  
        if 'ADX' in analysis_list.get('indicators', []):
            indicators.append(AverageDirectionalIndex(length=14))  # Trend strength
        if 'FIBONACCI' in analysis_list.get('indicators', []):
            indicators.append(FibonacciRetracement())
        
        return indicators
    
    def analyze_symbol(self, symbol, klines_data):
        """
        Perform technical analysis on a symbol.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC-USDT')
            klines_data (list): Candlestick data from KuCoin API
            
        Returns:
            dict: Analysis results including indicators and sentiment
        """
        try:
            # Convert klines data to DataFrame
            df = self._prepare_dataframe(klines_data)
            self.logger.info(f"Analyzing {symbol} with {len(df)} data points")
            
            if df.empty or len(df) < 100:  # Need enough data for indicators
                self.logger.warning(f"Not enough data for {symbol} analysis")
                return {
                    "symbol": symbol,
                    "timestamp": datetime.now().isoformat(),
                    "error": "Insufficient data for analysis",
                    "indicators": {},
                    "sentiment": {
                        "overall": "neutral",
                        "strength": "none",
                        "confidence": 0.0
                    }
                }
            
            # Calculate indicators
            indicator_results = {}
            indicator_signals = []
            
            for indicator in self.indicators:
                try:
                    signal = indicator.get_signal(df)
                    indicator_results[indicator.name] = signal
                    indicator_signals.append(signal)
                except Exception as e:
                    self.logger.error(f"Error calculating {indicator.name} for {symbol}: {str(e)}")
            
            # Analyze sentiment
            sentiment = self.sentiment_analyzer.analyze(indicator_signals, df)
            
            # Prepare analysis summary
            summary = self._generate_summary(symbol, df, indicator_results, sentiment)
            
            return {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "price": df['close'].iloc[-1],
                "indicators": indicator_results,
                "sentiment": sentiment,
                "analysis_summary": summary,
                "volume": df['volume'].iloc[-1]
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {str(e)}")
            return {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "indicators": {},
                "sentiment": {
                    "overall": "neutral",
                    "strength": "none",
                    "confidence": 0.0
                }
            }
    
    def _prepare_dataframe(self, klines_data):
        """
        Convert KuCoin klines data to pandas DataFrame.
        
        Args:
            klines_data (list): Candlestick data from KuCoin API
            
        Returns:
            pd.DataFrame: Prepared DataFrame with OHLCV data
        """
        # KuCoin API returns data in format [timestamp, open, close, high, low, volume, ...]
        # columns = ['timestamp', 'open', 'close', 'high', 'low', 'volume']
        columns = ['timestamp', 'open', 'close', 'high', 'low', 'volume', 'amount']
        df = pd.DataFrame(klines_data, columns=columns)
        
        # Convert types
        for col in ['open', 'close', 'high', 'low', 'volume']:
            df[col] = pd.to_numeric(df[col])
        
        # Convert timestamp to datetime
        # Convert strings to numeric first
        df['timestamp'] = pd.to_numeric(df['timestamp'])
        # Then apply to_datetime with unit
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        return df
    
    def _generate_summary(self, symbol, df, indicator_results, sentiment):
        """
        Generate a human-readable analysis summary.
        
        Args:
            symbol (str): Trading pair symbol
            df (pd.DataFrame): Price data
            indicator_results (dict): Results from technical indicators
            sentiment (dict): Sentiment analysis results
            
        Returns:
            str: Analysis summary
        """
        current_price = df['close'].iloc[-1]
        prev_price = df['close'].iloc[-2]
        price_change = (current_price - prev_price) / prev_price * 100
        
        summary_parts = []
        
        # Add price information
        summary_parts.append(f"{symbol} is trading at {current_price} ({price_change:.2f}% change)")
        
        # Add sentiment
        sentiment_str = f"{sentiment['strength']} {sentiment['overall']}" if sentiment['strength'] != 'none' else 'neutral'
        summary_parts.append(f"Overall sentiment: {sentiment_str} (confidence: {sentiment['confidence']:.2f})")
        
        # Add key indicator insights
        if 'RSI_14' in indicator_results:
            rsi = indicator_results['RSI_14']
            rsi_value = rsi['value']
            if rsi_value > 70:
                summary_parts.append(f"RSI is overbought at {rsi_value:.2f}")
            elif rsi_value < 30:
                summary_parts.append(f"RSI is oversold at {rsi_value:.2f}")
        
        if any(k.startswith('MACD') for k in indicator_results):
            macd_key = next(k for k in indicator_results if k.startswith('MACD'))
            macd = indicator_results[macd_key]
            if macd['signal'] in ['bullish', 'strongly_bullish']:
                summary_parts.append("MACD shows bullish momentum")
            elif macd['signal'] in ['bearish', 'strongly_bearish']:
                summary_parts.append("MACD shows bearish momentum")
        
        if any(k.startswith('BBANDS') for k in indicator_results):
            bb_key = next(k for k in indicator_results if k.startswith('BBANDS'))
            bb = indicator_results[bb_key]
            if bb['signal'] == 'bullish':
                summary_parts.append("Price is near the lower Bollinger Band, suggesting potential oversold conditions")
            elif bb['signal'] == 'bearish':
                summary_parts.append("Price is near the upper Bollinger Band, suggesting potential overbought conditions")
        
        # Combine all parts
        return " ".join(summary_parts)
