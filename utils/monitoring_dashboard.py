import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
import os
import json
from datetime import datetime, timedelta
import psutil
import time
import threading
import logging

# Initialize logger
logger = logging.getLogger(__name__)

class SystemMetrics:
    """Collects system metrics for monitoring"""
    
    def __init__(self, history_size=100):
        """
        Initialize the system metrics collector
        
        Args:
            history_size (int): Number of data points to keep in history
        """
        self.history_size = history_size
        self.metrics_history = []
        self.lock = threading.Lock()
        self.running = False
        self.collection_thread = None
    
    def start_collection(self, interval=5):
        """
        Start collecting metrics at regular intervals
        
        Args:
            interval (int): Collection interval in seconds
        """
        if self.running:
            return
        
        self.running = True
        self.collection_thread = threading.Thread(
            target=self._collect_metrics_loop,
            args=(interval,),
            daemon=True
        )
        self.collection_thread.start()
    
    def stop_collection(self):
        """Stop collecting metrics"""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=1)
    
    def _collect_metrics_loop(self, interval):
        """
        Continuously collect metrics at specified interval
        
        Args:
            interval (int): Collection interval in seconds
        """
        while self.running:
            try:
                self.collect_current_metrics()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error collecting metrics: {str(e)}")
    
    def collect_current_metrics(self):
        """Collect current system metrics"""
        try:
            # Get CPU, memory, and disk usage
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get network I/O stats
            net_io = psutil.net_io_counters()
            
            # Get process info
            process = psutil.Process(os.getpid())
            process_memory = process.memory_info().rss / (1024 * 1024)  # MB
            process_cpu = process.cpu_percent()
            
            # Create metrics record
            metrics = {
                'timestamp': datetime.now(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used_gb': memory.used / (1024**3),
                    'memory_total_gb': memory.total / (1024**3),
                    'disk_percent': disk.percent,
                    'disk_used_gb': disk.used / (1024**3),
                    'disk_total_gb': disk.total / (1024**3),
                    'net_sent_mb': net_io.bytes_sent / (1024**2),
                    'net_recv_mb': net_io.bytes_recv / (1024**2)
                },
                'process': {
                    'memory_mb': process_memory,
                    'cpu_percent': process_cpu
                }
            }
            
            # Add to history with thread safety
            with self.lock:
                self.metrics_history.append(metrics)
                # Trim history if needed
                if len(self.metrics_history) > self.history_size:
                    self.metrics_history = self.metrics_history[-self.history_size:]
        
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}")
    
    def get_metrics_history(self):
        """
        Get the metrics history
        
        Returns:
            list: List of metrics records
        """
        with self.lock:
            return self.metrics_history.copy()

class PerformanceMetrics:
    """Analyzes application performance metrics from logs"""
    
    def __init__(self, log_file="logs/kucoin_analysis_bot_performance.log"):
        """
        Initialize the performance metrics analyzer
        
        Args:
            log_file (str): Path to performance log file
        """
        self.log_file = log_file
    
    def get_recent_metrics(self, hours=24):
        """
        Get recent performance metrics
        
        Args:
            hours (int): Number of hours of data to retrieve
            
        Returns:
            pd.DataFrame: DataFrame with performance metrics
        """
        try:
            # Calculate start time
            start_time = datetime.now() - timedelta(hours=hours)
            
            # Read log file
            logs = []
            
            if not os.path.exists(self.log_file):
                return pd.DataFrame()
            
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
                            
                            # Skip if before start time
                            if timestamp < start_time:
                                continue
                            
                            # Add to logs
                            logs.append(log_data)
                    except (json.JSONDecodeError, ValueError, KeyError):
                        # Skip invalid lines
                        continue
            
            # Convert to DataFrame
            if not logs:
                return pd.DataFrame()
            
            df = pd.DataFrame(logs)
            
            # Parse timestamp
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            
            return df
        
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return pd.DataFrame()
    
    def get_operation_stats(self, df=None, hours=24):
        """
        Get operation statistics
        
        Args:
            df (pd.DataFrame, optional): DataFrame with performance data
            hours (int): Number of hours of data to retrieve
            
        Returns:
            dict: Operation statistics
        """
        if df is None:
            df = self.get_recent_metrics(hours)
        
        if df.empty:
            return {}
        
        # Group by operation
        operation_stats = df.groupby("operation")["duration_ms"].agg([
            "count", "mean", "median", "min", "max"
        ]).reset_index()
        
        # Sort by mean duration (descending)
        operation_stats = operation_stats.sort_values("mean", ascending=False)
        
        return operation_stats.to_dict(orient="records")
    
    def get_time_series_data(self, df=None, hours=24, interval='1h'):
        """
        Get time series data for performance metrics
        
        Args:
            df (pd.DataFrame, optional): DataFrame with performance data
            hours (int): Number of hours of data to retrieve
            interval (str): Resampling interval
            
        Returns:
            dict: Time series data
        """
        if df is None:
            df = self.get_recent_metrics(hours)
        
        if df.empty:
            return {}
        
        # Set timestamp as index
        df = df.set_index("timestamp")
        
        # Resample by interval
        resampled = df.resample(interval)["duration_ms"].agg([
            "count", "mean", "max"
        ]).reset_index()
        
        # Convert to dict
        return {
            "timestamps": resampled["timestamp"].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
            "counts": resampled["count"].tolist(),
            "mean_durations": resampled["mean"].tolist(),
            "max_durations": resampled["max"].tolist()
        }

