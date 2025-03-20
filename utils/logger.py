import logging
import os
import time
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import traceback
from functools import wraps

class Logger:
    """
    Advanced logging system for the application
    """
    
    def __init__(
        self, 
        app_name: str = "kucoin_analysis_bot",
        log_dir: str = "logs",
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        max_file_size: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5
    ):
        """
        Initialize the logger
        
        Args:
            app_name (str): Application name
            log_dir (str): Directory to store log files
            console_level (int): Logging level for console output
            file_level (int): Logging level for file output
            max_file_size (int): Maximum size of log file before rotation
            backup_count (int): Number of backup files to keep
        """
        self.app_name = app_name
        self.log_dir = log_dir
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(logging.DEBUG)  # Capture all levels
        
        # Remove existing handlers if any
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Create formatters
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        console_handler.setFormatter(console_formatter)
        
        # Create file handler for general logs
        general_log_file = os.path.join(log_dir, f"{app_name}.log")
        file_handler = RotatingFileHandler(
            general_log_file, 
            maxBytes=max_file_size, 
            backupCount=backup_count
        )
        file_handler.setLevel(file_level)
        file_handler.setFormatter(file_formatter)
        
        # Create file handler for error logs
        error_log_file = os.path.join(log_dir, f"{app_name}_error.log")
        error_handler = RotatingFileHandler(
            error_log_file, 
            maxBytes=max_file_size, 
            backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        
        # Create daily rotating file handler for performance logs
        performance_log_file = os.path.join(log_dir, f"{app_name}_performance.log")
        performance_handler = TimedRotatingFileHandler(
            performance_log_file,
            when="midnight",
            interval=1,
            backupCount=30  # Keep 30 days of performance logs
        )
        performance_handler.setLevel(logging.INFO)
        performance_handler.setFormatter(file_formatter)
        
        # Add handlers to logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(performance_handler)
        
        # Create performance logger
        self.performance_logger = logging.getLogger(f"{app_name}.performance")
        self.performance_logger.setLevel(logging.INFO)
        
        # Remove existing handlers if any
        if self.performance_logger.handlers:
            self.performance_logger.handlers.clear()
        
        # Add performance handler
        self.performance_logger.addHandler(performance_handler)
        
        # Log initialization
        self.logger.info(f"Logger initialized for {app_name}")
    
    def get_logger(self):
        """
        Get the main logger
        
        Returns:
            logging.Logger: Main logger
        """
        return self.logger
    
    def log_performance(self, operation: str, duration: float, metadata: dict = None):
        """
        Log performance metrics
        
        Args:
            operation (str): Operation being performed
            duration (float): Duration in seconds
            metadata (dict, optional): Additional metadata
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "duration_ms": duration * 1000,  # Convert to milliseconds
            "metadata": metadata or {}
        }
        
        self.performance_logger.info(json.dumps(log_data))
    
    def performance_monitor(self, operation_name: str = None):
        """
        Decorator to monitor performance of a function
        
        Args:
            operation_name (str, optional): Name of the operation
            
        Returns:
            function: Decorated function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    end_time = time.time()
                    
                    # Log performance
                    op_name = operation_name or func.__name__
                    self.log_performance(
                        operation=op_name,
                        duration=end_time - start_time,
                        metadata={"success": True}
                    )
                    
                    return result
                except Exception as e:
                    end_time = time.time()
                    
                    # Log performance with error
                    op_name = operation_name or func.__name__
                    self.log_performance(
                        operation=op_name,
                        duration=end_time - start_time,
                        metadata={
                            "success": False,
                            "error": str(e)
                        }
                    )
                    
                    # Re-raise the exception
                    raise
            
            return wrapper
        
        return decorator
    
    def exception_handler(self, log_traceback: bool = True):
        """
        Decorator to handle and log exceptions
        
        Args:
            log_traceback (bool): Whether to log the full traceback
            
        Returns:
            function: Decorated function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Log the exception
                    if log_traceback:
                        self.logger.error(
                            f"Exception in {func.__name__}: {str(e)}\n{traceback.format_exc()}"
                        )
                    else:
                        self.logger.error(f"Exception in {func.__name__}: {str(e)}", exc_info=True)
                    
                    # Re-raise the exception
                    raise
            
            return wrapper
        
        return decorator
