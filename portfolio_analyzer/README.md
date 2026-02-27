# Portfolio Analyzer

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Tests](https://img.shields.io/badge/tests-195%2F195-brightgreen.svg)
![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen.svg)
![License](https://img.shields.io/badge/license-ISC-blue.svg)

A comprehensive Python tool for analyzing stock portfolio performance with precise cash flow tracking and S&P 500 benchmarking.

## Why This Tool

**Better than fixed-period snapshots:**
Standard apps show returns for fixed periods (1, 3, 5, 10 years) by comparing two snapshots. This misses important context:
- If you invested $5K one year ago and $20K three months ago, the "1 year return" ignores that most of your money hasn't been invested for 1 year
- XIRR accounts for this - your actual time-weighted return is much more accurate than simple snapshots

**Know if active stock picking is worth it:**
This tool compares your portfolio to S&P 500 to help answer: "Should I just buy an index fund instead?"
- If consistently underperforming S&P 500, a low-cost index fund might be a better strategy
- Helps separate skill from luck - are you outperforming the market, or just lucky?
- You decide what to do with this information - the tool removes the guesswork

**Multi-period analysis at any time interval:**
Unlike apps locked to 1/3/5/10 year periods, analyze any date range you want
- "What was my return from March 2023 to now?"
- "How did I perform in the bull market of 2024?" 
- Compare any periods without artificial constraints

**Real cash flow accounting:**
- **When** you invested your money
- **How much** you invested at each time  
- **Real returns** accounting for your actual investment patterns

This tool uses **XIRR (Internal Rate of Return)** to calculate your true performance accounting for investment timing and amounts. Combined with **real S&P 500 market data**, you get exact comparisons to help guide your investment decisions.

## Features

- **Cash Flow Tracking**: Complete investment timeline tracking with XIRR calculations
  - Accounts for when and how much you invested
  - Accurately reflects your true returns vs random snapshots
  - Weighted CAGR reflects your actual capital deployment
  
- **CAGR & XIRR Analysis**: 
  - Compound Annual Growth Rate for simple long-term performance
  - Extended Internal Rate of Return for time-weighted accuracy
  - Works correctly with irregular investment patterns

- **S&P 500 Benchmarking**: 
  - Real market data from yfinance (never estimates or approximations)
  - Precise outperformance calculation vs actual market performance
  - Trade-level and portfolio-level benchmark comparison
  
- **Detailed Performance Metrics**:
  - Symbol-level aggregation showing performance per stock
  - Weighted metrics accounting for investment size and duration
  - Gain/loss breakdown and win/loss rates
  - Comprehensive trade-level analysis

- **Multiple Report Formats**:
  - Text reports with detailed analysis
  - PDF reports with professional visualizations and charts
  - Interactive HTML dashboards with Plotly charts and dark mode support

- **Investor Comparison (New in v1.3.5)**:
  - Compare your portfolio XIRR against legendary investors (Buffett, Lynch, Greenblatt)
  - Benchmark against S&P 500, NASDAQ, and Global Stocks
  - Ranked table and interactive bar chart with your portfolio highlighted
  
- **Transparent & Auditable**: 
  - 195 tests (94% coverage) validate every calculation
  - Open source - inspect exactly how calculations work
  - No black boxes or mysterious algorithms
  
- **Production Ready**: v1.3.5 with comprehensive test coverage and validation

## Example Output

### Performance Summary
Here's what the analysis produces. Running on a sample portfolio with multiple trades across different time periods:

```
╔════════════════════════════════════════════════════════════════════╗
║              Portfolio Performance Analysis                        ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  Portfolio Value:        $198,309                                 ║
║  Total Gain:             $167,434  (↑ 542.3%)                    ║
║  Portfolio WCAGR:        25.1%     (vs S&P 500: 18.3%)           ║
║  Outperformance:         +6.8%     (beating index!)              ║
║                                                                    ║
╠════════════════════════════════════════════════════════════════════╣
║  By Symbol                                                         ║
╠══════════════╤═══════════╤════════════╤═══════════╤════════════════╣
║  Symbol      │   Shares  │  Cost Basis│   Value   │    Return %    ║
╠══════════════╪═══════════╪════════════╪═══════════╪════════════════╣
║  MSFT        │   150.00  │  $20,000   │  $82,500  │    +312.5%     ║
║  TSLA        │    25.00  │  $5,000    │  $52,300  │    +946.0%     ║
║  ^GSPC       │   100.00  │  $50,000   │  $63,509  │     +27.0%     ║
╚══════════════╧═══════════╧════════════╧═══════════╧════════════════╝
```

### Interactive Dashboard
The HTML report provides an interactive dashboard with:
- **Real-time metrics cards** showing portfolio value, gains, returns, and percentile
- **Plotly charts** visualizing top holdings, allocation, sector breakdown, and performance
- **Investor Comparison** (NEW v1.3.5): 
  - Compare your XIRR against legendary investors (Warren Buffett, Peter Lynch, Joel Greenblatt, etc.)
  - See your rank and percentile vs. 10 professional investors and market indices
  - Interactive bar chart highlighting your portfolio
  - Ranked table with detailed investor performance data
- **Expandable trade details** showing every buy and current performance
- **Responsive design** works on desktop, tablet, and mobile
- **Dark mode support** for comfortable viewing

### Example Dashboard
See a live interactive example with investor comparison:
https://rawcdn.githack.com/zhybear/finance_tools/main/portfolio_analyzer/examples/example_report.html

The example shows your portfolio ranked against professional investors and includes:
- Your rank: #3 of 11 investors/benchmarks
- Your XIRR: 20.87% (beating Warren Buffett at 20.1%!)
- Percentile: 82nd percentile
- Outperformance vs S&P 500: +10.27%

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
MSFT,75,2016-08-22,57.67
NVDA,50,2018-06-10,6.56
```

Prices shown are historical close values (adjusted for splits/dividends) for the trading dates listed.

## Testing

```bash
# Run all tests (195 total)
python -m unittest discover -s tests -p "test_*.py" -v

# Run specific test module
python -m unittest tests.test_analyzer -v
python -m unittest tests.test_reports -v
python -m unittest tests.test_loaders -v
python -m unittest tests.test_investor_comparison -v

# Quick run (quiet mode)
python -m unittest discover -s tests -p "test_*.py" -q
```

**Test Coverage**: 94% (195 tests covering all modules: analyzer, reports, loaders, metrics, utils, investor_comparison, and CLI)

## Architecture

- **analyzer.py**: Core portfolio analysis engine
- **metrics.py**: CAGR and XIRR calculations
- **reports.py**: Text, PDF, and HTML report generation
- **loaders.py**: CSV file loading and validation
- **utils.py**: Helper functions and utilities
- **cli.py**: Command-line interface

## Version

Current version: **1.3.5** (Production Ready)

See RELEASE_NOTES.md for detailed changelog.
