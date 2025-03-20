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
import asyncio
from concurrent.futures import ThreadPoolExecutor

from datetime import datetime, timedelta
from config.user_config import UserConfig

# Initialize user config
user_config = UserConfig()

# Initialize logger
logger_instance = Logger(
    app_name="kucoin_analysis_bot",
    log_dir="logs"
)
logger = logger_instance.get_logger()

# Initialize components
settings = Settings()
symbol_storage = SymbolStorage()
kucoin_client = KuCoinClient(
    api_key=settings.kucoin_api_key,
    api_secret=settings.kucoin_api_secret,
    api_passphrase=settings.kucoin_api_passphrase
)
analysis_engine = AnalysisEngine(config=user_config.get_config())

# Initialize symbols from KuCoin instead of using symbols.json
symbol_storage.initialize_symbols_from_kucoin(kucoin_client)

# Initialize Telegram notifier
telegram_notifier = None
if settings.telegram_bot_token and settings.telegram_notifications_enabled:
    telegram_notifier = TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id)
    logger.info("Telegram notifications enabled")

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

        settings = Settings()
        primary_tf = settings.main_timeframe
        
        for timeframe in settings.default_timeframes:
            # Calculate appropriate start time based on timeframe
            if timeframe == "1week":
                # Get 5 years of weekly data (260 candles)
                start_time = int(time.time() - (86400 * 365 * 5))
                min_candles = 50  # About 1 year of weekly data
            elif timeframe == "3day":
                # Get 3 years of 3-day data (365 candles)
                start_time = int(time.time() - (86400 * 365 * 3))
                min_candles = 60  # About 6 months of 3-day data
            elif timeframe == "1day":
                # Get 1 year of daily data (365 candles)
                start_time = int(time.time() - (86400 * 365))
                min_candles = 100  # About 3-4 months of daily data
            elif timeframe == "12hour":
                # Get 180 days of 12h data (360 candles)
                start_time = int(time.time() - (86400 * 180))
                min_candles = 120  # About 60 days of 12h data
            elif timeframe == "8hour":
                # Get 120 days of 8h data (360 candles)
                start_time = int(time.time() - (86400 * 120))
                min_candles = 150  # About 50 days of 8h data
            elif timeframe == "6hour":
                # Get 90 days of 6h data (360 candles)
                start_time = int(time.time() - (86400 * 90))
                min_candles = 160  # About 40 days of 6h data
            elif timeframe == "4hour":
                # Get 60 days of 4h data (360 candles)
                start_time = int(time.time() - (86400 * 60))
                min_candles = 180  # About 30 days of 4h data
            elif timeframe == "2hour":
                # Get 30 days of 2h data (360 candles)
                start_time = int(time.time() - (86400 * 30))
                min_candles = 200  # About 17 days of 2h data
            elif timeframe == "1hour":
                # Get 21 days of hourly data (504 candles)
                start_time = int(time.time() - (86400 * 21))
                min_candles = 240  # About 10 days of hourly data
            elif timeframe == "30min":
                # Get 14 days of 30min data (672 candles)
                start_time = int(time.time() - (86400 * 14))
                min_candles = 288  # About 6 days of 30min data
            elif timeframe == "15min":
                # Get 7 days of 15min data (672 candles)
                start_time = int(time.time() - (86400 * 7))
                min_candles = 384  # About 4 days of 15min data
            elif timeframe == "5min":
                # Get 3 days of 5min data (864 candles)
                start_time = int(time.time() - (86400 * 3))
                min_candles = 576  # About 2 days of 5min data
            elif timeframe == "1min":
                # Get 1 day of 1min data (1440 candles)
                start_time = int(time.time() - 86400)
                min_candles = 720  # About 12 hours of 1min data
            else:
                # Default to 7 days
                start_time = int(time.time() - (86400 * 7))
                min_candles = 100
            
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
                    time.sleep(0.5) 

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
                    logger.error(f"Exception getting {timeframe} data for {symbol}: {str(e)}", exc_info=True)
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
            
        if primary_tf not in timeframe_data:
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
            
        # Get current price for the symbol
        try:
            ticker = kucoin_client.get_ticker(symbol)
            current_price = float(ticker.get("data", {}).get("price", 0))
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {str(e)}", exc_info=True)
            current_price = 0
            
        # Analyze symbol using available data for primary timeframe
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
                logger.error(f"Error in multi-timeframe analysis for {symbol}: {str(e)}", exc_info=True)
        
        # Store analysis result
        symbol_storage.store_analysis(symbol, analysis)
        logger.info(f"Analysis completed for {symbol} using {len(timeframe_data)} timeframes")
        
        # Check if we should send a Telegram notification
        if telegram_notifier and "sentiment" in analysis and settings.telegram_notifications_enabled:
            sentiment = analysis["sentiment"]
            confidence = sentiment.get("confidence", 0.0)
            sentiment_key = f"{sentiment.get('strength', 'none')} {sentiment.get('overall', 'neutral')}"
            volume = analysis.get("volume", 0.0)
            potential_profit_pct = analysis.get("indicators", {}).get("FIBONACCI", {}).get("value", {}).get("potential_profit_pct", settings.telegram_notify_on_profit_buy)
            risk_reward_ratio = analysis.get("indicators", {}).get("FIBONACCI", {}).get("value", {}).get("risk_reward_ratio", settings.telegram_notify_on_plr)
            rsi = analysis.get("indicators", {}).get("RSI", {}).get("value", settings.telegram_notify_on_rsi_buy)
            
            # Send notification for strong buy signals
            if sentiment_key.lower() in settings.telegram_notify_on_sentiment and \
            confidence >= settings.telegram_notify_on_confidence and \
            volume >= settings.telegram_notify_on_volume and \
            risk_reward_ratio >= settings.telegram_notify_on_plr and \
            rsi <= settings.telegram_notify_on_rsi_buy and \
            potential_profit_pct >= settings.telegram_notify_on_profit_buy: 
                logger.info(f"Sending Telegram notification for {symbol}: {sentiment_key}")
                # The notifier will now check internally if the notification should be sent
                telegram_notifier.send_analysis_alert(symbol, analysis)
        
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {str(e)}", exc_info=True)
        # Store error analysis
        symbol_storage.store_analysis(symbol, {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "indicators": {},
            "sentiment": {"overall": "neutral", "strength": "none", "confidence": 0.0}
        })

