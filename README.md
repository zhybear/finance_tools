# Portfolio Performance Analyzer

A Python tool for analyzing stock portfolio performance and comparing against S&P 500 benchmark.

## Features

- **CAGR & XIRR Analysis**: Calculate both Compound Annual Growth Rate and Extended Internal Rate of Return
- **S&P 500 Comparison**: Compare your portfolio performance against S&P 500 benchmark
- **Symbol Aggregation**: View accumulated earnings and metrics per stock symbol
- **Text Reports**: Generate detailed text reports with per-trade and per-symbol analysis
- **PDF Visualizations**: Create professional 2-page PDF reports with charts and tables
- **HTML Dashboard**: Interactive HTML reports with Plotly charts, sortable tables, and dark mode
- **CSV Support**: Load trades from CSV files with validation
- **Modular Architecture**: Clean separation of concerns across 7 focused modules

## Installation

```bash
pip3 install yfinance pandas numpy scipy matplotlib seaborn plotly
```

## Usage

### Command Line Usage

```bash
# Analyze trades from CSV file
python3 -m portfolio_analyzer.cli --csv your_trades.csv

# Save text report to file
python3 -m portfolio_analyzer.cli --csv your_trades.csv --output report.txt

# Generate PDF report with visualizations
python3 -m portfolio_analyzer.cli --csv your_trades.csv --pdf report.pdf

# Generate interactive HTML dashboard
python3 -m portfolio_analyzer.cli --csv your_trades.csv --html report.html

# All report formats together
python3 -m portfolio_analyzer.cli --csv your_trades.csv --output report.txt --pdf report.pdf --html report.html
```

### Python API Usage

```python
from portfolio_analyzer import PortfolioAnalyzer, load_trades_from_csv

# Load trades from CSV
trades = load_trades_from_csv("your_trades.csv")

# Create analyzer
analyzer = PortfolioAnalyzer(trades)

# Generate reports
analyzer.print_report()  # Text to stdout
analyzer.generate_pdf_report("report.pdf")  # PDF
analyzer.generate_html_report("dashboard.html")  # HTML

# Get analysis data programmatically
analysis = analyzer.analyze_portfolio()
print(f"Portfolio CAGR: {analysis['portfolio_cagr']:.2f}%")
print(f"Portfolio XIRR: {analysis['portfolio_xirr']:.2f}%")
```

### Running Tests

```bash
# Run all unit tests
python3 -m unittest test_stock.py -v

# Run specific test class
python3 -m unittest test_stock.TestCAGRCalculation -v
```

## CSV Format

Create a CSV file with the following format:

```csv
symbol,shares,purchase_date,price
AAPL,100,2015-04-15,125.50
MSFT,75,2016-08-22,57.20
NVDA,50,2018-06-10,55.25
```

**Required Columns:**
- `symbol`: Stock ticker symbol (e.g., AAPL, MSFT)
- `shares`: Number of shares purchased (positive number)
- `purchase_date`: Purchase date in YYYY-MM-DD format
- `price`: Purchase price per share (positive number)

**Example Files:**
- `example_trades.csv` - Diverse portfolio example with 12 stocks
  (Load your own portfolio by specifying your CSV file with --csv)

## Output Reports

### Text Report Format

Each report includes:
1. **Individual Stock Performance** - Per-trade details with both CAGR and XIRR metrics
2. **Accumulated Metrics** - Per-symbol aggregation with weighted averages for both metrics
3. **Portfolio Summary** - Total gains, CAGR, XIRR, and outperformance vs S&P 500

### PDF Report (2+ Pages)

**Page 1: Summary & Charts**
- Portfolio summary box with CAGR and XIRR metrics
- Top 10 holdings by current value (pie chart with legend)
- Top 8 performers by CAGR (bar chart with S&P 500 comparison line)
- Top 8 performers by XIRR (bar chart with S&P 500 comparison line) - **NEW**
- Top 8 by dollar gain (bar chart)
- Position statistics (winning/losing/neutral positions)

**Page 2: Detailed Table**
- Top 10 positions with all key metrics
- Columns: Symbol, Trades, Invested, Current, Gain, Gain%, CAGR%, XIRR%

## Example Output

```
=== PORTFOLIO SUMMARY ===
Initial Investment: $[total_invested]
Current Value: $[current_value]
Total Gain: $[total_gain]
Portfolio CAGR: [cagr]%
Portfolio XIRR: [xirr]%
S&P 500 CAGR: [sp500_cagr]%
S&P 500 XIRR: [sp500_xirr]%
Portfolio Outperformance (CAGR): [outperf_cagr]%
Portfolio Outperformance (XIRR): [outperf_xirr]%
```


## Key Metrics Explained

### CAGR (Compound Annual Growth Rate) - NEW Weighted Formula in 1.1

**For single trades**: `CAGR = ((End Value / Start Value)^(1/Years) - 1) × 100`

**For multiple trades (weighted)**:
```
For each trade i:
  r_i = CAGR from purchase_date_i to today
  w_i = investment_amount_i × years_held_i
  
Weighted CAGR = Σ(r_i × w_i) / Σ(w_i)
```

This weights each transaction by both its investment size and holding period, giving more prominence to early, large purchases.