# Initialize the dashboard app
app = dash.Dash(__name__, title="KuCoin Analysis Bot - Monitoring Dashboard")

# Initialize metrics collectors
system_metrics = SystemMetrics()
performance_metrics = PerformanceMetrics()

# Start collecting system metrics
system_metrics.start_collection(interval=5)

# Define the dashboard layout
app.layout = html.Div([
    html.H1("KuCoin Analysis Bot - Monitoring Dashboard"),
    
    html.Div([
        html.H2("System Health"),
        
        html.Div([
            html.Div([
                html.H3("CPU Usage"),
                dcc.Graph(id='cpu-graph')
            ], className='graph-container'),
            
            html.Div([
                html.H3("Memory Usage"),
                dcc.Graph(id='memory-graph')
            ], className='graph-container'),
            
            html.Div([
                html.H3("Disk Usage"),
                dcc.Graph(id='disk-graph')
            ], className='graph-container'),
            
            html.Div([
                html.H3("Process Resources"),
                dcc.Graph(id='process-graph')
            ], className='graph-container')
        ], className='graph-row')
    ], className='section'),
    
    html.Div([
        html.H2("Performance Metrics"),
        
        html.Div([
            html.Div([
                html.H3("Operation Durations"),
                dcc.Graph(id='operations-graph')
            ], className='graph-container'),
            
            html.Div([
                html.H3("Request Counts"),
                dcc.Graph(id='requests-graph')
            ], className='graph-container')
        ], className='graph-row')
    ], className='section'),
    
    # Refresh interval
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # in milliseconds (5 seconds)
        n_intervals=0
    )
], className='dashboard')

