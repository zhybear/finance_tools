import pandas as pd
from stock import PortfolioAnalyzer

# Monkey patch to debug
original_XIRR = PortfolioAnalyzer.calculate_xirr

count = [0]  # counter

def debug_xirr(self, dates, cash_flows):
    count[0] += 1
    # Show MULTI-cashflow calls (3+ flows)
    if len(dates) >= 3:
        dates_sorted = all(dates[i] <= dates[i+1] for i in range(len(dates)-1)) if len(dates) > 1 else True
        print(f"\nXIRR Call #{count[0]}: {len(dates)} cash flows, sorted={dates_sorted}")
        print(f"  Dates: {dates[0]} ... {dates[-1]}")
        print(f"  Cash flows: {cash_flows[0]:,.0f} ... {cash_flows[-1]:,.0f}")
        result = original_XIRR(self, dates, cash_flows)
        print(f"  → XIRR = {result:.2f}%")
        return result
    else:
        return original_XIRR(self, dates, cash_flows)

PortfolioAnalyzer.calculate_xirr = debug_xirr

df = pd.read_csv('my_trades.csv', dtype={'symbol': str, 'shares': float, 'price': float})
df['purchase_date'] = pd.to_datetime(df['purchase_date']).dt.strftime('%Y-%m-%d')
df['symbol'] = df['symbol'].str.strip()
trades = df.to_dict('records')

analyzer = PortfolioAnalyzer(trades)
print("Calculating portfolio analysis...")
analysis = analyzer.analyze_portfolio()

print(f"\n\nFINAL\nPortfolio CAGR: {analysis['portfolio_cagr']:.1f}%")
print(f"Portfolio XIRR: {analysis['portfolio_xirr']:.1f}%")

print("\nCalculating symbol stats...")
symbol_stats = analyzer._calculate_symbol_accumulation(analysis['trades'])

print(f"\n\nNVDA Symbol-level:")
print(f"  CAGR: {symbol_stats['NVDA']['avg_cagr']:.1f}%")
print(f"  XIRR: {symbol_stats['NVDA']['avg_xirr']:.1f}%")
