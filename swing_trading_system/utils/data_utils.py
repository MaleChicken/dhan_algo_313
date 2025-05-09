import pandas as pd
import numpy as np
import datetime
import logging
from typing import Tuple, List, Dict, Optional, Union

# Set up logger
logger = logging.getLogger(__name__)

def validate_data(df: pd.DataFrame, symbol: str, timeframe: str) -> Tuple[bool, List[str]]:
    """
    Validate data for completeness and quality.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing OHLCV data
    symbol : str
        Symbol being validated
    timeframe : str
        Timeframe of the data
        
    Returns:
    --------
    is_valid : bool
        Whether the data is valid
    issues : list
        List of issues found in the data
    """
    issues = []
    
    # Check for required columns
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        issues.append(f"Missing columns: {missing_columns}")
    
    # Check for missing values
    if df.isnull().any().any():
        null_counts = df.isnull().sum()
        null_columns = [f"{col}: {null_counts[col]}" for col in df.columns if null_counts[col] > 0]
        issues.append(f"Null values found: {', '.join(null_columns)}")
    
    # Check for duplicate dates
    if df.index.duplicated().any():
        dup_count = df.index.duplicated().sum()
        issues.append(f"Found {dup_count} duplicate dates")
    
    # Check for gaps in daily data
    if timeframe == 'daily':
        # Check for missing business days
        # This is a simplified check, real implementation should account for holidays
        all_days = pd.date_range(start=df.index.min(), end=df.index.max(), freq='B')
        missing_days = all_days.difference(df.index)
        if len(missing_days) > 0:
            issues.append(f"Found {len(missing_days)} missing business days")
    
    # Check for price anomalies
    price_zero = (df['close'] <= 0).sum()
    if price_zero > 0:
        issues.append(f"Found {price_zero} days with closing price <= 0")
    
    high_low_issue = (df['high'] < df['low']).sum()
    if high_low_issue > 0:
        issues.append(f"Found {high_low_issue} days where high < low")
    
    # Check for extreme price movements (potential data errors)
    daily_returns = df['close'].pct_change()
    extreme_moves = (daily_returns.abs() > 0.20).sum()  # 20% daily move
    if extreme_moves > 0:
        issues.append(f"Found {extreme_moves} days with >20% price movement (potential data errors)")
    
    return len(issues) == 0, issues

def clean_data(df: pd.DataFrame, symbol: str, timeframe: str) -> pd.DataFrame:
    """
    Clean and prepare data for analysis.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing OHLCV data
    symbol : str
        Symbol being cleaned
    timeframe : str
        Timeframe of the data
        
    Returns:
    --------
    cleaned_df : pd.DataFrame
        Cleaned DataFrame
    """
    logger.info(f"Cleaning {timeframe} data for {symbol}")
    
    # Create a copy to avoid modifying the original
    cleaned_df = df.copy()
    
    # Remove duplicates if any
    if cleaned_df.index.duplicated().any():
        cleaned_df = cleaned_df[~cleaned_df.index.duplicated(keep='first')]
        logger.info(f"Removed duplicate dates from {symbol} data")
    
    # Handle missing values
    if cleaned_df.isnull().any().any():
        # Forward fill missing values (carries previous value forward)
        cleaned_df.fillna(method='ffill', inplace=True)
        
        # If there are still NaN values (e.g., at the beginning), use backward fill
        if cleaned_df.isnull().any().any():
            cleaned_df.fillna(method='bfill', inplace=True)
            
        logger.info(f"Filled missing values in {symbol} data")
    
    # Fix high/low inconsistencies
    high_low_inconsistency = cleaned_df['high'] < cleaned_df['low']
    if high_low_inconsistency.any():
        # Swap high and low values where inconsistent
        inconsistent_rows = high_low_inconsistency
        temp_high = cleaned_df.loc[inconsistent_rows, 'high'].copy()
        cleaned_df.loc[inconsistent_rows, 'high'] = cleaned_df.loc[inconsistent_rows, 'low']
        cleaned_df.loc[inconsistent_rows, 'low'] = temp_high
        logger.info(f"Fixed {inconsistent_rows.sum()} high/low inconsistencies in {symbol} data")
    
    # Ensure OHLC values are consistent
    # High should be >= Open, Close, Low
    cleaned_df['high'] = cleaned_df[['high', 'open', 'close']].max(axis=1)
    # Low should be <= Open, Close, High
    cleaned_df['low'] = cleaned_df[['low', 'open', 'close']].min(axis=1)
    
    # Handle zero or negative prices
    zero_or_negative = (cleaned_df[['open', 'high', 'low', 'close']] <= 0).any(axis=1)
    if zero_or_negative.any():
        # Remove rows with zero or negative prices
        cleaned_df = cleaned_df[~zero_or_negative]
        logger.info(f"Removed {zero_or_negative.sum()} rows with zero or negative prices in {symbol} data")
    
    # Handle extreme price movements (potential data errors)
    # This is simplified and would need refinement for production
    daily_returns = cleaned_df['close'].pct_change()
    extreme_moves = daily_returns.abs() > 0.20  # 20% daily move
    if extreme_moves.any():
        # Flag extreme moves but don't remove them automatically
        logger.warning(f"Found {extreme_moves.sum()} extreme price movements in {symbol} data")
        # Here you could implement more sophisticated handling
    
    # Sort by date to ensure chronological order
    cleaned_df.sort_index(inplace=True)
    
    logger.info(f"Cleaning completed for {symbol} {timeframe} data")
    return cleaned_df

def align_timeframes(daily_df: pd.DataFrame, weekly_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Ensure daily and weekly dataframes are properly aligned.
    
    Parameters:
    -----------
    daily_df : pd.DataFrame
        Daily timeframe data
    weekly_df : pd.DataFrame
        Weekly timeframe data
        
    Returns:
    --------
    daily_aligned : pd.DataFrame
        Aligned daily data
    weekly_aligned : pd.DataFrame
        Aligned weekly data
    """
    logger.info("Aligning daily and weekly timeframes")
    
    # Ensure both dataframes are sorted
    daily_df = daily_df.sort_index()
    weekly_df = weekly_df.sort_index()
    
    # Get date ranges
    daily_start = daily_df.index.min()
    daily_end = daily_df.index.max()
    weekly_start = weekly_df.index.min()
    weekly_end = weekly_df.index.max()
    
    # Determine common date range
    common_start = max(daily_start, weekly_start)
    common_end = min(daily_end, weekly_end)
    
    logger.info(f"Common date range: {common_start.date()} to {common_end.date()}")
    
    # Filter daily data
    daily_aligned = daily_df[(daily_df.index >= common_start) & (daily_df.index <= common_end)]
    
    # Filter weekly data
    weekly_aligned = weekly_df[(weekly_df.index >= common_start) & (weekly_df.index <= common_end)]
    
    logger.info(f"Aligned data: {len(daily_aligned)} daily bars, {len(weekly_aligned)} weekly bars")
    
    return daily_aligned, weekly_aligned