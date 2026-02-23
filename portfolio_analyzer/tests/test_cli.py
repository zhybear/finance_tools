"""
Unit tests for Portfolio Performance Analyzer

Run with:
    python3 -m unittest test_cli.py -v

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
    
    def test_cli_with_all_format_options(self):
        """Test CLI with all output formats at once"""
        from portfolio_analyzer.cli import main
        from unittest.mock import patch
        import sys
        
        temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        temp_csv.write("symbol,shares,purchase_date,price\n")
        temp_csv.write("SBUX,10,2020-01-02,89.35\n")
        temp_csv.close()
        
        temp_txt = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        temp_txt.close()
        
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_pdf.close()
        
        temp_html = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
        temp_html.close()
        
        try:
            with patch.object(sys, 'argv', [
                'cli',
                '--csv', temp_csv.name,
                '--output', temp_txt.name,
                '--pdf', temp_pdf.name,
                '--html', temp_html.name
            ]):
                main()
            
            # All three output files should exist
            self.assertTrue(os.path.exists(temp_txt.name), "Text report not created")
            self.assertTrue(os.path.exists(temp_pdf.name), "PDF report not created")
            self.assertTrue(os.path.exists(temp_html.name), "HTML report not created")
        finally:
            for f in [temp_csv.name, temp_txt.name, temp_pdf.name, temp_html.name]:
                if os.path.exists(f):
                    os.unlink(f)


    """Run all tests with verbose output"""
    unittest.main(argv=[''], verbosity=2, exit=False)


class TestCLIPhase2(unittest.TestCase):
    """Phase 2 production hardening tests for CLI"""
    
    def test_cli_malformed_csv_error_handling(self):
        """Test CLI graceful handling of malformed CSV"""
        csv_content = """symbol,shares,purchase_date,price
SBUX,invalid_shares,2020-01-02,89.35"""
        
        temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        temp_csv.write(csv_content)
        temp_csv.close()
        
        try:
            from portfolio_analyzer.cli import main
            from unittest.mock import patch
            import sys
            
            # Some data is valid (header), but no valid trades
            # This should either process what's valid or error gracefully
            with patch.object(sys, 'argv', ['cli', '--csv', temp_csv.name]):
                try:
                    main()
                    # If it doesn't raise, that's acceptable (graceful handling)
                except SystemExit:
                    # Exiting is also acceptable for error cases
                    pass
        finally:
            os.unlink(temp_csv.name)
    
    def test_cli_invalid_output_path_handling(self):
        """Test CLI handling of invalid output path"""
        from portfolio_analyzer.cli import main
        from unittest.mock import patch
        import sys
        
        # Use an invalid path that can't be written to
        invalid_path = "/dev/null/impossible/path/report.txt"
        
        with patch.object(sys, 'argv', ['cli', '--output', invalid_path]):
            # Should handle gracefully
            try:
                main()
            except (SystemExit, FileNotFoundError, OSError):
                # Any of these are acceptable error handling
                pass
    
    def test_cli_with_empty_csv_file(self):
        """Test CLI with empty CSV file (no data rows)"""
        csv_content = """symbol,shares,purchase_date,price
"""
        
        temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        temp_csv.write(csv_content)
        temp_csv.close()
        
        try:
            from portfolio_analyzer.cli import main
            from unittest.mock import patch
            import sys
            
            with patch.object(sys, 'argv', ['cli', '--csv', temp_csv.name]):
                with self.assertRaises(SystemExit):
                    # Should exit due to empty CSV
                    main()
        finally:
            os.unlink(temp_csv.name)
    
    def test_cli_output_formats_combination(self):
        """Test various combinations of output formats"""
        from portfolio_analyzer.cli import main
        from unittest.mock import patch
        import sys
        
        temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        temp_csv.write("symbol,shares,purchase_date,price\n")
        temp_csv.write("SBUX,10,2020-01-02,89.35\n")
        temp_csv.close()
        
        temp_txt = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        temp_txt.close()
        
        try:
            with patch.object(sys, 'argv', [
                'cli',
                '--csv', temp_csv.name,
                '--output', temp_txt.name,
            ]):
                main()
            
            # Text file should be created
            self.assertTrue(os.path.exists(temp_txt.name))
            
            # Should have content
            with open(temp_txt.name, 'r') as f:
                content = f.read()
                self.assertGreater(len(content), 0)
                self.assertIn('SBUX', content)
        finally:
            os.unlink(temp_csv.name)
            if os.path.exists(temp_txt.name):
                os.unlink(temp_txt.name)


if __name__ == '__main__':
    unittest.main(verbosity=2)
