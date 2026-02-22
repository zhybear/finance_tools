"""CSV data loaders for portfolio analyzer."""

from datetime import datetime
from typing import List, Dict
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def load_trades_from_csv(path: str) -> List[Dict]:
    """
    Load and validate trades from a CSV file.
    
    CSV Format:
        Symbol must be valid stock tickers, shares must be positive, 
        purchase_date in YYYY-MM-DD format, price must be positive.
    
    Args:
        path: Path to CSV file with columns: symbol, shares, purchase_date, price
    
    Returns:
        List of trade dictionaries with validated and normalized data
    
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If CSV is missing required columns or has invalid structure
    """
    try:
        if not path or not path.endswith('.csv'):
            raise ValueError(f"Expected CSV file, got: {path}")
        
        df = pd.read_csv(path)
        required = {"symbol", "shares", "purchase_date", "price"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}. Expected: {required}")
        
        if len(df) == 0:
            raise ValueError("CSV file is empty")
        
        # Normalize types
        df = df.copy()
        df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()
        df["shares"] = pd.to_numeric(df["shares"], errors="coerce")
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        parsed_dates = pd.to_datetime(df["purchase_date"], errors="coerce")
        df["purchase_date"] = parsed_dates.dt.strftime("%Y-%m-%d")
        
        # Drop rows with invalid types
        df = df.dropna(subset=["symbol", "shares", "price", "purchase_date"])
        
        if len(df) == 0:
            raise ValueError("No valid trades found in CSV after validation")
        
        ordered_cols = ["symbol", "shares", "purchase_date", "price"]
        trades = df[ordered_cols].to_dict(orient="records")
        logger.info(f"Loaded {len(trades)} trades from {path}")
        return trades
    except FileNotFoundError:
        logger.error(f"CSV file not found: {path}")
        raise
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        raise
