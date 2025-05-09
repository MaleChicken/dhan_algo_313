# tests/test_visualization.py
import sys
import os
import datetime
import logging

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from swing_trading_system.data_feeds.multi_timeframe_data import MultiTimeframeData
from swing_trading_system.utils.visualization import (
    plot_price_with_indicators, 
    plot_multi_timeframe_analysis,
    create_swing_trade_report
)
from swing_trading_system.utils.logging_utils import setup_logging

# Set up logging
logger = setup_logging(log_level=logging.INFO)

def test_visualization():
    """
    Test data visualization functions.
    """
    logger.info("Starting visualization test")
    
    # Define test parameters
    symbol = "NIFTY"  # Using Nifty index for testing
    end_date = datetime.datetime.now().date()
    start_date = end_date - datetime.timedelta(days=365)  # 1 year of data
    
    # Initialize multi-timeframe data
    mtf_data = MultiTimeframeData(symbol)
    
    # Fetch data
    success = mtf_data.fetch_data(
        timeframes=['daily', 'weekly'],
        start_date=start_date,
        end_date=end_date
    )
    
    if not success:
        logger.error("Failed to fetch data for visualization test")
        return
    
    # Add indicators
    indicators = {
        'SMA': {'period': 20},
        'RSI': {'period': 14},
        'ADX': {'period': 14},
        'PLUS_DI': {'period': 14},
        'MINUS_DI': {'period': 14},
        'STOCH': {'fastk_period': 5, 'slowk_period': 3, 'slowd_period': 3}
    }
    
    for timeframe in ['daily', 'weekly']:
        mtf_data.add_indicators(timeframe, indicators)
    
    # Get data frames
    daily_df = mtf_data.get_data('daily')
    weekly_df = mtf_data.get_data('weekly')
    
    if daily_df is None or weekly_df is None:
        logger.error("Missing data for visualization test")
        return
    
    # Create output directory
    output_dir = "tests/visualizations"
    os.makedirs(output_dir, exist_ok=True)
    
    # Test single timeframe visualization
    logger.info("Testing single timeframe visualization")
    
    daily_plot_path = os.path.join(output_dir, f"{symbol}_daily_indicators.png")
    plot_price_with_indicators(
        df=daily_df,
        symbol=symbol,
        timeframe='daily',
        output_path=daily_plot_path
    )
    logger.info(f"Generated daily visualization: {daily_plot_path}")
    
    weekly_plot_path = os.path.join(output_dir, f"{symbol}_weekly_indicators.png")
    plot_price_with_indicators(
        df=weekly_df,
        symbol=symbol,
        timeframe='weekly',
        output_path=weekly_plot_path
    )
    logger.info(f"Generated weekly visualization: {weekly_plot_path}")
    
    # Test multi-timeframe visualization
    logger.info("Testing multi-timeframe visualization")
    
    mtf_plot_path = os.path.join(output_dir, f"{symbol}_multi_timeframe.png")
    plot_multi_timeframe_analysis(
        daily_df=daily_df,
        weekly_df=weekly_df,
        symbol=symbol,
        output_path=mtf_plot_path
    )
    logger.info(f"Generated multi-timeframe visualization: {mtf_plot_path}")
    
    # Test swing trade report
    logger.info("Testing swing trade report generation")
    
    report_path = os.path.join(output_dir, f"{symbol}_swing_trade_report.csv")
    signals = create_swing_trade_report(
        df=daily_df,
        symbol=symbol,
        output_path=report_path
    )
    
    if not signals.empty:
        logger.info(f"Generated swing trade report with {len(signals)} signals: {report_path}")
        
        # Log some sample signals
        for idx, signal in signals.head(3).iterrows():
            logger.info(f"Signal on {idx.date()}: {signal['reaction_setup']} (ADX: {signal['adx']:.1f}, RSI: {signal['rsi']:.1f})")
    else:
        logger.info("No swing trade signals found in the test period")
    
    logger.info("Visualization test completed")

if __name__ == "__main__":
    test_visualization()