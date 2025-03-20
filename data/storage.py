import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

class SymbolStorage:
    """
    Manages storage of symbols and analysis results
    """
    
    def __init__(self, data_dir: str = "data/storage"):
        """
        Initialize the symbol storage
        
        Args:
            data_dir (str): Directory to store data files
        """

        self.n_files = 2
        self.data_dir = data_dir
        self.symbols_file = os.path.join(data_dir, "symbols.json")
        self.analysis_dir = os.path.join(data_dir, "analysis")
        self.logger = logging.getLogger(__name__)
        
        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.analysis_dir, exist_ok=True)
        
        # Initialize symbols list if it doesn't exist
        if not os.path.exists(self.symbols_file):
            self._save_symbols([])
    
    def get_symbols(self) -> List[str]:
        """
        Get list of tracked symbols
        
        Returns:
            List[str]: List of symbols
        """
        try:
            with open(self.symbols_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Error reading symbols file: {str(e)}", exc_info=True)
            return []
    
    def add_symbol(self, symbol: str) -> bool:
        """
        Add a symbol to track
        
        Args:
            symbol (str): Symbol to add
            
        Returns:
            bool: True if added, False if already exists
        """
        symbols = self.get_symbols()
        
        # Check if symbol already exists
        if symbol in symbols:
            return False
        
        # Add symbol and save
        symbols.append(symbol)
        self._save_symbols(symbols)
        return True
    
    def remove_symbol(self, symbol: str) -> bool:
        """
        Remove a symbol from tracking
        
        Args:
            symbol (str): Symbol to remove
            
        Returns:
            bool: True if removed, False if not found
        """
        symbols = self.get_symbols()
        
        # Check if symbol exists
        if symbol not in symbols:
            return False
        
        # Remove symbol and save
        symbols.remove(symbol)
        self._save_symbols(symbols)
        return True
    
    def symbol_exists(self, symbol: str) -> bool:
        """
        Check if a symbol is being tracked
        
        Args:
            symbol (str): Symbol to check
            
        Returns:
            bool: True if symbol exists
        """
        return symbol in self.get_symbols()
    
    def _save_symbols(self, symbols: List[str]) -> None:
        """
        Save symbols list to file
        
        Args:
            symbols (List[str]): List of symbols to save
        """
        try:
            with open(self.symbols_file, 'w') as f:
                json.dump(symbols, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving symbols file: {str(e)}", exc_info=True)

    def store_analysis(self, symbol: str, analysis: Dict[str, Any]) -> bool:
        """
        Store analysis result for a symbol
        
        Args:
            symbol (str): Symbol
            analysis (Dict[str, Any]): Analysis result
            
        Returns:
            bool: True if stored successfully
        """
        try:
            # Create symbol directory if it doesn't exist
            symbol_dir = os.path.join(self.analysis_dir, symbol)
            os.makedirs(symbol_dir, exist_ok=True)
            
            # Store latest analysis
            latest_file = os.path.join(symbol_dir, "latest.json")
            with open(latest_file, 'w') as f:
                json.dump(analysis, f, indent=2, cls=NumpyEncoder)
            
            # Store historical analysis with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            history_file = os.path.join(symbol_dir, f"{timestamp}.json")
            with open(history_file, 'w') as f:
                json.dump(analysis, f, indent=2, cls=NumpyEncoder)
            
            # Maintain history limit (keep last n analyses)
            self._prune_history(symbol_dir, self.n_files)
            
            return True
        except Exception as e:
            self.logger.error(f"Error storing analysis for {symbol}: {str(e)}", exc_info=True)
            return False
    
    def get_analysis(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get latest analysis for a symbol
        
        Args:
            symbol (str): Symbol
            
        Returns:
            Optional[Dict[str, Any]]: Analysis result or None if not found
        """
        latest_file = os.path.join(self.analysis_dir, symbol, "latest.json")
        
        try:
            if os.path.exists(latest_file):
                with open(latest_file, 'r') as f:
                    return json.load(f)
            return None
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Error reading analysis for {symbol}: {str(e)}", exc_info=True)
            return None
    
    def get_analysis_history(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get historical analysis for a symbol
        
        Args:
            symbol (str): Symbol
            limit (int): Maximum number of historical analyses to return
            
        Returns:
            List[Dict[str, Any]]: List of historical analyses
        """
        symbol_dir = os.path.join(self.analysis_dir, symbol)
        
        try:
            if not os.path.exists(symbol_dir):
                return []
            
            # Get all history files except latest.json
            history_files = [f for f in os.listdir(symbol_dir) if f != "latest.json"]
            
            # Sort by timestamp (newest first)
            history_files.sort(reverse=True)
            
            # Load history data
            history = []
            for file in history_files[:limit]:
                file_path = os.path.join(symbol_dir, file)
                try:
                    with open(file_path, 'r') as f:
                        history.append(json.load(f))
                except (json.JSONDecodeError, FileNotFoundError):
                    continue
            
            return history
        except Exception as e:
            self.logger.error(f"Error reading history for {symbol}: {str(e)}", exc_info=True)
            return []
    
    def _prune_history(self, symbol_dir: str, max_files: int) -> None:
        """
        Remove oldest history files if count exceeds max_files
        
        Args:
            symbol_dir (str): Symbol directory
            max_files (int): Maximum number of history files to keep
        """
        try:
            # Get all history files except latest.json
            history_files = [f for f in os.listdir(symbol_dir) if f != "latest.json"]
            
            # If we have more files than the limit, remove oldest ones
            if len(history_files) > max_files:
                # Sort by timestamp (oldest first)
                history_files.sort()
                
                # Remove oldest files
                for file in history_files[:(len(history_files) - max_files)]:
                    os.remove(os.path.join(symbol_dir, file))
        except Exception as e:
            self.logger.error(f"Error pruning history in {symbol_dir}: {str(e)}", exc_info=True)

    def fetch_symbols_from_kucoin(self, kucoin_client):
        """
        Fetch all available symbols from KuCoin API and filter according to requirements
        
        Args:
            kucoin_client: KuCoin client instance
            
        Returns:
            List[str]: Filtered list of symbols
        """
        try:
            # Get all symbols from KuCoin
            response = kucoin_client.get_symbols()
            response = response.get("data", [])
            
            if "error" in response:
                self.logger.error(f"Error fetching symbols: {response['error']}", exc_info=True)
                return []
            
            # Filter symbols based on requirements
            filtered_symbols = []
            
            import re
            for symbol_data in response:
                symbol = symbol_data.get("symbol")
                base_currency = symbol_data.get("baseCurrency")
                quote_currency = symbol_data.get("quoteCurrency")
                
                # Skip if any required field is missing
                if not all([symbol, base_currency, quote_currency]):
                    continue
                    
                # Keep only USDT quote currency
                if quote_currency != "USDT":
                    continue
                    
                # Skip symbols ending with UP or DOWN
                if base_currency.endswith("UP") or base_currency.endswith("DOWN"):
                    continue
                    
                # Skip symbols with numbers in base currency
                if re.search(r'\d', base_currency.lower()):
                    continue
                    
                filtered_symbols.append(symbol)

            self.logger.info(f"Fetched {len(filtered_symbols)} symbols from KuCoin after filtering")
            
            return filtered_symbols
            
        except Exception as e:
            self.logger.error(f"Error fetching symbols from KuCoin: {str(e)}", exc_info=True)
            return []

    def initialize_symbols_from_kucoin(self, kucoin_client):
        """
        Initialize symbols list from KuCoin API
        
        Args:
            kucoin_client: KuCoin client instance
            
        Returns:
            bool: True if successful
        """
        try:
            # Fetch symbols from KuCoin
            symbols = self.fetch_symbols_from_kucoin(kucoin_client)
            
            if not symbols:
                self.logger.warning("No symbols fetched from KuCoin, keeping existing symbols")
                return False
            
            # symbols = [
            #     "ARX-USDT"
            # ]
            
            # Save the symbols
            self._save_symbols(symbols)
            self.logger.info(f"Initialized {len(symbols)} symbols from KuCoin")

            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing symbols from KuCoin: {str(e)}", exc_info=True)
            return False
