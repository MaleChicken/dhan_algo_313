# swing_trading_system/utils/visualization.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import logging
from typing import Optional, List, Dict, Tuple

logger = logging.getLogger(__name__)

def plot_price_with_indicators(df: pd.DataFrame, 
                              symbol: str, 
                              timeframe: str,
                              output_path: Optional[str] = None,
                              show_plots: bool = False) -> None:
    """
    Create a visualization of price data with technical indicators.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with price and indicator data
    symbol : str
        Symbol being visualized
    timeframe : str
        Timeframe of the data
    output_path : str, optional
        Path to save the plot to
    show_plots : bool
        Whether to display the plot interactively
    """
    logger.info(f"Creating visualization for {symbol} ({timeframe})")
    
    # Determine which indicators are available in the DataFrame
    has_sma = any(col.startswith('sma_') for col in df.columns)
    has_rsi = any(col.startswith('rsi_') for col in df.columns)
    has_adx = any(col.startswith('adx_') for col in df.columns)
    has_di = any(col.startswith('plus_di_') for col in df.columns) and any(col.startswith('minus_di_') for col in df.columns)
    has_stoch = 'stoch_k' in df.columns and 'stoch_d' in df.columns
    
    # Determine subplot count
    subplot_count = 1  # Price is always included
    if has_rsi:
        subplot_count += 1
    if has_adx and has_di:
        subplot_count += 1
    if has_stoch:
        subplot_count += 1
    
    # Create figure and subplots
    fig, axs = plt.subplots(subplot_count, 1, figsize=(12, 4 * subplot_count), sharex=True)
    
    # If there's only one subplot, put it in a list to make indexing consistent
    if subplot_count == 1:
        axs = [axs]
    
    # Plot price and MA
    ax_idx = 0
    axs[ax_idx].plot(df.index, df['close'], label='Close', color='blue')
    axs[ax_idx].set_title(f"{symbol} - {timeframe} - Price Chart with Indicators")
    axs[ax_idx].set_ylabel("Price")
    axs[ax_idx].grid(True)
    
    # Add SMA if available
    if has_sma:
        for col in df.columns:
            if col.startswith('sma_'):
                period = col.split('_')[1]
                axs[ax_idx].plot(df.index, df[col], label=f'SMA({period})', alpha=0.7)
    
    axs[ax_idx].legend()
    
    # Plot RSI if available
    if has_rsi:
        ax_idx += 1
        
        for col in df.columns:
            if col.startswith('rsi_'):
                period = col.split('_')[1]
                axs[ax_idx].plot(df.index, df[col], label=f'RSI({period})', color='purple')
                
                # Add overbought/oversold lines
                axs[ax_idx].axhline(70, color='red', linestyle='--', alpha=0.5)
                axs[ax_idx].axhline(30, color='green', linestyle='--', alpha=0.5)
                
                axs[ax_idx].set_ylabel(f"RSI({period})")
                axs[ax_idx].set_ylim(0, 100)
                axs[ax_idx].grid(True)
                axs[ax_idx].legend()
    
    # Plot ADX and DI if available
    if has_adx and has_di:
        ax_idx += 1
        
        for col in df.columns:
            if col.startswith('adx_'):
                period = col.split('_')[1]
                axs[ax_idx].plot(df.index, df[col], label=f'ADX({period})', color='black')
        
        for col in df.columns:
            if col.startswith('plus_di_'):
                period = col.split('_')[1]
                axs[ax_idx].plot(df.index, df[col], label=f'+DI({period})', color='green')
            elif col.startswith('minus_di_'):
                period = col.split('_')[1]
                axs[ax_idx].plot(df.index, df[col], label=f'-DI({period})', color='red')
        
        # Add ADX threshold line
        axs[ax_idx].axhline(25, color='blue', linestyle='--', alpha=0.5)
        
        axs[ax_idx].set_ylabel("ADX/DI")
        axs[ax_idx].grid(True)
        axs[ax_idx].legend()
    
    # Plot Stochastics if available
    if has_stoch:
        ax_idx += 1
        
        axs[ax_idx].plot(df.index, df['stoch_k'], label='%K', color='blue')
        axs[ax_idx].plot(df.index, df['stoch_d'], label='%D', color='red')
        
        # Add overbought/oversold lines
        axs[ax_idx].axhline(80, color='red', linestyle='--', alpha=0.5)
        axs[ax_idx].axhline(20, color='green', linestyle='--', alpha=0.5)
        
        axs[ax_idx].set_ylabel("Stochastic")
        axs[ax_idx].set_ylim(0, 100)
        axs[ax_idx].grid(True)
        axs[ax_idx].legend()
    
    # Format x-axis dates
    axs[-1].set_xlabel("Date")
    axs[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    axs[-1].xaxis.set_major_locator(mdates.AutoDateLocator())
    
    plt.tight_layout()
    
    # Save plot if path provided
    if output_path:
        plt.savefig(output_path)
        logger.info(f"Saved visualization to {output_path}")
    
    # Show plot if requested
    if show_plots:
        plt.show()
    else:
        plt.close()

def plot_multi_timeframe_analysis(daily_df: pd.DataFrame, 
                                 weekly_df: pd.DataFrame, 
                                 symbol: str,
                                 output_path: Optional[str] = None,
                                 show_plots: bool = False) -> None:
    """
    Create a visualization comparing multiple timeframes.
    
    Parameters:
    -----------
    daily_df : pd.DataFrame
        DataFrame with daily price and indicator data
    weekly_df : pd.DataFrame
        DataFrame with weekly price and indicator data
    symbol : str
        Symbol being visualized
    output_path : str, optional
        Path to save the plot to
    show_plots : bool
        Whether to display the plot interactively
    """
    logger.info(f"Creating multi-timeframe visualization for {symbol}")
    
    # Create figure with 3 rows and 2 columns
    fig, axs = plt.subplots(3, 2, figsize=(15, 12))
    fig.suptitle(f"{symbol} - Multi-Timeframe Analysis", fontsize=16)
    
    # Row 1: Price Charts
    # Daily price
    axs[0, 0].plot(daily_df.index, daily_df['close'], label='Close', color='blue')
    if 'sma_20' in daily_df.columns:
        axs[0, 0].plot(daily_df.index, daily_df['sma_20'], label='SMA(20)', alpha=0.7)
    axs[0, 0].set_title(f"Daily Price")
    axs[0, 0].set_ylabel("Price")
    axs[0, 0].grid(True)
    axs[0, 0].legend()
    
    # Weekly price
    axs[0, 1].plot(weekly_df.index, weekly_df['close'], label='Close', color='blue')
    if 'sma_20' in weekly_df.columns:
        axs[0, 1].plot(weekly_df.index, weekly_df['sma_20'], label='SMA(20)', alpha=0.7)
    axs[0, 1].set_title(f"Weekly Price")
    axs[0, 1].set_ylabel("Price")
    axs[0, 1].grid(True)
    axs[0, 1].legend()
    
    # Row 2: ADX/DI
    # Daily ADX/DI
    if 'adx_14' in daily_df.columns and 'plus_di_14' in daily_df.columns and 'minus_di_14' in daily_df.columns:
        axs[1, 0].plot(daily_df.index, daily_df['adx_14'], label='ADX(14)', color='black')
        axs[1, 0].plot(daily_df.index, daily_df['plus_di_14'], label='+DI(14)', color='green')
        axs[1, 0].plot(daily_df.index, daily_df['minus_di_14'], label='-DI(14)', color='red')
        axs[1, 0].axhline(25, color='blue', linestyle='--', alpha=0.5)
        axs[1, 0].set_title(f"Daily ADX/DI")
        axs[1, 0].set_ylabel("Value")
        axs[1, 0].grid(True)
        axs[1, 0].legend()
    
    # Weekly ADX/DI
    if 'adx_14' in weekly_df.columns and 'plus_di_14' in weekly_df.columns and 'minus_di_14' in weekly_df.columns:
        axs[1, 1].plot(weekly_df.index, weekly_df['adx_14'], label='ADX(14)', color='black')
        axs[1, 1].plot(weekly_df.index, weekly_df['plus_di_14'], label='+DI(14)', color='green')
        axs[1, 1].plot(weekly_df.index, weekly_df['minus_di_14'], label='-DI(14)', color='red')
        axs[1, 1].axhline(25, color='blue', linestyle='--', alpha=0.5)
        axs[1, 1].set_title(f"Weekly ADX/DI")
        axs[1, 1].set_ylabel("Value")
        axs[1, 1].grid(True)
        axs[1, 1].legend()
    
    # Row 3: RSI or Stochastics
    # Daily RSI
    if 'rsi_14' in daily_df.columns:
        axs[2, 0].plot(daily_df.index, daily_df['rsi_14'], label='RSI(14)', color='purple')
        axs[2, 0].axhline(70, color='red', linestyle='--', alpha=0.5)
        axs[2, 0].axhline(30, color='green', linestyle='--', alpha=0.5)
        axs[2, 0].set_title(f"Daily RSI")
        axs[2, 0].set_ylabel("RSI")
        axs[2, 0].set_ylim(0, 100)
        axs[2, 0].grid(True)
        axs[2, 0].legend()
    
    # Weekly RSI
    if 'rsi_14' in weekly_df.columns:
        axs[2, 1].plot(weekly_df.index, weekly_df['rsi_14'], label='RSI(14)', color='purple')
        axs[2, 1].axhline(70, color='red', linestyle='--', alpha=0.5)
        axs[2, 1].axhline(30, color='green', linestyle='--', alpha=0.5)
        axs[2, 1].set_title(f"Weekly RSI")
        axs[2, 1].set_ylabel("RSI")
        axs[2, 1].set_ylim(0, 100)
        axs[2, 1].grid(True)
        axs[2, 1].legend()
    
    # Format dates for all x-axes
    for i in range(3):
        for j in range(2):
            axs[i, j].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            axs[i, j].xaxis.set_major_locator(mdates.AutoDateLocator())
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])  # Adjust for the title
    
    # Save plot if path provided
    if output_path:
        plt.savefig(output_path)
        logger.info(f"Saved multi-timeframe visualization to {output_path}")
    
    # Show plot if requested
    if show_plots:
        plt.show()
    else:
        plt.close()

