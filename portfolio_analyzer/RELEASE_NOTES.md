# Release Notes

# Release Notes

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
