# Portfolio Analyzer Test Suite

Modular test structure for comprehensive testing of all portfolio_analyzer components.

## Structure

```
tests/
├── __init__.py           # Test package initialization
├── conftest.py           # Shared fixtures and caching setup
├── test_metrics.py       # CAGR and XIRR calculation tests
├── test_loaders.py       # CSV loading and validation tests
├── test_analyzer.py      # Core analyzer and benchmark tests
├── test_reports.py       # Report generation tests
├── test_cli.py           # Command-line interface tests
├── test_investor_comparison.py # Investor comparison dashboard tests
└── test_utils.py         # Utility function tests
```

**Total**: 7 focused test modules

## Running Tests

### All Tests
```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

### Individual Modules
```bash
python3 -m unittest tests.test_metrics -v      # CAGR/XIRR tests
python3 -m unittest tests.test_loaders -v      # CSV loading tests
python3 -m unittest tests.test_analyzer -v     # Core analyzer tests
python3 -m unittest tests.test_reports -v      # Report generation tests
python3 -m unittest tests.test_cli -v          # CLI tests
python3 -m unittest tests.test_investor_comparison -v  # Investor comparison tests
python3 -m unittest tests.test_utils -v        # Utility tests
```

### Specific Test Classes
```bash
python3 -m unittest tests.test_metrics.TestCAGRCalculation -v
python3 -m unittest tests.test_analyzer.TestPortfolioAnalysis -v
```

### Quick Mode (no verbose output)
```bash
python3 -m unittest discover tests -q
```

## Test Modules

### test_metrics.py
Tests for financial calculations:
- **TestCAGRCalculation**: Basic CAGR, weighted CAGR, edge cases
- **TestXIRRCalculation**: Newton-Raphson solver, multi-cash-flow scenarios

### test_loaders.py
Tests for data loading:
- **TestCSVLoading**: File loading, validation, error handling

### test_analyzer.py
Tests for core analysis engine:
- **TestSP500Benchmark**: Benchmark data validation
- **TestTradeValidation**: Trade data validation rules
- **TestPortfolioAnalysis**: Portfolio-wide calculations
- **TestSP500BenchmarkCSV**: Integration test with CSV
- **TestSymbolAccumulation**: Per-symbol aggregation

### test_reports.py
Tests for report generation:
- **TestPDFDataPreparation**: PDF data formatting
- **TestReportGeneration**: Text report output
- **TestHTMLReportWithCharts**: HTML dashboard creation with charts
- **TestPDFReportGeneration**: PDF report creation

### test_cli.py
Tests for command-line interface:
- **TestCLI**: Argument parsing, file handling, error scenarios

### test_utils.py
Tests for utility functions:
- **TestSafeDivide**: Zero-division handling
- **TestUtilsFunctions**: Timezone normalization, DataFrame extraction
- **TestTickerNormalization**: Ticker normalization and analyzer integration

### test_investor_comparison.py
Tests for investor comparison dashboards:
- **TestInvestorComparison**: Ranking, chart data, and HTML rendering

## Test Coverage

```bash
# Run with coverage
python3 -m coverage run -m unittest discover tests
python3 -m coverage report --include="portfolio_analyzer/*"
```

**Current Coverage**: 94% (205 tests)

## Benefits of Modular Structure

✅ **Easier Navigation**: Find tests by component (metrics, loaders, etc.)  
✅ **Faster Development**: Run only affected tests during development  
✅ **Better Organization**: Focused modules with clear scopes  
✅ **Clear Dependencies**: Each module imports only what it needs  
✅ **Parallel Testing**: Can run modules in parallel if needed  

## Migration from test_stock.py

The original `test_stock.py` (968 lines) has been split into 6 focused modules. 

**Before (v1.2.0)**:
```bash
python3 -m unittest test_stock -v
```

**After (v1.2.1+)**:
```bash
python3 -m unittest discover tests -v
```

All test functionality is preserved with no changes to test logic.

## Author

Zhuo Robert Li  
Version: 1.3.5  
License: ISC

## Current Test Count

**Total Tests**: 205 (as of 2026-02-26)

### Coverage Highlights

- Investor comparison ranking and HTML chart coverage
- Ticker normalization and trade validation coverage
- Cached yfinance requests to keep the full suite fast

