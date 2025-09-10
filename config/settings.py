"""
Configuration loading and validation for UniLinkUp Telegram Bot
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


def load_bot_token() -> str:
    """
    Load and validate bot token from environment variables
    
    Returns:
        str: Bot token
        
    Raises:
        ValueError: If bot token is not configured
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token or token == "YOUR_BOT_TOKEN_HERE":
        raise ValueError(
            "Bot token not configured. Please set TELEGRAM_BOT_TOKEN environment variable."
        )
    
    return token


def validate_configuration() -> bool:
    """
    Validate all required configuration settings
    
    Returns:
        bool: True if configuration is valid
    """
    try:
        load_bot_token()
        logger.info("Configuration validation successful")
        return True
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        return False


def get_log_level() -> str:
    """
    Get logging level from environment variable
    
    Returns:
        str: Log level (default: INFO)
    """
    return os.getenv("LOG_LEVEL", "INFO").upper()


def is_debug_mode() -> bool:
    """
    Check if debug mode is enabled
    
    Returns:
        bool: True if debug mode is enabled
    """
    return os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")