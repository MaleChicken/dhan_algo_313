import backtrader as bt
import pandas as pd
import numpy as np
import datetime
import os
import configparser
import logging
from pathlib import Path
from typing import Optional, Tuple, Union, Dict, List

# Import Dhan-Tradehull
from Dhan_Tradehull import dhan

# Set up logger
logger = logging.getLogger(__name__)

class DhanDataFeed:
    """
    Data feed adapter for Dhan-Tradehull to Backtrader.
    Fetches historical price data and converts to Backtrader format.
    """
    
    def __init__(self, 
                 config_path: str = 'configs/config.ini',
                 secrets_path: str = 'configs/secrets.ini',
                 cache_dir: Optional[str] = None, 
                 cache_expiry_days: Optional[int] = None):
        """
        Initialize the Dhan data feed adapter.
        
        Parameters:
        -----------
        config_path : str
            Path to configuration file
        secrets_path : str
            Path to secrets file with API credentials
        cache_dir : str, optional
            Directory to cache data (overrides config if provided)
        cache_expiry_days : int, optional
            Days before cache expires (overrides config if provided)
        """
        # Load configuration
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        
        # Set cache directory and expiry
        self.cache_dir = cache_dir or self.config['DATA'].get('raw_data_path', 'data/raw')
        self.cache_expiry_days = cache_expiry_days or int(self.config['DATA'].get('cache_expiry_days', '7'))
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize Dhan client
        self.dhan_client = None
        self._init_dhan_client(secrets_path)
    
    def _init_dhan_client(self, secrets_path: str):
        """
        Initialize the Dhan-Tradehull client with credentials.
        
        Parameters:
        -----------
        secrets_path : str
            Path to secrets file with API credentials
        """
        if not os.path.exists(secrets_path):
            logger.warning(f"Secrets file not found: {secrets_path}")
            return
        
        try:
            secrets = configparser.ConfigParser()
            secrets.read(secrets_path)
            
            if 'DHAN' not in secrets:
                logger.warning("DHAN section not found in secrets file")
                return
            
            client_id = secrets['DHAN'].get('client_id')
            access_token = secrets['DHAN'].get('access_token')
            
            if not client_id or not access_token:
                logger.warning("Missing required Dhan-Tradehull credentials")
                return
            
            # Initialize Dhan client with credentials
            # Note: This implementation might need adjustment based on the
            # actual API of Dhan-Tradehull 3.0.6
            self.dhan_client = dhan(
                client_id=client_id,
                access_token=access_token
            )
            logger.info("Dhan-Tradehull client initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Dhan-Tradehull client: {e}")
    
    def get_data(self, 
                 symbol: str, 
                 timeframe: str = 'daily',
                 start_date: Optional[datetime.date] = None,
                 end_date: Optional[datetime.date] = None) -> Optional[bt.feeds.PandasData]:
        """
        Get historical price data for a symbol and convert to Backtrader format.
        
        Parameters:
        -----------
        symbol : str
            Stock symbol or index name (e.g., 'RELIANCE', 'NIFTY')
        timeframe : str
            Data timeframe ('daily', 'weekly', etc.)
        start_date : datetime.date, optional
            Start date for data
        end_date : datetime.date, optional
            End date for data
            
        Returns:
        --------
        data_feed : bt.feeds.PandasData or None
            Backtrader data feed if successful, None otherwise
        """
        if self.dhan_client is None:
            logger.error("Dhan-Tradehull client not initialized")
            return None
        
        # Set default dates if not provided
        if end_date is None:
            end_date = datetime.datetime.now().date()
        if start_date is None:
            start_date = end_date - datetime.timedelta(days=365)  # Default to 1 year
        
        # Check cache first
        cache_exists, cached_data = self._check_cache(symbol, timeframe, start_date, end_date)
        if cache_exists:
            logger.info(f"Using cached data for {symbol} ({timeframe})")
            return self._create_bt_data_feed(cached_data)
        
        # Fetch from API if no cache
        try:
            data = self._fetch_from_api(symbol, timeframe, start_date, end_date)
            if data is not None and not data.empty:
                self._save_to_cache(symbol, timeframe, data)
                return self._create_bt_data_feed(data)
            else:
                logger.warning(f"No data returned for {symbol}")
                return None
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def _fetch_from_api(self, 
                       symbol: str, 
                       timeframe: str, 
                       start_date: datetime.date,
                       end_date: datetime.date) -> Optional[pd.DataFrame]:
        """
        Fetch historical data from Dhan-Tradehull API.
        
        Parameters:
        -----------
        symbol : str
            Stock symbol or index name
        timeframe : str
            Data timeframe
        start_date : datetime.date
            Start date for data
        end_date : datetime.date
            End date for data
            
        Returns:
        --------
        data : pd.DataFrame or None
            DataFrame with historical price data
        """
        logger.info(f"Fetching {timeframe} data for {symbol} from {start_date} to {end_date}")
        
        # Convert timeframe to Dhan-Tradehull format
        tf_mapping = {
            'daily': 'D',
            'weekly': 'W',
            'monthly': 'M',
            '1min': '1',
            '5min': '5',
            '15min': '15',
            '30min': '30',
            '60min': '60'
        }
        
        dhan_timeframe = tf_mapping.get(timeframe.lower())
        if dhan_timeframe is None:
            logger.error(f"Unsupported timeframe: {timeframe}")
            return None
        
        # Format dates for API
        from_date_str = start_date.strftime('%Y-%m-%d')
        to_date_str = end_date.strftime('%Y-%m-%d')
        
        # Determine exchange (this may need refinement based on actual requirements)
        exchange = "NSE"  # Default to NSE
        if symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
            exchange = "NSE_INDEX"
        
        try:
            # Note: The actual method name and parameters may need adjustment
            # based on the Dhan-Tradehull 3.0.6 API
            historical_data = self.dhan_client.get_historical_data(
                symbol=symbol,
                interval=dhan_timeframe,
                from_date=from_date_str,
                to_date=to_date_str,
                exchange=exchange
            )
            
            # Process API response
            if not historical_data:
                logger.warning(f"Empty response from API for {symbol}")
                return None
            
            # Convert to DataFrame (adjust based on actual API response structure)
            df = pd.DataFrame(historical_data)
            
            # Rename columns if needed to match our standard format
            # This mapping might need adjustment based on actual response
            column_map = {
                'date': 'date',          # Assuming 'date' is returned
                'open': 'open',          # Assuming 'open' is returned
                'high': 'high',          # Assuming 'high' is returned
                'low': 'low',            # Assuming 'low' is returned
                'close': 'close',        # Assuming 'close' is returned
                'volume': 'volume'       # Assuming 'volume' is returned
            }
            
            # Apply column mapping
            df.rename(columns=column_map, inplace=True, errors='ignore')
            
            # Ensure required columns exist
            required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                logger.error(f"Missing required columns in API response: {missing_columns}")
                return None
            
            # Convert date to datetime and set as index
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            
            # Convert numeric columns to float
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Handle any NaN values
            df.dropna(inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error in API call: {str(e)}")
            return None
    
    def _check_cache(self, 
                    symbol: str, 
                    timeframe: str, 
                    start_date: datetime.date, 
                    end_date: datetime.date) -> Tuple[bool, Optional[pd.DataFrame]]:
        """
        Check if valid cached data exists for the specified parameters.
        
        Parameters:
        -----------
        symbol : str
            Stock symbol or index name
        timeframe : str
            Data timeframe
        start_date : datetime.date
            Start date for data
        end_date : datetime.date
            End date for data
            
        Returns:
        --------
        cache_exists : bool
            Whether valid cache exists
        cached_data : pd.DataFrame or None
            Cached data if it exists, None otherwise
        """
        cache_file = os.path.join(self.cache_dir, f"{symbol}_{timeframe}.csv")
        
        if not os.path.exists(cache_file):
            return False, None
        
        # Check file modification time
        file_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(cache_file))
        cache_age_days = (datetime.datetime.now() - file_mtime).days
        
        if cache_age_days > self.cache_expiry_days:
            logger.info(f"Cache for {symbol} is {cache_age_days} days old, exceeding {self.cache_expiry_days} day limit")
            return False, None
        
        try:
            df = pd.read_csv(cache_file)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # Check if cached data covers the requested period
            if df.index.min().date() > start_date:
                logger.info(f"Cached data for {symbol} starts after requested start date")
                return False, None
                
            if df.index.max().date() < end_date:
                logger.info(f"Cached data for {symbol} ends before requested end date")
                return False, None
                
            return True, df
            
        except Exception as e:
            logger.error(f"Error reading cached data: {e}")
            return False, None
    
    def _save_to_cache(self, symbol: str, timeframe: str, data: pd.DataFrame):
        """
        Save data to cache.
        
        Parameters:
        -----------
        symbol : str
            Stock symbol or index name
        timeframe : str
            Data timeframe
        data : pd.DataFrame
            Data to cache
        """
        cache_file = os.path.join(self.cache_dir, f"{symbol}_{timeframe}.csv")
        
        try:
            # Reset index to include date column
            data_to_save = data.reset_index()
            data_to_save.to_csv(cache_file, index=False)
            logger.info(f"Saved {symbol} {timeframe} data to cache")
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")
    
    def _create_bt_data_feed(self, dataframe: pd.DataFrame) -> bt.feeds.PandasData:
        """
        Convert pandas DataFrame to Backtrader data feed.
        
        Parameters:
        -----------
        dataframe : pd.DataFrame
            DataFrame with OHLCV data
            
        Returns:
        --------
        data_feed : bt.feeds.PandasData
            Backtrader data feed
        """
        # Create a Backtrader data feed from the pandas DataFrame
        data_feed = bt.feeds.PandasData(
            dataname=dataframe,
            datetime=None,  # Date is already the index
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=-1  # No open interest data
        )
        
        return data_feed