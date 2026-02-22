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

# Sum all trades
total_initial = sum(t['initial_value'] for t in nvda_trades)
total_current = sum(t['current_value'] for t in nvda_trades)

print(f"Total invested in NVDA: ${total_initial:,.0f}")
print(f"Total current value: ${total_current:,.0f}")
print(f"Total gain: ${total_current - total_initial:,.0f}")
print(f"Total gain %: {((total_current / total_initial) - 1) * 100:.1f}%")

# Calculate CAGR manually 
first_date = min(t['purchase_date'] for t in nvda_trades)
last_date = "2026-02-20"
import datetime
d1 = datetime.datetime.strptime(first_date, '%Y-%m-%d')
d2 = datetime.datetime.strptime(last_date, '%Y-%m-%d')
years = (d2 - d1).days / 365.25
cagr = (total_current / total_initial) ** (1 / years) - 1
print(f"\nManual CAGR calculation: {cagr*100:.1f}% over {years:.1f} years")

# But the reported metric is different - let's see what's reported
symbol_stats = analyzer._calculate_symbol_accumulation(analysis['trades'])
nvda_stat = symbol_stats['NVDA']
print(f"\nReported metrics from code:")
print(f"  CAGR: {nvda_stat['avg_cagr']:.1f}%")
print(f"  XIRR: {nvda_stat['avg_xirr']:.1f}%")
print(f"  Total current value (code): ${nvda_stat['total_current_value']:,.0f}")
print(f"  Total initial value (code): ${nvda_stat['total_initial_value']:,.0f}")
