"""Portfolio Performance Analyzer

A comprehensive tool for analyzing stock portfolio performance against the S&P 500 benchmark.
Calculates both CAGR (Compound Annual Growth Rate) and XIRR (Extended Internal Rate of Return)
for individual trades and overall portfolio performance.

Features:
- Load trades from CSV file
- Calculate per-trade and per-symbol performance metrics
- Generate PDF and text reports with visualizations
- Compare against S&P 500 benchmark
- Account for irregular investment timing with XIRR

Usage:
    python3 stock.py --csv trades.csv --output report.txt --pdf report.pdf

Author: Portfolio Analytics
Version: 1.0.0
"""

import yfinance as yf
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import pandas as pd
import argparse
import sys
import numpy as np
from scipy.optimize import newton
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Try to import XIRR calculation library
try:
    import numpy_financial as npf
    XIRR_AVAILABLE = True
except ImportError:
    XIRR_AVAILABLE = False

# Try to import visualization libraries
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend for PDF generation
    import seaborn as sns
    VISUALIZATIONS_AVAILABLE = True
except ImportError:
    VISUALIZATIONS_AVAILABLE = False

# Constants
DAYS_PER_YEAR = 365.25
SP500_SYMBOL = '^GSPC'


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

class PortfolioAnalyzer:
    """
    Analyzes stock portfolio performance against S&P 500 benchmark.
    
    This class provides comprehensive analysis of stock trades including:
    - Individual trade performance metrics (CAGR, XIRR)
    - Symbol-level aggregated metrics
    - Portfolio-wide performance summary
    - Comparison against S&P 500 index
    
    Attributes:
        trades: List of trade dictionaries
        _stock_history_cache: Cache of downloaded stock price histories (optimization)
        _sp500_full_history: Cache of S&P 500 price history
    
    Example:
        analyzer = PortfolioAnalyzer(trades)
        analysis = analyzer.analyze_portfolio()
        analyzer.print_report()
        analyzer.generate_pdf_report('report.pdf')
    """
    
    def __init__(self, trades: List[Dict]):
        """
        Initialize portfolio analyzer.
        
        Args:
            trades: List of dictionaries with keys:
                   - symbol (str): Stock ticker symbol 
                   - shares (float): Number of shares
                   - purchase_date (str): Purchase date in YYYY-MM-DD format
                   - price (float): Purchase price per share
                   
        Example:
            trades = [
                {'symbol': 'AAPL', 'shares': 100, 'purchase_date': '2020-01-01', 'price': 75.5},
                {'symbol': 'MSFT', 'shares': 50, 'purchase_date': '2020-06-15', 'price': 200.0}
            ]
            analyzer = PortfolioAnalyzer(trades)
        """
        if not isinstance(trades, list):
            raise TypeError(f"trades must be a list, got {type(trades)}")
        
        self.trades = trades
        self._stock_history_cache = {}
        self._sp500_full_history = None
        self._analysis_cache = None

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

    def _normalize_datetime(self, dt: pd.Timestamp) -> pd.Timestamp:
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
    
    def _safe_divide(self, numerator: float, denominator: float, default: float = 0.0) -> float:
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

    def calculate_xirr(self, dates: List[str], cash_flows: List[float]) -> float:
        """
        Calculate Extended Internal Rate of Return (XIRR).
        
        XIRR accounts for the precise timing of cash flows, providing more accurate returns
        when investments are made at different times. Uses Newton-Raphson root finding to
        solve: NPV = Σ(CF / (1+r)^(Years)) = 0
        
        Args:
            dates: List of dates in YYYY-MM-DD format for each cash flow
            cash_flows: List of cash flows (negative for investments, positive for returns)
                       Must have at least 2 cash flows with different signs
            
        Returns:
            XIRR as a percentage (e.g., 15.5 for 15.5%)
            Returns 0.0 if XIRR cannot be calculated (singular matrix, no solution, etc.)
        """
        if len(dates) != len(cash_flows) or len(dates) < 2:
            return 0.0
        
        # Check for at least one positive and one negative cash flow
        if all(cf >= 0 for cf in cash_flows) or all(cf <= 0 for cf in cash_flows):
            logger.debug(f"XIRR requires both positive and negative cash flows")
            return 0.0
        
        try:
            # For simple 2-cash-flow case, XIRR equals CAGR mathematically
            if len(dates) == 2 and len(cash_flows) == 2:
                initial = abs(cash_flows[0])
                final = cash_flows[1]
                if initial > 0 and final >= 0:
                    years = (pd.to_datetime(dates[1]) - pd.to_datetime(dates[0])).days / DAYS_PER_YEAR
                    if years > 0:
                        ratio = final / initial
                        if ratio > 0:
                            xirr_decimal = (ratio ** (1.0 / years)) - 1.0
                            return xirr_decimal * 100
            
            # Convert date strings to datetime objects
            date_objects = [pd.to_datetime(d) for d in dates]
            
            # Calculate days from first date for each cash flow
            start_date = date_objects[0]
            days_from_start = [(d - start_date).days for d in date_objects]
            
            # Define NPV function for root finding
            def npv_func(rate):
                """Calculate NPV for given rate (as decimal, not percentage)"""
                npv = 0
                for i, cf in enumerate(cash_flows):
                    days = days_from_start[i]
                    years = days / DAYS_PER_YEAR
                    if rate <= -1:  # Avoid domain errors
                        return float('inf')
                    npv += cf / ((1 + rate) ** years)
                return npv
            
            # Try multiple initial guesses to find convergence
            for initial_guess in [0.1, 0.01, -0.1, 0.5, -0.5]:
                try:
                    xirr_decimal = newton(npv_func, initial_guess, maxiter=100)
                    
                    # Validate result
                    if np.isnan(xirr_decimal) or np.isinf(xirr_decimal):
                        continue
                    
                    # Verify NPV is close to 0
                    npv_check = npv_func(xirr_decimal)
                    if abs(npv_check) < 1e-6:  # Within tolerance
                        return xirr_decimal * 100
                except (RuntimeError, ValueError, OverflowError):
                    continue
            
            logger.debug(f"XIRR convergence failed for {len(dates)} cash flows")
            return 0.0
        except Exception as e:
            logger.warning(f"XIRR calculation error: {e}")
            return 0.0

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

            # Calculate XIRR for stock (if available)
            stock_xirr = 0.0
            if XIRR_AVAILABLE:
                stock_xirr = self.calculate_xirr(
                    [purchase_date, current_date.strftime('%Y-%m-%d')],
                    [-initial_value, current_value]
                )

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

            # Calculate XIRR for S&P 500 (if available)
            sp500_xirr = 0.0
            if XIRR_AVAILABLE:
                sp500_xirr = self.calculate_xirr(
                    [purchase_date, current_date.strftime('%Y-%m-%d')],
                    [-initial_value, sp500_current_value]
                )

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
                'stock_xirr': stock_xirr,
                'sp500_xirr': sp500_xirr,
                'sp500_current_value': sp500_current_value,
                'outperformance': stock_cagr - sp500_cagr,
                'xirr_outperformance': stock_xirr - sp500_xirr,
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
        Analyze entire portfolio performance with investment-weighted CAGR and XIRR.
        
        Uses investment-weighted average holding period to calculate portfolio CAGR,
        ensuring larger investments have proportionally more influence on the result.
        Calculates portfolio XIRR from aggregate cash flows.
        
        Returns:
            Dictionary containing:
                - trades: List of individual trade performance dictionaries
                - total_initial_value: Total amount invested
                - total_current_value: Current portfolio value
                - total_sp500_current_value: Expected value if invested in S&P 500
                - portfolio_cagr: Portfolio CAGR percentage
                - sp500_cagr: Benchmark S&P 500 CAGR percentage
                - portfolio_xirr: Portfolio XIRR percentage (accounts for timing)
                - sp500_xirr: S&P 500 XIRR percentage
                - portfolio_outperformance: Portfolio CAGR - S&P 500 CAGR
                - portfolio_xirr_outperformance: Portfolio XIRR - S&P 500 XIRR
        """
        results = []
        total_initial_value = 0
        total_current_value = 0
        total_sp500_current_value = 0
        weighted_years_sum = 0
        
        # For XIRR calculation
        cash_flow_dates = []
        cash_flows_stocks = []
        cash_flows_sp500 = []

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
                
                # Collect cash flows for XIRR (negative for outflow/purchase)
                cash_flow_dates.append(perf['purchase_date'])
                cash_flows_stocks.append(-perf['initial_value'])
                cash_flows_sp500.append(-perf['initial_value'])

        # Add final value as cash inflow (positive for return)
        if results:
            final_date = results[-1]['purchase_date']
            # Use today's date as final date
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Only add final values if we have initial investments
            if cash_flows_stocks:
                cash_flow_dates.append(today)
                cash_flows_stocks.append(total_current_value)
                cash_flows_sp500.append(total_sp500_current_value)

        # Calculate investment-weighted average holding period
        # This ensures each dollar invested has equal weight in the time calculation
        portfolio_xirr = 0.0
        sp500_xirr = 0.0
        
        if total_initial_value > 0:
            weighted_years = weighted_years_sum / total_initial_value
            portfolio_cagr = self.calculate_cagr(total_initial_value, total_current_value, weighted_years)
            sp500_cagr = self.calculate_cagr(total_initial_value, total_sp500_current_value, weighted_years)
            
            # CRITICAL: Sort cash flows by date (must be chronological for XIRR calculation)
            if cash_flow_dates:
                date_cf_pairs_stocks = list(zip(cash_flow_dates, cash_flows_stocks))
                date_cf_pairs_stocks.sort(key=lambda x: x[0])
                cash_flow_dates_sorted = [d for d, cf in date_cf_pairs_stocks]
                cash_flows_stocks_sorted = [cf for d, cf in date_cf_pairs_stocks]
                
                # Do the same for S&P 500 cash flows
                date_cf_pairs_sp500 = list(zip(cash_flow_dates, cash_flows_sp500))
                date_cf_pairs_sp500.sort(key=lambda x: x[0])
                cash_flows_sp500_sorted = [cf for d, cf in date_cf_pairs_sp500]
            else:
                cash_flow_dates_sorted = cash_flow_dates
                cash_flows_stocks_sorted = cash_flows_stocks
                cash_flows_sp500_sorted = cash_flows_sp500
            
            # Calculate portfolio XIRR with sorted dates
            portfolio_xirr = self.calculate_xirr(cash_flow_dates_sorted, cash_flows_stocks_sorted)
            sp500_xirr = self.calculate_xirr(cash_flow_dates_sorted, cash_flows_sp500_sorted)
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
            'portfolio_xirr': portfolio_xirr,
            'sp500_xirr': sp500_xirr,
            'portfolio_outperformance': portfolio_cagr - sp500_cagr,
            'portfolio_xirr_outperformance': portfolio_xirr - sp500_xirr
        }

    # ============================================================================
    # Reporting
    # ============================================================================
    
    def _calculate_symbol_accumulation(self, trades: List[Dict]) -> Dict:
        """
        Calculate accumulated earnings and metrics for each stock symbol.
        
        Groups all trades by symbol and aggregates their performance metrics.
        For XIRR, recalculates from actual cash flows (not weighted average of individual XIPRs).
        
        Args:
            trades: List of trade performance dictionaries
            
        Returns:
            Dictionary mapping symbols to accumulated metrics with total gains,
            weighted averages, and true symbol-level XIRR calculated from all cash flows.
        """
        symbol_stats = {}
        symbol_trades = {}  # Store trades by symbol for XIRR calculation
        
        # Aggregate trades by symbol
        for trade in trades:
            symbol = trade['symbol']
            if symbol not in symbol_stats:
                symbol_stats[symbol] = {
                    'trades_count': 0,
                    'total_shares': 0,
                    'total_initial_value': 0,
                    'total_current_value': 0,
                    'total_sp500_value': 0,
                    'total_sp500_xirr_weighted': 0,
                    'total_years_weighted': 0,
                }
                symbol_trades[symbol] = []
            
            stats = symbol_stats[symbol]
            stats['trades_count'] += 1
            stats['total_shares'] += trade['shares']
            stats['total_initial_value'] += trade['initial_value']
            stats['total_current_value'] += trade['current_value']
            stats['total_sp500_value'] += trade['sp500_current_value']
            stats['total_sp500_xirr_weighted'] += trade['sp500_xirr'] * trade['initial_value']
            stats['total_years_weighted'] += trade['years_held'] * trade['initial_value']
            symbol_trades[symbol].append(trade)
        
        # Calculate final metrics for each symbol
        for symbol, stats in symbol_stats.items():
            initial_val = stats['total_initial_value']
            current_val = stats['total_current_value']
            sp500_val = stats['total_sp500_value']
            
            # Gain calculations
            stats['total_gain'] = current_val - initial_val
            sp500_gain = sp500_val - initial_val
            stats['sp500_gain'] = sp500_gain
            stats['outperformance'] = stats['total_gain'] - sp500_gain
            
            # Calculate weighted average years held
            stats['avg_years_held'] = self._safe_divide(stats['total_years_weighted'], initial_val, 0.0)
            
            # Calculate weighted CAGR:
            # For each transaction i: r_i = CAGR from purchase_date_i to today
            #                         w_i = investment_amount_i * years_held_i
            # weighted_CAGR = Σ(r_i * w_i) / Σ(w_i)
            if stats['trades_count'] > 0:
                trades_for_symbol = symbol_trades[symbol]
                trades_with_dates = [t for t in trades_for_symbol if 'purchase_date' in t]
                
                if trades_with_dates:
                    total_weighted_cagr = 0.0
                    total_weight = 0.0
                    
                    for trade in trades_with_dates:
                        # Calculate years from this specific purchase to today
                        purchase_date = pd.to_datetime(trade['purchase_date'])
                        today = pd.Timestamp.now()
                        years_held = (today - purchase_date).days / 365.25
                        
                        # Calculate CAGR for this individual transaction
                        individual_cagr = self.calculate_cagr(
                            trade['initial_value'],
                            trade['current_value'],
                            years_held if years_held > 0 else 0.1
                        )
                        
                        # Weight = investment_amount * years_held
                        weight = trade['initial_value'] * years_held
                        
                        total_weighted_cagr += individual_cagr * weight
                        total_weight += weight
                    
                    # Weighted average CAGR
                    stats['avg_cagr'] = self._safe_divide(total_weighted_cagr, total_weight, 0.0)
                else:
                    # Fallback for test data: use weighted average years
                    stats['avg_cagr'] = self.calculate_cagr(initial_val, current_val, stats['avg_years_held'])
            else:
                stats['avg_cagr'] = 0.0
            
            # Other metrics
            stats['gain_percentage'] = self._safe_divide(stats['total_gain'], initial_val, 0.0) * 100
            stats['outperformance_pct'] = self._safe_divide(stats['outperformance'], initial_val, 0.0) * 100
            
            # Calculate true symbol-level XIRR from all cash flows (not weighted average)
            # Only if actual trades with purchase_date info are available
            if XIRR_AVAILABLE and stats['trades_count'] > 0:
                trades_for_symbol = symbol_trades[symbol]
                # Check if trades have purchase_date (from actual analysis, not tests)
                if trades_for_symbol and 'purchase_date' in trades_for_symbol[0]:
                    # Collect all purchase dates and current date with cash flows
                    dates = [t['purchase_date'] for t in trades_for_symbol]
                    cash_flows = [-t['initial_value'] for t in trades_for_symbol]
                    
                    # CRITICAL: Sort dates and cash flows together (dates may not be in order)
                    # If dates are out of order, XIRR calculation will be completely wrong
                    date_cf_pairs = list(zip(dates, cash_flows))
                    date_cf_pairs.sort(key=lambda x: x[0])
                    dates = [d for d, cf in date_cf_pairs]
                    cash_flows = [cf for d, cf in date_cf_pairs]
                    
                    # Add final cash flow (sale at current price)
                    dates.append(str(pd.Timestamp.now().date()))
                    cash_flows.append(current_val)
                    
                    # Calculate XIRR
                    xirr_result = self.calculate_xirr(dates, cash_flows)
                    stats['avg_xirr'] = xirr_result
                else:
                    # Fallback for test data: use weighted average
                    total_xirr_weighted = sum(t['stock_xirr'] * t['initial_value'] 
                                             for t in trades_for_symbol)
                    stats['avg_xirr'] = self._safe_divide(total_xirr_weighted, initial_val, 0.0)
            else:
                stats['avg_xirr'] = 0.0
            
            stats['avg_sp500_xirr'] = self._safe_divide(stats['total_sp500_xirr_weighted'], initial_val, 0.0)
            stats['xirr_outperformance_pct'] = stats['avg_xirr'] - stats['avg_sp500_xirr']
            
            # Remove intermediate calculation fields
            del stats['total_sp500_xirr_weighted']
            del stats['total_years_weighted']
        
        return symbol_stats
    
    def print_report(self, output_file: Optional[str] = None) -> None:
        """
        Print formatted portfolio analysis report to console and optionally to file.
        
        Displays individual trade performance, accumulated earnings per symbol,
        and portfolio summary with:
        - Current values and CAGR for each trade
        - Accumulated earnings and metrics per symbol
        - Portfolio totals and weighted CAGR
        - Comparison against S&P 500 benchmark
        
        Args:
            output_file: Optional path to save report as text file
        """
        analysis = self.analyze_portfolio()

        if not analysis['trades']:
            print("No valid trades to analyze.")
            return

        # Calculate symbol accumulation
        symbol_stats = self._calculate_symbol_accumulation(analysis['trades'])
        
        # Group trades by symbol
        trades_by_symbol = {}
        for trade in analysis['trades']:
            symbol = trade['symbol']
            if symbol not in trades_by_symbol:
                trades_by_symbol[symbol] = []
            trades_by_symbol[symbol].append(trade)
        
        # Build report output
        report_lines = []
        report_lines.append("\n=== INDIVIDUAL STOCK PERFORMANCE ===")
        
        # Iterate through symbols in sorted order
        for symbol in sorted(trades_by_symbol.keys()):
            trades = trades_by_symbol[symbol]
            symbol_data = symbol_stats[symbol]
            
            # Print individual trades for this symbol
            for trade in trades:
                report_lines.append(f"\n{trade['symbol']}:")
                report_lines.append(f"  Shares: {trade['shares']} @ ${trade['purchase_price']:.2f}")
                report_lines.append(f"  Current Price: ${trade['current_price']:.2f}")
                report_lines.append(f"  Initial Value: ${trade['initial_value']:.2f}")
                report_lines.append(f"  Current Value: ${trade['current_value']:.2f}")
                report_lines.append(f"  Gain: ${trade['current_value'] - trade['initial_value']:.2f}")
                report_lines.append(f"  Stock CAGR: {trade['stock_cagr']:.2f}%")
                report_lines.append(f"  Stock XIRR: {trade['stock_xirr']:.2f}%")
                report_lines.append(f"  S&P 500 CAGR: {trade['sp500_cagr']:.2f}%")
                report_lines.append(f"  S&P 500 XIRR: {trade['sp500_xirr']:.2f}%")
                report_lines.append(f"  Outperformance (CAGR): {trade['outperformance']:.2f}%")
                report_lines.append(f"  Outperformance (XIRR): {trade['xirr_outperformance']:.2f}%")
            
            # Print accumulated stats for this symbol
            report_lines.append(f"\n--- {symbol} ACCUMULATED ---")
            report_lines.append(f"  Total Trades: {symbol_data['trades_count']}")
            report_lines.append(f"  Total Shares: {symbol_data['total_shares']:.0f}")
            report_lines.append(f"  Total Initial Investment: ${symbol_data['total_initial_value']:.2f}")
            report_lines.append(f"  Total Current Value: ${symbol_data['total_current_value']:.2f}")
            report_lines.append(f"  Total Gain: ${symbol_data['total_gain']:.2f} ({symbol_data['gain_percentage']:.2f}%)")
            report_lines.append(f"  Expected S&P 500 Value: ${symbol_data['total_sp500_value']:.2f}")
            report_lines.append(f"  Outperformance vs S&P 500: ${symbol_data['outperformance']:.2f} ({symbol_data['outperformance_pct']:.2f}%)")
            report_lines.append(f"  Weighted Avg CAGR: {symbol_data['avg_cagr']:.2f}%")
            report_lines.append(f"  Weighted Avg XIRR: {symbol_data['avg_xirr']:.2f}%")
            report_lines.append(f"  Avg S&P 500 XIRR: {symbol_data['avg_sp500_xirr']:.2f}%")
            report_lines.append(f"  XIRR Outperformance: {symbol_data['xirr_outperformance_pct']:.2f}%")
            report_lines.append(f"  Weighted Avg Years Held: {symbol_data['avg_years_held']:.2f} years")

        report_lines.append("\n=== PORTFOLIO SUMMARY ===")
        report_lines.append(f"Initial Investment: ${analysis['total_initial_value']:.2f}")
        report_lines.append(f"Current Value: ${analysis['total_current_value']:.2f}")
        report_lines.append(f"Total Gain: ${analysis['total_current_value'] - analysis['total_initial_value']:.2f}")
        report_lines.append(f"Expected Value if Invested in S&P 500: ${analysis['total_sp500_current_value']:.2f}")
        report_lines.append(f"\nPortfolio CAGR: {analysis['portfolio_cagr']:.2f}%")
        report_lines.append(f"Portfolio XIRR: {analysis.get('portfolio_xirr', 0.0):.2f}%")
        report_lines.append(f"S&P 500 CAGR: {analysis['sp500_cagr']:.2f}%")
        report_lines.append(f"S&P 500 XIRR: {analysis.get('sp500_xirr', 0.0):.2f}%")
        report_lines.append(f"\nPortfolio Outperformance (CAGR): {analysis['portfolio_outperformance']:.2f}%")
        report_lines.append(f"Portfolio Outperformance (XIRR): {analysis.get('portfolio_xirr_outperformance', 0.0):.2f}%")
        
        # Print to console
        for line in report_lines:
            print(line)
        
        # Optionally save to file
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write('\n'.join(report_lines))
                print(f"\n✅ Report saved to: {output_file}")
            except Exception as e:
                print(f"\n⚠️  Error saving report to file: {e}")
    
    def _prepare_pdf_data(self, analysis: Dict, symbol_stats: Dict) -> Dict:
        """
        Prepare data needed for PDF visualizations (sorted once for efficiency).
        
        Sorts symbol statistics by multiple metrics to avoid repeated sorting in PDF generation.
        
        Args:
            analysis: Portfolio analysis results
            symbol_stats: Symbol statistics dictionary
            
        Returns:
            Dictionary with pre-sorted data for all charts including CAGR and XIRR performers
        """
        return {
            'top_10_value': sorted(symbol_stats.items(), 
                                  key=lambda x: x[1]['total_current_value'], reverse=True)[:10],
            'top_8_cagr': sorted(symbol_stats.items(), 
                                key=lambda x: x[1]['avg_cagr'], reverse=True)[:8],
            'top_8_xirr': sorted(symbol_stats.items(), 
                                key=lambda x: x[1]['avg_xirr'], reverse=True)[:8],
            'top_8_gain': sorted(symbol_stats.items(), 
                                key=lambda x: x[1]['total_gain'], reverse=True)[:8],
            'winning': sum(1 for s in symbol_stats.values() if s['total_gain'] > 0),
            'losing': sum(1 for s in symbol_stats.values() if s['total_gain'] < 0),
            'neutral': sum(1 for s in symbol_stats.values() if s['total_gain'] == 0),
            'total_symbols': len(symbol_stats)
        }

    def _add_summary_box(self, ax, analysis: Dict) -> None:
        """Add portfolio summary text box to axis with CAGR and XIRR metrics."""
        summary_text = f"""
