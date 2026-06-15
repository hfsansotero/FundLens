import numpy as np
import pandas as pd


def log_returns(prices: pd.Series) -> pd.Series:
    """Compute log-returns: ln(P_t / P_{t-1}). Result index-aligned with prices."""
    return np.log(prices / prices.shift(1))


def cumulative_returns(log_ret: pd.Series) -> pd.Series:
    """Convert log-returns to cumulative returns (growth of $1)."""
    return np.exp(log_ret.cumsum())


def annualized_return(log_ret: pd.Series, trading_days: int = 252) -> float:
    """Annualized geometric return from a log-return series."""
    total_log = log_ret.sum()
    n_days = len(log_ret)
    if n_days == 0:
        return float("nan")
    return float(np.exp(total_log * trading_days / n_days) - 1)
