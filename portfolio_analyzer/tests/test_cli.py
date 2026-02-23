"""
Unit tests for Portfolio Performance Analyzer

Run with:
    python3 -m unittest test_cli.py -v

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
        temp_csv.write("SBUX,10,2020-01-02,89.35\n")
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
    unittest.main(verbosity=2)
