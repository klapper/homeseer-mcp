"""
Configuration management for HomeSeer MCP Server.

Supports configuration from:
1. JSON configuration file (config.json)
2. Environment variables (prefixed with HOMESEER_)

Environment variables take precedence over config file values.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class HomeSeerConfig:
    """HomeSeer API configuration."""
    
    # API endpoint
    url: str = "https://connected2.homeseer.com/json"
    
    # Authentication - either username/password OR token
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    
    # Additional settings
    source: str = "homeseer-mcp"
    timeout: int = 30
    verify_ssl: bool = True
    
    def get_auth_params(self) -> Dict[str, str]:
        """
        Get authentication parameters for API requests.
        
        Returns:
            Dict with 'user' and 'pass' OR 'token' key based on configuration.
        """
        auth_params = {}
        
        if self.token:
            # Token authentication takes precedence
            auth_params["token"] = self.token
        elif self.username and self.password:
            # Username/password authentication
            auth_params["user"] = self.username
            auth_params["pass"] = self.password
        
        return auth_params
    
    def get_request_params(self, **kwargs) -> Dict[str, Any]:
        """
        Build request parameters including authentication.
        
        Args:
            **kwargs: Additional parameters to include in the request
            
        Returns:
            Dict with all parameters including authentication and source
        """
        params = {"source": self.source}
        params.update(self.get_auth_params())
        params.update(kwargs)
        return params
    
    @property
    def base_url(self) -> str:
        """Get the base API URL (normalized)."""
        return self.url.rstrip("/")


class ConfigManager:
    """Manages configuration loading from multiple sources."""
    
    CONFIG_FILE_NAME = "config.json"
    ENV_PREFIX = "HOMESEER_"
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Optional path to config file. If None, searches for
                        config.json in current directory and parent directories.
        """
        self.config_path = config_path or self._find_config_file()
        self._config: Optional[HomeSeerConfig] = None
    
    def _find_config_file(self) -> Optional[Path]:
        """
        Search for config.json in current directory and parent directories.
        
        Returns:
            Path to config file if found, None otherwise.
        """
        current_dir = Path.cwd()
        
        # Check current directory
        config_file = current_dir / self.CONFIG_FILE_NAME
        if config_file.exists():
            return config_file
        
        # Check script directory
        script_dir = Path(__file__).parent
        config_file = script_dir / self.CONFIG_FILE_NAME
        if config_file.exists():
            return config_file
        
        # Check parent directory
        parent_config = script_dir.parent / self.CONFIG_FILE_NAME
        if parent_config.exists():
            return parent_config
        
        return None
    
    def _load_from_file(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Returns:
            Dict with configuration values from file, empty dict if file not found.
        """
        if not self.config_path or not self.config_path.exists():
            logger.info(f"Config file not found at {self.config_path}, using defaults")
            return {}
        
        try:
            with open(self.config_path, "r") as f:
                config_data = json.load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                return config_data
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file {self.config_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error reading config file {self.config_path}: {e}")
            return {}
    
    def _load_from_env(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables.
        
        Environment variables should be prefixed with HOMESEER_:
        - HOMESEER_URL
        - HOMESEER_USERNAME
        - HOMESEER_PASSWORD
        - HOMESEER_TOKEN
        - HOMESEER_SOURCE
        - HOMESEER_TIMEOUT
        - HOMESEER_VERIFY_SSL
        
        Returns:
            Dict with configuration values from environment.
        """
        config = {}
        
        # Map environment variable names to config keys
        env_mappings = {
            "URL": "url",
            "USERNAME": "username",
            "PASSWORD": "password",
            "TOKEN": "token",
            "SOURCE": "source",
            "TIMEOUT": "timeout",
            "VERIFY_SSL": "verify_ssl",
        }
        
        for env_suffix, config_key in env_mappings.items():
            env_var = f"{self.ENV_PREFIX}{env_suffix}"
            value = os.environ.get(env_var)
            
            if value is not None:
                # Type conversion for non-string values
                if config_key == "timeout":
                    try:
                        value = int(value)
                    except ValueError:
                        logger.warning(f"Invalid timeout value in {env_var}, using default")
                        continue
                elif config_key == "verify_ssl":
                    value = value.lower() in ("true", "1", "yes", "on")
                
                config[config_key] = value
                logger.debug(f"Loaded {config_key} from environment variable {env_var}")
        
        return config
    
    def load_config(self) -> HomeSeerConfig:
        """
        Load configuration from all sources with precedence.
        
        Precedence order (highest to lowest):
        1. Environment variables
        2. Configuration file
        3. Default values
        
        Returns:
            HomeSeerConfig object with loaded configuration.
        """
        # Start with defaults
        config_dict = {}
        
        # Load from file (overrides defaults)
        file_config = self._load_from_file()
        config_dict.update(file_config)
        
        # Load from environment (overrides file)
        env_config = self._load_from_env()
        config_dict.update(env_config)
        
        # Create config object
        self._config = HomeSeerConfig(**config_dict)
        
        # Log final configuration (without sensitive data)
        logger.info(f"Configuration loaded - URL: {self._config.url}, Source: {self._config.source}")
        if self._config.token:
            logger.info("Authentication: Token")
        elif self._config.username:
            logger.info(f"Authentication: Username/Password (user: {self._config.username})")
        else:
            logger.warning("No authentication configured")
        
        return self._config
    
    def get_config(self) -> HomeSeerConfig:
        """
        Get current configuration, loading if not already loaded.
        
        Returns:
            HomeSeerConfig object.
        """
        if self._config is None:
            return self.load_config()
        return self._config
    
    def reload_config(self) -> HomeSeerConfig:
        """
        Force reload configuration from sources.
        
        Returns:
            HomeSeerConfig object with reloaded configuration.
        """
        self._config = None
        return self.load_config()


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """
    Get the global configuration manager instance.
    
    Returns:
        ConfigManager singleton instance.
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> HomeSeerConfig:
    """
    Get the current HomeSeer configuration.
    
    Convenience function for getting configuration without managing ConfigManager.
    
    Returns:
        HomeSeerConfig object.
    """
    return get_config_manager().get_config()