PORTFOLIO SUMMARY
Initial: ${analysis['total_initial_value']:,.0f}  |  Current: ${analysis['total_current_value']:,.0f}  |  Gain: ${analysis['total_current_value'] - analysis['total_initial_value']:,.0f}

CAGR: {analysis['portfolio_cagr']:.1f}%  |  XIRR: {analysis.get('portfolio_xirr', 0.0):.1f}%  |  S&P 500 CAGR: {analysis['sp500_cagr']:.1f}%  |  S&P 500 XIRR: {analysis.get('sp500_xirr', 0.0):.1f}%

Outperformance (CAGR): {analysis['portfolio_outperformance']:.1f}%  |  Outperformance (XIRR): {analysis.get('portfolio_xirr_outperformance', 0.0):.1f}%
        """
        ax.axis('off')
        ax.text(0.5, 0.5, summary_text, fontsize=10, family='monospace',
               verticalalignment='center', horizontalalignment='center',
               bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.25, pad=0.8))

    def _add_stats_box(self, ax, data: Dict) -> None:
        """Add position statistics text box to axis (compact version)."""
        win_rate = self._safe_divide(data['winning'], data['total_symbols'], 0.0) * 100
        stats_text = f"""
STATISTICS

Winning: {data['winning']}
Losing: {data['losing']}
Neutral: {data['neutral']}
Total: {data['total_symbols']}

