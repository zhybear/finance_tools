"""Report generation module for portfolio analyzer.

Author: Zhuo Robert Li
Version: 1.3.4
"""

from typing import Optional, Dict, Any, List, Tuple
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

# Color constants
COLOR_POSITIVE = '#10b981'
COLOR_NEGATIVE = '#ef4444'
COLOR_NEUTRAL = '#9ca3af'

def get_performance_color(value: float) -> str:
    """Get color based on performance value."""
    return COLOR_POSITIVE if value >= 0 else COLOR_NEGATIVE

def calculate_win_loss_stats(symbol_stats: Dict) -> Tuple[int, int, int]:
    """Calculate winning, losing, and breakeven position counts.
    
    Returns:
        Tuple of (winning_count, losing_count, breakeven_count)
    """
    winning = sum(1 for s in symbol_stats.values() if s['total_gain'] > 0)
    losing = sum(1 for s in symbol_stats.values() if s['total_gain'] < 0)
    breakeven = sum(1 for s in symbol_stats.values() if s['total_gain'] == 0)
    return winning, losing, breakeven


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
                report_lines.append(f"  Stock WCAGR: {trade['stock_cagr']:.2f}%")
                report_lines.append(f"  Stock XIRR: {trade['stock_xirr']:.2f}%")
                report_lines.append(f"  S&P 500 WCAGR: {trade['sp500_cagr']:.2f}%")
                report_lines.append(f"  S&P 500 XIRR: {trade['sp500_xirr']:.2f}%")
                report_lines.append(f"  Outperformance (WCAGR): {trade['outperformance']:.2f}%")
                report_lines.append(f"  Outperformance (XIRR): {trade['xirr_outperformance']:.2f}%")
            
            report_lines.append(f"\n--- {symbol} ACCUMULATED ---")
            report_lines.append(f"  Total Trades: {symbol_data['trades_count']}")
            report_lines.append(f"  Total Shares: {symbol_data['total_shares']:.0f}")
            report_lines.append(f"  Total Initial Investment: ${symbol_data['total_initial_value']:.2f}")
            report_lines.append(f"  Total Current Value: ${symbol_data['total_current_value']:.2f}")
            report_lines.append(f"  Total Gain: ${symbol_data['total_gain']:.2f} ({symbol_data['gain_percentage']:.2f}%)")
            report_lines.append(f"  Expected S&P 500 Value: ${symbol_data['total_sp500_value']:.2f}")
            report_lines.append(f"  Outperformance vs S&P 500: ${symbol_data['outperformance']:.2f} ({symbol_data['outperformance_pct']:.2f}%)")
            report_lines.append(f"  WCAGR: {symbol_data['avg_cagr']:.2f}%")
            report_lines.append(f"  Weighted Avg XIRR: {symbol_data['avg_xirr']:.2f}%")
            report_lines.append(f"  S&P 500 WCAGR: {symbol_data['avg_sp500_cagr']:.2f}%")
            report_lines.append(f"  S&P 500 XIRR: {symbol_data['avg_sp500_xirr']:.2f}%")
            report_lines.append(f"  XIRR Outperformance: {symbol_data['xirr_outperformance_pct']:.2f}%")
            report_lines.append(f"  Weighted Avg Years Held: {symbol_data['avg_years_held']:.2f} years")

        report_lines.append("\n=== PORTFOLIO SUMMARY ===")
        report_lines.append(f"Initial Investment: ${analysis['total_initial_value']:.2f}")
        report_lines.append(f"Current Value: ${analysis['total_current_value']:.2f}")
        report_lines.append(f"Total Gain: ${analysis['total_current_value'] - analysis['total_initial_value']:.2f}")
        report_lines.append(f"Expected Value if Invested in S&P 500: ${analysis['total_sp500_current_value']:.2f}")
        report_lines.append(f"\nPortfolio WCAGR: {analysis['portfolio_cagr']:.2f}%")
        report_lines.append(f"Portfolio XIRR: {analysis.get('portfolio_xirr', 0.0):.2f}%")
        report_lines.append(f"S&P 500 WCAGR: {analysis['sp500_cagr']:.2f}%")
        report_lines.append(f"S&P 500 XIRR: {analysis.get('sp500_xirr', 0.0):.2f}%")
        report_lines.append(f"\nPortfolio Outperformance (WCAGR): {analysis['portfolio_outperformance']:.2f}%")
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
        Generate PDF report with visualizations and tables.
        
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
            pdf_data = PDFReportGenerator._prepare_pdf_data(symbol_stats, analysis)
            
            with PdfPages(pdf_path) as pdf:
                # Page 1: Summary metrics and top holdings
                fig = plt.figure(figsize=(11, 8.5))
                fig.suptitle('Portfolio Performance Report', fontsize=18, fontweight='bold', y=0.98)
                
                # Create grid for layout
                gs = fig.add_gridspec(3, 2, hspace=0.4, wspace=0.3, 
                                     top=0.92, bottom=0.05, left=0.08, right=0.95)
                
                # Summary metrics table (top)
                ax1 = fig.add_subplot(gs[0, :])
                ax1.axis('off')
                ax1.text(0.5, 1.0, 'Portfolio Summary', ha='center', va='top', 
                        fontsize=14, fontweight='bold', transform=ax1.transAxes)
                
                summary_data = [
                    ['Initial Investment', f"${analysis['total_initial_value']:,.2f}"],
                    ['Current Value', f"${analysis['total_current_value']:,.2f}"],
                    ['Total Gain/Loss', f"${analysis['total_current_value'] - analysis['total_initial_value']:,.2f}"],
                    ['Portfolio WCAGR', f"{analysis['portfolio_cagr']:.2f}%"],
                    ['Portfolio XIRR', f"{analysis.get('portfolio_xirr', 0):.2f}%"],
                    ['S&P 500 WCAGR', f"{analysis['sp500_cagr']:.2f}%"],
                    ['S&P 500 XIRR', f"{analysis.get('sp500_xirr', 0):.2f}%"],
                    ['Outperformance', f"{analysis.get('portfolio_xirr_outperformance', 0):.2f}%"]
                ]
                
                summary_table = ax1.table(cellText=summary_data, cellLoc='left', loc='center',
                                         colWidths=[0.4, 0.3], bbox=[0.1, 0, 0.8, 0.85])
                summary_table.auto_set_font_size(False)
                summary_table.set_fontsize(11)
                summary_table.scale(1, 1.8)
                
                for i in range(len(summary_data)):
                    summary_table[(i, 0)].set_facecolor('#f0f0f0')
                    summary_table[(i, 0)].set_text_props(weight='bold')
                
                # Top 10 holdings by value table
                ax2 = fig.add_subplot(gs[1:, 0])
                ax2.axis('off')
                ax2.text(0.5, 1.05, 'Top 10 Holdings by Value', ha='center', 
                        fontsize=12, fontweight='bold', transform=ax2.transAxes)
                
                table_data = [['Symbol', 'Value', 'Gain%', 'XIRR%']]
                for symbol, stats in pdf_data['top_10_value']:
                    table_data.append([
                        symbol,
                        f"${stats['total_current_value']:,.0f}",
                        f"{stats['gain_percentage']:.1f}%",
                        f"{stats['avg_xirr']:.1f}%"
                    ])
                
                holdings_table = ax2.table(cellText=table_data, cellLoc='center', loc='center',
                                          colWidths=[0.2, 0.3, 0.25, 0.25])
                holdings_table.auto_set_font_size(False)
                holdings_table.set_fontsize(9)
                holdings_table.scale(1, 1.5)
                
                # Header formatting
                for i in range(len(table_data[0])):
                    holdings_table[(0, i)].set_facecolor('#4CAF50')
                    holdings_table[(0, i)].set_text_props(weight='bold', color='white')
                
                # Top 8 by XIRR chart
                ax3 = fig.add_subplot(gs[1:, 1])
                top_xirr = pdf_data['top_8_xirr']
                symbols = [s[0] for s in top_xirr]
                xirrs = [s[1]['avg_xirr'] for s in top_xirr]
                colors = [get_performance_color(x) for x in xirrs]
                
                ax3.barh(symbols, xirrs, color=colors, alpha=0.7)
                ax3.set_xlabel('XIRR (%)', fontweight='bold')
                ax3.set_title('Top 8 Performers by XIRR', fontweight='bold', pad=15)
                ax3.grid(axis='x', alpha=0.3, linestyle='--')
                ax3.axvline(x=0, color='black', linewidth=0.8)
                
                # Add value labels
                for i, (symbol, xirr) in enumerate(zip(symbols, xirrs)):
                    ax3.text(xirr, i, f' {xirr:.1f}%', va='center', 
                            ha='left' if xirr >= 0 else 'right', fontsize=8)
                
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)
                
                # Page 2: Detailed charts
                fig2 = plt.figure(figsize=(11, 8.5))
                fig2.suptitle('Portfolio Analysis - Detailed Metrics', fontsize=18, fontweight='bold', y=0.98)
                
                gs2 = fig2.add_gridspec(2, 2, hspace=0.35, wspace=0.3,
                                       top=0.92, bottom=0.08, left=0.08, right=0.95)
                
                # Top gains by dollar amount
                ax4 = fig2.add_subplot(gs2[0, 0])
                top_gains = pdf_data['top_8_gain']
                symbols_gain = [s[0] for s in top_gains]
                gains = [s[1]['total_gain'] for s in top_gains]
                colors_gain = [get_performance_color(g) for g in gains]
                
                ax4.barh(symbols_gain, gains, color=colors_gain, alpha=0.7)
                ax4.set_xlabel('Gain/Loss ($)', fontweight='bold')
                ax4.set_title('Top 8 by Dollar Gain/Loss', fontweight='bold', pad=15)
                ax4.grid(axis='x', alpha=0.3, linestyle='--')
                ax4.axvline(x=0, color='black', linewidth=0.8)
                
                for i, (symbol, gain) in enumerate(zip(symbols_gain, gains)):
                    ax4.text(gain, i, f' ${gain:,.0f}', va='center',
                            ha='left' if gain >= 0 else 'right', fontsize=8)
                
                # Top by WCAGR
                ax5 = fig2.add_subplot(gs2[0, 1])
                top_cagr = pdf_data['top_8_cagr']
                symbols_cagr = [s[0] for s in top_cagr]
                cagrs = [s[1]['avg_cagr'] for s in top_cagr]
                colors_cagr = [get_performance_color(c) for c in cagrs]
                
                ax5.barh(symbols_cagr, cagrs, color=colors_cagr, alpha=0.7)
                ax5.set_xlabel('WCAGR (%)', fontweight='bold')
                ax5.set_title('Top 8 by WCAGR', fontweight='bold', pad=15)
                ax5.grid(axis='x', alpha=0.3, linestyle='--')
                ax5.axvline(x=0, color='black', linewidth=0.8)
                
                for i, (symbol, cagr) in enumerate(zip(symbols_cagr, cagrs)):
                    ax5.text(cagr, i, f' {cagr:.1f}%', va='center',
                            ha='left' if cagr >= 0 else 'right', fontsize=8)
                
                # Portfolio allocation pie chart
                ax6 = fig2.add_subplot(gs2[1, 0])
                top_5_alloc = pdf_data['top_10_value'][:5]
                sizes = [s[1]['total_current_value'] for s in top_5_alloc]
                labels = [s[0] for s in top_5_alloc]
                
                # Add "Others" category
                total_top5 = sum(sizes)
                total_value = analysis['total_current_value']
                if total_value > total_top5:
                    sizes.append(total_value - total_top5)
                    labels.append('Others')
                
                colors_pie = plt.cm.Set3(range(len(sizes)))
                ax6.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                       colors=colors_pie, textprops={'fontsize': 9})
                ax6.set_title('Portfolio Allocation (Top 5)', fontweight='bold', pad=15)
                
                # Win/Loss distribution
                ax7 = fig2.add_subplot(gs2[1, 1])
                winning, losing, breakeven = calculate_win_loss_stats(symbol_stats)
                
                categories = ['Winners', 'Losers', 'Breakeven']
                counts = [winning, losing, breakeven]
                colors_bar = [COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_NEUTRAL]
                
                bars = ax7.bar(categories, counts, color=colors_bar, alpha=0.7)
                ax7.set_ylabel('Number of Positions', fontweight='bold')
                ax7.set_title('Win/Loss Distribution', fontweight='bold', pad=15)
                ax7.grid(axis='y', alpha=0.3, linestyle='--')
                
                # Add count labels on bars
                for bar, count in zip(bars, counts):
                    height = bar.get_height()
                    ax7.text(bar.get_x() + bar.get_width()/2., height,
                            f'{int(count)}', ha='center', va='bottom', fontweight='bold')
                
                pdf.savefig(fig2, bbox_inches='tight')
                plt.close(fig2)
            
            print(f"✅ PDF report generated: {pdf_path}")
        except Exception as e:
            print(f"⚠️  Error generating PDF: {e}")
            import traceback
            traceback.print_exc()
    
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
    """Generates interactive HTML portfolio dashboards with Plotly charts."""
    
    @staticmethod
    def generate(analyzer: PortfolioAnalyzer, html_path: str) -> None:
        """
        Generate interactive HTML dashboard report with visualizations.
        
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
            sorted_symbols = sorted(symbol_stats.items(), 
                                   key=lambda x: x[1]['total_current_value'], 
                                   reverse=True)
            
            # Group trades by symbol for detail view
            trades_by_symbol = {}
            for trade in analysis['trades']:
                symbol = trade['symbol']
                if symbol not in trades_by_symbol:
                    trades_by_symbol[symbol] = []
                trades_by_symbol[symbol].append(trade)
            
            # Calculate metrics
            cagr = analysis['portfolio_cagr']
            xirr = analysis.get('portfolio_xirr', 0.0)
            sp500_wcagr = analysis['sp500_cagr']
            sp500_xirr_val = analysis.get('sp500_xirr', 0.0)
            total_gain = analysis['total_current_value'] - analysis['total_initial_value']
            gain_pct = safe_divide(total_gain, analysis['total_initial_value'], 0.0) * 100
            
            # Generate Plotly charts
            charts_html = ""
            
            try:
                import plotly.graph_objects as go
                from plotly.subplots import make_subplots
                
                # Chart 1: Top 10 Holdings by Value
                top_10 = sorted_symbols[:10]
                fig1 = go.Figure(data=[
                    go.Bar(
                        x=[s[1]['total_current_value'] for s in top_10],
                        y=[s[0] for s in top_10],
                        orientation='h',
                        marker=dict(
                            color=[s[1]['total_gain'] for s in top_10],
                            colorscale='RdYlGn',
                            showscale=True,
                            colorbar=dict(title="Gain ($)")
                        ),
                        text=[f"${s[1]['total_current_value']:,.0f}" for s in top_10],
                        textposition='outside',
                        textfont=dict(size=10),
                        hovertemplate='<b>%{y}</b><br>Value: $%{x:,.2f}<br>Gain: $%{marker.color:,.2f}<extra></extra>'
                    )
                ])
                fig1.update_layout(
                    title='Top 10 Holdings by Current Value',
                    xaxis_title='Current Value ($)',
                    yaxis_title='Symbol',
                    height=500,
                    template='plotly_white',
                    showlegend=False,
                    margin=dict(l=80, r=150, t=60, b=60)
                )
                charts_html += f'<div class="chart-container"><div id="chart1"></div></div>'
                chart1_json = fig1.to_json()
                
                # Chart 2: Top 10 by XIRR Performance
                top_xirr = sorted(symbol_stats.items(), key=lambda x: x[1]['avg_xirr'], reverse=True)[:10]
                fig2 = go.Figure(data=[
                    go.Bar(
                        x=[s[0] for s in top_xirr],
                        y=[s[1]['avg_xirr'] for s in top_xirr],
                        marker=dict(
                            color=[s[1]['avg_xirr'] for s in top_xirr],
                            colorscale='RdYlGn',
                            showscale=False
                        ),
                        text=[f"{s[1]['avg_xirr']:.1f}%" for s in top_xirr],
                        textposition='outside',
                        textfont=dict(size=11, weight='bold'),
                        hovertemplate='<b>%{x}</b><br>XIRR: %{y:.2f}%<extra></extra>'
                    )
                ])
                fig2.update_layout(
                    title='Top 10 Performers by XIRR',
                    xaxis_title='Symbol',
                    yaxis_title='XIRR (%)',
                    height=500,
                    template='plotly_white',
                    showlegend=False,
                    margin=dict(l=60, r=60, t=60, b=80)
                )
                charts_html += f'<div class="chart-container"><div id="chart2"></div></div>'
                chart2_json = fig2.to_json()
                
                # Chart 3: Portfolio Allocation Pie Chart
                top_8_value = sorted_symbols[:8]
                values = [s[1]['total_current_value'] for s in top_8_value]
                labels = [s[0] for s in top_8_value]
                
                total_top8 = sum(values)
                total_value = analysis['total_current_value']
                if total_value > total_top8:
                    values.append(total_value - total_top8)
                    labels.append('Others')
                
                fig3 = go.Figure(data=[
                    go.Pie(
                        labels=labels,
                        values=values,
                        hole=0.3,
                        hovertemplate='<b>%{label}</b><br>Value: $%{value:,.2f}<br>%{percent}<extra></extra>',
                        textinfo='label+percent',
                        textfont=dict(size=12)
                    )
                ])
                fig3.update_layout(
                    title='Portfolio Allocation by Value',
                    height=500,
                    template='plotly_white',
                    margin=dict(l=20, r=20, t=60, b=20)
                )
                charts_html += f'<div class="chart-container"><div id="chart3"></div></div>'
                chart3_json = fig3.to_json()
                
                # Chart 4: XIRR vs WCAGR Scatter
                fig4 = go.Figure(data=[
                    go.Scatter(
                        x=[s[1]['avg_xirr'] for s in sorted_symbols],
                        y=[s[1]['avg_cagr'] for s in sorted_symbols],
                        mode='markers',
                        marker=dict(
                            size=[max(5, min(50, s[1]['total_current_value']/1000)) for s in sorted_symbols],
                            color=[s[1]['total_gain'] for s in sorted_symbols],
                            colorscale='RdYlGn',
                            showscale=True,
                            colorbar=dict(title="Gain ($)"),
                            line=dict(width=1, color='white')
                        ),
                        text=[s[0] for s in sorted_symbols],
                        hovertemplate='<b>%{text}</b><br>XIRR: %{x:.2f}%<br>WCAGR: %{y:.2f}%<br>Gain: $%{marker.color:,.2f}<extra></extra>'
                    )
                ])
                
                # Add diagonal reference line
                all_xirr = [s[1]['avg_xirr'] for s in sorted_symbols]
                all_cagr = [s[1]['avg_cagr'] for s in sorted_symbols]
                min_val = min(min(all_xirr), min(all_cagr))
                max_val = max(max(all_xirr), max(all_cagr))
                fig4.add_trace(go.Scatter(
                    x=[min_val, max_val],
                    y=[min_val, max_val],
                    mode='lines',
                    line=dict(dash='dash', color='gray', width=1),
                    showlegend=False,
                    hoverinfo='skip',
                    name='x=y'
                ))
                
                fig4.update_layout(
                    title='XIRR vs WCAGR Performance (Bubble Size = Position Value)',
                    xaxis_title='XIRR (%)',
                    yaxis_title='WCAGR (%)',
                    height=500,
                    template='plotly_white',
                    showlegend=False,
                    margin=dict(l=60, r=100, t=60, b=60)
                )
                charts_html += f'<div class="chart-container"><div id="chart4"></div></div>'
                chart4_json = fig4.to_json()
                
                # Chart 5: Win/Loss Distribution
                winning, losing, breakeven = calculate_win_loss_stats(symbol_stats)
                
                fig5 = go.Figure(data=[
                    go.Bar(
                        x=['Winners', 'Losers', 'Breakeven'],
                        y=[winning, losing, breakeven],
                        marker=dict(color=[COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_NEUTRAL]),
                        text=[winning, losing, breakeven],
                        textposition='outside',
                        textfont=dict(size=14, weight='bold'),
                        hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
                    )
                ])
                fig5.update_layout(
                    title='Win/Loss Distribution',
                    xaxis_title='Category',
                    yaxis_title='Number of Positions',
                    height=400,
                    template='plotly_white',
                    showlegend=False,
                    margin=dict(l=60, r=60, t=60, b=60)
                )
                charts_html += f'<div class="chart-container"><div id="chart5"></div></div>'
                chart5_json = fig5.to_json()
                
                # Generate chart rendering JavaScript
                charts_script = f"""
