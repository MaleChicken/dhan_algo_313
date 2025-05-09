# swing_trading_system/data_feeds/fetch_data.py
import argparse
import logging
import datetime
import configparser
import os
from typing import List, Optional

from swing_trading_system.data_feeds.dhan_data_feed import DhanDataFeed
from swing_trading_system.data_feeds.multi_timeframe_data import MultiTimeframeData
from swing_trading_system.utils.data_quality import analyze_data_quality, generate_quality_report, plot_data_quality
from swing_trading_system.utils.logging_utils import setup_logging

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Fetch and process data for swing trading system")
    
    parser.add_argument(
        "--symbols", "-s",
        nargs="+",
        default=["NIFTY"],
        help="Symbols to fetch data for"
    )
    
    parser.add_argument(
        "--timeframes", "-t",
        nargs="+",
        default=["daily", "weekly"],
        help="Timeframes to fetch data for"
    )
    
    parser.add_argument(
        "--start-date", "-sd",
        type=lambda s: datetime.datetime.strptime(s, "%Y-%m-%d").date(),
        help="Start date for data (YYYY-MM-DD)"
    )
    
    parser.add_argument(
        "--end-date", "-ed",
        type=lambda s: datetime.datetime.strptime(s, "%Y-%m-%d").date(),
        default=datetime.datetime.now().date(),
        help="End date for data (YYYY-MM-DD)"
    )
    
    parser.add_argument(
        "--config", "-c",
        default="configs/config.ini",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--secrets", "-sc",
        default="configs/secrets.ini",
        help="Path to secrets file"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        default="data/processed",
        help="Output directory for processed data"
    )
    
    parser.add_argument(
        "--add-indicators", "-i",
        action="store_true",
        help="Add technical indicators to the data"
    )
    
    parser.add_argument(
        "--quality-check", "-q",
        action="store_true",
        help="Perform data quality analysis"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(log_level=log_level)
    
    logger.info("Starting data fetch process")
    logger.info(f"Symbols: {args.symbols}")
    logger.info(f"Timeframes: {args.timeframes}")
    logger.info(f"Date range: {args.start_date or 'Default (1 year)'} to {args.end_date}")
    
    # Initialize data feed
    data_feed = DhanDataFeed(
        config_path=args.config,
        secrets_path=args.secrets
    )
    
    # Process each symbol
    for symbol in args.symbols:
        logger.info(f"Processing {symbol}")
        
        # Initialize multi-timeframe data
        mtf_data = MultiTimeframeData(symbol, data_feed)
        
        # Fetch data
        success = mtf_data.fetch_data(
            timeframes=args.timeframes,
            start_date=args.start_date,
            end_date=args.end_date
        )
        
        if not success:
            logger.error(f"Failed to fetch data for {symbol}")
            continue
        
        # Add indicators if requested
        if args.add_indicators:
            logger.info(f"Adding indicators to {symbol} data")
            
            indicators = {
                'SMA': {'period': 20},
                'RSI': {'period': 14},
                'ADX': {'period': 14},
                'PLUS_DI': {'period': 14},
                'MINUS_DI': {'period': 14},
                'STOCH': {'fastk_period': 5, 'slowk_period': 3, 'slowd_period': 3}
            }
            
            for timeframe in args.timeframes:
                mtf_data.add_indicators(timeframe, indicators)
        
        # Save processed data
        mtf_data.save_data(directory=args.output_dir)
        logger.info(f"Saved processed data for {symbol} to {args.output_dir}")
        
        # Perform quality check if requested
        if args.quality_check:
            logger.info(f"Performing data quality analysis for {symbol}")
            
            for timeframe in args.timeframes:
                df = mtf_data.get_data(timeframe)
                
                if df is None or df.empty:
                    logger.warning(f"No {timeframe} data available for {symbol}")
                    continue
                
                # Analyze data quality
                quality_results = analyze_data_quality(df, symbol, timeframe)
                
                # Generate quality report
                report_path = generate_quality_report(quality_results)
                logger.info(f"Generated quality report: {report_path}")
                
                # Generate quality plot
                plot_path = plot_data_quality(df, symbol, timeframe)
                logger.info(f"Generated quality plot: {plot_path}")
                
                # Log issues
                if quality_results['issues']:
                    logger.warning(f"Found {len(quality_results['issues'])} data quality issues for {symbol} {timeframe}")
                    for issue in quality_results['issues']:
                        logger.warning(f"- {issue}")
                else:
                    logger.info(f"No data quality issues found for {symbol} {timeframe}")
    
    logger.info("Data fetch process completed")

if __name__ == "__main__":
    main()