async def analyze_all_symbols_async():
    try:
        """Analyze all tracked symbols asynchronously"""
        symbols = symbol_storage.get_symbols()
        logger.info(f"Analyzing {len(symbols)} symbols asynchronously")
        
        # Create a thread pool for running the analysis tasks
        # Limit concurrency to avoid rate limits
        max_workers = min(10, len(symbols))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create a list to hold all the futures
            futures = []
            
            # Submit all analysis tasks to the executor
            for symbol in symbols:
                future = executor.submit(analyze_symbol, symbol)
                futures.append(future)
            
            # Process results as they complete
            for i, future in enumerate(futures):
                try:
                    # Wait for the task to complete
                    await asyncio.wrap_future(future)
                    logger.info(f"Completed analysis {i+1}/{len(symbols)}")
                except KeyboardInterrupt:
                    exit()
                except Exception as e:
                    logger.error(f"Error in async analysis task: {str(e)}", exc_info=True)
        
        logger.info("Async analysis cycle completed")
    except Exception as e:
        logger.error(f"Error in async analysis task: {str(e)}", exc_info=True)

# Replace the existing analyze_all_symbols function with this one
@logger_instance.performance_monitor("analyze_all_symbols")
def analyze_all_symbols():
    """Analyze all tracked symbols"""
    # Run the async function in the event loop
    asyncio.run(analyze_all_symbols_async())

def refresh_symbols():
    """Refresh the list of symbols from KuCoin"""
    logger.info("Refreshing symbols from KuCoin")
    symbol_storage.initialize_symbols_from_kucoin(kucoin_client)

def start_scheduler():
    """Start the background scheduler for periodic analysis"""
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        analyze_all_symbols, 
        'interval', 
        minutes=settings.analysis_interval,
        next_run_time=datetime.now() + timedelta(seconds=5)  # First run after 1 minutes
    )

    scheduler.add_job(
        refresh_symbols, 
        'interval', 
        hours=12,  # Refresh once a day
        next_run_time=datetime.now() + timedelta(minutes=5)  # First run after 5 minutes
    )
    
    scheduler.start()
    logger.info(f"Scheduler started with {settings.analysis_interval} minute interval")

    return scheduler

def start_dashboard():
    """Start the monitoring dashboard in a separate thread"""
    dashboard_thread = threading.Thread(
        target=launch_dashboard,
        kwargs={"port": 8050, "open_browser": False},
        daemon=True
    )
    dashboard_thread.start()
    logger.info("Monitoring dashboard started on port 8050")

# Create a function to run initial analysis in background
def run_initial_analysis():
    """Run initial analysis in a background thread"""
    logger.info("Starting initial analysis in background thread")
    try:
        analyze_all_symbols()
    except Exception as e:
        logger.error(f"Error in initial analysis: {str(e)}", exc_info=True)

if __name__ == "__main__":
    try:
        # Create required directories
        os.makedirs("logs", exist_ok=True)
        os.makedirs("data/storage", exist_ok=True)
        
        # Start the monitoring dashboard
        start_dashboard()
        
        # Start the background scheduler
        scheduler = start_scheduler()
        
        # Start the FastAPI server
        logger.info("Starting API server")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}", exc_info=True)
    except KeyboardInterrupt:
        logger.info("Shutting down application")
    finally:
        scheduler.shutdown(wait=False)
