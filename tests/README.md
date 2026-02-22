# Portfolio Analyzer Test Suite

Modular test structure for comprehensive testing of all portfolio_analyzer components.

## Structure

```
tests/
├── __init__.py           # Test package initialization
├── test_metrics.py       # CAGR and XIRR calculation tests (238 lines)
├── test_loaders.py       # CSV loading and validation tests (91 lines)
├── test_analyzer.py      # Core analyzer and benchmark tests (329 lines)
├── test_reports.py       # Report generation tests (176 lines)
├── test_cli.py           # Command-line interface tests (133 lines)
└── test_utils.py         # Utility function tests (124 lines)
```

**Total**: 1,120 lines across 6 focused modules (was 968 lines in single file)

## Running Tests

### All Tests
```bash
python3 -m unittest discover tests -v
```

### Individual Modules
```bash
python3 -m unittest tests.test_metrics -v      # CAGR/XIRR tests
python3 -m unittest tests.test_loaders -v      # CSV loading tests
python3 -m unittest tests.test_analyzer -v     # Core analyzer tests
python3 -m unittest tests.test_reports -v      # Report generation tests
python3 -m unittest tests.test_cli -v          # CLI tests
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
- **TestCAGRCalculation** (6 tests): Basic CAGR, weighted CAGR, edge cases
- **TestXIRRCalculation** (7 tests): Newton-Raphson solver, multi-cash-flow scenarios

### test_loaders.py
Tests for data loading:
- **TestCSVLoading** (3 tests): File loading, validation, error handling

### test_analyzer.py
Tests for core analysis engine:
- **TestSP500Benchmark** (2 tests): Benchmark data validation
- **TestTradeValidation** (5 tests): Trade data validation rules
- **TestPortfolioAnalysis** (2 tests): Portfolio-wide calculations
- **TestSP500BenchmarkCSV** (1 test): Integration test with CSV
- **TestSymbolAccumulation** (3 tests): Per-symbol aggregation

### test_reports.py
Tests for report generation:
- **TestPDFDataPreparation** (2 tests): PDF data formatting
- **TestReportGeneration** (3 tests): Text report output
- **TestHTMLReportGeneration** (3 tests): HTML dashboard creation

### test_cli.py
Tests for command-line interface:
- **TestCLI** (7 tests): Argument parsing, file handling, error scenarios

### test_utils.py
Tests for utility functions:
- **TestSafeDivide** (4 tests): Zero-division handling
- **TestUtilsFunctions** (7 tests): Timezone normalization, DataFrame extraction

## Test Coverage

```bash
# Run with coverage
python3 -m coverage run -m unittest discover tests
python3 -m coverage report --include="portfolio_analyzer/*"
```

**Current Coverage**: 88% (535 statements, 62 uncovered)

## Benefits of Modular Structure

✅ **Easier Navigation**: Find tests by component (metrics, loaders, etc.)  
✅ **Faster Development**: Run only affected tests during development  
✅ **Better Organization**: Each module < 330 lines (highly maintainable)  
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
Version: 1.2.0  
License: ISC
