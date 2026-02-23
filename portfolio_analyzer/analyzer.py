"""Core portfolio analyzer class.

Author: Zhuo Robert Li
"""

import yfinance as yf
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
import logging

from .metrics import calculate_cagr, calculate_xirr, DAYS_PER_YEAR
from .utils import (
    safe_divide, normalize_history_index, normalize_datetime,
    extract_history, download_history, SP500_SYMBOL
)

logger = logging.getLogger(__name__)

# Try to import optional libraries 
try:
    import numpy_financial as npf
    XIRR_AVAILABLE = True
except ImportError:
    XIRR_AVAILABLE = False


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
        """
        if not isinstance(trades, list):
            raise TypeError(f"trades must be a list, got {type(trades)}")
        
        self.trades = trades
        self._stock_history_cache = {}
        self._sp500_full_history = None
        self._analysis_cache = None

    def _prepare_histories(self, trades: List[Dict]) -> None:
        """Bulk download and cache all stock and S&P 500 price histories."""
        symbols = {trade["symbol"] for trade in trades}
        if not symbols:
            return

        earliest_date = min(trade["purchase_date"] for trade in trades)
        data = download_history(list(symbols), earliest_date)

        if not data.empty:
            if isinstance(data.columns, pd.MultiIndex):
                for symbol in symbols:
                    symbol_hist = extract_history(data, symbol).dropna(how="all")
                    if not symbol_hist.empty:
                        self._stock_history_cache[symbol] = normalize_history_index(symbol_hist)
            else:
                symbol = next(iter(symbols))
                self._stock_history_cache[symbol] = normalize_history_index(data)

        if self._sp500_full_history is None:
            sp500_data = download_history([SP500_SYMBOL], earliest_date)
            sp500_hist = extract_history(sp500_data, SP500_SYMBOL)
            self._sp500_full_history = normalize_history_index(sp500_hist)

    def _validate_trade(self, trade: Dict) -> bool:
        """Validate that a trade has all required fields and valid values.
        
        Args:
            trade: Trade dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_keys = {"symbol", "shares", "purchase_date", "price"}
        
        if not isinstance(trade, dict):
            logger.warning("Invalid trade: expected dict")
            return False
        
        missing = required_keys - trade.keys()
        if missing:
            logger.warning(f"Invalid trade: missing keys {missing}")
            return False
        
        if not isinstance(trade["symbol"], str) or not trade["symbol"].strip():
            logger.warning("Invalid trade: symbol must be a non-empty string")
            return False
        
        if not isinstance(trade["shares"], (int, float)) or trade["shares"] <= 0:
            logger.warning("Invalid trade: shares must be a positive number")
            return False
        
        if not isinstance(trade["price"], (int, float)) or trade["price"] <= 0:
            logger.warning("Invalid trade: price must be a positive number")
            return False
        
        if not isinstance(trade["purchase_date"], str):
            logger.warning("Invalid trade: purchase_date must be a string in YYYY-MM-DD format")
            return False
        
        try:
            datetime.fromisoformat(trade["purchase_date"])
        except ValueError:
            logger.warning("Invalid trade: purchase_date must be in YYYY-MM-DD format")
            return False
        
        return True

    def get_stock_performance(
        self, 
        symbol: str, 
        purchase_date: str, 
        shares: int, 
        purchase_price: float
    ) -> Optional[Dict]:
        """Calculate performance metrics for a single trade."""
        try:
            hist = self._stock_history_cache.get(symbol)
            if hist is None or hist.empty:
                stock = yf.Ticker(symbol)
                hist = stock.history(start=purchase_date)
                hist = normalize_history_index(hist)
                self._stock_history_cache[symbol] = hist

            purchase_dt = normalize_datetime(pd.to_datetime(purchase_date))
            hist = hist.loc[hist.index >= purchase_dt]

            if hist.empty:
                return None

            current_price = hist['Close'].iloc[-1]
            current_date = normalize_datetime(hist.index[-1])

            years_held = (current_date - purchase_dt).days / DAYS_PER_YEAR
            if years_held <= 0:
                print(f"Invalid holding period for {symbol}: {purchase_date} not before {current_date.date()}")
                return None

            initial_value = purchase_price * shares
            current_value = current_price * shares
            stock_cagr = calculate_cagr(initial_value, current_value, years_held)

            stock_xirr = 0.0
            if XIRR_AVAILABLE:
                stock_xirr = calculate_xirr(
                    [purchase_date, current_date.strftime('%Y-%m-%d')],
                    [-initial_value, current_value]
                )

            if self._sp500_full_history is not None and not self._sp500_full_history.empty:
                sp500_hist = self._sp500_full_history.loc[self._sp500_full_history.index >= purchase_dt]
            else:
                sp500 = yf.Ticker(SP500_SYMBOL)
                sp500_hist = sp500.history(start=purchase_date)
                sp500_hist = normalize_history_index(sp500_hist)
                sp500_hist = sp500_hist.loc[sp500_hist.index >= purchase_dt]
            
            if sp500_hist.empty:
                return None
            
            sp500_purchase_price = sp500_hist['Close'].iloc[0]
            sp500_current_price = sp500_hist['Close'].iloc[-1]
            sp500_current_value = (sp500_current_price / sp500_purchase_price) * initial_value
            sp500_cagr = calculate_cagr(initial_value, sp500_current_value, years_held)

            sp500_xirr = 0.0
            if XIRR_AVAILABLE:
                sp500_xirr = calculate_xirr(
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

    def analyze_portfolio(self) -> Dict:
        """Analyze entire portfolio performance with weighted CAGR and XIRR."""
        results = []
        total_initial_value = 0
        total_current_value = 0
        total_sp500_current_value = 0
        weighted_years_sum = 0
        
        cash_flow_dates = []
        cash_flows_stocks = []
        cash_flows_sp500 = []

        valid_trades = [trade for trade in self.trades if self._validate_trade(trade)]
        self._prepare_histories(valid_trades)

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
                
                cash_flow_dates.append(perf['purchase_date'])
                cash_flows_stocks.append(-perf['initial_value'])
                cash_flows_sp500.append(-perf['initial_value'])

        if results:
            today = datetime.now().strftime('%Y-%m-%d')
            
            if cash_flows_stocks:
                cash_flow_dates.append(today)
                cash_flows_stocks.append(total_current_value)
                cash_flows_sp500.append(total_sp500_current_value)

        portfolio_xirr = 0.0
        sp500_xirr = 0.0
        
        if total_initial_value > 0:
            weighted_years = weighted_years_sum / total_initial_value
            portfolio_cagr = calculate_cagr(total_initial_value, total_current_value, weighted_years)
            sp500_cagr = calculate_cagr(total_initial_value, total_sp500_current_value, weighted_years)
            
            if cash_flow_dates:
                # Sort cash flows by date (optimization: sort once, use for both stock and sp500)
                sorted_pairs = sorted(zip(cash_flow_dates, cash_flows_stocks, cash_flows_sp500), 
                                     key=lambda x: x[0])
                cash_flow_dates_sorted = [d for d, _, _ in sorted_pairs]
                cash_flows_stocks_sorted = [stock_cf for _, stock_cf, _ in sorted_pairs]
                cash_flows_sp500_sorted = [sp500_cf for _, _, sp500_cf in sorted_pairs]
            else:
                cash_flow_dates_sorted = cash_flow_dates
                cash_flows_stocks_sorted = cash_flows_stocks
                cash_flows_sp500_sorted = cash_flows_sp500
            
            portfolio_xirr = calculate_xirr(cash_flow_dates_sorted, cash_flows_stocks_sorted)
            sp500_xirr = calculate_xirr(cash_flow_dates_sorted, cash_flows_sp500_sorted)
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

    def _calculate_symbol_accumulation(self, trades: List[Dict]) -> Dict:
        """Calculate accumulated earnings and metrics for each stock symbol."""
        symbol_stats = {}
        symbol_trades = {}
        
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
                    'total_sp500_cagr_weighted': 0,
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
            stats['total_sp500_cagr_weighted'] += trade['sp500_cagr'] * trade['initial_value']
            stats['total_years_weighted'] += trade['years_held'] * trade['initial_value']
            symbol_trades[symbol].append(trade)
        
        for symbol, stats in symbol_stats.items():
            initial_val = stats['total_initial_value']
            current_val = stats['total_current_value']
            sp500_val = stats['total_sp500_value']
            
            stats['total_gain'] = current_val - initial_val
            sp500_gain = sp500_val - initial_val
            stats['sp500_gain'] = sp500_gain
            stats['outperformance'] = stats['total_gain'] - sp500_gain
            
            stats['avg_years_held'] = safe_divide(stats['total_years_weighted'], initial_val, 0.0)
            
            if stats['trades_count'] > 0:
                trades_for_symbol = symbol_trades[symbol]
                trades_with_dates = [t for t in trades_for_symbol if 'purchase_date' in t]
                
                if trades_with_dates:
                    total_weighted_cagr = 0.0
                    total_weight = 0.0
                    
                    for trade in trades_with_dates:
                        purchase_date = pd.to_datetime(trade['purchase_date'])
                        today = pd.Timestamp.now()
                        years_held = (today - purchase_date).days / 365.25
                        
                        individual_cagr = calculate_cagr(
                            trade['initial_value'],
                            trade['current_value'],
                            years_held if years_held > 0 else 0.1
                        )
                        
                        weight = trade['initial_value'] * years_held
                        total_weighted_cagr += individual_cagr * weight
                        total_weight += weight
                    
                    stats['avg_cagr'] = safe_divide(total_weighted_cagr, total_weight, 0.0)
                else:
                    stats['avg_cagr'] = calculate_cagr(initial_val, current_val, stats['avg_years_held'])
            else:
                stats['avg_cagr'] = 0.0
            
            stats['gain_percentage'] = safe_divide(stats['total_gain'], initial_val, 0.0) * 100
            stats['outperformance_pct'] = safe_divide(stats['outperformance'], initial_val, 0.0) * 100
            
            if XIRR_AVAILABLE and stats['trades_count'] > 0:
                trades_for_symbol = symbol_trades[symbol]
                if trades_for_symbol and 'purchase_date' in trades_for_symbol[0]:
                    dates = [t['purchase_date'] for t in trades_for_symbol]
                    cash_flows = [-t['initial_value'] for t in trades_for_symbol]
                    
                    date_cf_pairs = list(zip(dates, cash_flows))
                    date_cf_pairs.sort(key=lambda x: x[0])
                    dates = [d for d, cf in date_cf_pairs]
                    cash_flows = [cf for d, cf in date_cf_pairs]
                    
                    dates.append(str(pd.Timestamp.now().date()))
                    cash_flows.append(current_val)
                    
                    xirr_result = calculate_xirr(dates, cash_flows)
                    stats['avg_xirr'] = xirr_result
                else:
                    total_xirr_weighted = sum(t['stock_xirr'] * t['initial_value'] 
                                             for t in trades_for_symbol)
                    stats['avg_xirr'] = safe_divide(total_xirr_weighted, initial_val, 0.0)
            else:
                stats['avg_xirr'] = 0.0
            
            stats['avg_sp500_xirr'] = safe_divide(stats['total_sp500_xirr_weighted'], initial_val, 0.0)
            stats['avg_sp500_cagr'] = safe_divide(stats['total_sp500_cagr_weighted'], initial_val, 0.0)
            stats['xirr_outperformance_pct'] = stats['avg_xirr'] - stats['avg_sp500_xirr']
            
            del stats['total_sp500_xirr_weighted']
            del stats['total_sp500_cagr_weighted']
            del stats['total_years_weighted']
        
        return symbol_stats
    
    def print_report(self, output_file: Optional[str] = None) -> None:
        """Generate and print text report."""
        from .reports import TextReportGenerator
        TextReportGenerator.generate(self, output_file=output_file)
    
    def generate_pdf_report(self, pdf_path: str) -> None:
        """Generate PDF report with visualizations."""
        from .reports import PDFReportGenerator
        PDFReportGenerator.generate(self, pdf_path)
    
    def generate_html_report(self, html_path: str) -> None:
        """Generate interactive HTML dashboard report."""
        from .reports import HTMLReportGenerator
        HTMLReportGenerator.generate(self, html_path)
    
    # Backward compatibility methods
    def calculate_cagr(self, start_value: float, end_value: float, years: float) -> float:
        """Backward compatibility wrapper for calculate_cagr function."""
        return calculate_cagr(start_value, end_value, years)
    
    def calculate_xirr(self, dates: list, cash_flows: list) -> float:
        """Backward compatibility wrapper for calculate_xirr function."""
        return calculate_xirr(dates, cash_flows)
    
    def _safe_divide(self, numerator: float, denominator: float, default: float = 0.0) -> float:
        """Backward compatibility wrapper for safe_divide function."""
        return safe_divide(numerator, denominator, default)
