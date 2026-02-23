#!/usr/bin/env python3
"""Verification script for new code changes"""

import unittest
import sys

# Load and run critical tests
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# Add specific test methods
from tests.test_analyzer import TestSymbolAccumulation, TestSP500Benchmark
from tests.test_reports import TestReportGeneration

# Add new tests
suite.addTest(TestSymbolAccumulation('test_sp500_cagr_calculation'))
suite.addTest(TestSymbolAccumulation('test_sp500_xirr_vs_wcagr_multi_trade'))
suite.addTest(TestSymbolAccumulation('test_symbol_stats_contains_required_fields'))
suite.addTest(TestSymbolAccumulation('test_sp500_xirr_weighted_calculation'))
suite.addTest(TestReportGeneration('test_html_report_contains_tooltips'))
suite.addTest(TestReportGeneration('test_html_report_wcagr_label'))
suite.addTest(TestReportGeneration('test_html_report_sp500_columns'))

# Add existing tests to ensure no regressions
suite.addTest(TestSP500Benchmark('test_sp500_vs_itself_single_trade'))
suite.addTest(TestSymbolAccumulation('test_symbol_accumulation_single_symbol'))
suite.addTest(TestSymbolAccumulation('test_symbol_accumulation_multiple_symbols'))
suite.addTest(TestReportGeneration('test_pdf_report_creates_file'))
suite.addTest(TestReportGeneration('test_html_report_contains_plotly'))

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

# Print summary
print(f"\n{'='*60}")
print(f"Tests run: {result.testsRun}")
print(f"Failures: {len(result.failures)}")
print(f"Errors: {len(result.errors)}")
print(f"Success: {result.wasSuccessful()}")
print(f"{'='*60}")

sys.exit(0 if result.wasSuccessful() else 1)
