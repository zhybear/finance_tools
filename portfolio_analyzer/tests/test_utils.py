"""
Unit tests for Portfolio Performance Analyzer

Run with:
    python3 -m unittest test_utils.py -v

Author: Zhuo Robert Li
Version: 1.3.4
License: ISC
"""

import unittest
import tempfile
import os
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
from portfolio_analyzer import PortfolioAnalyzer, load_trades_from_csv, calculate_cagr, calculate_xirr

class TestSafeDivide(unittest.TestCase):
    """Test the _safe_divide helper method"""
    
    def setUp(self):
        self.analyzer = PortfolioAnalyzer([])
    
    def test_safe_divide_normal(self):
        """Test normal division"""
        result = self.analyzer._safe_divide(10, 2, 0)
        self.assertEqual(result, 5.0)
    
    def test_safe_divide_zero_denominator(self):
        """Test division by zero returns default"""
        result = self.analyzer._safe_divide(10, 0, 99)
        self.assertEqual(result, 99)
    
    def test_safe_divide_zero_denominator_default_zero(self):
        """Test division by zero with default=0"""
        result = self.analyzer._safe_divide(10, 0, 0)
        self.assertEqual(result, 0)
    
    def test_safe_divide_negative_denominator(self):
        """Test negative denominator returns default"""
        result = self.analyzer._safe_divide(10, -5, 0)
        self.assertEqual(result, 0)



class TestUtilsFunctions(unittest.TestCase):
    """Test utility functions in utils.py"""
    
    def test_normalize_history_index_empty_dataframe(self):
        """Test normalize_history_index with empty DataFrame"""
        from portfolio_analyzer.utils import normalize_history_index
        
        empty_df = pd.DataFrame()
        result = normalize_history_index(empty_df)
        self.assertTrue(result.empty)
    
    def test_normalize_history_index_with_timezone(self):
        """Test normalize_history_index removes timezone"""
        from portfolio_analyzer.utils import normalize_history_index
        
        dates = pd.date_range('2020-01-01', periods=3, tz='UTC')
        df = pd.DataFrame({'price': [100, 101, 102]}, index=dates)
        
        result = normalize_history_index(df)
        self.assertIsNone(result.index.tz)
    
    def test_normalize_datetime_with_timezone(self):
        """Test normalize_datetime removes timezone"""
        from portfolio_analyzer.utils import normalize_datetime
        
        dt = pd.Timestamp('2020-01-01', tz='UTC')
        result = normalize_datetime(dt)
        self.assertIsNone(result.tzinfo)
    
    def test_extract_history_empty_dataframe(self):
        """Test extract_history with empty DataFrame"""
        from portfolio_analyzer.utils import extract_history
        
        empty_df = pd.DataFrame()
        result = extract_history(empty_df, 'SBUX')
        self.assertTrue(result.empty)
    
    def test_extract_history_multiindex_columns(self):
        """Test extract_history with MultiIndex columns"""
        from portfolio_analyzer.utils import extract_history
        
        # Create MultiIndex DataFrame like yf.download returns
        dates = pd.date_range('2020-01-01', periods=3)
        columns = pd.MultiIndex.from_product([['Close', 'Open'], ['SBUX', 'MSFT']])
        data = np.random.rand(3, 4)
        df = pd.DataFrame(data, index=dates, columns=columns)
        
        result = extract_history(df, 'SBUX')
        self.assertFalse(result.empty)
        self.assertIn('Close', result.columns)
    
    def test_extract_history_symbol_not_found(self):
        """Test extract_history when symbol not in MultiIndex"""
        from portfolio_analyzer.utils import extract_history
        
        dates = pd.date_range('2020-01-01', periods=3)
        columns = pd.MultiIndex.from_product([['Close'], ['SBUX']])
        data = np.random.rand(3, 1)
        df = pd.DataFrame(data, index=dates, columns=columns)
        
        result = extract_history(df, 'NONEXISTENT')
        self.assertTrue(result.empty)

    def test_extract_history_single_symbol(self):
        """Test extract_history returns data for single-symbol DataFrame"""
        from portfolio_analyzer.utils import extract_history

        dates = pd.date_range('2020-01-01', periods=3)
        df = pd.DataFrame({'Close': [100, 101, 102]}, index=dates)

        result = extract_history(df, 'SBUX')
        self.assertTrue(result.equals(df))
    
    def test_download_history_exception_handling(self):
        """Test download_history handles exceptions gracefully"""
        from portfolio_analyzer.utils import download_history
        from unittest.mock import patch
        
        with patch('portfolio_analyzer.utils.yf.download', side_effect=Exception("Network error")):
            result = download_history(['SBUX'], '2020-01-01')
            self.assertTrue(result.empty)

    def test_download_history_success(self):
        """Test download_history returns data from yfinance"""
        from portfolio_analyzer.utils import download_history
        from unittest.mock import patch

        dates = pd.date_range('2020-01-01', periods=2)
        df = pd.DataFrame({'Close': [100, 101]}, index=dates)

        with patch('portfolio_analyzer.utils.yf.download', return_value=df):
            result = download_history(['SBUX'], '2020-01-01')
            self.assertTrue(result.equals(df))


