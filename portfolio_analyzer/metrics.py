"""Metrics calculation module for portfolio analysis.

Provides CAGR (Compound Annual Growth Rate) and XIRR (Extended Internal Rate of Return)
calculation functions.
"""

import numpy as np
import pandas as pd
from scipy.optimize import newton
import logging

logger = logging.getLogger(__name__)

DAYS_PER_YEAR = 365.25


def calculate_cagr(start_value: float, end_value: float, years: float) -> float:
    """
    Calculate Compound Annual Growth Rate (CAGR).
    
    Formula: CAGR = ((End Value / Start Value) ^ (1 / Years) - 1) * 100
    
    Args:
        start_value: Initial investment value
        end_value: Final investment value
        years: Time period in years
        
    Returns:
        CAGR as a percentage (e.g., 15.5 for 15.5%)
    """
    if start_value <= 0 or years <= 0:
        return 0.0
    return (pow(end_value / start_value, 1 / years) - 1) * 100


def calculate_xirr(dates: list[str], cash_flows: list[float]) -> float:
    """
    Calculate Extended Internal Rate of Return (XIRR).
    
    XIRR accounts for the precise timing of cash flows, providing more accurate returns
    when investments are made at different times. Uses Newton-Raphson root finding to
    solve: NPV = Σ(CF / (1+r)^(Years)) = 0
    
    Args:
        dates: List of dates in YYYY-MM-DD format for each cash flow
        cash_flows: List of cash flows (negative for investments, positive for returns)
                   Must have at least 2 cash flows with different signs
        
    Returns:
        XIRR as a percentage (e.g., 15.5 for 15.5%)
        Returns 0.0 if XIRR cannot be calculated
    """
    if len(dates) != len(cash_flows) or len(dates) < 2:
        return 0.0
    
    # Check for at least one positive and one negative cash flow
    if all(cf >= 0 for cf in cash_flows) or all(cf <= 0 for cf in cash_flows):
        logger.debug("XIRR requires both positive and negative cash flows")
        return 0.0
    
    try:
        # Convert date strings to datetime objects
        date_objects = [pd.to_datetime(d) for d in dates]
        
        # Calculate days from first date
        start_date = date_objects[0]
        days_from_start = [(d - start_date).days for d in date_objects]
        
        def npv_func(rate):
            """Calculate NPV for given rate (as decimal)"""
            npv = 0
            for i, cf in enumerate(cash_flows):
                days = days_from_start[i]
                years = days / DAYS_PER_YEAR
                if rate <= -1:
                    return float('inf')
                npv += cf / ((1 + rate) ** years)
            return npv
        
        # Try multiple initial guesses
        for initial_guess in [0.1, 0.01, -0.1, 0.5, -0.5]:
            try:
                xirr_decimal = newton(npv_func, initial_guess, maxiter=100)
                
                if np.isnan(xirr_decimal) or np.isinf(xirr_decimal):
                    continue
                
                npv_check = npv_func(xirr_decimal)
                if abs(npv_check) < 1e-6:
                    return xirr_decimal * 100
            except (RuntimeError, ValueError, OverflowError):
                continue
        
        logger.debug(f"XIRR convergence failed for {len(dates)} cash flows")
        return 0.0
    except Exception as e:
        logger.warning(f"XIRR calculation error: {e}")
        return 0.0
