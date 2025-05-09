# tests/test_data_feed.py
import sys
import os
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import logging

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from swing_trading_system.data_feeds.dhan_data_feed import DhanDataFeed
from swing_trading_system.utils.data_utils import validate_data, clean_data
from swing_trading_system.utils.logging_utils import setup_logging

# Set up logging
logger = setup_logging(log_level=logging.INFO)

def test_data_fetching():
    """
    Test fetching data from Dhan-Tradehull and validating it.
    """
    logger.info("Starting data feed test")
    
    # Initialize data feed
    data_feed = DhanDataFeed()
    
    # Define test parameters
    symbol = "NIFTY"  # Using Nifty index for testing
    end_date = datetime.datetime.now().date()
    start_date = end_date - datetime.timedelta(days=365)  # 1 year of data
    
    # Test daily data
    logger.info(f"Testing daily data for {symbol}")
    daily_data = data_feed.get_data(
        symbol=symbol,
        timeframe='daily',
        start_date=start_date,
        end_date=end_date
    )
    
    # Test weekly data
    logger.info(f"Testing weekly data for {symbol}")
    weekly_data = data_feed.get_data(
        symbol=symbol,
        timeframe='weekly',
        start_date=start_date,
        end_date=end_date
    )
    
    # Validate data if fetched successfully
    if daily_data:
        # Convert to DataFrame for analysis
        daily_df = daily_data.dataname  # Getting the underlying pandas DataFrame
        
        # Validate data quality
        is_valid, issues = validate_data(daily_df, symbol, 'daily')
        
        if not is_valid:
            logger.warning("Daily data validation issues:")
            for issue in issues:
                logger.warning(f"- {issue}")
                
            # Try cleaning the data
            logger.info("Attempting to clean daily data")
            cleaned_df = clean_data(daily_df, symbol, 'daily')
            
            # Check if cleaning fixed the issues
            is_valid_after_clean, issues_after_clean = validate_data(cleaned_df, symbol, 'daily')
            if is_valid_after_clean:
                logger.info("Data cleaning resolved all issues")
            else:
                logger.warning("Issues remain after cleaning:")
                for issue in issues_after_clean:
                    logger.warning(f"- {issue}")
        else:
            logger.info("Daily data passed validation checks")
        
        # Plot the data
        plt.figure(figsize=(12, 6))
        plt.plot(daily_df.index, daily_df['close'])
        plt.title(f"{symbol} Daily Closing Prices")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.grid(True)
        plt.tight_layout()
        
        # Save the plot
        plot_dir = "tests/plots"
        os.makedirs(plot_dir, exist_ok=True)
        plt.savefig(f"{plot_dir}/{symbol}_daily.png")
        logger.info(f"Saved daily price plot to {plot_dir}/{symbol}_daily.png")
        plt.close()
    else:
        logger.error("Failed to fetch daily data")
    
    # Similar validation for weekly data
    if weekly_data:
        weekly_df = weekly_data.dataname
        
        is_valid, issues = validate_data(weekly_df, symbol, 'weekly')
        if not is_valid:
            logger.warning("Weekly data validation issues:")
            for issue in issues:
                logger.warning(f"- {issue}")
        else:
            logger.info("Weekly data passed validation checks")
        
        # Plot weekly data
        plt.figure(figsize=(12, 6))
        plt.plot(weekly_df.index, weekly_df['close'])
        plt.title(f"{symbol} Weekly Closing Prices")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.grid(True)
        plt.tight_layout()
        
        # Save the plot
        plot_dir = "tests/plots"
        os.makedirs(plot_dir, exist_ok=True)
        plt.savefig(f"{plot_dir}/{symbol}_weekly.png")
        logger.info(f"Saved weekly price plot to {plot_dir}/{symbol}_weekly.png")
        plt.close()
    else:
        logger.error("Failed to fetch weekly data")
    
    # Test alignment between timeframes
    if daily_data and weekly_data:
        from swing_trading_system.utils.data_utils import align_timeframes
        
        daily_df = daily_data.dataname
        weekly_df = weekly_data.dataname
        
        daily_aligned, weekly_aligned = align_timeframes(daily_df, weekly_df)
        
        logger.info(f"Alignment results: {len(daily_aligned)} daily bars, {len(weekly_aligned)} weekly bars")
        
        # Test basic indicators
        try:
            import talib
            
            # Calculate some basic indicators
            daily_aligned['sma20'] = talib.SMA(daily_aligned['close'], timeperiod=20)
            daily_aligned['rsi'] = talib.RSI(daily_aligned['close'], timeperiod=14)
            daily_aligned['adx'] = talib.ADX(daily_aligned['high'], daily_aligned['low'], daily_aligned['close'], timeperiod=14)
            
            # Plot with indicators
            plt.figure(figsize=(12, 8))
            
            # Price with SMA
            ax1 = plt.subplot(3, 1, 1)
            ax1.plot(daily_aligned.index, daily_aligned['close'], label='Close')
            ax1.plot(daily_aligned.index, daily_aligned['sma20'], label='SMA(20)', alpha=0.7)
            ax1.set_title(f"{symbol} with Indicators")
            ax1.set_ylabel("Price")
            ax1.legend()
            ax1.grid(True)
            
            # RSI
            ax2 = plt.subplot(3, 1, 2, sharex=ax1)
            ax2.plot(daily_aligned.index, daily_aligned['rsi'], color='purple')
            ax2.axhline(70, color='red', linestyle='--', alpha=0.5)
            ax2.axhline(30, color='green', linestyle='--', alpha=0.5)
            ax2.set_ylabel("RSI")
            ax2.set_ylim(0, 100)
            ax2.grid(True)
            
            # ADX
            ax3 = plt.subplot(3, 1, 3, sharex=ax1)
            ax3.plot(daily_aligned.index, daily_aligned['adx'], color='blue')
            ax3.axhline(25, color='red', linestyle='--', alpha=0.5)
            ax3.set_ylabel("ADX")
            ax3.set_xlabel("Date")
            ax3.grid(True)
            
            plt.tight_layout()
            plt.savefig(f"{plot_dir}/{symbol}_indicators.png")
            logger.info(f"Saved indicators plot to {plot_dir}/{symbol}_indicators.png")
            plt.close()
            
        except ImportError:
            logger.warning("TA-Lib not installed, skipping indicator tests")
    
    logger.info("Data fetching test completed")

if __name__ == "__main__":
    test_data_fetching()