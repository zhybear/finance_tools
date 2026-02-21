"""Portfolio Performance Analyzer

Compares stock portfolio performance against S&P 500 benchmark.
Calculates CAGR (Compound Annual Growth Rate) for individual trades and overall portfolio.
"""

import yfinance as yf
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
import argparse
import sys

# Constants
DAYS_PER_YEAR = 365.25
SP500_SYMBOL = '^GSPC'


def load_trades_from_csv(path: str) -> List[Dict]:
    """
    Load and validate trades from a CSV file.
    
    Args:
        path: Path to CSV file with columns: symbol, shares, purchase_date, price
    
    Returns:
        List of trade dictionaries with validated and normalized data
    
    Raises:
        ValueError: If CSV is missing required columns
    """
    df = pd.read_csv(path)
    required = {"symbol", "shares", "purchase_date", "price"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")

    # Normalize types
    df = df.copy()
    df["symbol"] = df["symbol"].astype(str).str.strip()
    df["shares"] = pd.to_numeric(df["shares"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    parsed_dates = pd.to_datetime(df["purchase_date"], errors="coerce")
    df["purchase_date"] = parsed_dates.dt.strftime("%Y-%m-%d")

    # Drop rows with invalid types
    df = df.dropna(subset=["symbol", "shares", "price", "purchase_date"])

    ordered_cols = ["symbol", "shares", "purchase_date", "price"]
    return df[ordered_cols].to_dict(orient="records")

class PortfolioAnalyzer:
    """
    Analyzes stock portfolio performance against S&P 500 benchmark.
    
    Attributes:
        trades: List of trade dictionaries
        _stock_history_cache: Cache of downloaded stock price histories
        _sp500_full_history: Cache of S&P 500 price history
    """
    
    def __init__(self, trades: List[Dict]):
        """
        Initialize portfolio analyzer.
        
        Args:
            trades: List of dictionaries with keys: symbol, shares, purchase_date, price
                   Example: {'symbol': 'AAPL', 'shares': 100, 'purchase_date': '2020-01-01', 'price': 75.5}
        """
        self.trades = trades
        self._stock_history_cache = {}
        self._sp500_full_history = None

    # ============================================================================
    # Data Normalization and Extraction
    # ============================================================================
    
    def _normalize_history_index(self, hist: pd.DataFrame) -> pd.DataFrame:
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

    def _normalize_datetime(self, dt) -> pd.Timestamp:
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

    def _extract_history(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
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

    def _download_history(self, tickers: List[str], start_date: str) -> pd.DataFrame:
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

    def _prepare_histories(self, trades: List[Dict]) -> None:
        """
        Bulk download and cache all stock and S&P 500 price histories.
        
        This optimization downloads all unique symbols in one API call,
        significantly faster than individual downloads.
        
        Args:
            trades: List of trade dictionaries
        """
        symbols = {trade["symbol"] for trade in trades}
        if not symbols:
            return

        # Find earliest purchase date to minimize data download
        earliest_date = min(trade["purchase_date"] for trade in trades)

        # Bulk download all stock histories
        data = self._download_history(list(symbols), earliest_date)

        if not data.empty:
            if isinstance(data.columns, pd.MultiIndex):
                # Extract and cache each symbol's history
                for symbol in symbols:
                    symbol_hist = self._extract_history(data, symbol).dropna(how="all")
                    if not symbol_hist.empty:
                        self._stock_history_cache[symbol] = self._normalize_history_index(symbol_hist)
            else:
                # Single symbol case
                symbol = next(iter(symbols))
                self._stock_history_cache[symbol] = self._normalize_history_index(data)

        # Download S&P 500 benchmark history once
        if self._sp500_full_history is None:
            sp500_data = self._download_history([SP500_SYMBOL], earliest_date)
            sp500_hist = self._extract_history(sp500_data, SP500_SYMBOL)
            self._sp500_full_history = self._normalize_history_index(sp500_hist)

    # ============================================================================
    # Validation
    # ============================================================================
    
    def _validate_trade(self, trade: Dict) -> bool:
        """
        Validate that a trade has all required fields with correct types and values.
        
        Args:
            trade: Trade dictionary to validate
            
        Returns:
            True if valid, False otherwise (prints error message)
        """
        required_keys = {"symbol", "shares", "purchase_date", "price"}
        
        # Check if trade is a dictionary
        if not isinstance(trade, dict):
            print("Invalid trade: expected dict")
            return False
        
        # Check for missing keys
        missing = required_keys - trade.keys()
        if missing:
            print(f"Invalid trade: missing keys {missing}")
            return False
        
        # Validate symbol
        if not isinstance(trade["symbol"], str) or not trade["symbol"].strip():
            print("Invalid trade: symbol must be a non-empty string")
            return False
        
        # Validate shares
        if not isinstance(trade["shares"], (int, float)) or trade["shares"] <= 0:
            print("Invalid trade: shares must be a positive number")
            return False
        
        # Validate price
        if not isinstance(trade["price"], (int, float)) or trade["price"] <= 0:
            print("Invalid trade: price must be a positive number")
            return False
        
        # Validate purchase date format
        if not isinstance(trade["purchase_date"], str):
            print("Invalid trade: purchase_date must be a string in YYYY-MM-DD format")
            return False
        
        try:
            datetime.fromisoformat(trade["purchase_date"])
        except ValueError:
            print("Invalid trade: purchase_date must be in YYYY-MM-DD format")
            return False
        
        return True

    # ============================================================================
    # Performance Calculations
    # ============================================================================
    
    def calculate_cagr(self, start_value: float, end_value: float, years: float) -> float:
        """
        Calculate Compound Annual Growth Rate (CAGR).
        
        Formula: CAGR = ((End Value / Start Value) ^ (1 / Years) - 1) * 100
        
        Args:
            start_value: Initial investment value
            end_value: Final investment value
            years: Time period in years
            
        Returns:
            CAGR as a percentage (e.g., 15.5 for 15.5%)
        """
        if start_value <= 0 or years <= 0:
            return 0.0
        return (pow(end_value / start_value, 1 / years) - 1) * 100

    def get_stock_performance(
        self, 
        symbol: str, 
        purchase_date: str, 
        shares: int, 
        purchase_price: float
    ) -> Optional[Dict]:
        """
        Calculate performance metrics for a single trade.
        
        Compares stock performance against S&P 500 benchmark using same investment amount.
        
        Args:
            symbol: Stock ticker symbol
            purchase_date: Purchase date in YYYY-MM-DD format
            shares: Number of shares purchased
            purchase_price: Purchase price per share
            
        Returns:
            Dictionary with performance metrics or None if data unavailable:
                - symbol, shares, purchase_date, purchase_price
                - current_price, initial_value, current_value
                - stock_cagr, sp500_cagr, sp500_current_value
                - outperformance (stock CAGR - S&P 500 CAGR)
                - years_held
        """
        try:
            hist = self._stock_history_cache.get(symbol)
            if hist is None or hist.empty:
                stock = yf.Ticker(symbol)
                hist = stock.history(start=purchase_date)
                hist = self._normalize_history_index(hist)
                self._stock_history_cache[symbol] = hist

            purchase_dt = self._normalize_datetime(pd.to_datetime(purchase_date))
            hist = hist.loc[hist.index >= purchase_dt]

            if hist.empty:
                return None

            current_price = hist['Close'].iloc[-1]
            current_date = self._normalize_datetime(hist.index[-1])

            years_held = (current_date - purchase_dt).days / DAYS_PER_YEAR
            if years_held <= 0:
                print(f"Invalid holding period for {symbol}: purchase_date {purchase_date} is not before latest data date {current_date.date()}")
                return None

            # Calculate stock performance
            initial_value = purchase_price * shares
            current_value = current_price * shares
            stock_cagr = self.calculate_cagr(initial_value, current_value, years_held)

            # Calculate S&P 500 benchmark for same investment amount and period
            if self._sp500_full_history is not None and not self._sp500_full_history.empty:
                sp500_hist = self._sp500_full_history.loc[self._sp500_full_history.index >= purchase_dt]
            else:
                # Fallback: individual download if bulk download failed
                sp500 = yf.Ticker(SP500_SYMBOL)
                sp500_hist = sp500.history(start=purchase_date)
                sp500_hist = self._normalize_history_index(sp500_hist)
                sp500_hist = sp500_hist.loc[sp500_hist.index >= purchase_dt]
            if sp500_hist.empty:
                return None
            sp500_purchase_price = sp500_hist['Close'].iloc[0]
            sp500_current_price = sp500_hist['Close'].iloc[-1]

            # Calculate what the same investment would be worth in S&P 500
            sp500_current_value = (sp500_current_price / sp500_purchase_price) * initial_value
            sp500_cagr = self.calculate_cagr(initial_value, sp500_current_value, years_held)

            return {
                'symbol': symbol,
                'shares': shares,
                'purchase_date': purchase_date,
                'purchase_price': purchase_price,
                'current_price': current_price,
                'initial_value': initial_value,
                'current_value': current_value,
                'stock_cagr': stock_cagr,
                'sp500_cagr': sp500_cagr,
                'sp500_current_value': sp500_current_value,
                'outperformance': stock_cagr - sp500_cagr,
                'years_held': years_held
            }
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None

    # ============================================================================
    # Portfolio Analysis
    # ============================================================================
    
    def analyze_portfolio(self) -> Dict:
        """
        Analyze entire portfolio performance with investment-weighted CAGR.
        
        Uses investment-weighted average holding period to calculate portfolio CAGR,
        ensuring larger investments have proportionally more influence on the result.
        
        Returns:
            Dictionary containing:
                - trades: List of individual trade performance dictionaries
                - total_initial_value: Total amount invested
                - total_current_value: Current portfolio value
                - total_sp500_current_value: Expected value if invested in S&P 500
                - portfolio_cagr: Portfolio CAGR percentage
                - sp500_cagr: Benchmark S&P 500 CAGR percentage
                - portfolio_outperformance: Portfolio CAGR - S&P 500 CAGR
        """
        results = []
        total_initial_value = 0
        total_current_value = 0
        total_sp500_current_value = 0
        weighted_years_sum = 0

        valid_trades = [trade for trade in self.trades if self._validate_trade(trade)]
        self._prepare_histories(valid_trades)

        # Calculate performance for each trade
        for trade in valid_trades:
            perf = self.get_stock_performance(
                symbol=trade['symbol'],
                purchase_date=trade['purchase_date'],
                shares=trade['shares'],
                purchase_price=trade['price']
            )
            if perf:
                results.append(perf)
                total_initial_value += perf['initial_value']
                total_current_value += perf['current_value']
                total_sp500_current_value += perf['sp500_current_value']
                weighted_years_sum += perf['initial_value'] * perf['years_held']

        # Calculate investment-weighted average holding period
        # This ensures each dollar invested has equal weight in the time calculation
        if total_initial_value > 0:
            weighted_years = weighted_years_sum / total_initial_value
            portfolio_cagr = self.calculate_cagr(total_initial_value, total_current_value, weighted_years)
            sp500_cagr = self.calculate_cagr(total_initial_value, total_sp500_current_value, weighted_years)
        else:
            weighted_years = 0
            portfolio_cagr = 0
            sp500_cagr = 0

        return {
            'trades': results,
            'total_initial_value': total_initial_value,
            'total_current_value': total_current_value,
            'total_sp500_current_value': total_sp500_current_value,
            'portfolio_cagr': portfolio_cagr,
            'sp500_cagr': sp500_cagr,
            'portfolio_outperformance': portfolio_cagr - sp500_cagr
        }

    # ============================================================================
    # Reporting
    # ============================================================================
    
    def print_report(self) -> None:
        """
        Print formatted portfolio analysis report to console.
        
        Displays individual trade performance and portfolio summary with:
        - Current values and CAGR for each trade
        - Portfolio totals and weighted CAGR
        - Comparison against S&P 500 benchmark
        """
        analysis = self.analyze_portfolio()

        if not analysis['trades']:
            print("No valid trades to analyze.")
            return

        print("\n=== INDIVIDUAL STOCK PERFORMANCE ===")
        for trade in analysis['trades']:
            print(f"\n{trade['symbol']}:")
            print(f"  Shares: {trade['shares']} @ ${trade['purchase_price']:.2f}")
            print(f"  Current Price: ${trade['current_price']:.2f}")
            print(f"  Stock CAGR: {trade['stock_cagr']:.2f}%")
            print(f"  S&P 500 CAGR: {trade['sp500_cagr']:.2f}%")
            print(f"  Outperformance: {trade['outperformance']:.2f}%")

        print("\n=== PORTFOLIO SUMMARY ===")
        print(f"Initial Investment: ${analysis['total_initial_value']:.2f}")
        print(f"Current Value: ${analysis['total_current_value']:.2f}")
        print(f"Expected Value if Invested in S&P 500: ${analysis['total_sp500_current_value']:.2f}")
        print(f"Portfolio CAGR: {analysis['portfolio_cagr']:.2f}%")
        print(f"S&P 500 CAGR: {analysis['sp500_cagr']:.2f}%")
        print(f"Portfolio Outperformance: {analysis['portfolio_outperformance']:.2f}%")


# ============================================================================
# Command Line Interface
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Portfolio Analyzer")
    parser.add_argument("--csv", help="Path to CSV file with trades")
    args = parser.parse_args()

    if args.csv:
        try:
            trades = load_trades_from_csv(args.csv)
        except Exception as e:
            print(f"Failed to load CSV: {e}")
            sys.exit(1)
    else:
        trades = [
            {"symbol": "AAPL", "shares": 100, "purchase_date": "2020-01-02", "price": 75.5},
            {"symbol": "MSFT", "shares": 50, "purchase_date": "2021-01-04", "price": 220.0},
        ]

    analyzer = PortfolioAnalyzer(trades)
    analyzer.print_report()