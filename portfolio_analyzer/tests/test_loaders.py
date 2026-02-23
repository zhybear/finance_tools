"""
Unit tests for Portfolio Performance Analyzer

Run with:
    python3 -m unittest test_loaders.py -v

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

class TestCSVLoading(unittest.TestCase):
    """Test CSV file loading and validation"""
    
    def test_load_valid_csv(self):
        """Test loading a properly formatted CSV file"""
        csv_content = """symbol,shares,purchase_date,price
    SBUX,100,2020-01-02,89.35
    MSFT,50,2021-01-04,220.00
    NVDA,25,2019-06-15,145.75"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            trades = load_trades_from_csv(temp_file)
            self.assertEqual(len(trades), 3)
            self.assertEqual(trades[0]['symbol'], 'SBUX')
            self.assertEqual(trades[0]['shares'], 100)
            self.assertEqual(trades[0]['price'], 89.35)
            self.assertEqual(trades[0]['purchase_date'], '2020-01-02')
        finally:
            os.unlink(temp_file)
    
    def test_load_csv_missing_columns(self):
        """Test that CSV with missing columns raises ValueError"""
        csv_content = """symbol,shares,purchase_date
    SBUX,100,2020-01-02"""
        
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
    SBUX,100,2020-01-02,89.35
    MSFT,invalid,2021-01-04,220.00
    NVDA,25,not-a-date,145.75
    TSLA,-50,2020-05-01,100.00"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            trades = load_trades_from_csv(temp_file)
            # SBUX is valid, TSLA has negative shares but will load (validation happens later)
            # Only rows with truly invalid data types are filtered by CSV loader
            # MSFT (invalid shares parsed as NaN) and NVDA (invalid date) are dropped
            self.assertGreater(len(trades), 0)
            # Verify SBUX is in the results
            symbols = [t['symbol'] for t in trades]
            self.assertIn('SBUX', symbols)
            # MSFT and NVDA should be filtered out due to parse errors
            self.assertNotIn('MSFT', symbols)
            self.assertNotIn('NVDA', symbols)
        finally:
            os.unlink(temp_file)




if __name__ == '__main__':
    unittest.main(verbosity=2)
