"""
Shared test fixtures and test data builders for portfolio analyzer tests.

This module provides common fixtures and helper classes to reduce duplication
and improve maintainability across test modules.

Author: Zhuo Robert Li
Version: 1.3.3
License: ISC
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any


class TradeBuilder:
    """Builder class for creating test trade data efficiently."""
    
    # Common test symbols with historical prices for consistency
    SYMBOL_DATA = {
        'MSFT': {'name': 'Microsoft', 'date_2020': 160.84, 'date_2021': 222.16, 'date_2022': 310.23},
        'SBUX': {'name': 'Starbucks', 'date_2020': 89.35, 'date_2021': 108.62, 'date_2022': 85.42},
        'AAPL': {'name': 'Apple', 'date_2020': 75.09, 'date_2021': 145.00, 'date_2022': 150.42},
        'NVDA': {'name': 'NVIDIA', 'date_2020': 100.00, 'date_2021': 145.00, 'date_2022': 130.00},
        'TSLA': {'name': 'Tesla', 'date_2020': 130.00, 'date_2021': 380.00, 'date_2022': 370.00},
    }
    
    @staticmethod
    def simple_trade(symbol: str = 'MSFT', shares: int = 100, 
                    purchase_date: str = '2020-01-02', price: float = None) -> Dict[str, Any]:
        """
        Create a simple trade dict for testing.
        
        Args:
            symbol: Stock symbol (default: 'MSFT')
            shares: Number of shares (default: 100)
            purchase_date: Purchase date in YYYY-MM-DD format
            price: Stock price at purchase (auto-selected if None)
        
        Returns:
            Trade dictionary with symbol, shares, purchase_date, and price
        """
        if price is None:
            if symbol in TradeBuilder.SYMBOL_DATA:
                pair_key = 'date_' + purchase_date.split('-')[0]
                price = TradeBuilder.SYMBOL_DATA[symbol].get(pair_key, 100.0)
            else:
                price = 100.0
        
        return {
            'symbol': symbol,
            'shares': shares,
            'purchase_date': purchase_date,
            'price': float(price)
        }
    
    @staticmethod
    def multi_trade(*trades) -> List[Dict[str, Any]]:
        """
        Create a list of trades from arguments.
        
        Can accept either trade dicts or results from simple_trade().
        
        Example:
            trades = TradeBuilder.multi_trade(
                TradeBuilder.simple_trade('MSFT', 50, '2020-01-02'),
                TradeBuilder.simple_trade('SBUX', 100, '2020-01-02'),
            )
        """
        return list(trades)
    
    @staticmethod
    def single_symbol_multi_date(symbol: str = 'MSFT', shares_per_trade: int = 20,
                                 num_trades: int = 3, start_year: int = 2020) -> List[Dict[str, Any]]:
        """
        Create multiple trades of the same symbol on different dates.
        
        Args:
            symbol: Stock symbol
            shares_per_trade: Shares per trade
            num_trades: Number of trades to create
            start_year: Starting year for first trade
        
        Returns:
            List of trade dictionaries
        """
        trades = []
        for i in range(num_trades):
            year = start_year + i
            price = TradeBuilder._get_price_for_year(symbol, year)
            trades.append({
                'symbol': symbol,
                'shares': shares_per_trade,
                'purchase_date': f'{year}-01-02',
                'price': price
            })
        return trades
    
    @staticmethod
    def sp500_trades(num_trades: int = 3, start_year: int = 2018) -> List[Dict[str, Any]]:
        """
        Create S&P 500 benchmark trades for testing.
        
        Args:
            num_trades: Number of trades
            start_year: Starting year
        
        Returns:
            List of S&P 500 trades
        """
        sp500_prices = {
            2018: 2734.62,
            2019: 2822.48,
            2020: 3500.31,
            2021: 4709.85,
            2022: 3839.50,
            2023: 4887.71,
        }
        
        trades = []
        for i in range(num_trades):
            year = start_year + i
            if year in sp500_prices:
                trades.append({
                    'symbol': '^GSPC',
                    'shares': 50 + (i * 25),
                    'purchase_date': f'{year}-06-01',
                    'price': sp500_prices[year]
                })
        return trades
    
    @staticmethod
    def diverse_portfolio(num_shares_per_symbol: int = 20,
                         purchase_date: str = '2020-01-02') -> List[Dict[str, Any]]:
        """
        Create a diverse portfolio with multiple symbols.
        
        Args:
            num_shares_per_symbol: Shares per symbol
            purchase_date: Purchase date for all trades
        
        Returns:
            List of trades across different symbols
        """
        symbols = ['MSFT', 'SBUX', 'NVDA', 'AAPL', 'TSLA']
        trades = []
        for symbol in symbols:
            price = TradeBuilder._get_price_for_year(symbol, int(purchase_date.split('-')[0]))
            trades.append({
                'symbol': symbol,
                'shares': num_shares_per_symbol,
                'purchase_date': purchase_date,
                'price': price
            })
        return trades
    
    @staticmethod
    def large_portfolio(num_symbols: int = 50, shares_per_symbol: int = 10) -> List[Dict[str, Any]]:
        """
        Create a large portfolio for performance testing.
        
        Args:
            num_symbols: Number of different symbols (will repeat core symbols)
            shares_per_symbol: Shares per symbol
        
        Returns:
            List of trades for a large portfolio
        """
        core_symbols = list(TradeBuilder.SYMBOL_DATA.keys())
        trades = []
        
        for i in range(num_symbols):
            symbol = core_symbols[i % len(core_symbols)]
            trades.append({
                'symbol': f'{symbol}_{i}' if i >= len(core_symbols) else symbol,
                'shares': shares_per_symbol,
                'purchase_date': '2020-06-01',
                'price': 100.0 + (i % 50)
            })
        return trades
    
    @staticmethod
    def _get_price_for_year(symbol: str, year: int) -> float:
        """Helper to get historical price for a symbol/year."""
        key = f'date_{year}'
        if symbol in TradeBuilder.SYMBOL_DATA:
            return TradeBuilder.SYMBOL_DATA[symbol].get(key, 100.0)
        return 100.0
    
    @staticmethod
    def recent_trade(symbol: str = 'MSFT', days_back: int = 5,
                    shares: int = 1, price: float = 400.0) -> Dict[str, Any]:
        """
        Create a recent trade (for testing breakeven/near-current positions).
        
        Args:
            symbol: Stock symbol
            days_back: Days in the past from today
            shares: Number of shares
            price: Stock price at purchase
        
        Returns:
            Recent trade dictionary
        """
        date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        return {
            'symbol': symbol,
            'shares': shares,
            'purchase_date': date,
            'price': price
        }
    
    @staticmethod
    def old_trade(symbol: str = 'MSFT', years_back: int = 5,
                 shares: int = 20, price: float = 100.0) -> Dict[str, Any]:
        """
        Create an old trade (for testing long-term performance).
        
        Args:
            symbol: Stock symbol
            years_back: Years in the past
            shares: Number of shares
            price: Stock price at purchase
        
        Returns:
            Old trade dictionary
        """
        year = datetime.now().year - years_back
        return {
            'symbol': symbol,
            'shares': shares,
            'purchase_date': f'{year}-01-02',
            'price': price
        }


class TestDataConstants:
    """Common test data constants."""
    
    # Common dates for consistent testing
    DATE_2020 = '2020-01-02'
    DATE_2021 = '2021-01-04'
    DATE_2022 = '2022-01-03'
    DATE_2023 = '2023-01-03'
    
    # Common prices to ensure consistency
    MSFT_2020 = 160.84
    MSFT_2021 = 222.16
    MSFT_2022 = 310.23
    
    SBUX_2020 = 89.35
    SBUX_2021 = 108.62
    SBUX_2022 = 85.42
    
    AAPL_2020 = 75.09
    AAPL_2021 = 145.00
    AAPL_2022 = 150.42
