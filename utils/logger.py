"""
DEV ZIKKY TELEGRAM - Logging System
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

def setup_logger():
    """Setup logging configuration"""
    logger = logging.getLogger('DEV_ZIKKY_TELEGRAM')
    logger.setLevel(logging.INFO)
    
    # Create logs directory
    log_dir = Path('./logs')
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # File handler
    file_handler = logging.FileHandler('./logs/bot.log')
    file_handler.setLevel(logging.INFO)
    
    # Format
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def get_logger():
    """Get the logger instance"""
    return logging.getLogger('DEV_ZIKKY_TELEGRAM')

def log_command(user_id, user_name, command, args=''):
    """Log command usage"""
    logger = get_logger()
    logger.info(f"📩 Command: {command} | User: {user_name} ({user_id}) | Args: {args}")
    
            