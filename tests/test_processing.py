"""Tests for processing layer."""

import numpy as np
import pandas as pd
import pytest

from fundlens.processing.returns import log_returns, cumulative_returns, annualized_return
from fundlens.processing.volatility import rolling_volatility


def test_log_returns_first_is_nan(sample_prices):
    lr = log_returns(sample_prices)
    assert pd.isna(lr.iloc[0])
    assert not pd.isna(lr.iloc[1])


def test_cumulative_returns_starts_near_one(sample_prices):
    lr = log_returns(sample_prices).dropna()
    cum = cumulative_returns(lr)
    assert abs(cum.iloc[0] - 1.0) < 0.1  # first return is close to $1


def test_rolling_vol_shape(sample_prices):
    lr = log_returns(sample_prices)
    vol = rolling_volatility(lr, window=30)
    assert len(vol) == len(sample_prices)


def test_annualized_return_positive_for_uptrend():
    prices = pd.Series([100.0, 101.0, 102.0, 103.0])
    lr = log_returns(prices).dropna()
    assert annualized_return(lr) > 0
