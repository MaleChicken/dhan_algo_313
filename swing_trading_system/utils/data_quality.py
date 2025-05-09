# swing_trading_system/utils/data_quality.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

def analyze_data_quality(df: pd.DataFrame, symbol: str, timeframe: str) -> Dict:
    """
    Perform comprehensive data quality analysis on price data.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with price data
    symbol : str
        Symbol being analyzed
    timeframe : str
        Timeframe of the data
        
    Returns:
    --------
    results : dict
        Dictionary with analysis results
    """
    results = {
        'symbol': symbol,
        'timeframe': timeframe,
        'start_date': df.index.min(),
        'end_date': df.index.max(),
        'total_bars': len(df),
        'issues': [],
        'statistics': {},
        'anomalies': []
    }
    
    # Check for basic data availability and completeness
    results['statistics']['missing_values_count'] = df.isnull().sum().to_dict()
    results['statistics']['duplicate_dates_count'] = df.index.duplicated().sum()
    
    if df.isnull().any().any():
        results['issues'].append("Data contains missing values")
    
    if df.index.duplicated().any():
        results['issues'].append("Data contains duplicate dates")
    
    # Check for price anomalies
    price_zero = (df['close'] <= 0).sum()
    if price_zero > 0:
        results['issues'].append(f"Data contains {price_zero} records with close price <= 0")
    
    high_low_issue = (df['high'] < df['low']).sum()
    if high_low_issue > 0:
        results['issues'].append(f"Data contains {high_low_issue} records where high < low")
    
    # Check for extreme price movements
    daily_returns = df['close'].pct_change()
    results['statistics']['daily_returns_mean'] = daily_returns.mean()
    results['statistics']['daily_returns_std'] = daily_returns.std()
    results['statistics']['daily_returns_min'] = daily_returns.min()
    results['statistics']['daily_returns_max'] = daily_returns.max()
    
    # Identify extreme price movements (potential data errors)
    threshold = 0.20  # 20% daily move
    extreme_moves = daily_returns.abs() > threshold
    extreme_moves_count = extreme_moves.sum()
    
    if extreme_moves_count > 0:
        results['issues'].append(f"Data contains {extreme_moves_count} days with >20% price movement")
        
        # Add details of extreme moves to anomalies
        for idx in df.index[extreme_moves]:
            date_str = idx.strftime('%Y-%m-%d')
            pct_change = daily_returns.loc[idx] * 100
            results['anomalies'].append({
                'date': date_str,
                'close': df.loc[idx, 'close'],
                'previous_close': df.loc[idx - pd.Timedelta(days=1), 'close'] if idx - pd.Timedelta(days=1) in df.index else None,
                'pct_change': pct_change,
                'type': 'extreme_price_movement'
            })
    
    # Check for gaps in daily data
    if timeframe == 'daily':
        all_days = pd.date_range(start=df.index.min(), end=df.index.max(), freq='B')
        missing_days = all_days.difference(df.index)
        results['statistics']['missing_days_count'] = len(missing_days)
        
        if len(missing_days) > 0:
            results['issues'].append(f"Data contains {len(missing_days)} missing business days")
            
            # Add a sample of missing days to anomalies
            for day in missing_days[:10]:  # Show first 10 missing days
                results['anomalies'].append({
                    'date': day.strftime('%Y-%m-%d'),
                    'type': 'missing_day'
                })
    
    # Check for volume anomalies
    if 'volume' in df.columns:
        zero_volume = (df['volume'] <= 0).sum()
        results['statistics']['zero_volume_count'] = zero_volume
        
        if zero_volume > 0:
            results['issues'].append(f"Data contains {zero_volume} records with volume <= 0")
    
    # Check for open/close anomalies
    if 'open' in df.columns and 'close' in df.columns:
        unchanged_bars = (df['open'] == df['close']).sum()
        results['statistics']['unchanged_bars_count'] = unchanged_bars
        
        if unchanged_bars > len(df) * 0.5:  # If more than 50% of bars are unchanged
            results['issues'].append(f"Data contains {unchanged_bars} ({unchanged_bars/len(df)*100:.1f}%) bars with unchanged price")
    
    return results

