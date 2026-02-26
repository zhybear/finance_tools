"""
Unit tests for Investor Comparison Module

Run with:
    python3 -m unittest test_investor_comparison.py -v

Author: Zhuo Robert Li
Version: 1.3.5
License: ISC
"""

import unittest
from portfolio_analyzer.investor_comparison import InvestorBenchmark, FamousInvestor


class TestFamousInvestorDataclass(unittest.TestCase):
    """Test FamousInvestor data class"""
    
    def test_famous_investor_creation(self):
        """Test creating a FamousInvestor instance"""
        investor = FamousInvestor(
            name='Warren Buffett',
            xirr=20.1,
            period_start='1965',
            period_end='2023',
            notes='Test notes',
            category='value'
        )
        
        self.assertEqual(investor.name, 'Warren Buffett')
        self.assertEqual(investor.xirr, 20.1)
        self.assertEqual(investor.period_start, '1965')
        self.assertEqual(investor.period_end, '2023')
        self.assertEqual(investor.notes, 'Test notes')
        self.assertEqual(investor.category, 'value')
    
    def test_famous_investor_fields(self):
        """Test all required fields exist"""
        investor = FamousInvestor(
            name='Test',
            xirr=15.0,
            period_start='2000',
            period_end='2020',
            notes='Notes',
            category='growth'
        )
        
        # Verify all fields are accessible
        self.assertIsNotNone(investor.name)
        self.assertIsNotNone(investor.xirr)
        self.assertIsNotNone(investor.period_start)
        self.assertIsNotNone(investor.period_end)
        self.assertIsNotNone(investor.notes)
        self.assertIsNotNone(investor.category)


class TestInvestorBenchmarkData(unittest.TestCase):
    """Test InvestorBenchmark static data"""
    
    def test_famous_investors_exist(self):
        """Test that famous investors are defined"""
        self.assertGreater(len(InvestorBenchmark.FAMOUS_INVESTORS), 0)
        self.assertIn('Warren Buffett', InvestorBenchmark.FAMOUS_INVESTORS)
        self.assertIn('Peter Lynch', InvestorBenchmark.FAMOUS_INVESTORS)
        self.assertIn('Joel Greenblatt', InvestorBenchmark.FAMOUS_INVESTORS)
    
    def test_market_benchmarks_exist(self):
        """Test that market benchmarks are defined"""
        self.assertGreater(len(InvestorBenchmark.MARKET_BENCHMARKS), 0)
        
        # Check for key benchmarks
        benchmark_names = list(InvestorBenchmark.MARKET_BENCHMARKS.keys())
        self.assertTrue(any('S&P 500' in name for name in benchmark_names))
        self.assertTrue(any('NASDAQ' in name for name in benchmark_names))
    
    def test_famous_investors_have_valid_xirr(self):
        """Test that all famous investors have valid XIRR values"""
        for name, investor in InvestorBenchmark.FAMOUS_INVESTORS.items():
            self.assertIsInstance(investor.xirr, (int, float))
            self.assertGreater(investor.xirr, -100)  # XIRR should be reasonable
            self.assertLess(investor.xirr, 200)  # Max reasonable XIRR
    
    def test_joel_greenblatt_has_highest_xirr(self):
        """Test that Joel Greenblatt has highest XIRR among famous investors"""
        all_investors = {**InvestorBenchmark.FAMOUS_INVESTORS, **InvestorBenchmark.MARKET_BENCHMARKS}
        joel = all_investors['Joel Greenblatt']
        
        # Joel should have one of the highest XIRRs
        self.assertGreater(joel.xirr, 40.0)

    def test_growth_projection(self):
        """Test growth projection calculation"""
        projected = InvestorBenchmark.get_growth_projection(1000, 10.0, 2)
        self.assertAlmostEqual(projected, 1210.0, places=2)


