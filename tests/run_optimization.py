import logging
import os
from datetime import datetime

from data.kucoin_client import KuCoinClient
from config.settings import Settings
from parameter_optimizer import ParameterOptimizer
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Run parameter optimization
    """
    # Initialize components
    settings = Settings()
    
    # Check if KuCoin credentials are available
    if not all([settings.kucoin_api_key, settings.kucoin_api_secret, settings.kucoin_api_passphrase]):
        logger.error("KuCoin API credentials not found. Cannot proceed with optimization.", exc_info=True)
        return
    
    # Initialize KuCoin client
    kucoin_client = KuCoinClient(
        api_key=settings.kucoin_api_key,
        api_secret=settings.kucoin_api_secret,
        api_passphrase=settings.kucoin_api_passphrase
    )
    
    # Initialize optimizer
    optimizer = ParameterOptimizer(kucoin_client)
    
    # Create output directory
    output_dir = "optimization_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # Symbols to optimize for
    symbols = ["BTC-USDT", "ETH-USDT"]
    
    # Date range for optimization (use recent data)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now().replace(day=1) - pd.DateOffset(months=3)).strftime("%Y-%m-%d")
    
    logger.info(f"Optimizing parameters for period {start_date} to {end_date}")
    
    # Run optimization for each symbol
    for symbol in symbols:
        logger.info(f"Optimizing parameters for {symbol}")
        
        # Optimize RSI parameters
        rsi_results = optimizer.optimize_rsi_parameters(symbol, start_date, end_date)
        optimizer.save_results(
            rsi_results, 
            f"{output_dir}/{symbol}_rsi_optimization.json"
        )
        
        # Optimize MACD parameters
        macd_results = optimizer.optimize_macd_parameters(symbol, start_date, end_date)
        optimizer.save_results(
            macd_results, 
            f"{output_dir}/{symbol}_macd_optimization.json"
        )
        
        # Optimize Bollinger Bands parameters
        bbands_results = optimizer.optimize_bollinger_bands_parameters(symbol, start_date, end_date)
        optimizer.save_results(
            bbands_results, 
            f"{output_dir}/{symbol}_bbands_optimization.json"
        )
        
        logger.info(f"Completed optimization for {symbol}")
    
    logger.info("All parameter optimizations completed")

if __name__ == "__main__":
    main()
