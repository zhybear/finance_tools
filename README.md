# Finance Tools

A collection of professional-grade financial analysis tools built with Python.

## Repository Structure

This monorepo contains modular financial analysis tools:

```
finance_tools/
├── portfolio_analyzer/    # Portfolio performance analysis (v1.3.3)
│   ├── README.md         # Full documentation
│   ├── requirements.txt   # Dependencies
│   └── example_trades.csv # Sample data
│
├── LICENSE               # MIT License
└── README.md            # This file
```

## Tools

### Portfolio Analyzer

Analyze stock portfolio performance with detailed CAGR/XIRR metrics and S&P 500 benchmarking.

**Quick Start:**
```bash
cd portfolio_analyzer
pip install -r requirements.txt
python3 -m portfolio_analyzer.cli --csv example_trades.csv
```

**Full Documentation:** See [portfolio_analyzer/README.md](portfolio_analyzer/README.md)

## License

MIT License - See [LICENSE](LICENSE) file
