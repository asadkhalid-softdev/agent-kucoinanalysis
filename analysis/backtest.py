import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import logging

class Backtester:
    """
    Backtesting system to validate analysis accuracy.
    """
    
    def __init__(self, analysis_engine):
        """
        Initialize the backtester.
        
        Args:
            analysis_engine (AnalysisEngine): The analysis engine to test
        """
        self.analysis_engine = analysis_engine
        self.logger = logging.getLogger(__name__)
    
    def run_backtest(self, symbol, klines_data, lookback_periods=30, forward_periods=5):
        """
        Run a backtest on historical data.
        
        Args:
            symbol (str): Trading pair symbol
            klines_data (list): Historical candlestick data
            lookback_periods (int): Number of periods to look back for each test
            forward_periods (int): Number of periods to look forward for result validation
            
        Returns:
            dict: Backtest results including accuracy metrics
        """
        self.logger.info(f"Starting backtest for {symbol} with {lookback_periods} lookback and {forward_periods} forward periods")
        
        try:
            # Convert to DataFrame for easier manipulation
            df = self.analysis_engine._prepare_dataframe(klines_data)
            
            if len(df) < lookback_periods + forward_periods:
                self.logger.warning(f"Insufficient data for backtest: need {lookback_periods + forward_periods}, got {len(df)}")
                return {
                    "symbol": symbol,
                    "error": "Insufficient data for backtest",
                    "accuracy": 0.0
                }
            
            # Initialize results
            results = []
            
            # Run analysis on historical windows
            for i in range(len(df) - lookback_periods - forward_periods):
                # Get data window
                window = df.iloc[i:i+lookback_periods].copy()
                
                try:
                    # Run analysis on window
                    analysis = self.analysis_engine.analyze_symbol(symbol, window.values.tolist())
                    
                    # Get forward window for validation
                    forward_window = df.iloc[i+lookback_periods:i+lookback_periods+forward_periods]
                    
                    # Calculate price change in forward window
                    start_price = forward_window['close'].iloc[0]
                    end_price = forward_window['close'].iloc[-1]
                    price_change_pct = (end_price - start_price) / start_price * 100
                    
                    # Determine if analysis was correct
                    sentiment = analysis['sentiment']['overall']
                    strength = analysis['sentiment']['strength']
                    
                    if sentiment == 'buy' and price_change_pct > 0:
                        correct = True
                    elif sentiment == 'sell' and price_change_pct < 0:
                        correct = True
                    elif sentiment == 'neutral' and abs(price_change_pct) < 1.0:  # 1% threshold for neutral
                        correct = True
                    else:
                        correct = False
                    
                    results.append({
                        'timestamp': window.index[-1],
                        'sentiment': sentiment,
                        'strength': strength,
                        'price_change_pct': price_change_pct,
                        'correct': correct
                    })
                except Exception as e:
                    self.logger.error(f"Error analyzing window {i}: {str(e)}", exc_info=True)
                    continue
            
            if not results:
                self.logger.warning("No valid results from backtest")
                return {
                    "symbol": symbol,
                    "error": "No valid results from backtest",
                    "accuracy": 0.0
                }
            
            # Calculate accuracy metrics
            total_tests = len(results)
            correct_tests = sum(1 for r in results if r['correct'])
            accuracy = correct_tests / total_tests if total_tests > 0 else 0.0
            
            return {
                "symbol": symbol,
                "accuracy": accuracy,
                "total_tests": total_tests,
                "correct_tests": correct_tests,
                "results": results
            }
            
        except Exception as e:
            self.logger.error(f"Error running backtest: {str(e)}", exc_info=True)
            return {
                "symbol": symbol,
                "error": str(e),
                "accuracy": 0.0
            }
    
    def generate_report(self, backtest_results, output_file=None):
        """
        Generate a detailed report of backtest results.
        
        Args:
            backtest_results (dict): Results from run_backtest
            output_file (str, optional): File to save report to
            
        Returns:
            str: Generated report
        """
        if "error" in backtest_results:
            return f"Error in backtest: {backtest_results['error']}"
        
        report = []
        report.append(f"Backtest Report for {backtest_results['symbol']}")
        report.append("=" * 50)
        report.append(f"Total Tests: {backtest_results['total_tests']}")
        report.append(f"Correct Predictions: {backtest_results['correct_tests']}")
        report.append(f"Accuracy: {backtest_results['accuracy']:.2%}")
        report.append("\nDetailed Results:")
        report.append("-" * 50)
        
        for result in backtest_results['results']:
            report.append(f"Timestamp: {result['timestamp']}")
            report.append(f"Sentiment: {result['sentiment']} ({result['strength']})")
            report.append(f"Price Change: {result['price_change_pct']:.2f}%")
            report.append(f"Correct: {'Yes' if result['correct'] else 'No'}")
            report.append("-" * 30)
        
        report_text = "\n".join(report)
        
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(report_text)
                self.logger.info(f"Report saved to {output_file}")
            except Exception as e:
                self.logger.error(f"Error saving report: {str(e)}", exc_info=True)
        
        return report_text
    
    def plot_results(self, backtest_results, output_file=None):
        """
        Generate a plot of backtest results.
        
        Args:
            backtest_results (dict): Results from run_backtest
            output_file (str, optional): File to save plot to
        """
        if "error" in backtest_results:
            self.logger.error(f"Cannot plot results: {backtest_results['error']}")
            return
        
        try:
            # Create figure with subplots
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            # Plot price changes
            timestamps = [r['timestamp'] for r in backtest_results['results']]
            price_changes = [r['price_change_pct'] for r in backtest_results['results']]
            
            ax1.plot(timestamps, price_changes, 'b-', label='Price Change %')
            ax1.set_title('Price Changes Over Time')
            ax1.set_xlabel('Time')
            ax1.set_ylabel('Price Change %')
            ax1.grid(True)
            ax1.legend()
            
            # Format x-axis dates
            ax1.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d %H:%M'))
            
            # Plot accuracy
            cumulative_correct = np.cumsum([1 if r['correct'] else 0 for r in backtest_results['results']])
            total_tests = range(1, len(backtest_results['results']) + 1)
            accuracy = [correct/total for correct, total in zip(cumulative_correct, total_tests)]
            
            ax2.plot(timestamps, accuracy, 'g-', label='Cumulative Accuracy')
            ax2.set_title('Cumulative Accuracy Over Time')
            ax2.set_xlabel('Time')
            ax2.set_ylabel('Accuracy')
            ax2.grid(True)
            ax2.legend()
            
            # Format x-axis dates
            ax2.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d %H:%M'))
            
            # Adjust layout
            plt.tight_layout()
            
            if output_file:
                plt.savefig(output_file)
                self.logger.info(f"Plot saved to {output_file}")
            else:
                plt.show()
            
            plt.close()
            
        except Exception as e:
            self.logger.error(f"Error plotting results: {str(e)}", exc_info=True)
