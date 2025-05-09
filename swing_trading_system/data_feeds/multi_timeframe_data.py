# swing_trading_system/data_feeds/multi_timeframe_data.py
import pandas as pd
import numpy as np
import logging
import datetime
from typing import Dict, Tuple, Optional, List

from swing_trading_system.data_feeds.dhan_data_feed import DhanDataFeed
from swing_trading_system.utils.data_utils import validate_data, clean_data, align_timeframes

logger = logging.getLogger(__name__)

class MultiTimeframeData:
    """
    Manages data across multiple timeframes for a trading instrument.
    Ensures proper alignment between timeframes for synchronized analysis.
    """
    
    def __init__(self, symbol: str, dhan_feed: Optional[DhanDataFeed] = None):
        """
        Initialize the multi-timeframe data manager.
        
        Parameters:
        -----------
        symbol : str
            Symbol to fetch data for
        dhan_feed : DhanDataFeed, optional
            Pre-initialized Dhan data feed instance
        """
        self.symbol = symbol
        self.data_feed = dhan_feed or DhanDataFeed()
        self.timeframes = {}  # Will store data for different timeframes
    
    def fetch_data(self, 
                  timeframes: List[str] = ['daily', 'weekly'],
                  start_date: Optional[datetime.date] = None,
                  end_date: Optional[datetime.date] = None) -> bool:
        """
        Fetch data for multiple timeframes and store internally.
        
        Parameters:
        -----------
        timeframes : list
            List of timeframes to fetch
        start_date : datetime.date, optional
            Start date for data
        end_date : datetime.date, optional
            End date for data
            
        Returns:
        --------
        success : bool
            Whether all data was fetched successfully
        """
        # Set default dates if not provided
        if end_date is None:
            end_date = datetime.datetime.now().date()
        if start_date is None:
            start_date = end_date - datetime.timedelta(days=365)  # Default to 1 year
        
        success = True
        
        # Fetch data for each timeframe
        for tf in timeframes:
            logger.info(f"Fetching {tf} data for {self.symbol}")
            
            data = self.data_feed.get_data(
                symbol=self.symbol,
                timeframe=tf,
                start_date=start_date,
                end_date=end_date
            )
            
            if data is None:
                logger.error(f"Failed to fetch {tf} data for {self.symbol}")
                success = False
                continue
            
            # Store the pandas DataFrame
            self.timeframes[tf] = data.dataname
            
            # Validate and clean the data
            is_valid, issues = validate_data(self.timeframes[tf], self.symbol, tf)
            
            if not is_valid:
                logger.warning(f"Data validation issues for {tf} timeframe:")
                for issue in issues:
                    logger.warning(f"- {issue}")
                
                # Clean the data
                logger.info(f"Cleaning {tf} data")
                self.timeframes[tf] = clean_data(self.timeframes[tf], self.symbol, tf)
        
        # Align timeframes if multiple were fetched
        if len(self.timeframes) > 1 and 'daily' in self.timeframes and 'weekly' in self.timeframes:
            logger.info("Aligning daily and weekly timeframes")
            self.timeframes['daily'], self.timeframes['weekly'] = align_timeframes(
                self.timeframes['daily'], 
                self.timeframes['weekly']
            )
        
        return success
    
    def get_data(self, timeframe: str) -> Optional[pd.DataFrame]:
        """
        Get data for a specific timeframe.
        
        Parameters:
        -----------
        timeframe : str
            Timeframe to get data for
            
        Returns:
        --------
        data : pd.DataFrame or None
            DataFrame with price data for the requested timeframe
        """
        return self.timeframes.get(timeframe)
    
    def add_indicators(self, timeframe: str, indicators: Dict[str, dict]) -> bool:
        """
        Add technical indicators to a specific timeframe.
        
        Parameters:
        -----------
        timeframe : str
            Timeframe to add indicators to
        indicators : dict
            Dictionary of indicators to add, where keys are indicator names
            and values are dictionaries of parameters
            
        Returns:
        --------
        success : bool
            Whether indicators were added successfully
        """
        if timeframe not in self.timeframes:
            logger.error(f"Timeframe {timeframe} not available")
            return False
        
        df = self.timeframes[timeframe]
        
        try:
            import talib
            
            for indicator, params in indicators.items():
                if indicator == 'SMA':
                    df[f"sma_{params['period']}"] = talib.SMA(
                        df['close'], 
                        timeperiod=params['period']
                    )
                elif indicator == 'RSI':
                    df[f"rsi_{params['period']}"] = talib.RSI(
                        df['close'], 
                        timeperiod=params['period']
                    )
                elif indicator == 'ADX':
                    df[f"adx_{params['period']}"] = talib.ADX(
                        df['high'], 
                        df['low'], 
                        df['close'], 
                        timeperiod=params['period']
                    )
                elif indicator == 'PLUS_DI':
                    df[f"plus_di_{params['period']}"] = talib.PLUS_DI(
                        df['high'], 
                        df['low'], 
                        df['close'], 
                        timeperiod=params['period']
                    )
                elif indicator == 'MINUS_DI':
                    df[f"minus_di_{params['period']}"] = talib.MINUS_DI(
                        df['high'], 
                        df['low'], 
                        df['close'], 
                        timeperiod=params['period']
                    )
                elif indicator == 'STOCH':
                    slowk, slowd = talib.STOCH(
                        df['high'],
                        df['low'],
                        df['close'],
                        fastk_period=params.get('fastk_period', 5),
                        slowk_period=params.get('slowk_period', 3),
                        slowk_matype=params.get('slowk_matype', 0),
                        slowd_period=params.get('slowd_period', 3),
                        slowd_matype=params.get('slowd_matype', 0)
                    )
                    df[f"stoch_k"] = slowk
                    df[f"stoch_d"] = slowd
                else:
                    logger.warning(f"Unsupported indicator: {indicator}")
            
            return True
            
        except ImportError:
            logger.error("TA-Lib not installed, cannot add indicators")
            return False

    def save_data(self, directory: str = 'data/processed') -> bool:
        """
        Save all timeframe data to CSV files.
        
        Parameters:
        -----------
        directory : str
            Directory to save data to
            
        Returns:
        --------
        success : bool
            Whether all data was saved successfully
        """
        import os
        os.makedirs(directory, exist_ok=True)
        
        success = True
        
        for tf, data in self.timeframes.items():
            filename = f"{self.symbol}_{tf}.csv"
            filepath = os.path.join(directory, filename)
            
            try:
                # Reset index to include date as a column
                data_to_save = data.reset_index()
                data_to_save.to_csv(filepath, index=False)
                logger.info(f"Saved {tf} data to {filepath}")
            except Exception as e:
                logger.error(f"Error saving {tf} data: {e}")
                success = False
        
        return success