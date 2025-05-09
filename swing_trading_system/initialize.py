# swing_trading_system/initialize.py
import os
import logging
import argparse
import datetime
import configparser
import shutil
from pathlib import Path

from swing_trading_system.utils.logging_utils import setup_logging

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Initialize swing trading system")
    
    parser.add_argument(
        "--config", "-c",
        default="configs/config.ini",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--overwrite", "-o",
        action="store_true",
        help="Overwrite existing files"
    )
    
    parser.add_argument(
        "--create-dirs", "-d",
        action="store_true",
        help="Create directory structure"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def create_directory_structure():
    """Create the project directory structure."""
    directories = [
        "data/raw",
        "data/processed",
        "data/quality_reports",
        "logs",
        "configs",
        "tests/plots",
        "tests/visualizations",
        "swing_trading_system/strategies",
        "swing_trading_system/data_feeds",
        "swing_trading_system/indicators",
        "swing_trading_system/utils",
        "swing_trading_system/risk_management",
        "swing_trading_system/backtest"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")

def create_default_config(config_path, overwrite=False):
    """Create default configuration file."""
    if os.path.exists(config_path) and not overwrite:
        logger.info(f"Config file already exists at {config_path}, skipping")
        return
    
    config = configparser.ConfigParser()
    
    config['DEFAULT'] = {
        'raw_data_path': 'data/raw',
        'processed_data_path': 'data/processed'
    }
    
    config['DATA'] = {
        'default_timeframe': 'daily',
        'higher_timeframe': 'weekly',
        'cache_expiry_days': '7'
    }
    
    config['BACKTEST'] = {
        'initial_capital': '1000000',
        'commission_rate': '0.0020',  # 0.2%
        'slippage': '0.0005'  # 0.05%
    }
    
    config['STRATEGY'] = {
        'adx_period': '14',
        'di_period': '14',
        'rsi_period': '7',
        'ma_period': '20',
        'risk_percentage': '0.02'
    }
    
    config['DHAN'] = {
        'client_id': '',
        'access_token': ''
    }
    
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w') as f:
        config.write(f)
    
    logger.info(f"Created default configuration file at {config_path}")

def create_secrets_template(secrets_path):
    """Create template for secrets file."""
    if os.path.exists(secrets_path):
        logger.info(f"Secrets file already exists at {secrets_path}, skipping")
        return
    
    config = configparser.ConfigParser()
    
    config['DHAN'] = {
        'client_id': 'your_client_id_here',
        'access_token': 'your_access_token_here'
    }
    
    os.makedirs(os.path.dirname(secrets_path), exist_ok=True)
    
    with open(secrets_path, 'w') as f:
        config.write(f)
    
    logger.info(f"Created secrets template at {secrets_path}")

def create_gitignore():
    """Create .gitignore file."""
    gitignore_path = '.gitignore'
    
    if os.path.exists(gitignore_path):
        logger.info(f".gitignore file already exists, skipping")
        return
    
    content = """
# Virtual environment
venv/

# Python cache files
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
dist/
build/
*.egg-info/

# Data files
*.csv
*.h5
*.pickle

# Jupyter Notebook
.ipynb_checkpoints

# Local configuration
secrets.ini
.env

# Log files
logs/
*.log
"""
    
    with open(gitignore_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Created .gitignore file")

def run_basic_tests():
    """Run basic tests to verify the setup."""
    tests = [
        "tests/test_data_feed.py",
        "tests/test_data_quality.py",
        "tests/test_visualization.py"
    ]
    
    for test in tests:
        if not os.path.exists(test):
            logger.warning(f"Test file {test} not found, skipping")
            continue
        
        logger.info(f"Running test: {test}")
        
        try:
            import subprocess
            result = subprocess.run(
                ["python", test],
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Test {test} completed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Test {test} failed with error: {e}")
            logger.error(f"Output: {e.output}")

def main():
    args = parse_args()
    
    # Setup logging
    global logger
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(log_level=log_level)
    
    logger.info("Initializing swing trading system")
    
    # Create directory structure if requested
    if args.create_dirs:
        create_directory_structure()
    
    # Create default config file
    create_default_config(args.config, overwrite=args.overwrite)
    
    # Create secrets template
    secrets_path = os.path.join(os.path.dirname(args.config), "secrets.ini")
    create_secrets_template(secrets_path)
    
    # Create .gitignore
    create_gitignore()
    
    # Run basic tests if the files exist
    run_basic_tests()
    
    logger.info("Initialization completed")

if __name__ == "__main__":
    main()