Win Rate: {win_rate:.0f}%
        """
        ax.axis('off')
        ax.text(0.5, 0.5, stats_text, fontsize=9, family='monospace',
               verticalalignment='center', horizontalalignment='center',
               bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.4, pad=0.6))

    def _add_bar_chart(self, ax, labels, values, title: str, xlabel: str, 
                      positive_color='green', negative_color='red') -> None:
        """Add a horizontal bar chart with color-coding by sign."""
        colors = [positive_color if v >= 0 else negative_color for v in values]
        bars = ax.barh(labels, values, color=colors, alpha=0.75, edgecolor='black', linewidth=0.5)
        ax.set_xlabel(xlabel, fontweight='bold', fontsize=9)
        ax.set_title(title, fontweight='bold', fontsize=10, pad=8)
        ax.grid(axis='x', alpha=0.2, linestyle='--')
        ax.tick_params(axis='both', labelsize=8)
        # Add value labels on bars
        for i, (label, value) in enumerate(zip(labels, values)):
            ax.text(value, i, f' {value:.1f}', va='center', fontsize=7, fontweight='bold')

    def generate_pdf_report(self, pdf_path: str) -> None:
        """
        Generate a comprehensive PDF report with visualizations.
        
        Creates a PDF with charts showing portfolio composition, performance,
        and key metrics. Requires matplotlib and seaborn libraries.
        
        Args:
            pdf_path: Path where PDF file will be saved
        """
        if not VISUALIZATIONS_AVAILABLE:
            print("⚠️  Visualization libraries not available. Install with:")
            print("   pip3 install matplotlib seaborn")
            return
        
        try:
            from matplotlib.backends.backend_pdf import PdfPages
            
            analysis = self.analyze_portfolio()
            if not analysis['trades']:
                print("No valid trades to analyze.")
                return
            
            symbol_stats = self._calculate_symbol_accumulation(analysis['trades'])
            pdf_data = self._prepare_pdf_data(analysis, symbol_stats)
            
            with PdfPages(pdf_path) as pdf:
                # Page 1: Summary metrics and key charts
                # Better layout: summary at top, charts in middle, stats on side
                fig = plt.figure(figsize=(12, 11))
                fig.suptitle('Portfolio Performance Report', fontsize=18, fontweight='bold', y=0.98)
                gs = fig.add_gridspec(4, 3, hspace=0.55, wspace=0.4, top=0.94, bottom=0.05)
                
                # Summary box (spans full width at top)
                self._add_summary_box(fig.add_subplot(gs[0, :]), analysis)
                
                # Portfolio composition pie chart (full width, row 1)
                ax_pie = fig.add_subplot(gs[1, :])
                labels = [s[0] for s in pdf_data['top_10_value']]
                sizes = [s[1]['total_current_value'] for s in pdf_data['top_10_value']]
                colors = plt.cm.Set3(range(len(labels)))
                total_value = sum(sizes)
                # Create legend labels with percentages
                legend_labels = [f"{label} ({size/total_value*100:.1f}%)" 
                                for label, size in zip(labels, sizes)]
                wedges, texts = ax_pie.pie(sizes, colors=colors, startangle=90)
                ax_pie.set_title('Top 10 Holdings by Value', fontweight='bold', pad=10)
                # Position legend outside pie chart to avoid overlap
                ax_pie.legend(wedges, legend_labels, title='Holdings', loc='upper left', 
                             bbox_to_anchor=(0.75, 1), fontsize=7.5, framealpha=0.95)
                
                # CAGR comparison chart (row 2, left)
                names = [s[0] for s in pdf_data['top_8_cagr']]
                cagrs = [s[1]['avg_cagr'] for s in pdf_data['top_8_cagr']]
                self._add_bar_chart(fig.add_subplot(gs[2, 0:2]), names, cagrs, 
                                   'Top 8 Performers by CAGR', 'CAGR %')
                fig.axes[-1].axvline(x=analysis['sp500_cagr'], color='blue', linestyle='--', 
                                    label=f"S&P 500: {analysis['sp500_cagr']:.1f}%")
                fig.axes[-1].legend(fontsize=8)
                
                # XIRR comparison chart (row 2, right)
                names = [s[0] for s in pdf_data['top_8_xirr']]
                xirrs = [s[1]['avg_xirr'] for s in pdf_data['top_8_xirr']]
                self._add_bar_chart(fig.add_subplot(gs[2, 2]), names, xirrs, 
                                   'XIRR %', 'XIRR %')
                fig.axes[-1].axvline(x=analysis.get('sp500_xirr', 0.0), color='blue', linestyle='--', 
                                    label=f"S&P 500: {analysis.get('sp500_xirr', 0.0):.1f}%")
                fig.axes[-1].legend(fontsize=8)
                
                # Dollar gain chart (row 3, left)
                names = [s[0] for s in pdf_data['top_8_gain']]
                gains = [s[1]['total_gain'] for s in pdf_data['top_8_gain']]
                self._add_bar_chart(fig.add_subplot(gs[3, 0:2]), names, gains, 
                                   'Top 8 by Total Dollar Gain', 'Total Gain ($)',
                                   positive_color='darkgreen', negative_color='darkred')
                
                # Statistics box (row 3, right - smaller and better positioned)
                self._add_stats_box(fig.add_subplot(gs[3, 2]), pdf_data)
                
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)
                
                # Page 2: Top performers detailed table
                fig = plt.figure(figsize=(11, 8.5))
                fig.suptitle('Top 10 Positions - Detailed Metrics', fontsize=16, fontweight='bold')
                ax = fig.add_subplot(111)
                ax.axis('tight')
                ax.axis('off')
                
                table_data = [['Symbol', 'Trades', 'Invested', 'Current', 'Gain', 'Gain%', 'CAGR%', 'XIRR%']]
                for symbol, stats in pdf_data['top_10_value']:
                    table_data.append([
                        symbol,
                        f"{stats['trades_count']}",
                        f"${stats['total_initial_value']:.0f}",
                        f"${stats['total_current_value']:.0f}",
                        f"${stats['total_gain']:.0f}",
                        f"{stats['gain_percentage']:.1f}%",
                        f"{stats['avg_cagr']:.1f}%",
                        f"{stats['avg_xirr']:.1f}%"
                    ])
                
                table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                               colWidths=[0.1, 0.1, 0.13, 0.13, 0.13, 0.13, 0.13, 0.13])
                table.auto_set_font_size(False)
                table.set_fontsize(10)
                table.scale(1, 2)
                
                # Style header row
                for i in range(len(table_data[0])):
                    table[(0, i)].set_facecolor('#4CAF50')
                    table[(0, i)].set_text_props(weight='bold', color='white')
                
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)
            
            print(f"✅ PDF report generated: {pdf_path}")
            
        except Exception as e:
            print(f"⚠️  Error generating PDF: {e}")

    def generate_html_report(self, html_path: str) -> None:
        """
        Generate a professional interactive HTML dashboard report.
        
        Includes:
        - Summary metrics and KPIs
        - Interactive Plotly charts
        - Sortable/filterable data tables
        - Dark mode support
        - Print-friendly layout
        
        Args:
            html_path: Path where the HTML file will be saved
        """
        try:
            # Prepare data
            analysis = self.analyze_portfolio()
            if not analysis['trades']:
                print("No valid trades to analyze.")
                return
            
            symbol_stats = self._calculate_symbol_accumulation(analysis['trades'])
            pdf_data = self._prepare_pdf_data(analysis, symbol_stats)
            
            # Start building HTML
            html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Analytics Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link href="https://cdn.datatables.net/1.13.6/css/dataTables.bootstrap5.min.css" rel="stylesheet">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/dataTables.bootstrap5.min.js"></script>
    <style>
        :root {
            --bg-primary: #ffffff;
            --bg-secondary: #f8f9fa;
            --text-primary: #1a1a1a;
            --text-secondary: #666666;
            --border-color: #e0e0e0;
            --accent-color: #0066cc;
            --positive: #10b981;
            --negative: #ef4444;
            --warning: #f59e0b;
        }
        
        body.dark-mode {
            --bg-primary: #1a1a1a;
            --bg-secondary: #2d2d2d;
            --text-primary: #ffffff;
            --text-secondary: #b0b0b0;
            --border-color: #444444;
            --accent-color: #3b82f6;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: var(--bg-secondary);
            color: var(--text-primary);
            transition: background-color 0.3s, color 0.3s;
            line-height: 1.6;
        }
        
        .navbar {
            background: linear-gradient(135deg, var(--accent-color) 0%, #0052a3 100%);
            color: white;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .navbar h1 {
            font-size: 1.8rem;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        
        .navbar-controls {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        
        .toggle-btn {
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.4);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .toggle-btn:hover {
            background: rgba(255,255,255,0.3);
            border-color: white;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .metric-card {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            transition: all 0.3s;
        }
        
        .metric-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        
        .metric-label {
            color: var(--text-secondary);
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-primary);
            display: flex;
            align-items: baseline;
            gap: 0.5rem;
        }
        
        .metric-unit {
            font-size: 0.875rem;
            color: var(--text-secondary);
            font-weight: 400;
        }
        
        .metric-positive { color: var(--positive); }
        .metric-negative { color: var(--negative); }
        
        .section {
            background: var(--bg-primary);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            border: 1px solid var(--border-color);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        
        .section-title {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--accent-color);
            color: var(--text-primary);
        }
        
        .chart-container {
            min-height: 400px;
            margin-bottom: 1rem;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }
        
        table thead {
            background: var(--bg-secondary);
            border-bottom: 2px solid var(--border-color);
        }
        
        table th {
            padding: 1rem;
            text-align: left;
            font-weight: 600;
            color: var(--text-primary);
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        table td {
            padding: 1rem;
            border-bottom: 1px solid var(--border-color);
            color: var(--text-primary);
        }
        
        table tbody tr:hover {
            background: var(--bg-secondary);
        }
        
        .number {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-weight: 600;
        }
        
        .positive-return { color: var(--positive); }
        .negative-return { color: var(--negative); }
        
        .dataTables_wrapper {
            margin-top: 1.5rem;
        }
        
        @media (max-width: 768px) {
            .container { padding: 1rem; }
            .navbar { padding: 1rem; flex-direction: column; gap: 1rem; }
            .navbar h1 { font-size: 1.3rem; }
            .metrics-grid { grid-template-columns: 1fr; }
            .section { padding: 1rem; }
        }
        
        @media print {
            .navbar-controls { display: none; }
            .dataTables_filter, .dataTables_length, .dataTables_info, .dataTables_paginate { display: none !important; }
            .section { break-inside: avoid; page-break-inside: avoid; }
        }
    </style>
</head>
<body>
    <div class="navbar">
        <h1>📊 Portfolio Analytics</h1>
        <div class="navbar-controls">
            <button class="toggle-btn" onclick="toggleDarkMode()">🌙 Dark Mode</button>
            <button class="toggle-btn" onclick="window.print()">🖨️ Print</button>
        </div>
    </div>
    
    <div class="container">
        <!-- Key Metrics Section -->
        <div class="metrics-grid">
"""
            
            # Add metric cards - using analysis dict which has all portfolio metrics
            cagr = analysis['portfolio_cagr']
            xirr = analysis.get('portfolio_xirr', 0.0)
            total_gain = analysis['total_current_value'] - analysis['total_initial_value']
            gain_pct = self._safe_divide(total_gain, analysis['total_initial_value'], 0.0) * 100
            
            html_content += f"""
            <div class="metric-card">
                <div class="metric-label">Portfolio Value</div>
                <div class="metric-value">${analysis['total_current_value']:,.0f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Gain</div>
                <div class="metric-value {('metric-positive' if total_gain >= 0 else 'metric-negative')}">${total_gain:,.0f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Return %</div>
                <div class="metric-value {('metric-positive' if gain_pct >= 0 else 'metric-negative')}">{gain_pct:.1f}<span class="metric-unit">%</span></div>
            </div>
            <div class="metric-card">
                <div class="metric-label">CAGR</div>
                <div class="metric-value {('metric-positive' if cagr >= 0 else 'metric-negative')}">{cagr:.1f}<span class="metric-unit">%</span></div>
            </div>
            <div class="metric-card">
                <div class="metric-label">XIRR (Time-Weighted)</div>
                <div class="metric-value {('metric-positive' if xirr >= 0 else 'metric-negative')}">{xirr:.1f}<span class="metric-unit">%</span></div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Invested Capital</div>
                <div class="metric-value">${analysis['total_initial_value']:,.0f}</div>
            </div>
        </div>
        
        <!-- Charts Section -->
        <div class="section">
            <h2 class="section-title">Position Allocation</h2>
            <div class="chart-container" id="pieChart"></div>
        </div>
        
        <div class="section">
            <h2 class="section-title">Performance Metrics</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem;">
                <div class="chart-container" id="cagrChart"></div>
                <div class="chart-container" id="xirrChart"></div>
                <div class="chart-container" id="gainChart"></div>
            </div>
        </div>
        
        <!-- Top Positions Table -->
        <div class="section">
            <h2 class="section-title">Top 10 Holdings</h2>
            <table id="topPositionsTable" class="table table-striped">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Trades</th>
                        <th>Invested</th>
                        <th>Current Value</th>
                        <th>Dollar Gain</th>
                        <th>Return %</th>
                        <th>CAGR %</th>
                        <th>XIRR %</th>
                    </tr>
                </thead>
                <tbody>
"""
            
            # Add top positions rows
            for symbol, stats in pdf_data['top_10_value']:
                html_content += f"""
                    <tr>
                        <td><strong>{symbol}</strong></td>
                        <td class="number">{stats['trades_count']}</td>
                        <td class="number">${stats['total_initial_value']:,.0f}</td>
                        <td class="number">${stats['total_current_value']:,.0f}</td>
                        <td class="number {('positive-return' if stats['total_gain'] >= 0 else 'negative-return')}">${stats['total_gain']:,.0f}</td>
                        <td class="number {('positive-return' if stats['gain_percentage'] >= 0 else 'negative-return')}">{stats['gain_percentage']:.1f}%</td>
                        <td class="number {('positive-return' if stats['avg_cagr'] >= 0 else 'negative-return')}">{stats['avg_cagr']:.1f}%</td>
                        <td class="number {('positive-return' if stats['avg_xirr'] >= 0 else 'negative-return')}">{stats['avg_xirr']:.1f}%</td>
                    </tr>
"""
            
            html_content += """
                </tbody>
            </table>
        </div>
        
        <!-- All Positions Table -->
        <div class="section">
            <h2 class="section-title">All Positions</h2>
            <table id="allPositionsTable" class="table table-striped">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Trades</th>
                        <th>Invested</th>
                        <th>Current Value</th>
                        <th>Dollar Gain</th>
                        <th>Return %</th>
                        <th>CAGR %</th>
                        <th>XIRR %</th>
                    </tr>
                </thead>
                <tbody>
"""
            
            # Add all positions (sorted by current value)
            sorted_symbols = sorted(symbol_stats.items(), 
                                   key=lambda x: x[1]['total_current_value'], 
                                   reverse=True)
            for symbol, stats in sorted_symbols:
                html_content += f"""
                    <tr>
                        <td><strong>{symbol}</strong></td>
                        <td class="number">{stats['trades_count']}</td>
                        <td class="number">${stats['total_initial_value']:,.0f}</td>
                        <td class="number">${stats['total_current_value']:,.0f}</td>
                        <td class="number {('positive-return' if stats['total_gain'] >= 0 else 'negative-return')}">${stats['total_gain']:,.0f}</td>
                        <td class="number {('positive-return' if stats['gain_percentage'] >= 0 else 'negative-return')}">{stats['gain_percentage']:.1f}%</td>
                        <td class="number {('positive-return' if stats['avg_cagr'] >= 0 else 'negative-return')}">{stats['avg_cagr']:.1f}%</td>
                        <td class="number {('positive-return' if stats['avg_xirr'] >= 0 else 'negative-return')}">{stats['avg_xirr']:.1f}%</td>
                    </tr>
"""
            
            html_content += """
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        // Dark mode toggle
        function toggleDarkMode() {
            document.body.classList.toggle('dark-mode');
            localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
        }
        
        // Load dark mode preference
        if (localStorage.getItem('darkMode') === 'true') {
            document.body.classList.add('dark-mode');
        }
        
        // Initialize DataTables
        $(document).ready(function() {
            $('#topPositionsTable').DataTable({
                paging: false,
                searching: true,
                info: false,
                columnDefs: [{
                    targets: [1,2,3,4,5,6,7],
                    className: 'dt-right'
                }]
            });
            
            $('#allPositionsTable').DataTable({
                pageLength: 25,
                columnDefs: [{
                    targets: [1,2,3,4,5,6,7],
                    className: 'dt-right'
                }]
            });
            
            // Create Pie Chart
            createPieChart();
            createCAGRChart();
            createXIRRChart();
            createGainChart();
        });
        
        function createPieChart() {
            const data = ["""
            
            # Add pie chart data
            for symbol, stats in pdf_data['top_10_value']:
                html_content += f"{{x: '{symbol}', value: {stats['total_current_value']:.0f}}},"
            
            html_content += """
            ];
            
            const layout = {
                title: 'Top 10 Holdings by Value',
                height: 400,
                font: { family: 'sans-serif' }
            };
            
            const trace = {
                labels: data.map(d => d.x),
                values: data.map(d => d.value),
                type: 'pie',
                textposition: 'inside',
                textinfo: 'label+percent'
            };
            
            Plotly.newPlot('pieChart', [trace], layout, {responsive: true});
        }
        
        function createCAGRChart() {
            const topData = ["""
            
            for symbol, stats in pdf_data['top_10_value']:
                html_content += f"{{symbol: '{symbol}', cagr: {stats['avg_cagr']:.2f}}},"
            
            html_content += """
            ];
            
            const trace = {
                x: topData.map(d => d.symbol),
                y: topData.map(d => d.cagr),
                type: 'bar',
                marker: {
                    color: topData.map(d => d.cagr >= 0 ? '#10b981' : '#ef4444')
                }
            };
            
            const layout = {
                title: 'CAGR by Symbol',
                xaxis: { title: 'Symbol' },
                yaxis: { title: 'CAGR %' },
                height: 400,
                margin: { b: 100 }
            };
            
            Plotly.newPlot('cagrChart', [trace], layout, {responsive: true});
        }
        
        function createXIRRChart() {
            const topData = ["""
            
            for symbol, stats in pdf_data['top_10_value']:
                html_content += f"{{symbol: '{symbol}', xirr: {stats['avg_xirr']:.2f}}},"
            
            html_content += """
            ];
            
            const trace = {
                x: topData.map(d => d.symbol),
                y: topData.map(d => d.xirr),
                type: 'bar',
                marker: {
                    color: topData.map(d => d.xirr >= 0 ? '#10b981' : '#ef4444')
                }
            };
            
            const layout = {
                title: 'XIRR by Symbol',
                xaxis: { title: 'Symbol' },
                yaxis: { title: 'XIRR %' },
                height: 400,
                margin: { b: 100 }
            };
            
            Plotly.newPlot('xirrChart', [trace], layout, {responsive: true});
        }
        
        function createGainChart() {
            const topData = ["""
            
            for symbol, stats in pdf_data['top_10_value']:
                html_content += f"{{symbol: '{symbol}', gain: {stats['total_gain']:.0f}}},"
            
            html_content += """
            ];
            
            const trace = {
                x: topData.map(d => d.symbol),
                y: topData.map(d => d.gain),
                type: 'bar',
                marker: {
                    color: topData.map(d => d.gain >= 0 ? '#10b981' : '#ef4444')
                }
            };
            
            const layout = {
                title: 'Dollar Gain by Symbol',
                xaxis: { title: 'Symbol' },
                yaxis: { title: 'Gain ($)' },
                height: 400,
                margin: { b: 100 }
            };
            
            Plotly.newPlot('gainChart', [trace], layout, {responsive: true});
        }
    </script>
</body>
</html>
"""
            
            # Write HTML file
            with open(html_path, 'w') as f:
                f.write(html_content)
            
            print(f"✅ HTML report generated: {html_path}")
            
        except Exception as e:
            print(f"⚠️  Error generating HTML: {e}")
            import traceback
            traceback.print_exc()


# ============================================================================
# Command Line Interface
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Portfolio Analyzer")
    parser.add_argument("--csv", help="Path to CSV file with trades")
    parser.add_argument("--output", "-o", help="Path to save report to text file")
    parser.add_argument("--pdf", help="Path to save report as PDF file with visualizations")
    parser.add_argument("--html", help="Path to save interactive HTML dashboard report")
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
    analyzer.print_report(output_file=args.output)
    
    if args.pdf:
        analyzer.generate_pdf_report(args.pdf)
    
    if args.html:
        analyzer.generate_html_report(args.html)