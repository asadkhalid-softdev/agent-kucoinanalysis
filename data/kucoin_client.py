import base64
import hashlib
import hmac
import json
import logging
import time
from urllib.parse import urlencode
import pytz

from typing import Optional
import dateparser
from binance.exceptions import UnknownDateFormat
import requests
from datetime import datetime

class RateLimitExceeded(Exception):
    """Exception raised when KuCoin API rate limit is exceeded."""
    pass

class KuCoinRateLimiter:
    """
    Rate limiter for KuCoin API to handle request limits.
    KuCoin limits to 30 requests per 3 seconds.
    """
    def __init__(self, max_requests=25, time_frame=3):
        """
        Initialize the rate limiter.
        
        Args:
            max_requests (int): Maximum number of requests allowed
            time_frame (int): Time frame in seconds
        """
        self.max_requests = max_requests  # Setting below the limit for safety
        self.time_frame = time_frame
        self.request_timestamps = []
    
    def wait_if_needed(self):
        """
        Check if we need to wait before making another request.
        If too many requests have been made recently, this will sleep.
        """
        current_time = time.time()
        
        # Remove timestamps older than the time frame
        self.request_timestamps = [ts for ts in self.request_timestamps 
                                  if current_time - ts < self.time_frame]
        
        # If we've reached the limit, wait until we can make another request
        if len(self.request_timestamps) >= self.max_requests:
            oldest_timestamp = min(self.request_timestamps)
            sleep_time = self.time_frame - (current_time - oldest_timestamp)
            if sleep_time > 0:
                logging.info(f"Rate limit approaching, waiting {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        # Add the current request timestamp
        self.request_timestamps.append(time.time())

def convert_ts_str(ts_str):
    if ts_str is None:
        return ts_str
    if type(ts_str) == int:
        return ts_str
    return date_to_seconds(ts_str)

def date_to_seconds(date_str: str) -> int:
    """Convert UTC date to milliseconds

    If using offset strings add "UTC" to date string e.g. "now UTC", "11 hours ago UTC"

    See dateparse docs for formats http://dateparser.readthedocs.io/en/latest/

    :param date_str: date in readable format, i.e. "January 01, 2018", "11 hours ago UTC", "now UTC"
    """
    # get epoch value in UTC
    epoch: datetime = datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)
    # parse our date string
    d: Optional[datetime] = dateparser.parse(date_str, settings={'TIMEZONE': "UTC"})
    if not d:
        raise UnknownDateFormat(date_str)

    # if the date is not timezone aware apply UTC timezone
    if d.tzinfo is None or d.tzinfo.utcoffset(d) is None:
        d = d.replace(tzinfo=pytz.utc)

    # return the difference in time
    return int((d - epoch).total_seconds())

