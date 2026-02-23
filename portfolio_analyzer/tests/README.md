# Portfolio Analyzer Test Suite

Modular test structure for comprehensive testing of all portfolio_analyzer components.

## Structure

```
tests/
├── __init__.py           # Test package initialization
├── test_metrics.py       # CAGR and XIRR calculation tests
├── test_loaders.py       # CSV loading and validation tests
├── test_analyzer.py      # Core analyzer and benchmark tests
├── test_reports.py       # Report generation tests
├── test_cli.py           # Command-line interface tests
└── test_utils.py         # Utility function tests
```

**Total**: 6 focused test modules

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

## Test Coverage

```bash
# Run with coverage
python3 -m coverage run -m unittest discover tests
python3 -m coverage report --include="portfolio_analyzer/*"
```

**Current Coverage**: 91% (694 statements, 61 uncovered)

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
Version: 1.3.3  
License: ISC

## Current Test Count

**Total Tests**: 124 (as of 2026-02-22)

### Test Growth History

- **Initial**: 83 tests (core functionality)
- **Phase 1 (2026-02-22)**: +20 tests (edge cases, empty portfolios, type validation)
- **Phase 2 (2026-02-22)**: +21 tests (production hardening, performance, consistency)
- **Current**: 124 tests (49% increase)

### Phase 1: Edge Case Testing (+20 tests)

**test_loaders.py** (+8):
- Empty CSV file handling
- Rows with blank lines
- Whitespace normalization in symbols
- Negative shares validation
- Zero price handling
- Future and very old date support
- CSV format edge cases

**test_analyzer.py** (+8):
- Empty portfolio analysis
- Single trade portfolios
- Type validation (invalid inputs)
- Duplicate symbol aggregation (same/different days)
- Cache consistency across multiple calls
- Mixed performance (wins + losses)

**test_reports.py** (+4):
- Text reports with empty portfolios
- HTML reports with empty portfolios
- Single-trade portfolio reports

**test_cli.py** (+1):
- Combined output format options (--output --pdf --html)

### Phase 2: Production Hardening (+21 tests)

**test_analyzer.py** (+7):
- Large portfolio performance (100 trades)
- Concurrent analyzer instances
- Unicode symbol handling
- Timezone-aware timestamp handling
- Stock split adjusted prices
- Delisted stock handling
- Report generation consistency

**test_loaders.py** (+6):
- Multiple date format parsing
- Unicode symbol names (BRK.A, BRK.B)
- CSV files with extra columns
- Fractional share support
- Extreme price ranges (BRK.A ~$350k, penny stocks ~$0.0001)

**test_reports.py** (+4):
- Text report consistency (identical on repeated runs)
- HTML report required sections validation
- PDF report creation without errors
- Multi-symbol portfolio rendering

**test_cli.py** (+4):
- Malformed CSV error handling
- Invalid output path handling
- Empty CSV file validation
- Output format combinations

### Test Coverage by Component

| Module | Tests | Coverage |
|--------|-------|----------|
| test_metrics.py | ~25 | CAGR/XIRR formulas |
| test_loaders.py | 17 | CSV parsing & validation |
| test_analyzer.py | 45 | Portfolio analysis & benchmarks |
| test_reports.py | 14 | Report generation |
| test_cli.py | 13 | Command-line interface |
| test_utils.py | 10 | Utility functions |
| **Total** | **124** | **91%** |

### Edge Cases Covered

✅ Empty portfolios  
✅ Single-trade portfolios  
✅ Large portfolios (100+ trades)  
✅ Concurrent analyzer instances  
✅ Duplicate symbols (same/different dates)  
✅ Unicode in symbols (BRK.A, BRK.B)  
✅ Extreme prices ($350k+ and $0.0001)  
✅ Fractional shares  
✅ Future and very old dates  
✅ Empty CSV files  
✅ Malformed CSV data  
✅ Missing/invalid output paths  
✅ Stock splits & dividends  
✅ Delisted stocks  
✅ Timezone handling  
✅ Report consistency & validation

