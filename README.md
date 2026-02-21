# Portfolio Performance Analyzer

A Python tool for analyzing stock portfolio performance and comparing against S&P 500 benchmark.

## Features

- **Portfolio Analysis**: Calculate CAGR (Compound Annual Growth Rate) for individual trades and overall portfolio
- **S&P 500 Comparison**: Compare your portfolio performance against S&P 500 benchmark
- **Symbol Aggregation**: View accumulated earnings and metrics per stock symbol
- **Text Reports**: Generate detailed text reports with per-trade and per-symbol analysis
- **PDF Visualizations**: Create professional 2-page PDF reports with charts and tables
- **CSV Support**: Load trades from CSV files with validation

## Installation

```bash
pip3 install yfinance pandas matplotlib seaborn
```

## Usage

### Basic Command Line Usage

```bash
# Analyze trades from CSV file with default symbols
python3 stock.py --csv your_trades.csv

# Save text report to file
python3 stock.py --csv your_trades.csv --output report.txt

# Generate PDF report with visualizations
python3 stock.py --csv your_trades.csv --pdf report.pdf

# Both text and PDF reports
python3 stock.py --csv your_trades.csv --output report.txt --pdf report.pdf
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
- `my_trades.csv` - User's portfolio (if loaded via --csv option)

## Output Reports

### Text Report Format

Each report includes:
1. **Individual Stock Performance** - Per-trade details with CAGR and S&P 500 comparison
2. **Accumulated Metrics** - Per-symbol aggregation with weighted averages
3. **Portfolio Summary** - Total gains, overall CAGR, outperformance vs S&P 500

### PDF Report (2 Pages)

**Page 1: Summary & Charts**
- Portfolio summary metrics box
- Top 10 holdings by value (pie chart with legend)
- Top 8 performers by CAGR (bar chart with S&P 500 reference line)
- Top 8 by dollar gain (bar chart)
- Position statistics (winning/losing positions)

**Page 2: Detailed Table**
- Top 10 positions with detailed metrics
- Columns: Symbol, Trades, Invested, Current, Gain, Gain%, CAGR%

## Example Output

```
=== PORTFOLIO SUMMARY ===
Initial Investment: $159,835.52
Current Value: $2,795,071.13
Total Gain: $2,635,235.61
Portfolio CAGR: 75.06%
S&P 500 CAGR: 15.83%
Portfolio Outperformance: 59.23%
```

## Key Metrics Explained

- **CAGR** (Compound Annual Growth Rate): Annual growth rate accounting for reinvestment
  - Formula: `((End Value / Start Value)^(1/Years) - 1) × 100`
- **Initial Investment**: Total amount invested across all trades
- **Current Value**: Today's market value of all positions
- **Outperformance**: Portfolio CAGR minus S&P 500 CAGR
- **Weighted CAGR**: Investment-weighted average CAGR (larger investments weighted more)

## Code Structure

### Main Classes

- `PortfolioAnalyzer`: Core analysis engine
  - `analyze_portfolio()`: Calculate overall portfolio metrics
  - `get_stock_performance()`: Calculate individual trade performance
  - `print_report()`: Generate text reports
  - `generate_pdf_report()`: Create PDF visualizations

- Helper Functions
  - `load_trades_from_csv()`: Load and validate CSV files

### Key Methods

- `calculate_cagr()`: Calculate compound annual growth rate
- `_validate_trade()`: Validate trade data
- `_prepare_histories()`: Bulk download stock price histories
- `_safe_divide()`: Safe division with zero-handling
- `_calculate_symbol_accumulation()`: Aggregate trades by symbol

## Testing

The project includes 28+ comprehensive unit tests covering:
- CAGR calculations (5 tests)
- S&P 500 benchmark validation (3 tests)
- CSV loading and validation (3 tests)
- Trade validation (5 tests)
- Portfolio analysis (2 tests)
- Symbol accumulation (3 tests)
- Safe division helper (3 tests)
- PDF data preparation (2 tests)
- Report generation (2 tests)
- S&P 500 self-consistency integration test (1 test)

Run tests with:
```bash
python3 -m unittest test_stock.py -v
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

## Performance

- Bulk download optimization: Downloads all stocks in 1 API call instead of N calls
- 10-100x faster than individual stock downloads
- Caching of price histories for repeated analysis
- Investment-weighted calculation for accurate portfolio metrics

## License

Open source for portfolio analysis and education.
