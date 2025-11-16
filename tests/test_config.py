"""
Unit tests for configuration module.
"""

import json
from config import HomeSeerConfig, ConfigManager


class TestHomeSeerConfig:
    """Tests for HomeSeerConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = HomeSeerConfig()
        assert config.url == "https://connected2.homeseer.com/json"
        assert config.username is None
        assert config.password is None
        assert config.token is None
        assert config.source == "homeseer-mcp"
        assert config.timeout == 30
        assert config.verify_ssl is True
    
    def test_base_url_normalization(self):
        """Test base_url property normalizes trailing slashes."""
        config = HomeSeerConfig(url="https://example.com/json/")
        assert config.base_url == "https://example.com/json"
        
        config = HomeSeerConfig(url="https://example.com/json")
        assert config.base_url == "https://example.com/json"
    
    def test_get_auth_params_with_token(self):
        """Test authentication params with token."""
        config = HomeSeerConfig(token="test-token-123")
        auth_params = config.get_auth_params()
        assert auth_params == {"token": "test-token-123"}
    
    def test_get_auth_params_with_username_password(self):
        """Test authentication params with username/password."""
        config = HomeSeerConfig(username="testuser", password="testpass")
        auth_params = config.get_auth_params()
        assert auth_params == {"user": "testuser", "pass": "testpass"}
    
    def test_get_auth_params_token_precedence(self):
        """Test that token takes precedence over username/password."""
        config = HomeSeerConfig(
            token="test-token",
            username="testuser",
            password="testpass"
        )
        auth_params = config.get_auth_params()
        assert auth_params == {"token": "test-token"}
        assert "user" not in auth_params
        assert "pass" not in auth_params
    
    def test_get_auth_params_no_auth(self):
        """Test authentication params when no auth is configured."""
        config = HomeSeerConfig()
        auth_params = config.get_auth_params()
        assert auth_params == {}
    
    def test_get_request_params(self):
        """Test building complete request parameters."""
        config = HomeSeerConfig(token="test-token", source="TestSource")
        params = config.get_request_params(request="getstatus", ref=123)
        
        assert params["source"] == "TestSource"
        assert params["token"] == "test-token"
        assert params["request"] == "getstatus"
        assert params["ref"] == 123


class TestConfigManager:
    """Tests for ConfigManager class."""
    
    def test_load_from_file(self, tmp_path):
        """Test loading configuration from JSON file."""
        config_file = tmp_path / "config.json"
        config_data = {
            "url": "http://test.local/JSON",
            "token": "test-token",
            "timeout": 60
        }
        
        with open(config_file, "w") as f:
            json.dump(config_data, f)
        
        manager = ConfigManager(config_path=config_file)
        config = manager.load_config()
        
        assert config.url == "http://test.local/JSON"
        assert config.token == "test-token"
        assert config.timeout == 60
        assert config.source == "homeseer-mcp"  # Default value
    
    def test_load_from_invalid_json(self, tmp_path):
        """Test handling of invalid JSON file."""
        config_file = tmp_path / "config.json"
        
        with open(config_file, "w") as f:
            f.write("{ invalid json }")
        
        manager = ConfigManager(config_path=config_file)
        config = manager.load_config()
        
        # Should fall back to defaults
        assert config.url == "https://connected2.homeseer.com/json"
    
    def test_load_from_missing_file(self, tmp_path):
        """Test handling of missing config file."""
        config_file = tmp_path / "nonexistent.json"
        
        manager = ConfigManager(config_path=config_file)
        config = manager.load_config()
        
        # Should use defaults
        assert config.url == "https://connected2.homeseer.com/json"
    
    def test_load_from_env(self, monkeypatch):
        """Test loading configuration from environment variables."""
        monkeypatch.setenv("HOMESEER_URL", "http://env.test/JSON")
        monkeypatch.setenv("HOMESEER_TOKEN", "env-token")
        monkeypatch.setenv("HOMESEER_TIMEOUT", "45")
        monkeypatch.setenv("HOMESEER_VERIFY_SSL", "false")
        
        manager = ConfigManager(config_path=None)
        config = manager.load_config()
        
        assert config.url == "http://env.test/JSON"
        assert config.token == "env-token"
        assert config.timeout == 45
        assert config.verify_ssl is False
    
    def test_env_precedence_over_file(self, tmp_path, monkeypatch):
        """Test that environment variables override file configuration."""
        config_file = tmp_path / "config.json"
        config_data = {
            "url": "http://file.test/JSON",
            "token": "file-token",
            "timeout": 30
        }
        
        with open(config_file, "w") as f:
            json.dump(config_data, f)
        
        monkeypatch.setenv("HOMESEER_URL", "http://env.test/JSON")
        monkeypatch.setenv("HOMESEER_TOKEN", "env-token")
        
        manager = ConfigManager(config_path=config_file)
        config = manager.load_config()
        
        # Environment variables should override
        assert config.url == "http://env.test/JSON"
        assert config.token == "env-token"
        # File value should be used when no env var exists
        assert config.timeout == 30
    
    def test_verify_ssl_parsing(self, monkeypatch):
        """Test various string values for verify_ssl parsing."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("on", True),
            ("false", False),
            ("False", False),
            ("0", False),
            ("no", False),
            ("off", False),
            ("anything", False),
        ]
        
        for env_value, expected in test_cases:
            monkeypatch.setenv("HOMESEER_VERIFY_SSL", env_value)
            manager = ConfigManager(config_path=None)
            config = manager.load_config()
            assert config.verify_ssl == expected, f"Failed for value: {env_value}"
    
    def test_get_config_caching(self, tmp_path):
        """Test that get_config caches the configuration."""
        config_file = tmp_path / "config.json"
        config_data = {"url": "http://test.local/JSON"}
        
        with open(config_file, "w") as f:
            json.dump(config_data, f)
        
        manager = ConfigManager(config_path=config_file)
        
        # First call loads config
        config1 = manager.get_config()
        # Second call should return cached config
        config2 = manager.get_config()
        
        assert config1 is config2
    
    def test_reload_config(self, tmp_path):
        """Test that reload_config forces a fresh load."""
        config_file = tmp_path / "config.json"
        config_data = {"url": "http://test1.local/JSON"}
        
        with open(config_file, "w") as f:
            json.dump(config_data, f)
        
        manager = ConfigManager(config_path=config_file)
        config1 = manager.get_config()
        
        # Update config file
        config_data = {"url": "http://test2.local/JSON"}
        with open(config_file, "w") as f:
            json.dump(config_data, f)
        
        # Reload should pick up new values
        config2 = manager.reload_config()
        
        assert config1.url == "http://test1.local/JSON"
        assert config2.url == "http://test2.local/JSON"


class TestGlobalFunctions:
    """Tests for global convenience functions."""
    
    def test_get_config_creates_manager(self):
        """Test that get_config creates a global ConfigManager."""
        from config import get_config
        
        config = get_config()
        assert config is not None
        assert isinstance(config, HomeSeerConfig)
