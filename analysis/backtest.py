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
        try:
            # Convert to DataFrame for easier manipulation
            df = self.analysis_engine._prepare_dataframe(klines_data)
            
            if len(df) < lookback_periods + forward_periods:
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
                
                # Store result
                results.append({
                    'timestamp': window['timestamp'].iloc[-1],
                    'sentiment': sentiment,
                    'strength': strength,
                    'price_change_pct': price_change_pct,
                    'correct': correct
                })
            
            # Calculate accuracy metrics
            results_df = pd.DataFrame(results)
            
            if len(results_df) == 0:
                return {
                    "symbol": symbol,
                    "error": "No valid backtest periods",
                    "accuracy": 0.0
                }
            
            overall_accuracy = results_df['correct'].mean()
            
            # Calculate accuracy by sentiment
            sentiment_accuracy = {}
            for sentiment in results_df['sentiment'].unique():
                sentiment_df = results_df[results_df['sentiment'] == sentiment]
                sentiment_accuracy[sentiment] = {
                    'count': len(sentiment_df),
                    'accuracy': sentiment_df['correct'].mean() if len(sentiment_df) > 0 else 0.0
                }
            
            # Calculate accuracy by strength
            strength_accuracy = {}
            for strength in results_df['strength'].unique():
                strength_df = results_df[results_df['strength'] == strength]
                strength_accuracy[strength] = {
                    'count': len(strength_df),
                    'accuracy': strength_df['correct'].mean() if len(strength_df) > 0 else 0.0
                }
            
            return {
                "symbol": symbol,
                "periods_tested": len(results_df),
                "overall_accuracy": overall_accuracy,
                "sentiment_accuracy": sentiment_accuracy,
                "strength_accuracy": strength_accuracy,
                "detailed_results": results
            }
            
        except Exception as e:
            self.logger.error(f"Error in backtest for {symbol}: {str(e)}")
            return {
                "symbol": symbol,
                "error": str(e),
                "accuracy": 0.0
            }
    
    def generate_report(self, backtest_results, output_file=None):
        """
        Generate a detailed backtest report.
        
        Args:
            backtest_results (dict): Results from run_backtest
            output_file (str, optional): Path to save the report
            
        Returns:
            str: Report text
        """
        if 'error' in backtest_results:
            return f"Backtest Error: {backtest_results['error']}"
        
        symbol = backtest_results['symbol']
        overall_accuracy = backtest_results['overall_accuracy']
        periods_tested = backtest_results['periods_tested']
        
        report = [
            f"Backtest Report for {symbol}",
            f"Periods Tested: {periods_tested}",
            f"Overall Accuracy: {overall_accuracy:.2%}",
            "\nAccuracy by Sentiment:",
        ]
        
        for sentiment, data in backtest_results['sentiment_accuracy'].items():
            report.append(f"  {sentiment}: {data['accuracy']:.2%} ({data['count']} signals)")
        
        report.append("\nAccuracy by Strength:")
        for strength, data in backtest_results['strength_accuracy'].items():
            report.append(f"  {strength}: {data['accuracy']:.2%} ({data['count']} signals)")
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
        
        return report_text
    
    def plot_results(self, backtest_results, output_file=None):
        """
        Generate a plot of backtest results.
        
        Args:
            backtest_results (dict): Results from run_backtest
            output_file (str, optional): Path to save the plot
        """
        if 'error' in backtest_results or 'detailed_results' not in backtest_results:
            return
        
        results = backtest_results['detailed_results']
        results_df = pd.DataFrame(results)
        
        if len(results_df) == 0:
            return
        
        # Convert timestamp to datetime if it's not already
        if not isinstance(results_df['timestamp'].iloc[0], datetime):
            results_df['timestamp'] = pd.to_datetime(results_df['timestamp'])
        
        # Create figure and axis
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        # Plot price change
        ax1.plot(results_df['timestamp'], results_df['price_change_pct'], label='Price Change %')
        ax1.axhline(y=0, color='r', linestyle='-', alpha=0.3)
        ax1.set_ylabel('Price Change %')
        ax1.set_title(f'Backtest Results for {backtest_results["symbol"]}')
        ax1.legend()
        
        # Plot sentiment
        sentiment_map = {'buy': 1, 'neutral': 0, 'sell': -1}
        results_df['sentiment_value'] = results_df['sentiment'].map(sentiment_map)
        
        # Color points by correctness
        correct_points = results_df[results_df['correct']]
        incorrect_points = results_df[~results_df['correct']]
        
        ax2.scatter(correct_points['timestamp'], correct_points['sentiment_value'], 
                   color='green', label='Correct', alpha=0.7)
        ax2.scatter(incorrect_points['timestamp'], incorrect_points['sentiment_value'], 
                   color='red', label='Incorrect', alpha=0.7)
        
        ax2.set_yticks([-1, 0, 1])
        ax2.set_yticklabels(['Sell', 'Neutral', 'Buy'])
        ax2.set_ylabel('Sentiment')
        ax2.set_xlabel('Date')
        ax2.legend()
        
        # Format x-axis
        date_form = DateFormatter("%Y-%m-%d")
        ax2.xaxis.set_major_formatter(date_form)
        fig.autofmt_xdate()
        
        # Add accuracy text
        accuracy_text = f"Overall Accuracy: {backtest_results['overall_accuracy']:.2%}"
        fig.text(0.02, 0.02, accuracy_text, fontsize=12)
        
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file)
            plt.close()
        else:
            plt.show()
