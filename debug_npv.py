import pandas as pd
from stock import PortfolioAnalyzer
import datetime

df = pd.read_csv('my_trades.csv', dtype={'symbol': str, 'shares': float, 'price': float})
df['purchase_date'] = pd.to_datetime(df['purchase_date']).dt.strftime('%Y-%m-%d')
df['symbol'] = df['symbol'].str.strip()
trades = df.to_dict('records')

analyzer = PortfolioAnalyzer(trades)
analysis = analyzer.analyze_portfolio()

# Get NVDA trades
nvda_trades = sorted(
    [t for t in analysis['trades'] if t['symbol'] == 'NVDA'],
    key=lambda t: t['purchase_date']
)

# Prepare cash flows
dates = [t['purchase_date'] for t in nvda_trades]
cash_flows = [-t['initial_value'] for t in nvda_trades]
current_val = sum(t['current_value'] for t in nvda_trades)

dates.append("2026-02-20")
cash_flows.append(current_val)

# Verify: Check NPV at both CAGR and reported XIRR

def calculate_npv(rate, dates, cash_flows):
    """Calculate NPV at given rate"""
    npv = 0
    base_date = pd.to_datetime(dates[0])
    for d, cf in zip(dates, cash_flows):
        d_parsed = pd.to_datetime(d)
        years = (d_parsed - base_date).days / 365.25
        npv += cf / ((1 + rate) ** years)
    return npv

cagr = 0.283
xirr = 0.494

npv_at_cagr = calculate_npv(cagr, dates, cash_flows)
npv_at_xirr = calculate_npv(xirr, dates, cash_flows)

print(f"NVDA Cash flows (first & last):")
print(f"  Dates: {dates[0]} ... {dates[-1]}")
print(f"  CFs:   ${cash_flows[0]:,.0f} ... ${cash_flows[-1]:,.0f}")
print(f"  Total trades: {len(dates)} cash flows\n")

print(f"NPV Analysis:")
print(f"  At CAGR = 28.3%: NPV = ${npv_at_cagr:,.0f}")
print(f"  At XIRR = 49.4%: NPV = ${npv_at_xirr:,.0f}")
print(f"\nExpected: XIRR's NPV should be ≈ $0, CAGR's NPV should NOT be $0")
print(f"\nInterpretation:")
if abs(npv_at_xirr) < 1000 and abs(npv_at_cagr) > 1000:
    print(f"  ✓ XIRR is mathematically correct (NPV ≈ 0)")
    print(f"  → XIRR can legitimately differ from CAGR for multi-purchase portfolios")
else:
    print(f"  ⚠️ Something is wrong - both NPVs are non-zero")
    print(f"  → Possible numerical solver issue")
