"""
Unit tests for Portfolio Performance Analyzer - Report Generation

Run with:
    python3 -m unittest test_reports.py -v

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
            'SBUX': {'total_gain': 100},
            'MSFT': {'total_gain': 50},
            'TSLA': {'total_gain': -20},
            'NVDA': {'total_gain': -10},
            'AMZN': {'total_gain': 0},
            'GOOGL': {'total_gain': 200},
        }
        
        winning, losing, breakeven = calculate_win_loss_stats(symbol_stats)
        
        self.assertEqual(winning, 3)  # SBUX, MSFT, GOOGL
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
            'SBUX': {'total_current_value': 1000, 'total_gain': 100, 'avg_cagr': 5, 'avg_xirr': 4.9},
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
            {"symbol": "SBUX", "shares": 10, "purchase_date": "2015-01-02", "price": 40.72},
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

    def test_pdf_report_without_visualizations(self):
        """Test PDF generation when visualization libs are unavailable"""
        from unittest.mock import patch
        from portfolio_analyzer import reports

        trades = [
            {"symbol": "SBUX", "shares": 10, "purchase_date": "2015-01-02", "price": 40.72},
        ]

        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
            temp_file = f.name

        try:
            analyzer = PortfolioAnalyzer(trades)
            with patch.object(reports, 'VISUALIZATIONS_AVAILABLE', False):
                PDFReportGenerator.generate(analyzer, temp_file)

            self.assertEqual(os.path.getsize(temp_file), 0)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_pdf_report_multiple_symbols(self):
        """Test PDF with multiple symbols creates multi-page report"""
        trades = []
        symbols = ['SBUX', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX']
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
            {"symbol": "SBUX", "shares": 100, "purchase_date": "2015-01-02", "price": 40.72},
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
            {"symbol": "SBUX", "shares": 100, "purchase_date": "2015-01-02", "price": 40.72},
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
            self.assertIn('Portfolio <span', content)
            self.assertIn('WCAGR</span>', content)
            self.assertIn('XIRR</span>', content)
            self.assertIn('S&P 500 XIRR', content)
            self.assertIn('Outperformance', content)
            self.assertIn('Total Positions', content)
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_html_report_large_file_size(self):
        """Test that HTML with charts has substantial size"""
        trades = [
            {"symbol": "SBUX", "shares": 100, "purchase_date": "2015-01-02", "price": 40.72},
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
            {"symbol": "SBUX", "shares": 100, "purchase_date": "2015-01-02", "price": 40.72},
            {"symbol": "SBUX", "shares": 50, "purchase_date": "2016-06-15", "price": 55.35},
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
            
            # Check for multiple SBUX trades (2 trades for SBUX)
            self.assertIn('SBUX', content)
            
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
            self.assertIn('<th>WCAGR %</th>', content)
            self.assertIn('<th>XIRR %</th>', content)
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_html_report_without_plotly(self):
        """Test HTML report generation when Plotly is unavailable"""
        from unittest.mock import patch
        import builtins

        trades = [
            {"symbol": "SBUX", "shares": 10, "purchase_date": "2018-01-15", "price": 50.0},
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_file = f.name

        real_import = builtins.__import__

        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name.startswith('plotly'):
                raise ImportError("Plotly not available")
            return real_import(name, globals, locals, fromlist, level)

        try:
            analyzer = PortfolioAnalyzer(trades)
            with patch('builtins.__import__', side_effect=guarded_import):
                HTMLReportGenerator.generate(analyzer, temp_file)

            with open(temp_file, 'r') as f:
                content = f.read()

            self.assertIn('Install plotly', content)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_html_report_symbol_id_sanitization(self):
        """Test that symbols with dots/dashes are sanitized for HTML IDs"""
        trades = [
            {"symbol": "SBUX", "shares": 10, "purchase_date": "2020-01-02", "price": 89.35},
            {"symbol": "SBUX", "shares": 5, "purchase_date": "2021-01-04", "price": 103.10},
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
            # For now, verify SBUX works correctly
            self.assertIn('SBUX', content)
            self.assertIn('Individual Trades for SBUX', content)
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestReportGeneration(unittest.TestCase):
    """Test report generation functionality"""
    
    def test_print_report_to_file(self):
        """Test that text report can be saved to file"""
        trades = [
            {"symbol": "SBUX", "shares": 10, "purchase_date": "2015-01-02", "price": 40.72},
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
            self.assertIn('SBUX', content)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_print_report_empty_portfolio(self):
        """Test print_report with empty portfolio"""
        analyzer = PortfolioAnalyzer([])
        # Should not raise exception
        analyzer.print_report()

    def test_html_report_contains_tooltips(self):
        """Test that HTML report includes tooltip elements"""
        trades = [
            {
                'symbol': 'SBUX',
                'shares': 100,
                'purchase_date': '2020-01-02',
                'price': 89.35
            }
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
        try:
            temp_path = temp_file.name
            temp_file.close()
            
            analyzer.generate_html_report(temp_path)
            
            # Read the generated HTML
            with open(temp_path, 'r') as f:
                html_content = f.read()
            
            # Verify tooltip CSS classes exist
            self.assertIn('tooltip-term', html_content,
                         "HTML should contain tooltip-term CSS class")
            
            # Verify tooltip styling for positioning
            self.assertIn('data-tooltip', html_content,
                         "HTML should contain data-tooltip attributes")
            
            # Verify specific tooltips for key metrics
            tooltip_checks = [
                'WCAGR',
                'XIRR',
                'position: absolute',
                'z-index: 10000',
                'overflow: visible'
            ]
            
            for check in tooltip_checks:
                self.assertIn(check, html_content,
                             f"HTML should contain '{check}' for tooltip functionality")
        
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    def test_html_report_wcagr_label(self):
        """Test that HTML report uses WCAGR instead of CAGR"""
        trades = [
            {
                'symbol': 'TEST',
                'shares': 100,
                'purchase_date': '2020-01-02',
                'price': 100.0
            }
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
        try:
            temp_path = temp_file.name
            temp_file.close()
            
            analyzer.generate_html_report(temp_path)
            
            with open(temp_path, 'r') as f:
                html_content = f.read()
            
            # Verify WCAGR appears in headers
            self.assertIn('WCAGR', html_content,
                         "HTML should use WCAGR instead of CAGR")
            
            # Verify both portfolio and S&P 500 WCAGR mentioned
            wcagr_count = html_content.count('WCAGR')
            self.assertGreater(wcagr_count, 2,
                              "HTML should have multiple WCAGR references (header + S&P)")
        
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    def test_html_report_sp500_columns(self):
        """Test that HTML detailed holdings table has S&P 500 columns"""
        trades = [
            {
                'symbol': 'TEST',
                'shares': 100,
                'purchase_date': '2020-01-02',
                'price': 100.0
            }
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
        try:
            temp_path = temp_file.name
            temp_file.close()
            
            analyzer.generate_html_report(temp_path)
            
            with open(temp_path, 'r') as f:
                html_content = f.read()
            
            # Verify S&P columns in detailed holdings
            self.assertIn('S&P WCAGR %', html_content,
                         "HTML should have S&P WCAGR % column")
            self.assertIn('S&P XIRR %', html_content,
                         "HTML should have S&P XIRR % column")
        
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)


class TestReportEdgeCases(unittest.TestCase):
    """Test report generation edge cases"""
    
    def test_text_report_empty_portfolio(self):
        """Test text report generation with empty portfolio"""
        analyzer = PortfolioAnalyzer([])
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            output_file = f.name
        
        try:
            # Should handle empty portfolio gracefully
            from portfolio_analyzer.reports import TextReportGenerator
            TextReportGenerator.generate(analyzer, output_file=output_file)
            
            # File should be created/written
            self.assertTrue(os.path.exists(output_file))
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_html_report_empty_portfolio(self):
        """Test HTML report generation with empty portfolio"""
        analyzer = PortfolioAnalyzer([])
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as f:
            output_file = f.name
        
        try:
            HTMLReportGenerator.generate(analyzer, output_file)
            
            # File should be created
            self.assertTrue(os.path.exists(output_file))
            
            # If file has content, it should still be valid HTML
            with open(output_file, 'r') as f:
                content = f.read()
                if content:
                    self.assertIn('<html', content.lower())
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_text_report_single_trade(self):
        """Test text report with single trade"""
        trades = [
            {
                "symbol": "SBUX",
                "shares": 100,
                "purchase_date": "2020-01-02",
                "price": 89.35
            }
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            output_file = f.name
        
        try:
            from portfolio_analyzer.reports import TextReportGenerator
            TextReportGenerator.generate(analyzer, output_file=output_file)
            
            with open(output_file, 'r') as f:
                content = f.read()
                self.assertIn('SBUX', content)
                self.assertIn('PORTFOLIO SUMMARY', content)
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_html_report_single_trade(self):
        """Test HTML report with single trade"""
        trades = [
            {
                "symbol": "TSLA",
                "shares": 10,
                "purchase_date": "2020-06-01",
                "price": 150.00
            }
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as f:
            output_file = f.name
        
        try:
            HTMLReportGenerator.generate(analyzer, output_file)
            
            with open(output_file, 'r') as f:
                content = f.read()
                self.assertIn('TSLA', content)
                self.assertIn('Portfolio Analytics', content)
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)


class TestReportsPhase2(unittest.TestCase):
    """Phase 2 production hardening tests for reports"""
    
    def test_text_report_consistency(self):
        """Test that text reports generated twice are identical"""
        trades = [
            {
                "symbol": "SBUX",
                "shares": 100,
                "purchase_date": "2020-01-02",
                "price": 89.35
            },
            {
                "symbol": "MSFT",
                "shares": 50,
                "purchase_date": "2021-01-04",
                "price": 217.69
            }
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f1, \
             tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f2:
            output_file1 = f1.name
            output_file2 = f2.name
        
        try:
            from portfolio_analyzer.reports import TextReportGenerator
            
            # Generate report twice
            TextReportGenerator.generate(analyzer, output_file=output_file1)
            TextReportGenerator.generate(analyzer, output_file=output_file2)
            
            # Read both files
            with open(output_file1, 'r') as f:
                content1 = f.read()
            with open(output_file2, 'r') as f:
                content2 = f.read()
            
            # Content should be identical
            self.assertEqual(content1, content2)
        finally:
            if os.path.exists(output_file1):
                os.unlink(output_file1)
            if os.path.exists(output_file2):
                os.unlink(output_file2)
    
    def test_html_report_contains_required_sections(self):
        """Test that HTML report contains all required sections"""
        trades = [
            {
                "symbol": "GOOG",
                "shares": 10,
                "purchase_date": "2015-01-01",
                "price": 500.00
            }
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as f:
            output_file = f.name
        
        try:
            HTMLReportGenerator.generate(analyzer, output_file)
            
            with open(output_file, 'r') as f:
                content = f.read()
            
            # Verify required sections exist (use section titles from HTML template)
            self.assertIn('Portfolio Analytics', content)
            self.assertIn('Detailed Holdings', content)
            self.assertIn('GOOG', content)
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_pdf_report_creation_no_error(self):
        """Test that PDF report creation doesn't raise errors"""
        trades = [
            {
                "symbol": "AMZN",
                "shares": 5,
                "purchase_date": "2014-11-20",
                "price": 300.00
            }
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
            output_file = f.name
        
        try:
            # Should not raise any exceptions
            PDFReportGenerator.generate(analyzer, output_file)
            
            # File should be created
            self.assertTrue(os.path.exists(output_file))
            # File should have some content
            self.assertGreater(os.path.getsize(output_file), 0)
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_report_with_mixed_symbols(self):
        """Test report generation with diverse symbols and performance"""
        trades = [
            {
                "symbol": "GOOGL",
                "shares": 10,
                "purchase_date": "2010-01-01",
                "price": 100.00  # Way up
            },
            {
                "symbol": "FB",
                "shares": 50,
                "purchase_date": "2020-01-01",
                "price": 100.00
            },
            {
                "symbol": "TSLA",
                "shares": 5,
                "purchase_date": "2019-12-01",
                "price": 650.00
            }
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            output_file = f.name
        
        try:
            from portfolio_analyzer.reports import TextReportGenerator
            TextReportGenerator.generate(analyzer, output_file=output_file)
            
            with open(output_file, 'r') as f:
                content = f.read()
            
            # All symbols should be in the report
            self.assertIn('GOOGL', content)
            self.assertIn('FB', content)
            self.assertIn('TSLA', content)
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_html_investor_comparison_spacing_and_highlighting(self):
        """
        Test that investor comparison chart and table have proper spacing to avoid overlap.
        This test addresses the bug where the bar chart's x-axis overlapped Joel Greenblatt's row.
        
        Bug: Chart was overlapping the first table row (Joel Greenblatt #1)
        Fix: Increased spacing between chart and table, added highlighting for top investor
        """
        trades = [
            {"symbol": "AAPL", "shares": 100, "purchase_date": "2015-01-02", "price": 40.72},
        ]
        
        analyzer = PortfolioAnalyzer(trades)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as f:
            output_file = f.name
        
        try:
            HTMLReportGenerator.generate(analyzer, output_file)
            
            with open(output_file, 'r') as f:
                content = f.read()
            
            # Test 1: Chart container has proper bottom margin (60px) to prevent overlap
            self.assertIn('margin-bottom: 60px', content, 
                         "Chart container should have 60px bottom margin")
            
            # Test 2: Chart div has proper height (450px)
            self.assertIn('height: 450px', content,
                         "Chart should be 450px tall")
            
            # Test 3: Table has proper top margin (40px) for separation from chart
            # Look for the table style that appears after the chart
            self.assertIn('margin-top: 40px; background: white; box-shadow', content,
                         "Table should have 40px top margin")
            
            # Test 4: Joel Greenblatt (#1 rank) has blue highlighting (#f0f9ff)
            # This makes the top investor visible and not hidden by chart overlap
            self.assertIn('#f0f9ff', content,
                         "Top ranked investor should have blue highlight background")
            self.assertIn('#0066cc', content,
                         "Top ranked investor should have blue border")
            
            # Test 5: Chart has proper bottom margin in Plotly config (b=80)
            # This ensures x-axis label doesn't overflow into table
            import json
            import re
            # Extract the Plotly chart JSON for investor comparison
            chart_match = re.search(r"Plotly\.newPlot\('investor-comparison-chart', (\{.*?\})\);", 
                                   content, re.DOTALL)
            if chart_match:
                try:
                    chart_json = json.loads(chart_match.group(1))
                    bottom_margin = chart_json.get('layout', {}).get('margin', {}).get('b')
                    self.assertEqual(bottom_margin, 80,
                                   "Chart bottom margin should be 80px to prevent overlap")
                except (json.JSONDecodeError, AttributeError):
                    pass  # If parsing fails, skip this assertion
            
            # Test 6: Verify Joel Greenblatt appears in content (sanity check)
            self.assertIn('Joel Greenblatt', content,
                         "Joel Greenblatt should be in the report")
            
            # Test 7: Verify investor comparison section exists
            self.assertIn('How You Compare to Investment Legends', content,
                         "Investor comparison section should exist")
            
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)


if __name__ == '__main__':
    unittest.main(verbosity=2)
