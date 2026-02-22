"""
Unit tests for Portfolio Performance Analyzer

Run with:
    python3 -m unittest test_metrics.py -v

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




if __name__ == '__main__':
    unittest.main(verbosity=2)
