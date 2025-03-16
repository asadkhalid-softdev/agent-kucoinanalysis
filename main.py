import uvicorn
import logging
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
import time
import os
import threading

from api.routes import app
from data.storage import SymbolStorage
from analysis.engine import AnalysisEngine
from data.kucoin_client import KuCoinClient
from config.settings import Settings
from utils.logger import Logger
from utils.dashboard_launcher import launch_dashboard
from utils.telegram_notifier import TelegramNotifier
import config.settings as settings

from datetime import datetime

# Initialize logger
logger_instance = Logger(
    app_name="kucoin_analysis_bot",
    log_dir="logs"
)
logger = logger_instance.get_logger()

# Initialize Telegram notifier
telegram_notifier = None
if settings.telegram_bot_token and settings.telegram_notifications_enabled:
    telegram_notifier = TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id)
    logger.info("Telegram notifications enabled")

# Initialize components
settings = Settings()
symbol_storage = SymbolStorage()
kucoin_client = KuCoinClient(
    api_key=settings.kucoin_api_key,
    api_secret=settings.kucoin_api_secret,
    api_passphrase=settings.kucoin_api_passphrase
)
analysis_engine = AnalysisEngine()

@logger_instance.performance_monitor("analyze_symbol")
def analyze_symbol(symbol):
    """
    Analyze a single symbol with performance monitoring
    
    Args:
        symbol (str): Symbol to analyze
    """
    try:
        # Get klines data for different timeframes
        timeframe_data = {}
        current_time = int(time.time())
        
        for timeframe in settings.default_timeframes:
            
            # Calculate appropriate start time based on timeframe
            if timeframe == "1week":
                # Get 200 days of data
                start_time = "1 year ago"
                # Need at least 50 days for meaningful analysis
                min_candles = 50
            elif timeframe == "1day":
                # Get 200 days of data
                start_time = "200 days ago"
                # Need at least 50 days for meaningful analysis
                min_candles = 50
            elif timeframe == "4hour":
                # Get 30 days of 4h data (180 candles)
                start_time = "30 days ago"
                min_candles = 120
            elif timeframe == "1hour":
                # Get 14 days of hourly data (336 candles)
                start_time = "14 days ago"
                min_candles = 200
            else:  # "15min"
                # Get 5 days of 15min data (480 candles)
                start_time = "5 days ago"
                min_candles = 300
            
            # Try to get klines with retry logic
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                try:
                    klines = kucoin_client.get_klines(
                        symbol=symbol, 
                        kline_type=timeframe,
                        start_time=start_time,
                        end_time=current_time
                    )
                    klines = klines.get("data", [])

                    # Check if we have enough data
                    if "error" not in klines and len(klines) >= min_candles:
                        timeframe_data[timeframe] = klines
                        logger.info(f"Retrieved {len(klines)} {timeframe} candles for {symbol}")
                        break
                    elif "error" not in klines:
                        logger.warning(f"Insufficient {timeframe} data for {symbol}: got {len(klines)} candles, need {min_candles}")
                    else:
                        logger.warning(f"Error getting {timeframe} data for {symbol}: {klines.get('error')}")
                    
                    retry_count += 1
                    time.sleep(1)  # Avoid rate limiting
                    
                except Exception as e:
                    logger.error(f"Exception getting {timeframe} data for {symbol}: {str(e)}")
                    retry_count += 1
                    time.sleep(2)  # Longer delay on exception
        
        # Skip if no data available or missing primary timeframe
        if not timeframe_data:
            logger.warning(f"No data available for {symbol}")
            symbol_storage.store_analysis(symbol, {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "error": "No data available from KuCoin API",
                "indicators": {},
                "sentiment": {"overall": "neutral", "strength": "none", "confidence": 0.0}
            })
            return
            
        if main_tf not in timeframe_data:
            logger.warning(f"Missing primary timeframe (1hour) data for {symbol}")
            # Try to use 4hour or 15min as fallback
            primary_tf = next(iter(timeframe_data.keys())) if timeframe_data else None
            if not primary_tf:
                symbol_storage.store_analysis(symbol, {
                    "symbol": symbol,
                    "timestamp": datetime.now().isoformat(),
                    "error": "Missing primary timeframe data",
                    "indicators": {},
                    "sentiment": {"overall": "neutral", "strength": "none", "confidence": 0.0}
                })
                return
            logger.info(f"Using {primary_tf} as fallback timeframe for {symbol}")
        else:
            primary_tf = main_tf
            
        # Get current price for the symbol
        try:
            ticker = kucoin_client.get_ticker(symbol)
            current_price = float(ticker.get("data", {}).get("price", 0))
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {str(e)}")
            current_price = 0
            
        # Analyze symbol using available data
        analysis = analysis_engine.analyze_symbol(symbol, timeframe_data[primary_tf])
        
        # Add current price if not present
        if "price" not in analysis and current_price > 0:
            analysis["price"] = current_price
            
        # Add multi-timeframe analysis if multiple timeframes available
        if len(timeframe_data) > 1 and hasattr(analysis_engine, 'multi_timeframe_analysis'):
            try:
                multi_tf_analysis = analysis_engine.multi_timeframe_analysis(symbol, timeframe_data)
                analysis["multi_timeframe"] = multi_tf_analysis
            except Exception as e:
                logger.error(f"Error in multi-timeframe analysis for {symbol}: {str(e)}")
        
        # Store analysis result
        symbol_storage.store_analysis(symbol, analysis)
        logger.info(f"Analysis completed for {symbol} using {len(timeframe_data)} timeframes")
        
        # Check if we should send a Telegram notification
        if telegram_notifier and "sentiment" in analysis:
            sentiment = analysis["sentiment"]
            sentiment_key = f"{sentiment.get('strength', 'none')} {sentiment.get('overall', 'neutral')}"
            
            # Send notification for strong buy signals
            if sentiment_key.lower() in settings.telegram_notify_on_sentiment:
                logger.info(f"Sending Telegram notification for {symbol}: {sentiment_key}")
                telegram_notifier.send_analysis_alert(symbol, analysis)
        
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {str(e)}")
        # Store error analysis
        symbol_storage.store_analysis(symbol, {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "indicators": {},
            "sentiment": {"overall": "neutral", "strength": "none", "confidence": 0.0}
        })

