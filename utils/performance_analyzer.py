import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

class PerformanceAnalyzer:
    """
    Analyzes application performance from logs
    """
    
    def __init__(self, log_file: str = "logs/performance.log"):
        """
        Initialize the performance analyzer
        
        Args:
            log_file (str): Path to the performance log file
        """
        self.log_file = log_file
        self.logger = logging.getLogger(__name__)
    
    def load_logs(self, days: int = 7) -> pd.DataFrame:
        """
        Load performance logs for analysis
        
        Args:
            days (int): Number of days of logs to load
            
        Returns:
            pd.DataFrame: DataFrame with performance data
        """
        self.logger.debug(f"Loading performance logs for the last {days} days")
        
        # Calculate start date
        start_date = datetime.now() - timedelta(days=days)
        
        # Initialize empty list for logs
        logs = []
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        # Extract JSON part from log line
                        json_start = line.find('{')
                        if json_start >= 0:
                            json_str = line[json_start:]
                            log_data = json.loads(json_str)
                            
                            # Parse timestamp
                            timestamp = datetime.fromisoformat(log_data["timestamp"])
                            
                            # Skip if before start date
                            if timestamp < start_date:
                                continue
                            # Add to logs
                            logs.append(log_data)
                    except (json.JSONDecodeError, ValueError, KeyError) as e:
                        self.logger.warning(f"Invalid log line: {str(e)}")
                        # Skip invalid lines
                        continue
        except FileNotFoundError:
            self.logger.warning(f"Performance log file not found: {self.log_file}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        if not logs:
            self.logger.warning("No valid logs found in the specified time period")
            return pd.DataFrame()
        
        df = pd.DataFrame(logs)
        
        # Parse timestamp
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        # Extract metadata columns
        if "metadata" in df.columns:
            # Explode metadata dictionary into separate columns
            metadata_df = pd.json_normalize(df["metadata"])
            
            # Add metadata columns to main DataFrame
            for col in metadata_df.columns:
                df[f"metadata_{col}"] = metadata_df[col]
        
        self.logger.info(f"Loaded {len(df)} performance log entries")
        return df
    
    def analyze_operation_performance(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Analyze performance by operation
        
        Args:
            df (pd.DataFrame, optional): DataFrame with performance data
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        self.logger.debug("Analyzing operation performance")
        
        if df is None:
            df = self.load_logs()
        
        if df.empty:
            self.logger.warning("No performance data available for analysis")
            return {"error": "No performance data available"}
        
        # Group by operation
        operation_stats = df.groupby("operation")["duration_ms"].agg([
            "count", "mean", "median", "min", "max", "std"
        ]).reset_index()
        
        # Calculate 95th percentile
        operation_stats["p95"] = df.groupby("operation")["duration_ms"].quantile(0.95).values
        
        # Sort by mean duration (descending)
        operation_stats = operation_stats.sort_values("mean", ascending=False)
        
        results = {
            "operation_stats": operation_stats.to_dict(orient="records"),
            "total_operations": len(df),
            "unique_operations": len(operation_stats),
            "slowest_operation": operation_stats.iloc[0]["operation"] if not operation_stats.empty else None,
            "fastest_operation": operation_stats.iloc[-1]["operation"] if not operation_stats.empty else None
        }
        
        self.logger.info(f"Performance analysis complete: {len(operation_stats)} unique operations analyzed")
        return results
    
    def analyze_time_trends(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Analyze performance trends over time
        
        Args:
            df (pd.DataFrame, optional): DataFrame with performance data
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        if df is None:
            df = self.load_logs()
        
        if df.empty:
            return {"error": "No performance data available"}
        
        # Set timestamp as index
        df = df.set_index("timestamp")
        
        # Resample by hour
        hourly_stats = df.resample("H")["duration_ms"].agg([
            "count", "mean", "median", "max"
        ]).reset_index()
        
        # Identify peak hours
        peak_hours = hourly_stats.sort_values("mean", ascending=False).head(3)
        
        return {
            "hourly_stats": hourly_stats.to_dict(orient="records"),
            "peak_hours": peak_hours.to_dict(orient="records"),
            "trend": "increasing" if hourly_stats["mean"].corr(hourly_stats.index) > 0.3 else "stable"
        }
    
    def analyze_errors(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Analyze errors in performance logs
        
        Args:
            df (pd.DataFrame, optional): DataFrame with performance data
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        if df is None:
            df = self.load_logs()
        
        if df.empty:
            return {"error": "No performance data available"}
        
        # Filter for operations with errors
        if "metadata_success" in df.columns:
            error_df = df[df["metadata_success"] == False]
            
            if error_df.empty:
                return {"error_count": 0, "error_rate": 0.0, "error_operations": []}
            
            # Group by operation
            error_stats = error_df.groupby("operation").size().reset_index(name="error_count")
            
            # Calculate error rate by operation
            total_by_op = df.groupby("operation").size().reset_index(name="total_count")
            error_stats = error_stats.merge(total_by_op, on="operation")
            error_stats["error_rate"] = error_stats["error_count"] / error_stats["total_count"]
            
            # Sort by error count (descending)
            error_stats = error_stats.sort_values("error_count", ascending=False)
            
            return {
                "error_count": len(error_df),
                "error_rate": len(error_df) / len(df),
                "error_operations": error_stats.to_dict(orient="records")
            }
        else:
            return {"error": "No error data available"}
    
    def generate_report(self, output_file: str = "performance_report.html") -> str:
        """
        Generate a comprehensive performance report
        
        Args:
            output_file (str): Path to save the report
            
        Returns:
            str: Path to the generated report
        """
        # Load data
        df = self.load_logs()
        
        if df.empty:
            return "No performance data available"
        
        # Run analyses
        operation_analysis = self.analyze_operation_performance(df)
        time_analysis = self.analyze_time_trends(df)
        error_analysis = self.analyze_errors(df)
        
        # Create plots
        self._create_plots(df, os.path.dirname(output_file))
        
        # Generate HTML report
        html = self._generate_html_report(
            df, 
            operation_analysis, 
            time_analysis, 
            error_analysis,
            os.path.dirname(output_file)
        )
        
        # Save report
        with open(output_file, 'w') as f:
            f.write(html)
        
        return output_file
    
    def _create_plots(self, df: pd.DataFrame, output_dir: str) -> None:
        """
        Create performance plots
        
        Args:
            df (pd.DataFrame): DataFrame with performance data
            output_dir (str): Directory to save plots
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Set style
        sns.set(style="whitegrid")
        
        # 1. Operation duration boxplot
        plt.figure(figsize=(12, 6))
        sns.boxplot(x="operation", y="duration_ms", data=df)
        plt.xticks(rotation=45, ha="right")
        plt.title("Operation Duration Distribution")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "operation_duration.png"))
        plt.close()
        
        # 2. Time trend line plot
        df_time = df.set_index("timestamp")
        hourly_mean = df_time.resample("H")["duration_ms"].mean()
        
        plt.figure(figsize=(12, 6))
        hourly_mean.plot()
        plt.title("Average Operation Duration Over Time")
        plt.ylabel("Duration (ms)")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "time_trend.png"))
        plt.close()
        
        # 3. Error rate by operation (if error data available)
        if "metadata_success" in df.columns:
            # Calculate error rate by operation
            error_rates = df.groupby("operation")["metadata_success"].agg(
                error_rate=lambda x: 1 - x.mean()
            ).reset_index()
            
            # Sort by error rate
            error_rates = error_rates.sort_values("error_rate", ascending=False)
            
            plt.figure(figsize=(12, 6))
            sns.barplot(x="operation", y="error_rate", data=error_rates)
            plt.xticks(rotation=45, ha="right")
            plt.title("Error Rate by Operation")
            plt.ylabel("Error Rate")
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, "error_rates.png"))
            plt.close()
    
    def _generate_html_report(
        self, 
        df: pd.DataFrame, 
        operation_analysis: Dict[str, Any],
        time_analysis: Dict[str, Any],
        error_analysis: Dict[str, Any],
        image_dir: str
    ) -> str:
        """
        Generate HTML report
        
        Args:
            df (pd.DataFrame): DataFrame with performance data
            operation_analysis (Dict[str, Any]): Operation performance analysis
            time_analysis (Dict[str, Any]): Time trend analysis
            error_analysis (Dict[str, Any]): Error analysis
            image_dir (str): Directory with plot images
            
        Returns:
            str: HTML report
        """
        # Create HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Performance Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .summary {{ background-color: #e6f7ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .chart {{ margin: 20px 0; max-width: 100%; }}
            </style>
        </head>
        <body>
            <h1>Performance Analysis Report</h1>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="summary">
                <h2>Summary</h2>
                <p>Total operations analyzed: {len(df)}</p>
                <p>Unique operations: {operation_analysis.get('unique_operations', 'N/A')}</p>
                <p>Slowest operation: {operation_analysis.get('slowest_operation', 'N/A')}</p>
                <p>Error rate: {error_analysis.get('error_rate', 0) * 100:.2f}%</p>
                <p>Performance trend: {time_analysis.get('trend', 'N/A')}</p>
            </div>
            
            <h2>Operation Performance</h2>
            <div class="chart">
                <img src="operation_duration.png" alt="Operation Duration Distribution" style="max-width: 100%;">
            </div>
            
            <table>
                <tr>
                    <th>Operation</th>
                    <th>Count</th>
                    <th>Mean (ms)</th>
                    <th>Median (ms)</th>
                    <th>Min (ms)</th>
                    <th>Max (ms)</th>
                    <th>P95 (ms)</th>
                </tr>
        """
        
        # Add operation stats rows
        for stat in operation_analysis.get('operation_stats', []):
            html += f"""
                <tr>
                    <td>{stat['operation']}</td>
                    <td>{stat['count']}</td>
                    <td>{stat['mean']:.2f}</td>
                    <td>{stat['median']:.2f}</td>
                    <td>{stat['min']:.2f}</td>
                    <td>{stat['max']:.2f}</td>
                    <td>{stat['p95']:.2f}</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h2>Performance Over Time</h2>
            <div class="chart">
                <img src="time_trend.png" alt="Performance Over Time" style="max-width: 100%;">
            </div>
            
            <h3>Peak Hours</h3>
            <table>
                <tr>
                    <th>Timestamp</th>
                    <th>Operation Count</th>
                    <th>Mean Duration (ms)</th>
                    <th>Max Duration (ms)</th>
                </tr>
        """
        
        # Add peak hours rows
        for peak in time_analysis.get('peak_hours', []):
            html += f"""
                <tr>
                    <td>{peak['timestamp']}</td>
                    <td>{peak['count']}</td>
                    <td>{peak['mean']:.2f}</td>
                    <td>{peak['max']:.2f}</td>
                </tr>
            """
        
        html += """
            </table>
        """
        
        # Add error section if available
        if error_analysis.get('error_count', 0) > 0:
            html += """
                <h2>Error Analysis</h2>
                <div class="chart">
                    <img src="error_rates.png" alt="Error Rates by Operation" style="max-width: 100%;">
                </div>
                
                <table>
                    <tr>
                        <th>Operation</th>
                        <th>Error Count</th>
                        <th>Total Count</th>
                        <th>Error Rate</th>
                    </tr>
            """
            
            # Add error stats rows
            for error in error_analysis.get('error_operations', []):
                html += f"""
                    <tr>
                        <td>{error['operation']}</td>
                        <td>{error['error_count']}</td>
                        <td>{error['total_count']}</td>
                        <td>{error['error_rate'] * 100:.2f}%</td>
                    </tr>
                """
            
            html += """
                </table>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html
