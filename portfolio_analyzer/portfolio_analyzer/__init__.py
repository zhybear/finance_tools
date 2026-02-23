"""Portfolio Performance Analyzer - A comprehensive tool for analyzing stock portfolio performance.

This package provides:
- CAGR and XIRR calculations
- S&P 500 benchmark comparison
- Multi-format reporting (text, PDF, HTML)
- Symbol-level aggregation
"""

from .loaders import load_trades_from_csv
from .analyzer import PortfolioAnalyzer
from .metrics import calculate_cagr, calculate_xirr
from .reports import TextReportGenerator, PDFReportGenerator, HTMLReportGenerator
from .cli import main

__version__ = "1.3.2"
__author__ = "Zhuo Robert Li"
__license__ = "ISC"

__all__ = [
    'PortfolioAnalyzer',
    'load_trades_from_csv',
    'calculate_cagr',
    'calculate_xirr',
    'TextReportGenerator',
    'PDFReportGenerator',
    'HTMLReportGenerator',
    'main',
]
