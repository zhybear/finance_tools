"""
Unit tests for Portfolio Performance Analyzer

Run with:
    python3 -m unittest test_reports.py -v

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




if __name__ == '__main__':
    unittest.main(verbosity=2)