**Example**:
- Trade 1: $100 invested 5 years ago → $200 (CAGR=14.87%), weight = 100×5 = 500
- Trade 2: $100 invested 1 year ago → $110 (CAGR=10%), weight = 100×1 = 100
- **Weighted CAGR = (14.87×500 + 10×100) / 600 = 14.14%**

**Best for**: Understanding average return considering both time and size of investments

### XIRR (Extended Internal Rate of Return)

The rate where NPV (Net Present Value) = 0:
```
NPV = Σ(CF / (1+r)^(Years from purchase to today)) = 0
```

Solved using Newton-Raphson optimization. Accounts for exact timing of cash flows.

**Best for**: Investments with multiple purchases at different dates

**Key Difference from CAGR**: XIRR weights all cash flows by exact timing, while weighted CAGR uses simple weighting by size and duration.

### Other Metrics

- **Initial Investment**: Total amount invested across all trades
- **Current Value**: Today's market value of all positions
- **Gain**: Dollar amount of profit/loss
- **Gain %**: Percentage gain on total investment
- **Outperformance**: Your metric minus S&P 500 metric

## Code Structure (v1.2.0)

The portfolio analyzer is organized as a modular package for maintainability and extensibility:

### Package Architecture

```
portfolio_analyzer/
├── __init__.py         # Package exports and version
├── analyzer.py         # Core PortfolioAnalyzer class (442 lines)
├── metrics.py          # CAGR and XIRR calculations (99 lines)
├── loaders.py          # CSV loading and validation (65 lines)
├── reports.py          # Report generators (319 lines)
├── utils.py            # Helper functions (110 lines)
└── cli.py              # Command-line interface (46 lines)
```

### Main Classes

- **`PortfolioAnalyzer`** (analyzer.py): Core analysis engine
  - `analyze_portfolio()`: Calculate overall portfolio metrics
  - `get_stock_performance()`: Calculate individual trade performance
  - `print_report()`: Generate text reports
  - `generate_pdf_report()`: Create PDF visualizations
  - `generate_html_report()`: Create interactive HTML dashboards

- **Report Generators** (reports.py)
  - `TextReportGenerator`: Console and text file reports
  - `PDFReportGenerator`: Professional PDF reports with charts
  - `HTMLReportGenerator`: Interactive dashboards with Plotly

### Key Functions

- **Metrics** (metrics.py)
  - `calculate_cagr()`: Compound annual growth rate
  - `calculate_xirr()`: Extended internal rate of return (Newton-Raphson)

- **Loaders** (loaders.py)
  - `load_trades_from_csv()`: Load and validate CSV files

- **Utils** (utils.py)
  - `safe_divide()`: Zero-safe division
  - `normalize_history_index()`: Timezone handling
  - `download_history()`: Bulk stock price download

## Testing

The project includes 55 comprehensive unit tests with 88% code coverage:

**Test Coverage by Module:**
- `__init__.py`: 100% (package exports)
- `cli.py`: 96% (command-line interface)
- `loaders.py`: 91% (CSV loading)
- `reports.py`: 90% (report generation)
- `analyzer.py`: 86% (core analysis)
- `metrics.py`: 77% (CAGR/XIRR calculations)
- `utils.py`: 97% (helper functions)

**Test Suites:**
- CAGR calculations (6 tests) - Including weighted CAGR formula
- XIRR calculations (7 tests) - Newton-Raphson convergence
- CLI interface (7 tests) - Argument parsing and file handling
- CSV loading and validation (3 tests)
- Trade validation (5 tests)
- Portfolio analysis (2 tests)
- Symbol accumulation (3 tests)
- Utils functions (7 tests) - Timezone handling, downloads
- Report generation (8 tests) - Text, PDF, HTML outputs
- S&P 500 benchmark (4 tests) - Self-consistency validation

Run tests with:
```bash
python3 -m unittest test_stock.py -v

# With coverage report
python3 -m coverage run -m unittest test_stock
python3 -m coverage report --include="portfolio_analyzer/*"
```

## Example Analysis

Using `example_trades.csv` (12-stock portfolio from 2014-2019):

```
Loaded 12 example trades:
  AAPL: 100 shares @ $125.5
  MSFT: 75 shares @ $57.2
  NVDA: 50 shares @ $55.25
  TSLA: 25 shares @ $84.65
  GOOGL: 40 shares @ $847.5
  AMZN: 15 shares @ $312.0
  META: 60 shares @ $165.5
  NFLX: 30 shares @ $436.0
  SHOP: 20 shares @ $132.5
  JPM: 50 shares @ $104.75
  BRK.B: 10 shares @ $179.5
  AMD: 80 shares @ $13.95
```

## Notes

- All dates must be in YYYY-MM-DD format
- Stock prices are fetched from Yahoo Finance in real-time
- S&P 500 symbol used: ^GSPC
- Timezone handling is automatic (UTC normalization)
- Division-by-zero operations are safely handled
- XIRR uses scipy's Newton-Raphson optimization (requires scipy)

## Performance

- Bulk download optimization: Downloads all stocks in 1 API call instead of N calls
- 10-100x faster than individual stock downloads
- Caching of price histories for repeated analysis
- Investment-weighted calculation for accurate portfolio metrics

## License

Open source for portfolio analysis and education.
