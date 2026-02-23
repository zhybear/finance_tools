"""Command-line interface for portfolio analyzer.

Author: Zhuo Robert Li
"""

import argparse
import sys
from .loaders import load_trades_from_csv
from .analyzer import PortfolioAnalyzer
from .reports import TextReportGenerator, PDFReportGenerator, HTMLReportGenerator


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Portfolio Performance Analyzer")
    parser.add_argument("--csv", help="Path to CSV file with trades")
    parser.add_argument("--output", "-o", help="Path to save report to text file")
    parser.add_argument("--pdf", help="Path to save report as PDF file with visualizations")
    parser.add_argument("--html", help="Path to save interactive HTML dashboard report")
    args = parser.parse_args()

    if args.csv:
        try:
            trades = load_trades_from_csv(args.csv)
        except Exception as e:
            print(f"Failed to load CSV: {e}")
            sys.exit(1)
    else:
        trades = [
            {"symbol": "AAPL", "shares": 100, "purchase_date": "2020-01-02", "price": 75.5},
            {"symbol": "MSFT", "shares": 50, "purchase_date": "2021-01-04", "price": 220.0},
        ]

    analyzer = PortfolioAnalyzer(trades)
    
    # Generate text report
    TextReportGenerator.generate(analyzer, output_file=args.output)
    
    # Generate PDF if requested
    if args.pdf:
        PDFReportGenerator.generate(analyzer, args.pdf)
    
    # Generate HTML if requested
    if args.html:
        HTMLReportGenerator.generate(analyzer, args.html)


if __name__ == "__main__":
    main()