class KuCoinClient:
    def __init__(self, api_key="", api_secret="", api_passphrase=""):
        """
        Initialize the KuCoin API client with authentication credentials.
        
        Args:
            api_key (str): Your KuCoin API key
            api_secret (str): Your KuCoin API secret
            api_passphrase (str): Your KuCoin API passphrase
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase
        self.base_url = "https://api.kucoin.com"
        self.session = requests.Session()
        self.rate_limiter = KuCoinRateLimiter()
        
        # Encrypt passphrase if credentials are provided
        if api_passphrase and api_secret:
            self.encrypted_passphrase = self._sign(
                api_passphrase.encode('utf-8'), 
                api_secret.encode('utf-8')
            )
        else:
            self.encrypted_passphrase = ""
            logging.warning("API credentials not provided. Only public endpoints available.")
    
    def _sign(self, message, secret):
        """Sign a message using HMAC-SHA256 and encode with base64."""
        signature = hmac.new(secret, message, hashlib.sha256)
        return base64.b64encode(signature.digest()).decode()
    
    def _get_headers(self, method, endpoint, body=""):
        """Generate authentication headers for KuCoin API requests."""
        timestamp = str(int(time.time() * 1000))
        
        # Create signature string
        signature_string = timestamp + method + endpoint + (body if body else "")
        signature = self._sign(
            signature_string.encode('utf-8'), 
            self.api_secret.encode('utf-8')
        )
        
        return {
            "KC-API-KEY": self.api_key,
            "KC-API-SIGN": signature,
            "KC-API-TIMESTAMP": timestamp,
            "KC-API-PASSPHRASE": self.encrypted_passphrase,
            "KC-API-KEY-VERSION": "2",
            "Content-Type": "application/json"
        }
    
    def get_ticker(self, symbol):
        """
        Get ticker information for a specific symbol with caching.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC-USDT')
            
        Returns:
            dict: Ticker data including price, volume, etc.
        """
        endpoint = "/api/v1/market/orderbook/level1"
        params = {"symbol": symbol}
        
        response = self._request("GET", f"{endpoint}?symbol={symbol}")
            
        return response
    
    def get_klines(self, symbol, kline_type="1hour", start_time=None, end_time=None):
        """
        Get candlestick data for a specific symbol with caching.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC-USDT')
            kline_type (str): Kline interval (e.g., '1min', '1hour', '1day')
            start_time (int, optional): Start time in milliseconds
            end_time (int, optional): End time in milliseconds
            
        Returns:
            list: List of klines data
        """
        params = {
            "symbol": symbol,
            "type": kline_type
        }
        
        if start_time:
            params["startAt"] = convert_ts_str(start_time)
        if end_time:
            params["endAt"] = convert_ts_str(end_time)

        endpoint = "/api/v1/market/candles"
        
        query_string = urlencode(params)
        response = self._request("GET", f"{endpoint}?{query_string}")
        
        return response
    
    def get_24h_stats(self, symbol):
        """
        Get 24-hour statistics for a specific symbol with caching.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC-USDT')
            
        Returns:
            dict: 24-hour statistics including high, low, volume, etc.
        """
        endpoint = "/api/v1/market/stats"
        params = {"symbol": symbol}
        
        response = self._request("GET", f"{endpoint}?symbol={symbol}")
        
        return response
    
    def get_symbols(self):
        """
        Get list of symbol pairs with caching.
        
        Args:
            None
            
        Returns:
            list: List of symbol data dictionaries
        """
        endpoint = "/api/v1/symbols"
        
        response = self._request("GET", endpoint)
        
        # Extract the data array from the response
        if "data" in response:
            return response["data"]
        else:
            return []
    
    def get_all_tickers(self):
        """
        Get ticker information for all trading pairs with caching.
        
        Args:
            None
            
        Returns:
            dict: Ticker data for all symbols
        """
        endpoint = "/api/v1/market/allTickers"
        
        response = self._request("GET", endpoint)
        
        return response
    
    def get_market_list(self):
        """
        Get list of available markets with caching.
        
        Args:
            None
            
        Returns:
            dict: List of available markets
        """
        endpoint = "/api/v1/markets"
        
        response = self._request("GET", endpoint)
        
        return response
    
    def get_symbols(self, market=None):
        """
        Get list of symbol pairs with caching.
        
        Args:
            market (str, optional): Market (e.g., 'BTC', 'USDT')
            
        Returns:
            dict: List of symbol pairs
        """
        endpoint = "/api/v1/symbols"
        params = {}
        
        if market:
            params["market"] = market
        
        query_string = f"?market={market}" if market else ""
        response = self._request("GET", f"{endpoint}{query_string}")
        
        return response
    
    def get_currencies(self):
        """
        Get list of currencies with caching.
        
        Args:
            None
            
        Returns:
            dict: List of currencies
        """
        endpoint = "/api/v1/currencies"
        
        response = self._request("GET", endpoint)
        
        return response
    
    def _request(self, method, endpoint, params=None, data=None):
        """
        Send a request to the KuCoin API with rate limiting.
        
        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint
            params (dict, optional): Query parameters for GET requests
            data (dict, optional): Request body for POST requests
            
        Returns:
            dict: Response data from the API
        """
        # Wait if needed to avoid rate limit
        self.rate_limiter.wait_if_needed()
        
        url = self.base_url + endpoint
        body = ""
        
        if data:
            body = json.dumps(data)
            
        headers = self._get_headers(method, endpoint, body)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                data=body if body else None
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP Error: {e}")
            if response.status_code == 429:
                logging.warning("Rate limit exceeded. Implementing backoff strategy.")
                raise RateLimitExceeded("Too many requests to KuCoin API")
            return {"error": str(e), "status_code": response.status_code}
        except requests.exceptions.RequestException as e:
            logging.error(f"Request Error: {e}")
            return {"error": str(e)}
    
