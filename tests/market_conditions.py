import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import matplotlib.pyplot as plt
from typing import Dict, List, Any

from analysis.engine import AnalysisEngine
from data.kucoin_client import KuCoinClient

class MarketConditionTester:
    """
    Tests the analysis engine under various market conditions
    """
    
    def __init__(self, analysis_engine: AnalysisEngine, kucoin_client: KuCoinClient = None):
        """
        Initialize the market condition tester
        
        Args:
            analysis_engine (AnalysisEngine): The analysis engine to test
            kucoin_client (KuCoinClient, optional): KuCoin client for data retrieval
        """
        self.analysis_engine = analysis_engine
        self.kucoin_client = kucoin_client
        self.logger = logging.getLogger(__name__)
        
    def test_bull_market(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Test the analysis engine on a bull market period
        
        Args:
            symbol (str): Symbol to test
            start_date (str): Start date in format 'YYYY-MM-DD'
            end_date (str): End date in format 'YYYY-MM-DD'
            
        Returns:
            Dict[str, Any]: Test results
        """
        self.logger.info(f"Testing bull market for {symbol} from {start_date} to {end_date}")
        
        # Get historical data for the specified period
        klines = self._get_historical_data(symbol, start_date, end_date)
        
        if not klines:
            return {"error": "Failed to retrieve historical data"}
        
        # Run analysis
        analysis_results = self._run_analysis_on_period(symbol, klines)
        
        # Evaluate results
        evaluation = self._evaluate_results(analysis_results, "bull")
        
        return {
            "symbol": symbol,
            "market_condition": "bull",
            "period": f"{start_date} to {end_date}",
            "analysis_count": len(analysis_results),
            "evaluation": evaluation
        }
    
    def test_bear_market(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Test the analysis engine on a bear market period
        
        Args:
            symbol (str): Symbol to test
            start_date (str): Start date in format 'YYYY-MM-DD'
            end_date (str): End date in format 'YYYY-MM-DD'
            
        Returns:
            Dict[str, Any]: Test results
        """
        self.logger.info(f"Testing bear market for {symbol} from {start_date} to {end_date}")
        
        # Get historical data for the specified period
        klines = self._get_historical_data(symbol, start_date, end_date)
        
        if not klines:
            return {"error": "Failed to retrieve historical data"}
        
        # Run analysis
        analysis_results = self._run_analysis_on_period(symbol, klines)
        
        # Evaluate results
        evaluation = self._evaluate_results(analysis_results, "bear")
        
        return {
            "symbol": symbol,
            "market_condition": "bear",
            "period": f"{start_date} to {end_date}",
            "analysis_count": len(analysis_results),
            "evaluation": evaluation
        }
    
    def test_sideways_market(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Test the analysis engine on a sideways/ranging market period
        
        Args:
            symbol (str): Symbol to test
            start_date (str): Start date in format 'YYYY-MM-DD'
            end_date (str): End date in format 'YYYY-MM-DD'
            
        Returns:
            Dict[str, Any]: Test results
        """
        self.logger.info(f"Testing sideways market for {symbol} from {start_date} to {end_date}")
        
        # Get historical data for the specified period
        klines = self._get_historical_data(symbol, start_date, end_date)
        
        if not klines:
            return {"error": "Failed to retrieve historical data"}
        
        # Run analysis
        analysis_results = self._run_analysis_on_period(symbol, klines)
        
        # Evaluate results
        evaluation = self._evaluate_results(analysis_results, "sideways")
        
        return {
            "symbol": symbol,
            "market_condition": "sideways",
            "period": f"{start_date} to {end_date}",
            "analysis_count": len(analysis_results),
            "evaluation": evaluation
        }
    
    def test_high_volatility(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Test the analysis engine during high volatility periods
        
        Args:
            symbol (str): Symbol to test
            start_date (str): Start date in format 'YYYY-MM-DD'
            end_date (str): End date in format 'YYYY-MM-DD'
            
        Returns:
            Dict[str, Any]: Test results
        """
        self.logger.info(f"Testing high volatility for {symbol} from {start_date} to {end_date}")
        
        # Get historical data for the specified period
        klines = self._get_historical_data(symbol, start_date, end_date)
        
        if not klines:
            return {"error": "Failed to retrieve historical data"}
        
        # Run analysis
        analysis_results = self._run_analysis_on_period(symbol, klines)
        
        # Evaluate results
        evaluation = self._evaluate_results(analysis_results, "volatile")
        
        return {
            "symbol": symbol,
            "market_condition": "high_volatility",
            "period": f"{start_date} to {end_date}",
            "analysis_count": len(analysis_results),
            "evaluation": evaluation
        }
    
    def _get_historical_data(self, symbol: str, start_date: str, end_date: str) -> List[List]:
        """
        Get historical klines data for a period
        
        Args:
            symbol (str): Symbol to get data for
            start_date (str): Start date in format 'YYYY-MM-DD'
            end_date (str): End date in format 'YYYY-MM-DD'
            
        Returns:
            List[List]: Klines data
        """
        try:
            # Convert dates to timestamps
            start_timestamp = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
            end_timestamp = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
            
            if self.kucoin_client:
                # Use KuCoin client to get data
                klines = self.kucoin_client.get_klines(
                    symbol=symbol,
                    kline_type="1hour",
                    start_time=start_timestamp,
                    end_time=end_timestamp
                )
                
                if "data" in klines:
                    return klines["data"]
                else:
                    self.logger.error(f"Failed to get klines data: {klines}")
                    return []
            else:
                # Use sample data for testing without KuCoin client
                self.logger.warning("No KuCoin client provided, using sample data")
                return self._generate_sample_data(start_timestamp, end_timestamp)
        except Exception as e:
            self.logger.error(f"Error getting historical data: {str(e)}")
            return []
    
    def _generate_sample_data(self, start_timestamp: int, end_timestamp: int) -> List[List]:
        """
        Generate sample klines data for testing
        
        Args:
            start_timestamp (int): Start timestamp
            end_timestamp (int): End timestamp
            
        Returns:
            List[List]: Sample klines data
        """
        # Generate hourly timestamps
        timestamps = list(range(start_timestamp, end_timestamp, 3600))
        
        # Generate sample data
        sample_data = []
        base_price = 10000.0
        
        for i, timestamp in enumerate(timestamps):
            # Generate random price movement
            price_change = np.random.normal(0, 100)
            price = max(1, base_price + price_change)
            base_price = price
            
            # Create kline [timestamp, open, close, high, low, volume]
            open_price = price
            close_price = price + np.random.normal(0, 20)
            high_price = max(open_price, close_price) + abs(np.random.normal(0, 10))
            low_price = min(open_price, close_price) - abs(np.random.normal(0, 10))
            volume = abs(np.random.normal(100, 50))
            
            kline = [timestamp, open_price, close_price, high_price, low_price, volume]
            sample_data.append(kline)
        
        return sample_data
    
    def _run_analysis_on_period(self, symbol: str, klines: List[List]) -> List[Dict[str, Any]]:
        """
        Run analysis on a series of klines using sliding window
        
        Args:
            symbol (str): Symbol being analyzed
            klines (List[List]): Klines data
            
        Returns:
            List[Dict[str, Any]]: Analysis results
        """
        analysis_results = []
        window_size = 200  # Number of candles needed for analysis
        
        if len(klines) < window_size:
            self.logger.warning(f"Not enough data points for analysis, need {window_size}, got {len(klines)}")
            return []
        
        # Use sliding window to analyze the period
        for i in range(len(klines) - window_size):
            window = klines[i:i+window_size]
            
            try:
                # Run analysis on this window
                analysis = self.analysis_engine.analyze_symbol(symbol, window)
                analysis_results.append(analysis)
            except Exception as e:
                self.logger.error(f"Error analyzing window {i}: {str(e)}")
        
        return analysis_results
    
    def _evaluate_results(self, analysis_results: List[Dict[str, Any]], market_type: str) -> Dict[str, Any]:
        """
        Evaluate analysis results for a specific market condition
        
        Args:
            analysis_results (List[Dict[str, Any]]): Analysis results
            market_type (str): Type of market (bull, bear, sideways, volatile)
            
        Returns:
            Dict[str, Any]: Evaluation metrics
        """
        if not analysis_results:
            return {"error": "No analysis results to evaluate"}
        
        # Count sentiment types
        sentiment_counts = {"buy": 0, "sell": 0, "neutral": 0}
        strength_counts = {"strong": 0, "moderate": 0, "weak": 0, "none": 0}
        confidence_values = []
        
        for result in analysis_results:
            if "sentiment" in result:
                sentiment = result["sentiment"]["overall"]
                strength = result["sentiment"]["strength"]
                confidence = result["sentiment"]["confidence"]
                
                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
                strength_counts[strength] = strength_counts.get(strength, 0) + 1
                confidence_values.append(confidence)
        
        # Calculate metrics
        total_analyses = len(analysis_results)
        sentiment_distribution = {k: v / total_analyses for k, v in sentiment_counts.items()}
        strength_distribution = {k: v / total_analyses for k, v in strength_counts.items()}
        avg_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0
        
        # Evaluate appropriateness for market type
        appropriateness_score = self._calculate_appropriateness(
            sentiment_distribution, 
            strength_distribution, 
            market_type
        )
        
        return {
            "sentiment_distribution": sentiment_distribution,
            "strength_distribution": strength_distribution,
            "average_confidence": avg_confidence,
            "appropriateness_score": appropriateness_score,
            "total_analyses": total_analyses
        }
    
    def _calculate_appropriateness(
        self, 
        sentiment_distribution: Dict[str, float], 
        strength_distribution: Dict[str, float], 
        market_type: str
    ) -> float:
        """
        Calculate how appropriate the analysis results are for the market type
        
        Args:
            sentiment_distribution (Dict[str, float]): Distribution of sentiments
            strength_distribution (Dict[str, float]): Distribution of strengths
            market_type (str): Type of market
            
        Returns:
            float: Appropriateness score (0-1)
        """
        # Define expected distributions for different market types
        if market_type == "bull":
            # In bull markets, expect more buy signals
            expected_sentiment = {"buy": 0.7, "neutral": 0.2, "sell": 0.1}
        elif market_type == "bear":
            # In bear markets, expect more sell signals
            expected_sentiment = {"buy": 0.1, "neutral": 0.2, "sell": 0.7}
        elif market_type == "sideways":
            # In sideways markets, expect more neutral signals
            expected_sentiment = {"buy": 0.3, "neutral": 0.4, "sell": 0.3}
        elif market_type == "volatile":
            # In volatile markets, expect mix of strong signals
            expected_sentiment = {"buy": 0.4, "neutral": 0.2, "sell": 0.4}
        else:
            # Default balanced expectation
            expected_sentiment = {"buy": 0.33, "neutral": 0.34, "sell": 0.33}
        
        # Calculate difference from expected distribution
        sentiment_diff = sum(
            abs(sentiment_distribution.get(k, 0) - v) 
            for k, v in expected_sentiment.items()
        ) / 2  # Divide by 2 because sum of absolute differences is in [0, 2]
        
        # Convert difference to similarity score (0-1)
        appropriateness_score = 1 - sentiment_diff
        
        return appropriateness_score
    
    def plot_results(self, results: Dict[str, Any], output_file: str = None):
        """
        Plot test results
        
        Args:
            results (Dict[str, Any]): Test results
            output_file (str, optional): Path to save the plot
        """
        if "evaluation" not in results or "error" in results["evaluation"]:
            self.logger.error("Cannot plot results: Invalid results data")
            return
        
        evaluation = results["evaluation"]
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        # Plot sentiment distribution
        sentiment_labels = list(evaluation["sentiment_distribution"].keys())
        sentiment_values = list(evaluation["sentiment_distribution"].values())
        ax1.bar(sentiment_labels, sentiment_values, color=['green', 'gray', 'red'])
        ax1.set_title('Sentiment Distribution')
        ax1.set_ylabel('Proportion')
        ax1.set_ylim(0, 1)
        
        # Plot strength distribution
        strength_labels = list(evaluation["strength_distribution"].keys())
        strength_values = list(evaluation["strength_distribution"].values())
        ax2.bar(strength_labels, strength_values, color=['darkblue', 'blue', 'lightblue', 'gray'])
        ax2.set_title('Signal Strength Distribution')
        ax2.set_ylabel('Proportion')
        ax2.set_ylim(0, 1)
        
        # Add overall metrics as text
        fig.text(
            0.5, 0.01, 
            f"Symbol: {results['symbol']} | Market: {results['market_condition']} | "
            f"Period: {results['period']}\n"
            f"Appropriateness Score: {evaluation['appropriateness_score']:.2f} | "
            f"Avg Confidence: {evaluation['average_confidence']:.2f} | "
            f"Total Analyses: {evaluation['total_analyses']}",
            ha='center', fontsize=12
        )
        
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        
        if output_file:
            plt.savefig(output_file)
            plt.close()
        else:
            plt.show()
