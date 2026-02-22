"""Report generation module for portfolio analyzer.

Author: Zhuo Robert Li
"""

from typing import Optional, Dict, Any
import logging
from datetime import datetime
from .analyzer import PortfolioAnalyzer
from .utils import safe_divide

logger = logging.getLogger(__name__)

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    import seaborn as sns
    VISUALIZATIONS_AVAILABLE = True
except ImportError:
    VISUALIZATIONS_AVAILABLE = False


class TextReportGenerator:
    """Generates text-based portfolio reports."""
    
    @staticmethod
    def generate(analyzer: PortfolioAnalyzer, output_file: Optional[str] = None) -> None:
        """
        Generate text portfolio report.
        
        Args:
            analyzer: PortfolioAnalyzer instance
            output_file: Optional path to save report
        """
        analysis = analyzer.analyze_portfolio()

        if not analysis['trades']:
            print("No valid trades to analyze.")
            return

        symbol_stats = analyzer._calculate_symbol_accumulation(analysis['trades'])
        
        trades_by_symbol = {}
        for trade in analysis['trades']:
            symbol = trade['symbol']
            if symbol not in trades_by_symbol:
                trades_by_symbol[symbol] = []
            trades_by_symbol[symbol].append(trade)
        
        report_lines = []
        report_lines.append("\n=== INDIVIDUAL STOCK PERFORMANCE ===")
        
        for symbol in sorted(trades_by_symbol.keys()):
            trades = trades_by_symbol[symbol]
            symbol_data = symbol_stats[symbol]
            
            for trade in trades:
                report_lines.append(f"\n{trade['symbol']}:")
                report_lines.append(f"  Shares: {trade['shares']} @ ${trade['purchase_price']:.2f}")
                report_lines.append(f"  Current Price: ${trade['current_price']:.2f}")
                report_lines.append(f"  Initial Value: ${trade['initial_value']:.2f}")
                report_lines.append(f"  Current Value: ${trade['current_value']:.2f}")
                report_lines.append(f"  Gain: ${trade['current_value'] - trade['initial_value']:.2f}")
                report_lines.append(f"  Stock CAGR: {trade['stock_cagr']:.2f}%")
                report_lines.append(f"  Stock XIRR: {trade['stock_xirr']:.2f}%")
                report_lines.append(f"  S&P 500 CAGR: {trade['sp500_cagr']:.2f}%")
                report_lines.append(f"  S&P 500 XIRR: {trade['sp500_xirr']:.2f}%")
                report_lines.append(f"  Outperformance (CAGR): {trade['outperformance']:.2f}%")
                report_lines.append(f"  Outperformance (XIRR): {trade['xirr_outperformance']:.2f}%")
            
            report_lines.append(f"\n--- {symbol} ACCUMULATED ---")
            report_lines.append(f"  Total Trades: {symbol_data['trades_count']}")
            report_lines.append(f"  Total Shares: {symbol_data['total_shares']:.0f}")
            report_lines.append(f"  Total Initial Investment: ${symbol_data['total_initial_value']:.2f}")
            report_lines.append(f"  Total Current Value: ${symbol_data['total_current_value']:.2f}")
            report_lines.append(f"  Total Gain: ${symbol_data['total_gain']:.2f} ({symbol_data['gain_percentage']:.2f}%)")
            report_lines.append(f"  Expected S&P 500 Value: ${symbol_data['total_sp500_value']:.2f}")
            report_lines.append(f"  Outperformance vs S&P 500: ${symbol_data['outperformance']:.2f} ({symbol_data['outperformance_pct']:.2f}%)")
            report_lines.append(f"  Weighted Avg CAGR: {symbol_data['avg_cagr']:.2f}%")
            report_lines.append(f"  Weighted Avg XIRR: {symbol_data['avg_xirr']:.2f}%")
            report_lines.append(f"  Avg S&P 500 XIRR: {symbol_data['avg_sp500_xirr']:.2f}%")
            report_lines.append(f"  XIRR Outperformance: {symbol_data['xirr_outperformance_pct']:.2f}%")
            report_lines.append(f"  Weighted Avg Years Held: {symbol_data['avg_years_held']:.2f} years")

        report_lines.append("\n=== PORTFOLIO SUMMARY ===")
        report_lines.append(f"Initial Investment: ${analysis['total_initial_value']:.2f}")
        report_lines.append(f"Current Value: ${analysis['total_current_value']:.2f}")
        report_lines.append(f"Total Gain: ${analysis['total_current_value'] - analysis['total_initial_value']:.2f}")
        report_lines.append(f"Expected Value if Invested in S&P 500: ${analysis['total_sp500_current_value']:.2f}")
        report_lines.append(f"\nPortfolio CAGR: {analysis['portfolio_cagr']:.2f}%")
        report_lines.append(f"Portfolio XIRR: {analysis.get('portfolio_xirr', 0.0):.2f}%")
        report_lines.append(f"S&P 500 CAGR: {analysis['sp500_cagr']:.2f}%")
        report_lines.append(f"S&P 500 XIRR: {analysis.get('sp500_xirr', 0.0):.2f}%")
        report_lines.append(f"\nPortfolio Outperformance (CAGR): {analysis['portfolio_outperformance']:.2f}%")
        report_lines.append(f"Portfolio Outperformance (XIRR): {analysis.get('portfolio_xirr_outperformance', 0.0):.2f}%")
        
        for line in report_lines:
            print(line)
        
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write('\n'.join(report_lines))
                print(f"\n✅ Report saved to: {output_file}")
            except Exception as e:
                print(f"\n⚠️  Error saving report to file: {e}")


