import numpy as np
import pandas as pd


def rolling_volatility(log_ret: pd.Series, window: int, trading_days: int = 252) -> pd.Series:
    """Annualized rolling volatility (std dev of log-returns × sqrt(252))."""
    return log_ret.rolling(window, min_periods=window // 2).std() * np.sqrt(trading_days)


def ewma_volatility(log_ret: pd.Series, span: int = 30, trading_days: int = 252) -> pd.Series:
    """Annualized EWMA volatility."""
    return log_ret.ewm(span=span).std() * np.sqrt(trading_days)


def sharpe_ratio(log_ret: pd.Series, window: int, risk_free: float = 0.0, trading_days: int = 252) -> pd.Series:
    """Rolling Sharpe ratio. risk_free is annual; converted to daily internally."""
    rf_daily = risk_free / trading_days
    excess = log_ret - rf_daily
    roll_mean = excess.rolling(window, min_periods=window // 2).mean()
    roll_std = excess.rolling(window, min_periods=window // 2).std()
    return (roll_mean / roll_std) * np.sqrt(trading_days)