@logger_instance.performance_monitor("analyze_all_symbols")
def analyze_all_symbols():
    """Analyze all tracked symbols with performance monitoring"""
    symbols = symbol_storage.get_symbols()
    logger.info(f"Analyzing {len(symbols)} symbols")
    
    for symbol in symbols:
        analyze_symbol(symbol)
        # Sleep to avoid rate limiting
        time.sleep(1)
    
    logger.info("Analysis cycle completed")

def start_scheduler():
    """Start the background scheduler for periodic analysis"""
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        analyze_all_symbols, 
        'interval', 
        minutes=settings.analysis_interval,
        next_run_time=None
    )
    scheduler.start()
    logger.info(f"Scheduler started with {settings.analysis_interval} minute interval")

def start_dashboard():
    """Start the monitoring dashboard in a separate thread"""
    dashboard_thread = threading.Thread(
        target=launch_dashboard,
        kwargs={"port": 8050, "open_browser": False},
        daemon=True
    )
    dashboard_thread.start()
    logger.info("Monitoring dashboard started on port 8050")

if __name__ == "__main__":
    # Create required directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data/storage", exist_ok=True)
    os.makedirs("cache/kucoin", exist_ok=True)

    main_tf = "1day"
    
    # Start the monitoring dashboard
    start_dashboard()
    
    # Start the background scheduler
    start_scheduler()
    
    # Run initial analysis
    analyze_all_symbols()
    
    # Start the FastAPI server
    logger.info("Starting API server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
