"""Utility functions for portfolio analyzer."""

import pandas as pd
import yfinance as yf
import logging

logger = logging.getLogger(__name__)

DAYS_PER_YEAR = 365.25
SP500_SYMBOL = '^GSPC'


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero.
    
    Args:
        numerator: Dividend
        denominator: Divisor
        default: Value to return if denominator is zero
        
    Returns:
        Result of numerator / denominator, or default if denominator <= 0
    """
    return (numerator / denominator) if denominator > 0 else default


def normalize_history_index(hist: pd.DataFrame) -> pd.DataFrame:
    """
    Remove timezone information from DataFrame index to enable comparisons.
    
    Args:
        hist: DataFrame with datetime index
        
    Returns:
        DataFrame with timezone-naive index
    """
    if hist.empty:
        return hist
    if getattr(hist.index, "tz", None) is not None:
        hist = hist.copy()
        hist.index = hist.index.tz_localize(None)
    return hist


def normalize_datetime(dt: pd.Timestamp) -> pd.Timestamp:
    """
    Remove timezone information from datetime object.
    
    Args:
        dt: Datetime or Timestamp object
        
    Returns:
        Timezone-naive Timestamp
    """
    if getattr(dt, "tzinfo", None) is not None:
        return dt.tz_localize(None)
    return dt


def extract_history(data: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Extract single symbol's data from multi-ticker DataFrame.
    
    Args:
        data: DataFrame from yf.download (may have MultiIndex columns)
        symbol: Stock symbol to extract
        
    Returns:
        DataFrame with single symbol's price data
    """
    if data.empty:
        return data
        
    # Handle MultiIndex columns from bulk download
    if isinstance(data.columns, pd.MultiIndex):
        level0 = data.columns.get_level_values(0)
        level1 = data.columns.get_level_values(1)
        if symbol in level0:
            return data.xs(symbol, level=0, axis=1)
        if symbol in level1:
            return data.xs(symbol, level=1, axis=1)
        return pd.DataFrame()
    
    # Single symbol download
    return data


def download_history(tickers: list[str], start_date: str) -> pd.DataFrame:
    """
    Download historical price data from Yahoo Finance.
    
    Args:
        tickers: List of stock symbols
        start_date: Start date in YYYY-MM-DD format
        
    Returns:
        DataFrame with historical price data or empty DataFrame on failure
    """
    try:
        return yf.download(
            tickers=" ".join(sorted(tickers)),
            start=start_date,
            group_by="ticker",
            auto_adjust=False,
            progress=False,
            threads=True,
        )
    except Exception:
        return pd.DataFrame()
