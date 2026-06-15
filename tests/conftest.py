"""Shared pytest fixtures."""

import pytest
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fundlens.storage.database import Base


@pytest.fixture(scope="session")
def in_memory_engine():
    """DuckDB in-memory engine — fast, isolated, no files."""
    engine = create_engine("duckdb:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(in_memory_engine):
    Session = sessionmaker(bind=in_memory_engine)
    s = Session()
    yield s
    s.rollback()
    s.close()


@pytest.fixture
def sample_prices() -> pd.Series:
    """5 years of synthetic daily prices (log-normal random walk)."""
    np.random.seed(42)
    n = 252 * 5
    log_ret = np.random.normal(0.0003, 0.01, n)
    prices = 100 * np.exp(np.cumsum(log_ret))
    idx = pd.bdate_range("2019-01-02", periods=n)
    return pd.Series(prices, index=idx, name="nav")


@pytest.fixture
def sample_df(sample_prices) -> pd.DataFrame:
    """DataFrame with date/nav/log_return/source columns."""
    import numpy as np
    df = sample_prices.reset_index()
    df.columns = ["date", "nav"]
    df["date"] = df["date"].dt.date
    df["log_return"] = np.log(df["nav"] / df["nav"].shift(1))
    df["source"] = "mock"
    return df.dropna().reset_index(drop=True)
