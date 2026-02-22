import pandas as pd
from stock import PortfolioAnalyzer

# Load trades
df = pd.read_csv('my_trades.csv', dtype={'symbol': str, 'shares': float, 'price': float})
df['purchase_date'] = pd.to_datetime(df['purchase_date']).dt.strftime('%Y-%m-%d')
df['symbol'] = df['symbol'].str.strip()
trades = df.to_dict('records')

analyzer = PortfolioAnalyzer(trades)
analysis = analyzer.analyze_portfolio()

print("PORTFOLIO LEVEL:")
print(f"  CAGR: {analysis['portfolio_cagr']:.1f}%")
print(f"  XIRR: {analysis['portfolio_xirr']:.1f}%")
print(f"  Difference: {analysis['portfolio_xirr'] - analysis['portfolio_cagr']:.1f}%")

symbol_stats = analyzer._calculate_symbol_accumulation(analysis['trades'])

print("\n\nSYMBOL LEVEL (symbol with multiple trades):")
symbols_to_check = ['NVDA', 'AAPL', 'MSFT', 'AMD', 'TSLA', 'ADBE']
for symbol in symbols_to_check:
    if symbol in symbol_stats:
        s = symbol_stats[symbol]
        if s['trades_count'] > 2:  # Multi-trade symbols
            print(f"\n{symbol} ({s['trades_count']} trades):")
            print(f"  CAGR: {s['avg_cagr']:.2f}%")
            print(f"  XIRR: {s['avg_xirr']:.2f}%")
            print(f"  Difference: {s['avg_xirr'] - s['avg_cagr']:.2f}%")
