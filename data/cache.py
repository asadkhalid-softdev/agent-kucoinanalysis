import json
import os
import time
from datetime import datetime, timedelta

class APICache:
    """
    Cache for API responses to minimize redundant API calls.
    """
    def __init__(self, cache_dir="cache", default_ttl=300):
        """
        Initialize the cache.
        
        Args:
            cache_dir (str): Directory to store cache files
            default_ttl (int): Default time-to-live in seconds (5 minutes)
        """
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def _get_cache_key(self, endpoint, params=None):
        """
        Generate a unique cache key for an API request.
        
        Args:
            endpoint (str): API endpoint
            params (dict, optional): Request parameters
            
        Returns:
            str: Cache key
        """
        if params:
            param_str = json.dumps(params, sort_keys=True)
            return f"{endpoint}_{param_str}"
        return endpoint
    
    def _get_cache_path(self, cache_key):
        """
        Get the file path for a cache key.
        
        Args:
            cache_key (str): Cache key
            
        Returns:
            str: File path
        """
        # Create a filename-safe version of the cache key
        safe_key = "".join(c if c.isalnum() else "_" for c in cache_key)
        return os.path.join(self.cache_dir, f"{safe_key}.json")
    
    def get(self, endpoint, params=None, ttl=None):
        """
        Get cached data for an API request.
        
        Args:
            endpoint (str): API endpoint
            params (dict, optional): Request parameters
            ttl (int, optional): Time-to-live in seconds
            
        Returns:
            dict: Cached data or None if not found or expired
        """
        ttl = ttl or self.default_ttl
        cache_key = self._get_cache_key(endpoint, params)
        cache_path = self._get_cache_path(cache_key)
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    cached_data = json.load(f)
                
                # Check if cache is expired
                if time.time() - cached_data['timestamp'] < ttl:
                    return cached_data['data']
            except (json.JSONDecodeError, KeyError) as e:
                # Invalid cache file, ignore and return None
                pass
        
        return None
    
    def set(self, endpoint, data, params=None):
        """
        Cache data for an API request.
        
        Args:
            endpoint (str): API endpoint
            data (dict): Data to cache
            params (dict, optional): Request parameters
        """
        cache_key = self._get_cache_key(endpoint, params)
        cache_path = self._get_cache_path(cache_key)
        
        cached_data = {
            'timestamp': time.time(),
            'data': data
        }
        
        with open(cache_path, 'w') as f:
            json.dump(cached_data, f)
    
    def clear(self, endpoint=None, params=None):
        """
        Clear cache for a specific endpoint or all cache.
        
        Args:
            endpoint (str, optional): API endpoint
            params (dict, optional): Request parameters
        """
        if endpoint:
            cache_key = self._get_cache_key(endpoint, params)
            cache_path = self._get_cache_path(cache_key)
            
            if os.path.exists(cache_path):
                os.remove(cache_path)
        else:
            # Clear all cache
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