# Define callback to update CPU graph
@app.callback(
    Output('cpu-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_cpu_graph(n):
    metrics_history = system_metrics.get_metrics_history()
    
    if not metrics_history:
        return go.Figure()
    
    timestamps = [m['timestamp'] for m in metrics_history]
    cpu_values = [m['system']['cpu_percent'] for m in metrics_history]
    
    return {
        'data': [
            go.Scatter(
                x=timestamps,
                y=cpu_values,
                name='CPU Usage',
                fill='tozeroy',
                line=dict(color='#1f77b4')
            )
        ],
        'layout': go.Layout(
            xaxis=dict(title='Time'),
            yaxis=dict(title='CPU Usage (%)', range=[0, 100]),
            margin=dict(l=40, r=20, t=10, b=30),
            height=250
        )
    }

# Define callback to update memory graph
@app.callback(
    Output('memory-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_memory_graph(n):
    metrics_history = system_metrics.get_metrics_history()
    
    if not metrics_history:
        return go.Figure()
    
    timestamps = [m['timestamp'] for m in metrics_history]
    memory_values = [m['system']['memory_percent'] for m in metrics_history]
    
    return {
        'data': [
            go.Scatter(
                x=timestamps,
                y=memory_values,
                name='Memory Usage',
                fill='tozeroy',
                line=dict(color='#ff7f0e')
            )
        ],
        'layout': go.Layout(
            xaxis=dict(title='Time'),
            yaxis=dict(title='Memory Usage (%)', range=[0, 100]),
            margin=dict(l=40, r=20, t=10, b=30),
            height=250
        )
    }

# Define callback to update disk graph
@app.callback(
    Output('disk-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_disk_graph(n):
    metrics_history = system_metrics.get_metrics_history()
    
    if not metrics_history:
        return go.Figure()
    
    timestamps = [m['timestamp'] for m in metrics_history]
    disk_values = [m['system']['disk_percent'] for m in metrics_history]
    
    return {
        'data': [
            go.Scatter(
                x=timestamps,
                y=disk_values,
                name='Disk Usage',
                fill='tozeroy',
                line=dict(color='#2ca02c')
            )
        ],
        'layout': go.Layout(
            xaxis=dict(title='Time'),
            yaxis=dict(title='Disk Usage (%)', range=[0, 100]),
            margin=dict(l=40, r=20, t=10, b=30),
            height=250
        )
    }

# Define callback to update process graph
@app.callback(
    Output('process-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_process_graph(n):
    metrics_history = system_metrics.get_metrics_history()
    
    if not metrics_history:
        return go.Figure()
    
    timestamps = [m['timestamp'] for m in metrics_history]
    process_cpu = [m['process']['cpu_percent'] for m in metrics_history]
    process_memory = [m['process']['memory_mb'] for m in metrics_history]
    
    return {
        'data': [
            go.Scatter(
                x=timestamps,
                y=process_cpu,
                name='Process CPU',
                line=dict(color='#d62728')
            ),
            go.Scatter(
                x=timestamps,
                y=process_memory,
                name='Process Memory (MB)',
                line=dict(color='#9467bd'),
                yaxis='y2'
            )
        ],
        'layout': go.Layout(
            xaxis=dict(title='Time'),
            yaxis=dict(title='CPU Usage (%)'),
            yaxis2=dict(
                title='Memory (MB)',
                overlaying='y',
                side='right'
            ),
            legend=dict(x=0, y=1.1, orientation='h'),
            margin=dict(l=40, r=40, t=10, b=30),
            height=250
        )
    }

# Define callback to update operations graph
@app.callback(
    Output('operations-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_operations_graph(n):
    df = performance_metrics.get_recent_metrics(hours=24)
    
    if df.empty:
        return go.Figure()
    
    operation_stats = performance_metrics.get_operation_stats(df)
    
    if not operation_stats:
        return go.Figure()
    
    operations = [stat['operation'] for stat in operation_stats]
    mean_durations = [stat['mean'] for stat in operation_stats]
    max_durations = [stat['max'] for stat in operation_stats]
    
    return {
        'data': [
            go.Bar(
                x=operations,
                y=mean_durations,
                name='Mean Duration (ms)',
                marker=dict(color='#17becf')
            ),
            go.Bar(
                x=operations,
                y=max_durations,
                name='Max Duration (ms)',
                marker=dict(color='#bcbd22')
            )
        ],
        'layout': go.Layout(
            xaxis=dict(title='Operation'),
            yaxis=dict(title='Duration (ms)'),
            barmode='group',
            legend=dict(x=0, y=1.1, orientation='h'),
            margin=dict(l=40, r=20, t=10, b=100),
            height=300
        )
    }

# Define callback to update requests graph
@app.callback(
    Output('requests-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_requests_graph(n):
    df = performance_metrics.get_recent_metrics(hours=24)
    
    if df.empty:
        return go.Figure()
    
    time_series = performance_metrics.get_time_series_data(df, interval='15min')
    
    if not time_series or 'timestamps' not in time_series:
        return go.Figure()
    
    return {
        'data': [
            go.Scatter(
                x=time_series['timestamps'],
                y=time_series['counts'],
                name='Request Count',
                line=dict(color='#e377c2')
            ),
            go.Scatter(
                x=time_series['timestamps'],
                y=time_series['mean_durations'],
                name='Mean Duration (ms)',
                line=dict(color='#7f7f7f'),
                yaxis='y2'
            )
        ],
        'layout': go.Layout(
            xaxis=dict(title='Time'),
            yaxis=dict(title='Request Count'),
            yaxis2=dict(
                title='Duration (ms)',
                overlaying='y',
                side='right'
            ),
            legend=dict(x=0, y=1.1, orientation='h'),
            margin=dict(l=40, r=40, t=10, b=30),
            height=300
        )
    }

def run_dashboard(host='0.0.0.0', port=8050, debug=False):
    """
    Run the monitoring dashboard
    
    Args:
        host (str): Host to run the dashboard on
        port (int): Port to run the dashboard on
        debug (bool): Whether to run in debug mode
    """
    try:
        app.run_server(host=host, port=port, debug=debug)
    finally:
        # Stop metrics collection when dashboard stops
        system_metrics.stop_collection()

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the dashboard
    run_dashboard(debug=True)