class PDFReportGenerator:
    """Generates PDF portfolio reports with visualizations."""
    
    @staticmethod
    def generate(analyzer: PortfolioAnalyzer, pdf_path: str) -> None:
        """
        Generate PDF  report with visualizations.
        
        Args:
            analyzer: PortfolioAnalyzer instance
            pdf_path: Path to save PDF file
        """
        if not VISUALIZATIONS_AVAILABLE:
            print("⚠️  Visualization libraries not available. Install with:")
            print("   pip3 install matplotlib seaborn")
            return
        
        try:
            from matplotlib.backends.backend_pdf import PdfPages
            
            analysis = analyzer.analyze_portfolio()
            if not analysis['trades']:
                print("No valid trades to analyze.")
                return
            
            symbol_stats = analyzer._calculate_symbol_accumulation(analysis['trades'])
            pdf_data = analyzer._prepare_pdf_data(analysis, symbol_stats) if hasattr(analyzer, '_prepare_pdf_data') else PDFReportGenerator._prepare_pdf_data(symbol_stats, analysis)
            
            with PdfPages(pdf_path) as pdf:
                # Just create a simple PDF for now
                fig = plt.figure(figsize=(11, 8.5))
                fig.suptitle('Portfolio Performance Report', fontsize=16, fontweight='bold')
                ax = fig.add_subplot(111)
                ax.axis('off')
                
                table_data = [['Symbol', 'Trades', 'Invested', 'Current', 'Gain', 'Gain%', 'CAGR%', 'XIRR%']]
                top_10 = sorted(symbol_stats.items(), key=lambda x: x[1]['total_current_value'], reverse=True)[:10]
                
                for symbol, stats in top_10:
                    table_data.append([
                        symbol,
                        f"{stats['trades_count']}",
                        f"${stats['total_initial_value']:.0f}",
                        f"${stats['total_current_value']:.0f}",
                        f"${stats['total_gain']:.0f}",
                        f"{stats['gain_percentage']:.1f}%",
                        f"{stats['avg_cagr']:.1f}%",
                        f"{stats['avg_xirr']:.1f}%"
                    ])
                
                table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                               colWidths=[0.1, 0.1, 0.13, 0.13, 0.13, 0.13, 0.13, 0.13])
                table.auto_set_font_size(False)
                table.set_fontsize(10)
                table.scale(1, 2)
                
                for i in range(len(table_data[0])):
                    table[(0, i)].set_facecolor('#4CAF50')
                    table[(0, i)].set_text_props(weight='bold', color='white')
                
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)
            
            print(f"✅ PDF report generated: {pdf_path}")
        except Exception as e:
            print(f"⚠️  Error generating PDF: {e}")
    
    @staticmethod
    def _prepare_pdf_data(symbol_stats: Dict, analysis: Dict) -> Dict:
        """Prepare data for PDF visualization."""
        return {
            'top_10_value': sorted(symbol_stats.items(), 
                                  key=lambda x: x[1]['total_current_value'], reverse=True)[:10],
            'top_8_cagr': sorted(symbol_stats.items(), 
                                key=lambda x: x[1]['avg_cagr'], reverse=True)[:8],
            'top_8_xirr': sorted(symbol_stats.items(), 
                                key=lambda x: x[1]['avg_xirr'], reverse=True)[:8],
            'top_8_gain': sorted(symbol_stats.items(), 
                                key=lambda x: x[1]['total_gain'], reverse=True)[:8],
        }


