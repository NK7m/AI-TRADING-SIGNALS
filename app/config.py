"""
Configuration management for the AI Trading Signals Bot.
"""

import os
import yaml
from pathlib import Path
from typing import Optional
from loguru import logger
from .schemas import Config


class ConfigManager:
    """Manages application configuration from YAML and environment variables."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/config.yaml"
        self._config: Optional[Config] = None
    
    def load_config(self) -> Config:
        """Load configuration from YAML file and environment variables."""
        if self._config is not None:
            return self._config
        
        try:
            # Load YAML config
            config_data = self._load_yaml_config()
            
            # Override with environment variables
            config_data = self._apply_env_overrides(config_data)
            
            # Validate and create config object
            self._config = Config(**config_data)
            
            logger.info("Configuration loaded successfully")
            return self._config
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _load_yaml_config(self) -> dict:
        """Load configuration from YAML file."""
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        if not config_data:
            raise ValueError("Configuration file is empty or invalid")
        
        return config_data
    
    def _apply_env_overrides(self, config_data: dict) -> dict:
        """Apply environment variable overrides to configuration."""
        # LLM API Key
        if "GEMINI_API_KEY" in os.environ:
            if "llm" not in config_data:
                config_data["llm"] = {}
            config_data["llm"]["api_key"] = os.environ["GEMINI_API_KEY"]
        
        # Discord Webhook URL
        if "DISCORD_WEBHOOK_URL" in os.environ:
            if "discord" not in config_data:
                config_data["discord"] = {}
            config_data["discord"]["webhook_url"] = os.environ["DISCORD_WEBHOOK_URL"]
        
        # Discord Bot Token
        if "DISCORD_BOT_TOKEN" in os.environ:
            if "discord" not in config_data:
                config_data["discord"] = {}
            config_data["discord"]["bot_token"] = os.environ["DISCORD_BOT_TOKEN"]
        
        # Discord Channel ID
        if "DISCORD_CHANNEL_ID" in os.environ:
            if "discord" not in config_data:
                config_data["discord"] = {}
            config_data["discord"]["channel_id"] = os.environ["DISCORD_CHANNEL_ID"]
        
        # Process template variables in config
        config_data = self._process_template_variables(config_data)
        
        return config_data
    
    def _process_template_variables(self, config_data: dict) -> dict:
        """Process template variables like ${GEMINI_API_KEY} in config."""
        def process_value(value):
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                return os.environ.get(env_var, value)
            elif isinstance(value, dict):
                return {k: process_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [process_value(item) for item in value]
            else:
                return value
        
        return process_value(config_data)
    
    def get_config(self) -> Config:
        """Get the current configuration."""
        if self._config is None:
            return self.load_config()
        return self._config
    
    def reload_config(self) -> Config:
        """Reload configuration from files."""
        self._config = None
        return self.load_config()


# Global config manager instance
config_manager = ConfigManager()


def get_config() -> Config:
    """Get the application configuration."""
    return config_manager.get_config()

