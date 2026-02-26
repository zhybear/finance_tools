# Release Notes

## 1.3.5 (2026-02-25) - Investor Comparison Dashboard

### New Features
- **Investor comparison dashboard**: Rank your portfolio XIRR against legendary investors and market benchmarks
- **Interactive investor bar chart**: Visual comparison across all 10 investors with your portfolio highlighted
- **Ranked comparison table**: Clear ordering with performance notes and time periods
- **Educational disclaimer**: Historical performance data guidance included in the report

### Live Example
View the interactive report with investor comparison:
https://rawcdn.githack.com/zhybear/finance_tools/main/portfolio_analyzer/examples/example_report.html

### Tests and Coverage
- Added 38 unit tests for investor comparison module
- Maintained overall coverage at 91%

## 1.3.4 (2026-02-23) - Precision & Consistency Focus

### What Makes This Release Special

**Cash Flow Aware Analysis**
- Tracks every buy date and amount, not just fixed-point snapshots
- XIRR (Internal Rate of Return) accounts for investment timing - more accurate than comparing "value today vs 3 years ago"
- Works with any time period - analyze any date range, not limited to preset years (1, 3, 5, 10)
- Weighted CAGR reflects your actual capital deployment and timing
- Accurate performance even with irregular buying patterns

**S&P 500 Benchmarking - Know If Active Stock Picking Is Worth It**
- Compare your portfolio returns to S&P 500 index fund performance
- If consistently underperforming S&P 500, a low-cost index fund might be a better option
- Real market data from yfinance (never estimates or approximations)
- Helps you make informed decision: Is active stock selection worth the effort vs passive indexing?
- Outperformance calculations are perfectly consistent (0% when comparing identical assets)

**Mathematically Rigorous**
- All calculations use standard financial formulas with full transparency
- Consistent results across repeated analysis - same input always produces exact same output
- No approximations or tolerance hacks - results are mathematically exact

**Comprehensive Testing**
- 149 tests (91% code coverage) validate every calculation
- Phase 3: 25 new analytics validation tests focusing on calculation accuracy
- Tests ensure consistency across repeated analysis, different trade orders, and edge cases
- You can verify and audit all calculations against the test suite

**Practical & Transparent**
- Multiple output formats: Text (detailed), PDF (professional), HTML (interactive)
- Trade-level analysis shows individual CAGR/XIRR for each stock
- Symbol-level aggregation with weighted metrics
- Source code is fully open - you can see exactly how calculations work

### Testing Improvements - Phase 3
- **Phase 3**: Added 25 analytics validation tests focused on calculation accuracy and portfolio consistency
- **Total Tests**: Increased from 124 to 149 (79% increase from original 83)
- **Coverage**: Maintained at 91% code coverage
- **New Test Classes**:
  - `TestXIRRConvergenceDifficultCases`: Extreme high/low returns, uneven investments
  - `TestOutperformanceCalculationAccuracy`: CAGR/XIRR outperformance tracking, underperformance detection
  - `TestSymbolStatsAggregationAccuracy`: Single/multi-symbol aggregation, gain/loss calculations
  - `TestPortfolioSummaryConsistency`: Total value consistency, current value, gain/loss matching
  - `TestWinLossRateCalculation`: All winning trades, mixed portfolios
  - `TestBreakevenPositionIdentification`: Recent trades, CAGR breakeven indicators
  - `TestSP500BenchmarkVsRealPortfolio`: Independent calculations, value tracking
  - `TestAnalyticsCalculationAccuracy`: CAGR/XIRR consistency, years held, gain/loss signs
  - `TestMultiSymbolAnalyticsAggregation`: CAGR weighting, diverse portfolios
  - `TestPortfolioConsistencyAcrossAnalyses`: Repeated analysis, order independence

### Key Improvements
- **S&P 500 Accuracy Fix**: Uses real market closing prices for benchmark calculations, ensuring perfect consistency when comparing S&P 500 to itself
- **Timestamp Consistency**: Analyzer initialization caches evaluation timestamp, ensuring identical results across repeated analysis
- **Test Infrastructure**: Created `conftest.py` with `TradeBuilder` class and `TestDataConstants` for maintainable test code
- **Code Optimization**: Documented performance characteristics and verified efficiency for 100-1000 trade portfolios

## 1.3.3 (2026-02-22)

### Features
- Added S&P 500 WCAGR/XIRR benchmarking and HTML tooltip refinements
- Improved examples with verified historical stock prices
- Monorepo cleanup and examples directory included

### Testing Improvements
- **Phase 1**: Added 20 edge case tests (empty portfolios, type validation, data edge cases)
- **Phase 2**: Added 21 production hardening tests (100+ trade portfolios, concurrent instances, extreme prices, report consistency)
- **Total Tests**: Increased from 83 to 124 (49% increase)
- **Coverage**: Maintained at 91% code coverage
- **New Test Classes**:
  - `TestAnalyzerEdgeCases`: Empty portfolios, single trades, duplicate symbols, cache consistency
  - `TestAnalyzerPhase2`: Large portfolios, concurrent instances, unicode symbols, stock splits, report consistency
  - `TestLoadersPhase2`: Date formats, unicode symbols, extra columns, fractional shares, extreme prices
  - `TestReportsPhase2`: Report consistency, HTML sections, multi-symbol portfolios
  - `TestCLIPhase2`: Malformed CSV, invalid paths, empty files, combined options

### Documentation
- Updated all examples with real historical stock prices verified from Yahoo Finance
- Updated tests/README.md with comprehensive test documentation and coverage details
- Added TEST_COVERAGE_ANALYSIS.md with detailed gap analysis and recommendations

## 1.3.2 (2026-02-21)
- Code optimization and cleanup.

## 1.3.1 (2026-02-21)
- Performance and code-quality improvements.
- Documentation polish and attribution updates.

## 1.3.0 (2026-02-21)
- Modularized the test suite into focused modules.

## 1.2.0 (2026-02-21)
- Modular architecture and improved test coverage.
- PDF report improvements and layout refinements.

## 1.1.0 (2026-02-21)
- Weighted CAGR for multi-transaction symbols.
- XIRR reliability fixes and ordering corrections.

## 1.0 (2026-02-21)
- Initial release with core analyzer, CAGR/XIRR, CSV loading, reports, and tests.