class TestTickerNormalization(unittest.TestCase):
    """Test ticker symbol normalization functionality"""
    
    def test_normalize_ticker_brkb(self):
        """Test BRKB normalizes to BRK.B"""
        from portfolio_analyzer.utils import normalize_ticker
        
        result = normalize_ticker('BRKB')
        self.assertEqual(result, 'BRK.B')
    
    def test_normalize_ticker_brk_dash_b(self):
        """Test BRK-B normalizes to BRK.B"""
        from portfolio_analyzer.utils import normalize_ticker
        
        result = normalize_ticker('BRK-B')
        self.assertEqual(result, 'BRK.B')
    
    def test_normalize_ticker_brka(self):
        """Test BRKA normalizes to BRK.A"""
        from portfolio_analyzer.utils import normalize_ticker
        
        result = normalize_ticker('BRKA')
        self.assertEqual(result, 'BRK.A')
    
    def test_normalize_ticker_lowercase(self):
        """Test lowercase tickers are converted to uppercase"""
        from portfolio_analyzer.utils import normalize_ticker
        
        result = normalize_ticker('brkb')
        self.assertEqual(result, 'BRK.B')
    
    def test_normalize_ticker_with_whitespace(self):
        """Test whitespace is stripped"""
        from portfolio_analyzer.utils import normalize_ticker
        
        result = normalize_ticker('  BRKB  ')
        self.assertEqual(result, 'BRK.B')
    
    def test_normalize_ticker_unchanged(self):
        """Test normal tickers pass through unchanged"""
        from portfolio_analyzer.utils import normalize_ticker
        
        result = normalize_ticker('AAPL')
        self.assertEqual(result, 'AAPL')
    
    def test_normalize_ticker_empty_string(self):
        """Test empty string returns empty string"""
        from portfolio_analyzer.utils import normalize_ticker
        
        result = normalize_ticker('')
        self.assertEqual(result, '')
    
    def test_normalize_ticker_already_normalized(self):
        """Test already normalized ticker stays the same"""
        from portfolio_analyzer.utils import normalize_ticker
        
        result = normalize_ticker('BRK.B')
        self.assertEqual(result, 'BRK.B')


class TestAnalyzerTickerNormalization(unittest.TestCase):
    """Test that analyzer applies ticker normalization during validation"""
    
    def test_analyzer_normalizes_brkb_trade(self):
        """Test analyzer normalizes BRKB to BRK.B in trade validation"""
        trade = {
            'symbol': 'BRKB',
            'shares': 10,
            'price': 100.0,
            'purchase_date': '2020-01-02'
        }
        
        analyzer = PortfolioAnalyzer([trade])
        
        # After validation, the symbol should be normalized
        valid_trades = [t for t in analyzer.trades if analyzer._validate_trade(t)]
        self.assertEqual(len(valid_trades), 1)
        self.assertEqual(valid_trades[0]['symbol'], 'BRK.B')
    
    def test_analyzer_normalizes_lowercase_ticker(self):
        """Test analyzer normalizes lowercase tickers"""
        trade = {
            'symbol': 'aapl',
            'shares': 10,
            'price': 100.0,
            'purchase_date': '2020-01-02'
        }
        
        analyzer = PortfolioAnalyzer([trade])
        valid_trades = [t for t in analyzer.trades if analyzer._validate_trade(t)]
        self.assertEqual(len(valid_trades), 1)
        self.assertEqual(valid_trades[0]['symbol'], 'AAPL')




if __name__ == '__main__':
    unittest.main(verbosity=2)
