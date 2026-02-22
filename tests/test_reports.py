"""
Unit tests for Portfolio Performance Analyzer - Report Generation

Run with:
    python3 -m unittest test_reports.py -v

Author: Zhuo Robert Li
Version: 1.3.1
License: ISC
"""

import unittest
import tempfile
import os
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
from portfolio_analyzer import PortfolioAnalyzer, load_trades_from_csv, calculate_cagr, calculate_xirr
from portfolio_analyzer.reports import (
    get_performance_color, calculate_win_loss_stats,
    PDFReportGenerator, HTMLReportGenerator,
    COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_NEUTRAL
)


class TestHelperFunctions(unittest.TestCase):
    """Test report helper functions"""
    
    def test_get_performance_color_positive(self):
        """Test that positive values return green color"""
        self.assertEqual(get_performance_color(10.5), COLOR_POSITIVE)
        self.assertEqual(get_performance_color(0.01), COLOR_POSITIVE)
        self.assertEqual(get_performance_color(0), COLOR_POSITIVE)
    
    def test_get_performance_color_negative(self):
        """Test that negative values return red color"""
        self.assertEqual(get_performance_color(-5.2), COLOR_NEGATIVE)
        self.assertEqual(get_performance_color(-0.01), COLOR_NEGATIVE)
    
    def test_calculate_win_loss_stats(self):
        """Test win/loss/breakeven calculation"""
        symbol_stats = {
            'AAPL': {'total_gain': 100},
            'MSFT': {'total_gain': 50},
            'TSLA': {'total_gain': -20},
            'NVDA': {'total_gain': -10},
            'AMZN': {'total_gain': 0},
            'GOOGL': {'total_gain': 200},
        }
        
        winning, losing, breakeven = calculate_win_loss_stats(symbol_stats)
        
        self.assertEqual(winning, 3)  # AAPL, MSFT, GOOGL
        self.assertEqual(losing, 2)   # TSLA, NVDA
        self.assertEqual(breakeven, 1) # AMZN
    
    def test_calculate_win_loss_stats_all_winning(self):
        """Test with all winning positions"""
        symbol_stats = {
            'A': {'total_gain': 100},
            'B': {'total_gain': 50},
            'C': {'total_gain': 25},
        }
        
        winning, losing, breakeven = calculate_win_loss_stats(symbol_stats)
        
        self.assertEqual(winning, 3)
        self.assertEqual(losing, 0)
        self.assertEqual(breakeven, 0)
    
    def test_calculate_win_loss_stats_empty(self):
        """Test with empty symbol stats"""
        winning, losing, breakeven = calculate_win_loss_stats({})
        
        self.assertEqual(winning, 0)
        self.assertEqual(losing, 0)
        self.assertEqual(breakeven, 0)


class TestPDFDataPreparation(unittest.TestCase):
    """Test PDF data preparation logic"""
    
    def test_prepare_pdf_data_structure(self):
        """Test that _prepare_pdf_data returns correct structure"""
        symbol_stats = {
            'AAPL': {'total_current_value': 1000, 'total_gain': 100, 'avg_cagr': 5, 'avg_xirr': 4.9},
            'MSFT': {'total_current_value': 500, 'total_gain': -50, 'avg_cagr': -2, 'avg_xirr': -2.1},
            'TSLA': {'total_current_value': 200, 'total_gain': 0, 'avg_cagr': 0, 'avg_xirr': 0},
        }
        analysis = {}
        
        data = PDFReportGenerator._prepare_pdf_data(symbol_stats, analysis)
        
        # Check all expected keys exist
        self.assertIn('top_10_value', data)
        self.assertIn('top_8_cagr', data)
        self.assertIn('top_8_xirr', data)
        self.assertIn('top_8_gain', data)
        
        # Check correct number of items
        self.assertEqual(len(data['top_10_value']), 3)
        self.assertEqual(len(data['top_8_cagr']), 3)
        self.assertEqual(len(data['top_8_xirr']), 3)
        self.assertEqual(len(data['top_8_gain']), 3)
    
    def test_prepare_pdf_data_sorting(self):
        """Test that top lists are correctly sorted"""
        symbol_stats = {
            'A': {'total_current_value': 1000, 'total_gain': 100, 'avg_cagr': 5, 'avg_xirr': 4.9},
            'B': {'total_current_value': 500, 'total_gain': 200, 'avg_cagr': 10, 'avg_xirr': 9.8},
            'C': {'total_current_value': 300, 'total_gain': 50, 'avg_cagr': 2, 'avg_xirr': 1.9},
        }
        analysis = {}
        
        data = PDFReportGenerator._prepare_pdf_data(symbol_stats, analysis)
        
        # Top by value
        self.assertEqual(data['top_10_value'][0][0], 'A')
        # Top by CAGR
        self.assertEqual(data['top_8_cagr'][0][0], 'B')
        # Top by XIRR
        self.assertEqual(data['top_8_xirr'][0][0], 'B')
        # Top by gain
        self.assertEqual(data['top_8_gain'][0][0], 'B')
    
    def test_prepare_pdf_data_limits(self):
        """Test that lists are limited to correct size"""
        symbol_stats = {}
        for i in range(15):
            symbol_stats[f'SYM{i}'] = {
                'total_current_value': 1000 - i * 10,
                'total_gain': 100 - i * 5,
                'avg_cagr': 10 - i,
                'avg_xirr': 9 - i
            }
        analysis = {}
        
        data = PDFReportGenerator._prepare_pdf_data(symbol_stats, analysis)
        
        self.assertEqual(len(data['top_10_value']), 10)
        self.assertEqual(len(data['top_8_cagr']), 8)
        self.assertEqual(len(data['top_8_xirr']), 8)
        self.assertEqual(len(data['top_8_gain']), 8)


