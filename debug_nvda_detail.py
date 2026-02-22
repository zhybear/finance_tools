import pandas as pd
from stock import PortfolioAnalyzer

df = pd.read_csv('my_trades.csv', dtype={'symbol': str, 'shares': float, 'price': float})
df['purchase_date'] = pd.to_datetime(df['purchase_date']).dt.strftime('%Y-%m-%d')
df['symbol'] = df['symbol'].str.strip()
trades = df.to_dict('records')

analyzer = PortfolioAnalyzer(trades)
analysis = analyzer.analyze_portfolio()

# Now manually check NVDA trades
nvda_trades = [t for t in analysis['trades'] if t['symbol'] == 'NVDA']
print(f"NVDA has {len(nvda_trades)} trades in analysis\n")

# Get only NVDA trades in order
nvda_trades_sorted = sorted(nvda_trades, key=lambda t: t['purchase_date'])

print("NVDA purchases (sorted by date):")
total_cost = 0
for i, t in enumerate(nvda_trades_sorted):
    total_cost += t['initial_value']
    print(f"{i+1:2}. {t['purchase_date']}: ${t['initial_value']:>10,.0f}  (total invested so far: ${total_cost:>12,.0f})")

print(f"\nTotal invested in NVDA: ${total_cost:,.0f}")
print(f"Current value: ${nvda_trades[0]['current_value']:,.0f}")
print(f"Gain: ${nvda_trades[0]['current_value'] - total_cost:,.0f}")
print(f"Gain %: {((nvda_trades[0]['current_value'] / total_cost) - 1) * 100:.1f}%")

# Calculate CAGR manually
first_date = nvda_trades_sorted[0]['purchase_date']
nvda_trades_sorted[0]['purchase_date']
import datetime
last_date = "2026-02-20"
d1 = datetime.datetime.strptime(first_date, '%Y-%m-%d')
d2 = datetime.datetime.strptime(last_date, '%Y-%m-%d')
years = (d2 - d1).days / 365.25
cagr = (nvda_trades[0]['current_value'] / total_cost) ** (1 / years) - 1
print(f"\nManual CAGR calculation: {cagr*100:.1f}% over {years:.1f} years")