def create_swing_trade_report(df: pd.DataFrame, 
                             symbol: str,
                             output_path: Optional[str] = None,
                             show_plots: bool = False) -> pd.DataFrame:
    """
    Create a report of potential swing trade setups.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with price and indicator data
    symbol : str
        Symbol being analyzed
    output_path : str, optional
        Path to save the report to
    show_plots : bool
        Whether to display the plots interactively
        
    Returns:
    --------
    signals : pd.DataFrame
        DataFrame with identified setups
    """
    logger.info(f"Analyzing potential swing trade setups for {symbol}")
    
    # Check for required indicators
    required_indicators = ['adx_14', 'plus_di_14', 'minus_di_14', 'rsi_14']
    missing_indicators = [ind for ind in required_indicators if ind not in df.columns]
    
    if missing_indicators:
        logger.error(f"Missing required indicators: {missing_indicators}")
        return pd.DataFrame()
    
    # Create a DataFrame to store signals
    signals = pd.DataFrame(index=df.index)
    signals['date'] = df.index
    signals['close'] = df['close']
    signals['adx'] = df['adx_14']
    signals['plus_di'] = df['plus_di_14']
    signals['minus_di'] = df['minus_di_14']
    signals['rsi'] = df['rsi_14']
    
    # Determine the trend based on DI lines
    signals['trend'] = 'NONE'
    signals.loc[signals['plus_di'] > signals['minus_di'], 'trend'] = 'UP'
    signals.loc[signals['plus_di'] < signals['minus_di'], 'trend'] = 'DOWN'
    
    # Determine trend strength based on ADX
    signals['trend_strength'] = 'WEAK'
    signals.loc[signals['adx'] >= 20, 'trend_strength'] = 'MODERATE'
    signals.loc[signals['adx'] >= 30, 'trend_strength'] = 'STRONG'
    
    # Check for DI crossovers (potential trend changes)
    signals['di_crossover'] = 'NONE'
    signals['plus_di_prev'] = signals['plus_di'].shift(1)
    signals['minus_di_prev'] = signals['minus_di'].shift(1)
    
    # Bullish crossover
    bullish_cross = (signals['plus_di_prev'] < signals['minus_di_prev']) & (signals['plus_di'] > signals['minus_di'])
    signals.loc[bullish_cross, 'di_crossover'] = 'BULLISH'
    
    # Bearish crossover
    bearish_cross = (signals['plus_di_prev'] > signals['minus_di_prev']) & (signals['plus_di'] < signals['minus_di'])
    signals.loc[bearish_cross, 'di_crossover'] = 'BEARISH'
    
    # Check for reaction setups
    signals['reaction_setup'] = 'NONE'
    
    # Identify potential long setups in uptrend
    uptrend = signals['trend'] == 'UP'
    rsi_oversold = signals['rsi'] < 40
    rsi_turning_up = signals['rsi'] > signals['rsi'].shift(1)
    
    long_setup = uptrend & rsi_oversold & rsi_turning_up
    signals.loc[long_setup, 'reaction_setup'] = 'LONG'
    
    # Identify potential short setups in downtrend
    downtrend = signals['trend'] == 'DOWN'
    rsi_overbought = signals['rsi'] > 60
    rsi_turning_down = signals['rsi'] < signals['rsi'].shift(1)
    
    short_setup = downtrend & rsi_overbought & rsi_turning_down
    signals.loc[short_setup, 'reaction_setup'] = 'SHORT'
    
    # Filter to only include rows with signals
    signal_rows = signals[signals['reaction_setup'] != 'NONE']
    
    logger.info(f"Found {len(signal_rows)} potential swing trade setups for {symbol}")
    
    # If output path provided, save report
    if output_path:
        signal_rows.to_csv(output_path)
        logger.info(f"Saved swing trade report to {output_path}")
    
    # If plots requested, visualize the setups
    if show_plots and not signal_rows.empty:
        num_signals = min(len(signal_rows), 5)  # Limit to 5 plots
        
        for i, (idx, row) in enumerate(signal_rows.head(num_signals).iterrows()):
            # Get 20 bars before and 10 bars after the signal
            start_idx = df.index.get_loc(idx) - 20
            end_idx = df.index.get_loc(idx) + 10
            
            if start_idx < 0:
                start_idx = 0
            if end_idx >= len(df):
                end_idx = len(df) - 1
            
            plot_df = df.iloc[start_idx:end_idx+1]
            
            # Create plot
            fig, axs = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
            
            # Price plot
            axs[0].plot(plot_df.index, plot_df['close'], label='Close', color='blue')
            if 'sma_20' in plot_df.columns:
                axs[0].plot(plot_df.index, plot_df['sma_20'], label='SMA(20)', alpha=0.7)
            
            # Highlight the signal bar
            axs[0].scatter([idx], [row['close']], color='red', s=100, zorder=5)
            
            axs[0].set_title(f"{symbol} - {row['reaction_setup']} Setup on {idx.date()} (ADX: {row['adx']:.1f}, RSI: {row['rsi']:.1f})")
            axs[0].set_ylabel("Price")
            axs[0].grid(True)
            axs[0].legend()
            
            # ADX/DI plot
            axs[1].plot(plot_df.index, plot_df['adx_14'], label='ADX', color='black')
            axs[1].plot(plot_df.index, plot_df['plus_di_14'], label='+DI', color='green')
            axs[1].plot(plot_df.index, plot_df['minus_di_14'], label='-DI', color='red')
            axs[1].axhline(25, color='blue', linestyle='--', alpha=0.5)
            
            # Highlight the signal bar
            axs[1].scatter([idx], [row['adx']], color='red', s=100, zorder=5)
            
            axs[1].set_ylabel("ADX/DI")
            axs[1].grid(True)
            axs[1].legend()
            
            # RSI plot
            axs[2].plot(plot_df.index, plot_df['rsi_14'], label='RSI', color='purple')
            axs[2].axhline(70, color='red', linestyle='--', alpha=0.5)
            axs[2].axhline(30, color='green', linestyle='--', alpha=0.5)
            
            # Highlight the signal bar
            axs[2].scatter([idx], [row['rsi']], color='red', s=100, zorder=5)
            
            axs[2].set_ylabel("RSI")
            axs[2].set_ylim(0, 100)
            axs[2].grid(True)
            axs[2].legend()
            
            # Format dates
            axs[2].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            axs[2].xaxis.set_major_locator(mdates.AutoDateLocator())
            
            plt.tight_layout()
            plt.show()
    
    return signal_rows