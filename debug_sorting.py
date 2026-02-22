import pandas as pd
from stock import PortfolioAnalyzer

# Add a monkey patch to debug XIRR calculation
original_calculate_xirr = PortfolioAnalyzer.calculate_xirr

def debug_calculate_xirr(self, dates, cash_flows):
    # Check if dates are sorted
    is_sorted = all(dates[i] <= dates[i+1] for i in range(len(dates)-1)) if len(dates) > 1 else True
    if not is_sorted:
        print(f"  WARNING: Dates NOT sorted!")
        print(f"    First 3: {dates[:3]}")
        print(f"    Last 3: {dates[-3:]}")
    result = original_calculate_xirr(self, dates, cash_flows)
    return result

PortfolioAnalyzer.calculate_xirr = debug_calculate_xirr

# Load trades
df = pd.read_csv('my_trades.csv', dtype={'symbol': str, 'shares': float, 'price': float})
df['purchase_date'] = pd.to_datetime(df['purchase_date']).dt.strftime('%Y-%m-%d')
df['symbol'] = df['symbol'].str.strip()
trades = df.to_dict('records')

analyzer = PortfolioAnalyzer(trades)
analysis = analyzer.analyze_portfolio()

print("\nPortfolio CAGR: {:.1f}%".format(analysis['portfolio_cagr']))
print("Portfolio XIRR: {:.1f}%".format(analysis['portfolio_xirr']))

symbol_stats = analyzer._calculate_symbol_accumulation(analysis['trades'])

print("\n\nSymbol-level check (NVDA):")
if 'NVDA' in symbol_stats:
    s = symbol_stats['NVDA']
    print(f"NVDA CAGR: {s['avg_cagr']:.2f}%")
    print(f"NVDA XIRR: {s['avg_xirr']:.2f}%")
