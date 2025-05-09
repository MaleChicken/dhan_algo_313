import logging
import sys
import os
from datetime import datetime
from pathlib import Path

def setup_logging(log_dir: str = 'logs', log_level: int = logging.INFO) -> logging.Logger:
    """
    Set up logging configuration.
    
    Parameters:
    -----------
    log_dir : str
        Directory to store log files
    log_level : int
        Logging level (e.g., logging.INFO, logging.DEBUG)
        
    Returns:
    --------
    logger : logging.Logger
        Configured logger
    """
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('swing_trading')
    logger.setLevel(log_level)
    
    # Remove existing handlers if any
    if logger.handlers:
        logger.handlers.clear()
    
    # Create file handler with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f'swing_trading_{timestamp}.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger