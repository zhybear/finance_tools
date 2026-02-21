"""Portfolio Performance Analyzer

Compares stock portfolio performance against S&P 500 benchmark.
Calculates CAGR (Compound Annual Growth Rate) and XIRR (Extended Internal Rate of Return) 
for individual trades and overall portfolio.
"""

import yfinance as yf
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
import argparse
import sys
import numpy as np
from scipy.optimize import newton

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
        
        XIRR accounts for the timing of cash flows, providing a more accurate return
        metric when investments are made at different times.
        
        Args:
            dates: List of dates in YYYY-MM-DD format for each cash flow
            cash_flows: List of cash flows (negative for investments, positive for returns)
                       Must have at least 2 cash flows
            
        Returns:
            XIRR as a percentage (e.g., 15.5 for 15.5%)
            Returns 0.0 if XIRR cannot be calculated
        """
        if len(dates) != len(cash_flows) or len(dates) < 2:
            return 0.0
        
        try:
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
            
            return 0.0
        except Exception:
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
    
    def _calculate_symbol_accumulation(self, trades: List[Dict]) -> Dict:
        """
        Calculate accumulated earnings and metrics for each stock symbol.
        
        Groups all trades by symbol and aggregates their performance metrics.
        
        Args:
            trades: List of trade performance dictionaries
            
        Returns:
            Dictionary mapping symbols to accumulated metrics with total gains,
            weighted averages, and S&P 500 comparison for each symbol.
        """
        symbol_stats = {}
        
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
                    'total_cagr_weighted': 0,
                    'total_xirr_weighted': 0,
                    'total_sp500_xirr_weighted': 0,
                    'total_years_weighted': 0,
                }
            
            stats = symbol_stats[symbol]
            stats['trades_count'] += 1
            stats['total_shares'] += trade['shares']
            stats['total_initial_value'] += trade['initial_value']
            stats['total_current_value'] += trade['current_value']
            stats['total_sp500_value'] += trade['sp500_current_value']
            stats['total_cagr_weighted'] += trade['stock_cagr'] * trade['initial_value']
            stats['total_xirr_weighted'] += trade['stock_xirr'] * trade['initial_value']
            stats['total_sp500_xirr_weighted'] += trade['sp500_xirr'] * trade['initial_value']
            stats['total_years_weighted'] += trade['years_held'] * trade['initial_value']
        
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
            
            # Weighted averages using safe division helper
            stats['gain_percentage'] = self._safe_divide(stats['total_gain'], initial_val, 0.0) * 100
            stats['avg_cagr'] = self._safe_divide(stats['total_cagr_weighted'], initial_val, 0.0)
            stats['avg_xirr'] = self._safe_divide(stats['total_xirr_weighted'], initial_val, 0.0)
            stats['avg_sp500_xirr'] = self._safe_divide(stats['total_sp500_xirr_weighted'], initial_val, 0.0)
            stats['avg_years_held'] = self._safe_divide(stats['total_years_weighted'], initial_val, 0.0)
            stats['outperformance_pct'] = self._safe_divide(stats['outperformance'], initial_val, 0.0) * 100
            stats['xirr_outperformance_pct'] = stats['avg_xirr'] - stats['avg_sp500_xirr']
            
            # Remove intermediate calculation fields
            del stats['total_cagr_weighted']
            del stats['total_xirr_weighted']
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
                report_lines.append(f"  S&P 500 CAGR: {trade['sp500_cagr']:.2f}%")
                report_lines.append(f"  Outperformance: {trade['outperformance']:.2f}%")
            
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
            report_lines.append(f"  Weighted Avg Years Held: {symbol_data['avg_years_held']:.2f} years")

        report_lines.append("\n=== PORTFOLIO SUMMARY ===")
        report_lines.append(f"Initial Investment: ${analysis['total_initial_value']:.2f}")
        report_lines.append(f"Current Value: ${analysis['total_current_value']:.2f}")
        report_lines.append(f"Total Gain: ${analysis['total_current_value'] - analysis['total_initial_value']:.2f}")
        report_lines.append(f"Expected Value if Invested in S&P 500: ${analysis['total_sp500_current_value']:.2f}")
        report_lines.append(f"Portfolio CAGR: {analysis['portfolio_cagr']:.2f}%")
        report_lines.append(f"S&P 500 CAGR: {analysis['sp500_cagr']:.2f}%")
        report_lines.append(f"Portfolio Outperformance: {analysis['portfolio_outperformance']:.2f}%")
        
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
        
        Args:
            analysis: Portfolio analysis results
            symbol_stats: Symbol statistics dictionary
            
        Returns:
            Dictionary with pre-sorted data for all charts
        """
        return {
            'top_10_value': sorted(symbol_stats.items(), 
                                  key=lambda x: x[1]['total_current_value'], reverse=True)[:10],
            'top_8_cagr': sorted(symbol_stats.items(), 
                                key=lambda x: x[1]['avg_cagr'], reverse=True)[:8],
            'top_8_gain': sorted(symbol_stats.items(), 
                                key=lambda x: x[1]['total_gain'], reverse=True)[:8],
            'winning': sum(1 for s in symbol_stats.values() if s['total_gain'] > 0),
            'losing': sum(1 for s in symbol_stats.values() if s['total_gain'] < 0),
            'neutral': sum(1 for s in symbol_stats.values() if s['total_gain'] == 0),
            'total_symbols': len(symbol_stats)
        }

    def _add_summary_box(self, ax, analysis: Dict) -> None:
        """Add portfolio summary text box to axis."""
        summary_text = f"""
PORTFOLIO SUMMARY
Initial Investment: ${analysis['total_initial_value']:,.2f}
Current Value: ${analysis['total_current_value']:,.2f}
Total Gain: ${analysis['total_current_value'] - analysis['total_initial_value']:,.2f}

Portfolio CAGR: {analysis['portfolio_cagr']:.2f}%
S&P 500 CAGR: {analysis['sp500_cagr']:.2f}%
Outperformance: {analysis['portfolio_outperformance']:.2f}%

Expected S&P 500 Value: ${analysis['total_sp500_current_value']:,.2f}
Actual Return vs Expected: {(analysis['total_current_value'] / analysis['total_sp500_current_value'] * 100):.1f}%
        """
        ax.axis('off')
        ax.text(0.1, 0.5, summary_text, fontsize=11, family='monospace',
               verticalalignment='center', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))

    def _add_stats_box(self, ax, data: Dict) -> None:
        """Add position statistics text box to axis."""
        win_rate = self._safe_divide(data['winning'], data['total_symbols'], 0.0) * 100
        stats_text = f"""
POSITION STATISTICS

Winning Positions: {data['winning']}
Losing Positions: {data['losing']}
Neutral Positions: {data['neutral']}
Total Symbols: {data['total_symbols']}

Win Rate: {win_rate:.1f}%
        """
        ax.axis('off')
        ax.text(0.1, 0.5, stats_text, fontsize=11, family='monospace',
               verticalalignment='center', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.3))

    def _add_bar_chart(self, ax, labels, values, title: str, xlabel: str, 
                      positive_color='green', negative_color='red') -> None:
        """Add a horizontal bar chart with color-coding by sign."""
        colors = [positive_color if v >= 0 else negative_color for v in values]
        ax.barh(labels, values, color=colors, alpha=0.7)
        ax.set_xlabel(xlabel, fontweight='bold')
        ax.set_title(title, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)

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
                fig = plt.figure(figsize=(11, 8.5))
                fig.suptitle('Portfolio Performance Report', fontsize=16, fontweight='bold')
                gs = fig.add_gridspec(3, 2, hspace=0.4, wspace=0.3)
                
                # Summary box
                self._add_summary_box(fig.add_subplot(gs[0, :]), analysis)
                
                # Portfolio composition pie chart (with legend including percentages)
                ax_pie = fig.add_subplot(gs[1, 0])
                labels = [s[0] for s in pdf_data['top_10_value']]
                sizes = [s[1]['total_current_value'] for s in pdf_data['top_10_value']]
                colors = plt.cm.Set3(range(len(labels)))
                total_value = sum(sizes)
                # Create legend labels with percentages
                legend_labels = [f"{label} ({size/total_value*100:.1f}%)" 
                                for label, size in zip(labels, sizes)]
                wedges, texts = ax_pie.pie(sizes, colors=colors, startangle=90)
                ax_pie.set_title('Top 10 Holdings by Value', fontweight='bold')
                # Create legend outside pie with percentages to avoid label overlap
                ax_pie.legend(wedges, legend_labels, title='Holdings', loc='center left', 
                             bbox_to_anchor=(1, 0, 0.5, 1), fontsize=8)
                
                # CAGR comparison chart
                names = [s[0] for s in pdf_data['top_8_cagr']]
                cagrs = [s[1]['avg_cagr'] for s in pdf_data['top_8_cagr']]
                self._add_bar_chart(fig.add_subplot(gs[1, 1]), names, cagrs, 
                                   'Top 8 Performers by CAGR', 'CAGR %')
                fig.axes[-1].axvline(x=analysis['sp500_cagr'], color='blue', linestyle='--', 
                                    label=f"S&P 500: {analysis['sp500_cagr']:.1f}%")
                fig.axes[-1].legend()
                
                # Dollar gain chart
                names = [s[0] for s in pdf_data['top_8_gain']]
                gains = [s[1]['total_gain'] for s in pdf_data['top_8_gain']]
                self._add_bar_chart(fig.add_subplot(gs[2, 0]), names, gains, 
                                   'Top 8 by Total Dollar Gain', 'Total Gain ($)',
                                   positive_color='darkgreen', negative_color='darkred')
                
                # Statistics box
                self._add_stats_box(fig.add_subplot(gs[2, 1]), pdf_data)
                
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)
                
                # Page 2: Top performers detailed table
                fig = plt.figure(figsize=(11, 8.5))
                fig.suptitle('Top 10 Positions - Detailed Metrics', fontsize=16, fontweight='bold')
                ax = fig.add_subplot(111)
                ax.axis('tight')
                ax.axis('off')
                
                table_data = [['Symbol', 'Trades', 'Invested', 'Current', 'Gain', 'Gain%', 'CAGR%']]
                for symbol, stats in pdf_data['top_10_value']:
                    table_data.append([
                        symbol,
                        f"{stats['trades_count']}",
                        f"${stats['total_initial_value']:.0f}",
                        f"${stats['total_current_value']:.0f}",
                        f"${stats['total_gain']:.0f}",
                        f"{stats['gain_percentage']:.1f}%",
                        f"{stats['avg_cagr']:.1f}%"
                    ])
                
                table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                               colWidths=[0.1, 0.1, 0.15, 0.15, 0.15, 0.15, 0.15])
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


# ============================================================================
# Command Line Interface
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Portfolio Analyzer")
    parser.add_argument("--csv", help="Path to CSV file with trades")
    parser.add_argument("--output", "-o", help="Path to save report to text file")
    parser.add_argument("--pdf", help="Path to save report as PDF file with visualizations")
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