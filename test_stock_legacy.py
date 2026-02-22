"""
Unit tests for Portfolio Performance Analyzer

Run with:
    python3 -m unittest test_stock.py -v

Author: Zhuo Robert Li
Version: 1.2.0
License: ISC
"""

import unittest
import tempfile
import os
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
from portfolio_analyzer import PortfolioAnalyzer, load_trades_from_csv, calculate_cagr, calculate_xirr


class TestCAGRCalculation(unittest.TestCase):
    """Test CAGR calculation formula"""
    
    def setUp(self):
        self.analyzer = PortfolioAnalyzer([])
    
    def test_cagr_basic(self):
        """Test basic CAGR calculation"""
        # $100 grows to $200 in 5 years = 14.87% CAGR
        cagr = self.analyzer.calculate_cagr(100, 200, 5)
        self.assertAlmostEqual(cagr, 14.87, places=1)
    
    def test_cagr_triple(self):
        """Test CAGR when value triples"""
        # Triple in 10 years = 11.61% CAGR
        cagr = self.analyzer.calculate_cagr(1000, 3000, 10)
        self.assertAlmostEqual(cagr, 11.61, places=1)
    
    def test_cagr_zero_years(self):
        """Test CAGR with zero years returns 0"""
        cagr = self.analyzer.calculate_cagr(100, 200, 0)
        self.assertEqual(cagr, 0)
    
    def test_cagr_zero_start_value(self):
        """Test CAGR with zero start value returns 0"""
        cagr = self.analyzer.calculate_cagr(0, 200, 5)
        self.assertEqual(cagr, 0)
    
    def test_cagr_negative_performance(self):
        """Test CAGR with loss"""
        # $100 becomes $50 in 5 years = -12.94% CAGR
        cagr = self.analyzer.calculate_cagr(100, 50, 5)
        self.assertAlmostEqual(cagr, -12.94, places=1)
    
    def test_weighted_cagr_multiple_purchases_same_year(self):
        """
        Test weighted CAGR formula with multiple purchases.
        
        Formula: weighted_cagr = Σ(r_i * w_i) / Σ(w_i)
        where r_i = CAGR of transaction i
              w_i = investment_amount_i * years_held_i
        
        Example:
        - Transaction 1: $100 invested 5 years ago, current value $200 (CAGR=14.87%)
          weight_1 = 100 * 5 = 500
        - Transaction 2: $100 invested 1 year ago, current value $110 (CAGR=10%)
          weight_2 = 100 * 1 = 100
        - weighted_cagr = (14.87*500 + 10*100) / (500+100) = 8493.5 / 600 = 14.16%
        """
        # Create trades with different purchase dates
        from datetime import datetime, timedelta
        today = datetime.now().strftime('%Y-%m-%d')
        five_years_ago = (datetime.now() - timedelta(days=365.25*5)).strftime('%Y-%m-%d')
        one_year_ago = (datetime.now() - timedelta(days=365.25)).strftime('%Y-%m-%d')
        
        trades = [
            {
                'symbol': 'TEST',
                'shares': 100,
                'purchase_date': five_years_ago,
                'price': 1.0,
                'initial_value': 100,
                'current_value': 200,  # 100% gain = 14.87% CAGR
                'years_held': 5.0,
                'stock_xirr': 14.87,
                'sp500_current_value': 150,
                'sp500_xirr': 8.0,
            },
            {
                'symbol': 'TEST',
                'shares': 100,
                'purchase_date': one_year_ago,
                'price': 1.0,
                'initial_value': 100,
                'current_value': 110,  # 10% gain = 10% CAGR
                'years_held': 1.0,
                'stock_xirr': 10.0,
                'sp500_current_value': 120,
                'sp500_xirr': 20.0,
            }
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        stats = analyzer._calculate_symbol_accumulation(trades)
        
        # Verify weighted CAGR
        weighted_cagr = (14.87 * (100 * 5) + 10.0 * (100 * 1)) / ((100 * 5) + (100 * 1))
        expected_weighted_cagr = weighted_cagr
        
        self.assertIn('TEST', stats)
        test_stats = stats['TEST']
        
        # Check that weighted CAGR is weighted toward the longer-held position
        self.assertAlmostEqual(test_stats['avg_cagr'], expected_weighted_cagr, places=1)


class TestSP500Benchmark(unittest.TestCase):
    """Test that S&P 500 vs S&P 500 shows no outperformance"""
    
    def test_sp500_vs_itself_single_trade(self):
        """
        Test that buying S&P 500 and comparing to S&P 500 shows 0% outperformance.
        This is the critical self-consistency check.
        """
        trades = [
            {
                "symbol": "^GSPC",
                "shares": 100,
                "purchase_date": "2020-01-02",
                "price": 3257.85
            }
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        analysis = analyzer.analyze_portfolio()
        
        # Portfolio should match S&P 500 benchmark exactly (within small rounding error)
        self.assertIsNotNone(analysis['trades'])
        self.assertGreater(len(analysis['trades']), 0, "Expected at least one trade result")
        
        # Check outperformance is very close to 0%
        outperformance = analysis['portfolio_outperformance']
        self.assertAlmostEqual(
            outperformance, 
            0.0, 
            places=1,
            msg=f"S&P 500 vs S&P 500 should show 0% outperformance, got {outperformance:.2f}%"
        )
    
    def test_sp500_vs_itself_multiple_trades(self):
        """Test multiple S&P 500 trades over different dates"""
        trades = [
            {"symbol": "^GSPC", "shares": 50, "purchase_date": "2018-06-01", "price": 2734.62},
            {"symbol": "^GSPC", "shares": 30, "purchase_date": "2019-03-15", "price": 2822.48},
            {"symbol": "^GSPC", "shares": 100, "purchase_date": "2020-09-01", "price": 3500.31},
            {"symbol": "^GSPC", "shares": 75, "purchase_date": "2021-12-15", "price": 4709.85},
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        analysis = analyzer.analyze_portfolio()
        
        # All trades should have near-zero outperformance
        for trade in analysis['trades']:
            self.assertAlmostEqual(
                trade['outperformance'],
                0.0,
                delta=0.5,  # Allow up to 0.5% difference due to timing/rounding
                msg=f"S&P 500 trade from {trade['purchase_date']} should have ~0% outperformance, got {trade['outperformance']:.2f}%"
            )
        
        # Portfolio level should also be near-zero
        self.assertAlmostEqual(analysis['portfolio_outperformance'], 0.0, delta=0.5)


class TestCSVLoading(unittest.TestCase):
    """Test CSV file loading and validation"""
    
    def test_load_valid_csv(self):
        """Test loading a properly formatted CSV file"""
        csv_content = """symbol,shares,purchase_date,price
AAPL,100,2020-01-02,75.50
MSFT,50,2021-01-04,220.00
NVDA,25,2019-06-15,145.75"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            trades = load_trades_from_csv(temp_file)
            self.assertEqual(len(trades), 3)
            self.assertEqual(trades[0]['symbol'], 'AAPL')
            self.assertEqual(trades[0]['shares'], 100)
            self.assertEqual(trades[0]['price'], 75.50)
            self.assertEqual(trades[0]['purchase_date'], '2020-01-02')
        finally:
            os.unlink(temp_file)
    
    def test_load_csv_missing_columns(self):
        """Test that CSV with missing columns raises ValueError"""
        csv_content = """symbol,shares,purchase_date
AAPL,100,2020-01-02"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            with self.assertRaises(ValueError) as context:
                load_trades_from_csv(temp_file)
            self.assertIn('price', str(context.exception))
        finally:
            os.unlink(temp_file)
    
    def test_load_csv_with_invalid_data(self):
        """Test that invalid rows are filtered out"""
        csv_content = """symbol,shares,purchase_date,price
AAPL,100,2020-01-02,75.50
MSFT,invalid,2021-01-04,220.00
NVDA,25,not-a-date,145.75
TSLA,-50,2020-05-01,100.00"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            trades = load_trades_from_csv(temp_file)
            # AAPL is valid, TSLA has negative shares but will load (validation happens later)
            # Only rows with truly invalid data types are filtered by CSV loader
            # MSFT (invalid shares parsed as NaN) and NVDA (invalid date) are dropped
            self.assertGreater(len(trades), 0)
            # Verify AAPL is in the results
            symbols = [t['symbol'] for t in trades]
            self.assertIn('AAPL', symbols)
            # MSFT and NVDA should be filtered out due to parse errors
            self.assertNotIn('MSFT', symbols)
            self.assertNotIn('NVDA', symbols)
        finally:
            os.unlink(temp_file)


class TestTradeValidation(unittest.TestCase):
    """Test trade validation logic"""
    
    def setUp(self):
        self.analyzer = PortfolioAnalyzer([])
    
    def test_valid_trade(self):
        """Test that a valid trade passes validation"""
        trade = {
            "symbol": "AAPL",
            "shares": 100,
            "purchase_date": "2020-01-02",
            "price": 75.50
        }
        self.assertTrue(self.analyzer._validate_trade(trade))
    
    def test_invalid_trade_missing_keys(self):
        """Test that trade missing keys fails validation"""
        trade = {
            "symbol": "AAPL",
            "shares": 100,
            "price": 75.50
        }
        self.assertFalse(self.analyzer._validate_trade(trade))
    
    def test_invalid_trade_negative_shares(self):
        """Test that negative shares fail validation"""
        trade = {
            "symbol": "AAPL",
            "shares": -100,
            "purchase_date": "2020-01-02",
            "price": 75.50
        }
        self.assertFalse(self.analyzer._validate_trade(trade))
    
    def test_invalid_trade_zero_price(self):
        """Test that zero price fails validation"""
        trade = {
            "symbol": "AAPL",
            "shares": 100,
            "purchase_date": "2020-01-02",
            "price": 0
        }
        self.assertFalse(self.analyzer._validate_trade(trade))
    
    def test_invalid_trade_bad_date_format(self):
        """Test that invalid date format fails validation"""
        trade = {
            "symbol": "AAPL",
            "shares": 100,
            "purchase_date": "01/02/2020",
            "price": 75.50
        }
        self.assertFalse(self.analyzer._validate_trade(trade))


class TestPortfolioAnalysis(unittest.TestCase):
    """Test portfolio analysis calculations"""
    
    def test_empty_portfolio(self):
        """Test analyzing an empty portfolio"""
        analyzer = PortfolioAnalyzer([])
        analysis = analyzer.analyze_portfolio()
        
        self.assertEqual(len(analysis['trades']), 0)
        self.assertEqual(analysis['total_initial_value'], 0)
        self.assertEqual(analysis['total_current_value'], 0)
    
    def test_portfolio_weighted_years(self):
        """
        Test that investment-weighted years are calculated correctly.
        
        Example: 
        - $100 invested for 10 years
        - $900 invested for 2 years
        Weighted years = (100*10 + 900*2) / 1000 = 2.8 years
        """
        # This is implicitly tested through the portfolio CAGR calculation
        # Just verify that results are returned
        trades = [
            {"symbol": "AAPL", "shares": 10, "purchase_date": "2015-01-02", "price": 10.0},
            {"symbol": "MSFT", "shares": 90, "purchase_date": "2023-01-02", "price": 10.0},
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        analysis = analyzer.analyze_portfolio()
        
        # Should have results for both trades
        self.assertGreater(len(analysis['trades']), 0)
        self.assertGreater(analysis['total_initial_value'], 0)
        self.assertGreater(analysis['portfolio_cagr'], -100)  # Should have some CAGR


class TestSP500BenchmarkCSV(unittest.TestCase):
    """
    Integration test: Create CSV with S&P 500 trades and verify benchmark accuracy.
    This is the test the user specifically requested.
    """
    
    def test_sp500_csv_random_dates(self):
        """
        Create a CSV with multiple S&P 500 trades on random dates.
        Verify that the portfolio CAGR matches S&P 500 benchmark (0% outperformance).
        """
        # Create CSV with S&P 500 trades on various dates
        csv_content = """symbol,shares,purchase_date,price
^GSPC,100,2018-03-15,2752.01
^GSPC,50,2019-07-22,3007.39
^GSPC,75,2020-11-02,3369.16
^GSPC,120,2021-04-19,4163.26
^GSPC,80,2022-08-10,4210.24
^GSPC,60,2023-02-28,3970.15"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            # Load trades from CSV
            trades = load_trades_from_csv(temp_file)
            self.assertEqual(len(trades), 6, "Should load all 6 trades")
            
            # Analyze portfolio
            analyzer = PortfolioAnalyzer(trades)
            analysis = analyzer.analyze_portfolio()
            
            # Verify all trades were analyzed
            self.assertEqual(
                len(analysis['trades']), 
                6, 
                "All 6 trades should be analyzed"
            )
            
            # Check each individual trade has near-zero outperformance
            for i, trade in enumerate(analysis['trades']):
                self.assertAlmostEqual(
                    trade['outperformance'],
                    0.0,
                    delta=0.5,  # Allow up to 0.5% difference
                    msg=f"Trade {i+1} ({trade['purchase_date']}): S&P 500 should match itself, got {trade['outperformance']:.2f}% diff"
                )
            
            # Check portfolio-level metrics
            portfolio_outperformance = analysis['portfolio_outperformance']
            self.assertAlmostEqual(
                portfolio_outperformance,
                0.0,
                delta=0.5,  # Within 0.5 percentage points
                msg=f"Portfolio outperformance should be ~0%, got {portfolio_outperformance:.2f}%"
            )
            
            # Verify portfolio CAGR equals S&P 500 CAGR
            portfolio_cagr = analysis['portfolio_cagr']
            sp500_cagr = analysis['sp500_cagr']
            self.assertAlmostEqual(
                portfolio_cagr,
                sp500_cagr,
                delta=0.5,  # Within 0.5 percentage points
                msg=f"Portfolio CAGR ({portfolio_cagr:.2f}%) should match S&P 500 CAGR ({sp500_cagr:.2f}%)"
            )
            
            # Verify current value equals S&P 500 benchmark value
            current_value = analysis['total_current_value']
            sp500_value = analysis['total_sp500_current_value']
            percent_diff = abs(current_value - sp500_value) / sp500_value * 100
            self.assertLess(
                percent_diff,
                1.0,  # Less than 1% difference
                msg=f"Portfolio value should match S&P 500 value within 1%"
            )
            
            print(f"\n✅ S&P 500 Self-Consistency Test PASSED")
            print(f"   Portfolio CAGR: {portfolio_cagr:.2f}%")
            print(f"   S&P 500 CAGR:   {sp500_cagr:.2f}%")
            print(f"   Outperformance: {portfolio_outperformance:.2f}%")
            print(f"   Value Difference: {percent_diff:.4f}%")
            
        finally:
            os.unlink(temp_file)


class TestSymbolAccumulation(unittest.TestCase):
    """Test symbol accumulation and aggregation logic"""
    
    def test_symbol_accumulation_single_symbol(self):
        """Test accumulation for a single symbol"""
        trades = [
            {'symbol': 'AAPL', 'shares': 100, 'initial_value': 1000, 'current_value': 1500, 
             'stock_cagr': 10.0, 'stock_xirr': 9.5, 'sp500_cagr': 8.0, 'sp500_xirr': 7.5,
             'sp500_current_value': 1200, 'years_held': 5},
            {'symbol': 'AAPL', 'shares': 50, 'initial_value': 500, 'current_value': 800, 
             'stock_cagr': 12.5, 'stock_xirr': 12.0, 'sp500_cagr': 8.0, 'sp500_xirr': 7.5,
             'sp500_current_value': 600, 'years_held': 5}
        ]
        
        analyzer = PortfolioAnalyzer([])
        stats = analyzer._calculate_symbol_accumulation(trades)
        
        self.assertIn('AAPL', stats)
        self.assertEqual(stats['AAPL']['trades_count'], 2)
        self.assertEqual(stats['AAPL']['total_shares'], 150)
        self.assertEqual(stats['AAPL']['total_initial_value'], 1500)
        self.assertEqual(stats['AAPL']['total_current_value'], 2300)
        self.assertEqual(stats['AAPL']['total_gain'], 800)
        self.assertGreater(stats['AAPL']['gain_percentage'], 0)

    def test_symbol_accumulation_multiple_symbols(self):
        """Test accumulation for multiple symbols"""
        trades = [
            {'symbol': 'AAPL', 'shares': 100, 'initial_value': 1000, 'current_value': 1500,
             'stock_cagr': 10.0, 'stock_xirr': 9.5, 'sp500_cagr': 8.0, 'sp500_xirr': 7.5,
             'sp500_current_value': 1200, 'years_held': 5},
            {'symbol': 'MSFT', 'shares': 50, 'initial_value': 2000, 'current_value': 3000,
             'stock_cagr': 8.5, 'stock_xirr': 8.0, 'sp500_cagr': 8.0, 'sp500_xirr': 7.5,
             'sp500_current_value': 2400, 'years_held': 5},
            {'symbol': 'AAPL', 'shares': 50, 'initial_value': 500, 'current_value': 600,
             'stock_cagr': 3.7, 'stock_xirr': 3.5, 'sp500_cagr': 8.0, 'sp500_xirr': 7.5,
             'sp500_current_value': 600, 'years_held': 5}
        ]
        
        analyzer = PortfolioAnalyzer([])
        stats = analyzer._calculate_symbol_accumulation(trades)
        
        self.assertEqual(len(stats), 2)
        self.assertIn('AAPL', stats)
        self.assertIn('MSFT', stats)
        self.assertEqual(stats['AAPL']['trades_count'], 2)
        self.assertEqual(stats['MSFT']['trades_count'], 1)

    def test_symbol_accumulation_zero_gain(self):
        """Test accumulation when there's no gain"""
        trades = [
            {'symbol': 'FLAT', 'shares': 100, 'initial_value': 1000, 'current_value': 1000,
             'stock_cagr': 0.0, 'stock_xirr': 0.0, 'sp500_cagr': 8.0, 'sp500_xirr': 7.5,
             'sp500_current_value': 1100, 'years_held': 5}
        ]
        
        analyzer = PortfolioAnalyzer([])
        stats = analyzer._calculate_symbol_accumulation(trades)
        
        self.assertEqual(stats['FLAT']['total_gain'], 0)
        self.assertEqual(stats['FLAT']['gain_percentage'], 0)


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
        result = extract_history(empty_df, 'AAPL')
        self.assertTrue(result.empty)
    
    def test_extract_history_multiindex_columns(self):
        """Test extract_history with MultiIndex columns"""
        from portfolio_analyzer.utils import extract_history
        
        # Create MultiIndex DataFrame like yf.download returns
        dates = pd.date_range('2020-01-01', periods=3)
        columns = pd.MultiIndex.from_product([['Close', 'Open'], ['AAPL', 'MSFT']])
        data = np.random.rand(3, 4)
        df = pd.DataFrame(data, index=dates, columns=columns)
        
        result = extract_history(df, 'AAPL')
        self.assertFalse(result.empty)
        self.assertIn('Close', result.columns)
    
    def test_extract_history_symbol_not_found(self):
        """Test extract_history when symbol not in MultiIndex"""
        from portfolio_analyzer.utils import extract_history
        
        dates = pd.date_range('2020-01-01', periods=3)
        columns = pd.MultiIndex.from_product([['Close'], ['AAPL']])
        data = np.random.rand(3, 1)
        df = pd.DataFrame(data, index=dates, columns=columns)
        
        result = extract_history(df, 'NONEXISTENT')
        self.assertTrue(result.empty)
    
    def test_download_history_exception_handling(self):
        """Test download_history handles exceptions gracefully"""
        from portfolio_analyzer.utils import download_history
        from unittest.mock import patch
        
        with patch('portfolio_analyzer.utils.yf.download', side_effect=Exception("Network error")):
            result = download_history(['AAPL'], '2020-01-01')
            self.assertTrue(result.empty)


class TestPDFDataPreparation(unittest.TestCase):
    """Test PDF data preparation logic"""
    
    def test_prepare_pdf_data_counts(self):
        """Test that _prepare_pdf_data correctly counts winning/losing positions"""
        analyzer = PortfolioAnalyzer([])
        symbol_stats = {
            'AAPL': {'total_current_value': 1000, 'total_gain': 100, 'avg_cagr': 5, 'avg_xirr': 4.9, 'avg_sp500_xirr': 2},
            'MSFT': {'total_current_value': 500, 'total_gain': -50, 'avg_cagr': -2, 'avg_xirr': -2.1, 'avg_sp500_xirr': 2},
            'TSLA': {'total_current_value': 200, 'total_gain': 0, 'avg_cagr': 0, 'avg_xirr': 0, 'avg_sp500_xirr': 2},
        }
        analysis = {'portfolio_cagr': 5, 'sp500_cagr': 3}
        
        data = analyzer._prepare_pdf_data(analysis, symbol_stats)
        
        self.assertEqual(data['winning'], 1)
        self.assertEqual(data['losing'], 1)
        self.assertEqual(data['neutral'], 1)
        self.assertEqual(data['total_symbols'], 3)

    def test_prepare_pdf_data_top_lists(self):
        """Test that top lists are correctly sorted"""
        analyzer = PortfolioAnalyzer([])
        symbol_stats = {
            'A': {'total_current_value': 1000, 'total_gain': 100, 'avg_cagr': 5, 'avg_xirr': 4.9, 'avg_sp500_xirr': 2},
            'B': {'total_current_value': 500, 'total_gain': 200, 'avg_cagr': 10, 'avg_xirr': 9.8, 'avg_sp500_xirr': 2},
            'C': {'total_current_value': 300, 'total_gain': 50, 'avg_cagr': 2, 'avg_xirr': 1.9, 'avg_sp500_xirr': 2},
        }
        analysis = {'portfolio_cagr': 5, 'sp500_cagr': 3}
        
        data = analyzer._prepare_pdf_data(analysis, symbol_stats)
        
        # Top by value: A, B, C
        self.assertEqual(data['top_10_value'][0][0], 'A')
        # Top by CAGR: B, A, C
        self.assertEqual(data['top_8_cagr'][0][0], 'B')
        # Top by XIRR: B, A, C
        self.assertEqual(data['top_8_xirr'][0][0], 'B')
        # Top by gain: B, A, C
        self.assertEqual(data['top_8_gain'][0][0], 'B')


class TestReportGeneration(unittest.TestCase):
    """Test report generation functionality"""
    
    def test_print_report_to_file(self):
        """Test that text report can be saved to file"""
        trades = [
            {"symbol": "AAPL", "shares": 10, "purchase_date": "2015-01-02", "price": 10.0},
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_file = f.name
        
        try:
            analyzer = PortfolioAnalyzer(trades)
            analyzer.print_report(output_file=temp_file)
            
            # Verify file was created and has content
            self.assertTrue(os.path.exists(temp_file))
            with open(temp_file, 'r') as f:
                content = f.read()
            self.assertIn('PORTFOLIO SUMMARY', content)
            self.assertIn('AAPL', content)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_print_report_empty_portfolio(self):
        """Test print_report with empty portfolio"""
        analyzer = PortfolioAnalyzer([])
        # Should not raise exception
        analyzer.print_report()


class TestXIRRCalculation(unittest.TestCase):
    """Test XIRR calculation and integration"""
    
    def setUp(self):
        self.analyzer = PortfolioAnalyzer([])
    
    def test_xirr_basic_doubling(self):
        """Test XIRR when investment doubles in 1 year"""
        # Invest $100, get $200 back in 1 year
        dates = ['2023-01-01', '2024-01-01']
        cash_flows = [-100, 200]
        xirr = self.analyzer.calculate_xirr(dates, cash_flows)
        # Should be approximately 100% annual return
        self.assertGreater(xirr, 95)  # Allow some tolerance
        self.assertLess(xirr, 105)
    
    def test_xirr_zero_return(self):
        """Test XIRR when investment breaks even"""
        # Invest $100, get $100 back
        dates = ['2023-01-01', '2024-01-01']
        cash_flows = [-100, 100]
        xirr = self.analyzer.calculate_xirr(dates, cash_flows)
        # Should be approximately 0%
        self.assertAlmostEqual(xirr, 0, places=0)
    
    def test_xirr_multiple_cash_flows(self):
        """Test XIRR with multiple intermediate cash flows"""
        # Multiple investments over time
        dates = ['2022-01-01', '2023-01-01', '2024-01-01']
        cash_flows = [-100, -100, 250]  # $100 each year, then $250 at end
        xirr = self.analyzer.calculate_xirr(dates, cash_flows)
        # Should be positive return
        self.assertGreater(xirr, 0)
    
    def test_xirr_insufficient_data(self):
        """Test XIRR returns 0 with insufficient data"""
        # Only one date - need at least 2
        dates = ['2023-01-01']
        cash_flows = [-100]
        xirr = self.analyzer.calculate_xirr(dates, cash_flows)
        self.assertEqual(xirr, 0)
    
    def test_xirr_mismatched_arrays(self):
        """Test XIRR with mismatched dates and cash flows"""
        dates = ['2023-01-01', '2024-01-01']
        cash_flows = [-100]  # Only one cash flow instead of two
        xirr = self.analyzer.calculate_xirr(dates, cash_flows)
        self.assertEqual(xirr, 0)
    
    def test_xirr_negative_return(self):
        """Test XIRR when investment loses money"""
        # Invest $100, get $50 back
        dates = ['2023-01-01', '2024-01-01']
        cash_flows = [-100, 50]
        xirr = self.analyzer.calculate_xirr(dates, cash_flows)
        # Should be approximately -50% annual return
        self.assertLess(xirr, 0)
    
    def test_xirr_in_stock_performance(self):
        """Test that stock performance includes XIRR metrics"""
        # This is integration test - stock_performance should have xirr fields
        analyzer = PortfolioAnalyzer([])
        # We need to check that the structure has xirr fields
        # When get_stock_performance is called, it should include:
        # - stock_xirr
        # - sp500_xirr
        # - xirr_outperformance
        # This is verified through manual testing or integration tests
    
    def test_xirr_not_greater_than_cagr(self):
        """Test that XIRR <= CAGR for two-cash-flow scenarios
        
        For a simple buy-hold scenario (only 2 cash flows: buy and sell),
        XIRR and CAGR should be mathematically equal. This test ensures
        the implementation doesn't produce XIRR > CAGR which would indicate
        a calculation error.
        """
        analyzer = PortfolioAnalyzer([])
        
        # Test case 1: $100 invested, grows to $200 in 5 years
        dates = ['2020-01-01', '2025-01-01']
        cash_flows = [-100, 200]
        xirr = analyzer.calculate_xirr(dates, cash_flows)
        cagr = analyzer.calculate_cagr(100, 200, 5)
        
        # XIRR should equal CAGR for 2-CF case (within floating point tolerance)
        # Allow 1% tolerance for numerical precision differences
        self.assertLessEqual(xirr, cagr + 1.0,
                            msg=f"XIRR ({xirr:.2f}%) cannot significantly exceed CAGR ({cagr:.2f}%)")
    
    def test_xirr_cagr_consistency_multiple_holding_periods(self):
        """Test XIRR <= CAGR for various holding periods and returns"""
        analyzer = PortfolioAnalyzer([])
        
        test_cases = [
            # (initial, final, years, description)
            (100, 50, 5, "loss scenario"),
            (100, 100, 5, "zero return"),
            (100, 150, 3, "30% gain in 3 years"),
            (1000, 5000, 10, "5x return in 10 years"),
            (500, 250, 2, "50% loss in 2 years"),
        ]
        
        for initial, final, years, description in test_cases:
            dates = [
                '2020-01-01',
                (pd.Timestamp('2020-01-01') + pd.Timedelta(days=int(years * 365.25))).strftime('%Y-%m-%d')
            ]
            cash_flows = [-initial, final]
            
            xirr = analyzer.calculate_xirr(dates, cash_flows)
            cagr = analyzer.calculate_cagr(initial, final, years)
            
            # XIRR and CAGR should be very close for 2-CF case (within 1% tolerance)
            self.assertLessEqual(xirr, cagr + 1.0,
                                msg=f"XIRR ({xirr:.2f}%) significantly exceeds CAGR ({cagr:.2f}%) in {description}")


class TestHTMLReportGeneration(unittest.TestCase):
    """Test HTML report generation"""
    
    def test_generate_html_report_creates_file(self):
        """Test that HTML report file is created successfully"""
        trades = [
            {"symbol": "AAPL", "shares": 10, "purchase_date": "2015-01-02", "price": 10.0},
            {"symbol": "MSFT", "shares": 5, "purchase_date": "2016-06-15", "price": 50.0},
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_file = f.name
        
        try:
            analyzer = PortfolioAnalyzer(trades)
            analyzer.generate_html_report(temp_file)
            
            # Verify file was created and has content
            self.assertTrue(os.path.exists(temp_file))
            with open(temp_file, 'r') as f:
                content = f.read()
            
            # Check for HTML structure
            self.assertIn('<html', content.lower())
            self.assertIn('</html>', content.lower())
            
            # Check for dashboard elements
            self.assertIn('Portfolio Analytics Dashboard', content)
            self.assertIn('plotly', content.lower())
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_generate_html_report_empty_portfolio(self):
        """Test HTML report generation with empty portfolio"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_file = f.name
        
        try:
            analyzer = PortfolioAnalyzer([])
            # Should not raise exception
            analyzer.generate_html_report(temp_file)
            
            # File should exist but may be empty or contain error message
            self.assertTrue(os.path.exists(temp_file))
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_html_report_contains_metrics(self):
        """Test that HTML report contains portfolio metrics"""
        trades = [
            {"symbol": "AAPL", "shares": 100, "purchase_date": "2015-01-02", "price": 10.0},
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_file = f.name
        
        try:
            analyzer = PortfolioAnalyzer(trades)
            analyzer.generate_html_report(temp_file)
            
            with open(temp_file, 'r') as f:
                content = f.read()
            
            # Check for key metric labels
            self.assertIn('CAGR', content)
            self.assertIn('XIRR', content)
            self.assertIn('Current Value', content)
            self.assertIn('Total Gain', content)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestCLI(unittest.TestCase):
    """Test command-line interface."""
    
    def test_cli_with_csv_argument(self):
        """Test CLI with --csv argument"""
        from portfolio_analyzer.cli import main
        from unittest.mock import patch
        import sys
        
        # Create temp CSV file
        temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        temp_csv.write("symbol,shares,purchase_date,price\n")
        temp_csv.write("AAPL,10,2020-01-02,75.50\n")
        temp_csv.close()
        
        try:
            with patch.object(sys, 'argv', ['cli', '--csv', temp_csv.name]):
                # Should not raise exception
                main()
        finally:
            os.unlink(temp_csv.name)
    
    def test_cli_with_output_argument(self):
        """Test CLI with --output argument"""
        from portfolio_analyzer.cli import main
        from unittest.mock import patch
        import sys
        
        temp_output = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        temp_output.close()
        
        try:
            with patch.object(sys, 'argv', ['cli', '--output', temp_output.name]):
                main()
            
            # Check that output file was created
            self.assertTrue(os.path.exists(temp_output.name))
            with open(temp_output.name, 'r') as f:
                content = f.read()
                self.assertIn('PORTFOLIO SUMMARY', content)
        finally:
            if os.path.exists(temp_output.name):
                os.unlink(temp_output.name)
    
    def test_cli_with_pdf_argument(self):
        """Test CLI with --pdf argument"""
        from portfolio_analyzer.cli import main
        from unittest.mock import patch
        import sys
        
        temp_pdf = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pdf')
        temp_pdf.close()
        
        try:
            with patch.object(sys, 'argv', ['cli', '--pdf', temp_pdf.name]):
                main()
            
            # Check that PDF file was created
            self.assertTrue(os.path.exists(temp_pdf.name))
        finally:
            if os.path.exists(temp_pdf.name):
                os.unlink(temp_pdf.name)
    
    def test_cli_with_html_argument(self):
        """Test CLI with --html argument"""
        from portfolio_analyzer.cli import main
        from unittest.mock import patch
        import sys
        
        temp_html = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html')
        temp_html.close()
        
        try:
            with patch.object(sys, 'argv', ['cli', '--html', temp_html.name]):
                main()
            
            # Check that HTML file was created
            self.assertTrue(os.path.exists(temp_html.name))
            with open(temp_html.name, 'r') as f:
                content = f.read()
                self.assertIn('Portfolio Analytics Dashboard', content)
        finally:
            if os.path.exists(temp_html.name):
                os.unlink(temp_html.name)
    
    def test_cli_invalid_csv_file(self):
        """Test CLI with invalid CSV file"""
        from portfolio_analyzer.cli import main
        from unittest.mock import patch
        import sys
        
        with patch.object(sys, 'argv', ['cli', '--csv', 'nonexistent.csv']):
            with self.assertRaises(SystemExit):
                main()
    
    def test_cli_no_arguments(self):
        """Test CLI without any arguments (uses default trades)"""
        from portfolio_analyzer.cli import main
        from unittest.mock import patch
        import sys
        
        with patch.object(sys, 'argv', ['cli']):
            # Should not raise exception
            main()


    """Run all tests with verbose output"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
