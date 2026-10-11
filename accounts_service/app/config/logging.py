"""
Accounts Service - Logging Configuration

Configures logging to both console and file.

Author: GDB Architecture Team
"""

import logging
import logging.handlers
from pathlib import Path
from app.config.settings import settings


def setup_logging():
    """
    Configure logging for the application.
    
    Logs are written to:
    - Console (INFO level and above)
    - File (DEBUG level and above)
    
    Log file location: logs/accounts_service.log
    """
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Capture all levels
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler (INFO level and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File Handler (DEBUG level and above)
    # Rotate log file when it reaches 10MB, keep 5 backups
    file_handler = logging.handlers.RotatingFileHandler(
        filename='logs/accounts_service.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Set log level based on environment
    if settings.debug or settings.environment == "development":
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)
    
    logger.info(f"🔧 Logging configured - Level: {settings.log_level}")
    logger.info(f"📁 Log file: logs/accounts_service.log")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