def generate_quality_report(results: Dict, output_dir: str = 'data/quality_reports') -> str:
    """
    Generate a data quality report from analysis results.
    
    Parameters:
    -----------
    results : dict
        Dictionary with analysis results
    output_dir : str
        Directory to save reports to
        
    Returns:
    --------
    report_path : str
        Path to the generated report
    """
    import os
    import json
    from datetime import datetime
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Create report filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_name = f"{results['symbol']}_{results['timeframe']}_quality_{timestamp}"
    
    # Save JSON report
    json_path = os.path.join(output_dir, f"{report_name}.json")
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=4, default=str)  # default=str handles datetime serialization
    
    # Generate HTML report
    html_path = os.path.join(output_dir, f"{report_name}.html")
    
    with open(html_path, 'w') as f:
        f.write(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Data Quality Report: {results['symbol']} ({results['timeframe']})</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                .issue {{ color: red; }}
                .statistic {{ margin-bottom: 5px; }}
                .anomaly {{ margin-bottom: 10px; border-left: 3px solid #ddd; padding-left: 10px; }}
                .summary {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>Data Quality Report</h1>
            <div class="summary">
                <p><strong>Symbol:</strong> {results['symbol']}</p>
                <p><strong>Timeframe:</strong> {results['timeframe']}</p>
                <p><strong>Period:</strong> {results['start_date']} to {results['end_date']}</p>
                <p><strong>Total Bars:</strong> {results['total_bars']}</p>
                <p><strong>Issues Found:</strong> {len(results['issues'])}</p>
            </div>
            
            <h2>Issues</h2>
            <ul>
        """)
        
        if results['issues']:
            for issue in results['issues']:
                f.write(f"<li class='issue'>{issue}</li>\n")
        else:
            f.write("<li>No issues found.</li>\n")
        
        f.write("""
            </ul>
            
            <h2>Statistics</h2>
            <div class="statistics">
        """)
        
        for key, value in results['statistics'].items():
            if isinstance(value, dict):
                f.write(f"<h3>{key}</h3>\n<ul>\n")
                for k, v in value.items():
                    f.write(f"<li class='statistic'>{k}: {v}</li>\n")
                f.write("</ul>\n")
            else:
                f.write(f"<p class='statistic'><strong>{key}:</strong> {value}</p>\n")
        
        f.write("""
            </div>
            
            <h2>Anomalies</h2>
            <div class="anomalies">
        """)
        
        if results['anomalies']:
            for anomaly in results['anomalies']:
                f.write("<div class='anomaly'>\n")
                for key, value in anomaly.items():
                    f.write(f"<p><strong>{key}:</strong> {value}</p>\n")
                f.write("</div>\n")
        else:
            f.write("<p>No anomalies detected.</p>\n")
        
        f.write("""
            </div>
        </body>
        </html>
        """)
    
    logger.info(f"Generated data quality report: {html_path}")
    return html_path

def plot_data_quality(df: pd.DataFrame, symbol: str, timeframe: str, output_dir: str = 'data/quality_reports') -> str:
    """
    Generate data quality visualization.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with price data
    symbol : str
        Symbol being analyzed
    timeframe : str
        Timeframe of the data
    output_dir : str
        Directory to save plots to
        
    Returns:
    --------
    plot_path : str
        Path to the generated plot
    """
    import os
    from datetime import datetime
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Create plot filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    plot_name = f"{symbol}_{timeframe}_quality_{timestamp}.png"
    plot_path = os.path.join(output_dir, plot_name)
    
    # Create figure with subplots
    fig, axs = plt.subplots(3, 1, figsize=(12, 15), sharex=True)
    
    # Plot 1: Price with anomalies
    axs[0].plot(df.index, df['close'], label='Close Price')
    axs[0].set_title(f"{symbol} ({timeframe}) - Price with Potential Anomalies")
    axs[0].set_ylabel("Price")
    axs[0].grid(True)
    
    # Highlight extreme price movements
    daily_returns = df['close'].pct_change()
    extreme_moves = daily_returns.abs() > 0.20  # 20% daily move
    if extreme_moves.any():
        axs[0].scatter(
            df.index[extreme_moves], 
            df.loc[extreme_moves, 'close'],
            color='red',
            s=50,
            label='Extreme Moves'
        )
    
    axs[0].legend()
    
    # Plot 2: Daily Returns
    axs[1].plot(df.index, daily_returns, label='Daily Returns', color='blue')
    axs[1].axhline(y=0, color='k', linestyle='-', alpha=0.3)
    axs[1].axhline(y=0.20, color='r', linestyle='--', alpha=0.7, label='+20%')
    axs[1].axhline(y=-0.20, color='r', linestyle='--', alpha=0.7, label='-20%')
    axs[1].set_title(f"{symbol} ({timeframe}) - Daily Returns")
    axs[1].set_ylabel("Returns")
    axs[1].grid(True)
    axs[1].legend()
    
    # Plot 3: Volume
    if 'volume' in df.columns:
        axs[2].bar(df.index, df['volume'], label='Volume', color='green', alpha=0.6)
        axs[2].set_title(f"{symbol} ({timeframe}) - Volume")
        axs[2].set_ylabel("Volume")
        axs[2].grid(True)
        
        # Highlight zero volume days
        zero_volume = df['volume'] <= 0
        if zero_volume.any():
            axs[2].scatter(
                df.index[zero_volume],
                df.loc[zero_volume, 'volume'],
                color='red',
                s=50,
                label='Zero Volume'
            )
            axs[2].legend()
    else:
        axs[2].text(0.5, 0.5, "Volume data not available", horizontalalignment='center', verticalalignment='center', transform=axs[2].transAxes)
    
    axs[2].set_xlabel("Date")
    
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()
    
    logger.info(f"Generated data quality plot: {plot_path}")
    return plot_path