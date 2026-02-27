"""
Unit tests for HTML report sortable table functionality

Run with:
    python3 -m unittest test_html_sorting.py -v

Author: Zhuo Robert Li
Version: 1.3.6
License: ISC
"""

import unittest
import tempfile
import os
from datetime import datetime, timedelta
from portfolio_analyzer import PortfolioAnalyzer
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class TestHTMLSortableTable(unittest.TestCase):
    """Test sortable table functionality in HTML reports"""
    
    def setUp(self):
        """Create test portfolio with multiple symbols for sorting tests"""
        self.trades = [
            {
                'symbol': 'AAPL',
                'shares': 10,
                'purchase_date': '2020-01-02',
                'price': 300.0
            },
            {
                'symbol': 'MSFT',
                'shares': 20,
                'purchase_date': '2020-01-02',
                'price': 160.0
            },
            {
                'symbol': 'GOOGL',
                'shares': 5,
                'purchase_date': '2020-01-02',
                'price': 1400.0
            },
            {
                'symbol': 'TSLA',
                'shares': 15,
                'purchase_date': '2020-01-02',
                'price': 88.0
            },
            {
                'symbol': 'NVDA',
                'shares': 25,
                'purchase_date': '2020-01-02',
                'price': 60.0
            },
        ]
        self.analyzer = PortfolioAnalyzer(self.trades)
    
    def test_html_table_has_sortable_headers(self):
        """Test that table headers have sortable class and data-sort attributes"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            html_path = f.name
        
        try:
            self.analyzer.generate_html_report(html_path)
            
            with open(html_path, 'r') as f:
                html_content = f.read()
            
            # Check for sortable class on headers
            self.assertIn('class="sortable"', html_content)
            
            # Check for data-sort attributes for each column
            self.assertIn('data-sort="symbol"', html_content)
            self.assertIn('data-sort="trades"', html_content)
            self.assertIn('data-sort="invested"', html_content)
            self.assertIn('data-sort="current_value"', html_content)
            self.assertIn('data-sort="gain"', html_content)
            self.assertIn('data-sort="return_pct"', html_content)
            self.assertIn('data-sort="wcagr"', html_content)
            self.assertIn('data-sort="xirr"', html_content)
            self.assertIn('data-sort="sp500_wcagr"', html_content)
            self.assertIn('data-sort="sp500_xirr"', html_content)
            
            # Check for onclick handlers
            self.assertIn('onclick="sortTable(', html_content)
            
        finally:
            if os.path.exists(html_path):
                os.unlink(html_path)
    
    def test_html_rows_have_data_attributes(self):
        """Test that symbol rows have data attributes for all sortable columns"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            html_path = f.name
        
        try:
            self.analyzer.generate_html_report(html_path)
            
            with open(html_path, 'r') as f:
                html_content = f.read()
            
            # Check that symbol rows have data attributes
            self.assertIn('data-symbol=', html_content)
            self.assertIn('data-trades=', html_content)
            self.assertIn('data-invested=', html_content)
            self.assertIn('data-current-value=', html_content)
            self.assertIn('data-gain=', html_content)
            self.assertIn('data-return-pct=', html_content)
            self.assertIn('data-wcagr=', html_content)
            self.assertIn('data-xirr=', html_content)
            self.assertIn('data-sp500-wcagr=', html_content)
            self.assertIn('data-sp500-xirr=', html_content)
            
        finally:
            if os.path.exists(html_path):
                os.unlink(html_path)
    
    def test_javascript_sort_function_exists(self):
        """Test that sortTable JavaScript function is present"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            html_path = f.name
        
        try:
            self.analyzer.generate_html_report(html_path)
            
            with open(html_path, 'r') as f:
                html_content = f.read()
            
            # Check for sortTable function definition
            self.assertIn('function sortTable(column)', html_content)
            
            # Check for key sorting logic
            self.assertIn('currentSort', html_content)
            self.assertIn('getAttribute(\'data-\'', html_content)
            self.assertIn('sort-arrow', html_content)
            
            # Check for NaN handling
            self.assertIn('isNaN', html_content)
            
            # Check for tie-breaker logic (symbol sorting)
            self.assertIn('data-symbol', html_content)
            
        finally:
            if os.path.exists(html_path):
                os.unlink(html_path)
    
    def test_css_styles_for_sorting(self):
        """Test that CSS styles for sortable elements exist"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            html_path = f.name
        
        try:
            self.analyzer.generate_html_report(html_path)
            
            with open(html_path, 'r') as f:
                html_content = f.read()
            
            # Check for sortable styles
            self.assertIn('th.sortable', html_content)
            self.assertIn('cursor: pointer', html_content)
            self.assertIn('.sort-arrow', html_content)
            self.assertIn('.sorted', html_content)
            
        finally:
            if os.path.exists(html_path):
                os.unlink(html_path)
    
    def test_default_sort_on_page_load(self):
        """Test that default sort is applied on page load"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            html_path = f.name
        
        try:
            self.analyzer.generate_html_report(html_path)
            
            with open(html_path, 'r') as f:
                html_content = f.read()
            
            # Check for DOMContentLoaded event listener
            self.assertIn('DOMContentLoaded', html_content)
            
            # Check that default sort is by return_pct
            self.assertIn("sortTable('return_pct')", html_content)
            
        finally:
            if os.path.exists(html_path):
                os.unlink(html_path)
    
    def test_table_has_tbody_id(self):
        """Test that tbody has an id for JavaScript manipulation"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            html_path = f.name
        
        try:
            self.analyzer.generate_html_report(html_path)
            
            with open(html_path, 'r') as f:
                html_content = f.read()
            
            # Check for tbody id
            self.assertIn('id="holdings-tbody"', html_content)
            self.assertIn('id="holdings-table"', html_content)
            
        finally:
            if os.path.exists(html_path):
                os.unlink(html_path)
    
    def test_sort_arrows_for_all_columns(self):
        """Test that sort arrow spans exist for all sortable columns"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            html_path = f.name
        
        try:
            self.analyzer.generate_html_report(html_path)
            
            with open(html_path, 'r') as f:
                html_content = f.read()
            
            # Check for arrow IDs for each column
            self.assertIn('id="arrow-symbol"', html_content)
            self.assertIn('id="arrow-trades"', html_content)
            self.assertIn('id="arrow-invested"', html_content)
            self.assertIn('id="arrow-current_value"', html_content)
            self.assertIn('id="arrow-gain"', html_content)
            self.assertIn('id="arrow-return_pct"', html_content)
            self.assertIn('id="arrow-wcagr"', html_content)
            self.assertIn('id="arrow-xirr"', html_content)
            self.assertIn('id="arrow-sp500_wcagr"', html_content)
            self.assertIn('id="arrow-sp500_xirr"', html_content)
            
        finally:
            if os.path.exists(html_path):
                os.unlink(html_path)
    
    @unittest.skipUnless(BS4_AVAILABLE, "BeautifulSoup4 not available")
    def test_html_structure_with_beautifulsoup(self):
        """Test HTML structure using BeautifulSoup for detailed validation"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            html_path = f.name
        
        try:
            self.analyzer.generate_html_report(html_path)
            
            with open(html_path, 'r') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Check table exists
            table = soup.find('table', {'id': 'holdings-table'})
            self.assertIsNotNone(table, "Holdings table not found")
            
            # Check thead has sortable headers
            thead = table.find('thead')
            self.assertIsNotNone(thead)
            
            sortable_headers = thead.find_all('th', {'class': 'sortable'})
            self.assertEqual(len(sortable_headers), 10, "Should have 10 sortable column headers")
            
            # Check each header has data-sort attribute
            for header in sortable_headers:
                self.assertIsNotNone(header.get('data-sort'), 
                                   f"Header missing data-sort attribute: {header.text}")
                self.assertIsNotNone(header.get('onclick'), 
                                   f"Header missing onclick handler: {header.text}")
            
            # Check tbody exists
            tbody = table.find('tbody', {'id': 'holdings-tbody'})
            self.assertIsNotNone(tbody, "Holdings tbody not found")
            
            # Check symbol rows have data attributes
            symbol_rows = tbody.find_all('tr', {'class': 'symbol-row'})
            self.assertGreater(len(symbol_rows), 0, "No symbol rows found")
            
            for row in symbol_rows:
                self.assertIsNotNone(row.get('data-symbol'), "Row missing data-symbol")
                self.assertIsNotNone(row.get('data-trades'), "Row missing data-trades")
                self.assertIsNotNone(row.get('data-invested'), "Row missing data-invested")
                self.assertIsNotNone(row.get('data-current-value'), "Row missing data-current-value")
                self.assertIsNotNone(row.get('data-gain'), "Row missing data-gain")
                self.assertIsNotNone(row.get('data-return-pct'), "Row missing data-return-pct")
            
        finally:
            if os.path.exists(html_path):
                os.unlink(html_path)
    
    def test_toggle_trades_still_works(self):
        """Test that toggleTrades function is still present and functional"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            html_path = f.name
        
        try:
            self.analyzer.generate_html_report(html_path)
            
            with open(html_path, 'r') as f:
                html_content = f.read()
            
            # Check toggleTrades function still exists
            self.assertIn('function toggleTrades', html_content)
            self.assertIn('trades-row', html_content)
            self.assertIn('expand-icon', html_content)
            
        finally:
            if os.path.exists(html_path):
                os.unlink(html_path)


class TestSortingEdgeCases(unittest.TestCase):
    """Test edge cases for sorting functionality"""
    
    def test_single_symbol_portfolio(self):
        """Test sorting works with single symbol"""
        trades = [{'symbol': 'AAPL', 'shares': 10, 'purchase_date': '2020-01-02', 'price': 300.0}]
        analyzer = PortfolioAnalyzer(trades)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            html_path = f.name
        
        try:
            analyzer.generate_html_report(html_path)
            
            with open(html_path, 'r') as f:
                html_content = f.read()
            
            # Should still have sorting enabled
            self.assertIn('function sortTable', html_content)
            self.assertIn('class="sortable"', html_content)
            
        finally:
            if os.path.exists(html_path):
                os.unlink(html_path)
    
    def test_multiple_trades_same_symbol(self):
        """Test that nested trades rows move with their parent symbol row"""
        trades = [
            {'symbol': 'AAPL', 'shares': 10, 'purchase_date': '2020-01-02', 'price': 300.0},
            {'symbol': 'AAPL', 'shares': 5, 'purchase_date': '2021-01-02', 'price': 350.0},
            {'symbol': 'MSFT', 'shares': 20, 'purchase_date': '2020-01-02', 'price': 160.0},
        ]
        analyzer = PortfolioAnalyzer(trades)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            html_path = f.name
        
        try:
            analyzer.generate_html_report(html_path)
            
            with open(html_path, 'r') as f:
                html_content = f.read()
            
            # Check that sorting logic preserves trades rows
            self.assertIn('const tradesRowId', html_content)
            self.assertIn('tbody.appendChild(symbolRow)', html_content)
            self.assertIn('tbody.appendChild(tradesRow)', html_content)
            
        finally:
            if os.path.exists(html_path):
                os.unlink(html_path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
