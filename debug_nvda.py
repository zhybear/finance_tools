import pandas as pd
from stock import PortfolioAnalyzer

# Load trades
df = pd.read_csv('my_trades.csv', dtype={'symbol': str, 'shares': float, 'price': float})
df['purchase_date'] = pd.to_datetime(df['purchase_date']).dt.strftime('%Y-%m-%d')
df['symbol'] = df['symbol'].str.strip()
trades = df.to_dict('records')

# Debug NVDA specifically
nvda_trades = [t for t in trades if t['symbol'] == 'NVDA']
print(f"NVDA trades ({len(nvda_trades)} total):")
print("\nPurchase dates in order:")
for i, t in enumerate(nvda_trades):
    print(f"  {i+1}. {t['purchase_date']} - {t['shares']} shares @ ${t['price']}")

# Now sort them
dates = [pd.to_datetime(t['purchase_date']).date() for t in nvda_trades]
print(f"\nDates (as loaded): {dates[:5]}  ... (unsorted?)")

# Check if sorted
is_sorted = all(dates[i] <= dates[i+1] for i in range(len(dates)-1))
print(f"Are dates sorted? {is_sorted}")

sorted_dates = sorted(dates)
print(f"Dates (sorted): {sorted_dates[:5]}  ...")

if dates != sorted_dates:
    print("\n⚠️  DATES ARE OUT OF ORDER - this would cause spurious roots!")