<script>
    Plotly.newPlot('chart1', {chart1_json});
    Plotly.newPlot('chart2', {chart2_json});
    Plotly.newPlot('chart3', {chart3_json});
    Plotly.newPlot('chart4', {chart4_json});
    Plotly.newPlot('chart5', {chart5_json});
</script>
"""
            except ImportError:
                charts_html = '<div class="section"><p style="color: #ef4444;">⚠️ Install plotly for interactive charts: <code>pip3 install plotly</code></p></div>'
                charts_script = ""
            
            # Build full HTML
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Analytics Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .header h1 {{ margin: 0; font-size: 2.5rem; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .metric-card {{ background: white; padding: 24px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .metric-label {{ color: #666; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
        .metric-value {{ font-size: 2.2rem; font-weight: 700; color: #333; margin-top: 12px; }}
        .positive {{ color: #10b981; }}
        .negative {{ color: #ef4444; }}
        .chart-container {{ background: white; padding: 25px; border-radius: 10px; margin-bottom: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        th {{ background: #f8f9fa; padding: 16px; text-align: left; font-weight: 600; border-bottom: 2px solid #0066cc; font-size: 0.9rem; color: #333; text-transform: uppercase; letter-spacing: 0.3px; }}
        td {{ padding: 14px 16px; border-bottom: 1px solid #eee; font-size: 0.95rem; }}
        tr:hover {{ background: #f9fafb; }}
        .symbol-row {{ cursor: pointer; transition: background 0.2s; }}
        .symbol-row:hover {{ background: #e8f4f8; }}
        .symbol-cell {{ display: flex; align-items: center; gap: 8px; }}
        .expand-icon {{ display: inline-block; width: 16px; height: 16px; transition: transform 0.3s; font-size: 12px; color: #0066cc; }}
        .expand-icon.expanded {{ transform: rotate(90deg); }}
        .trades-row {{ display: none; background: #f8f9fa; }}
        .trades-row.show {{ display: table-row; }}
        .trades-detail {{ padding: 0 !important; }}
        .trades-table {{ width: 100%; margin: 10px 0; background: white; border: 1px solid #e0e0e0; }}
        .trades-table th {{ background: #e8f4f8; padding: 10px; font-size: 0.85rem; border-bottom: 1px solid #d0d0d0; }}
        .trades-table td {{ padding: 10px; font-size: 0.9rem; border-bottom: 1px solid #f0f0f0; }}
        .trade-count {{ color: #0066cc; font-weight: 600; text-decoration: underline; text-decoration-style: dotted; }}
        h2 {{ margin-top: 0; color: #333; border-bottom: 3px solid #0066cc; padding-bottom: 12px; font-size: 1.8rem; }}
        .number {{ font-family: 'SF Mono', Monaco, monospace; font-weight: 600; }}
        .tooltip-term {{ position: relative; cursor: help; border-bottom: 1px dotted #0066cc; }}
        .tooltip-term:hover::after {{ 
            content: attr(data-tooltip); 
            position: absolute; 
            bottom: 125%; 
            left: 50%; 
            transform: translateX(-50%); 
            background-color: #333; 
            color: white; 
            padding: 8px 12px; 
            border-radius: 6px; 
            font-size: 0.85rem; 
            white-space: nowrap; 
            z-index: 10000; 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-weight: 400;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        .tooltip-term:hover::before {{ 
            content: ''; 
            position: absolute; 
            bottom: 115%; 
            left: 50%; 
            transform: translateX(-50%); 
            border: 6px solid transparent; 
            border-top-color: #333; 
            z-index: 10000;
        }}
        .section {{ background: white; padding: 25px; border-radius: 10px; margin-bottom: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); overflow: visible; }}
        table {{ overflow: visible; }}
        th, td {{ overflow: visible; }} 
        }}
        @media (max-width: 768px) {{
            .metrics {{ grid-template-columns: 1fr; }}
            .metric-value {{ font-size: 1.8rem; }}
            .header h1 {{ font-size: 1.8rem; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Portfolio Analytics Dashboard</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 1.1rem;">Comprehensive Investment Performance Analysis</p>
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
                <div class="metric-label">Portfolio <span class="tooltip-term" data-tooltip="Weighted CAGR: Compound Annual Growth Rate weighted by investment amount and time held">WCAGR</span></div>
                <div class="metric-value {('positive' if cagr >= 0 else 'negative')}">{cagr:.1f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Portfolio <span class="tooltip-term" data-tooltip="XIRR: Internal Rate of Return accounting for timing and size of each cash flow">XIRR</span></div>
                <div class="metric-value {('positive' if xirr >= 0 else 'negative')}">{xirr:.1f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">S&P 500 <span class="tooltip-term" data-tooltip="S&P 500 WCAGR: Weighted average annual return of S&P 500 for your investment periods">WCAGR</span></div>
                <div class="metric-value">{sp500_wcagr:.1f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">S&P 500 <span class="tooltip-term" data-tooltip="S&P 500 XIRR: True return of S&P 500 given your exact investment dates and amounts">XIRR</span></div>
                <div class="metric-value">{sp500_xirr_val:.1f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Outperformance</div>
                <div class="metric-value {('positive' if analysis.get('portfolio_xirr_outperformance', 0) >= 0 else 'negative')}">{analysis.get('portfolio_xirr_outperformance', 0):.1f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Positions</div>
                <div class="metric-value">{len(symbol_stats)}</div>
            </div>
        </div>
        
        {charts_html}
        
        <div class="section">
            <h2>Detailed Holdings</h2>
            <table>
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Trades</th>
                        <th>Invested</th>
                        <th>Current Value</th>
                        <th>Gain</th>
                        <th>Return %</th>
                        <th><span class="tooltip-term" data-tooltip="Weighted CAGR: Compound Annual Growth Rate weighted by amount and time">WCAGR %</span></th>
                        <th><span class="tooltip-term" data-tooltip="XIRR: Internal Rate of Return for actual cash flows">XIRR %</span></th>
                        <th><span class="tooltip-term" data-tooltip="S&P WCAGR: Bench. weighted avg return">S&P WCAGR %</span></th>
                        <th><span class="tooltip-term" data-tooltip="S&P XIRR: Benchmark internal rate return">S&P XIRR %</span></th>
                    </tr>
                </thead>
                <tbody>
"""
            
            for symbol, stats in sorted_symbols:
                symbol_id = symbol.replace('.', '_').replace('-', '_')  # Create valid HTML ID
                trades_count = stats['trades_count']
                
                # Main symbol row (clickable)
                html_content += f"""
                    <tr class="symbol-row" onclick="toggleTrades('{symbol_id}')">
                        <td>
                            <div class="symbol-cell">
                                <span class="expand-icon" id="icon-{symbol_id}">▶</span>
                                <strong>{symbol}</strong>
                            </div>
                        </td>
                        <td class="number trade-count">{trades_count}</td>
                        <td class="number">${stats['total_initial_value']:,.0f}</td>
                        <td class="number">${stats['total_current_value']:,.0f}</td>
                        <td class="number {'positive' if stats['total_gain'] >= 0 else 'negative'}">${stats['total_gain']:,.0f}</td>
                        <td class="number {'positive' if stats['gain_percentage'] >= 0 else 'negative'}">{stats['gain_percentage']:.1f}%</td>
                        <td class="number {'positive' if stats['avg_cagr'] >= 0 else 'negative'}">{stats['avg_cagr']:.1f}%</td>
                        <td class="number {'positive' if stats['avg_xirr'] >= 0 else 'negative'}">{stats['avg_xirr']:.1f}%</td>
                        <td class="number">{stats['avg_sp500_cagr']:.1f}%</td>
                        <td class="number">{stats['avg_sp500_xirr']:.1f}%</td>
                    </tr>
"""
                
                # Hidden detail row with individual trades
                if symbol in trades_by_symbol and trades_count > 0:
                    html_content += f"""
                    <tr class="trades-row" id="trades-{symbol_id}">
                        <td colspan="10" class="trades-detail">
                            <div style="padding: 15px; background: #f8f9fa;">
                                <h4 style="margin: 0 0 10px 0; color: #0066cc;">Individual Trades for {symbol}</h4>
                                <table class="trades-table">
                                    <thead>
                                        <tr>
                                            <th>Date</th>
                                            <th>Shares</th>
                                            <th>Purchase Price</th>
                                            <th>Current Price</th>
                                            <th>Initial Value</th>
                                            <th>Current Value</th>
                                            <th>Gain</th>
                                            <th>WCAGR %</th>
                                            <th>XIRR %</th>
                                            <th>S&P WCAGR %</th>
                                            <th>S&P XIRR %</th>
                                        </tr>
                                    </thead>
                                    <tbody>
"""
                    for trade in trades_by_symbol[symbol]:
                        trade_gain = trade['current_value'] - trade['initial_value']
                        gain_class = 'positive' if trade_gain >= 0 else 'negative'
                        html_content += f"""
                                        <tr>
                                            <td>{trade['purchase_date']}</td>
                                            <td class="number">{trade['shares']}</td>
                                            <td class="number">${trade['purchase_price']:.2f}</td>
                                            <td class="number">${trade['current_price']:.2f}</td>
                                            <td class="number">${trade['initial_value']:,.2f}</td>
                                            <td class="number">${trade['current_value']:,.2f}</td>
                                            <td class="number {gain_class}">${trade_gain:,.2f}</td>
                                            <td class="number {('positive' if trade['stock_cagr'] >= 0 else 'negative')}">{trade['stock_cagr']:.2f}%</td>
                                            <td class="number {('positive' if trade['stock_xirr'] >= 0 else 'negative')}">{trade['stock_xirr']:.2f}%</td>
                                            <td class="number">{trade['sp500_cagr']:.2f}%</td>
                                            <td class="number">{trade['sp500_xirr']:.2f}%</td>
                                        </tr>
"""
                    
                    html_content += """
                                    </tbody>
                                </table>
                            </div>
                        </td>
                    </tr>
"""
            
            html_content += f"""
                </tbody>
            </table>
        </div>
    </div>
    {charts_script}
    <script>
        function toggleTrades(symbolId) {{
            const tradesRow = document.getElementById('trades-' + symbolId);
            const icon = document.getElementById('icon-' + symbolId);
            
            if (tradesRow.classList.contains('show')) {{
                tradesRow.classList.remove('show');
                icon.classList.remove('expanded');
            }} else {{
                tradesRow.classList.add('show');
                icon.classList.add('expanded');
            }}
        }}
    </script>
</body>
</html>
"""
            
            with open(html_path, 'w') as f:
                f.write(html_content)
            
            print(f"✅ HTML report generated: {html_path}")
        except Exception as e:
            print(f"⚠️  Error generating HTML: {e}")
            import traceback
            traceback.print_exc()