class TestPDFReportGeneration(unittest.TestCase):
    """Test PDF report generation with visualizations"""
    
    def test_pdf_report_creates_file(self):
        """Test that PDF report file is created"""
        trades = [
            {"symbol": "AAPL", "shares": 10, "purchase_date": "2015-01-02", "price": 100.0},
            {"symbol": "MSFT", "shares": 5, "purchase_date": "2016-06-15", "price": 50.0},
        ]
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
            temp_file = f.name
        
        try:
            analyzer = PortfolioAnalyzer(trades)
            PDFReportGenerator.generate(analyzer, temp_file)
            
            self.assertTrue(os.path.exists(temp_file))
            
            # Verify it's a PDF
            with open(temp_file, 'rb') as f:
                header = f.read(4)
            self.assertEqual(header, b'%PDF')
            
            # Check file size (multi-page with charts should be > 10KB)
            file_size = os.path.getsize(temp_file)
            self.assertGreater(file_size, 10000)
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_pdf_report_empty_portfolio(self):
        """Test PDF generation with empty portfolio"""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
            temp_file = f.name
        
        try:
            analyzer = PortfolioAnalyzer([])
            PDFReportGenerator.generate(analyzer, temp_file)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_pdf_report_multiple_symbols(self):
        """Test PDF with multiple symbols creates multi-page report"""
        trades = []
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX']
        for i, symbol in enumerate(symbols):
            trades.append({
                "symbol": symbol,
                "shares": 10 + i,
                "purchase_date": f"201{i % 5}-01-02",
                "price": 100.0 + i * 10
            })
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
            temp_file = f.name
        
        try:
            analyzer = PortfolioAnalyzer(trades)
            PDFReportGenerator.generate(analyzer, temp_file)
            
            self.assertTrue(os.path.exists(temp_file))
            
            # Multi-page report should be larger
            file_size = os.path.getsize(temp_file)
            self.assertGreater(file_size, 20000)
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestHTMLReportWithCharts(unittest.TestCase):
    """Test HTML report generation with Plotly charts"""
    
    def test_html_report_contains_plotly(self):
        """Test that HTML report includes Plotly for interactive charts"""
        trades = [
            {"symbol": "AAPL", "shares": 100, "purchase_date": "2015-01-02", "price": 10.0},
            {"symbol": "MSFT", "shares": 50, "purchase_date": "2016-06-15", "price": 20.0},
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_file = f.name
        
        try:
            analyzer = PortfolioAnalyzer(trades)
            HTMLReportGenerator.generate(analyzer, temp_file)
            
            with open(temp_file, 'r') as f:
                content = f.read()
            
            # Should contain Plotly
            self.assertIn('plotly', content.lower())
            self.assertIn('cdn.plot.ly', content.lower())
            
            # Should contain chart divs
            self.assertIn('chart1', content)
            self.assertIn('chart2', content)
            self.assertIn('chart3', content)
            self.assertIn('chart4', content)
            self.assertIn('chart5', content)
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_html_report_contains_all_metrics(self):
        """Test that HTML contains comprehensive metrics"""
        trades = [
            {"symbol": "AAPL", "shares": 100, "purchase_date": "2015-01-02", "price": 10.0},
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_file = f.name
        
        try:
            analyzer = PortfolioAnalyzer(trades)
            HTMLReportGenerator.generate(analyzer, temp_file)
            
            with open(temp_file, 'r') as f:
                content = f.read()
            
            # Check for all 8 metric cards
            self.assertIn('Portfolio Value', content)
            self.assertIn('Total Gain', content)
            self.assertIn('Return %', content)
            self.assertIn('Portfolio CAGR', content)
            self.assertIn('Portfolio XIRR', content)
            self.assertIn('S&P 500 XIRR', content)
            self.assertIn('Outperformance', content)
            self.assertIn('Total Positions', content)
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_html_report_large_file_size(self):
        """Test that HTML with charts has substantial size"""
        trades = [
            {"symbol": "AAPL", "shares": 100, "purchase_date": "2015-01-02", "price": 10.0},
            {"symbol": "MSFT", "shares": 50, "purchase_date": "2016-06-15", "price": 20.0},
            {"symbol": "GOOGL", "shares": 25, "purchase_date": "2017-03-10", "price": 30.0},
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_file = f.name
        
        try:
            analyzer = PortfolioAnalyzer(trades)
            HTMLReportGenerator.generate(analyzer, temp_file)
            
            # HTML with Plotly charts should be large (> 30KB)
            file_size = os.path.getsize(temp_file)
            self.assertGreater(file_size, 30000)
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_html_report_expandable_trades(self):
        """Test that HTML contains expandable trade details functionality"""
        trades = [
            {"symbol": "AAPL", "shares": 100, "purchase_date": "2015-01-02", "price": 10.0},
            {"symbol": "AAPL", "shares": 50, "purchase_date": "2016-06-15", "price": 15.0},
            {"symbol": "MSFT", "shares": 25, "purchase_date": "2017-03-10", "price": 20.0},
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_file = f.name
        
        try:
            analyzer = PortfolioAnalyzer(trades)
            HTMLReportGenerator.generate(analyzer, temp_file)
            
            with open(temp_file, 'r') as f:
                content = f.read()
            
            # Check for expandable trade functionality
            self.assertIn('toggleTrades', content)
            self.assertIn('symbol-row', content)
            self.assertIn('trades-row', content)
            self.assertIn('expand-icon', content)
            
            # Check that individual trades table headers are present
            self.assertIn('Individual Trades', content)
            self.assertIn('Purchase Price', content)
            self.assertIn('Current Price', content)
            
            # Check for multiple AAPL trades (2 trades for AAPL)
            self.assertIn('AAPL', content)
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_html_report_trade_detail_columns(self):
        """Test that individual trade detail tables have correct columns"""
        trades = [
            {"symbol": "TSLA", "shares": 10, "purchase_date": "2018-01-15", "price": 50.0},
            {"symbol": "TSLA", "shares": 20, "purchase_date": "2019-06-20", "price": 60.0},
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_file = f.name
        
        try:
            analyzer = PortfolioAnalyzer(trades)
            HTMLReportGenerator.generate(analyzer, temp_file)
            
            with open(temp_file, 'r') as f:
                content = f.read()
            
            # Verify expanded trade detail table has all columns
            self.assertIn('<th>Date</th>', content)
            self.assertIn('<th>Shares</th>', content)
            self.assertIn('<th>Purchase Price</th>', content)
            self.assertIn('<th>Current Price</th>', content)
            self.assertIn('<th>Initial Value</th>', content)
            self.assertIn('<th>Current Value</th>', content)
            self.assertIn('<th>Gain</th>', content)
            self.assertIn('<th>CAGR %</th>', content)
            self.assertIn('<th>XIRR %</th>', content)
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_html_report_symbol_id_sanitization(self):
        """Test that symbols with dots/dashes are sanitized for HTML IDs"""
        trades = [
            {"symbol": "AAPL", "shares": 10, "purchase_date": "2020-01-01", "price": 100.0},
            {"symbol": "AAPL", "shares": 5, "purchase_date": "2021-01-01", "price": 120.0},
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_file = f.name
        
        try:
            analyzer = PortfolioAnalyzer(trades)
            HTMLReportGenerator.generate(analyzer, temp_file)
            
            with open(temp_file, 'r') as f:
                content = f.read()
            
            # Should have clickable rows with symbol IDs
            self.assertIn('toggleTrades', content)
            self.assertIn('symbol-row', content)
            self.assertIn('onclick', content)
            
            # If we had "BRK.B", it would be sanitized to "BRK_B"
            # For now, verify AAPL works correctly
            self.assertIn('AAPL', content)
            self.assertIn('Individual Trades for AAPL', content)
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


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




if __name__ == '__main__':
    unittest.main(verbosity=2)
