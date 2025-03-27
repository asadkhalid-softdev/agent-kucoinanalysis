import pandas as pd
import logging
from datetime import datetime

from analysis.indicators import (
    SimpleMovingAverage, ExponentialMovingAverage, RSI, 
    MACD, BollingerBands, OnBalanceVolume, StochasticOscillator,
    AverageDirectionalIndex, FibonacciRetracement, CandlestickPattern
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
        if 'CANDLESTICK' in analysis_list.get('indicators', []):
            indicators.append(CandlestickPattern())
        
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
                    self.logger.error(f"Error calculating {indicator.name} for {symbol}: {str(e)}", exc_info=True)
            
            # Analyze sentiment
            sentiment = self.sentiment_analyzer.analyze(indicator_signals)
            
            return {
                "symbol": symbol,
                "price": df['close'].iloc[-1],
                "volume": df['volume'].iloc[-1],
                "timestamp": datetime.now().isoformat(),
                "indicators": indicator_results,
                "sentiment": sentiment
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {str(e)}", exc_info=True)
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
        columns = ['timestamp', 'open', 'close', 'high', 'low', 'amount', 'volume']
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