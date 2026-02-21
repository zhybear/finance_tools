# Quick Start Guide

## Getting Started with example_trades.csv

The `example_trades.csv` file contains a sample 12-stock portfolio that you can use to test the portfolio analyzer.

### Quick Test

```bash
# Load and analyze the example portfolio
python3 stock.py --csv example_trades.csv

# Generate text report
python3 stock.py --csv example_trades.csv --output example_report.txt

# Generate PDF report with charts
python3 stock.py --csv example_trades.csv --pdf example_report.pdf

# Both reports at once
python3 stock.py --csv example_trades.csv --output example_report.txt --pdf example_report.pdf
```

## Example Portfolio Contents

The `example_trades.csv` includes 12 diverse stocks:

| Symbol | Shares | Date       | Price  | Industry        |
|--------|--------|------------|--------|-----------------|
| AAPL   | 100    | 2015-04-15 | $125.5 | Technology      |
| MSFT   | 75     | 2016-08-22 | $57.2  | Technology      |
| NVDA   | 50     | 2018-06-10 | $55.25 | Semiconductors  |
| TSLA   | 25     | 2019-12-01 | $84.65 | Electric Vehicles|
| GOOGL  | 40     | 2017-03-05 | $847.5 | Technology      |
| AMZN   | 15     | 2014-11-20 | $312.0 | E-Commerce      |
| META   | 60     | 2019-05-18 | $165.5 | Social Media    |
| NFLX   | 30     | 2015-01-12 | $436.0 | Streaming       |
| SHOP   | 20     | 2017-09-08 | $132.5 | E-Commerce      |
| JPM    | 50     | 2018-02-14 | $104.75| Finance         |
| BRK.B  | 10     | 2016-11-27 | $179.5 | Holding Company |
| AMD    | 80     | 2017-04-03 | $13.95 | Semiconductors  |

**Total Initial Investment**: ~$139,000 (2014-2019 purchase dates)

## Expected Results

When you run the analysis on this example portfolio, you'll see:

1. **Individual Trade Performance**: Each trade shows current value, CAGR, and outperformance vs S&P 500
2. **Per-Symbol Aggregation**: Stocks with multiple trades show accumulated totals
3. **Portfolio Summary**: Overall metrics comparing your portfolio to S&P 500

## How to Use Your Own Data

1. Create a CSV file with your trades in this format:

```csv
symbol,shares,purchase_date,price
AAPL,100,2020-01-15,75.50
MSFT,50,2021-06-20,220.00
MY_STOCK,10,2022-03-10,150.00
```

2. Run the analyzer:

```bash
python3 stock.py --csv your_trades.csv --output your_report.txt --pdf your_report.pdf
```

## Key Features Demonstrated

Using the example file, you'll see:

- ✅ **Multi-year portfolio tracking** (2014-2019 trades)
- ✅ **Technology sector dominance** (8/12 stocks in tech)
- ✅ **Diversification** (semiconductors, e-commerce, finance, holding companies)
- ✅ **Different performance periods** (IPOs to mature companies)
- ✅ **S&P 500 benchmark comparison** (verify your outperformance)
- ✅ **Text and PDF report generation**

## Next Steps

1. **Test with the example**:
   ```bash
   python3 stock.py --csv example_trades.csv
   ```

2. **Run the test suite**:
   ```bash
   python3 -m unittest test_stock.py -v
   ```

3. **Create your own portfolio**:
   - List your actual trades in CSV format
   - Run the same commands with your file

4. **Review the reports**:
   - Check `example_report.txt` for detailed metrics
   - View `example_report.pdf` for visualizations

## Support

For complete documentation, see [README.md](README.md)

For questions about CSV format, CAGR calculation, or metrics, check the README's detailed explanations.
