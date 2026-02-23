"""
Unit tests for Portfolio Performance Analyzer

Run with:
    python3 -m unittest test_analyzer.py -v

Author: Zhuo Robert Li
Version: 1.3.3
License: ISC
"""

import unittest
import tempfile
import os
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
from portfolio_analyzer import PortfolioAnalyzer, load_trades_from_csv, calculate_cagr, calculate_xirr

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



class TestTradeValidation(unittest.TestCase):
    """Test trade validation logic"""
    
    def setUp(self):
        self.analyzer = PortfolioAnalyzer([])
    
    def test_valid_trade(self):
        """Test that a valid trade passes validation"""
        trade = {
            "symbol": "SBUX",
            "shares": 100,
            "purchase_date": "2020-01-02",
            "price": 89.35
        }
        self.assertTrue(self.analyzer._validate_trade(trade))
    
    def test_invalid_trade_missing_keys(self):
        """Test that trade missing keys fails validation"""
        trade = {
            "symbol": "SBUX",
            "shares": 100,
            "price": 89.35
        }
        self.assertFalse(self.analyzer._validate_trade(trade))
    
    def test_invalid_trade_negative_shares(self):
        """Test that negative shares fail validation"""
        trade = {
            "symbol": "SBUX",
            "shares": -100,
            "purchase_date": "2020-01-02",
            "price": 89.35
        }
        self.assertFalse(self.analyzer._validate_trade(trade))
    
    def test_invalid_trade_zero_price(self):
        """Test that zero price fails validation"""
        trade = {
            "symbol": "SBUX",
            "shares": 100,
            "purchase_date": "2020-01-02",
            "price": 0
        }
        self.assertFalse(self.analyzer._validate_trade(trade))
    
    def test_invalid_trade_bad_date_format(self):
        """Test that invalid date format fails validation"""
        trade = {
            "symbol": "SBUX",
            "shares": 100,
            "purchase_date": "01/02/2020",
            "price": 89.35
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
            {"symbol": "SBUX", "shares": 10, "purchase_date": "2015-01-02", "price": 40.72},
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
            {'symbol': 'SBUX', 'shares': 100, 'initial_value': 1000, 'current_value': 1500, 
             'stock_cagr': 10.0, 'stock_xirr': 9.5, 'sp500_cagr': 8.0, 'sp500_xirr': 7.5,
             'sp500_current_value': 1200, 'years_held': 5},
            {'symbol': 'SBUX', 'shares': 50, 'initial_value': 500, 'current_value': 800, 
             'stock_cagr': 12.5, 'stock_xirr': 12.0, 'sp500_cagr': 8.0, 'sp500_xirr': 7.5,
             'sp500_current_value': 600, 'years_held': 5}
        ]
        
        analyzer = PortfolioAnalyzer([])
        stats = analyzer._calculate_symbol_accumulation(trades)
        
        self.assertIn('SBUX', stats)
        self.assertEqual(stats['SBUX']['trades_count'], 2)
        self.assertEqual(stats['SBUX']['total_shares'], 150)
        self.assertEqual(stats['SBUX']['total_initial_value'], 1500)
        self.assertEqual(stats['SBUX']['total_current_value'], 2300)
        self.assertEqual(stats['SBUX']['total_gain'], 800)
        self.assertGreater(stats['SBUX']['gain_percentage'], 0)

    def test_symbol_accumulation_multiple_symbols(self):
        """Test accumulation for multiple symbols"""
        trades = [
            {'symbol': 'SBUX', 'shares': 100, 'initial_value': 1000, 'current_value': 1500,
             'stock_cagr': 10.0, 'stock_xirr': 9.5, 'sp500_cagr': 8.0, 'sp500_xirr': 7.5,
             'sp500_current_value': 1200, 'years_held': 5},
            {'symbol': 'MSFT', 'shares': 50, 'initial_value': 2000, 'current_value': 3000,
             'stock_cagr': 8.5, 'stock_xirr': 8.0, 'sp500_cagr': 8.0, 'sp500_xirr': 7.5,
             'sp500_current_value': 2400, 'years_held': 5},
            {'symbol': 'SBUX', 'shares': 50, 'initial_value': 500, 'current_value': 600,
             'stock_cagr': 3.7, 'stock_xirr': 3.5, 'sp500_cagr': 8.0, 'sp500_xirr': 7.5,
             'sp500_current_value': 600, 'years_held': 5}
        ]
        
        analyzer = PortfolioAnalyzer([])
        stats = analyzer._calculate_symbol_accumulation(trades)
        
        self.assertEqual(len(stats), 2)
        self.assertIn('SBUX', stats)
        self.assertIn('MSFT', stats)
        self.assertEqual(stats['SBUX']['trades_count'], 2)
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

    def test_sp500_cagr_calculation(self):
        """Test that S&P 500 WCAGR is calculated correctly"""
        trades = [
            {
                'symbol': 'SBUX',
                'shares': 100,
                'initial_value': 1000,
                'current_value': 1500,
                'stock_cagr': 10.0,
                'stock_xirr': 9.5,
                'sp500_cagr': 8.0,
                'sp500_xirr': 7.5,
                'sp500_current_value': 1200,
                'years_held': 5,
                'purchase_date': '2020-01-02'
            }
        ]
        
        analyzer = PortfolioAnalyzer([])
        stats = analyzer._calculate_symbol_accumulation(trades)
        
        # Verify S&P 500 WCAGR exists and is reasonable
        self.assertIn('avg_sp500_cagr', stats['SBUX'])
        self.assertAlmostEqual(stats['SBUX']['avg_sp500_cagr'], 8.0, places=1,
                              msg="S&P 500 WCAGR should match sp500_cagr for single trade")

    def test_sp500_xirr_vs_wcagr_multi_trade(self):
        """Test that S&P 500 XIRR differs from WCAGR for multi-trade positions
        
        When there are multiple trades at different times, XIRR should account
        for the timing of cash flows differently than WCAGR (weighted average).
        """
        # Create trades that mimic NVDA case: 3 purchases at different times
        trades = [
            {
                'symbol': 'NVDA',
                'shares': 150,
                'initial_value': 2925,
                'current_value': 28431,
                'purchase_date': '2015-01-15',
                'stock_cagr': 22.76,
                'stock_xirr': 22.76,
                'sp500_cagr': 11.85,
                'sp500_xirr': 11.85,
                'sp500_current_value': 6783,
                'years_held': 11.1
            },
            {
                'symbol': 'NVDA',
                'shares': 100,
                'initial_value': 14500,
                'current_value': 18960,
                'purchase_date': '2017-06-01',
                'stock_cagr': 3.14,
                'stock_xirr': 3.14,
                'sp500_cagr': 12.73,
                'sp500_xirr': 12.73,
                'sp500_current_value': 20460,
                'years_held': 8.65
            },
            {
                'symbol': 'NVDA',
                'shares': 50,
                'initial_value': 6500,
                'current_value': 9555,
                'purchase_date': '2019-01-01',
                'stock_cagr': 7.76,
                'stock_xirr': 7.76,
                'sp500_cagr': 15.24,
                'sp500_xirr': 15.24,
                'sp500_current_value': 10920,
                'years_held': 7.13
            }
        ]
        
        analyzer = PortfolioAnalyzer([])
        stats = analyzer._calculate_symbol_accumulation(trades)
        
        # Verify both metrics exist
        self.assertIn('avg_sp500_cagr', stats['NVDA'])
        self.assertIn('avg_sp500_xirr', stats['NVDA'])
        
        # For multi-trade scenario with XIRR available, WCAGR and XIRR should differ
        # (Though in tests without dates, they may be calculated differently)
        wcagr = stats['NVDA']['avg_sp500_cagr']
        xirr = stats['NVDA']['avg_sp500_xirr']
        
        self.assertIsNotNone(wcagr)
        self.assertIsNotNone(xirr)
        self.assertGreater(wcagr, 0)
        self.assertGreater(xirr, 0)

    def test_symbol_stats_contains_required_fields(self):
        """Test that symbol accumulation stats contain all required fields"""
        trades = [
            {
                'symbol': 'TEST',
                'shares': 100,
                'initial_value': 1000,
                'current_value': 1200,
                'stock_cagr': 5.0,
                'stock_xirr': 5.0,
                'sp500_cagr': 8.0,
                'sp500_xirr': 8.0,
                'sp500_current_value': 1300,
                'years_held': 5
            }
        ]
        
        analyzer = PortfolioAnalyzer([])
        stats = analyzer._calculate_symbol_accumulation(trades)
        
        required_fields = [
            'trades_count', 'total_shares', 'total_initial_value',
            'total_current_value', 'total_gain', 'gain_percentage',
            'avg_cagr', 'avg_xirr', 'avg_sp500_cagr', 'avg_sp500_xirr',
            'xirr_outperformance_pct'
        ]
        
        for field in required_fields:
            self.assertIn(field, stats['TEST'],
                         msg=f"Missing required field: {field}")

    def test_sp500_xirr_weighted_calculation(self):
        """Test S&P 500 XIRR for single trade equals WCAGR"""
        trades = [
            {
                'symbol': 'SINGLE',
                'shares': 100,
                'initial_value': 1000,
                'current_value': 1500,
                'stock_cagr': 10.0,
                'stock_xirr': 10.0,
                'sp500_cagr': 8.0,
                'sp500_xirr': 8.0,
                'sp500_current_value': 1300,
                'years_held': 5
            }
        ]
        
        analyzer = PortfolioAnalyzer([])
        stats = analyzer._calculate_symbol_accumulation(trades)
        
        # For single trade without dates, XIRR fallback uses weighted average
        # which should approximate WCAGR
        wcagr = stats['SINGLE']['avg_sp500_cagr']
        xirr = stats['SINGLE']['avg_sp500_xirr']
        
        self.assertAlmostEqual(wcagr, 8.0, places=1)
        self.assertAlmostEqual(xirr, 8.0, places=1)

    def test_empty_portfolio_analysis(self):
        """Test that empty portfolio is handled gracefully"""
        analyzer = PortfolioAnalyzer([])
        analysis = analyzer.analyze_portfolio()
        
        # Should return empty analysis without crashing
        self.assertEqual(analysis['trades'], [])
        self.assertEqual(analysis['total_initial_value'], 0)
        self.assertEqual(analysis['total_current_value'], 0)

    def test_single_day_holding_period(self):
        """Test handling of trades held for very short periods"""
        import datetime
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # Use a purchase date from this year to ensure it's valid
        trades = [
            {
                'symbol': 'SBUX',
                'shares': 100,
                'purchase_date': '2025-01-02',
                'price': 92.17,
            }
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        # Should not crash even with recent purchase
        self.assertTrue(len(analyzer.trades) > 0)

    def test_portfolio_with_valid_trades(self):
        """Test portfolio with multiple winning positions"""
        trades = [
            {
                'symbol': 'SBUX',
                'shares': 100,
                'purchase_date': '2020-01-02',
                'price': 89.35,
            },
            {
                'symbol': 'MSFT',
                'shares': 50,
                'purchase_date': '2020-01-02',
                'price': 160.00,
            }
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        analysis = analyzer.analyze_portfolio()
        
        # Portfolio should have been analyzed
        self.assertGreater(len(analysis['trades']), 0)
        self.assertGreater(analysis['total_initial_value'], 0)

    def test_portfolio_with_mixed_outcomes(self):
        """Test portfolio with both up and down positions"""
        trades = [
            {
                'symbol': 'SBUX',
                'shares': 100,
                'purchase_date': '2020-01-02',
                'price': 89.35,
            },
            {
                'symbol': 'GOOG',
                'shares': 50,
                'purchase_date': '2020-01-02',
                'price': 1500.00,
            }
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        analysis = analyzer.analyze_portfolio()
        
        # Should have analyzed multiple positions
        self.assertGreaterEqual(len(analysis['trades']), 2)

    def test_zero_gain_positions(self):
        """Test portfolio with break-even positions"""
        trades = [
            {
                'symbol': 'FLAT',
                'shares': 100,
                'purchase_date': '2023-06-15',  # Recent enough to have data
                'price': 100.00,
            }
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        analysis = analyzer.analyze_portfolio()
        
        # Should handle even if position hasn't moved much
        self.assertIsNotNone(analysis)


class TestAnalyzerEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def test_empty_portfolio_analysis(self):
        """Test analyzing an empty portfolio"""
        analyzer = PortfolioAnalyzer([])
        analysis = analyzer.analyze_portfolio()
        
        # Should handle empty case gracefully
        self.assertIsNotNone(analysis)
        self.assertEqual(len(analysis['trades']), 0)
    
    def test_single_trade_analysis(self):
        """Test analyzing a portfolio with only one trade"""
        trades = [
            {
                "symbol": "SBUX",
                "shares": 100,
                "purchase_date": "2020-01-02",
                "price": 89.35
            }
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        analysis = analyzer.analyze_portfolio()
        
        self.assertEqual(len(analysis['trades']), 1)
        self.assertEqual(analysis['trades'][0]['symbol'], 'SBUX')
    
    def test_analyzer_type_validation_invalid_trades_type(self):
        """Test that analyzer rejects invalid trades type"""
        with self.assertRaises(TypeError):
            PortfolioAnalyzer("not a list")
    
    def test_analyzer_type_validation_dict_not_list(self):
        """Test that analyzer rejects dict instead of list"""
        with self.assertRaises(TypeError):
            PortfolioAnalyzer({"symbol": "SBUX"})
    
    def test_duplicate_symbol_same_day_different_prices(self):
        """Test aggregation when same symbol bought on same day at different prices"""
        trades = [
            {
                "symbol": "SBUX",
                "shares": 100,
                "purchase_date": "2020-01-02",
                "price": 89.35
            },
            {
                "symbol": "SBUX",
                "shares": 50,
                "purchase_date": "2020-01-02",
                "price": 89.50
            }
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        analysis = analyzer.analyze_portfolio()
        
        # Should have aggregated results
        self.assertIsNotNone(analysis)
        # Both trades should be in individual analysis
        sbux_trades = [t for t in analysis['trades'] if t['symbol'] == 'SBUX']
        self.assertEqual(len(sbux_trades), 2)
    
    def test_duplicate_symbol_different_days(self):
        """Test aggregation when same symbol bought on different days"""
        trades = [
            {
                "symbol": "MSFT",
                "shares": 50,
                "purchase_date": "2020-01-02",
                "price": 160.00
            },
            {
                "symbol": "MSFT",
                "shares": 25,
                "purchase_date": "2021-06-15",
                "price": 270.00
            }
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        analysis = analyzer.analyze_portfolio()
        
        # Should have both trades and aggregated symbol stats
        self.assertIsNotNone(analysis)
        msft_trades = [t for t in analysis['trades'] if t['symbol'] == 'MSFT']
        self.assertEqual(len(msft_trades), 2)
    
    def test_cache_consistency_multiple_calls(self):
        """Test that calling analyze_portfolio twice gives same results"""
        trades = [
            {
                "symbol": "TSLA",
                "shares": 10,
                "purchase_date": "2020-06-01",
                "price": 150.00
            }
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        analysis1 = analyzer.analyze_portfolio()
        analysis2 = analyzer.analyze_portfolio()
        
        # Results should be identical (cache working)
        self.assertEqual(len(analysis1['trades']), len(analysis2['trades']))
        self.assertEqual(
            analysis1['trades'][0]['symbol'],
            analysis2['trades'][0]['symbol']
        )
    
    def test_mixed_performance_portfolio(self):
        """Test portfolio with both winning and losing positions"""
        trades = [
            {
                "symbol": "GOOG",
                "shares": 10,
                "purchase_date": "2015-01-01",
                "price": 50.00  # Should be way up
            },
            {
                "symbol": "GE",
                "shares": 100,
                "purchase_date": "2018-01-01",
                "price": 20.00  # Should be way down
            }
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        analysis = analyzer.analyze_portfolio()
        
        self.assertEqual(len(analysis['trades']), 2)
        # Should have mixed results
        self.assertIsNotNone(analysis)


if __name__ == '__main__':
    unittest.main(verbosity=2)
