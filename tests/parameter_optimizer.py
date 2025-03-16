import pandas as pd
import numpy as np
import itertools
import logging
from typing import Dict, List, Any, Tuple
import json
import os
from datetime import datetime

from analysis.engine import AnalysisEngine
from data.kucoin_client import KuCoinClient
from analysis.backtest import Backtester

class ParameterOptimizer:
    """
    Optimizes analysis parameters for accuracy
    """
    
    def __init__(self, kucoin_client: KuCoinClient):
        """
        Initialize the parameter optimizer
        
        Args:
            kucoin_client (KuCoinClient): KuCoin client for data retrieval
        """
        self.kucoin_client = kucoin_client
        self.logger = logging.getLogger(__name__)
        
    def optimize_rsi_parameters(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str,
        window_range: List[int] = None,
        overbought_range: List[int] = None,
        oversold_range: List[int] = None
    ) -> Dict[str, Any]:
        """
        Optimize RSI parameters
        
        Args:
            symbol (str): Symbol to optimize for
            start_date (str): Start date in format 'YYYY-MM-DD'
            end_date (str): End date in format 'YYYY-MM-DD'
            window_range (List[int], optional): Range of window values to test
            overbought_range (List[int], optional): Range of overbought values to test
            oversold_range (List[int], optional): Range of oversold values to test
            
        Returns:
            Dict[str, Any]: Optimization results
        """
        self.logger.info(f"Optimizing RSI parameters for {symbol}")
        
        # Set default parameter ranges if not provided
        window_range = window_range or [7, 9, 14, 21, 25]
        overbought_range = overbought_range or [65, 70, 75, 80]
        oversold_range = oversold_range or [20, 25, 30, 35]
        
        # Get historical data
        klines = self._get_historical_data(symbol, start_date, end_date)
        
        if not klines or len(klines) < 200:
            return {"error": "Insufficient historical data"}
        
        # Prepare parameter combinations
        param_combinations = list(itertools.product(
            window_range, 
            overbought_range, 
            oversold_range
        ))
        
        self.logger.info(f"Testing {len(param_combinations)} parameter combinations")
        
        # Test each parameter combination
        results = []
        
        for window, overbought, oversold in param_combinations:
            # Skip invalid combinations
            if oversold >= overbought:
                continue
                
            # Create analysis engine with custom RSI parameters
            config = {
                "rsi_window": window,
                "rsi_overbought": overbought,
                "rsi_oversold": oversold
            }
            
            analysis_engine = AnalysisEngine(config)
            backtester = Backtester(analysis_engine)
            
            # Run backtest
            backtest_result = backtester.run_backtest(
                symbol, 
                klines, 
                lookback_periods=window + 10,  # Add buffer for indicator calculation
                forward_periods=5  # Look 5 periods ahead for validation
            )
            
            # Store result
            if "error" not in backtest_result:
                results.append({
                    "window": window,
                    "overbought": overbought,
                    "oversold": oversold,
                    "accuracy": backtest_result["overall_accuracy"],
                    "periods_tested": backtest_result["periods_tested"]
                })
        
        # Find best parameters
        if results:
            best_result = max(results, key=lambda x: x["accuracy"])
            
            return {
                "symbol": symbol,
                "parameter": "RSI",
                "best_parameters": {
                    "window": best_result["window"],
                    "overbought": best_result["overbought"],
                    "oversold": best_result["oversold"]
                },
                "best_accuracy": best_result["accuracy"],
                "all_results": results
            }
        else:
            return {"error": "No valid results"}
    
    def optimize_macd_parameters(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str,
        fast_range: List[int] = None,
        slow_range: List[int] = None,
        signal_range: List[int] = None
    ) -> Dict[str, Any]:
        """
        Optimize MACD parameters
        
        Args:
            symbol (str): Symbol to optimize for
            start_date (str): Start date in format 'YYYY-MM-DD'
            end_date (str): End date in format 'YYYY-MM-DD'
            fast_range (List[int], optional): Range of fast EMA values to test
            slow_range (List[int], optional): Range of slow EMA values to test
            signal_range (List[int], optional): Range of signal EMA values to test
            
        Returns:
            Dict[str, Any]: Optimization results
        """
        self.logger.info(f"Optimizing MACD parameters for {symbol}")
        
        # Set default parameter ranges if not provided
        fast_range = fast_range or [8, 10, 12, 15]
        slow_range = slow_range or [21, 24, 26, 30]
        signal_range = signal_range or [7, 9, 10, 12]
        
        # Get historical data
        klines = self._get_historical_data(symbol, start_date, end_date)
        
        if not klines or len(klines) < 200:
            return {"error": "Insufficient historical data"}
        
        # Prepare parameter combinations
        param_combinations = list(itertools.product(
            fast_range, 
            slow_range, 
            signal_range
        ))
        
        self.logger.info(f"Testing {len(param_combinations)} parameter combinations")
        
        # Test each parameter combination
        results = []
        
        for fast, slow, signal in param_combinations:
            # Skip invalid combinations
            if fast >= slow:
                continue
                
            # Create analysis engine with custom MACD parameters
            config = {
                "macd_fast": fast,
                "macd_slow": slow,
                "macd_signal": signal
            }
            
            analysis_engine = AnalysisEngine(config)
            backtester = Backtester(analysis_engine)
            
            # Run backtest
            backtest_result = backtester.run_backtest(
                symbol, 
                klines, 
                lookback_periods=slow + 10,  # Add buffer for indicator calculation
                forward_periods=5  # Look 5 periods ahead for validation
            )
            
            # Store result
            if "error" not in backtest_result:
                results.append({
                    "fast": fast,
                    "slow": slow,
                    "signal": signal,
                    "accuracy": backtest_result["overall_accuracy"],
                    "periods_tested": backtest_result["periods_tested"]
                })
        
        # Find best parameters
        if results:
            best_result = max(results, key=lambda x: x["accuracy"])
            
            return {
                "symbol": symbol,
                "parameter": "MACD",
                "best_parameters": {
                    "fast": best_result["fast"],
                    "slow": best_result["slow"],
                    "signal": best_result["signal"]
                },
                "best_accuracy": best_result["accuracy"],
                "all_results": results
            }
        else:
            return {"error": "No valid results"}
    
    def optimize_bollinger_bands_parameters(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str,
        window_range: List[int] = None,
        std_dev_range: List[float] = None
    ) -> Dict[str, Any]:
        """
        Optimize Bollinger Bands parameters
        
        Args:
            symbol (str): Symbol to optimize for
            start_date (str): Start date in format 'YYYY-MM-DD'
            end_date (str): End date in format 'YYYY-MM-DD'
            window_range (List[int], optional): Range of window values to test
            std_dev_range (List[float], optional): Range of standard deviation values to test
            
        Returns:
            Dict[str, Any]: Optimization results
        """
        self.logger.info(f"Optimizing Bollinger Bands parameters for {symbol}")
        
        # Set default parameter ranges if not provided
        window_range = window_range or [10, 15, 20, 25, 30]
        std_dev_range = std_dev_range or [1.5, 2.0, 2.5, 3.0]
        
        # Get historical data
        klines = self._get_historical_data(symbol, start_date, end_date)
        
        if not klines or len(klines) < 200:
            return {"error": "Insufficient historical data"}
        
        # Prepare parameter combinations
        param_combinations = list(itertools.product(
            window_range, 
            std_dev_range
        ))
        
        self.logger.info(f"Testing {len(param_combinations)} parameter combinations")
        
        # Test each parameter combination
        results = []
        
        for window, std_dev in param_combinations:
            # Create analysis engine with custom Bollinger Bands parameters
            config = {
                "bbands_window": window,
                "bbands_std_dev": std_dev
            }
            
            analysis_engine = AnalysisEngine(config)
            backtester = Backtester(analysis_engine)
            
            # Run backtest
            backtest_result = backtester.run_backtest(
                symbol, 
                klines, 
                lookback_periods=window + 10,  # Add buffer for indicator calculation
                forward_periods=5  # Look 5 periods ahead for validation
            )
            
            # Store result
            if "error" not in backtest_result:
                results.append({
                    "window": window,
                    "std_dev": std_dev,
                    "accuracy": backtest_result["overall_accuracy"],
                    "periods_tested": backtest_result["periods_tested"]
                })
        
        # Find best parameters
        if results:
            best_result = max(results, key=lambda x: x["accuracy"])
            
            return {
                "symbol": symbol,
                "parameter": "Bollinger Bands",
                "best_parameters": {
                    "window": best_result["window"],
                    "std_dev": best_result["std_dev"]
                },
                "best_accuracy": best_result["accuracy"],
                "all_results": results
            }
        else:
            return {"error": "No valid results"}
    
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
            
            # Get klines data
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
        except Exception as e:
            self.logger.error(f"Error getting historical data: {str(e)}")
            return []
    
    def save_results(self, results: Dict[str, Any], filename: str) -> None:
        """
        Save optimization results to file
        
        Args:
            results (Dict[str, Any]): Optimization results
            filename (str): File to save results to
        """
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            self.logger.info(f"Results saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving results: {str(e)}")