class TestGetComparison(unittest.TestCase):
    """Test InvestorBenchmark.get_comparison() method"""
    
    def test_get_comparison_returns_dict(self):
        """Test that get_comparison returns a dictionary"""
        result = InvestorBenchmark.get_comparison(19.1, 13.2)
        self.assertIsInstance(result, dict)
    
    def test_get_comparison_has_required_keys(self):
        """Test that comparison result has all required keys"""
        result = InvestorBenchmark.get_comparison(19.1, 13.2)
        
        required_keys = [
            'user_xirr',
            'user_rank',
            'user_percentile',
            'total_investors',
            'comparisons',
            'commentary',
            'outperformance_vs_sp500'
        ]
        
        for key in required_keys:
            self.assertIn(key, result, f"Missing key: {key}")
    
    def test_get_comparison_user_xirr(self):
        """Test that user XIRR is correctly returned"""
        user_xirr = 19.1
        result = InvestorBenchmark.get_comparison(user_xirr, 13.2)
        self.assertEqual(result['user_xirr'], user_xirr)
    
    def test_get_comparison_includes_all_investors(self):
        """Test that all investors are included in comparisons"""
        result = InvestorBenchmark.get_comparison(19.1, 13.2)
        comparisons = result['comparisons']
        
        # Should have famous investors + benchmarks + user
        expected_count = len(InvestorBenchmark.FAMOUS_INVESTORS) + len(InvestorBenchmark.MARKET_BENCHMARKS) + 1
        self.assertEqual(len(comparisons), expected_count)
    
    def test_get_comparison_includes_user_portfolio(self):
        """Test that user portfolio is included in comparisons"""
        result = InvestorBenchmark.get_comparison(19.1, 13.2)
        comparisons = result['comparisons']
        
        user_found = any(c.get('is_user') for c in comparisons)
        self.assertTrue(user_found, "User portfolio not found in comparisons")
    
    def test_get_comparison_sorted_by_xirr(self):
        """Test that comparisons are sorted by XIRR descending"""
        result = InvestorBenchmark.get_comparison(19.1, 13.2)
        comparisons = result['comparisons']
        
        # Check that XIRRs are in descending order
        xirrs = [c['xirr'] for c in comparisons]
        self.assertEqual(xirrs, sorted(xirrs, reverse=True))
    
    def test_get_comparison_has_ranks(self):
        """Test that all comparisons have rank numbers"""
        result = InvestorBenchmark.get_comparison(19.1, 13.2)
        comparisons = result['comparisons']
        
        expected_count = len(comparisons)
        for i, comp in enumerate(comparisons, 1):
            self.assertIn('rank', comp)
            self.assertEqual(comp['rank'], i)
    
    def test_user_rank_correct(self):
        """Test that user rank is correctly calculated"""
        result = InvestorBenchmark.get_comparison(19.1, 13.2)
        
        # User with 19.1% XIRR should be around rank 5
        # (between Peter Lynch 29.2% and Warren Buffett 20.1%)
        self.assertGreater(result['user_rank'], 1)
        self.assertLess(result['user_rank'], len(result['comparisons']))
    
    def test_total_investors_count(self):
        """Test that total_investors count is correct"""
        result = InvestorBenchmark.get_comparison(19.1, 13.2)
        
        # Should include famous investors + benchmarks + user portfolio
        expected_total = len(InvestorBenchmark.FAMOUS_INVESTORS) + len(InvestorBenchmark.MARKET_BENCHMARKS) + 1
        self.assertEqual(result['total_investors'], expected_total)
    
    def test_percentile_calculation(self):
        """Test that percentile is calculated correctly"""
        result = InvestorBenchmark.get_comparison(19.1, 13.2)
        
        percentile = result['user_percentile']
        self.assertGreater(percentile, 0)
        self.assertLessEqual(percentile, 100)
    
    def test_outperformance_vs_sp500(self):
        """Test S&P 500 outperformance calculation"""
        user_xirr = 19.1
        result = InvestorBenchmark.get_comparison(user_xirr, 13.2)
        
        # S&P 500 XIRR is typically around 10.6%
        outperformance = result['outperformance_vs_sp500']
        expected = user_xirr - 10.6
        self.assertAlmostEqual(outperformance, expected, places=1)
    
    def test_commentary_exists(self):
        """Test that commentary is generated"""
        result = InvestorBenchmark.get_comparison(19.1, 13.2)
        
        self.assertIsNotNone(result['commentary'])
        self.assertIsInstance(result['commentary'], str)
        self.assertGreater(len(result['commentary']), 0)
    
    def test_comparison_entries_have_required_fields(self):
        """Test that each comparison entry has required fields"""
        result = InvestorBenchmark.get_comparison(19.1, 13.2)
        
        required_fields = ['rank', 'name', 'xirr', 'category', 'notes', 'period']
        
        for comp in result['comparisons']:
            for field in required_fields:
                self.assertIn(field, comp, f"Missing field '{field}' in comparison")
    
    def test_high_performing_user_commentary(self):
        """Test commentary for high-performing user"""
        result = InvestorBenchmark.get_comparison(30.0, 10.0)  # Very high XIRR
        
        commentary = result['commentary']
        # Should contain positive emoji/words for high performance
        self.assertTrue(
            any(term in commentary for term in ['🌟', 'LEGENDARY', 'EXCELLENT', '🏆'])
        )
    
    def test_low_performing_user_commentary(self):
        """Test commentary for low-performing user"""
        result = InvestorBenchmark.get_comparison(5.0, 10.0)  # Low XIRR
        
        commentary = result['commentary']
        # Should be more cautious
        self.assertIsNotNone(commentary)


