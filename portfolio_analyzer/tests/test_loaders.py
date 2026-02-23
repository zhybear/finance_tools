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
    
    def test_load_empty_csv_file(self):
        """Test that empty CSV file (no data rows) raises ValueError"""
        csv_content = """symbol,shares,purchase_date,price
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            with self.assertRaises(ValueError) as context:
                load_trades_from_csv(temp_file)
            self.assertIn('empty', str(context.exception).lower())
        finally:
            os.unlink(temp_file)
    
    def test_load_csv_with_empty_rows(self):
        """Test that CSV with empty rows is handled gracefully"""
        csv_content = """symbol,shares,purchase_date,price
SBUX,100,2020-01-02,89.35

MSFT,50,2021-01-04,220.00
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            trades = load_trades_from_csv(temp_file)
            self.assertEqual(len(trades), 2)
            symbols = [t['symbol'] for t in trades]
            self.assertIn('SBUX', symbols)
            self.assertIn('MSFT', symbols)
        finally:
            os.unlink(temp_file)
    
    def test_load_csv_with_whitespace_normalization(self):
        """Test that whitespace in symbols is stripped and normalized"""
        csv_content = """symbol,shares,purchase_date,price
 sbux ,100,2020-01-02,89.35
MSFT  ,50,2021-01-04,220.00"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            trades = load_trades_from_csv(temp_file)
            self.assertEqual(len(trades), 2)
            self.assertEqual(trades[0]['symbol'], 'SBUX')
            self.assertEqual(trades[1]['symbol'], 'MSFT')
        finally:
            os.unlink(temp_file)
    
    def test_load_csv_with_negative_shares(self):
        """Test that negative shares are loaded (validation at analyzer level)"""
        csv_content = """symbol,shares,purchase_date,price
SBUX,-100,2020-01-02,89.35"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            trades = load_trades_from_csv(temp_file)
            self.assertEqual(len(trades), 1)
            self.assertEqual(trades[0]['shares'], -100)  # Loader accepts it; analyzer validates
        finally:
            os.unlink(temp_file)
    
    def test_load_csv_with_zero_price(self):
        """Test that zero price is loaded (validation at analyzer level)"""
        csv_content = """symbol,shares,purchase_date,price
SBUX,100,2020-01-02,0.0"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            trades = load_trades_from_csv(temp_file)
            self.assertEqual(len(trades), 1)
            self.assertEqual(trades[0]['price'], 0.0)
        finally:
            os.unlink(temp_file)
    
    def test_load_csv_with_future_date(self):
        """Test that future purchase dates are loaded (validation at analyzer level)"""
        future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        csv_content = f"""symbol,shares,purchase_date,price
SBUX,100,{future_date},89.35"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            trades = load_trades_from_csv(temp_file)
            self.assertEqual(len(trades), 1)
            self.assertEqual(trades[0]['purchase_date'], future_date)
        finally:
            os.unlink(temp_file)
    
    def test_load_csv_with_very_old_date(self):
        """Test that very old dates (before market opening) are loaded"""
        csv_content = """symbol,shares,purchase_date,price
IBM,100,1920-01-15,100.00"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            trades = load_trades_from_csv(temp_file)
            self.assertEqual(len(trades), 1)
            self.assertEqual(trades[0]['purchase_date'], '1920-01-15')
        finally:
            os.unlink(temp_file)


class TestLoadersPhase2(unittest.TestCase):
    """Phase 2 production hardening tests for loaders"""
    
    def test_date_parsing_multiple_formats(self):
        """Test that different date formats are parsed correctly"""
        # Test YYYY-MM-DD format (standard)
        csv_content = """symbol,shares,purchase_date,price
SBUX,100,2020-01-02,89.35"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            trades = load_trades_from_csv(temp_file)
            self.assertEqual(trades[0]['purchase_date'], '2020-01-02')
            # Should be normalized to YYYY-MM-DD
            self.assertEqual(len(trades[0]['purchase_date']), 10)
        finally:
            os.unlink(temp_file)
    
    def test_unicode_symbol_names(self):
        """Test that symbols with special characters are handled"""
        csv_content = """symbol,shares,purchase_date,price
BRK.B,10,2020-01-02,179.50
BRK.A,5,2020-01-02,279.50"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            trades = load_trades_from_csv(temp_file)
            self.assertEqual(len(trades), 2)
            # Verify symbols are properly normalized
            symbols = [t['symbol'] for t in trades]
            self.assertIn('BRK.B', symbols)
            self.assertIn('BRK.A', symbols)
        finally:
            os.unlink(temp_file)
    
    def test_csv_with_extra_columns(self):
        """Test that CSV with extra columns is handled gracefully"""
        csv_content = """symbol,shares,purchase_date,price,notes,exchange
SBUX,100,2020-01-02,89.35,good deal,NASDAQ
MSFT,50,2021-01-04,220.00,excellent,NASDAQ"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            trades = load_trades_from_csv(temp_file)
            # Should load successfully, ignoring extra columns
            self.assertEqual(len(trades), 2)
            self.assertEqual(trades[0]['symbol'], 'SBUX')
            self.assertEqual(trades[1]['symbol'], 'MSFT')
        finally:
            os.unlink(temp_file)
    
    def test_csv_with_decimal_shares(self):
        """Test that fractional shares are handled correctly"""
        csv_content = """symbol,shares,purchase_date,price
SBUX,100.5,2020-01-02,89.35
MSFT,50.25,2021-01-04,220.00"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            trades = load_trades_from_csv(temp_file)
            self.assertEqual(len(trades), 2)
            self.assertAlmostEqual(trades[0]['shares'], 100.5)
            self.assertAlmostEqual(trades[1]['shares'], 50.25)
        finally:
            os.unlink(temp_file)
    
    def test_csv_with_very_high_prices(self):
        """Test loading stocks with very high prices (like BRK.A)"""
        csv_content = """symbol,shares,purchase_date,price
BRK.A,1,2020-01-02,350000.00
TSLA,100,2020-01-02,800.00"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            trades = load_trades_from_csv(temp_file)
            self.assertEqual(len(trades), 2)
            self.assertEqual(trades[0]['price'], 350000.00)
            self.assertEqual(trades[1]['price'], 800.00)
        finally:
            os.unlink(temp_file)
    
    def test_csv_with_very_low_prices(self):
        """Test loading penny stocks with very low prices"""
        csv_content = """symbol,shares,purchase_date,price
PENNY,10000,2020-01-02,0.01
MICRO,5000,2020-01-02,0.0001"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            trades = load_trades_from_csv(temp_file)
            self.assertEqual(len(trades), 2)
            self.assertEqual(trades[0]['price'], 0.01)
            self.assertEqual(trades[1]['price'], 0.0001)
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main(verbosity=2)
