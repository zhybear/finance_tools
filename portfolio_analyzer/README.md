# Portfolio Analyzer

A comprehensive Python tool for analyzing stock portfolio performance with S&P 500 benchmarking.

## Features

- **CAGR & XIRR Analysis**: Compound Annual Growth Rate and Extended Internal Rate of Return calculations
- **S&P 500 Comparison**: Compare portfolio performance against S&P 500 benchmark index
- **Symbol Aggregation**: View accumulated metrics per stock symbol
- **Multiple Report Formats**:
  - Text reports with detailed analysis
  - PDF reports with professional visualizations and charts
  - Interactive HTML dashboards with Plotly charts and dark mode support
- **CSV Support**: Load and validate trades from CSV files
- **Modular Architecture**: Clean, testable code with separation of concerns
- **Production Ready**: v1.3.3 with comprehensive test coverage (91%)

## Installation

```bash
# Required dependencies
pip install yfinance pandas numpy scipy

# Optional (for visualizations)
pip install matplotlib seaborn plotly reportlab
```

## Quick Start

### Try the Example

The `examples/` directory contains a sample portfolio with pre-generated outputs:

- **Input**: `examples/example_trades.csv` (12-stock portfolio)
- **Outputs**: 
  - `examples/example_report.txt` (Text report with detailed analysis)
  - `examples/example_report.pdf` (PDF with charts and visualizations)
  - **[`examples/example_report.html`](https://rawcdn.githack.com/zhybear/finance_tools/main/portfolio_analyzer/examples/example_report.html)** (Interactive HTML dashboard - click to preview)

Generate these yourself:
```bash
python -m portfolio_analyzer.cli --csv examples/example_trades.csv --output examples/example_report.txt --pdf examples/example_report.pdf --html examples/example_report.html
```

### Command Line

```bash
# Analyze trades from CSV
python -m portfolio_analyzer.cli --csv trades.csv

# Generate text report
python -m portfolio_analyzer.cli --csv trades.csv --output report.txt

# Generate PDF with charts
python -m portfolio_analyzer.cli --csv trades.csv --pdf report.pdf

# Generate interactive HTML dashboard
python -m portfolio_analyzer.cli --csv trades.csv --html report.html

# All formats at once
python -m portfolio_analyzer.cli --csv trades.csv --output report.txt --pdf report.pdf --html report.html
```

### Python API

```python
from portfolio_analyzer import PortfolioAnalyzer, load_trades_from_csv

# Load trades
trades = load_trades_from_csv("trades.csv")

# Create analyzer
analyzer = PortfolioAnalyzer(trades)

# Generate reports
analyzer.print_report()
analyzer.generate_pdf_report("report.pdf")
analyzer.generate_html_report("dashboard.html")

# Access analysis data
analysis = analyzer.analyze_portfolio()
print(f"Portfolio CAGR: {analysis['portfolio_cagr']:.2f}%")
print(f"Portfolio XIRR: {analysis['portfolio_xirr']:.2f}%")
```

## CSV Format

```csv
symbol,shares,purchase_date,price
SBUX,100,2015-04-15,48.14
MSFT,75,2016-08-22,57.20
NVDA,50,2018-06-10,55.25
```

Prices shown are historical close values for the listed dates.

## Testing

```bash
# Run all tests
python -m unittest discover -s tests -p "test_*.py" -v

# Run specific test
python -m unittest tests.test_analyzer -v
```

## Architecture

- **analyzer.py**: Core portfolio analysis engine
- **metrics.py**: CAGR and XIRR calculations
- **reports.py**: Text, PDF, and HTML report generation
- **loaders.py**: CSV file loading and validation
- **utils.py**: Helper functions and utilities
- **cli.py**: Command-line interface

## Version

Current version: **1.3.3** (Production Ready)

See RELEASE_NOTES.md for detailed changelog.
