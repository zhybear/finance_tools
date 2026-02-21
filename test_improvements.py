#!/usr/bin/env python3
"""Quick test of improvements to verify code works"""

from stock import PortfolioAnalyzer

# Test 1: _safe_divide
analyzer = PortfolioAnalyzer([])
assert analyzer._safe_divide(10, 2, 0) == 5.0, "safe_divide normal"
assert analyzer._safe_divide(10, 0, 99) == 99, "safe_divide zero div"
assert analyzer._safe_divide(10, -5, 0) == 0, "safe_divide negative"
print("✅ _safe_divide tests passed")

# Test 2: symbol accumulation
trades = [
    {'symbol': 'TEST', 'shares': 100, 'initial_value': 1000, 'current_value': 1500,
     'stock_cagr': 10.0, 'sp500_current_value': 1200, 'years_held': 5},
    {'symbol': 'TEST', 'shares': 50, 'initial_value': 500, 'current_value': 750,
     'stock_cagr': 8.0, 'sp500_current_value': 600, 'years_held': 5},
]
stats = analyzer._calculate_symbol_accumulation(trades)
assert 'TEST' in stats, "TEST symbol in stats"
assert stats['TEST']['trades_count'] == 2, "2 trades counted"
assert stats['TEST']['total_gain'] == 750, "total gain calculated"
assert stats['TEST']['gain_percentage'] == 50.0, "gain percentage calculated"
print("✅ Symbol accumulation tests passed")

# Test 3: PDF data prep
analysis = {'portfolio_cagr': 5, 'sp500_cagr': 3}
symbol_stats = {
    'A': {'total_current_value': 1000, 'total_gain': 100, 'avg_cagr': 5},
    'B': {'total_current_value': 500, 'total_gain': -50, 'avg_cagr': -2},
    'C': {'total_current_value': 200, 'total_gain': 0, 'avg_cagr': 0},
}
data = analyzer._prepare_pdf_data(analysis, symbol_stats)
assert data['winning'] == 1, "1 winning position"
assert data['losing'] == 1, "1 losing position"
assert data['neutral'] == 1, "1 neutral position"
assert data['total_symbols'] == 3, "3 total symbols"
print("✅ PDF data prep tests passed")

# Test 4: CAGR calculation
cagr1 = analyzer.calculate_cagr(100, 200, 5)
assert abs(cagr1 - 14.87) < 0.1, f"CAGR basic calculation: {cagr1}"
cagr2 = analyzer.calculate_cagr(100, 50, 5)
assert abs(cagr2 - (-12.94)) < 0.1, f"CAGR negative: {cagr2}"
cagr3 = analyzer.calculate_cagr(0, 100, 5)
assert cagr3 == 0, "CAGR zero start"
cagr4 = analyzer.calculate_cagr(100, 200, 0)
assert cagr4 == 0, "CAGR zero years"
print("✅ CAGR calculation tests passed")

print("\n✅✅✅ All improvement tests PASSED! ✅✅✅")
