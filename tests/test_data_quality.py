# tests/test_data_quality.py
import sys
import os
import datetime
import logging

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from swing_trading_system.data_feeds.dhan_data_feed import DhanDataFeed
from swing_trading_system.data_feeds.multi_timeframe_data import MultiTimeframeData
from swing_trading_system.utils.data_quality import analyze_data_quality, generate_quality_report, plot_data_quality
from swing_trading_system.utils.logging_utils import setup_logging

# Set up logging
logger = setup_logging(log_level=logging.INFO)

def test_data_quality():
    """
    Test data quality analysis on fetched data.
    """
    logger.info("Starting data quality test")
    
    # Define test parameters
    symbols = ["NIFTY", "RELIANCE", "HDFCBANK"]  # Example symbols
    end_date = datetime.datetime.now().date()
    start_date = end_date - datetime.timedelta(days=365)  # 1 year of data
    
    # Initialize data feed
    data_feed = DhanDataFeed()
    
    for symbol in symbols:
        logger.info(f"Testing data quality for {symbol}")
        
        # Use MultiTimeframeData to fetch data
        mtf_data = MultiTimeframeData(symbol, data_feed)
        success = mtf_data.fetch_data(
            timeframes=['daily', 'weekly'],
            start_date=start_date,
            end_date=end_date
        )
        
        if not success:
            logger.error(f"Failed to fetch data for {symbol}")
            continue
        
        # Analyze and report on each timeframe
        for timeframe in ['daily', 'weekly']:
            df = mtf_data.get_data(timeframe)
            
            if df is None or df.empty:
                logger.warning(f"No {timeframe} data available for {symbol}")
                continue
            
            # Analyze data quality
            quality_results = analyze_data_quality(df, symbol, timeframe)
            
            # Generate report
            report_path = generate_quality_report(quality_results)
            logger.info(f"Generated quality report for {symbol} {timeframe}: {report_path}")
            
            # Generate quality plot
            plot_path = plot_data_quality(df, symbol, timeframe)
            logger.info(f"Generated quality plot for {symbol} {timeframe}: {plot_path}")
            
            # Log key statistics
            logger.info(f"Data quality analysis for {symbol} {timeframe}:")
            logger.info(f"- Total bars: {quality_results['total_bars']}")
            logger.info(f"- Date range: {quality_results['start_date']} to {quality_results['end_date']}")
            logger.info(f"- Issues found: {len(quality_results['issues'])}")
            
            for issue in quality_results['issues']:
                logger.warning(f"- Issue: {issue}")
        
        # Try adding indicators
        try:
            # Add indicators to daily timeframe
            indicators = {
                'SMA': {'period': 20},
                'RSI': {'period': 14},
                'ADX': {'period': 14},
                'PLUS_DI': {'period': 14},
                'MINUS_DI': {'period': 14},
                'STOCH': {'fastk_period': 5, 'slowk_period': 3, 'slowd_period': 3}
            }
            
            mtf_data.add_indicators('daily', indicators)
            
            # Save the data with indicators
            mtf_data.save_data()
            
            logger.info(f"Successfully added indicators and saved data for {symbol}")
            
        except Exception as e:
            logger.error(f"Error adding indicators to {symbol} data: {e}")
    
    logger.info("Data quality test completed")

if __name__ == "__main__":
    test_data_quality()