class TestGetChartData(unittest.TestCase):
    """Test InvestorBenchmark.get_chart_data() method"""
    
    def test_get_chart_data_returns_dict(self):
        """Test that get_chart_data returns dictionary"""
        result = InvestorBenchmark.get_comparison(19.1, 13.2)
        chart_data = InvestorBenchmark.get_chart_data(result['comparisons'])
        
        self.assertIsInstance(chart_data, dict)
    
    def test_get_chart_data_has_required_keys(self):
        """Test that chart data has required keys"""
        result = InvestorBenchmark.get_comparison(19.1, 13.2)
        chart_data = InvestorBenchmark.get_chart_data(result['comparisons'])
        
        required_keys = ['names', 'xirrs', 'categories', 'colors']
        for key in required_keys:
            self.assertIn(key, chart_data)
    
    def test_get_chart_data_arrays_same_length(self):
        """Test that all arrays in chart data have same length"""
        result = InvestorBenchmark.get_comparison(19.1, 13.2)
        chart_data = InvestorBenchmark.get_chart_data(result['comparisons'])
        
        names_len = len(chart_data['names'])
        xirrs_len = len(chart_data['xirrs'])
        colors_len = len(chart_data['colors'])
        
        self.assertEqual(names_len, xirrs_len)
        self.assertEqual(names_len, colors_len)
    
    def test_get_chart_data_includes_all_investors(self):
        """Test that chart data includes all investors"""
        result = InvestorBenchmark.get_comparison(19.1, 13.2)
        chart_data = InvestorBenchmark.get_chart_data(result['comparisons'])
        
        # Should include all investors from comparisons
        self.assertEqual(len(chart_data['names']), len(result['comparisons']))
    
    def test_get_chart_data_user_included(self):
        """Test that user portfolio is in chart data"""
        result = InvestorBenchmark.get_comparison(19.1, 13.2)
        chart_data = InvestorBenchmark.get_chart_data(result['comparisons'])
        
        user_found = any('Your Portfolio' in name or 'your' in name.lower() 
                        for name in chart_data['names'])
        self.assertTrue(user_found)
    
    def test_get_chart_data_sorted_xirrs(self):
        """Test that XIRR values are in descending order"""
        result = InvestorBenchmark.get_comparison(19.1, 13.2)
        chart_data = InvestorBenchmark.get_chart_data(result['comparisons'])
        
        xirrs = chart_data['xirrs']
        self.assertEqual(xirrs, sorted(xirrs, reverse=True))
    
    def test_get_chart_data_colors_valid(self):
        """Test that colors are valid hex codes"""
        result = InvestorBenchmark.get_comparison(19.1, 13.2)
        chart_data = InvestorBenchmark.get_chart_data(result['comparisons'])
        
        for color in chart_data['colors']:
            # Should be valid hex color
            self.assertTrue(color.startswith('#'))
            self.assertEqual(len(color), 7)  # #RRGGBB


class TestGenerateCommentary(unittest.TestCase):
    """Test InvestorBenchmark._generate_commentary() method"""
    
    def test_commentary_legendary_performance(self):
        """Test commentary for legendary performance (very high XIRR)"""
        commentary = InvestorBenchmark._generate_commentary(50.0, 2, 10)
        
        self.assertIsInstance(commentary, str)
        self.assertGreater(len(commentary), 0)
        # Should mention excellent/legendary performance
        self.assertTrue(
            any(word in commentary.upper() for word in ['LEGENDARY', 'EXCELLENT', 'REMARKABLE'])
        )
    
    def test_commentary_excellent_performance(self):
        """Test commentary for excellent performance"""
        commentary = InvestorBenchmark._generate_commentary(25.0, 4, 10)
        
        self.assertIsInstance(commentary, str)
        self.assertGreater(len(commentary), 0)
    
    def test_commentary_average_performance(self):
        """Test commentary for average performance"""
        commentary = InvestorBenchmark._generate_commentary(10.0, 5, 10)
        
        self.assertIsInstance(commentary, str)
        self.assertGreater(len(commentary), 0)
    
    def test_commentary_underperformance(self):
        """Test commentary for underperformance"""
        commentary = InvestorBenchmark._generate_commentary(5.0, 9, 10)
        
        self.assertIsInstance(commentary, str)
        self.assertGreater(len(commentary), 0)
    
    def test_commentary_contains_emoji(self):
        """Test that commentary contains emoji"""
        commentary = InvestorBenchmark._generate_commentary(19.1, 5, 10)
        
        # Should contain at least one emoji
        emoji_characters = ['🏆', '⭐', '✅', '🌟', '📊', '⚠️', '❌', '🎯']
        self.assertTrue(any(emoji in commentary for emoji in emoji_characters))


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def test_zero_xirr(self):
        """Test with zero XIRR"""
        result = InvestorBenchmark.get_comparison(0.0, 10.0)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['user_xirr'], 0.0)
    
    def test_negative_xirr(self):
        """Test with negative XIRR (loss)"""
        result = InvestorBenchmark.get_comparison(-10.0, 10.0)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['user_xirr'], -10.0)
    
    def test_very_high_xirr(self):
        """Test with very high XIRR"""
        result = InvestorBenchmark.get_comparison(100.0, 10.0)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['user_xirr'], 100.0)
        # User should be ranked very high
        self.assertLess(result['user_rank'], 3)
    
    def test_short_holding_period(self):
        """Test with very short holding period"""
        result = InvestorBenchmark.get_comparison(19.1, 0.1)
        
        self.assertIsNotNone(result)
        self.assertGreater(result['user_percentile'], 0)
    
    def test_very_long_holding_period(self):
        """Test with very long holding period"""
        result = InvestorBenchmark.get_comparison(19.1, 50.0)
        
        self.assertIsNotNone(result)
        self.assertGreater(result['user_percentile'], 0)


if __name__ == '__main__':
    unittest.main()
