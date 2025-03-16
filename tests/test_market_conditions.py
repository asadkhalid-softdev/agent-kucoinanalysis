import logging
import os
from datetime import datetime

from analysis.engine import AnalysisEngine
from data.kucoin_client import KuCoinClient
from config.settings import Settings
from tests.market_conditions import MarketConditionTester

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Run market condition tests
    """
    # Initialize components
    settings = Settings()
    analysis_engine = AnalysisEngine()
    
    # Initialize KuCoin client if credentials are available
    kucoin_client = None
    if settings.kucoin_api_key and settings.kucoin_api_secret and settings.kucoin_api_passphrase:
        kucoin_client = KuCoinClient(
            api_key=settings.kucoin_api_key,
            api_secret=settings.kucoin_api_secret,
            api_passphrase=settings.kucoin_api_passphrase
        )
    
    # Initialize tester
    tester = MarketConditionTester(analysis_engine, kucoin_client)
    
    # Create output directory
    output_dir = "test_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # Test symbols
    symbols = ["BTC-USDT", "ETH-USDT"]
    
    # Define test periods for different market conditions
    # These are example periods for Bitcoin - adjust as needed
    test_periods = {
        "bull": {
            "start_date": "2024-01-01",
            "end_date": "2024-03-01"  # Bull market in early 2024
        },
        "bear": {
            "start_date": "2022-04-01",
            "end_date": "2022-06-01"  # Bear market in mid-2022
        },
        "sideways": {
            "start_date": "2023-06-01",
            "end_date": "2023-08-01"  # Sideways market in mid-2023
        },
        "volatile": {
            "start_date": "2022-11-01",
            "end_date": "2022-12-01"  # Volatile period in late 2022
        }
    }
    
    # Run tests for each symbol and market condition
    # Run tests for each symbol and market condition
    for symbol in symbols:
        logger.info(f"Testing {symbol} under different market conditions")
        
        # Test bull market
        bull_results = tester.test_bull_market(
            symbol,
            test_periods["bull"]["start_date"],
            test_periods["bull"]["end_date"]
        )
        tester.plot_results(
            bull_results, 
            output_file=f"{output_dir}/{symbol}_bull_market.png"
        )
        
        # Test bear market
        bear_results = tester.test_bear_market(
            symbol,
            test_periods["bear"]["start_date"],
            test_periods["bear"]["end_date"]
        )
        tester.plot_results(
            bear_results, 
            output_file=f"{output_dir}/{symbol}_bear_market.png"
        )
        
        # Test sideways market
        sideways_results = tester.test_sideways_market(
            symbol,
            test_periods["sideways"]["start_date"],
            test_periods["sideways"]["end_date"]
        )
        tester.plot_results(
            sideways_results, 
            output_file=f"{output_dir}/{symbol}_sideways_market.png"
        )
        
        # Test volatile market
        volatile_results = tester.test_high_volatility(
            symbol,
            test_periods["volatile"]["start_date"],
            test_periods["volatile"]["end_date"]
        )
        tester.plot_results(
            volatile_results, 
            output_file=f"{output_dir}/{symbol}_volatile_market.png"
        )
        
        logger.info(f"Completed testing for {symbol}")
    
    logger.info("All market condition tests completed")

if __name__ == "__main__":
    main()

