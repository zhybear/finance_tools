import pandas as pd
from stock import PortfolioAnalyzer

# Monkey patch to debug
original_XIRR = PortfolioAnalyzer.calculate_xirr

count = [0]  # counter

def debug_xirr(self, dates, cash_flows):
    count[0] += 1
    if count[0] <= 15:  # Only show first few calls
        dates_sorted = all(dates[i] <= dates[i+1] for i in range(len(dates)-1)) if len(dates) > 1 else True
        print(f"\nXIRR Call #{count[0]}: {len(dates)} cash flows, sorted={dates_sorted}")
        if len(dates) <= 5:
            for i, (d,cf) in enumerate(zip(dates, cash_flows)):
                print(f"  {d}: ${cf:,.0f}")
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
analysis = analyzer.analyze_portfolio()

print(f"\n\nFINAL Portfolio CAGR: {analysis['portfolio_cagr']:.1f}%, XIRR: {analysis['portfolio_xirr']:.1f}%")
