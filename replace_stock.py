#!/usr/bin/env python3
"""Replace stock.py with a backward-compatibility shim."""

content = """\"\"\"Portfolio Performance Analyzer - Backward compatibility shim.

This module provides backward compatibility by re-exporting the main components
from the refactored portfolio_analyzer package.

For new code, import directly from portfolio_analyzer:
    from portfolio_analyzer import PortfolioAnalyzer, load_trades_from_csv

Author: Zhuo Robert Li
Version: 1.2.0
License: ISC
\"\"\"

# Import all public symbols from the package
from portfolio_analyzer import (
    PortfolioAnalyzer,
    load_trades_from_csv,
    calculate_cagr,
    calculate_xirr,
    TextReportGenerator,
    PDFReportGenerator,
    HTMLReportGenerator,
)

# For backward compatibility - also expose at module level
__all__ = [
    'PortfolioAnalyzer',
    'load_trades_from_csv',
    'calculate_cagr',
    'calculate_xirr',
    'TextReportGenerator',
    'PDFReportGenerator',
    'HTMLReportGenerator',
]

# CLI entry point (allows: python3 stock.py --csv trades.csv --pdf report.pdf)
if __name__ == '__main__':
    from portfolio_analyzer.cli import main
    main()
"""

with open('/Users/zhuoli/python/stock/stock.py', 'w') as f:
    f.write(content)
print("✅ stock.py replaced with backward-compatibility shim")
