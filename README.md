# Finance Tools

Professional-grade financial analysis tools built with Python for transparent, auditable portfolio analysis.

## Repository Structure

This monorepo contains modular financial analysis tools:

```
finance_tools/
├── portfolio_analyzer/    # Portfolio performance analysis (v1.3.4)
│   ├── README.md         # Full documentation
│   ├── requirements.txt   # Dependencies
│   └── example_trades.csv # Sample data
│
├── LICENSE               # MIT License
└── README.md            # This file
```

## Tools

### Portfolio Analyzer

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Tests](https://img.shields.io/badge/tests-149%2F149-brightgreen.svg)
![Coverage](https://img.shields.io/badge/coverage-91%25-brightgreen.svg)
![License](https://img.shields.io/badge/license-ISC-blue.svg)

**Analyze stock portfolio performance with cash flow tracking and real S&P 500 benchmarking.**

What makes this different:
- **Cash Flow Aware**: XIRR calculations account for when and how much you invested (not just snapshots)
- **Multi-Period Analysis**: Analyze any time period, not locked to 1/3/5/10 year presets
- **S&P 500 Comparison**: Helps you decide if active stock picking beats a simple index fund investment
- **Real Market Data**: S&P 500 benchmark uses actual yfinance closing prices
- **Mathematically Rigorous**: All calculations are transparent and testable (149 tests, 91% coverage)
- **Multiple Formats**: Text, PDF, and interactive HTML reports

**Example Dashboard:**
Check [portfolio_analyzer/examples/example_report.html](portfolio_analyzer/examples/example_report.html) for a live interactive dashboard showing:
- Real-time performance metrics (portfolio value, gains, returns)
- Interactive Plotly charts visualizing performance
- Expandable trade-by-trade breakdown
- Responsive design (desktop/mobile)

**Quick Start:**
```bash
cd portfolio_analyzer
pip install -r requirements.txt
python3 -m portfolio_analyzer.cli --csv example_trades.csv
```

**Full Documentation & Screenshots:** See [portfolio_analyzer/README.md](portfolio_analyzer/README.md)

## Philosophy

These tools prioritize:
- **Accuracy** - Real data, no estimates or approximations
- **Transparency** - Open source, fully auditable calculations
- **Rigor** - Comprehensive test coverage validates every metric
- **Usability** - CLI, Python API, and multiple output formats

## License

MIT License - See [LICENSE](LICENSE) file
