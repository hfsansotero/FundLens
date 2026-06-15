import pandas as pd
import numpy as np


def drawdown_series(prices: pd.Series) -> pd.Series:
    """Drawdown at each point: (price - running_max) / running_max."""
    running_max = prices.cummax()
    return (prices - running_max) / running_max


def max_drawdown(prices: pd.Series) -> float:
    return float(drawdown_series(prices).min())


def recovery_periods(prices: pd.Series) -> list[dict]:
    """List of dict with keys: peak_date, trough_date, recovery_date, drawdown_pct."""
    # TODO: implement in Phase 1
    raise NotImplementedError
