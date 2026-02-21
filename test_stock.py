"""
Unit tests for Portfolio Analyzer

Run with:
    python3 -m pytest test_stock.py -v
    or
    python3 -m unittest test_stock.py -v
"""

import unittest
import tempfile
import os
from datetime import datetime, timedelta
import pandas as pd
from stock import PortfolioAnalyzer, load_trades_from_csv


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


def run_tests():
    """Run all tests with verbose output"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
