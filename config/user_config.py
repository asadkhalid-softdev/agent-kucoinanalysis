import os
import json
import logging
from typing import Dict, Any, Optional, List

class UserConfig:
    """
    Manages user configuration settings
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize the user configuration manager
        
        Args:
            config_dir (str): Directory to store configuration files
        """
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "user_config.json")
        self.default_config_file = os.path.join(config_dir, "default_config.json")
        self.logger = logging.getLogger(__name__)
        
        # Create directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)
        
        # Initialize default configuration if it doesn't exist
        if not os.path.exists(self.config_file):
            self._save_config(self._get_default_config())
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration
        
        Returns:
            Dict[str, Any]: Default configuration
        """
        with open(self.default_config_file, 'r') as f:
            return json.load(f)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration
        
        Returns:
            Dict[str, Any]: Current configuration
        """
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Error reading configuration file: {str(e)}", exc_info=True)
            # Return default config if there's an error
            return self._get_default_config()
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """
        Update configuration
        
        Args:
            new_config (Dict[str, Any]): New configuration to merge with existing
            
        Returns:
            bool: True if updated successfully
        """
        try:
            # Get current config
            current_config = self.get_config()
            
            # Deep merge the new config with the current one
            updated_config = self._deep_merge(current_config, new_config)
            
            # Save updated config
            self._save_config(updated_config)
            return True
        except Exception as e:
            self.logger.error(f"Error updating configuration: {str(e)}", exc_info=True)
            return False
    
    def get_value(self, key_path: str, default: Any = None) -> Any:
        """
        Get a specific configuration value using dot notation
        
        Args:
            key_path (str): Key path using dot notation (e.g., "analysis.interval")
            default (Any): Default value if key doesn't exist
            
        Returns:
            Any: Configuration value or default
        """
        config = self.get_config()
        keys = key_path.split('.')
        
        # Navigate through the config dictionary
        for key in keys:
            if isinstance(config, dict) and key in config:
                config = config[key]
            else:
                return default
        
        return config
    
    def set_value(self, key_path: str, value: Any) -> bool:
        """
        Set a specific configuration value using dot notation
        
        Args:
            key_path (str): Key path using dot notation (e.g., "analysis.interval")
            value (Any): Value to set
            
        Returns:
            bool: True if set successfully
        """
        try:
            config = self.get_config()
            keys = key_path.split('.')
            
            # Navigate to the parent dictionary
            current = config
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # Set the value
            current[keys[-1]] = value
            
            # Save updated config
            self._save_config(config)
            return True
        except Exception as e:
            self.logger.error(f"Error setting configuration value: {str(e)}", exc_info=True)
            return False
    
    def reset_to_defaults(self) -> bool:
        """
        Reset configuration to defaults
        
        Returns:
            bool: True if reset successfully
        """
        try:
            self._save_config(self._get_default_config())
            return True
        except Exception as e:
            self.logger.error(f"Error resetting configuration: {str(e)}", exc_info=True)
            return False
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """
        Save configuration to file
        
        Args:
            config (Dict[str, Any]): Configuration to save
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving configuration file: {str(e)}", exc_info=True)
    
    def _deep_merge(self, d1: Dict[str, Any], d2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries
        
        Args:
            d1 (Dict[str, Any]): First dictionary
            d2 (Dict[str, Any]): Second dictionary (overrides d1)
            
        Returns:
            Dict[str, Any]: Merged dictionary
        """
        result = d1.copy()
        
        for key, value in d2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge dictionaries
                result[key] = self._deep_merge(result[key], value)
            else:
                # Override or add value
                result[key] = value
        
        return result
