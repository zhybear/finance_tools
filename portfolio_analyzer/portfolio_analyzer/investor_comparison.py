"""Investor comparison module for benchmarking against famous investors.

Author: Zhuo Robert Li
Version: 1.3.5
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class FamousInvestor:
    """Data class for famous investor information."""
    name: str
    xirr: float
    period_start: str
    period_end: str
    notes: str
    category: str  # 'value', 'growth', 'all-market', 'index'


class InvestorBenchmark:
    """Manages famous investor data and comparisons."""
    
    # Historical famous investors and their performance
    FAMOUS_INVESTORS = {
        'Warren Buffett': FamousInvestor(
            name='Warren Buffett',
            xirr=20.1,
            period_start='1965',
            period_end='2023',
            notes='Berkshire Hathaway founder. Most revered investor of all time.',
            category='value'
        ),
        'Peter Lynch': FamousInvestor(
            name='Peter Lynch',
            xirr=29.2,
            period_start='1977',
            period_end='1990',
            notes='Fidelity Magellan Fund manager. One of best track records ever.',
            category='growth'
        ),
        'Bill Miller': FamousInvestor(
            name='Bill Miller',
            xirr=15.8,
            period_start='1991',
            period_end='2005',
            notes='Beat S&P 500 for 15 consecutive years (rare feat).',
            category='value'
        ),
        'George Soros': FamousInvestor(
            name='George Soros',
            xirr=20.0,
            period_start='1969',
            period_end='2000',
            notes='Quantum Fund manager. Master of currency and macro investing.',
            category='hedge'
        ),
        'Joel Greenblatt': FamousInvestor(
            name='Joel Greenblatt',
            xirr=48.1,
            period_start='1985',
            period_end='2005',
            notes='Gotham Capital founder. Exceptional 20-year track record.',
            category='growth'
        ),
        'David Swensen': FamousInvestor(
            name='David Swensen',
            xirr=11.9,
            period_start='1992',
            period_end='2021',
            notes='Yale endowment manager. Conservative diversified approach.',
            category='all-market'
        ),
    }
    
    MARKET_BENCHMARKS = {
        'S&P 500 (US Stocks)': FamousInvestor(
            name='S&P 500 (US Stocks)',
            xirr=10.6,
            period_start='1926',
            period_end='2023',
            notes='Standard US large-cap market index.',
            category='index'
        ),
        'NASDAQ (Tech Heavy)': FamousInvestor(
            name='NASDAQ (Tech Heavy)',
            xirr=10.8,
            period_start='1971',
            period_end='2023',
            notes='Technology and growth stock focused index.',
            category='index'
        ),
        'Global Stocks': FamousInvestor(
            name='Global Stocks',
            xirr=8.5,
            period_start='1970',
            period_end='2023',
            notes='Diversified international stock markets.',
            category='index'
        ),
    }
    
    @classmethod
    def get_comparison(cls, user_xirr: float, user_years: float) -> Dict:
        """
        Generate comparison data for user portfolio vs famous investors.
        
        Args:
            user_xirr: User's portfolio XIRR (percentage)
            user_years: Number of years portfolio has been held
            
        Returns:
            Dictionary with ranking, commentary, and comparison data
        """
        all_investors = {**cls.FAMOUS_INVESTORS, **cls.MARKET_BENCHMARKS}
        
        # Create comparison list with user portfolio
        comparisons = []
        for name, investor in all_investors.items():
            comparisons.append({
                'rank': 0,  # Will be set after sorting
                'name': name,
                'xirr': investor.xirr,
                'category': investor.category,
                'notes': investor.notes,
                'period': f"{investor.period_start}-{investor.period_end}",
            })
        
        # Add user portfolio
        comparisons.append({
            'rank': 0,
            'name': 'Your Portfolio',
            'xirr': user_xirr,
            'category': 'personal',
            'notes': f'Your actual {user_years:.1f}-year track record',
            'period': 'Your Period',
            'is_user': True,
        })
        
        # Sort by XIRR (highest first)
        comparisons.sort(key=lambda x: x['xirr'], reverse=True)
        
        # Add ranks and calculate stats
        for i, comp in enumerate(comparisons, 1):
            comp['rank'] = i
        
        # Find user's position
        user_rank = next(c['rank'] for c in comparisons if c.get('is_user'))
        
        # Calculate metrics
        all_xirrs = [c['xirr'] for c in comparisons if not c.get('is_user')]
        percentile = (len(all_xirrs) - len([x for x in all_xirrs if x > user_xirr])) / len(all_xirrs) * 100
        
        # Generate commentary
        commentary = cls._generate_commentary(user_xirr, user_rank, len(comparisons))
        
        return {
            'user_xirr': user_xirr,
            'user_rank': user_rank,
            'user_percentile': percentile,
            'total_investors': len(comparisons),  # Include user in total count
            'comparisons': comparisons,
            'commentary': commentary,
            'outperformance_vs_sp500': user_xirr - 10.6,  # S&P 500 XIRR
        }
    
    @classmethod
    def _generate_commentary(cls, user_xirr: float, rank: int, total: int) -> str:
        """Generate fun commentary based on performance."""
        
        if user_xirr >= 29:
            return f"🌟 LEGENDARY! You're competing with Peter Lynch territory. This is elite-level exceptional."
        elif user_xirr >= 20:
            return f"🏆 EXCELLENT! You're in Warren Buffett's league. You've beaten 99%+ of investors."
        elif user_xirr >= 15:
            return f"🎯 GREAT! You've outperformed most professional fund managers. Your strategy works!"
        elif user_xirr >= 10.6:
            return f"✅ SOLID! You're beating the S&P 500. You're doing better than passive investors."
        elif user_xirr >= 8:
            return f"📊 OK. You're tracking close to markets. Consider refining your strategy."
        else:
            return f"⚠️ CAUTION. You're underperforming the market. Time to reassess your approach."
    
    @classmethod
    def get_chart_data(cls, comparisons: List[Dict]) -> Dict:
        """Prepare data for visualization charts."""
        
        # Show all investors in chart for complete comparison
        top_investors = comparisons  # Show all investors, sorted by XIRR desc
        
        return {
            'names': [c['name'] for c in top_investors],
            'xirrs': [c['xirr'] for c in top_investors],
            'categories': [c['category'] for c in top_investors],
            'colors': cls._get_colors(top_investors),
        }
    
    @classmethod
    def _get_colors(cls, comparisons: List[Dict]) -> List[str]:
        """Get colors for chart based on investor category."""
        
        color_map = {
            'value': '#1f77b4',      # Blue
            'growth': '#2ca02c',     # Green
            'hedge': '#d62728',      # Red
            'all-market': '#ff7f0e', # Orange
            'index': '#9467bd',      # Purple
            'personal': '#17becf',   # Cyan - highlight user
        }
        
        return [color_map.get(c['category'], '#7f7f7f') for c in comparisons]
    
    @classmethod
    def get_growth_projection(cls, initial: float, xirr: float, years: int) -> float:
        """Calculate portfolio growth given XIRR and years."""
        return initial * ((1 + xirr / 100) ** years)