class HTMLReportGenerator:
    """Generates interactive HTML portfolio dashboards."""
    
    @staticmethod
    def generate(analyzer: PortfolioAnalyzer, html_path: str) -> None:
        """
        Generate interactive HTML dashboard report.
        
        Args:
            analyzer: PortfolioAnalyzer instance
            html_path: Path to save HTML file
        """
        try:
            analysis = analyzer.analyze_portfolio()
            if not analysis['trades']:
                print("No valid trades to analyze.")
                return
            
            symbol_stats = analyzer._calculate_symbol_accumulation(analysis['trades'])
            
            # Build minimal HTML with essential metrics
            cagr = analysis['portfolio_cagr']
            xirr = analysis.get('portfolio_xirr', 0.0)
            total_gain = analysis['total_current_value'] - analysis['total_initial_value']
            gain_pct = safe_divide(total_gain, analysis['total_initial_value'], 0.0) * 100
            
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Analytics Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }}
        .metric-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric-label {{ color: #666; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; }}
        .metric-value {{ font-size: 2rem; font-weight: 700; color: #333; margin-top: 10px; }}
        .positive {{ color: #10b981; }}
        .negative {{ color: #ef4444; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        th {{ background: #f5f5f5; padding: 15px; text-align: left; font-weight: 600; border-bottom: 2px solid #0066cc; }}
        td {{ padding: 12px 15px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f9f9f9; }}
        .section {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h2 {{ margin-top: 0; color: #333; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }}
        .number {{ font-family: monospace; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Portfolio Analytics Dashboard</h1>
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-label">Portfolio Value</div>
                <div class="metric-value">${analysis['total_current_value']:,.0f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Gain</div>
                <div class="metric-value {('positive' if total_gain >= 0 else 'negative')}">${total_gain:,.0f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Return %</div>
                <div class="metric-value {('positive' if gain_pct >= 0 else 'negative')}">{gain_pct:.1f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">CAGR</div>
                <div class="metric-value {('positive' if cagr >= 0 else 'negative')}">{cagr:.1f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">XIRR</div>
                <div class="metric-value {('positive' if xirr >= 0 else 'negative')}">{xirr:.1f}%</div>
            </div>
        </div>
        
        <div class="section">
            <h2>All Positions</h2>
            <table>
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Trades</th>
                        <th>Invested</th>
                        <th>Current Value</th>
                        <th>Gain</th>
                        <th>Return %</th>
                        <th>CAGR %</th>
                        <th>XIRR %</th>
                    </tr>
                </thead>
                <tbody>
"""
            
            sorted_symbols = sorted(symbol_stats.items(), 
                                   key=lambda x: x[1]['total_current_value'], 
                                   reverse=True)
            for symbol, stats in sorted_symbols:
                html_content += f"""
                    <tr>
                        <td><strong>{symbol}</strong></td>
                        <td class="number">{stats['trades_count']}</td>
                        <td class="number">${stats['total_initial_value']:,.0f}</td>
                        <td class="number">${stats['total_current_value']:,.0f}</td>
                        <td class="number {'positive' if stats['total_gain'] >= 0 else 'negative'}">${stats['total_gain']:,.0f}</td>
                        <td class="number {'positive' if stats['gain_percentage'] >= 0 else 'negative'}">{stats['gain_percentage']:.1f}%</td>
                        <td class="number {'positive' if stats['avg_cagr'] >= 0 else 'negative'}">{stats['avg_cagr']:.1f}%</td>
                        <td class="number {'positive' if stats['avg_xirr'] >= 0 else 'negative'}">{stats['avg_xirr']:.1f}%</td>
                    </tr>
"""
            
            html_content += """
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""
            
            with open(html_path, 'w') as f:
                f.write(html_content)
            
            print(f"✅ HTML report generated: {html_path}")
        except Exception as e:
            print(f"⚠️  Error generating HTML: {e}")
