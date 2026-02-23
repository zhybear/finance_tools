"""
Portfolio Performance Analyzer - Test Suite

Modular test package for comprehensive testing of all portfolio_analyzer components.

Run all tests:
    python3 -m unittest discover tests -v

Run specific module:
    python3 -m unittest tests.test_metrics -v
    python3 -m unittest tests.test_loaders -v
    python3 -m unittest tests.test_analyzer -v
    python3 -m unittest tests.test_reports -v
    python3 -m unittest tests.test_cli -v
    python3 -m unittest tests.test_utils -v

Author: Zhuo Robert Li
Version: 1.2.0
License: ISC
"""

__all__ = [
    'test_metrics',
    'test_loaders',
    'test_analyzer',
    'test_reports',
    'test_cli',
    'test_utils',
]
