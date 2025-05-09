# Swing Trading System

A comprehensive swing trading system implementing Ashwani Gujral's "Entering Trends on Reaction" methodology from his book "How to Make Money Trading Derivatives: An Insider's Guide."

## Overview

This system identifies trends in higher timeframes using the ADX/DI system and then enters on reactions (pullbacks/rallies) in lower timeframes, enhanced with Nifty market context for Indian markets.

### Key Components

- **ADX/DI System**: Uses Wilder's Average Directional Movement Index to identify trending vs. trading markets
- **Multi-Timeframe Analysis**: Analyzes weekly charts for trend direction and daily charts for entry timing
- **Reaction Entries**: Enters trades during pullbacks in uptrends and rallies in downtrends using MA, RSI, and stochastics
- **Nifty Context**: Aligns individual stock trades with the broader market trend
- **Position Sizing**: Adjusts position size based on trend strength and market alignment
- **Risk Management**: Calculates stop losses based on pivot points

## Setup

### Prerequisites

- Python 3.8 or higher
- TA-Lib (Technical Analysis Library)
- Backtrader
- Dhan-Tradehull API access

## Implementation Plan

The implementation follows this phased approach:

1. **Phase 1**: Environment Setup and Data Infrastructure
2. **Phase 2**: Indicator and Signal Implementation
3. **Phase 3**: Risk Management and Position Sizing
4. **Phase 4**: Strategy Integration and Basic Backtesting
5. **Phase 5**: Validation Framework Implementation
6. **Phase 6**: Comprehensive Backtesting and Optimization
7. **Phase 7**: Live Trading Implementation
8. **Phase 8**: Performance Analysis and Reporting

## Directory Structure

- `configs/`: Configuration files
- `data/`: Market data (raw and processed)
- `swing_trading_system/`: Core system modules
  - `data_feeds/`: Data acquisition modules
  - `strategies/`: Trading strategy implementations
  - `indicators/`: Technical indicators and signal generators
  - `utils/`: Utility functions and tools
  - `risk_management/`: Risk management modules
  - `backtest/`: Backtesting framework
- `tests/`: Test scripts and utilities
- `logs/`: Log files"

